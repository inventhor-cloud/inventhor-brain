# Cleanup Policy

INVENTHOR can report unused, broken, duplicated, outdated, unsafe or resource-heavy modules. A detection is **not** permission to delete or replace an installed component.

## Safe classification

1. **Current and verified** — preserve, do not rebuild or duplicate.
2. **Source-only or fixture-tested** — retain as development work; do not report as live-installed.
3. **Historical cloud reference / stale generated view** — label as non-authoritative and redirect to current canonical source; preserve history.
4. **Idle but valid** — sleep or defer work, with a documented wake condition. Retain task/health events while sleeping.
5. **Suspected duplicate** — compare canonical target, owner, hashes, dependencies and live usage before proposing merge; never merge by name alone.
6. **Damaged or unsafe** — quarantine only through an existing approved mechanism with evidence, isolation scope and recovery path.

## Procedure

- Use existing Main/Organizer/Operator registries; do not build another task store or second Brain.
- Begin with a bounded read-only inventory: installed version, signatures, active leases, module dependents, task ownership and health.
- Write a **proposed** change list with exact paths, scope, affected dependents, before/after hashes, risk and rollback plan.
- Deterministic tests first; check conflicts with active work. In particular, Brain cleanup cannot preempt an active QA Factory/Operator release task or modify its files.
- For safe reversible states, existing authorized mechanisms may mark inactive, place into sleep, or request quarantine. New release, service restart, certificate enrollment, UAC and permanent deletion have their separate approvals.
- After a change, verify system services, canonical task handoff, queue integrity, last-known-good and changed module hashes. On failed verification revert or stop with a clear blocker.
- Never infer that CI or source tests mean live installation or QA certification.

## Hard stops

Never automatically remove: canonical task/event history; production keys; owner content; trusted installers/rollback backups; installed signed binaries; live queue leases; active code worktrees; or the only copy of evidence. Any permanent deletion requires explicit owner approval and tested recovery path.

## Idle / performance goal

Unused modules should sleep, while the thin Main/Operator health path remains responsive. Detect idle by proven runtime usage (not just static import counts), preserve dependency wake-up, and record resource savings only from actual measurements.

This is public Brain policy only; it does not activate a PC cleanup operation.
