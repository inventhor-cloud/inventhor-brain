import json
import unittest
from copy import deepcopy
from pathlib import Path
from provider_independence.provider_candidate_gate import (
    assess_free_candidates, EvaluationRequest, CandidateEvaluationDenied
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "provider_independence" / "free_provider_candidates_20261024.json"


def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def eval_c(role="coding_evaluation", data="PUBLIC_SYNTHETIC", cat=None):
    return assess_free_candidates(
        catalog() if cat is None else cat,
        EvaluationRequest(role=role, data_class=data),
    )


def selected(arr, identifier):
    return next(x for x in arr if x.provider_id == identifier)


class ProviderCandidateGateTests(unittest.TestCase):
    def test_free_api_candidates_remain_nonrunning(self):
        arr = eval_c()
        for provider in ("google-gemini-api", "groqcloud", "mistral-studio"):
            item = selected(arr, provider)
            self.assertEqual(item.disposition, "CANDIDATE_ONLY")
            self.assertFalse(item.may_call_api)
            self.assertFalse(item.may_activate)
            self.assertFalse(item.may_send_data)
            self.assertTrue(item.requires_native_enrollment)

    def test_private_data_never_auto_sent_to_free_remote(self):
        for category in ("PRIVATE_OWNER", "CUSTOMER_CONFIDENTIAL"):
            arr = eval_c(data=category)
            for provider in ("google-gemini-api", "groqcloud", "mistral-studio"):
                self.assertEqual(
                    selected(arr, provider).disposition, "BLOCKED_PRIVATE_DATA"
                )

    def test_local_only_proposed_for_private_local_role(self):
        arr = eval_c(role="private_local_assistance", data="PRIVATE_OWNER")
        local = selected(arr, "ollama-local")
        self.assertEqual(local.disposition, "CANDIDATE_ONLY")
        self.assertFalse(local.may_send_data)

    def test_trial_or_consumer_free_not_api_free(self):
        arr = eval_c(role="complex_code_review")
        self.assertEqual(
            selected(arr, "anthropic-claude-api").disposition,
            "NOT_SUSTAINABLY_FREE_API",
        )
        arr = eval_c(role="sourced_research")
        self.assertEqual(
            selected(arr, "perplexity").disposition,
            "NOT_SUSTAINABLY_FREE_API",
        )

    def test_unknown_or_enabled_catalog_denied(self):
        for key, val in (
            ("authority", "LIVE_NATIVE"),
            ("default_enabled", True),
            ("runtime_authoritative", True),
        ):
            cat = catalog()
            cat[key] = val
            with self.subTest(key=key):
                with self.assertRaises(CandidateEvaluationDenied):
                    eval_c(cat=cat)

    def test_malicious_provider_status_cannot_be_switched_live(self):
        cat = catalog()
        cat["providers"][0]["status"] = "ACTIVE"
        with self.assertRaisesRegex(
            CandidateEvaluationDenied, "UNAPPROVED_PROVIDER_ACTIVATION"
        ):
            eval_c(cat=cat)

    def test_duplicate_provider_denied(self):
        cat = catalog()
        cat["providers"].append(deepcopy(cat["providers"][0]))
        with self.assertRaisesRegex(
            CandidateEvaluationDenied, "DUPLICATE_OR_INVALID_PROVIDER"
        ):
            eval_c(cat=cat)

    def test_unknown_role_denied(self):
        with self.assertRaisesRegex(
            CandidateEvaluationDenied, "UNKNOWN_EVALUATION_ROLE"
        ):
            eval_c(role="RUN_SHELL")

    def test_premium_provider_not_selected_under_zero_budget(self):
        arr = eval_c(role="coding_evaluation")
        self.assertEqual(
            selected(arr, "kimi-api").disposition,
            "NOT_SUSTAINABLY_FREE_API",
        )
        arr = eval_c(role="fast_model_comparison")
        self.assertEqual(
            selected(arr, "cerebras-inference").disposition,
            "NOT_SUSTAINABLY_FREE_API",
        )

    def test_model_catalog_does_not_store_credentials(self):
        cat = catalog()
        all_keys = json.dumps(cat).lower()
        for dangerous in ('"api_key"', '"token"', '"password"', '"secret_key"'):
            self.assertNotIn(dangerous, all_keys)
        self.assertFalse(cat["default_enabled"])


if __name__ == "__main__":
    unittest.main()
