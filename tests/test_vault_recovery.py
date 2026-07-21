from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personal_ai.vault import (
    RecoveryKeyFormatError,
    VaultStore,
    generate_recovery_material,
    recovery_secret_from_base64url,
    recovery_secret_from_bip39,
)


class VaultRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.vault_path = (
            Path(self.temp_directory.name)
            / "recovery-test"
            / "synthetic-vault.sqlite3"
        )
        self.passphrase = "synthetic vault recovery test only"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_bip39_and_base64url_represent_same_secret(self) -> None:
        material = generate_recovery_material()

        self.assertEqual(len(material.secret), 32)
        self.assertEqual(len(material.bip39_phrase.split()), 24)
        self.assertEqual(
            recovery_secret_from_bip39(material.bip39_phrase),
            material.secret,
        )
        self.assertEqual(
            recovery_secret_from_base64url(material.base64url_code),
            material.secret,
        )

    def test_invalid_recovery_material_is_rejected(self) -> None:
        with self.assertRaises(RecoveryKeyFormatError):
            recovery_secret_from_bip39("not a valid phrase")

        with self.assertRaises(RecoveryKeyFormatError):
            recovery_secret_from_base64url("not valid base64url!")

    def test_vault_unlocks_with_phrase_and_base64url(self) -> None:
        material = generate_recovery_material()

        vault = VaultStore.create(
            self.vault_path,
            self.passphrase,
            recovery_key=material.secret,
        )

        record_id = vault.put_record(
            "profile",
            {"display_name": "Synthetic Recovery Test User"},
        )
        vault.close()

        phrase_vault = VaultStore.open_with_recovery_bip39(
            self.vault_path,
            material.bip39_phrase,
        )
        phrase_record = phrase_vault.get_record(record_id)
        self.assertEqual(
            phrase_record.payload["display_name"],
            "Synthetic Recovery Test User",
        )
        phrase_vault.close()

        code_vault = VaultStore.open_with_recovery_base64url(
            self.vault_path,
            material.base64url_code,
        )
        code_record = code_vault.get_record(record_id)
        self.assertEqual(
            code_record.payload["display_name"],
            "Synthetic Recovery Test User",
        )
        code_vault.close()


if __name__ == "__main__":
    unittest.main()
