import { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Cloud,
  Copy,
  Download,
  KeyRound,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";
import { createLocalVault } from "./api";
import type {
  AppLanguage,
  LocalVaultOnboardingResponse,
  OnboardingStatus,
} from "./types";

type CopyText = {
  title: string;
  subtitle: string;
  localAccount: string;
  onlineAccount: string;
  onlineLater: string;
  profileName: string;
  profilePlaceholder: string;
  addressName: string;
  addressHint: string;
  passphrase: string;
  passphraseConfirm: string;
  recoveryTitle: string;
  recoveryDescription: string;
  recoveryChoice: string;
  createPreview: string;
  emptyName: string;
  emptyPassphrase: string;
  passphraseMismatch: string;
  securityNote: string;
  confirmTitle: string;
  confirmDescription: string;
  confirmProfile: string;
  confirmAddress: string;
  confirmRecovery: string;
  acknowledge: string;
  finalCreate: string;
  cancel: string;
  creating: string;
  createError: string;
  recoveryResultTitle: string;
  phrase: string;
  code: string;
  copyPhrase: string;
  copyCode: string;
  download: string;
  copied: string;
  recoveryWarning: string;
  recoveryAcknowledgment: string;
  continue: string;
  successWithoutRecovery: string;
};

const copy: Record<AppLanguage, CopyText> = {
  fa: {
    title: "راه‌اندازی Personal AI",
    subtitle: "ابتدا Vault محلی و profile رمزگذاری‌شدهٔ خودت را آماده کن.",
    localAccount: "حساب محلی",
    onlineAccount: "حساب آنلاین",
    onlineLater: "OAuth providerها بعد از Local Vault onboarding فعال می‌شوند.",
    profileName: "نام اصلی",
    profilePlaceholder: "مثال: Mohammad Reza",
    addressName: "نامی که دستیار صدا می‌زند",
    addressHint: "اگر خالی بماند، همان نام اصلی استفاده می‌شود.",
    passphrase: "Vault Passphrase",
    passphraseConfirm: "تکرار Vault Passphrase",
    recoveryTitle: "Recovery Key اختیاری",
    recoveryDescription:
      "اگر passphrase را فراموش کنی، فقط Recovery Phrase یا Base64url Code می‌تواند Vault را باز کند.",
    recoveryChoice: "Recovery Key بساز",
    createPreview: "ساخت Vault نیازمند تأیید نهایی است",
    emptyName: "نام اصلی لازم است.",
    emptyPassphrase: "Vault Passphrase نباید خالی باشد.",
    passphraseMismatch: "دو passphrase یکسان نیستند.",
    securityNote:
      "Passphrase در مرورگر، localStorage یا log ذخیره نمی‌شود.",
    confirmTitle: "تأیید نهایی ساخت Vault",
    confirmDescription:
      "این عمل یک Vault رمزگذاری‌شده و اولین profile محلی را ایجاد می‌کند.",
    confirmProfile: "Profile Name",
    confirmAddress: "Address Name",
    confirmRecovery: "Recovery Key",
    acknowledge:
      "می‌دانم این عمل Vault محلی می‌سازد و passphrase آن قابل بازیابی نیست.",
    finalCreate: "ایجاد Vault رمزگذاری‌شده",
    cancel: "لغو",
    creating: "در حال ساخت Vault...",
    createError: "ساخت Vault انجام نشد.",
    recoveryResultTitle: "Recovery Key خود را ذخیره کن",
    phrase: "English BIP39 Recovery Phrase",
    code: "Base64url Recovery Code",
    copyPhrase: "کپی Phrase",
    copyCode: "کپی Code",
    download: "دانلود فایل Recovery",
    copied: "کپی شد",
    recoveryWarning:
      "این اطلاعات فقط یک‌بار نمایش داده می‌شوند. فایل دانلودی plaintext حساس است.",
    recoveryAcknowledgment:
      "Recovery Phrase و Base64url Code را در مکان امن ذخیره کرده‌ام.",
    continue: "ادامه",
    successWithoutRecovery: "Vault محلی با موفقیت ساخته شد.",
  },
  en: {
    title: "Set up Personal AI",
    subtitle: "First prepare your local encrypted Vault and profile.",
    localAccount: "Local Account",
    onlineAccount: "Online Account",
    onlineLater: "OAuth providers are enabled after Local Vault onboarding.",
    profileName: "Profile Name",
    profilePlaceholder: "Example: Mohammad Reza",
    addressName: "How the assistant addresses you",
    addressHint: "If empty, Profile Name is used.",
    passphrase: "Vault Passphrase",
    passphraseConfirm: "Confirm Vault Passphrase",
    recoveryTitle: "Optional Recovery Key",
    recoveryDescription:
      "If you forget the passphrase, only the Recovery Phrase or Base64url Code can unlock the Vault.",
    recoveryChoice: "Create Recovery Key",
    createPreview: "Vault creation requires final confirmation",
    emptyName: "Profile Name is required.",
    emptyPassphrase: "Vault Passphrase cannot be empty.",
    passphraseMismatch: "Passphrases do not match.",
    securityNote:
      "The passphrase is not saved in browser storage or logs.",
    confirmTitle: "Final Vault Creation Confirmation",
    confirmDescription:
      "This action creates an encrypted local Vault and first local profile.",
    confirmProfile: "Profile Name",
    confirmAddress: "Address Name",
    confirmRecovery: "Recovery Key",
    acknowledge:
      "I understand this creates a local Vault and the passphrase cannot be recovered.",
    finalCreate: "Create Encrypted Vault",
    cancel: "Cancel",
    creating: "Creating Vault...",
    createError: "Vault creation failed.",
    recoveryResultTitle: "Store your Recovery Key",
    phrase: "English BIP39 Recovery Phrase",
    code: "Base64url Recovery Code",
    copyPhrase: "Copy Phrase",
    copyCode: "Copy Code",
    download: "Download Recovery File",
    copied: "Copied",
    recoveryWarning:
      "This information is displayed once. The downloaded file is sensitive plaintext.",
    recoveryAcknowledgment:
      "I stored the Recovery Phrase and Base64url Code in a secure location.",
    continue: "Continue",
    successWithoutRecovery: "Local Vault was created successfully.",
  },
  ar: {
    title: "إعداد Personal AI",
    subtitle: "أنشئ أولاً خزنتك المحلية وملفك الشخصي المشفر.",
    localAccount: "حساب محلي",
    onlineAccount: "حساب عبر الإنترنت",
    onlineLater: "يتم تفعيل موفري OAuth بعد إعداد الخزنة المحلية.",
    profileName: "اسم الملف الشخصي",
    profilePlaceholder: "مثال: Mohammad Reza",
    addressName: "الاسم الذي يناديك به المساعد",
    addressHint: "إذا تركته فارغاً، يستخدم اسم الملف الشخصي.",
    passphrase: "عبارة مرور الخزنة",
    passphraseConfirm: "تأكيد عبارة مرور الخزنة",
    recoveryTitle: "مفتاح استرداد اختياري",
    recoveryDescription:
      "إذا نسيت عبارة المرور، يمكن لعبارة الاسترداد أو رمز Base64url فقط فتح الخزنة.",
    recoveryChoice: "إنشاء مفتاح استرداد",
    createPreview: "إنشاء الخزنة يحتاج تأكيداً نهائياً",
    emptyName: "اسم الملف الشخصي مطلوب.",
    emptyPassphrase: "عبارة مرور الخزنة لا يمكن أن تكون فارغة.",
    passphraseMismatch: "عبارتا المرور غير متطابقتين.",
    securityNote: "لا يتم حفظ عبارة المرور في المتصفح أو السجلات.",
    confirmTitle: "تأكيد إنشاء الخزنة",
    confirmDescription: "سيتم إنشاء خزنة محلية مشفرة وملف شخصي.",
    confirmProfile: "اسم الملف الشخصي",
    confirmAddress: "اسم النداء",
    confirmRecovery: "مفتاح الاسترداد",
    acknowledge: "أفهم أن عبارة مرور الخزنة لا يمكن استعادتها.",
    finalCreate: "إنشاء خزنة مشفرة",
    cancel: "إلغاء",
    creating: "جارٍ إنشاء الخزنة...",
    createError: "تعذر إنشاء الخزنة.",
    recoveryResultTitle: "احفظ مفتاح الاسترداد",
    phrase: "عبارة استرداد BIP39 الإنجليزية",
    code: "رمز استرداد Base64url",
    copyPhrase: "نسخ العبارة",
    copyCode: "نسخ الرمز",
    download: "تنزيل ملف الاسترداد",
    copied: "تم النسخ",
    recoveryWarning: "تظهر هذه المعلومات مرة واحدة والملف النصي حساس.",
    recoveryAcknowledgment: "حفظت معلومات الاسترداد في مكان آمن.",
    continue: "متابعة",
    successWithoutRecovery: "تم إنشاء الخزنة المحلية بنجاح.",
  },
  tr: {
    title: "Personal AI kurulumu",
    subtitle: "Önce yerel şifreli Vault ve profilini hazırlayın.",
    localAccount: "Yerel Hesap",
    onlineAccount: "Çevrimiçi Hesap",
    onlineLater: "OAuth sağlayıcıları Local Vault onboarding sonrasında etkinleşir.",
    profileName: "Profil Adı",
    profilePlaceholder: "Örnek: Mohammad Reza",
    addressName: "Asistanın sana hitap edeceği ad",
    addressHint: "Boş bırakılırsa Profil Adı kullanılır.",
    passphrase: "Vault Parolası",
    passphraseConfirm: "Vault Parolasını Doğrula",
    recoveryTitle: "İsteğe Bağlı Kurtarma Anahtarı",
    recoveryDescription:
      "Parolayı unutursanız yalnızca Recovery Phrase veya Base64url Code Vault'u açabilir.",
    recoveryChoice: "Kurtarma Anahtarı oluştur",
    createPreview: "Vault oluşturma son onay gerektirir",
    emptyName: "Profil Adı gereklidir.",
    emptyPassphrase: "Vault Parolası boş olamaz.",
    passphraseMismatch: "Parolalar eşleşmiyor.",
    securityNote: "Parola browser storage veya loglarda saklanmaz.",
    confirmTitle: "Son Vault Oluşturma Onayı",
    confirmDescription: "Şifreli yerel Vault ve profil oluşturulur.",
    confirmProfile: "Profil Adı",
    confirmAddress: "Hitap Adı",
    confirmRecovery: "Kurtarma Anahtarı",
    acknowledge: "Vault parolasının kurtarılamayacağını anlıyorum.",
    finalCreate: "Şifreli Vault Oluştur",
    cancel: "İptal",
    creating: "Vault oluşturuluyor...",
    createError: "Vault oluşturulamadı.",
    recoveryResultTitle: "Kurtarma Anahtarını Sakla",
    phrase: "English BIP39 Recovery Phrase",
    code: "Base64url Recovery Code",
    copyPhrase: "Phrase Kopyala",
    copyCode: "Code Kopyala",
    download: "Recovery Dosyasını İndir",
    copied: "Kopyalandı",
    recoveryWarning: "Bu bilgi bir kez gösterilir; indirilen dosya hassas düz metindir.",
    recoveryAcknowledgment: "Kurtarma bilgilerini güvenli bir yerde sakladım.",
    continue: "Devam",
    successWithoutRecovery: "Yerel Vault başarıyla oluşturuldu.",
  },
};

export function OnboardingScreen({
  language,
  status,
  onVaultCreated,
}: {
  language: AppLanguage;
  status: OnboardingStatus;
  onVaultCreated: () => void;
}) {
  const t = copy[language];
  const [profileName, setProfileName] = useState("");
  const [addressName, setAddressName] = useState("");
  const [passphrase, setPassphrase] = useState("");
  const [confirmPassphrase, setConfirmPassphrase] = useState("");
  const [createRecoveryKey, setCreateRecoveryKey] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [recoveryResult, setRecoveryResult] =
    useState<LocalVaultOnboardingResponse | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const validationMessage = useMemo(() => {
    if (!profileName.trim()) return t.emptyName;
    if (!passphrase.trim()) return t.emptyPassphrase;
    if (passphrase !== confirmPassphrase) return t.passphraseMismatch;
    return null;
  }, [confirmPassphrase, passphrase, profileName, t]);

  const openConfirmation = () => {
    setNotice(validationMessage);

    if (!validationMessage) {
      setAcknowledged(false);
      setConfirmationOpen(true);
    }
  };

  const finalCreate = async () => {
    if (!acknowledged) return;

    setSubmitting(true);
    setNotice(null);

    try {
      const result = await createLocalVault({
        profile_name: profileName,
        address_name: addressName.trim() || null,
        vault_passphrase: passphrase,
        create_recovery_key: createRecoveryKey,
      });

      setConfirmationOpen(false);
      setPassphrase("");
      setConfirmPassphrase("");

      if (result.recovery_key_created) {
        setRecoveryResult(result);
      } else {
        setNotice(t.successWithoutRecovery);
        onVaultCreated();
      }
    } catch {
      setNotice(t.createError);
      setConfirmationOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  const copyText = async (label: string, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(label);
    } catch {
      setCopied(null);
    }
  };

  const downloadRecovery = () => {
    if (!recoveryResult?.recovery_phrase || !recoveryResult.recovery_base64url) {
      return;
    }

    const content = [
      "Personal AI Recovery Key",
      "",
      "English BIP39 Recovery Phrase:",
      recoveryResult.recovery_phrase,
      "",
      "Base64url Recovery Code:",
      recoveryResult.recovery_base64url,
      "",
      "Keep this file in a secure location.",
    ].join("\n");

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "personal-ai-recovery-key.txt";
    link.click();

    URL.revokeObjectURL(url);
  };

  const completeRecovery = () => {
    setRecoveryResult(null);
    setCopied(null);
    setNotice(t.successWithoutRecovery);
    onVaultCreated();
  };

  if (recoveryResult?.recovery_phrase && recoveryResult.recovery_base64url) {
    return (
      <section className="onboarding-screen recovery-result">
        <div className="onboarding-heading">
          <div className="onboarding-icon">
            <KeyRound size={30} />
          </div>
          <div>
            <h3>{t.recoveryResultTitle}</h3>
            <p>{t.recoveryWarning}</p>
          </div>
        </div>

        <div className="recovery-material">
          <strong>{t.phrase}</strong>
          <code dir="ltr">{recoveryResult.recovery_phrase}</code>
          <button
            className="button secondary"
            onClick={() =>
              void copyText(t.copyPhrase, recoveryResult.recovery_phrase!)
            }
            type="button"
          >
            <Copy size={16} />
            {copied === t.copyPhrase ? t.copied : t.copyPhrase}
          </button>
        </div>

        <div className="recovery-material">
          <strong>{t.code}</strong>
          <code dir="ltr">{recoveryResult.recovery_base64url}</code>
          <button
            className="button secondary"
            onClick={() =>
              void copyText(
                t.copyCode,
                recoveryResult.recovery_base64url!,
              )
            }
            type="button"
          >
            <Copy size={16} />
            {copied === t.copyCode ? t.copied : t.copyCode}
          </button>
        </div>

        <button
          className="button secondary"
          onClick={downloadRecovery}
          type="button"
        >
          <Download size={16} />
          {t.download}
        </button>

        <label className="recovery-acknowledgment">
          <input
            checked={acknowledged}
            onChange={(event) => setAcknowledged(event.target.checked)}
            type="checkbox"
          />
          <span>{t.recoveryAcknowledgment}</span>
        </label>

        <button
          className="button primary onboarding-submit"
          disabled={!acknowledged}
          onClick={completeRecovery}
          type="button"
        >
          <CheckCircle2 size={17} />
          {t.continue}
        </button>
      </section>
    );
  }

  return (
    <section
      className="onboarding-screen"
      dir={language === "fa" || language === "ar" ? "rtl" : "ltr"}
    >
      <div className="onboarding-heading">
        <div className="onboarding-icon">
          <ShieldCheck size={30} />
        </div>
        <div>
          <h3>
            <span>{t.title.replace("Personal AI", "").trim()}</span>{" "}
            <bdi dir="ltr">Personal AI</bdi>
          </h3>
          <p>{t.subtitle}</p>
        </div>
      </div>

      <div className="onboarding-account-options">
        <button className="account-option is-active" type="button">
          <UserRound size={18} />
          {t.localAccount}
        </button>
        <button className="account-option" disabled type="button">
          <Cloud size={18} />
          {t.onlineAccount}
        </button>
      </div>

      <p className="onboarding-muted">{t.onlineLater}</p>

      <div className="onboarding-grid">
        <label>
          <span>{t.profileName}</span>
          <input
            className="onboarding-text-input"
            dir="auto"
            onChange={(event) => setProfileName(event.target.value)}
            placeholder={t.profilePlaceholder}
            value={profileName}
          />
          <small aria-hidden="true" className="onboarding-field-spacer">
            &nbsp;
          </small>
        </label>

        <label>
          <span>{t.addressName}</span>
          <input
            className="onboarding-text-input"
            dir="auto"
            onChange={(event) => setAddressName(event.target.value)}
            placeholder={profileName || t.profilePlaceholder}
            value={addressName}
          />
          <small>{t.addressHint}</small>
        </label>

        <label>
          <span>{t.passphrase}</span>
          <input
            autoComplete="new-password"
            className="onboarding-password-input"
            dir="ltr"
            onChange={(event) => setPassphrase(event.target.value)}
            type="password"
            value={passphrase}
          />
        </label>

        <label>
          <span>{t.passphraseConfirm}</span>
          <input
            autoComplete="new-password"
            className="onboarding-password-input"
            dir="ltr"
            onChange={(event) => setConfirmPassphrase(event.target.value)}
            type="password"
            value={confirmPassphrase}
          />
        </label>
      </div>

      <label className="recovery-choice">
        <input
          checked={createRecoveryKey}
          onChange={(event) => setCreateRecoveryKey(event.target.checked)}
          type="checkbox"
        />
        <span>
          <strong>{t.recoveryChoice}</strong>
          <small className="onboarding-bidi-text">
            {t.recoveryDescription}{" "}
            <bdi dir="ltr">Recovery Phrase · Base64url</bdi>
          </small>
        </span>
        <KeyRound size={20} />
      </label>

      <div className="onboarding-security-note">
        <AlertTriangle size={17} />
        <span>{t.securityNote}</span>
      </div>

      <button
        className="button primary onboarding-submit"
        onClick={openConfirmation}
        type="button"
      >
        <CheckCircle2 size={17} />
        {t.createPreview}
      </button>

      {notice && <p className="onboarding-notice">{notice}</p>}

      <p className="onboarding-status">
        {status.vault_configured
          ? "Vault configured"
          : "Vault not created"}
      </p>

      {confirmationOpen && (
        <div className="vault-confirmation-layer">
          <button
            aria-label={t.cancel}
            className="vault-confirmation-backdrop"
            onClick={() => setConfirmationOpen(false)}
            type="button"
          />

          <div className="vault-confirmation-modal">
            <button
              aria-label={t.cancel}
              className="icon-button confirmation-close"
              onClick={() => setConfirmationOpen(false)}
              type="button"
            >
              <X size={20} />
            </button>

            <h3>{t.confirmTitle}</h3>
            <p>{t.confirmDescription}</p>

            <dl>
              <div>
                <dt>{t.confirmProfile}</dt>
                <dd dir="auto">{profileName.trim()}</dd>
              </div>
              <div>
                <dt>{t.confirmAddress}</dt>
                <dd dir="auto">{addressName.trim() || profileName.trim()}</dd>
              </div>
              <div>
                <dt>{t.confirmRecovery}</dt>
                <dd>{createRecoveryKey ? t.recoveryChoice : t.cancel}</dd>
              </div>
            </dl>

            <label className="confirmation-acknowledgment">
              <input
                checked={acknowledged}
                onChange={(event) => setAcknowledged(event.target.checked)}
                type="checkbox"
              />
              <span>{t.acknowledge}</span>
            </label>

            <div className="confirmation-actions">
              <button
                className="button secondary"
                onClick={() => setConfirmationOpen(false)}
                type="button"
              >
                {t.cancel}
              </button>
              <button
                className="button primary"
                disabled={!acknowledged || submitting}
                onClick={() => void finalCreate()}
                type="button"
              >
                <CheckCircle2 size={16} />
                {submitting ? t.creating : t.finalCreate}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
