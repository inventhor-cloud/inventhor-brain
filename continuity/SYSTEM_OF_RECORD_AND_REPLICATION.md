# System of Record and Replication Architecture

## Canonical model

INVENTHOR Main System is the System of Record (SoR).

Canonical datasets:
- Project Registry
- Project State
- Work Item Backlog
- Ready / Work Queue
- Event Log / Audit Log
- Architecture Decision Records
- Idea Backlog
- Artifact Registry metadata
- Evidence Store metadata
- Checkpoints
- Handoff Packets

## Windows Operator replica

Windows Operator receives only the execution-relevant slice of the SoR:
- current task
- required project context
- capability policy
- acceptance criteria
- artifact/evidence destinations
- current revision / epoch

Operator writes back:
- state transitions
- execution evidence
- artifacts
- failures/blockers
- checkpoints
- resource/health data

The Operator may cache these records locally so work survives temporary disconnection.

## Cloud replica

A cloud replica may mirror the SoR for continuity between devices and AI providers.

Recommended behavior:
- version every record
- keep immutable event/audit history
- encrypt private project data at rest
- never sync local pairing keys or machine secrets
- use optimistic concurrency/version checks
- resolve conflicts using revision/epoch ownership, not last-writer-wins alone
- allow read-only provider resume packets to be generated from cloud state

## Bootstrap from existing desktop backup

Current INVENTHOR Main System source/runtime backup is known to exist only in a Desktop backup package on the Windows PC.

That package is a bootstrap source, not yet canonical until imported and inventoried.

Bootstrap process:
1. Session Agent resolves the real interactive-user Desktop.
2. Operator inventories the backup package without modifying it.
3. Create a hash manifest and read-only snapshot.
4. Extract/import project architecture, Organizer/task state, modules and configuration into a staging workspace.
5. Map legacy names to the standard terminology in STANDARD_TERMINOLOGY.md.
6. Build the Project Registry and initial Event Log.
7. Validate before promoting imported state to the INVENTHOR SoR.
8. Keep the original Desktop backup untouched until the new SoR is verified.

## Provider resume flow

New chat/provider:
1. read System of Record index
2. read active Project State
3. read latest Checkpoint/Handoff Packet
4. read relevant ADRs
5. read Ready Queue
6. continue the first eligible work item

This avoids replaying long chat history and reduces provider-token usage.
