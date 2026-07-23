from __future__ import annotations

import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

from personal_ai.vault import VaultRecord, VaultStore
from personal_ai.vault.session import VaultLockedError, VaultSessionManager


CONVERSATION_CATALOG_TYPE = "conversation_catalog"
CONVERSATION_MESSAGE_TYPE = "conversation_message"
MEMORY_CATALOG_TYPE = "memory_catalog"
MEMORY_TYPE = "memory"
CONVERSATION_ATTACHMENT_TYPE = "conversation_attachment"
CONVERSATION_ATTACHMENT_CHUNK_TYPE = "conversation_attachment_chunk"

MAX_TITLE_CHARACTERS = 200
MAX_MESSAGE_CHARACTERS = 8_000
MAX_MEMORY_CHARACTERS = 4_000
MAX_MODEL_SHARE_ATTACHMENT_BYTES = 1 * 1024 * 1024
MODEL_SHARE_ATTACHMENT_CHUNK_CHARACTERS = 6_000


class ConversationMemoryError(Exception):
    """Base error for encrypted conversation and memory operations."""


class ConversationMemoryLockedError(ConversationMemoryError):
    """Raised when persistence is requested while the Vault is locked."""


class ConversationMemoryNotFoundError(ConversationMemoryError):
    """Raised when a private conversation or memory does not exist."""


class ConversationMemoryValidationError(ConversationMemoryError):
    """Raised for invalid user-selected persistence input."""


@dataclass(frozen=True)
class ConversationSummary:
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
        }


@dataclass(frozen=True)
class ConversationMessage:
    message_id: str
    conversation_id: str
    sequence: int
    role: str
    content: str
    created_at: str
    kind: str = "text"
    model_share: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "sequence": self.sequence,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "kind": self.kind,
            "model_share": self.model_share,
        }


@dataclass(frozen=True)
class MemoryItem:
    memory_id: str
    content: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "created_at": self.created_at,
        }


class ConversationMemoryService:
    """Explicit-only encrypted persistence using an unlocked local Vault."""

    def __init__(self, vault_session_manager: VaultSessionManager) -> None:
        self._vault_session_manager = vault_session_manager

    def list_conversations(self) -> list[ConversationSummary]:
        with self._vault_access() as vault:
            _, catalog = self._catalog(vault, CONVERSATION_CATALOG_TYPE)
            return self._conversation_entries(catalog)

    def create_conversation(self, title: str) -> ConversationSummary:
        normalized_title = self._require_text(title, "Conversation title", MAX_TITLE_CHARACTERS)
        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, CONVERSATION_CATALOG_TYPE)
            timestamp = self._now()
            summary = ConversationSummary(
                conversation_id=uuid.uuid4().hex,
                title=normalized_title,
                created_at=timestamp,
                updated_at=timestamp,
                message_count=0,
            )
            entries = [summary.to_dict(), *self._catalog_entries(catalog)]
            self._save_catalog(vault, catalog_record, CONVERSATION_CATALOG_TYPE, entries)
            return summary

    def get_conversation(self, conversation_id: str) -> tuple[ConversationSummary, list[ConversationMessage]]:
        self._require_id(conversation_id, "Conversation")
        with self._vault_access() as vault:
            _, catalog = self._catalog(vault, CONVERSATION_CATALOG_TYPE)
            summary = self._find_conversation(catalog, conversation_id)
            messages = self._conversation_messages(vault, conversation_id)
            return summary, messages

    def append_message(self, conversation_id: str, role: str, content: str) -> ConversationMessage:
        self._require_id(conversation_id, "Conversation")
        if role not in ("user", "assistant"):
            raise ConversationMemoryValidationError("Message role must be user or assistant.")
        message_content = self._require_text(content, "Message", MAX_MESSAGE_CHARACTERS)

        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, CONVERSATION_CATALOG_TYPE)
            summary = self._find_conversation(catalog, conversation_id)
            existing = self._conversation_messages(vault, conversation_id)
            timestamp = self._now()
            message = ConversationMessage(
                message_id=uuid.uuid4().hex,
                conversation_id=conversation_id,
                sequence=len(existing),
                role=role,
                content=message_content,
                created_at=timestamp,
            )
            vault.put_record(CONVERSATION_MESSAGE_TYPE, message.to_dict())

            entries = self._catalog_entries(catalog)
            for entry in entries:
                if entry["conversation_id"] == conversation_id:
                    entry["updated_at"] = timestamp
                    entry["message_count"] = summary.message_count + 1
                    break
            self._save_catalog(vault, catalog_record, CONVERSATION_CATALOG_TYPE, entries)
            return message

    def append_model_share(
        self,
        conversation_id: str,
        *,
        canonical_path: str,
        content: str,
        size_bytes: int,
        sha256: str,
        sensitive: bool,
    ) -> ConversationMessage:
        """Persist an explicitly saved model-share attachment in encrypted chunks."""
        self._require_id(conversation_id, "Conversation")
        path = self._require_text(canonical_path, "Canonical path", 4_000)
        attachment_content = self._require_model_share_content(content)
        actual_size = len(attachment_content.encode("utf-8"))
        if size_bytes != actual_size:
            raise ConversationMemoryValidationError("Model-share size does not match content.")
        expected_sha256 = self._require_text(sha256, "Model-share digest", 128)
        actual_sha256 = __import__("hashlib").sha256(
            attachment_content.encode("utf-8")
        ).hexdigest()
        if expected_sha256 != actual_sha256:
            raise ConversationMemoryValidationError("Model-share digest does not match content.")

        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, CONVERSATION_CATALOG_TYPE)
            summary = self._find_conversation(catalog, conversation_id)
            existing = self._conversation_messages(vault, conversation_id)
            timestamp = self._now()
            attachment_id = uuid.uuid4().hex
            message_id = uuid.uuid4().hex
            chunk_record_ids: list[str] = []
            for index, chunk in enumerate(self._split_model_share_content(attachment_content)):
                chunk_record_ids.append(vault.put_record(
                    CONVERSATION_ATTACHMENT_CHUNK_TYPE,
                    {
                        "attachment_id": attachment_id,
                        "index": index,
                        "content": chunk,
                    },
                ))

            metadata: dict[str, object] = {
                "attachment_id": attachment_id,
                "canonical_path": path,
                "size_bytes": actual_size,
                "sha256": actual_sha256,
                "sensitive": bool(sensitive),
                "chunk_count": len(chunk_record_ids),
                "created_at": timestamp,
            }
            vault.put_record(
                CONVERSATION_ATTACHMENT_TYPE,
                {
                    **metadata,
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "chunk_record_ids": chunk_record_ids,
                },
            )
            stored = ConversationMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                sequence=len(existing),
                role="user",
                content="[Local model-share attachment]",
                created_at=timestamp,
                kind="model_share",
            )
            vault.put_record(CONVERSATION_MESSAGE_TYPE, stored.to_dict())
            self._increment_conversation_message_count(
                vault, catalog_record, catalog, summary, timestamp
            )
            return ConversationMessage(
                **{**stored.__dict__, "content": attachment_content, "model_share": metadata}
            )

    def delete_conversation(self, conversation_id: str) -> None:
        self._require_id(conversation_id, "Conversation")
        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, CONVERSATION_CATALOG_TYPE)
            self._find_conversation(catalog, conversation_id)
            for message in self._conversation_messages(vault, conversation_id):
                vault.delete_record(message.message_id)
            self._delete_model_share_attachments(vault, conversation_id)
            entries = [
                entry
                for entry in self._catalog_entries(catalog)
                if entry["conversation_id"] != conversation_id
            ]
            self._save_catalog(vault, catalog_record, CONVERSATION_CATALOG_TYPE, entries)

    def delete_all_conversations(self) -> int:
        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, CONVERSATION_CATALOG_TYPE)
            entries = self._catalog_entries(catalog)
            for entry in entries:
                for message in self._conversation_messages(vault, entry["conversation_id"]):
                    vault.delete_record(message.message_id)
                self._delete_model_share_attachments(vault, entry["conversation_id"])
            self._save_catalog(vault, catalog_record, CONVERSATION_CATALOG_TYPE, [])
            return len(entries)

    def list_memories(self) -> list[MemoryItem]:
        with self._vault_access() as vault:
            _, catalog = self._catalog(vault, MEMORY_CATALOG_TYPE)
            items: list[MemoryItem] = []
            for entry in self._catalog_entries(catalog):
                record = vault.get_record(entry["record_id"])
                payload = record.payload
                items.append(MemoryItem(
                    memory_id=payload["memory_id"],
                    content=payload["content"],
                    created_at=payload["created_at"],
                ))
            return items

    def create_memory(self, content: str) -> MemoryItem:
        memory_content = self._require_text(content, "Memory", MAX_MEMORY_CHARACTERS)
        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, MEMORY_CATALOG_TYPE)
            timestamp = self._now()
            item = MemoryItem(
                memory_id=uuid.uuid4().hex,
                content=memory_content,
                created_at=timestamp,
            )
            record_id = vault.put_record(MEMORY_TYPE, item.to_dict())
            entries = [{"memory_id": item.memory_id, "record_id": record_id}, *self._catalog_entries(catalog)]
            self._save_catalog(vault, catalog_record, MEMORY_CATALOG_TYPE, entries)
            return item

    def delete_memory(self, memory_id: str) -> None:
        self._require_id(memory_id, "Memory")
        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, MEMORY_CATALOG_TYPE)
            entries = self._catalog_entries(catalog)
            target = next((entry for entry in entries if entry["memory_id"] == memory_id), None)
            if target is None:
                raise ConversationMemoryNotFoundError("Memory does not exist.")
            vault.delete_record(target["record_id"])
            self._save_catalog(
                vault,
                catalog_record,
                MEMORY_CATALOG_TYPE,
                [entry for entry in entries if entry["memory_id"] != memory_id],
            )

    def delete_all_memories(self) -> int:
        with self._vault_access() as vault:
            catalog_record, catalog = self._catalog(vault, MEMORY_CATALOG_TYPE)
            entries = self._catalog_entries(catalog)
            for entry in entries:
                vault.delete_record(entry["record_id"])
            self._save_catalog(vault, catalog_record, MEMORY_CATALOG_TYPE, [])
            return len(entries)

    @contextmanager
    def _vault_access(self):
        try:
            with self._vault_session_manager.access() as vault:
                yield vault
        except VaultLockedError as error:
            raise ConversationMemoryLockedError("Vault is locked.") from error

    def _catalog(self, vault: VaultStore, record_type: str) -> tuple[VaultRecord | None, dict[str, object]]:
        catalog = vault.find_first_record_by_type(record_type)
        if catalog is None:
            return None, {"entries": []}
        entries = catalog.payload.get("entries")
        if not isinstance(entries, list):
            raise ConversationMemoryValidationError("Encrypted catalog is invalid.")
        return catalog, catalog.payload

    def _save_catalog(self, vault: VaultStore, catalog: VaultRecord | None, record_type: str, entries: list[dict[str, object]]) -> None:
        payload = {"entries": entries, "updated_at": self._now()}
        if catalog is None:
            vault.put_record(record_type, payload)
        else:
            vault.replace_record(record_type, payload, record_id=catalog.record_id)

    @staticmethod
    def _catalog_entries(catalog: dict[str, object]) -> list[dict[str, object]]:
        entries = catalog.get("entries", [])
        if not isinstance(entries, list):
            raise ConversationMemoryValidationError("Encrypted catalog entries are invalid.")
        return [dict(entry) for entry in entries if isinstance(entry, dict)]

    def _conversation_entries(self, catalog: dict[str, object]) -> list[ConversationSummary]:
        entries: list[ConversationSummary] = []
        for entry in self._catalog_entries(catalog):
            try:
                entries.append(ConversationSummary(
                    conversation_id=str(entry["conversation_id"]),
                    title=str(entry["title"]),
                    created_at=str(entry["created_at"]),
                    updated_at=str(entry["updated_at"]),
                    message_count=int(entry["message_count"]),
                ))
            except (KeyError, TypeError, ValueError) as error:
                raise ConversationMemoryValidationError("Encrypted conversation catalog is invalid.") from error
        return entries

    def _find_conversation(self, catalog: dict[str, object], conversation_id: str) -> ConversationSummary:
        for summary in self._conversation_entries(catalog):
            if summary.conversation_id == conversation_id:
                return summary
        raise ConversationMemoryNotFoundError("Conversation does not exist.")

    def _conversation_messages(self, vault: VaultStore, conversation_id: str) -> list[ConversationMessage]:
        attachments = self._model_share_attachments(vault, conversation_id)
        messages: list[ConversationMessage] = []
        for record in vault.find_records_by_type(CONVERSATION_MESSAGE_TYPE):
            payload = record.payload
            if payload.get("conversation_id") != conversation_id:
                continue
            try:
                kind = str(payload.get("kind", "text"))
                message_id = str(payload["message_id"])
                content = str(payload["content"])
                model_share = None
                if kind == "model_share":
                    attachment = attachments.get(message_id)
                    if attachment is None:
                        raise ConversationMemoryValidationError("Model-share attachment is unavailable.")
                    content, model_share = self._read_model_share_attachment(vault, attachment)
                messages.append(ConversationMessage(
                    message_id=message_id,
                    conversation_id=str(payload["conversation_id"]),
                    sequence=int(payload["sequence"]),
                    role=str(payload["role"]),
                    content=content,
                    created_at=str(payload["created_at"]),
                    kind=kind,
                    model_share=model_share,
                ))
            except (KeyError, TypeError, ValueError) as error:
                raise ConversationMemoryValidationError("Encrypted conversation message is invalid.") from error
        return sorted(messages, key=lambda message: message.sequence)

    def _increment_conversation_message_count(
        self,
        vault: VaultStore,
        catalog_record: VaultRecord | None,
        catalog: dict[str, object],
        summary: ConversationSummary,
        timestamp: str,
    ) -> None:
        entries = self._catalog_entries(catalog)
        for entry in entries:
            if entry["conversation_id"] == summary.conversation_id:
                entry["updated_at"] = timestamp
                entry["message_count"] = summary.message_count + 1
                break
        self._save_catalog(vault, catalog_record, CONVERSATION_CATALOG_TYPE, entries)

    def _model_share_attachments(
        self, vault: VaultStore, conversation_id: str
    ) -> dict[str, dict[str, object]]:
        attachments: dict[str, dict[str, object]] = {}
        for record in vault.find_records_by_type(CONVERSATION_ATTACHMENT_TYPE):
            payload = record.payload
            if payload.get("conversation_id") == conversation_id:
                payload = dict(payload)
                payload["record_id"] = record.record_id
                message_id = payload.get("message_id")
                if isinstance(message_id, str):
                    attachments[message_id] = payload
        return attachments

    def _read_model_share_attachment(
        self, vault: VaultStore, attachment: dict[str, object]
    ) -> tuple[str, dict[str, object]]:
        chunk_record_ids = attachment.get("chunk_record_ids")
        if not isinstance(chunk_record_ids, list) or not chunk_record_ids:
            raise ConversationMemoryValidationError("Model-share attachment chunks are invalid.")
        chunks: list[tuple[int, str]] = []
        for record_id in chunk_record_ids:
            record = vault.get_record(str(record_id))
            payload = record.payload
            chunks.append((int(payload["index"]), str(payload["content"])))
        content = "".join(chunk for _, chunk in sorted(chunks))
        metadata = {
            key: attachment[key]
            for key in ("attachment_id", "canonical_path", "size_bytes", "sha256", "sensitive", "chunk_count", "created_at")
            if key in attachment
        }
        actual_size = len(content.encode("utf-8"))
        if actual_size != metadata.get("size_bytes"):
            raise ConversationMemoryValidationError("Model-share attachment size is invalid.")
        actual_sha256 = __import__("hashlib").sha256(content.encode("utf-8")).hexdigest()
        if actual_sha256 != metadata.get("sha256"):
            raise ConversationMemoryValidationError("Model-share attachment digest is invalid.")
        return content, metadata

    def _delete_model_share_attachments(self, vault: VaultStore, conversation_id: str) -> None:
        for record in vault.find_records_by_type(CONVERSATION_ATTACHMENT_TYPE):
            payload = record.payload
            if payload.get("conversation_id") != conversation_id:
                continue
            for chunk_record_id in payload.get("chunk_record_ids", []):
                vault.delete_record(str(chunk_record_id))
            vault.delete_record(record.record_id)

    @staticmethod
    def _split_model_share_content(content: str) -> list[str]:
        return [
            content[index:index + MODEL_SHARE_ATTACHMENT_CHUNK_CHARACTERS]
            for index in range(0, len(content), MODEL_SHARE_ATTACHMENT_CHUNK_CHARACTERS)
        ]

    @staticmethod
    def _require_model_share_content(value: str) -> str:
        if not isinstance(value, str) or not value:
            raise ConversationMemoryValidationError("Model-share content cannot be empty.")
        if len(value.encode("utf-8")) > MAX_MODEL_SHARE_ATTACHMENT_BYTES:
            raise ConversationMemoryValidationError("Model-share content exceeds the 1 MiB limit.")
        return value

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _require_id(value: str, label: str) -> None:
        if not isinstance(value, str) or not value:
            raise ConversationMemoryValidationError(f"{label} ID is invalid.")

    @staticmethod
    def _require_text(value: str, label: str, limit: int) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ConversationMemoryValidationError(f"{label} cannot be empty.")
        if len(value) > limit:
            raise ConversationMemoryValidationError(f"{label} is too long.")
        return value
