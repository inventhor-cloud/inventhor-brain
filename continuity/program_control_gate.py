"""Source-only program autonomy preflight for the ONE INVENTHOR Brain/Operator.

Legacy user-facing modules become independent real programs, not embedded
modules. Each program exposes its own versioned, explicit capabilities. This
validator never signs, grants permissions, gets a lease or executes commands:
the installed native host must attest program/owner/Organizer facts itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_ALLOWED_RISK = frozenset({"SAFE_REVERSIBLE", "OWNER_GATE_REQUIRED"})
MAX_CAPABILITIES = 64
MAX_AGE = timedelta(seconds=60)


class ProgramControlDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ProgramContext:
    program_id: str
    program_version: str
    program_runtime: str  # REAL_RUNNING, STOPPED, UNKNOWN
    bridge_connected: bool
    document_id: str
    document_revision: int
    opened_project_id: str
    native_task_id: str
    native_task_revision: int
    observed_at: datetime
    published_capabilities: tuple[str, ...]
    owner_allowed_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class ProgramActionAdvisory:
    program_id: str
    document_revision: int
    native_task_id: str
    native_task_revision: int
    requested_capability: str
    disposition: str
    reason: str
    origin: str = "SOURCE_ONLY_PROGRAM_ACTION_PROPOSAL_NOT_EXECUTION"
    native_context_authenticated: bool = False
    owner_permission_authenticated: bool = False
    owner_approval_granted: bool = False
    lease_claimed: bool = False
    program_changed: bool = False
    can_dispatch: bool = False


def _id(v: object, what: str) -> str:
    if not isinstance(v, str) or not _ID.fullmatch(v):
        raise ProgramControlDenied("INVALID_" + what)
    return v


def _bool(v: object, what: str) -> bool:
    if type(v) is not bool:
        raise ProgramControlDenied("INVALID_" + what)
    return v


def prepare_program_action(
    context: ProgramContext, *, expected_program_id: str,
    expected_project_id: str, expected_task_id: str,
    expected_task_revision: int, requested_capability: str,
    risk: str, now: datetime,
) -> ProgramActionAdvisory:
    """Fail closed on stale/mixed program context, never dispatch from source."""
    if not isinstance(context, ProgramContext):
        raise ProgramControlDenied("PROGRAM_CONTEXT_REQUIRED")
    for field in (
        "program_id", "program_version", "document_id", "opened_project_id",
        "native_task_id",
    ):
        _id(getattr(context, field), field.upper())
    for label, val in (
        ("EXPECTED_PROGRAM_ID", expected_program_id),
        ("EXPECTED_PROJECT_ID", expected_project_id),
        ("EXPECTED_TASK_ID", expected_task_id),
        ("CAPABILITY", requested_capability),
    ):
        _id(val, label)
    for field, val in (
        ("DOCUMENT_REVISION", context.document_revision),
        ("NATIVE_TASK_REVISION", context.native_task_revision),
        ("EXPECTED_TASK_REVISION", expected_task_revision),
    ):
        if type(val) is not int or val < 1:
            raise ProgramControlDenied("INVALID_" + field)
    _bool(context.bridge_connected, "BRIDGE_CONNECTED")
    if (not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None
        or not isinstance(context.observed_at, datetime)
        or context.observed_at.tzinfo is None
        or context.observed_at.utcoffset() is None):
        raise ProgramControlDenied("AWARE_TIMESTAMPS_REQUIRED")
    observed = context.observed_at.astimezone(timezone.utc)
    current = now.astimezone(timezone.utc)
    if observed > current + timedelta(seconds=5) or current - observed > MAX_AGE:
        raise ProgramControlDenied("STALE_OR_FUTURE_PROGRAM_CONTEXT")
    if context.program_id != expected_program_id:
        raise ProgramControlDenied("WRONG_OPEN_PROGRAM")
    if context.opened_project_id != expected_project_id:
        raise ProgramControlDenied("WRONG_OPEN_PROJECT")
    if context.native_task_id != expected_task_id:
        raise ProgramControlDenied("WRONG_NATIVE_TASK")
    if context.native_task_revision != expected_task_revision:
        raise ProgramControlDenied("STALE_NATIVE_TASK_REVISION")
    if (context.program_runtime not in ("REAL_RUNNING", "STOPPED", "UNKNOWN")):
        raise ProgramControlDenied("INVALID_PROGRAM_RUNTIME")
    if (not isinstance(context.published_capabilities, tuple)
        or not isinstance(context.owner_allowed_capabilities, tuple)
        or len(context.published_capabilities) > MAX_CAPABILITIES
        or len(context.owner_allowed_capabilities) > MAX_CAPABILITIES):
        raise ProgramControlDenied("INVALID_CAPABILITY_SET")
    for caps in (context.published_capabilities, context.owner_allowed_capabilities):
        if len(caps) != len(set(caps)):
            raise ProgramControlDenied("DUPLICATE_CAPABILITIES")
        for cap in caps:
            _id(cap, "PUBLISHED_CAPABILITY")
    if risk not in _ALLOWED_RISK:
        raise ProgramControlDenied("INVALID_RISK_CLASS")

    def result(disposition: str, reason: str) -> ProgramActionAdvisory:
        return ProgramActionAdvisory(
            program_id=context.program_id,
            document_revision=context.document_revision,
            native_task_id=context.native_task_id,
            native_task_revision=context.native_task_revision,
            requested_capability=requested_capability,
            disposition=disposition,
            reason=reason,
        )

    if context.program_runtime != "REAL_RUNNING" or not context.bridge_connected:
        return result("BLOCKED", "ACTUAL_PROGRAM_BRIDGE_NOT_RUNNING")
    if requested_capability not in context.published_capabilities:
        return result("BLOCKED", "PROGRAM_CAPABILITY_NOT_EXPOSED")
    if requested_capability not in context.owner_allowed_capabilities:
        return result("BLOCKED", "OWNER_CAPABILITY_NOT_ALLOWED")
    if risk == "OWNER_GATE_REQUIRED":
        return result("BLOCKED", "FRESH_OWNER_APPROVAL_REQUIRED")
    return result(
        "NATIVE_PREFLIGHT_REQUIRED",
        "READ_NATIVE_LEASE_PERMISSIONS_AND_PROGRAM_REVISION_BEFORE_EXECUTION",
    )
