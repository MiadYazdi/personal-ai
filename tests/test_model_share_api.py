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
        self, messages: list[ChatMessage], mode: str
    ) -> Iterator[str]:
        self.calls.append((messages, mode))
        yield "<think>hidden</think>Synthetic compact result"

    def close(self) -> None:
        self.closed = True


class ModelShareApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.scope = self.root / "scope"
        self.scope.mkdir()
        self.file = self.scope / "fixture.txt"
        self.content = "Synthetic local model-share text. " * 100
        self.file.write_text(self.content, encoding="utf-8")
        self.runtime = FakeRuntime()
        self.app = create_app(
            vault_path=self.root / "vault.sqlite3",
            preference_path=self.root / "preferences.json",
            chat_runtime=self.runtime,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def test_preview_does_not_call_runtime_and_streams_synthetic_result(self) -> None:
        payload = {
            "selected_scope": str(self.scope),
            "requested_path": str(self.file),
            "content": self.content,
        }
        preview = self.client.post("/api/v1/device-agent/model-share/preview", json=payload)
        self.assertEqual(preview.status_code, 200)
        plan = preview.json()
        self.assertEqual(self.runtime.calls, [])
        self.assertGreater(plan["chunk_count"], 1)
        self.assertFalse(plan["sensitive"])

        stream = self.client.post(
            "/api/v1/device-agent/model-share/stream",
            json={
                **payload,
                "plan_id": plan["plan_id"],
                "operation_id": plan["operation_id"],
                "confirmed": True,
                "mode": "quick",
            },
        )
        self.assertEqual(stream.status_code, 200)
        events = [json.loads(line) for line in stream.text.splitlines() if line]
        self.assertTrue(any(event["type"] == "progress" for event in events))
        self.assertTrue(any(event["type"] == "delta" for event in events))
        self.assertEqual(events[-1], {"type": "done"})
        self.assertGreater(len(self.runtime.calls), 1)
        self.assertEqual(self.app.state.permission_engine.pending_audit_count, 1)

    def test_sensitive_share_requires_fresh_confirmation(self) -> None:
        sensitive_file = self.scope / "secret.txt"
        sensitive_file.write_text("Synthetic sensitive content", encoding="utf-8")
        payload = {
            "selected_scope": str(self.scope),
            "requested_path": str(sensitive_file),
            "content": "Synthetic sensitive content",
        }
        plan = self.client.post("/api/v1/device-agent/model-share/preview", json=payload).json()
        response = self.client.post(
            "/api/v1/device-agent/model-share/stream",
            json={
                **payload,
                "plan_id": plan["plan_id"],
                "operation_id": plan["operation_id"],
                "confirmed": True,
                "mode": "quick",
            },
        )
        events = [json.loads(line) for line in response.text.splitlines() if line]
        self.assertEqual(events[0]["type"], "error")
        self.assertEqual(self.runtime.calls, [])


if __name__ == "__main__":
    unittest.main()
