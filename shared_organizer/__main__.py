"""Read-only Main Organizer advisory adapter for an authenticated host.

One <=1 MiB JSON envelope via stdin. Supports existing canonical WORK_CONTINUE
and explicitly selected source-only MODULE_INVENTORY_REVIEW / OWNER_MODULE_REQUEST.
No filesystem, network, queue write, provider, claim or background worker.

This module is NOT an alternate intent router, installer or task scheduler.
"""
from __future__ import annotations

import json
import sys

from .board import advise_next_work
from .inventory import review_module_inventory
from .owner_modules import review_owner_module_request

MAX_ENVELOPE_BYTES = 1_048_576


def evaluate_envelope(envelope: object) -> dict:
    if not isinstance(envelope, dict):
        return _blocked("INVALID_ENVELOPE")
    if type(envelope.get("schema_version")) is not int or envelope["schema_version"] != 1:
        return _blocked("NOT_A_CANONICAL_CONTINUE_INTENT")
    if any(key in envelope for key in ("owner_approval", "execute", "release", "skip_policy")):
        return _blocked("UNTRUSTED_EXECUTION_FLAGS")

    intent = envelope.get("intent")
    if intent in ("MODULE_INVENTORY_REVIEW", "OWNER_MODULE_REQUEST"):
        required = ("catalog", "snapshot_revision", "host_time_iso")
        if any(key not in envelope for key in required):
            return _blocked("MISSING_MAIN_CONTEXT")
        try:
            if intent == "MODULE_INVENTORY_REVIEW":
                if "observations" not in envelope:
                    return _blocked("MISSING_MAIN_CONTEXT")
                return review_module_inventory(
                    envelope["catalog"], envelope["observations"],
                    host_snapshot_revision=envelope["snapshot_revision"],
                    host_time_iso=envelope["host_time_iso"],
                    project_id=envelope.get("project_id"),
                )
            if "module_request" not in envelope:
                return _blocked("MISSING_MAIN_CONTEXT")
            return review_owner_module_request(
                envelope["module_request"], envelope["catalog"],
                host_snapshot_revision=envelope["snapshot_revision"],
                host_time_iso=envelope["host_time_iso"],
            )
        except (TypeError, ValueError, KeyError, OverflowError):
            return _blocked("INVALID_MAIN_CONTEXT")

    if intent != "WORK_CONTINUE":
        return _blocked("NOT_A_CANONICAL_CONTINUE_INTENT")
    required = (
        "projects", "queue", "candidate_agent", "active_leases",
        "snapshot_revision", "host_time_iso",
    )
    if any(key not in envelope for key in required):
        return _blocked("MISSING_MAIN_CONTEXT")
    try:
        return advise_next_work(
            projects=envelope["projects"],
            queue=envelope["queue"],
            candidate_agent=envelope["candidate_agent"],
            active_leases=envelope["active_leases"],
            host_snapshot_revision=envelope["snapshot_revision"],
            host_time_iso=envelope["host_time_iso"],
            project_id=envelope.get("project_id"),
            handoffs=envelope.get("handoffs"),
        )
    except (TypeError, ValueError, KeyError, OverflowError):
        return _blocked("INVALID_MAIN_CONTEXT")


def _blocked(reason: str) -> dict:
    return {
        "status": reason,
        "candidate": None,
        "diagnostics": [],
        "state": "SOURCE_REFERENCE_ONLY",
        "may_execute": False,
        "may_claim_task": False,
        "may_mark_done": False,
        "requires_main_snapshot_attestation": True,
        "requires_host_atomic_lease": True,
    }


def main() -> int:
    payload = sys.stdin.buffer.read(MAX_ENVELOPE_BYTES + 1)
    if len(payload) > MAX_ENVELOPE_BYTES:
        print(json.dumps(_blocked("INPUT_TOO_LARGE"), ensure_ascii=False))
        return 2
    try:
        raw = payload.decode("utf-8", errors="strict")
        envelope = json.loads(raw)
    except (UnicodeError, ValueError):
        print(json.dumps(_blocked("INVALID_JSON"), ensure_ascii=False))
        return 2

    result = evaluate_envelope(envelope)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in (
        "HOST_LEASE_REQUIRED", "SOURCE_COVERAGE_REVIEW",
        "OWNER_CHOICE_READY_FOR_HOST_VALIDATION",
        "REVIEW_EXISTING_MODULE_EXTENSION",
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())
