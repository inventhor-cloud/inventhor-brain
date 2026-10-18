import copy
import json
import subprocess
import sys
import unittest

from shared_organizer.__main__ import evaluate_envelope

from shared_organizer.execution_packet import review_operator_handoff

REV = "rev-verified-9"
ACT = "a" * 64
TREE = "b" * 64
BASE = "1" * 40
HEAD = "2" * 40


def advice():
    return {
        "status": "NEXT_DEVELOPMENT_STEP_ADVISORY",
        "state": "SOURCE_REFERENCE_ONLY",
        "may_execute": False, "may_claim_task": False,
        "candidate": {
            "project_id": "INVENTHOR_MAIN", "task_id": "T-CHILD",
            "queue_revision": REV,
            "scope_keys": ["module:core", "path:windows/core"],
            "next_action": "REVALIDATE_AND_ACQUIRE_HOST_LEASE",
            "max_changed_files_per_step": 4,
            "learning_evidence_ref": "QA-VERIFIED",
        },
        "budget": {
            "steps_available_this_cycle": 1,
            "max_parallel_tasks": 1, "active_tasks": 0,
            "paid_providers_enabled": False,
            "provider_budget_units_remaining": 0,
        },
    }


def plan():
    return {
        "project_id": "INVENTHOR_MAIN", "task_id": "T-CHILD",
        "step_kind": "PATCH_AND_TEST", "estimated_changed_files": 2,
        "estimated_provider_cost_units": 0,
        "provider_required": False,
        "provider_quota_verified": False,
        "action_sha256": ACT, "source_tree_sha256": TREE,
        "base_commit": BASE, "candidate_commit": HEAD,
        "prior_failed_action_hashes": [],
    }


def review(a=None, p=None):
    return review_operator_handoff(
        advice() if a is None else a, plan() if p is None else p,
        host_snapshot_revision=REV,
    )


class ExecutionHandoffTests(unittest.TestCase):
    def test_pinned_handoff_is_nonexecuting_and_requires_real_main(self):
        r = review()
        self.assertEqual(r["status"], "HOST_HANDOFF_PACKET_READY")
        self.assertEqual(r["packet"]["task_id"], "T-CHILD")
        self.assertEqual(r["packet"]["next_action"],
                         "HOST_VALIDATE_PINS_ACQUIRE_ATOMIC_LEASE_AND_APPROVE")
        self.assertIsNone(r["packet"]["host_lease_receipt"])
        self.assertIsNone(r["packet"]["host_authentication_receipt"])
        self.assertFalse(r["packet"]["execution_allowed"])
        for permission in ("may_execute", "may_sign_receipt", "may_change_files",
                           "may_acquire_lease", "may_install", "may_spend_money"):
            self.assertFalse(r[permission])

    def test_idempotency_fingerprint_stable(self):
        self.assertEqual(review()["packet"]["handoff_fingerprint"],
                         review()["packet"]["handoff_fingerprint"])

    def test_new_action_plan_changes_deduplication_fingerprint(self):
        p = plan()
        p["action_sha256"] = "c" * 64
        self.assertNotEqual(review()["packet"]["handoff_fingerprint"],
                            review(p=p)["packet"]["handoff_fingerprint"])

    def test_altered_scope_changes_fingerprint_and_is_canonicalized(self):
        a = advice()
        a["candidate"]["scope_keys"] = ["path:Windows/Core", "module:core"]
        different = review(a=a)["packet"]["handoff_fingerprint"]
        self.assertEqual(different, review()["packet"]["handoff_fingerprint"])
        a["candidate"]["scope_keys"] = ["module:core"]
        self.assertNotEqual(review(a=a)["packet"]["handoff_fingerprint"], different)

    def test_wrong_project_or_task_stops_cross_project_mistake(self):
        p = plan()
        p["project_id"] = "VIKTORIJA"
        self.assertEqual(review(p=p)["reason"], "INVALID_OR_UNPINNED_SOURCE_PLAN")
        p = plan()
        p["task_id"] = "T-DIFFERENT"
        self.assertEqual(review(p=p)["reason"], "INVALID_OR_UNPINNED_SOURCE_PLAN")

    def test_source_pin_mismatch_and_short_sha_rejected(self):
        p = plan()
        p["candidate_commit"] = p["base_commit"]
        self.assertEqual(review(p=p)["reason"], "INVALID_OR_UNPINNED_SOURCE_PLAN")
        p["candidate_commit"] = "abc123"
        self.assertEqual(review(p=p)["reason"], "INVALID_OR_UNPINNED_SOURCE_PLAN")
        a = advice()
        a["candidate"]["queue_revision"] = "prior-revision"
        self.assertEqual(review(a=a)["reason"], "STALE_OR_UNSCOPED_CANDIDATE")

    def test_completed_or_untrusted_chain_advice_rejected(self):
        a = advice()
        a["may_execute"] = True
        self.assertEqual(review(a=a)["reason"], "INVALID_OR_EXECUTABLE_CHAIN_ADVICE")
        a = advice()
        a["status"] = "PAUSED"
        self.assertEqual(review(a=a)["reason"], "INVALID_OR_EXECUTABLE_CHAIN_ADVICE")

    def test_task_has_to_offer_real_lease_acquisition(self):
        a = advice()
        a["candidate"]["next_action"] = "APPLY_NO_CHECKS"
        self.assertEqual(review(a=a)["reason"], "STALE_OR_UNSCOPED_CANDIDATE")

    def test_scope_traversal_and_case_insensitive_duplicate_rejected(self):
        for scope in ("path:../secrets", "path:windows/../secrets",
                      "path:C:/windows", "path:foo\\bar", "module:"):
            with self.subTest(scope=scope):
                a = advice()
                a["candidate"]["scope_keys"] = [scope]
                self.assertEqual(review(a=a)["reason"], "STALE_OR_UNSCOPED_CANDIDATE")
        a = advice()
        a["candidate"]["scope_keys"] = ["path:WINDOWS/CORE", "path:windows/core"]
        self.assertEqual(review(a=a)["reason"], "STALE_OR_UNSCOPED_CANDIDATE")

    def test_repeat_failed_exact_action_is_held(self):
        p = plan()
        p["prior_failed_action_hashes"] = [ACT.upper()]
        self.assertEqual(review(p=p)["status"], "HOLD_REPEATED_FAILURE")
        self.assertFalse(review(p=p)["may_execute"])

    def test_new_action_after_failed_hash_is_reconsidered(self):
        p = plan()
        p["action_sha256"] = "c" * 64
        p["prior_failed_action_hashes"] = [ACT]
        self.assertEqual(review(p=p)["status"], "HOST_HANDOFF_PACKET_READY")

    def test_file_batch_limit_not_silently_increased(self):
        p = plan()
        p["estimated_changed_files"] = 5
        self.assertEqual(review(p=p)["reason"], "OWNER_FILE_BATCH_LIMIT")
        a = advice()
        a["candidate"]["max_changed_files_per_step"] = 5
        self.assertEqual(review(a=a, p=p)["status"], "HOST_HANDOFF_PACKET_READY")

    def test_owner_paused_or_busy_budget_stops_handoff(self):
        a = advice()
        a["budget"]["steps_available_this_cycle"] = 0
        self.assertEqual(review(a=a)["reason"], "OWNER_CYCLE_BUDGET_EXHAUSTED")
        a = advice()
        a["budget"]["active_tasks"] = 1
        self.assertEqual(review(a=a)["reason"], "OWNER_PARALLEL_LIMIT_REACHED")

    def test_paid_provider_disabled_by_default(self):
        p = plan()
        p["estimated_provider_cost_units"] = 1
        self.assertEqual(review(p=p)["reason"], "PAID_PROVIDER_DISABLED")
        a = advice()
        a["budget"]["paid_providers_enabled"] = True
        self.assertEqual(review(a=a, p=p)["reason"], "PROVIDER_BUDGET_EXHAUSTED")
        a["budget"]["provider_budget_units_remaining"] = 1
        self.assertEqual(review(a=a, p=p)["status"], "HOST_HANDOFF_PACKET_READY")
        self.assertFalse(review(a=a, p=p)["may_spend_money"])

    def test_required_provider_quota_has_to_be_verified(self):
        p = plan()
        p["provider_required"] = True
        self.assertEqual(review(p=p)["reason"], "UNVERIFIED_PROVIDER_REQUIREMENT")
        p["provider_quota_verified"] = True
        self.assertEqual(review(p=p)["status"], "HOST_HANDOFF_PACKET_READY")

    def test_bad_prior_history_does_not_allow_replay(self):
        p = plan()
        p["prior_failed_action_hashes"] = ["secret.txt"]
        self.assertEqual(review(p=p)["reason"], "INVALID_OR_UNPINNED_SOURCE_PLAN")
        p["prior_failed_action_hashes"] = [ACT, ACT]
        self.assertEqual(review(p=p)["reason"], "INVALID_OR_UNPINNED_SOURCE_PLAN")

    def test_noninteger_limits_rejected(self):
        p = plan()
        p["estimated_changed_files"] = True
        self.assertEqual(review(p=p)["reason"], "INVALID_OR_UNPINNED_SOURCE_PLAN")
        a = advice()
        a["candidate"]["max_changed_files_per_step"] = True
        self.assertEqual(review(a=a)["reason"], "OWNER_FILE_BATCH_LIMIT")

    def test_invalid_learning_evidence_reference_rejected(self):
        a = advice()
        a["candidate"]["learning_evidence_ref"] = "C:\\secrets\\token"
        self.assertEqual(review(a=a)["reason"], "STALE_OR_UNSCOPED_CANDIDATE")

    def test_packet_contains_no_shell_command_or_secret(self):
        packet = review()["packet"]
        for key in ("command", "shell", "exec", "file_content", "token", "password"):
            self.assertNotIn(key, packet)
        self.assertEqual(packet["quality_gates"][-1],
                         "MAIN_QUALITY_FACTORY_ACCEPTANCE")



class MainOperatorHandoffAdapterTests(unittest.TestCase):
    def envelope(self):
        return {
            "schema_version": 1,
            "intent": "OPERATOR_HANDOFF_REVIEW",
            "snapshot_revision": REV,
            "chain_advice": advice(),
            "source_plan": plan(),
        }

    def test_existing_main_adapter_issues_one_unprivileged_packet(self):
        r = evaluate_envelope(self.envelope())
        self.assertEqual(r["status"], "HOST_HANDOFF_PACKET_READY")
        self.assertFalse(r["may_execute"])
        self.assertIsNone(r["packet"]["host_lease_receipt"])

    def test_cli_reports_single_machine_readable_packet_without_side_effects(self):
        run = subprocess.run(
            [sys.executable, "-m", "shared_organizer"],
            input=json.dumps(self.envelope()),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(run.stdout.splitlines()), 1)
        out = json.loads(run.stdout)
        self.assertEqual(out["status"], "HOST_HANDOFF_PACKET_READY")
        self.assertFalse(out["packet"]["execution_allowed"])

    def test_cli_rejects_direct_instruction_to_execute(self):
        inp = self.envelope()
        inp["execute"] = True
        r = evaluate_envelope(inp)
        self.assertEqual(r["status"], "UNTRUSTED_EXECUTION_FLAGS")

    def test_cli_rejects_missing_pins_instead_of_using_defaults(self):
        inp = self.envelope()
        del inp["source_plan"]
        r = evaluate_envelope(inp)
        self.assertEqual(r["status"], "MISSING_MAIN_CONTEXT")
