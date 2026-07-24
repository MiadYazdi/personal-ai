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
    const payload = await response.json().catch(() => null) as {
      detail?: unknown;
    } | null;
    const detail = typeof payload?.detail === "string"
      ? payload.detail
      : `Local API returned HTTP ${response.status}`;
    throw new Error(detail);
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

export type ModelShareAttachmentMetadata = {
  attachment_id: string;
  canonical_path: string;
  size_bytes: number;
  sha256: string;
  sensitive: boolean;
  chunk_count: number;
  created_at: string;
};

export type SavedConversationMessage = {
  message_id: string;
  conversation_id: string;
  sequence: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  kind?: "text" | "model_share";
  model_share?: ModelShareAttachmentMetadata | null;
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

export function appendSavedConversationModelShare(
  conversationId: string,
  share: { canonical_path: string; content: string; size_bytes: number; sha256: string; sensitive: boolean },
): Promise<SavedConversationMessage> {
  return requestJson(`/api/v1/conversations/${conversationId}/model-shares`, {
    method: "POST",
    body: JSON.stringify(share),
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


export type ModelSharePlan = {
  plan_id: string; operation_id: string; canonical_path: string; source_bytes: number;
  content_sha256: string; sensitive: boolean; chunk_count: number;
  chunks: { index: number; characters: number; bytes: number }[];
  requires_sensitive_confirmation: boolean; large_share_warning: boolean;
  storage: string; destination: string;
};
export type ModelShareStreamEvent = {
  type: "progress" | "delta" | "done" | "cancelled" | "error";
  content?: string; message?: string; completed?: number; total?: number; phase?: string;
};
export function previewModelShare(payload: { selected_scope: string; requested_path: string; content: string }): Promise<ModelSharePlan> {
  return requestJson("/api/v1/device-agent/model-share/preview", { method: "POST", body: JSON.stringify(payload) });
}
export async function streamModelShare(
  payload: { selected_scope: string; requested_path: string; content: string; plan_id: string; operation_id: string; confirmed: boolean; sensitive_confirmed: boolean; mode: ThinkingMode },
  onEvent: (event: ModelShareStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/device-agent/model-share/stream`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal });
  if (!response.ok || response.body === null) throw new Error(`Local model-share returned HTTP ${response.status}`);
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
  const emit = (line: string) => { if (line.trim()) onEvent(JSON.parse(line) as ModelShareStreamEvent); };
  while (true) {
    const { done, value } = await reader.read();
    if (value) buffer += decoder.decode(value, { stream: true });
    let newline = buffer.indexOf("\n");
    while (newline >= 0) { emit(buffer.slice(0, newline)); buffer = buffer.slice(newline + 1); newline = buffer.indexOf("\n"); }
    if (done) { buffer += decoder.decode(); emit(buffer); return; }
  }
}
export function cancelModelShare(operationId: string): Promise<{ cancelled: boolean }> {
  return requestJson(`/api/v1/device-agent/model-share/cancel/${operationId}`, { method: "POST" });
}


export type ApplicationLaunchPreview = {
  launch: {
    desktop_id: string;
    canonical_desktop_path: string;
    application_name: string;
    argv: string[];
    executable_path: string;
    desktop_sha256: string;
    execution: "not_started";
  };
  policy: DeviceAgentPreview["policy"];
  execution_enabled: false;
};

export function previewApplicationLaunch(desktopEntry: string): Promise<ApplicationLaunchPreview> {
  return requestJson("/api/v1/device-agent/launch-preview", {
    method: "POST",
    body: JSON.stringify({ desktop_entry: desktopEntry }),
  });
}


export type ApplicationLaunchExecution = {
  launch: ApplicationLaunchPreview["launch"];
  authorization: { action_id: string; decision: string; pending_audit: boolean; grant_id: string | null };
  execution: { pid: number; argv: string[]; canonical_desktop_path: string; desktop_sha256: string; started: true };
  execution_enabled: true;
};

export function executeApplicationLaunch(
  desktopEntry: string,
  expectedDesktopSha256: string,
): Promise<ApplicationLaunchExecution> {
  return requestJson("/api/v1/device-agent/launch-execute", {
    method: "POST",
    body: JSON.stringify({
      desktop_entry: desktopEntry,
      expected_desktop_sha256: expectedDesktopSha256,
      confirmed: true,
    }),
  });
}

export type NativePickerMode = "open_file" | "select_directory" | "save_file" | "desktop_entry";
export type NativePickerSelection = { mode: NativePickerMode; cancelled: boolean; path: string | null };

export function selectFromSystem(mode: NativePickerMode, title: string): Promise<NativePickerSelection> {
  return requestJson("/api/v1/device-agent/native-picker", {
    method: "POST",
    body: JSON.stringify({ mode, title }),
  });
}


export type TerminalExecutionPreviewResponse = {
  terminal: {
    argv: string[];
    cwd: string;
    executable_path: string;
    expected_effect: string;
    timeout_seconds: number;
    request_sha256: string;
    shell: false;
    max_output_bytes: number;
  };
  policy: DeviceAgentPreview["policy"];
  execution_enabled: false;
};

export function previewTerminalExecution(payload: {
  argv: string[];
  cwd: string;
  expected_effect: string;
  timeout_seconds: number;
}): Promise<TerminalExecutionPreviewResponse> {
  return requestJson("/api/v1/device-agent/terminal-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}


export type WriteFilePreviewResponse = {
  write: {
    selected_scope: string;
    canonical_path: string;
    operation: "create" | "overwrite";
    old_sha256: string | null;
    new_sha256: string;
    old_size_bytes: number;
    new_size_bytes: number;
    resulting_mode: string;
    diff: string;
    diff_truncated: boolean;
    request_sha256: string;
    text_limit_bytes: number;
    diff_limit_bytes: number;
  };
  policy: DeviceAgentPreview["policy"];
  execution_enabled: false;
};

export function previewWriteFile(payload: {
  selected_scope: string;
  requested_path: string;
  content: string;
}): Promise<WriteFilePreviewResponse> {
  return requestJson("/api/v1/device-agent/write-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type OnlineControlStatus = {
  online_default_enabled: false;
  network_execution_enabled: false;
  configured_providers: string[];
  credential_storage: string;
  controlled_evolution: "proposal_only";
  automatic_code_apply: false;
  guardrails: string[];
};

export type OnlineEgressPreviewResponse = {
  egress: {
    provider_id: string;
    model_id: string;
    action: string;
    destination: string;
    outbound_summary: string;
    data_categories: string[];
    estimated_bytes: number;
    request_sha256: string;
    network_default_enabled: false;
    network_execution_enabled: false;
    requires_fresh_confirmation: true;
    requires_vault_unlock: true;
  };
  policy: DeviceAgentPreview["policy"];
  execution_enabled: false;
};

export type ControlledEvolutionPreviewResponse = {
  evolution: {
    canonical_repository_scope: string;
    proposal_summary: string;
    proposal_sha256: string;
    diff_sha256: string;
    diff_bytes: number;
    touched_files: string[];
    validation_plan: string[];
    proposal_only: true;
    apply_enabled: false;
    requires_human_review: true;
    requires_fresh_confirmation: true;
  };
  policy: DeviceAgentPreview["policy"];
  execution_enabled: false;
};

export function fetchOnlineControlStatus(): Promise<OnlineControlStatus> {
  return requestJson("/api/v1/online-control/status");
}

export function previewOnlineEgress(payload: {
  provider_id: string;
  model_id: string;
  action: "online_chat" | "web_search" | "model_update" | "source_update";
  outbound_summary: string;
  data_categories: string[];
  estimated_bytes: number;
}): Promise<OnlineEgressPreviewResponse> {
  return requestJson("/api/v1/online-control/egress-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function previewControlledEvolution(payload: {
  repository_scope: string;
  proposal_summary: string;
  proposed_diff: string;
  validation_plan: string[];
}): Promise<ControlledEvolutionPreviewResponse> {
  return requestJson("/api/v1/online-control/evolution-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type GoogleGroundingStatus = {
  provider: "google-gemini-grounding";
  configured: boolean;
  endpoint: string;
  tool: "google_search";
  network_execution_enabled: false;
  credential_source: string;
};

export type GoogleGroundingPreviewResponse = {
  grounding: {
    model_id: string;
    query_sha256: string;
    query_characters: number;
    request_sha256: string;
    endpoint: string;
    tool: "google_search";
    network_execution_enabled: false;
    requires_fresh_confirmation: true;
    requires_vault_unlock: true;
  };
  policy: DeviceAgentPreview["policy"];
  execution_enabled: false;
};

export function fetchGoogleGroundingStatus(): Promise<GoogleGroundingStatus> {
  return requestJson("/api/v1/online-control/google-grounding-status");
}

export function previewGoogleGrounding(payload: {
  query: string;
  model_id: string;
}): Promise<GoogleGroundingPreviewResponse> {
  return requestJson("/api/v1/online-control/google-grounding-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type OnlineProvider = {
  provider_id: string;
  display_name: string;
  credential_configured: boolean;
  credential_environment: string | null;
  capabilities: string[];
  adapter_status: string;
  notes: string;
  secret_exposed: false;
};

export type ProviderAccessPreviewResponse = {
  access: {
    provider: OnlineProvider;
    capability: string;
    target_description: string;
    outbound_summary_sha256: string;
    data_categories: string[];
    estimated_bytes: number;
    request_sha256: string;
    network_execution_enabled: false;
    requires_fresh_confirmation: true;
    requires_vault_unlock: true;
    cost_review_required: true;
    automatic_execution: false;
  };
  policy: DeviceAgentPreview["policy"];
  execution_enabled: false;
};

export function fetchOnlineProviders(): Promise<{
  providers: OnlineProvider[];
  network_execution_enabled: false;
  automatic_execution: false;
}> {
  return requestJson("/api/v1/online-control/providers");
}

export function previewProviderAccess(payload: {
  provider_id: string;
  capability: string;
  target_description: string;
  outbound_summary: string;
  data_categories: string[];
  estimated_bytes: number;
}): Promise<ProviderAccessPreviewResponse> {
  return requestJson("/api/v1/online-control/provider-access-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type InternetAccessSettings = {
  master_enabled: boolean;
  scopes: {
    google_grounding: boolean;
    provider_inference: boolean;
    direct_web: boolean;
    code_update: boolean;
  };
  network_execution_enabled: false;
  always_requires_fresh_confirmation: true;
  always_requires_vault_unlock: true;
  automatic_execution: false;
};

export function fetchInternetAccessSettings(): Promise<InternetAccessSettings> {
  return requestJson("/api/v1/internet-access");
}

export function saveInternetAccessSettings(payload: {
  master_enabled: boolean;
  scopes: InternetAccessSettings["scopes"];
}): Promise<InternetAccessSettings> {
  return requestJson("/api/v1/internet-access", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
