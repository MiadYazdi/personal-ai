from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from .models import ChatMessage, ChatMode


class ChatRuntimeError(Exception):
    """Raised when the local language model cannot serve a chat request."""


class LlamaCppQwenRuntime:
    """Lazy, CPU-only Qwen runtime behind the portable ChatRuntime contract."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        n_ctx: int = 2048,
        n_threads: int = 8,
        max_tokens: int = 512,
        llama_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._model_path = Path(model_path)
        self._n_ctx = n_ctx
        self._n_threads = n_threads
        self._max_tokens = max_tokens
        self._llama_factory = llama_factory
        self._llm: Any | None = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._llm is not None

    def stream_completion(
        self,
        messages: list[ChatMessage],
        mode: ChatMode,
    ) -> Iterator[str]:
        llm = self._ensure_loaded()

        request_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
        ]

        try:
            with self._inference_lock:
                stream = llm.create_chat_completion(
                    messages=request_messages,
                    max_tokens=self._max_tokens,
                    temperature=0.7 if mode == "quick" else 0.55,
                    stream=True,
                )
                for chunk in stream:
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        yield content
        except ChatRuntimeError:
            raise
        except Exception as error:
            raise ChatRuntimeError("Local model inference failed.") from error

    def close(self) -> None:
        llm = self._llm
        self._llm = None

        close = getattr(llm, "close", None)
        if callable(close):
            close()

    def _ensure_loaded(self) -> Any:
        if self._llm is not None:
            return self._llm

        with self._load_lock:
            if self._llm is not None:
                return self._llm

            if not self._model_path.is_file():
                raise ChatRuntimeError("Verified local model file is unavailable.")

            factory = self._llama_factory or self._default_llama_factory

            try:
                self._llm = factory(
                    model_path=str(self._model_path),
                    n_ctx=self._n_ctx,
                    n_threads=self._n_threads,
                    n_gpu_layers=0,
                    verbose=False,
                )
            except Exception as error:
                raise ChatRuntimeError("Local model could not be loaded.") from error

            return self._llm

    @staticmethod
    def _default_llama_factory(**kwargs: Any) -> Any:
        try:
            from llama_cpp import Llama
        except ImportError as error:
            raise ChatRuntimeError("llama-cpp-python is not installed.") from error

        return Llama(**kwargs)
