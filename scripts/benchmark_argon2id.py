from __future__ import annotations

import os
import platform
import time

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


TEST_PASSPHRASE = b"personal-ai-argon2id-benchmark-only"

CANDIDATES = [
    {
        "name": "Balanced",
        "memory_mib": 64,
        "memory_cost": 64 * 1024,
        "iterations": 1,
        "lanes": 4,
    },
    {
        "name": "Recommended",
        "memory_mib": 64,
        "memory_cost": 64 * 1024,
        "iterations": 3,
        "lanes": 4,
    },
    {
        "name": "Stronger",
        "memory_mib": 128,
        "memory_cost": 128 * 1024,
        "iterations": 3,
        "lanes": 4,
    },
]


def main() -> None:
    print("=== Argon2id local benchmark ===")
    print(f"Platform: {platform.platform()}")
    print("Test data: synthetic only")
    print("Output key length: 32 bytes")

    for candidate in CANDIDATES:
        salt = os.urandom(16)

        started = time.perf_counter()

        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=candidate["iterations"],
            lanes=candidate["lanes"],
            memory_cost=candidate["memory_cost"],
        )

        derived_key = kdf.derive(TEST_PASSPHRASE)
        elapsed = time.perf_counter() - started

        if len(derived_key) != 32:
            raise RuntimeError("Unexpected derived-key length.")

        print(
            f"{candidate['name']}: "
            f"memory={candidate['memory_mib']}MiB, "
            f"iterations={candidate['iterations']}, "
            f"lanes={candidate['lanes']}, "
            f"seconds={elapsed:.3f}"
        )

    print("SUCCESS: Argon2id benchmark completed.")


if __name__ == "__main__":
    main()
