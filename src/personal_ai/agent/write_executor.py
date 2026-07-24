from __future__ import annotations

import difflib
import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

MAX_TEXT_BYTES = 1 * 1024 * 1024
MAX_DIFF_BYTES = 64 * 1024


class WriteFileError(ValueError):
    """Raised when a selected-scope text-file write cannot be safely previewed."""


@dataclass(frozen=True)
class _FileState:
    content: str
    sha256: str
    size_bytes: int
    mode: int


@dataclass(frozen=True)
class WriteFilePreview:
    selected_scope: str
    canonical_path: str
    operation: str
    old_sha256: str | None
    new_sha256: str
    old_size_bytes: int
    new_size_bytes: int
    resulting_mode: str
    diff: str
    diff_truncated: bool
    request_sha256: str
    _content: str = field(repr=False, compare=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_scope": self.selected_scope,
            "canonical_path": self.canonical_path,
            "operation": self.operation,
            "old_sha256": self.old_sha256,
            "new_sha256": self.new_sha256,
            "old_size_bytes": self.old_size_bytes,
            "new_size_bytes": self.new_size_bytes,
            "resulting_mode": self.resulting_mode,
            "diff": self.diff,
            "diff_truncated": self.diff_truncated,
            "request_sha256": self.request_sha256,
            "text_limit_bytes": MAX_TEXT_BYTES,
            "diff_limit_bytes": MAX_DIFF_BYTES,
        }


@dataclass(frozen=True)
class WriteFileResult:
    canonical_path: str
    operation: str
    sha256: str
    size_bytes: int
    permission_octal: str

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_path": self.canonical_path,
            "operation": self.operation,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "permission_octal": self.permission_octal,
        }


AtomicWriter = Callable[[Path, bytes, int, bool], None]


class UbuntuWriteFileExecutor:
    """Selected-scope UTF-8 writer with digest recheck and atomic replacement."""

    def __init__(self, *, atomic_writer: AtomicWriter | None = None) -> None:
        self._atomic_writer = atomic_writer or self._atomic_write

    def preview(
        self,
        selected_scope: str | Path,
        requested_path: str | Path,
        content: str,
    ) -> WriteFilePreview:
        new_bytes = self._validate_new_content(content)
        scope, target = self._canonical_scope_and_target(
            selected_scope,
            requested_path,
        )
        current = self._read_current_state(target)

        operation = "create" if current is None else "overwrite"
        old_content = "" if current is None else current.content
        old_sha256 = None if current is None else current.sha256
        old_size_bytes = 0 if current is None else current.size_bytes
        resulting_mode = 0o600 if current is None else current.mode
        new_sha256 = hashlib.sha256(new_bytes).hexdigest()
        diff, diff_truncated = self._make_diff(
            old_content,
            content,
            target,
        )

        digest_payload = {
            "selected_scope": str(scope),
            "canonical_path": str(target),
            "operation": operation,
            "old_sha256": old_sha256,
            "new_sha256": new_sha256,
            "old_size_bytes": old_size_bytes,
            "new_size_bytes": len(new_bytes),
            "resulting_mode": resulting_mode,
        }
        request_sha256 = hashlib.sha256(
            json.dumps(
                digest_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return WriteFilePreview(
            selected_scope=str(scope),
            canonical_path=str(target),
            operation=operation,
            old_sha256=old_sha256,
            new_sha256=new_sha256,
            old_size_bytes=old_size_bytes,
            new_size_bytes=len(new_bytes),
            resulting_mode=oct(resulting_mode),
            diff=diff,
            diff_truncated=diff_truncated,
            request_sha256=request_sha256,
            _content=content,
        )

    def execute(
        self,
        preview: WriteFilePreview,
        *,
        expected_request_sha256: str,
    ) -> WriteFileResult:
        if preview.request_sha256 != expected_request_sha256:
            raise WriteFileError("Write request changed; preview again.")

        refreshed = self.preview(
            preview.selected_scope,
            preview.canonical_path,
            preview._content,
        )
        if refreshed.request_sha256 != preview.request_sha256:
            raise WriteFileError(
                "Target changed since preview; review the new diff first."
            )

        mode = int(preview.resulting_mode, 8)
        content_bytes = preview._content.encode("utf-8")
        self._atomic_writer(
            Path(preview.canonical_path),
            content_bytes,
            mode,
            preview.operation == "create",
        )

        return WriteFileResult(
            canonical_path=preview.canonical_path,
            operation=preview.operation,
            sha256=preview.new_sha256,
            size_bytes=preview.new_size_bytes,
            permission_octal=preview.resulting_mode,
        )

    @staticmethod
    def _validate_new_content(content: str) -> bytes:
        if not isinstance(content, str):
            raise WriteFileError("UTF-8 text content is required.")
        try:
            encoded = content.encode("utf-8")
        except UnicodeEncodeError as error:
            raise WriteFileError("Content is not valid UTF-8 text.") from error
        if b"\x00" in encoded:
            raise WriteFileError("NUL bytes are not allowed in text files.")
        if len(encoded) > MAX_TEXT_BYTES:
            raise WriteFileError("Text exceeds the 1 MiB v1 limit.")
        return encoded

    @staticmethod
    def _canonical_scope_and_target(
        selected_scope: str | Path,
        requested_path: str | Path,
    ) -> tuple[Path, Path]:
        try:
            scope = Path(selected_scope).expanduser().resolve(strict=True)
        except OSError as error:
            raise WriteFileError("Selected write scope is unavailable.") from error

        if not scope.is_dir():
            raise WriteFileError("Selected write scope must be an existing directory.")

        requested = Path(requested_path).expanduser()
        candidate = requested if requested.is_absolute() else scope / requested
        if not candidate.name:
            raise WriteFileError("A target file name is required.")

        try:
            parent = candidate.parent.resolve(strict=True)
        except OSError as error:
            raise WriteFileError(
                "Target parent directory must already exist."
            ) from error

        if not parent.is_dir():
            raise WriteFileError("Target parent must be a directory.")

        target = parent / candidate.name
        try:
            target.relative_to(scope)
        except ValueError as error:
            raise WriteFileError(
                "Canonical target is outside the selected write scope."
            ) from error

        return scope, target

    @staticmethod
    def _read_current_state(target: Path) -> _FileState | None:
        try:
            info = os.lstat(target)
        except FileNotFoundError:
            return None
        except OSError as error:
            raise WriteFileError("Target metadata could not be read.") from error

        if stat.S_ISLNK(info.st_mode):
            raise WriteFileError("Symbolic-link targets are not writable.")
        if not stat.S_ISREG(info.st_mode):
            raise WriteFileError("Only regular UTF-8 text files are writable.")
        if info.st_size > MAX_TEXT_BYTES:
            raise WriteFileError("Existing text exceeds the 1 MiB v1 limit.")

        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW

        try:
            fd = os.open(target, flags)
        except OSError as error:
            raise WriteFileError("Existing target could not be safely opened.") from error

        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):
                raise WriteFileError("Only regular UTF-8 text files are writable.")
            if opened.st_size > MAX_TEXT_BYTES:
                raise WriteFileError("Existing text exceeds the 1 MiB v1 limit.")

            chunks: list[bytes] = []
            remaining = MAX_TEXT_BYTES + 1
            while remaining > 0:
                chunk = os.read(fd, remaining)
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
        finally:
            os.close(fd)

        if len(raw) > MAX_TEXT_BYTES or b"\x00" in raw:
            raise WriteFileError("Existing file is binary or exceeds the text limit.")

        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WriteFileError("Existing file is not valid UTF-8 text.") from error

        return _FileState(
            content=content,
            sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw),
            mode=stat.S_IMODE(opened.st_mode),
        )

    @staticmethod
    def _make_diff(
        old_content: str,
        new_content: str,
        target: Path,
    ) -> tuple[str, bool]:
        diff = "".join(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(target),
                tofile=str(target),
                n=3,
            )
        )
        encoded = diff.encode("utf-8")
        truncated = len(encoded) > MAX_DIFF_BYTES
        return (
            encoded[:MAX_DIFF_BYTES].decode("utf-8", errors="replace"),
            truncated,
        )

    @staticmethod
    def _atomic_write(
        target: Path,
        content: bytes,
        mode: int,
        create_only: bool,
    ) -> None:
        temporary_path: Path | None = None
        fd = -1

        try:
            fd, raw_temporary_path = tempfile.mkstemp(
                prefix=".personal-ai-write-",
                dir=target.parent,
            )
            temporary_path = Path(raw_temporary_path)
            os.fchmod(fd, mode)

            with os.fdopen(fd, "wb", closefd=True) as stream:
                fd = -1
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())

            if create_only:
                try:
                    os.link(temporary_path, target)
                except FileExistsError as error:
                    raise WriteFileError(
                        "Target appeared after preview; preview again."
                    ) from error
                os.unlink(temporary_path)
                temporary_path = None
            else:
                os.replace(temporary_path, target)
                temporary_path = None

            directory_flags = os.O_RDONLY
            if hasattr(os, "O_DIRECTORY"):
                directory_flags |= os.O_DIRECTORY
            directory_fd = os.open(target.parent, directory_flags)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

        except WriteFileError:
            raise
        except OSError as error:
            raise WriteFileError("Atomic file write could not be completed.") from error
        finally:
            if fd >= 0:
                os.close(fd)
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass
