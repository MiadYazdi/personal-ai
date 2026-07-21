export type AppLanguage = "fa" | "en" | "ar" | "tr";
export type ThemeMode = "system" | "dark" | "light";
export type ThinkingMode = "quick" | "deep";

export type VaultState = "not_created" | "locked" | "unlocked";

export type VaultUnlockMethod =
  | "passphrase"
  | "recovery_bip39"
  | "recovery_base64url";
export type SidebarPlacement = "left" | "right";
export type SidebarMode = "expanded" | "compact" | "hidden";
export type SidebarWidth = "normal" | "wide";
export type MobileSidebarMode =
  | "compact"
  | "expanded";
export type FontScale = "small" | "default" | "large" | "xlarge";
export type UiDensity = "compact" | "comfortable";
export type MotionPreference = "system" | "full" | "reduced";
export type ControlsLocation =
  | "sidebar_settings"
  | "header"
  | "both";

export const WIDGET_IDS = ["vault", "model", "agent", "online"] as const;

export type WidgetId = (typeof WIDGET_IDS)[number];

export interface UiPreferences {
  schema_version: number;
  language: AppLanguage;
  theme: ThemeMode;
  accent_color: string;
  sidebar_placement: SidebarPlacement;
  sidebar_mode: SidebarMode;
  sidebar_width: SidebarWidth;
  mobile_sidebar_mode: MobileSidebarMode;
  font_scale: FontScale;
  ui_density: UiDensity;
  motion: MotionPreference;
  controls_location: ControlsLocation;
  selected_preset: "default" | "focus" | "minimal" | "custom";
  widget_order: WidgetId[];
  hidden_widgets: WidgetId[];
}

export const DEFAULT_UI_PREFERENCES: UiPreferences = {
  schema_version: 3,
  language: "fa",
  theme: "system",
  accent_color: "cyan",
  sidebar_placement: "left",
  sidebar_mode: "expanded",
  sidebar_width: "normal",
  mobile_sidebar_mode: "compact",
  font_scale: "default",
  ui_density: "comfortable",
  motion: "system",
  controls_location: "both",
  selected_preset: "default",
  widget_order: [...WIDGET_IDS],
  hidden_widgets: [],
};

export interface PersonalAIStatus {
  product_name: string;
  version: string;
  local_mode: boolean;
  online_mode: boolean;
  vault: {
    state: VaultState;
    database_exists: boolean;
  };
  model: {
    available: boolean;
    loaded: boolean;
    id: string | null;
    manifest_verified: boolean;
    thinking_modes: ThinkingMode[];
  };
  device_agent: {
    platform: string;
    state: string;
    requires_user_session: boolean;
  };
  api: {
    bind_scope: string;
    port: number;
  };
}


export interface OnboardingStatus {
  vault_configured: boolean;
  vault_state: VaultState;
  profile_available: boolean;
}

export interface VaultProfileContext {
  profile_name: string;
  address_name: string;
}

export interface VaultSessionStatus {
  vault_configured: boolean;
  vault_state: VaultState;
  profile_context: VaultProfileContext | null;
  inactivity_timeout_seconds: number;
}

export interface VaultUnlockRequest {
  method: VaultUnlockMethod;
  passphrase?: string;
  recovery_phrase?: string;
  recovery_base64url?: string;
}


export interface LocalVaultOnboardingRequest {
  profile_name: string;
  address_name: string | null;
  vault_passphrase: string;
  create_recovery_key: boolean;
}

export interface LocalVaultOnboardingResponse {
  vault_created: boolean;
  profile_id: string;
  address_name: string;
  recovery_key_created: boolean;
  recovery_phrase?: string;
  recovery_base64url?: string;
}
