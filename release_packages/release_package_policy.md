# Release Package Policy

Every approved central brain improvement should become a user-facing update with a short changelog and one update button.

## Canonical storage and verification boundary

The requested one-click update is a **future UI feature**, not permission to deploy arbitrary GitHub content. See `continuity/ARTIFACT_STORAGE_ARCHITECTURE_V1.md`.

Main Organizer is the system of record for Artifact Registry **metadata**; existing source repos remain source repositories; Windows Operator may download, stage and verify immutable module/application packages under a host-approved, storage-validated root (proposed D: archive). Actual installed status is host attested, not inferred from source builds.

Before any install: verify PROJECT_ID / MODULE_ID, dependency compatibility, target device, pinned source revision, file SHA-256, release acceptance evidence, trusted publisher, access policy, disk space, backup/rollback and explicit Owner approval when required. On failure, preserve old version and return evidence. Never silently remove source, user files or old backups. Never upload private family data or secrets as generic release assets.

`continuity/artifact_registry.source.json` is an empty **source example**, not the live installed module database. `shared_organizer/artifacts.py` is a read-only manifest preflight and never grants release/install authority.
