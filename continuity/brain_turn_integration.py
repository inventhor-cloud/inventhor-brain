"""Compose ONE no-side-effect Brain turn from the existing native Organizer.

This wires the previously separate source contracts into one integration
boundary: exact CLI handoff + trusted native read + owner focus + finite task
advice + trace + attributable agent identity. The native Main host is still
required to supply authoritative adapters. Nothing here dispatches work.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json
from typing import Any, Mapping, Protocol, Sequence

from continuity.agent_action_origin import (
    ActionOriginProposal, NativeActorContext, prepare_origin,
)
from continuity.decision_trace import AdvisoryTrace, make_advisory_trace
from continuity.focus_adviser import (
    Advisory, FocusEnvelope, propose_next,
)
from continuity.live_handoff_gate import LiveTaskPort
from continuity.native_readonly_attachment import (
    BrainReadOnlyAttachment, ExactHandoffReader,
    prepare_read_only_attachment,
)


class AgentTurnDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class TrustedMainContextPort(LiveTaskPort, Protocol):
    """Only a local, owner-authorized Main/Organizer host can implement this.

    The host must independently prove the owner plan, snapshot epoch and
    per-session identity from native runtime facts (NOT arbitrary caller JSON).
    """
    def read_focus_snapshot(
        self, task_id: str,
    ) -> tuple[FocusEnvelope, Sequence[Mapping[str, Any]]]: ...

    def verify_focus_snapshot(
        self,
        read: BrainReadOnlyAttachment,
        focus: FocusEnvelope,
        tasks: Sequence[Mapping[str, Any]],
    ) -> bool: ...

    def read_actor_context(
        self, task_id: str, worker: str,
    ) -> NativeActorContext: ...

    def verify_actor_context(self, context: NativeActorContext) -> bool: ...


@dataclass(frozen=True)
class BrainTurnPreparation:
    attachment: BrainReadOnlyAttachment
    advisory: Advisory
    trace: AdvisoryTrace
    actor: ActionOriginProposal
    plan_revision: int
    packet_class: str = "HOST_COMPOSED_READ_ONLY_BRAIN_TURN_NOT_DISPATCH"
    may_claim: bool = False
    may_send_message: bool = False
    may_install: bool = False
    native_runtime_installed_verified: bool = False

    def as_json(self) -> str:
        # This bundle intentionally contains no owner identity, credentials,
        # native lease token, private project files, or free-form model prompt.
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False)


def prepare_brain_turn(
    cli: ExactHandoffReader,
    host: TrustedMainContextPort,
    task_id: str,
    *,
    worker: str,
    expected_target: str,
    now: datetime,
) -> BrainTurnPreparation:
    """Draft one grounded, attributable step; do not execute any step.

    Caller cannot inject a plan or an actor context: both are freshly READ
    from the owner-controlled trusted host after exact task cross-check.
    """
    attachment = prepare_read_only_attachment(
        cli, host, task_id, worker=worker, expected_target=expected_target,
        now=now,
    )
    try:
        focus, tasks = host.read_focus_snapshot(task_id)
    except Exception as exc:
        raise AgentTurnDenied("NATIVE_FOCUS_READ_UNAVAILABLE") from exc
    if not isinstance(focus, FocusEnvelope) or not isinstance(tasks, (list, tuple)):
        raise AgentTurnDenied("NATIVE_FOCUS_FORMAT_INVALID")
    if (focus.focus_task_id != attachment.task_id
        or focus.project_id != attachment.project_id
        or focus.target_id != attachment.target_id):
        raise AgentTurnDenied("FOCUS_TASK_SCOPE_MISMATCH")
    try:
        verified = host.verify_focus_snapshot(attachment, focus, tasks)
    except Exception as exc:
        raise AgentTurnDenied("FOCUS_VERIFIER_UNAVAILABLE") from exc
    if verified is not True:
        raise AgentTurnDenied("FOCUS_PROVENANCE_NOT_VERIFIED")
    advisory = propose_next(
        focus, tasks, now=now, native_snapshot_verified=True,
    )
    trace = make_advisory_trace(focus, advisory)
    try:
        proof = host.read_actor_context(task_id, worker)
    except Exception as exc:
        raise AgentTurnDenied("NATIVE_ACTOR_READ_UNAVAILABLE") from exc
    if not isinstance(proof, NativeActorContext):
        raise AgentTurnDenied("NATIVE_ACTOR_FORMAT_INVALID")
    if (proof.task_id != attachment.task_id
        or proof.plan_id != focus.plan_id
        or proof.plan_revision != focus.plan_revision
        or proof.worker_id != worker):
        raise AgentTurnDenied("ACTOR_TASK_PLAN_SCOPE_MISMATCH")
    actor = prepare_origin(
        proof, action="TASK_ADVICE", destination="INTERNAL_ORGANIZER",
        now=now, verify_host_context=host.verify_actor_context,
    )
    return BrainTurnPreparation(
        attachment=attachment, advisory=advisory, trace=trace,
        actor=actor, plan_revision=focus.plan_revision,
    )
