from __future__ import annotations

from dataclasses import dataclass

from .permissions import AgentCapability


@dataclass(frozen=True)
class UbuntuReadOnlyCapabilities:
    adapter_id: str = "ubuntu-read-only-v1"
    platform: str = "ubuntu"
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "platform": self.platform,
            "mode": "preview_only",
            "execution_enabled": self.execution_enabled,
            "available_capabilities": [
                AgentCapability.READ_METADATA,
                AgentCapability.READ_TEXT,
                AgentCapability.LAUNCH_APP,
                AgentCapability.RUN_TERMINAL,
                AgentCapability.WRITE_FILE,
                AgentCapability.DELETE_FILE,
                AgentCapability.NETWORK,
                AgentCapability.READ_SECRET,
                AgentCapability.ADMIN,
            ],
            "guarantees": [
                "No file scan",
                "No command execution",
                "No app launch",
                "No network action",
                "No administrator action",
            ],
        }


class UbuntuReadOnlyCapabilityAdapter:
    """Reports declared Ubuntu capability policy without touching the system."""

    def snapshot(self) -> UbuntuReadOnlyCapabilities:
        return UbuntuReadOnlyCapabilities()
