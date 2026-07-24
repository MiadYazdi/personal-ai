from __future__ import annotations

import stat
import tempfile
import unittest
from pathlib import Path

from personal_ai.internet_access import (
    InternetAccessController,
    InternetAccessError,
)


class InternetAccessControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_directory.name) / "internet-access.json"
        self.controller = InternetAccessController(self.path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_defaults_deny_and_saved_settings_are_private(self) -> None:
        defaults = self.controller.load()
        self.assertFalse(defaults.master_enabled)

        saved = self.controller.update(
            master_enabled=True,
            scopes={
                "google_grounding": True,
                "provider_inference": False,
                "direct_web": False,
                "code_update": False,
            },
        )

        self.assertTrue(saved.master_enabled)
        self.assertTrue(saved.scopes["google_grounding"])
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.controller.require_allowed("google_grounding")

        with self.assertRaises(InternetAccessError):
            self.controller.require_allowed("direct_web")

    def test_unknown_or_invalid_scopes_are_rejected(self) -> None:
        with self.assertRaises(InternetAccessError):
            self.controller.update(
                master_enabled=True,
                scopes={"google_grounding": True},
            )

        with self.assertRaises(InternetAccessError):
            self.controller.require_allowed("unknown_scope")


if __name__ == "__main__":
    unittest.main()
