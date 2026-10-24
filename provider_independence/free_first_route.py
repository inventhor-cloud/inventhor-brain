"""Free-first provider choice in the EXISTING INVENTHOR Brain architecture.

SOURCE ADVICE ONLY: no network request, login, browser/chat automation,
credential, new queue, account connection, purchase, or Provider Gateway here.
The trusted Main host must verify account/model entitlement, privacy clearance
and quotas immediately before each request. AI-created facts are not trusted.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, Sequence

CAPABILITIES = frozenset({"reasoning", "code_assist", "summarize", "research", "classification"})
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")
PROVIDER_RE = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
MAX_CANDIDATES = 16

class FreeRouteDenied(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

@dataclass(frozen=True)
class NativeProviderFact:
    """Host-observed capabilities and model; not a self-asserted LLM response."""
    provider_id: str
    model_id: str
    transport: Literal["LOCAL", "OFFICIAL_API"]
    capabilities: tuple[str, ...]
    state: Literal["READY", "COOLDOWN", "UNAVAILABLE"]
    # Trusted host inspects actual free API tier+endpoint, not chat subscription.
    free_api_eligible: bool
    paid_fallback_disabled: bool
    remaining_free_requests: int
    validated_account: bool
    credential_ready: bool
    # Only local model can receive PRIVATE data; any external receives PUBLIC only.
    approved_for_public_data: bool
    priority: int

@dataclass(frozen=True)
class FreeRoutePolicy:
    requested_capability: str
    data_class: Literal["PUBLIC", "PRIVATE"]
    authorized_provider_ids: tuple[str, ...]
    verified_owner_policy_revision: int
    allow_external_api: bool = False
    forbid_billing: bool = True
    requires_native_provider_recheck: bool = True

@dataclass(frozen=True)
class FreeRouteAdvice:
    chosen_provider_id: str | None
    chosen_model_id: str | None
    reasons: tuple[str, ...]
    denied: tuple[tuple[str, str], ...]
    disposition: str = "READ_ONLY_FREE_FIRST_ADVICE_NOT_DISPATCH"
    can_send_request: bool = False
    can_charge: bool = False
    can_access_secrets: bool = False

def _id(value: str, pattern: re.Pattern[str], code: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise FreeRouteDenied(code)
    return value

def advise_free_provider(
    policy: FreeRoutePolicy,
    candidates: Sequence[NativeProviderFact],
    *,
    native_account_and_policy_verified: bool,
) -> FreeRouteAdvice:
    """Rank FREE/local candidates, never authorize a provider call.

    No API price estimate is fabricated: an account/endpoint must be verified
    by the real native host and each future inference needs fresh validation.
    """
    if native_account_and_policy_verified is not True:
        raise FreeRouteDenied("TRUSTED_PROVIDER_POLICY_REQUIRED")
    if not isinstance(policy, FreeRoutePolicy):
        raise FreeRouteDenied("ROUTE_POLICY_REQUIRED")
    if policy.forbid_billing is not True or policy.requires_native_provider_recheck is not True:
        raise FreeRouteDenied("NO_UNEXPECTED_BILLING_GUARD_REQUIRED")
    if (type(policy.verified_owner_policy_revision) is not int
        or policy.verified_owner_policy_revision < 1):
        raise FreeRouteDenied("POLICY_REVISION_REQUIRED")
    if policy.requested_capability not in CAPABILITIES:
        raise FreeRouteDenied("CAPABILITY_NOT_SUPPORTED")
    if policy.data_class not in ("PUBLIC", "PRIVATE"):
        raise FreeRouteDenied("UNVERIFIED_DATA_CLASS")
    ids = policy.authorized_provider_ids
    if (not isinstance(ids, tuple) or not ids or len(ids) > MAX_CANDIDATES
        or len(set(ids)) != len(ids)):
        raise FreeRouteDenied("APPROVED_PROVIDER_IDS_REQUIRED")
    for identifier in ids:
        _id(identifier, PROVIDER_RE, "INVALID_APPROVED_PROVIDER_ID")
    if not isinstance(candidates, (list, tuple)) or len(candidates) > MAX_CANDIDATES:
        raise FreeRouteDenied("CANDIDATE_LIMIT_EXCEEDED")
    seen = set()
    available = []
    denied = []
    for item in candidates:
        if not isinstance(item, NativeProviderFact):
            raise FreeRouteDenied("INVALID_NATIVE_PROVIDER_RECORD")
        identifier = _id(item.provider_id, PROVIDER_RE, "INVALID_PROVIDER_ID")
        _id(item.model_id, MODEL_RE, "INVALID_PINNED_MODEL_ID")
        if identifier in seen:
            raise FreeRouteDenied("DUPLICATE_PROVIDER_FACT")
        seen.add(identifier)
        if (not isinstance(item.capabilities, tuple)
            or any(x not in CAPABILITIES for x in item.capabilities)):
            raise FreeRouteDenied("INVALID_PROVIDER_CAPABILITIES")
        if type(item.priority) is not int or not 0 <= item.priority <= 10:
            raise FreeRouteDenied("INVALID_NATIVE_PRIORITY")
        if type(item.remaining_free_requests) is not int or item.remaining_free_requests < 0:
            raise FreeRouteDenied("INVALID_QUOTA_REMAINING")
        reason = None
        if identifier not in ids:
            reason = "NOT_OWNER_APPROVED"
        elif item.state != "READY":
            reason = "NOT_READY"
        elif policy.requested_capability not in item.capabilities:
            reason = "CAPABILITY_MISSING"
        elif item.paid_fallback_disabled is not True:
            reason = "PAID_FALLBACK_NOT_DISABLED"
        elif item.transport == "LOCAL":
            # Local models still require a verified installed model, not just a
            # config entry. They must not expose network/service credentials.
            if item.validated_account is not True:
                reason = "LOCAL_MODEL_NOT_VERIFIED"
        elif item.transport == "OFFICIAL_API":
            if policy.data_class != "PUBLIC":
                reason = "PRIVATE_DATA_CANNOT_LEAVE_LOCAL_HOST"
            elif policy.allow_external_api is not True:
                reason = "EXTERNAL_API_NOT_APPROVED"
            elif item.approved_for_public_data is not True:
                reason = "EXTERNAL_DATA_POLICY_NOT_APPROVED"
            elif not (item.free_api_eligible is True
                      and item.remaining_free_requests > 0):
                reason = "NO_VERIFIED_FREE_API_QUOTA"
            elif not (item.validated_account is True and item.credential_ready is True):
                reason = "API_ACCOUNT_NOT_CONNECTED"
        else:
            reason = "UNSUPPORTED_TRANSPORT"
        if reason:
            denied.append((identifier, reason))
        else:
            # FREE/local first; stable choice, no hidden provider fallback.
            available.append((0 if item.transport == "LOCAL" else 1,
                              item.priority, identifier, item.model_id))
    available.sort()
    selected = available[0] if available else None
    reasons = ("OWNER_APPROVED", "ACTUAL_LOCAL_MODEL_OR_FREE_API_QUOTA",
               "NO_BILLING", "NATIVE_RECHECK_BEFORE_EVERY_CALL") if selected else ()
    return FreeRouteAdvice(
        selected[2] if selected else None,
        selected[3] if selected else None,
        reasons, tuple(denied),
    )
