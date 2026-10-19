"""Read-only acceptance and budget reconciliation for one Main -> Operator cycle.

This is a pure proposal, not an attestation or a ledger writer. The authorized
Main host must independently authenticate Quality Factory evidence and apply
the counters with a same-revision compare-and-swap before starting more work.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import re

_IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_HASH = re.compile(r"[0-9a-fA-F]{64}\Z")


def _id(value: object) -> bool:
    return isinstance(value, str) and _IDENT.fullmatch(value) is not None


def _hash(value: object) -> bool:
    return isinstance(value, str) and _HASH.fullmatch(value) is not None


def _time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo and parsed.utcoffset() is not None else None
    except (ValueError, OverflowError):
        return None


def review_cycle_feedback(packet: object, feedback: object, ledger: object, *,
                          host_snapshot_revision: str, host_time_iso: str) -> dict:
    """Suggest a single bounded ledger transition; never activate the next job.

    Both the feedback and the input ledger are HOST-SUPPLIED CLAIMS here.
    Even a success needs Main quality attestation and atomic ledger CAS.
    """
    def output(status: str, reason: str = "", transition: dict | None = None) -> dict:
        return {
            "status": status, "reason": reason,
            "proposed_transition": transition,
            "state": "SOURCE_REFERENCE_ONLY",
            "may_write_ledger": False, "may_mark_task_done": False,
            "may_execute_next": False, "may_charge_provider": False,
            "may_skip_quality": False, "may_replay_failed_action": False,
            "requires_main_authenticated_quality_receipt": True,
            "requires_main_ledger_cas": True,
            "requires_fresh_scope_and_snapshot_revalidation": True,
        }

    if (not isinstance(packet, Mapping) or not isinstance(feedback, Mapping)
        or not isinstance(ledger, Mapping) or not _id(host_snapshot_revision)):
        return output("BLOCKED", "INVALID_FEEDBACK_ENVELOPE")
    now = _time(host_time_iso)
    captured = _time(ledger.get("captured_at"))
    completed = _time(feedback.get("completed_at"))
    if (now is None or captured is None or completed is None
        or not -5 <= (now-captured).total_seconds() <= 120
        or not -5 <= (now-completed).total_seconds() <= 120
        or ledger.get("owner_local_date") != now.date().isoformat()):
        return output("BLOCKED", "STALE_LEDGER_OR_FEEDBACK")

    if (type(packet.get("schema_version")) is not int
        or packet.get("schema_version") != 1
        or packet.get("queue_revision") != host_snapshot_revision
        or packet.get("execution_allowed") is not False
        or packet.get("host_authentication_receipt") is not None
        or packet.get("host_lease_receipt") is not None
        or not _id(packet.get("project_id"))
        or not _id(packet.get("task_id"))
        or not _hash(packet.get("handoff_fingerprint"))
        or not _hash(packet.get("action_sha256"))
        or not _hash(packet.get("source_tree_sha256"))):
        return output("BLOCKED", "UNPINNED_OR_EXECUTABLE_HANDOFF_PACKET")

    if (type(feedback.get("schema_version")) is not int
        or feedback.get("schema_version") != 1
        or feedback.get("source") != "INVENTHOR_QUALITY_FACTORY"
        or feedback.get("snapshot_revision") != host_snapshot_revision
        or feedback.get("project_id") != packet["project_id"]
        or feedback.get("task_id") != packet["task_id"]
        or not _hash(feedback.get("handoff_fingerprint"))
        or feedback["handoff_fingerprint"].lower()
           != packet["handoff_fingerprint"].lower()
        or not _hash(feedback.get("action_sha256"))
        or feedback["action_sha256"].lower() != packet["action_sha256"].lower()
        or not _hash(feedback.get("before_tree_sha256"))
        or feedback["before_tree_sha256"].lower()
           != packet["source_tree_sha256"].lower()
        or not _id(feedback.get("quality_evidence_ref"))
        or not _id(feedback.get("backup_ref"))
        or not _id(feedback.get("rollback_plan_ref"))
        or not isinstance(feedback.get("outcome"), str)
        or feedback["outcome"] not in ("VERIFIED_DONE", "VERIFIED_FAILURE")
        or type(feedback.get("tests_passed")) is not int
        or feedback["tests_passed"] < 0
        or type(feedback.get("tests_failed")) is not int
        or feedback["tests_failed"] < 0
        or not _hash(feedback.get("after_tree_sha256"))):
        return output("BLOCKED", "INVALID_QUALITY_FACTORY_FEEDBACK")

    succeeded = feedback["outcome"] == "VERIFIED_DONE"
    failure = feedback.get("failure_fingerprint")
    if (succeeded and (feedback["tests_failed"] != 0
                       or feedback["tests_passed"] < 1
                       or failure is not None)):
        return output("BLOCKED", "SUCCESS_WITHOUT_CLEAN_QUALITY_EVIDENCE")
    if not succeeded and not _hash(failure):
        return output("BLOCKED", "FAILURE_WITHOUT_RETRY_FINGERPRINT")

    if (type(ledger.get("schema_version")) is not int
        or ledger.get("schema_version") != 1
        or ledger.get("source") != "INVENTHOR_MAIN_DEVELOPMENT_LEDGER"
        or ledger.get("snapshot_revision") != host_snapshot_revision
        or type(ledger.get("steps_remaining_today")) is not int
        or not 0 <= ledger["steps_remaining_today"] <= 10000
        or type(ledger.get("active_tasks")) is not int
        or not 0 <= ledger["active_tasks"] <= 10000):
        return output("BLOCKED", "INVALID_MAIN_LEDGER")

    processed = ledger.get("processed_handoff_fingerprints")
    if (not isinstance(processed, list) or len(processed) > 512
        or any(not _hash(h) for h in processed)
        or len(set(h.lower() for h in processed)) != len(processed)):
        return output("BLOCKED", "INVALID_OR_DUPLICATED_LEDGER_HISTORY")
    pin = packet["handoff_fingerprint"].lower()
    if pin in {h.lower() for h in processed}:
        return output("ALREADY_RECORDED", "NO_REPEAT_BUDGET_OR_TASK_TRANSITION")
    if ledger["steps_remaining_today"] == 0 or ledger["active_tasks"] == 0:
        return output("BLOCKED", "LEDGER_BUDGET_OR_ACTIVE_TASK_MISMATCH")

    remaining = ledger["steps_remaining_today"] - 1
    active = ledger["active_tasks"] - 1
    return output(
        "FEEDBACK_RECONCILIATION_ADVISORY",
        "MAIN_HOST_MUST_VERIFY_QUALITY_AND_CAS_LEDGER",
        {
            "project_id": packet["project_id"],
            "task_id": packet["task_id"],
            "handoff_fingerprint": pin,
            "quality_evidence_ref": feedback["quality_evidence_ref"],
            "verified_result_claim": feedback["outcome"],
            "failed_action_fingerprint": failure.lower() if failure else None,
            "proposed_steps_remaining_today": remaining,
            "proposed_active_tasks": active,
            "append_processed_handoff_fingerprint": pin,
            "next_action": (
                "HOST_VERIFY_DONE_UPDATE_CANONICAL_TASK_THEN_REPLAN"
                if succeeded and remaining > 0
                else "HOST_RECORD_FAILURE_AND_DIAGNOSE_NEW_ACTION"
                if not succeeded else "HOST_CHECKPOINT_DAILY_BUDGET_EXHAUSTED"
            ),
            "may_write": False,
            "may_start_next_task": False,
        },
    )
