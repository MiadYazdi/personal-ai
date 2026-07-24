from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personal_ai.agent.launch_executor import LaunchExecutionError, UbuntuApplicationLaunchPreview


class FakeProcess:
    pid = 4242


class LaunchExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name) / "applications"
        root.mkdir()
        (root / "synthetic.desktop").write_text("[Desktop Entry]\nType=Application\nName=Synthetic\nExec=synthetic-app --safe\n", encoding="utf-8")
        self.calls: list[tuple[tuple[str, ...], dict[str, object]]] = []
        def fake_popen(argv, **kwargs):
            self.calls.append((tuple(argv), kwargs))
            return FakeProcess()
        self.executor = UbuntuApplicationLaunchPreview(
            desktop_roots=[root],
            executable_resolver=lambda value: "/usr/bin/synthetic-app" if value == "synthetic-app" else None,
            popen_factory=fake_popen,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_launch_uses_resolved_executable_without_shell(self) -> None:
        preview = self.executor.preview("synthetic.desktop")
        result = self.executor.launch(preview, expected_desktop_sha256=preview.desktop_sha256)
        self.assertEqual(result.pid, 4242)
        self.assertEqual(self.calls[0][0], ("/usr/bin/synthetic-app", "--safe"))
        self.assertEqual(self.calls[0][1]["cwd"], "/")
        self.assertTrue(self.calls[0][1]["start_new_session"])

    def test_digest_change_rejects_before_popen(self) -> None:
        preview = self.executor.preview("synthetic.desktop")
        with self.assertRaises(LaunchExecutionError):
            self.executor.launch(preview, expected_desktop_sha256="wrong")
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
