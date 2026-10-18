import copy
import unittest

from shared_organizer.agent_learning import (
    advise_fix_memory_promotion, review_agent_lessons,
)
from shared_organizer.development_chain import review_development_chain

REV = "rev7"
TIME = "2026-10-18T12:00:00Z"
FAIL = "d" * 64


def event(eid, agent, outcome, when, resolution=None, verified=False):
    return {
        "event_id": eid, "project_id": "MAIN", "task_id": "T1",
        "agent_id": agent, "step": "TEST", "outcome": outcome,
        "timestamp": when, "evidence_ref": "QA-" + eid,
        "failure_fingerprint": None if resolution else FAIL,
        "resolved_failure_fingerprint": resolution,
        "quality_verified": verified,
    }


def report():
    return {
        "schema_version": 1, "source": "INVENTHOR_MAIN",
        "snapshot_revision": REV, "captured_at": TIME,
        "events": [
            event("F1", "CODEX", "FAILED", "2026-10-18T11:50:00Z"),
            event("F2", "GPT", "FAILED", "2026-10-18T11:51:00Z"),
            event("FIX", "LOCAL", "VERIFIED_PASS",
                  "2026-10-18T11:52:00Z", resolution=FAIL, verified=True),
        ],
    }


def lessons():
    return review_agent_lessons(
        report(), host_snapshot_revision=REV, host_time_iso=TIME)


def memory(entries=None):
    return {
        "schema_version": 1,
        "source": "INVENTHOR_MAIN_FIX_MEMORY",
        "snapshot_revision": REV,
        "fixes": [] if entries is None else entries,
    }


def known(lesson, evidence):
    return {
        "project_id": lesson["project_id"],
        "lesson_fingerprint": lesson["lesson_fingerprint"],
        "verified_recovery_evidence_ref": evidence,
    }


def promote(review=None, mem=None):
    return advise_fix_memory_promotion(
        lessons() if review is None else review,
        memory() if mem is None else mem,
        host_snapshot_revision=REV,
    )


class FixMemoryPromotionTests(unittest.TestCase):
    def test_new_verified_lesson_proposed_for_canonical_memory(self):
        r = promote()
        self.assertEqual(r["status"], "FIX_MEMORY_INTAKE_ADVISORY")
        self.assertEqual(r["memory_target"], "INVENTHOR_MAIN_FIX_MEMORY")
        self.assertEqual(r["proposals"][0]["next_action"],
                         "PROPOSE_NEW_CANONICAL_FIX_MEMORY_RECORD")
        self.assertFalse(r["may_write_memory"])
        self.assertFalse(r["may_auto_apply_fix"])
        self.assertFalse(r["may_delete_history"])

    def test_repeat_same_lesson_and_evidence_reuses_existing_memory(self):
        l = lessons()["lessons"][0]
        r = promote(mem=memory([known(l, "QA-FIX")]))
        self.assertEqual(r["proposals"][0]["next_action"],
                         "REUSE_EXISTING_CANONICAL_MEMORY")

    def test_quality_fix_enriches_previous_unresolved_lesson(self):
        l = lessons()["lessons"][0]
        r = promote(mem=memory([known(l, None)]))
        self.assertEqual(r["proposals"][0]["next_action"],
                         "REVIEW_VERIFIED_RECOVERY_ENRICHMENT")

    def test_conflicting_solution_evidence_requires_review(self):
        l = lessons()["lessons"][0]
        r = promote(mem=memory([known(l, "QA-OLD")]))
        self.assertEqual(r["proposals"][0]["next_action"],
                         "REVIEW_CONFLICTING_FIX_EVIDENCE")

    def test_duplicate_memory_records_are_not_silently_collapsed(self):
        l = lessons()["lessons"][0]
        f = known(l, "QA-FIX")
        self.assertEqual(promote(mem=memory([f, f]))["reason"],
                         "DUPLICATE_KNOWN_FIX")

    def test_stale_memory_revision_fails_closed(self):
        m = memory()
        m["snapshot_revision"] = "old"
        self.assertEqual(promote(mem=m)["reason"],
                         "UNPINNED_OR_INVALID_FIX_MEMORY")

    def test_bad_path_in_evidence_blocked(self):
        l = lessons()["lessons"][0]
        self.assertEqual(
            promote(mem=memory([known(l, "C:\\user\\secrets")]))["reason"],
            "INVALID_KNOWN_FIX_ENTRY",
        )

    def test_untrusted_lesson_status_rejected(self):
        l = lessons()
        l["status"] = "SOME_AGENT_SAYS_OK"
        self.assertEqual(promote(review=l)["reason"],
                         "INVALID_MEMORY_PROMOTION_INPUT")

    def test_idempotent_proposals_on_same_snapshot(self):
        self.assertEqual(promote()["proposals"], promote()["proposals"])

    def test_excessive_requested_promotions_rejected(self):
        r = advise_fix_memory_promotion(
            lessons(), memory(), host_snapshot_revision=REV,
            max_candidates=1000,
        )
        self.assertEqual(r["reason"], "INVALID_MEMORY_PROMOTION_INPUT")

    def test_development_chain_carries_memory_advice_without_moving_tasks(self):
        queue = {
            "schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
            "snapshot_revision": REV, "captured_at": TIME,
            "work_items": [{"project_id": "MAIN", "id": "T-NEW",
                            "state": "READY", "scope_keys": ["module:next"],
                            "title": "Next improvement"}],
        }
        settings = {
            "schema_version": 1, "source": "INVENTHOR_MAIN_SETTINGS",
            "snapshot_revision": REV, "enabled": True,
            "max_steps_per_cycle": 1, "steps_remaining_today": 1,
            "max_parallel_tasks": 1, "active_tasks": 0,
            "max_changed_files_per_step": 4,
            "provider_budget_units_remaining": 0,
            "paid_providers_enabled": False,
        }
        quality = {
            "schema_version": 1, "source": "INVENTHOR_QUALITY_FACTORY",
            "snapshot_revision": REV, "verified_tasks": [],
        }
        r = review_development_chain(
            [{"project_id": "MAIN"}], queue, settings, quality, report(),
            candidate_agent="GPT", active_leases=[],
            host_snapshot_revision=REV, host_time_iso=TIME,
            fix_memory_snapshot=memory(),
        )
        self.assertEqual(r["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")
        self.assertEqual(
            r["fix_memory_promotion_proposals"][0]["next_action"],
            "PROPOSE_NEW_CANONICAL_FIX_MEMORY_RECORD",
        )
        self.assertFalse(r["may_create_task"])
        self.assertFalse(r["may_execute"])
