from __future__ import annotations

import base64
import re
import secrets
from dataclasses import dataclass

from mnemonic import Mnemonic


RECOVERY_SECRET_LENGTH = 32
BASE64URL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

ENGLISH_BIP39 = Mnemonic("english")


class RecoveryKeyFormatError(ValueError):
    """Raised when BIP39 phrase or Base64url recovery code is invalid."""


@dataclass(frozen=True)
class RecoveryMaterial:
    """One-time user-facing representations of the same recovery secret."""

    secret: bytes
    bip39_phrase: str
    base64url_code: str


def generate_recovery_material() -> RecoveryMaterial:
    secret = secrets.token_bytes(RECOVERY_SECRET_LENGTH)
    phrase = ENGLISH_BIP39.to_mnemonic(secret)

    if not ENGLISH_BIP39.check(phrase):
        raise RuntimeError("Generated BIP39 phrase did not validate.")

    return RecoveryMaterial(
        secret=secret,
        bip39_phrase=phrase,
        base64url_code=recovery_secret_to_base64url(secret),
    )


def recovery_secret_to_base64url(secret: bytes) -> str:
    _validate_secret(secret)

    return (
        base64.urlsafe_b64encode(secret)
        .decode("ascii")
        .rstrip("=")
    )


def recovery_secret_from_bip39(phrase: str) -> bytes:
    if not isinstance(phrase, str):
        raise RecoveryKeyFormatError("Recovery phrase must be text.")

    normalized = " ".join(phrase.strip().split())

    if not ENGLISH_BIP39.check(normalized):
        raise RecoveryKeyFormatError(
            "Recovery phrase is not a valid English BIP39 phrase."
        )

    secret = bytes(ENGLISH_BIP39.to_entropy(normalized))
    _validate_secret(secret)

    return secret


def recovery_secret_from_base64url(code: str) -> bytes:
    if not isinstance(code, str):
        raise RecoveryKeyFormatError("Recovery code must be text.")

    normalized = code.strip()

    if not normalized or BASE64URL_PATTERN.fullmatch(normalized) is None:
        raise RecoveryKeyFormatError(
            "Recovery code is not valid Base64url text."
        )

    padding = "=" * (-len(normalized) % 4)

    try:
        secret = base64.b64decode(
            (normalized + padding).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except Exception as error:
        raise RecoveryKeyFormatError(
            "Recovery code could not be decoded."
        ) from error

    _validate_secret(secret)

    return secret


def _validate_secret(secret: bytes) -> None:
    if not isinstance(secret, bytes) or len(secret) != RECOVERY_SECRET_LENGTH:
        raise RecoveryKeyFormatError(
            "Recovery secret must contain exactly 32 bytes."
        )
