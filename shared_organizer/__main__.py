"""Read-only Organizer continuation adapter for an authenticated Main host.

Input: one <=1 MiB JSON envelope via stdin, containing host-exported project,
queue, lease, checkpoint references and an already canonical WORK_CONTINUE
intent. Output: exactly one JSON advisory via stdout. No filesystem, network,
queue write, provider invocation, claim, release or background worker.

This module is deliberately NOT a second intent router or task scheduler.
"""
from __future__ import annotations

import json
import sys

from .board import advise_next_work

MAX_ENVELOPE_BYTES = 1_048_576


def evaluate_envelope(envelope: object) -> dict:
    if not isinstance(envelope, dict):
        return _blocked("INVALID_ENVELOPE")
    if envelope.get("schema_version") != 1 or envelope.get("intent") != "WORK_CONTINUE":
        return _blocked("NOT_A_CANONICAL_CONTINUE_INTENT")
    required = (
        "projects", "queue", "candidate_agent", "active_leases",
        "snapshot_revision", "host_time_iso",
    )
    if any(key not in envelope for key in required):
        return _blocked("MISSING_MAIN_CONTEXT")
    if any(key in envelope for key in ("owner_approval", "execute", "release", "skip_policy")):
        return _blocked("UNTRUSTED_EXECUTION_FLAGS")
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
    return 0 if result["status"] == "HOST_LEASE_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
