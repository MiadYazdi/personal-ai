import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Eye,
  KeyRound,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  fetchGoogleGroundingStatus,
  previewGoogleGrounding,
  type GoogleGroundingPreviewResponse,
  type GoogleGroundingStatus,
} from "./api";
import type { AppLanguage } from "./types";

type Copy = {
  title: string;
  subtitle: string;
  configured: string;
  notConfigured: string;
  model: string;
  query: string;
  preview: string;
  destination: string;
  tool: string;
  digest: string;
  chars: string;
  vault: string;
  noNetwork: string;
  error: string;
  close: string;
};

const copy: Record<AppLanguage, Copy> = {
  fa: {
    title: "Google Search رسمی",
    subtitle: "فقط پیش‌نمایش محلی؛ جست‌وجو تا تأیید جداگانه اجرا نمی‌شود.",
    configured: "کلید محلی پیکربندی شده است",
    notConfigured: "کلید محلی هنوز پیکربندی نشده است",
    model: "مدل Gemini",
    query: "متن جست‌وجوی ارسالی",
    preview: "پیش‌نمایش جست‌وجو",
    destination: "مقصد رسمی",
    tool: "ابزار",
    digest: "هش درخواست",
    chars: "تعداد نویسهٔ ارسالی",
    vault: "اجرای واقعی فقط با باز کردن Vault و تأیید تازهٔ یک‌باره ممکن است.",
    noNetwork: "این Preview هیچ داده‌ای به Google ارسال نمی‌کند.",
    error: "پیش‌نمایش Google انجام نشد.",
    close: "بستن",
  },
  en: {
    title: "Official Google Search",
    subtitle: "Local preview only; search does not run until separate confirmation.",
    configured: "Local credential is configured",
    notConfigured: "Local credential is not configured yet",
    model: "Gemini model",
    query: "Search text to send",
    preview: "Preview search",
    destination: "Official destination",
    tool: "Tool",
    digest: "Request digest",
    chars: "Outgoing character count",
    vault: "Real execution requires Vault Unlock and fresh one-time confirmation.",
    noNetwork: "This preview sends no data to Google.",
    error: "Google preview could not be completed.",
    close: "Close",
  },
  ar: {
    title: "بحث Google الرسمي",
    subtitle: "معاينة محلية فقط؛ لن يُنفّذ البحث قبل تأكيد منفصل.",
    configured: "تم إعداد المفتاح المحلي",
    notConfigured: "لم يتم إعداد المفتاح المحلي بعد",
    model: "نموذج Gemini",
    query: "نص البحث المُرسل",
    preview: "معاينة البحث",
    destination: "الوجهة الرسمية",
    tool: "الأداة",
    digest: "بصمة الطلب",
    chars: "عدد المحارف الخارجة",
    vault: "يتطلب التنفيذ الفعلي فتح Vault وتأكيداً جديداً لمرة واحدة.",
    noNetwork: "لا ترسل هذه المعاينة أي بيانات إلى Google.",
    error: "تعذرت معاينة Google.",
    close: "إغلاق",
  },
  tr: {
    title: "Resmî Google Arama",
    subtitle: "Yalnızca yerel önizleme; ayrı onay olmadan arama çalışmaz.",
    configured: "Yerel kimlik bilgisi yapılandırıldı",
    notConfigured: "Yerel kimlik bilgisi henüz yapılandırılmadı",
    model: "Gemini modeli",
    query: "Gönderilecek arama metni",
    preview: "Aramayı önizle",
    destination: "Resmî hedef",
    tool: "Araç",
    digest: "İstek özeti",
    chars: "Dışarı giden karakter sayısı",
    vault: "Gerçek yürütme Vault Unlock ve yeni tek seferlik onay gerektirir.",
    noNetwork: "Bu önizleme Google'a veri göndermez.",
    error: "Google önizlemesi tamamlanamadı.",
    close: "Kapat",
  },
};

export function GoogleGroundingPanel({
  language,
  onClose,
}: {
  language: AppLanguage;
  onClose: () => void;
}) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [status, setStatus] = useState<GoogleGroundingStatus | null>(null);
  const [modelId, setModelId] = useState("gemini-3.5-flash");
  const [query, setQuery] = useState(
    language === "fa"
      ? "نمونهٔ پیش‌نمایش جست‌وجوی Google؛ هیچ داده‌ای ارسال نمی‌شود."
      : "Synthetic Google Search preview; no data is sent.",
  );
  const [preview, setPreview] =
    useState<GoogleGroundingPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchGoogleGroundingStatus()
      .then(setStatus)
      .catch(() => setError(t.error));
  }, [t.error]);

  const requestPreview = async () => {
    try {
      setPreview(
        await previewGoogleGrounding({
          query: query.trim(),
          model_id: modelId.trim(),
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
      <aside className="agent-panel google-grounding-panel">
        <header>
          <div>
            <p className="eyebrow">
              <Search size={16} />
              {t.preview}
            </p>
            <h3>{t.title}</h3>
          </div>
          <button className="icon-button" onClick={onClose} type="button">
            <X size={20} />
          </button>
        </header>

        <div className="agent-content">
          <section className="agent-section">
            <div className="agent-status">
              <ShieldCheck size={18} />
              <div>
                <strong>{t.subtitle}</strong>
                <span>
                  <KeyRound size={14} />
                  {status?.configured ? t.configured : t.notConfigured}
                </span>
              </div>
            </div>
          </section>

          <section className="agent-section">
            <label>
              <span>{t.model}</span>
              <input
                dir="ltr"
                value={modelId}
                onChange={(event) => setModelId(event.target.value)}
              />
            </label>
            <label>
              <span>{t.query}</span>
              <textarea
                dir={direction}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <button
              className="button primary"
              onClick={() => void requestPreview()}
              type="button"
            >
              <Eye size={16} />
              {t.preview}
            </button>
          </section>

          {preview && (
            <section className="agent-section agent-preview-result google-summary">
              <p><strong>{t.destination}:</strong> <bdi dir="ltr">{preview.grounding.endpoint}</bdi></p>
              <p><strong>{t.tool}:</strong> <bdi dir="ltr">{preview.grounding.tool}</bdi></p>
              <p><strong>{t.model}:</strong> <bdi dir="ltr">{preview.grounding.model_id}</bdi></p>
              <p><strong>{t.chars}:</strong> <bdi dir="ltr">{preview.grounding.query_characters}</bdi></p>
              <p><strong>{t.digest}:</strong> <bdi dir="ltr">{preview.grounding.request_sha256}</bdi></p>
              <p className="agent-warning"><AlertTriangle size={16} />{t.noNetwork}</p>
              <p className="agent-warning"><AlertTriangle size={16} />{t.vault}</p>
            </section>
          )}

          {error && <p className="agent-error"><bdi dir="ltr">{error}</bdi></p>}
        </div>

        <footer>
          <button className="button" onClick={onClose} type="button">
            {t.close}
          </button>
        </footer>
      </aside>
    </div>
  );
}
