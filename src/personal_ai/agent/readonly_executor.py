from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


MAX_TEXT_BYTES = 1 * 1024 * 1024
SENSITIVE_PATH_PARTS = {
    ".ssh",
    ".gnupg",
    ".netrc",
    ".aws",
    ".kube",
    ".mozilla",
    ".pki",
}
SENSITIVE_NAME_TOKENS = {"secret", "token", "credential", "credentials", "password", "wallet"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".kdbx", ".ovpn"}


class ReadOnlyExecutorError(Exception):
    """Base error for selected-scope Ubuntu read-only operations."""


class PathScopeError(ReadOnlyExecutorError):
    """Raised when a canonical path falls outside user-approved scope."""


class TextLimitError(ReadOnlyExecutorError):
    """Raised when text exceeds the v1 size limit or is not safe text."""


class SensitiveReadConfirmationRequired(ReadOnlyExecutorError):
    """Raised before reading sensitive content without fresh confirmation."""


class SensitiveModelShareConfirmationRequired(ReadOnlyExecutorError):
    """Raised before sharing sensitive content with the local model."""


class ReadMode(StrEnum):
    METADATA = "read_metadata"
    TEXT = "read_text"


@dataclass(frozen=True)
class ReadPreview:
    selected_scope: str
    canonical_path: str
    mode: ReadMode
    sensitive: bool
    size_bytes: int
    text_limit_bytes: int
    requires_sensitive_confirmation: bool
    requires_model_share_confirmation: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_scope": self.selected_scope,
            "canonical_path": self.canonical_path,
            "mode": self.mode,
            "sensitive": self.sensitive,
            "size_bytes": self.size_bytes,
            "text_limit_bytes": self.text_limit_bytes,
            "requires_sensitive_confirmation": self.requires_sensitive_confirmation,
            "requires_model_share_confirmation": self.requires_model_share_confirmation,
        }


@dataclass(frozen=True)
class MetadataResult:
    canonical_path: str
    file_type: str
    size_bytes: int
    modified_ns: int
    permission_octal: str
    sensitive: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_path": self.canonical_path,
            "file_type": self.file_type,
            "size_bytes": self.size_bytes,
            "modified_ns": self.modified_ns,
            "permission_octal": self.permission_octal,
            "sensitive": self.sensitive,
        }


@dataclass(frozen=True)
class TextResult:
    metadata: MetadataResult
    content: str
    share_with_model: bool


class UbuntuReadOnlyExecutor:
    """Selected-scope metadata/text reader; it never writes or executes commands."""

    def preview(self, selected_scope: str | Path, requested_path: str | Path, mode: ReadMode) -> ReadPreview:
        scope, target = self._canonical_scope_and_target(selected_scope, requested_path)
        metadata = self._metadata(target)
        sensitive = self._is_sensitive(target)
        return ReadPreview(
            selected_scope=str(scope),
            canonical_path=str(target),
            mode=mode,
            sensitive=sensitive,
            size_bytes=metadata.size_bytes,
            text_limit_bytes=MAX_TEXT_BYTES,
            requires_sensitive_confirmation=sensitive and mode == ReadMode.TEXT,
            requires_model_share_confirmation=sensitive and mode == ReadMode.TEXT,
        )

    def read_metadata(self, selected_scope: str | Path, requested_path: str | Path) -> MetadataResult:
        _, target = self._canonical_scope_and_target(selected_scope, requested_path)
        return self._metadata(target)

    def read_text(
        self,
        selected_scope: str | Path,
        requested_path: str | Path,
        *,
        sensitive_confirmed: bool = False,
        share_with_model: bool = False,
        model_share_confirmed: bool = False,
    ) -> TextResult:
        _, target = self._canonical_scope_and_target(selected_scope, requested_path)
        metadata = self._metadata(target)
        if metadata.sensitive and not sensitive_confirmed:
            raise SensitiveReadConfirmationRequired("Sensitive content requires fresh confirmation.")
        if share_with_model and not model_share_confirmed:
            raise SensitiveModelShareConfirmationRequired("Model sharing requires separate confirmation.")
        if metadata.size_bytes > MAX_TEXT_BYTES:
            raise TextLimitError("Text file exceeds the 1 MiB v1 limit.")

        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(target, flags)
        try:
            current = os.fstat(fd)
            if not stat.S_ISREG(current.st_mode):
                raise TextLimitError("Only regular text files can be read.")
            if current.st_size > MAX_TEXT_BYTES:
                raise TextLimitError("Text file exceeds the 1 MiB v1 limit.")
            raw = os.read(fd, MAX_TEXT_BYTES + 1)
        finally:
            os.close(fd)

        if len(raw) > MAX_TEXT_BYTES or b"\x00" in raw:
            raise TextLimitError("File is binary or exceeds the text limit.")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise TextLimitError("File is not valid UTF-8 text.") from error
        return TextResult(metadata=metadata, content=content, share_with_model=share_with_model)

    def _canonical_scope_and_target(self, selected_scope: str | Path, requested_path: str | Path) -> tuple[Path, Path]:
        scope = Path(selected_scope).expanduser().resolve(strict=True)
        target = Path(requested_path).expanduser().resolve(strict=True)
        if scope.is_file():
            allowed = target == scope
        else:
            try:
                target.relative_to(scope)
                allowed = True
            except ValueError:
                allowed = False
        if not allowed:
            raise PathScopeError("Canonical path is outside the selected scope.")
        return scope, target

    def _metadata(self, target: Path) -> MetadataResult:
        info = target.stat()
        if stat.S_ISREG(info.st_mode):
            file_type = "regular_file"
        elif stat.S_ISDIR(info.st_mode):
            file_type = "directory"
        else:
            file_type = "other"
        return MetadataResult(
            canonical_path=str(target),
            file_type=file_type,
            size_bytes=info.st_size,
            modified_ns=info.st_mtime_ns,
            permission_octal=oct(stat.S_IMODE(info.st_mode)),
            sensitive=self._is_sensitive(target),
        )

    @staticmethod
    def _is_sensitive(target: Path) -> bool:
        lowered_parts = {part.lower() for part in target.parts}
        name = target.name.lower()
        stem_tokens = set(name.replace("-", "_").replace(".", "_").split("_"))
        return (
            bool(lowered_parts & SENSITIVE_PATH_PARTS)
            or bool(stem_tokens & SENSITIVE_NAME_TOKENS)
            or target.suffix.lower() in SENSITIVE_SUFFIXES
        )
