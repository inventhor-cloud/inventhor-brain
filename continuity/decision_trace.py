"""Deterministic *advisory* decision trace for the existing native Organizer.

A SHA-256 fingerprint is for deduplication/debugging only, NOT a signature,
authorization, QA attestation, cryptographic receipt or write to a ledger.
The native host must checkpoint an advisory after independent validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from continuity.focus_adviser import Advisory, FocusDenied, FocusEnvelope


@dataclass(frozen=True)
class AdvisoryTrace:
    fingerprint: str
    canonical_json: str
    source_class: str = "BRAIN_READ_ONLY_ADVISORY_NOT_NATIVE_RECEIPT"
    dispatch_authorized: bool = False
    qa_verified: bool = False

    def as_json(self) -> str:
        return json.dumps({
            "schema_version": 1, "fingerprint": self.fingerprint,
            "source_class": self.source_class,
            "dispatch_authorized": self.dispatch_authorized,
            "qa_verified": self.qa_verified,
            "advisory": json.loads(self.canonical_json),
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_advisory_trace(
    focus: FocusEnvelope,
    advisory: Advisory,
) -> AdvisoryTrace:
    if not isinstance(focus, FocusEnvelope) or not isinstance(advisory, Advisory):
        raise FocusDenied("TRACE_INPUT_INVALID")
    if advisory.plan_id != focus.plan_id or advisory.focus_task_id != focus.focus_task_id:
        raise FocusDenied("ADVISORY_PLAN_MISMATCH")
    if advisory.claim_authorized:
        raise FocusDenied("FORGED_DISPATCH_AUTHORITY")
    proposal = advisory.next_step
    if proposal is not None:
        if (proposal.plan_id != focus.plan_id
            or proposal.plan_revision != focus.plan_revision
            or proposal.target_id != focus.target_id
            or proposal.can_execute_from_proposal
            or not proposal.requires_fresh_native_claim
            or proposal.task_id not in focus.authorized_work_ids):
            raise FocusDenied("FORGED_PROPOSAL")
    if len(advisory.deferred) > 64:
        raise FocusDenied("TRACE_TOO_MANY_DEFERRED_TASKS")
    data = {
        "schema_version": 1,
        "plan_id": focus.plan_id,
        "plan_revision": focus.plan_revision,
        "plan_state": focus.plan_state,
        "focus_task_id": focus.focus_task_id,
        "target_id": focus.target_id,
        "observed_at": focus.observed_at.isoformat(),
        "proposed_task_id": proposal.task_id if proposal else None,
        "decision": advisory.disposition,
        "reasons": list(proposal.reasons) if proposal else [],
        "deferred": [{"task_id": a, "reason": b}
                     for a, b in advisory.deferred],
        "authorization": "READ_ONLY_ONLY_NATIVE_CLAIM_REQUIRED",
        "proof_level": "SOURCE_ADVISORY_NOT_RUNTIME_EVIDENCE",
    }
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False)
    if len(canonical.encode("utf-8")) > 16000:
        raise FocusDenied("TRACE_TOO_LARGE")
    fingerprint = sha256(canonical.encode("utf-8")).hexdigest()
    return AdvisoryTrace(fingerprint, canonical)
