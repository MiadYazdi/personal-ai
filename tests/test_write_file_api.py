from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.agent.write_executor import UbuntuWriteFileExecutor
from personal_ai.api.app import create_app


class WriteFileApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.scope = root / "scope"
        self.scope.mkdir()
        self.calls: list[tuple[Path, bytes, int, bool]] = []

        def fake_atomic_writer(target, content, mode, create_only):
            self.calls.append((target, content, mode, create_only))

        executor = UbuntuWriteFileExecutor(
            atomic_writer=fake_atomic_writer,
        )
        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            write_file_executor=executor,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def payload(self) -> dict[str, object]:
        return {
            "selected_scope": str(self.scope),
            "requested_path": "synthetic-created.txt",
            "content": "synthetic write-file API content\n",
        }

    def test_locked_preview_requires_vault_and_never_calls_writer(self) -> None:
        response = self.client.post(
            "/api/v1/device-agent/write-preview",
            json=self.payload(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["policy"]["vault_required"])
        self.assertFalse(response.json()["execution_enabled"])
        self.assertEqual(self.calls, [])

    def test_unlocked_confirmed_execution_uses_fake_writer_only(self) -> None:
        created = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic Write Test",
                "vault_passphrase": "synthetic write test passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(created.status_code, 200)

        unlocked = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": "synthetic write test passphrase",
            },
        )
        self.assertEqual(unlocked.status_code, 200)

        preview = self.client.post(
            "/api/v1/device-agent/write-preview",
            json=self.payload(),
        )
        self.assertEqual(preview.status_code, 200)
        digest = preview.json()["write"]["request_sha256"]

        unconfirmed = self.client.post(
            "/api/v1/device-agent/write",
            json={
                **self.payload(),
                "expected_request_sha256": digest,
                "confirmed": False,
            },
        )
        self.assertEqual(unconfirmed.status_code, 422)
        self.assertEqual(self.calls, [])

        executed = self.client.post(
            "/api/v1/device-agent/write",
            json={
                **self.payload(),
                "expected_request_sha256": digest,
                "confirmed": True,
            },
        )
        self.assertEqual(executed.status_code, 200)
        self.assertTrue(executed.json()["execution_enabled"])
        self.assertEqual(executed.json()["result"]["operation"], "create")
        self.assertEqual(self.calls[0][0].name, "synthetic-created.txt")
        self.assertTrue(self.calls[0][3])


if __name__ == "__main__":
    unittest.main()
