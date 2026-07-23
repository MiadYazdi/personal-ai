from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.agent.launch_executor import UbuntuApplicationLaunchPreview
from personal_ai.api.app import create_app


class LaunchPreviewApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        apps = root / "applications"
        apps.mkdir()
        (apps / "synthetic.desktop").write_text("[Desktop Entry]\nType=Application\nName=Synthetic App\nExec=synthetic-app\n", encoding="utf-8")
        executor = UbuntuApplicationLaunchPreview(
            desktop_roots=[apps],
            executable_resolver=lambda value: "/usr/bin/synthetic-app" if value == "synthetic-app" else None,
        )
        self.app = create_app(
            vault_path=root / "vault.sqlite3",
            preference_path=root / "preferences.json",
            launch_preview_executor=executor,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.chat_service.close()
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp.cleanup()

    def test_launch_preview_is_exact_and_non_executing(self) -> None:
        response = self.client.post("/api/v1/device-agent/launch-preview", json={"desktop_entry": "synthetic.desktop"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["launch"]["application_name"], "Synthetic App")
        self.assertEqual(response.json()["policy"]["allowed_decisions"], ["once"])
        self.assertFalse(response.json()["execution_enabled"])


if __name__ == "__main__":
    unittest.main()
