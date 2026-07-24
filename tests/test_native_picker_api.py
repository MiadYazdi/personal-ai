from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.agent.native_picker import UbuntuNativePicker
from personal_ai.api.app import create_app


class NativePickerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.calls = 0

        def runner(*args, **kwargs):
            self.calls += 1
            return subprocess.CompletedProcess([], 0, "/tmp/synthetic.desktop\n", "")

        picker = UbuntuNativePicker(
            dialog_binary=Path(__file__),
            dialog_runner=runner,
            session_available=lambda: True,
        )
        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            native_picker=picker,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp.cleanup()

    def test_picker_api_returns_fake_selection(self) -> None:
        response = self.client.post(
            "/api/v1/device-agent/native-picker",
            json={"mode": "desktop_entry", "title": "Synthetic picker"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["cancelled"])
        self.assertEqual(response.json()["path"], "/tmp/synthetic.desktop")
        self.assertEqual(self.calls, 1)
