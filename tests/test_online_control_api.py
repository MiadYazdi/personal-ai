from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app
from personal_ai.online_control import OnlineControlPlanner


class OnlineControlApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            online_control_planner=OnlineControlPlanner(root),
        )
        self.client = TestClient(self.app)
        self.root = root

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def test_status_and_egress_preview_remain_offline(self) -> None:
        status = self.client.get("/api/v1/online-control/status")
        self.assertEqual(status.status_code, 200)
        self.assertFalse(status.json()["online_default_enabled"])
        self.assertFalse(status.json()["automatic_code_apply"])

        preview = self.client.post(
            "/api/v1/online-control/egress-preview",
            json={
                "provider_id": "future-provider",
                "model_id": "future-model",
                "action": "online_chat",
                "outbound_summary": "Synthetic preview only.",
                "data_categories": ["synthetic_text"],
                "estimated_bytes": 32,
            },
        )
        self.assertEqual(preview.status_code, 200)
        self.assertFalse(preview.json()["execution_enabled"])
        self.assertTrue(preview.json()["policy"]["vault_required"])
        self.assertFalse(
            preview.json()["egress"]["network_execution_enabled"]
        )

    def test_evolution_preview_never_applies_a_patch(self) -> None:
        response = self.client.post(
            "/api/v1/online-control/evolution-preview",
            json={
                "repository_scope": str(self.root),
                "proposal_summary": "Synthetic proposal only.",
                "proposed_diff": (
                    "diff --git a/src/example.py b/src/example.py\n"
                    "--- a/src/example.py\n"
                    "+++ b/src/example.py\n"
                    "@@ -1 +1 @@\n"
                    "-old\n"
                    "+new\n"
                ),
                "validation_plan": ["Run synthetic tests", "Review diff"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["execution_enabled"])
        self.assertTrue(response.json()["evolution"]["proposal_only"])
        self.assertFalse(response.json()["evolution"]["apply_enabled"])


if __name__ == "__main__":
    unittest.main()
