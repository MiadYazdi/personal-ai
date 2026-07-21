from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from personal_ai.ui_preferences import (
    UI_PREFERENCES_SCHEMA_VERSION,
    UiPreferenceStore,
    UiPreferenceValidationError,
    UiPreferences,
)


class UiPreferenceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.path = (
            Path(self.temp_directory.name)
            / "preferences"
            / "ui-preferences.json"
        )
        self.store = UiPreferenceStore(self.path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_missing_file_returns_v4_defaults(self) -> None:
        preferences = self.store.load()

        self.assertEqual(
            preferences.schema_version,
            UI_PREFERENCES_SCHEMA_VERSION,
        )
        self.assertEqual(preferences.language, "fa")
        self.assertEqual(preferences.sidebar_placement, "left")
        self.assertEqual(preferences.sidebar_mode, "expanded")
        self.assertEqual(preferences.mobile_sidebar_mode, "compact")
        self.assertEqual(preferences.controls_location, "sidebar_settings")

    def test_v1_file_migrates_to_v4(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "theme": "dark",
                    "accent_color": "violet",
                    "sidebar_mode": "compact",
                    "selected_preset": "custom",
                    "widget_order": ["model", "vault", "agent", "online"],
                    "hidden_widgets": ["online"],
                }
            ),
            encoding="utf-8",
        )

        migrated = self.store.load()

        self.assertEqual(
            migrated.schema_version,
            UI_PREFERENCES_SCHEMA_VERSION,
        )
        self.assertEqual(migrated.theme, "dark")
        self.assertEqual(migrated.sidebar_mode, "compact")
        self.assertEqual(migrated.mobile_sidebar_mode, "compact")
        self.assertEqual(migrated.controls_location, "sidebar_settings")

    def test_v2_file_migrates_to_v4(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.path.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "language": "tr",
                    "theme": "light",
                    "accent_color": "#22c55e",
                    "sidebar_placement": "right",
                    "sidebar_mode": "expanded",
                    "sidebar_width": "wide",
                    "font_scale": "large",
                    "ui_density": "compact",
                    "motion": "reduced",
                    "controls_location": "header",
                    "selected_preset": "custom",
                    "widget_order": ["online", "model", "vault", "agent"],
                    "hidden_widgets": ["agent"],
                }
            ),
            encoding="utf-8",
        )

        migrated = self.store.load()

        self.assertEqual(migrated.language, "tr")
        self.assertEqual(migrated.sidebar_placement, "right")
        self.assertEqual(migrated.sidebar_width, "wide")
        self.assertEqual(migrated.mobile_sidebar_mode, "compact")
        self.assertEqual(migrated.controls_location, "header")

    def test_v3_mobile_behavior_maps_to_v4_mode(self) -> None:
        mappings = {
            "follow_desktop": "compact",
            "compact_rail": "compact",
            "drawer": "expanded",
        }

        for old_behavior, expected_mode in mappings.items():
            with self.subTest(old_behavior=old_behavior):
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(
                    json.dumps(
                        {
                            "schema_version": 3,
                            "language": "en",
                            "theme": "system",
                            "accent_color": "cyan",
                            "sidebar_placement": "left",
                            "sidebar_mode": "compact",
                            "sidebar_width": "normal",
                            "mobile_sidebar_behavior": old_behavior,
                            "font_scale": "default",
                            "ui_density": "comfortable",
                            "motion": "system",
                            "controls_location": "both",
                            "selected_preset": "default",
                            "widget_order": [
                                "vault",
                                "model",
                                "agent",
                                "online",
                            ],
                            "hidden_widgets": [],
                        }
                    ),
                    encoding="utf-8",
                )

                migrated = self.store.load()
                self.assertEqual(
                    migrated.mobile_sidebar_mode,
                    expected_mode,
                )

    def test_atomic_save_and_load_v4_preferences(self) -> None:
        preferences = UiPreferences.from_mapping(
            {
                "language": "ar",
                "theme": "dark",
                "accent_color": "#22c55e",
                "sidebar_placement": "right",
                "sidebar_mode": "compact",
                "sidebar_width": "wide",
                "mobile_sidebar_mode": "expanded",
                "font_scale": "large",
                "ui_density": "compact",
                "motion": "reduced",
                "controls_location": "both",
                "selected_preset": "custom",
                "widget_order": ["model", "vault", "online", "agent"],
                "hidden_widgets": ["online"],
            }
        )

        self.store.save(preferences)
        loaded = self.store.load()

        self.assertEqual(loaded, preferences)

        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["schema_version"], 5)
        self.assertEqual(saved["mobile_sidebar_mode"], "expanded")

    def test_v4_app_menu_migrates_to_sidebar_settings(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.path.write_text(
            json.dumps(
                {
                    "schema_version": 4,
                    "language": "en",
                    "theme": "system",
                    "accent_color": "cyan",
                    "sidebar_placement": "left",
                    "sidebar_mode": "compact",
                    "sidebar_width": "normal",
                    "mobile_sidebar_mode": "compact",
                    "font_scale": "default",
                    "ui_density": "comfortable",
                    "motion": "system",
                    "controls_location": "app_menu",
                    "selected_preset": "default",
                    "widget_order": [
                        "vault",
                        "model",
                        "agent",
                        "online",
                    ],
                    "hidden_widgets": [],
                }
            ),
            encoding="utf-8",
        )

        migrated = self.store.load()

        self.assertEqual(
            migrated.controls_location,
            "sidebar_settings",
        )


    def test_invalid_v4_values_are_rejected(self) -> None:
        invalid_examples = [
            {"language": "unsupported"},
            {"sidebar_placement": "top"},
            {"sidebar_mode": "floating"},
            {"sidebar_width": "huge"},
            {"mobile_sidebar_mode": "drawer"},
            {"font_scale": "tiny"},
            {"ui_density": "spacious"},
            {"motion": "fast"},
            {"controls_location": "unknown"},
            {"accent_color": "not-a-valid-color"},
        ]

        for invalid_data in invalid_examples:
            with self.subTest(invalid_data=invalid_data):
                with self.assertRaises(UiPreferenceValidationError):
                    UiPreferences.from_mapping(invalid_data)

    def test_invalid_widget_order_is_rejected(self) -> None:
        with self.assertRaises(UiPreferenceValidationError):
            UiPreferences.from_mapping(
                {
                    "widget_order": ["vault", "model", "agent", "agent"],
                }
            )

    @unittest.skipUnless(os.name == "posix", "POSIX permission test")
    def test_posix_permissions(self) -> None:
        self.store.save(UiPreferences())

        directory_mode = self.path.parent.stat().st_mode & 0o777
        file_mode = self.path.stat().st_mode & 0o777

        self.assertEqual(directory_mode, 0o700)
        self.assertEqual(file_mode, 0o600)


if __name__ == "__main__":
    unittest.main()
