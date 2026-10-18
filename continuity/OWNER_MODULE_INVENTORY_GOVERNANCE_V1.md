# INVENTHOR Brain — Owner-Directed Open Module Governance / Inventory V1

**18 October 2026 — SOURCE_IMPLEMENTED / NOT LOCAL_DEPLOYED.**

INVENTHOR is a user-controlled modular assistant. Its owner decides which apps, modules, providers, languages, device features and capabilities the product should support. This Brain-side module planner implements **no hardcoded whitelist or arbitrary product-category prohibition**. The owner may describe a new module or expand an existing one. The system should show constraints and evidence, not silently override the owner's product decisions.

## One brain; one canonical registry

This work extends **the existing INVENTHOR Main + Organizer**. No second inventory authority, scheduler, project, task manager or unbounded background agent is introduced. Canonical Main's live registry and per-project boundaries remain the system of record. GitHub `module_catalog.json`, `continuity/work_queue.json` and this source code are source snapshots/reference materials, **not** live Windows host state.

A Main-host-invoked function may consume, subject to project access permission, current canonical module declarations and Windows Operator observations:

- `shared_organizer.inventory.review_module_inventory(catalog, observations, host_snapshot_revision, host_time_iso, project_id)` detects 100% vs partial declared capability coverage, missing modules, unexpected capabilities, ambiguous capability ownership, stale claims, unpinned snapshots and unregistered observations.
- `shared_organizer.owner_modules.review_owner_module_request(request, catalog, host_snapshot_revision, host_time_iso)` accepts owner-requested custom modules, without vendor/category whitelists. It identifies existing canonical module IDs before proposing duplicates, detects same-project capability overlaps and supplies an explicit user-configurable routing review.
- Data schemas are bounded and deterministic to avoid parser errors and accidental writes. Names/IDs are canonical interface identifiers; formats are technical interoperability checks, **not** app-category restrictions.
- `REPORTED_COMPLETE` means **all declared capabilities have a host-supplied PASS+evidence reference**, not that the source, executable, actual permission, integration or test results have been independently authenticated. The Quality Factory must verify each evidence reference before calling functionality `LIVE_VERIFIED`.

## Owner product authority vs execution safety

The owner has the final say on product features, extension modules, app support, UI and provider choices. The Brain must not invent prohibitions or substitute the assistant's product preferences. Requested behaviors are mapped to available implementations, not unconditionally assumed impossible because a module is new.

A bare `requester_role=OWNER` field does not authenticate the caller. Actual installation, file writes, Windows system privileges, secrets, the privacy/consent of other persons, irreversible operations, valid package integrity, conflict-free live leases and backup/rollback remain independently checked by the trusted host. This separates **owner product choices** from the truth of whether a particular operation is currently supported and authorized.

The source planner does **not** change Windows security configuration, disable OS policy, grant access to others' files, sign packages, deploy software, bypass Organizer active leases, or perform covert background actions. If a concrete module cannot be installed yet, it reports what integration/runtime prerequisite is missing and lets the owner decide the next product direction; it must not pretend installation was completed.

## Minimum on-device integration acceptance

1. Map each Owner request to the **existing** Main project and Organizer work item, or ask for explicit project choice only if genuinely unresolved. Do not create duplicate projects or replay completed tasks.
2. Read a newly attested Main/Operator module/capability snapshot pinned to the same host revision, show missing/partial/unverified capabilities, and keep unrelated project identities and private user memory isolated.
3. Detect mixed/ambiguous capability ownership. Allow user-chosen dispatch priority through trusted Main configuration; do not silently pick a random module.
4. Require verified evidence from a full capability test (UI, logic, service, dependencies and runtime behavior) before reporting `LIVE_VERIFIED`; report `SOURCE_TESTED` separately.
5. Allow owner-defined new module categories and capabilities even when absent from current `module_catalog.json`; avoid static vendor/provider/category allowlists.
6. Preserve current installed release, backups, and rollback until signed and attested install/health gates are finished; never interpret the source advisory as a deployment permission.
7. Keep provider-token costs low: capability matching and basic inventory audits are deterministic/local; AI is reserved for ambiguous interpretation and owner-requested reasoning.

## Source tests

`tests/test_module_inventory.py` verifies partial coverage, stale/unverified observations, duplicate data and route collisions. `tests/test_owner_modules.py` verifies unlimited product-category choices, project isolation, non-duplicating extensions, explicit routing ambiguity and lack of unilateral host authority. CI uses Python stdlib and no paid provider.

These are **source acceptance tests**, not confirmation that the Owner's installed INVENTHOR Brain/Windows Operator currently invokes these functions. Integration must be performed by the authorized current Main host after Code Review, atomic task/scope lease validation and UI/runtime acceptance. The existing Desktop/Service update task remains separate.
