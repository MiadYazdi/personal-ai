import type { AppLanguage } from "./types";

export type TextKey =
  | "product"
  | "subtitle"
  | "conversation"
  | "localMode"
  | "online"
  | "onlineDisabled"
  | "noExternal"
  | "vault"
  | "model"
  | "agent"
  | "quick"
  | "deep"
  | "ready"
  | "setupRequired"
  | "locked"
  | "unlocked"
  | "notStarted"
  | "systemStatus"
  | "modelMessage"
  | "language"
  | "theme"
  | "system"
  | "dark"
  | "light"
  | "appMenu"
  | "settings"
  | "customize"
  | "save"
  | "saving"
  | "saved"
  | "unsaved"
  | "close"
  | "refresh"
  | "accent"
  | "customColor"
  | "sidebar"
  | "placement"
  | "left"
  | "right"
  | "mode"
  | "expanded"
  | "compact"
  | "hidden"
  | "width"
  | "normal"
  | "wide"
  | "fontScale"
  | "small"
  | "default"
  | "large"
  | "xlarge"
  | "density"
  | "comfortable"
  | "motion"
  | "full"
  | "reduced"
  | "controlsLocation"
  | "sidebarSettings"
  | "header"
  | "both"
  | "mobileBehavior"
  | "followDesktop"
  | "compactRail"
  | "drawer"
  | "widgets"
  | "show"
  | "hide"
  | "presets"
  | "focus"
  | "minimal"
  | "reset"
  | "dragHelp"
  | "openControls"
  | "saveError"
  | "loadError"
  | "chatPlaceholder";

export interface LocalePack {
  direction: "rtl" | "ltr";
  labels: Record<TextKey, string>;
}

const en: LocalePack = {
  direction: "ltr",
  labels: {
    product: "Personal AI",
    subtitle: "Personal, local-first and controllable assistant",
    conversation: "Conversation workspace",
    localMode: "Local mode",
    online: "Online",
    onlineDisabled: "Online disabled",
    noExternal: "No external request is active",
    vault: "Vault",
    model: "Local model",
    agent: "Device Agent",
    quick: "Quick",
    deep: "Deep",
    ready: "Ready",
    setupRequired: "Setup required",
    locked: "Locked",
    unlocked: "Unlocked",
    notStarted: "Not started yet",
    systemStatus: "System status",
    modelMessage: "Local chat is ready. This first history stays only in the browser.",
    language: "Language",
    theme: "Theme",
    system: "System",
    dark: "Dark",
    light: "Light",
    appMenu: "App menu",
    settings: "Settings",
    customize: "Customize UI",
    save: "Save preferences",
    saving: "Saving...",
    saved: "Preferences saved",
    unsaved: "Unsaved changes",
    close: "Close",
    refresh: "Refresh status",
    accent: "Accent color",
    customColor: "Custom color",
    sidebar: "Sidebar",
    placement: "Placement",
    left: "Left",
    right: "Right",
    mode: "Mode",
    expanded: "Expanded",
    compact: "Compact",
    hidden: "Hidden",
    width: "Width",
    normal: "Normal",
    wide: "Wide",
    fontScale: "Font size",
    small: "Small",
    default: "Default",
    large: "Large",
    xlarge: "Extra large",
    density: "Density",
    comfortable: "Comfortable",
    motion: "Motion",
    full: "Full",
    reduced: "Reduced",
    controlsLocation: "Controls location",
    sidebarSettings: "Sidebar settings",
    header: "Header",
    both: "Both",
    mobileBehavior: "Mobile sidebar",
    followDesktop: "Follow desktop",
    compactRail: "Compact rail",
    drawer: "Drawer",
    widgets: "Widgets",
    show: "Show",
    hide: "Hide",
    presets: "Presets",
    focus: "Focus",
    minimal: "Minimal",
    reset: "Reset layout",
    dragHelp: "Drag cards by their handles, then save preferences.",
    openControls: "Open controls",
    saveError: "Could not save preferences",
    loadError: "Could not load local preferences",
    chatPlaceholder: "The chat core will connect to the local model in the next step...",
  },
};

const fa: LocalePack = {
  direction: "rtl",
  labels: {
    product: "Personal AI",
    subtitle: "دستیار شخصی، محلی و قابل‌کنترل",
    conversation: "فضای گفت‌وگو",
    localMode: "حالت محلی",
    online: "آنلاین",
    onlineDisabled: "اینترنت غیرفعال",
    noExternal: "هیچ درخواست خارجی فعالی وجود ندارد",
    vault: "Vault",
    model: "مدل محلی",
    agent: "Device Agent",
    quick: "Quick",
    deep: "Deep",
    ready: "آماده",
    setupRequired: "نیازمند راه‌اندازی",
    locked: "قفل است",
    unlocked: "باز است",
    notStarted: "هنوز شروع نشده",
    systemStatus: "وضعیت سیستم",
    modelMessage: "چت محلی آماده است. تاریخچهٔ این مرحله فقط در مرورگر نگه داشته می‌شود.",
    language: "زبان",
    theme: "تم",
    system: "سیستم",
    dark: "تیره",
    light: "روشن",
    appMenu: "منوی برنامه",
    settings: "تنظیمات",
    customize: "شخصی‌سازی رابط",
    save: "ذخیرهٔ تنظیمات",
    saving: "در حال ذخیره...",
    saved: "تنظیمات ذخیره شد",
    unsaved: "تغییرات ذخیره نشده",
    close: "بستن",
    refresh: "به‌روزرسانی وضعیت",
    accent: "رنگ اصلی",
    customColor: "رنگ دلخواه",
    sidebar: "نوار کناری",
    placement: "محل",
    left: "چپ",
    right: "راست",
    mode: "حالت",
    expanded: "باز",
    compact: "فشرده",
    hidden: "مخفی",
    width: "عرض",
    normal: "عادی",
    wide: "عریض",
    fontScale: "اندازهٔ فونت",
    small: "کوچک",
    default: "پیش‌فرض",
    large: "بزرگ",
    xlarge: "خیلی بزرگ",
    density: "تراکم رابط",
    comfortable: "راحت",
    motion: "حرکت",
    full: "کامل",
    reduced: "کم",
    controlsLocation: "محل کنترل‌ها",
    sidebarSettings: "تنظیمات Sidebar",
    header: "Header",
    both: "هر دو",
    mobileBehavior: "Sidebar موبایل",
    followDesktop: "هماهنگ با دسکتاپ",
    compactRail: "نوار فشرده",
    drawer: "Drawer",
    widgets: "ویجت‌ها",
    show: "نمایش",
    hide: "مخفی‌کردن",
    presets: "چیدمان‌های آماده",
    focus: "تمرکز",
    minimal: "حداقلی",
    reset: "بازنشانی چیدمان",
    dragHelp: "کارت‌ها را از handle جابه‌جا کن و سپس تنظیمات را ذخیره کن.",
    openControls: "بازکردن کنترل‌ها",
    saveError: "ذخیرهٔ تنظیمات انجام نشد",
    loadError: "بارگذاری تنظیمات محلی انجام نشد",
    chatPlaceholder: "هستهٔ چت در مرحلهٔ بعد به مدل محلی متصل می‌شود...",
  },
};

const ar: LocalePack = {
  direction: "rtl",
  labels: {
    product: "Personal AI",
    subtitle: "مساعد شخصي محلي وقابل للتحكم",
    conversation: "مساحة المحادثة",
    localMode: "الوضع المحلي",
    online: "عبر الإنترنت",
    onlineDisabled: "الإنترنت معطل",
    noExternal: "لا يوجد طلب خارجي نشط",
    vault: "الخزنة",
    model: "النموذج المحلي",
    agent: "وكيل الجهاز",
    quick: "Quick",
    deep: "Deep",
    ready: "جاهز",
    setupRequired: "يتطلب الإعداد",
    locked: "مقفل",
    unlocked: "مفتوح",
    notStarted: "لم يبدأ بعد",
    systemStatus: "حالة النظام",
    modelMessage: "المحادثة المحلية جاهزة. يبقى سجل هذه المرحلة في المتصفح فقط.",
    language: "اللغة",
    theme: "المظهر",
    system: "النظام",
    dark: "داكن",
    light: "فاتح",
    appMenu: "قائمة التطبيق",
    settings: "الإعدادات",
    customize: "تخصيص الواجهة",
    save: "حفظ التفضيلات",
    saving: "جارٍ الحفظ...",
    saved: "تم حفظ التفضيلات",
    unsaved: "تغييرات غير محفوظة",
    close: "إغلاق",
    refresh: "تحديث الحالة",
    accent: "لون التمييز",
    customColor: "لون مخصص",
    sidebar: "الشريط الجانبي",
    placement: "الموضع",
    left: "يسار",
    right: "يمين",
    mode: "الوضع",
    expanded: "موسّع",
    compact: "مضغوط",
    hidden: "مخفي",
    width: "العرض",
    normal: "عادي",
    wide: "واسع",
    fontScale: "حجم الخط",
    small: "صغير",
    default: "افتراضي",
    large: "كبير",
    xlarge: "كبير جداً",
    density: "كثافة الواجهة",
    comfortable: "مريح",
    motion: "الحركة",
    full: "كاملة",
    reduced: "مخففة",
    controlsLocation: "مكان التحكم",
    sidebarSettings: "إعدادات الشريط",
    header: "الرأس",
    both: "كلاهما",
    mobileBehavior: "الشريط الجانبي للجوال",
    followDesktop: "اتباع سطح المكتب",
    compactRail: "شريط مضغوط",
    drawer: "درج",
    widgets: "الأدوات",
    show: "إظهار",
    hide: "إخفاء",
    presets: "تخطيطات جاهزة",
    focus: "تركيز",
    minimal: "بسيط",
    reset: "إعادة التخطيط",
    dragHelp: "اسحب البطاقات من المقبض ثم احفظ التفضيلات.",
    openControls: "فتح التحكم",
    saveError: "تعذر حفظ التفضيلات",
    loadError: "تعذر تحميل التفضيلات المحلية",
    chatPlaceholder: "سيتم ربط المحادثة بالنموذج المحلي في الخطوة التالية...",
  },
};

const tr: LocalePack = {
  direction: "ltr",
  labels: {
    product: "Personal AI",
    subtitle: "Kişisel, yerel öncelikli ve kontrol edilebilir asistan",
    conversation: "Sohbet alanı",
    localMode: "Yerel mod",
    online: "Çevrimiçi",
    onlineDisabled: "Çevrimiçi devre dışı",
    noExternal: "Etkin harici istek yok",
    vault: "Kasa",
    model: "Yerel model",
    agent: "Cihaz Aracısı",
    quick: "Quick",
    deep: "Deep",
    ready: "Hazır",
    setupRequired: "Kurulum gerekli",
    locked: "Kilitli",
    unlocked: "Açık",
    notStarted: "Henüz başlamadı",
    systemStatus: "Sistem durumu",
    modelMessage: "Yerel sohbet hazır. Bu aşamanın geçmişi yalnızca tarayıcıda kalır.",
    language: "Dil",
    theme: "Tema",
    system: "Sistem",
    dark: "Koyu",
    light: "Açık",
    appMenu: "Uygulama menüsü",
    settings: "Ayarlar",
    customize: "Arayüzü özelleştir",
    save: "Tercihleri kaydet",
    saving: "Kaydediliyor...",
    saved: "Tercihler kaydedildi",
    unsaved: "Kaydedilmemiş değişiklikler",
    close: "Kapat",
    refresh: "Durumu yenile",
    accent: "Vurgu rengi",
    customColor: "Özel renk",
    sidebar: "Kenar çubuğu",
    placement: "Konum",
    left: "Sol",
    right: "Sağ",
    mode: "Mod",
    expanded: "Genişletilmiş",
    compact: "Kompakt",
    hidden: "Gizli",
    width: "Genişlik",
    normal: "Normal",
    wide: "Geniş",
    fontScale: "Yazı boyutu",
    small: "Küçük",
    default: "Varsayılan",
    large: "Büyük",
    xlarge: "Çok büyük",
    density: "Arayüz yoğunluğu",
    comfortable: "Rahat",
    motion: "Hareket",
    full: "Tam",
    reduced: "Azaltılmış",
    controlsLocation: "Kontrol konumu",
    sidebarSettings: "Kenar çubuğu ayarları",
    header: "Başlık",
    both: "Her ikisi",
    mobileBehavior: "Mobil kenar çubuğu",
    followDesktop: "Masaüstünü takip et",
    compactRail: "Kompakt şerit",
    drawer: "Çekmece",
    widgets: "Bileşenler",
    show: "Göster",
    hide: "Gizle",
    presets: "Hazır düzenler",
    focus: "Odak",
    minimal: "Minimal",
    reset: "Düzeni sıfırla",
    dragHelp: "Kartları tutamaçtan sürükleyin ve tercihleri kaydedin.",
    openControls: "Kontrolleri aç",
    saveError: "Tercihler kaydedilemedi",
    loadError: "Yerel tercihler yüklenemedi",
    chatPlaceholder: "Sohbet çekirdeği sonraki adımda yerel modele bağlanacak...",
  },
};

export const LOCALES: Record<AppLanguage, LocalePack> = {
  fa,
  en,
  ar,
  tr,
};

export function localeFor(language: AppLanguage): LocalePack {
  return LOCALES[language] ?? LOCALES.en;
}
