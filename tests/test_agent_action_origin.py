import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from continuity.agent_action_origin import (
    NativeActorContext, OriginDenied, prepare_origin
)

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)


def native():
    return NativeActorContext(
        task_id="TASK_CANONICAL", plan_id="PLAN_OWNER_QA",
        plan_revision=4, actor_agent="CODEX",
        worker_id="CODEX_QA_WORKER", session_id="SESSION_001",
        observed_at=NOW, expires_at=NOW + timedelta(minutes=2),
        native_evidence_ref="PREFLIGHT_APPROVED_REF",
    )


def prepare(proof=None, *, action="CHECKPOINT_DRAFT",
            destination="INTERNAL_ORGANIZER", now=NOW, verifier=None):
    return prepare_origin(
        native() if proof is None else proof, action=action,
        destination=destination, now=now,
        verify_host_context=(lambda p: True) if verifier is None else verifier,
    )


class OriginGuardTests(unittest.TestCase):
    def denies(self, reason, **kw):
        with self.assertRaises(OriginDenied) as ex:
            prepare(**kw)
        self.assertEqual(ex.exception.code, reason)

    def test_internal_proposal_labels_actual_agent_never_owner(self):
        x = prepare()
        data = json.loads(x.to_json())
        self.assertEqual(data["actor_agent"], "CODEX")
        self.assertEqual(data["origin"], "AUTOMATED_AGENT")
        self.assertFalse(data["impersonates_owner"])
        self.assertFalse(data["is_executed"])
        self.assertFalse(data["is_native_receipt"])
        self.assertFalse(data["may_send_chat_message"])
        self.assertEqual(data["native_evidence_ref"], "PREFLIGHT_APPROVED_REF")

    def test_never_send_chat_or_email_through_internal_proposal(self):
        for destination in (
            "CHATGPT_USER_MESSAGE", "CHATGPT_WEB_UI",
            "EMAIL", "SOCIAL_POST", "WEBHOOK", "PROVIDER_API",
        ):
            with self.subTest(destination=destination):
                self.denies("EXTERNAL_MESSAGE_DESTINATION_DENIED",
                            destination=destination)

    def test_read_only_actions_only(self):
        for action in ("RUN_SHELL", "CLAIM", "INSTALL", "SIGN_QA", "WRITE_LEDGER"):
            with self.subTest(action=action):
                self.denies("ACTION_NOT_IN_READ_ONLY_CONTRACT", action=action)

    def test_only_current_three_agents(self):
        self.denies("UNSUPPORTED_AGENT", proof=replace(
            native(), actor_agent="UNKNOWN"))
        self.denies("UNSUPPORTED_AGENT", proof=replace(
            native(), actor_agent="OWNER"))

    def test_provenance_host_denial_or_error_fails_closed(self):
        self.denies("NATIVE_CONTEXT_NOT_VERIFIED", verifier=lambda p: False)
        def fail(p):
            raise ValueError("backend unavailable")
        self.denies("NATIVE_VERIFIER_ERROR", verifier=fail)

    def test_stale_observation_denied(self):
        self.denies("STALE_OR_FUTURE_NATIVE_CONTEXT",
                    now=NOW + timedelta(minutes=2))
        self.denies("STALE_OR_FUTURE_NATIVE_CONTEXT",
                    now=NOW - timedelta(seconds=11))

    def test_expired_or_zero_length_context_denied(self):
        self.denies("NATIVE_CONTEXT_EXPIRED",
                    proof=replace(native(), expires_at=NOW))
        self.denies("NATIVE_CONTEXT_EXPIRED",
                    proof=replace(native(), expires_at=NOW - timedelta(seconds=1)))

    def test_require_timezone_and_real_revision(self):
        self.denies("INVALID_NOW", now=NOW.replace(tzinfo=None))
        self.denies("INVALID_OBSERVED_AT",
                    proof=replace(native(), observed_at=NOW.replace(tzinfo=None)))
        for bad in (0, True, -1, "4"):
            with self.subTest(bad=bad):
                self.denies("INVALID_PLAN_REVISION",
                            proof=replace(native(), plan_revision=bad))

    def test_no_user_identity_or_freeform_prompt_stored(self):
        x = prepare()
        payload = json.loads(x.to_json())
        self.assertNotIn("owner_user_id", payload)
        self.assertNotIn("message_body", payload)
        self.assertNotIn("credentials", payload)
        self.assertNotIn("signing_key", payload)

    def test_duplicate_trace_stable_different_actor_distinct(self):
        a = prepare().fingerprint
        self.assertEqual(a, prepare().fingerprint)
        gpt = replace(native(), actor_agent="GPT", worker_id="GPT_WORKER")
        self.assertNotEqual(a, prepare(proof=gpt).fingerprint)
        newer = replace(native(), plan_revision=5)
        self.assertNotEqual(a, prepare(proof=newer).fingerprint)

    def test_id_path_injection_fails_before_verifier(self):
        invoked = []
        bad = replace(native(), session_id="../../bad")
        self.denies("INVALID_SESSION_ID", proof=bad,
                    verifier=lambda p: invoked.append(p) or True)
        self.assertEqual(invoked, [])

    def test_only_native_host_may_establish_truth(self):
        self.denies("NATIVE_CONTEXT_NOT_VERIFIED",
                    verifier=lambda p: "true")
        self.denies("NATIVE_VERIFIER_ERROR", verifier=lambda p: 1 / 0)


if __name__ == "__main__":
    unittest.main()
