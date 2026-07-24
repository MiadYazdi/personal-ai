from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass

MAX_SUMMARY_CHARS = 4_000
MAX_TARGET_CHARS = 500
MAX_ESTIMATED_BYTES = 16 * 1024 * 1024

ALLOWED_CAPABILITIES = {
    "google_search_grounding",
    "model_inference",
    "web_fetch",
    "code_evolution_proposal",
    "source_update_proposal",
}


class ProviderRegistryError(ValueError):
    """Raised when a provider access preview is invalid."""


@dataclass(frozen=True)
class OnlineProviderDefinition:
    provider_id: str
    display_name: str
    credential_environment: str | None
    capabilities: tuple[str, ...]
    adapter_status: str
    notes: str

    def to_dict(self) -> dict[str, object]:
        configured = bool(
            self.credential_environment
            and os.environ.get(self.credential_environment)
        )
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "credential_configured": configured,
            "credential_environment": self.credential_environment,
            "capabilities": list(self.capabilities),
            "adapter_status": self.adapter_status,
            "notes": self.notes,
            "secret_exposed": False,
        }


@dataclass(frozen=True)
class ProviderAccessPreview:
    provider: OnlineProviderDefinition
    capability: str
    target_description: str
    outbound_summary_sha256: str
    data_categories: tuple[str, ...]
    estimated_bytes: int
    request_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider.to_dict(),
            "capability": self.capability,
            "target_description": self.target_description,
            "outbound_summary_sha256": self.outbound_summary_sha256,
            "data_categories": list(self.data_categories),
            "estimated_bytes": self.estimated_bytes,
            "request_sha256": self.request_sha256,
            "network_execution_enabled": False,
            "requires_fresh_confirmation": True,
            "requires_vault_unlock": True,
            "cost_review_required": True,
            "automatic_execution": False,
        }


class ProviderRegistry:
    """Local provider catalogue and consent preview; never connects to a provider."""

    def __init__(
        self,
        providers: tuple[OnlineProviderDefinition, ...] | None = None,
    ) -> None:
        self._providers = {
            provider.provider_id: provider
            for provider in (providers or self._default_providers())
        }

    def list_providers(self) -> list[dict[str, object]]:
        return [
            provider.to_dict()
            for provider in sorted(
                self._providers.values(),
                key=lambda item: item.display_name.lower(),
            )
        ]

    def preview_access(
        self,
        *,
        provider_id: str,
        capability: str,
        target_description: str,
        outbound_summary: str,
        data_categories: list[str],
        estimated_bytes: int,
    ) -> ProviderAccessPreview:
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderRegistryError("Selected provider is unavailable.")

        if (
            capability not in ALLOWED_CAPABILITIES
            or capability not in provider.capabilities
        ):
            raise ProviderRegistryError(
                "Selected provider does not support this capability."
            )

        if (
            not isinstance(target_description, str)
            or not target_description.strip()
            or len(target_description) > MAX_TARGET_CHARS
        ):
            raise ProviderRegistryError("Target description is invalid.")

        if (
            not isinstance(outbound_summary, str)
            or not outbound_summary.strip()
            or len(outbound_summary) > MAX_SUMMARY_CHARS
        ):
            raise ProviderRegistryError("Outbound summary is invalid.")

        if (
            not isinstance(estimated_bytes, int)
            or estimated_bytes < 0
            or estimated_bytes > MAX_ESTIMATED_BYTES
        ):
            raise ProviderRegistryError("Estimated outbound size is invalid.")

        categories = tuple(
            value.strip().lower()
            for value in data_categories
            if isinstance(value, str) and value.strip()
        )
        if len(categories) > 12 or len(categories) != len(set(categories)):
            raise ProviderRegistryError("Data categories are invalid.")

        summary_sha256 = hashlib.sha256(
            outbound_summary.strip().encode("utf-8")
        ).hexdigest()
        digest = hashlib.sha256(
            json.dumps(
                {
                    "provider_id": provider.provider_id,
                    "capability": capability,
                    "target_description": target_description.strip(),
                    "outbound_summary_sha256": summary_sha256,
                    "data_categories": categories,
                    "estimated_bytes": estimated_bytes,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return ProviderAccessPreview(
            provider=provider,
            capability=capability,
            target_description=target_description.strip(),
            outbound_summary_sha256=summary_sha256,
            data_categories=categories,
            estimated_bytes=estimated_bytes,
            request_sha256=digest,
        )

    @staticmethod
    def _default_providers() -> tuple[OnlineProviderDefinition, ...]:
        return (
            OnlineProviderDefinition(
                "google_gemini",
                "Google Gemini + Google Search",
                "PERSONAL_AI_GEMINI_API_KEY",
                (
                    "google_search_grounding",
                    "model_inference",
                    "code_evolution_proposal",
                    "source_update_proposal",
                ),
                "foundation_ready",
                "Official Google Grounding connector is implemented; execution stays off until confirmed.",
            ),
            OnlineProviderDefinition(
                "openai",
                "OpenAI",
                "PERSONAL_AI_OPENAI_API_KEY",
                (
                    "model_inference",
                    "code_evolution_proposal",
                    "source_update_proposal",
                ),
                "registry_only",
                "Provider adapter requires separate reviewed implementation.",
            ),
            OnlineProviderDefinition(
                "anthropic",
                "Anthropic",
                "PERSONAL_AI_ANTHROPIC_API_KEY",
                (
                    "model_inference",
                    "code_evolution_proposal",
                    "source_update_proposal",
                ),
                "registry_only",
                "Provider adapter requires separate reviewed implementation.",
            ),
            OnlineProviderDefinition(
                "xai",
                "xAI",
                "PERSONAL_AI_XAI_API_KEY",
                (
                    "model_inference",
                    "code_evolution_proposal",
                    "source_update_proposal",
                ),
                "registry_only",
                "Provider adapter requires separate reviewed implementation.",
            ),
            OnlineProviderDefinition(
                "openrouter",
                "OpenRouter",
                "PERSONAL_AI_OPENROUTER_API_KEY",
                (
                    "model_inference",
                    "code_evolution_proposal",
                    "source_update_proposal",
                ),
                "registry_only",
                "Provider adapter requires separate reviewed implementation.",
            ),
            OnlineProviderDefinition(
                "openai_compatible",
                "OpenAI-compatible provider",
                "PERSONAL_AI_OPENAI_COMPATIBLE_API_KEY",
                (
                    "model_inference",
                    "code_evolution_proposal",
                    "source_update_proposal",
                ),
                "registry_only",
                "Endpoint and adapter require separate reviewed implementation.",
            ),
            OnlineProviderDefinition(
                "direct_web",
                "Direct Web",
                None,
                ("web_fetch",),
                "planned",
                "Direct URL fetching requires separate domain, privacy, and execution controls.",
            ),
        )
