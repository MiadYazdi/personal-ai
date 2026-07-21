from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Literal, Protocol


ChatMode = Literal["quick", "deep"]
ChatRole = Literal["system", "user", "assistant"]
ChatEventType = Literal["delta", "done", "error"]


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str


@dataclass(frozen=True)
class ChatStreamEvent:
    event_type: ChatEventType
    content: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {"type": self.event_type}
        if self.content:
            payload["content"] = self.content
        if self.message:
            payload["message"] = self.message
        return payload


class ChatRuntime(Protocol):
    @property
    def is_loaded(self) -> bool: ...

    def stream_completion(
        self,
        messages: list[ChatMessage],
        mode: ChatMode,
    ) -> Iterator[str]: ...

    def close(self) -> None: ...
