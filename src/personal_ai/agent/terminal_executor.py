from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .permissions import SHELL_EXECUTABLES, SHELL_OPERATORS, TerminalPreview

MAX_TIMEOUT_SECONDS = 600
DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_BYTES = 64 * 1024


class TerminalExecutionError(ValueError):
    pass


@dataclass(frozen=True)
class TerminalExecutionPreview:
    argv: tuple[str, ...]
    cwd: str
    executable_path: str
    expected_effect: str
    timeout_seconds: int
    request_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "cwd": self.cwd,
            "executable_path": self.executable_path,
            "expected_effect": self.expected_effect,
            "timeout_seconds": self.timeout_seconds,
            "request_sha256": self.request_sha256,
            "shell": False,
            "max_output_bytes": MAX_OUTPUT_BYTES,
        }


@dataclass(frozen=True)
class TerminalRunResult:
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    timed_out: bool
    duration_ms: int


@dataclass(frozen=True)
class TerminalExecutionResult:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    output_truncated: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "duration_ms": self.duration_ms,
            "output_truncated": self.output_truncated,
        }


class UbuntuStructuredTerminalExecutor:
    def __init__(
        self,
        *,
        executable_resolver: Callable[[str], str | None] = shutil.which,
        runner: Callable[[tuple[str, ...], str, int], TerminalRunResult] | None = None,
    ) -> None:
        self._executable_resolver = executable_resolver
        self._runner = runner or self._run_exact

    def preview(
        self,
        argv: list[str] | tuple[str, ...],
        cwd: str,
        expected_effect: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> TerminalExecutionPreview:
        tokens = tuple(argv)
        self._validate(tokens, cwd, expected_effect, timeout_seconds)

        executable = self._executable_resolver(tokens[0])
        if not executable:
            raise TerminalExecutionError("Terminal executable is unavailable.")

        canonical_cwd = Path(cwd).expanduser().resolve(strict=True)
        if not canonical_cwd.is_dir():
            raise TerminalExecutionError("Terminal cwd must be a directory.")

        resolved_argv = (str(Path(executable).resolve()), *tokens[1:])
        digest = hashlib.sha256(
            json.dumps(
                {
                    "argv": resolved_argv,
                    "cwd": str(canonical_cwd),
                    "effect": expected_effect,
                    "timeout": timeout_seconds,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        return TerminalExecutionPreview(
            resolved_argv,
            str(canonical_cwd),
            resolved_argv[0],
            expected_effect,
            timeout_seconds,
            digest,
        )

    def execute(
        self,
        preview: TerminalExecutionPreview,
        *,
        expected_request_sha256: str,
    ) -> TerminalExecutionResult:
        if preview.request_sha256 != expected_request_sha256:
            raise TerminalExecutionError("Terminal request changed; preview again.")

        result = self._runner(
            preview.argv,
            preview.cwd,
            preview.timeout_seconds,
        )

        stdout, stdout_truncated = self._clip(result.stdout)
        stderr, stderr_truncated = self._clip(result.stderr)

        return TerminalExecutionResult(
            result.exit_code,
            stdout,
            stderr,
            result.timed_out,
            result.duration_ms,
            stdout_truncated or stderr_truncated,
        )

    @staticmethod
    def _validate(
        argv: tuple[str, ...],
        cwd: str,
        expected_effect: str,
        timeout_seconds: int,
    ) -> None:
        if not argv or any(not isinstance(item, str) or not item for item in argv):
            raise TerminalExecutionError("Exact argv is required.")

        executable = Path(argv[0]).name.lower()
        if executable in {*SHELL_EXECUTABLES, "sudo", "env", "pkexec"}:
            raise TerminalExecutionError("Shell and sudo executables are prohibited.")

        if any(
            item in SHELL_OPERATORS or "\n" in item or "\r" in item
            for item in argv
        ):
            raise TerminalExecutionError("Shell operators are prohibited.")

        if not isinstance(cwd, str) or not cwd:
            raise TerminalExecutionError("Terminal cwd is required.")

        if not isinstance(expected_effect, str) or not expected_effect.strip():
            raise TerminalExecutionError("Expected effect is required.")

        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise TerminalExecutionError("Timeout must be between 1 and 600 seconds.")

    @staticmethod
    def _clip(value: bytes) -> tuple[str, bool]:
        truncated = len(value) > MAX_OUTPUT_BYTES
        return (
            value[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace"),
            truncated,
        )

    @staticmethod
    def _run_exact(
        argv: tuple[str, ...],
        cwd: str,
        timeout_seconds: int,
    ) -> TerminalRunResult:
        started = time.monotonic()
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            close_fds=True,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            return TerminalRunResult(
                process.returncode,
                stdout,
                stderr,
                False,
                int((time.monotonic() - started) * 1000),
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return TerminalRunResult(
                None,
                stdout,
                stderr,
                True,
                int((time.monotonic() - started) * 1000),
            )
