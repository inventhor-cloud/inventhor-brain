import unittest
from shared_organizer.board import view, assess_takeover

PROJECTS = [
    {"project_id": "P-A", "title": "Operator", "objective": "Unattended work",
     "architecture": {"brain": "INVENTHOR", "body": "Windows Operator"},
     "module_refs": ["windows.control"], "rules_refs": ["constitution:v1"],
     "acceptance_definition": "end-to-end verified"},
    {"project_id": "P-B", "title": "Viktorija", "objective": "Learning"}
]
QUEUE = {"schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
         "work_items": [
             {"project_id": "P-A", "id": "T1", "title": "Inspect", "state": "READY"},
             {"project_id": "P-A", "id": "T2", "title": "Review", "state": "REVIEW_PENDING"},
             {"project_id": "P-B", "id": "T3", "title": "Study", "state": "CHECKPOINTED"}]}
HANDOFF = [{"project_id": "P-A", "task_id": "T2", "handoff_id": "H1",
            "created_at": "2026-10-16T10:00:00Z",
            "next_action": "Check test evidence", "evidence_refs": ["github:pr:1"],
            "do_not_repeat": ["verified bootstrap"]}]
TIME = "2026-10-16T11:00:00+00:00"

def lease(agent="codex", scopes=None, status="RUNNING", expiry="2026-10-16T12:00:00Z"):
    return {"agent_id": agent, "project_id": "P-A", "task_id": "OTHER",
            "scope_keys": scopes or ["path:windows/core"], "status": status,
            "expires_at": expiry, "snapshot_revision": "rev7"}

def candidate(state="READY"):
    return {"project_id": "P-A", "task_id": "T1", "state": state}

class SharedOrganizerTests(unittest.TestCase):
    def test_project_specific_buckets(self):
        v = view(PROJECTS, QUEUE, HANDOFF)
        self.assertEqual(v["projects"][0]["counts"]["TODO"], 1)
        self.assertEqual(v["projects"][0]["counts"]["REVIEW"], 1)
        self.assertEqual(v["projects"][1]["counts"]["IN_PROGRESS"], 1)
        self.assertFalse(v["may_execute"])

    def test_architecture_comes_from_project(self):
        p = view(PROJECTS, QUEUE)["projects"][0]
        self.assertEqual(p["architecture"]["brain"], "INVENTHOR")
        self.assertEqual(p["module_refs"], ["windows.control"])

    def test_handoff_evidence_and_next_action(self):
        t = view(PROJECTS, QUEUE, HANDOFF)["projects"][0]["buckets"]["REVIEW"][0]
        self.assertEqual(t["next_action"], "Check test evidence")
        self.assertEqual(t["evidence_refs"], ["github:pr:1"])

    def test_agents_visible_without_mutating_tasks(self):
        v = view(PROJECTS, QUEUE, leases=[dict(lease(), task_id="T1")])
        t = v["projects"][0]["buckets"]["TODO"][0]
        self.assertEqual(t["assigned_agents"], ["codex"])

    def test_unregistered_project_flag(self):
        q = {**QUEUE, "work_items": QUEUE["work_items"] + [
            {"project_id": "UNKNOWN", "id": "T4", "state": "READY"}]}
        self.assertEqual(view(PROJECTS, q)["unregistered_project_ids"], ["UNKNOWN"])

    def test_duplicate_canonical_task_rejected(self):
        q = {**QUEUE, "work_items": QUEUE["work_items"] * 2}
        with self.assertRaises(ValueError):
            view(PROJECTS, q)

    def test_invalid_queue_rejected(self):
        with self.assertRaises(ValueError):
            view(PROJECTS, {"work_items": []})

    def test_idea_bucket_is_project_specific(self):
        v = view(PROJECTS, QUEUE, ideas=[{"project_id": "P-B", "id": "idea-1"}])
        self.assertEqual(v["projects"][1]["counts"]["IDEAS"], 1)
        self.assertEqual(v["projects"][0]["counts"]["IDEAS"], 0)

    def test_overlapping_path_conflict(self):
        r = assess_takeover(candidate(), "gpt", ["path:windows/core/tests"],
                            [lease()], "rev7", TIME)
        self.assertEqual(r["decision"], "CONFLICT")
        self.assertEqual(r["conflicting_agents"], ["codex"])

    def test_same_task_different_agent_conflict(self):
        r = assess_takeover(candidate(), "gpt", ["module:ui"],
                            [dict(lease(), task_id="T1")], "rev7", TIME)
        self.assertEqual(r["decision"], "CONFLICT")

    def test_other_project_does_not_block(self):
        r = assess_takeover(candidate(), "gpt", ["path:windows/core"],
                            [dict(lease(), project_id="P-B")], "rev7", TIME)
        self.assertEqual(r["decision"], "HOST_LEASE_REQUIRED")

    def test_disjoint_scope_still_requires_host(self):
        r = assess_takeover(candidate(), "gpt", ["path:windows/ui"],
                            [lease()], "rev7", TIME)
        self.assertEqual(r["decision"], "HOST_LEASE_REQUIRED")
        self.assertFalse(r["may_take_ownership"])
        self.assertFalse(r["may_execute"])

    def test_expired_lease_requires_reconciliation(self):
        r = assess_takeover(candidate(), "gpt", ["module:ui"],
                            [lease(expiry="2026-10-16T10:00:00Z")], "rev7", TIME)
        self.assertEqual(r["reason"], "STALE_OR_EXPIRED_LEASE_REQUIRES_HOST_RECONCILIATION")

    def test_stale_snapshot_requires_reconciliation(self):
        r = assess_takeover(candidate(), "gpt", ["module:ui"],
                            [dict(lease(), snapshot_revision="old")], "rev7", TIME)
        self.assertEqual(r["decision"], "BLOCKED")

    def test_terminal_never_replayed(self):
        for state in ("BS", "BF", "DONE", "FAILED_TERMINAL"):
            with self.subTest(state=state):
                self.assertEqual(
                    assess_takeover(candidate(state), "gpt", ["module:ui"], [], "rev7", TIME)["reason"],
                    "TERMINAL_TASK_REPLAY")

    def test_running_task_no_duplicate(self):
        r = assess_takeover(candidate("RUNNING"), "gpt", ["module:ui"], [], "rev7", TIME)
        self.assertEqual(r["reason"], "TASK_NOT_ELIGIBLE_FOR_HANDOFF")

    def test_duplicate_scope_rejected(self):
        r = assess_takeover(candidate(), "gpt", ["module:ui", "module:ui"], [], "rev7", TIME)
        self.assertEqual(r["reason"], "DUPLICATE_SCOPE")

    def test_missing_host_time_fails_closed(self):
        r = assess_takeover(candidate(), "gpt", ["module:ui"], [], "rev7", "unknown")
        self.assertEqual(r["decision"], "BLOCKED")

    def test_review_task_requires_lease(self):
        r = assess_takeover(candidate("REVIEW_PENDING"), "reviewer", ["module:tests"], [], "rev7", TIME)
        self.assertEqual(r["decision"], "HOST_LEASE_REQUIRED")

if __name__ == "__main__":
    unittest.main()
