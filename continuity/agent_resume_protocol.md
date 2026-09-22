# Agent Resume Protocol

Every new chat/provider/session must treat INVENTHOR continuity as the canonical state source.

## On start

Read the continuity manifest, then all ACTIVE/P0 project state records.

Build a compact internal resume packet containing only:
- architecture decisions
- completed/verified facts
- implemented-but-not-verified facts
- blockers
- current next task
- acceptance criteria
- relevant evidence/source references
- idea pool items only when they affect the current task

Do not ask the user to repeat information already present in canonical continuity.

## On execution

Choose one finite next task whose prerequisites are satisfied.
Prefer Operator/local execution for builds, tests, scans, packaging, file operations and repetitive work.
Use expensive AI/provider reasoning only for decisions, architecture, review or problems that Operator cannot solve deterministically.

## On handoff

Before ending a meaningful work session, write a handoff record containing:
- project_id
- from_agent/provider
- current state
- what changed
- evidence references
- blockers
- exact next task
- do_not_repeat
- unresolved decisions

The next provider continues from that handoff rather than replaying the full history.

## Truth rules

REQUESTED is not DONE.
SOURCE_IMPLEMENTED is not RUNTIME_VERIFIED.
CI_PASS is not LOCAL_DEPLOYED.
LOCAL_DEPLOYED is not END_TO_END_CONNECTED.
DONE requires project-specific evidence.
