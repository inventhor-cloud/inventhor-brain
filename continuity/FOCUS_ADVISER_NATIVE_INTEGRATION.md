# Brain owner-focus adviser: native Organizer integration

Status: SOURCE_TESTED_ONLY. Not installed or dispatched. Owner focus remains QA Factory; GPT Brain source work and Codex QA work must not overlap in mutable files.

## What was built

The new Python module continuity/focus_adviser.py is a deterministic, in-memory adviser. It neither invents Work Items nor writes to a queue, claims a lease, calls a model, signs evidence, or executes an Operator command. This avoids a duplicate Brain/Organizer.

It accepts ONE native approved plan with plan ID, revision, exact approved Work Item IDs, target, parent goal, project, capability whitelist, and an up-to-date consistent native task snapshot. The host must authenticate these inputs; a boolean supplied by any AI is NOT authentication.

The adviser proposes only existing finite TODO tasks with the correct project, target and parent; no active owner; exact allowed capability; verified DONE dependencies visible within the same native snapshot; bounded estimated steps (1..8), priority (0..3, 0 highest). It chooses lowest priority number, then shortest number of steps, then stable task ID. Missing or contradictory dependency evidence blocks the task. A new idea cannot preempt QA until the owner promotes its actual registered Work Item via the canonical Organizer.

All outputs are advisory ONLY: claim_authorized=false, can_execute_from_proposal=false, requires_fresh_native_claim=true. No selection can authorize an install or independent QA observation signature.

## Required existing .NET runtime attachment

1. Verify original owner-approved plan, exact task scope, project and capability against the canonical Organizer ledger and immutable event history.
2. Load current live tasks, dependencies, lock owners and an actual monotonic revision from one consistent native epoch. Never fabricate revision, UTC observation time, installed QA status, signer or PID.
3. Call the read-only adviser and receive one proposed exact task ID plus stable reasons.
4. Under the existing Organizer lock reread task state and expected work hash. Perform native task lease/ownership and fresh preflight-show/ack/verify before WRITE. Never rely on the Python proposal as permission.
5. Operator executes only the already-approved finite capability. Reconcile uncertain/crashed outcomes before any retry; never replay terminal jobs.
6. Persist actual evidence and completed/remaining/next-action checkpoint on the same canonical task. Release the existing lease.
7. GPT, Codex or INVENTHOR session rehydrates from fresh exact native handoff, not GitHub snapshot. QA factory live witness, release signing, UAC and rollback remain separate security gates.

This source repository has no verified Main .NET bridge, install, running native dispatcher or actual QA live outcome yet.

## Source and installed acceptance

Run python3 -m unittest discover -s tests -v and tools/verify_reference_freshness.py for source checks. Installation acceptance requires one owner-authorized PAUSED plan, two independent finite safe tasks, a fresh native preflight and confirmed receipt/ACK plus negative checks for stale snapshot, duplicate ID, inconsistent dependencies, wrong target, foreign worker, exhausted budget, resume after crash and terminal replay. Any missing native gate means no automated dispatch, no READY/QA PASS claim.

Treat GitHub PR #6 as source-level review, not live deployment. Do not alter Codex QA/Studio workspaces or share secrets in this public repository.
