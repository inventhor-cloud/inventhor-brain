"""Read-only, bounded next-step adviser for the existing INVENTHOR Organizer.

No database, queue writer, provider invocation, lease, signing or dispatcher.
All inputs must be projected by a trusted Main/Organizer host from a fresh
native snapshot. The proposed choice is NEVER an execution authorization.
New ideas cannot preempt the owner-authorized focus task.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

MAX_TASKS = 64
MAX_DEPENDENCIES = 24
MAX_AGE = timedelta(seconds=60)
STATES = frozenset({"TODO", "DOING", "BLOCKED", "DONE", "VERIFY", "IDEA", "ARCHIVED"})


class FocusDenied(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class FocusEnvelope:
    """Snapshot identifiers are trusted only after *native* host validation."""
    plan_id: str
    project_id: str
    focus_task_id: str
    target_id: str
    plan_revision: int
    observed_at: datetime
    authorized_work_ids: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class StepProposal:
    task_id: str
    target_id: str
    plan_id: str
    plan_revision: int
    reasons: tuple[str, ...]
    requires_fresh_native_claim: bool = True
    can_execute_from_proposal: bool = False


@dataclass(frozen=True)
class Advisory:
    focus_task_id: str
    plan_id: str
    next_step: StepProposal | None
    deferred: tuple[tuple[str, str], ...]
    disposition: str
    claim_authorized: bool = False


def _identity(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise FocusDenied("INVALID_" + label)
    if not all(c.isascii() and (c.isalnum() or c in "_-.") for c in value):
        raise FocusDenied("UNSAFE_" + label)
    return value


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise FocusDenied("TIMESTAMP_MUST_BE_AWARE")
    return value.astimezone(timezone.utc)


def propose_next(
    envelope: FocusEnvelope,
    tasks: Sequence[Mapping[str, Any]],
    *,
    now: datetime,
    native_snapshot_verified: bool,
) -> Advisory:
    """Choose an existing, finite, explicitly preauthorized candidate.

    The trusted caller must independently verify the envelope, exact native
    ledger snapshot and owner policy. Passing native_snapshot_verified=True
    in an AI-produced call does NOT grant authority: all output is read-only.
    """
    if not native_snapshot_verified:
        raise FocusDenied("NATIVE_SNAPSHOT_REQUIRED")
    if not isinstance(envelope, FocusEnvelope):
        raise FocusDenied("FOCUS_ENVELOPE_REQUIRED")
    for key in ("plan_id", "project_id", "focus_task_id", "target_id"):
        _identity(getattr(envelope, key), key.upper())
    if type(envelope.plan_revision) is not int or envelope.plan_revision < 1:
        raise FocusDenied("INVALID_PLAN_REVISION")
    current = _aware(now)
    observed = _aware(envelope.observed_at)
    if observed > current + timedelta(seconds=5) or current - observed > MAX_AGE:
        raise FocusDenied("STALE_FOCUS_SNAPSHOT")
    if not isinstance(tasks, (list, tuple)) or len(tasks) > MAX_TASKS:
        raise FocusDenied("TASK_SET_TOO_LARGE")
    allowed = envelope.authorized_work_ids
    capabilities = envelope.allowed_capabilities
    if not isinstance(allowed, tuple) or not allowed or len(allowed) > MAX_TASKS:
        raise FocusDenied("EXPLICIT_WORK_IDS_REQUIRED")
    if not isinstance(capabilities, tuple) or not capabilities or len(capabilities) > 24:
        raise FocusDenied("EXPLICIT_CAPABILITIES_REQUIRED")
    ids = [_identity(x, "AUTHORIZED_WORK_ID") for x in allowed]
    caps = [_identity(x, "CAPABILITY") for x in capabilities]
    if len(set(ids)) != len(ids) or len(set(caps)) != len(caps):
        raise FocusDenied("DUPLICATE_POLICY_ENTRY")

    # Duplicate task IDs make the whole native projection ambiguous.
    index: dict[str, Mapping[str, Any]] = {}
    for item in tasks:
        if not isinstance(item, Mapping):
            raise FocusDenied("INVALID_TASK_RECORD")
        task_id = _identity(item.get("task_id"), "TASK_ID")
        if task_id in index:
            raise FocusDenied("DUPLICATE_TASK_ID")
        index[task_id] = item

    ready = []
    deferred = []
    for task_id in ids:
        item = index.get(task_id)
        if item is None:
            deferred.append((task_id, "NOT_IN_LIVE_SNAPSHOT"))
            continue
        if (item.get("project_id") != envelope.project_id
            or item.get("target_id") != envelope.target_id
            or item.get("parent_id") != envelope.focus_task_id):
            deferred.append((task_id, "OUTSIDE_OWNER_FOCUS"))
            continue
        state = item.get("state")
        if state not in STATES:
            raise FocusDenied("UNKNOWN_TASK_STATE")
        if state != "TODO":
            deferred.append((task_id, "NOT_READY_STATE_" + state))
            continue
        if item.get("task_kind") != "TASK":
            deferred.append((task_id, "NOT_FINITE_TASK"))
            continue
        owner = item.get("active_worker")
        if owner not in (None, ""):
            deferred.append((task_id, "OWNER_OR_LEASE_PRESENT"))
            continue
        if item.get("capability") not in caps:
            deferred.append((task_id, "CAPABILITY_NOT_IN_APPROVED_PLAN"))
            continue
        deps = item.get("dependencies")
        if not isinstance(deps, list) or len(deps) > MAX_DEPENDENCIES:
            deferred.append((task_id, "DEPENDENCY_PROOF_MISSING"))
            continue
        missing = False
        seen_deps = set()
        for dep in deps:
            if not isinstance(dep, Mapping):
                missing = True
                break
            dep_id = dep.get("task_id")
            if not isinstance(dep_id, str) or dep_id in seen_deps:
                missing = True
                break
            seen_deps.add(dep_id)
            # Native host must verify the dependency evidence, not a provider.
            if index.get(dep_id, {}).get("state") != "DONE":
                missing = True
        if missing:
            deferred.append((task_id, "DEPENDENCY_NOT_CONFIRMED_DONE"))
            continue
        priority, steps = item.get("priority"), item.get("estimated_steps")
        if type(priority) is not int or priority not in (0, 1, 2, 3):
            deferred.append((task_id, "PRIORITY_NOT_VALIDATED"))
            continue
        if type(steps) is not int or not 1 <= steps <= 8:
            deferred.append((task_id, "UNBOUNDED_STEPS"))
            continue
        # No capability grants are inferred from an LLM or source description.
        ready.append((priority, steps, task_id))
    ready.sort(key=lambda r: (r[0], r[1], r[2]))
    choice = None
    if ready:
        priority, steps, task_id = ready[0]
        choice = StepProposal(
            task_id, envelope.target_id, envelope.plan_id,
            envelope.plan_revision,
            (f"OWNER_PLAN_EXPLICIT_WORK_ID", f"PRIORITY_{priority}",
             f"FINITE_STEPS_{steps}", "DEPENDENCIES_DONE_IN_SNAPSHOT",
             "MUST_RECHECK_NATIVE_LEASE_AND_PREFLIGHT"),
        )
    return Advisory(
        envelope.focus_task_id, envelope.plan_id, choice, tuple(deferred),
        "READ_ONLY_CANDIDATE_ONLY" if choice else "NO_AUTHORIZED_READY_WORK",
    )
