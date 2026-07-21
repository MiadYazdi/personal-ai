from __future__ import annotations

from collections.abc import Iterator

from personal_ai.conversation_memory import (
    ConversationMemoryLockedError,
    ConversationMemoryService,
)
from personal_ai.vault.session import VaultLockedError, VaultSessionManager

from .models import ChatMessage, ChatMode, ChatRuntime, ChatStreamEvent
from .runtime import ChatRuntimeError


MAX_MESSAGES = 16
MAX_MESSAGE_CHARACTERS = 8_000


class ChatRequestValidationError(ValueError):
    """Raised for invalid local chat requests before model loading."""


class ThinkingTagFilter:
    """Suppress Qwen thinking blocks, including tokens split across chunks."""

    _OPEN = "<think>"
    _CLOSE = "</think>"

    def __init__(self) -> None:
        self._buffer = ""
        self._inside_think = False

    def feed(self, content: str) -> list[str]:
        self._buffer += content
        output: list[str] = []

        while True:
            if self._inside_think:
                closing = self._buffer.find(self._CLOSE)
                if closing < 0:
                    self._buffer = self._buffer[-(len(self._CLOSE) - 1) :]
                    break

                self._buffer = self._buffer[closing + len(self._CLOSE) :]
                self._inside_think = False
                continue

            opening = self._buffer.find(self._OPEN)
            if opening >= 0:
                if opening:
                    output.append(self._buffer[:opening])
                self._buffer = self._buffer[opening + len(self._OPEN) :]
                self._inside_think = True
                continue

            keep = len(self._OPEN) - 1
            if len(self._buffer) > keep:
                output.append(self._buffer[:-keep])
                self._buffer = self._buffer[-keep:]
            break

        return output

    def finish(self) -> list[str]:
        if self._inside_think:
            self._buffer = ""
            return []

        output = [self._buffer] if self._buffer else []
        self._buffer = ""
        return output


class ChatService:
    """Local-only Chat Core with transient history and read-only Vault context."""

    def __init__(
        self,
        runtime: ChatRuntime,
        vault_session_manager: VaultSessionManager,
    ) -> None:
        self._runtime = runtime
        self._vault_session_manager = vault_session_manager

    def validate_request(
        self,
        messages: list[ChatMessage],
        mode: ChatMode,
    ) -> None:
        if mode not in ("quick", "deep"):
            raise ChatRequestValidationError("Unsupported thinking mode.")

        if not messages or len(messages) > MAX_MESSAGES:
            raise ChatRequestValidationError(
                f"Chat requires between 1 and {MAX_MESSAGES} messages."
            )

        if messages[-1].role != "user":
            raise ChatRequestValidationError(
                "The last chat message must belong to the user."
            )

        for message in messages:
            if message.role not in ("user", "assistant"):
                raise ChatRequestValidationError("Unsupported chat role.")
            if not isinstance(message.content, str) or not message.content.strip():
                raise ChatRequestValidationError(
                    "Chat message content cannot be empty."
                )
            if len(message.content) > MAX_MESSAGE_CHARACTERS:
                raise ChatRequestValidationError("Chat message is too long.")

    def stream_chat(
        self,
        messages: list[ChatMessage],
        mode: ChatMode,
    ) -> Iterator[ChatStreamEvent]:
        self.validate_request(messages, mode)
        profile_context = self._read_private_profile_context()
        selected_memories = self._read_selected_memories()
        prompt = [
            ChatMessage(
                role="system",
                content=self._system_prompt(mode, profile_context, selected_memories),
            ),
            *messages,
        ]
        thinking_filter = ThinkingTagFilter()

        try:
            for raw_chunk in self._runtime.stream_completion(prompt, mode):
                for visible_chunk in thinking_filter.feed(raw_chunk):
                    if visible_chunk:
                        yield ChatStreamEvent(
                            event_type="delta",
                            content=visible_chunk,
                        )

            for visible_chunk in thinking_filter.finish():
                if visible_chunk:
                    yield ChatStreamEvent(
                        event_type="delta",
                        content=visible_chunk,
                    )

            yield ChatStreamEvent(event_type="done")
        except ChatRuntimeError:
            yield ChatStreamEvent(
                event_type="error",
                message="Local model could not complete this response.",
            )

    def close(self) -> None:
        self._runtime.close()

    def _read_private_profile_context(self) -> tuple[str, str] | None:
        try:
            with self._vault_session_manager.access() as vault:
                profile = vault.find_first_record_by_type("profile")
        except VaultLockedError:
            return None

        if profile is None:
            return None

        profile_name = profile.payload.get("profile_name")
        address_name = profile.payload.get("address_name")

        if not isinstance(profile_name, str) or not profile_name.strip():
            return None
        if not isinstance(address_name, str) or not address_name.strip():
            address_name = profile_name

        return profile_name, address_name

    def _read_selected_memories(self) -> list[str]:
        try:
            items = ConversationMemoryService(self._vault_session_manager).list_memories()
        except ConversationMemoryLockedError:
            return []

        # Explicitly selected memories only; limit prompt growth on CPU context.
        return [item.content[:500] for item in items[:20]]

    @staticmethod
    def _system_prompt(
        mode: ChatMode,
        profile_context: tuple[str, str] | None,
        selected_memories: list[str],
    ) -> str:
        lines = [
            "You are Personal AI, a helpful local-first assistant.",
            "Answer directly in the user's language when possible.",
            "Do not claim private memory or profile context unless it is provided below.",
        ]

        if mode == "quick":
            lines.append("/no_think")

        if profile_context is not None:
            profile_name, address_name = profile_context
            lines.extend(
                [
                    "Private context for this request only:",
                    f"Profile name: {profile_name}",
                    f"Address the user as: {address_name}",
                ]
            )

        if selected_memories:
            lines.append("User-selected memory for this request only:")
            lines.extend(f"- {memory}" for memory in selected_memories)

        return "\n".join(lines)
