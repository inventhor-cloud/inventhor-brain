"""Source-only cross-domain diagnostic triage for INVENTHOR Main.

No physical action, tool command, device data access, or generated-media action
is performed. Main must independently authorize the user, validate device
identity, check expertise and risk, and verify actual repair outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass


DOMAINS = frozenset({
    "AUTOMOTIVE", "MOTORCYCLE", "BICYCLE", "COMPUTER", "PHONE",
    "TABLET", "HOME_APPLIANCE", "HOME_ELECTRICAL", "HVAC",
    "PLUMBING", "AUDIO", "INDUSTRIAL", "POWER_TOOL", "OTHER",
})

HIGH_RISK = frozenset({
    "HIGH_VOLTAGE", "MAINS_POWER", "ENERGIZED", "STORED_ENERGY",
    "HYBRID_EV_HV", "BATTERY_THERMAL_EVENT", "FIRE_SMOKE",
    "GAS_LEAK", "REFRIGERANT_RELEASE", "PRESSURIZED_SYSTEM",
    "CRITICAL_BRAKE_STEERING", "LIFTING_OR_CRUSH_HAZARD",
    "MOVING_MACHINERY", "SAFETY_SYSTEM", "UNKNOWN_HAZARD",
})


@dataclass(frozen=True)
class RepairTriageContext:
    case_id: str
    domain: str
    session_authorized: bool
    hazards_assessed: bool
    hazards: tuple[str, ...] = ()
    device_identity_verified: bool = False
    revision_verified: bool = False
    observed_symptom_present: bool = False
    objective_evidence_present: bool = False
    relevant_manual_verified: bool = False
    image_needed: bool = False


@dataclass(frozen=True)
class RepairTriageAdvice:
    status: str
    next_step: str
    reason: str
    may_execute_repair: bool = False
    may_access_device: bool = False
    may_claim_diagnosis: bool = False
    may_generate_visual: bool = False
    source_only: bool = True


def plan_repair_triage(context: RepairTriageContext) -> RepairTriageAdvice:
    """Suggest one safe workflow step, with no implied repair permission."""
    def advise(state: str, step: str, reason: str) -> RepairTriageAdvice:
        return RepairTriageAdvice(state, step, reason)

    if not isinstance(context, RepairTriageContext):
        return advise("BLOCKED", "NONE", "INVALID_CONTEXT")
    if not isinstance(context.case_id, str) or not 0 < len(context.case_id.strip()) <= 128:
        return advise("BLOCKED", "NONE", "INVALID_CASE")
    if context.domain not in DOMAINS:
        return advise("BLOCKED", "NONE", "UNKNOWN_DOMAIN")
    bool_fields = (context.session_authorized, context.hazards_assessed,
                   context.device_identity_verified, context.revision_verified,
                   context.observed_symptom_present, context.objective_evidence_present,
                   context.relevant_manual_verified, context.image_needed)
    if any(type(v) is not bool for v in bool_fields):
        return advise("BLOCKED", "NONE", "INVALID_POLICY_FLAGS")
    if not context.session_authorized:
        return advise("BLOCKED", "AUTHORIZE_SESSION", "MAIN_AUTH_REQUIRED")
    if not context.hazards_assessed:
        return advise("REVIEW_REQUIRED", "ASSESS_HAZARDS", "RISK_NOT_ASSESSED")
    if not isinstance(context.hazards, (tuple, list)) or any(
        not isinstance(h, str) or h not in HIGH_RISK for h in context.hazards
    ):
        return advise("REVIEW_REQUIRED", "ASSESS_HAZARDS", "INVALID_HAZARD_CLASSIFICATION")
    if context.hazards:
        return advise("SPECIALIST_REVIEW", "REFER_TO_QUALIFIED_TECHNICIAN",
                      "HIGH_RISK_REPAIR_REQUIRES_QUALIFIED_OVERSIGHT")
    if not context.device_identity_verified:
        return advise("SOURCE_ADVICE_ONLY", "IDENTIFY_DEVICE", "IDENTITY_UNKNOWN")
    if not context.revision_verified:
        return advise("SOURCE_ADVICE_ONLY", "VERIFY_MODEL_REVISION", "REVISION_UNKNOWN")
    if not context.observed_symptom_present:
        return advise("SOURCE_ADVICE_ONLY", "DOCUMENT_SYMPTOM", "SYMPTOM_MISSING")
    if not context.objective_evidence_present:
        return advise("SOURCE_ADVICE_ONLY", "COLLECT_NONINVASIVE_EVIDENCE",
                      "DIAGNOSIS_NEEDS_EVIDENCE")
    if not context.relevant_manual_verified:
        return advise("SOURCE_ADVICE_ONLY", "VERIFY_REPAIR_DOCUMENTATION",
                      "SERVICE_SOURCE_NOT_VALIDATED")
    if context.image_needed:
        return advise("SOURCE_ADVICE_ONLY", "CONSULT_EXISTING_VISUAL_POLICY",
                      "SELECT_VISUAL_ONLY_IF_USEFUL")
    return advise("SOURCE_ADVICE_ONLY", "PROPOSE_TESTABLE_CAUSES",
                  "MULTIPLE_CAUSES_REQUIRE_CONFIRMATION")
