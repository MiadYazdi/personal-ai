from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from personal_ai.vault import (
    RecoveryMaterial,
    VaultStore,
    generate_recovery_material,
)


class OnboardingError(Exception):
    """Base onboarding error."""


class OnboardingValidationError(OnboardingError):
    """Raised when user onboarding input is invalid."""


class OnboardingConflictError(OnboardingError):
    """Raised when onboarding tries to create an existing Vault."""


@dataclass(frozen=True)
class OnboardingStatus:
    vault_configured: bool
    vault_state: str
    profile_available: bool

    def to_dict(self) -> dict[str, bool | str]:
        return {
            "vault_configured": self.vault_configured,
            "vault_state": self.vault_state,
            "profile_available": self.profile_available,
        }


@dataclass(frozen=True)
class OnboardingResult:
    vault_created: bool
    profile_id: str
    address_name: str
    recovery_key_created: bool
    recovery_material: RecoveryMaterial | None

    def to_api_dict(self) -> dict[str, object]:
        response: dict[str, object] = {
            "vault_created": self.vault_created,
            "profile_id": self.profile_id,
            "address_name": self.address_name,
            "recovery_key_created": self.recovery_key_created,
        }

        if self.recovery_material is not None:
            response["recovery_phrase"] = (
                self.recovery_material.bip39_phrase
            )
            response["recovery_base64url"] = (
                self.recovery_material.base64url_code
            )

        return response


class OnboardingService:
    """Creates local encrypted Vaults and their first profile record."""

    def __init__(self, vault_path: str | Path) -> None:
        self.vault_path = Path(vault_path)

    def status(self) -> OnboardingStatus:
        configured = self.vault_path.is_file()

        return OnboardingStatus(
            vault_configured=configured,
            vault_state="locked" if configured else "not_created",
            profile_available=configured,
        )

    def create_local_vault(
        self,
        *,
        profile_name: str,
        address_name: str | None,
        vault_passphrase: str,
        create_recovery_key: bool,
    ) -> OnboardingResult:
        normalized_profile_name = self._validate_profile_name(profile_name)
        normalized_address_name = self._normalize_address_name(
            address_name,
            normalized_profile_name,
        )
        self._validate_passphrase(vault_passphrase)

        if self.vault_path.exists():
            raise OnboardingConflictError(
                "A local Vault is already configured."
            )

        recovery_material = (
            generate_recovery_material()
            if create_recovery_key
            else None
        )

        vault: VaultStore | None = None

        try:
            vault = VaultStore.create(
                self.vault_path,
                vault_passphrase,
                recovery_key=(
                    recovery_material.secret
                    if recovery_material is not None
                    else None
                ),
            )

            profile_id = uuid.uuid4().hex
            timestamp = datetime.now(UTC).isoformat()

            vault.put_record(
                "profile",
                {
                    "profile_id": profile_id,
                    "profile_name": normalized_profile_name,
                    "address_name": normalized_address_name,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                },
                record_id=profile_id,
            )

            return OnboardingResult(
                vault_created=True,
                profile_id=profile_id,
                address_name=normalized_address_name,
                recovery_key_created=recovery_material is not None,
                recovery_material=recovery_material,
            )

        except Exception:
            if vault is not None:
                vault.close()

            self._remove_partial_vault_files()
            raise

        finally:
            if vault is not None:
                vault.close()

    def _remove_partial_vault_files(self) -> None:
        for path in (
            self.vault_path,
            Path(f"{self.vault_path}-wal"),
            Path(f"{self.vault_path}-shm"),
            Path(f"{self.vault_path}-journal"),
        ):
            if path.exists():
                path.unlink()

    @staticmethod
    def _validate_profile_name(profile_name: str) -> str:
        if not isinstance(profile_name, str):
            raise OnboardingValidationError(
                "Profile Name must be text."
            )

        normalized = profile_name.strip()

        if not normalized:
            raise OnboardingValidationError(
                "Profile Name cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_address_name(
        address_name: str | None,
        profile_name: str,
    ) -> str:
        if address_name is None:
            return profile_name

        if not isinstance(address_name, str):
            raise OnboardingValidationError(
                "Address Name must be text."
            )

        normalized = address_name.strip()
        return normalized or profile_name

    @staticmethod
    def _validate_passphrase(passphrase: str) -> None:
        if not isinstance(passphrase, str):
            raise OnboardingValidationError(
                "Vault passphrase must be text."
            )

        if not passphrase.strip():
            raise OnboardingValidationError(
                "Vault passphrase cannot be empty."
            )
