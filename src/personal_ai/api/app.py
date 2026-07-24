from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from personal_ai.agent import (
    AgentActionRequest,
    AgentCapability,
    PermissionEngine,
    TerminalPreview,
    UbuntuReadOnlyCapabilityAdapter,
    GrantDecision,
)
from personal_ai.agent.launch_executor import (
    LaunchExecutionError,
    LaunchPreviewError,
    UbuntuApplicationLaunchPreview,
)
from personal_ai.agent.readonly_executor import (
    ReadMode,
    ReadOnlyExecutorError,
    UbuntuReadOnlyExecutor,
)
from personal_ai.model_share import LocalModelShareService, ModelShareError
from personal_ai.conversation_memory import (
    ConversationMemoryLockedError,
    ConversationMemoryNotFoundError,
    ConversationMemoryService,
    ConversationMemoryValidationError,
)
from personal_ai.chat import (
    ChatMessage,
    ChatRequestValidationError,
    ChatRuntime,
    ChatService,
    LlamaCppQwenRuntime,
)
from personal_ai.onboarding import (
    OnboardingConflictError,
    OnboardingService,
    OnboardingValidationError,
)
from personal_ai.ui_preferences import (
    UiPreferenceStore,
    UiPreferenceValidationError,
    UiPreferences,
)
from personal_ai.vault.session import (
    VaultAlreadyUnlockedError,
    VaultNotConfiguredError,
    VaultSessionManager,
    VaultSessionStorageError,
    VaultSessionUnlockError,
    VaultSessionValidationError,
)


APP_VERSION = "0.1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = PROJECT_ROOT / "models" / "qwen3-8b"
MODEL_MANIFEST_PATH = MODEL_DIR / "manifest.json"
MODEL_FILE_PATH = MODEL_DIR / "Qwen3-8B-Q4_K_M.gguf"
VAULT_DATABASE_PATH = (
    PROJECT_ROOT / "data" / "local" / "personal-ai-vault.sqlite3"
)
UI_PREFERENCES_PATH = (
    PROJECT_ROOT / "data" / "local" / "ui-preferences.json"
)

LOCAL_WEB_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


class LocalVaultOnboardingRequest(BaseModel):
    profile_name: str
    address_name: str | None = None
    vault_passphrase: str
    create_recovery_key: bool = False


class VaultUnlockRequest(BaseModel):
    method: Literal[
        "passphrase",
        "recovery_bip39",
        "recovery_base64url",
    ] = "passphrase"
    passphrase: str | None = None
    recovery_phrase: str | None = None
    recovery_base64url: str | None = None


class ChatMessageRequest(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class LocalChatRequest(BaseModel):
    messages: list[ChatMessageRequest]
    mode: Literal["quick", "deep"] = "quick"


class ConversationCreateRequest(BaseModel):
    title: str


class ConversationMessageCreateRequest(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ConversationModelShareCreateRequest(BaseModel):
    canonical_path: str
    content: str
    size_bytes: int
    sha256: str
    sensitive: bool = False


class MemoryCreateRequest(BaseModel):
    content: str


class LaunchPreviewRequest(BaseModel):
    desktop_entry: str


class LaunchExecuteRequest(LaunchPreviewRequest):
    expected_desktop_sha256: str
    confirmed: bool = False


class AgentTerminalPreviewRequest(BaseModel):
    argv: list[str]
    cwd: str
    expected_effect: str


class AgentPreviewRequest(BaseModel):
    capability: AgentCapability
    target_scope: str
    description: str
    preview: str
    terminal: AgentTerminalPreviewRequest | None = None


class ReadOnlyPreviewRequest(BaseModel):
    selected_scope: str
    requested_path: str
    mode: Literal["read_metadata", "read_text"]


class ModelSharePreviewRequest(BaseModel):
    selected_scope: str
    requested_path: str
    content: str


class ModelShareStreamRequest(ModelSharePreviewRequest):
    plan_id: str
    operation_id: str
    confirmed: bool = False
    sensitive_confirmed: bool = False
    mode: Literal["quick", "deep"] = "quick"


class ReadOnlyExecuteRequest(ReadOnlyPreviewRequest):
    confirmed: bool = False
    sensitive_confirmed: bool = False
    share_with_model: bool = False
    model_share_confirmed: bool = False


def _load_model_manifest() -> dict[str, Any] | None:
    if not MODEL_MANIFEST_PATH.is_file():
        return None

    try:
        return json.loads(MODEL_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_status_payload(
    vault_path: Path = VAULT_DATABASE_PATH,
    *,
    vault_state: str | None = None,
    model_loaded: bool = False,
) -> dict[str, Any]:
    manifest = _load_model_manifest()
    model_available = MODEL_FILE_PATH.is_file() and manifest is not None
    vault_exists = vault_path.is_file()

    return {
        "product_name": "Personal AI",
        "version": APP_VERSION,
        "local_mode": True,
        "online_mode": False,
        "vault": {
            "state": vault_state or (
                "locked" if vault_exists else "not_created"
            ),
            "database_exists": vault_exists,
        },
        "model": {
            "available": model_available,
            "loaded": model_loaded,
            "id": manifest.get("model_id") if manifest else None,
            "manifest_verified": manifest is not None,
            "thinking_modes": ["quick", "deep"],
        },
        "device_agent": {
            "platform": "ubuntu",
            "state": "preview_only",
            "requires_user_session": True,
        },
        "api": {
            "bind_scope": "127.0.0.1 only",
            "port": 8765,
        },
    }


def create_app(
    *,
    vault_path: Path | None = None,
    preference_path: Path | None = None,
    chat_runtime: ChatRuntime | None = None,
    launch_preview_executor: UbuntuApplicationLaunchPreview | None = None,
) -> FastAPI:
    active_vault_path = vault_path or VAULT_DATABASE_PATH
    active_preference_path = preference_path or UI_PREFERENCES_PATH

    onboarding_service = OnboardingService(active_vault_path)
    ui_preference_store = UiPreferenceStore(active_preference_path)
    vault_session_manager = VaultSessionManager(active_vault_path)
    active_chat_runtime = chat_runtime or LlamaCppQwenRuntime(MODEL_FILE_PATH)
    chat_service = ChatService(active_chat_runtime, vault_session_manager)
    conversation_memory_service = ConversationMemoryService(vault_session_manager)
    permission_engine = PermissionEngine(vault_session_manager)
    capability_adapter = UbuntuReadOnlyCapabilityAdapter()
    read_only_executor = UbuntuReadOnlyExecutor()
    active_launch_preview_executor = launch_preview_executor or UbuntuApplicationLaunchPreview()
    model_share_service = LocalModelShareService(
        active_chat_runtime, read_only_executor, permission_engine
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            chat_service.close()
            vault_session_manager.close()

    app = FastAPI(
        title="Personal AI Local API",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.vault_session_manager = vault_session_manager
    app.state.chat_service = chat_service
    app.state.conversation_memory_service = conversation_memory_service
    app.state.permission_engine = permission_engine
    app.state.capability_adapter = capability_adapter
    app.state.read_only_executor = read_only_executor
    app.state.launch_preview_executor = active_launch_preview_executor
    app.state.model_share_service = model_share_service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=LOCAL_WEB_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "PUT", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "personal-ai-local-api",
            "bind_scope": "localhost",
        }

    @app.get("/api/v1/status")
    def status() -> dict[str, Any]:
        vault_status = vault_session_manager.status()
        return build_status_payload(
            active_vault_path,
            vault_state=vault_status.vault_state,
            model_loaded=active_chat_runtime.is_loaded,
        )

    @app.get("/api/v1/ui-config")
    def ui_config() -> dict[str, Any]:
        return {
            "product_name": "Personal AI",
            "languages": ["fa", "en", "ar", "tr"],
            "themes": ["system", "dark", "light"],
            "thinking_modes": ["quick", "deep"],
            "online_default": False,
        }

    @app.get("/api/v1/ui-preferences")
    def get_ui_preferences() -> dict[str, Any]:
        return ui_preference_store.load().to_dict()

    @app.put("/api/v1/ui-preferences")
    def put_ui_preferences(
        preferences: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            parsed_preferences = UiPreferences.from_mapping(preferences)
            return ui_preference_store.save(parsed_preferences).to_dict()
        except UiPreferenceValidationError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.get("/api/v1/onboarding/status")
    def onboarding_status() -> dict[str, bool | str]:
        onboarding_status = onboarding_service.status()
        vault_status = vault_session_manager.status()

        return {
            "vault_configured": onboarding_status.vault_configured,
            "vault_state": vault_status.vault_state,
            "profile_available": onboarding_status.profile_available,
        }

    @app.post("/api/v1/onboarding/local-vault")
    def onboarding_local_vault(
        request: LocalVaultOnboardingRequest,
    ) -> dict[str, object]:
        try:
            result = onboarding_service.create_local_vault(
                profile_name=request.profile_name,
                address_name=request.address_name,
                vault_passphrase=request.vault_passphrase,
                create_recovery_key=request.create_recovery_key,
            )
            return result.to_api_dict()
        except OnboardingValidationError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except OnboardingConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/api/v1/vault/status")
    def vault_status() -> dict[str, object]:
        return vault_session_manager.status().to_dict()

    @app.post("/api/v1/vault/unlock")
    def unlock_vault(
        request: VaultUnlockRequest,
    ) -> dict[str, object]:
        try:
            if request.method == "passphrase":
                status = vault_session_manager.unlock_with_passphrase(
                    request.passphrase
                )
            elif request.method == "recovery_bip39":
                status = vault_session_manager.unlock_with_recovery_bip39(
                    request.recovery_phrase
                )
            else:
                status = vault_session_manager.unlock_with_recovery_base64url(
                    request.recovery_base64url
                )

            return status.to_dict()

        except VaultSessionValidationError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        except VaultNotConfiguredError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

        except VaultAlreadyUnlockedError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

        except VaultSessionUnlockError as error:
            raise HTTPException(
                status_code=401,
                detail="Vault credential was rejected.",
            ) from error

        except VaultSessionStorageError as error:
            raise HTTPException(
                status_code=503,
                detail="Vault is unavailable.",
            ) from error

    @app.post("/api/v1/vault/lock")
    def lock_vault() -> dict[str, object]:
        return vault_session_manager.lock().to_dict()

    @app.post("/api/v1/chat/stream")
    def stream_local_chat(
        request: LocalChatRequest,
    ) -> StreamingResponse:
        messages = [
            ChatMessage(role=item.role, content=item.content)
            for item in request.messages
        ]

        try:
            chat_service.validate_request(messages, request.mode)
        except ChatRequestValidationError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        def encode_events():
            for event in chat_service.stream_chat(messages, request.mode):
                payload = json.dumps(
                    event.to_dict(),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                yield f"{payload}\n"

        return StreamingResponse(
            encode_events(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-store"},
        )

    def conversation_error(error: Exception) -> HTTPException:
        if isinstance(error, ConversationMemoryLockedError):
            return HTTPException(status_code=423, detail="Vault is locked.")
        if isinstance(error, ConversationMemoryNotFoundError):
            return HTTPException(status_code=404, detail="Private record does not exist.")
        return HTTPException(status_code=422, detail=str(error))

    @app.get("/api/v1/conversations")
    def list_conversations() -> dict[str, object]:
        try:
            return {
                "conversations": [
                    item.to_dict()
                    for item in conversation_memory_service.list_conversations()
                ]
            }
        except (ConversationMemoryLockedError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.post("/api/v1/conversations")
    def create_conversation(
        request: ConversationCreateRequest,
    ) -> dict[str, object]:
        try:
            return conversation_memory_service.create_conversation(request.title).to_dict()
        except (ConversationMemoryLockedError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.get("/api/v1/conversations/{conversation_id}")
    def get_conversation(conversation_id: str) -> dict[str, object]:
        try:
            summary, messages = conversation_memory_service.get_conversation(conversation_id)
            return {
                "conversation": summary.to_dict(),
                "messages": [message.to_dict() for message in messages],
            }
        except (ConversationMemoryLockedError, ConversationMemoryNotFoundError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.post("/api/v1/conversations/{conversation_id}/messages")
    def append_conversation_message(
        conversation_id: str,
        request: ConversationMessageCreateRequest,
    ) -> dict[str, object]:
        try:
            return conversation_memory_service.append_message(
                conversation_id,
                request.role,
                request.content,
            ).to_dict()
        except (ConversationMemoryLockedError, ConversationMemoryNotFoundError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.post("/api/v1/conversations/{conversation_id}/model-shares")
    def append_conversation_model_share(
        conversation_id: str,
        request: ConversationModelShareCreateRequest,
    ) -> dict[str, object]:
        try:
            return conversation_memory_service.append_model_share(
                conversation_id,
                canonical_path=request.canonical_path,
                content=request.content,
                size_bytes=request.size_bytes,
                sha256=request.sha256,
                sensitive=request.sensitive,
            ).to_dict()
        except (ConversationMemoryLockedError, ConversationMemoryNotFoundError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.delete("/api/v1/conversations/{conversation_id}")
    def delete_conversation(conversation_id: str) -> dict[str, bool]:
        try:
            conversation_memory_service.delete_conversation(conversation_id)
            return {"deleted": True}
        except (ConversationMemoryLockedError, ConversationMemoryNotFoundError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.delete("/api/v1/conversations")
    def delete_all_conversations() -> dict[str, int]:
        try:
            return {"deleted_count": conversation_memory_service.delete_all_conversations()}
        except (ConversationMemoryLockedError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.get("/api/v1/memories")
    def list_memories() -> dict[str, object]:
        try:
            return {"memories": [item.to_dict() for item in conversation_memory_service.list_memories()]}
        except (ConversationMemoryLockedError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.post("/api/v1/memories")
    def create_memory(request: MemoryCreateRequest) -> dict[str, object]:
        try:
            return conversation_memory_service.create_memory(request.content).to_dict()
        except (ConversationMemoryLockedError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.delete("/api/v1/memories/{memory_id}")
    def delete_memory(memory_id: str) -> dict[str, bool]:
        try:
            conversation_memory_service.delete_memory(memory_id)
            return {"deleted": True}
        except (ConversationMemoryLockedError, ConversationMemoryNotFoundError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.delete("/api/v1/memories")
    def delete_all_memories() -> dict[str, int]:
        try:
            return {"deleted_count": conversation_memory_service.delete_all_memories()}
        except (ConversationMemoryLockedError, ConversationMemoryValidationError) as error:
            raise conversation_error(error) from error

    @app.get("/api/v1/device-agent/capabilities")
    def device_agent_capabilities() -> dict[str, object]:
        return capability_adapter.snapshot().to_dict()

    @app.post("/api/v1/device-agent/preview")
    def preview_device_agent_action(request: AgentPreviewRequest) -> dict[str, object]:
        terminal = None
        if request.terminal is not None:
            terminal = TerminalPreview(
                argv=tuple(request.terminal.argv),
                cwd=request.terminal.cwd,
                expected_effect=request.terminal.expected_effect,
            )
        try:
            action = AgentActionRequest.create(
                capability=request.capability,
                target_scope=request.target_scope,
                device_id="ubuntu-current-user-session",
                description=request.description,
                preview=request.preview,
                terminal=terminal,
            )
            return {
                "request": {
                    "action_id": action.action_id,
                    "capability": action.capability,
                    "target_scope": action.target_scope,
                    "description": action.description,
                    "preview": action.preview,
                    "terminal": action.terminal.to_dict() if action.terminal else None,
                },
                "policy": permission_engine.preview(action).to_dict(),
                "execution_enabled": False,
            }
        except Exception as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/api/v1/device-agent/launch-preview")
    def preview_application_launch(request: LaunchPreviewRequest) -> dict[str, object]:
        try:
            launch = active_launch_preview_executor.preview(request.desktop_entry)
            action = AgentActionRequest.create(
                capability=AgentCapability.LAUNCH_APP,
                target_scope=launch.canonical_desktop_path,
                device_id="ubuntu-current-user-session",
                description="User-requested application launch preview",
                preview="Launch exact desktop entry without shell execution",
                audit_metadata={
                    "desktop_id": launch.desktop_id,
                    "desktop_sha256": launch.desktop_sha256,
                    "executable_path": launch.executable_path,
                },
            )
            return {
                "launch": launch.to_dict(),
                "policy": permission_engine.preview(action).to_dict(),
                "execution_enabled": False,
            }
        except (LaunchPreviewError, Exception) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/api/v1/device-agent/launch-execute")
    def execute_application_launch(request: LaunchExecuteRequest) -> dict[str, object]:
        if not request.confirmed:
            raise HTTPException(status_code=422, detail="Fresh launch confirmation is required.")
        try:
            launch = active_launch_preview_executor.preview(request.desktop_entry)
            if launch.desktop_sha256 != request.expected_desktop_sha256:
                raise LaunchExecutionError("Desktop entry changed; preview again before launch.")
            action = AgentActionRequest.create(
                capability=AgentCapability.LAUNCH_APP,
                target_scope=launch.canonical_desktop_path,
                device_id="ubuntu-current-user-session",
                description="User-confirmed exact application launch",
                preview="Launch exact desktop entry without shell execution",
                audit_metadata={
                    "desktop_id": launch.desktop_id,
                    "desktop_sha256": launch.desktop_sha256,
                    "executable_path": launch.executable_path,
                },
            )
            authorization = permission_engine.approve(action, GrantDecision.ONCE)
            execution = active_launch_preview_executor.launch(
                launch,
                expected_desktop_sha256=request.expected_desktop_sha256,
            )
            return {
                "launch": launch.to_dict(),
                "authorization": authorization.__dict__,
                "execution": execution.to_dict(),
                "execution_enabled": True,
            }
        except (LaunchPreviewError, LaunchExecutionError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.get("/api/v1/device-agent/audit-status")
    def device_agent_audit_status() -> dict[str, object]:
        return {
            "pending_volatile_audit_count": permission_engine.pending_audit_count,
            "execution_enabled": False,
        }

    @app.post("/api/v1/device-agent/read-preview")
    def preview_read_only_action(request: ReadOnlyPreviewRequest) -> dict[str, object]:
        try:
            return read_only_executor.preview(
                request.selected_scope,
                request.requested_path,
                ReadMode(request.mode),
            ).to_dict()
        except ReadOnlyExecutorError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/api/v1/device-agent/read")
    def execute_read_only_action(request: ReadOnlyExecuteRequest) -> dict[str, object]:
        if not request.confirmed:
            raise HTTPException(status_code=422, detail="Fresh user confirmation is required.")
        try:
            preview = read_only_executor.preview(
                request.selected_scope,
                request.requested_path,
                ReadMode(request.mode),
            )
            if preview.requires_sensitive_confirmation and not request.sensitive_confirmed:
                raise HTTPException(status_code=422, detail="Sensitive content requires fresh confirmation.")
            if request.share_with_model and not request.model_share_confirmed:
                raise HTTPException(status_code=422, detail="Model sharing requires separate confirmation.")
            action = AgentActionRequest.create(
                capability=(AgentCapability.READ_METADATA if request.mode == "read_metadata" else AgentCapability.READ_TEXT),
                target_scope=preview.canonical_path,
                device_id="ubuntu-current-user-session",
                description="User-confirmed read-only action",
                preview=f"Read {request.mode} from selected canonical path",
            )
            authorization = permission_engine.approve(action, GrantDecision.ONCE)
            if request.mode == "read_metadata":
                return {
                    "preview": preview.to_dict(),
                    "authorization": authorization.__dict__,
                    "metadata": read_only_executor.read_metadata(request.selected_scope, request.requested_path).to_dict(),
                }
            result = read_only_executor.read_text(
                request.selected_scope,
                request.requested_path,
                sensitive_confirmed=request.sensitive_confirmed,
                share_with_model=request.share_with_model,
                model_share_confirmed=request.model_share_confirmed,
            )
            return {
                "preview": preview.to_dict(),
                "authorization": authorization.__dict__,
                "metadata": result.metadata.to_dict(),
                "content": result.content,
                "share_with_model": result.share_with_model,
            }
        except HTTPException:
            raise
        except ReadOnlyExecutorError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/api/v1/device-agent/model-share/preview")
    def preview_model_share(request: ModelSharePreviewRequest) -> dict[str, object]:
        try:
            return model_share_service.preview(
                selected_scope=request.selected_scope,
                requested_path=request.requested_path,
                content=request.content,
            ).to_dict()
        except ModelShareError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/api/v1/device-agent/model-share/stream")
    def stream_model_share(request: ModelShareStreamRequest) -> StreamingResponse:
        def encode_events():
            try:
                for event in model_share_service.stream(
                    selected_scope=request.selected_scope,
                    requested_path=request.requested_path,
                    content=request.content,
                    plan_id=request.plan_id,
                    operation_id=request.operation_id,
                    confirmed=request.confirmed,
                    sensitive_confirmed=request.sensitive_confirmed,
                    mode=request.mode,
                ):
                    yield json.dumps(event.to_dict(), ensure_ascii=False, separators=(",", ":")) + "\n"
            except ModelShareError as error:
                yield json.dumps({"type": "error", "message": str(error)}, ensure_ascii=False) + "\n"

        return StreamingResponse(
            encode_events(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/api/v1/device-agent/model-share/cancel/{operation_id}")
    def cancel_model_share(operation_id: str) -> dict[str, bool]:
        return {"cancelled": model_share_service.cancel(operation_id)}

    return app


app = create_app()
