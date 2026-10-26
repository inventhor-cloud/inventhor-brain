#!/usr/bin/env python3
"""Fail-closed source hygiene checks for public INVENTHOR Brain draft.

This check is intentionally *not* native Organizer evidence or an installed
runtime test. It protects the current owner architecture from regressions and
prevents legacy mirrored task data being mistaken for live work.
Standard library only. No network, secrets, installs, queues or side effects.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CORES = ("INVENTHOR", "OPERATOR", "ORGANIZER", "STUDIO_DESIGN", "QA_FACTORY")
CONTRACT = "system_constitution/ACTIVE_PRODUCT_ARCHITECTURE_20261026.json"
REQUIRED = (
    CONTRACT,
    "system_constitution/core_rules.md",
    "continuity/OWNER_PRIORITY_PRODUCT_ENGINE_20261026.md",
    "continuity/OWNER_WORK_INTAKE_POLICY.md",
    "continuity/studio_factory_handoff.py",
    "continuity/core_activation_gate.py",
    "continuity/brain_turn_integration.py",
    "continuity/organizer_cli_reader.py",
    "continuity/continuity_manifest.json",
    "continuity/work_queue.json",
    "continuity/idea_pool.json",
    "continuity/LIVE_SOURCE_FRESHNESS_GATE.md",
    "CONTINUE_HERE.md",
    "README.md",
)
ARCHIVE_SNAPSHOTS = (
    "continuity/continuity_manifest.json",
    "continuity/work_queue.json",
    "continuity/idea_pool.json",
    "continuity/active_projects/WINDOWS_OPERATOR_P0_UNATTENDED.json",
)


def _json(path: str, errors: list[str]) -> dict:
    try:
        item = json.loads((ROOT / path).read_text(encoding="utf-8"))
        if not isinstance(item, dict):
            raise ValueError("expected JSON object")
        return item
    except (ValueError, OSError, UnicodeError) as exc:
        errors.append(f"{path}: invalid/unreadable JSON: {exc}")
        return {}


def inspect_source() -> list[str]:
    errors: list[str] = []
    for file in REQUIRED:
        if not (ROOT / file).is_file():
            errors.append(f"MISSING_REQUIRED:{file}")
    if errors:
        return errors
    policy = _json(CONTRACT, errors)
    records = policy.get("core_systems")
    if not isinstance(records, list):
        errors.append("CORE_SYSTEMS_NOT_LIST")
        records = []
    ids = [x.get("id") if isinstance(x, dict) else None for x in records]
    if ids != list(CORES):
        errors.append(f"CORE_ARCHITECTURE_DRIFT:{ids!r}")
    if len(ids) != len(set(ids)):
        errors.append("DUPLICATE_CORE_SYSTEM")
    aliases = policy.get("aliases")
    if not isinstance(aliases, dict):
        errors.append("ALIASES_INVALID")
        aliases = {}
    for label in ("QA", "FACTORY", "FABRIKA", "KALITE_FABRIKASI"):
        if aliases.get(label) != "QA_FACTORY":
            errors.append("QA_FACTORY_ALIAS_DRIFT:" + label)
    for key, value in aliases.items():
        if value not in CORES:
            errors.append("UNKNOWN_ALIAS_TARGET:" + str(key))
    if policy.get("priority") != "P0_ONLY":
        errors.append("OWNER_PRIORITY_NOT_P0_ONLY")
    if policy.get("native_organizer_goal_update_status") != "NOT_VERIFIED":
        errors.append("PUBLIC_MIRROR_CLAIMS_NATIVE_ORGANIZER_UPDATED")
    if policy.get("installed_system_status") != "NOT_VERIFIED":
        errors.append("PUBLIC_MIRROR_CLAIMS_INSTALLED")
    rules = policy.get("execution_policy")
    if not isinstance(rules, dict):
        errors.append("EXECUTION_POLICY_MISSING")
        rules = {}
    for value in ("reuse_ids", "no_lease_takeover", "no_replay_terminal",
                  "source_ci_not_installed_qa"):
        if rules.get(value) is not True:
            errors.append("EXECUTION_GUARD_MISSING:" + value)
    for required in ("STUDIO_REAL_EDITABLE_DESIGN",
                     "OPERATOR_REAL_PROGRAM_BUILD_AND_RUN",
                     "SAME_QA_FACTORY_RETEST_CHANGED_ARTIFACT_IF_FAILED"):
        if required not in policy.get("mandatory_workflow", []):
            errors.append("WORKFLOW_STEP_MISSING:" + required)

    # Reference mirrors exist to preserve history, never to queue live jobs.
    for filename in ARCHIVE_SNAPSHOTS:
        item = _json(filename, errors)
        if item.get("runtime_authoritative") is not False:
            errors.append("OLD_SNAPSHOT_MAY_CLAIM_RUNTIME_AUTHORITY:" + filename)
        if item.get("reference_snapshot_only") is not True:
            errors.append("OLD_SNAPSHOT_NOT_MARKED_REFERENCE:" + filename)
        if item.get("state_freshness") != "UNVERIFIED":
            errors.append("OLD_SNAPSHOT_FRESHNESS_CLAIM:" + filename)

    for filepath, required_lines in (
        ("CONTINUE_HERE.md", ("ÜST MİMARİ TALİMAT — 2026-10-26",
                              CONTRACT)),
        ("system_constitution/core_rules.md",
         ("GÜNCEL SAHİP MİMARİ KURALI", "ACTIVE_PRODUCT_ARCHITECTURE_20261026.json")),
        ("continuity/OWNER_WORK_INTAKE_POLICY.md",
         ("CURRENT OWNER PRIORITY 2026-10-26",)),
    ):
        data = (ROOT / filepath).read_text(encoding="utf-8")
        for fragment in required_lines:
            if fragment not in data[:1800]:
                errors.append(f"ACTIVE_RULES_NOT_FIRST:{filepath}:{fragment}")

    # Archived plans may be quoted for history, but cannot pose as the
    # active rule when opened without reading the newer entry point.
    old_plan = (ROOT / "continuity/OWNER_CORE_APPLICATION_FACTORY_GOAL_20261025.md")
    if old_plan.is_file():
        if "SUPERSEDED" not in old_plan.read_text(encoding="utf-8")[:500]:
            errors.append("HISTORICAL_OWNER_PLAN_NOT_MARKED_SUPERSEDED")
    return errors


def main() -> int:
    errors = inspect_source()
    if errors:
        for issue in errors:
            print("BRAIN_SOURCE_HYGIENE_FAIL:", issue)
        return 1
    print("BRAIN_SOURCE_HYGIENE_PASS: five-system rule and old task reference fence")
    print("NOTE: SOURCE_ONLY; native Organizer, installed Brain and QA NOT verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
