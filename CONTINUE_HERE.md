# Continue Here

STATUS=CONTINUITY_SYSTEM_ACTIVE
LAST_VERIFIED=2026-09-22

SYSTEM_OF_RECORD=INVENTHOR_MAIN
EXECUTION_REPLICA=WINDOWS_OPERATOR
CLOUD_ROLE=SYNCED_REPLICA
PROVIDER_CHAT_ROLE=NON_CANONICAL_CONTEXT

ACTIVE_PROJECT=WINDOWS_OPERATOR_P0_UNATTENDED
NEXT_TASK=Finish Windows Operator V2.3 CI/deploy path, then verify Session Agent and unattended execution on WINDOWS-INVENTHOR.

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
