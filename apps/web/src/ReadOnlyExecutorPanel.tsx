import { useState, type FormEvent } from "react";
import { AlertTriangle, Eye, FileText, LockKeyhole, X } from "lucide-react";

import {
  executeReadOnlyPath,
  previewReadOnlyPath,
  type ReadOnlyExecutionResult,
  type ReadOnlyPreview,
} from "./api";
import type { AppLanguage } from "./types";

type Copy = {
  title: string;
  subtitle: string;
  path: string;
  mode: string;
  metadata: string;
  text: string;
  preview: string;
  previewReady: string;
  canonical: string;
  size: string;
  sensitive: string;
  sensitiveWarning: string;
  sensitiveDialog: string;
  confirmRead: string;
  read: string;
  reading: string;
  contentTemporary: string;
  modelSeparate: string;
  error: string;
  close: string;
  result: string;
};

const copy: Record<AppLanguage, Copy> = {
  fa: {
    title: "دسترسی فقط‌خواندنی",
    subtitle: "فقط مسیر انتخاب‌شده بررسی می‌شود؛ هیچ پیمایش، نوشتن یا اجرای فرمانی انجام نمی‌شود.",
    path: "مسیر انتخاب‌شده",
    mode: "نوع خواندن",
    metadata: "اطلاعات پایه",
    text: "متن فایل",
    preview: "نمایش پیش‌نمایش",
    previewReady: "پیش‌نمایش آماده است. برای خواندن همین مورد، دکمهٔ زیر را انتخاب کنید.",
    canonical: "مسیر قطعی",
    size: "اندازه",
    sensitive: "مسیر حساس",
    sensitiveWarning: "محتوای حساس فقط با تأیید تازه خوانده می‌شود و خودکار به مدل ارسال نمی‌شود.",
    sensitiveDialog: "این مسیر حساس است. آیا می‌خواهید فقط همین موردِ پیش‌نمایش‌شده را بخوانید؟",
    confirmRead: "می‌دانم این خواندن فقط برای همین مسیرِ پیش‌نمایش‌شده است.",
    read: "خواندن همین مورد",
    reading: "در حال خواندن…",
    contentTemporary: "نتیجه موقت است و در حافظه یا Vault ذخیره نمی‌شود.",
    modelSeparate: "اشتراک‌گذاری با مدل به تأیید جداگانه نیاز دارد و در این بخش فعال نیست.",
    error: "پیش‌نمایش یا خواندن مسیر انجام نشد.",
    close: "بستن",
    result: "نتیجهٔ خواندن",
  },
  en: {
    title: "Read-only access",
    subtitle: "Only the selected path is inspected; no scan, write, or command execution occurs.",
    path: "Selected path",
    mode: "Read mode",
    metadata: "Metadata",
    text: "File text",
    preview: "Show preview",
    previewReady: "The preview is ready. Choose the button below to read this exact item.",
    canonical: "Canonical path",
    size: "Size",
    sensitive: "Sensitive path",
    sensitiveWarning: "Sensitive content needs fresh confirmation and is never sent to the model automatically.",
    sensitiveDialog: "This is a sensitive path. Read only this previewed item?",
    confirmRead: "I understand that this read applies only to this previewed path.",
    read: "Read this item",
    reading: "Reading…",
    contentTemporary: "The result is temporary and is not stored in memory or Vault.",
    modelSeparate: "Sharing with the model needs separate confirmation and is not enabled here.",
    error: "The path preview or read could not be completed.",
    close: "Close",
    result: "Read result",
  },
  ar: {
    title: "وصول للقراءة فقط",
    subtitle: "يُفحَص المسار المحدد فقط؛ لا يتم مسح أو كتابة أو تنفيذ أوامر.",
    path: "المسار المحدد",
    mode: "نوع القراءة",
    metadata: "معلومات أساسية",
    text: "نص الملف",
    preview: "إظهار المعاينة",
    previewReady: "المعاينة جاهزة. اختر الزر أدناه لقراءة هذا العنصر نفسه.",
    canonical: "المسار الفعلي",
    size: "الحجم",
    sensitive: "مسار حساس",
    sensitiveWarning: "المحتوى الحساس يحتاج تأكيداً جديداً ولا يُرسل إلى النموذج تلقائياً.",
    sensitiveDialog: "هذا مسار حساس. هل تريد قراءة هذا العنصر المعروض في المعاينة فقط؟",
    confirmRead: "أفهم أن هذه القراءة تخص هذا المسار المعروض في المعاينة فقط.",
    read: "قراءة هذا العنصر",
    reading: "جارٍ القراءة…",
    contentTemporary: "النتيجة مؤقتة ولا تُحفظ في الذاكرة أو Vault.",
    modelSeparate: "مشاركة المحتوى مع النموذج تحتاج تأكيداً منفصلاً وليست مفعلة هنا.",
    error: "تعذرت معاينة المسار أو قراءته.",
    close: "إغلاق",
    result: "نتيجة القراءة",
  },
  tr: {
    title: "Salt okunur erişim",
    subtitle: "Yalnızca seçilen yol incelenir; tarama, yazma veya komut çalıştırma yapılmaz.",
    path: "Seçilen yol",
    mode: "Okuma türü",
    metadata: "Temel bilgi",
    text: "Dosya metni",
    preview: "Önizlemeyi göster",
    previewReady: "Önizleme hazır. Tam olarak bu öğeyi okumak için aşağıdaki düğmeyi seçin.",
    canonical: "Kesin yol",
    size: "Boyut",
    sensitive: "Hassas yol",
    sensitiveWarning: "Hassas içerik yeni onay ister ve modele otomatik gönderilmez.",
    sensitiveDialog: "Bu hassas bir yoldur. Yalnızca önizlemesi gösterilen bu öğe okunsun mu?",
    confirmRead: "Bu okumanın yalnızca önizlemesi gösterilen yol için olduğunu anlıyorum.",
    read: "Bu öğeyi oku",
    reading: "Okunuyor…",
    contentTemporary: "Sonuç geçicidir; memory veya Vault'a kaydedilmez.",
    modelSeparate: "Modelle paylaşım ayrı onay ister ve burada etkin değildir.",
    error: "Yol önizlemesi veya okuması tamamlanamadı.",
    close: "Kapat",
    result: "Okuma sonucu",
  },
};

export function ReadOnlyExecutorPanel({ language, onClose }: { language: AppLanguage; onClose: () => void }) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [path, setPath] = useState("");
  const [mode, setMode] = useState<"read_metadata" | "read_text">("read_metadata");
  const [preview, setPreview] = useState<ReadOnlyPreview | null>(null);
  const [result, setResult] = useState<ReadOnlyExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isReading, setIsReading] = useState(false);

  const resetForNewRequest = () => {
    setPreview(null);
    setResult(null);
    setError(null);
    setConfirmed(false);
  };

  const previewPath = async () => {
    if (!path.trim() || isPreviewing) return;
    setIsPreviewing(true);
    try {
      setPreview(await previewReadOnlyPath({ selected_scope: path, requested_path: path, mode }));
      setResult(null);
      setError(null);
      setConfirmed(false);
    } catch {
      setPreview(null);
      setError(t.error);
    } finally {
      setIsPreviewing(false);
    }
  };

  const submitPreview = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // Enter is used only to create the preview. It never reads content.
    if (!preview) void previewPath();
  };

  const readPath = async () => {
    if (!preview || !confirmed || isReading) return;

    const sensitiveConfirmed = !preview.requires_sensitive_confirmation || window.confirm(t.sensitiveDialog);
    if (!sensitiveConfirmed) return;

    setIsReading(true);
    try {
      setResult(await executeReadOnlyPath({
        selected_scope: path,
        requested_path: path,
        mode,
        confirmed: true,
        sensitive_confirmed: sensitiveConfirmed,
      }));
      setError(null);
    } catch {
      setError(t.error);
    } finally {
      setIsReading(false);
    }
  };

  return <div className="readonly-layer" dir={direction}>
    <button className="readonly-backdrop" onClick={onClose} type="button" aria-label={t.close} />
    <aside className="readonly-panel" aria-busy={isPreviewing || isReading}>
      <header>
        <div>
          <p className="eyebrow"><FileText size={16} />{t.title}</p>
          <h3>{t.title}</h3>
        </div>
        <button className="icon-button" onClick={onClose} type="button" aria-label={t.close}><X size={20} /></button>
      </header>
      <div className="readonly-content">
        <p className="readonly-muted">{t.subtitle}</p>
        <form onSubmit={submitPreview}>
          <label>
            <span>{t.path}</span>
            <input
              dir="ltr"
              value={path}
              onChange={(event) => { setPath(event.target.value); resetForNewRequest(); }}
              placeholder="/home/user/selected-file.txt"
            />
          </label>
          <label>
            <span>{t.mode}</span>
            <select value={mode} onChange={(event) => { setMode(event.target.value as "read_metadata" | "read_text"); resetForNewRequest(); }}>
              <option value="read_metadata">{t.metadata}</option>
              <option value="read_text">{t.text}</option>
            </select>
          </label>
          {!preview && <button className="button primary readonly-preview-button" disabled={!path.trim() || isPreviewing} type="submit">
            <Eye size={16} />{t.preview}
          </button>}
        </form>

        {preview && <section className="readonly-result">
          <p><strong>{t.canonical}:</strong> <bdi dir="ltr">{preview.canonical_path}</bdi></p>
          <p><strong>{t.size}:</strong> <bdi dir="ltr">{preview.size_bytes}</bdi> {language === "fa" ? "بایت" : language === "ar" ? "بايت" : language === "tr" ? "bayt" : "bytes"}</p>
          {preview.sensitive && <p className="readonly-warning"><AlertTriangle size={16} />{t.sensitive}: {t.sensitiveWarning}</p>}
          <p className="readonly-muted">{t.previewReady}</p>
          <label className="readonly-confirm">
            <input checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} type="checkbox" />
            <span>{t.confirmRead}</span>
          </label>
          <button className="button primary" disabled={!confirmed || isReading} onClick={() => void readPath()} type="button">
            <LockKeyhole size={16} />{isReading ? t.reading : t.read}
          </button>
        </section>}

        {result && <section className="readonly-result">
          <h4>{t.result}</h4>
          <pre dir="ltr">{JSON.stringify(result.metadata, null, 2)}</pre>
          {result.content !== undefined && <>
            <pre dir="auto">{result.content}</pre>
            <p className="readonly-muted">{t.contentTemporary}</p>
            <p className="readonly-muted">{t.modelSeparate}</p>
          </>}
        </section>}
        {error && <p className="readonly-error">{error}</p>}
      </div>
      <footer><button className="button" onClick={onClose} type="button">{t.close}</button></footer>
    </aside>
  </div>;
}
