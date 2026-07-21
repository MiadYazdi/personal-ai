from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VAULT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class VaultKdfParams:
    algorithm: str = "argon2id"
    memory_cost: int = 128 * 1024
    iterations: int = 3
    lanes: int = 4
    output_length: int = 32
    salt_length: int = 16


@dataclass(frozen=True)
class VaultRecord:
    record_id: str
    record_type: str
    payload: dict[str, Any]
    created_at: str
