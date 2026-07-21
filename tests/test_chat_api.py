from __future__ import annotations

import json
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app
from personal_ai.chat import ChatMessage


class FakeRuntime:
    def __init__(self) -> None:
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
        yield "<think>hidden</think>"
        yield "Synthetic streamed reply"

    def close(self) -> None:
        self.closed = True


class ChatApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        temp_root = Path(self.temp_directory.name)
        self.vault_path = temp_root / "vault" / "chat.sqlite3"
        self.preference_path = temp_root / "ui" / "preferences.json"
        self.runtime = FakeRuntime()
        self.app = create_app(
            vault_path=self.vault_path,
            preference_path=self.preference_path,
            chat_runtime=self.runtime,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    @staticmethod
    def _events(response_text: str) -> list[dict[str, str]]:
        return [
            json.loads(line)
            for line in response_text.splitlines()
            if line.strip()
        ]

    def test_quick_streams_final_text_without_thinking(self) -> None:
        response = self.client.post(
            "/api/v1/chat/stream",
            json={
                "mode": "quick",
                "messages": [{"role": "user", "content": "Synthetic hello"}],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"].split(";")[0], "application/x-ndjson")
        events = self._events(response.text)
        visible = "".join(
            event.get("content", "")
            for event in events
            if event["type"] == "delta"
        )
        self.assertEqual(visible, "Synthetic streamed reply")
        self.assertEqual(events[-1], {"type": "done"})
        self.assertIn("/no_think", self.runtime.calls[0][0][0].content)

    def test_invalid_chat_request_is_rejected_before_runtime(self) -> None:
        response = self.client.post(
            "/api/v1/chat/stream",
            json={"mode": "quick", "messages": []},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.runtime.calls, [])

    def test_unlocked_chat_receives_profile_context_without_persistence(self) -> None:
        created = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic Chat User",
                "address_name": "Synthetic Chat Alias",
                "vault_passphrase": "synthetic chat passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(created.status_code, 200)

        unlocked = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": "synthetic chat passphrase",
            },
        )
        self.assertEqual(unlocked.status_code, 200)

        response = self.client.post(
            "/api/v1/chat/stream",
            json={
                "mode": "deep",
                "messages": [{"role": "user", "content": "Synthetic hello"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        prompt = self.runtime.calls[0][0][0].content
        self.assertIn("Synthetic Chat User", prompt)
        self.assertIn("Synthetic Chat Alias", prompt)
        self.assertNotIn("/no_think", prompt)
