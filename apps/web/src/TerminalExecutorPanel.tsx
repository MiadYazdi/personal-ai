import { useState } from "react";
import {
  AlertTriangle,
  Eye,
  FolderOpen,
  ShieldCheck,
  TerminalSquare,
  X,
} from "lucide-react";

import {
  previewTerminalExecution,
  selectFromSystem,
  type TerminalExecutionPreviewResponse,
} from "./api";
import type { AppLanguage } from "./types";

type Copy = {
  title: string;
  subtitle: string;
  args: string;
  argsHint: string;
  cwd: string;
  chooseFolder: string;
  effect: string;
  timeout: string;
  seconds: string;
  preview: string;
  previewHint: string;
  executable: string;
  resolvedArgs: string;
  requestHash: string;
  outputLimit: string;
  vault: string;
  allowed: string;
  pickerError: string;
  previewError: string;
  invalid: string;
  close: string;
};

const copy: Record<AppLanguage, Copy> = {
  fa: {
    title: "فرمان ساخت‌یافته",
    subtitle: "فقط پیش‌نمایش محلی؛ تا تأیید جداگانه هیچ فرمانی اجرا نمی‌شود.",
    args: "آرگومان‌های دقیق فرمان",
    argsHint: "هر آرگومان را در یک خط بنویسید. پوسته، sudo، env، pkexec و عملگرهای پوسته پذیرفته نمی‌شوند.",
    cwd: "پوشهٔ کاری",
    chooseFolder: "انتخاب پوشه از سیستم",
    effect: "اثر مورد انتظار",
    timeout: "مهلت اجرا",
    seconds: "ثانیه",
    preview: "پیش‌نمایش فرمان",
    previewHint: "این مرحله فقط مسیر اجرایی، پوشهٔ کاری، هش درخواست و سیاست مجوز را بررسی می‌کند.",
    executable: "مسیر اجرایی حل‌شده",
    resolvedArgs: "آرگومان‌های حل‌شده",
    requestHash: "هش درخواست",
    outputLimit: "حد نمایش خروجی",
    vault: "برای اجرای بعدی، باز کردن Vault و تأیید یک‌باره لازم است.",
    allowed: "تصمیم‌های مجاز",
    pickerError: "انتخاب پوشه از سیستم انجام نشد.",
    previewError: "پیش‌نمایش فرمان انجام نشد.",
    invalid: "آرگومان‌ها، پوشهٔ کاری، اثر مورد انتظار و مهلت معتبر لازم است.",
    close: "بستن",
  },
  en: {
    title: "Structured terminal",
    subtitle: "Local preview only; no command runs until a separate confirmation.",
    args: "Exact command arguments",
    argsHint: "Enter one argument per line. Shells, sudo, env, pkexec, and shell operators are rejected.",
    cwd: "Working directory",
    chooseFolder: "Choose folder from system",
    effect: "Expected effect",
    timeout: "Timeout",
    seconds: "seconds",
    preview: "Preview command",
    previewHint: "This step checks only the executable path, working directory, request digest, and permission policy.",
    executable: "Resolved executable",
    resolvedArgs: "Resolved arguments",
    requestHash: "Request digest",
    outputLimit: "Output display limit",
    vault: "Later execution requires Vault Unlock and a fresh one-time confirmation.",
    allowed: "Allowed decisions",
    pickerError: "The system folder selection could not be completed.",
    previewError: "The command preview could not be completed.",
    invalid: "Valid arguments, working directory, expected effect, and timeout are required.",
    close: "Close",
  },
  ar: {
    title: "طرفية منظّمة",
    subtitle: "معاينة محلية فقط؛ لن يُنفّذ أي أمر قبل تأكيد منفصل.",
    args: "وسائط الأمر الدقيقة",
    argsHint: "اكتب كل وسيط في سطر مستقل. يتم رفض الصدفة وsudo وenv وpkexec وعوامل الصدفة.",
    cwd: "مجلد العمل",
    chooseFolder: "اختيار مجلد من النظام",
    effect: "الأثر المتوقع",
    timeout: "مهلة التنفيذ",
    seconds: "ثانية",
    preview: "معاينة الأمر",
    previewHint: "تتحقق هذه الخطوة فقط من المسار التنفيذي ومجلد العمل وبصمة الطلب وسياسة الإذن.",
    executable: "المسار التنفيذي المحلول",
    resolvedArgs: "الوسائط المحلولة",
    requestHash: "بصمة الطلب",
    outputLimit: "حد عرض المخرجات",
    vault: "يتطلب التنفيذ لاحقاً فتح Vault وتأكيداً جديداً لمرة واحدة.",
    allowed: "القرارات المسموح بها",
    pickerError: "تعذر اختيار المجلد من النظام.",
    previewError: "تعذرت معاينة الأمر.",
    invalid: "الوسائط ومجلد العمل والأثر المتوقع والمهلة الصحيحة مطلوبة.",
    close: "إغلاق",
  },
  tr: {
    title: "Yapılandırılmış terminal",
    subtitle: "Yalnızca yerel önizleme; ayrı onay olmadan hiçbir komut çalışmaz.",
    args: "Tam komut bağımsız değişkenleri",
    argsHint: "Her bağımsız değişkeni ayrı satıra yazın. Kabuklar, sudo, env, pkexec ve kabuk işleçleri reddedilir.",
    cwd: "Çalışma klasörü",
    chooseFolder: "Sistemden klasör seç",
    effect: "Beklenen etki",
    timeout: "Zaman aşımı",
    seconds: "saniye",
    preview: "Komutu önizle",
    previewHint: "Bu adım yalnızca yürütülebilir yolunu, çalışma klasörünü, istek özetini ve izin politikasını denetler.",
    executable: "Çözümlenen yürütülebilir",
    resolvedArgs: "Çözümlenen bağımsız değişkenler",
    requestHash: "İstek özeti",
    outputLimit: "Çıktı görüntüleme sınırı",
    vault: "Sonraki yürütme için Vault Unlock ve yeni tek seferlik onay gerekir.",
    allowed: "İzin verilen kararlar",
    pickerError: "Sistem klasörü seçilemedi.",
    previewError: "Komut önizlemesi tamamlanamadı.",
    invalid: "Geçerli bağımsız değişkenler, çalışma klasörü, beklenen etki ve zaman aşımı gerekir.",
    close: "Kapat",
  },
};

export function TerminalExecutorPanel({
  language,
  onClose,
}: {
  language: AppLanguage;
  onClose: () => void;
}) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [argvText, setArgvText] = useState("git\nstatus");
  const [cwd, setCwd] = useState("/tmp");
  const [expectedEffect, setExpectedEffect] = useState(
    language === "fa" ? "نمایش وضعیت مخزن" : "Show repository status",
  );
  const [timeout, setTimeout] = useState("30");
  const [preview, setPreview] =
    useState<TerminalExecutionPreviewResponse | null>(null);
  const [picking, setPicking] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetPreview = () => {
    setPreview(null);
    setError(null);
  };

  const chooseDirectory = async () => {
    if (picking) return;
    setPicking(true);
    try {
      const result = await selectFromSystem("select_directory", t.chooseFolder);
      if (!result.cancelled && result.path) {
        setCwd(result.path);
        resetPreview();
      }
    } catch {
      setError(t.pickerError);
    } finally {
      setPicking(false);
    }
  };

  const requestPreview = async () => {
    const argv = argvText
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);
    const timeoutSeconds = Number(timeout);

    if (
      !argv.length ||
      !cwd.trim() ||
      !expectedEffect.trim() ||
      !Number.isInteger(timeoutSeconds) ||
      timeoutSeconds < 1 ||
      timeoutSeconds > 600
    ) {
      setPreview(null);
      setError(t.invalid);
      return;
    }

    setPreviewing(true);
    try {
      setPreview(
        await previewTerminalExecution({
          argv,
          cwd: cwd.trim(),
          expected_effect: expectedEffect.trim(),
          timeout_seconds: timeoutSeconds,
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

  return (
    <div className="agent-layer" dir={direction}>
      <button className="agent-backdrop" onClick={onClose} type="button" />
      <aside className="agent-panel terminal-panel">
        <header>
          <div>
            <p className="eyebrow">
              <TerminalSquare size={16} />
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
              <span>{t.args}</span>
              <textarea
                className="terminal-argv-input"
                dir="ltr"
                onChange={(event) => {
                  setArgvText(event.target.value);
                  resetPreview();
                }}
                spellCheck={false}
                value={argvText}
              />
              <small>{t.argsHint}</small>
            </label>

            <label>
              <span>{t.cwd}</span>
              <input
                dir="ltr"
                onChange={(event) => {
                  setCwd(event.target.value);
                  resetPreview();
                }}
                value={cwd}
              />
            </label>

            <button
              className="button"
              disabled={picking}
              onClick={() => void chooseDirectory()}
              type="button"
            >
              <FolderOpen size={16} />
              {t.chooseFolder}
            </button>

            <label>
              <span>{t.effect}</span>
              <input
                dir={direction}
                onChange={(event) => {
                  setExpectedEffect(event.target.value);
                  resetPreview();
                }}
                value={expectedEffect}
              />
            </label>

            <label>
              <span>{t.timeout}</span>
              <div className="terminal-timeout-row" dir="ltr">
                <input
                  max="600"
                  min="1"
                  onChange={(event) => {
                    setTimeout(event.target.value);
                    resetPreview();
                  }}
                  type="number"
                  value={timeout}
                />
                <span>{t.seconds}</span>
              </div>
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
                <strong>{t.executable}:</strong>{" "}
                <bdi dir="ltr">{preview.terminal.executable_path}</bdi>
              </p>
              <p>
                <strong>{t.resolvedArgs}:</strong>{" "}
                <bdi dir="ltr">{preview.terminal.argv.join(" ")}</bdi>
              </p>
              <p>
                <strong>{t.cwd}:</strong>{" "}
                <bdi dir="ltr">{preview.terminal.cwd}</bdi>
              </p>
              <p>
                <strong>{t.effect}:</strong> {preview.terminal.expected_effect}
              </p>
              <p>
                <strong>{t.timeout}:</strong>{" "}
                <bdi dir="ltr">
                  {preview.terminal.timeout_seconds} {t.seconds}
                </bdi>
              </p>
              <p>
                <strong>{t.requestHash}:</strong>{" "}
                <bdi dir="ltr">{preview.terminal.request_sha256}</bdi>
              </p>
              <p>
                <strong>{t.outputLimit}:</strong>{" "}
                <bdi dir="ltr">
                  {preview.terminal.max_output_bytes} bytes
                </bdi>
              </p>
              <p>
                <strong>{t.allowed}:</strong>{" "}
                <bdi dir="ltr">
                  {preview.policy.allowed_decisions.join(", ") || "none"}
                </bdi>
              </p>
              {preview.policy.vault_required && (
                <p className="agent-warning">
                  <AlertTriangle size={16} />
                  {t.vault}
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
