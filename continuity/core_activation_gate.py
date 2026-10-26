"""Four-core activation readiness advisory for the EXISTING INVENTHOR Brain.

No queue, service, installer, cleanup module, native lease or PC side effect.
GitHub/source input is never a live attestation. A real native Main/Organizer
host must authenticate evidence separately before any deployment/activation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

# Four owner-facing systems. The ORIGINAL Organizer remains internal to INVENTHOR.
CORE = ("INVENTHOR", "OPERATOR", "STUDIO_DESIGN", "QA_FACTORY")
REQUIRED_LINKS = (
    "BRAIN_OPERATOR", "BRAIN_ORGANIZER", "OPERATOR_ORGANIZER",
    "OPERATOR_QA", "QA_ORGANIZER", "PROGRAM_ACTION_BRIDGE",
    "INVENTHOR_STUDIO", "STUDIO_OPERATOR", "STUDIO_QA",
    "STUDIO_REAL_RENDER",
)
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
MAX_AGE = timedelta(seconds=60)


class ActivationInvalid(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ComponentObservation:
    component_id: str
    state: str  # ACTIVE, INACTIVE, UNKNOWN, never auto-convert to READY
    artifact_sha256: str  # hash of alleged installed artifact, not proof
    signature_verified: bool
    rollback_verified: bool
    heartbeat_fresh: bool


@dataclass(frozen=True)
class LinkObservation:
    link_id: str
    authenticated: bool
    result_ack_verified: bool


@dataclass(frozen=True)
class CoreActivationSnapshot:
    task_id: str
    native_revision: int
    observed_at: datetime
    components: tuple[ComponentObservation, ...]
    links: tuple[LinkObservation, ...]
    active_noncore_ids: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    qa_live_witness_verified: bool


@dataclass(frozen=True)
class CoreActivationAdvice:
    disposition: str
    blockers: tuple[str, ...]
    next_action: str
    source_class: str = "FOUR_CORE_SOURCE_ADVISORY_NOT_RUNTIME_ATTESTATION"
    native_snapshot_authenticated: bool = False
    activation_executed: bool = False
    live_status_verified: bool = False
    deployment_authorized: bool = False
    deletion_authorized: bool = False


def _id(value: object, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ActivationInvalid("INVALID_" + field)
    return value


def _verified_bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise ActivationInvalid("INVALID_" + field)
    return value


def evaluate_core_activation(
    snapshot: CoreActivationSnapshot, *, now: datetime,
) -> CoreActivationAdvice:
    """Review *claimed* native facts; NEVER activate, install, delete or claim live.

    Even a fully green source projection only requests independent native host
    verification of Organizer revision, owner lease, signer and QA witness.
    """
    if not isinstance(snapshot, CoreActivationSnapshot):
        raise ActivationInvalid("SNAPSHOT_TYPE_REQUIRED")
    _id(snapshot.task_id, "TASK_ID")
    if type(snapshot.native_revision) is not int or snapshot.native_revision < 1:
        raise ActivationInvalid("INVALID_NATIVE_REVISION")
    if (not isinstance(now, datetime) or now.tzinfo is None
        or now.utcoffset() is None or not isinstance(snapshot.observed_at, datetime)
        or snapshot.observed_at.tzinfo is None
        or snapshot.observed_at.utcoffset() is None):
        raise ActivationInvalid("AWARE_TIMESTAMPS_REQUIRED")
    now_utc = now.astimezone(timezone.utc)
    observed = snapshot.observed_at.astimezone(timezone.utc)
    if observed > now_utc + timedelta(seconds=5) or now_utc - observed > MAX_AGE:
        raise ActivationInvalid("STALE_OR_FUTURE_SNAPSHOT")
    if (not isinstance(snapshot.components, tuple)
        or len(snapshot.components) > len(CORE)
        or not isinstance(snapshot.links, tuple)
        or len(snapshot.links) > len(REQUIRED_LINKS)):
        raise ActivationInvalid("BOUNDED_CORE_INPUT_REQUIRED")
    if (not isinstance(snapshot.active_noncore_ids, tuple)
        or len(snapshot.active_noncore_ids) > 64
        or not isinstance(snapshot.unresolved_conflicts, tuple)
        or len(snapshot.unresolved_conflicts) > 32):
        raise ActivationInvalid("BOUNDED_SCOPE_INPUT_REQUIRED")
    _verified_bool(snapshot.qa_live_witness_verified, "QA_WITNESS")

    component_index: dict[str, ComponentObservation] = {}
    for item in snapshot.components:
        if not isinstance(item, ComponentObservation):
            raise ActivationInvalid("INVALID_COMPONENT")
        cid = _id(item.component_id, "COMPONENT_ID")
        if cid not in CORE or cid in component_index:
            raise ActivationInvalid("UNKNOWN_OR_DUPLICATE_CORE")
        if item.state not in ("ACTIVE", "INACTIVE", "UNKNOWN"):
            raise ActivationInvalid("UNKNOWN_CORE_STATE")
        if not isinstance(item.artifact_sha256, str) or not _HASH.fullmatch(item.artifact_sha256):
            raise ActivationInvalid("INVALID_ARTIFACT_HASH")
        for field in ("signature_verified", "rollback_verified", "heartbeat_fresh"):
            _verified_bool(getattr(item, field), field.upper())
        component_index[cid] = item
    link_index: dict[str, LinkObservation] = {}
    for item in snapshot.links:
        if not isinstance(item, LinkObservation):
            raise ActivationInvalid("INVALID_LINK")
        lid = _id(item.link_id, "LINK_ID")
        if lid not in REQUIRED_LINKS or lid in link_index:
            raise ActivationInvalid("UNKNOWN_OR_DUPLICATE_LINK")
        _verified_bool(item.authenticated, "LINK_AUTH")
        _verified_bool(item.result_ack_verified, "LINK_ACK")
        link_index[lid] = item
    for part in snapshot.active_noncore_ids + snapshot.unresolved_conflicts:
        _id(part, "SCOPE_ITEM")
    if len(set(snapshot.active_noncore_ids)) != len(snapshot.active_noncore_ids):
        raise ActivationInvalid("DUPLICATE_NONCORE")
    if len(set(snapshot.unresolved_conflicts)) != len(snapshot.unresolved_conflicts):
        raise ActivationInvalid("DUPLICATE_CONFLICT")

    blockers = []
    for cid in CORE:
        component = component_index.get(cid)
        if component is None:
            blockers.append(cid + ":MISSING")
            continue
        if component.state != "ACTIVE":
            blockers.append(cid + ":NOT_ACTIVE")
        if not component.signature_verified:
            blockers.append(cid + ":SIGNER_NOT_VERIFIED")
        if not component.rollback_verified:
            blockers.append(cid + ":ROLLBACK_NOT_VERIFIED")
        if not component.heartbeat_fresh:
            blockers.append(cid + ":HEARTBEAT_NOT_FRESH")
    for lid in REQUIRED_LINKS:
        link = link_index.get(lid)
        if link is None:
            blockers.append(lid + ":MISSING")
        elif not link.authenticated or not link.result_ack_verified:
            blockers.append(lid + ":NO_AUTHENTICATED_ACK")
    if not snapshot.qa_live_witness_verified:
        blockers.append("QA:LIVE_WITNESS_MISSING")
    for module_id in snapshot.active_noncore_ids:
        blockers.append("NONCORE_ACTIVE:" + module_id)
    for conflict in snapshot.unresolved_conflicts:
        blockers.append("UNRESOLVED_CONFLICT:" + conflict)

    return CoreActivationAdvice(
        disposition="BLOCKED" if blockers else "NATIVE_REVIEW_REQUIRED",
        blockers=tuple(blockers),
        next_action=(
            "RECONCILE_NATIVE_ORGANIZER_AND_OPERATOR_BEFORE_ACTIVATION"
            if blockers else
            "VERIFY_NATIVE_HOST_PROVENANCE_LEASE_SIGNER_QA_AND_OWNER_GATES"
        ),
    )
