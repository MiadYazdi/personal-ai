from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personal_ai.conversation_memory import (
    ConversationMemoryLockedError,
    ConversationMemoryService,
)
from personal_ai.vault import VaultStore
from personal_ai.vault.session import VaultSessionManager


class ConversationMemoryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_directory.name) / "memory.sqlite3"
        self.passphrase = "synthetic memory passphrase"
        vault = VaultStore.create(self.vault_path, self.passphrase)
        vault.close()
        self.session = VaultSessionManager(self.vault_path)
        self.service = ConversationMemoryService(self.session)

    def tearDown(self) -> None:
        self.session.close()
        self.temp_directory.cleanup()

    def test_locked_vault_rejects_persistence(self) -> None:
        with self.assertRaises(ConversationMemoryLockedError):
            self.service.create_conversation("Synthetic conversation")

    def test_conversation_and_memory_are_encrypted_and_deletable(self) -> None:
        self.session.unlock_with_passphrase(self.passphrase)
        conversation = self.service.create_conversation("Synthetic conversation")
        first = self.service.append_message(conversation.conversation_id, "user", "Synthetic private message")
        second = self.service.append_message(conversation.conversation_id, "assistant", "Synthetic private response")

        summaries = self.service.list_conversations()
        self.assertEqual(summaries[0].message_count, 2)
        loaded, messages = self.service.get_conversation(conversation.conversation_id)
        self.assertEqual(loaded.title, "Synthetic conversation")
        self.assertEqual([message.message_id for message in messages], [first.message_id, second.message_id])

        memory = self.service.create_memory("Synthetic selected memory")
        self.assertEqual(self.service.list_memories()[0].memory_id, memory.memory_id)

        raw = self.vault_path.read_bytes()
        self.assertNotIn(b"Synthetic conversation", raw)
        self.assertNotIn(b"Synthetic private message", raw)
        self.assertNotIn(b"Synthetic selected memory", raw)

        self.service.delete_memory(memory.memory_id)
        self.assertEqual(self.service.list_memories(), [])
        self.service.delete_conversation(conversation.conversation_id)
        self.assertEqual(self.service.list_conversations(), [])

    def test_bulk_delete_removes_only_explicitly_saved_records(self) -> None:
        self.session.unlock_with_passphrase(self.passphrase)
        first = self.service.create_conversation("First")
        second = self.service.create_conversation("Second")
        self.service.append_message(first.conversation_id, "user", "One")
        self.service.append_message(second.conversation_id, "user", "Two")
        self.service.create_memory("Memory one")
        self.service.create_memory("Memory two")

        self.assertEqual(self.service.delete_all_conversations(), 2)
        self.assertEqual(self.service.delete_all_memories(), 2)
        self.assertEqual(self.service.list_conversations(), [])
        self.assertEqual(self.service.list_memories(), [])
