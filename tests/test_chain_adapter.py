import json
import subprocess
import sys
import unittest

from shared_organizer.__main__ import evaluate_envelope

TIME = "2026-10-18T12:00:00Z"
REV = "r17"


def base():
    return {"schema_version": 1, "snapshot_revision": REV,
            "host_time_iso": TIME, "agent_report": {
                "schema_version": 1, "source": "INVENTHOR_MAIN",
                "snapshot_revision": REV, "captured_at": TIME, "events": [],
            }}


def chain():
    return {
        **base(), "intent": "DEVELOPMENT_CHAIN_REVIEW",
        "projects": [{"project_id": "MAIN", "architecture_snapshot_ref": "arch:1"}],
        "queue": {
            "schema_version": 1, "system_of_record": "INVENTHOR_MAIN",
            "snapshot_revision": REV, "captured_at": TIME,
            "work_items": [
                {"project_id": "MAIN", "id": "T-0", "state": "DONE"},
                {"project_id": "MAIN", "id": "T-1", "state": "READY",
                 "priority": "P0", "title": "Next dependent module",
                 "scope_keys": ["module:next"], "depends_on": ["T-0"]},
            ],
        },
        "quality_report": {
            "schema_version": 1, "source": "INVENTHOR_QUALITY_FACTORY",
            "snapshot_revision": REV, "verified_tasks": [
                {"project_id": "MAIN", "task_id": "T-0",
                 "result": "VERIFIED_DONE", "evidence_ref": "QA-0"},
            ],
        },
        "settings": {
            "schema_version": 1, "source": "INVENTHOR_MAIN_SETTINGS",
            "snapshot_revision": REV, "enabled": True,
            "max_steps_per_cycle": 1, "steps_remaining_today": 4,
            "max_parallel_tasks": 1, "active_tasks": 0,
            "max_changed_files_per_step": 4,
            "paid_providers_enabled": False,
            "provider_budget_units_remaining": 0,
        },
        "candidate_agent": "BRAIN", "active_leases": [],
    }


def cli(payload):
    return subprocess.run(
        [sys.executable, "-m", "shared_organizer"],
        input=json.dumps(payload), capture_output=True, text=True,
        check=False,
    )


class AgentLearningChainAdapterTests(unittest.TestCase):
    def test_agent_learning_source_only_handler(self):
        payload = {**base(), "intent": "AGENT_LESSON_REVIEW"}
        result = evaluate_envelope(payload)
        self.assertEqual(result["status"], "LESSONS_REVIEW_READY")
        self.assertFalse(result["may_train_model"])
        self.assertFalse(result["may_auto_apply_fix"])

    def test_cli_agent_lesson_intent(self):
        finished = cli({**base(), "intent": "AGENT_LESSON_REVIEW"})
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertEqual(len(finished.stdout.splitlines()), 1)
        self.assertEqual(json.loads(finished.stdout)["status"], "LESSONS_REVIEW_READY")

    def test_chain_uses_existing_main_scope_and_does_not_execute(self):
        result = evaluate_envelope(chain())
        self.assertEqual(result["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")
        self.assertEqual(result["candidate"]["task_id"], "T-1")
        self.assertFalse(result["may_create_task"])
        self.assertFalse(result["may_claim_task"])
        self.assertFalse(result["may_execute"])

    def test_cli_chain_intent(self):
        finished = cli(chain())
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertEqual(len(finished.stdout.splitlines()), 1)
        obj = json.loads(finished.stdout)
        self.assertEqual(obj["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")
        self.assertFalse(obj["may_spend_money"])

    def test_limit_reached_has_successful_but_paused_cli(self):
        payload = chain()
        payload["settings"]["steps_remaining_today"] = 0
        finished = cli(payload)
        self.assertEqual(finished.returncode, 0)
        self.assertEqual(json.loads(finished.stdout)["status"], "PAUSED")

    def test_quality_evidence_required(self):
        payload = chain()
        payload["quality_report"]["verified_tasks"] = []
        result = evaluate_envelope(payload)
        self.assertEqual(result["status"], "NO_SAFE_STEP")

    def test_malicious_execute_flag_rejected(self):
        payload = chain()
        payload["execute"] = True
        self.assertEqual(evaluate_envelope(payload)["status"], "UNTRUSTED_EXECUTION_FLAGS")

    def test_missing_quality_input_rejected(self):
        payload = chain()
        del payload["quality_report"]
        self.assertEqual(evaluate_envelope(payload)["status"], "MISSING_MAIN_CONTEXT")

    def test_wrong_intent_not_executable(self):
        payload = chain()
        payload["intent"] = "DEPLOY_NOW_WITH_NO_QA"
        self.assertEqual(evaluate_envelope(payload)["status"],
                         "NOT_A_CANONICAL_CONTINUE_INTENT")

    def test_source_only_diagnostics_not_raw_event_content(self):
        payload = chain()
        payload["agent_report"]["events"] = [
            {
                "event_id": "E1", "project_id": "MAIN", "task_id": "T-0",
                "agent_id": "CODEX", "step": "TEST", "outcome": "FAILED",
                "timestamp": "2026-10-18T11:45:00Z",
                "evidence_ref": "QA-F1",
                "quality_verified": False,
                "failure_fingerprint": "f" * 64,
            },
        ]
        result = evaluate_envelope(payload)
        self.assertEqual(result["status"], "NEXT_DEVELOPMENT_STEP_ADVISORY")
        self.assertNotIn("QA-F1", str(result))
