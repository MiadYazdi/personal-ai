# Personal AI — UI Design v0.1

## Product Name

Display name: Personal AI

The display name must be configurable for each user in the future.

## UI Goals

The user interface must be:

- Professional
- Modern
- Futuristic
- Readable
- Interactive
- Privacy-first
- Suitable for daily life, coding and device collaboration

Visual effects must not reduce readability or performance.

## Theme System

Initial theme behavior:

- Follow the operating-system theme by default.
- The user can explicitly select System, Dark or Light.
- The selected preference is stored locally per user.
- The UI must remain readable in all themes.

## Language and Text Direction

Language is selected during onboarding.

Supported initial UI languages:

- Persian
- English

Direction rules:

- Persian UI uses RTL.
- English UI uses LTR.
- Every message bubble determines its own direction.
- Code blocks, terminal commands, file paths, URLs and identifiers always use LTR.
- Mixed Persian and English text uses unicode-bidi: plaintext.
- Inputs may use automatic direction detection where appropriate.

Examples that must render correctly:

- فایل src/personal_ai/core.py را باز کن
- دستور python -m pytest را اجرا کن
- مسیر /home/miad004/Desktop/personal_ai را بررسی کن

## Primary Screens

1. Onboarding
   - Display name
   - UI language
   - Theme
   - Privacy explanation
   - Memory policy
   - Device permission introduction

2. Chat Workspace
   - Conversation history
   - Composer
   - Quick / Deep visible mode selector
   - Local / Online status
   - Model status
   - Streaming response area

3. Permission Cards
   - Requested action
   - Target scope
   - Device
   - Risk level
   - Always / Ask every time / Allow once choices

4. Memory Center
   - Suggested memories
   - Approved memories
   - Edit and delete controls
   - Search

5. Device and Tool Center
   - Connected devices
   - Device-agent status
   - Allowed capabilities
   - Local tool activity

6. Model and Privacy Settings
   - Local model selection
   - Quick / Deep settings
   - Model residency mode
   - Online feature controls
   - Update and download controls

## Technical Direction

Frontend:

- React
- TypeScript
- Vite
- Modern responsive CSS system
- Interactive component system
- Local browser access only in the first version

Backend:

- Python
- FastAPI
- Local-only binding to 127.0.0.1
- Shared core with CLI
- SQLite for local profile, memory and permission data

## Security and Privacy UI Rules

- Local / Online state is always visible.
- Online actions show what will be sent before transmission.
- A permission decision is never hidden.
- Sensitive actions use clear warning language.
- The UI never displays secrets, passwords or private keys in plain text.
- The UI never claims a device action succeeded unless the device agent confirms it.

## Accessibility and Responsiveness

- Keyboard navigation must work.
- Color alone cannot convey a warning or permission state.
- The interface must work on desktop browser sizes first.
- The architecture must remain responsive for future Android and iOS clients.

## Vault Status in the User Interface

The Web UI and CLI must clearly show Vault state:

- Locked
- Unlocked
- Unlock required for private action

Rules:

- Private profile, memory, conversations and secret settings are unavailable while Vault is locked.
- The UI must never display the Vault passphrase after entry.
- The UI must not imply that private memory is available when the Vault is locked.
- Onboarding must explain the difference between operating-system login and Vault unlock.
- Sensitive settings must show whether they are protected by the Vault.

## Vault Passphrase and Recovery UX

Vault onboarding must include:

- Explanation that Vault passphrase differs from operating-system login password.
- Passphrase strength guidance and warnings without an arbitrary hard block.
- Optional Recovery Key creation.
- Explicit warning before the user declines Recovery Key creation.
- One-time Recovery Key display with copy and local-save actions.
- A confirmation step that the user has stored the Recovery Key.
- Clear Locked and Unlocked Vault status after onboarding.


## Implemented UI Foundation v0.1

Implemented frontend stack:

- React 19.2.7
- TypeScript 7.0.2
- Vite 8.1.4
- Tailwind CSS 4.3.2
- Lucide React 1.24.0

Implemented UI foundation:

- System / Dark / Light theme selector
- Persian / English language selector
- RTL and LTR layout switching
- Mixed-language-safe code and path display rules
- Visible Quick / Deep mode selector
- Vault, model, online and Device Agent status cards
- Local API status fetch from 127.0.0.1:8765
- Production build verified successfully

Not yet implemented:

- Real chat composer and streaming responses
- Vault onboarding screens
- Permission decision cards connected to backend
- Memory center connected to encrypted Vault
- Device and tool control screens connected to Device Agent


## Localized Runtime Status and Bilingual Thinking Labels

Runtime API values may remain stable machine-readable English values.
The UI translates user-facing status values according to the selected UI language.

Examples:

- not_started becomes هنوز شروع نشده in Persian UI.
- Online becomes آنلاین in Persian UI.
- No external request is active is translated in Persian UI.

Thinking-mode display:

- Persian UI:
  سریع / Quick
  عمیق / Deep

- English UI:
  Quick
  Deep

Internal API values remain quick and deep.

## Browser Runtime Verification v0.1

The initial React interface was verified in a local browser session.

Verified:

- Local Vite UI at http://127.0.0.1:5173
- Local FastAPI data rendered successfully
- Persian RTL layout
- English LTR layout
- System theme UI
- Visible Quick and Deep selector
- Local model, Vault, Online and Device Agent status cards

Pending UI enhancement:

- Quick and Deep labels will remain English in both UI languages.
- Advanced user-customizable dashboard design is under roadmap review.

## Advanced Custom UI v1

Approved implementation scope before Vault onboarding:

- Accessible drag-and-drop Dashboard ordering
- Widget visibility controls
- Custom accent color
- Sidebar compact and expanded modes
- System, Dark and Light themes
- Layout presets
- Reset layout
- Local per-device persistence of non-private UI preferences

Reasoning-mode labels:

- Quick and Deep remain English in both Persian and English interfaces.
- Internal mode values remain quick and deep.

Persistence rules:

- Preferences are stored locally for the current operating-system user and device.
- No UI preference is sent to the internet.
- No personal profile, Vault record, memory or conversation is required.
- Future onboarding can migrate these preferences to a named Personal AI profile.

## Advanced Custom UI Implementation Dependencies

Installed packages:

- @dnd-kit/core==6.3.1
- @dnd-kit/sortable==10.0.0
- @dnd-kit/utilities==3.2.2

These packages will provide accessible drag-and-drop ordering for Dashboard widgets.
The drag-and-drop code is not implemented yet; only dependencies were installed and verified.

## Advanced Custom UI Backend Foundation v1

Implemented backend persistence foundation:

- GET /api/v1/ui-preferences
- PUT /api/v1/ui-preferences
- Local per-device non-private preference schema
- Atomic local preference storage
- Widget order and visibility validation
- Theme, accent, sidebar mode and preset validation

The React Custom UI controls are not implemented yet.
The next implementation stage connects these endpoints to the React interface.

## UI Preference GET Runtime Verification v1

Verified behavior:

- The local preference API returns initial defaults before any user customization is saved.
- Reading default preferences does not create a local preference file.
- React Custom UI can safely load defaults before the user changes layout, theme or widgets.

## UI Preference Persistence Verification v1

Verified local UI preference persistence:

- PUT successfully saves non-private UI preferences.
- GET returns the saved preferences.
- Default initial configuration is now stored locally.
- Preference storage is per device and remains outside the private Vault.
- POSIX directory mode 700 and file mode 600 were verified.

## React Customizer Implementation v1

Implemented controls:

- Open and close Customizer panel
- Save local UI preferences
- Theme selection
- Accent palette
- Custom hexadecimal accent color
- Sidebar expanded and compact mode
- Widget visibility controls
- Default, Focus and Minimal presets
- Reset layout
- Unsaved, saving, saved and error states

Current limitation:

- Dashboard cards are not drag-sortable yet.
- Drag-and-drop ordering is the next Custom UI implementation phase.

## React Customizer Browser Verification v1

Verified in the running local UI:

- Customizer panel rendering
- Theme and accent controls
- Sidebar mode controls
- Widget visibility controls
- Preset and reset controls
- Save state feedback
- Local preference persistence after page refresh

The next Custom UI feature is drag-and-drop dashboard ordering.

## Drag and Drop Implementation v1

Implemented:

- Drag handle on each visible Dashboard widget
- Pointer drag support
- Keyboard drag support
- Visual state for card being moved
- Reordering of visible cards
- Preservation of hidden widget positions
- Manual Save preferences requirement after layout changes

Pending verification:

- Browser drag interaction
- Save reordered layout
- Browser refresh persistence of reordered layout

## Direct Sidebar Toggle UX v1

UX decision:

- Sidebar compact/expanded control is a direct icon button at the top of the sidebar.
- Sidebar mode is removed from the Customizer panel.
- Toggle behavior is immediate and auto-saved.
- Auto-save affects sidebar_mode only.
- Other unsaved Customizer changes remain unsaved.
- Save failures restore the previous persisted sidebar mode and display an error.

## Advanced Custom UI v2 UX

Default visual baseline:

- Clean, readable and minimal main workspace.
- Modern optional dashboard cards.
- Default control location: App Menu at the bottom of the Sidebar.
- Header remains uncluttered by default.

Customizable UI settings:

- Sidebar placement: left or right
- Sidebar mode: expanded, compact or hidden
- Sidebar width: normal or wide
- Font scale: small, default, large or xlarge
- UI density: compact or comfortable
- Theme, accent and motion preference
- Control location: App Menu, Sidebar Settings or Header
- Widget order and visibility
- Layout presets and reset

Locale packs:

- fa, en, ar and tr are initial UI locales.
- RTL: fa and ar.
- LTR: en and tr.
- Unsupported UI locale falls back to English.

## UI Preference Schema v2

Available preference categories:

- Language
- Theme
- Accent color
- Sidebar placement, mode and width
- Font scale
- UI density
- Motion preference
- Controls location
- Widget order and visibility
- Layout preset

Backward compatibility:

- Existing v1 preferences load safely with v2 defaults.
- The file is upgraded only after explicit save.

## Runtime Schema Migration Verification v1 to v2

Verified:

- Existing UI preference file loads through the API as schema v2.
- Newly introduced UI settings receive approved defaults in memory.
- Existing saved layout settings are preserved.
- Disk file remains v1 until the user explicitly saves a preference.

## React Advanced Custom UI v2 Implementation

Implemented:

- App Menu default control placement
- Optional Header or Sidebar Settings control placement
- Sidebar left, right, hidden, compact, expanded and wide modes
- Language persistence
- fa, en, ar and tr locale packs
- Font scale controls
- UI density controls
- Motion controls
- Minimal Header default
- Custom UI preference schema v2 integration

Pending browser verification:

- App Menu placement
- Locale switching and refresh persistence
- Sidebar placement/mode/width persistence
- Font scale, density and motion behavior
- Drag-and-drop save and refresh persistence

## Sidebar Flush and Mobile Drawer v1

Desktop:

- Sidebar is visually flush with the left or right viewport edge.
- No centered-layout gutter separates Sidebar from the browser edge.

Mobile and tablet:

- Sidebar becomes an overlay drawer.
- Drawer opens from the selected left or right edge.
- Drawer closes with backdrop interaction.
- A mobile menu button is always available.
- Settings and App Menu remain reachable when the drawer is closed.

This behavior applies to responsive Web UI now and native mobile clients later.

## Sidebar Flush and Mobile Drawer Implementation v1

Implemented responsive controls:

- Full-width app layout
- Flush desktop Sidebar
- Mobile overlay drawer
- Mobile menu button
- Drawer backdrop close behavior
- Drawer close button
- Responsive access to App Menu

Pending browser verification:

- Flush left and right Sidebar placement
- Mobile drawer opening and closing
- Mobile App Menu access
- Layout preference persistence after refresh

## Sidebar Physical Layout and Mobile Schema v3

Desktop:

- Sidebar left/right placement is physical and independent from RTL/LTR text direction.
- A left Sidebar remains on the left for every UI language.

Mobile:

- follow_desktop maps Desktop expanded to drawer.
- follow_desktop maps Desktop compact to compact icon rail.
- follow_desktop maps Desktop hidden to mobile menu button and drawer.
- Users can explicitly choose compact rail or drawer per device.

Controls:

- controls_location supports App Menu, Sidebar Settings, Header and both.
- Default control behavior combines Sidebar App Menu with compact Header shortcuts.

## UI Preference Schema v3

Added preference fields:

- mobile_sidebar_behavior
- controls_location including both

Supported mobile sidebar options:

- follow_desktop
- compact_rail
- drawer

Backward compatibility:

- v1 and v2 files are loaded safely in v3.
- Missing values receive approved defaults.
- File upgrade occurs after explicit save.

## UI Preference v3 Runtime Verification

Verified:

- The running API returns v3 preferences.
- mobile_sidebar_behavior is available to the UI.
- controls_location is available to the UI.
- Existing user-selected preferences remain after migration.
- Explicit UI save persisted schema version 3 locally.

## React Schema v3 and Physical Sidebar Repair

Implemented:

- React default preference schema version 3
- Mobile sidebar behavior preference support
- controls_location=both support
- Physical sidebar placement independent from locale direction
- Compact rail and drawer CSS classes

Pending browser verification:

- Left Sidebar stays left after Persian or Arabic selection
- Right Sidebar stays right after language changes
- Mobile compact rail
- Mobile drawer
- Header shortcut and App Menu both behavior

## Physical Sidebar and Mobile Drawer Browser Verification v1

Verified:

- Physical left Sidebar in RTL and LTR UI
- Flush Sidebar layout
- Compact Desktop Sidebar rail
- Mobile compact rail
- Mobile Drawer
- Drawer close control
- App Menu access inside mobile Drawer

Still pending:

- Drag-and-drop save and browser refresh persistence.

## Responsive UI Alignment Repair Pending v1

Visual repair requirements:

- Header uses physical-left controls and logical-start title placement.
- Status cards align text to the active locale direction.
- Desktop cards use available width without centered-looking content.
- Mobile compact rail expands into a coherent drawer from the same edge.
- Mobile drawer and content cannot overlap incorrectly.
- Mobile card layout and typography must be responsive and readable.

Drag-and-drop final verification remains after responsive repair.

## Responsive UI Alignment Repair Implementation v1

Implemented visual behavior:

- Logical card text alignment
- Physical-left Header shortcut controls
- Locale-aware Header title alignment
- Full-width desktop layout
- Compact mobile rail
- Same-edge drawer expansion
- Single-column mobile widget cards
- Correct mobile content padding

Pending browser verification:

- Desktop RTL and LTR title/card alignment
- Mobile compact rail visual behavior
- Mobile drawer expansion and close behavior
- Drag-and-drop persistence

## Mobile Fixed Sidebar and Locale Dropdown v4

Mobile UX:

- Compact icon rail is always fixed on the selected edge.
- Sidebar toggle expands or compacts the same Sidebar.
- Expanded Sidebar overlays Main Content.
- No separate mobile close button, backdrop close or hidden Sidebar state.
- Sidebar remains available in every mobile state.

Language UX:

- Use custom language dropdown inside Settings.
- Options render directly below the language control.
- Locale selector does not depend on native browser popup placement.
- Settings panel visually overlays Sidebar.

## UI Preference Schema v4

Mobile Sidebar preference:

- compact
- expanded

Migration:

- v1, v2 and v3 preference files load safely as v4.
- Previous mobile drawer behavior migrates to compact or expanded.
- Mobile Sidebar never defaults to fully hidden.
- Disk file upgrades after explicit save.

## UI Preference v4 Runtime Verification

Verified:

- Running UI preference API returns schema v4.
- Legacy v3 mobile behavior maps to compact mobile Sidebar mode.
- Existing disk file remains unchanged until explicit save.

## Mobile Fixed Sidebar and Custom Locale Dropdown Implementation v4

Implemented:

- Fixed compact mobile rail
- Compact to expanded Sidebar toggle
- Same-edge expanded overlay
- Custom locale dropdown under language field
- Local language auto-save
- fa, en, ar and tr choices

Pending browser verification:

- Compact rail persistence
- Expanded overlay behavior
- No backdrop or separate close control
- Locale dropdown placement
- Language persistence after refresh
- Drag-and-drop persistence

## Advanced Custom UI v4 Browser Verification Complete

Browser-verified features:

- Desktop flush Sidebar
- Physical left/right placement independent from locale direction
- Compact and expanded Sidebar
- Mobile fixed rail
- Mobile expanded overlay
- Custom locale dropdown placement
- fa, en, ar and tr locale switching
- Language persistence
- Theme, accent, font scale, density and motion persistence
- App Menu and Header shortcut behavior
- Widget drag-and-drop persistence after refresh

Advanced Custom UI v4 acceptance is complete.

## Vault Onboarding UX Decisions v1

Required onboarding field:

- Profile Name.

Editable addressing:

- Address Name initially copies Profile Name.
- User can edit Address Name separately.
- Assistant uses Address Name in future conversation.

Recovery screen:

- Recovery Key is optional.
- If created, display both 24-word phrase and Base64url code.
- Show one-time copy and local-save actions.
- Require explicit acknowledgment before the user closes the recovery screen.

## English BIP39 Recovery Phrase UX v1

Recovery screen behavior:

- Recovery Phrase always uses English BIP39 words.
- UI instructions remain in the user-selected UI language.
- Base64url code is shown alongside the phrase.
- User receives a clear explanation that both forms represent the same secret.
- User must confirm that recovery material was stored before closing the one-time screen.

## Local and Online Account UX v1

Onboarding account choice:

- Local Account:
  Uses offline Vault onboarding.

- Online Account:
  Offers supported OAuth provider choices when user enables Online mode.

UX rules:

- OAuth login never replaces Vault passphrase.
- Provider password is never entered into Personal AI.
- Provider service connectors are separate consent screens.
- UI shows provider, requested scopes and data impact before authorization.
- Users can disconnect provider access later.

## BIP39 Recovery Library Verification v1

Verified implementation dependency:

- mnemonic==0.21

Verified presentation basis:

- English 24-word BIP39 phrase
- Base64url code for same recovery secret
- Local-only generation and validation

## BIP39 Recovery Core Implementation v1

Available backend capability:

- Generate English 24-word phrase.
- Generate matching Base64url code.
- Validate phrase and code during recovery.
- Unlock encrypted Vault through either representation.

UI recovery screen implementation remains pending.

## Vault Onboarding API UX v1

Local onboarding steps:

1. Select Local Account.
2. Enter Profile Name.
3. Optionally edit Address Name.
4. Enter and confirm non-empty Vault passphrase.
5. Choose whether to create optional Recovery Key.
6. If Recovery Key is created, show BIP39 phrase and Base64url code once.
7. Require user acknowledgment before closing recovery screen.

Validation UX:

- Empty Profile Name is rejected.
- Empty Vault passphrase is rejected.
- Short passphrase is warned about but not blocked by arbitrary length rules.

## Vault Onboarding Service UI Readiness v1

Available local API endpoints:

- GET /api/v1/onboarding/status
- POST /api/v1/onboarding/local-vault

UI can now implement:

- Local Account onboarding form
- Profile Name and Address Name fields
- Vault passphrase input and confirmation
- Optional Recovery Key choice
- One-time BIP39 and Base64url recovery display
- Status-aware onboarding flow

Browser onboarding UI remains pending.

## Vault Onboarding Status Runtime Verification v1

Verified UI precondition:

- Backend reports Vault not created.
- Onboarding UI may safely render Local Account creation flow.
- No profile or sensitive data exists before explicit user submission.

## React Vault Onboarding Preview UI v1

Implemented onboarding UI:

- Local Account state
- Online Account coming-later state
- Profile Name
- Address Name
- Passphrase and confirmation fields
- Optional Recovery Key selector
- Validation preview
- Security note

Important:

- Create Vault action is preview-only.
- No POST onboarding request is sent yet.
- No real Vault or profile can be created through this UI stage.

## Onboarding Bidi and Form Layout Repair Pending v1

Required UI repair:

- Apply logical-start alignment to labels and descriptions.
- Use dir=auto for Profile Name and Address Name fields.
- Use LTR direction for passphrase fields.
- Use unicode-bidi: plaintext for mixed-language help text.
- Use BDI isolation for technical tokens.
- Keep form inputs equal height and aligned in desktop grid.
- Use a single column on mobile.

## Onboarding Bidi and Form Layout Repair Implementation v1

Implemented:

- dir=auto text inputs for names
- LTR passphrase inputs
- BDI-safe technical terms
- Logical text alignment
- Equal desktop form input sizing
- Responsive mobile form layout

Pending browser verification:

- Persian form alignment
- English form alignment
- Mixed-language helper text
- No actual Vault submission

## Onboarding Geometry and Autofill Repair Implementation v1

Implemented:

- Equal Profile Name and Address Name field geometry
- Controlled centered onboarding form width
- Consistent input heights
- Browser autofill theme override
- Responsive mobile form width

Pending browser verification:

- Symmetric name fields
- Password autofill visual theme
- Centered form layout

## Sidebar Footer Controls Default v1

Default UI:

- Refresh and Settings icons live at the bottom of Sidebar.
- Header remains minimal.
- English title starts near Sidebar on the left.
- RTL title uses logical right alignment.

Custom UI:

- User can select Sidebar footer, Header or both control locations.

## Sidebar Footer Controls Implementation v1

Implemented:

- Settings and Refresh in Sidebar footer
- Default app_menu control placement
- Minimal Header in default mode
- User-selectable Header or both control locations

Verification:

- Current local preference saved as app_menu.
- Browser visual verification remains pending.

## Sidebar Settings Navigation and Schema v5

Default Sidebar:

Conversation
Widgets
Device Agent
Settings

Footer:

Local Mode
Refresh

Controls location UI:

- Sidebar Settings
- Header
- Both

The App Menu option is removed from the UI.

## Sidebar Settings Navigation Implementation v1

Implemented UI:

- Settings icon below Device Agent
- Refresh icon in Sidebar footer
- App Menu option removed from controls location UI
- Minimal Header in Sidebar Settings mode
- Header controls available only for Header or Both settings

Verification:

- React production build passed.
- Browser verification remains required.

## UI Preference Schema v5 Runtime Verification

Verified:

- Running UI preference API returns schema v5.
- Current control placement is sidebar_settings.
- Browser refresh can now verify Settings navigation below Device Agent.

## Vault Onboarding Preview Browser Verification Complete v1

Verified UI:

- Sidebar Settings navigation
- Sidebar Footer Refresh action
- Header layout
- Centered onboarding panel
- Bidi-safe name fields
- Themed passphrase fields
- Recovery Key preview
- Preview-only validation without POST submission

Next UI phase:

- Explicit confirmation modal
- Real local Vault POST submission
- One-time Recovery Key display

## Final Vault Creation Confirmation UI v1

Modal:

- Show Profile Name.
- Show Address Name.
- Show Recovery Key choice.
- Do not show passphrase.
- Require explicit acknowledgment checkbox.
- Final Create button triggers POST only after acknowledgment.

Recovery result screen:

- Show English BIP39 phrase once.
- Show Base64url code once.
- Copy phrase button.
- Copy code button.
- Download local plaintext recovery text file.
- Clear recovery material after acknowledgment.
- Warn user that downloaded file is sensitive plaintext.

## Final Vault Confirmation Implementation v1

Implemented UI:

- Final confirmation modal
- Profile/Address/Recovery summary
- Acknowledgment checkbox
- Final Create button
- One-time recovery phrase and code screen
- Copy and download actions
- Recovery acknowledgment and continue action

Browser verification remains required before real Vault creation.

## Dashboard Bidi and Locked Vault UI Repair v1

Implemented:

- Localized locked Vault status
- Logical card text alignment
- Bidi-safe workspace status text
- Physical left Quick/Deep controls

Pending browser verification:

- Persian dashboard alignment
- English dashboard alignment
- Locked Vault status display
- Quick/Deep physical left placement

## Online Card and Chat RTL Repair v1

Implemented:

- Explicit per-card locale direction
- RTL Online card alignment
- LTR Online card alignment
- Locale-aware chat placeholder direction

Pending browser verification:

- Persian Online card
- Persian chat placeholder
- English card and placeholder

## Dashboard Bidi Browser Verification Complete v1

Browser-verified:

- Persian RTL Dashboard
- English LTR Dashboard
- Online card Bidi alignment
- Locked Vault localized status
- Chat placeholder direction
- Physical left Quick/Deep placement
- English System Status + Quick/Deep left toolbar layout

## Vault Unlock UI Design v1

Default unlock screen:

- Locked Vault status
- Passphrase input by default
- Passphrase input LTR
- Secondary Recovery Key option
- Recovery Phrase and Base64url methods shown only after explicit selection
- Unlock success updates profile/address context
- Lock action available after unlock
- Inactivity auto-lock after 30 minutes

## Vault Unlock UI Implementation and Browser Verification v1

Implemented:

- Responsive Local Vault panel for locked and unlocked states.
- Passphrase default, password visibility control, LTR credential fields, local-only notice, and generic non-secret errors.
- Secondary Recovery Key selection with explicit BIP39/Base64url method choice.
- Manual Lock action, unlocked Profile/Address context and 30-minute inactivity information.
- Persian, English, Arabic and Turkish copy; RTL local-only alignment repaired for Persian/Arabic.
- Browser verification confirmed real local passphrase unlock, profile detection, manual lock, and API status returning `locked` after the test. No credential was shared in chat.
- Production TypeScript/Vite builds passed after implementation and RTL repair.

Dashboard privacy presentation decision:

- The local model status card, ready state and model identifier are intentionally not shown in the personal Dashboard.
- The remaining visible cards use an adaptive grid with no empty model-card column.
- This is presentation-level concealment only; it does not remove the local model or hide technical metadata from local filesystem/API access.

## Local Chat Core UI and Bidi Content Rule v1

Implemented chat UI:

- Active local streaming Composer with Quick/Deep mode selection, temporary browser-only history and manual Stop.
- Copy is available for User and Assistant messages. Copy is user-initiated and writes only to the local operating-system clipboard.
- User-message Edit discards later temporary turns and streams a replacement response; Assistant Regenerate repeats the previous user context; Clear history removes only Browser state.
- The model status card, ready state, identifier, Widget setting and stale pre-chat status text are not shown in the personal UI.

Bidi Content Rule v1:

1. Localized UI sentences use the active locale and do not mix casual untranslated English words into Persian/Arabic copy.
2. Intentional technical tokens, URLs, codes and credentials use explicit LTR/BDI isolation.
3. Persian/Arabic editable UI fields begin RTL; English/Turkish fields begin LTR; technical credentials remain LTR.
4. User and Assistant message paragraphs use `dir=auto` and `unicode-bidi: plaintext`, so the message content—not an English sender label—controls Persian/Arabic text and emoji direction.
5. Enter sends a message; Shift+Enter inserts a line break.

Browser verification completed for streaming messages, Quick/Deep controls, temporary history, model UI concealment, adaptive cards, RTL placeholder/content repair and message actions.

## Conversation and Memory UI Design v1

Approved controls:

- `Save locally to Vault` is off by default for a new conversation and shows explicit storage state.
- Saved conversation list supports open, rename/title later, individual delete and bulk delete with confirmation.
- Every user-selected message can offer `Save as memory`; memory management supports individual and bulk deletion with confirmation.
- Saved content must disappear from rendered Browser state on manual or automatic Vault Lock.
- Copy remains a user-initiated local clipboard action and is not a persistence mechanism.
- UI language/Bidi rules apply to all conversation and memory labels, dialogs and confirmations.

## Conversation and Memory UI Implementation v1

Implemented user controls:

- `Save locally` is off by default and opens an explicit encrypted-storage confirmation before creating a saved conversation.
- `Save as memory` is a per-message, user-initiated action.
- Manage saved data supports open, individual delete and bulk delete for conversations and memories, with explicit confirmation.
- Editing/regenerating a saved conversation leaves its encrypted version unchanged and marks new changes as temporary until the user explicitly saves again.
- Vault Lock removes the active saved conversation from Browser state; locked persistence endpoints expose no stored content.
- Browser verification completed with synthetic data only; no personal conversation or memory was intentionally retained.

## Device Agent Permission UI Design v1

Permission request screen must show before execution:

- Human-readable action, exact capability, target scope and affected application/file/device.
- Exact terminal argv and cwd where relevant; no hidden shell behavior.
- Risk class, data leaving device, expected result and available rollback information.
- Decision controls: Deny, Allow once, Allow this session, and Scoped expiry only when the action is Observe/Launch.
- Fresh confirmation for Write, Delete, Network, secrets, admin and other high-risk actions.
- Clear warning when a safe locked-Vault action has only volatile pending audit and must be unlocked later to seal audit.
- Audit panel distinguishes sealed encrypted events, pending volatile events and unavailable/lost events after restart.

## Device Agent Preview UI Implementation v1

Implemented:

- Device Agent sidebar opens a preview-only panel in all four UI languages.
- Panel shows adapter guarantees, capability/risk/scope/effect preview and volatile audit count.
- Terminal preview accepts exact argv display only and does not execute it.
- Persian labels are localized; only technical code values remain LTR.
- Browser verification confirmed preview-only behavior and no system action execution.

## Permission Decision Changeability v1

- Permission settings must show active Session and Scoped grants with capability, exact scope, device and expiry.
- User can revoke, shorten expiry, replace scope or delete a safe persistent grant at any time.
- High-risk actions show an explicit warning and one-time Proceed/Deny decision; no persistent high-risk toggle is shown.
- UI must distinguish permission settings (user-editable) from audit history (historical records).
- Every permission change is previewed before saving and applies immediately to future requests.

## Ubuntu Read-Only Executor UI Design v1

- User selects an exact path/scope; UI shows resolved canonical scope before read confirmation.
- Metadata and Text are distinct options with a visible 1 MiB limit.
- Sensitive classifications show a severe one-time warning, but user retains the right to proceed within OS permissions.
- `Share with Personal AI` is a separate disabled-by-default control after a sensitive read; it is not implied by read confirmation.
- Result UI labels content as temporary, not persisted and not copied automatically.
- No recursive scan, write/delete, terminal or application launch control is present in v1 executor UI.

## Ubuntu Read-Only Executor UI Implementation v1

The Device Agent includes a compact localized Ubuntu read-only panel. The user enters a selected path and chooses metadata or text mode. Enter and the preview action create only a preview; they never read content.

After a preview, the interface shows the canonical path, size, and any sensitivity warning. The user must activate a clear checkbox confirming that the read applies only to that exact previewed path, then choose the normal read button. A sensitive path additionally prompts for fresh one-time confirmation. Changing the path or mode clears the preview and its confirmation.

The preview and read actions are full-width and centered within the panel, with intentional spacing from the mode control. Persian and Arabic use RTL layout while paths and technical values remain explicit LTR. Results are marked temporary, not saved to Vault or memory, and not automatically shared with the model.

## Local Model Share UI Implementation v1

After a confirmed read-text result, the Read-Only panel offers a separate local-model-share preparation action. The user sees a fixed plan with canonical path, byte size, chunk count, sensitivity warning, and large-job warning. A dedicated acknowledgement is required before processing starts; sensitive content also receives a fresh browser confirmation.

While local processing runs, the panel shows progress and offers cancellation. Cancellation stops future chunks after the current local model operation completes. The result is sent to the conversation as a local assistant response.

The shared raw content appears in the conversation as a collapsed, expandable card showing path, byte count, and chunk count. It is not a normal chat prompt message, so later ordinary chat requests do not silently include it. If the user explicitly saves the conversation while the Vault is unlocked, the card is persisted as an encrypted attachment; otherwise it remains browser-temporary.

## Local Model Share Synthetic UI Verification v1

The home-browser verification confirmed the Read-Only text result, local model-share plan, one-time confirmation, and Chat card flow using the synthetic `/tmp` file only. The chat card displays localized byte and chunk labels, an expandable raw-text view, and the final local assistant response. No personal file or Vault content was used.
