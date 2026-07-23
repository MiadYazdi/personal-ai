from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personal_ai.agent.launch_executor import LaunchPreviewError, UbuntuApplicationLaunchPreview


class LaunchPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "applications"
        self.root.mkdir()
        self.entry = self.root / "synthetic.desktop"
        self.entry.write_text("[Desktop Entry]\nType=Application\nName=Synthetic App\nExec=synthetic-app --safe\n", encoding="utf-8")
        self.executor = UbuntuApplicationLaunchPreview(
            desktop_roots=[self.root],
            executable_resolver=lambda value: "/usr/bin/synthetic-app" if value == "synthetic-app" else None,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_exact_desktop_entry_preview_never_launches(self) -> None:
        preview = self.executor.preview("synthetic.desktop")
        self.assertEqual(preview.application_name, "Synthetic App")
        self.assertEqual(preview.argv, ("synthetic-app", "--safe"))
        self.assertEqual(preview.executable_path, "/usr/bin/synthetic-app")
        self.assertEqual(len(preview.desktop_sha256), 64)

    def test_placeholders_and_outside_paths_are_rejected(self) -> None:
        self.entry.write_text("[Desktop Entry]\nType=Application\nName=Unsafe\nExec=synthetic-app %U\n", encoding="utf-8")
        with self.assertRaises(LaunchPreviewError):
            self.executor.preview("synthetic.desktop")
        with self.assertRaises(LaunchPreviewError):
            self.executor.preview("../outside.desktop")


if __name__ == "__main__":
    unittest.main()
