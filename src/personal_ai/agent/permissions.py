from __future__ import annotations

import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

from personal_ai.vault import VaultStore
from personal_ai.vault.session import VaultLockedError, VaultSessionManager


MAX_SCOPED_GRANT_DAYS = 30
AUDIT_RECORD_TYPE = "device_agent_audit"
GRANT_RECORD_TYPE = "device_agent_grant"


class AgentPermissionError(Exception):
    """Base error for Device Agent permission decisions."""


class AgentPermissionValidationError(AgentPermissionError):
    """Raised when an action preview or grant request is invalid."""


class AgentPermissionDeniedError(AgentPermissionError):
    """Raised when default-deny policy rejects an approval request."""


class AgentVaultLockedError(AgentPermissionError):
    """Raised when an action needs immediate encrypted Vault audit."""


class AgentCapability(StrEnum):
    READ_METADATA = "read_metadata"
    READ_TEXT = "read_text"
    LAUNCH_APP = "launch_app"
    RUN_TERMINAL = "run_terminal"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    NETWORK = "network"
    READ_SECRET = "read_secret"
    ADMIN = "admin"


class AgentRisk(StrEnum):
    OBSERVE = "observe"
    LAUNCH = "launch"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    HIGH = "high"


class GrantDecision(StrEnum):
    DENY = "deny"
    ONCE = "once"
    SESSION = "session"
    SCOPED = "scoped"


SAFE_CAPABILITIES = {
    AgentCapability.READ_METADATA,
    AgentCapability.READ_TEXT,
    AgentCapability.LAUNCH_APP,
}

HIGH_RISK_CAPABILITIES = {
    AgentCapability.WRITE_FILE,
    AgentCapability.DELETE_FILE,
    AgentCapability.NETWORK,
    AgentCapability.READ_SECRET,
    AgentCapability.ADMIN,
}

SHELL_EXECUTABLES = {"sh", "bash", "zsh", "fish", "dash", "cmd", "powershell", "pwsh"}
SHELL_OPERATORS = {"|", "||", "&&", ";", ">", ">>", "<", "<<", "&"}


@dataclass(frozen=True)
class TerminalPreview:
    argv: tuple[str, ...]
    cwd: str
    expected_effect: str

    def to_dict(self) -> dict[str, object]:
        return {"argv": list(self.argv), "cwd": self.cwd, "expected_effect": self.expected_effect, "shell": False}


@dataclass(frozen=True)
class AgentActionRequest:
    action_id: str
    capability: AgentCapability
    target_scope: str
    device_id: str
    description: str
    preview: str
    terminal: TerminalPreview | None = None
    audit_metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        capability: AgentCapability,
        target_scope: str,
        device_id: str,
        description: str,
        preview: str,
        terminal: TerminalPreview | None = None,
        audit_metadata: dict[str, object] | None = None,
    ) -> "AgentActionRequest":
        return cls(
            uuid.uuid4().hex,
            capability,
            target_scope,
            device_id,
            description,
            preview,
            terminal,
            dict(audit_metadata or {}),
        )

    @property
    def risk(self) -> AgentRisk:
        if self.capability in {AgentCapability.READ_METADATA, AgentCapability.READ_TEXT}:
            return AgentRisk.OBSERVE
        if self.capability == AgentCapability.LAUNCH_APP:
            return AgentRisk.LAUNCH
        if self.capability == AgentCapability.WRITE_FILE:
            return AgentRisk.WRITE
        if self.capability == AgentCapability.DELETE_FILE:
            return AgentRisk.DESTRUCTIVE
        return AgentRisk.HIGH


@dataclass(frozen=True)
class PermissionGrant:
    grant_id: str
    capability: AgentCapability
    target_scope: str
    device_id: str
    issued_at: str
    expires_at: str | None
    decision: GrantDecision

    def to_dict(self) -> dict[str, str | None]:
        return {"grant_id": self.grant_id, "capability": self.capability, "target_scope": self.target_scope, "device_id": self.device_id, "issued_at": self.issued_at, "expires_at": self.expires_at, "decision": self.decision}


@dataclass(frozen=True)
class AgentAuditEvent:
    event_id: str
    action_id: str
    capability: AgentCapability
    target_scope: str
    device_id: str
    decision: GrantDecision
    risk: AgentRisk
    created_at: str
    deferred: bool
    audit_metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {"event_id": self.event_id, "action_id": self.action_id, "capability": self.capability, "target_scope": self.target_scope, "device_id": self.device_id, "decision": self.decision, "risk": self.risk, "created_at": self.created_at, "deferred": self.deferred, "audit_metadata": self.audit_metadata}


@dataclass(frozen=True)
class PermissionAuthorization:
    action_id: str
    decision: GrantDecision
    pending_audit: bool
    grant_id: str | None


@dataclass(frozen=True)
class PermissionPreview:
    action_id: str
    capability: AgentCapability
    risk: AgentRisk
    allowed_decisions: tuple[GrantDecision, ...]
    vault_required: bool
    reason: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "capability": self.capability,
            "risk": self.risk,
            "allowed_decisions": list(self.allowed_decisions),
            "vault_required": self.vault_required,
            "reason": self.reason,
        }


class PermissionEngine:
    """Default-deny policy core. It authorizes previews but never executes actions."""

    def __init__(self, vault_session_manager: VaultSessionManager) -> None:
        self._vault_session_manager = vault_session_manager
        self._session_grants: list[PermissionGrant] = []
        self._pending_audits: list[AgentAuditEvent] = []

    def allowed_decisions(self, request: AgentActionRequest) -> tuple[GrantDecision, ...]:
        self._validate_request(request)
        unlocked = self._vault_session_manager.status().vault_state == "unlocked"
        if request.capability == AgentCapability.RUN_TERMINAL:
            if not unlocked:
                raise AgentVaultLockedError("Vault unlock is required for terminal audit.")
            return (GrantDecision.ONCE,)
        if request.capability in HIGH_RISK_CAPABILITIES:
            if not unlocked:
                raise AgentVaultLockedError("Vault unlock is required for high-risk actions.")
            return (GrantDecision.ONCE,)
        if request.capability in SAFE_CAPABILITIES:
            return (GrantDecision.ONCE,) if not unlocked else (GrantDecision.ONCE, GrantDecision.SESSION, GrantDecision.SCOPED)
        raise AgentPermissionDeniedError("Capability is denied by default.")

    def preview(self, request: AgentActionRequest) -> PermissionPreview:
        try:
            decisions = self.allowed_decisions(request)
            return PermissionPreview(
                action_id=request.action_id,
                capability=request.capability,
                risk=request.risk,
                allowed_decisions=decisions,
                vault_required=False,
                reason=None,
            )
        except AgentVaultLockedError as error:
            return PermissionPreview(
                action_id=request.action_id,
                capability=request.capability,
                risk=request.risk,
                allowed_decisions=(),
                vault_required=True,
                reason=str(error),
            )

    def approve(self, request: AgentActionRequest, decision: GrantDecision, *, expires_at: datetime | None = None) -> PermissionAuthorization:
        if decision not in self.allowed_decisions(request) or decision == GrantDecision.DENY:
            raise AgentPermissionDeniedError("This permission decision is not allowed for the action.")
        now = datetime.now(UTC)
        grant: PermissionGrant | None = None
        if decision == GrantDecision.SESSION:
            grant = self._create_grant(request, decision, now, None)
            self._session_grants.append(grant)
        elif decision == GrantDecision.SCOPED:
            if expires_at is None or expires_at.tzinfo is None or expires_at <= now or expires_at > now + timedelta(days=MAX_SCOPED_GRANT_DAYS):
                raise AgentPermissionValidationError("Scoped expiry must be within 30 days.")
            grant = self._create_grant(request, decision, now, expires_at)
            with self._vault_access() as vault:
                vault.put_record(GRANT_RECORD_TYPE, grant.to_dict())
        event = AgentAuditEvent(
            uuid.uuid4().hex,
            request.action_id,
            request.capability,
            request.target_scope,
            request.device_id,
            decision,
            request.risk,
            now.isoformat(),
            False,
            dict(request.audit_metadata),
        )
        if self._vault_session_manager.status().vault_state == "unlocked":
            with self._vault_access() as vault:
                vault.put_record(AUDIT_RECORD_TYPE, event.to_dict())
            return PermissionAuthorization(request.action_id, decision, False, grant.grant_id if grant else None)
        self._pending_audits.append(AgentAuditEvent(**{**event.__dict__, "deferred": True}))
        return PermissionAuthorization(request.action_id, decision, True, None)

    def is_session_granted(self, request: AgentActionRequest) -> bool:
        return any(self._grant_matches(grant, request) for grant in self._session_grants)

    def seal_pending_audits(self) -> int:
        if not self._pending_audits:
            return 0
        with self._vault_access() as vault:
            for event in self._pending_audits:
                vault.put_record(AUDIT_RECORD_TYPE, event.to_dict())
        count = len(self._pending_audits)
        self._pending_audits.clear()
        return count

    @property
    def pending_audit_count(self) -> int:
        return len(self._pending_audits)

    @staticmethod
    def _validate_request(request: AgentActionRequest) -> None:
        for value, label in ((request.action_id, "Action ID"), (request.target_scope, "Target scope"), (request.device_id, "Device ID"), (request.description, "Description"), (request.preview, "Preview")):
            if not isinstance(value, str) or not value.strip():
                raise AgentPermissionValidationError(f"{label} is required.")
        if request.capability == AgentCapability.RUN_TERMINAL:
            if request.terminal is None:
                raise AgentPermissionValidationError("Terminal action requires exact argv preview.")
            PermissionEngine._validate_terminal_preview(request.terminal)
        elif request.terminal is not None:
            raise AgentPermissionValidationError("Terminal preview is allowed only for terminal capability.")

    @staticmethod
    def _validate_terminal_preview(preview: TerminalPreview) -> None:
        if not preview.argv or any(not isinstance(arg, str) or not arg for arg in preview.argv):
            raise AgentPermissionValidationError("Terminal argv is required.")
        if Path(preview.argv[0]).name.lower() in SHELL_EXECUTABLES:
            raise AgentPermissionDeniedError("Shell executables are prohibited.")
        if any(arg in SHELL_OPERATORS or "\n" in arg or "\r" in arg for arg in preview.argv):
            raise AgentPermissionDeniedError("Shell operators are prohibited.")
        if not isinstance(preview.cwd, str) or not preview.cwd or not isinstance(preview.expected_effect, str) or not preview.expected_effect.strip():
            raise AgentPermissionValidationError("Terminal preview is incomplete.")

    @staticmethod
    def _create_grant(request: AgentActionRequest, decision: GrantDecision, issued_at: datetime, expires_at: datetime | None) -> PermissionGrant:
        return PermissionGrant(uuid.uuid4().hex, request.capability, request.target_scope, request.device_id, issued_at.isoformat(), expires_at.isoformat() if expires_at else None, decision)

    @staticmethod
    def _grant_matches(grant: PermissionGrant, request: AgentActionRequest) -> bool:
        return grant.capability == request.capability and grant.target_scope == request.target_scope and grant.device_id == request.device_id

    @contextmanager
    def _vault_access(self):
        try:
            with self._vault_session_manager.access() as vault:
                yield vault
        except VaultLockedError as error:
            raise AgentVaultLockedError("Vault unlock is required for encrypted audit.") from error
