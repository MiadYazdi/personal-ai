from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app


class ReadOnlyExecutorApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.scope = self.root / "scope"
        self.scope.mkdir()
        self.file = self.scope / "fixture.txt"
        self.file.write_text("Synthetic API text", encoding="utf-8")
        self.app = create_app(
            vault_path=self.root / "vault.sqlite3",
            preference_path=self.root / "preferences.json",
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def test_preview_and_confirmed_metadata_read_without_execution(self) -> None:
        payload = {
            "selected_scope": str(self.scope),
            "requested_path": str(self.file),
            "mode": "read_metadata",
        }
        preview = self.client.post("/api/v1/device-agent/read-preview", json=payload)
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json()["mode"], "read_metadata")

        denied = self.client.post("/api/v1/device-agent/read", json=payload)
        self.assertEqual(denied.status_code, 422)

        result = self.client.post(
            "/api/v1/device-agent/read",
            json={**payload, "confirmed": True},
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["metadata"]["file_type"], "regular_file")
        self.assertTrue(result.json()["authorization"]["pending_audit"])

    def test_text_read_respects_scope_and_returns_synthetic_content_only(self) -> None:
        result = self.client.post(
            "/api/v1/device-agent/read",
            json={
                "selected_scope": str(self.scope),
                "requested_path": str(self.file),
                "mode": "read_text",
                "confirmed": True,
            },
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["content"], "Synthetic API text")
        self.assertFalse(result.json()["share_with_model"])


if __name__ == "__main__":
    unittest.main()
