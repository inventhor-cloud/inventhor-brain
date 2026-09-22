# INVENTHOR Continuity System

Purpose: let a new chat, a different AI/provider, or a restarted Brain continue work without rebuilding context from scratch.

The canonical continuity record lives in INVENTHOR, not inside any provider conversation.

## Read order for every new AI/session

1. `continuity/continuity_manifest.json`
2. the active project records listed by that manifest
3. `continuity/idea_pool.json`
4. the latest project evidence / ledger references
5. only then choose the next finite task

## Write rule

After a meaningful architecture decision, completed task, blocker, or change of next task, update the relevant project record and manifest.

Do not copy entire chat transcripts into continuity state. Store compact structured facts, decisions, evidence references, blockers and next actions.

## Provider-neutral rule

GPT, Codex, Gemini or another future provider receives the same resume packet. Provider-specific chat history is optional context, never canonical project truth.

## Operator rule

Windows Operator is execution-only. It may mirror current task state and evidence locally for resilience, but INVENTHOR continuity remains canonical.


## Standard software vocabulary

Use the names in `STANDARD_TERMINOLOGY.md`: System of Record, Project Registry, Work Item Backlog, Work Queue, Event Log, Checkpoint, Handoff Packet, Architecture Decision Record, Artifact Registry, Evidence Store, Local Replica and Replication.

## Replication

INVENTHOR Main is the System of Record. Windows Operator is an execution Local Replica. Cloud may hold a synchronized replica for cross-device/provider continuity. Provider chats are never canonical state.

The existing INVENTHOR Main desktop backup is a bootstrap source and must be inventoried read-only before import.
