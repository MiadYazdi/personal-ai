import type {
  LocalVaultOnboardingRequest,
  LocalVaultOnboardingResponse,
  OnboardingStatus,
  PersonalAIStatus,
  ThinkingMode,
  UiPreferences,
  VaultSessionStatus,
  VaultUnlockRequest,
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8765";

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Local API returned HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

export function fetchPersonalAIStatus(): Promise<PersonalAIStatus> {
  return requestJson<PersonalAIStatus>("/api/v1/status");
}

export function fetchUiPreferences(): Promise<UiPreferences> {
  return requestJson<UiPreferences>("/api/v1/ui-preferences");
}

export function saveUiPreferences(
  preferences: UiPreferences,
): Promise<UiPreferences> {
  return requestJson<UiPreferences>("/api/v1/ui-preferences", {
    method: "PUT",
    body: JSON.stringify(preferences),
  });
}


export function fetchOnboardingStatus(): Promise<OnboardingStatus> {
  return requestJson<OnboardingStatus>("/api/v1/onboarding/status");
}


export function createLocalVault(
  request: LocalVaultOnboardingRequest,
): Promise<LocalVaultOnboardingResponse> {
  return requestJson<LocalVaultOnboardingResponse>(
    "/api/v1/onboarding/local-vault",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}


export function fetchVaultSessionStatus(): Promise<VaultSessionStatus> {
  return requestJson<VaultSessionStatus>("/api/v1/vault/status");
}

export function unlockVault(
  request: VaultUnlockRequest,
): Promise<VaultSessionStatus> {
  return requestJson<VaultSessionStatus>("/api/v1/vault/unlock", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function lockVault(): Promise<VaultSessionStatus> {
  return requestJson<VaultSessionStatus>("/api/v1/vault/lock", {
    method: "POST",
  });
}


export type LocalChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type LocalChatStreamEvent = {
  type: "delta" | "done" | "error";
  content?: string;
  message?: string;
};

export async function streamLocalChat(
  messages: LocalChatMessage[],
  mode: ThinkingMode,
  onEvent: (event: LocalChatStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, mode }),
    signal,
  });

  if (!response.ok || response.body === null) {
    throw new Error(`Local chat returned HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const emitLine = (line: string) => {
    if (line.trim()) {
      onEvent(JSON.parse(line) as LocalChatStreamEvent);
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (value) {
      buffer += decoder.decode(value, { stream: true });
    }

    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex >= 0) {
      emitLine(buffer.slice(0, newlineIndex));
      buffer = buffer.slice(newlineIndex + 1);
      newlineIndex = buffer.indexOf("\n");
    }

    if (done) {
      buffer += decoder.decode();
      emitLine(buffer);
      return;
    }
  }
}


export type SavedConversationSummary = {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type SavedConversationMessage = {
  message_id: string;
  conversation_id: string;
  sequence: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type SavedMemory = {
  memory_id: string;
  content: string;
  created_at: string;
};

export function listSavedConversations(): Promise<{ conversations: SavedConversationSummary[] }> {
  return requestJson("/api/v1/conversations");
}

export function createSavedConversation(title: string): Promise<SavedConversationSummary> {
  return requestJson("/api/v1/conversations", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export function getSavedConversation(
  conversationId: string,
): Promise<{ conversation: SavedConversationSummary; messages: SavedConversationMessage[] }> {
  return requestJson(`/api/v1/conversations/${conversationId}`);
}

export function appendSavedConversationMessage(
  conversationId: string,
  message: LocalChatMessage,
): Promise<SavedConversationMessage> {
  return requestJson(`/api/v1/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify(message),
  });
}

export function deleteSavedConversation(conversationId: string): Promise<{ deleted: boolean }> {
  return requestJson(`/api/v1/conversations/${conversationId}`, { method: "DELETE" });
}

export function deleteAllSavedConversations(): Promise<{ deleted_count: number }> {
  return requestJson("/api/v1/conversations", { method: "DELETE" });
}

export function listSavedMemories(): Promise<{ memories: SavedMemory[] }> {
  return requestJson("/api/v1/memories");
}

export function createSavedMemory(content: string): Promise<SavedMemory> {
  return requestJson("/api/v1/memories", {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function deleteSavedMemory(memoryId: string): Promise<{ deleted: boolean }> {
  return requestJson(`/api/v1/memories/${memoryId}`, { method: "DELETE" });
}

export function deleteAllSavedMemories(): Promise<{ deleted_count: number }> {
  return requestJson("/api/v1/memories", { method: "DELETE" });
}


export type DeviceAgentCapability =
  | "read_metadata"
  | "read_text"
  | "launch_app"
  | "run_terminal"
  | "write_file"
  | "delete_file"
  | "network"
  | "read_secret"
  | "admin";

export type DeviceAgentCapabilities = {
  adapter_id: string;
  platform: string;
  mode: "preview_only";
  execution_enabled: boolean;
  available_capabilities: DeviceAgentCapability[];
  guarantees: string[];
};

export type DeviceAgentPreview = {
  request: {
    action_id: string;
    capability: DeviceAgentCapability;
    target_scope: string;
    description: string;
    preview: string;
    terminal: { argv: string[]; cwd: string; expected_effect: string; shell: false } | null;
  };
  policy: {
    action_id: string;
    capability: DeviceAgentCapability;
    risk: string;
    allowed_decisions: string[];
    vault_required: boolean;
    reason: string | null;
  };
  execution_enabled: false;
};

export function fetchDeviceAgentCapabilities(): Promise<DeviceAgentCapabilities> {
  return requestJson("/api/v1/device-agent/capabilities");
}

export function previewDeviceAgentAction(payload: {
  capability: DeviceAgentCapability;
  target_scope: string;
  description: string;
  preview: string;
  terminal?: { argv: string[]; cwd: string; expected_effect: string };
}): Promise<DeviceAgentPreview> {
  return requestJson("/api/v1/device-agent/preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchDeviceAgentAuditStatus(): Promise<{
  pending_volatile_audit_count: number;
  execution_enabled: boolean;
}> {
  return requestJson("/api/v1/device-agent/audit-status");
}


export type ReadOnlyPreview = {
  selected_scope: string;
  canonical_path: string;
  mode: "read_metadata" | "read_text";
  sensitive: boolean;
  size_bytes: number;
  text_limit_bytes: number;
  requires_sensitive_confirmation: boolean;
  requires_model_share_confirmation: boolean;
};

export type ReadOnlyExecutionResult = {
  preview: ReadOnlyPreview;
  authorization: { pending_audit: boolean };
  metadata: { canonical_path: string; file_type: string; size_bytes: number; modified_ns: number; permission_octal: string; sensitive: boolean };
  content?: string;
  share_with_model?: boolean;
};

export function previewReadOnlyPath(payload: { selected_scope: string; requested_path: string; mode: "read_metadata" | "read_text" }): Promise<ReadOnlyPreview> {
  return requestJson("/api/v1/device-agent/read-preview", { method: "POST", body: JSON.stringify(payload) });
}

export function executeReadOnlyPath(payload: { selected_scope: string; requested_path: string; mode: "read_metadata" | "read_text"; confirmed: boolean; sensitive_confirmed?: boolean; share_with_model?: boolean; model_share_confirmed?: boolean }): Promise<ReadOnlyExecutionResult> {
  return requestJson("/api/v1/device-agent/read", { method: "POST", body: JSON.stringify(payload) });
}
