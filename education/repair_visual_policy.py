"""Visual selection policy for INVENTHOR Main's repair guidance (source-only).

The policy decides IF a repair step benefits from an illustration and its
provenance. It does NOT inspect photos, operate a camera, generate an image,
certify a schematic, identify PCB pads, authorize electrical work, or route
tasks. The actual Main host must independently verify input facts and consent.
"""
from __future__ import annotations

from dataclasses import dataclass

# Opaque categorical statuses; no user text or private filenames are returned.
HAZARDS = frozenset({
    "MAINS_POWER", "ENERGIZED", "HIGH_VOLTAGE", "UNKNOWN_STORED_ENERGY",
    "LARGE_CAPACITOR", "SWOLLEN_BATTERY", "DAMAGED_LITHIUM_CELL",
    "BATTERY_LEAK", "FIRE_SMOKE", "EXPOSED_WIRING",
    "GAS_LEAK", "PRESSURIZED_SYSTEM", "MOVING_MACHINERY",
    "CRITICAL_BRAKE_STEERING", "HYBRID_EV_HV", "LIFTING_OR_CRUSH_HAZARD",
    "UNKNOWN_HAZARD",
})
VISUAL_GOALS = frozenset({
    "GENERAL_CONCEPT", "PART_IDENTIFICATION", "COMPONENT_LOCATION",
    "CIRCUIT_CONNECTION", "CONNECTOR_PINOUT", "MEASUREMENT_POINT",
    "DISASSEMBLY_ORIENTATION",
})
# Invented schematics, connector numbering, test points and physical locations
# are never an acceptable fallback for missing factual source imagery.
PRECISE_GOALS = frozenset({
    "COMPONENT_LOCATION", "CIRCUIT_CONNECTION", "CONNECTOR_PINOUT",
    "MEASUREMENT_POINT", "DISASSEMBLY_ORIENTATION",
})


@dataclass(frozen=True)
class RepairVisualContext:
    """Host-supplied facts about ONE guidance step; no raw photo/audio data."""

    case_id: str
    step_id: str
    authorized_session: bool
    needs_visual: bool
    visual_goal: str
    device_identity_verified: bool = False
    device_revision_verified: bool = False
    user_photo_exists: bool = False
    user_photo_authorized: bool = False
    photo_shows_required_area: bool = False
    verified_service_visual_exists: bool = False
    approved_existing_visual_sufficient: bool = False
    low_risk_disconnected: bool = False
    hazard_flags: tuple[str, ...] = ()
    illustration_adds_clarity: bool = False
    domain: str = "ELECTRONICS"


@dataclass(frozen=True)
class RepairVisualAdvice:
    status: str
    next_visual_action: str
    reason: str
    can_generate_illustrative_image: bool = False
    image_must_be_labeled_illustrative: bool = True
    may_instruct_physical_repair: bool = False
    may_claim_hardware_verified: bool = False
    may_access_camera: bool = False
    may_upload_photo: bool = False
    may_edit_original_photo: bool = False
    source_only: bool = True


def choose_repair_visual(context: RepairVisualContext) -> RepairVisualAdvice:
    """Choose the least-fabricated visual for one Main-authorized guidance step.

    * Source photo or verified service visual beats generated art.
    * Low-risk, generic CONCEPT illustrations may be generated ONLY when
      useful and existing sources are insufficient.
    * Precise pinouts, wiring and test locations are never guessed.
    * This never grants camera/network/control/physical-repair permissions.
    """
    def advise(status: str, action: str, reason: str,
               generation: bool = False) -> RepairVisualAdvice:
        return RepairVisualAdvice(status, action, reason, generation)

    if not isinstance(context, RepairVisualContext):
        return advise("BLOCKED", "NO_VISUAL", "INVALID_CONTEXT")
    if any(not isinstance(i, str) or not 0 < len(i.strip()) <= 128
           for i in (context.case_id, context.step_id)):
        return advise("BLOCKED", "NO_VISUAL", "INVALID_SCOPE")
    bools = (
        context.authorized_session, context.needs_visual,
        context.device_identity_verified, context.device_revision_verified,
        context.user_photo_exists, context.user_photo_authorized,
        context.photo_shows_required_area,
        context.verified_service_visual_exists,
        context.approved_existing_visual_sufficient,
        context.low_risk_disconnected, context.illustration_adds_clarity,
    )
    if any(type(x) is not bool for x in bools):
        return advise("BLOCKED", "NO_VISUAL", "INVALID_POLICY_FLAGS")
    if not context.authorized_session:
        return advise("BLOCKED", "NO_VISUAL", "MAIN_AUTHORIZATION_REQUIRED")
    if context.domain not in {
        "ELECTRONICS", "AUTOMOTIVE", "MOTORCYCLE", "BICYCLE",
        "COMPUTER", "PHONE", "TABLET", "HOME_APPLIANCE",
        "HOME_ELECTRICAL", "HVAC", "PLUMBING", "AUDIO",
        "INDUSTRIAL", "POWER_TOOL", "OTHER",
    }:
        return advise("BLOCKED", "NO_VISUAL", "UNKNOWN_REPAIR_DOMAIN")
    if context.visual_goal not in VISUAL_GOALS:
        return advise("BLOCKED", "NO_VISUAL", "UNKNOWN_VISUAL_GOAL")
    if not isinstance(context.hazard_flags, (tuple, list)) or any(
        not isinstance(x, str) or x not in HAZARDS for x in context.hazard_flags
    ):
        return advise("BLOCKED", "NO_VISUAL", "UNKNOWN_HAZARD_STATUS")
    if context.hazard_flags:
        return advise("STOP_REFER", "SAFETY_NOTICE",
                      "ELECTRICAL_OR_BATTERY_HAZARD_REVIEW")
    if not context.low_risk_disconnected:
        return advise("BLOCKED", "SAFE_PRECHECK",
                      "DISCONNECTED_LOW_RISK_STATE_NOT_VERIFIED")
    if context.user_photo_exists and not context.user_photo_authorized:
        return advise("BLOCKED", "REQUEST_PHOTO_CONSENT",
                      "EXISTING_PHOTO_NOT_AUTHORIZED")
    if not context.needs_visual:
        return advise("SOURCE_ADVICE_ONLY", "TEXT_GUIDANCE",
                      "VISUAL_NOT_NEEDED")
    if context.user_photo_exists and context.photo_shows_required_area:
        return advise("SOURCE_ADVICE_ONLY", "ANNOTATE_COPY_OF_USER_PHOTO",
                      "REAL_SOURCE_IMAGE_PREFERRED")
    if (context.verified_service_visual_exists
        and context.device_identity_verified and context.device_revision_verified):
        return advise("SOURCE_ADVICE_ONLY", "SHOW_VERIFIED_SERVICE_VISUAL",
                      "DEVICE_AND_REVISION_SOURCE_MATCH")
    if context.approved_existing_visual_sufficient:
        return advise("SOURCE_ADVICE_ONLY", "REUSE_EXISTING_VISUAL",
                      "NO_GENERATION_REQUIRED")
    if context.visual_goal in PRECISE_GOALS:
        return advise("REVIEW_REQUIRED", "REQUEST_REAL_PHOTO_OR_VERIFIED_MANUAL",
                      "DEVICE_SPECIFIC_GEOMETRY_MUST_NOT_BE_INVENTED")
    if context.illustration_adds_clarity:
        return advise("SOURCE_ADVICE_ONLY", "GENERATE_LABELED_CONCEPT_DIAGRAM",
                      "GENERIC_DIAGRAM_NEEDED_FOR_EXPLANATION", generation=True)
    return advise("SOURCE_ADVICE_ONLY", "TEXT_GUIDANCE",
                  "GENERATION_NOT_JUSTIFIED")
