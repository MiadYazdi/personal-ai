from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app
from personal_ai.provider_registry import ProviderRegistry


class ProviderRegistryApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            provider_registry=ProviderRegistry(),
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def test_provider_list_and_access_preview_remain_offline(self) -> None:
        listing = self.client.get("/api/v1/online-control/providers")
        self.assertEqual(listing.status_code, 200)
        self.assertFalse(listing.json()["network_execution_enabled"])
        self.assertGreaterEqual(len(listing.json()["providers"]), 6)

        preview = self.client.post(
            "/api/v1/online-control/provider-access-preview",
            json={
                "provider_id": "google_gemini",
                "capability": "google_search_grounding",
                "target_description": "Google Search Grounding",
                "outbound_summary": "Synthetic provider preview only.",
                "data_categories": ["synthetic_text"],
                "estimated_bytes": 64,
            },
        )
        self.assertEqual(preview.status_code, 200)
        self.assertFalse(preview.json()["execution_enabled"])
        self.assertTrue(preview.json()["policy"]["vault_required"])
        self.assertFalse(
            preview.json()["access"]["network_execution_enabled"]
        )


if __name__ == "__main__":
    unittest.main()
