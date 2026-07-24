from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from personal_ai.agent.native_picker import NativePickerMode, UbuntuNativePicker


class NativePickerTests(unittest.TestCase):
    def _picker(self, result, calls):
        def runner(argv, **kwargs):
            calls.append(list(argv))
            return result

        return UbuntuNativePicker(
            dialog_binary=Path(__file__),
            dialog_runner=runner,
            session_available=lambda: True,
        )

    def test_file_selection_returns_fake_path(self) -> None:
        calls = []
        picker = self._picker(
            subprocess.CompletedProcess([], 0, "/tmp/synthetic.txt\n", ""),
            calls,
        )
        result = picker.select(NativePickerMode.OPEN_FILE, title="Synthetic picker")
        self.assertFalse(result.cancelled)
        self.assertEqual(result.path, "/tmp/synthetic.txt")
        self.assertIn("--file-selection", calls[0])

    def test_cancel_and_desktop_filter(self) -> None:
        calls = []
        picker = self._picker(subprocess.CompletedProcess([], 1, "", ""), calls)
        result = picker.select(NativePickerMode.DESKTOP_ENTRY, title="Synthetic picker")
        self.assertTrue(result.cancelled)
        self.assertIsNone(result.path)
        self.assertIn("--file-filter=Desktop entries | *.desktop", calls[0])
