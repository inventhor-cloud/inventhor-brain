"""Provider-neutral live handoff gate, source-only (NOT installed runtime).

The only authority is a trusted local Organizer adapter. No cloud queue, new
Brain, background worker, installer, or signed QA acceptance is created here.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Mapping, Protocol

SOURCE = "CANONICAL_WORK_ITEMS_AND_EVENTS_READ_ONLY"
STATES = frozenset({"IDEA", "TODO", "DOING", "BLOCKED", "VERIFY", "DONE", "ARCHIVED"})
MAX_ITEMS = 24

class HandoffDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

@dataclass(frozen=True)
class LeaseAdmission:
    """Host result only. Never send native lease tokens to provider context."""
    accepted: bool
    task_id: str
    target_id: str
    revision: int
    owner: str
    expires_at: datetime | None

class LiveTaskPort(Protocol):
    """Must be implemented by owner-authorized native .NET host.

    The port, not an AI response, must independently verify provenance,
    acquire the real task lease with atomic revision comparison, and perform
    Organizer's existing preflight/ack/verify sequence.
    """
    def read_exact(self, task_id: str) -> Mapping[str, Any]: ...
    def verify_read_provenance(self, record: Mapping[str, Any]) -> bool: ...
    def claim_if_unchanged(self, *, task_id: str, target_id: str,
                           revision: int, worker: str) -> LeaseAdmission: ...

@dataclass(frozen=True)
class ResumePacket:
    task_id: str
    project_id: str
    target_id: str
    revision: int
    state: str
    stage: str
    completed: tuple[str, ...]
    remaining: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    blocker: str
    next_action: str
    observed_at: datetime
    mode: Literal["READ_ONLY", "WRITE_CLAIMED"]

@dataclass(frozen=True)
class CheckpointDraft:
    """Proposed fields, NOT a persisted checkpoint or QA approval."""
    task_id: str
    expected_revision: int
    completed: tuple[str, ...]
    remaining: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    stage: str
    next_action: str

def _text(obj: Mapping[str, Any], key: str) -> str:
    v = obj.get(key)
    if not isinstance(v, str) or not v.strip() or len(v) > 1024:
        raise HandoffDenied("INVALID_" + key.upper())
    return v.strip()

def _items(obj: Mapping[str, Any], key: str) -> tuple[str, ...]:
    values = obj.get(key)
    if not isinstance(values, list) or len(values) > MAX_ITEMS:
        raise HandoffDenied("INVALID_" + key.upper())
    if any(not isinstance(x, str) or not x.strip() or len(x) > 480 for x in values):
        raise HandoffDenied("INVALID_" + key.upper())
    return tuple(x.strip() for x in values)

def _time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise HandoffDenied("INVALID_OBSERVED_TIME")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HandoffDenied("INVALID_OBSERVED_TIME") from exc
    if t.tzinfo is None or t.utcoffset() is None:
        raise HandoffDenied("UNZONED_OBSERVED_TIME")
    return t.astimezone(timezone.utc)

def resume(port: LiveTaskPort, task_id: str, *, now: datetime,
           worker: str, expected_target: str, write: bool = False,
           max_age: timedelta = timedelta(seconds=60)) -> ResumePacket:
    """Read current canonical task; request native lease only for writes.

    Any missing native provenance, revision, dependency or ownership fact
    fails closed. Source/fixture success is not an installed or live QA pass.
    """
    if any(not isinstance(s, str) or not s or len(s) > 128
           for s in (task_id, worker, expected_target)):
        raise HandoffDenied("INVALID_IDENTITY")
    if now.tzinfo is None or now.utcoffset() is None:
        raise HandoffDenied("NOW_UNZONED")
    if max_age <= timedelta(0) or max_age > timedelta(minutes=5):
        raise HandoffDenied("INVALID_MAX_AGE")
    raw = port.read_exact(task_id)
    if not isinstance(raw, Mapping) or not port.verify_read_provenance(raw):
        raise HandoffDenied("UNTRUSTED_LIVE_RESPONSE")
    if raw.get("source") != SOURCE:
        raise HandoffDenied("NON_CANONICAL_SOURCE")
    if _text(raw, "task_id") != task_id:
        raise HandoffDenied("TASK_MISMATCH")
    project = _text(raw, "project_id")
    target = _text(raw, "target_id")
    if target != expected_target:
        raise HandoffDenied("TARGET_MISMATCH")
    revision = raw.get("revision")
    if type(revision) is not int or revision < 1:
        raise HandoffDenied("REVISION_REQUIRED")
    observed = _time(raw.get("observed_at"))
    current = now.astimezone(timezone.utc)
    if observed > current + timedelta(seconds=5):
        raise HandoffDenied("FUTURE_HANDOFF")
    if current - observed > max_age:
        raise HandoffDenied("STALE_HANDOFF")
    state = _text(raw, "state")
    if state not in STATES:
        raise HandoffDenied("UNKNOWN_STATE")
    completed = _items(raw, "completed")
    remaining = _items(raw, "remaining")
    evidence = _items(raw, "evidence_refs")
    stage, blocker, next_action = (raw.get("stage", ""), raw.get("blocker", ""),
                                    raw.get("next_action", ""))
    if any(not isinstance(s, str) or len(s) > 1024
           for s in (stage, blocker, next_action)):
        raise HandoffDenied("INVALID_DETAIL")
    mode: Literal["READ_ONLY", "WRITE_CLAIMED"] = "READ_ONLY"
    if write:
        if state not in ("TODO", "DOING"):
            raise HandoffDenied("NOT_WRITABLE_STATE")
        deps = raw.get("dependencies")
        if not isinstance(deps, list) or len(deps) > MAX_ITEMS:
            raise HandoffDenied("DEPENDENCIES_MISSING_OR_INVALID")
        seen = set()
        for dep in deps:
            if not isinstance(dep, dict):
                raise HandoffDenied("INVALID_DEPENDENCY")
            dep_id = _text(dep, "task_id")
            if dep_id in seen:
                raise HandoffDenied("DUPLICATE_DEPENDENCY")
            seen.add(dep_id)
            if dep.get("state") != "DONE":
                raise HandoffDenied("DEPENDENCY_NOT_DONE")
        # Even an expired-looking lease must go through native reconciliation.
        if raw.get("active_worker") not in (None, ""):
            raise HandoffDenied("LEASE_REQUIRES_RECONCILIATION")
        if not remaining or not next_action.strip():
            raise HandoffDenied("NO_EXPLICIT_REMAINING_WORK")
        lease = port.claim_if_unchanged(task_id=task_id, target_id=target,
                                        revision=revision, worker=worker)
        if not isinstance(lease, LeaseAdmission) or not lease.accepted:
            raise HandoffDenied("NATIVE_CLAIM_DENIED")
        if (lease.task_id != task_id or lease.target_id != target
            or lease.revision != revision or lease.owner != worker):
            raise HandoffDenied("NATIVE_CLAIM_MISMATCH")
        if (lease.expires_at is None or lease.expires_at.tzinfo is None
            or lease.expires_at <= current):
            raise HandoffDenied("NATIVE_CLAIM_EXPIRED")
        mode = "WRITE_CLAIMED"
    return ResumePacket(task_id, project, target, revision, state, stage,
                        completed, remaining, evidence, blocker,
                        next_action.strip(), observed, mode)

def draft_next_checkpoint(claimed: ResumePacket, *,
                          verified_completed: list[str],
                          still_remaining: list[str],
                          evidence_refs: list[str],
                          stage: str, next_action: str) -> CheckpointDraft:
    """Form strict delta only; owner runtime must commit/release separately."""
    if claimed.mode != "WRITE_CLAIMED":
        raise HandoffDenied("HANDOFF_WITHOUT_NATIVE_CLAIM")
    completed = _items({"completed": verified_completed}, "completed")
    remaining = _items({"remaining": still_remaining}, "remaining")
    refs = _items({"evidence_refs": evidence_refs}, "evidence_refs")
    if not completed or not refs:
        raise HandoffDenied("HANDOFF_EVIDENCE_REQUIRED")
    if not remaining or not isinstance(next_action, str) or not next_action.strip():
        raise HandoffDenied("HANDOFF_CONTINUATION_REQUIRED")
    if not isinstance(stage, str) or not stage.strip() or len(stage) > 128:
        raise HandoffDenied("HANDOFF_STAGE_REQUIRED")
    if "LIVE_QA_VERIFIED" in stage or "SIGNED_RELEASED" in stage:
        raise HandoffDenied("TRUSTED_RELEASE_GATE_REQUIRED")
    return CheckpointDraft(claimed.task_id, claimed.revision, completed,
                           remaining, refs, stage, next_action.strip())
