from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from personal_ai.agent import (
    AgentActionRequest,
    AgentCapability,
    AgentPermissionDeniedError,
    AgentVaultLockedError,
    GrantDecision,
    PermissionEngine,
    TerminalPreview,
)
from personal_ai.vault import VaultStore
from personal_ai.vault.session import VaultSessionManager


class PermissionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_directory.name) / "agent.sqlite3"
        self.passphrase = "synthetic agent passphrase"
        vault = VaultStore.create(self.vault_path, self.passphrase)
        vault.close()
        self.session = VaultSessionManager(self.vault_path)
        self.engine = PermissionEngine(self.session)

    def tearDown(self) -> None:
        self.session.close()
        self.temp_directory.cleanup()

    def _request(self, capability: AgentCapability, terminal: TerminalPreview | None = None) -> AgentActionRequest:
        return AgentActionRequest.create(
            capability=capability,
            target_scope="synthetic-scope",
            device_id="synthetic-ubuntu-device",
            description="Synthetic permission preview",
            preview="Synthetic operation only",
            terminal=terminal,
        )

    def test_locked_safe_once_creates_volatile_pending_audit(self) -> None:
        request = self._request(AgentCapability.READ_METADATA)
        authorization = self.engine.approve(request, GrantDecision.ONCE)
        self.assertTrue(authorization.pending_audit)
        self.assertEqual(self.engine.pending_audit_count, 1)

        self.session.unlock_with_passphrase(self.passphrase)
        self.assertEqual(self.engine.seal_pending_audits(), 1)
        with self.session.access() as vault:
            self.assertEqual(len(vault.find_records_by_type("device_agent_audit")), 1)

    def test_high_risk_actions_require_unlock_and_once_only(self) -> None:
        request = self._request(AgentCapability.WRITE_FILE)
        with self.assertRaises(AgentVaultLockedError):
            self.engine.allowed_decisions(request)

        self.session.unlock_with_passphrase(self.passphrase)
        self.assertEqual(self.engine.allowed_decisions(request), (GrantDecision.ONCE,))
        with self.assertRaises(AgentPermissionDeniedError):
            self.engine.approve(request, GrantDecision.SESSION)

    def test_terminal_requires_exact_non_shell_one_time_preview(self) -> None:
        self.session.unlock_with_passphrase(self.passphrase)
        request = self._request(
            AgentCapability.RUN_TERMINAL,
            TerminalPreview(("git", "status"), "/tmp", "Show repository status"),
        )
        self.assertEqual(self.engine.allowed_decisions(request), (GrantDecision.ONCE,))
        self.assertFalse(self.engine.approve(request, GrantDecision.ONCE).pending_audit)

        unsafe = self._request(
            AgentCapability.RUN_TERMINAL,
            TerminalPreview(("bash", "-c", "echo unsafe"), "/tmp", "Run shell"),
        )
        with self.assertRaises(AgentPermissionDeniedError):
            self.engine.allowed_decisions(unsafe)

    def test_safe_session_and_scoped_grants_are_bound_to_scope_and_device(self) -> None:
        self.session.unlock_with_passphrase(self.passphrase)
        request = self._request(AgentCapability.LAUNCH_APP)
        self.engine.approve(request, GrantDecision.SESSION)
        self.assertTrue(self.engine.is_session_granted(request))

        scoped = self._request(AgentCapability.READ_TEXT)
        authorization = self.engine.approve(
            scoped,
            GrantDecision.SCOPED,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        self.assertIsNotNone(authorization.grant_id)
        with self.session.access() as vault:
            self.assertEqual(len(vault.find_records_by_type("device_agent_grant")), 1)


if __name__ == "__main__":
    unittest.main()
