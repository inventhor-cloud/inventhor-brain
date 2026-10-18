import copy
import unittest

from shared_organizer.agent_learning import review_agent_lessons
from shared_organizer.development_chain import review_development_chain

TIME = "2026-10-18T12:00:00Z"
REV = "snapshot-7"
FAILURE = "a" * 64
WORK_FP = "b" * 64


def agent_event(eid, agent, outcome, at, *, project="MAIN",
                task="T-BASE", failure=FAILURE, resolved=None,
                quality=False, step="TEST"):
    return {
        "event_id": eid, "project_id": project, "task_id": task,
        "agent_id": agent, "step": step, "outcome": outcome,
        "timestamp": at, "failure_fingerprint": failure,
        "resolved_failure_fingerprint": resolved,
        "quality_verified": quality, "evidence_ref": "QA-" + eid,
    }


def agent_report(events=None):
    return {"schema_version": 1, "source": "INVENTHOR_MAIN",
            "snapshot_revision": REV, "captured_at": TIME,
            "events": [] if events is None else events}


def settings(**kw):
    x = {
        "schema_version": 1, "source": "INVENTHOR_MAIN_SETTINGS",
        "snapshot_revision": REV, "enabled": True,
        "max_steps_per_cycle": 1, "steps_remaining_today": 4,
        "max_parallel_tasks": 1, "active_tasks": 0,
        "max_changed_files_per_step": 4,
        "paid_providers_enabled": False,
        "provider_budget_units_remaining": 0,
    }
    x.update(kw)
    return x


def queue():
    return {
        "schema_version": 1,
        "system_of_record": "INVENTHOR_MAIN",
        "snapshot_revision": REV,
        "captured_at": TIME,
        "work_items": [
            {"project_id": "MAIN", "id": "T-BASE", "state": "DONE",
             "title": "Verified shared core", "scope_keys": ["module:core"]},
            {"project_id": "MAIN", "id": "T-NEXT", "state": "READY",
             "title": "Advance dependent UI", "priority": "P0",
             "scope_keys": ["path:ui/main"],
             "depends_on": ["T-BASE"]},
        ],
    }


def quality(tasks=None):
    return {
        "schema_version": 1, "source": "INVENTHOR_QUALITY_FACTORY",
        "snapshot_revision": REV,
        "verified_tasks": (
            [{"project_id": "MAIN", "task_id": "T-BASE",
              "result": "VERIFIED_DONE", "evidence_ref": "QA-BASE"}]
            if tasks is None else tasks),
    }


PROJECTS = [{"project_id": "MAIN", "architecture_snapshot_ref": "arch:1"},
            {"project_id": "VIKTORIJA", "architecture_snapshot_ref": "arch:2"}]


def chain(q=None, setts=None, proofs=None, observations=None,
          projects=None, **kw):
    return review_development_chain(
        PROJECTS if projects is None else projects,
        queue() if q is None else q,
        settings() if setts is None else setts,
        quality() if proofs is None else proofs,
        agent_report() if observations is None else observations,
        candidate_agent="INVENTHOR", active_leases=[],
        host_snapshot_revision=REV, host_time_iso=TIME, **kw,
    )


class CrossAgentLearningTests(unittest.TestCase):
    def failures(self):
        return [
            agent_event("F1", "CODEX", "FAILED", "2026-10-18T11:50:00Z"),
            agent_event("F2", "GPT", "FAILED", "2026-10-18T11:51:00Z"),
        ]

    def learn(self, events, **kw):
        return review_agent_lessons(
            agent_report(events), host_snapshot_revision=REV,
            host_time_iso=TIME, **kw,
        )

    def test_repeated_failure_from_two_agents_is_a_single_lesson(self):
        r = self.learn(self.failures())
        self.assertEqual(r["status"], "LESSONS_REVIEW_READY")
        self.assertEqual(len(r["lessons"]), 1)
        item = r["lessons"][0]
        self.assertEqual(item["failed_attempts"], 2)
        self.assertEqual(item["agents_observed"], ["CODEX", "GPT"])
        self.assertEqual(item["next_action"], "HOLD_IDENTICAL_RETRY_AND_DIAGNOSE")
        self.assertFalse(r["may_replay_failure"])
        self.assertFalse(r["may_auto_apply_fix"])
        self.assertFalse(r["may_train_model"])

    def test_later_quality_verified_recovery_creates_reuse_candidate(self):
        records = self.failures() + [
            agent_event("GOOD", "OTHER_AGENT", "VERIFIED_PASS",
                        "2026-10-18T11:53:00Z", task="T-FIX",
                        failure=None, resolved=FAILURE, quality=True)]
        r = self.learn(records)
        lesson = r["lessons"][0]
        self.assertEqual(lesson["verified_recovery_task_id"], "T-FIX")
        self.assertEqual(lesson["verified_recovery_evidence_ref"], "QA-GOOD")
        self.assertEqual(lesson["next_action"], "REVIEW_VERIFIED_RECOVERY_FOR_REUSE")
        self.assertFalse(r["may_auto_apply_fix"])

    def test_unverified_success_does_not_override_repeat_failure(self):
        records = self.failures() + [
            agent_event("CLAIM", "OTHER_AGENT", "VERIFIED_PASS",
                        "2026-10-18T11:54:00Z",
                        resolved=FAILURE, quality=False)]
        self.assertEqual(
            self.learn(records)["lessons"][0]["next_action"],
            "HOLD_IDENTICAL_RETRY_AND_DIAGNOSE",
        )

    def test_single_failure_without_repair_does_not_create_lesson(self):
        self.assertEqual(self.learn(self.failures()[:1])["lessons"], [])

    def test_success_before_failure_is_not_recovery(self):
        event = agent_event("GOOD", "S", "VERIFIED_PASS",
                            "2026-10-18T11:45:00Z",
                            resolved=FAILURE, quality=True)
        r = self.learn([event, *self.failures()])
        self.assertEqual(r["lessons"][0]["verified_recovery_evidence_ref"], None)

    def test_cross_project_similar_errors_never_leak_recovery(self):
        records = self.failures() + [
            agent_event("EXT", "OTHER", "VERIFIED_PASS",
                        "2026-10-18T11:53:00Z", project="VIKTORIJA",
                        resolved=FAILURE, quality=True)]
        r = self.learn(records, project_id="MAIN")
        self.assertEqual(r["inspected_event_count"], 2)
        self.assertEqual(r["lessons"][0]["verified_recovery_evidence_ref"], None)
        self.assertNotIn("VIKTORIJA", str(r))

    def test_same_report_deterministic_lesson_identity(self):
        a, b = self.learn(self.failures()), self.learn(list(reversed(self.failures())))
        self.assertEqual(a["lessons"], b["lessons"])

    def test_duplicate_event_id_invalidates_report(self):
        rows = self.failures()
        self.assertEqual(self.learn(rows + rows)["reason"], "DUPLICATE_AGENT_EVENT")

    def test_stale_report_rejected(self):
        r = agent_report(self.failures())
        r["snapshot_revision"] = "other"
        self.assertEqual(review_agent_lessons(r, host_snapshot_revision=REV,
                                             host_time_iso=TIME)["status"], "BLOCKED")

    def test_future_and_bad_fingerprint_rejected(self):
        rows = self.failures()
        rows[0]["timestamp"] = "2026-10-18T12:05:00Z"
        self.assertEqual(self.learn(rows)["reason"], "INVALID_AGENT_EVENT")
        rows = self.failures()
        rows[0]["failure_fingerprint"] = "../secret"
        self.assertEqual(self.learn(rows)["reason"], "INVALID_AGENT_EVENT")

    def test_nonboolean_attestation_is_rejected(self):
        rows = self.failures()
        rows[0]["quality_verified"] = "true"
        self.assertEqual(self.learn(rows)["reason"], "INVALID_AGENT_EVENT")

    def test_max_lessons_bounded(self):
        r = review_agent_lessons(agent_report(), host_snapshot_revision=REV,
                                 host_time_iso=TIME, max_lessons=1000)
        self.assertEqual(r["reason"], "INVALID_LEARNING_INPUT")


class GovernedDevelopmentChainTests(unittest.TestCase):
    def test_verified_completion_advances_existing_dependent_task(self):
        r = chain()
        self.assertEqual(r["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")
        self.assertEqual(r["candidate"]["task_id"], "T-NEXT")
        self.assertEqual(r["candidate"]["next_action"],
                         "REVALIDATE_AND_ACQUIRE_HOST_LEASE")
        self.assertFalse(r["may_execute"])
        self.assertFalse(r["may_create_task"])
        self.assertFalse(r["may_spend_money"])

    def test_unverified_done_does_not_unlock_dependency(self):
        r = chain(proofs=quality([]))
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertIn("COMPLETED_DEPENDENCY_LACKS_QUALITY_EVIDENCE",
                      [x["reason"] for x in r["diagnostics"]])

    def test_nonblocking_independent_task_is_selected(self):
        q = queue()
        q["work_items"].append({
            "project_id": "MAIN", "id": "T-FREE", "title": "Another module",
            "state": "READY", "priority": "P1", "scope_keys": ["module:free"]})
        r = chain(q=q, proofs=quality([]))
        self.assertEqual(r["candidate"]["task_id"], "T-FREE")

    def test_max_daily_budget_stops_even_when_task_ready(self):
        r = chain(setts=settings(steps_remaining_today=0))
        self.assertEqual(r["status"], "PAUSED")
        self.assertEqual(r["reason"], "OWNER_STEP_LIMIT_REACHED")

    def test_owner_toggle_stops_work(self):
        r = chain(setts=settings(enabled=False))
        self.assertEqual(r["reason"], "OWNER_DISABLED_SELF_DEVELOPMENT")

    def test_parallel_bound_blocks_new_task(self):
        r = chain(setts=settings(active_tasks=1, max_parallel_tasks=1))
        self.assertEqual(r["reason"], "OWNER_PARALLEL_LIMIT_REACHED")

    def test_paid_provider_disabled_by_default(self):
        q = queue()
        q["work_items"][1]["estimated_provider_cost_units"] = 1
        r = chain(q=q)
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertIn("PAID_PROVIDER_DISABLED_BY_OWNER",
                      [x["reason"] for x in r["diagnostics"]])

    def test_paid_provider_can_be_owner_configured_without_spending(self):
        q = queue()
        q["work_items"][1]["estimated_provider_cost_units"] = 2
        r = chain(q=q, setts=settings(paid_providers_enabled=True,
                                     provider_budget_units_remaining=2))
        self.assertEqual(r["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")
        self.assertFalse(r["may_spend_money"])
        self.assertFalse(r["may_execute"])

    def test_owner_adjustable_file_change_limit(self):
        q = queue()
        q["work_items"][1]["estimated_changed_files"] = 5
        r = chain(q=q)
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertIn("SPLIT_STEP_TO_OWNER_FILE_LIMIT",
                      [x["reason"] for x in r["diagnostics"]])
        a = chain(q=q, setts=settings(max_changed_files_per_step=6))
        self.assertEqual(a["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")

    def test_repeated_failure_from_agents_holds_same_retry(self):
        q = queue()
        q["work_items"][1]["last_failure_fingerprint"] = FAILURE
        report = agent_report([
            agent_event("F1", "CODEX", "FAILED", "2026-10-18T11:50:00Z"),
            agent_event("F2", "GPT", "FAILED", "2026-10-18T11:51:00Z"),
        ])
        r = chain(q=q, observations=report)
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertIn("HOLD_REPEATED_AGENT_FAILURE",
                      [x["reason"] for x in r["diagnostics"]])

    def test_verified_other_agent_fix_is_advice_not_auto_patch(self):
        q = queue()
        q["work_items"][1]["last_failure_fingerprint"] = FAILURE
        events = [
            agent_event("F1", "CODEX", "FAILED", "2026-10-18T11:50:00Z"),
            agent_event("F2", "GPT", "FAILED", "2026-10-18T11:51:00Z"),
            agent_event("S", "LOCAL", "VERIFIED_PASS",
                        "2026-10-18T11:55:00Z", task="T-FIX",
                        resolved=FAILURE, quality=True),
        ]
        r = chain(q=q, observations=agent_report(events))
        self.assertEqual(r["candidate"]["learning_evidence_ref"], "QA-S")
        self.assertFalse(r["may_execute"])

    def test_completed_fingerprint_is_not_replayed(self):
        q = queue()
        q["work_items"][0]["work_fingerprint"] = WORK_FP
        q["work_items"][1]["work_fingerprint"] = WORK_FP
        r = chain(q=q)
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertIn("EXISTING_COMPLETED_WORK_FINGERPRINT",
                      [x["reason"] for x in r["diagnostics"]])

    def test_identical_ready_work_fingerprint_blocks_both(self):
        q = queue()
        q["work_items"][1]["work_fingerprint"] = WORK_FP
        q["work_items"].append({
            "project_id": "MAIN", "id": "T-SIMILAR", "state": "READY",
            "title": "Other title for same work",
            "work_fingerprint": WORK_FP,
            "scope_keys": ["module:separate"],
        })
        r = chain(q=q)
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertIn("DUPLICATE_ACTIVE_WORK_FINGERPRINT",
                      [x["reason"] for x in r["diagnostics"]])

    def test_other_project_completion_does_not_unlock_main(self):
        q = queue()
        q["work_items"][0]["state"] = "WAITING_REVIEW"
        q["work_items"].append({
            "project_id": "VIKTORIJA", "id": "T-BASE", "state": "DONE",
            "scope_keys": ["module:other"],
        })
        r = chain(q=q, proofs=quality([{
            "project_id": "VIKTORIJA", "task_id": "T-BASE",
            "result": "VERIFIED_DONE", "evidence_ref": "QA-OTHER",
        }]))
        self.assertEqual(r["status"], "NO_SAFE_STEP")

    def test_bad_host_setting_revision_rejected(self):
        x = settings()
        x["snapshot_revision"] = "old"
        r = chain(setts=x)
        self.assertEqual(r["reason"], "INVALID_OWNER_DEVELOPMENT_SETTINGS")

    def test_malformed_agent_report_blocks_without_execution(self):
        x = agent_report()
        x["source"] = "PROVIDER_UNVERIFIED"
        self.assertEqual(chain(observations=x)["status"], "BLOCKED")

    def test_quality_receipt_duplicate_rejected(self):
        x = quality()
        x["verified_tasks"] *= 2
        self.assertEqual(chain(proofs=x)["reason"], "DUPLICATE_COMPLETION_EVIDENCE")

    def test_terminal_task_not_in_queue_is_not_created(self):
        q = queue()
        q["work_items"] = q["work_items"][:1]
        r = chain(q=q)
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertFalse(r["may_create_task"])

    def test_lease_conflict_is_preserved(self):
        active = [{
            "project_id": "MAIN", "task_id": "OTHER", "agent_id": "CODEX",
            "status": "RUNNING", "snapshot_revision": REV,
            "scope_keys": ["path:ui/main"], "expires_at": "2026-10-18T12:05:00Z",
        }]
        r = review_development_chain(
            PROJECTS, queue(), settings(), quality(), agent_report(),
            candidate_agent="INVENTHOR", active_leases=active,
            host_snapshot_revision=REV, host_time_iso=TIME,
        )
        self.assertEqual(r["status"], "NO_SAFE_STEP")
        self.assertFalse(r["may_claim_task"])

    def test_invalid_owner_budget_bool_as_integer_rejected(self):
        r = chain(setts=settings(max_steps_per_cycle=True))
        self.assertEqual(r["reason"], "INVALID_OWNER_DEVELOPMENT_LIMITS")



def inventory_catalog():
    return {
        "schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
        "snapshot_revision": REV,
        "modules": [
            {"project_id": "MAIN", "module_id": "module_a",
             "declared_capabilities": ["READ_STATE", "WRITE_STATE"]},
            {"project_id": "VIKTORIJA", "module_id": "module_a",
             "declared_capabilities": ["READ_STATE"]},
        ],
    }


def inventory_observations():
    return {
        "schema_version": 1, "source": "WINDOWS_OPERATOR",
        "snapshot_revision": REV, "captured_at": TIME,
        "modules": [
            {"project_id": "MAIN", "module_id": "module_a", "status": "ACTIVE",
             "capabilities": [
                 {"name": "READ_STATE", "result": "PASS",
                  "evidence_ref": "QA-READ"},
             ]},
            {"project_id": "VIKTORIJA", "module_id": "module_a",
             "status": "ACTIVE", "capabilities": [
                {"name": "READ_STATE", "result": "PASS",
                 "evidence_ref": "QA-OTHER"},
             ]},
        ],
    }


def chain_with_inventory(q=None, cat=None, obs=None, **kw):
    return review_development_chain(
        PROJECTS, queue() if q is None else q, settings(),
        quality(), agent_report(), candidate_agent="INVENTHOR",
        active_leases=[], host_snapshot_revision=REV, host_time_iso=TIME,
        module_catalog=inventory_catalog() if cat is None else cat,
        module_observations=inventory_observations() if obs is None else obs,
        **kw,
    )


class InventoryDevelopmentBridgeTests(unittest.TestCase):
    def test_gap_is_proposed_to_canonical_main_intake_not_silently_added(self):
        r = chain_with_inventory()
        self.assertEqual(r["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")
        gap = r["inventory_gap_for_main_intake"]
        self.assertEqual(gap["project_id"], "MAIN")
        self.assertEqual(gap["module_id"], "module_a")
        self.assertEqual(gap["capability"], "WRITE_STATE")
        self.assertEqual(gap["next_action"], "PROPOSE_TO_EXISTING_MAIN_WORK_INTAKE")
        self.assertIsNone(gap["proposed_task_id"])
        self.assertFalse(gap["may_create_task"])
        self.assertFalse(r["may_create_task"])

    def test_incomplete_inventory_rejected_without_new_task(self):
        r = review_development_chain(
            PROJECTS, queue(), settings(), quality(), agent_report(),
            candidate_agent="INVENTHOR", active_leases=[],
            host_snapshot_revision=REV, host_time_iso=TIME,
            module_catalog=inventory_catalog(),
        )
        self.assertEqual(r["reason"], "INCOMPLETE_INVENTORY_SNAPSHOT")
        self.assertFalse(r["may_create_task"])

    def test_stale_observation_fails_closed(self):
        o = inventory_observations()
        o["captured_at"] = "2026-10-18T11:50:00Z"
        self.assertEqual(chain_with_inventory(obs=o)["reason"],
                         "INVENTORY_STALE_INVENTORY_OBSERVATION")

    def test_proposal_matches_existing_task_by_target_without_duplication(self):
        q = queue()
        q["work_items"].append({
            "project_id": "MAIN", "id": "T-ALREADY",
            "state": "READY", "title": "Fix capability",
            "priority": "P1", "scope_keys": ["module:module_a"],
            "target_module_id": "module_a",
            "target_capability": "WRITE_STATE",
        })
        r = chain_with_inventory(q=q)
        gap = r["inventory_gap_for_main_intake"]
        self.assertEqual(gap["next_action"], "TRACK_EXISTING_WORK_ITEM")
        self.assertEqual(gap["matched_task_ids"], ["T-ALREADY"])
        self.assertIsNone(gap["proposed_task_id"])

    def test_terminal_task_will_not_be_replayed_automatically(self):
        q = queue()
        q["work_items"].append({
            "project_id": "MAIN", "id": "T-CLOSED",
            "state": "BS", "title": "Fix capability",
            "target_module_id": "module_a",
            "target_capability": "WRITE_STATE",
        })
        gap = chain_with_inventory(q=q)["inventory_gap_for_main_intake"]
        self.assertEqual(gap["next_action"], "HOST_REVIEW_TERMINAL_EVIDENCE")
        self.assertEqual(gap["matched_task_ids"], ["T-CLOSED"])

    def test_duplicate_target_tasks_need_main_reconciliation(self):
        q = queue()
        for n in ("A", "B"):
            q["work_items"].append({
                "project_id": "MAIN", "id": "T-" + n,
                "state": "READY", "title": "Different title " + n,
                "priority": "P1", "scope_keys": ["module:module_a"],
                "target_module_id": "module_a",
                "target_capability": "WRITE_STATE",
            })
        gap = chain_with_inventory(q=q)["inventory_gap_for_main_intake"]
        self.assertEqual(gap["next_action"], "HOST_RECONCILE_DUPLICATE_EXISTING_WORK")
        self.assertEqual(gap["matched_task_ids"], ["T-A", "T-B"])

    def test_project_scope_never_returns_other_private_module(self):
        r = chain_with_inventory(project_id="VIKTORIJA")
        self.assertIsNone(r["inventory_gap_for_main_intake"])

    def test_stable_gap_fingerprint_across_repeated_calls(self):
        a = chain_with_inventory()["inventory_gap_for_main_intake"]
        b = chain_with_inventory()["inventory_gap_for_main_intake"]
        self.assertEqual(a["suggestion_fingerprint"],
                         b["suggestion_fingerprint"])
        self.assertEqual(len(a["suggestion_fingerprint"]), 64)

    def test_no_gap_when_evidence_for_all_capabilities_is_reported(self):
        o = inventory_observations()
        o["modules"][0]["capabilities"].append({
            "name": "WRITE_STATE", "result": "PASS",
            "evidence_ref": "QA-WRITE",
        })
        self.assertIsNone(chain_with_inventory(obs=o)["inventory_gap_for_main_intake"])
