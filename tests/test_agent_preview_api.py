from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app


class AgentPreviewApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.vault_path = root / "vault.sqlite3"
        self.preference_path = root / "preferences.json"
        self.app = create_app(vault_path=self.vault_path, preference_path=self.preference_path)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def test_read_only_capability_adapter_never_executes(self) -> None:
        response = self.client.get("/api/v1/device-agent/capabilities")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "preview_only")
        self.assertFalse(response.json()["execution_enabled"])
        self.assertIn("No command execution", response.json()["guarantees"])

    def test_locked_safe_preview_allows_once_with_no_execution(self) -> None:
        response = self.client.post(
            "/api/v1/device-agent/preview",
            json={
                "capability": "read_metadata",
                "target_scope": "synthetic-path",
                "description": "Synthetic metadata preview",
                "preview": "Would read metadata only",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["policy"]["allowed_decisions"], ["once"])
        self.assertFalse(response.json()["execution_enabled"])

    def test_terminal_preview_is_blocked_while_vault_locked(self) -> None:
        response = self.client.post(
            "/api/v1/device-agent/preview",
            json={
                "capability": "run_terminal",
                "target_scope": "synthetic-repository",
                "description": "Synthetic terminal preview",
                "preview": "Would show git status",
                "terminal": {"argv": ["git", "status"], "cwd": "/tmp", "expected_effect": "Show status"},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["policy"]["vault_required"])
        self.assertEqual(response.json()["policy"]["allowed_decisions"], [])
        self.assertFalse(response.json()["execution_enabled"])


if __name__ == "__main__":
    unittest.main()
