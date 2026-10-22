# Live Source and Freshness Gate (INVENTHOR Brain)

Status: policy / cloud reference, **not** proof of installed runtime behavior.
Scope: GPT, Codex and INVENTHOR/Operator now. Additional providers remain backlog.

## One source of truth

- The **owner-authorized local INVENTHOR Main/Organizer ledger and event log** hold current work status, task ownership, dependencies, checkpoints and evidence references.
- This GitHub repository is a **public, sanitised reference and continuity mirror**. A GitHub file, chat transcript, static `continuity/work_queue.json` or `CONTINUE_HERE.md` cannot authorise a new task, prove it is DONE or replace a local lease.
- Legacy queue, manifest and active-project examples are dated snapshots. Do not use their `READY`, `BLOCKED`, `ACTIVE` or `NEXT_TASK` fields to start work without fresh owner-runtime confirmation.
- Main Brain is the planner; Operator is the execution body. No duplicate Brain, writable cloud task ledger, provider-owned queue or parallel work database.

## Mandatory handoff, regardless of agent

1. Obtain the **exact canonical TASK_ID** from the owner-authorized live service. If unavailable, stop at read-only analysis and report `LIVE_HANDOFF_UNAVAILABLE`; never guess from a dated cloud snapshot.
2. Read the task-scoped **live handoff**: project/target, current state, dependency state, owner/lease/session, last verified checkpoint, completed items, remaining items, blockers, next action, evidence reference and artifact hashes.
3. Check that both the task state and the evidence are fresh. A single `DONE` flag or an AI answer is not acceptance. Distinguish `SOURCE_TESTED`, `INSTALLED`, `LIVE_QA_VERIFIED` and `SIGNED_RELEASED`.
4. Before any write, acquire the existing canonical lease and **fresh explicit preflight**. If another worker owns the target or dependency is unresolved, do not preempt, steal locks, or replay terminal work.
5. Run the **smallest outstanding authorized step**. Record bounded evidence and checkpoint arrays for both completed and remaining items; include last verified version/hash where applicable.
6. Release the lease on planned handoff. The next worker must reread the live record and revalidate before starting. After a crash or unknown remote result, reconcile first rather than retry a side effect.
7. If current live state cannot be read, **fail closed** for changes and installation; independent safe read-only investigation may proceed.

## Owner priority and non-interruption

The current owner priority is the actual QA Factory end-to-end acceptance (including independent UI witness, trusted QA evidence, signed release, canary and rollback), while Brain housekeeping may proceed in separate non-conflicting scope. The initial collaboration roster is GPT, Codex and INVENTHOR. New provider integrations are **planned, not current scope**.

A newly mentioned feature is an **idea/backlog candidate by default**, not an implicit preemption. Deduplicate against the canonical work list, record its goal and intended target, then return to the current priority. A new active work assignment or priority override requires a clear owner instruction and normal task-admission safeguards.

## Clean operation

- **No secrets, private files, personal memory or live machine paths** in this public mirror. Never copy a full live ledger here.
- Clean up by verifying, classifying, retiring stale references and deleting only under existing owner policies, with a reversible record; avoid mass deletions and duplicate projects.
- Use deterministic, cheap local tools for hash, build, tests and metadata; invoke costly AI/providers for analysis, design or code changes that need them.
- Idle components should sleep without hiding actionable task, approval or fault states.

## Test/rollout acceptance

The policy is **not installed** until the trusted local GPT/Codex/INVENTHOR adapters implement automatic live handoff entry checks and checkpoint exit checks. Verify with a single cross-agent task and negative tests for stale cloud state, lost link, conflicting writer, expired lease, dependency not DONE, duplicated terminal execution and restart reconciliation. The real QA factory and Main connector are separate gated acceptance phases.
