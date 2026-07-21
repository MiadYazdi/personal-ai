# Personal AI — Architecture v0.1

## هدف

یک دستیار شخصی، چنددستگاهی و چندکاربره که:

- فارسی و انگلیسی را پشتیبانی می‌کند.
- در گفتگو، ترجمه، برنامه‌ریزی، کدنویسی، فایل‌ها و برنامه‌ها همکاری می‌کند.
- برای Ubuntu، Windows، Android و iOS طراحی می‌شود.
- نسخهٔ اجرایی اول آن روی Ubuntu ساخته و آزمایش می‌شود.
- ابتدا متنی است و سپس صوت و قابلیت‌های پیشرفته اضافه می‌شوند.

## قرارداد مشترک همهٔ پلتفرم‌ها

این قوانین برای Ubuntu، Windows، Android، iOS و هر client آینده یکسان هستند:

1. دادهٔ شخصی کاربر خودکار از دستگاه خارج نمی‌شود.
2. حافظه فقط با تأیید کاربر ذخیره می‌شود.
3. اینترنت فقط با انتخاب و اجازهٔ کاربر استفاده می‌شود.
4. هر عمل سیستمی از Permission Engine عبور می‌کند.
5. داده، حافظه و مجوزهای هر کاربر جدا هستند.
6. دستیار بدون درخواست روشن کاربر خودسرانه عمل نمی‌کند.
7. کارهای حساس همیشه تأیید تازه لازم دارند.
8. voice cloning فقط با رضایت روشن همان شخص فعال می‌شود.
9. محدودیت‌های فنی سیستم‌عامل دور زده نمی‌شوند؛ دستیار باید محدودیت را شفاف اعلام کند.

قانون و حریم خصوصی در همهٔ پلتفرم‌ها یکسان است، اما توانایی فنی سیستم‌عامل‌ها ممکن است متفاوت باشد.

## حالت Local و Online

### Local / Offline

- مدل محلی، حافظهٔ محلی، فایل‌های محلی و ابزارهای مجاز دستگاه استفاده می‌شوند.
- هیچ اتصال شبکه‌ای از سوی برنامه برقرار نمی‌شود.
- profile، فایل‌ها، گفتگوها، حافظه، صدا و کلیدهای شخصی در دستگاه می‌مانند.

### Online با انتخاب کاربر

کاربر می‌تواند برای کار مشخص اجازه دهد، از جمله:

- جست‌وجوی وب
- بررسی یا دانلود آپدیت برنامه
- بررسی یا دانلود مدل محلی جدید
- دریافت knowledge pack عمومی
- استفاده از provider آنلاین در آینده
- ارسال feedbackی که خود کاربر جداگانه انتخاب کرده است

قوانین Online:

1. profile، حافظه، گفتگو، فایل، صدا و secretهای کاربر خودکار ارسال نمی‌شوند.
2. دستیار اطلاعات حافظهٔ شخصی را خودکار به query آنلاین اضافه نمی‌کند.
3. اگر query شامل دادهٔ شخصی یا حساس باشد، پیش از ارسال نمایش داده و تأیید گرفته می‌شود.
4. برای دانلود، منبع، نسخه، حجم، hash و هدف دانلود نمایش داده می‌شود.
5. اتصال اینترنتی IP و metadata شبکه را برای سرور مقصد آشکار می‌کند، اما دادهٔ شخصی ذخیره‌شده ارسال نمی‌شود.
6. آپدیت مدل یا برنامه به معنی train مخفی مدل با دادهٔ کاربر نیست.

## یادگیری و حافظه

دستیار به سه روش بهتر می‌شود:

1. حافظهٔ شخصی تأییدشده توسط کاربر.
2. دانش محلی از فایل‌ها، پروژه‌ها، پوشه‌ها یا PDFهای مجاز.
3. آپدیت اختیاری برنامه، مدل یا knowledge pack.

مدل به‌صورت مخفی با گفتگوها یا فایل‌های شخصی train نمی‌شود.

## کاربران و حریم خصوصی

هر کاربر مستقل است و داده‌هایش با کاربر دیگر مخلوط نمی‌شود:

- profile
- conversations
- memory
- permissions
- local knowledge index
- optional voice data

feedback عمومی فقط زمانی ارسال می‌شود که کاربر دادهٔ موردنظر را جداگانه انتخاب، مشاهده و تأیید کند.

نسخهٔ اول برای سازنده و چند tester مورداعتماد طراحی می‌شود.

## همگام‌سازی بین دستگاه‌های یک کاربر

نسخهٔ اول sync خودکار یا cloud sync ندارد.

روش نسخهٔ اول:

Device A
  -> Export دستی
Encrypted package
  -> انتقال توسط خود کاربر
Device B
  -> Import با رمز یا کلید همان کاربر

هیچ سرور اجباری وجود ندارد و دادهٔ شخصی در اینترنت منتقل نمی‌شود.

## معماری کلان

Assistant Core:
- profile
- memory
- permission policy
- planning
- local and online providers

Device-specific components:
- Ubuntu Device Agent
- Windows Device Agent
- Android Client
- iOS Client

هر Device Agent فقط روی همان دستگاه و با مجوزهای همان کاربر عمل می‌کند.

## سیاست مجوزها

هر مجوز شامل این بخش‌ها است:

Capability + Target Scope + Device + Expiry

نمونه:

Read files + all user-accessible files + Ubuntu/Miad + always

سه گزینهٔ مجوز:

1. همیشه برای همین scope اجازه بده.
2. هر بار قبل از اجرا سؤال کن.
3. فقط همین یک‌بار اجازه بده.

مجوز دائمی فقط برای همان device، capability و scope معتبر است.
دستیار بدون درخواست روشن کاربر خودسرانه عمل نمی‌کند.

حتی با مجوز دائمی، این کارها همیشه تأیید تازه لازم دارند:

- حذف یا overwrite فایل
- ارسال، upload یا اشتراک‌گذاری داده
- نصب برنامه یا اجرای فایل دانلودشده
- تغییرات مهم سیستم
- sudo یا دسترسی administrator
- خواندن یا export کردن password، token، SSH key یا secret
- پرداخت، خرید، انتشار عمومی یا ورود به حساب‌ها

## مرز دسترسی Device Agent

پس از مجوز کاربر، Device Agent می‌تواند با همهٔ فایل‌ها و برنامه‌هایی کار کند که حساب فعلی به آن‌ها دسترسی دارد، شامل:

- فایل‌ها و پوشه‌های Home
- پوشه‌های مخفی
- پروژه‌های برنامه‌نویسی
- برنامه‌های نصب‌شده
- ترمینال
- فایل‌های متنی
- پنجره و برنامهٔ فعال، با preview مناسب برای تایپ یا automation

برای کارهای administrator:

- agent دائمی با root اجرا نمی‌شود.
- هر کار admin تأیید تازه لازم دارد.
- سیستم‌عامل پنجرهٔ واقعی sudo یا permission را نمایش می‌دهد.
- رمز administrator در پروژه، حافظه یا گفتگو ذخیره نمی‌شود.

## Automation برنامه‌ها

دو سطح automation وجود دارد:

1. General UI Automation:
   - بازکردن برنامه
   - بازکردن فایل
   - تایپ در پنجرهٔ هدف
   - workflowهای ساده با preview و تأیید

2. App-Specific Connector:
   - اتصال قابل‌اعتمادتر به برنامه‌های مهم
   - نمونه‌های آینده: VS Code، Git، مرورگر، Photoshop و تقویم

اگر قابلیت یک برنامه به cloud متکی باشد، دستیار پیش از استفاده آن را اعلام و اجازه می‌گیرد.

## Voice

- نسخهٔ اول: متن.
- مرحلهٔ بعد: speech-to-text و text-to-speech.
- دستیار کاربر را با نام انتخابی او صدا می‌زند.
- صدای دستیار قابل انتخاب است.
- voice cloning فقط اختیاری، با رضایت روشن همان شخص و نگهداری محلی دادهٔ صوتی خواهد بود.

## اولویت MVP روی Ubuntu

1. CLI و Local Web UI
2. onboarding و profile محلی
3. گفت‌وگوی فارسی و انگلیسی
4. حافظهٔ پیشنهادی با تأیید کاربر
5. Permission Engine سه‌گزینه‌ای
6. Local Model Provider و benchmark مدل Qwen3 8B
7. ابزارهای Ubuntu برای فایل‌ها، برنامه‌ها، ترمینال و کدنویسی
8. ثبت محلی و شفاف درخواست‌ها و مجوزها

## تصمیم‌های انجام‌شده و باز

### تصمیم‌های انجام‌شده

- Local Runtime:
  llama-cpp-python==0.3.34 داخل .venv

- Local Model:
  Qwen3-8B-Q4_K_M.gguf

- Official Model Repository:
  Qwen/Qwen3-8B-GGUF

- Pinned Model Revision:
  7c41481f57cb95916b40956ab2f0b139b296d974

- Verified Model SHA-256:
  d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785

- Local Backend:
  FastAPI==0.139.0 and Uvicorn==0.51.0

- Local Web UI:
  React==19.2.7, TypeScript==7.0.2, Vite==8.1.4,
  Tailwind CSS==4.3.2 and Lucide React==1.24.0

- CLI:
  Python argparse CLI shared with the same Personal AI core

- Vault Cryptography:
  cryptography==49.0.0, Argon2id and AES-256-GCM

### تصمیم‌های باز

- فرمت انسانی Recovery Key و روش نمایش/ذخیرهٔ یک‌بارهٔ آن
- فرمت و پروتکل رمزگذاری export/import بین دستگاه‌ها
- طراحی دقیق Android و iOS
- connectorهای تخصصی VS Code، Photoshop و برنامه‌های دیگر
- Vault onboarding و ایجاد اولین profile واقعی
- Local chat endpoint و اتصال Web UI به Qwen3
- Permission Engine و Ubuntu Device Agent

## Persistent Desktop Agent and Manual Login

Ubuntu and Windows desktop behavior is designed as follows:

System boot
  -> Operating-system login screen
  -> The user manually enters their own account password
  -> Persistent Personal AI agent starts inside that user session
  -> Local CLI, Local Web UI, memory, permissions and device tools are ready

Rules:

1. The assistant never stores, receives or types an operating-system password.
2. Each person manually signs in to their own operating-system account.
3. The persistent agent starts automatically only after successful login to that user session.
4. The agent runs with the permissions of the logged-in user, never as permanent root.
5. Administrator actions still require fresh approval and the real sudo or operating-system permission prompt.
6. When the device is locked or the user logs out, the assistant does not bypass the lock screen or control the unavailable desktop session.
7. After the user logs in again, the agent can start automatically in that user session.

## Configurable Model Residency

The agent is persistent, but model residency is configurable per device:

- Lazy-load: the model loads when a conversation needs it and can unload after idle time.
- Keep-warm: the model remains loaded in RAM for faster first responses.

The selected mode must be visible and changeable by the user.
The final default mode will be chosen after Qwen3 8B memory and speed benchmarks.

## Mobile Background Behavior

Android and iOS follow the same privacy, memory and permission contract.
However, each mobile operating system can limit background execution.

The mobile client must:

- Clearly report whether it is currently active, suspended or unavailable.
- Never claim to control an unavailable device.
- Request each platform permission transparently.
- Use only platform-approved background, notification and automation capabilities.

## Visible Quick and Deep Thinking Modes

The user interface must visibly expose two Qwen3 reasoning modes:

- Quick mode: for daily chat, translation, planning, simple coding and device commands.
  The local Qwen3 prompt uses the /no_think soft switch to avoid unnecessary reasoning output.

- Deep mode: for difficult analysis, complex debugging, architecture and tasks that need longer reasoning.
  The interface uses normal thinking behavior or the /think soft switch.

The user chooses the mode visibly before each request.
The assistant must not silently switch a user-selected mode.

## Hybrid Vault for Private Data

Personal AI uses a Hybrid Vault model for user privacy.

Data categories:

1. Non-private operational settings:
   - UI language
   - theme
   - device status
   - non-sensitive application preferences

   These are protected by operating-system account permissions.

2. Private Vault data:
   - user profile
   - personal memory
   - conversations
   - voice samples and voice-cloning data
   - API keys, tokens and secrets
   - encrypted device-export packages

   These data require Vault unlock and must not be stored as plaintext.

Vault lifecycle:

System boot
  -> user manually logs in to the operating-system account
  -> Personal AI Agent starts
  -> Vault begins locked
  -> user enters their own Vault passphrase
  -> private memory and profile become available

Rules:

- The assistant never stores the Vault passphrase in plaintext.
- A locked Vault prevents reading private memory, conversations, voice data and secrets.
- The agent can remain active while the Vault is locked, but it cannot claim private context is available.
- Operating-system file access never means Personal AI may copy user files into Vault without explicit permission.
- Before real private data is stored, the encryption and key-management implementation must be reviewed separately.
- Recovery-key design is required before the product is distributed beyond trusted testers.

## Vault KDF Profile v1

The initial Personal AI Vault uses Argon2id for deriving a 32-byte wrapping key from the user Vault passphrase.

Selected parameters:

- algorithm: Argon2id
- salt length: 16 bytes minimum
- output length: 32 bytes
- memory_cost: 131072 KiB (128 MiB)
- iterations: 3
- lanes: 4

Ubuntu benchmark result:

- 128 MiB, 3 iterations and 4 lanes completed in approximately 0.156 seconds on the initial development device.

Rules:

- The KDF salt and parameters are stored in the Vault header.
- The Vault passphrase is never stored.
- A random Vault data key is wrapped by the passphrase-derived key.
- Vault records use authenticated encryption with AES-256-GCM.
- Future rekey or KDF-hardening changes must preserve the ability to unlock existing Vaults.
- Android and iOS performance must be benchmarked before changing this portable baseline.

## Vault Passphrase and Recovery Policy v1

Vault passphrase policy:

- The Vault passphrase must be separate from the operating-system account password.
- The user has final passphrase choice.
- The application provides clear strength guidance and warnings, but does not block a user-selected passphrase solely by length.
- The application must never claim a weak passphrase is secure.
- The Vault passphrase is never stored in plaintext.

Recovery Key policy:

- Recovery Key creation is optional.
- The user is clearly warned that forgotten passphrase plus no Recovery Key means permanent data loss.
- A Recovery Key is shown only at creation time.
- The assistant does not store, upload, sync or display the Recovery Key again.
- The user is responsible for storing the Recovery Key in a password manager or another safe location.
- Recovery design must use a separate cryptographic path to unlock the Vault data key without the normal passphrase.

## SQLite Encrypted Vault Storage v1

Development Vault location:

data/local/personal-ai-vault.sqlite3

Production Vault location:

- Ubuntu: ~/.local/share/personal-ai/
- Windows: AppData/Local/PersonalAI/
- Android: app-private storage
- iOS: app-private storage

Vault database design:

vault_header stores only non-private metadata:

- vault_id
- schema_version
- created_at
- KDF algorithm, salt and parameters
- passphrase-wrapped Vault data key
- passphrase wrapping nonce
- optional recovery-wrapped Vault data key
- optional recovery wrapping nonce

vault_records stores encrypted private records:

- random record_id
- schema_version
- nonce
- ciphertext

Private payload fields, record type and sensitive timestamps are encrypted within ciphertext.

Security rules:

- SQLite never stores private profile, memory, conversation, secret or voice data as plaintext.
- Every Vault record uses a separate AES-256-GCM nonce.
- AES-GCM associated data binds record_id and schema version.
- Vault database directory uses restricted operating-system permissions.
- SQLite WAL and journal files contain ciphertext only.
- Vault database files are never committed to Git.
- A copied Vault file cannot be decrypted without a valid passphrase or optional Recovery Key.


## Verified Implementation Milestone v0.1

Verified local runtime:

- Python 3.12 virtual environment is active.
- llama-cpp-python==0.3.34 imports successfully.
- Qwen3-8B-Q4_K_M.gguf is downloaded and SHA-256 verified.
- Qwen3 local CPU inference completed in Quick and Deep test modes.

Verified Hybrid Vault foundation:

- cryptography==49.0.0 is installed.
- Argon2id and AES-256-GCM synthetic self-test passed.
- Vault Core uses SQLite encrypted records.
- Five synthetic Vault unit tests passed:
  create/reopen, passphrase rejection, Recovery Key unlock,
  tamper rejection and POSIX permissions.

Verified application foundation:

- FastAPI==0.139.0 and Uvicorn==0.51.0 import successfully.
- CLI command: python -m personal_ai status
- Local API endpoints created:
  /api/v1/health
  /api/v1/status
  /api/v1/ui-config
- React Vertical Slice source exists.
- React production build completed successfully.
- Planned local ports are available:
  backend 127.0.0.1:8765
  frontend 127.0.0.1:5173

Not yet implemented:

- Real Vault onboarding and private user profile
- Local chat endpoint connected to Qwen3
- Permanent user-session agent
- Permission Engine
- Ubuntu file/program automation
- Windows, Android and iOS clients

## Local API Runtime Verification v0.1

The FastAPI backend was started successfully as a temporary local process.

Verified local binding:

- http://127.0.0.1:8765
- bind scope: localhost only

Verified endpoints:

- GET /api/v1/health
- GET /api/v1/status
- GET /api/v1/ui-config

Verified status behavior:

- Local mode is enabled.
- Online mode is disabled.
- Qwen3 model manifest is available and verified.
- The local model is not loaded by status requests.
- No real Vault database exists yet.
- No Device Agent has started yet.

## Local Web UI Browser Verification v0.1

The React Web UI was started and verified in a local browser session.

Verified local URL:

- http://127.0.0.1:5173

Verified browser behavior:

- FastAPI status data rendered in the React UI.
- Qwen3 model availability rendered correctly.
- Vault setup-required status rendered correctly.
- Online-disabled status rendered correctly.
- Persian UI rendered in RTL.
- English UI rendered in LTR.
- Raw API status values such as not_started were translated for Persian UI.
- Quick and Deep mode selector changed state visually.
- No external network service was required for browser verification.

## Advanced Custom UI Before Vault Onboarding

Advanced Custom UI is approved before real Vault onboarding.

Initial approved scope:

- Dashboard card drag-and-drop ordering
- Show and hide dashboard widgets
- Custom accent color
- System, Dark and Light theme selection
- Sidebar compact and expanded modes
- Multiple dashboard presets
- Reset layout action
- Local per-device UI preference persistence

Privacy rules:

- UI preferences are non-private operational settings.
- UI preferences remain on the local device.
- UI preferences do not require Vault unlock.
- UI preferences never include profile, memory, conversations, secrets or voice data.
- UI preference storage must use restricted local file permissions.

## Advanced Custom UI Dependencies v1

Installed frontend drag-and-drop dependencies:

- @dnd-kit/core==6.3.1
- @dnd-kit/sortable==10.0.0
- @dnd-kit/utilities==3.2.2

Verification:

- Dependency tree resolved without conflict.
- React production build completed successfully after installation.
- The dependencies are local frontend packages only.
- No backend, Vault, model or Device Agent behavior changed in this phase.

## Local UI Preference Store v1

Implemented backend components:

- src/personal_ai/ui_preferences.py
- tests/test_ui_preferences.py

Implemented local storage behavior:

- Default preferences are returned when no local file exists.
- Preference schema validates theme, accent color, sidebar mode,
  preset, widget order and hidden widgets.
- Local save uses atomic temporary-file replacement.
- On POSIX systems, preference directory uses mode 700 and preference file uses mode 600.
- UI preference storage remains separate from Vault private data.

Implemented local API endpoints:

- GET /api/v1/ui-preferences
- PUT /api/v1/ui-preferences

Verification:

- Five synthetic UI preference tests passed.
- All Vault tests remained successful.
- Total Python synthetic test count: 10.
- No real UI preference file was created during tests.

## UI Preference API Default Runtime Verification v1

Verified local endpoint:

- GET /api/v1/ui-preferences

Verified behavior:

- Returns default UI preferences when no local preference file exists.
- Default theme: system.
- Default accent color: cyan.
- Default sidebar mode: expanded.
- Default widget order: vault, model, agent, online.
- No preference file was created by GET.
- Endpoint verification was performed through localhost only.

## UI Preference Persistence Runtime Verification v1

Verified local endpoint:

- PUT /api/v1/ui-preferences
- GET /api/v1/ui-preferences after persistence

Verified behavior:

- Default non-private UI preferences were saved successfully.
- GET returned the same persisted values after PUT.
- Local preference file was created at:
  data/local/ui-preferences.json
- Local preference directory permission verified: 700.
- Local preference file permission verified: 600.
- Stored data contains only non-private UI configuration.
- No Vault, profile, memory, conversation, secret or voice data was created.

## React Customizer Foundation v1

Implemented React Custom UI behavior:

- Loads local preferences through GET /api/v1/ui-preferences.
- Saves local preferences through PUT /api/v1/ui-preferences.
- Provides a visible Customizer panel.
- Supports System, Dark and Light theme state.
- Supports named accent palette and custom hexadecimal accent color.
- Supports sidebar compact and expanded modes.
- Supports widget visibility state.
- Supports Default, Focus and Minimal UI presets.
- Supports reset to default layout.
- Displays save, saving, saved and error states.
- Keeps Quick and Deep labels in English for all UI languages.

Verification:

- React production build passed after Customizer implementation.
- Drag-and-drop ordering remains intentionally unimplemented until the next phase.

## React Customizer Browser Runtime Verification v1

Verified in a local browser session:

- Customizer panel opens and closes correctly.
- Theme controls work.
- Accent color controls work.
- Sidebar compact and expanded controls work.
- Widget visibility controls work.
- Layout preset controls work.
- Reset layout control works.
- Save preference action succeeds.
- Saved UI preferences remain after browser refresh.
- Only non-private per-device UI configuration is persisted.

No Vault profile, personal memory, conversation, secret or voice data was created during this verification.

## Dashboard Drag and Drop Foundation v1

Implemented frontend drag-and-drop behavior:

- dnd-kit DndContext
- PointerSensor with activation distance
- KeyboardSensor with sortable keyboard coordinates
- SortableContext using rect sorting strategy
- Visible Dashboard widget reordering
- Hidden widgets preserved in the overall widget order
- Drag handles with visual dragging state
- Manual preference save required before new order persists

Verification:

- React production build passed after drag-and-drop implementation.
- Browser interaction verification remains the next required step.

## Direct Sidebar Toggle UX v1

Sidebar behavior:

- Sidebar compact and expanded control is not located inside the Customizer panel.
- A direct icon-based toggle is located at the top of the sidebar.
- The toggle remains visible in both expanded and compact sidebar modes.
- Clicking the toggle changes sidebar mode immediately.
- Sidebar mode auto-saves locally through the existing UI preference API.
- Sidebar auto-save must persist only sidebar_mode and must not silently save unrelated unsaved Customizer changes.
- If local save fails, sidebar mode returns to its previous persisted state and an error is shown.

## Advanced Custom UI v2 Layout and Internationalization

Approved UI preference schema expansion:

- language: fa | en | ar | tr
- theme: system | dark | light
- accent_color: named palette or #RRGGBB
- sidebar_placement: left | right
- sidebar_mode: expanded | compact | hidden
- sidebar_width: normal | wide
- font_scale: small | default | large | xlarge
- ui_density: compact | comfortable
- motion: system | full | reduced
- controls_location: app_menu | sidebar_settings | header
- widget_order
- hidden_widgets
- selected_preset

Approved defaults:

- language: fa
- theme: system
- sidebar_placement: left
- sidebar_mode: expanded
- sidebar_width: normal
- font_scale: default
- ui_density: comfortable
- motion: system
- controls_location: app_menu

Control placement rules:

- Default global controls are in the App Menu at the bottom of the Sidebar.
- App Menu works before a real Personal AI profile exists.
- Users can later move controls to Sidebar Settings or Header.

Localization rules:

- UI uses local translation packs.
- Initial supported UI locales: Persian, English, Arabic and Turkish.
- Persian and Arabic are RTL.
- English and Turkish are LTR.
- Unsupported locale packs use English fallback.
- Model response language support is separate from UI locale support.

Future preference sync rules:

- Layout, widget order, sidebar placement, width, font scale and density remain per device.
- Language and theme may become profile-syncable in a future encrypted sync phase.

## UI Preference Schema v2 Migration

Implemented local UI preference schema version 2.

New persisted fields:

- language
- sidebar_placement
- sidebar_width
- font_scale
- ui_density
- motion
- controls_location

Migration behavior:

- Schema version 1 files are accepted.
- Version 1 files migrate to version 2 in memory.
- Existing v1 values such as theme, accent color, sidebar mode,
  preset, widget order and hidden widgets are preserved.
- New v2 fields receive approved defaults.
- Source file remains v1 until a successful explicit save.
- The next save writes schema_version 2 atomically.

Verification:

- v1 migration test passed.
- v2 validation tests passed.
- All Vault tests remained successful.
- Total synthetic Python test count: 11.

## UI Preference v1 to v2 Runtime Migration Verification

Verified through the running local API:

- GET /api/v1/ui-preferences returned schema_version 2.
- Existing schema v1 file remained schema_version 1 on disk.
- New v2 defaults were added in memory.
- Existing v1 values including theme, accent, sidebar mode,
  selected preset and widget order were preserved.
- No file rewrite occurred before an explicit save.

## React Advanced Custom UI v2 Implementation

Implemented React behavior:

- schema v2 preference consumption
- automatic language persistence
- local UI locale packs: fa, en, ar and tr
- RTL support for fa and ar
- LTR support for en and tr
- minimal default Header
- App Menu at bottom of Sidebar
- user-selectable controls location
- sidebar placement, mode and width controls
- font scale, density and motion controls
- schema v2-compatible drag-and-drop dashboard behavior

Verification:

- React production build passed.
- Previous TypeScript Sidebar Toggle type error is resolved.
- Browser verification is the next required step.

## Sidebar Flush and Mobile Drawer v1

Desktop and laptop behavior:

- Sidebar is flush to the selected browser or application edge.
- No outer gutter is allowed between Sidebar and viewport edge.
- Sidebar can use left or right placement.
- Sidebar supports expanded, compact, hidden, normal and wide modes.

Responsive mobile behavior:

- Sidebar must not disappear permanently on small screens.
- Sidebar becomes an edge-attached drawer.
- Drawer placement follows local left/right preference.
- Drawer is closed by default on mobile.
- A mobile menu button remains available to open the drawer.
- Drawer overlays main content and closes through backdrop interaction.
- App Menu and settings remain reachable on mobile.

Cross-platform rule:

- Sidebar behavior semantics remain consistent across Ubuntu, Windows,
  Android and iOS clients.
- Native mobile clients will use platform-appropriate navigation drawer
  and gesture implementations.
- Layout preferences remain per device.

## Sidebar Flush and Mobile Drawer Implementation v1

Implemented responsive Web UI behavior:

- app layout now uses full viewport width without centered maximum width.
- Desktop Sidebar is flush to selected left or right edge.
- Mobile Sidebar renders as fixed overlay drawer.
- Mobile menu button opens the drawer.
- Mobile drawer backdrop closes the drawer.
- Drawer close button is available inside the mobile drawer.
- App Menu remains available through the responsive drawer.
- Sidebar hidden state can be reopened through mobile controls.

Verification:

- React production build passed.
- Desktop and responsive browser verification remain required.

## Sidebar Physical Layout and Mobile Schema v3

Physical Sidebar placement rule:

- Sidebar placement is independent from UI text direction.
- sidebar_placement=left always places Sidebar physically on the left.
- sidebar_placement=right always places Sidebar physically on the right.
- Persian or Arabic RTL direction must not move a left Sidebar to the right.
- Text inside each UI region keeps its own locale direction.

Schema version 3 adds:

- mobile_sidebar_behavior:
  follow_desktop | compact_rail | drawer

- controls_location:
  app_menu | sidebar_settings | header | both

Mobile behavior mapping when mobile_sidebar_behavior=follow_desktop:

- Desktop expanded -> mobile drawer with mobile menu button.
- Desktop compact -> mobile compact icon rail.
- Desktop hidden -> mobile menu button with on-demand drawer.

Mobile users can override follow_desktop with compact_rail or drawer.

Migration rules:

- Schema v1 and v2 preference files are accepted.
- Schema v1 and v2 are migrated in memory to schema v3.
- Existing saved fields are preserved.
- New schema v3 fields receive approved defaults.
- Existing preference file is not rewritten until explicit save.

## UI Preference Schema v3 Migration

Implemented local UI preference schema version 3.

New persisted fields:

- mobile_sidebar_behavior
- controls_location now supports both

Migration support:

- Schema v1 to v3
- Schema v2 to v3
- Schema v3 current format

Migration behavior:

- Existing values are preserved.
- Missing mobile_sidebar_behavior defaults to follow_desktop.
- Missing controls_location defaults to both.
- Files are migrated in memory.
- Existing file is rewritten only after explicit save.

Verification:

- v1 to v3 migration test passed.
- v2 to v3 migration test passed.
- v3 validation test passed.
- Total synthetic Python test count: 12.
- Vault tests remained successful.

## UI Preference v3 Runtime Verification

Verified through the running local API:

- GET /api/v1/ui-preferences returned schema_version 3.
- mobile_sidebar_behavior returned follow_desktop.
- controls_location returned a valid v3 value.
- Existing user-selected language, layout and typography preferences were preserved.
- Local preference file is now schema_version 3 after an explicit UI save.
- v3 preference persistence remains local and non-private.

## React Schema v3 and Physical Sidebar Repair

Implemented frontend schema v3 support:

- mobile_sidebar_behavior type and default
- controls_location supports both
- React default preference schema_version is 3
- locale packs include mobile sidebar and controls labels

Implemented layout correction:

- Physical Sidebar placement no longer depends on RTL or LTR text direction.
- Sidebar left and right positioning is controlled by sidebar_placement.
- Mobile behavior derives compact rail or drawer from schema v3 preference.
- Header shortcut controls are prepared for controls_location=both.

Verification:

- React production build passed after repair.

## Physical Sidebar and Mobile Drawer Browser Verification v1

Verified in local browser sessions:

Desktop:

- Left Sidebar remained physically left in Persian RTL UI.
- Left Sidebar remained physically left in English LTR UI.
- Sidebar was visually flush with the viewport edge.
- Compact Sidebar icon rail rendered correctly.
- App Menu remained accessible.

Mobile responsive view:

- Compact rail rendered on the selected edge.
- Mobile Drawer opened correctly.
- Drawer close control rendered correctly.
- Drawer overlay behavior worked.
- App Menu remained accessible inside mobile Drawer.

Pending verification:

- Drag-and-drop layout save and refresh persistence.

## Responsive UI Alignment Repair Pending v1

Browser review identified remaining visual issues:

Desktop:

- RTL title and card content alignment must use the logical content edge.
- Header shortcut controls must remain physically left.
- Status card text must not remain visually centered in oversized card space.

Mobile:

- Compact rail and expanded drawer must behave as one coherent edge-attached navigation system.
- Drawer must expand from the same selected edge as the compact rail.
- Mobile layout must avoid overlapping rails, drawers, controls and content.
- Cards, typography and spacing require responsive mobile alignment review.

The previous physical Sidebar and mobile browser verification is partial.
Final visual acceptance remains pending until this repair is built and verified.

## Responsive UI Alignment Repair Implementation v1

Implemented CSS repair:

- Header uses physical-left control placement and logical title direction.
- Status card text aligns to locale direction.
- Desktop cards use full available content width.
- Compact mobile rail uses fixed narrow edge width.
- Compact rail expands into same-edge mobile drawer.
- Responsive content padding changes when compact rail is visible.
- Mobile card grid becomes a single column.
- Drawer and mobile content spacing were repaired.

Verification:

- React production build passed.
- Browser visual verification remains required.

## Mobile Fixed Sidebar and Locale Dropdown v4

This section supersedes previous mobile drawer behavior.

Mobile Sidebar rules:

- Mobile Sidebar always exists as a compact edge rail by default.
- mobile_sidebar_mode supports:
  compact | expanded
- Compact rail is fixed to the selected physical edge.
- Expanded Sidebar overlays Main Content from the same edge.
- The same Sidebar toggle changes compact and expanded modes.
- Mobile does not use a separate close button, backdrop close action, menu-only state or hidden Sidebar state.
- Desktop Sidebar hidden mode remains a separate desktop-only behavior.

Schema migration:

- Schema v4 replaces mobile_sidebar_behavior with mobile_sidebar_mode.
- v3 follow_desktop maps to compact by default.
- v3 compact_rail maps to compact.
- v3 drawer maps to expanded.
- New default: mobile_sidebar_mode=compact.

Localization control rules:

- Language selector uses a custom application dropdown.
- Dropdown appears directly below its own language field.
- Native browser select popup is not used for language selection.
- When Customizer is open, it overlays Sidebar and prevents confusing simultaneous panels.

## UI Preference Schema v4 Migration

Implemented local UI preference schema version 4.

Schema v4 change:

- mobile_sidebar_behavior is replaced by mobile_sidebar_mode.
- mobile_sidebar_mode supports compact | expanded.
- controls_location supports both.

Migration rules:

- v1 defaults to mobile_sidebar_mode=compact.
- v2 defaults to mobile_sidebar_mode=compact.
- v3 follow_desktop maps to compact.
- v3 compact_rail maps to compact.
- v3 drawer maps to expanded.
- Existing preference fields are preserved.
- Disk rewrite occurs only after explicit save.

Verification:

- v1, v2 and v3 migration tests passed.
- v4 validation tests passed.
- Total synthetic Python test count: 13.
- Vault tests remained successful.

## UI Preference v4 Runtime Verification

Verified through the local API:

- GET /api/v1/ui-preferences returned schema_version 4.
- Existing schema v3 mobile_sidebar_behavior migrated in memory.
- API returned mobile_sidebar_mode=compact.
- Existing v3 preference file remained unchanged on disk before explicit save.
- Existing user preference values remained preserved.

## Mobile Fixed Sidebar and Custom Locale Dropdown Implementation v4

Implemented React behavior:

- mobile_sidebar_mode is used by the frontend.
- Mobile Sidebar remains present as compact rail.
- Sidebar toggle changes compact and expanded mobile modes.
- Expanded Sidebar overlays Main Content from the same physical edge.
- Separate mobile close button, backdrop close action and menu-only behavior are removed from the intended mobile flow.
- Custom locale dropdown replaces native browser language select.
- Locale dropdown renders directly below its own language field.
- Language selection auto-saves locally.
- Locale options include fa, en, ar and tr.

Verification:

- React production build passed.
- Browser verification remains required.

## Advanced Custom UI v4 Browser Verification Complete

Verified in local browser sessions:

- Desktop Sidebar physical placement remained correct across RTL and LTR locales.
- Desktop Sidebar flush layout worked.
- Mobile Fixed Sidebar compact rail worked.
- Mobile Sidebar expanded overlay worked.
- Mobile Sidebar toggle compact and expanded behavior worked.
- No separate mobile close button, backdrop close action or menu-only state was required.
- App Menu and settings remained accessible.
- Custom locale dropdown rendered below its language field.
- Locale selection persisted after refresh.
- Widget visibility, theme, accent, typography, density and motion preferences persisted.
- Drag-and-drop widget order was saved and persisted after refresh.

Advanced Custom UI v4 is complete.

## Vault Onboarding Decisions v1

Initial required profile data:

- Profile Name only.

Profile naming behavior:

- Address Name defaults to Profile Name.
- Address Name is stored separately and can be edited later.
- The assistant addresses the user using Address Name.
- Age, interests, goals and other personal data remain optional and require explicit user input later.

Recovery Key display:

- Recovery Key remains optional.
- When selected, the user receives both:
  - a readable 24-word recovery phrase
  - a Base64url technical recovery code
- Both forms represent the same local recovery secret.
- Recovery material is shown only once and never uploaded, synced or stored by the assistant.

## English BIP39 Recovery Phrase v1

Recovery Phrase policy:

- Recovery Phrase uses English BIP39 wordlist only.
- Recovery Phrase contains 24 words.
- UI language does not affect Recovery Phrase word language.
- A Base64url recovery code represents the same recovery secret.
- Both representations are shown only once during Recovery Key creation.
- English-only wordlist reduces validation, interoperability and recovery errors.
- Multi-language BIP39 wordlists may be considered only in a future reviewed phase.

## Local Vault First and OAuth Provider Architecture v1

Authentication modes:

1. Local Account:
   - Fully offline.
   - Uses local Vault and Vault passphrase.
   - Does not require any external provider.

2. Online Account:
   - User may choose OAuth login with a supported provider.
   - OAuth identity does not replace Vault passphrase.
   - Private Vault remains separately encrypted.

Target identity providers:

- Google
- Apple
- Microsoft
- GitHub
- X / Twitter

Provider implementation rules:

- Use standard OAuth authorization flows with PKCE for desktop and mobile public clients.
- Never collect or store provider passwords.
- Provider tokens are secrets and must be encrypted in Vault or platform key storage.
- Each provider is implemented as an isolated adapter.
- OAuth provider login is distinct from service connector authorization.

Service connector rules:

- Google identity login is separate from Calendar, Drive and Gmail scopes.
- Microsoft identity login is separate from Outlook, OneDrive and Calendar scopes.
- GitHub identity login is separate from repository access.
- Every connector requests explicit scopes, shows what data is requested and remains revocable.
- X / Twitter connector availability and provider conditions must be reviewed before implementation.

Implementation order:

1. Complete local Vault onboarding.
2. Build provider interface without active providers.
3. Implement Google OAuth adapter with PKCE.
4. Add Apple, Microsoft, GitHub and X adapters in separate phases.

## BIP39 Recovery Library Verification v1

Installed dependency:

- mnemonic==0.21

Verified synthetic behavior:

- 32-byte random entropy generated locally.
- Entropy encoded as English 24-word BIP39 phrase.
- BIP39 checksum validated.
- Phrase decoded back to identical entropy.
- Same entropy encoded as Base64url code.

No real user Recovery Key, Vault profile or passphrase was created during verification.

## BIP39 Recovery Core Implementation v1

Implemented files:

- src/personal_ai/vault/recovery.py
- src/personal_ai/vault/store.py
- tests/test_vault_recovery.py

Implemented behavior:

- Generate 32-byte recovery secret.
- Generate English BIP39 24-word phrase.
- Generate Base64url code for same secret.
- Decode BIP39 phrase to recovery secret.
- Decode Base64url code to recovery secret.
- Validate BIP39 checksum.
- Reject invalid recovery phrase and invalid Base64url code.
- Unlock Vault with BIP39 phrase.
- Unlock Vault with Base64url code.

Verification:

- BIP39 entropy conversion repaired to bytes.
- All synthetic unit tests passed.
- Total Python synthetic test count: 16.
- No real user profile, passphrase or Recovery Key was created.

## Vault Onboarding API Design v1

Status endpoint:

- GET /api/v1/onboarding/status
- Returns non-sensitive Vault onboarding state only.

Local Vault creation endpoint:

- POST /api/v1/onboarding/local-vault

Request fields:

- profile_name: required, trimmed, non-empty
- address_name: optional, defaults to profile_name
- vault_passphrase: required, trimmed, non-empty
- create_recovery_key: optional boolean

On successful Vault creation:

- Create encrypted local Vault.
- Create first encrypted profile record.
- profile record contains profile_id, profile_name, address_name,
  created_at and updated_at.
- Recovery material is generated only when requested.

Recovery response rules:

- English BIP39 phrase and Base64url code are returned once only.
- Recovery representations are never logged or returned by status endpoints.
- Plaintext recovery material is not stored inside Vault.
- Raw recovery secret only participates in encrypted Vault key wrapping.

Validation:

- Passphrase strength remains user-selected.
- Empty passphrase is rejected.
- Empty profile_name is rejected after trimming.

## Active Development Root v1

Active development project root:

- /data/personal_ai

Migration verification:

- Source and destination passed rsync checksum verification.
- Qwen3 model SHA-256 matched the verified manifest.
- Destination Python environment and frontend lock verified successfully.
- Old verified copy remains at:
  ~/Desktop/personal_ai
- Old copy is retained until explicit user approval for archival or deletion.

## Personal AI Folder Icon v1

Custom local project icon:

- Asset path:
  /data/personal_ai/assets/icons/personal-ai-folder.svg
- Concept:
  Folder with AI neural spark.
- Applied to:
  /data/personal_ai folder metadata in Nautilus.
- Applied to:
  Personal AI Folder desktop launcher.
- Icon asset is local and uses no external resource.

## Portable Project Icon Theme v1

Implemented icon theme assets:

- Category SVG icons are stored under:
  assets/icons/project-theme
- Root folder icon:
  assets/icons/personal-ai-folder.svg

Implemented portable icon behavior:

- scripts/apply_project_icons.py applies Nautilus metadata icons.
- Script assigns icons to meaningful project folders and file types.
- Script excludes generated, dependency and IDE metadata folders.
- .directory fallback files are generated for managed folders.
- Project icons can be re-applied after path move or system migration.

Applied scope:

- Root project folder
- Meaningful project subfolders
- Python, TypeScript, Markdown, JSON, SVG, GGUF and desktop launcher files

## FastAPI TestClient Dependency Verification v1

Installed testing dependency:

- httpx==0.28.1
- httpcore==1.0.9
- certifi==2026.6.17

Verification:

- Synthetic FastAPI TestClient request passed.
- Package consistency check passed.

Compatibility note:

- Current Starlette emitted a deprecation warning indicating that
  httpx-based TestClient support is deprecated in favor of httpx2.
- No onboarding API tests are implemented yet.
- httpx2 compatibility metadata must be reviewed before choosing the
  final synthetic API testing dependency.

## httpx2 FastAPI TestClient Verification v1

Installed dependency:

- httpx2==2.7.0
- httpcore2==2.7.0
- truststore==0.10.4

Verification:

- FastAPI TestClient synthetic request passed.
- No deprecation warning was captured.
- httpx2 is selected as the preferred synthetic API testing stack.

Cleanup pending:

- Legacy httpx, httpcore and certifi remain installed temporarily.
- Cleanup requires explicit approval before removal.

## Final FastAPI Synthetic Test Stack v1

Final testing dependencies:

- httpx2==2.7.0
- httpcore2==2.7.0
- truststore==0.10.4

Verification:

- FastAPI TestClient synthetic request passed after cleanup.
- No deprecation warning was captured.
- Legacy httpx, httpcore and certifi were removed.
- Package consistency check passed.

## Vault Onboarding Service Implementation v1

Implemented files:

- src/personal_ai/onboarding.py
- src/personal_ai/api/app.py
- tests/test_onboarding_service.py
- tests/test_onboarding_api.py

Implemented endpoints:

- GET /api/v1/onboarding/status
- POST /api/v1/onboarding/local-vault

Implemented behavior:

- Local Vault onboarding validation.
- Required non-empty Profile Name.
- Optional Address Name defaulting to Profile Name.
- Required non-empty Vault passphrase.
- Optional English BIP39 and Base64url Recovery Key response.
- First encrypted profile record creation.
- Profile ID is used as Vault record ID.
- Duplicate Vault creation rejection.
- Temporary Vault cleanup on creation failure.
- Status endpoint excludes recovery phrase and recovery code.

Verification:

- Service and API synthetic tests passed.
- Total Python synthetic test count: 25.
- No real user profile or real Vault was created.

## Vault Onboarding Status Runtime Verification v1

Verified through running local API:

- GET /api/v1/onboarding/status returned HTTP success.
- vault_configured=false
- vault_state=not_created
- profile_available=false

No local Vault, profile record, Recovery Key or sensitive onboarding data was created during verification.

## React Vault Onboarding Preview UI v1

Implemented frontend files:

- apps/web/src/Onboarding.tsx
- apps/web/src/App.tsx
- apps/web/src/api.ts
- apps/web/src/types.ts
- apps/web/src/styles.css

Implemented UI behavior:

- Fetch onboarding status from local API.
- Render Local Account onboarding preview when Vault is not created.
- Render Profile Name and Address Name inputs.
- Render Vault passphrase and confirmation inputs.
- Render optional Recovery Key selection.
- Render client-side validation preview.
- Vault creation submission remains confirmation-gated and does not POST yet.

Verification:

- React production build passed.
- Browser verification requires backend restart because running API process predates onboarding endpoints.

## Onboarding Bidi and Form Layout Repair Pending v1

Browser review identified onboarding UI issues:

- Persian and English mixed text requires stronger bidirectional isolation.
- User-entered text fields require automatic direction detection.
- Password fields require explicit LTR direction.
- Technical tokens inside RTL help text require bidi-safe presentation.
- Form labels, fields and help text require consistent logical alignment.
- Desktop form columns require equal input geometry.
- Mobile onboarding layout requires single-column responsive behavior.

Onboarding visual acceptance remains pending until this repair is implemented and browser-verified.

## Onboarding Bidi and Form Layout Repair Implementation v1

Implemented onboarding UI behavior:

- Profile Name and Address Name use automatic text direction.
- Vault passphrase fields use explicit LTR direction.
- Technical tokens use BDI-safe presentation.
- Mixed-language help text uses unicode-bidi-safe behavior.
- Labels and descriptions use logical-start alignment.
- Desktop form fields use equal visual geometry.
- Mobile form remains responsive in a single-column layout.

Verification:

- React production build passed.
- Browser visual verification remains required.

## Onboarding Geometry and Autofill Repair Implementation v1

Implemented UI repairs:

- Profile Name field includes invisible helper spacer.
- Address Name helper text and Profile Name spacer create equal grid geometry.
- Desktop onboarding panel uses controlled centered width.
- Input labels and fields align on equal baselines.
- Chrome password autofill background is overridden to match active UI theme.
- Mobile onboarding panel remains full-width responsive.

Verification:

- React production build passed.
- Browser visual verification remains required.

## Sidebar Footer Controls Default v1

Default global control placement:

- Refresh and Settings controls are located in the Sidebar footer.
- The default controls_location is app_menu.
- Header remains uncluttered by default.
- English Header title aligns close to the physical left Sidebar edge.
- RTL Header title aligns to its logical right edge.

Customization:

- controls_location=header moves controls to Header.
- controls_location=both shows controls in Sidebar footer and Header.
- controls_location=sidebar_settings keeps settings in Sidebar navigation.

This decision supersedes the previous default controls_location=both.

## Sidebar Footer Controls Implementation v1

Implemented behavior:

- Sidebar Footer contains Settings and Refresh actions.
- Default controls_location changed to app_menu.
- Existing v1 preference migration default updated to app_menu.
- Current local preference saved with controls_location=app_menu.
- Header remains minimal when app_menu is selected.
- Header controls remain available through explicit header or both customization.

Verification:

- Full Python synthetic suite passed.
- React production build passed.

## Sidebar Settings Navigation and Schema v5

Default Sidebar navigation order:

- Conversation
- Widgets
- Device Agent
- Settings

Settings appears directly below Device Agent.

Sidebar footer:

- Local Mode status
- Refresh action

Control location schema v5:

- sidebar_settings
- header
- both

Removed UI value:

- app_menu

Default:

- controls_location=sidebar_settings

Behavior:

- sidebar_settings places Settings below Device Agent and Refresh in footer.
- header places Settings and Refresh in Header.
- both provides Sidebar Settings/Footer Refresh plus Header shortcuts.

Migration:

- Previous app_menu value migrates to sidebar_settings.
- Missing controls_location defaults to sidebar_settings.
- Existing user preference file remains unchanged until explicit save.

## UI Preference Schema v5 Implementation v1

Implemented schema v5:

- controls_location values:
  sidebar_settings | header | both
- app_menu is migrated to sidebar_settings.
- New default controls_location is sidebar_settings.
- Sidebar navigation places Settings below Device Agent.
- Sidebar footer places Refresh below Local Mode.
- Header remains minimal in sidebar_settings mode.

Verification:

- Full Python synthetic suite passed.
- Total Python synthetic test count: 26.
- React production build passed.

## UI Preference Schema v5 Runtime Verification

Verified through local API:

- GET /api/v1/ui-preferences returned schema_version 5.
- Existing app_menu preference migrated to sidebar_settings.
- Current local preference now uses controls_location=sidebar_settings.
- No Vault profile or sensitive data was created during verification.

## Vault Onboarding Preview Browser Verification Complete v1

Verified in local browser:

- Sidebar Settings icon appears below Device Agent.
- Refresh action appears in Sidebar footer.
- Header remains minimal in sidebar_settings mode.
- English title aligns near the physical left Sidebar.
- Persian title follows logical RTL placement.
- Onboarding form is centered and visually symmetric.
- Profile and Address Name field geometry is aligned.
- Password fields match active UI theme.
- Onboarding preview validation operates without creating a real Vault.

No real profile, Vault or recovery material was created during browser verification.

## Final Vault Creation Confirmation UX v1

Real Vault creation flow:

- Client-side validation completes first.
- Final confirmation modal shows Profile Name, Address Name and Recovery Key choice.
- Vault passphrase is never displayed in modal.
- Explicit acknowledgment is required before POST submission.
- POST /api/v1/onboarding/local-vault executes only after final confirmation.

Recovery display:

- English BIP39 phrase and Base64url code are returned once.
- User can copy either representation.
- User can download a local plaintext .txt recovery file.
- Recovery download file contains sensitive plaintext recovery material.
- UI must warn users to store downloaded file in a secure location.
- Recovery material is cleared from browser state after acknowledgment.

## Final Vault Confirmation Implementation v1

Implemented frontend capability:

- Final confirmation modal after client validation.
- Explicit acknowledgment checkbox.
- POST /api/v1/onboarding/local-vault only after acknowledgment.
- Vault passphrase is not rendered in confirmation modal.
- One-time recovery result screen.
- BIP39 phrase and Base64url copy actions.
- Local plaintext recovery text file download.
- Recovery result cleared after acknowledgment.
- Successful creation triggers onboarding status refresh.

Verification:

- React production build passed.
- Browser preview verification remains required before real user creation.

## Compromised Recovery Key Security Remediation v1

Security event:

- A generated Recovery Phrase and Base64url code were exposed in a shared screenshot.
- Recovery material was treated as compromised.

Remediation:

- The associated local Vault database was deleted.
- Vault sidecar files were verified absent.
- Downloaded recovery text file was verified absent from Downloads.
- UI preference file was retained because it contains only non-private UI configuration.
- Future Vault creation requires a newly generated Recovery Key.
- Previous recovery material is invalid for the new Vault because the old Vault no longer exists.

Operational rule:

- Do not paste or upload new Recovery Phrase or Base64url code into chat, screenshots or public storage.

## First Local Vault Creation v1

Verified through local API:

- A local encrypted Vault was created successfully.
- Vault status is locked after creation.
- A profile record is available inside encrypted Vault storage.
- A Recovery Key was created and user confirmed secure storage.
- Recovery phrase and code are not recorded in project documentation.
- No provider OAuth account is connected.

## Dashboard Bidi and Locked Vault UI Repair v1

Implemented UI behavior:

- Vault locked state is translated by locale.
- Status card text uses logical locale alignment.
- Workspace status text uses Bidi-safe presentation.
- Quick and Deep controls remain physically left.
- Persian and Arabic dashboard text aligns RTL.
- English and Turkish dashboard text aligns LTR.

Verification:

- React production build passed.
- Browser visual verification remains required.

## Online Card and Chat RTL Repair v1

Implemented UI behavior:

- Each Dashboard Status Card receives explicit locale direction.
- RTL card labels, values and details align right.
- LTR card labels, values and details align left.
- Chat placeholder direction follows current UI locale.
- Persian chat placeholder aligns right.
- English chat placeholder aligns left.
- Quick and Deep physical left behavior remains unchanged.

Verification:

- React production build passed.
- Browser visual verification remains required.

## Dashboard Bidi Browser Verification Complete v1

Verified in local browser:

- Locked Vault status rendered correctly.
- Persian card and workspace text aligned RTL.
- English card and workspace text aligned LTR.
- Online card alignment was corrected.
- Chat placeholder direction followed current locale.
- Quick and Deep controls remained physically left.
- English System Status appeared above Quick and Deep near Sidebar.
- Header and Sidebar placement remained correct.

Dashboard Bidi visual acceptance is complete.

## Vault Unlock Flow Design v1

Unlock methods:

- Default: Vault Passphrase
- Secondary: English BIP39 Recovery Phrase
- Secondary: Base64url Recovery Code

Runtime behavior:

- Vault key exists only in running Backend memory after unlock.
- Vault passphrase and recovery input are not logged or stored.
- Vault automatically locks after 30 minutes of inactivity.
- Backend restart always returns Vault to locked state.
- System lock integration is planned later with Device Agent.

API endpoints:

- GET /api/v1/vault/status
- POST /api/v1/vault/unlock
- POST /api/v1/vault/lock

## Vault Session Manager and Unlock API Implementation v1

Implemented Backend runtime session behavior:

- `VaultSessionManager` owns the active unlocked `VaultStore` only in Backend memory.
- The Vault starts locked; Backend restart and FastAPI lifespan shutdown close active sessions.
- `GET /api/v1/vault/status`, `POST /api/v1/vault/unlock`, and `POST /api/v1/vault/lock` are implemented.
- Unlock supports passphrase, English BIP39 Recovery Phrase, and Base64url Recovery Code. Credentials and Vault keys are never returned by status or response payloads.
- Successful unlock exposes only `profile_name` and `address_name` while unlocked. Manual lock is idempotent and clears that context.
- Dashboard and onboarding status use the active runtime Vault state.

Inactivity and concurrency behavior:

- Default inactivity timeout is 1,800 seconds (30 minutes); a daemon timer performs actual auto-lock and status polling does not refresh it.
- Future private features must use `VaultSessionManager.access()` so Vault access is serialized and activity refreshes the timeout.
- FastAPI worker threads and the timer can differ from the unlock thread. SQLite connections use `check_same_thread=False`, while `VaultSessionManager` protects session operations with one `RLock`. `VaultStore` is not independently safe for uncontrolled concurrent use.
- Close releases the SQLite connection and Vault-key references. Python memory zeroization remains best-effort only.

Verification:

- 33 synthetic Python tests passed, including passphrase and both recovery methods, status synchronization, manual/repeated lock, credential non-echo, timer auto-lock, and cross-thread close.
- The real Vault was not unlocked, modified, or used by these tests.

## Vault Unlock UI Integration v1

The React frontend now integrates the local Vault session API:

- `VaultUnlock.tsx` uses only the local `/api/v1/vault/status`, `/unlock`, and `/lock` endpoints.
- Passphrase is the default UI method and uses an LTR password field.
- Recovery is secondary: the user explicitly opens Recovery Key options, then explicitly chooses English BIP39 phrase or Base64url code before its field is shown.
- Credentials are held only in component state for submission, cleared after successful unlock/lock, and never rendered into status or error text.
- The unlocked view shows only decrypted profile name/address context, the 30-minute timeout, refresh, and manual Lock.
- The frontend polls status once per minute only to notice auto-lock; Backend status polling does not refresh session activity.
- All Vault UI requests remain on `127.0.0.1`; no external provider or network request was added.

## Local Chat Core v1 Implementation

Local inference architecture:

- `ChatRuntime` is a portable runtime contract; `LlamaCppQwenRuntime` is the current Ubuntu CPU adapter and lazy-loads the verified Qwen3 GGUF only on the first request.
- Current local runtime profile is CPU-only, `n_ctx=2048`, `n_threads=8`, `n_gpu_layers=0`, and a single inference lock prevents concurrent CPU overload.
- `POST /api/v1/chat/stream` returns local NDJSON streaming events: `delta`, `done`, or a generic non-secret `error`.
- Requests are limited to transient `user`/`assistant` messages. No provider, external request, browser storage, conversation record, or memory record is added in Chat Core v1.
- Quick inserts `/no_think`; Deep uses normal Qwen thinking behavior. A chunk-safe filter removes `<think>...</think>` output from all user-visible streaming content.

Vault and privacy boundary:

- With a locked Vault, the model receives no private Profile, Address, memory or secret context.
- With an unlocked Vault, Profile Name and Address Name are read only for that one prompt through `VaultSessionManager.access()`; they are not persisted in Chat Core history.
- Browser Chat history is temporary and is cleared by refresh or the explicit Clear history control. It is not written to the Vault in this milestone.
- Browser Stop aborts local stream rendering. A synchronous CPU generator can require a short interval to finish its current work internally after the browser aborts.

Verification:

- 39 synthetic Python tests passed, including NDJSON streaming, Quick `/no_think`, thinking-tag suppression, input validation, locked/private context separation and unlocked profile context.
- A real local Quick synthetic request completed with the final response `local chat ready.` while the Vault was locked.
- The model loaded locally only; no credential, Profile context, conversation or external data was included in that test.

## Cross-Platform Personal Life Assistant Direction v1

Personal AI remains a local-first, policy-controlled life assistant intended to run on desktop and mobile platforms. Ubuntu/llama.cpp is the first adapter, not a permanent platform constraint. Vault privacy, permission policy, provider abstraction and chat contracts must remain portable to future Windows, Android and iOS adapters.

## Conversation and Memory Vault Design v1

Approved privacy policy:

- Chat remains temporary by default. A user explicitly enables `Save locally to Vault` for a conversation before persistent writes begin.
- Long-term memory is explicit-only in v1 through `Save as memory`; model extraction or automatic memory creation is not allowed.
- Saved conversations and memories remain until user deletion. There is no silent retention expiry in v1.
- Individual and bulk deletion actions require clear UI confirmation.
- When the Vault locks, decrypted saved conversation state is cleared from Browser UI and must be read again only after unlock.

Encrypted storage design:

- `conversation_catalog` is one encrypted record containing private conversation list metadata.
- Each `conversation_message` is an encrypted record with a random record ID and encrypted conversation ID, sequence, role, content and timestamps.
- `memory_catalog` and individual `memory` records follow the same encrypted pattern.
- VaultStore gains authenticated encrypted replacement and deletion operations. Replacement always uses a fresh AES-GCM nonce and atomic SQLite commit.
- No conversation title, message body, memory content, tag, source ID or timestamp becomes plaintext SQLite metadata.

Runtime behavior:

- Only an unlocked Vault may read or write saved conversations/memories.
- Chat Core v1 temporary history remains the fallback when saving is not explicitly enabled.
- Future retrieval/ranking is separate from this persistence milestone; v1 passes only user-selected memory into model context.

## Conversation and Memory Vault Implementation v1

Encrypted storage implementation:

- `VaultStore.find_records_by_type`, `replace_record` and `delete_record` support private record discovery, authenticated encrypted replacement with a fresh AES-GCM nonce, and record deletion.
- Conversation catalog, conversation messages, memory catalog and memory records are all encrypted Vault payloads. SQLite receives only random record IDs, schema version, nonce and ciphertext.
- `ConversationMemoryService` requires `VaultSessionManager.access()` for every operation. A locked Vault returns no private data and rejects persistence.
- Conversations are explicit-only: create, append, list, read, individual delete and bulk delete are exposed only through local API routes guarded by Vault Unlock.
- Memories are explicit-only: selected message content can be stored, listed, individually deleted or bulk deleted while unlocked.
- Chat Core injects at most 20 user-selected memory items, each capped at 500 characters, only while Vault is unlocked. It never performs automatic extraction.

Verification:

- 46 synthetic Python tests passed, including encrypted persistence, locked API guard, explicit conversation/memory lifecycle, deletion and selected-memory prompt context.
- Browser verification created only synthetic conversation/memory content in the real Vault after explicit user confirmation, verified the lists, deleted both, and manually locked the Vault.
- Final locked-state checks returned no private data: the Vault status had no profile context and conversation/memory endpoints returned `Vault is locked.`

## Device Agent Permission Policy Design v1

Agent baseline:

- Device Agent is disabled by default and uses default deny.
- Every request has an action ID, capability, target scope, device identity, risk class, preview, requested grant lifetime and audit outcome.
- Natural-language intent never directly becomes unrestricted shell, file or device access.

Capability and risk tiers:

1. Observe: read non-secret metadata or explicitly scoped text.
2. Launch: open an explicitly identified local app or file.
3. Write: create or modify user files.
4. Destructive: delete, overwrite, move irreversibly or alter permissions.
5. Network, secret, admin and financial/public actions.

Grant policy:

- Observe and Launch may receive Once, current Session, or exact Scoped expiry grants up to 30 days.
- Scope binds capability, canonical target selector, current device, profile and expiry.
- Write, Destructive, Network, secret, admin and financial/public actions always require fresh confirmation and never receive persistent grants.
- Session grants are memory-only and clear on Vault Lock or Backend restart.

Terminal policy:

- Terminal v1 uses exact argv, executable, cwd and declared expected effect preview.
- `shell=true`, pipes, redirection, wildcard expansion, hidden environment injection and implicit command chaining are prohibited.
- Every terminal execution is one-time confirmed, including read-only commands.

Audit policy:

- Durable audit records are encrypted Vault records containing no copied file content or secret values.
- Vault Unlock is required for immediate encrypted audit storage.
- While Vault is Locked, only safe Observe/Launch actions may run after explicit confirmation; they enter an in-memory volatile pending-audit queue.
- On next Vault Unlock, pending audit events are sealed into encrypted Vault audit records and marked deferred.
- If Backend restarts before Vault Unlock, the volatile queue is lost; UI must disclose this limitation and never claim a durable audit exists.
- All higher-risk actions require Vault Unlock so audit is written before execution.

Cross-platform contract:

- Platform adapters report available capabilities but may never bypass OS permission prompts, lock screens, sandbox constraints or administrator authentication.
- Ubuntu is the first adapter; Windows, Android and iOS implement the same policy contract with platform-native enforcement.

## Device Agent Permission Engine Core v1

Implemented policy-only core:

- `PermissionEngine` evaluates requests and creates authorization/audit models but has no action executor. It cannot run commands, read files, launch apps, write files or control devices.
- Capabilities are explicitly classified as Observe, Launch, Write, Destructive or High risk.
- Default deny is enforced. Safe capabilities may use Once, Session or Scoped expiry grants only while unlocked; high-risk capabilities only allow fresh Once approval while unlocked.
- Terminal preview accepts exact argv, cwd and expected effect. Shell executables, shell operators, command chaining, redirection and newline injection are rejected.
- Session grants remain memory-only. Scoped grants are encrypted Vault records and expire within 30 days.
- Encrypted audit records are written immediately while unlocked. A locked Vault allows only approved safe Once actions to create volatile pending-audit events; `seal_pending_audits` writes them encrypted after unlock.
- No actual executor, UI permission dialog, OS integration or Device Agent process exists in this milestone.

Verification:

- 50 synthetic Python tests passed.
- Tests cover locked safe pending audit, later encrypted audit sealing, high-risk unlock requirement, exact non-shell terminal preview, scoped/session grants and encrypted audit/grant records.
- No real file, terminal, program, network or device action was executed.

## Device Agent Preview Adapter Implementation v1

Implemented safely without execution:

- Ubuntu read-only capability adapter declares platform policy and guarantees: no file scan, command execution, app launch, network action or administrator action.
- `POST /api/v1/device-agent/preview` constructs and evaluates a permission request only. It does not issue a grant or invoke an executor.
- `GET /api/v1/device-agent/capabilities` and `/audit-status` expose preview-only state and volatile pending-audit count without private Vault content.
- 53 synthetic tests passed, including safe locked preview, locked terminal block and read-only adapter guarantees.
- Browser verification confirmed read-metadata preview shows Observe/Once and terminal preview requires Vault Unlock; no actual action was executed.

## User Sovereignty Permission Policy v1

The user is the final authority for requested device actions:

- Permission Engine informs, previews and warns; it does not silently substitute its own risk preference for an explicit user request.
- Default deny means no autonomous execution without user request and approval. It does not mean a user is prevented from proceeding with a dangerous requested action.
- Dangerous actions require an explicit fresh warning/confirmation with exact scope, effect, risk, data leaving the device and rollback information where available.
- User may proceed once after the warning, subject to real OS permissions, sandbox constraints and visible sudo/permission prompts. The agent never bypasses these controls.
- Dangerous grants are never persistent. User control is preserved through one-time confirmation, not through a later unattended high-risk action.
- Safe Session and Scoped grants are editable, revocable and deletable by the user at any time. Changes apply to the next authorization evaluation immediately.
- Audit events are historical records, separate from permission grants. Future audit controls may support explicit user deletion with a separate confirmed privacy policy; audit events are never silently altered.
- Passwords, Vault passphrases, Recovery material, tokens and secrets remain non-storable/non-enterable by the agent regardless of user grant changes.

## Ubuntu Read-Only Executor Design v1

Scope and path boundary:

- The executor begins with only a user-selected file or directory scope. It never scans Home or recursively discovers user files by default.
- Every requested path is canonicalized before preview and execution. A symlink that resolves outside the selected canonical scope requires a new explicit scope preview and confirmation.
- Read actions use no-follow/open-time protections where Ubuntu APIs support them to reduce path-swap and symlink races.

Read capabilities:

- `read_metadata` returns only path, file type, byte size, modified time and permission summary; it never returns file content.
- `read_text` is limited to regular text files up to 1 MiB in v1. Larger/binary files require a future separate policy and are not silently truncated into model context.
- No Write, Delete, Rename, Move, Launch, Terminal, Network, Secret export or Admin executor is included in this milestone.

Sensitive path policy:

- Sensitive path groups include `.ssh`, `.gnupg`, browser profiles, credential stores and secret configuration patterns.
- User may request sensitive content with a severe one-time warning and fresh confirmation, subject to OS access controls.
- Sensitive content is never written to audit plaintext, Vault memory, conversation persistence or clipboard automatically.
- Reading sensitive content does not automatically share it with Qwen. A separate explicit `Share with Personal AI` confirmation is required before it can enter one local model prompt.

Audit and execution behavior:

- Preview shows canonical path, requested read mode, size limit, sensitivity classification, content-to-model status and the exact audit outcome.
- Metadata/text read creates the Permission Engine audit event before returning data when Vault is unlocked; locked safe reads use the approved volatile pending-audit policy.
- The executor returns a short-lived result to the requesting UI; it never persists read content by itself.

## Ubuntu Read-Only Executor Implementation v1

The Ubuntu read-only executor is implemented for explicitly selected canonical files or directories only. It provides `read_metadata` and `read_text` through the Device Agent API, without any default Home-directory scan, recursive discovery, command execution, writing, network request, app launch, or administrator operation.

`POST /api/v1/device-agent/read-preview` returns a scoped preview. `POST /api/v1/device-agent/read` requires an explicit confirmation for the exact previewed item. Text reads are limited to regular UTF-8 files of at most 1 MiB; binary, NUL-containing, oversized, out-of-scope, and symlink-escape paths are rejected. `O_NOFOLLOW` is used where supported.

Sensitive paths require fresh confirmation. Read content is temporary and is never automatically sent to the local model; model sharing remains a separate future permission flow. The implementation has synthetic API/core tests and a user-controlled `/tmp` metadata-only verification. No personal file content was intentionally retained.

## Dual-Device Development Synchronization v1

The project worktree was verified on the home and workplace Ubuntu systems using the same deterministic 98-entry SHA-256 manifest. The selected source tree, model manifest and GGUF file, encrypted Vault database, and local UI preferences matched exactly before either worktree was designated canonical.

The home worktree is now the canonical development source. The workplace worktree remains an unchanged fallback until source-only Git synchronization is configured. The private Git remote will contain code, tests, documentation, assets, requirements, scripts, and the small model manifest only. It must never contain model weights, Vault data, local preferences, virtual environments, package caches, build outputs, credentials, or recovery material.

The GGUF model is installed independently on each device and verified locally by checksum. The encrypted Vault is not synchronized by Git and must have only one active writable copy at a time. Until an approved portable encrypted Vault workflow exists, the Vault is used only on the home system.

## Home Runtime Bootstrap Implementation v1

The canonical home worktree was prepared and verified on Ubuntu 26.04. Its runtime matches the validated workplace baseline: Python 3.12.13 from the deadsnakes PPA, Node 22.22.1, npm 9.2.0, CMake 4.2.3, GNU g++ 15.2.0, and GNU Make 4.4.1.

Python dependencies are installed in a project-local, Git-ignored `.venv` using Python 3.12 and `requirements/python.lock.txt`. The transferred virtual environment was incomplete and was rebuilt only after explicit confirmation. Frontend dependencies are installed in Git-ignored `apps/web/node_modules` from `package-lock.json`; the transferred dependency directory was also rebuilt after its required local executables were found missing.

Verification on the home system succeeded: the Vite production build completed and all 59 synthetic Python tests passed. The verification did not start the application services, load the GGUF model, or unlock the personal Vault. Model weights, Vault data, local preferences, `.venv`, `node_modules`, and build output remain outside Git.
