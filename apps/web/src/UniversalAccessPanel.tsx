import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Eye,
  KeyRound,
  Network,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  fetchOnlineProviders,
  previewProviderAccess,
  type OnlineProvider,
  type ProviderAccessPreviewResponse,
} from "./api";
import type { AppLanguage } from "./types";

type Copy = {
  title: string;
  subtitle: string;
  provider: string;
  capability: string;
  target: string;
  categories: string;
  bytes: string;
  summary: string;
  preview: string;
  configured: string;
  notConfigured: string;
  adapter: string;
  registry: string;
  destination: string;
  digest: string;
  policy: string;
  noNetwork: string;
  vault: string;
  cost: string;
  error: string;
  close: string;
};

const copy: Record<AppLanguage, Copy> = {
  fa: {
    title: "مجوزهای سرویس‌های آنلاین",
    subtitle: "فقط پیش‌نمایش مجوز؛ هیچ سرویس خارجی خودکار اجرا نمی‌شود.",
    provider: "سرویس",
    capability: "توانایی درخواستی",
    target: "مقصد یا اثر مورد انتظار",
    categories: "دسته‌های دادهٔ اعلام‌شده",
    bytes: "حجم تقریبی خروجی",
    summary: "خلاصهٔ دادهٔ خروجی",
    preview: "پیش‌نمایش مجوز",
    configured: "کلید محلی پیکربندی شده",
    notConfigured: "کلید محلی پیکربندی نشده",
    adapter: "وضعیت رابط",
    registry: "فهرست سرویس‌ها",
    destination: "مقصد",
    digest: "هش درخواست",
    policy: "سیاست مجوز",
    noNetwork: "این مرحله هیچ اتصال خارجی برقرار نمی‌کند.",
    vault: "اجرای واقعی در آینده، Vault باز و تأیید تازهٔ یک‌باره می‌خواهد.",
    cost: "هزینه یا سهمیهٔ سرویس باید پیش از اجرای واقعی بررسی شود.",
    error: "پیش‌نمایش مجوز انجام نشد.",
    close: "بستن",
  },
  en: {
    title: "Online service permissions",
    subtitle: "Permission preview only; no external service runs automatically.",
    provider: "Provider",
    capability: "Requested capability",
    target: "Expected target or effect",
    categories: "Declared data categories",
    bytes: "Estimated outbound bytes",
    summary: "Outbound data summary",
    preview: "Preview permission",
    configured: "Local credential configured",
    notConfigured: "Local credential not configured",
    adapter: "Adapter status",
    registry: "Provider registry",
    destination: "Destination",
    digest: "Request digest",
    policy: "Permission policy",
    noNetwork: "No external connection is made at this stage.",
    vault: "Future real execution requires an unlocked Vault and fresh one-time confirmation.",
    cost: "Provider cost or quota must be reviewed before real execution.",
    error: "Permission preview could not be completed.",
    close: "Close",
  },
  ar: {
    title: "أذونات الخدمات عبر الإنترنت",
    subtitle: "معاينة إذن فقط؛ لا تعمل أي خدمة خارجية تلقائياً.",
    provider: "الخدمة",
    capability: "القدرة المطلوبة",
    target: "الهدف أو الأثر المتوقع",
    categories: "فئات البيانات المعلنة",
    bytes: "حجم الخروج التقريبي",
    summary: "ملخص البيانات الخارجة",
    preview: "معاينة الإذن",
    configured: "تم إعداد المفتاح المحلي",
    notConfigured: "لم يتم إعداد المفتاح المحلي",
    adapter: "حالة الواجهة",
    registry: "فهرس الخدمات",
    destination: "الوجهة",
    digest: "بصمة الطلب",
    policy: "سياسة الإذن",
    noNetwork: "لن يتم إجراء أي اتصال خارجي في هذه المرحلة.",
    vault: "يتطلب التنفيذ الفعلي مستقبلاً Vault مفتوحاً وتأكيداً جديداً لمرة واحدة.",
    cost: "يجب مراجعة تكلفة الخدمة أو حصتها قبل التنفيذ الفعلي.",
    error: "تعذرت معاينة الإذن.",
    close: "إغلاق",
  },
  tr: {
    title: "Çevrimiçi hizmet izinleri",
    subtitle: "Yalnızca izin önizlemesi; hiçbir dış hizmet otomatik çalışmaz.",
    provider: "Hizmet",
    capability: "İstenen yetenek",
    target: "Beklenen hedef veya etki",
    categories: "Beyan edilen veri kategorileri",
    bytes: "Tahmini dışarı giden bayt",
    summary: "Dışarı giden veri özeti",
    preview: "İzni önizle",
    configured: "Yerel kimlik bilgisi yapılandırıldı",
    notConfigured: "Yerel kimlik bilgisi yapılandırılmadı",
    adapter: "Bağdaştırıcı durumu",
    registry: "Hizmet listesi",
    destination: "Hedef",
    digest: "İstek özeti",
    policy: "İzin politikası",
    noNetwork: "Bu aşamada hiçbir dış bağlantı kurulmaz.",
    vault: "Gelecekte gerçek yürütme için açık Vault ve yeni tek seferlik onay gerekir.",
    cost: "Gerçek yürütmeden önce hizmet maliyeti veya kotası incelenmelidir.",
    error: "İzin önizlemesi tamamlanamadı.",
    close: "Kapat",
  },
};

export function UniversalAccessPanel({
  language,
  onClose,
}: {
  language: AppLanguage;
  onClose: () => void;
}) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [providers, setProviders] = useState<OnlineProvider[]>([]);
  const [providerId, setProviderId] = useState("google_gemini");
  const [capability, setCapability] = useState("google_search_grounding");
  const [target, setTarget] = useState("Google Search Grounding");
  const [categories, setCategories] = useState("synthetic_text");
  const [estimatedBytes, setEstimatedBytes] = useState("128");
  const [summary, setSummary] = useState(
    "Synthetic permission preview only; no data leaves this device.",
  );
  const [preview, setPreview] =
    useState<ProviderAccessPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedProvider = useMemo(
    () => providers.find((item) => item.provider_id === providerId) ?? null,
    [providerId, providers],
  );

  useEffect(() => {
    void fetchOnlineProviders()
      .then((result) => setProviders(result.providers))
      .catch(() => setError(t.error));
  }, [t.error]);

  const changeProvider = (next: string) => {
    const provider = providers.find((item) => item.provider_id === next);
    setProviderId(next);
    setCapability(provider?.capabilities[0] ?? "");
    setPreview(null);
  };

  const requestPreview = async () => {
    try {
      setPreview(
        await previewProviderAccess({
          provider_id: providerId,
          capability,
          target_description: target.trim(),
          outbound_summary: summary.trim(),
          data_categories: categories
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          estimated_bytes: Number(estimatedBytes),
        }),
      );
      setError(null);
    } catch (reason) {
      setPreview(null);
      setError(reason instanceof Error ? reason.message : t.error);
    }
  };

  return (
    <div className="agent-layer" dir={direction}>
      <button className="agent-backdrop" onClick={onClose} type="button" />
      <aside className="agent-panel universal-access-panel">
        <header>
          <div>
            <p className="eyebrow"><Network size={16} />{t.preview}</p>
            <h3>{t.title}</h3>
          </div>
          <button className="icon-button" onClick={onClose} type="button"><X size={20} /></button>
        </header>

        <div className="agent-content">
          <section className="agent-section">
            <div className="agent-status">
              <ShieldCheck size={18} />
              <div><strong>{t.subtitle}</strong><span>{t.noNetwork}</span></div>
            </div>
          </section>

          <section className="agent-section">
            <label><span>{t.provider}</span><select dir="ltr" value={providerId} onChange={(event) => changeProvider(event.target.value)}>{providers.map((item) => <option key={item.provider_id} value={item.provider_id}>{item.display_name}</option>)}</select></label>
            <label><span>{t.capability}</span><select dir="ltr" value={capability} onChange={(event) => { setCapability(event.target.value); setPreview(null); }}>{selectedProvider?.capabilities.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
            <label><span>{t.target}</span><input dir={direction} value={target} onChange={(event) => setTarget(event.target.value)} /></label>
            <label><span>{t.categories}</span><input dir="ltr" value={categories} onChange={(event) => setCategories(event.target.value)} /></label>
            <label><span>{t.bytes}</span><input dir="ltr" min="0" type="number" value={estimatedBytes} onChange={(event) => setEstimatedBytes(event.target.value)} /></label>
            <label><span>{t.summary}</span><textarea dir={direction} value={summary} onChange={(event) => setSummary(event.target.value)} /></label>
            <button className="button primary" onClick={() => void requestPreview()} type="button"><Eye size={16} />{t.preview}</button>
          </section>

          {selectedProvider && (
            <details className="provider-registry-details">
              <summary><KeyRound size={16} />{t.registry}</summary>
              <p><strong>{t.adapter}:</strong> <bdi dir="ltr">{selectedProvider.adapter_status}</bdi></p>
              <p>{selectedProvider.credential_configured ? t.configured : t.notConfigured}</p>
              <p className="agent-muted" dir="auto">{selectedProvider.notes}</p>
            </details>
          )}

          {preview && (
            <section className="agent-section agent-preview-result provider-access-summary">
              <p><strong>{t.destination}:</strong> <bdi dir="ltr">{preview.access.provider.display_name}</bdi></p>
              <p><strong>{t.capability}:</strong> <bdi dir="ltr">{preview.access.capability}</bdi></p>
              <p><strong>{t.categories}:</strong> <bdi dir="ltr">{preview.access.data_categories.join(", ") || "none"}</bdi></p>
              <p><strong>{t.bytes}:</strong> <bdi dir="ltr">{preview.access.estimated_bytes}</bdi></p>
              <p><strong>{t.digest}:</strong> <bdi dir="ltr">{preview.access.request_sha256}</bdi></p>
              <p className="agent-warning"><AlertTriangle size={16} />{t.noNetwork}</p>
              <p className="agent-warning"><AlertTriangle size={16} />{t.vault}</p>
              <p className="agent-warning"><AlertTriangle size={16} />{t.cost}</p>
            </section>
          )}

          {error && <p className="agent-error"><bdi dir="ltr">{error}</bdi></p>}
        </div>

        <footer><button className="button" onClick={onClose} type="button">{t.close}</button></footer>
      </aside>
    </div>
  );
}
