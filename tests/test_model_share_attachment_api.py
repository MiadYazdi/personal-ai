from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app
from personal_ai.conversation_memory import (
    CONVERSATION_ATTACHMENT_CHUNK_TYPE,
    CONVERSATION_ATTACHMENT_TYPE,
)


class ModelShareAttachmentApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.vault_path = root / "vault" / "attachments.sqlite3"
        self.preference_path = root / "ui" / "preferences.json"
        self.app = create_app(vault_path=self.vault_path, preference_path=self.preference_path)
        self.client = TestClient(self.app)
        created = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic Attachment User",
                "address_name": "Synthetic Alias",
                "vault_passphrase": "synthetic attachment passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(created.status_code, 200)
        unlocked = self.client.post(
            "/api/v1/vault/unlock",
            json={"method": "passphrase", "passphrase": "synthetic attachment passphrase"},
        )
        self.assertEqual(unlocked.status_code, 200)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def test_chunked_model_share_attachment_round_trips_and_deletes(self) -> None:
        conversation = self.client.post(
            "/api/v1/conversations", json={"title": "Synthetic attachment"}
        ).json()
        content = "Synthetic model-share text. " * 700
        payload = {
            "canonical_path": "/synthetic/fixture.txt",
            "content": content,
            "size_bytes": len(content.encode("utf-8")),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "sensitive": False,
        }
        saved = self.client.post(
            f"/api/v1/conversations/{conversation['conversation_id']}/model-shares",
            json=payload,
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["kind"], "model_share")
        self.assertEqual(saved.json()["content"], content)
        self.assertGreater(saved.json()["model_share"]["chunk_count"], 1)

        loaded = self.client.get(
            f"/api/v1/conversations/{conversation['conversation_id']}"
        ).json()["messages"]
        self.assertEqual(loaded[0]["content"], content)
        self.assertEqual(loaded[0]["kind"], "model_share")
        self.assertNotIn(content.encode("utf-8"), self.vault_path.read_bytes())

        deleted = self.client.delete(
            f"/api/v1/conversations/{conversation['conversation_id']}"
        )
        self.assertEqual(deleted.status_code, 200)
        with self.app.state.vault_session_manager.access() as vault:
            self.assertEqual(vault.find_records_by_type(CONVERSATION_ATTACHMENT_TYPE), [])
            self.assertEqual(vault.find_records_by_type(CONVERSATION_ATTACHMENT_CHUNK_TYPE), [])

    def test_model_share_attachment_requires_unlocked_vault(self) -> None:
        self.client.post("/api/v1/vault/lock")
        response = self.client.post(
            "/api/v1/conversations/not-used/model-shares",
            json={
                "canonical_path": "/synthetic/fixture.txt",
                "content": "Synthetic",
                "size_bytes": 9,
                "sha256": hashlib.sha256(b"Synthetic").hexdigest(),
                "sensitive": False,
            },
        )
        self.assertEqual(response.status_code, 423)


if __name__ == "__main__":
    unittest.main()
