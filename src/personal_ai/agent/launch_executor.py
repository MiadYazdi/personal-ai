from __future__ import annotations

import configparser
import hashlib
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from .permissions import SHELL_EXECUTABLES, SHELL_OPERATORS


DEFAULT_DESKTOP_ROOTS = (
    Path.home() / ".local" / "share" / "applications",
    Path("/usr/share/applications"),
)
BLOCKED_EXECUTABLES = {*SHELL_EXECUTABLES, "env", "sudo", "pkexec"}


class LaunchPreviewError(ValueError):
    """Raised when an exact desktop entry cannot form a safe launch preview."""


class LaunchExecutionError(LaunchPreviewError):
    """Raised when a confirmed exact launch cannot start."""


@dataclass(frozen=True)
class DesktopLaunchPreview:
    desktop_id: str
    canonical_desktop_path: str
    application_name: str
    argv: tuple[str, ...]
    executable_path: str
    desktop_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "desktop_id": self.desktop_id,
            "canonical_desktop_path": self.canonical_desktop_path,
            "application_name": self.application_name,
            "argv": list(self.argv),
            "executable_path": self.executable_path,
            "desktop_sha256": self.desktop_sha256,
            "execution": "not_started",
        }


@dataclass(frozen=True)
class LaunchExecutionResult:
    pid: int
    argv: tuple[str, ...]
    canonical_desktop_path: str
    desktop_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "argv": list(self.argv),
            "canonical_desktop_path": self.canonical_desktop_path,
            "desktop_sha256": self.desktop_sha256,
            "started": True,
        }


class UbuntuApplicationLaunchPreview:
    """Exact desktop-entry resolution and preview; it never launches an app."""

    def __init__(
        self,
        *,
        desktop_roots: Iterable[str | Path] = DEFAULT_DESKTOP_ROOTS,
        executable_resolver: Callable[[str], str | None] = shutil.which,
        popen_factory: Callable[..., object] = subprocess.Popen,
    ) -> None:
        self._desktop_roots = tuple(Path(root).expanduser() for root in desktop_roots)
        self._executable_resolver = executable_resolver
        self._popen_factory = popen_factory

    def preview(self, desktop_entry: str) -> DesktopLaunchPreview:
        entry_path, desktop_id = self._resolve_exact_entry(desktop_entry)
        raw = entry_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        parser = configparser.ConfigParser(interpolation=None, strict=True)
        try:
            parser.read_string(raw.decode("utf-8"))
        except (UnicodeDecodeError, configparser.Error) as error:
            raise LaunchPreviewError("Desktop entry is not valid UTF-8 application metadata.") from error
        if not parser.has_section("Desktop Entry"):
            raise LaunchPreviewError("Desktop entry has no Desktop Entry section.")
        section = parser["Desktop Entry"]
        if section.get("Type", "").strip() != "Application":
            raise LaunchPreviewError("Desktop entry must have Type=Application.")
        name = section.get("Name", "").strip()
        exec_line = section.get("Exec", "").strip()
        if not name or not exec_line:
            raise LaunchPreviewError("Desktop entry requires Name and Exec.")
        try:
            argv = tuple(shlex.split(exec_line, posix=True))
        except ValueError as error:
            raise LaunchPreviewError("Desktop Exec cannot be parsed safely.") from error
        self._validate_argv(argv)
        executable = self._executable_resolver(argv[0])
        if not executable:
            raise LaunchPreviewError("Desktop executable is unavailable on this device.")
        return DesktopLaunchPreview(
            desktop_id=desktop_id,
            canonical_desktop_path=str(entry_path),
            application_name=name,
            argv=argv,
            executable_path=str(Path(executable).resolve()),
            desktop_sha256=digest,
        )

    def launch(
        self,
        preview: DesktopLaunchPreview,
        *,
        expected_desktop_sha256: str,
    ) -> LaunchExecutionResult:
        if preview.desktop_sha256 != expected_desktop_sha256:
            raise LaunchExecutionError("Desktop entry changed; preview again before launch.")
        argv = (preview.executable_path, *preview.argv[1:])
        try:
            process = self._popen_factory(
                argv,
                cwd="/",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
            pid = getattr(process, "pid", None)
        except OSError as error:
            raise LaunchExecutionError("Confirmed application could not be started.") from error
        if not isinstance(pid, int) or pid <= 0:
            raise LaunchExecutionError("Launch process did not provide a valid PID.")
        return LaunchExecutionResult(
            pid=pid,
            argv=argv,
            canonical_desktop_path=preview.canonical_desktop_path,
            desktop_sha256=preview.desktop_sha256,
        )

    def _resolve_exact_entry(self, value: str) -> tuple[Path, str]:
        if not isinstance(value, str) or not value.strip():
            raise LaunchPreviewError("Desktop entry ID or path is required.")
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            resolved = candidate.resolve(strict=True)
            root = self._matching_root(resolved)
            if root is None:
                raise LaunchPreviewError("Desktop entry is outside approved application roots.")
            return self._require_desktop_file(resolved), str(resolved.relative_to(root))
        if candidate.name != value or not value.endswith(".desktop") or ".." in candidate.parts:
            raise LaunchPreviewError("Desktop ID must be an exact relative .desktop path.")
        for root in self._desktop_roots:
            exact = root / candidate
            if exact.is_file():
                resolved = exact.resolve(strict=True)
                if self._matching_root(resolved) is not None:
                    return self._require_desktop_file(resolved), value
        raise LaunchPreviewError("Requested desktop entry does not exist in approved roots.")

    def _matching_root(self, target: Path) -> Path | None:
        for root in self._desktop_roots:
            try:
                canonical_root = root.resolve(strict=True)
                target.relative_to(canonical_root)
                return canonical_root
            except (FileNotFoundError, ValueError):
                continue
        return None

    @staticmethod
    def _require_desktop_file(path: Path) -> Path:
        if not path.is_file() or path.suffix != ".desktop":
            raise LaunchPreviewError("Requested entry must be a regular .desktop file.")
        return path

    @staticmethod
    def _validate_argv(argv: tuple[str, ...]) -> None:
        if not argv or any(not item for item in argv):
            raise LaunchPreviewError("Desktop Exec is empty.")
        executable = Path(argv[0]).name.lower()
        if executable in BLOCKED_EXECUTABLES:
            raise LaunchPreviewError("Shell, sudo, and environment executables are not allowed.")
        if any(item in SHELL_OPERATORS or "\n" in item or "\r" in item for item in argv):
            raise LaunchPreviewError("Desktop Exec contains a prohibited shell operator.")
        if any("%" in item for item in argv):
            raise LaunchPreviewError("Desktop file and URL placeholders are not supported in v1.")
