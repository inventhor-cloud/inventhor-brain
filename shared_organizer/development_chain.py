"""Bounded self-development chain advisor for the EXISTING INVENTHOR Main.

A verified completion can unblock its registered dependent Work Items. Main
still chooses/leases work using the canonical Organizer. This module only
filters an immutable, revision-pinned *view* and proposes one cheap next step.

No auto-generated projects/tasks, background process, payment, code execution,
self-modification, retry storm, deployment or claimed runtime attestation.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import re

from .agent_learning import review_agent_lessons
from .board import advise_next_work, _queue_rows

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_HEX64 = re.compile(r"[0-9a-fA-F]{64}\Z")
_TERMINAL = frozenset(("DONE", "BS"))
_ACTIVE = frozenset(("READY", "QUEUED", "CHECKPOINTED", "WAITING_PROVIDER"))


def _id(v: object) -> bool:
    return isinstance(v, str) and _ID.fullmatch(v) is not None


def _time(v: object) -> datetime | None:
    if not isinstance(v, str):
        return None
    try:
        t = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except (ValueError, OverflowError):
        return None


def review_development_chain(projects: object, queue: object, settings: object,
                             quality_report: object, agent_report: object, *,
                             candidate_agent: str, active_leases: object,
                             host_snapshot_revision: str, host_time_iso: str,
                             project_id: str | None = None,
                             handoffs: list[Mapping] | None = None) -> dict:
    """Suggest at most one next canonical work item based on verified prerequisites.

    Settings are an owner-adjustable Main-snapshot policy *reference*, never
    permission to spend, install or take a task. Only Main host can atomically
    update settings, acquire scope leases and schedule approved execution.
    """
    def response(status: str, reason: str = "", candidate: dict | None = None,
                 diagnostics: list[dict] | None = None,
                 learning: list[dict] | None = None,
                 budget: dict | None = None) -> dict:
        return {
            "status": status, "reason": reason,
            "candidate": candidate, "diagnostics": diagnostics or [],
            "learning_suggestions": learning or [],
            "budget": budget or {},
            "state": "SOURCE_REFERENCE_ONLY",
            "may_execute": False, "may_claim_task": False,
            "may_create_task": False, "may_install": False,
            "may_spend_money": False, "may_mark_done": False,
            "requires_main_snapshot_attestation": True,
            "requires_main_atomic_lease": True,
            "requires_quality_evidence_verification": True,
        }

    if (not isinstance(projects, list) or not isinstance(queue, Mapping)
        or not isinstance(settings, Mapping) or not isinstance(quality_report, Mapping)
        or not _id(candidate_agent) or not _id(host_snapshot_revision)
        or (project_id is not None and not _id(project_id))
        or not isinstance(active_leases, list)):
        return response("BLOCKED", "INVALID_CHAIN_INPUT")
    now = _time(host_time_iso)
    queue_time = _time(queue.get("captured_at"))
    if (now is None or queue_time is None or
        not -5 <= (now-queue_time).total_seconds() <= 120 or
        queue.get("snapshot_revision") != host_snapshot_revision):
        return response("BLOCKED", "STALE_OR_UNPINNED_MAIN_QUEUE")
    if (type(settings.get("schema_version")) is not int
        or settings.get("schema_version") != 1
        or settings.get("source") != "INVENTHOR_MAIN_SETTINGS"
        or settings.get("snapshot_revision") != host_snapshot_revision
        or type(settings.get("enabled")) is not bool):
        return response("BLOCKED", "INVALID_OWNER_DEVELOPMENT_SETTINGS")

    integer_limits = {
        "max_steps_per_cycle": (1, 32),
        "steps_remaining_today": (0, 10000),
        "max_parallel_tasks": (1, 32),
        "active_tasks": (0, 10000),
        "max_changed_files_per_step": (1, 256),
        "provider_budget_units_remaining": (0, 1000000),
    }
    if any(type(settings.get(k)) is not int or not low <= settings[k] <= high
           for k, (low, high) in integer_limits.items()):
        return response("BLOCKED", "INVALID_OWNER_DEVELOPMENT_LIMITS")
    if type(settings.get("paid_providers_enabled")) is not bool:
        return response("BLOCKED", "INVALID_PROVIDER_BUDGET_POLICY")
    limit = min(settings["max_steps_per_cycle"], settings["steps_remaining_today"])
    budget = {
        "steps_available_this_cycle": limit,
        "max_parallel_tasks": settings["max_parallel_tasks"],
        "active_tasks": settings["active_tasks"],
        "max_changed_files_per_step": settings["max_changed_files_per_step"],
        "paid_providers_enabled": settings["paid_providers_enabled"],
        "provider_budget_units_remaining": settings["provider_budget_units_remaining"],
    }
    if not settings["enabled"]:
        return response("PAUSED", "OWNER_DISABLED_SELF_DEVELOPMENT", budget=budget)
    if not limit:
        return response("PAUSED", "OWNER_STEP_LIMIT_REACHED", budget=budget)
    if settings["active_tasks"] >= settings["max_parallel_tasks"]:
        return response("PAUSED", "OWNER_PARALLEL_LIMIT_REACHED", budget=budget)

    if (type(quality_report.get("schema_version")) is not int or
        quality_report.get("schema_version") != 1 or
        quality_report.get("source") != "INVENTHOR_QUALITY_FACTORY" or
        quality_report.get("snapshot_revision") != host_snapshot_revision
        or not isinstance(quality_report.get("verified_tasks"), list)
        or len(quality_report["verified_tasks"]) > 512):
        return response("BLOCKED", "INVALID_QUALITY_FACTORY_REPORT", budget=budget)
    q_seen: set[tuple[str, str]] = set()
    for record in quality_report["verified_tasks"]:
        if (not isinstance(record, Mapping)
            or not _id(record.get("project_id")) or not _id(record.get("task_id"))
            or not _id(record.get("evidence_ref"))
            or record.get("result") != "VERIFIED_DONE"):
            return response("BLOCKED", "INVALID_COMPLETION_EVIDENCE", budget=budget)
        key = (record["project_id"], record["task_id"])
        if key in q_seen:
            return response("BLOCKED", "DUPLICATE_COMPLETION_EVIDENCE", budget=budget)
        q_seen.add(key)

    lessons = review_agent_lessons(
        agent_report, host_snapshot_revision=host_snapshot_revision,
        host_time_iso=host_time_iso, project_id=project_id, max_lessons=16,
    )
    if lessons["status"] != "LESSONS_REVIEW_READY":
        return response("BLOCKED", "AGENT_EVIDENCE_" + lessons["reason"], budget=budget)

    try:
        rows = _queue_rows(queue)
    except ValueError as ex:
        return response("BLOCKED", "UNTRUSTED_CANONICAL_WORK_QUEUE",
                        diagnostics=[{"reason": str(ex)}], budget=budget)
    by_key = {(r["project_id"], r.get("task_id", r.get("id"))): r for r in rows}
    diagnostics: list[dict] = []
    def report(tid: str, reason: str) -> None:
        if len(diagnostics) < 64:
            diagnostics.append({"task_id": tid, "reason": reason})

    # Stale shared title/fingerprint and already completed work are not replayed.
    completed_fps: set[tuple[str, str]] = set()
    active_fps: dict[tuple[str, str], list[str]] = {}
    for r in rows:
        pid, tid = r["project_id"], r.get("task_id", r.get("id"))
        fp = r.get("work_fingerprint")
        if fp is not None and (not isinstance(fp, str) or not _HEX64.fullmatch(fp)):
            return response("BLOCKED", "INVALID_WORK_FINGERPRINT", budget=budget)
        if fp:
            key = (pid, fp.lower())
            if r.get("state") in _TERMINAL:
                completed_fps.add(key)
            elif r.get("state") in _ACTIVE:
                active_fps.setdefault(key, []).append(tid)

    holds = {(row["project_id"], row["failure_fingerprint"]): row
             for row in lessons["lessons"]
             if row["next_action"] == "HOLD_IDENTICAL_RETRY_AND_DIAGNOSE"}
    reuse = {(row["project_id"], row["failure_fingerprint"]): row
             for row in lessons["lessons"]
             if row["verified_recovery_evidence_ref"]}
    shadow_rows: list[dict] = []
    for r in rows:
        copy = dict(r)
        pid, tid = r["project_id"], r.get("task_id", r.get("id"))
        if r.get("state") not in _ACTIVE:
            shadow_rows.append(copy)
            continue
        dependency = r.get("depends_on", [])
        # The canonical adviser also performs dependency and scope checks.
        if isinstance(dependency, list):
            unverified_done = [
                dep for dep in dependency
                if isinstance(dep, str)
                and (pid, dep) in by_key
                and by_key[(pid, dep)].get("state") in _TERMINAL
                and (pid, dep) not in q_seen
            ]
            if unverified_done:
                copy["state"] = "WAITING_DEPENDENCY"
                report(tid, "COMPLETED_DEPENDENCY_LACKS_QUALITY_EVIDENCE")
        fp = r.get("work_fingerprint")
        if fp and (pid, fp.lower()) in completed_fps:
            copy["state"] = "WAITING_REVIEW"
            report(tid, "EXISTING_COMPLETED_WORK_FINGERPRINT")
        elif fp and len(active_fps.get((pid, fp.lower()), [])) > 1:
            copy["state"] = "WAITING_REVIEW"
            report(tid, "DUPLICATE_ACTIVE_WORK_FINGERPRINT")
        failure = r.get("last_failure_fingerprint")
        if failure is not None:
            if not isinstance(failure, str) or not _HEX64.fullmatch(failure):
                return response("BLOCKED", "INVALID_FAILURE_FINGERPRINT", budget=budget)
            if (pid, failure.lower()) in holds:
                copy["state"] = "WAITING_REVIEW"
                report(tid, "HOLD_REPEATED_AGENT_FAILURE")
        # Provider cost refers to a host-recorded plan estimate, not price
        # speculation. No cost or unknown estimate => use cheap local steps.
        cost = r.get("estimated_provider_cost_units", 0)
        if type(cost) is not int or cost < 0:
            return response("BLOCKED", "INVALID_PROVIDER_COST_ESTIMATE", budget=budget)
        if cost and not settings["paid_providers_enabled"]:
            copy["state"] = "WAITING_PROVIDER"
            report(tid, "PAID_PROVIDER_DISABLED_BY_OWNER")
        elif cost > settings["provider_budget_units_remaining"]:
            copy["state"] = "WAITING_PROVIDER"
            report(tid, "OWNER_PROVIDER_BUDGET_EXCEEDED")
        files = r.get("estimated_changed_files", 1)
        if type(files) is not int or files < 0:
            return response("BLOCKED", "INVALID_CHANGE_SIZE_ESTIMATE", budget=budget)
        if files > settings["max_changed_files_per_step"]:
            copy["state"] = "WAITING_REVIEW"
            report(tid, "SPLIT_STEP_TO_OWNER_FILE_LIMIT")
        shadow_rows.append(copy)

    shadow_queue = dict(queue)
    shadow_queue["work_items"] = shadow_rows
    advice = advise_next_work(
        projects=projects, queue=shadow_queue, candidate_agent=candidate_agent,
        active_leases=active_leases, host_snapshot_revision=host_snapshot_revision,
        host_time_iso=host_time_iso, project_id=project_id, handoffs=handoffs,
    )
    diagnostics.extend(advice.get("diagnostics", [])[:max(0, 64-len(diagnostics))])
    if advice["status"] != "HOST_LEASE_REQUIRED":
        return response("NO_SAFE_STEP", advice["status"], diagnostics=diagnostics,
                        learning=lessons["lessons"], budget=budget)
    choice = dict(advice["candidate"])
    task = by_key[(choice["project_id"], choice["task_id"])]
    failure = task.get("last_failure_fingerprint")
    related = reuse.get((choice["project_id"], failure.lower())) if failure else None
    choice["learning_evidence_ref"] = (
        related["verified_recovery_evidence_ref"] if related else None)
    choice["max_changed_files_per_step"] = settings["max_changed_files_per_step"]
    choice["chain_mode"] = "SINGLE_FINITE_HOST_LEASE_CANDIDATE"
    return response("NEXT_DEVELOPMENT_STEP_ADVISORY",
                    "MAIN_HOST_MUST_REVALIDATE_AND_ACQUIRE_LEASE",
                    candidate=choice, diagnostics=diagnostics,
                    learning=lessons["lessons"], budget=budget)
