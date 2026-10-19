import unittest
import json
import subprocess
import sys
from shared_organizer.__main__ import evaluate_envelope
from shared_organizer.board import (view, assess_takeover, event_inbox, review_resume_packet,
                                    advise_next_work, advise_read_only_source_comparison)

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

    def test_unrelated_stale_scope_does_not_freeze_entire_project(self):
        unrelated = lease(scopes=["path:windows/audio"],
                          expiry="2026-10-16T10:00:00Z")
        r = assess_takeover(candidate(), "gpt", ["path:windows/core"],
                            [unrelated], "rev7", TIME)
        self.assertEqual(r["decision"], "HOST_LEASE_REQUIRED")
        self.assertFalse(r["may_execute"])

    def test_stale_same_task_even_disjoint_path_still_blocks(self):
        stale_same = dict(lease(scopes=["path:windows/audio"],
                               expiry="2026-10-16T10:00:00Z"), task_id="T1")
        r = assess_takeover(candidate(), "gpt", ["path:windows/core"],
                            [stale_same], "rev7", TIME)
        self.assertEqual(r["reason"],
                         "STALE_OR_EXPIRED_LEASE_REQUIRES_HOST_RECONCILIATION")

    def test_stale_other_agent_overlap_still_blocks(self):
        stale = lease(scopes=["path:windows/core"],
                      expiry="2026-10-16T10:00:00Z")
        r = assess_takeover(candidate(), "gpt", ["path:windows/core/tests"],
                            [stale], "rev7", TIME)
        self.assertEqual(r["decision"], "BLOCKED")

    def test_malformed_unrelated_lease_fails_closed(self):
        stale = lease(scopes=["path:windows/audio"],
                      expiry="2026-10-16T10:00:00Z")
        stale["scope_keys"] = []
        r = assess_takeover(candidate(), "gpt", ["path:windows/core"],
                            [stale], "rev7", TIME)
        self.assertEqual(r["reason"], "MALFORMED_LEASE")

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

    def test_todo_write_handoff_identifies_exact_host_activation(self):
        r = assess_takeover(candidate("TODO"), "codex",
                            ["path:windows/core"], [], "rev7", TIME)
        self.assertEqual(r["decision"], "BLOCKED")
        self.assertEqual(r["reason"], "HOST_MUST_ACTIVATE_TODO_BEFORE_WRITE_LEASE")
        self.assertFalse(r["may_execute"])
        self.assertFalse(r["may_take_ownership"])

    def test_read_only_comparison_no_task_flip_or_host_lease(self):
        r = advise_read_only_source_comparison(candidate("TODO"),
                 ["windows/src/Inventhor.Operator.Core/TaskEngine.cs",
                  "windows/src/Inventhor.Operator.Core/ModuleManager.cs"])
        self.assertEqual(r["status"], "SOURCE_COMPARISON_ADVICE")
        self.assertEqual(len(r["paths"]), 2)
        self.assertTrue(r["can_propose_read_only_comparison"])
        self.assertFalse(r["requires_host_write_lease"])
        self.assertFalse(r["may_read_private_files"])
        self.assertFalse(r["may_mutate_files"])
        self.assertFalse(r["may_change_task_state"])
        self.assertFalse(r["may_take_ownership"])

    def test_read_only_comparison_does_not_replay_terminal_execution(self):
        r = advise_read_only_source_comparison(candidate("BS"), ["foo/bar.cs"])
        self.assertEqual(r["status"], "BLOCKED")
        self.assertFalse(r["may_merge"])

    def test_read_only_comparison_refuses_traversal_or_duplicate_paths(self):
        for paths in (["../secret"], ["windows/../secret"],
                      ["src/A.cs", "SRC/a.cs"], ["C:/secrets/file"],
                      [], [None]):
            with self.subTest(paths=paths):
                r = advise_read_only_source_comparison(candidate("TODO"), paths)
                self.assertEqual(r["status"], "BLOCKED")
                self.assertFalse(r["can_propose_read_only_comparison"])

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



class NextWorkAdviceTests(unittest.TestCase):
    PROJECTS = [
        {"project_id": "P-A", "architecture_snapshot_ref": "arch7"},
        {"project_id": "P-B", "architecture_snapshot_ref": "arch7"}
    ]

    def task(self, tid="T1", project="P-A", state="READY", priority="P1",
             order=10, scope="module:core", deps=None, title=None):
        return {"project_id": project, "task_id": tid,
                "state": state, "priority": priority, "order": order,
                "title": title or f"Task {tid}", "scope_keys": [scope],
                "depends_on": deps or []}

    def queue(self, rows):
        return {"schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
                "snapshot_revision": "rev7", "captured_at": TIME,
                "work_items": rows}

    def advise(self, rows, *, leases=None, project_id=None, handoffs=None,
               projects=None, time=TIME, queue=None):
        return advise_next_work(
            projects if projects is not None else self.PROJECTS,
            queue if queue is not None else self.queue(rows),
            "gpt", leases if leases is not None else [],
            "rev7", time, project_id=project_id, handoffs=handoffs)

    def test_p0_prioritized_over_p2_without_execute(self):
        r = self.advise([self.task("T2", priority="P2"),
                         self.task("T0", priority="P0", order=99)])
        self.assertEqual(r["candidate"]["task_id"], "T0")
        self.assertEqual(r["status"], "HOST_LEASE_REQUIRED")
        self.assertFalse(r["may_execute"])
        self.assertFalse(r["may_claim_task"])

    def test_explicit_project_scoping(self):
        r = self.advise([self.task("T1", project="P-A", priority="P0"),
                         self.task("T2", project="P-B", priority="P1")],
                        project_id="P-B")
        self.assertEqual(r["candidate"]["project_id"], "P-B")

    def test_unknown_project_fails_closed(self):
        self.assertEqual(
            self.advise([self.task()], project_id="INVENTED")["status"],
            "PROJECT_NOT_REGISTERED")

    def test_missing_snapshot_revision_is_not_live_queue(self):
        q = self.queue([self.task()])
        del q["snapshot_revision"]
        self.assertEqual(self.advise([], queue=q)["status"],
                         "UNVERSIONED_OR_MISMATCHED_SNAPSHOT")

    def test_stale_or_future_snapshot_fails(self):
        q = self.queue([self.task()])
        q["captured_at"] = "2026-10-16T10:00:00Z"
        self.assertEqual(self.advise([], queue=q)["status"],
                         "STALE_QUEUE_REQUIRES_MAIN_REFRESH")
        q["captured_at"] = "2026-10-16T12:00:00Z"
        self.assertEqual(self.advise([], queue=q)["status"],
                         "STALE_QUEUE_REQUIRES_MAIN_REFRESH")

    def test_real_legacy_cloud_queue_has_no_live_authority(self):
        q = self.queue([self.task()])
        del q["captured_at"]
        self.assertEqual(self.advise([], queue=q)["status"],
                         "UNVERSIONED_OR_MISMATCHED_SNAPSHOT")

    def test_dependency_blocks_until_main_marks_done(self):
        rows = [self.task("T1", state="READY", priority="P0", deps=["T0"]),
                self.task("T0", state="CHECKPOINTED", priority="P1")]
        r = self.advise(rows)
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")
        self.assertTrue(any(x["reason"] == "DEPENDENCY_NOT_VERIFIED"
                            for x in r["diagnostics"]))
        rows[1] = self.task("T0", state="DONE")
        r = self.advise(rows)
        self.assertEqual(r["candidate"]["task_id"], "T1")

    def test_same_task_id_other_project_does_not_satisfy_dependency(self):
        rows = [self.task("T1", deps=["T0"]),
                self.task("T0", project="P-B", state="DONE")]
        r = self.advise(rows, project_id="P-A")
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")

    def test_unknown_dependency_never_claimed_complete(self):
        r = self.advise([self.task(deps=["missing"])])
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")
        self.assertIn("missing", r["diagnostics"][0]["depends_on"])

    def test_same_task_and_ancestor_scope_conflict_skips(self):
        rows = [self.task("T1", priority="P0", scope="path:src/core"),
                self.task("T2", priority="P1", scope="path:src/ui")]
        r = self.advise(rows, leases=[lease(scopes=["path:src"])])
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")
        self.assertTrue(all(x["reason"] == "ANOTHER_AGENT_OWNS_OVERLAPPING_WORK"
                            for x in r["diagnostics"]))

    def test_disjoint_scope_can_select_alternative_task(self):
        rows = [self.task("T1", priority="P0", scope="path:src/core"),
                self.task("T2", priority="P1", scope="path:other/ui")]
        r = self.advise(rows, leases=[lease(scopes=["path:src/core"])])
        self.assertEqual(r["candidate"]["task_id"], "T2")

    def test_stale_lease_requires_reconciliation(self):
        r = self.advise([self.task()], leases=[dict(lease(), snapshot_revision="old")])
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")
        self.assertEqual(r["diagnostics"][0]["reason"],
                         "STALE_OR_EXPIRED_LEASE_REQUIRES_HOST_RECONCILIATION")

    def test_duplicate_titles_block_both_tasks(self):
        r = self.advise([self.task("T1", title="  Run Unit Tests  "),
                         self.task("T2", title="run unit tests")])
        self.assertEqual(r["status"], "NO_VERIFIED_ELIGIBLE_WORK")
        self.assertEqual([i["reason"] for i in r["diagnostics"]],
                         ["DUPLICATE_WORK_CANDIDATE"] * 2)

    def test_missing_scope_blocked(self):
        t = self.task()
        t["scope_keys"] = []
        r = self.advise([t])
        self.assertEqual(r["diagnostics"][0]["reason"],
                         "TASK_SCOPE_NOT_REGISTERED")

    def test_terminal_never_replayed(self):
        for state in ("DONE", "BS", "BF", "FAILED_TERMINAL"):
            with self.subTest(state=state):
                r = self.advise([self.task(state=state)])
                self.assertIsNone(r["candidate"])

    def test_blocked_and_waiting_approval_not_started(self):
        rows = [self.task("T1", state="BLOCKED"),
                self.task("T2", state="WAITING_APPROVAL"),
                self.task("T3", state="WAITING_DEPENDENCY")]
        self.assertIsNone(self.advise(rows)["candidate"])

    def test_checkpointed_requires_exact_handoff(self):
        t = self.task(state="CHECKPOINTED")
        r = self.advise([t])
        self.assertEqual(r["diagnostics"][0]["reason"],
                         "HANDOFF_MISSING_OR_AMBIGUOUS")

    def test_valid_checkpoint_handoff_still_requires_host(self):
        t = self.task(state="WAITING_PROVIDER")
        packet = {
            "schema_version": 1, "handoff_id": "H1", "project_id": "P-A",
            "task_id": "T1", "source_revision": "rev7",
            "architecture_snapshot_ref": "arch7",
            "next_action": "Resume test", "next_agent_role": "IMPLEMENTER",
            "created_at": TIME, "scope_keys": ["module:core"],
            "checkpoint_ref": "checkpoint:source:1"
        }
        r = self.advise([t], handoffs=[packet])
        self.assertEqual(r["status"], "HOST_LEASE_REQUIRED")
        self.assertEqual(r["candidate"]["next_action"], "RESUME_FROM_ATTESTED_CHECKPOINT")
        self.assertFalse(r["may_execute"])

    def test_fake_checkpoint_rejected(self):
        t = self.task(state="CHECKPOINTED")
        packet = {
            "schema_version": 1, "handoff_id": "H1", "project_id": "P-A",
            "task_id": "T1", "source_revision": "rev7",
            "architecture_snapshot_ref": "arch7",
            "next_action": "Resume test", "next_agent_role": "IMPLEMENTER",
            "created_at": TIME, "scope_keys": ["module:core"]
        }
        r = self.advise([t], handoffs=[packet])
        self.assertEqual(r["diagnostics"][0]["reason"], "CHECKPOINT_MISSING")

    def test_invalid_dependency_rejected(self):
        t = self.task()
        t["depends_on"] = "T0"
        self.assertEqual(self.advise([t])["diagnostics"][0]["reason"],
                         "INVALID_DEPENDENCY_LIST")

    def test_unregistered_work_item_project_blocked(self):
        r = self.advise([self.task(project="P-UNKNOWN")])
        self.assertEqual(r["status"], "UNREGISTERED_WORK_ITEM_PROJECT")


class ContinueAdapterTests(unittest.TestCase):
    def packet(self):
        return {
            "schema_version": 1,
            "intent": "WORK_CONTINUE",
            "projects": [{"project_id": "P-A", "architecture_snapshot_ref": "arch7"}],
            "queue": {"schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
                      "snapshot_revision": "rev7", "captured_at": TIME,
                      "work_items": [{"project_id": "P-A", "task_id": "T1",
                                      "title": "Verify state", "state": "READY",
                                      "priority": "P0", "scope_keys": ["module:core"]}]},
            "candidate_agent": "gpt",
            "active_leases": [],
            "snapshot_revision": "rev7",
            "host_time_iso": TIME,
        }

    def test_canonical_continue_intent_yields_one_unclaimed_task(self):
        result = evaluate_envelope(self.packet())
        self.assertEqual(result["status"], "HOST_LEASE_REQUIRED")
        self.assertEqual(result["candidate"]["task_id"], "T1")
        self.assertFalse(result["may_execute"])

    def test_shell_text_not_valid_canonical_intent(self):
        p = self.packet()
        p["intent"] = "G; rm -rf /"
        r = evaluate_envelope(p)
        self.assertEqual(r["status"], "NOT_A_CANONICAL_CONTINUE_INTENT")
        self.assertIsNone(r["candidate"])

    def test_missing_main_lease_inventory_never_defaults_empty(self):
        p = self.packet()
        del p["active_leases"]
        self.assertEqual(evaluate_envelope(p)["status"], "MISSING_MAIN_CONTEXT")

    def test_untrusted_execute_flags_blocked(self):
        p = self.packet()
        p["execute"] = True
        self.assertEqual(evaluate_envelope(p)["status"], "UNTRUSTED_EXECUTION_FLAGS")

    def test_advisory_output_contains_no_secrets_or_execution_grant(self):
        result = evaluate_envelope(self.packet())
        self.assertEqual(result["state"], "SOURCE_REFERENCE_ONLY")
        self.assertTrue(result["requires_host_atomic_lease"])
        self.assertFalse(result["may_mark_done"])

    def test_cli_has_one_machine_readable_json_response(self):
        p = self.packet()
        run = subprocess.run([sys.executable, "-m", "shared_organizer"],
                             input=json.dumps(p, ensure_ascii=False),
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["candidate"]["task_id"], "T1")
        self.assertEqual(run.stderr, "")

    def test_cli_invalid_json_is_safe_without_stacktrace(self):
        run = subprocess.run([sys.executable, "-m", "shared_organizer"],
                             input="{bad json}", capture_output=True,
                             text=True, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)["status"], "INVALID_JSON")


if __name__ == "__main__":
    unittest.main()
