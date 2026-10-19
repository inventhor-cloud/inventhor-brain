"""Cross-platform wired/wireless vehicle-adapter link selection (source only).

INVENTHOR Main owns the single diagnostic session. Platform adapters may
eventually use Android Bluetooth/USB, iOS BLE/ExternalAccessory/network,
Windows/Linux USB/serial/Bluetooth/network, J2534/OEM bridges, etc.
No real driver, socket, accessory, Bluetooth scan, connection or ECU command
is implemented or authorized by this module.

Hardware compatibility is NOT inferred from operating system or plug shape:
the trusted host must attest each adapter+device+driver/protocol combination.
"""
from __future__ import annotations

from dataclasses import dataclass

PLATFORMS = frozenset({"ANDROID", "IOS", "WINDOWS", "LINUX", "MACOS"})
KINDS = {
    "USB_SERIAL": "WIRED",
    "USB_VENDOR": "WIRED",
    "J2534_USB": "WIRED",
    "ETHERNET": "WIRED",
    "BLUETOOTH_LE": "WIRELESS",
    "BLUETOOTH_CLASSIC": "WIRELESS",
    "WIFI": "WIRELESS",
    "WIFI_DIRECT": "WIRELESS",
}
PREFERENCES = frozenset({"AUTO", "WIRED", "WIRELESS"})
# A connection attempt is owned by a platform-specific adapter, never by
# the AI response or this decision helper.
_ORDER = ("USB_SERIAL", "J2534_USB", "USB_VENDOR", "ETHERNET",
          "BLUETOOTH_LE", "WIFI", "WIFI_DIRECT", "BLUETOOTH_CLASSIC")


@dataclass(frozen=True)
class LinkOption:
    kind: str
    adapter_supports_link: bool
    host_driver_or_api_available: bool
    app_permission_granted: bool
    accessory_protocol_verified: bool
    link_ready: bool
    read_service_supported: bool
    # The host MUST attest this using real device/vendor evidence. The
    # declaration alone does not make the connection trustworthy.
    host_compatibility_attested: bool = False
    platform_accessory_authorized: bool = False


@dataclass(frozen=True)
class VehicleLinkContext:
    session_id: str
    platform: str
    preference: str
    main_authorized: bool
    user_consented: bool
    adapter_identity_verified: bool
    vehicle_identity_verified: bool
    options: tuple[LinkOption, ...]


@dataclass(frozen=True)
class VehicleLinkAdvice:
    status: str
    next_step: str
    reason: str
    selected_kind: str | None = None
    selected_medium: str | None = None
    alternative_kinds: tuple[str, ...] = ()
    requires_real_host_attestation: bool = True
    may_open_connection: bool = False
    may_send_vehicle_commands: bool = False
    may_claim_device_visible: bool = False
    may_claim_connected: bool = False
    source_only: bool = True


def plan_vehicle_link(ctx: VehicleLinkContext) -> VehicleLinkAdvice:
    """Pick compatible already-*attested* link candidates; no device I/O."""
    def out(status: str, step: str, reason: str, kind: str | None = None,
            alternatives: tuple[str, ...] = ()) -> VehicleLinkAdvice:
        return VehicleLinkAdvice(
            status, step, reason, kind, KINDS.get(kind) if kind else None,
            alternatives
        )

    if not isinstance(ctx, VehicleLinkContext):
        return out("BLOCKED", "NONE", "INVALID_CONTEXT")
    if not isinstance(ctx.session_id, str) or not 0 < len(ctx.session_id.strip()) <= 128:
        return out("BLOCKED", "NONE", "INVALID_SESSION")
    if ctx.platform not in PLATFORMS:
        return out("REVIEW_REQUIRED", "VERIFY_PLATFORM", "UNKNOWN_PLATFORM")
    if ctx.preference not in PREFERENCES:
        return out("BLOCKED", "NONE", "INVALID_PREFERENCE")
    if any(type(x) is not bool for x in (
        ctx.main_authorized, ctx.user_consented, ctx.adapter_identity_verified,
        ctx.vehicle_identity_verified,
    )):
        return out("BLOCKED", "NONE", "INVALID_AUTH_FLAGS")
    if not ctx.main_authorized:
        return out("BLOCKED", "AUTHORIZE_MAIN", "MAIN_AUTHORIZATION_REQUIRED")
    if not ctx.user_consented:
        return out("BLOCKED", "REQUEST_LINK_CONSENT", "USER_LINK_CONSENT_REQUIRED")
    if not ctx.adapter_identity_verified:
        return out("REVIEW_REQUIRED", "IDENTIFY_ADAPTER", "ADAPTER_NOT_VERIFIED")
    if not ctx.vehicle_identity_verified:
        return out("REVIEW_REQUIRED", "IDENTIFY_VEHICLE", "VEHICLE_NOT_VERIFIED")
    if not isinstance(ctx.options, (tuple, list)) or len(ctx.options) > len(KINDS):
        return out("BLOCKED", "NONE", "INVALID_OPTIONS")

    options: dict[str, LinkOption] = {}
    for option in ctx.options:
        if not isinstance(option, LinkOption) or option.kind not in KINDS:
            return out("BLOCKED", "NONE", "UNKNOWN_LINK_TYPE")
        if option.kind in options:
            return out("BLOCKED", "NONE", "DUPLICATE_LINK_DECLARATION")
        flags = (
            option.adapter_supports_link, option.host_driver_or_api_available,
            option.app_permission_granted, option.accessory_protocol_verified,
            option.link_ready, option.read_service_supported,
            option.host_compatibility_attested,
            option.platform_accessory_authorized,
        )
        if any(type(v) is not bool for v in flags):
            return out("BLOCKED", "NONE", "INVALID_LINK_FLAGS")
        options[option.kind] = option

    if not options:
        return out("REVIEW_REQUIRED", "DISCOVER_LINKS", "NO_ADAPTER_LINK_DECLARED")

    eligible: list[str] = []
    for kind in _ORDER:
        if kind not in options:
            continue
        option = options[kind]
        if not all((
            option.adapter_supports_link, option.host_driver_or_api_available,
            option.app_permission_granted, option.accessory_protocol_verified,
            option.link_ready, option.read_service_supported,
            option.host_compatibility_attested,
        )):
            continue
        # iOS accessory protocols and drivers are NOT automatically equivalent
        # to generic desktop serial or commodity Classic Bluetooth. The actual
        # device/app entitlement must be confirmed before offering a candidate.
        if ctx.platform == "IOS" and kind in (
            "BLUETOOTH_CLASSIC", "USB_SERIAL", "USB_VENDOR", "J2534_USB"
        ) and not option.platform_accessory_authorized:
            continue
        eligible.append(kind)

    if ctx.preference != "AUTO":
        eligible = [kind for kind in eligible if KINDS[kind] == ctx.preference]
    if not eligible:
        return out("REVIEW_REQUIRED", "VERIFY_LINK_OR_CHOOSE_ANOTHER_MEDIUM",
                   "NO_COMPATIBLE_ATTESTED_LINK")
    return out("SOURCE_PLAN_ONLY", "PREPARE_SELECTED_PLATFORM_ADAPTER",
               "HOST_MUST_OPEN_AND_VALIDATE_CONNECTION",
               eligible[0], tuple(eligible[1:]))
