from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app


class InternetAccessApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            internet_access_path=root / "internet-access.json",
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def test_defaults_and_user_controlled_update(self) -> None:
        initial = self.client.get("/api/v1/internet-access")
        self.assertEqual(initial.status_code, 200)
        self.assertFalse(initial.json()["master_enabled"])

        updated = self.client.put(
            "/api/v1/internet-access",
            json={
                "master_enabled": True,
                "scopes": {
                    "google_grounding": True,
                    "provider_inference": False,
                    "direct_web": False,
                    "code_update": False,
                },
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertTrue(updated.json()["master_enabled"])
        self.assertTrue(updated.json()["scopes"]["google_grounding"])
        self.assertFalse(updated.json()["network_execution_enabled"])


if __name__ == "__main__":
    unittest.main()
