# Autonomous Execution Architecture

Status: ACTIVE
Date: 2026-09-22

## Goal

INVENTHOR must continue approved project work even when the current chat/session/provider quota ends.

The live chat is a control surface, not the runtime.

## Standard architecture terms

- System of Record (SoR): canonical project/task truth in INVENTHOR Main.
- Durable Work Queue: persisted Work Items that survive chat/provider/process restarts.
- Workflow Orchestrator: advances Work Items through a finite state machine.
- Scheduler: selects the next eligible Work Item.
- Checkpoint: durable progress boundary for resumable work.
- Provider Gateway: provider-neutral reasoning interface.
- Provider Router: selects GPT/Codex/Gemini/local/future provider by capability, quota, cost and policy.
- Quota Manager: tracks provider budget/cooldown/limits.
- Rate Limiter: prevents provider/API overuse.
- Circuit Breaker: temporarily stops failing providers/services.
- Retry Policy: bounded retries with backoff.
- Dead-Letter Queue (DLQ): terminally blocked Work Items requiring review.
- Module Registry: installed Operator capabilities/modules.
- Artifact Registry: generated builds/packages/files and hashes.
- Evidence Store: logs/tests/screenshots/results.
- Event Log / Audit Log: append-oriented state transitions.
- Sync Engine: replicates canonical state to Windows Operator/cloud.
- Local Replica: Operator-side cached execution slice.

## Core rule

INVENTHOR is the Brain.
Windows Operator is the Body.

However, the Body contains a deterministic Workflow Orchestrator so it can finish already-authorized Work Items without a live human/provider session.

The Operator does not invent new product goals. It executes queued Work Items, follows acceptance criteria, retries deterministic steps, and asks the Provider Gateway only when semantic reasoning is actually needed.

## Work Item state machine

IDEA_POOL -> BACKLOG -> READY -> QUEUED -> RUNNING -> CHECKPOINTED -> DONE

Side states:
- WAITING_PROVIDER
- WAITING_NETWORK
- WAITING_DEPENDENCY
- WAITING_APPROVAL
- BLOCKED
- RETRY_SCHEDULED
- FAILED_TERMINAL
- DEAD_LETTER
- SUPERSEDED
- MERGED

DONE always requires evidence according to policy.

## Autonomous loop

1. Sync current project slice from SoR.
2. Select the highest-priority eligible READY/QUEUED Work Item.
3. Resolve required capabilities from Module Registry.
4. Run deterministic/local steps first.
5. Persist Checkpoint after each meaningful step.
6. If reasoning is required, query Provider Gateway.
7. Provider Router selects an allowed provider using capability, quota, cost, privacy and cooldown.
8. Validate provider output before execution.
9. Execute through Windows Operator modules.
10. Store evidence/artifacts.
11. Update Event Log and Work Item state.
12. Continue with the next eligible Work Item.

The loop does not depend on an open ChatGPT conversation.

## Provider policy

Preferred order:
1. deterministic/local Operator logic
2. cached knowledge / local indexes
3. configured official provider API/connector
4. approved local model if available
5. browser/UI automation only as an explicit fallback

Never scrape or bypass provider authentication/quotas.
Provider credentials remain in a secure local/secret store and are never committed to Git or continuity records.

## Quota-aware routing

Each provider record tracks:
- capability set
- current quota/budget
- cooldown_until
- recent latency
- recent failure rate
- cost class
- privacy class
- model availability
- last successful request

Routing should use the cheapest suitable provider first, subject to quality and policy.
If one provider is exhausted or unavailable, the Work Item moves to WAITING_PROVIDER or another eligible provider is selected.

## Research/library access

Research is capability-based, not arbitrary web wandering.

Supported source classes:
- official documentation
- package registries
- source repositories
- SDK/docs indexes
- internal knowledge base
- approved web search/provider tools

Every external fact used to change code should keep source/provenance metadata where practical.

## Project/module inventory

Every project, module, plugin and artifact is registered with:
- stable ID
- version
- state
- capabilities
- dependencies
- source location
- last build/test result
- evidence references
- current owner/executor
- update timestamp

This inventory is visible in INVENTHOR Main and mirrored to Windows Operator.

## Sync

INVENTHOR Main remains the System of Record.
Windows Operator maintains a Local Replica of:
- active projects
- Work Queue
- Module Registry
- current Checkpoints
- provider availability summary
- artifact/evidence metadata

Offline work appends local events to an outbox and syncs after reconnect.

## Safety / authority

Autonomy is bounded by Access Profile and task policy.
No provider may bypass:
- authentication
- audit/evidence
- access profile
- explicit approval requirements
- protected paths/secrets
- destructive-action safeguards


## Bootstrap-to-Main migration rule

Some control features may temporarily exist on Windows Operator so development can continue before INVENTHOR Main is fully restored/imported.

Temporary Operator-side bootstrap features may include:
- temporary command entry / control surfaces
- temporary provider invocation helpers
- temporary voice-control bridge
- temporary project/resume controls
- temporary local orchestration helpers

Final ownership must move to INVENTHOR Main:

INVENTHOR Main owns:
- voice intent understanding
- natural-language command interpretation
- Provider Gateway / Provider Router / Quota Manager
- Organizer / Workflow Orchestrator / Durable Work Queue
- Project Registry / Module Registry / Idea Backlog
- System of Record / Knowledge Graph / Checkpoints / Handoff Packets
- global policy and Owner authority

Windows Operator keeps only execution-local responsibilities:
- desktop/session control
- file/process/service/system operations
- build/test/package/run
- local deterministic dedupe/fingerprint checks
- local cache/replica
- evidence/artifact collection
- offline outbox/retry/recovery

Migration principle:
Temporary bootstrap logic on Operator must be modular, removable and protocol-driven. When INVENTHOR Main gains the corresponding feature, the Operator-side bootstrap module is disabled and purged without changing the execution contract.
