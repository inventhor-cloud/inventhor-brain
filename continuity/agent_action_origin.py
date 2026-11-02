"""Non-impersonating action-origin proposals for GPT, Codex and INVENTHOR.

Source-only protection. Actual authorization and the true author of a message
can be established ONLY by the owner-controlled native Main/Organizer host.
Never infer that text appearing in ChatGPT came from this module.
No chat UI automation, API request, ledger mutation or session launch here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Callable, Literal


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_AGENT = frozenset({"GPT", "CODEX", "INVENTHOR"})
_ACTION = frozenset({"TASK_CONTEXT_READ", "CHECKPOINT_DRAFT", "TASK_ADVICE"})
_ALLOWED_TARGET = "INTERNAL_ORGANIZER"
_MAX_SKEW = timedelta(seconds=10)
_MAX_AGE = timedelta(seconds=60)


class OriginDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class NativeActorContext:
    """Opaque native-host assertion; not an authorization token by itself."""
    task_id: str
    plan_id: str
    plan_revision: int
    actor_agent: str
    worker_id: str
    session_id: str
    observed_at: datetime
    expires_at: datetime
    native_evidence_ref: str


@dataclass(frozen=True)
class ActionOriginProposal:
    task_id: str
    plan_id: str
    plan_revision: int
    actor_agent: str
    worker_id: str
    session_id: str
    action: str
    destination: str
    observed_at: str
    native_evidence_ref: str
    fingerprint: str
    # This must never claim that an automated agent equals the human owner.
    origin: Literal["AUTOMATED_AGENT"] = "AUTOMATED_AGENT"
    impersonates_owner: bool = False
    is_executed: bool = False
    may_send_chat_message: bool = False
    is_native_receipt: bool = False

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))


def _id(value: str, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise OriginDenied("INVALID_" + field)
    return value


def _time(t: datetime, field: str) -> datetime:
    if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() is None:
        raise OriginDenied("INVALID_" + field)
    return t.astimezone(timezone.utc)


def prepare_origin(
    proof: NativeActorContext,
    *,
    action: str,
    destination: str,
    now: datetime,
    verify_host_context: Callable[[NativeActorContext], bool],
) -> ActionOriginProposal:
    """Return an auditable *unexecuted* internal action proposal.

    The callable MUST be provided by a trusted native host whose authority
    cannot be replaced by an LLM or a GitHub JSON value. A True return
    indicates only proof provenance verification. It is not execution consent
    or approval to send external messages.
    """
    if not isinstance(proof, NativeActorContext):
        raise OriginDenied("NATIVE_ACTOR_CONTEXT_REQUIRED")
    if not callable(verify_host_context):
        raise OriginDenied("NATIVE_VERIFIER_REQUIRED")
    for field in ("task_id", "plan_id", "actor_agent", "worker_id",
                  "session_id", "native_evidence_ref"):
        _id(getattr(proof, field), field.upper())
    if proof.actor_agent not in _AGENT:
        raise OriginDenied("UNSUPPORTED_AGENT")
    if type(proof.plan_revision) is not int or proof.plan_revision < 1:
        raise OriginDenied("INVALID_PLAN_REVISION")
    if destination != _ALLOWED_TARGET:
        # In particular, never treat an operator/provider as human author of
        # a ChatGPT user message, DM, email or public post.
        raise OriginDenied("EXTERNAL_MESSAGE_DESTINATION_DENIED")
    if action not in _ACTION:
        raise OriginDenied("ACTION_NOT_IN_READ_ONLY_CONTRACT")
    current = _time(now, "NOW")
    observed = _time(proof.observed_at, "OBSERVED_AT")
    expires = _time(proof.expires_at, "EXPIRES_AT")
    if observed > current + _MAX_SKEW or current - observed > _MAX_AGE:
        raise OriginDenied("STALE_OR_FUTURE_NATIVE_CONTEXT")
    if expires <= current or expires <= observed:
        raise OriginDenied("NATIVE_CONTEXT_EXPIRED")
    try:
        verified = verify_host_context(proof)
    except Exception as exc:
        raise OriginDenied("NATIVE_VERIFIER_ERROR") from exc
    if verified is not True:
        raise OriginDenied("NATIVE_CONTEXT_NOT_VERIFIED")

    canonical = {
        "v": 1, "task_id": proof.task_id, "plan_id": proof.plan_id,
        "plan_revision": proof.plan_revision, "actor_agent": proof.actor_agent,
        "worker_id": proof.worker_id, "session_id": proof.session_id,
        "observed_at": observed.isoformat(),
        "native_evidence_ref": proof.native_evidence_ref,
        "action": action, "destination": destination,
    }
    digest = sha256(json.dumps(canonical, sort_keys=True,
                               separators=(",", ":")).encode()).hexdigest()
    return ActionOriginProposal(
        task_id=proof.task_id, plan_id=proof.plan_id,
        plan_revision=proof.plan_revision, actor_agent=proof.actor_agent,
        worker_id=proof.worker_id, session_id=proof.session_id,
        action=action, destination=destination,
        observed_at=observed.isoformat(),
        native_evidence_ref=proof.native_evidence_ref, fingerprint=digest,
    )
