"""Non-executing vehicle diagnostic interface planner for INVENTHOR Main.

A vehicle may support OBD-II, UDS over CAN, DoIP, J2534/OEM service,
J1939, or another verified manufacturer interface. Support must be discovered
per vehicle and connected adapter; model/year alone cannot establish it.
Never transmits a bus frame, writes a module, clears a DTC or connects hardware.
"""
from __future__ import annotations

from dataclasses import dataclass


READ_SERVICES = frozenset({
    "DISCOVER", "READ_IDENTIFICATION", "READ_DTC", "READ_FREEZE_FRAME",
    "READ_LIVE_DATA", "READ_OEM_MODULE_STATUS",
})
CHANGE_SERVICES = frozenset({
    "CLEAR_DTC", "SERVICE_RESET", "ACTUATOR_TEST", "CALIBRATION",
    "ADAPTATION", "ECU_CODING", "ECU_PROGRAMMING", "SECURITY_SERVICE",
})
ALL_SERVICES = READ_SERVICES | CHANGE_SERVICES
INTERFACES = frozenset({
    "OBD_GENERIC", "OBDONUDS", "UDS_CAN", "DOIP", "J2534",
    "J1939", "OEM_TOOL", "OTHER_VERIFIED",
})
SAFETY_AREAS = frozenset({
    "BRAKES", "STEERING", "AIRBAG_SRS", "ADAS", "POWERTRAIN_CONTROL",
    "HIGH_VOLTAGE_SYSTEM", "IMMOBILIZER_SECURITY", "UNKNOWN_CRITICAL",
})


@dataclass(frozen=True)
class VehicleDiagnosticContext:
    session_id: str
    requested_service: str
    interface_type: str
    main_session_authorized: bool
    user_consented_to_link: bool
    adapter_identified: bool
    adapter_trusted: bool
    vehicle_identified: bool
    vehicle_revision_confirmed: bool
    service_supported_by_adapter_and_vehicle: bool
    # Link and policy attributes are assertions that a real Main host must
    # verify independently. This helper cannot attest them.
    vehicle_stationary_verified: bool = False
    safety_area: str | None = None
    service_document_verified: bool = False
    explicit_owner_approval: bool = False
    authorized_oem_access: bool = False
    qualified_technician_present: bool = False
    stable_power_supply_verified: bool = False
    recovery_plan_verified: bool = False


@dataclass(frozen=True)
class VehicleDiagnosticAdvice:
    status: str
    next_step: str
    reason: str
    read_only: bool
    requires_real_host_attestation: bool = True
    may_execute: bool = False
    may_send_vehicle_commands: bool = False
    may_claim_connection_active: bool = False
    may_claim_dtc_cause_proven: bool = False
    source_only: bool = True


def plan_vehicle_diagnostic(context: VehicleDiagnosticContext) -> VehicleDiagnosticAdvice:
    """Recommend a scoped service plan; never authorizes or issues ECU commands."""
    def result(state: str, next_step: str, reason: str,
               read_only: bool) -> VehicleDiagnosticAdvice:
        return VehicleDiagnosticAdvice(state, next_step, reason, read_only)

    if not isinstance(context, VehicleDiagnosticContext):
        return result("BLOCKED", "NONE", "INVALID_CONTEXT", False)
    if not isinstance(context.session_id, str) or not 0 < len(context.session_id.strip()) <= 128:
        return result("BLOCKED", "NONE", "INVALID_SESSION", False)
    if context.requested_service not in ALL_SERVICES:
        return result("BLOCKED", "NONE", "UNKNOWN_SERVICE", False)
    is_read = context.requested_service in READ_SERVICES
    if context.interface_type not in INTERFACES:
        return result("REVIEW_REQUIRED", "IDENTIFY_INTERFACE",
                      "INTERFACE_NOT_VERIFIED", is_read)
    booleans = (
        context.main_session_authorized, context.user_consented_to_link,
        context.adapter_identified, context.adapter_trusted, context.vehicle_identified,
        context.vehicle_revision_confirmed, context.service_supported_by_adapter_and_vehicle,
        context.vehicle_stationary_verified, context.service_document_verified,
        context.explicit_owner_approval, context.authorized_oem_access,
        context.qualified_technician_present,
        context.stable_power_supply_verified, context.recovery_plan_verified,
    )
    if any(type(b) is not bool for b in booleans):
        return result("BLOCKED", "NONE", "INVALID_TRUST_FLAGS", is_read)
    if context.safety_area is not None and context.safety_area not in SAFETY_AREAS:
        return result("REVIEW_REQUIRED", "CLASSIFY_SAFETY_AREA",
                      "INVALID_SAFETY_CLASSIFICATION", is_read)
    if not context.main_session_authorized:
        return result("BLOCKED", "AUTHORIZE_MAIN_SESSION",
                      "MAIN_SESSION_UNAUTHORIZED", is_read)
    if not context.user_consented_to_link:
        return result("BLOCKED", "REQUEST_VEHICLE_LINK_CONSENT",
                      "VEHICLE_ACCESS_NOT_CONSENTED", is_read)
    if not context.adapter_identified or not context.adapter_trusted:
        return result("REVIEW_REQUIRED", "VERIFY_ADAPTER",
                      "ADAPTER_IDENTITY_OR_TRUST_MISSING", is_read)
    if not context.vehicle_identified or not context.vehicle_revision_confirmed:
        return result("REVIEW_REQUIRED", "VERIFY_VEHICLE_AND_VARIANT",
                      "VEHICLE_VARIANT_NOT_VERIFIED", is_read)
    if not context.service_supported_by_adapter_and_vehicle:
        return result("UNSUPPORTED_HERE", "LOOK_UP_COMPATIBLE_INTERFACE",
                      "SERVICE_NOT_SUPPORTED_BY_THIS_LINK", is_read)

    if is_read:
        return result("HOST_REVIEW_REQUIRED", "PREPARE_SCOPED_READ_SESSION",
                      "READ_PLAN_READY_HOST_MUST_ATTEST", True)

    # Advanced functionality remains in the architecture (coding, resets,
    # programming, actuator tests), but is never dispatched by text/model.
    if not context.vehicle_stationary_verified:
        return result("REVIEW_REQUIRED", "VERIFY_SAFE_VEHICLE_STATE",
                      "VEHICLE_STATE_NOT_VERIFIED", False)
    if not context.service_document_verified:
        return result("REVIEW_REQUIRED", "GET_VERIFIED_SERVICE_PROCEDURE",
                      "SERVICE_PROCEDURE_NOT_VERIFIED", False)
    if not context.explicit_owner_approval:
        return result("BLOCKED", "REQUEST_EXACT_ACTION_APPROVAL",
                      "EXPLICIT_CHANGE_APPROVAL_REQUIRED", False)
    if not context.authorized_oem_access:
        return result("REVIEW_REQUIRED", "VERIFY_MANUFACTURER_ACCESS",
                      "OEM_SECURITY_ACCESS_NOT_VERIFIED", False)
    if context.safety_area is not None and not context.qualified_technician_present:
        return result("SPECIALIST_REVIEW", "ARRANGE_QUALIFIED_SUPERVISION",
                      "SAFETY_CRITICAL_SYSTEM", False)
    if context.requested_service == "ECU_PROGRAMMING" and (
        not context.stable_power_supply_verified or not context.recovery_plan_verified
    ):
        return result("REVIEW_REQUIRED", "VERIFY_STABLE_POWER_AND_RECOVERY",
                      "PROGRAMMING_RECOVERY_NOT_READY", False)
    return result("HOST_REVIEW_REQUIRED", "PREPARE_SCOPED_MANUFACTURER_WORKFLOW",
                  "NO_BUS_WRITE_UNTIL_REAL_HOST_APPROVES", False)
