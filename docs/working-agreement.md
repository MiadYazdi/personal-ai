# Personal AI — Working Agreement

## Core Rules

1. No project phase starts without explicit user confirmation.
2. No technical decision is made from assumptions when the required fact can be checked.
3. Every proposed installation, system change, internet action, sensitive access or destructive operation must explain:
   - what changes,
   - why it is needed,
   - how it works,
   - what data leaves the device, if any.
4. The assistant distinguishes clearly between:
   - verified fact,
   - technical proposal,
   - unresolved question requiring user input.
5. Commands and explanations are reviewed carefully before being provided.

## Path Stability Rule

A user question, idea or consultation request does not automatically change the approved project path.

When a possible path change is identified, the assistant must first provide:

1. The proposed change.
2. The logical reason for it.
3. The expected benefit.
4. The cost, risk or trade-off.
5. Available alternatives.
6. The effect on the current approved roadmap.

The project path changes only after explicit user approval.

## Decision Persistence Rule

Important decisions must be recorded in project documentation.

The assistant must preserve and follow approved decisions, including:

- local-first and user-controlled online behavior,
- Hybrid Vault privacy model,
- permission policy,
- manual operating-system login,
- platform support strategy,
- UI language and direction rules,
- Quick and Deep model modes,
- confirmed technical stack,
- current approved roadmap.

## Current Approved Roadmap

1. Development environment and local Qwen3 runtime.
2. Hybrid Vault core and synthetic security tests.
3. Local FastAPI backend, CLI and React Vertical Slice.
4. Temporary localhost execution and browser verification.
5. Vault onboarding and first real user profile.
6. Local chat integration with Qwen3.
7. Permission Engine and Ubuntu Device Agent.
8. Persistent user-session agent.
9. Windows, Android and iOS clients in later phases.



## Current Implementation Status

Active development root:

- /data/personal_ai

Old verified copy retained:

- ~/Desktop/personal_ai

Completed milestones include:

- Development environment, local model runtime and verified model integrity.
- First real local encrypted Vault and profile created.
- Recovery Key created and user confirmed secure storage.
- Dashboard Bidi, Locked Vault, Online Card and Chat RTL browser verification completed.
- FastAPI backend, CLI, React UI and Advanced Custom UI v4.
- Vault onboarding API, service and browser flow.
- Vault Unlock Flow Design approved: passphrase default, recovery secondary, 30-minute auto-lock.

- Vault Session Manager and local unlock/lock API implemented; 33 synthetic tests passed.

- Runtime session supports passphrase, English BIP39 and Base64url recovery methods; actual 30-minute timer auto-lock and cross-thread close behavior verified.

- Vault Unlock UI implemented and browser-verified locally: passphrase default, recovery secondary, profile context, manual lock and auto-lock status are available in four UI languages.

- Personal Dashboard intentionally hides the local model card, ready status and model identifier; adaptive cards fill the released layout space. This is UI presentation only, not a security boundary.

- Local Qwen Chat Core implemented and verified: lazy local Qwen runtime, NDJSON streaming, Quick/Deep, thinking-tag suppression, read-only unlocked Profile context and no conversation persistence.

- Chat UI supports temporary Browser history, Stop, Copy, User Edit, Assistant Regenerate and Clear history; all actions remain outside the Vault in v1.

- Bidi Content Rule v1 implemented and browser-verified for localized copy, editable fields, technical LTR values, mixed content and emoji direction.

- Product direction reaffirmed: Personal AI is a local-first, policy-controlled cross-platform life assistant; Ubuntu is the first adapter, with Windows, Android and iOS remaining planned targets.

- Conversation & Memory Vault Design v1 approved: conversations are opt-in, memories are user-selected only, retention is manual, deletion is confirmed, and Vault Lock clears decrypted Browser state.

- Conversation & Memory Vault v1 implemented and browser-verified: encrypted opt-in conversations, explicit memories, manual retention, confirmed deletion, selected-memory context and Locked-state privacy guard.

- Device Agent Permission Policy Design v1 approved: default deny, scoped safe grants, fresh high-risk confirmation, structured one-time terminal preview, encrypted Vault audit and volatile pending audit only for safe locked-Vault actions.

- Device Agent Permission Engine Core v1 implemented and verified with 50 synthetic tests. It authorizes previews and audit models only; no real system/device action executor exists.

- Device Agent Preview Adapter/UI v1 implemented and browser-verified: localized preview/audit panel and Ubuntu read-only capability discovery are available; execution remains disabled.

- User Sovereignty Permission Policy v1 approved: user may proceed with a warned dangerous requested action once, safe grants remain editable/revocable, and dangerous grants never become unattended persistent permissions.

- Ubuntu Read-Only Executor Design v1 approved: selected canonical path scope, 1 MiB text cap, no default scan, sensitive content one-time warning, and separate model-share confirmation.










- Local Vault First and OAuth provider architecture decisions.
- Safe project copy and checksum verification to /data/personal_ai.
- Personal AI launchers and Portable Project Icon Theme.
- Final httpx2 FastAPI TestClient stack verified without deprecation warnings.

Current next proposed milestone:

Implement Ubuntu Read-Only Executor Core with synthetic metadata/text fixtures, canonical-path/symlink defense and encrypted audit tests; no real user file read occurs until explicit user preview confirmation in a later browser test.

No provider OAuth account is connected yet.

## Documentation Synchronization Rule

After every completed project phase, before any next phase begins:

1. Verify the actual result of the completed work.
2. State clearly whether the phase succeeded, failed or needs repair.
3. Audit the impact of that work on existing project documentation.
4. Update the relevant existing documentation when a decision, implementation state, dependency, roadmap item or security rule changed.
5. Show Git status after documentation review.
6. If no documentation update is needed, explicitly state:
   Documentation audit: no update required.
7. Do not begin the next phase until verification and documentation synchronization are complete.

This rule exists to keep code, installed dependencies, actual runtime behavior,
documentation and the approved roadmap synchronized at all times.

## Read-Only Confirmation Workflow v1

For the Ubuntu Read-Only Executor, a real read is always user-controlled:

1. The user selects a path and requests a preview, optionally with Enter.
2. The preview identifies the exact canonical path and relevant risk information.
3. The user actively checks the confirmation box for that exact preview.
4. The user selects the separate read button to perform the one scoped read.
5. Sensitive paths require an additional fresh warning confirmation.

Enter never performs a real read. A path or mode change invalidates the preceding preview and confirmation. No selected content is automatically stored, sent to the model, or shared externally.

## Dual-Device Canonical Workspace Policy v1

- The home worktree is the canonical Personal AI project source after a successful deterministic manifest comparison with the workplace copy.
- The workplace worktree remains a fallback until the private Git workflow is configured and verified.
- Source synchronization uses private Git only after a reviewed first commit and explicit approval before any network push. Model weights, Vault data, local preferences, credentials, recovery material, virtual environments, dependency caches, and build outputs remain outside Git.
- The encrypted Vault has one active writable location at a time. It is used on the home system until a separately approved portable encrypted storage procedure is available.
- No worktree is overwritten or deleted merely because another copy exists. Before any future repair or transfer, compare deterministic manifests and transfer only confirmed missing or differing files.

## Home Runtime Rebuild Procedure v1

Machine-local runtime artifacts are never treated as portable project source. On a new or transferred Ubuntu system, Python virtual environments and frontend dependency directories must be audited before use. If a transferred `.venv` or `node_modules` directory is incomplete, it is not silently trusted or overwritten: the user sees the result and explicitly approves its rebuild or preservation.

Runtime installation is disclosed in advance. Adding a package source, installing system packages, downloading Python packages, and downloading frontend packages each require explicit user approval. The canonical home runtime uses Python 3.12.13, Node 22.22.1, and npm 9.2.0. Local build/test verification is completed before any application service is started.

Generated runtime paths remain Git-ignored. The Vault is not used as a synchronization mechanism and remains active only on the home system until a separately approved portable encrypted storage workflow is available.

## Local Model Share Consent and Retention v1

- A read confirmation never substitutes for a model-share confirmation. Sharing text with the local model always requires a separate fixed-plan acknowledgement.
- The plan displays canonical path, size, digest, chunk count, and sensitivity before execution. It is invalid if its digest no longer matches the supplied text and path context.
- Large text is never silently shortened. The user may approve the complete local chunk plan, observe progress, and cancel remaining work.
- Raw shared content is visible in a collapsed conversation card. It remains temporary unless the user explicitly saves the conversation while the Vault is unlocked.
- Saved raw attachments are encrypted in Vault chunks and are deleted with the conversation. Audit records contain metadata only, never raw content.
- No model-share test or implementation step accesses a real user file, unlocks a real Vault, or invokes the real model without an explicit user action in the live UI.
