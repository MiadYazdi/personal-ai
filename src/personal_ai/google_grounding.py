from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

GEMINI_GROUNDING_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/interactions"
)
DEFAULT_GEMINI_GROUNDING_MODEL = "gemini-3.5-flash"
MAX_QUERY_CHARS = 12_000
REQUEST_TIMEOUT_SECONDS = 60

Transport = Callable[[str, dict[str, str], bytes, int], tuple[int, bytes]]
KeyProvider = Callable[[], str | None]


class GoogleGroundingError(ValueError):
    """Raised when a Google Grounding request cannot be safely prepared."""


@dataclass(frozen=True)
class GoogleGroundingPreview:
    model_id: str
    query: str
    query_sha256: str
    request_sha256: str
    endpoint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "query_sha256": self.query_sha256,
            "query_characters": len(self.query),
            "request_sha256": self.request_sha256,
            "endpoint": self.endpoint,
            "tool": "google_search",
            "network_execution_enabled": False,
            "requires_fresh_confirmation": True,
            "requires_vault_unlock": True,
        }


@dataclass(frozen=True)
class GoogleGroundingSource:
    title: str
    url: str

    def to_dict(self) -> dict[str, str]:
        return {"title": self.title, "url": self.url}


@dataclass(frozen=True)
class GoogleGroundingResult:
    text: str
    sources: tuple[GoogleGroundingSource, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "sources": [source.to_dict() for source in self.sources],
        }


class GoogleGroundingConnector:
    """Official Gemini Google Search adapter; never runs until execute is called."""

    def __init__(
        self,
        *,
        key_provider: KeyProvider | None = None,
        transport: Transport | None = None,
        endpoint: str = GEMINI_GROUNDING_ENDPOINT,
    ) -> None:
        self._key_provider = key_provider or (
            lambda: os.environ.get("PERSONAL_AI_GEMINI_API_KEY")
        )
        self._transport = transport or self._default_transport
        self._endpoint = endpoint

    def status(self) -> dict[str, object]:
        return {
            "provider": "google-gemini-grounding",
            "configured": bool(self._key_provider()),
            "endpoint": self._endpoint,
            "tool": "google_search",
            "network_execution_enabled": False,
            "credential_source": "local environment only",
        }

    def preview(self, *, query: str, model_id: str) -> GoogleGroundingPreview:
        if (
            not isinstance(query, str)
            or not query.strip()
            or len(query) > MAX_QUERY_CHARS
            or "\x00" in query
        ):
            raise GoogleGroundingError("Grounded search query is invalid.")

        if not isinstance(model_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9._-]{0,63}",
            model_id,
        ):
            raise GoogleGroundingError("Grounding model identifier is invalid.")

        normalized_query = query.strip()
        query_sha256 = hashlib.sha256(
            normalized_query.encode("utf-8")
        ).hexdigest()
        request_sha256 = hashlib.sha256(
            json.dumps(
                {
                    "model_id": model_id,
                    "query_sha256": query_sha256,
                    "endpoint": self._endpoint,
                    "tool": "google_search",
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return GoogleGroundingPreview(
            model_id=model_id,
            query=normalized_query,
            query_sha256=query_sha256,
            request_sha256=request_sha256,
            endpoint=self._endpoint,
        )

    def execute(
        self,
        preview: GoogleGroundingPreview,
        *,
        expected_request_sha256: str,
    ) -> GoogleGroundingResult:
        if preview.request_sha256 != expected_request_sha256:
            raise GoogleGroundingError(
                "Grounded search request changed; preview again."
            )

        api_key = self._key_provider()
        if not api_key:
            raise GoogleGroundingError(
                "Local Gemini credential is not configured."
            )

        body = json.dumps(
            {
                "model": preview.model_id,
                "input": preview.query,
                "tools": [{"type": "google_search"}],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        status_code, raw_response = self._transport(
            preview.endpoint,
            {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            body,
            REQUEST_TIMEOUT_SECONDS,
        )

        if status_code < 200 or status_code >= 300:
            raise GoogleGroundingError(
                "Google Grounding request was rejected or unavailable."
            )

        try:
            payload = json.loads(raw_response.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GoogleGroundingError(
                "Google Grounding returned an invalid response."
            ) from error

        text = payload.get("output_text")
        if not isinstance(text, str) or not text.strip():
            raise GoogleGroundingError(
                "Google Grounding returned no readable response."
            )

        sources: list[GoogleGroundingSource] = []
        for step in payload.get("steps", []):
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue
            for block in step.get("content", []):
                if not isinstance(block, dict):
                    continue
                for annotation in block.get("annotations", []):
                    if not isinstance(annotation, dict):
                        continue
                    if annotation.get("type") != "url_citation":
                        continue
                    title = annotation.get("title")
                    url = annotation.get("url")
                    if (
                        isinstance(title, str)
                        and title.strip()
                        and isinstance(url, str)
                        and url.startswith(("https://", "http://"))
                    ):
                        source = GoogleGroundingSource(title.strip(), url)
                        if source not in sources:
                            sources.append(source)

        return GoogleGroundingResult(text=text.strip(), sources=tuple(sources))

    @staticmethod
    def _default_transport(
        endpoint: str,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: int,
    ) -> tuple[int, bytes]:
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout_seconds,
            ) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()
        except urllib.error.URLError as error:
            raise GoogleGroundingError(
                "Google Grounding network connection failed."
            ) from error
