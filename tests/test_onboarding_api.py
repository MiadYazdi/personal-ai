from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_ai.api.app import create_app
from personal_ai.vault import VaultStore


class OnboardingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        temp_root = Path(self.temp_directory.name)

        self.vault_path = temp_root / "vault" / "api-vault.sqlite3"
        self.preference_path = temp_root / "ui" / "preferences.json"

        self.client = TestClient(
            create_app(
                vault_path=self.vault_path,
                preference_path=self.preference_path,
            )
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_status_has_no_secret_fields_before_onboarding(self) -> None:
        response = self.client.get("/api/v1/onboarding/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "vault_configured": False,
                "vault_state": "not_created",
                "profile_available": False,
            },
        )

    def test_create_vault_without_recovery(self) -> None:
        response = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic API User",
                "address_name": "",
                "vault_passphrase": "synthetic api passphrase",
                "create_recovery_key": False,
            },
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertTrue(body["vault_created"])
        self.assertFalse(body["recovery_key_created"])
        self.assertEqual(body["address_name"], "Synthetic API User")
        self.assertNotIn("recovery_phrase", body)
        self.assertNotIn("recovery_base64url", body)

        status_response = self.client.get("/api/v1/onboarding/status")
        self.assertEqual(status_response.status_code, 200)
        self.assertTrue(status_response.json()["vault_configured"])
        self.assertNotIn("recovery_phrase", status_response.json())
        self.assertNotIn("recovery_base64url", status_response.json())

    def test_create_vault_with_recovery(self) -> None:
        response = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic API User",
                "address_name": "Synthetic Alias",
                "vault_passphrase": "synthetic api passphrase",
                "create_recovery_key": True,
            },
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertTrue(body["recovery_key_created"])
        self.assertEqual(len(body["recovery_phrase"].split()), 24)
        self.assertTrue(body["recovery_base64url"])

    def test_blank_values_and_duplicate_vault_are_rejected(self) -> None:
        blank_name = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "   ",
                "address_name": None,
                "vault_passphrase": "synthetic api passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(blank_name.status_code, 422)

        blank_passphrase = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic API User",
                "address_name": None,
                "vault_passphrase": "   ",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(blank_passphrase.status_code, 422)

        first = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic API User",
                "address_name": None,
                "vault_passphrase": "synthetic api passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(first.status_code, 200)

        duplicate = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Another Synthetic User",
                "address_name": None,
                "vault_passphrase": "another synthetic passphrase",
                "create_recovery_key": False,
            },
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_created_profile_is_encrypted_vault_record(self) -> None:
        response = self.client.post(
            "/api/v1/onboarding/local-vault",
            json={
                "profile_name": "Synthetic Profile",
                "address_name": "Synthetic Alias",
                "vault_passphrase": "synthetic api passphrase",
                "create_recovery_key": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        profile_id = response.json()["profile_id"]

        vault = VaultStore.open(
            self.vault_path,
            "synthetic api passphrase",
        )
        profile = vault.get_record(profile_id)
        vault.close()

        self.assertEqual(profile.record_type, "profile")
        self.assertEqual(
            profile.payload["address_name"],
            "Synthetic Alias",
        )
