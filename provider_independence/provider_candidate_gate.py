"""Candidate-only, free-first provider evaluator; no network or credentials.

This is a review tool for the EXISTING INVENTHOR Provider Gateway, not a new
router, dispatcher, provider subscription or runtime installation. Any native
API use requires independently authenticated provider enrollment, quotas,
commercial/data policy review, owner approval and verified local integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

FREE_API_CATEGORIES = frozenset({
    "limited_model_api_free_tier", "rate_limited_free_api",
    "limited_monthly_free_api", "free_models_rate_limited",
    "daily_neuron_allowance", "local_compute_no_api_usage_charge",
})
_ALLOWED_DATA = frozenset({"PUBLIC_SYNTHETIC", "PRIVATE_OWNER", "CUSTOMER_CONFIDENTIAL"})
_ALLOWED_ROLES = frozenset({
    "coding_evaluation", "fast_inference", "model_comparison",
    "nonprivate_prototyping", "text_tasks", "small_jobs",
    "model_prototyping", "private_local_assistance", "offline_fallback",
    "complex_code_review", "architecture", "sourced_research",
})
_ALL_FREE_TYPES = FREE_API_CATEGORIES | frozenset({
    "small_new_user_trial_credit_not_recurring_free_tier",
    "consumer_basic_search_free_api_not_assumed_free",
    "one_time_initial_trial_credit", "pay_as_you_go_api",
})


class CandidateEvaluationDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class EvaluationRequest:
    role: str
    data_class: str
    monthly_spending_allowed: bool = False


@dataclass(frozen=True)
class CandidateAssessment:
    provider_id: str
    disposition: str
    reason: str
    may_send_data: bool = False
    may_call_api: bool = False
    may_activate: bool = False
    requires_native_enrollment: bool = True


def assess_free_candidates(
    catalog: Mapping[str, Any],
    request: EvaluationRequest,
) -> tuple[CandidateAssessment, ...]:
    """Evaluate research options; never automatically invoke any provider."""
    if not isinstance(catalog, Mapping) or catalog.get("authority") != "RESEARCH_ONLY_NOT_INSTALLED_OR_CONNECTED":
        raise CandidateEvaluationDenied("TRUSTED_PROVIDER_CATALOG_REQUIRED")
    if (catalog.get("default_enabled") is not False
        or catalog.get("runtime_authoritative") is not False):
        raise CandidateEvaluationDenied("RESEARCH_CATALOG_CANNOT_ENABLE_RUNTIME")
    if not isinstance(request, EvaluationRequest):
        raise CandidateEvaluationDenied("REQUEST_REQUIRED")
    if request.role not in _ALLOWED_ROLES:
        raise CandidateEvaluationDenied("UNKNOWN_EVALUATION_ROLE")
    if request.data_class not in _ALLOWED_DATA:
        raise CandidateEvaluationDenied("UNKNOWN_DATA_CLASS")
    if type(request.monthly_spending_allowed) is not bool:
        raise CandidateEvaluationDenied("INVALID_SPENDING_POLICY")
    providers = catalog.get("providers")
    if not isinstance(providers, list) or len(providers) > 32:
        raise CandidateEvaluationDenied("INVALID_PROVIDER_CATALOG")
    seen = set()
    result = []
    for item in providers:
        if not isinstance(item, dict):
            raise CandidateEvaluationDenied("MALFORMED_PROVIDER")
        identifier = item.get("id")
        if (not isinstance(identifier, str) or not identifier
            or len(identifier) > 100 or identifier in seen):
            raise CandidateEvaluationDenied("DUPLICATE_OR_INVALID_PROVIDER")
        seen.add(identifier)
        if item.get("status") != "CANDIDATE_DISABLED":
            raise CandidateEvaluationDenied("UNAPPROVED_PROVIDER_ACTIVATION")
        free_type = item.get("free_type")
        if free_type not in _ALL_FREE_TYPES:
            raise CandidateEvaluationDenied("UNKNOWN_FREE_TIER_KIND")
        allowed_roles = item.get("recommended_for")
        if (not isinstance(allowed_roles, list)
            or len(allowed_roles) > 20
            or any(role not in _ALLOWED_ROLES for role in allowed_roles)):
            raise CandidateEvaluationDenied("INVALID_ROLE_LIST")
        kind = item.get("interface")
        if kind not in ("api", "api_aggregator", "local_runtime", "web_research_and_separate_api"):
            raise CandidateEvaluationDenied("INVALID_INTERFACE")
        reason = "SOURCE_CANDIDATE_REQUIRES_NATIVE_ENROLLMENT"
        status = "CANDIDATE_ONLY"
        if request.role not in allowed_roles:
            status, reason = "NOT_RECOMMENDED_FOR_ROLE", "ROLE_NOT_IN_CAPABILITIES"
        elif request.data_class != "PUBLIC_SYNTHETIC" and kind != "local_runtime":
            status, reason = "BLOCKED_PRIVATE_DATA", "DO_NOT_SEND_PRIVATE_DATA_TO_FREE_REMOTE_SERVICE"
        elif kind == "local_runtime" and request.data_class != "PUBLIC_SYNTHETIC" and item.get("privacy") != "local_only_when_cloud_features_disabled_and_data_stays_on_machine":
            status, reason = "BLOCKED_LOCAL_PRIVACY_NOT_VERIFIED", "PRIVATE_LOCAL_MODE_REQUIRED"
        elif free_type not in FREE_API_CATEGORIES:
            status, reason = "NOT_SUSTAINABLY_FREE_API", "TRIAL_WEB_ONLY_OR_PAY_AS_YOU_GO"
        result.append(CandidateAssessment(identifier, status, reason))
    return tuple(result)
