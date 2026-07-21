from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app


class ConversationMemoryApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.vault_path = root / "vault" / "memory-api.sqlite3"
        self.preference_path = root / "ui" / "preferences.json"
        self.app = create_app(
            vault_path=self.vault_path,
            preference_path=self.preference_path,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def _create_and_unlock(self) -> None:
        created = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic Memory User",
                "address_name": "Synthetic Alias",
                "vault_passphrase": "synthetic memory passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(created.status_code, 200)
        unlocked = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": "synthetic memory passphrase",
            },
        )
        self.assertEqual(unlocked.status_code, 200)

    def test_locked_vault_blocks_persistence_api(self) -> None:
        response = self.client.get("/api/v1/conversations")
        self.assertEqual(response.status_code, 423)
        self.assertNotIn("conversation", response.text.lower())

    def test_explicit_conversation_and_memory_lifecycle(self) -> None:
        self._create_and_unlock()

        created = self.client.post(
            "/api/v1/conversations",
            json={"title": "Synthetic saved conversation"},
        )
        self.assertEqual(created.status_code, 200)
        conversation_id = created.json()["conversation_id"]

        user_message = self.client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"role": "user", "content": "Synthetic user content"},
        )
        assistant_message = self.client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"role": "assistant", "content": "Synthetic assistant content"},
        )
        self.assertEqual(user_message.status_code, 200)
        self.assertEqual(assistant_message.status_code, 200)

        listed = self.client.get("/api/v1/conversations")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["conversations"][0]["message_count"], 2)

        detail = self.client.get(f"/api/v1/conversations/{conversation_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.json()["messages"]), 2)

        memory = self.client.post(
            "/api/v1/memories",
            json={"content": "Synthetic explicit memory"},
        )
        self.assertEqual(memory.status_code, 200)
        memory_id = memory.json()["memory_id"]
        self.assertEqual(self.client.get("/api/v1/memories").json()["memories"][0]["memory_id"], memory_id)

        self.assertEqual(self.client.delete(f"/api/v1/memories/{memory_id}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/v1/conversations/{conversation_id}").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/conversations").json()["conversations"], [])

    def test_bulk_delete_requires_unlocked_vault(self) -> None:
        self._create_and_unlock()
        self.client.post("/api/v1/conversations", json={"title": "First"})
        self.client.post("/api/v1/conversations", json={"title": "Second"})
        self.client.post("/api/v1/memories", json={"content": "One"})
        self.client.post("/api/v1/memories", json={"content": "Two"})

        conversations = self.client.delete("/api/v1/conversations")
        memories = self.client.delete("/api/v1/memories")
        self.assertEqual(conversations.json()["deleted_count"], 2)
        self.assertEqual(memories.json()["deleted_count"], 2)


if __name__ == "__main__":
    unittest.main()
