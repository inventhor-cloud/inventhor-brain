> **CURRENT OWNER PRIORITY 2026-10-26:** ONLY finish actual production platform **INVENTHOR, OPERATOR, ORGANIZER, STUDIO_DESIGN, QA_FACTORY** (QA=Fabrika; Organizer is the one existing canonical ledger). All other modules and future program initiatives are deferred and MUST NOT be started. This explicitly supersedes the 2026-10-25 separate-program conversion instructions for active work. The native Organizer existing task/project goal must be aligned by current authorized worker, not from a GitHub mirror. See [latest owner production engine contract](OWNER_PRIORITY_PRODUCT_ENGINE_20261026.md).

# Owner Work Intake Policy

Status: ACTIVE

Every new Owner request that represents work must enter the canonical **idea/backlog intake** unless it is purely conversational. Intake is not permission to start, and an existing active job is not implicitly preempted. Only an explicit owner priority-change instruction can override the current target, subject to existing authorization and safety checks.

Intake pipeline:
1. normalize the request
2. compute stable fingerprint
3. compare against Project Registry / Work Queue / Module Registry / Knowledge Graph
4. classify as NEW / RELATED / MERGE_CANDIDATE / DUPLICATE
5. if duplicate, link to the existing Work Item instead of creating another
6. if related, attach dependency/relation
7. assign project, priority and prerequisites
8. insert into the canonical Idea Pool or Work Item backlog; mark non-urgent/new feature requests as PLANNED and do not automatically make them executable
9. when authorized and eligible, promote the canonical Work Item and replicate only the execution-relevant slice to Windows Operator
10. continue automatically **only if** explicit work-plan authorization, ownership/lease and prerequisites are satisfied; unrelated ideas never interrupt in-flight work

Owner can reprioritize at any time.

Default execution policy:
- deterministic/local Operator work first
- provider use only when semantic reasoning is actually needed
- do not spend provider tokens on build/test/hash/copy/download/inventory/retry/status work
- checkpoint after meaningful progress
- keep evidence
- never claim DONE without acceptance evidence

The queue survives chat/provider/session changes.

## Operator / Brain scope boundary

GPT/Codex/INVENTHOR collaboration and the QA Factory are the immediate owner priority. Brain cleanup may proceed concurrently in non-overlapping files/targets. Additional provider integrations belong in the backlog until the owner changes priorities. This file is public reference policy, not an executable work authorization or a replacement for live canonical Organizer records. See [LIVE_SOURCE_FRESHNESS_GATE.md](LIVE_SOURCE_FRESHNESS_GATE.md).

## HISTORICAL owner priority — 2026-10-25 / superseded by 2026-10-26 five systems

The Owner explicitly overrode earlier product/module expansion priorities. For **new intake and Organizer goal reconciliation**, only four cores stay active: INVENTHOR Brain/Main, Operator, existing canonical Organizer, existing App Factory/QA. The product goal is the complete spoken/written **idea -> design -> genuine live preview/runtime -> actual change/update -> Factory QA -> repair -> QA retest -> approved release** loop, with user-controlled revisions and optional manual mouse intervention. [Owner goal and native migration handoff](OWNER_CORE_APPLICATION_FACTORY_GOAL_20261025.md).

Other products/modules (including Viktorija, Cleaner, Antivirus and future standalone extensions) are **DEFERRED** in the **same Organizer**, with intact recoverable source/evidence, pending native registry/lease validation and approved reversible isolation. No duplicate modules, Studios, queues or QA services. This priority change must be reflected in the current *existing* native Organizer Project/Work Item goal and acceptance criteria by its active authorized worker; no blind overwrite, task replay, new task ID or mass mutation from a source mirror. The GitHub version of this policy is informative only, not the canonical native migration receipt.
