import { useEffect, useState } from "react";
import { AlertTriangle, Eye, Laptop, ShieldCheck, X } from "lucide-react";

import {
  fetchDeviceAgentAuditStatus,
  fetchDeviceAgentCapabilities,
  previewApplicationLaunch,
  previewDeviceAgentAction,
  type ApplicationLaunchPreview,
  type DeviceAgentCapability,
  type DeviceAgentPreview,
} from "./api";
import { ReadOnlyExecutorPanel } from "./ReadOnlyExecutorPanel";
import type { AppLanguage, ThinkingMode } from "./types";

type Text = {
  title: string;
  subtitle: string;
  adapter: string;
  preview: string;
  check: string;
  scope: string;
  description: string;
  effect: string;
  terminal: string;
  risk: string;
  allowed: string;
  vault: string;
  audit: string;
  pending: string;
  close: string;
  error: string;
  launchTitle: string;
  desktopEntry: string;
  launchPreview: string;
  applicationName: string;
  resolvedExec: string;
  digest: string;
  launchWarning: string;
};

const text: Record<AppLanguage, Text> = {
  fa: { title: "عامل دستگاه", subtitle: "فقط پیش‌نمایش سیاست مجوز؛ هیچ اقدام سیستمی اجرا نمی‌شود.", adapter: "Ubuntu فقط خواندنی", preview: "پیش‌نمایش درخواست", check: "بررسی سیاست مجوز", scope: "دامنهٔ هدف", description: "توضیح اقدام", effect: "اثر مورد انتظار", terminal: "آرگومان‌های دقیق ترمینال", risk: "سطح ریسک", allowed: "تصمیم‌های مجاز", vault: "باز کردن Vault لازم است", audit: "ثبت موقت ممیزی", pending: "مورد در انتظار", close: "بستن", error: "دادهٔ عامل دستگاه بارگذاری نشد.", launchTitle: "پیش‌نمایش باز کردن برنامه", desktopEntry: "شناسه یا مسیر ورودی برنامه", launchPreview: "بررسی برنامه", applicationName: "نام برنامه", resolvedExec: "فرمان حل‌شده", digest: "هش", launchWarning: "باز کردن برنامه از مجوزهای خود سیستم‌عامل استفاده می‌کند؛ عامل هیچ مجوزی را دور نمی‌زند." },
  en: { title: "Device Agent", subtitle: "Policy preview only; no system action can run.", adapter: "Ubuntu read-only", preview: "Action preview", check: "Check policy", scope: "Target scope", description: "Action description", effect: "Expected effect", terminal: "Exact terminal argv", risk: "Risk", allowed: "Allowed decisions", vault: "Vault Unlock required", audit: "Volatile audit", pending: "pending", close: "Close", error: "Device Agent data could not be loaded.", launchTitle: "Application launch preview", desktopEntry: "Desktop entry ID or path", launchPreview: "Preview application", applicationName: "Application name", resolvedExec: "Resolved command", digest: "Digest", launchWarning: "The launched app uses its own OS permissions; the Agent never bypasses them." },
  ar: { title: "وكيل الجهاز", subtitle: "معاينة policy فقط؛ لا يمكن تنفيذ أي action للنظام.", adapter: "Ubuntu للقراءة فقط", preview: "معاينة action", check: "فحص policy", scope: "Target scope", description: "وصف action", effect: "الأثر المتوقع", terminal: "Terminal argv الدقيق", risk: "المخاطر", allowed: "القرارات المسموحة", vault: "فتح Vault مطلوب", audit: "Audit مؤقت", pending: "قيد الانتظار", close: "إغلاق", error: "تعذر تحميل بيانات وكيل الجهاز.", launchTitle: "معاينة فتح البرنامج", desktopEntry: "معرّف أو مسار إدخال البرنامج", launchPreview: "فحص البرنامج", applicationName: "اسم البرنامج", resolvedExec: "الأمر المحلول", digest: "البصمة", launchWarning: "البرنامج المفتوح يستخدم أذونات نظام التشغيل الخاصة به؛ الوكيل لا يتجاوز أي أذونات." },
  tr: { title: "Cihaz Aracısı", subtitle: "Yalnızca policy önizlemesi; hiçbir sistem eylemi çalışamaz.", adapter: "Salt okunur Ubuntu", preview: "Action önizlemesi", check: "Policy kontrolü", scope: "Target scope", description: "Action açıklaması", effect: "Beklenen etki", terminal: "Tam terminal argv", risk: "Risk", allowed: "İzin verilen kararlar", vault: "Vault Unlock gerekli", audit: "Volatile audit", pending: "bekliyor", close: "Kapat", error: "Cihaz Aracısı verisi yüklenemedi.", launchTitle: "Uygulama açma önizlemesi", desktopEntry: "Desktop entry kimliği veya yolu", launchPreview: "Uygulamayı önizle", applicationName: "Uygulama adı", resolvedExec: "Çözümlenen komut", digest: "Özet", launchWarning: "Açılan uygulama kendi işletim sistemi izinlerini kullanır; Aracı bunları asla aşmaz." },
};

const capabilities: DeviceAgentCapability[] = ["read_metadata", "launch_app", "run_terminal", "write_file", "delete_file"];

export function DeviceAgentPanel({ language, thinkingMode, onClose }: { language: AppLanguage; thinkingMode: ThinkingMode; onClose: () => void }) {
  const t = text[language];
  const isPersian = language === "fa";
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [capability, setCapability] = useState<DeviceAgentCapability>("read_metadata");
  const [scope, setScope] = useState(isPersian ? "مسیر انتخاب‌شده" : "selected-path");
  const [description, setDescription] = useState(isPersian ? "فقط پیش‌نمایش" : "Preview only");
  const [effect, setEffect] = useState(isPersian ? "هیچ اقدامی اجرا نمی‌شود" : "No action will run");
  const [argv, setArgv] = useState("git status");
  const [desktopEntry, setDesktopEntry] = useState("");
  const [preview, setPreview] = useState<DeviceAgentPreview | null>(null);
  const [launchPreview, setLaunchPreview] = useState<ApplicationLaunchPreview | null>(null);
  const [pending, setPending] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [readOnlyOpen, setReadOnlyOpen] = useState(false);

  const load = async () => {
    try {
      const [capabilitiesResult, auditResult] = await Promise.all([fetchDeviceAgentCapabilities(), fetchDeviceAgentAuditStatus()]);
      if (capabilitiesResult.execution_enabled) setError(t.error);
      setPending(auditResult.pending_volatile_audit_count);
    } catch { setError(t.error); }
  };
  useEffect(() => { void load(); }, []);

  const checkPolicy = async () => {
    try {
      if (capability === "launch_app") {
        setLaunchPreview(await previewApplicationLaunch(desktopEntry));
        setPreview(null);
      } else {
        const payload: Parameters<typeof previewDeviceAgentAction>[0] = { capability, target_scope: scope, description, preview: effect };
        if (capability === "run_terminal") payload.terminal = { argv: argv.trim().split(/\s+/).filter(Boolean), cwd: "/tmp", expected_effect: effect };
        setPreview(await previewDeviceAgentAction(payload));
        setLaunchPreview(null);
      }
      setError(null);
    } catch { setPreview(null); setLaunchPreview(null); setError(t.error); }
  };

  return <>
    <div className="agent-layer" dir={direction}>
    <button className="agent-backdrop" onClick={onClose} type="button" />
    <aside className="agent-panel">
      <header><div><p className="eyebrow"><Laptop size={16} />{t.adapter}</p><h3>{t.title}</h3></div><button className="icon-button" onClick={onClose} type="button"><X size={20} /></button></header>
      <div className="agent-content">
        <section className="agent-section"><div className="agent-status"><ShieldCheck size={18} /><div><strong>{isPersian ? "فقط پیش‌نمایش" : "Preview only"}</strong><span>{isPersian ? "هیچ فرمان، فایل، برنامه یا اقدام دستگاه اجرا نمی‌شود." : "No command, file, app or device action can run"}</span></div></div><p>{t.subtitle}</p></section>
        <section className="agent-section"><h4>{capability === "launch_app" ? t.launchTitle : t.preview}</h4><label><span>{isPersian ? "توانمندی" : "Capability"}</span><select value={capability} onChange={(event) => { setCapability(event.target.value as DeviceAgentCapability); setLaunchPreview(null); setPreview(null); }}>{capabilities.map((item: DeviceAgentCapability) => <option key={item} value={item}>{item}</option>)}</select></label>{capability === "launch_app" ? <><label><span>{t.desktopEntry}</span><input dir="ltr" value={desktopEntry} placeholder="org.example.App.desktop" onChange={(event) => setDesktopEntry(event.target.value)} /></label><p className="agent-muted">{t.launchWarning}</p></> : <><label><span>{t.scope}</span><input dir={direction} value={scope} onChange={(event) => setScope(event.target.value)} /></label><label><span>{t.description}</span><input dir={direction} value={description} onChange={(event) => setDescription(event.target.value)} /></label><label><span>{t.effect}</span><input dir={direction} value={effect} onChange={(event) => setEffect(event.target.value)} /></label>{capability === "run_terminal" && <label><span>{t.terminal}</span><input dir="ltr" value={argv} onChange={(event) => setArgv(event.target.value)} /></label>}</>}<button className="button primary" disabled={capability === "launch_app" && !desktopEntry.trim()} onClick={() => void checkPolicy()} type="button"><Eye size={16} />{capability === "launch_app" ? t.launchPreview : t.check}</button></section>
        {preview && <section className="agent-section agent-preview-result"><p>{t.risk}: {isPersian && preview.policy.risk === "observe" ? "مشاهده" : preview.policy.risk}</p>{preview.policy.vault_required ? <p className="agent-warning"><AlertTriangle size={16} />{t.vault}</p> : <p>{t.allowed}: {isPersian && preview.policy.allowed_decisions.join(", ") === "once" ? "فقط یک‌بار" : preview.policy.allowed_decisions.join(", ") || "none"}</p>}</section>}
        {launchPreview && <section className="agent-section agent-preview-result"><p><strong>{t.applicationName}:</strong> {launchPreview.launch.application_name}</p><p><strong>{t.desktopEntry}:</strong> <bdi dir="ltr">{launchPreview.launch.desktop_id}</bdi></p><p><strong>{t.resolvedExec}:</strong> <bdi dir="ltr">{launchPreview.launch.argv.join(" ")}</bdi></p><p><strong>{t.digest}:</strong> <bdi dir="ltr">{launchPreview.launch.desktop_sha256}</bdi></p><p className="agent-muted">{t.launchWarning}</p><p>{t.allowed}: {launchPreview.policy.allowed_decisions.join(", ") || "none"}</p></section>}
        <button className="button" onClick={() => setReadOnlyOpen(true)} type="button">
          {language === "fa" ? "خواندن فقط‌خواندنی فایل" : "Read-only file access"}
        </button>
        <section className="agent-section"><h4>{t.audit}</h4><p><bdi dir="ltr">{pending}</bdi> {t.pending}</p></section>
        {error && <p className="agent-error">{error}</p>}
      </div>
      <footer><button className="button" onClick={onClose} type="button">{t.close}</button></footer>
    </aside>
    </div>
    {readOnlyOpen && <ReadOnlyExecutorPanel language={language} thinkingMode={thinkingMode} onClose={() => setReadOnlyOpen(false)} />}
  </>;
}
