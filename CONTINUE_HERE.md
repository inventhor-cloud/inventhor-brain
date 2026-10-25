# Continue Here

**IMPORTANT (2026-10-22):** These are public cloud reference files, not live local work authority. The operator and Main may have newer installed state; see [live source/freshness gate](continuity/LIVE_SOURCE_FRESHNESS_GATE.md) and obtain exact task-scoped handoff from the owner-authorized canonical Organizer before any write, status claim or restart. The earlier project/next task noted below is historical, not the current priority. Default: new ideas go to intake without interrupting active QA or separately scoped Brain housekeeping. No new providers are in the immediate GPT/Codex/INVENTHOR roster.


STATUS=REFERENCE_ONLY_LIVE_TASK_RECHECK_REQUIRED
LAST_CLOUD_REFERENCE_VERIFIED=2026-09-22
CURRENT_RUNTIME_VERIFIED=NO

SYSTEM_OF_RECORD=INVENTHOR_MAIN
EXECUTION_REPLICA=WINDOWS_OPERATOR
CLOUD_ROLE=SYNCED_REPLICA
PROVIDER_CHAT_ROLE=NON_CANONICAL_CONTEXT

HISTORICAL_ACTIVE_PROJECT_20260922=WINDOWS_OPERATOR_P0_UNATTENDED
HISTORICAL_NEXT_TASK_20260922=Finish Windows Operator V2.3 CI/deploy path, then verify Session Agent and unattended execution on WINDOWS-INVENTHOR.

BOOTSTRAP_SOURCE=The current INVENTHOR Main System exists only in a Desktop backup package on WINDOWS-INVENTHOR. Inventory and hash it read-only before importing anything.

READ_FIRST:
1. continuity/continuity_manifest.json
2. continuity/STANDARD_TERMINOLOGY.md
3. continuity/SYSTEM_OF_RECORD_AND_REPLICATION.md
4. continuity/active_projects/WINDOWS_OPERATOR_P0_UNATTENDED.json
5. continuity/idea_pool.json
6. latest Handoff Packet / Checkpoint / Event Log references

DO_NOT_REPEAT:
- Android Operator development
- rebuilding project context from chat history
- treating CI_PASS as LOCAL_DEPLOYED
- treating provider conversation as canonical project truth

Any new AI/provider must resume from the System of Record and select exactly one finite eligible Work Item.

## OWNER CORE-ACTIVATION DIRECTION — 2026-10-25

ACTIVE_SCOPE=INVENTHOR_BRAIN,OPERATOR,ORGANIZER,QA_FACTORY
OTHER_MODULES=DEFERRED_FUTURE_SEPARATE_PROJECTS_NOT_AUTO_ACTIVATED
OWNER_EXPERIENCE=Actual program opens; single small movable INVENTHOR voice/text assistant in the program; authorized Operator edits the real program, user may take over; Organizer tracks work and QA Factory tests.
SOURCE_ACTIVATION_CHECK=continuity/core_activation_gate.py
SOURCE_ACTIVATION_TEST=tests/test_core_activation_gate.py
CURRENT_SOURCE_TEST=GitHub Actions 40223408469 success at commit 84cd3b0c6e2d7a4e259ed0071237e2d74458b5c7 (SOURCE ONLY)
ACTIVATION_LIMIT=This source-only gate cannot activate installed code, grant a native lease, sign a release, or attest live QA. Never claim activation from this mirror.
KNOWN_NATIVE_BLOCKERS=Last reported QA Factory 0.5.0 installed / 0.7 draft, 17 Operator PR#3 versus local conflicts with Cleanup locally deleted, Main/Operator native ACK not proven, signing/rollback witness pending. Native Organizer must be freshly read to verify whether these are still current.
NEXT_NATIVE_STEP=Trusted Main/Organizer owner/lease check, classify deployed core versus deferred modules, reconcile Operator conflict, verify exact signed artifacts/rollback/handshake and QA acceptance, then owner-gated progressive activation. No blind merge/deletion/restore or duplicate modules. DC low quota/offline is not a Brain runtime state.

## FOUR-CORE COMPOSED BRAIN REVIEW — 2026-10-25

SOURCE=continuity/core_brain_review.py
TEST=tests/test_core_brain_review.py
FUNCTION=prepare_core_brain_review
INPUT=Exact native Organizer handoff + independently trusted Main context host + one claimed CoreActivationSnapshot + exact task/revision/time.
OUTPUT=CoreBrainReview: current task and finite safe advisory + four-core activation blockers in one bounded read-only object.
SAFETY=Never dispatch/claim/install/delete. Even zero reported blockers => NATIVE_REVIEW_REQUIRED, not activated. Does not authenticate arbitrary caller's activation facts. Must not be used as a security ticket.
NATIVE_HOST_GAP=Real Main must collect, authenticate and reconcile same-epoch installed evidence for all four components; verify native owner/lease, signatures, artifact hashes, Operator result ACK, QA witness and rollback. Native Composer/real-program command execution is separately gated.
SCOPE=Four-core integration only; no new module, queue, factory, voice provider or app.
