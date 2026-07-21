from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app
from personal_ai.vault import VaultStore
from personal_ai.vault.session import VaultSessionManager


class VaultSessionManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.vault_path = (
            Path(self.temp_directory.name)
            / "vault"
            / "session-vault.sqlite3"
        )
        self.passphrase = "synthetic session passphrase"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _create_synthetic_vault(self) -> None:
        vault = VaultStore.create(self.vault_path, self.passphrase)
        vault.put_record(
            "profile",
            {
                "profile_name": "Synthetic Session User",
                "address_name": "Synthetic Alias",
            },
            record_id="synthetic-profile",
        )
        vault.close()

    def test_auto_lock_timer_releases_the_session(self) -> None:
        self._create_synthetic_vault()

        manager = VaultSessionManager(
            self.vault_path,
            inactivity_timeout_seconds=0.05,
        )

        try:
            unlocked = manager.unlock_with_passphrase(self.passphrase)
            self.assertEqual(unlocked.vault_state, "unlocked")

            deadline = time.monotonic() + 2.0
            while (
                manager.status().vault_state == "unlocked"
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)

            locked = manager.status()
            self.assertEqual(locked.vault_state, "locked")
            self.assertIsNone(locked.profile_context)
        finally:
            manager.close()

    def test_lock_can_close_a_session_from_a_different_thread(self) -> None:
        self._create_synthetic_vault()
        manager = VaultSessionManager(self.vault_path)
        manager.unlock_with_passphrase(self.passphrase)

        errors: list[BaseException] = []

        def lock_from_worker() -> None:
            try:
                manager.lock()
            except BaseException as error:
                errors.append(error)

        worker = threading.Thread(target=lock_from_worker)
        worker.start()
        worker.join(timeout=2.0)

        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(manager.status().vault_state, "locked")


class VaultSessionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        temp_root = Path(self.temp_directory.name)

        self.vault_path = temp_root / "vault" / "api-vault.sqlite3"
        self.preference_path = temp_root / "ui" / "preferences.json"
        self.passphrase = "synthetic API session passphrase"

        self.app = create_app(
            vault_path=self.vault_path,
            preference_path=self.preference_path,
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.vault_session_manager.close()
        self.client.close()
        self.temp_directory.cleanup()

    def _create_vault(
        self,
        *,
        create_recovery_key: bool = False,
    ) -> dict[str, object]:
        response = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic API Session User",
                "address_name": "Synthetic API Alias",
                "vault_passphrase": self.passphrase,
                "create_recovery_key": create_recovery_key,
            },
        )

        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_status_before_creation_and_unlock_without_vault(self) -> None:
        status = self.client.get("/api/v1/vault/status")

        self.assertEqual(status.status_code, 200)
        self.assertEqual(
            status.json()["vault_state"],
            "not_created",
        )
        self.assertFalse(status.json()["vault_configured"])
        self.assertIsNone(status.json()["profile_context"])

        unlock = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": self.passphrase,
            },
        )

        self.assertEqual(unlock.status_code, 409)
        self.assertNotIn(self.passphrase, unlock.text)

    def test_passphrase_unlock_status_and_manual_lock(self) -> None:
        self._create_vault()

        before = self.client.get("/api/v1/vault/status")
        self.assertEqual(before.status_code, 200)
        self.assertEqual(before.json()["vault_state"], "locked")
        self.assertIsNone(before.json()["profile_context"])

        unlock = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": self.passphrase,
            },
        )

        self.assertEqual(unlock.status_code, 200)
        body = unlock.json()
        self.assertEqual(body["vault_state"], "unlocked")
        self.assertEqual(
            body["profile_context"],
            {
                "profile_name": "Synthetic API Session User",
                "address_name": "Synthetic API Alias",
            },
        )
        self.assertEqual(body["inactivity_timeout_seconds"], 1800.0)
        self.assertNotIn(self.passphrase, unlock.text)

        dashboard_status = self.client.get("/api/v1/status")
        self.assertEqual(
            dashboard_status.json()["vault"]["state"],
            "unlocked",
        )

        onboarding_status = self.client.get(
            "/api/v1/onboarding/status"
        )
        self.assertEqual(
            onboarding_status.json()["vault_state"],
            "unlocked",
        )

        lock = self.client.post("/api/v1/vault/lock")
        self.assertEqual(lock.status_code, 200)
        self.assertEqual(lock.json()["vault_state"], "locked")
        self.assertIsNone(lock.json()["profile_context"])

        repeated_lock = self.client.post("/api/v1/vault/lock")
        self.assertEqual(repeated_lock.status_code, 200)
        self.assertEqual(repeated_lock.json()["vault_state"], "locked")

    def test_wrong_or_blank_passphrase_is_rejected_without_echo(self) -> None:
        self._create_vault()

        blank = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": "   ",
            },
        )
        self.assertEqual(blank.status_code, 422)

        wrong_passphrase = "incorrect synthetic passphrase"
        wrong = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": wrong_passphrase,
            },
        )

        self.assertEqual(wrong.status_code, 401)
        self.assertNotIn(wrong_passphrase, wrong.text)

        status = self.client.get("/api/v1/vault/status")
        self.assertEqual(status.json()["vault_state"], "locked")

    def test_bip39_and_base64url_recovery_unlock(self) -> None:
        creation = self._create_vault(create_recovery_key=True)

        bip39_unlock = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "recovery_bip39",
                "recovery_phrase": creation["recovery_phrase"],
            },
        )
        self.assertEqual(bip39_unlock.status_code, 200)
        self.assertEqual(
            bip39_unlock.json()["vault_state"],
            "unlocked",
        )

        self.client.post("/api/v1/vault/lock")

        base64_unlock = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "recovery_base64url",
                "recovery_base64url": creation["recovery_base64url"],
            },
        )
        self.assertEqual(base64_unlock.status_code, 200)
        self.assertEqual(
            base64_unlock.json()["vault_state"],
            "unlocked",
        )

        self.assertNotIn(
            creation["recovery_base64url"],
            base64_unlock.text,
        )

    def test_second_unlock_is_rejected(self) -> None:
        self._create_vault()

        first_unlock = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": self.passphrase,
            },
        )
        self.assertEqual(first_unlock.status_code, 200)

        second_unlock = self.client.post(
            "/api/v1/vault/unlock",
            json={
                "method": "passphrase",
                "passphrase": self.passphrase,
            },
        )
        self.assertEqual(second_unlock.status_code, 409)
        self.assertNotIn(self.passphrase, second_unlock.text)
