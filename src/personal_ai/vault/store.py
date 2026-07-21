from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .crypto import (
    VaultIntegrityError,
    VaultUnlockError,
    decrypt_aead,
    derive_passphrase_key,
    encrypt_aead,
    generate_recovery_key,
    generate_vault_key,
)
from .models import VAULT_SCHEMA_VERSION, VaultKdfParams, VaultRecord
from .recovery import (
    recovery_secret_from_base64url,
    recovery_secret_from_bip39,
)


HEADER_SCHEMA = """
CREATE TABLE IF NOT EXISTS vault_header (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    vault_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    kdf_algorithm TEXT NOT NULL,
    kdf_salt BLOB NOT NULL,
    kdf_memory_cost INTEGER NOT NULL,
    kdf_iterations INTEGER NOT NULL,
    kdf_lanes INTEGER NOT NULL,
    kdf_output_length INTEGER NOT NULL,
    passphrase_wrap_nonce BLOB NOT NULL,
    passphrase_wrapped_key BLOB NOT NULL,
    recovery_wrap_nonce BLOB,
    recovery_wrapped_key BLOB
)
"""

RECORD_SCHEMA = """
CREATE TABLE IF NOT EXISTS vault_records (
    record_id TEXT PRIMARY KEY,
    schema_version INTEGER NOT NULL,
    nonce BLOB NOT NULL,
    ciphertext BLOB NOT NULL
)
"""


class VaultStore:
    """SQLite storage for encrypted Personal AI Vault records."""

    def __init__(
        self,
        path: Path,
        connection: sqlite3.Connection,
        vault_id: str,
        vault_key: bytes,
        kdf_params: VaultKdfParams,
    ) -> None:
        self._path = path
        self._connection = connection
        self._vault_id = vault_id
        self._vault_key = vault_key
        self._kdf_params = kdf_params

    @property
    def path(self) -> Path:
        return self._path

    @property
    def vault_id(self) -> str:
        return self._vault_id

    @property
    def kdf_params(self) -> VaultKdfParams:
        return self._kdf_params

    @classmethod
    def create(
        cls,
        path: str | Path,
        passphrase: str,
        *,
        recovery_key: bytes | None = None,
        kdf_params: VaultKdfParams | None = None,
    ) -> "VaultStore":
        db_path = Path(path)

        if db_path.exists():
            raise FileExistsError(f"Vault database already exists: {db_path}")

        params = kdf_params or VaultKdfParams()
        cls._prepare_directory(db_path.parent)

        connection = cls._connect(db_path)

        try:
            connection.execute(HEADER_SCHEMA)
            connection.execute(RECORD_SCHEMA)

            vault_id = uuid.uuid4().hex
            created_at = cls._utc_now()
            salt = os.urandom(params.salt_length)

            passphrase_key = derive_passphrase_key(passphrase, salt, params)
            vault_key = generate_vault_key()

            passphrase_nonce, passphrase_wrapped_key = encrypt_aead(
                passphrase_key,
                vault_key,
                cls._wrap_aad(vault_id, "passphrase"),
            )

            recovery_nonce: bytes | None = None
            recovery_wrapped_key: bytes | None = None

            if recovery_key is not None:
                recovery_nonce, recovery_wrapped_key = encrypt_aead(
                    recovery_key,
                    vault_key,
                    cls._wrap_aad(vault_id, "recovery"),
                )

            connection.execute(
                """
                INSERT INTO vault_header (
                    singleton,
                    vault_id,
                    schema_version,
                    created_at,
                    kdf_algorithm,
                    kdf_salt,
                    kdf_memory_cost,
                    kdf_iterations,
                    kdf_lanes,
                    kdf_output_length,
                    passphrase_wrap_nonce,
                    passphrase_wrapped_key,
                    recovery_wrap_nonce,
                    recovery_wrapped_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    vault_id,
                    VAULT_SCHEMA_VERSION,
                    created_at,
                    params.algorithm,
                    salt,
                    params.memory_cost,
                    params.iterations,
                    params.lanes,
                    params.output_length,
                    passphrase_nonce,
                    passphrase_wrapped_key,
                    recovery_nonce,
                    recovery_wrapped_key,
                ),
            )

            connection.commit()
            cls._restrict_permissions(db_path)

            return cls(
                path=db_path,
                connection=connection,
                vault_id=vault_id,
                vault_key=vault_key,
                kdf_params=params,
            )

        except Exception:
            connection.close()
            raise

    @classmethod
    def open(cls, path: str | Path, passphrase: str) -> "VaultStore":
        db_path = Path(path)
        connection = cls._connect(db_path)

        try:
            header = cls._read_header(connection)
            params = cls._params_from_header(header)

            passphrase_key = derive_passphrase_key(
                passphrase,
                bytes(header["kdf_salt"]),
                params,
            )

            vault_key = decrypt_aead(
                passphrase_key,
                bytes(header["passphrase_wrap_nonce"]),
                bytes(header["passphrase_wrapped_key"]),
                cls._wrap_aad(header["vault_id"], "passphrase"),
            )

            return cls(
                path=db_path,
                connection=connection,
                vault_id=header["vault_id"],
                vault_key=vault_key,
                kdf_params=params,
            )

        except (VaultIntegrityError, ValueError, KeyError) as error:
            connection.close()
            raise VaultUnlockError(
                "Vault could not be unlocked with this passphrase."
            ) from error

    @classmethod
    def open_with_recovery(
        cls,
        path: str | Path,
        recovery_key: bytes,
    ) -> "VaultStore":
        db_path = Path(path)
        connection = cls._connect(db_path)

        try:
            header = cls._read_header(connection)

            if (
                header["recovery_wrap_nonce"] is None
                or header["recovery_wrapped_key"] is None
            ):
                raise VaultUnlockError("This Vault has no Recovery Key path.")

            vault_key = decrypt_aead(
                recovery_key,
                bytes(header["recovery_wrap_nonce"]),
                bytes(header["recovery_wrapped_key"]),
                cls._wrap_aad(header["vault_id"], "recovery"),
            )

            return cls(
                path=db_path,
                connection=connection,
                vault_id=header["vault_id"],
                vault_key=vault_key,
                kdf_params=cls._params_from_header(header),
            )

        except VaultUnlockError:
            connection.close()
            raise
        except (VaultIntegrityError, ValueError, KeyError) as error:
            connection.close()
            raise VaultUnlockError(
                "Vault could not be unlocked with this Recovery Key."
            ) from error

    @classmethod
    def open_with_recovery_bip39(
        cls,
        path: str | Path,
        phrase: str,
    ) -> "VaultStore":
        return cls.open_with_recovery(
            path,
            recovery_secret_from_bip39(phrase),
        )

    @classmethod
    def open_with_recovery_base64url(
        cls,
        path: str | Path,
        code: str,
    ) -> "VaultStore":
        return cls.open_with_recovery(
            path,
            recovery_secret_from_base64url(code),
        )

    def put_record(
        self,
        record_type: str,
        payload: dict[str, Any],
        *,
        record_id: str | None = None,
    ) -> str:
        self._ensure_open()

        if not isinstance(record_type, str) or not record_type:
            raise ValueError("record_type must be a non-empty string.")

        if not isinstance(payload, dict):
            raise TypeError("Vault payload must be a dictionary.")

        if record_id is None:
            record_id = uuid.uuid4().hex
        elif not isinstance(record_id, str) or not record_id:
            raise ValueError("record_id must be a non-empty string.")

        encrypted_payload = {
            "record_type": record_type,
            "payload": payload,
            "created_at": self._utc_now(),
        }

        plaintext = json.dumps(
            encrypted_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        nonce, ciphertext = encrypt_aead(
            self._vault_key,
            plaintext,
            self._record_aad(record_id),
        )

        self._connection.execute(
            """
            INSERT INTO vault_records (
                record_id,
                schema_version,
                nonce,
                ciphertext
            ) VALUES (?, ?, ?, ?)
            """,
            (
                record_id,
                VAULT_SCHEMA_VERSION,
                nonce,
                ciphertext,
            ),
        )

        self._connection.commit()
        self._restrict_permissions(self._path)

        return record_id

    def get_record(self, record_id: str) -> VaultRecord:
        self._ensure_open()

        row = self._connection.execute(
            """
            SELECT record_id, schema_version, nonce, ciphertext
            FROM vault_records
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()

        if row is None:
            raise KeyError(f"Vault record does not exist: {record_id}")

        plaintext = decrypt_aead(
            self._vault_key,
            bytes(row["nonce"]),
            bytes(row["ciphertext"]),
            self._record_aad(row["record_id"]),
        )

        decoded = json.loads(plaintext.decode("utf-8"))

        return VaultRecord(
            record_id=row["record_id"],
            record_type=decoded["record_type"],
            payload=decoded["payload"],
            created_at=decoded["created_at"],
        )

    def find_first_record_by_type(
        self,
        record_type: str,
    ) -> VaultRecord | None:
        """Return the first encrypted record with the requested type."""

        self._ensure_open()

        if not isinstance(record_type, str) or not record_type:
            raise ValueError("record_type must be a non-empty string.")

        rows = self._connection.execute(
            """
            SELECT record_id
            FROM vault_records
            ORDER BY rowid ASC
            """
        ).fetchall()

        for row in rows:
            record = self.get_record(str(row["record_id"]))
            if record.record_type == record_type:
                return record

        return None

    def find_records_by_type(
        self,
        record_type: str,
    ) -> list[VaultRecord]:
        """Decrypt and return records matching a private record type."""

        self._ensure_open()

        if not isinstance(record_type, str) or not record_type:
            raise ValueError("record_type must be a non-empty string.")

        rows = self._connection.execute(
            """
            SELECT record_id
            FROM vault_records
            ORDER BY rowid ASC
            """
        ).fetchall()

        matches: list[VaultRecord] = []
        for row in rows:
            record = self.get_record(str(row["record_id"]))
            if record.record_type == record_type:
                matches.append(record)

        return matches

    def replace_record(
        self,
        record_type: str,
        payload: dict[str, Any],
        *,
        record_id: str,
    ) -> None:
        """Authenticated encrypted replacement using a fresh AES-GCM nonce."""

        self._ensure_open()

        if not isinstance(record_type, str) or not record_type:
            raise ValueError("record_type must be a non-empty string.")
        if not isinstance(payload, dict):
            raise TypeError("Vault payload must be a dictionary.")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("record_id must be a non-empty string.")

        encrypted_payload = {
            "record_type": record_type,
            "payload": payload,
            "created_at": self._utc_now(),
        }
        plaintext = json.dumps(
            encrypted_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        nonce, ciphertext = encrypt_aead(
            self._vault_key,
            plaintext,
            self._record_aad(record_id),
        )

        self._connection.execute(
            """
            INSERT INTO vault_records (
                record_id,
                schema_version,
                nonce,
                ciphertext
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                schema_version = excluded.schema_version,
                nonce = excluded.nonce,
                ciphertext = excluded.ciphertext
            """,
            (record_id, VAULT_SCHEMA_VERSION, nonce, ciphertext),
        )
        self._connection.commit()
        self._restrict_permissions(self._path)

    def delete_record(self, record_id: str) -> bool:
        """Delete one encrypted record by its non-private random record ID."""

        self._ensure_open()

        if not isinstance(record_id, str) or not record_id:
            raise ValueError("record_id must be a non-empty string.")

        cursor = self._connection.execute(
            "DELETE FROM vault_records WHERE record_id = ?",
            (record_id,),
        )
        self._connection.commit()
        self._restrict_permissions(self._path)
        return cursor.rowcount > 0

    def close(self) -> None:
        connection = self._connection
        self._connection = None

        try:
            if connection is not None:
                connection.close()
        finally:
            # Python cannot guarantee secure in-memory zeroization.
            # Removing this reference is only best-effort cleanup.
            self._vault_key = b""

    def __enter__(self) -> "VaultStore":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    @classmethod
    def _connect(cls, db_path: Path) -> sqlite3.Connection:
        # VaultSessionManager owns all cross-thread access with an RLock.
        # This permits FastAPI worker threads and the auto-lock timer to
        # close the same session connection safely.
        connection = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @classmethod
    def _prepare_directory(cls, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)

        if os.name == "posix":
            os.chmod(directory, 0o700)

    @classmethod
    def _restrict_permissions(cls, db_path: Path) -> None:
        if os.name != "posix":
            return

        for candidate in (
            db_path,
            Path(f"{db_path}-wal"),
            Path(f"{db_path}-shm"),
            Path(f"{db_path}-journal"),
        ):
            if candidate.exists():
                os.chmod(candidate, 0o600)

    @classmethod
    def _read_header(cls, connection: sqlite3.Connection) -> sqlite3.Row:
        header = connection.execute(
            "SELECT * FROM vault_header WHERE singleton = 1"
        ).fetchone()

        if header is None:
            raise VaultUnlockError("Vault header does not exist.")

        return header

    @classmethod
    def _params_from_header(cls, header: sqlite3.Row) -> VaultKdfParams:
        return VaultKdfParams(
            algorithm=header["kdf_algorithm"],
            memory_cost=header["kdf_memory_cost"],
            iterations=header["kdf_iterations"],
            lanes=header["kdf_lanes"],
            output_length=header["kdf_output_length"],
        )

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _wrap_aad(vault_id: str, wrap_type: str) -> bytes:
        return (
            f"personal-ai:vault-key-wrap:v1:{vault_id}:{wrap_type}"
        ).encode("utf-8")

    @staticmethod
    def _record_aad(record_id: str) -> bytes:
        return (
            f"personal-ai:vault-record:v{VAULT_SCHEMA_VERSION}:{record_id}"
        ).encode("utf-8")

    def _ensure_open(self) -> None:
        if self._connection is None or not self._vault_key:
            raise RuntimeError("Vault is closed.")
