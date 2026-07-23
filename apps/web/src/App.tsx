import {
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import {
  Activity,
  Bot,
  Code2,
  Cpu,
  Database,
  Eye,
  EyeOff,
  Globe,
  GripVertical,
  LayoutDashboard,
  Lock,
  Menu,
  Palette,
  PanelRight,
  RefreshCw,
  RotateCcw,
  Save,
  Settings,
  ShieldCheck,
  Sparkles,
  Type,
  X,
} from "lucide-react";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  rectSortingStrategy,
  sortableKeyboardCoordinates,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ChatComposer } from "./ChatComposer";
import { DeviceAgentPanel } from "./DeviceAgentPanel";
import { OnboardingScreen } from "./Onboarding";
import { VaultUnlockScreen } from "./VaultUnlock";
import {
  fetchOnboardingStatus,
  fetchPersonalAIStatus,
  fetchUiPreferences,
  saveUiPreferences,
} from "./api";
import { localeFor } from "./locales";
import {
  DEFAULT_UI_PREFERENCES,
  type AppLanguage,
  type OnboardingStatus,
  type PersonalAIStatus,
  type SidebarMode,
  type ThinkingMode,
  type UiPreferences,
  type WidgetId,
} from "./types";

const ACCENTS: Record<string, string> = {
  cyan: "#22d3ee",
  violet: "#a78bfa",
  emerald: "#34d399",
  amber: "#fbbf24",
  rose: "#fb7185",
};

const PRESETS: Record<"default" | "focus" | "minimal", UiPreferences> = {
  default: DEFAULT_UI_PREFERENCES,
  focus: {
    ...DEFAULT_UI_PREFERENCES,
    theme: "dark",
    sidebar_mode: "compact",
    selected_preset: "focus",
    widget_order: ["model", "vault", "agent", "online"],
    hidden_widgets: ["online"],
  },
  minimal: {
    ...DEFAULT_UI_PREFERENCES,
    sidebar_mode: "compact",
    selected_preset: "minimal",
    widget_order: ["model", "vault", "agent", "online"],
    hidden_widgets: ["agent", "online"],
  },
};

function accentHex(value: string): string {
  return ACCENTS[value] ?? value;
}

function StatusCard({
  icon,
  label,
  value,
  detail,
  direction,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  detail: string;
  direction: "rtl" | "ltr";
}) {
  return (
    <article className="status-card" dir={direction}>
      <div className="status-card-icon">{icon}</div>
      <div>
        <p className="status-card-label">{label}</p>
        <p className="status-card-value">{value}</p>
        <p className="status-card-detail">{detail}</p>
      </div>
    </article>
  );
}

function SortableWidget({
  id,
  label,
  children,
}: {
  id: WidgetId;
  label: string;
  children: ReactNode;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  return (
    <div
      className={isDragging ? "sortable-widget is-dragging" : "sortable-widget"}
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
      }}
    >
      <button
        aria-label={label}
        className="drag-handle"
        type="button"
        {...attributes}
        {...listeners}
      >
        <GripVertical size={18} />
      </button>
      {children}
    </div>
  );
}

export default function App() {
  const [status, setStatus] = useState<PersonalAIStatus | null>(null);
  const [onboardingStatus, setOnboardingStatus] =
    useState<OnboardingStatus | null>(null);
  const [preferences, setPreferences] = useState<UiPreferences>(
    DEFAULT_UI_PREFERENCES,
  );
  const [savedPreferences, setSavedPreferences] =
    useState<UiPreferences>(DEFAULT_UI_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sidebarSaving, setSidebarSaving] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [agentPanelOpen, setAgentPanelOpen] = useState(false);
  const [languageDropdownOpen, setLanguageDropdownOpen] =
    useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(
    () => window.matchMedia("(max-width: 900px)").matches,
  );
  const [apiError, setApiError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [thinkingMode, setThinkingMode] =
    useState<ThinkingMode>("quick");
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches,
  );

  const locale = localeFor(preferences.language);
  const t = locale.labels;
  const isDark =
    preferences.theme === "dark" ||
    (preferences.theme === "system" && systemDark);
  const accent = accentHex(preferences.accent_color);
  const isDirty =
    JSON.stringify(preferences) !== JSON.stringify(savedPreferences);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const shellStyle = useMemo(
    () =>
      ({
        "--accent": accent,
        "--accent-soft": `${accent}24`,
      }) as CSSProperties,
    [accent],
  );

  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const updateViewport = () => setIsMobileViewport(media.matches);
    media.addEventListener("change", updateViewport);
    return () => media.removeEventListener("change", updateViewport);
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setSystemDark(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  const refreshBackend = async () => {
    setLoading(true);
    setApiError(null);

    const [
      statusResult,
      preferenceResult,
      onboardingResult,
    ] = await Promise.allSettled([
      fetchPersonalAIStatus(),
      fetchUiPreferences(),
      fetchOnboardingStatus(),
    ]);

    if (statusResult.status === "fulfilled") {
      setStatus(statusResult.value);
    } else {
      setApiError(t.loadError);
    }

    if (preferenceResult.status === "fulfilled") {
      setPreferences(preferenceResult.value);
      setSavedPreferences(preferenceResult.value);
    } else {
      setApiError(t.loadError);
    }

    if (onboardingResult.status === "fulfilled") {
      setOnboardingStatus(onboardingResult.value);
    } else {
      setApiError(t.loadError);
    }

    setLoading(false);
  };

  useEffect(() => {
    void refreshBackend();
    // Initial fetch only. Refresh stays a user action.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const saveAllPreferences = async () => {
    setSaving(true);
    setSaveMessage(null);

    try {
      const saved = await saveUiPreferences(preferences);
      setPreferences(saved);
      setSavedPreferences(saved);
      setSaveMessage(t.saved);
    } catch {
      setSaveMessage(t.saveError);
    } finally {
      setSaving(false);
    }
  };

  const updateDraft = (patch: Partial<UiPreferences>) => {
    setSaveMessage(null);
    setPreferences((current) => ({
      ...current,
      ...patch,
      selected_preset: patch.selected_preset ?? "custom",
    }));
  };

  const saveLanguageImmediately = async (language: AppLanguage) => {
    const previousSaved = savedPreferences;
    const payload = { ...previousSaved, language };

    setPreferences((current) => ({ ...current, language }));
    setSaveMessage(null);

    try {
      const saved = await saveUiPreferences(payload);
      setSavedPreferences(saved);
    } catch {
      setPreferences((current) =>
        current.language === language
          ? { ...current, language: previousSaved.language }
          : current,
      );
      setSaveMessage(t.saveError);
    }
  };

  const toggleSidebar = async () => {
    const previousSaved = savedPreferences;

    if (isMobileViewport) {
      const nextMode: UiPreferences["mobile_sidebar_mode"] =
        preferences.mobile_sidebar_mode === "compact"
          ? "expanded"
          : "compact";

      const payload = {
        ...previousSaved,
        mobile_sidebar_mode: nextMode,
      };

      setPreferences((current) => ({
        ...current,
        mobile_sidebar_mode: nextMode,
      }));
      setSidebarSaving(true);
      setSaveMessage(null);

      try {
        const saved = await saveUiPreferences(payload);
        setSavedPreferences(saved);
      } catch {
        setPreferences((current) =>
          current.mobile_sidebar_mode === nextMode
            ? {
                ...current,
                mobile_sidebar_mode:
                  previousSaved.mobile_sidebar_mode,
              }
            : current,
        );
        setSaveMessage(t.saveError);
      } finally {
        setSidebarSaving(false);
      }

      return;
    }

    const nextMode: SidebarMode =
      preferences.sidebar_mode === "expanded"
        ? "compact"
        : "expanded";

    const payload = {
      ...previousSaved,
      sidebar_mode: nextMode,
    };

    setPreferences((current) => ({
      ...current,
      sidebar_mode: nextMode,
    }));
    setSidebarSaving(true);
    setSaveMessage(null);

    try {
      const saved = await saveUiPreferences(payload);
      setSavedPreferences(saved);
    } catch {
      setPreferences((current) =>
        current.sidebar_mode === nextMode
          ? {
              ...current,
              sidebar_mode: previousSaved.sidebar_mode,
            }
          : current,
      );
      setSaveMessage(t.saveError);
    } finally {
      setSidebarSaving(false);
    }
  };

  const applyPreset = (
    preset: "default" | "focus" | "minimal",
  ) => {
    const next = PRESETS[preset];
    setSaveMessage(null);
    setPreferences({
      ...next,
      language: preferences.language,
      sidebar_placement: preferences.sidebar_placement,
      sidebar_width: preferences.sidebar_width,
      font_scale: preferences.font_scale,
      ui_density: preferences.ui_density,
      motion: preferences.motion,
      controls_location: preferences.controls_location,
      widget_order: [...next.widget_order],
      hidden_widgets: [...next.hidden_widgets],
    });
  };

  const toggleWidget = (widgetId: WidgetId) => {
    setPreferences((current) => {
      const hidden = new Set(current.hidden_widgets);
      hidden.has(widgetId) ? hidden.delete(widgetId) : hidden.add(widgetId);

      return {
        ...current,
        selected_preset: "custom",
        hidden_widgets: [...hidden],
      };
    });
  };

  const isHidden = (widgetId: WidgetId) =>
    preferences.hidden_widgets.includes(widgetId);

  // The local model remains available to future chat work, but its
  // dashboard card is intentionally not shown in the personal UI.
  const visibleWidgetIds = preferences.widget_order.filter(
    (widgetId) => widgetId !== "model" && !isHidden(widgetId),
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const activeId = active.id as WidgetId;
    const overId = over.id as WidgetId;

    setPreferences((current) => {
      const visible = current.widget_order.filter(
        (widgetId) => widgetId !== "model" && !current.hidden_widgets.includes(widgetId),
      );
      const oldIndex = visible.indexOf(activeId);
      const newIndex = visible.indexOf(overId);

      if (oldIndex < 0 || newIndex < 0) {
        return current;
      }

      const reordered = arrayMove(visible, oldIndex, newIndex);
      let visibleIndex = 0;

      return {
        ...current,
        selected_preset: "custom",
        widget_order: current.widget_order.map((widgetId) => {
          if (current.hidden_widgets.includes(widgetId)) {
            return widgetId;
          }
          const next = reordered[visibleIndex];
          visibleIndex += 1;
          return next;
        }),
      };
    });
  };

  const vaultValue =
    status?.vault.state === "unlocked"
      ? t.unlocked
      : status?.vault.state === "locked"
        ? t.locked
        : t.setupRequired;
  const agentValue =
    status?.device_agent.state === "not_started"
      ? t.notStarted
      : status?.device_agent.state ?? t.notStarted;

  const widgets: Record<WidgetId, ReactNode> = {
    vault: (
      <StatusCard
        detail={status?.vault.database_exists ? "SQLite" : ""}
        direction={locale.direction}
        icon={<Lock size={20} />}
        label={t.vault}
        value={vaultValue}
      />
    ),
    model: (
      <StatusCard
        detail={status?.model.id ?? ""}
        direction={locale.direction}
        icon={<Cpu size={20} />}
        label={t.model}
        value={status?.model.available ? t.ready : t.setupRequired}
      />
    ),
    agent: (
      <StatusCard
        detail={status?.device_agent.platform ?? "ubuntu"}
        direction={locale.direction}
        icon={<Code2 size={20} />}
        label={t.agent}
        value={agentValue}
      />
    ),
    online: (
      <StatusCard
        detail={t.noExternal}
        direction={locale.direction}
        icon={<Globe size={20} />}
        label={t.online}
        value={t.onlineDisabled}
      />
    ),
  };

  const mobileSidebarExpanded =
    isMobileViewport &&
    preferences.mobile_sidebar_mode === "expanded";

  const sidebarVisible = preferences.sidebar_mode !== "hidden";
  const renderSidebar = isMobileViewport || sidebarVisible;
  const sidebarLabelsVisible =
    preferences.sidebar_mode === "expanded" ||
    mobileSidebarExpanded;

  const showHeaderControls =
    preferences.controls_location === "header" ||
    preferences.controls_location === "both";
  const showSidebarSettings =
    preferences.controls_location === "sidebar_settings" ||
    preferences.controls_location === "both";

  const showSidebarFooter =
    preferences.controls_location !== "header";

  const sidebarClasses = [
    "app-sidebar",
    preferences.sidebar_mode === "compact" ? "is-compact" : "",
    preferences.sidebar_width === "wide" ? "is-wide" : "",
    isMobileViewport ? "is-mobile-fixed" : "",
    mobileSidebarExpanded ? "is-mobile-expanded" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <main
      className="app-shell"
      data-density={preferences.ui_density}
      data-font-scale={preferences.font_scale}
      data-motion={preferences.motion}
      data-theme={isDark ? "dark" : "light"}
      data-onboarding={
        onboardingStatus && !onboardingStatus.vault_configured
          ? "true"
          : "false"
      }
      dir={locale.direction}
      lang={preferences.language}
      style={shellStyle}
    >
      <div
        className={`app-layout ${
          preferences.sidebar_placement === "right"
            ? "sidebar-right"
            : "sidebar-left"
        }`}
      dir="ltr"
      >
        {renderSidebar && (
          <aside
            className={`${sidebarClasses} ${
              mobileSidebarExpanded ? "is-mobile-expanded" : ""
            }`}
            dir={locale.direction}
          >
            <div className="brand-row">
              <div className="brand-identity">
                <div className="brand-icon">
                  <Bot size={24} />
                </div>
                {sidebarLabelsVisible && (
                  <div>
                    <h1>{t.product}</h1>
                    <p>v0.1.0 · local-first</p>
                  </div>
                )}
              </div>

              <button
                aria-label={t.compact}
                className="sidebar-toggle-button"
                disabled={sidebarSaving}
                onClick={() => void toggleSidebar()}
                type="button"
              >
                <PanelRight
                  className={
                    preferences.sidebar_mode === "compact"
                      ? "is-sidebar-compact"
                      : ""
                  }
                  size={18}
                />
              </button>
            </div>

            <nav className="sidebar-nav">
              <button className="sidebar-link" type="button">
                <LayoutDashboard size={18} />
                {sidebarLabelsVisible && (
                  <span>{t.conversation}</span>
                )}
              </button>
              <button className="sidebar-link" type="button">
                <Database size={18} />
                {sidebarLabelsVisible && (
                  <span>{t.widgets}</span>
                )}
              </button>
              <button
                className="sidebar-link"
                onClick={() => setAgentPanelOpen(true)}
                type="button"
              >
                <Activity size={18} />
                {sidebarLabelsVisible && (
                  <span>{t.agent}</span>
                )}
              </button>
              {showSidebarSettings && (
                <button
                  className="sidebar-link"
                  onClick={() => {
                setPanelOpen(true);
              }}
                  type="button"
                >
                  <Settings size={18} />
                  {sidebarLabelsVisible && (
                    <span>{t.settings}</span>
                  )}
                </button>
              )}
            </nav>

            <div className="sidebar-footer">
              <div className="local-card">
                <ShieldCheck size={16} />
                {sidebarLabelsVisible && (
                  <div>
                    <strong>{t.localMode}</strong>
                    <p>{t.noExternal}</p>
                  </div>
                )}
              </div>

              {showSidebarFooter && (
                <div className="sidebar-footer-controls">
                  <button
                    aria-label={t.refresh}
                    className="sidebar-footer-button"
                    disabled={loading}
                    onClick={() => void refreshBackend()}
                    title={t.refresh}
                    type="button"
                  >
                    <RefreshCw
                      className={loading ? "spin" : ""}
                      size={18}
                    />
                  </button>
                </div>
              )}
            </div>
          </aside>
        )}

        <section className="app-content" dir={locale.direction}>
          <header className="app-header" dir="ltr">
            <div className="header-title" dir={locale.direction}>
              <p className="eyebrow">
                <Sparkles size={16} />
                {t.subtitle}
              </p>
              <h2>{t.conversation}</h2>
            </div>

            {showHeaderControls && (
              <div className="header-controls">
                <button
                  className="icon-button"
                  onClick={() => {
                setPanelOpen(true);
              }}
                  title={t.openControls}
                  type="button"
                >
                  <Settings size={18} />
                </button>
                <button
                  className="icon-button"
                  disabled={loading}
                  onClick={() => void refreshBackend()}
                  title={t.refresh}
                  type="button"
                >
                  <RefreshCw className={loading ? "spin" : ""} size={18} />
                </button>
              </div>
            )}
          </header>

          {!sidebarVisible && (
            <button
              className="floating-sidebar-button"
              onClick={() =>
                setPreferences((current) => ({
                  ...current,
                  sidebar_mode: "expanded",
                }))
              }
              title={t.sidebar}
              type="button"
            >
              <Menu size={19} />
            </button>
          )}

          {onboardingStatus && !onboardingStatus.vault_configured && (
            <OnboardingScreen
              language={preferences.language}
              onVaultCreated={() => void refreshBackend()}
              status={onboardingStatus}
            />
          )}

          {onboardingStatus?.vault_configured && (
            <VaultUnlockScreen
              language={preferences.language}
              onVaultSessionChanged={() => void refreshBackend()}
            />
          )}

          <DndContext
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
            sensors={sensors}
          >
            <SortableContext
              items={visibleWidgetIds}
              strategy={rectSortingStrategy}
            >
              <section className="widget-grid">
                {visibleWidgetIds.map((widgetId) => (
                  <SortableWidget
                    id={widgetId}
                    key={widgetId}
                    label={t.dragHelp}
                  >
                    {widgets[widgetId]}
                  </SortableWidget>
                ))}
              </section>
            </SortableContext>
          </DndContext>

          <section className="workspace-card">
            <div className="workspace-toolbar" dir="ltr">
              <div className="workspace-toolbar-copy" dir={locale.direction}>
                <p className="workspace-title">{t.systemStatus}</p>
                <p className="workspace-description">
                  {apiError ?? t.modelMessage}
                </p>
              </div>

              <div className="thinking-toggle">
                {(["quick", "deep"] as ThinkingMode[]).map((mode) => (
                  <button
                    className={thinkingMode === mode ? "is-active" : ""}
                    key={mode}
                    onClick={() => setThinkingMode(mode)}
                    type="button"
                  >
                    {mode === "quick" ? t.quick : t.deep}
                  </button>
                ))}
              </div>
            </div>

            <ChatComposer
              language={preferences.language}
              mode={thinkingMode}
            />
          </section>
        </section>
      </div>

      {agentPanelOpen && (
        <DeviceAgentPanel
          language={preferences.language}
          thinkingMode={thinkingMode}
          onClose={() => setAgentPanelOpen(false)}
        />
      )}

      {panelOpen && (
        <div className="settings-layer">
          <button
            aria-label={t.close}
            className="settings-backdrop"
            onClick={() => setPanelOpen(false)}
            type="button"
          />

          <aside className="settings-panel">
            <header>
              <div>
                <p className="eyebrow">
                  <Settings size={16} />
                  {t.appMenu}
                </p>
                <h3>{t.settings}</h3>
              </div>
              <button
                aria-label={t.close}
                className="icon-button"
                onClick={() => setPanelOpen(false)}
                type="button"
              >
                <X size={20} />
              </button>
            </header>

            <div className="settings-content">
              <section className="settings-section">
                <div className="section-heading">
                  <Globe size={18} />
                  <span>{t.language}</span>
                </div>
                <div className="language-dropdown">
                  <button
                    className="language-dropdown-trigger"
                    onClick={() =>
                      setLanguageDropdownOpen((current) => !current)
                    }
                    type="button"
                  >
                    <span>
                      {{
                        fa: "فارسی",
                        en: "English",
                        ar: "العربية",
                        tr: "Türkçe",
                      }[preferences.language]}
                    </span>
                    <span aria-hidden="true">⌄</span>
                  </button>

                  {languageDropdownOpen && (
                    <div className="language-dropdown-menu">
                      {[
                        ["fa", "فارسی"],
                        ["en", "English"],
                        ["ar", "العربية"],
                        ["tr", "Türkçe"],
                      ].map(([code, label]) => (
                        <button
                          className={
                            preferences.language === code
                              ? "is-active"
                              : ""
                          }
                          key={code}
                          onClick={() => {
                            void saveLanguageImmediately(
                              code as AppLanguage,
                            );
                            setLanguageDropdownOpen(false);
                          }}
                          type="button"
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </section>

              <section className="settings-section">
                <div className="section-heading">
                  <Palette size={18} />
                  <span>{t.theme}</span>
                </div>
                <div className="segmented-control">
                  {(["system", "dark", "light"] as const).map((theme) => (
                    <button
                      className={
                        preferences.theme === theme ? "is-active" : ""
                      }
                      key={theme}
                      onClick={() => updateDraft({ theme })}
                      type="button"
                    >
                      {t[theme]}
                    </button>
                  ))}
                </div>

                <div className="section-heading top-gap">
                  <Palette size={18} />
                  <span>{t.accent}</span>
                </div>
                <div className="accent-palette">
                  {Object.entries(ACCENTS).map(([name, color]) => (
                    <button
                      className={
                        preferences.accent_color === name
                          ? "accent-option is-selected"
                          : "accent-option"
                      }
                      key={name}
                      onClick={() =>
                        updateDraft({ accent_color: name })
                      }
                      style={{ backgroundColor: color }}
                      type="button"
                    />
                  ))}
                </div>
                <label className="color-input-row">
                  <span>{t.customColor}</span>
                  <input
                    onChange={(event) =>
                      updateDraft({ accent_color: event.target.value })
                    }
                    type="color"
                    value={accent}
                  />
                </label>
              </section>

              <section className="settings-section">
                <div className="section-heading">
                  <PanelRight size={18} />
                  <span>{t.sidebar}</span>
                </div>

                <SettingsChoice
                  label={t.placement}
                  options={[
                    ["left", t.left],
                    ["right", t.right],
                  ]}
                  value={preferences.sidebar_placement}
                  onChange={(value) =>
                    updateDraft({
                      sidebar_placement: value as "left" | "right",
                    })
                  }
                />

                <SettingsChoice
                  label={t.mode}
                  options={[
                    ["expanded", t.expanded],
                    ["compact", t.compact],
                    ["hidden", t.hidden],
                  ]}
                  value={preferences.sidebar_mode}
                  onChange={(value) =>
                    updateDraft({
                      sidebar_mode: value as SidebarMode,
                    })
                  }
                />

                <SettingsChoice
                  label={t.width}
                  options={[
                    ["normal", t.normal],
                    ["wide", t.wide],
                  ]}
                  value={preferences.sidebar_width}
                  onChange={(value) =>
                    updateDraft({
                      sidebar_width: value as "normal" | "wide",
                    })
                  }
                />
              </section>

              <section className="settings-section">
                <div className="section-heading">
                  <PanelRight size={18} />
                  <span>{t.mobileBehavior}</span>
                </div>

                <SettingsChoice
                  label={t.mobileBehavior}
                  options={[
                    ["compact", t.compact],
                    ["expanded", t.expanded],
                  ]}
                  value={preferences.mobile_sidebar_mode}
                  onChange={(value) =>
                    updateDraft({
                      mobile_sidebar_mode:
                        value as UiPreferences["mobile_sidebar_mode"],
                    })
                  }
                />
              </section>

              <section className="settings-section">
                <div className="section-heading">
                  <Type size={18} />
                  <span>{t.fontScale}</span>
                </div>

                <SettingsChoice
                  label={t.fontScale}
                  options={[
                    ["small", t.small],
                    ["default", t.default],
                    ["large", t.large],
                    ["xlarge", t.xlarge],
                  ]}
                  value={preferences.font_scale}
                  onChange={(value) =>
                    updateDraft({
                      font_scale: value as UiPreferences["font_scale"],
                    })
                  }
                />

                <SettingsChoice
                  label={t.density}
                  options={[
                    ["compact", t.compact],
                    ["comfortable", t.comfortable],
                  ]}
                  value={preferences.ui_density}
                  onChange={(value) =>
                    updateDraft({
                      ui_density: value as UiPreferences["ui_density"],
                    })
                  }
                />

                <SettingsChoice
                  label={t.motion}
                  options={[
                    ["system", t.system],
                    ["full", t.full],
                    ["reduced", t.reduced],
                  ]}
                  value={preferences.motion}
                  onChange={(value) =>
                    updateDraft({
                      motion: value as UiPreferences["motion"],
                    })
                  }
                />
              </section>

              <section className="settings-section">
                <div className="section-heading">
                  <Settings size={18} />
                  <span>{t.controlsLocation}</span>
                </div>

                <SettingsChoice
                  label={t.controlsLocation}
                  options={[
                    ["sidebar_settings", t.sidebarSettings],
                    ["header", t.header],
                    ["both", t.both],
                  ]}
                  value={preferences.controls_location}
                  onChange={(value) =>
                    updateDraft({
                      controls_location:
                        value as UiPreferences["controls_location"],
                    })
                  }
                />
              </section>

              <section className="settings-section">
                <div className="section-heading">
                  <LayoutDashboard size={18} />
                  <span>{t.presets}</span>
                </div>
                <div className="preset-grid">
                  {(["default", "focus", "minimal"] as const).map(
                    (preset) => (
                      <button
                        className={
                          preferences.selected_preset === preset
                            ? "preset-button is-active"
                            : "preset-button"
                        }
                        key={preset}
                        onClick={() => applyPreset(preset)}
                        type="button"
                      >
                        {preset === "default"
                          ? t.default
                          : preset === "focus"
                            ? t.focus
                            : t.minimal}
                      </button>
                    ),
                  )}
                </div>
              </section>

              <section className="settings-section">
                <div className="section-heading">
                  <LayoutDashboard size={18} />
                  <span>{t.widgets}</span>
                </div>
                <div className="widget-toggle-list">
                  {preferences.widget_order
                    .filter((widgetId) => widgetId !== "model")
                    .map((widgetId) => (
                    <button
                      className="widget-toggle-row"
                      key={widgetId}
                      onClick={() => toggleWidget(widgetId)}
                      type="button"
                    >
                      <span>{widgetsLabel(t, widgetId)}</span>
                      <span>
                        {isHidden(widgetId) ? (
                          <>
                            <EyeOff size={16} />
                            {t.show}
                          </>
                        ) : (
                          <>
                            <Eye size={16} />
                            {t.hide}
                          </>
                        )}
                      </span>
                    </button>
                  ))}
                </div>
                <p className="field-help">{t.dragHelp}</p>
              </section>

              <section className="settings-section">
                <button
                  className="button secondary full-width"
                  onClick={() => applyPreset("default")}
                  type="button"
                >
                  <RotateCcw size={16} />
                  {t.reset}
                </button>
              </section>
            </div>

            <footer>
              <span className="save-status">
                {saveMessage ?? (isDirty ? t.unsaved : t.saved)}
              </span>
              <button
                className="button primary"
                disabled={saving || !isDirty}
                onClick={() => void saveAllPreferences()}
                type="button"
              >
                <Save size={16} />
                {saving ? t.saving : t.save}
              </button>
            </footer>
          </aside>
        </div>
      )}
    </main>
  );
}

function SettingsChoice({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: [string, string][];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="choice-row">
      <span>{label}</span>
      <div className="segmented-control">
        {options.map(([optionValue, optionLabel]) => (
          <button
            className={value === optionValue ? "is-active" : ""}
            key={optionValue}
            onClick={() => onChange(optionValue)}
            type="button"
          >
            {optionLabel}
          </button>
        ))}
      </div>
    </div>
  );
}

function widgetsLabel(
  labels: Record<string, string>,
  widgetId: WidgetId,
): string {
  if (widgetId === "vault") return labels.vault;
  if (widgetId === "model") return labels.model;
  if (widgetId === "agent") return labels.agent;
  return labels.online;
}
