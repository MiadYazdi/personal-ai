from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

KNOWN_SCOPES = {
    "google_grounding",
    "provider_inference",
    "direct_web",
    "code_update",
}


class InternetAccessError(ValueError):
    """Raised when Internet Access Center settings are invalid or deny an action."""


@dataclass(frozen=True)
class InternetAccessSettings:
    master_enabled: bool
    scopes: dict[str, bool]

    @classmethod
    def defaults(cls) -> "InternetAccessSettings":
        return cls(False, {scope: False for scope in sorted(KNOWN_SCOPES)})

    @classmethod
    def from_mapping(cls, value: object) -> "InternetAccessSettings":
        if not isinstance(value, dict):
            raise InternetAccessError("Internet access settings are invalid.")

        master_enabled = value.get("master_enabled")
        scopes = value.get("scopes")

        if not isinstance(master_enabled, bool) or not isinstance(scopes, dict):
            raise InternetAccessError("Internet access settings are invalid.")

        if set(scopes) != KNOWN_SCOPES or any(
            not isinstance(enabled, bool) for enabled in scopes.values()
        ):
            raise InternetAccessError("Internet access scopes are invalid.")

        return cls(
            master_enabled=master_enabled,
            scopes={scope: scopes[scope] for scope in sorted(KNOWN_SCOPES)},
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "master_enabled": self.master_enabled,
            "scopes": dict(self.scopes),
            "network_execution_enabled": False,
            "always_requires_fresh_confirmation": True,
            "always_requires_vault_unlock": True,
            "automatic_execution": False,
        }


class InternetAccessController:
    """Local user-controlled Internet Access settings; never performs network I/O."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> InternetAccessSettings:
        if not self._path.exists():
            return InternetAccessSettings.defaults()

        try:
            value = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise InternetAccessError(
                "Internet access settings are unavailable."
            ) from error

        return InternetAccessSettings.from_mapping(value)

    def save(self, settings: InternetAccessSettings) -> InternetAccessSettings:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self._path.parent, 0o700)

        fd, temporary_name = tempfile.mkstemp(
            prefix=".personal-ai-internet-access-",
            dir=self._path.parent,
        )
        temporary: Path | None = Path(temporary_name)

        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", closefd=True) as stream:
                fd = -1
                json.dump(
                    settings.to_dict(),
                    stream,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                stream.flush()
                os.fsync(stream.fileno())

            os.replace(temporary, self._path)
            temporary = None

        finally:
            if fd >= 0:
                os.close(fd)
            if temporary is not None and temporary.exists():
                temporary.unlink()

        return settings

    def update(
        self,
        *,
        master_enabled: bool,
        scopes: dict[str, bool],
    ) -> InternetAccessSettings:
        settings = InternetAccessSettings.from_mapping(
            {
                "master_enabled": master_enabled,
                "scopes": scopes,
            }
        )
        return self.save(settings)

    def require_allowed(self, scope: str) -> None:
        if scope not in KNOWN_SCOPES:
            raise InternetAccessError("Internet access scope is unknown.")

        settings = self.load()
        if not settings.master_enabled:
            raise InternetAccessError(
                "Internet Access Center master switch is off."
            )
        if not settings.scopes[scope]:
            raise InternetAccessError(
                "This Internet Access Center scope is off."
            )
