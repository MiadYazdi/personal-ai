from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

MAX_SUMMARY_CHARS = 4_000
MAX_ESTIMATED_BYTES = 16 * 1024 * 1024
MAX_PROPOSAL_DIFF_BYTES = 256 * 1024
MAX_VALIDATION_STEPS = 8
MAX_TOUCHED_FILES = 64
ALLOWED_ONLINE_ACTIONS = {
    "online_chat",
    "web_search",
    "model_update",
    "source_update",
}


class OnlineControlError(ValueError):
    """Raised when an online or controlled-evolution preview is invalid."""


@dataclass(frozen=True)
class OnlineEgressPreview:
    provider_id: str
    model_id: str
    action: str
    destination: str
    outbound_summary: str
    data_categories: tuple[str, ...]
    estimated_bytes: int
    request_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "action": self.action,
            "destination": self.destination,
            "outbound_summary": self.outbound_summary,
            "data_categories": list(self.data_categories),
            "estimated_bytes": self.estimated_bytes,
            "request_sha256": self.request_sha256,
            "network_default_enabled": False,
            "network_execution_enabled": False,
            "requires_fresh_confirmation": True,
            "requires_vault_unlock": True,
        }


@dataclass(frozen=True)
class ControlledEvolutionPreview:
    canonical_repository_scope: str
    proposal_summary: str
    proposal_sha256: str
    diff_sha256: str
    diff_bytes: int
    touched_files: tuple[str, ...]
    validation_plan: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_repository_scope": self.canonical_repository_scope,
            "proposal_summary": self.proposal_summary,
            "proposal_sha256": self.proposal_sha256,
            "diff_sha256": self.diff_sha256,
            "diff_bytes": self.diff_bytes,
            "touched_files": list(self.touched_files),
            "validation_plan": list(self.validation_plan),
            "proposal_only": True,
            "apply_enabled": False,
            "requires_human_review": True,
            "requires_fresh_confirmation": True,
        }


class OnlineControlPlanner:
    """Local-only online and self-improvement planning; it never connects or writes."""

    def __init__(self, project_root: str | Path) -> None:
        self._project_root = Path(project_root).expanduser().resolve(strict=True)

    def status(self) -> dict[str, object]:
        return {
            "online_default_enabled": False,
            "network_execution_enabled": False,
            "configured_providers": [],
            "credential_storage": "not_configured",
            "controlled_evolution": "proposal_only",
            "automatic_code_apply": False,
            "guardrails": [
                "No network action without fresh user confirmation",
                "No credential is stored or entered by the Agent",
                "No source patch applies without human diff review",
                "No code update runs without explicit test and execution approval",
            ],
        }

    def preview_egress(
        self,
        *,
        provider_id: str,
        model_id: str,
        action: str,
        outbound_summary: str,
        data_categories: list[str],
        estimated_bytes: int,
    ) -> OnlineEgressPreview:
        provider = self._validate_identifier(provider_id, "Provider identifier")
        model = self._validate_identifier(model_id, "Model identifier")

        if action not in ALLOWED_ONLINE_ACTIONS:
            raise OnlineControlError("Unsupported online action.")

        summary = self._validate_summary(outbound_summary, "Outbound summary")

        if (
            not isinstance(estimated_bytes, int)
            or estimated_bytes < 0
            or estimated_bytes > MAX_ESTIMATED_BYTES
        ):
            raise OnlineControlError("Estimated outbound size is invalid.")

        categories = tuple(
            item.strip().lower()
            for item in data_categories
            if isinstance(item, str) and item.strip()
        )
        if len(categories) > 12 or len(set(categories)) != len(categories):
            raise OnlineControlError("Data categories are invalid.")

        payload = {
            "provider_id": provider,
            "model_id": model,
            "action": action,
            "outbound_summary": summary,
            "data_categories": categories,
            "estimated_bytes": estimated_bytes,
        }
        digest = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return OnlineEgressPreview(
            provider_id=provider,
            model_id=model,
            action=action,
            destination=f"{provider}:{model}",
            outbound_summary=summary,
            data_categories=categories,
            estimated_bytes=estimated_bytes,
            request_sha256=digest,
        )

    def preview_evolution(
        self,
        *,
        repository_scope: str | Path,
        proposal_summary: str,
        proposed_diff: str,
        validation_plan: list[str],
    ) -> ControlledEvolutionPreview:
        try:
            scope = Path(repository_scope).expanduser().resolve(strict=True)
        except OSError as error:
            raise OnlineControlError("Repository scope is unavailable.") from error

        if scope != self._project_root:
            raise OnlineControlError(
                "Controlled evolution is limited to the active project root."
            )

        summary = self._validate_summary(proposal_summary, "Proposal summary")

        if not isinstance(proposed_diff, str) or not proposed_diff.strip():
            raise OnlineControlError("A proposed source diff is required.")

        try:
            diff_bytes = proposed_diff.encode("utf-8")
        except UnicodeEncodeError as error:
            raise OnlineControlError("Proposed diff is not valid UTF-8.") from error

        if b"\x00" in diff_bytes or len(diff_bytes) > MAX_PROPOSAL_DIFF_BYTES:
            raise OnlineControlError("Proposed diff exceeds the v1 safety limit.")

        steps = tuple(
            item.strip()
            for item in validation_plan
            if isinstance(item, str) and item.strip()
        )
        if not steps or len(steps) > MAX_VALIDATION_STEPS:
            raise OnlineControlError("A bounded validation plan is required.")
        if any("\n" in item or "\r" in item or len(item) > 240 for item in steps):
            raise OnlineControlError("Validation plan is invalid.")

        touched_files: list[str] = []
        for line in proposed_diff.splitlines():
            if not line.startswith("+++ b/"):
                continue
            value = line.removeprefix("+++ b/").strip()
            candidate = Path(value)
            if (
                not value
                or candidate.is_absolute()
                or ".." in candidate.parts
                or value.startswith(".git/")
            ):
                raise OnlineControlError("Proposed diff contains an unsafe path.")
            if value not in touched_files:
                touched_files.append(value)

        if not touched_files or len(touched_files) > MAX_TOUCHED_FILES:
            raise OnlineControlError(
                "Proposed diff must declare a bounded set of touched files."
            )

        diff_sha256 = hashlib.sha256(diff_bytes).hexdigest()
        proposal_payload = {
            "repository_scope": str(scope),
            "proposal_summary": summary,
            "diff_sha256": diff_sha256,
            "validation_plan": steps,
        }
        proposal_sha256 = hashlib.sha256(
            json.dumps(
                proposal_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return ControlledEvolutionPreview(
            canonical_repository_scope=str(scope),
            proposal_summary=summary,
            proposal_sha256=proposal_sha256,
            diff_sha256=diff_sha256,
            diff_bytes=len(diff_bytes),
            touched_files=tuple(touched_files),
            validation_plan=steps,
        )

    @staticmethod
    def _validate_identifier(value: str, label: str) -> str:
        if (
            not isinstance(value, str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", value)
        ):
            raise OnlineControlError(f"{label} is invalid.")
        return value

    @staticmethod
    def _validate_summary(value: str, label: str) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > MAX_SUMMARY_CHARS
        ):
            raise OnlineControlError(f"{label} is invalid.")
        return value.strip()
