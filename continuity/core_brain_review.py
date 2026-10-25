"""Read-only Brain review combining ONE native task with four-core readiness.

This is a source-level composition boundary, not an activation switch.
It cannot attest that an independently supplied activation snapshot is from
the trusted host; the installed Main/Organizer must establish that provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
import json

from continuity.brain_turn_integration import (
    BrainTurnPreparation, ExactHandoffReader, TrustedMainContextPort,
    prepare_brain_turn,
)
from continuity.core_activation_gate import (
    CoreActivationAdvice, CoreActivationSnapshot, evaluate_core_activation,
)


class CoreReviewDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class CoreBrainReview:
    """A bounded reference packet; no grants, receipts, leases or side effects."""

    task_id: str
    canonical_revision: int
    brain_turn: BrainTurnPreparation
    activation: CoreActivationAdvice
    packet_class: str = "COMPOSED_SOURCE_REVIEW_NOT_NATIVE_RECEIPT"
    activation_performed: bool = False
    claim_authorized: bool = False
    qa_live_verified: bool = False
    can_install: bool = False
    can_dispatch: bool = False

    def as_json(self) -> str:
        return json.dumps({
            "schema_version": 1,
            "task_id": self.task_id,
            "canonical_revision": self.canonical_revision,
            "brain_turn": json.loads(self.brain_turn.as_json()),
            "activation": asdict(self.activation),
            "packet_class": self.packet_class,
            "activation_performed": self.activation_performed,
            "claim_authorized": self.claim_authorized,
            "qa_live_verified": self.qa_live_verified,
            "can_install": self.can_install,
            "can_dispatch": self.can_dispatch,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def prepare_core_brain_review(
    cli: ExactHandoffReader,
    host: TrustedMainContextPort,
    task_id: str,
    *,
    worker: str,
    expected_target: str,
    now: datetime,
    activation_snapshot: CoreActivationSnapshot,
) -> CoreBrainReview:
    """Compose two safety advisories against one exact native task revision.

    - Brain turn remains read-only and has its own independent native host
      checks for Organizer, focus/plan and actor identity.
    - Activation facts are caller-provided *claims* only. Exact task/revision
      equality prevents accidental cross-task packaging, not forged evidence.
    - A successful report is NEVER live acceptance or permission to mutate.
    """
    if not isinstance(activation_snapshot, CoreActivationSnapshot):
        raise CoreReviewDenied("ACTIVATION_SNAPSHOT_REQUIRED")
    # Validating and consulting current task first ensures no stale public
    # queue, cross-provider fabricated task or terminal replay is considered.
    brain_turn = prepare_brain_turn(
        cli, host, task_id, worker=worker,
        expected_target=expected_target, now=now,
    )
    native = brain_turn.attachment
    if activation_snapshot.task_id != native.task_id:
        raise CoreReviewDenied("ACTIVATION_TASK_SCOPE_MISMATCH")
    if activation_snapshot.native_revision != native.canonical_revision:
        raise CoreReviewDenied("ACTIVATION_NATIVE_REVISION_MISMATCH")
    activation = evaluate_core_activation(activation_snapshot, now=now)
    return CoreBrainReview(
        task_id=native.task_id,
        canonical_revision=native.canonical_revision,
        brain_turn=brain_turn,
        activation=activation,
    )
