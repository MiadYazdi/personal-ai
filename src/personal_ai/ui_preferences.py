from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


UI_PREFERENCES_SCHEMA_VERSION = 5

WIDGET_IDS = ("vault", "model", "agent", "online")

ALLOWED_LANGUAGES = {"fa", "en", "ar", "tr"}
ALLOWED_THEMES = {"system", "dark", "light"}
ALLOWED_SIDEBAR_PLACEMENTS = {"left", "right"}
ALLOWED_SIDEBAR_MODES = {"expanded", "compact", "hidden"}
ALLOWED_SIDEBAR_WIDTHS = {"normal", "wide"}
ALLOWED_MOBILE_SIDEBAR_MODES = {"compact", "expanded"}
ALLOWED_FONT_SCALES = {"small", "default", "large", "xlarge"}
ALLOWED_UI_DENSITIES = {"compact", "comfortable"}
ALLOWED_MOTION_PREFERENCES = {"system", "full", "reduced"}
ALLOWED_CONTROL_LOCATIONS = {
    "sidebar_settings",
    "header",
    "both",
}
ALLOWED_PRESETS = {"default", "focus", "minimal", "custom"}
ALLOWED_ACCENT_COLORS = {"cyan", "violet", "emerald", "amber", "rose"}

HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


class UiPreferenceValidationError(ValueError):
    """Raised when local UI preferences do not match the allowed schema."""


@dataclass(frozen=True)
class UiPreferences:
    schema_version: int = UI_PREFERENCES_SCHEMA_VERSION
    language: str = "fa"
    theme: str = "system"
    accent_color: str = "cyan"
    sidebar_placement: str = "left"
    sidebar_mode: str = "expanded"
    sidebar_width: str = "normal"
    mobile_sidebar_mode: str = "compact"
    font_scale: str = "default"
    ui_density: str = "comfortable"
    motion: str = "system"
    controls_location: str = "sidebar_settings"
    selected_preset: str = "default"
    widget_order: tuple[str, ...] = WIDGET_IDS
    hidden_widgets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "language": self.language,
            "theme": self.theme,
            "accent_color": self.accent_color,
            "sidebar_placement": self.sidebar_placement,
            "sidebar_mode": self.sidebar_mode,
            "sidebar_width": self.sidebar_width,
            "mobile_sidebar_mode": self.mobile_sidebar_mode,
            "font_scale": self.font_scale,
            "ui_density": self.ui_density,
            "motion": self.motion,
            "controls_location": self.controls_location,
            "selected_preset": self.selected_preset,
            "widget_order": list(self.widget_order),
            "hidden_widgets": list(self.hidden_widgets),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "UiPreferences":
        if not isinstance(value, Mapping):
            raise UiPreferenceValidationError(
                "UI preferences must be a JSON object."
            )

        source_version = value.get("schema_version", 1)

        if source_version not in {1, 2, 3, 4, UI_PREFERENCES_SCHEMA_VERSION}:
            raise UiPreferenceValidationError(
                "Unsupported UI preference schema version."
            )

        language = value.get("language", "fa")
        theme = value.get("theme", "system")
        accent_color = value.get("accent_color", "cyan")
        sidebar_placement = value.get("sidebar_placement", "left")
        sidebar_mode = value.get("sidebar_mode", "expanded")
        sidebar_width = value.get("sidebar_width", "normal")

        if source_version == 3:
            legacy_behavior = value.get(
                "mobile_sidebar_behavior",
                "follow_desktop",
            )
            mobile_sidebar_mode = {
                "follow_desktop": "compact",
                "compact_rail": "compact",
                "drawer": "expanded",
            }.get(legacy_behavior)
        else:
            mobile_sidebar_mode = value.get(
                "mobile_sidebar_mode",
                "compact",
            )

        font_scale = value.get("font_scale", "default")
        ui_density = value.get("ui_density", "comfortable")
        motion = value.get("motion", "system")
        controls_location = value.get(
            "controls_location",
            "sidebar_settings",
        )

        if controls_location == "app_menu":
            controls_location = "sidebar_settings"
        selected_preset = value.get("selected_preset", "default")
        widget_order = cls._validate_widget_order(
            value.get("widget_order", list(WIDGET_IDS))
        )
        hidden_widgets = cls._validate_hidden_widgets(
            value.get("hidden_widgets", [])
        )

        cls._validate_choice("language", language, ALLOWED_LANGUAGES)
        cls._validate_choice("theme", theme, ALLOWED_THEMES)
        cls._validate_accent_color(accent_color)
        cls._validate_choice(
            "sidebar_placement",
            sidebar_placement,
            ALLOWED_SIDEBAR_PLACEMENTS,
        )
        cls._validate_choice(
            "sidebar_mode",
            sidebar_mode,
            ALLOWED_SIDEBAR_MODES,
        )
        cls._validate_choice(
            "sidebar_width",
            sidebar_width,
            ALLOWED_SIDEBAR_WIDTHS,
        )
        cls._validate_choice(
            "mobile_sidebar_mode",
            mobile_sidebar_mode,
            ALLOWED_MOBILE_SIDEBAR_MODES,
        )
        cls._validate_choice(
            "font_scale",
            font_scale,
            ALLOWED_FONT_SCALES,
        )
        cls._validate_choice(
            "ui_density",
            ui_density,
            ALLOWED_UI_DENSITIES,
        )
        cls._validate_choice(
            "motion",
            motion,
            ALLOWED_MOTION_PREFERENCES,
        )
        cls._validate_choice(
            "controls_location",
            controls_location,
            ALLOWED_CONTROL_LOCATIONS,
        )
        cls._validate_choice(
            "selected_preset",
            selected_preset,
            ALLOWED_PRESETS,
        )

        return cls(
            schema_version=UI_PREFERENCES_SCHEMA_VERSION,
            language=language,
            theme=theme,
            accent_color=accent_color,
            sidebar_placement=sidebar_placement,
            sidebar_mode=sidebar_mode,
            sidebar_width=sidebar_width,
            mobile_sidebar_mode=mobile_sidebar_mode,
            font_scale=font_scale,
            ui_density=ui_density,
            motion=motion,
            controls_location=controls_location,
            selected_preset=selected_preset,
            widget_order=widget_order,
            hidden_widgets=hidden_widgets,
        )

    @staticmethod
    def _validate_choice(
        field_name: str,
        value: Any,
        allowed_values: set[str],
    ) -> None:
        if not isinstance(value, str) or value not in allowed_values:
            raise UiPreferenceValidationError(
                f"Unsupported {field_name}."
            )

    @staticmethod
    def _validate_accent_color(value: Any) -> None:
        if not isinstance(value, str) or (
            value not in ALLOWED_ACCENT_COLORS
            and HEX_COLOR_PATTERN.fullmatch(value) is None
        ):
            raise UiPreferenceValidationError(
                "Unsupported accent color."
            )

    @staticmethod
    def _validate_widget_order(value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise UiPreferenceValidationError("widget_order must be a list.")

        order = tuple(value)

        if any(not isinstance(widget_id, str) for widget_id in order):
            raise UiPreferenceValidationError(
                "widget_order contains an invalid widget identifier."
            )

        if len(order) != len(WIDGET_IDS) or set(order) != set(WIDGET_IDS):
            raise UiPreferenceValidationError(
                "widget_order must contain every known widget exactly once."
            )

        return order

    @staticmethod
    def _validate_hidden_widgets(value: Any) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise UiPreferenceValidationError(
                "hidden_widgets must be a list."
            )

        hidden = tuple(value)

        if any(not isinstance(widget_id, str) for widget_id in hidden):
            raise UiPreferenceValidationError(
                "hidden_widgets contains an invalid widget identifier."
            )

        if len(hidden) != len(set(hidden)) or not set(hidden).issubset(
            set(WIDGET_IDS)
        ):
            raise UiPreferenceValidationError(
                "hidden_widgets contains unknown or duplicate widgets."
            )

        return hidden


class UiPreferenceStore:
    """Atomic local storage for non-private per-device UI preferences."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> UiPreferences:
        if not self.path.is_file():
            return UiPreferences()

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise UiPreferenceValidationError(
                "Local UI preference file cannot be read."
            ) from error

        # v1, v2 and v3 files migrate in memory.
        # Disk rewrite happens only after explicit save.
        return UiPreferences.from_mapping(raw)

    def save(self, preferences: UiPreferences) -> UiPreferences:
        if not isinstance(preferences, UiPreferences):
            raise TypeError("preferences must be a UiPreferences object.")

        self._prepare_directory()

        serialized = (
            json.dumps(
                preferences.to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=".ui-preferences-",
            suffix=".tmp",
            dir=self.path.parent,
        )

        temporary_path = Path(temporary_name)

        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())

            self._restrict_permissions(temporary_path)
            os.replace(temporary_path, self.path)
            self._restrict_permissions(self.path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

        return preferences

    def _prepare_directory(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if os.name == "posix":
            os.chmod(self.path.parent, 0o700)

    @staticmethod
    def _restrict_permissions(path: Path) -> None:
        if os.name == "posix" and path.exists():
            os.chmod(path, 0o600)
