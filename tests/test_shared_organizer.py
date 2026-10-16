import unittest
from shared_organizer.board import view, assess_takeover, event_inbox, review_resume_packet

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

    def test_invalid_scope_rejected(self):
        for path in ("path:../secret", "path:/system", "path:foo//bar", "path:foo\\bar", "module:*"):
            with self.subTest(path=path):
                r = assess_takeover(candidate(), "gpt", [path], [], "rev7", TIME)
                self.assertEqual(r["decision"], "BLOCKED")

    def test_broken_active_lease_scope_rejected(self):
        r = assess_takeover(candidate(), "gpt", ["module:ui"],
                            [dict(lease(), scope_keys=[])], "rev7", TIME)
        self.assertEqual(r["reason"], "MALFORMED_LEASE")

    def test_events_per_project_deduplicated(self):
        events = [
            {"event_id": "ev1", "kind": "SCOPE_RESERVED", "project_id": "P-A",
             "task_id": "T1", "agent_id": "codex", "scope_keys": ["module:ui"]},
            {"event_id": "ev1", "kind": "SCOPE_RESERVED", "project_id": "P-A",
             "task_id": "T1"},
            {"event_id": "ev2", "kind": "HANDOFF_READY", "project_id": "P-B",
             "task_id": "T3"},
        ]
        output = event_inbox(events, "P-A")
        self.assertEqual(len(output["events"]), 1)
        self.assertFalse(output["dispatch_authorized"])

    def test_seen_events_suppressed(self):
        event = [{"event_id": "e1", "kind": "REVIEW_REQUESTED",
                  "project_id": "P-A", "task_id": "T2"}]
        self.assertEqual(event_inbox(event, "P-A", {"e1"})["events"], [])

    def test_unsupported_event_does_not_notify(self):
        event = [{"event_id": "e1", "kind": "ARBITRARY_COMMAND",
                  "project_id": "P-A", "task_id": "T2"}]
        self.assertEqual(event_inbox(event, "P-A")["events"], [])

    def test_windows_path_case_conflict(self):
        r = assess_takeover(candidate(), "gpt", ["path:WINDOWS/Core/Tests"],
                            [lease(scopes=["path:windows/core"])], "rev7", TIME)
        self.assertEqual(r["decision"], "CONFLICT")

    def test_module_case_conflict(self):
        r = assess_takeover(candidate(), "gpt", ["module:Windows.Control"],
                            [lease(scopes=["module:windows.control"])], "rev7", TIME)
        self.assertEqual(r["decision"], "CONFLICT")

    def test_cross_module_and_path_needs_authoritative_mapping(self):
        r = assess_takeover(candidate(), "gpt", ["module:windows.control"],
                            [lease(scopes=["path:windows/control"])], "rev7", TIME)
        self.assertEqual(r["decision"], "CONFLICT")

    def test_same_prefix_different_directory_does_not_conflict(self):
        r = assess_takeover(candidate(), "gpt", ["path:windows/core2"],
                            [lease(scopes=["path:windows/core"])], "rev7", TIME)
        self.assertEqual(r["decision"], "HOST_LEASE_REQUIRED")

    def test_path_with_control_char_or_trailing_dot_rejected(self):
        for scope in ("path:module/file\nother", "path:module/file.", "path:module/ file"):
            with self.subTest(scope=scope):
                r = assess_takeover(candidate(), "gpt", [scope], [], "rev7", TIME)
                self.assertEqual(r["decision"], "BLOCKED")

    def test_agent_and_event_evidence_not_live_attested(self):
        v = view(PROJECTS, QUEUE, leases=[dict(lease(), task_id="T1")])
        t = v["projects"][0]["buckets"]["TODO"][0]
        self.assertEqual(t["assignment_evidence"], "UNVERIFIED_REFERENCE")
        e = event_inbox([{"event_id":"e5", "kind":"AGENT_STARTED",
                          "project_id":"P-A", "task_id":"T1"}], "P-A")
        self.assertEqual(e["events"][0]["source"], "UNATTESTED_EVENT_REFERENCE")
        self.assertFalse(e["dispatch_authorized"])

    def test_review_task_requires_lease(self):
        r = assess_takeover(candidate("REVIEW_PENDING"), "reviewer", ["module:tests"], [], "rev7", TIME)
        self.assertEqual(r["decision"], "HOST_LEASE_REQUIRED")


class PortableHandoffTests(unittest.TestCase):
    def base_packet(self):
        return {
            "schema_version": 1, "handoff_id": "handoff-7",
            "project_id": "P-A", "task_id": "T1",
            "source_revision": "rev7", "architecture_snapshot_ref": "arch7",
            "created_at": "2026-10-16T11:00:00+00:00",
            "next_action": "run unit tests", "next_agent_role": "IMPLEMENTER",
            "scope_keys": ["module:windows.control"], "checkpoint_ref": "checkpoint:7",
            "evidence_refs": ["commit:xyz"]
        }

    def examine(self, packet, state="READY", project=PROJECTS[0]):
        queue = {"schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
                 "work_items": [{"id": "T1", "project_id": "P-A", "state": state}]}
        return review_resume_packet(packet, project, queue, "arch7", "rev7")

    def test_valid_packet_never_grants_authority(self):
        r = self.examine(self.base_packet())
        self.assertEqual(r["status"], "HOST_RECONCILIATION_REQUIRED")
        self.assertFalse(r["may_claim_task"])
        self.assertFalse(r["may_execute"])
        self.assertTrue(r["requires_host_lease"])

    def test_stale_architecture(self):
        p = self.base_packet()
        p["architecture_snapshot_ref"] = "arch6"
        self.assertEqual(self.examine(p)["status"], "STALE_ARCHITECTURE")

    def test_stale_source_revision(self):
        p = self.base_packet()
        p["source_revision"] = "rev6"
        self.assertEqual(self.examine(p)["status"], "STALE_TASK_REVISION")

    def test_checkpoint_required_on_interruption(self):
        p = self.base_packet()
        del p["checkpoint_ref"]
        self.assertEqual(self.examine(p, state="WAITING_PROVIDER")["status"],
                         "CHECKPOINT_MISSING")

    def test_cannot_continue_terminal_task(self):
        for state in ("DONE", "BS", "BF", "FAILED_TERMINAL"):
            with self.subTest(state=state):
                self.assertEqual(self.examine(self.base_packet(), state)["status"],
                                 "TERMINAL_TASK_REPLAY")

    def test_reviewer_role_and_evidence(self):
        p = self.base_packet()
        self.assertEqual(self.examine(p, "REVIEW_PENDING")["status"],
                         "REVIEW_ROLE_REQUIRED")
        p["next_agent_role"] = "REVIEWER"
        p["evidence_refs"] = []
        self.assertEqual(self.examine(p, "REVIEW_PENDING")["status"],
                         "REVIEW_EVIDENCE_MISSING")
        p["evidence_refs"] = ["test:1"]
        self.assertEqual(self.examine(p, "REVIEW_PENDING")["status"],
                         "HOST_RECONCILIATION_REQUIRED")

    def test_scope_duplicates_are_case_insensitive(self):
        p = self.base_packet()
        p["scope_keys"] = ["module:WINDOWS.Control", "module:windows.control"]
        self.assertEqual(self.examine(p)["status"], "INVALID_HANDOFF_SCOPE")

    def test_missing_or_invalid_identity_rejected(self):
        p = self.base_packet()
        p["task_id"] = ""
        self.assertEqual(self.examine(p)["status"], "HANDOFF_FIELDS_MISSING")
        p = self.base_packet()
        p["project_id"] = "another"
        self.assertEqual(self.examine(p)["status"], "PROJECT_MISMATCH")

    def test_handoff_does_not_create_missing_task(self):
        p = self.base_packet()
        q = {"schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
             "work_items": []}
        result = review_resume_packet(p, PROJECTS[0], q, "arch7", "rev7")
        self.assertEqual(result["status"], "WORK_ITEM_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
