from __future__ import annotations

import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

from .models import VaultKdfParams


class VaultCryptoError(Exception):
    """Base error for Vault cryptographic operations."""


class VaultIntegrityError(VaultCryptoError):
    """Raised when authenticated encrypted data cannot be verified."""


class VaultUnlockError(VaultCryptoError):
    """Raised when a Vault cannot be unlocked."""


def _validate_aes256_key(key: bytes, label: str) -> None:
    if not isinstance(key, bytes) or len(key) != 32:
        raise ValueError(f"{label} must be exactly 32 bytes.")


def derive_passphrase_key(
    passphrase: str,
    salt: bytes,
    params: VaultKdfParams,
) -> bytes:
    if not isinstance(passphrase, str):
        raise TypeError("Vault passphrase must be a string.")

    if not isinstance(salt, bytes) or len(salt) < params.salt_length:
        raise ValueError("Vault salt is invalid.")

    if params.algorithm != "argon2id":
        raise ValueError(f"Unsupported Vault KDF: {params.algorithm}")

    kdf = Argon2id(
        salt=salt,
        length=params.output_length,
        iterations=params.iterations,
        lanes=params.lanes,
        memory_cost=params.memory_cost,
    )

    return kdf.derive(passphrase.encode("utf-8"))


def generate_vault_key() -> bytes:
    return os.urandom(32)


def generate_recovery_key() -> bytes:
    return os.urandom(32)


def encrypt_aead(
    key: bytes,
    plaintext: bytes,
    associated_data: bytes,
) -> tuple[bytes, bytes]:
    _validate_aes256_key(key, "AES-256-GCM key")

    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext


def decrypt_aead(
    key: bytes,
    nonce: bytes,
    ciphertext: bytes,
    associated_data: bytes,
) -> bytes:
    _validate_aes256_key(key, "AES-256-GCM key")

    try:
        return AESGCM(key).decrypt(nonce, ciphertext, associated_data)
    except InvalidTag as error:
        raise VaultIntegrityError(
            "Vault data could not be authenticated or decrypted."
        ) from error
