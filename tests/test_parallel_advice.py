"""Source-only multi-agent lane selection; no authority to execute."""
import unittest

from shared_organizer.parallel_advice import advise_parallel_lanes

NOW = "2026-10-19T02:05:00+02:00"
PROJECTS = [{"project_id": "BRAIN"}, {"project_id": "VIKTORIJA"}]


def task(i, scope, *, project="BRAIN", state="READY", priority="P1",
         deps=None, title=None):
    return {
        "project_id": project, "task_id": i, "title": title or f"Work {i}",
        "state": state, "priority": priority, "order": 10,
        "scope_keys": [scope], "depends_on": deps or [],
    }


def settings(**override):
    return {
        "schema_version": 1, "source": "INVENTHOR_MAIN_SETTINGS",
        "snapshot_revision": "rev9", "enabled": True,
        "max_parallel_tasks": 3, "active_tasks": 0,
        "max_steps_per_cycle": 3, "steps_remaining_today": 5,
        **override,
    }


def review(rows, *, cfg=None, leases=None, project_id=None,
           handoffs=None, revision="rev9", now=NOW):
    queue = {
        "schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
        "snapshot_revision": "rev9", "captured_at": NOW,
        "work_items": rows,
    }
    return advise_parallel_lanes(
        PROJECTS, queue, cfg if cfg is not None else settings(),
        candidate_agent="main-agent", active_leases=leases if leases is not None else [],
        host_snapshot_revision=revision, host_time_iso=now,
        project_id=project_id, handoffs=handoffs,
    )


class ParallelLaneTests(unittest.TestCase):
    def test_independent_existing_tasks_proposed_not_started(self):
        r = review([task("T1", "module:brain"), task("T2", "module:memory")])
        self.assertEqual(r["status"], "HOST_MULTI_LEASE_REVIEW_REQUIRED")
        self.assertEqual({x["task_id"] for x in r["proposals"]}, {"T1", "T2"})
        for name in ("may_execute", "may_claim_task", "may_create_task",
                     "may_spend_money"):
            self.assertFalse(r[name])
        self.assertTrue(r["requires_independent_atomic_lease_per_task"])

    def test_overlapping_path_families_not_run_together(self):
        r = review([task("T1", "path:windows/core"),
                    task("T2", "path:windows/core/ui"),
                    task("T3", "path:windows/audio")])
        self.assertEqual({x["task_id"] for x in r["proposals"]}, {"T1", "T3"})
        self.assertTrue(any(d["reason"] == "CONCURRENT_SCOPE_PROPOSAL_CONFLICT"
                            for d in r["diagnostics"]))

    def test_module_path_overlap_fails_closed_until_inventory_maps(self):
        r = review([task("T1", "module:ui"), task("T2", "path:windows/ui")])
        self.assertEqual(len(r["proposals"]), 1)

    def test_same_global_path_different_projects_not_concurrent(self):
        r = review([task("T1", "path:shared/config"),
                    task("T2", "path:shared/config", project="VIKTORIJA")])
        self.assertEqual(len(r["proposals"]), 1)

    def test_foreign_active_lease_blocks_global_same_path(self):
        lease = {
            "agent_id": "viktorija-agent", "project_id": "VIKTORIJA",
            "task_id": "UNRELATED", "status": "RUNNING",
            "scope_keys": ["path:shared/config"],
            "snapshot_revision": "rev9", "expires_at": "2026-10-19T04:00:00+02:00",
        }
        r = review([task("T1", "path:shared/config"),
                    task("T2", "path:brain/memory")], leases=[lease])
        self.assertEqual([x["task_id"] for x in r["proposals"]], ["T2"])
        self.assertNotIn("viktorija-agent", str(r))

    def test_stale_same_project_lease_requires_reconciliation(self):
        lease = {
            "agent_id": "other-agent", "project_id": "BRAIN",
            "task_id": "OTHER", "status": "RUNNING",
            "scope_keys": ["path:brain/memory"],
            "snapshot_revision": "rev9", "expires_at": "2026-10-19T01:00:00+02:00",
        }
        r = review([task("T1", "path:brain/memory")], leases=[lease])
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")

    def test_priority_selection_order_shared_policy(self):
        r = review([task("T1", "module:low", priority="P3"),
                    task("T0", "module:high", priority="P0")])
        self.assertEqual(r["proposals"][0]["task_id"], "T0")

    def test_budget_one_step_disallows_second_lane(self):
        r = review([task("T1", "module:a"), task("T2", "module:b")],
                   cfg=settings(max_steps_per_cycle=1))
        self.assertEqual(len(r["proposals"]), 1)

    def test_active_parallel_limit_applies_before_advisory(self):
        r = review([task("T1", "module:a")],
                   cfg=settings(max_parallel_tasks=2, active_tasks=2))
        self.assertEqual(r["status"], "OWNER_BUDGET_OR_PARALLEL_LIMIT")

    def test_explicit_owner_pause_applies(self):
        self.assertEqual(review([task("T1", "module:a")],
                                cfg=settings(enabled=False))["status"],
                         "OWNER_PAUSED")

    def test_snapshot_revision_stale_fails_closed(self):
        self.assertEqual(review([task("T1", "module:a")], revision="different")["status"],
                         "UNVERSIONED_OR_MISMATCHED_SNAPSHOT")

    def test_host_must_promote_todo_before_write_lease(self):
        self.assertEqual(review([task("T1", "module:a", state="TODO")])["status"],
                         "NO_VERIFIED_ELIGIBLE_WORK")

    def test_completed_dependency_never_fake_unblocked(self):
        r = review([task("T1", "module:a", deps=["DONE1"])])
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")

    def test_nonboolean_limit_rejected(self):
        r = review([task("T1", "module:a")], cfg=settings(active_tasks=True))
        self.assertEqual(r["status"], "INVALID_OWNER_LIMITS")

    def test_unknown_project_filter_fails_closed(self):
        r = review([task("T1", "module:a")], project_id="UNREGISTERED")
        self.assertEqual(r["status"], "PROJECT_NOT_REGISTERED")

    def test_no_provider_spending_or_executor_claim(self):
        r = review([task("T1", "module:a")])
        self.assertFalse(r["may_spend_money"])
        self.assertFalse(r["may_claim_task"])


if __name__ == "__main__":
    unittest.main()
