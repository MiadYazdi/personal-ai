from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app
from personal_ai.google_grounding import GoogleGroundingConnector


class GoogleGroundingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.calls = 0

        def fake_transport(*_args):
            self.calls += 1
            return 200, json.dumps(
                {"output_text": "Synthetic grounded API result.", "steps": []}
            ).encode("utf-8")

        connector = GoogleGroundingConnector(
            key_provider=lambda: "synthetic-key",
            transport=fake_transport,
        )
        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            google_grounding_connector=connector,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def payload(self) -> dict[str, str]:
        return {
            "query": "Synthetic grounded API preview only.",
            "model_id": "gemini-3.5-flash",
        }

    def test_locked_preview_never_calls_transport(self) -> None:
        response = self.client.post(
            "/api/v1/online-control/google-grounding-preview",
            json=self.payload(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["policy"]["vault_required"])
        self.assertFalse(response.json()["execution_enabled"])
        self.assertEqual(self.calls, 0)

    def test_unlocked_confirmed_execution_uses_fake_transport_only(self) -> None:
        self.assertEqual(
            self.client.post(
                "/api/v1/onboarding/local-vault",
                json={
                    "profile_name": "Synthetic Grounding Test",
                    "vault_passphrase": "synthetic grounding passphrase",
                    "create_recovery_key": False,
                },
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/vault/unlock",
                json={
                    "method": "passphrase",
                    "passphrase": "synthetic grounding passphrase",
                },
            ).status_code,
            200,
        )

        access = self.client.put(
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
        self.assertEqual(access.status_code, 200)

        preview = self.client.post(
            "/api/v1/online-control/google-grounding-preview",
            json=self.payload(),
        )
        digest = preview.json()["grounding"]["request_sha256"]

        blocked = self.client.post(
            "/api/v1/online-control/google-grounding-execute",
            json={
                **self.payload(),
                "expected_request_sha256": digest,
                "confirmed": False,
            },
        )
        self.assertEqual(blocked.status_code, 422)
        self.assertEqual(self.calls, 0)

        executed = self.client.post(
            "/api/v1/online-control/google-grounding-execute",
            json={
                **self.payload(),
                "expected_request_sha256": digest,
                "confirmed": True,
            },
        )
        self.assertEqual(executed.status_code, 200)
        self.assertEqual(
            executed.json()["result"]["text"],
            "Synthetic grounded API result.",
        )
        self.assertEqual(self.calls, 1)


if __name__ == "__main__":
    unittest.main()
