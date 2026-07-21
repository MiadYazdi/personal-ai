import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  Eye,
  EyeOff,
  KeyRound,
  Lock,
  LockKeyhole,
  RefreshCw,
  ShieldCheck,
  Unlock,
} from "lucide-react";

import {
  fetchVaultSessionStatus,
  lockVault,
  unlockVault,
} from "./api";
import type {
  AppLanguage,
  VaultSessionStatus,
  VaultUnlockRequest,
} from "./types";

type RecoveryMethod = "recovery_bip39" | "recovery_base64url";

type VaultUnlockCopy = {
  title: string;
  lockedTitle: string;
  unlockedTitle: string;
  passphrase: string;
  passphraseHint: string;
  unlock: string;
  unlocking: string;
  lock: string;
  locking: string;
  recovery: string;
  recoveryHint: string;
  recoveryPhrase: string;
  recoveryCode: string;
  usePassphrase: string;
  chooseRecovery: string;
  profile: string;
  address: string;
  autoLock: string;
  minutes: string;
  refresh: string;
  loading: string;
  emptyCredential: string;
  unlockError: string;
  lockError: string;
  statusError: string;
  localOnly: string;
};

const copy: Record<AppLanguage, VaultUnlockCopy> = {
  fa: {
    title: "Vault محلی",
    lockedTitle: "Vault قفل است",
    unlockedTitle: "Vault باز است",
    passphrase: "Vault Passphrase",
    passphraseHint: "Passphrase فقط برای بازکردن Vault محلی استفاده می‌شود و ذخیره نمی‌شود.",
    unlock: "بازکردن Vault",
    unlocking: "در حال بازکردن...",
    lock: "قفل‌کردن Vault",
    locking: "در حال قفل‌کردن...",
    recovery: "استفاده از Recovery Key",
    recoveryHint: "Recovery Phrase یا Base64url Code را فقط در صورت نیاز انتخاب کن.",
    recoveryPhrase: "English BIP39 Recovery Phrase",
    recoveryCode: "Base64url Recovery Code",
    usePassphrase: "استفاده از Passphrase",
    chooseRecovery: "روش Recovery را انتخاب کن",
    profile: "Profile",
    address: "نام خطاب",
    autoLock: "قفل خودکار پس از عدم فعالیت",
    minutes: "دقیقه",
    refresh: "به‌روزرسانی وضعیت",
    loading: "در حال دریافت وضعیت Vault...",
    emptyCredential: "Credential نباید خالی باشد.",
    unlockError: "Vault با این Credential باز نشد.",
    lockError: "قفل‌کردن Vault انجام نشد.",
    statusError: "وضعیت Vault بارگذاری نشد.",
    localOnly: "Credential فقط به Backend محلی روی 127.0.0.1 ارسال می‌شود.",
  },
  en: {
    title: "Local Vault",
    lockedTitle: "Vault is locked",
    unlockedTitle: "Vault is unlocked",
    passphrase: "Vault Passphrase",
    passphraseHint: "The passphrase is used only to unlock the local Vault and is not stored.",
    unlock: "Unlock Vault",
    unlocking: "Unlocking...",
    lock: "Lock Vault",
    locking: "Locking...",
    recovery: "Use Recovery Key",
    recoveryHint: "Choose Recovery Phrase or Base64url Code only when needed.",
    recoveryPhrase: "English BIP39 Recovery Phrase",
    recoveryCode: "Base64url Recovery Code",
    usePassphrase: "Use Passphrase",
    chooseRecovery: "Choose a Recovery method",
    profile: "Profile",
    address: "Address name",
    autoLock: "Automatic lock after inactivity",
    minutes: "minutes",
    refresh: "Refresh Vault status",
    loading: "Loading Vault status...",
    emptyCredential: "The credential cannot be empty.",
    unlockError: "The Vault could not be unlocked with this credential.",
    lockError: "The Vault could not be locked.",
    statusError: "The Vault status could not be loaded.",
    localOnly: "The credential is sent only to the local Backend on 127.0.0.1.",
  },
  ar: {
    title: "الخزنة المحلية",
    lockedTitle: "الخزنة مقفلة",
    unlockedTitle: "الخزنة مفتوحة",
    passphrase: "عبارة مرور الخزنة",
    passphraseHint: "تُستخدم عبارة المرور لفتح الخزنة المحلية فقط ولا يتم حفظها.",
    unlock: "فتح الخزنة",
    unlocking: "جارٍ الفتح...",
    lock: "قفل الخزنة",
    locking: "جارٍ القفل...",
    recovery: "استخدام مفتاح الاسترداد",
    recoveryHint: "اختر عبارة الاسترداد أو رمز Base64url عند الحاجة فقط.",
    recoveryPhrase: "عبارة استرداد BIP39 الإنجليزية",
    recoveryCode: "رمز استرداد Base64url",
    usePassphrase: "استخدام عبارة المرور",
    chooseRecovery: "اختر طريقة الاسترداد",
    profile: "الملف الشخصي",
    address: "اسم النداء",
    autoLock: "قفل تلقائي بعد عدم النشاط",
    minutes: "دقيقة",
    refresh: "تحديث حالة الخزنة",
    loading: "جارٍ تحميل حالة الخزنة...",
    emptyCredential: "لا يمكن أن تكون بيانات الفتح فارغة.",
    unlockError: "تعذر فتح الخزنة بهذه البيانات.",
    lockError: "تعذر قفل الخزنة.",
    statusError: "تعذر تحميل حالة الخزنة.",
    localOnly: "يتم إرسال بيانات الفتح إلى Backend المحلي على 127.0.0.1 فقط.",
  },
  tr: {
    title: "Yerel Kasa",
    lockedTitle: "Kasa kilitli",
    unlockedTitle: "Kasa açık",
    passphrase: "Vault Parolası",
    passphraseHint: "Parola yalnızca yerel Kasayı açmak için kullanılır ve saklanmaz.",
    unlock: "Kasayı Aç",
    unlocking: "Açılıyor...",
    lock: "Kasayı Kilitle",
    locking: "Kilitleniyor...",
    recovery: "Kurtarma Anahtarını Kullan",
    recoveryHint: "Recovery Phrase veya Base64url Code seçeneğini yalnızca gerektiğinde kullanın.",
    recoveryPhrase: "English BIP39 Recovery Phrase",
    recoveryCode: "Base64url Recovery Code",
    usePassphrase: "Parolayı Kullan",
    chooseRecovery: "Bir kurtarma yöntemi seçin",
    profile: "Profil",
    address: "Hitap adı",
    autoLock: "Hareketsizlik sonrası otomatik kilit",
    minutes: "dakika",
    refresh: "Kasa durumunu yenile",
    loading: "Kasa durumu yükleniyor...",
    emptyCredential: "Kimlik bilgisi boş olamaz.",
    unlockError: "Kasa bu kimlik bilgisiyle açılamadı.",
    lockError: "Kasa kilitlenemedi.",
    statusError: "Kasa durumu yüklenemedi.",
    localOnly: "Kimlik bilgisi yalnızca 127.0.0.1 üzerindeki yerel Backend'e gönderilir.",
  },
};

export function VaultUnlockScreen({
  language,
  onVaultSessionChanged,
}: {
  language: AppLanguage;
  onVaultSessionChanged: () => void;
}) {
  const t = copy[language];
  const [session, setSession] = useState<VaultSessionStatus | null>(null);
  const [credential, setCredential] = useState("");
  const [showCredential, setShowCredential] = useState(false);
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryMethod, setRecoveryMethod] =
    useState<RecoveryMethod | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<"unlock" | "lock" | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadStatus = async () => {
    try {
      const next = await fetchVaultSessionStatus();
      setSession(next);
      setNotice(null);
    } catch {
      setNotice(t.statusError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadStatus();
    const timer = window.setInterval(() => void loadStatus(), 60_000);
    return () => window.clearInterval(timer);
    // The status poll deliberately does not refresh Backend inactivity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isUnlocked = session?.vault_state === "unlocked";
  const timeoutMinutes = useMemo(
    () => Math.round((session?.inactivity_timeout_seconds ?? 1800) / 60),
    [session?.inactivity_timeout_seconds],
  );

  const choosePassphrase = () => {
    setCredential("");
    setShowCredential(false);
    setRecoveryMethod(null);
    setShowRecovery(false);
    setNotice(null);
  };

  const chooseRecovery = (method: RecoveryMethod) => {
    setCredential("");
    setShowCredential(false);
    setRecoveryMethod(method);
    setShowRecovery(true);
    setNotice(null);
  };

  const submitUnlock = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!credential.trim()) {
      setNotice(t.emptyCredential);
      return;
    }

    const request: VaultUnlockRequest = recoveryMethod === "recovery_bip39"
      ? { method: "recovery_bip39", recovery_phrase: credential }
      : recoveryMethod === "recovery_base64url"
        ? { method: "recovery_base64url", recovery_base64url: credential }
        : { method: "passphrase", passphrase: credential };

    setWorking("unlock");
    setNotice(null);

    try {
      const next = await unlockVault(request);
      setSession(next);
      setCredential("");
      setShowCredential(false);
      setShowRecovery(false);
      setRecoveryMethod(null);
      onVaultSessionChanged();
    } catch {
      setNotice(t.unlockError);
    } finally {
      setWorking(null);
    }
  };

  const submitLock = async () => {
    setWorking("lock");
    setNotice(null);

    try {
      const next = await lockVault();
      setSession(next);
      setCredential("");
      setShowCredential(false);
      setShowRecovery(false);
      setRecoveryMethod(null);
      onVaultSessionChanged();
    } catch {
      setNotice(t.lockError);
    } finally {
      setWorking(null);
    }
  };

  const activeLabel = recoveryMethod === "recovery_bip39"
    ? t.recoveryPhrase
    : recoveryMethod === "recovery_base64url"
      ? t.recoveryCode
      : t.passphrase;

  return (
    <section className="vault-unlock-card" dir={language === "fa" || language === "ar" ? "rtl" : "ltr"}>
      <div className="vault-unlock-heading">
        <div className="vault-unlock-icon">
          {isUnlocked ? <Unlock size={22} /> : <LockKeyhole size={22} />}
        </div>
        <div>
          <p className="vault-unlock-eyebrow">{t.title}</p>
          <h3>{isUnlocked ? t.unlockedTitle : t.lockedTitle}</h3>
        </div>
        <button
          aria-label={t.refresh}
          className="vault-status-refresh"
          disabled={loading || working !== null}
          onClick={() => {
            setLoading(true);
            void loadStatus();
          }}
          title={t.refresh}
          type="button"
        >
          <RefreshCw className={loading ? "spin" : ""} size={17} />
        </button>
      </div>

      {loading && session === null ? (
        <p className="vault-unlock-muted">{t.loading}</p>
      ) : isUnlocked ? (
        <div className="vault-unlocked-content">
          <div className="vault-profile-context">
            <ShieldCheck size={19} />
            <div>
              <strong>{session?.profile_context?.profile_name ?? t.profile}</strong>
              <span>
                {t.address}: {session?.profile_context?.address_name ?? "—"}
              </span>
            </div>
          </div>
          <p className="vault-unlock-muted">
            {t.autoLock}: {timeoutMinutes} {t.minutes}
          </p>
          <button
            className="button vault-lock-button"
            disabled={working !== null}
            onClick={() => void submitLock()}
            type="button"
          >
            <Lock size={17} />
            {working === "lock" ? t.locking : t.lock}
          </button>
        </div>
      ) : (
        <form className="vault-unlock-form" onSubmit={(event) => void submitUnlock(event)}>
          {!showRecovery ? (
            <>
              <label className="vault-credential-label">
                <span>{t.passphrase}</span>
                <span className="vault-credential-control" dir="ltr">
                  <input
                    autoComplete="current-password"
                    dir="ltr"
                    onChange={(event) => setCredential(event.target.value)}
                    type={showCredential ? "text" : "password"}
                    value={credential}
                  />
                  <button
                    aria-label={showCredential ? "Hide credential" : "Show credential"}
                    onClick={() => setShowCredential((current) => !current)}
                    type="button"
                  >
                    {showCredential ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </span>
              </label>
              <p className="vault-unlock-muted">{t.passphraseHint}</p>
              <button className="vault-recovery-link" onClick={() => setShowRecovery(true)} type="button">
                <KeyRound size={16} />
                {t.recovery}
              </button>
            </>
          ) : recoveryMethod === null ? (
            <div className="vault-recovery-choice">
              <p className="vault-unlock-muted">{t.recoveryHint}</p>
              <strong>{t.chooseRecovery}</strong>
              <div className="vault-recovery-options">
                <button onClick={() => chooseRecovery("recovery_bip39")} type="button">
                  {t.recoveryPhrase}
                </button>
                <button onClick={() => chooseRecovery("recovery_base64url")} type="button">
                  {t.recoveryCode}
                </button>
              </div>
              <button className="vault-recovery-link" onClick={choosePassphrase} type="button">
                {t.usePassphrase}
              </button>
            </div>
          ) : (
            <>
              <label className="vault-credential-label">
                <span>{activeLabel}</span>
                <span className="vault-credential-control" dir="ltr">
                  <input
                    autoComplete="off"
                    dir="ltr"
                    onChange={(event) => setCredential(event.target.value)}
                    type={showCredential ? "text" : "password"}
                    value={credential}
                  />
                  <button
                    aria-label={showCredential ? "Hide credential" : "Show credential"}
                    onClick={() => setShowCredential((current) => !current)}
                    type="button"
                  >
                    {showCredential ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </span>
              </label>
              <button className="vault-recovery-link" onClick={() => {
                setCredential("");
                setRecoveryMethod(null);
                setShowCredential(false);
              }} type="button">
                {t.chooseRecovery}
              </button>
              <button className="vault-recovery-link" onClick={choosePassphrase} type="button">
                {t.usePassphrase}
              </button>
            </>
          )}

          <p className="vault-local-only" dir="ltr">127.0.0.1 · {t.localOnly}</p>
          {notice && <p className="vault-unlock-notice" role="status">{notice}</p>}
          {showRecovery && recoveryMethod === null ? null : (
            <button className="button primary vault-unlock-submit" disabled={working !== null} type="submit">
              <Unlock size={17} />
              {working === "unlock" ? t.unlocking : t.unlock}
            </button>
          )}
        </form>
      )}

    </section>
  );
}
