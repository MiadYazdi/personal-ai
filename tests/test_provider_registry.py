from __future__ import annotations

import unittest

from personal_ai.provider_registry import (
    ProviderRegistry,
    ProviderRegistryError,
)


class ProviderRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ProviderRegistry()

    def test_registry_never_exposes_secret_and_preview_is_offline(self) -> None:
        providers = self.registry.list_providers()
        google = next(
            item for item in providers if item["provider_id"] == "google_gemini"
        )

        self.assertFalse(google["secret_exposed"])
        self.assertNotIn("credential_value", google)

        preview = self.registry.preview_access(
            provider_id="google_gemini",
            capability="google_search_grounding",
            target_description="Google Search Grounding",
            outbound_summary="Synthetic provider access preview only.",
            data_categories=["synthetic_text"],
            estimated_bytes=128,
        )

        self.assertFalse(preview.to_dict()["network_execution_enabled"])
        self.assertTrue(preview.to_dict()["requires_fresh_confirmation"])

    def test_unsupported_provider_capability_is_rejected(self) -> None:
        with self.assertRaises(ProviderRegistryError):
            self.registry.preview_access(
                provider_id="direct_web",
                capability="model_inference",
                target_description="Invalid combination",
                outbound_summary="Synthetic only.",
                data_categories=[],
                estimated_bytes=0,
            )


if __name__ == "__main__":
    unittest.main()
