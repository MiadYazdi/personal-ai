from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.agent.terminal_executor import (
    TerminalRunResult,
    UbuntuStructuredTerminalExecutor,
)
from personal_ai.api.app import create_app


class TerminalExecuteApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.calls = 0

        def fake_runner(argv, cwd, timeout_seconds):
            self.calls += 1
            return TerminalRunResult(
                exit_code=0,
                stdout=b"synthetic terminal result",
                stderr=b"",
                timed_out=False,
                duration_ms=5,
            )

        executor = UbuntuStructuredTerminalExecutor(
            executable_resolver=lambda value: (
                "/usr/bin/synthetic" if value == "synthetic" else None
            ),
            runner=fake_runner,
        )

        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            terminal_executor=executor,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    @staticmethod
    def request_payload() -> dict[str, object]:
        return {
            "argv": ["synthetic", "--safe"],
            "cwd": "/tmp",
            "expected_effect": "Synthetic terminal verification only",
            "timeout_seconds": 30,
        }

    def test_locked_preview_and_execution_never_run_fake_runner(self) -> None:
        preview = self.client.post(
            "/api/v1/device-agent/terminal-preview",
            json=self.request_payload(),
        )
        self.assertEqual(preview.status_code, 200)
        self.assertTrue(preview.json()["policy"]["vault_required"])
        self.assertFalse(preview.json()["execution_enabled"])
        self.assertEqual(self.calls, 0)

        blocked = self.client.post(
            "/api/v1/device-agent/terminal-execute",
            json={
                **self.request_payload(),
                "expected_request_sha256": "synthetic-mismatch",
                "confirmed": True,
            },
        )
        self.assertEqual(blocked.status_code, 422)
        self.assertEqual(self.calls, 0)

    def test_unlocked_confirmed_execution_uses_only_fake_runner(self) -> None:
        created = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic Terminal Test",
                "vault_passphrase": "synthetic terminal test passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(created.status_code, 200)

        unlocked = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": "synthetic terminal test passphrase",
            },
        )
        self.assertEqual(unlocked.status_code, 200)

        preview = self.client.post(
            "/api/v1/device-agent/terminal-preview",
            json=self.request_payload(),
        )
        self.assertEqual(preview.status_code, 200)
        digest = preview.json()["terminal"]["request_sha256"]

        unconfirmed = self.client.post(
            "/api/v1/device-agent/terminal-execute",
            json={
                **self.request_payload(),
                "expected_request_sha256": digest,
                "confirmed": False,
            },
        )
        self.assertEqual(unconfirmed.status_code, 422)
        self.assertEqual(self.calls, 0)

        executed = self.client.post(
            "/api/v1/device-agent/terminal-execute",
            json={
                **self.request_payload(),
                "expected_request_sha256": digest,
                "confirmed": True,
            },
        )
        self.assertEqual(executed.status_code, 200)
        self.assertTrue(executed.json()["execution_enabled"])
        self.assertEqual(
            executed.json()["result"]["stdout"],
            "synthetic terminal result",
        )
        self.assertFalse(executed.json()["authorization"]["pending_audit"])
        self.assertEqual(self.calls, 1)


if __name__ == "__main__":
    unittest.main()
