# INVENTHOR Main — Budgeted Self-Development & Cross-Agent Learning V1

**2026-10-18. SOURCE_IMPLEMENTED / SOURCE_TESTED after CI. NOT LOCAL_DEPLOYED.**

## Goal

Let each independently verified completed step enable the smallest already-existing downstream development work, without duplicate projects, unbounded module growth or paid provider traffic. Let INVENTHOR learn from **structured, evidence-backed** attempts by Codex, ChatGPT, local Operator agents and other connected providers. Owner edits the limits; this is not an implicit grant to rewrite production code.

The canonical actors remain:

- **Main Brain:** product choices, interpretation, owner settings, original durable Work Queue, Knowledge Graph, agent lessons, and task leases
- **Operator:** deterministic execution, builds/tests, screenshots/UI probes, evidence collection, local snapshots, bounded retry and rollback
- **Quality Factory:** independently assesses acceptance and fingerprints what genuinely passed/failed
- **Other AI agents:** produce work/evidence records; their claim of success never equals authenticated Quality Factory verification

There is **no second Organizer/queue/registry**, recursive autonomous model, model-weight retraining service, unrestricted tool access or separate paid control plane.

## Default owner-configurable limits (example only)

Reference: [SELF_DEVELOPMENT_SETTINGS.example.json](SELF_DEVELOPMENT_SETTINGS.example.json).

| Setting | Initial example | Meaning |
|---|---|---|
| \`enabled\` | \`true\` | Toggle all self-development selection on/off |
| \`max_steps_per_cycle\` | \`1\` | Small finite work batch; advisor proposes **one** at a time |
| \`steps_remaining_today\` | \`4\` | Host-owned daily budget, persisted across restarts and provider switches |
| \`max_parallel_tasks\` | \`1\` | Only one mutation job at a time initially |
| \`active_tasks\` | \`0\` | Authoritative host count, not inferred from an AI claim |
| \`max_changed_files_per_step\` | \`4\` | Larger changes must be split into smaller verified steps |
| \`paid_providers_enabled\` | \`false\` | No paid API calls in initial mode |
| \`provider_budget_units_remaining\` | \`0\` | Main owner may later enable an explicit budget |

The example is **not a live setting** and does not change the installed Windows app. Main Settings UI/host must own edits, per-project profiles, persistence, daily reset and atomic counters. The pure planner never silently raises limits, bills services or treats owner settings as permission for an unrelated host action. It accepts higher owner-selected ceilings where structurally valid.

## How the development chain works

1. A change lands in an existing Work Item with a stable \`PROJECT_ID + TASK_ID\`.
2. Operator builds/tests; Quality Factory records a \`VERIFIED_DONE\` evidence receipt tied to the current Main revision. Source tests are **not** evidence of a deployed runtime.
3. Main exports revision-pinned queue, projects, leases, owner settings, Quality Factory completions and structured agent evidence.
4. \`review_development_chain\` examines owner limits, completed dependency receipts, duplicate work fingerprints, repeated failures and active scope leases. It builds a **temporary filtered view**, never edits the canonical queue.
5. Existing \`advise_next_work\` chooses the one highest-priority eligible Work Item. New modules are not silently invented; when an Inventory gap needs a task, Main Owner Work Intake must dedupe and register it before the chain selects it.
6. Main host still performs authentication, current revision and epoch recheck, atomic task/filename lease CAS, provider-cost enforcement and operation approval. A plan is not a lease.
7. Operator executes the authorized finite step, records progress/evidence, and requests Quality Factory acceptance.
8. When a step is verified, Main updates counters, checkpoints, dependency status and learning events. It can invoke the planner again within the configured limits.
9. On quota exhaustion, loss of network, app restart, failed test, conflict, uncertain evidence or exhausted daily steps, Main checkpoints and stops; it does not restart the same failed command in a loop.

**Specific nonexecuting code paths**

- \`shared_organizer/development_chain.py::review_development_chain\`: budget, dependency evidence, project isolation, deduped work, retry and canonical scope assessment
- \`shared_organizer/agent_learning.py::review_agent_lessons\`: project-scoped deterministic failure/recovery signature matching
- \`shared_organizer/__main__.py::evaluate_envelope\`: existing source-only CLI intent \`DEVELOPMENT_CHAIN_REVIEW\` and \`AGENT_LESSON_REVIEW\`; does not start providers/workers
- \`shared_organizer/inventory.py\`: identifies exact missing module capabilities and finite next action
- \`shared_organizer/owner_modules.py\`: owner can choose arbitrary product/module categories without an allowlist; existing module extensions preferred to duplicates

## Learning from other agents, including mistakes

Use only structured Main-replicated **event records**, never copied private chat transcripts, passwords or unaudited AI self-praise. Each event records a unique event ID, project/task ID, agent ID, step type, outcome, timestamp, failure fingerprint, evidence reference, and an independent Quality Factory verification bit.

- Two identical errors by different agents produce one deterministic **"do not replay; diagnose"** lesson candidate.
- A later verified repair of that failure by any agent produces a **"review known working fix"** candidate with an evidence reference and relevant project task. It does **not** automatically copy/apply code.
- One unverified assertion, single error or a success that predates the failure cannot establish a reusable fix.
- Same fingerprint from a different project is not permission to share private information or reuse a project-specific solution.
- Repeated calls produce deterministic \`lesson_fingerprint\` values. Main must persist the appropriate lesson/evidence only after authenticating source and verifying referenced artifacts.
- No model fine-tuning or new paid service is needed for deterministic error learning. Higher-level semantic generalization can use an optional owner-configured provider *later*, only with data boundaries and budget.


## Pinned Main → Operator handoff packet

The existing read-only Main adapter now supports \`OPERATOR_HANDOFF_REVIEW\`. Main submits the last \`NEXT_DEVELOPMENT_STEP_ADVISORY\`, a **separately prepared** task-specific source plan and the same \`snapshot_revision\`. \`shared_organizer.execution_packet.review_operator_handoff\` checks:

- exact immutable \`PROJECT_ID + TASK_ID\`, unchanged queue revision and valid canonical file/module scope;
- full 40-character base + candidate commit pins and a 64-character source-tree SHA-256 claim;
- operation/action SHA-256, \`step_kind\`, file-count limit and the **owner budget**'s corresponding file limit;
- *explicit* prior failed-action fingerprint list (missing history is not treated as empty), repeat failure, available cycle budget, concurrent-job limit, zero-paid-provider default, and provider quota;
- deterministic project/task/source/action/step/scope fingerprint to help Main deduplicate an exact retry;
- required actual Main owner/scope/lease CAS, independent backup/rollback and Quality Factory acceptance.

The resulting \`HOST_HANDOFF_PACKET_READY\` packet is **not executable**: \`execution_allowed=false\`, no host authentication/lease receipt, no arbitrary shell commands and no ability to install, spend or overwrite. The authenticated Main host must recheck all original catalog/task/lease revisions and exact on-disk hashes at actual write time, create a separate authorization receipt and issue work to the current installed Operator. A GitHub draft passing source tests does **not** activate this workflow in the running PC.

This operational step list is not a product allowlist: it does not limit which owner-chosen apps or module types may be built. It constrains the provenance and size of code changes to avoid recreating Codex-style branch and file collisions.

## Gap detection and durable Fix Memory handoff

With optional revision-pinned \`module_catalog\` and \`module_observations\` supplied by the authentic host, the same chain can produce one \`inventory_gap_for_main_intake\` suggestion. It has stable SHA-256 \`suggestion_fingerprint\`, existing-task matches, the project/module/capability and an explicit \`next_action\`. Suggestions always have \`proposed_task_id=null\` and \`may_create_task=false\`; Main Owner Work Intake is responsible for validating source evidence and de-duplicating before registering any new Work Item. Verified terminal work is never automatically replayed.

\`advise_fix_memory_promotion\` accepts a current, host-attested \`INVENTHOR_MAIN_FIX_MEMORY\` snapshot and new cross-agent lessons. It suggests one of:

- \`PROPOSE_NEW_CANONICAL_FIX_MEMORY_RECORD\`: genuinely new lesson fingerprint
- \`REUSE_EXISTING_CANONICAL_MEMORY\`: identical lesson and evidence already known
- \`REVIEW_VERIFIED_RECOVERY_ENRICHMENT\`: earlier lesson exists, newly verified repair could enrich it
- \`REVIEW_CONFLICTING_FIX_EVIDENCE\`: preserved prior proof conflicts with the newer proof

Memory suggestions are bounded to four per planning call and never write, delete or overwrite the canonical Fix Memory ledger. Existing \`fix_memory/fix_memory_index.json\` is a **legacy GitHub template** with no live revision; it cannot itself be treated as an attested Main memory snapshot. Main host must supply the new revisioned envelope, verify Quality Factory receipts and persist proposals through its own authorized memory workflow.

The same planner explicitly holds tasks marked \`provider_required=true\` if the provider price or quota has not been verified. Default missing provider-cost data is never used as proof that a provider call is free. The caller's provider permissions and budget still require live host enforcement.

## Main quality feedback and daily budget reconciliation

`shared_organizer/cycle_feedback.py::review_cycle_feedback` completes the **source-only proposal** for the end of one finite development step. The existing `python -m shared_organizer` adapter exposes `DEVELOPMENT_FEEDBACK_REVIEW` with a revision-pinned `handoff_packet`, `quality_feedback`, `development_ledger`, `snapshot_revision` and `host_time_iso`.

The authenticated Main host must supply and verify:

- The nonexecuting exact `handoff_fingerprint`, project, task, action SHA-256 and original source-tree SHA-256 from its previously selected one-step handoff.
- A recent **Quality Factory** `VERIFIED_DONE` or `VERIFIED_FAILURE` record, the same project/task/action/tree identity, the QA evidence reference, a backup reference, a rollback-plan reference, and the actual test counts. A success cannot contain failed tests or zero passing tests.
- The current canonical owner-local day, remaining daily steps, number of active tasks and at most 512 previously consumed handoff fingerprints from the **existing Main Development Ledger**. The ledger is host owned; this source helper does not create a second database.

The advisor returns one of:

1. `FEEDBACK_RECONCILIATION_ADVISORY`: propose decrementing **one** daily step and one active task, appending exactly the used handoff fingerprint, and either moving the canonical work item to the host's independent acceptance flow or recording the verified failed action for diagnosis. It does **not** itself mark the task done or launch another task.
2. `ALREADY_RECORDED`: a prior completion for that handoff is present; propose **no mutation**, no extra budget deduction and no replay (including case-insensitive hash equality).
3. `BLOCKED`: stale data, insufficient quota, invalid or cross-task QA evidence, missing backup/rollback plan or malformed budget history. Do not retry the same unsafe mutation.

**Critical trust distinction:** the helper only checks the structure and consistency of **host-supplied claims**. A self-declared `source=INVENTHOR_QUALITY_FACTORY` value or source-only test is **not authentication**. Before applying any counter or queue change, Main must independently validate the issuer, signature/receipt, live epoch, lease and expected current revision, then perform a single atomic compare-and-swap. If any verification fails, the installed host does nothing.

CI tests cover successful finish, failed finish, exhausted daily budget, duplicate callback, another project's result, stale cross-version result, time-zone day boundary, malformed untrusted data and nonexecuting CLI integration.

## Quality and full chain acceptance (remaining host tasks)

Source-only Python tests validate planning, budgets, lessons and CLI. To claim **AUTONOMOUS_LOCAL_VERIFIED**, the installed Main/Operator must additionally pass:

1. Authenticated Main Owner Settings UI persists limits across sessions, allows manual edit/disable, and enforces counters without race/restart resets.
2. Live Operator receives the current task and exact scope through host-issued CAS lease; duplicated agents cannot write the same file.
3. Completing A with independent Quality Factory receipt unblocks registered dependency B; without real receipt B cannot start.
4. A failure repeated by Codex and another agent prevents the same retry. A later verified fix becomes a provenance-linked lesson accessible through authorized Main memory.
5. Operator can perform one small approved patch/build/test/checkpoint cycle, then follow on to the next registered task until the owner budget is reached.
6. No paid provider calls in default mode; provider usage is metered by the host, not trusted from chat context. Free GitHub CI can test source but does not imply zero hosting expense for other runtime choices.
7. Queue/task/learning memory survives app restart; never replays BS/BF/DONE items or creates duplicate task/module identities.
8. Every production change has a tested package, backup/rollback, live UI/service health and independent end-to-end acceptance. Source-only code cannot sign or install itself.

**Evidence states remain distinct:** \`SOURCE_IMPLEMENTED\` ≠ \`SOURCE_TESTED\` ≠ \`LOCAL_DEPLOYED\` ≠ \`AUTONOMOUS_LOCAL_VERIFIED\`.

This document extends \`AUTONOMOUS_EXECUTION_ARCHITECTURE.md\`, \`DEDUPLICATION_PIPELINE.md\`, and \`SHARED_ORGANIZER.md\`, without rewriting existing canonical user work or ignoring permissions for other people's data.
