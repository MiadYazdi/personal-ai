from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable


class NativePickerError(RuntimeError):
    pass


class NativePickerMode(StrEnum):
    OPEN_FILE = "open_file"
    SELECT_DIRECTORY = "select_directory"
    SAVE_FILE = "save_file"
    DESKTOP_ENTRY = "desktop_entry"


@dataclass(frozen=True)
class NativePickerSelection:
    mode: NativePickerMode
    cancelled: bool
    path: str | None

    def to_dict(self) -> dict[str, object]:
        return {"mode": self.mode, "cancelled": self.cancelled, "path": self.path}


class UbuntuNativePicker:
    """Fixed Zenity picker bridge; no shell and no Agent directory scan."""

    def __init__(
        self,
        *,
        dialog_binary: str | Path = "/usr/bin/zenity",
        dialog_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        session_available: Callable[[], bool] | None = None,
    ) -> None:
        self._dialog_binary = Path(dialog_binary)
        self._dialog_runner = dialog_runner
        self._session_available = session_available or self._default_session_available

    def select(self, mode: NativePickerMode, *, title: str) -> NativePickerSelection:
        if not self._dialog_binary.is_file():
            raise NativePickerError("Native picker provider is unavailable.")
        if not self._session_available():
            raise NativePickerError("A graphical local desktop session is required for the picker.")
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise NativePickerError("Picker title is invalid.")

        argv = [str(self._dialog_binary), "--file-selection", f"--title={title}"]

        if mode == NativePickerMode.SELECT_DIRECTORY:
            argv.append("--directory")
        elif mode == NativePickerMode.SAVE_FILE:
            argv.extend(["--save", "--confirm-overwrite"])
        elif mode == NativePickerMode.DESKTOP_ENTRY:
            argv.append("--file-filter=Desktop entries | *.desktop")
        elif mode != NativePickerMode.OPEN_FILE:
            raise NativePickerError("Unsupported picker mode.")

        try:
            completed = self._dialog_runner(
                argv,
                check=False,
                text=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=None,
            )
        except OSError as error:
            raise NativePickerError("Native picker could not be started.") from error

        if completed.returncode == 1:
            return NativePickerSelection(mode=mode, cancelled=True, path=None)
        if completed.returncode != 0:
            raise NativePickerError("Native picker failed without a selection.")

        selected = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else ""
        if not selected:
            raise NativePickerError("Native picker returned no path.")

        return NativePickerSelection(mode=mode, cancelled=False, path=selected)

    @staticmethod
    def _default_session_available() -> bool:
        return bool(
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        ) and bool(os.environ.get("DBUS_SESSION_BUS_ADDRESS"))
