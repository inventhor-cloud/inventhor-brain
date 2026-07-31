#!/usr/bin/env python3
"""Dependency-free validation for the software-brain foundation contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load(root: Path, name: str) -> dict:
    return json.loads((root / name).read_text(encoding="utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parent
    errors: list[str] = []
    try:
        manifest = load(root, "brain_manifest.json")
        registry = load(root, "capability_registry.json")
        policy = load(root, "filter_policy.json")
        continuation = load(root, "continuation_contract.json")
        gate = load(root, "operator_connection_gate.json")
    except Exception as exc:  # pragma: no cover
        print("STATUS=BF_SOFTWARE_BRAIN_CONTRACT_READ")
        print(f"ERROR={exc}")
        return 1

    required_files = set(manifest.get("required_contracts", []))
    actual_files = {
        "capability_registry.json",
        "filter_policy.json",
        "continuation_contract.json",
        "operator_connection_gate.json",
    }
    if required_files != actual_files:
        errors.append("REQUIRED_CONTRACT_SET_MISMATCH")
    if manifest.get("operator_connection") != "BLOCKED_UNTIL_VALIDATED":
        errors.append("MANIFEST_GATE_NOT_BLOCKED")
    if gate.get("status") != "BLOCKED_UNTIL_VALIDATED":
        errors.append("GATE_NOT_BLOCKED")
    if gate.get("initial_mode_after_validation") != "READ_ONLY_BRIDGE":
        errors.append("INITIAL_MODE_MUST_BE_READ_ONLY")
    if policy.get("promotion_rules", {}).get("anonymization_required") is not True:
        errors.append("ANONYMIZATION_REQUIRED")
    if policy.get("promotion_rules", {}).get("secret_scan_required") is not True:
        errors.append("SECRET_SCAN_REQUIRED")
    if policy.get("promotion_rules", {}).get("rollback_metadata_required") is not True:
        errors.append("ROLLBACK_REQUIRED")
    blocked = set(policy.get("blocked_data", []))
    for required in ("token", "password", "credential", "raw_conversation"):
        if required not in blocked:
            errors.append(f"BLOCKED_DATA_MISSING={required}")
    capabilities = registry.get("capabilities", [])
    ids = [item.get("capability_id") for item in capabilities]
    if not capabilities or len(ids) != len(set(ids)):
        errors.append("CAPABILITY_IDS_NOT_UNIQUE")
    defaults = registry.get("default_policy", {})
    for key in (
        "one_task_at_a_time",
        "explicit_task_id_required",
        "generic_handler_fallback",
        "fake_success",
        "finite_retries",
        "result_delivery_required",
    ):
        if key not in defaults:
            errors.append(f"DEFAULT_POLICY_MISSING={key}")
    states = set(continuation.get("states", []))
    if not {"PENDING", "RUNNING", "PAUSED", "WAITING", "BS", "BF"}.issubset(states):
        errors.append("CONTINUATION_STATES_INCOMPLETE")
    if continuation.get("resume_rules", {}).get("preserve_task_id") is not True:
        errors.append("TASK_ID_PRESERVATION_REQUIRED")
    if continuation.get("terminal_result_rules", {}).get("result_delivery_required") is not True:
        errors.append("RESULT_DELIVERY_REQUIRED")
    autonomous = continuation.get("autonomous_continuation", {})
    if autonomous.get("enabled") is not True:
        errors.append("AUTONOMOUS_CONTINUATION_DISABLED")
    if autonomous.get("mode") != "SEQUENTIAL_FINITE":
        errors.append("AUTONOMOUS_MODE_NOT_FINITE")
    if autonomous.get("advance_after") != "BS":
        errors.append("AUTONOMOUS_ADVANCE_MUST_REQUIRE_BS")
    if autonomous.get("never_invent_next_task") is not True:
        errors.append("NEXT_TASK_MUST_NOT_BE_INVENTED")

    if errors:
        print("STATUS=BF_SOFTWARE_BRAIN_FOUNDATION")
        for error in errors:
            print(f"ERROR={error}")
        return 1
    print("STATUS=BS_SOFTWARE_BRAIN_FOUNDATION_VALID")
    print("CONTRACTS=5")
    print("FILTER=ANONYMIZED_SECRET_SCANNED_ROLLBACK_REQUIRED")
    print("CONTINUATION=TASK_ID_PRESERVED")
    print("AUTONOMOUS=SEQUENTIAL_FINITE_AFTER_BS")
    print("OPERATOR_CONNECTION=BLOCKED_UNTIL_VALIDATED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
