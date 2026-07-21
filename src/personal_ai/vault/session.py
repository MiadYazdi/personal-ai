from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Literal

from .crypto import VaultUnlockError
from .recovery import RecoveryKeyFormatError
from .store import VaultStore


VaultState = Literal["not_created", "locked", "unlocked"]


class VaultSessionError(Exception):
    """Base error for Vault runtime session operations."""


class VaultNotConfiguredError(VaultSessionError):
    """Raised when an unlock is requested before Vault creation."""


class VaultAlreadyUnlockedError(VaultSessionError):
    """Raised when an unlock is requested for an active Vault session."""


class VaultSessionValidationError(VaultSessionError):
    """Raised when an unlock credential is absent or blank."""


class VaultSessionUnlockError(VaultSessionError):
    """Raised when a Vault credential cannot open the Vault."""


class VaultSessionStorageError(VaultSessionError):
    """Raised when the local Vault cannot be safely accessed."""


class VaultLockedError(VaultSessionError):
    """Raised when private Vault access is requested while locked."""


@dataclass(frozen=True)
class VaultProfileContext:
    """Minimal decrypted profile context available only while unlocked."""

    profile_name: str
    address_name: str

    def to_dict(self) -> dict[str, str]:
        return {
            "profile_name": self.profile_name,
            "address_name": self.address_name,
        }


@dataclass(frozen=True)
class VaultSessionStatus:
    vault_configured: bool
    vault_state: VaultState
    profile_context: VaultProfileContext | None
    inactivity_timeout_seconds: float

    def to_dict(self) -> dict[str, object]:
        return {
            "vault_configured": self.vault_configured,
            "vault_state": self.vault_state,
            "profile_context": (
                self.profile_context.to_dict()
                if self.profile_context is not None
                else None
            ),
            "inactivity_timeout_seconds": self.inactivity_timeout_seconds,
        }


class VaultSessionManager:
    """
    Owns the single in-memory unlocked Vault session for this Backend process.

    The passphrase and Recovery Key inputs are never retained. The opened
    VaultStore, including its Vault key, is released on lock, auto-lock, or
    Backend shutdown.
    """

    def __init__(
        self,
        vault_path: str | Path,
        *,
        inactivity_timeout_seconds: float = 30 * 60,
        monotonic_clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if (
            isinstance(inactivity_timeout_seconds, bool)
            or not isinstance(inactivity_timeout_seconds, (int, float))
            or inactivity_timeout_seconds <= 0
        ):
            raise ValueError(
                "inactivity_timeout_seconds must be a positive number."
            )

        self._vault_path = Path(vault_path)
        self._inactivity_timeout_seconds = float(
            inactivity_timeout_seconds
        )
        self._monotonic_clock = monotonic_clock
        self._lock = threading.RLock()

        self._vault: VaultStore | None = None
        self._profile_context: VaultProfileContext | None = None
        self._last_activity_at: float | None = None
        self._auto_lock_timer: threading.Timer | None = None
        self._timer_generation = 0

    def status(self) -> VaultSessionStatus:
        """Return session state without extending the inactivity timeout."""

        with self._lock:
            self._expire_if_needed_locked()
            return self._status_locked()

    def unlock_with_passphrase(
        self,
        passphrase: str | None,
    ) -> VaultSessionStatus:
        credential = self._validate_credential(passphrase)
        return self._unlock(
            lambda: VaultStore.open(self._vault_path, credential)
        )

    def unlock_with_recovery_bip39(
        self,
        phrase: str | None,
    ) -> VaultSessionStatus:
        credential = self._validate_credential(phrase)
        return self._unlock(
            lambda: VaultStore.open_with_recovery_bip39(
                self._vault_path,
                credential,
            )
        )

    def unlock_with_recovery_base64url(
        self,
        code: str | None,
    ) -> VaultSessionStatus:
        credential = self._validate_credential(code)
        return self._unlock(
            lambda: VaultStore.open_with_recovery_base64url(
                self._vault_path,
                credential,
            )
        )

    def lock(self) -> VaultSessionStatus:
        """Close the current Vault session; repeated locks are safe."""

        with self._lock:
            self._lock_locked()
            return self._status_locked()

    def close(self) -> None:
        """Release the session during Backend shutdown."""

        self.lock()

    @contextmanager
    def access(self) -> Iterator[VaultStore]:
        """
        Provide exclusive private Vault access and count it as activity.

        Future memory/chat/device features must use this context manager
        instead of holding a VaultStore reference independently.
        """

        with self._lock:
            self._expire_if_needed_locked()

            if self._vault is None:
                raise VaultLockedError("Vault is locked.")

            self._touch_locked()

            try:
                yield self._vault
            finally:
                if self._vault is not None:
                    self._touch_locked()

    def _unlock(
        self,
        opener: Callable[[], VaultStore],
    ) -> VaultSessionStatus:
        with self._lock:
            self._expire_if_needed_locked()

            if self._vault is not None:
                raise VaultAlreadyUnlockedError("Vault is already unlocked.")

            # Avoid sqlite3.connect creating an empty database on a bad path.
            if not self._vault_path.is_file():
                raise VaultNotConfiguredError(
                    "A local Vault is not configured."
                )

            vault: VaultStore | None = None

            try:
                vault = opener()
            except (
                VaultUnlockError,
                RecoveryKeyFormatError,
                ValueError,
            ) as error:
                raise VaultSessionUnlockError(
                    "Vault credential was rejected."
                ) from error
            except (OSError, sqlite3.Error) as error:
                raise VaultSessionStorageError(
                    "Vault storage could not be opened."
                ) from error

            try:
                profile_context = self._load_profile_context(vault)
            except Exception as error:
                vault.close()
                raise VaultSessionStorageError(
                    "Vault profile context could not be read."
                ) from error

            self._vault = vault
            self._profile_context = profile_context
            self._touch_locked()

            return self._status_locked()

    @staticmethod
    def _validate_credential(credential: str | None) -> str:
        if not isinstance(credential, str) or not credential.strip():
            raise VaultSessionValidationError(
                "A non-empty Vault credential is required."
            )

        # Passphrases deliberately keep leading/trailing whitespace intact.
        return credential

    @staticmethod
    def _load_profile_context(
        vault: VaultStore,
    ) -> VaultProfileContext | None:
        profile = vault.find_first_record_by_type("profile")

        if profile is None:
            return None

        profile_name = profile.payload.get("profile_name")
        address_name = profile.payload.get("address_name")

        if (
            not isinstance(profile_name, str)
            or not profile_name.strip()
        ):
            return None

        if not isinstance(address_name, str) or not address_name.strip():
            address_name = profile_name

        return VaultProfileContext(
            profile_name=profile_name,
            address_name=address_name,
        )

    def _status_locked(self) -> VaultSessionStatus:
        if self._vault is not None:
            return VaultSessionStatus(
                vault_configured=True,
                vault_state="unlocked",
                profile_context=self._profile_context,
                inactivity_timeout_seconds=(
                    self._inactivity_timeout_seconds
                ),
            )

        configured = self._vault_path.is_file()

        return VaultSessionStatus(
            vault_configured=configured,
            vault_state="locked" if configured else "not_created",
            profile_context=None,
            inactivity_timeout_seconds=self._inactivity_timeout_seconds,
        )

    def _touch_locked(self) -> None:
        self._last_activity_at = self._monotonic_clock()
        self._schedule_auto_lock_locked(
            delay_seconds=self._inactivity_timeout_seconds
        )

    def _expire_if_needed_locked(self) -> None:
        if self._vault is None or self._last_activity_at is None:
            return

        elapsed = self._monotonic_clock() - self._last_activity_at

        if elapsed >= self._inactivity_timeout_seconds:
            self._lock_locked()

    def _schedule_auto_lock_locked(self, *, delay_seconds: float) -> None:
        self._cancel_auto_lock_timer_locked()

        self._timer_generation += 1
        generation = self._timer_generation

        timer = threading.Timer(
            delay_seconds,
            self._on_auto_lock_timer,
            args=(generation,),
        )
        timer.daemon = True
        self._auto_lock_timer = timer
        timer.start()

    def _on_auto_lock_timer(self, generation: int) -> None:
        with self._lock:
            if (
                generation != self._timer_generation
                or self._vault is None
                or self._last_activity_at is None
            ):
                return

            elapsed = self._monotonic_clock() - self._last_activity_at
            remaining = self._inactivity_timeout_seconds - elapsed

            if remaining > 0:
                self._schedule_auto_lock_locked(
                    delay_seconds=remaining
                )
                return

            self._lock_locked()

    def _lock_locked(self) -> None:
        self._cancel_auto_lock_timer_locked()
        self._timer_generation += 1

        vault = self._vault
        self._vault = None
        self._profile_context = None
        self._last_activity_at = None

        if vault is not None:
            vault.close()

    def _cancel_auto_lock_timer_locked(self) -> None:
        if self._auto_lock_timer is not None:
            self._auto_lock_timer.cancel()
            self._auto_lock_timer = None
