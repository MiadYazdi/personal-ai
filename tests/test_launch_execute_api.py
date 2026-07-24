from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.agent.launch_executor import UbuntuApplicationLaunchPreview
from personal_ai.api.app import create_app


class FakeProcess:
    pid = 5252


class LaunchExecuteApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        apps = root / "applications"
        apps.mkdir()
        (apps / "synthetic.desktop").write_text("[Desktop Entry]\nType=Application\nName=Synthetic\nExec=synthetic-app\n", encoding="utf-8")
        self.calls = 0
        def fake_popen(*args, **kwargs):
            self.calls += 1
            return FakeProcess()
        executor = UbuntuApplicationLaunchPreview(
            desktop_roots=[apps],
            executable_resolver=lambda value: "/usr/bin/synthetic-app" if value == "synthetic-app" else None,
            popen_factory=fake_popen,
        )
        self.app = create_app(vault_path=root / "vault.sqlite3", preference_path=root / "preferences.json", launch_preview_executor=executor)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp.cleanup()

    def test_confirmed_launch_uses_once_policy_and_fake_process(self) -> None:
        preview = self.client.post("/api/v1/device-agent/launch-preview", json={"desktop_entry": "synthetic.desktop"}).json()
        response = self.client.post("/api/v1/device-agent/launch-execute", json={
            "desktop_entry": "synthetic.desktop",
            "expected_desktop_sha256": preview["launch"]["desktop_sha256"],
            "confirmed": True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["execution"]["started"])
        self.assertEqual(response.json()["execution"]["pid"], 5252)
        self.assertTrue(response.json()["authorization"]["pending_audit"])
        self.assertEqual(self.calls, 1)

    def test_unconfirmed_launch_never_starts_process(self) -> None:
        response = self.client.post("/api/v1/device-agent/launch-execute", json={
            "desktop_entry": "synthetic.desktop", "expected_desktop_sha256": "unused", "confirmed": False,
        })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.calls, 0)


if __name__ == "__main__":
    unittest.main()
