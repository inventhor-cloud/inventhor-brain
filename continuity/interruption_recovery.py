"""Fail-closed crash/interruption recovery adviser for the existing Organizer.

SOURCE-ONLY. It never retries, steals, claims, queues or writes anything.
No model-supplied state is sufficient: a trusted native host must verify the
exact canonical task, event/attempt history and same current revision.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Protocol

_ATTEMPTS = frozenset({
    "NONE", "PREPARED", "STARTED", "UNKNOWN",
    "CONFIRMED_FAILED", "CONFIRMED_SUCCEEDED",
})
_STATES = frozenset({"IDEA", "TODO", "DOING", "BLOCKED", "VERIFY", "DONE", "ARCHIVED"})
_MAX_AGE = timedelta(seconds=60)


class RecoveryDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class RecoverySnapshot:
    task_id: str
    project_id: str
    target_id: str
    revision: int
    state: str
    active_worker: str | None
    observed_at: datetime
    last_attempt: str
    last_attempt_id: str | None
    attempts_recorded: int
    remaining_retry_budget: int
    last_attempt_receipt_ref: str | None


class NativeRecoveryPort(Protocol):
    def read_recovery(self, task_id: str) -> RecoverySnapshot: ...
    def verify_recovery(self, task: RecoverySnapshot) -> bool: ...


@dataclass(frozen=True)
class RecoveryAdvice:
    task_id: str
    revision: int
    disposition: Literal[
        "TERMINAL_NO_REPLAY", "HOLD_ACTIVE_OWNER", "NATIVE_RECONCILIATION_REQUIRED",
        "HOLD_NOT_RUNNABLE", "FRESH_PREFLIGHT_REQUIRED",
        "NATIVE_RETRY_POLICY_RECHECK",
    ]
    reason: str
    last_attempt_id: str | None
    can_dispatch: bool = False
    can_claim: bool = False
    can_retry: bool = False
    native_reconciliation_completed: bool = False


def _str(value: str | None, label: str, *, required: bool = True) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value or len(value) > 128:
        raise RecoveryDenied("INVALID_" + label)
    if not all(c.isascii() and (c.isalnum() or c in "._-") for c in value):
        raise RecoveryDenied("UNSAFE_" + label)
    return value


def _clock(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise RecoveryDenied("INVALID_" + label)
    return value.astimezone(timezone.utc)


def advise_recovery(
    host: NativeRecoveryPort,
    task_id: str,
    *,
    now: datetime,
    expected_project: str,
    expected_target: str,
    expected_revision: int,
) -> RecoveryAdvice:
    """Recommend one safe outcome; no retries ever occur in this function."""
    _str(task_id, "TASK_ID")
    _str(expected_project, "PROJECT_ID")
    _str(expected_target, "TARGET_ID")
    if type(expected_revision) is not int or expected_revision < 1:
        raise RecoveryDenied("INVALID_EXPECTED_REVISION")
    current = _clock(now, "NOW")
    try:
        fact = host.read_recovery(task_id)
    except Exception as e:
        raise RecoveryDenied("NATIVE_RECOVERY_READ_UNAVAILABLE") from e
    if not isinstance(fact, RecoverySnapshot):
        raise RecoveryDenied("RECOVERY_SNAPSHOT_INVALID")
    try:
        valid = host.verify_recovery(fact)
    except Exception as e:
        raise RecoveryDenied("NATIVE_RECOVERY_PROVENANCE_ERROR") from e
    if valid is not True:
        raise RecoveryDenied("UNTRUSTED_RECOVERY_PROVENANCE")
    if (fact.task_id != task_id or fact.project_id != expected_project
        or fact.target_id != expected_target):
        raise RecoveryDenied("RECOVERY_SCOPE_MISMATCH")
    if type(fact.revision) is not int or fact.revision != expected_revision:
        raise RecoveryDenied("RECOVERY_REVISION_CHANGED")
    observed = _clock(fact.observed_at, "OBSERVED_AT")
    if observed > current + timedelta(seconds=5) or current - observed > _MAX_AGE:
        raise RecoveryDenied("RECOVERY_SNAPSHOT_STALE_OR_FUTURE")
    if fact.state not in _STATES:
        raise RecoveryDenied("UNKNOWN_TASK_STATE")
    _str(fact.active_worker, "ACTIVE_WORKER", required=False)
    if fact.last_attempt not in _ATTEMPTS:
        raise RecoveryDenied("UNKNOWN_ATTEMPT_STATUS")
    if (type(fact.attempts_recorded) is not int
        or not 0 <= fact.attempts_recorded <= 100000):
        raise RecoveryDenied("ATTEMPTS_INVALID")
    if (type(fact.remaining_retry_budget) is not int
        or not 0 <= fact.remaining_retry_budget <= 8):
        raise RecoveryDenied("RETRY_BUDGET_INVALID")
    _str(fact.last_attempt_id, "ATTEMPT_ID", required=False)
    _str(fact.last_attempt_receipt_ref, "RECEIPT_REF", required=False)
    if fact.last_attempt == "NONE":
        if (fact.attempts_recorded != 0 or fact.last_attempt_id is not None
            or fact.last_attempt_receipt_ref is not None):
            raise RecoveryDenied("CONTRADICTORY_NO_ATTEMPT_HISTORY")
    elif fact.attempts_recorded == 0 or fact.last_attempt_id is None:
        raise RecoveryDenied("MISSING_ATTEMPT_HISTORY")
    if (fact.last_attempt in ("CONFIRMED_FAILED", "CONFIRMED_SUCCEEDED")
        and not fact.last_attempt_receipt_ref):
        # Confirmation must have at least a native host-verifiable receipt.
        raise RecoveryDenied("CONFIRMED_ATTEMPT_WITHOUT_RECEIPT")
    if fact.last_attempt in ("PREPARED", "STARTED", "UNKNOWN"):
        if fact.last_attempt_receipt_ref is not None:
            # Do not accept a forged "receipt" for an unconfirmed attempt.
            raise RecoveryDenied("UNCONFIRMED_ATTEMPT_RECEIPT_CONTRADICTION")

    def result(disposition: str, reason: str) -> RecoveryAdvice:
        return RecoveryAdvice(
            task_id=task_id, revision=fact.revision, disposition=disposition,
            reason=reason, last_attempt_id=fact.last_attempt_id,
        )

    if fact.state in ("DONE", "ARCHIVED"):
        return result("TERMINAL_NO_REPLAY", "TASK_ALREADY_TERMINAL")
    if fact.active_worker is not None:
        return result("HOLD_ACTIVE_OWNER", "ACTIVE_OR_UNKNOWN_NATIVE_LEASE")
    if fact.state == "DOING":
        return result("NATIVE_RECONCILIATION_REQUIRED", "ORPHAN_RUNNING_TASK")
    if fact.state != "TODO":
        return result("HOLD_NOT_RUNNABLE", "TASK_STATE_NOT_ELIGIBLE")
    if fact.last_attempt in ("PREPARED", "STARTED", "UNKNOWN", "CONFIRMED_SUCCEEDED"):
        return result("NATIVE_RECONCILIATION_REQUIRED", "ATTEMPT_OUTCOME_UNRESOLVED")
    if fact.last_attempt == "CONFIRMED_FAILED":
        if fact.remaining_retry_budget == 0:
            return result("HOLD_NOT_RUNNABLE", "RETRY_BUDGET_EXHAUSTED")
        return result("NATIVE_RETRY_POLICY_RECHECK", "CONFIRMED_FAILURE_NEEDS_NATIVE_RETRY_GATE")
    return result("FRESH_PREFLIGHT_REQUIRED", "NO_PRIOR_EXECUTION_ATTEMPT")
