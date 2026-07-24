import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Eye,
  Globe2,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";

import {
  fetchOnlineControlStatus,
  previewControlledEvolution,
  previewOnlineEgress,
  type ControlledEvolutionPreviewResponse,
  type OnlineControlStatus,
  type OnlineEgressPreviewResponse,
} from "./api";
import type { AppLanguage } from "./types";

type Copy = {
  title: string;
  subtitle: string;
  offline: string;
  provider: string;
  model: string;
  action: string;
  categories: string;
  bytes: string;
  summary: string;
  previewEgress: string;
  noNetwork: string;
  evolution: string;
  proposal: string;
  diff: string;
  validation: string;
  previewEvolution: string;
  destination: string;
  digest: string;
  policy: string;
  vault: string;
  error: string;
  close: string;
};

const copy: Record<AppLanguage, Copy> = {
  fa: {
    title: "اتصال آنلاین و ارتقای کنترل‌شده",
    subtitle: "فقط پیش‌نمایش محلی؛ اینترنت و تغییر خودکار کد خاموش هستند.",
    offline: "اتصال آنلاین پیش‌فرض خاموش است",
    provider: "شناسهٔ سرویس",
    model: "شناسهٔ مدل",
    action: "نوع درخواست",
    categories: "دسته‌های دادهٔ اعلام‌شده",
    bytes: "حجم تقریبی خروجی",
    summary: "خلاصهٔ دادهٔ خروجی",
    previewEgress: "پیش‌نمایش خروج داده",
    noNetwork: "هیچ اتصال شبکه‌ای در این مرحله برقرار نمی‌شود.",
    evolution: "پیشنهاد ارتقای کد",
    proposal: "خلاصهٔ پیشنهاد",
    diff: "diff پیشنهادی",
    validation: "برنامهٔ اعتبارسنجی؛ هر مورد یک خط",
    previewEvolution: "پیش‌نمایش پیشنهاد",
    destination: "مقصد",
    digest: "هش",
    policy: "سیاست مجوز",
    vault: "برای اقدام واقعی در آینده، باز کردن Vault و تأیید تازه لازم است.",
    error: "پیش‌نمایش انجام نشد.",
    close: "بستن",
  },
  en: {
    title: "Online connection and controlled evolution",
    subtitle: "Local preview only; network and automatic code changes are off.",
    offline: "Online connection is off by default",
    provider: "Provider identifier",
    model: "Model identifier",
    action: "Request action",
    categories: "Declared data categories",
    bytes: "Estimated outbound bytes",
    summary: "Outbound data summary",
    previewEgress: "Preview data egress",
    noNetwork: "No network connection is made at this stage.",
    evolution: "Code-evolution proposal",
    proposal: "Proposal summary",
    diff: "Proposed diff",
    validation: "Validation plan; one item per line",
    previewEvolution: "Preview proposal",
    destination: "Destination",
    digest: "Digest",
    policy: "Permission policy",
    vault: "A future real action requires Vault Unlock and fresh confirmation.",
    error: "The preview could not be completed.",
    close: "Close",
  },
  ar: {
    title: "الاتصال عبر الإنترنت والتطوير المنضبط",
    subtitle: "معاينة محلية فقط؛ الشبكة وتغيير الكود التلقائي متوقفان.",
    offline: "الاتصال عبر الإنترنت متوقف افتراضياً",
    provider: "معرّف الخدمة",
    model: "معرّف النموذج",
    action: "نوع الطلب",
    categories: "فئات البيانات المعلنة",
    bytes: "حجم الخروج التقريبي",
    summary: "ملخص البيانات الخارجة",
    previewEgress: "معاينة خروج البيانات",
    noNetwork: "لن يتم إجراء اتصال شبكة في هذه المرحلة.",
    evolution: "اقتراح تطوير الكود",
    proposal: "ملخص الاقتراح",
    diff: "diff المقترح",
    validation: "خطة التحقق؛ عنصر واحد في كل سطر",
    previewEvolution: "معاينة الاقتراح",
    destination: "الوجهة",
    digest: "البصمة",
    policy: "سياسة الإذن",
    vault: "يتطلب الإجراء الفعلي مستقبلاً فتح Vault وتأكيداً جديداً.",
    error: "تعذرت المعاينة.",
    close: "إغلاق",
  },
  tr: {
    title: "Çevrimiçi bağlantı ve denetimli geliştirme",
    subtitle: "Yalnızca yerel önizleme; ağ ve otomatik kod değişikliği kapalıdır.",
    offline: "Çevrimiçi bağlantı varsayılan olarak kapalı",
    provider: "Hizmet tanımlayıcısı",
    model: "Model tanımlayıcısı",
    action: "İstek türü",
    categories: "Beyan edilen veri kategorileri",
    bytes: "Tahmini dışarı giden bayt",
    summary: "Dışarı giden veri özeti",
    previewEgress: "Veri çıkışını önizle",
    noNetwork: "Bu aşamada ağ bağlantısı kurulmaz.",
    evolution: "Kod geliştirme önerisi",
    proposal: "Öneri özeti",
    diff: "Önerilen diff",
    validation: "Doğrulama planı; satır başına bir öğe",
    previewEvolution: "Öneriyi önizle",
    destination: "Hedef",
    digest: "Özet",
    policy: "İzin politikası",
    vault: "Gelecekte gerçek işlem için Vault Unlock ve yeni onay gerekir.",
    error: "Önizleme tamamlanamadı.",
    close: "Kapat",
  },
};

export function OnlineControlPanel({
  language,
  onClose,
}: {
  language: AppLanguage;
  onClose: () => void;
}) {
  const t = copy[language];
  const direction = language === "fa" || language === "ar" ? "rtl" : "ltr";
  const [status, setStatus] = useState<OnlineControlStatus | null>(null);
  const [providerId, setProviderId] = useState("future-provider");
  const [modelId, setModelId] = useState("future-model");
  const [action, setAction] = useState<
    "online_chat" | "web_search" | "model_update" | "source_update"
  >("online_chat");
  const [categories, setCategories] = useState("synthetic_text");
  const [estimatedBytes, setEstimatedBytes] = useState("128");
  const [outboundSummary, setOutboundSummary] = useState(
    "Synthetic online preview only; no content leaves this device.",
  );
  const [egress, setEgress] = useState<OnlineEgressPreviewResponse | null>(null);
  const [proposalSummary, setProposalSummary] = useState(
    "Synthetic code-quality proposal only.",
  );
  const [proposedDiff, setProposedDiff] = useState(
    "diff --git a/src/example.py b/src/example.py\n--- a/src/example.py\n+++ b/src/example.py\n@@ -1 +1 @@\n-old\n+new\n",
  );
  const [validationPlan, setValidationPlan] = useState(
    "Run synthetic tests\nReview diff",
  );
  const [evolution, setEvolution] =
    useState<ControlledEvolutionPreviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchOnlineControlStatus()
      .then(setStatus)
      .catch(() => setError(t.error));
  }, [t.error]);

  const previewEgress = async () => {
    try {
      setEgress(
        await previewOnlineEgress({
          provider_id: providerId.trim(),
          model_id: modelId.trim(),
          action,
          outbound_summary: outboundSummary.trim(),
          data_categories: categories
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          estimated_bytes: Number(estimatedBytes),
        }),
      );
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
    }
  };

  const previewEvolution = async () => {
    try {
      setEvolution(
        await previewControlledEvolution({
          repository_scope: "/home/miad004/Desktop/Products all/personal_ai",
          proposal_summary: proposalSummary.trim(),
          proposed_diff: proposedDiff,
          validation_plan: validationPlan
            .split("\n")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      );
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t.error);
    }
  };

  return (
    <div className="agent-layer" dir={direction}>
      <button className="agent-backdrop" onClick={onClose} type="button" />
      <aside className="agent-panel online-control-panel">
        <header>
          <div>
            <p className="eyebrow">
              <Globe2 size={16} />
              {t.offline}
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
                <span>{status?.controlled_evolution ?? "proposal_only"}</span>
              </div>
            </div>
          </section>

          <section className="agent-section">
            <label><span>{t.provider}</span><input dir="ltr" value={providerId} onChange={(event) => setProviderId(event.target.value)} /></label>
            <label><span>{t.model}</span><input dir="ltr" value={modelId} onChange={(event) => setModelId(event.target.value)} /></label>
            <label><span>{t.action}</span><select dir="ltr" value={action} onChange={(event) => setAction(event.target.value as typeof action)}><option value="online_chat">online_chat</option><option value="web_search">web_search</option><option value="model_update">model_update</option><option value="source_update">source_update</option></select></label>
            <label><span>{t.categories}</span><input dir="ltr" value={categories} onChange={(event) => setCategories(event.target.value)} /></label>
            <label><span>{t.bytes}</span><input dir="ltr" min="0" type="number" value={estimatedBytes} onChange={(event) => setEstimatedBytes(event.target.value)} /></label>
            <label><span>{t.summary}</span><textarea dir={direction} value={outboundSummary} onChange={(event) => setOutboundSummary(event.target.value)} /></label>
            <button className="button primary" onClick={() => void previewEgress()} type="button"><Eye size={16} />{t.previewEgress}</button>
          </section>

          {egress && <section className="agent-section agent-preview-result online-summary">
            <p><strong>{t.destination}:</strong> <bdi dir="ltr">{egress.egress.destination}</bdi></p>
            <p><strong>{t.action}:</strong> <bdi dir="ltr">{egress.egress.action}</bdi></p>
            <p><strong>{t.categories}:</strong> <bdi dir="ltr">{egress.egress.data_categories.join(", ") || "none"}</bdi></p>
            <p><strong>{t.bytes}:</strong> <bdi dir="ltr">{egress.egress.estimated_bytes}</bdi></p>
            <p><strong>{t.digest}:</strong> <bdi dir="ltr">{egress.egress.request_sha256}</bdi></p>
            <p className="agent-warning"><AlertTriangle size={16} />{t.noNetwork}</p>
            <p className="agent-warning"><AlertTriangle size={16} />{t.vault}</p>
          </section>}

          <details className="online-evolution-details">
            <summary><Sparkles size={16} />{t.evolution}</summary>
            <div className="online-evolution-content">
              <label><span>{t.proposal}</span><input dir={direction} value={proposalSummary} onChange={(event) => setProposalSummary(event.target.value)} /></label>
              <label><span>{t.diff}</span><textarea className="online-diff-input" dir="ltr" value={proposedDiff} onChange={(event) => setProposedDiff(event.target.value)} /></label>
              <label><span>{t.validation}</span><textarea dir={direction} value={validationPlan} onChange={(event) => setValidationPlan(event.target.value)} /></label>
              <button className="button primary" onClick={() => void previewEvolution()} type="button"><Eye size={16} />{t.previewEvolution}</button>
            </div>
          </details>

          {evolution && <section className="agent-section agent-preview-result online-summary">
            <p><strong>{t.digest}:</strong> <bdi dir="ltr">{evolution.evolution.proposal_sha256}</bdi></p>
            <p><strong>{t.diff}:</strong> <bdi dir="ltr">{evolution.evolution.diff_sha256}</bdi></p>
            <p><strong>{t.bytes}:</strong> <bdi dir="ltr">{evolution.evolution.diff_bytes}</bdi></p>
            <p><strong>{t.validation}:</strong> {evolution.evolution.validation_plan.join(" · ")}</p>
            <details><summary>{t.diff}</summary><pre className="online-touched-files" dir="ltr">{evolution.evolution.touched_files.join("\n")}</pre></details>
            <p className="agent-warning"><AlertTriangle size={16} />{t.vault}</p>
          </section>}

          {error && <p className="agent-error"><bdi dir="ltr">{error}</bdi></p>}
        </div>

        <footer><button className="button" onClick={onClose} type="button">{t.close}</button></footer>
      </aside>
    </div>
  );
}
