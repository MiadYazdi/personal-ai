import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Globe2,
  Save,
  ShieldCheck,
  ToggleLeft,
  ToggleRight,
  X,
} from "lucide-react";

import {
  fetchInternetAccessSettings,
  saveInternetAccessSettings,
  type InternetAccessSettings,
} from "./api";
import type { AppLanguage } from "./types";

type ScopeKey = keyof InternetAccessSettings["scopes"];

type Copy = {
  title: string;
  subtitle: string;
  master: string;
  google: string;
  providers: string;
  web: string;
  code: string;
  save: string;
  saving: string;
  saved: string;
  warning: string;
  details: string;
  error: string;
  close: string;
};

const copy: Record<AppLanguage, Copy> = {
  fa: {
    title: "مرکز دسترسی اینترنت",
    subtitle: "همهٔ سطح‌های دسترسی دست توست؛ روشن‌بودن آن‌ها اجرای خودکار نیست.",
    master: "کلید اصلی اینترنت",
    google: "Google Search با Gemini",
    providers: "مدل‌ها و سرویس‌های خارجی",
    web: "خواندن مستقیم Web",
    code: "به‌روزرسانی و اصلاح کد",
    save: "ذخیرهٔ دسترسی‌ها",
    saving: "در حال ذخیره‌سازی…",
    saved: "تنظیمات محلی ذخیره شد.",
    warning: "هر اقدام واقعی همچنان Preview، Vault باز و تأیید تازهٔ یک‌باره می‌خواهد.",
    details: "این تنظیم فقط یک فایل محلی با مجوز 0600 می‌نویسد و هیچ داده‌ای به اینترنت نمی‌فرستد.",
    error: "تنظیمات دسترسی ذخیره نشد.",
    close: "بستن",
  },
  en: {
    title: "Internet Access Center",
    subtitle: "Every access level is yours to control; enabling one never means automatic execution.",
    master: "Internet master switch",
    google: "Google Search with Gemini",
    providers: "External models and services",
    web: "Direct Web reading",
    code: "Code update and improvement",
    save: "Save access settings",
    saving: "Saving…",
    saved: "Local settings saved.",
    warning: "Every real action still requires preview, unlocked Vault, and fresh one-time confirmation.",
    details: "This setting writes only a local mode-0600 file and sends no data to the internet.",
    error: "Access settings could not be saved.",
    close: "Close",
  },
  ar: {
    title: "مركز الوصول إلى الإنترنت",
    subtitle: "كل مستويات الوصول تحت تحكمك؛ تفعيلها لا يعني التنفيذ التلقائي.",
    master: "المفتاح الرئيسي للإنترنت",
    google: "بحث Google عبر Gemini",
    providers: "النماذج والخدمات الخارجية",
    web: "قراءة Web المباشرة",
    code: "تحديث الكود وتحسينه",
    save: "حفظ إعدادات الوصول",
    saving: "جارٍ الحفظ…",
    saved: "تم حفظ الإعدادات المحلية.",
    warning: "كل إجراء فعلي ما زال يتطلب معاينة وVault مفتوحاً وتأكيداً جديداً لمرة واحدة.",
    details: "يكتب هذا الإعداد ملفاً محلياً فقط بوضع 0600 ولا يرسل بيانات إلى الإنترنت.",
    error: "تعذر حفظ إعدادات الوصول.",
    close: "إغلاق",
  },
  tr: {
    title: "İnternet Erişim Merkezi",
    subtitle: "Her erişim düzeyi senin kontrolünde; etkinleştirme otomatik yürütme anlamına gelmez.",
    master: "İnternet ana anahtarı",
    google: "Gemini ile Google Arama",
    providers: "Harici modeller ve hizmetler",
    web: "Doğrudan Web okuma",
    code: "Kod güncelleme ve iyileştirme",
    save: "Erişim ayarlarını kaydet",
    saving: "Kaydediliyor…",
    saved: "Yerel ayarlar kaydedildi.",
    warning: "Her gerçek işlem yine önizleme, açık Vault ve yeni tek seferlik onay gerektirir.",
    details: "Bu ayar yalnızca 0600 modlu yerel bir dosya yazar ve internete veri göndermez.",
    error: "Erişim ayarları kaydedilemedi.",
    close: "Kapat",
  },
};

export function InternetAccessPanel({
  language,
  onClose,
}: {
  language: AppLanguage;
  onClose: () => void;
}) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [settings, setSettings] = useState<InternetAccessSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void fetchInternetAccessSettings()
      .then(setSettings)
      .catch(() => setMessage(t.error));
  }, [t.error]);

  const toggleScope = (scope: ScopeKey) => {
    setSettings((current) => current && {
      ...current,
      scopes: {
        ...current.scopes,
        [scope]: !current.scopes[scope],
      },
    });
    setMessage(null);
  };

  const save = async () => {
    if (!settings || saving) return;
    setSaving(true);
    try {
      const saved = await saveInternetAccessSettings({
        master_enabled: settings.master_enabled,
        scopes: settings.scopes,
      });
      setSettings(saved);
      setMessage(t.saved);
    } catch {
      setMessage(t.error);
    } finally {
      setSaving(false);
    }
  };

  const rows: Array<[ScopeKey, string]> = [
    ["google_grounding", t.google],
    ["provider_inference", t.providers],
    ["direct_web", t.web],
    ["code_update", t.code],
  ];

  return (
    <div className="agent-layer" dir={direction}>
      <button className="agent-backdrop" onClick={onClose} type="button" />
      <aside className="agent-panel internet-access-panel">
        <header>
          <div>
            <p className="eyebrow"><Globe2 size={16} />{t.master}</p>
            <h3>{t.title}</h3>
          </div>
          <button className="icon-button" onClick={onClose} type="button"><X size={20} /></button>
        </header>

        <div className="agent-content">
          <section className="agent-section">
            <div className="agent-status">
              <ShieldCheck size={18} />
              <div><strong>{t.subtitle}</strong><span>{t.details}</span></div>
            </div>
          </section>

          {settings && (
            <section className="agent-section internet-access-settings">
              <button
                className="internet-access-row is-master"
                onClick={() => {
                  setSettings({
                    ...settings,
                    master_enabled: !settings.master_enabled,
                  });
                  setMessage(null);
                }}
                type="button"
              >
                <span>{t.master}</span>
                {settings.master_enabled ? <ToggleRight size={26} /> : <ToggleLeft size={26} />}
              </button>

              {rows.map(([scope, label]) => (
                <button
                  className="internet-access-row"
                  key={scope}
                  onClick={() => toggleScope(scope)}
                  type="button"
                >
                  <span>{label}</span>
                  {settings.scopes[scope] ? <ToggleRight size={24} /> : <ToggleLeft size={24} />}
                </button>
              ))}

              <button
                className="button primary"
                disabled={saving}
                onClick={() => void save()}
                type="button"
              >
                <Save size={16} />
                {saving ? t.saving : t.save}
              </button>
            </section>
          )}

          <p className="agent-warning"><AlertTriangle size={16} />{t.warning}</p>
          {message && <p className={message === t.error ? "agent-error" : "agent-muted"}>{message}</p>}
        </div>

        <footer><button className="button" onClick={onClose} type="button">{t.close}</button></footer>
      </aside>
    </div>
  );
}
