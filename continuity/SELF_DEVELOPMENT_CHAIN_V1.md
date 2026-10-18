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
