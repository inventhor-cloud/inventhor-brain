import unittest
from dataclasses import replace

from provider_independence.free_first_route import (
    FreeRouteDenied, FreeRoutePolicy, NativeProviderFact, advise_free_provider,
)

def policy(**changes):
    d = dict(
        requested_capability="code_assist", data_class="PUBLIC",
        authorized_provider_ids=("ollama_local","gemini_api","groq_api",
                                 "openrouter_api", "claude_api"),
        verified_owner_policy_revision=1, allow_external_api=True,
        forbid_billing=True, requires_native_provider_recheck=True,
    )
    d.update(changes)
    return FreeRoutePolicy(**d)

def provider(identifier="gemini_api", transport="OFFICIAL_API", **changes):
    d = dict(
        provider_id=identifier, model_id="host_verified_model_v1",
        transport=transport, capabilities=("code_assist","summarize"),
        state="READY", free_api_eligible=True, paid_fallback_disabled=True,
        remaining_free_requests=12, validated_account=True,
        credential_ready=True, approved_for_public_data=True, priority=1,
    )
    d.update(changes)
    return NativeProviderFact(**d)

def route(candidates=None, owner=None, verified=True):
    return advise_free_provider(
        policy() if owner is None else owner,
        [provider()] if candidates is None else candidates,
        native_account_and_policy_verified=verified,
    )

class FreeFirstRoutingTests(unittest.TestCase):
    def deny(self, code, **kwargs):
        with self.assertRaises(FreeRouteDenied) as err:
            route(**kwargs)
        self.assertEqual(err.exception.code, code)

    def test_free_api_is_only_a_suggestion(self):
        a = route()
        self.assertEqual(a.chosen_provider_id, "gemini_api")
        self.assertEqual(a.chosen_model_id, "host_verified_model_v1")
        self.assertFalse(a.can_send_request)
        self.assertFalse(a.can_charge)
        self.assertFalse(a.can_access_secrets)

    def test_local_preferred_to_external_when_both_approved(self):
        a = route([
            provider("groq_api", priority=0),
            provider("ollama_local", "LOCAL", model_id="local_model",
                     free_api_eligible=False, remaining_free_requests=0,
                     approved_for_public_data=False, credential_ready=False,
                     priority=10),
        ])
        self.assertEqual(a.chosen_provider_id, "ollama_local")

    def test_free_chat_does_not_imply_free_api(self):
        a = route([provider("claude_api", free_api_eligible=False)])
        self.assertIsNone(a.chosen_provider_id)
        self.assertIn(("claude_api","NO_VERIFIED_FREE_API_QUOTA"), a.denied)

    def test_private_never_leaves_machine(self):
        a = route(
            [provider("gemini_api"), provider("ollama_local","LOCAL")],
            owner=policy(data_class="PRIVATE"))
        self.assertEqual(a.chosen_provider_id,"ollama_local")
        self.assertIn(("gemini_api","PRIVATE_DATA_CANNOT_LEAVE_LOCAL_HOST"),
                      a.denied)

    def test_no_local_model_returns_blocker_not_paid_fallback(self):
        a = route([provider("claude_api",free_api_eligible=False)],
                  owner=policy(data_class="PRIVATE"))
        self.assertIsNone(a.chosen_provider_id)
        self.assertEqual(a.disposition,"READ_ONLY_FREE_FIRST_ADVICE_NOT_DISPATCH")

    def test_free_quota_exhausted(self):
        a = route([provider("groq_api",remaining_free_requests=0)])
        self.assertEqual(a.denied,(("groq_api","NO_VERIFIED_FREE_API_QUOTA"),))
        self.assertIsNone(a.chosen_provider_id)

    def test_paid_fallback_must_be_off(self):
        a = route([provider(paid_fallback_disabled=False)])
        self.assertEqual(a.denied[0][1],"PAID_FALLBACK_NOT_DISABLED")
        self.deny("NO_UNEXPECTED_BILLING_GUARD_REQUIRED",
                  owner=policy(forbid_billing=False))

    def test_consumer_plan_not_connected_to_api(self):
        a = route([provider(validated_account=False)])
        self.assertIn(("gemini_api","API_ACCOUNT_NOT_CONNECTED"),a.denied)
        a = route([provider(credential_ready=False)])
        self.assertIn(("gemini_api","API_ACCOUNT_NOT_CONNECTED"),a.denied)

    def test_local_model_must_be_verified(self):
        a = route([provider("ollama_local","LOCAL",validated_account=False)])
        self.assertIn(("ollama_local","LOCAL_MODEL_NOT_VERIFIED"),a.denied)

    def test_external_data_policy_required(self):
        a = route(owner=policy(allow_external_api=False))
        self.assertIn(("gemini_api","EXTERNAL_API_NOT_APPROVED"),a.denied)
        a = route([provider(approved_for_public_data=False)])
        self.assertIn(("gemini_api","EXTERNAL_DATA_POLICY_NOT_APPROVED"),a.denied)

    def test_native_owner_policy_is_mandatory(self):
        self.deny("TRUSTED_PROVIDER_POLICY_REQUIRED",verified=False)
        self.deny("POLICY_REVISION_REQUIRED",
                  owner=policy(verified_owner_policy_revision=True))
        self.deny("NO_UNEXPECTED_BILLING_GUARD_REQUIRED",
                  owner=policy(requires_native_provider_recheck=False))

    def test_explicit_ids_no_auto_enrollment(self):
        a = route([provider("untrusted_api")])
        self.assertIn(("untrusted_api","NOT_OWNER_APPROVED"),a.denied)
        self.deny("APPROVED_PROVIDER_IDS_REQUIRED",
                  owner=policy(authorized_provider_ids=()))

    def test_duplicate_provider_identity_denied(self):
        self.deny("DUPLICATE_PROVIDER_FACT",
                  candidates=[provider(),provider()])

    def test_rate_limit_facts_not_invented(self):
        self.deny("INVALID_QUOTA_REMAINING",
                  candidates=[provider(remaining_free_requests=-1)])
        self.deny("INVALID_QUOTA_REMAINING",
                  candidates=[provider(remaining_free_requests=True)])

    def test_capability_and_status(self):
        a=route([provider("openrouter_api",capabilities=("research",))])
        self.assertEqual(a.denied[0][1],"CAPABILITY_MISSING")
        a=route([provider(state="COOLDOWN")])
        self.assertEqual(a.denied[0][1],"NOT_READY")

    def test_unknown_model_and_transport_denied(self):
        self.deny("INVALID_PINNED_MODEL_ID",
                  candidates=[provider(model_id="../../ credentials")])
        a=route([provider(transport="UNTRUSTED_WEB_SCRAPER")])
        self.assertEqual(a.denied[0][1],"UNSUPPORTED_TRANSPORT")

    def test_order_is_stable_not_vendor_bias(self):
        a=route([
            provider("openrouter_api",priority=0),
            provider("groq_api",priority=0),
        ])
        self.assertEqual(a.chosen_provider_id,"groq_api")


if __name__ == "__main__":
    unittest.main()
