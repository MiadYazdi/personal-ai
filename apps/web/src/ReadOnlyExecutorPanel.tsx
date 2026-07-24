import { useState, type FormEvent } from "react";
import { AlertTriangle, Eye, FileText, LockKeyhole, Share2, Square, X } from "lucide-react";

import {
  cancelModelShare,
  selectFromSystem,
  executeReadOnlyPath,
  previewModelShare,
  previewReadOnlyPath,
  streamModelShare,
  type ModelSharePlan,
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
  prepareShare: string;
  sharePlan: string;
  shareConfirm: string;
  shareRun: string;
  shareRunning: string;
  shareCancel: string;
  shareProgress: string;
  shareChunks: string;
  shareLargeWarning: string;
  shareError: string;
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
    prepareShare: "آماده‌سازی اشتراک با مدل محلی",
    sharePlan: "طرح اشتراک با مدل محلی",
    shareConfirm: "می‌دانم فقط همین طرح ثابت با مدل محلی پردازش می‌شود.",
    shareRun: "شروع پردازش محلی",
    shareRunning: "پردازش محلی در حال انجام است…",
    shareCancel: "لغو پردازش",
    shareProgress: "پیشرفت",
    shareChunks: "بخش",
    shareLargeWarning: "این متن بزرگ است و پردازش کامل آن ممکن است زمان زیادی بگیرد.",
    shareError: "طرح یا پردازش اشتراک با مدل انجام نشد.",
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
    prepareShare: "Prepare local model share",
    sharePlan: "Local model-share plan",
    shareConfirm: "I understand that only this fixed plan will be processed by the local model.",
    shareRun: "Start local processing",
    shareRunning: "Local processing is running…",
    shareCancel: "Cancel processing",
    shareProgress: "Progress",
    shareChunks: "chunks",
    shareLargeWarning: "This text is large; complete processing may take a long time.",
    shareError: "The model-share plan or processing could not be completed.",
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
    prepareShare: "إعداد مشاركة النموذج المحلي",
    sharePlan: "خطة مشاركة النموذج المحلي",
    shareConfirm: "أفهم أن هذه الخطة الثابتة فقط ستُعالج بواسطة النموذج المحلي.",
    shareRun: "بدء المعالجة المحلية",
    shareRunning: "المعالجة المحلية جارية…",
    shareCancel: "إلغاء المعالجة",
    shareProgress: "التقدم",
    shareChunks: "أجزاء",
    shareLargeWarning: "هذا النص كبير وقد تستغرق معالجته الكاملة وقتاً طويلاً.",
    shareError: "تعذر إكمال خطة أو معالجة مشاركة النموذج.",
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
    prepareShare: "Yerel model paylaşımını hazırla",
    sharePlan: "Yerel model paylaşım planı",
    shareConfirm: "Yalnızca bu sabit planın yerel model tarafından işleneceğini anlıyorum.",
    shareRun: "Yerel işlemeyi başlat",
    shareRunning: "Yerel işleme sürüyor…",
    shareCancel: "İşlemeyi iptal et",
    shareProgress: "İlerleme",
    shareChunks: "parça",
    shareLargeWarning: "Bu metin büyük; tam işleme uzun sürebilir.",
    shareError: "Model paylaşım planı veya işlemesi tamamlanamadı.",
  },
};

export function ReadOnlyExecutorPanel({ language, thinkingMode, onClose }: { language: AppLanguage; thinkingMode: "quick" | "deep"; onClose: () => void }) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const pickerLabels = {
    fa: { file: "انتخاب فایل از سیستم", folder: "انتخاب پوشه از سیستم", error: "انتخاب مسیر از سیستم انجام نشد." },
    en: { file: "Choose file from system", folder: "Choose folder from system", error: "System path selection failed." },
    ar: { file: "اختيار ملف من النظام", folder: "اختيار مجلد من النظام", error: "تعذر اختيار المسار من النظام." },
    tr: { file: "Sistemden dosya seç", folder: "Sistemden klasör seç", error: "Sistem yolu seçilemedi." },
  }[language];
  const [path, setPath] = useState("");
  const [mode, setMode] = useState<"read_metadata" | "read_text">("read_metadata");
  const [preview, setPreview] = useState<ReadOnlyPreview | null>(null);
  const [result, setResult] = useState<ReadOnlyExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const [picking, setPicking] = useState(false);
  const [sharePlan, setSharePlan] = useState<ModelSharePlan | null>(null);
  const [shareConfirmed, setShareConfirmed] = useState(false);
  const [shareRunning, setShareRunning] = useState(false);
  const [shareProgress, setShareProgress] = useState<{ completed: number; total: number; phase: string } | null>(null);
  const [shareError, setShareError] = useState<string | null>(null);
  const [shareController, setShareController] = useState<AbortController | null>(null);

  const resetForNewRequest = () => {
    setPreview(null);
    setResult(null);
    setError(null);
    setConfirmed(false);
    setSharePlan(null);
    setShareConfirmed(false);
    setShareProgress(null);
    setShareError(null);
  };

  const chooseFromSystem = async (mode: "open_file" | "select_directory") => {
    if (picking) return;
    setPicking(true);
    try {
      const selected = await selectFromSystem(
        mode,
        mode === "open_file" ? pickerLabels.file : pickerLabels.folder,
      );
      if (!selected.cancelled && selected.path) {
        setPath(selected.path);
        resetForNewRequest();
      }
    } catch {
      setError(pickerLabels.error);
    } finally {
      setPicking(false);
    }
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

  const prepareShare = async () => {
    if (!result?.content || !preview || shareRunning) return;
    try {
      setSharePlan(await previewModelShare({ selected_scope: path, requested_path: path, content: result.content }));
      setShareConfirmed(false);
      setShareError(null);
    } catch { setSharePlan(null); setShareError(t.shareError); }
  };

  const runShare = async () => {
    if (!result?.content || !preview || !sharePlan || !shareConfirmed || shareRunning) return;
    if (sharePlan.requires_sensitive_confirmation && !window.confirm(t.sensitiveDialog)) return;
    const controller = new AbortController();
    setShareController(controller);
    setShareRunning(true);
    setShareError(null);
    let finalContent = "";
    window.dispatchEvent(new CustomEvent("personal-ai:model-share", { detail: { type: "start", share: { canonical_path: sharePlan.canonical_path, content: result.content, size_bytes: sharePlan.source_bytes, sha256: sharePlan.content_sha256, sensitive: sharePlan.sensitive, chunk_count: sharePlan.chunk_count } } }));
    try {
      await streamModelShare({ selected_scope: path, requested_path: path, content: result.content, plan_id: sharePlan.plan_id, operation_id: sharePlan.operation_id, confirmed: true, sensitive_confirmed: sharePlan.requires_sensitive_confirmation, mode: thinkingMode }, (event) => {
        if (event.type === "progress" && event.total) setShareProgress({ completed: event.completed ?? 0, total: event.total, phase: event.phase ?? "chunks" });
        if (event.type === "delta" && event.content) finalContent += event.content;
        if (event.type === "error") setShareError(event.message || t.shareError);
        if (event.type === "cancelled") setShareError(event.message || t.shareError);
      }, controller.signal);
      if (finalContent.trim()) window.dispatchEvent(new CustomEvent("personal-ai:model-share", { detail: { type: "complete", content: finalContent } }));
    } catch (caught) {
      if (!(caught instanceof DOMException && caught.name === "AbortError")) setShareError(t.shareError);
    } finally { setShareController(null); setShareRunning(false); }
  };

  const cancelShare = () => {
    if (!sharePlan) return;
    shareController?.abort();
    void cancelModelShare(sharePlan.operation_id);
    window.dispatchEvent(new CustomEvent("personal-ai:model-share", { detail: { type: "cancelled" } }));
    setShareRunning(false);
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
            <div className="readonly-picker-actions">
              <button className="button" disabled={picking} onClick={() => void chooseFromSystem("open_file")} type="button">
                {pickerLabels.file}
              </button>
              <button className="button" disabled={picking} onClick={() => void chooseFromSystem("select_directory")} type="button">
                {pickerLabels.folder}
              </button>
            </div>
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
            {!sharePlan && <button className="button" disabled={shareRunning} onClick={() => void prepareShare()} type="button"><Share2 size={16} />{t.prepareShare}</button>}
            {sharePlan && <section className="readonly-share-plan">
              <strong>{t.sharePlan}</strong>
              <p><bdi dir="ltr">{sharePlan.canonical_path}</bdi></p>
              <p>{t.size}: <bdi dir="ltr">{sharePlan.source_bytes}</bdi> {language === "fa" ? "بایت" : language === "ar" ? "بايت" : language === "tr" ? "bayt" : "bytes"}</p>
              <p>{t.shareChunks}: <bdi dir="ltr">{sharePlan.chunk_count}</bdi></p>
              {sharePlan.large_share_warning && <p className="readonly-warning"><AlertTriangle size={16} />{t.shareLargeWarning}</p>}
              <label className="readonly-confirm"><input checked={shareConfirmed} disabled={shareRunning} onChange={(event) => setShareConfirmed(event.target.checked)} type="checkbox" /><span>{t.shareConfirm}</span></label>
              {shareProgress && <p className="readonly-muted">{t.shareProgress}: <bdi dir="ltr">{shareProgress.completed}/{shareProgress.total}</bdi></p>}
              {shareRunning ? <button className="button" onClick={cancelShare} type="button"><Square size={16} />{t.shareCancel}</button> : <button className="button primary" disabled={!shareConfirmed} onClick={() => void runShare()} type="button"><Share2 size={16} />{t.shareRun}</button>}
            </section>}
            {shareError && <p className="readonly-error">{shareError}</p>}
          </>}
        </section>}
        {error && <p className="readonly-error">{error}</p>}
      </div>
      <footer><button className="button" onClick={onClose} type="button">{t.close}</button></footer>
    </aside>
  </div>;
}
