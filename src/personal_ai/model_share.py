from __future__ import annotations

import hashlib
import json
import threading
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from personal_ai.agent.permissions import (
    AgentActionRequest,
    AgentCapability,
    GrantDecision,
    PermissionEngine,
)
from personal_ai.agent.readonly_executor import (
    MAX_TEXT_BYTES,
    ReadMode,
    ReadOnlyExecutorError,
    UbuntuReadOnlyExecutor,
)
from personal_ai.chat.models import ChatMessage, ChatMode, ChatRuntime
from personal_ai.chat.runtime import ChatRuntimeError
from personal_ai.chat.service import ThinkingTagFilter


MAX_MODEL_SHARE_CHUNK_CHARACTERS = 900
MAX_REDUCTION_BATCH = 3


class ModelShareError(ValueError):
    """Raised when an explicit local model-share plan is invalid."""


@dataclass(frozen=True)
class ModelSharePlan:
    plan_id: str
    operation_id: str
    canonical_path: str
    source_bytes: int
    content_sha256: str
    sensitive: bool
    chunk_count: int
    chunks: tuple[dict[str, int], ...]
    requires_sensitive_confirmation: bool
    large_share_warning: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "plan_id": self.plan_id,
            "operation_id": self.operation_id,
            "canonical_path": self.canonical_path,
            "source_bytes": self.source_bytes,
            "content_sha256": self.content_sha256,
            "sensitive": self.sensitive,
            "chunk_count": self.chunk_count,
            "chunks": list(self.chunks),
            "requires_sensitive_confirmation": self.requires_sensitive_confirmation,
            "large_share_warning": self.large_share_warning,
            "storage": "temporary_browser_until_explicit_conversation_save",
            "destination": "local_qwen_only",
        }


@dataclass(frozen=True)
class ModelShareEvent:
    event_type: str
    content: str = ""
    message: str = ""
    completed: int = 0
    total: int = 0
    phase: str = ""

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {"type": self.event_type}
        if self.content:
            result["content"] = self.content
        if self.message:
            result["message"] = self.message
        if self.total:
            result.update({"completed": self.completed, "total": self.total, "phase": self.phase})
        return result


class LocalModelShareService:
    """Explicit, local-only, cancellable chunked analysis for selected read results."""

    def __init__(
        self,
        runtime: ChatRuntime,
        executor: UbuntuReadOnlyExecutor,
        permissions: PermissionEngine,
    ) -> None:
        self._runtime = runtime
        self._executor = executor
        self._permissions = permissions
        self._operations: dict[str, threading.Event] = {}
        self._operations_lock = threading.Lock()

    def preview(
        self,
        *,
        selected_scope: str,
        requested_path: str,
        content: str,
    ) -> ModelSharePlan:
        if not isinstance(content, str) or not content:
            raise ModelShareError("Model-share content cannot be empty.")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_TEXT_BYTES:
            raise ModelShareError("Model-share content exceeds the 1 MiB read limit.")
        try:
            preview = self._executor.preview(selected_scope, requested_path, ReadMode.TEXT)
        except ReadOnlyExecutorError as error:
            raise ModelShareError(str(error)) from error
        if preview.size_bytes != len(encoded):
            raise ModelShareError("Selected file changed or content does not match the read result.")
        chunks = self._split_content(content)
        digest_payload = {
            "canonical_path": preview.canonical_path,
            "source_bytes": len(encoded),
            "content_sha256": hashlib.sha256(encoded).hexdigest(),
            "chunk_sizes": [len(chunk.encode("utf-8")) for chunk in chunks],
        }
        plan_id = hashlib.sha256(
            json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return ModelSharePlan(
            plan_id=plan_id,
            operation_id=uuid.uuid4().hex,
            canonical_path=preview.canonical_path,
            source_bytes=len(encoded),
            content_sha256=digest_payload["content_sha256"],
            sensitive=preview.sensitive,
            chunk_count=len(chunks),
            chunks=tuple(
                {"index": index + 1, "characters": len(chunk), "bytes": len(chunk.encode("utf-8"))}
                for index, chunk in enumerate(chunks)
            ),
            requires_sensitive_confirmation=preview.requires_model_share_confirmation,
            large_share_warning=len(chunks) > 8,
        )

    def cancel(self, operation_id: str) -> bool:
        with self._operations_lock:
            event = self._operations.get(operation_id)
        if event is None:
            return False
        event.set()
        return True

    def stream(
        self,
        *,
        selected_scope: str,
        requested_path: str,
        content: str,
        plan_id: str,
        operation_id: str,
        confirmed: bool,
        sensitive_confirmed: bool,
        mode: ChatMode,
    ) -> Iterator[ModelShareEvent]:
        plan = self.preview(
            selected_scope=selected_scope,
            requested_path=requested_path,
            content=content,
        )
        if not confirmed:
            raise ModelShareError("Fresh model-share confirmation is required.")
        if plan.plan_id != plan_id:
            raise ModelShareError("Model-share plan changed; preview again before sharing.")
        if plan.requires_sensitive_confirmation and not sensitive_confirmed:
            raise ModelShareError("Sensitive model sharing requires fresh confirmation.")
        if mode not in ("quick", "deep"):
            raise ModelShareError("Unsupported thinking mode.")

        cancel_event = threading.Event()
        with self._operations_lock:
            self._operations[operation_id] = cancel_event
        try:
            action = AgentActionRequest.create(
                capability=AgentCapability.READ_TEXT,
                target_scope=plan.canonical_path,
                device_id="ubuntu-current-user-session",
                description="User-confirmed local model share",
                preview="Chunked local Qwen analysis of selected read-only text",
                audit_metadata={
                    "source_bytes": plan.source_bytes,
                    "content_sha256": plan.content_sha256,
                    "chunk_count": plan.chunk_count,
                    "operation_id": operation_id,
                },
            )
            self._permissions.approve(action, GrantDecision.ONCE)
            chunks = self._split_content(content)
            summaries: list[str] = []
            yield ModelShareEvent("progress", completed=0, total=len(chunks), phase="chunks")
            for index, chunk in enumerate(chunks, start=1):
                if cancel_event.is_set():
                    yield ModelShareEvent("cancelled", message="Model-share processing was cancelled.")
                    return
                summaries.append(self._complete(
                    [
                        ChatMessage(role="system", content=(
                            "You are analyzing one chunk of a user-approved local document. "
                            "Return compact factual notes in at most 120 words. Do not mention hidden reasoning."
                        )),
                        ChatMessage(role="user", content=f"Document chunk {index}/{len(chunks)}:\n{chunk}"),
                    ],
                    mode,
                    cancel_event,
                ))
                yield ModelShareEvent("progress", completed=index, total=len(chunks), phase="chunks")

            level = 0
            while len(summaries) > 1:
                reduced: list[str] = []
                for batch_start in range(0, len(summaries), MAX_REDUCTION_BATCH):
                    if cancel_event.is_set():
                        yield ModelShareEvent("cancelled", message="Model-share processing was cancelled.")
                        return
                    batch = summaries[batch_start:batch_start + MAX_REDUCTION_BATCH]
                    level += 1
                    reduced.append(self._complete(
                        [
                            ChatMessage(role="system", content=(
                                "Combine the supplied local document notes without inventing facts. "
                                "Return compact notes in at most 160 words."
                            )),
                            ChatMessage(role="user", content="\n\n".join(batch)),
                        ],
                        mode,
                        cancel_event,
                    ))
                    yield ModelShareEvent("progress", completed=batch_start + len(batch), total=len(summaries), phase=f"reduce-{level}")
                summaries = reduced

            if cancel_event.is_set():
                yield ModelShareEvent("cancelled", message="Model-share processing was cancelled.")
                return
            final = self._complete(
                [
                    ChatMessage(role="system", content=(
                        "Answer the user directly using the approved local document analysis. "
                        "Be concise, factual, and answer in the user's language when possible."
                    )),
                    ChatMessage(role="user", content=summaries[0]),
                ],
                mode,
                cancel_event,
            )
            if cancel_event.is_set():
                yield ModelShareEvent("cancelled", message="Model-share processing was cancelled.")
                return
            yield ModelShareEvent("delta", content=final)
            yield ModelShareEvent("done")
        except ChatRuntimeError as error:
            yield ModelShareEvent("error", message=str(error))
        finally:
            with self._operations_lock:
                self._operations.pop(operation_id, None)

    @staticmethod
    def _split_content(content: str) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        for character in content:
            current.append(character)
            if len(current) >= MAX_MODEL_SHARE_CHUNK_CHARACTERS:
                chunks.append("".join(current))
                current = []
        if current:
            chunks.append("".join(current))
        return chunks

    def _complete(
        self,
        messages: list[ChatMessage],
        mode: ChatMode,
        cancel_event: threading.Event,
    ) -> str:
        filter_ = ThinkingTagFilter()
        output: list[str] = []
        for raw_chunk in self._runtime.stream_completion(messages, mode):
            if cancel_event.is_set():
                break
            output.extend(filter_.feed(raw_chunk))
        output.extend(filter_.finish())
        result = "".join(output).strip()
        if not result:
            raise ChatRuntimeError("Local model returned no visible model-share result.")
        return result
