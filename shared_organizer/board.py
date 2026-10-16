"""Read-only shared Organizer projection and advisory scope-conflict checks.

Canonical authority stays with INVENTHOR Main/WorkOrganizer. A GitHub replica,
agent message, snapshot, or lease string is NOT authenticated task ownership.
No executor, second task queue, lock service or autonomous agent is created.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import re

BUCKETS = ("IDEAS", "TODO", "IN_PROGRESS", "REVIEW", "DONE")
_IN_PROGRESS = frozenset((
    "RUNNING", "CHECKPOINTED", "INTERRUPTED", "WAITING_PROVIDER",
    "WAITING_NETWORK", "BLOCKED", "RETRY_SCHEDULED", "FAILED"))
_REVIEW = frozenset(("SOURCE_TESTED", "REVIEW_PENDING",
                     "WAITING_REVIEW", "VERIFICATION_PENDING"))
_DONE = frozenset(("DONE", "BS"))
_TERMINAL_NO_REPLAY = _DONE | frozenset((
    "BF", "FAILED_TERMINAL", "DEAD_LETTER", "MERGED", "SUPERSEDED"))
_ACTIVE_LEASE = frozenset(("LEASED", "RUNNING", "REVIEWING"))


def _ident(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= 256


def _references(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [v for v in values[:32] if _ident(v)]


def _bucket(state: str) -> str:
    if state in ("IDEA", "IDEA_POOL"):
        return "IDEAS"
    if state in _DONE:
        return "DONE"
    if state in _REVIEW:
        return "REVIEW"
    if state in _IN_PROGRESS or state in ("BF", "DEAD_LETTER", "FAILED_TERMINAL"):
        return "IN_PROGRESS"
    return "TODO"


def _time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def _valid_scope(value: object) -> bool:
    if not _ident(value) or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return False
    if value.startswith("module:"):
        return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value[7:]) is not None
    if value.startswith("path:"):
        sub = value[5:]
        return (bool(sub) and not sub.startswith("/") and
                "\\" not in sub and ":" not in sub and "//" not in sub and
                all(part not in ("", ".", "..") and
                    part == part.strip() and not part.endswith(".")
                    for part in sub.split("/")))
    return False


def _scope_conflict(one: str, two: str) -> bool:
    """Fail closed for module-vs-path until canonical Inventory maps both.

    Windows filesystem and Operator module identity compare case-insensitively.
    A false positive is safer than simultaneous writes to the same object.
    """
    if one.casefold() == two.casefold():
        return True
    if one.startswith("path:") and two.startswith("path:"):
        a, b = one[5:].casefold(), two[5:].casefold()
        return a.startswith(b + "/") or b.startswith(a + "/")
    if ((one.startswith("module:") and two.startswith("path:")) or
        (one.startswith("path:") and two.startswith("module:"))):
        return True  # Unknown module directory mapping: ask Main/Inventory.
    return False


def _queue_rows(queue: Mapping) -> list[Mapping]:
    if queue.get("schema_version") != 1 or queue.get("system_of_record") != "INVENTHOR_MAIN":
        raise ValueError("UNTRUSTED_QUEUE_SCHEMA")
    rows = queue.get("work_items")
    if not isinstance(rows, list):
        raise ValueError("MISSING_WORK_ITEMS")
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping) or not _ident(row.get("project_id")):
            raise ValueError("INVALID_WORK_ITEM")
        task_id = row.get("task_id", row.get("id"))
        if not _ident(task_id):
            raise ValueError("MISSING_TASK_ID")
        key = (row["project_id"], task_id)
        if key in seen:
            raise ValueError("DUPLICATE_CANONICAL_TASK")
        seen.add(key)
    return rows


def view(projects: list[Mapping], queue: Mapping,
         handoffs: list[Mapping] | None = None,
         leases: list[Mapping] | None = None,
         ideas: list[Mapping] | None = None) -> dict:
    """Project-by-project, detailed-on-demand projection. Never asserts runtime truth."""
    if not isinstance(projects, list) or not isinstance(queue, Mapping):
        raise ValueError("INVALID_PROJECTION_INPUT")
    rows = _queue_rows(queue)
    latest: dict[tuple[str, str], Mapping] = {}
    for packet in handoffs or []:
        if not isinstance(packet, Mapping):
            raise ValueError("INVALID_HANDOFF")
        key = (packet.get("project_id"), packet.get("task_id"))
        if all(_ident(k) for k in key):
            if key not in latest or str(packet.get("created_at", "")) > str(latest[key].get("created_at", "")):
                latest[key] = packet
    seen_projects = set()
    output = []
    for project in projects:
        if not isinstance(project, Mapping) or not _ident(project.get("project_id")):
            raise ValueError("INVALID_PROJECT")
        pid = project["project_id"]
        if pid in seen_projects:
            raise ValueError("DUPLICATE_PROJECT")
        seen_projects.add(pid)
        groups: dict[str, list] = {name: [] for name in BUCKETS}
        for task in rows:
            if task["project_id"] != pid:
                continue
            task_id = task.get("task_id", task.get("id"))
            packet = latest.get((pid, task_id), {})
            state = str(task.get("state", "UNKNOWN"))
            assignees = [p for p in (leases or []) if
                         isinstance(p, Mapping) and p.get("project_id") == pid and
                         p.get("task_id") == task_id and p.get("status") in _ACTIVE_LEASE]
            groups[_bucket(state)].append({
                "task_id": task_id, "title": task.get("title", ""),
                "state": state, "priority": task.get("priority", ""),
                "assignment_evidence": "UNVERIFIED_REFERENCE",
                "assigned_agents": sorted({a.get("agent_id") for a in assignees
                                           if _ident(a.get("agent_id"))}),
                "active_scopes": sorted({scope for a in assignees
                                        for scope in _references(a.get("scope_keys"))}),
                "last_handoff_at": packet.get("created_at"),
                "next_action": packet.get("next_action", packet.get("next_task", "")),
                "blockers": _references(packet.get("blockers")),
                "evidence_refs": _references(packet.get("evidence_refs")),
                "do_not_repeat": _references(packet.get("do_not_repeat")),
                "review_required_by": packet.get("review_required_by"),
                "handoff_id": packet.get("handoff_id"),
            })
        for idea in ideas or []:
            if isinstance(idea, Mapping) and idea.get("project_id") == pid:
                groups["IDEAS"].append({
                    "idea_id": idea.get("idea_id", idea.get("id")),
                    "title": idea.get("title", ""), "state": "IDEA_POOL"})
        output.append({
            "project_id": pid, "title": project.get("title", ""),
            "objective": project.get("objective", ""),
            "architecture": project.get("architecture", {}),
            "module_refs": _references(project.get("module_refs", [])),
            "source_repositories": project.get("source_repositories", {}),
            "rules_refs": _references(project.get("rules_refs", [])),
            "target_outcome": project.get("acceptance_definition", ""),
            "buckets": groups,
            "counts": {k: len(v) for k, v in groups.items()},
        })
    unregistered = sorted({r["project_id"] for r in rows if r["project_id"] not in seen_projects})
    return {"state": "SOURCE_REFERENCE_ONLY", "may_execute": False,
            "system_of_record": "INVENTHOR_MAIN", "projects": output,
            "unregistered_project_ids": unregistered}


def assess_takeover(task: Mapping, candidate_agent: str, desired_scopes: list[str],
                    active_leases: list[Mapping], host_snapshot_revision: str,
                    host_time_iso: str) -> dict:
    """Advice to host. Even a clear lane requires atomic host lease compare-and-swap."""
    def result(decision: str, reason: str, conflicts: list[str] | None = None) -> dict:
        return {"decision": decision, "reason": reason,
                "conflicting_agents": conflicts or [],
                "may_execute": False, "may_take_ownership": False,
                "requires_host_atomic_lease": True,
                "evidence_level": "SOURCE_REFERENCE_ONLY"}

    if (not isinstance(task, Mapping) or not _ident(task.get("project_id")) or
        not _ident(task.get("task_id", task.get("id"))) or not _ident(candidate_agent) or
        not _ident(host_snapshot_revision) or not isinstance(desired_scopes, list) or
        not desired_scopes or any(not _valid_scope(s) for s in desired_scopes)):
        return result("BLOCKED", "INVALID_IDENTITY_OR_SCOPE")
    if len(desired_scopes) != len(set(desired_scopes)):
        return result("BLOCKED", "DUPLICATE_SCOPE")
    state = task.get("state")
    if state in _TERMINAL_NO_REPLAY:
        return result("BLOCKED", "TERMINAL_TASK_REPLAY")
    if state not in ("READY", "QUEUED", "CHECKPOINTED", "WAITING_PROVIDER", "REVIEW_PENDING"):
        return result("BLOCKED", "TASK_NOT_ELIGIBLE_FOR_HANDOFF")
    timestamp = _time(host_time_iso)
    if timestamp is None:
        return result("BLOCKED", "UNVERIFIED_HOST_TIME")
    if not isinstance(active_leases, list):
        return result("BLOCKED", "LEASE_INVENTORY_MISSING")
    conflicts = []
    stale = False
    for lease in active_leases:
        if not isinstance(lease, Mapping):
            return result("BLOCKED", "MALFORMED_LEASE")
        if lease.get("status") not in _ACTIVE_LEASE:
            continue
        if lease.get("project_id") != task["project_id"]:
            continue
        if lease.get("snapshot_revision") != host_snapshot_revision:
            stale = True
            continue
        expires = _time(lease.get("expires_at"))
        if expires is None or expires <= timestamp:
            stale = True   # Never silently steal stale/expired lease.
            continue
        agent = lease.get("agent_id")
        scope_keys = lease.get("scope_keys")
        if not _ident(agent) or not isinstance(scope_keys, list) or not scope_keys:
            return result("BLOCKED", "MALFORMED_LEASE")
        if any(not _valid_scope(s) for s in scope_keys):
            return result("BLOCKED", "INVALID_LEASE_SCOPE")
        if agent != candidate_agent and any(
            _scope_conflict(requested, occupied)
            for requested in desired_scopes for occupied in scope_keys
        ):
            conflicts.append(agent)
        if lease.get("task_id") == task.get("task_id", task.get("id")) and agent != candidate_agent:
            conflicts.append(agent)
    if stale:
        return result("BLOCKED", "STALE_OR_EXPIRED_LEASE_REQUIRES_HOST_RECONCILIATION")
    if conflicts:
        return result("CONFLICT", "ANOTHER_AGENT_OWNS_OVERLAPPING_WORK",
                      sorted(set(conflicts)))
    return result("HOST_LEASE_REQUIRED", "ATOMIC_OWNER_LEASE_AND_POLICY_CHECK_REQUIRED")


VISIBLE_EVENTS = frozenset({
    "AGENT_STARTED", "SCOPE_RESERVED", "HANDOFF_READY",
    "REVIEW_REQUESTED", "WORK_BLOCKED", "PROVIDER_UNAVAILABLE",
    "TASK_VERIFICATION_FAILED", "TASK_VERIFIED_BY_HOST"
})


def event_inbox(events: list[Mapping], project_id: str,
                seen_event_ids: set[str] | None = None) -> dict:
    """Build UI notification *candidates* from trusted Main Event Log references.

    No push channel, background worker, email or notification permission is created.
    Do not treat self-declared host verification as trusted proof.
    """
    if not isinstance(events, list) or not _ident(project_id):
        raise ValueError("EVENT_INPUT_INVALID")
    already = seen_event_ids or set()
    output = []
    observed = set()
    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("EVENT_ROW_INVALID")
        event_id = event.get("event_id")
        kind = event.get("kind")
        task_id = event.get("task_id")
        if event.get("project_id") != project_id or kind not in VISIBLE_EVENTS:
            continue
        if not _ident(event_id) or not _ident(task_id):
            raise ValueError("EVENT_IDENTITY_MISSING")
        if event_id in already or event_id in observed:
            continue
        observed.add(event_id)
        output.append({
            "event_id": event_id, "project_id": project_id, "task_id": task_id,
            "kind": kind, "agent_id": event.get("agent_id"),
            "scope_keys": [s for s in _references(event.get("scope_keys"))
                           if _valid_scope(s)],
            "evidence_ref": event.get("evidence_ref") if _ident(
                event.get("evidence_ref")) else None,
            "source": "UNATTESTED_EVENT_REFERENCE",
        })
    return {"events": output, "dispatch_authorized": False,
            "state": "SOURCE_REFERENCE_ONLY"}
