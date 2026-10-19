"""Parallel lane proposals for the existing Main Organizer; never a scheduler.

Reuses advise_next_work's dependency, priority, snapshot, handoff and lease
checks. Independently prunes overlapping candidates, including shared physical
paths across registered project boundaries, without manufacturing leases.
"""
from __future__ import annotations

from collections.abc import Mapping

from .board import (
    _ident, _queue_rows, _scope_conflict, _valid_scope,
    advise_next_work,
)

_ACTIVE = frozenset({"LEASED", "RUNNING", "REVIEWING"})


def advise_parallel_lanes(
    projects: object, queue: object, settings: object, *,
    candidate_agent: str, active_leases: object,
    host_snapshot_revision: str, host_time_iso: str,
    project_id: str | None = None,
    handoffs: list[Mapping] | None = None,
) -> dict:
    """Propose disjoint existing tasks, each requiring its OWN Main CAS lease."""
    def answer(status: str, proposals: list[dict] | None = None,
               diagnostics: list[dict] | None = None) -> dict:
        return {
            "status": status,
            "proposals": proposals or [],
            "diagnostics": (diagnostics or [])[:32],
            "state": "SOURCE_REFERENCE_ONLY",
            "may_execute": False,
            "may_claim_task": False,
            "may_create_task": False,
            "may_spend_money": False,
            "requires_main_snapshot_attestation": True,
            "requires_independent_atomic_lease_per_task": True,
        }

    if (not isinstance(projects, list) or not isinstance(queue, Mapping)
        or not isinstance(settings, Mapping) or not isinstance(active_leases, list)
        or not _ident(candidate_agent) or not _ident(host_snapshot_revision)
        or (project_id is not None and not _ident(project_id))):
        return answer("INVALID_INPUT")
    if (type(settings.get("schema_version")) is not int
        or settings.get("schema_version") != 1
        or settings.get("source") != "INVENTHOR_MAIN_SETTINGS"
        or settings.get("snapshot_revision") != host_snapshot_revision
        or type(settings.get("enabled")) is not bool):
        return answer("UNTRUSTED_OWNER_SETTINGS")
    limits = {
        "max_parallel_tasks": (1, 32), "active_tasks": (0, 10000),
        "max_steps_per_cycle": (1, 32),
        "steps_remaining_today": (0, 10000),
    }
    if any(type(settings.get(k)) is not int or
           not low <= settings[k] <= high for k, (low, high) in limits.items()):
        return answer("INVALID_OWNER_LIMITS")
    if not settings["enabled"]:
        return answer("OWNER_PAUSED")
    available = min(
        settings["max_parallel_tasks"] - settings["active_tasks"],
        settings["max_steps_per_cycle"],
        settings["steps_remaining_today"],
    )
    if available <= 0:
        return answer("OWNER_BUDGET_OR_PARALLEL_LIMIT")

    try:
        rows = _queue_rows(queue)
    except ValueError:
        return answer("UNTRUSTED_CANONICAL_QUEUE")
    if len(rows) > 2048 or len(active_leases) > 512:
        return answer("BOUNDED_WORK_VIEW_REQUIRED")
    for lease in active_leases:
        if not isinstance(lease, Mapping):
            return answer("MALFORMED_LEASE_INVENTORY")
        if lease.get("status") not in _ACTIVE:
            continue
        scopes = lease.get("scope_keys")
        if not _ident(lease.get("project_id")) or not isinstance(scopes, list) or (
            not scopes or len(scopes) > 64 or
            any(not _valid_scope(scope) for scope in scopes)
        ):
            return answer("MALFORMED_LEASE_INVENTORY")

    remaining = list(rows)
    proposed: list[dict] = []
    used: list[tuple[str, list[str]]] = []
    diagnostics: list[dict] = []
    for _ in range(available):
        permitted: list[Mapping] = []
        for task in remaining:
            pid, scopes = task["project_id"], task.get("scope_keys")
            if not isinstance(scopes, list) or not scopes or (
                len(scopes) > 64 or any(not _valid_scope(s) for s in scopes)
            ):
                permitted.append(task)  # Existing single-lane validator rejects it.
                continue
            # Physical scope collisions cannot be made safe by different
            # project IDs; no foreign title, agent or path is disclosed.
            selected_conflict = any(
                any(_scope_conflict(s, used_scope) for s in scopes
                    for used_scope in prior_scopes)
                for _, prior_scopes in used
            )
            foreign_lease_conflict = any(
                lease.get("status") in _ACTIVE
                and lease.get("project_id") != pid
                and any(_scope_conflict(s, held) for s in scopes
                        for held in lease["scope_keys"])
                for lease in active_leases
            )
            if selected_conflict or foreign_lease_conflict:
                if len(diagnostics) < 32:
                    diagnostics.append({
                        "task_id": task.get("task_id", task.get("id")),
                        "reason": ("CONCURRENT_SCOPE_PROPOSAL_CONFLICT"
                                   if selected_conflict else
                                   "CROSS_PROJECT_SCOPE_LEASE_REQUIRES_MAIN_REVIEW"),
                    })
                continue
            permitted.append(task)

        filtered = dict(queue)
        filtered["work_items"] = permitted
        decision = advise_next_work(
            projects, filtered, candidate_agent, active_leases,
            host_snapshot_revision, host_time_iso,
            project_id=project_id, handoffs=handoffs,
        )
        if decision["status"] != "HOST_LEASE_REQUIRED":
            if not proposed:
                return answer(decision["status"], diagnostics=(
                    diagnostics + decision.get("diagnostics", [])
                ))
            break
        candidate = decision["candidate"]
        pid, tid = candidate["project_id"], candidate["task_id"]
        proposed.append(candidate)
        used.append((pid, candidate["scope_keys"]))
        remaining = [t for t in remaining if
                     (t["project_id"], t.get("task_id", t.get("id"))) != (pid, tid)]
    return answer("HOST_MULTI_LEASE_REVIEW_REQUIRED", proposed, diagnostics)
