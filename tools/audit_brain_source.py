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
    "continuity/OWNER_NONCORE_TOTAL_DETACH_HANDOFF_20261026.md",
    "continuity/OWNER_PORTABLE_NEW_PC_BOOTSTRAP_20261028.md",
    "continuity/OWNER_PRIORITY_CLEAN_CORE_THEN_CLOUD_20261028.md",
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
    newest = policy.get("current_owner_operational_override")
    if not isinstance(newest, dict) or newest.get("instruction_id") != "OWNER_FULL_NONCORE_DETACH_20261026":
        errors.append("LATEST_OWNER_FULL_DETACH_RULE_MISSING")
    else:
        if newest.get("complete_removal_not_equal_hide_or_disable") is not True:
            errors.append("NONCORE_HIDE_IS_NOT_COMPLETE_REMOVAL")
        if newest.get("status") != "SOURCE_POLICY_REGISTERED_NATIVE_UNVERIFIED":
            errors.append("FALSE_NATIVE_DETACH_SUCCESS")
        if newest.get("protect_user_data_and_rollback_material") is not True:
            errors.append("LOSS_OF_RECOVERABILITY_GUARD")
        if newest.get("native_organizer_exact_task_update_required") is not True:
            errors.append("MISSING_CANONICAL_ORGANIZER_HANDOFF")
    remove = policy.get("noncore_detachment_acceptance")
    acceptance = remove.get("complete_requires", {}) if isinstance(remove, dict) else {}
    for name in (
        "active_noncore_module_count",
        "active_noncore_dependency_edges",
        "orphan_noncore_runtime_registration_count",
        "orphan_noncore_service_startup_task_menu_count",
        "orphan_noncore_updater_installer_ci_reference_count",
    ):
        if type(acceptance.get(name)) is not int or acceptance[name] != 0:
            errors.append("NONCORE_ZERO_POSTCONDITION_MISSING:" + name)
    if not isinstance(remove, dict) or remove.get("unverified_runtime_is_not_success") is not True:
        errors.append("FALSE_NONCORE_REMOVAL_ATTESTATION")
    owner_sequence = policy.get("owner_execution_sequence_20261028")
    if not isinstance(owner_sequence, dict):
        errors.append("CURRENT_OWNER_CLEAN_FIRST_CLOUD_LATER_MISSING")
    else:
        if owner_sequence.get("phase_order") != [
            "P0_FULL_NONCORE_DETACH",
            "P1_COMPLETE_ONE_REAL_FIVE_SYSTEM_APP_FACTORY",
            "P2_CLOUD_ACCOUNT_RESTORE_FRESH_COMPUTER",
        ] or owner_sequence.get("current_phase") != "P0_FULL_NONCORE_DETACH":
            errors.append("CURRENT_OWNER_EXECUTION_ORDER_DRIFT")
        if owner_sequence.get("source_status") != "CURRENT_OWNER_PRIORITY_RECORDED_NATIVE_NOT_EXECUTED":
            errors.append("FALSE_CLEAN_CORE_NATIVE_SUCCESS")
        if owner_sequence.get("native_organizer_checkpoint_written_and_read_back") is not False:
            errors.append("FALSE_NATIVE_ORGANIZER_CLOUD_PRIORITY_WRITTEN")
        if owner_sequence.get("authoritative_read_first") != "continuity/OWNER_PRIORITY_CLEAN_CORE_THEN_CLOUD_20261028.md":
            errors.append("CURRENT_OWNER_HIGHEST_PRIORITY_HANDOFF_MISSING")
        p0 = owner_sequence.get("p0")
        if not isinstance(p0, dict) or not all(
            p0.get(key) is True for key in (
                "require_zero_legacy_module_dependency_in_all_five_cores",
                "require_zero_active_runtime_optional_modules",
                "prohibit_hide_only_or_disable_only_as_completion",
                "native_acceptance_not_verified",
            )
        ):
            errors.append("CORE_DETACHMENT_PRIORITY_WEAKENED")
        p2 = owner_sequence.get("p2")
        if not isinstance(p2, dict) or not all(
            p2.get(key) is True for key in (
                "cloud_development_deferred_until_p0_and_p1_acceptance",
                "restore_same_user_after_pc_format",
                "account_login_then_encrypted_versioned_organizer_and_projects_restore",
                "new_machine_device_identity_and_pairing_secrets",
                "cross_account_privacy_isolation",
                "fresh_pc_acceptance_not_verified",
            )
        ):
            errors.append("FUTURE_CLOUD_ACCOUNT_RESTORE_REQUIREMENTS_LOST")
    if not policy.get("new_agent_startup", [])[0].startswith("CURRENT OWNER PRIORITY (2026-10-28)"):
        errors.append("RESET_AGENT_NEWEST_OWNER_PRIORITY_NOT_FIRST")

    portable = policy.get("portable_new_computer_installation")
    if not isinstance(portable, dict):
        errors.append("PORTABLE_FRESH_MACHINE_REQUIREMENT_MISSING")
    else:
        if portable.get("priority") != "P2_AFTER_P0_CLEANUP_AND_P1_FACTORY" or portable.get("mandatory_final_product_requirement") is not True:
            errors.append("CLOUD_RESTORE_MUST_REMAIN_MANDATORY_P2")
        modes = portable.get("delivery_modes")
        names = {x.get("mode") for x in modes if isinstance(x, dict)} if isinstance(modes, list) else set()
        if names != {"PORTABLE_USER_MODE", "ONE_CLICK_LOCAL_INSTALL"}:
            errors.append("PORTABLE_INSTALL_MODE_DRIFT")
        required_claims = (
            "signed_release_tested", "portable_user_mode_tested",
            "fresh_pc_one_click_install_tested", "offline_first_run_tested",
            "native_organizer_checkpoint_updated",
        )
        for item in required_claims:
            if portable.get(item) is not False:
                errors.append("UNVERIFIED_PORTABILITY_CLAIM:" + item)
        if portable.get("status") != "SOURCE_OWNER_REQUIREMENT_RECORDED_FRESH_MACHINE_NOT_VERIFIED":
            errors.append("PORTABLE_CLEAN_INSTALL_FALSE_STATUS")
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
