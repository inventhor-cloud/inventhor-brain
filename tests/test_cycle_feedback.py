import copy
import json
import subprocess
import sys
import unittest

from shared_organizer.cycle_feedback import review_cycle_feedback
from shared_organizer.__main__ import evaluate_envelope

REV = "host-rev-42"
TIME = "2026-10-18T18:50:00+02:00"
HANDOFF = "a" * 64
ACTION = "b" * 64
TREE = "c" * 64
AFTER = "d" * 64


def packet():
    return {
        "schema_version": 1, "queue_revision": REV,
        "project_id": "INVENTHOR_MAIN", "task_id": "TASK-42",
        "handoff_fingerprint": HANDOFF, "action_sha256": ACTION,
        "source_tree_sha256": TREE, "execution_allowed": False,
        "host_authentication_receipt": None, "host_lease_receipt": None,
    }


def feedback(outcome="VERIFIED_DONE"):
    return {
        "schema_version": 1, "source": "INVENTHOR_QUALITY_FACTORY",
        "snapshot_revision": REV, "project_id": "INVENTHOR_MAIN",
        "task_id": "TASK-42", "handoff_fingerprint": HANDOFF,
        "action_sha256": ACTION, "before_tree_sha256": TREE,
        "after_tree_sha256": AFTER, "quality_evidence_ref": "QA-42",
        "backup_ref": "BACKUP-42", "rollback_plan_ref": "ROLLBACK-42",
        "outcome": outcome, "tests_passed": 434 if outcome == "VERIFIED_DONE" else 0,
        "tests_failed": 0 if outcome == "VERIFIED_DONE" else 1,
        "failure_fingerprint": None if outcome == "VERIFIED_DONE" else "f" * 64,
        "completed_at": TIME,
    }


def ledger(remaining=4, active=1, processed=None):
    return {
        "schema_version": 1, "source": "INVENTHOR_MAIN_DEVELOPMENT_LEDGER",
        "snapshot_revision": REV, "captured_at": TIME,
        "owner_local_date": "2026-10-18",
        "steps_remaining_today": remaining, "active_tasks": active,
        "processed_handoff_fingerprints": list(processed or []),
    }


def review(p=None, f=None, l=None):
    return review_cycle_feedback(
        packet() if p is None else p,
        feedback() if f is None else f,
        ledger() if l is None else l,
        host_snapshot_revision=REV, host_time_iso=TIME,
    )


class CycleFeedbackReviewTests(unittest.TestCase):
    def test_verified_completion_suggests_one_budget_decrement_and_next_plan(self):
        r = review()
        self.assertEqual(r["status"], "FEEDBACK_RECONCILIATION_ADVISORY")
        delta = r["proposed_transition"]
        self.assertEqual(delta["proposed_steps_remaining_today"], 3)
        self.assertEqual(delta["proposed_active_tasks"], 0)
        self.assertEqual(delta["next_action"],
                         "HOST_VERIFY_DONE_UPDATE_CANONICAL_TASK_THEN_REPLAN")
        self.assertEqual(delta["task_id"], "TASK-42")

    def test_cannot_mutate_host_or_claim_live_qa_by_itself(self):
        r = review()
        for key in ("may_execute_next", "may_write_ledger", "may_mark_task_done",
                    "may_charge_provider", "may_skip_quality",
                    "may_replay_failed_action"):
            self.assertFalse(r[key])
        self.assertTrue(r["requires_main_authenticated_quality_receipt"])
        self.assertTrue(r["requires_main_ledger_cas"])

    def test_same_handoff_feedback_is_idempotent(self):
        l = ledger(remaining=3, active=0, processed=[HANDOFF])
        r = review(l=l)
        self.assertEqual(r["status"], "ALREADY_RECORDED")
        self.assertIsNone(r["proposed_transition"])

    def test_case_insensitive_processed_fingerprint_never_double_charges(self):
        l = ledger(remaining=3, active=0, processed=[HANDOFF.upper()])
        self.assertEqual(review(l=l)["status"], "ALREADY_RECORDED")

    def test_failure_stops_retry_and_records_diagnostic_fingerprint(self):
        r = review(f=feedback("VERIFIED_FAILURE"))
        self.assertEqual(r["status"], "FEEDBACK_RECONCILIATION_ADVISORY")
        t = r["proposed_transition"]
        self.assertEqual(t["failed_action_fingerprint"], "f" * 64)
        self.assertEqual(t["next_action"], "HOST_RECORD_FAILURE_AND_DIAGNOSE_NEW_ACTION")
        self.assertEqual(t["proposed_steps_remaining_today"], 3)
        self.assertFalse(t["may_start_next_task"])

    def test_exhausted_cycle_checkpoints_after_final_success(self):
        r = review(l=ledger(remaining=1))
        self.assertEqual(r["proposed_transition"]["proposed_steps_remaining_today"], 0)
        self.assertEqual(r["proposed_transition"]["next_action"],
                         "HOST_CHECKPOINT_DAILY_BUDGET_EXHAUSTED")

    def test_no_budget_underflow_on_unrecorded_handoff(self):
        self.assertEqual(review(l=ledger(remaining=0))["reason"],
                         "LEDGER_BUDGET_OR_ACTIVE_TASK_MISMATCH")

    def test_no_active_host_task_stops_fake_callback(self):
        self.assertEqual(review(l=ledger(active=0))["reason"],
                         "LEDGER_BUDGET_OR_ACTIVE_TASK_MISMATCH")

    def test_wrong_task_or_project_never_updates_budget(self):
        f = feedback()
        f["task_id"] = "OTHER"
        self.assertEqual(review(f=f)["reason"], "INVALID_QUALITY_FACTORY_FEEDBACK")
        f = feedback()
        f["project_id"] = "VIKTORIJA"
        self.assertEqual(review(f=f)["reason"], "INVALID_QUALITY_FACTORY_FEEDBACK")

    def test_wrong_action_tree_or_handoff_fails_closed(self):
        for field in ("action_sha256", "before_tree_sha256", "handoff_fingerprint"):
            with self.subTest(field=field):
                f = feedback()
                f[field] = "0" * 64
                self.assertEqual(review(f=f)["reason"], "INVALID_QUALITY_FACTORY_FEEDBACK")

    def test_stale_host_ledger_and_replayed_old_feedback_rejected(self):
        l = ledger()
        l["captured_at"] = "2026-10-18T18:40:00+02:00"
        self.assertEqual(review(l=l)["reason"], "STALE_LEDGER_OR_FEEDBACK")
        f = feedback()
        f["completed_at"] = "2026-10-18T18:40:00+02:00"
        self.assertEqual(review(f=f)["reason"], "STALE_LEDGER_OR_FEEDBACK")

    def test_daily_budget_is_owner_local_day_not_utc_midnight(self):
        l = ledger()
        l["owner_local_date"] = "2026-10-17"
        self.assertEqual(review(l=l)["reason"], "STALE_LEDGER_OR_FEEDBACK")

    def test_false_success_if_tests_failed_or_none_passed_is_rejected(self):
        f = feedback()
        f["tests_failed"] = 1
        self.assertEqual(review(f=f)["reason"], "SUCCESS_WITHOUT_CLEAN_QUALITY_EVIDENCE")
        f = feedback()
        f["tests_passed"] = 0
        self.assertEqual(review(f=f)["reason"], "SUCCESS_WITHOUT_CLEAN_QUALITY_EVIDENCE")

    def test_failure_must_have_fingerprint(self):
        f = feedback("VERIFIED_FAILURE")
        f["failure_fingerprint"] = None
        self.assertEqual(review(f=f)["reason"], "FAILURE_WITHOUT_RETRY_FINGERPRINT")

    def test_missing_backup_or_rollback_is_not_success(self):
        for field in ("backup_ref", "rollback_plan_ref"):
            with self.subTest(field=field):
                f = feedback()
                f[field] = None
                self.assertEqual(review(f=f)["reason"], "INVALID_QUALITY_FACTORY_FEEDBACK")

    def test_forged_executable_packet_is_rejected(self):
        p = packet()
        p["execution_allowed"] = True
        self.assertEqual(review(p=p)["reason"], "UNPINNED_OR_EXECUTABLE_HANDOFF_PACKET")

    def test_provider_data_mutation_not_possible(self):
        p, f, l = packet(), feedback(), ledger()
        original = (copy.deepcopy(p), copy.deepcopy(f), copy.deepcopy(l))
        review(p=p, f=f, l=l)
        self.assertEqual((p, f, l), original)

    def test_invalid_hash_value_types_do_not_crash_review(self):
        for obj, field in ((packet(), "action_sha256"),
                           (packet(), "handoff_fingerprint")):
            obj[field] = {"code": "bad"}
            self.assertEqual(review(p=obj)["status"], "BLOCKED")
        for field in ("action_sha256", "before_tree_sha256",
                      "handoff_fingerprint", "outcome"):
            f = feedback()
            f[field] = {"code": "bad"}
            self.assertEqual(review(f=f)["status"], "BLOCKED")

    def test_bad_bool_integer_counters_are_rejected(self):
        for field in ("steps_remaining_today", "active_tasks"):
            l = ledger()
            l[field] = True
            self.assertEqual(review(l=l)["reason"], "INVALID_MAIN_LEDGER")

    def test_duplicate_history_blocks_instead_of_silent_reuse(self):
        l = ledger(processed=[HANDOFF, HANDOFF.upper()])
        self.assertEqual(review(l=l)["reason"],
                         "INVALID_OR_DUPLICATED_LEDGER_HISTORY")

    def test_wrong_quality_revision_and_source_stop_transition(self):
        f = feedback()
        f["snapshot_revision"] = "prior"
        self.assertEqual(review(f=f)["reason"], "INVALID_QUALITY_FACTORY_FEEDBACK")
        f = feedback()
        f["source"] = "CODEX"
        self.assertEqual(review(f=f)["reason"], "INVALID_QUALITY_FACTORY_FEEDBACK")

    def test_invalid_result_kind_is_not_verification(self):
        f = feedback()
        f["outcome"] = "AGENT_SAYS_PASSED"
        self.assertEqual(review(f=f)["reason"], "INVALID_QUALITY_FACTORY_FEEDBACK")



class CycleFeedbackAdapterTests(unittest.TestCase):
    def envelope(self):
        return {
            "schema_version": 1, "intent": "DEVELOPMENT_FEEDBACK_REVIEW",
            "snapshot_revision": REV, "host_time_iso": TIME,
            "handoff_packet": packet(), "quality_feedback": feedback(),
            "development_ledger": ledger(),
        }

    def test_canonical_main_intent_returns_one_nonexecuting_transition(self):
        r = evaluate_envelope(self.envelope())
        self.assertEqual(r["status"], "FEEDBACK_RECONCILIATION_ADVISORY")
        self.assertFalse(r["may_write_ledger"])
        self.assertFalse(r["may_mark_task_done"])
        self.assertFalse(r["may_execute_next"])

    def test_cli_reconciles_without_starting_a_task(self):
        done = subprocess.run(
            [sys.executable, "-m", "shared_organizer"],
            input=json.dumps(self.envelope()), text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(done.stdout.splitlines()), 1)
        r = json.loads(done.stdout)
        self.assertEqual(r["status"], "FEEDBACK_RECONCILIATION_ADVISORY")
        self.assertIsNotNone(r["proposed_transition"])
        self.assertFalse(r["proposed_transition"]["may_start_next_task"])

    def test_cli_idempotent_already_recorded_is_normal_nonmutating_outcome(self):
        e = self.envelope()
        e["development_ledger"] = ledger(3, 0, [HANDOFF])
        done = subprocess.run(
            [sys.executable, "-m", "shared_organizer"],
            input=json.dumps(e), text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["status"], "ALREADY_RECORDED")

    def test_no_cli_bypass_of_host_execution_gates(self):
        e = self.envelope()
        e["execute"] = True
        self.assertEqual(evaluate_envelope(e)["status"], "UNTRUSTED_EXECUTION_FLAGS")

    def test_missing_ledger_is_explicitly_rejected(self):
        e = self.envelope()
        e.pop("development_ledger")
        self.assertEqual(evaluate_envelope(e)["status"], "MISSING_MAIN_CONTEXT")

    def test_invalid_quality_evidence_does_not_become_success(self):
        e = self.envelope()
        e["quality_feedback"]["tests_failed"] = True
        done = subprocess.run(
            [sys.executable, "-m", "shared_organizer"],
            input=json.dumps(e), text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(done.returncode, 2)
        self.assertEqual(json.loads(done.stdout)["status"], "BLOCKED")
