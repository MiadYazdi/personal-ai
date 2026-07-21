from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from personal_ai.vault import (
    VaultIntegrityError,
    VaultStore,
    VaultUnlockError,
    generate_recovery_key,
)


class VaultStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.vault_path = (
            Path(self.temp_directory.name)
            / "vault-data"
            / "synthetic-vault.sqlite3"
        )
        self.passphrase = "synthetic test passphrase only"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_create_write_read_and_reopen(self) -> None:
        vault = VaultStore.create(self.vault_path, self.passphrase)

        record_id = vault.put_record(
            "profile",
            {
                "display_name": "Synthetic Test User",
                "preferred_languages": ["fa", "en"],
            },
        )

        record = vault.get_record(record_id)

        self.assertEqual(record.record_type, "profile")
        self.assertEqual(record.payload["display_name"], "Synthetic Test User")
        self.assertEqual(record.payload["preferred_languages"], ["fa", "en"])

        raw_database = self.vault_path.read_bytes()
        self.assertNotIn(b"Synthetic Test User", raw_database)
        self.assertNotIn(b"preferred_languages", raw_database)

        vault.close()

        reopened_vault = VaultStore.open(self.vault_path, self.passphrase)
        reopened_record = reopened_vault.get_record(record_id)

        self.assertEqual(
            reopened_record.payload["display_name"],
            "Synthetic Test User",
        )

        reopened_vault.close()

    def test_wrong_passphrase_is_rejected(self) -> None:
        vault = VaultStore.create(self.vault_path, self.passphrase)
        vault.close()

        with self.assertRaises(VaultUnlockError):
            VaultStore.open(self.vault_path, "incorrect synthetic passphrase")

    def test_optional_recovery_key_unlocks_vault(self) -> None:
        recovery_key = generate_recovery_key()

        vault = VaultStore.create(
            self.vault_path,
            self.passphrase,
            recovery_key=recovery_key,
        )

        record_id = vault.put_record(
            "memory",
            {"fact": "This is synthetic test data only."},
        )

        vault.close()

        recovered_vault = VaultStore.open_with_recovery(
            self.vault_path,
            recovery_key,
        )

        record = recovered_vault.get_record(record_id)

        self.assertEqual(
            record.payload["fact"],
            "This is synthetic test data only.",
        )

        recovered_vault.close()

        with self.assertRaises(VaultUnlockError):
            VaultStore.open_with_recovery(
                self.vault_path,
                os.urandom(32),
            )

    def test_tampered_ciphertext_is_rejected(self) -> None:
        vault = VaultStore.create(self.vault_path, self.passphrase)

        record_id = vault.put_record(
            "conversation",
            {"message": "Synthetic encrypted test message."},
        )

        vault.close()

        connection = sqlite3.connect(self.vault_path)

        ciphertext = connection.execute(
            """
            SELECT ciphertext
            FROM vault_records
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()[0]

        tampered = bytearray(ciphertext)
        tampered[-1] ^= 1

        connection.execute(
            """
            UPDATE vault_records
            SET ciphertext = ?
            WHERE record_id = ?
            """,
            (bytes(tampered), record_id),
        )

        connection.commit()
        connection.close()

        reopened_vault = VaultStore.open(self.vault_path, self.passphrase)

        with self.assertRaises(VaultIntegrityError):
            reopened_vault.get_record(record_id)

        reopened_vault.close()

    @unittest.skipUnless(os.name == "posix", "POSIX permission test")
    def test_posix_file_permissions(self) -> None:
        vault = VaultStore.create(self.vault_path, self.passphrase)
        vault.close()

        directory_mode = self.vault_path.parent.stat().st_mode & 0o777
        database_mode = self.vault_path.stat().st_mode & 0o777

        self.assertEqual(directory_mode, 0o700)
        self.assertEqual(database_mode, 0o600)


if __name__ == "__main__":
    unittest.main()
