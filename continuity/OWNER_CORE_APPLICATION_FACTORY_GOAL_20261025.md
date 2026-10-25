# INVENTHOR — Owner Hedefi: Tek Sistem, Uygulama Üretim Döngüsü

**Owner priority update: 2026-10-25 | P0 / four-core scope.**
**Status: OWNER INTENT MIRROR / DESIGN AND BACKLOG HANDOFF ONLY.**
This file is **not** the Windows canonical Organizer ledger, a new task, lease, implementation success, or installation permission. Codex has already received an Owner command; do **not** create duplicate work based on this file.

## 1. Final product target (overrides old feature proliferation)

Build **one clean INVENTHOR** with exactly four active, interconnected cores:

- **INVENTHOR Brain/Main:** understand Turkish natural language/voice, take instructions, plan, remember the current project/program/document, answer questions, propose and revise designs, supervise progress.
- **Operator:** carry out permitted real operations in the **actual program** and computer, report reliable status/ACK, stop/cancel/revert if actually supported.
- **Organizer:** the **only canonical** project/task/worker/lease/revision/checkpoint/dependency/idea/evidence ledger for INVENTHOR, Codex and approved providers. Reuse installed `WORK_ITEMS.jsonl`, `EVENTS.jsonl`, current native Organizer task IDs and owner/lease protocols. No second work queue.
- **Uygulama Fabrikası / QA:** the **only existing** quality control/real test system; real build, UI interaction, logic, security, version, rollback, tests and failure evidence. Repair/re-test loop uses the same Factory, never a second test studio.

Required internal program editor/preview/runtime adapters are implementation capabilities of these cores, **not** newly proliferated products/modules. Provider adapters are replaceable and subordinate.

## 2. User experience

- INVENTHOR home uses minimal **Yeni Sohbet / Sohbetler / Projeler / Programlar**.
- The owner can give a new product idea entirely by speaking or text, without touching mouse; INVENTHOR turns it into the existing Organizer project/plan only after checking for current records, ownership and exact task.
- **The actual app/program opens.** Its design and running behavior can be viewed **one-to-one**, not a fake screenshot/mockup or a separate chatbot canvas represented as an app. Preview/build/runtime state is explicitly labeled: `DESIGN_DRAFT`, `RENDERED_PREVIEW`, `RUNNING_PROGRAM`, `TESTED_BUILD` are **display semantics only**, not invented Organizer lifecycle states.
- A **single** compact movable/collapsible INVENTHOR composer remains inside/alongside that actual program: written chat, truthful live voice, STT, microphone state, progress, Stop, Undo, QA result. Owner may leave it tiny or expand it, may work with mouse, or leave all safe reversible edits to INVENTHOR.
- INVENTHOR should respond to "move this, change the layout, add that feature, improve this screen, change my mind about the idea" with a real program edit through Operator's verified capabilities. Design context = project, program, opened file/document, selected object, revision, capability permission, current task/lease, actual command result. If bridge is disconnected, do not fake a change.
- Owner can request an alternative idea or roll back a previous design; record chosen revision and discarded candidate without overwriting approved version silently. Changes must be reversible where feasible, with snapshot/diff and change log.

## 3. End-to-end application production cycle

The following are **workflow phases**, NOT new native Organizer task states:

```text
OWNER IDEA (voice/text)
  -> existing Organizer: deduplicate / current project+task / owner focus
  -> INVENTHOR: understand requirements, questions only when essential, plan
  -> real DESIGN + real interactive RENDER/PREVIEW
  -> actual PROGRAM RUN under permission-scoped Operator
  -> owner inspects live running program; may edit manually or change idea
  -> INVENTHOR applies authorized UPDATE to real program
  -> existing FACTORY QA: BUILD + INTERACTION + LOGIC + SECURITY + REGRESSION
       + revision/hash + evidence + rollback checks
  -> FAIL? link exact defect to SAME Organizer task/project,
       INVENTHOR diagnoses, Operator fixes under fresh lease, send back to SAME QA
       [bounded iterations; no infinite retry, no repeated unknown side effect]
  -> PASS? report independently verified acceptance and install/release readiness
       (separate owner gate for signing/UAC/installation/publishing)
  -> continued changes create new approved revision and run the same QA loop
```

INVENTHOR must control design, actual preview, execution, update, error diagnosis, repairing QA findings, resubmitting to QA, user-driven changed requirements and safe rollback. **Passing source unit tests is not proof that a real program opens or runs.** Failures are real blockers with evidence and a next finite action; no fabricated completion or endlessly looping retries.

## 4. Organizer canonical goal migration — REQUIRED NATIVE CODEX STEPS

**Important:** GitHub comments/documents are read-only mirrors. Only an authorized local Codex/Operator worker may update the real Organizer on the owner's PC.

1. Read **current exact canonical Organizer handoff** for the existing active P0 work; retain immutable PROJECT_ID and TASK_ID, live revision, checkpoint, last evidence and owner/lease. In previous records the relevant anchors included `TASK_20260925_OPERATOR_FOUNDATION_GATE`, Brain coordinator `TASK_20260926120200_1F352D`, and QA project `IDEA_20261009192901_335851`; verify they still exist, are eligible and are currently authoritative instead of assuming they are available.
2. Reconcile Codex's **already received** owner command with existing project/goal records (avoid duplicate command, project, task, new Studio/Factory, or restarting terminal work). Scope this as an explicit **owner priority change**, but **do not take over another worker's active lease**.
3. Update the canonical **existing project goal/acceptance criteria/next steps/dependencies** to exactly this one app-creation–design–real-preview–real-run–update–QA–repair–retest loop; don't merely paste a generic backlog note. Use existing supported native Organizer APIs, work item types and statuses. If schema does not permit goal mutation, record a backed-up, exact-task owner directive/checkpoint and report a schema migration blocker; do not hand-edit JSONL around the tool.
4. Inventory active host/services/menus/registries/jobs/capabilities/dependencies: `CORE`, `CORE_REQUIRED_INTERNAL`, `DEFERRED_NONCORE`. Defer all separate products (Viktorija, cleaner, antivirus, unrelated studios, experimental module projects, etc.) in **existing canonical Organizer** as future separate projects; keep recoverable source, design, test evidence and versioned archive. Remove inactive noncore links from the live four-core startup after dependency checks, backup, real tests and rollback; permanent deletion is separately owner-gated.
5. Keep only one Brain, one Operator executor, one Organizer store, one Factory/QA. Protect working UI/approved gear; simplify navigation rather than rebuilding existing approved design. UI changes must follow the approved **actual program + compact in-program assistant** contract at `inventhor-brain-design/intelligence/INVENTHOR_IN_PROGRAM_AI_ASSISTANT_V1.md`.
6. Verify reported **17 Operator PR#3 overlapping PC files** and locally deleted Cleanup. Do not restore an intentionally removed cleaner, blind-merge or overwrite Codex-owned native files. Create exact 3-way reconciliation/diff only under current task/lease; isolate only core-relevant changes.
7. Verify installed QA Factory version (previously **0.5.0**, 0.7 only draft), real Brain/Main/Organizer/Operator ACK and lease, signer, UAC, rollback and observable app UI. Only perform authorized staged deployment after independent QA.
8. Save genuine evidence checkpoint: actual task/project IDs, before/after goal, source paths and hashes, deferred project mapping, active integration map, test results, blockers and the **smallest next finite open step**. No terminal replays, fabricated receipts or batch resets.

### Suggested existing-Organizer acceptance criteria, not proof of completion

- P0 goal visible from **fresh exact canonical handoff**, with owner intention, original IDs, exact revision and one current owner.
- Only core+required internal services active; no dangling external module menu, startup or job; deferred projects independently recoverable.
- Owner opens real program and converses via one integrated small moving assistant, not a faux preview.
- Spoken or typed instruction safely changes one actual program element; results, stop/undo and mouse takeover have evidence.
- Owner changes mind; new version is applied without losing prior version.
- Program builds and actually runs. The QA Factory receives exact artifact hash and revision; test failures are linked to real Organizer tasks; one real correction is sent to QA again and independently passes.
- Installed release and owner approval gates work; actual status displayed honestly, no SOURCE_PASS => LIVE_PASS shortcut.

## 5. Current verified limits

Beyin source draft PR #6 contains source-level advisory and four-core readiness code; it **is not installed/activated** by GitHub commits. Operator draft PR #3 overlaps native Codex files and depends on Cleanup in source. Installed QA/ACK cannot be verified while the PC connection is offline. Native Organizer mutation is **NOT CONFIRMED**. No actual activation, deletion, new provider, paid actions, UAC, forced merge or signing is authorized by this document.

**Next:** Codex's already-active canonical task, once owner/lease checked, must update the original Organizer goal and execute one finite native plan step. Mirror state MUST remain `NATIVE_ORGANIZER_NOT_VERIFIED` until a fresh trusted handoff shows it.

## 6. Owner addendum: OLD MODULES BECOME SEPARATE PROGRAMS, NEVER PERMANENTLY EMBEDDED

**Final scope clarification 2026-10-25 (owner):** Every legacy *non-core* module that represents a user-facing feature/product is an individually listed **future standalone program**. It is not reattached as an integrated module to the live INVENTHOR shell. Real source candidates are listed in [DEFERRED_PROGRAM_CANDIDATES_20261025.json](DEFERRED_PROGRAM_CANDIDATES_20261025.json) (**SOURCE DIRECTORY EVIDENCE ONLY**, NOT a verified native inventory nor created Organizer tasks). Codex must enumerate any additional real installed module IDs rather than assuming this cloud candidate file is complete.

- **Core runtime remains exactly four:** Brain/Main, Operator, Organizer, App Factory/QA. Supporting mandatory adapters/security/transport components belong INSIDE those cores as implementation details, not as autonomous products. In particular, do not accidentally pull out the live Operator transport/permission/QA link merely because its historical name contains "module".
- **Each deferred user-facing module becomes ONE recoverable, distinct app/project** in the existing Organizer's program/project inventory: original module ID, intended app name, version/provenance, source archive, tests, assets, dependency classification, original active references, future backlog, and current migration status. Link to existing task IDs after deduplication; don't manufacture unverified Organizer records in the GitHub mirror.
- **No extra central service per program.** When the user starts a standalone program, it loads its own real interface and its small optional INVENTHOR voice/text assistant dock. A versioned and authenticated per-app adapter exposes program-document/selection/context, *all allowed native design and runtime capabilities*, edit/update/test/undo/cancel and real progress to the **single** central INVENTHOR Brain and **single** Operator. This permits comprehensive control over the features the program actually provides and the owner authorizes—not arbitrary privileged OS access, covert shell or secret leakage. Disconnected mode fails closed but ordinary manual use remains possible if the program supports it.
- **Detaching the legacy embedded module:** verify original Organizer work record and current Codex lease, backup sources and user data, identify registry/service/permission/UI/startup references, check that no four-core dependency is removed, execute one reversible detachment batch, confirm installed Factory regression and rollback, and only then remove obsolete references. For actual irreversible file deletion or loss of local data, obtain explicit owner approval. Preserve future standalone app candidate recoverability and historical decisions.
- **Acceptance:** opening Programs lists independent actual programs (not hidden feature modules), the program window works; the same central Brain+Operator may inspect authorized context, listen/respond, create/change design, execute changes and submit test versions to the existing Factory. No duplicate brain, no second Operator agent or central Organizer, no ghost embedded modules or dead links.
- **Codex integration requirement:** Native canonical Organizer **existing goal** should explicitly include "EACH DEFERRED MODULE -> SEPARATE PROGRAM", its inventory, archival/detachment milestones and acceptance checks. This owner addendum supersedes any previous wording implying all historical modules should remain installed or be re-created as integrated INVENTHOR plugins.
