from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personal_ai.onboarding import (
    OnboardingConflictError,
    OnboardingService,
    OnboardingValidationError,
)
from personal_ai.vault import VaultStore


class OnboardingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.vault_path = (
            Path(self.temp_directory.name)
            / "onboarding"
            / "synthetic-vault.sqlite3"
        )
        self.service = OnboardingService(self.vault_path)
        self.passphrase = "synthetic onboarding passphrase"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_status_before_and_after_vault_creation(self) -> None:
        before = self.service.status()
        self.assertFalse(before.vault_configured)
        self.assertEqual(before.vault_state, "not_created")

        result = self.service.create_local_vault(
            profile_name="Synthetic Test User",
            address_name=None,
            vault_passphrase=self.passphrase,
            create_recovery_key=False,
        )

        self.assertTrue(result.vault_created)
        self.assertEqual(result.address_name, "Synthetic Test User")
        self.assertFalse(result.recovery_key_created)
        self.assertIsNone(result.recovery_material)

        after = self.service.status()
        self.assertTrue(after.vault_configured)
        self.assertEqual(after.vault_state, "locked")

        vault = VaultStore.open(self.vault_path, self.passphrase)
        profile = vault.get_record(result.profile_id)
        vault.close()

        self.assertEqual(profile.record_type, "profile")
        self.assertEqual(
            profile.payload["profile_name"],
            "Synthetic Test User",
        )
        self.assertEqual(
            profile.payload["address_name"],
            "Synthetic Test User",
        )

    def test_custom_address_name_and_recovery_material(self) -> None:
        result = self.service.create_local_vault(
            profile_name="Synthetic Legal Name",
            address_name="Synthetic Address Name",
            vault_passphrase=self.passphrase,
            create_recovery_key=True,
        )

        self.assertTrue(result.recovery_key_created)
        self.assertIsNotNone(result.recovery_material)
        assert result.recovery_material is not None

        self.assertEqual(
            len(result.recovery_material.bip39_phrase.split()),
            24,
        )
        self.assertTrue(result.recovery_material.base64url_code)

    def test_blank_input_is_rejected(self) -> None:
        with self.assertRaises(OnboardingValidationError):
            self.service.create_local_vault(
                profile_name="   ",
                address_name=None,
                vault_passphrase=self.passphrase,
                create_recovery_key=False,
            )

        with self.assertRaises(OnboardingValidationError):
            self.service.create_local_vault(
                profile_name="Synthetic User",
                address_name=None,
                vault_passphrase="   ",
                create_recovery_key=False,
            )

    def test_duplicate_vault_is_rejected(self) -> None:
        self.service.create_local_vault(
            profile_name="Synthetic User",
            address_name=None,
            vault_passphrase=self.passphrase,
            create_recovery_key=False,
        )

        with self.assertRaises(OnboardingConflictError):
            self.service.create_local_vault(
                profile_name="Another Synthetic User",
                address_name=None,
                vault_passphrase=self.passphrase,
                create_recovery_key=False,
            )
