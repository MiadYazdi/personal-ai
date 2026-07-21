from __future__ import annotations

import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path

from personal_ai.chat import ChatMessage, ChatService
from personal_ai.conversation_memory import ConversationMemoryService
from personal_ai.vault import VaultStore
from personal_ai.vault.session import VaultSessionManager


class FakeRuntime:
    def __init__(self, chunks: list[str]) -> None:
        self.chunks = chunks
        self.calls: list[tuple[list[ChatMessage], str]] = []
        self.closed = False

    @property
    def is_loaded(self) -> bool:
        return False

    def stream_completion(
        self,
        messages: list[ChatMessage],
        mode: str,
    ) -> Iterator[str]:
        self.calls.append((messages, mode))
        yield from self.chunks

    def close(self) -> None:
        self.closed = True


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_directory.name) / "vault.sqlite3"
        self.passphrase = "synthetic chat passphrase"
        self.session = VaultSessionManager(self.vault_path)

        vault = VaultStore.create(self.vault_path, self.passphrase)
        vault.put_record(
            "profile",
            {
                "profile_name": "Synthetic Profile",
                "address_name": "Synthetic Alias",
            },
            record_id="synthetic-profile",
        )
        vault.close()

    def tearDown(self) -> None:
        self.session.close()
        self.temp_directory.cleanup()

    def test_quick_hides_thinking_and_uses_no_think_without_vault_context(self) -> None:
        runtime = FakeRuntime(["<thi", "nk>hidden reasoning</think>Visible answer"])
        service = ChatService(runtime, self.session)

        events = list(
            service.stream_chat(
                [ChatMessage(role="user", content="Synthetic question")],
                "quick",
            )
        )

        visible = "".join(
            event.content for event in events if event.event_type == "delta"
        )
        self.assertEqual(visible, "Visible answer")
        self.assertEqual(events[-1].event_type, "done")

        prompt, mode = runtime.calls[0]
        self.assertEqual(mode, "quick")
        self.assertIn("/no_think", prompt[0].content)
        self.assertNotIn("Synthetic Profile", prompt[0].content)

    def test_unlocked_profile_is_read_only_request_context(self) -> None:
        runtime = FakeRuntime(["Hello"])
        service = ChatService(runtime, self.session)
        self.session.unlock_with_passphrase(self.passphrase)

        events = list(
            service.stream_chat(
                [ChatMessage(role="user", content="Hello")],
                "deep",
            )
        )

        self.assertEqual(events[-1].event_type, "done")
        prompt, mode = runtime.calls[0]
        self.assertEqual(mode, "deep")
        self.assertNotIn("/no_think", prompt[0].content)
        self.assertIn("Synthetic Profile", prompt[0].content)
        self.assertIn("Synthetic Alias", prompt[0].content)


    def test_only_explicit_memory_is_added_when_vault_is_unlocked(self) -> None:
        runtime = FakeRuntime(["Hello"])
        service = ChatService(runtime, self.session)
        self.session.unlock_with_passphrase(self.passphrase)
        ConversationMemoryService(self.session).create_memory("Synthetic selected memory")

        list(service.stream_chat(
            [ChatMessage(role="user", content="Hello")],
            "quick",
        ))

        prompt = runtime.calls[0][0][0].content
        self.assertIn("Synthetic selected memory", prompt)

    def test_invalid_request_does_not_call_runtime(self) -> None:
        runtime = FakeRuntime(["unused"])
        service = ChatService(runtime, self.session)

        with self.assertRaises(ValueError):
            list(service.stream_chat([], "quick"))

        self.assertEqual(runtime.calls, [])
