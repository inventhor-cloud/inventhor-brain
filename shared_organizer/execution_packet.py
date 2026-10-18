"""Finite, provenance-pinned source-only work handoff from Main to Operator.

A plan is NOT an authorization or a runnable command. Canonical Main must
authenticate its owner, acquire an atomic revision/scope lease, verify the
snapshot/artifact hash and issue a separate signed execution receipt.
This module never runs commands, creates tasks, reads files or opens providers.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re

from .board import _valid_scope

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
_COMMIT = re.compile(r"[0-9a-fA-F]{40}\Z")
_STEPS = frozenset(("PATCH_AND_TEST", "MODULE_ONBOARD_AND_TEST",
                    "INVENTORY_VERIFY", "INTEGRATION_TEST"))


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _hex(value: object, regex: re.Pattern) -> bool:
    return isinstance(value, str) and regex.fullmatch(value) is not None


def review_operator_handoff(chain_advice: object, source_plan: object, *,
                            host_snapshot_revision: str) -> dict:
    """Construct one bounded, reproducible candidate for authenticated handoff.

    Artifact pins and evidence references are only claimed here. The live Main
    host and Operator installer must independently verify the content/lease.
    """
    def answer(status: str, reason: str, packet: dict | None = None) -> dict:
        return {
            "status": status, "reason": reason, "packet": packet,
            "state": "SOURCE_REFERENCE_ONLY",
            "may_execute": False, "may_sign_receipt": False,
            "may_acquire_lease": False, "may_change_files": False,
            "may_install": False, "may_spend_money": False,
            "requires_authenticated_main_host": True,
            "requires_lease_cas": True,
            "requires_verified_quality_gate": True,
            "requires_backup_and_rollback": True,
        }

    if (not isinstance(chain_advice, Mapping)
        or chain_advice.get("status") != "NEXT_DEVELOPMENT_STEP_ADVISORY"
        or chain_advice.get("state") != "SOURCE_REFERENCE_ONLY"
        or chain_advice.get("may_execute") is not False
        or chain_advice.get("may_claim_task") is not False
        or not isinstance(source_plan, Mapping)
        or not _valid_id(host_snapshot_revision)):
        return answer("BLOCKED", "INVALID_OR_EXECUTABLE_CHAIN_ADVICE")
    candidate = chain_advice.get("candidate")
    budget = chain_advice.get("budget")
    if not isinstance(candidate, Mapping) or not isinstance(budget, Mapping):
        return answer("BLOCKED", "MISSING_CANONICAL_CANDIDATE")
    pid, tid, revision = (candidate.get("project_id"), candidate.get("task_id"),
                          candidate.get("queue_revision"))
    scopes = candidate.get("scope_keys")
    if (not _valid_id(pid) or not _valid_id(tid)
        or revision != host_snapshot_revision
        or not isinstance(scopes, list) or not 0 < len(scopes) <= 64
        or any(not _valid_scope(s) for s in scopes)
        or len({s.casefold() for s in scopes}) != len(scopes)):
        return answer("BLOCKED", "STALE_OR_UNSCOPED_CANDIDATE")

    kind, plan_project, plan_task = (source_plan.get("step_kind"),
                                    source_plan.get("project_id"),
                                    source_plan.get("task_id"))
    changed = source_plan.get("estimated_changed_files")
    cost = source_plan.get("estimated_provider_cost_units")
    action_hash = source_plan.get("action_sha256")
    source_hash = source_plan.get("source_tree_sha256")
    base_commit = source_plan.get("base_commit")
    pr_commit = source_plan.get("candidate_commit")
    failures = source_plan.get("prior_failed_action_hashes", [])
    if (not isinstance(kind, str) or kind not in _STEPS
        or plan_project != pid or plan_task != tid
        or not _hex(action_hash, _SHA256) or not _hex(source_hash, _SHA256)
        or not _hex(base_commit, _COMMIT) or not _hex(pr_commit, _COMMIT)
        or base_commit.lower() == pr_commit.lower()
        or type(changed) is not int or changed < 0
        or type(cost) is not int or cost < 0
        or not isinstance(failures, list) or len(failures) > 64
        or any(not _hex(f, _SHA256) for f in failures)
        or len({f.lower() for f in failures}) != len(failures)):
        return answer("BLOCKED", "INVALID_OR_UNPINNED_SOURCE_PLAN")
    if action_hash.lower() in {f.lower() for f in failures}:
        return answer("HOLD_REPEATED_FAILURE", "IDENTICAL_FAILED_ACTION_REQUIRES_NEW_PLAN")
    max_files = candidate.get("max_changed_files_per_step")
    if (type(max_files) is not int or not 1 <= max_files <= 256
        or changed > max_files):
        return answer("BLOCKED", "OWNER_FILE_BATCH_LIMIT")
    if (type(budget.get("steps_available_this_cycle")) is not int
        or budget["steps_available_this_cycle"] < 1):
        return answer("BLOCKED", "OWNER_CYCLE_BUDGET_EXHAUSTED")
    if (type(budget.get("active_tasks")) is not int
        or type(budget.get("max_parallel_tasks")) is not int
        or budget["active_tasks"] >= budget["max_parallel_tasks"]):
        return answer("BLOCKED", "OWNER_PARALLEL_LIMIT_REACHED")
    if (type(budget.get("paid_providers_enabled")) is not bool
        or type(budget.get("provider_budget_units_remaining")) is not int):
        return answer("BLOCKED", "INVALID_PROVIDER_POLICY")
    if cost and not budget["paid_providers_enabled"]:
        return answer("BLOCKED", "PAID_PROVIDER_DISABLED")
    if cost > budget["provider_budget_units_remaining"]:
        return answer("BLOCKED", "PROVIDER_BUDGET_EXHAUSTED")

    # Never mistake the candidate for a signed instruction. The fingerprint is
    # purely an idempotency/deduplication hint until the host binds its epoch.
    raw = "\0".join((
        "inventhor-work-packet-v1", pid, tid, revision,
        kind, "\x1e".join(sorted(s.casefold() for s in scopes)),
        str(changed), str(cost), action_hash.lower(), source_hash.lower(),
        base_commit.lower(), pr_commit.lower(),
    ))
    packet_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    packet = {
        "schema_version": 1, "project_id": pid, "task_id": tid,
        "queue_revision": revision, "scope_keys": list(scopes),
        "step_kind": kind, "estimated_changed_files": changed,
        "estimated_provider_cost_units": cost,
        "action_sha256": action_hash.lower(),
        "source_tree_sha256": source_hash.lower(),
        "base_commit": base_commit.lower(),
        "candidate_commit": pr_commit.lower(),
        "handoff_fingerprint": packet_hash,
        "learning_evidence_ref": candidate.get("learning_evidence_ref"),
        "host_authentication_receipt": None,
        "host_lease_receipt": None,
        "execution_allowed": False,
        "next_action": "HOST_VALIDATE_PINS_ACQUIRE_ATOMIC_LEASE_AND_APPROVE",
        "quality_gates": [
            "SOURCE_PIN_AND_HASH_REVALIDATION", "SOURCE_BACKUP_AND_ROLLBACK",
            "BUILD_AND_REGRESSION_TESTS", "MAIN_QUALITY_FACTORY_ACCEPTANCE",
        ],
    }
    return answer("HOST_HANDOFF_PACKET_READY",
                  "NO_EXECUTION_AUTHORITY_FROM_SOURCE_PLAN", packet)
