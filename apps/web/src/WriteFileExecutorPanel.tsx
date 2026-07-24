import { useState } from "react";
import {
  AlertTriangle,
  Eye,
  FilePenLine,
  FolderOpen,
  Save,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  previewWriteFile,
  selectFromSystem,
  type WriteFilePreviewResponse,
} from "./api";
import type { AppLanguage } from "./types";

type Copy = {
  title: string;
  subtitle: string;
  scope: string;
  chooseFolder: string;
  target: string;
  chooseFile: string;
  content: string;
  preview: string;
  previewHint: string;
  operation: string;
  create: string;
  overwrite: string;
  canonicalPath: string;
  oldHash: string;
  newHash: string;
  oldSize: string;
  newSize: string;
  mode: string;
  diff: string;
  diffTruncated: string;
  vault: string;
  allowed: string;
  invalid: string;
  pickerError: string;
  previewError: string;
  close: string;
};

const copy: Record<AppLanguage, Copy> = {
  fa: {
    title: "نوشتن فایل",
    subtitle: "فقط پیش‌نمایش محلی؛ تا تأیید جداگانه هیچ فایل نوشته نمی‌شود.",
    scope: "دامنهٔ مجاز نوشتن",
    chooseFolder: "انتخاب پوشه از سیستم",
    target: "مسیر یا نام فایل مقصد",
    chooseFile: "انتخاب نام فایل از سیستم",
    content: "محتوای جدید UTF-8",
    preview: "پیش‌نمایش تغییر",
    previewHint: "پیش‌نمایش فقط مسیر کانونی، هش‌ها، حالت ایجاد یا بازنویسی و diff را بررسی می‌کند.",
    operation: "نوع عملیات",
    create: "ایجاد فایل",
    overwrite: "بازنویسی فایل",
    canonicalPath: "مسیر کانونی",
    oldHash: "هش پیشین",
    newHash: "هش جدید",
    oldSize: "اندازهٔ پیشین",
    newSize: "اندازهٔ جدید",
    mode: "مجوز فایل پس از نوشتن",
    diff: "تفاوت محتوا",
    diffTruncated: "diff به حد نمایش رسیده و کوتاه شده است.",
    vault: "برای نوشتن واقعی، باز کردن Vault و تأیید تازهٔ یک‌باره لازم است.",
    allowed: "تصمیم‌های مجاز",
    invalid: "دامنه، مسیر فایل و محتوای UTF-8 لازم است.",
    pickerError: "انتخاب مسیر از سیستم انجام نشد.",
    previewError: "پیش‌نمایش تغییر فایل انجام نشد.",
    close: "بستن",
  },
  en: {
    title: "Write file",
    subtitle: "Local preview only; no file is written until a separate confirmation.",
    scope: "Approved write scope",
    chooseFolder: "Choose folder from system",
    target: "Target file path or name",
    chooseFile: "Choose file name from system",
    content: "New UTF-8 content",
    preview: "Preview change",
    previewHint: "Preview checks only canonical path, hashes, create/overwrite mode, and diff.",
    operation: "Operation",
    create: "Create file",
    overwrite: "Overwrite file",
    canonicalPath: "Canonical path",
    oldHash: "Old hash",
    newHash: "New hash",
    oldSize: "Old size",
    newSize: "New size",
    mode: "Resulting file mode",
    diff: "Content diff",
    diffTruncated: "The diff reached its display limit and was shortened.",
    vault: "A real write requires Vault Unlock and a fresh one-time confirmation.",
    allowed: "Allowed decisions",
    invalid: "A scope, file path, and UTF-8 content are required.",
    pickerError: "The system path selection could not be completed.",
    previewError: "The file-change preview could not be completed.",
    close: "Close",
  },
  ar: {
    title: "كتابة ملف",
    subtitle: "معاينة محلية فقط؛ لن يُكتب أي ملف قبل تأكيد منفصل.",
    scope: "نطاق الكتابة المسموح",
    chooseFolder: "اختيار مجلد من النظام",
    target: "مسار أو اسم الملف الهدف",
    chooseFile: "اختيار اسم الملف من النظام",
    content: "محتوى UTF-8 الجديد",
    preview: "معاينة التغيير",
    previewHint: "تتحقق المعاينة فقط من المسار القانوني والبصمات ونوع الإنشاء أو الاستبدال والفرق.",
    operation: "نوع العملية",
    create: "إنشاء ملف",
    overwrite: "استبدال ملف",
    canonicalPath: "المسار القانوني",
    oldHash: "البصمة السابقة",
    newHash: "البصمة الجديدة",
    oldSize: "الحجم السابق",
    newSize: "الحجم الجديد",
    mode: "وضع الملف الناتج",
    diff: "فرق المحتوى",
    diffTruncated: "بلغ الفرق حد العرض وتم اختصاره.",
    vault: "تتطلب الكتابة الفعلية فتح Vault وتأكيداً جديداً لمرة واحدة.",
    allowed: "القرارات المسموح بها",
    invalid: "النطاق ومسار الملف ومحتوى UTF-8 مطلوبة.",
    pickerError: "تعذر اختيار المسار من النظام.",
    previewError: "تعذرت معاينة تغيير الملف.",
    close: "إغلاق",
  },
  tr: {
    title: "Dosya yaz",
    subtitle: "Yalnızca yerel önizleme; ayrı onay olmadan hiçbir dosya yazılmaz.",
    scope: "Onaylı yazma kapsamı",
    chooseFolder: "Sistemden klasör seç",
    target: "Hedef dosya yolu veya adı",
    chooseFile: "Sistemden dosya adı seç",
    content: "Yeni UTF-8 içerik",
    preview: "Değişikliği önizle",
    previewHint: "Önizleme yalnızca kanonik yolu, özetleri, oluşturma/değiştirme türünü ve farkı denetler.",
    operation: "İşlem",
    create: "Dosya oluştur",
    overwrite: "Dosyayı değiştir",
    canonicalPath: "Kanonik yol",
    oldHash: "Eski özet",
    newHash: "Yeni özet",
    oldSize: "Eski boyut",
    newSize: "Yeni boyut",
    mode: "Sonuç dosya modu",
    diff: "İçerik farkı",
    diffTruncated: "Fark görüntüleme sınırına ulaştı ve kısaltıldı.",
    vault: "Gerçek yazma için Vault Unlock ve yeni tek seferlik onay gerekir.",
    allowed: "İzin verilen kararlar",
    invalid: "Kapsam, dosya yolu ve UTF-8 içerik gerekir.",
    pickerError: "Sistem yolu seçilemedi.",
    previewError: "Dosya değişikliği önizlemesi tamamlanamadı.",
    close: "Kapat",
  },
};

export function WriteFileExecutorPanel({
  language,
  onClose,
}: {
  language: AppLanguage;
  onClose: () => void;
}) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [scope, setScope] = useState("");
  const [target, setTarget] = useState("");
  const [content, setContent] = useState("");
  const [preview, setPreview] = useState<WriteFilePreviewResponse | null>(null);
  const [picking, setPicking] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetPreview = () => {
    setPreview(null);
    setError(null);
  };

  const choosePath = async (mode: "select_directory" | "save_file") => {
    if (picking) return;
    setPicking(true);
    try {
      const selected = await selectFromSystem(
        mode,
        mode === "select_directory" ? t.chooseFolder : t.chooseFile,
      );
      if (!selected.cancelled && selected.path) {
        if (mode === "select_directory") setScope(selected.path);
        else setTarget(selected.path);
        resetPreview();
      }
    } catch {
      setError(t.pickerError);
    } finally {
      setPicking(false);
    }
  };

  const requestPreview = async () => {
    if (!scope.trim() || !target.trim()) {
      setPreview(null);
      setError(t.invalid);
      return;
    }

    setPreviewing(true);
    try {
      setPreview(
        await previewWriteFile({
          selected_scope: scope.trim(),
          requested_path: target.trim(),
          content,
        }),
      );
      setError(null);
    } catch {
      setPreview(null);
      setError(t.previewError);
    } finally {
      setPreviewing(false);
    }
  };

  const operationLabel = preview?.write.operation === "overwrite"
    ? t.overwrite
    : t.create;

  return (
    <div className="agent-layer" dir={direction}>
      <button className="agent-backdrop" onClick={onClose} type="button" />
      <aside className="agent-panel write-file-panel">
        <header>
          <div>
            <p className="eyebrow">
              <FilePenLine size={16} />
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
                <span>{t.previewHint}</span>
              </div>
            </div>
          </section>

          <section className="agent-section">
            <label>
              <span>{t.scope}</span>
              <input
                dir="ltr"
                onChange={(event) => {
                  setScope(event.target.value);
                  resetPreview();
                }}
                value={scope}
              />
            </label>

            <button
              className="button"
              disabled={picking}
              onClick={() => void choosePath("select_directory")}
              type="button"
            >
              <FolderOpen size={16} />
              {t.chooseFolder}
            </button>

            <label>
              <span>{t.target}</span>
              <input
                dir="ltr"
                onChange={(event) => {
                  setTarget(event.target.value);
                  resetPreview();
                }}
                value={target}
              />
            </label>

            <button
              className="button"
              disabled={picking}
              onClick={() => void choosePath("save_file")}
              type="button"
            >
              <Save size={16} />
              {t.chooseFile}
            </button>

            <label>
              <span>{t.content}</span>
              <textarea
                className="write-file-content-input"
                dir={direction}
                onChange={(event) => {
                  setContent(event.target.value);
                  resetPreview();
                }}
                value={content}
              />
            </label>

            <button
              className="button primary"
              disabled={previewing}
              onClick={() => void requestPreview()}
              type="button"
            >
              <Eye size={16} />
              {t.preview}
            </button>
          </section>

          {error && <p className="agent-error">{error}</p>}

          {preview && (
            <section className="agent-section agent-preview-result">
              <p>
                <strong>{t.operation}:</strong> {operationLabel}
              </p>
              <p>
                <strong>{t.canonicalPath}:</strong>{" "}
                <bdi dir="ltr">{preview.write.canonical_path}</bdi>
              </p>
              <p>
                <strong>{t.oldHash}:</strong>{" "}
                <bdi dir="ltr">{preview.write.old_sha256 ?? "—"}</bdi>
              </p>
              <p>
                <strong>{t.newHash}:</strong>{" "}
                <bdi dir="ltr">{preview.write.new_sha256}</bdi>
              </p>
              <p>
                <strong>{t.oldSize}:</strong>{" "}
                <bdi dir="ltr">{preview.write.old_size_bytes} bytes</bdi>
              </p>
              <p>
                <strong>{t.newSize}:</strong>{" "}
                <bdi dir="ltr">{preview.write.new_size_bytes} bytes</bdi>
              </p>
              <p>
                <strong>{t.mode}:</strong>{" "}
                <bdi dir="ltr">{preview.write.resulting_mode}</bdi>
              </p>
              <p>
                <strong>{t.allowed}:</strong>{" "}
                <bdi dir="ltr">
                  {preview.policy.allowed_decisions.join(", ") || "none"}
                </bdi>
              </p>
              <p className="agent-warning">
                <AlertTriangle size={16} />
                {t.vault}
              </p>
              <h4>{t.diff}</h4>
              <pre className="write-file-diff" dir="auto">
                {preview.write.diff || "—"}
              </pre>
              {preview.write.diff_truncated && (
                <p className="agent-warning">
                  <AlertTriangle size={16} />
                  {t.diffTruncated}
                </p>
              )}
            </section>
          )}
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
