"""Owner-directed, open-ended module onboarding *advice* for INVENTHOR Main.

The owner chooses product capabilities. No hardcoded module vendor, domain,
provider, programming language, platform or product-category whitelist exists.
Main's authenticated owner, current revision, source evidence, host grants,
installer and independent QA remain responsible for actual mutations.

Source-only; no loader, scheduler, file access, policy bypass or host claim.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import re

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_CAP = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except (ValueError, OverflowError):
        return None


def review_owner_module_request(request: object, catalog: object, *,
                                host_snapshot_revision: str, host_time_iso: str) -> dict:
    """Produce a non-binding, deterministic owner product-choice plan.

    A CLAIM of being the owner in request data never authenticates identity.
    Authenticated Main host must verify owner intent and existing installed
    sources before mutations. This function cannot deny a product category.
    """
    def response(status: str, reason: str, **values: object) -> dict:
        return {
            "status": status, "reason": reason,
            "policy": "OWNER_CHOOSES_MODULES_OPEN_CATALOG",
            "supported_product_categories": "UNRESTRICTED_BY_THIS_ADVISOR",
            "proposed": values.get("proposed"),
            "existing_module": values.get("existing_module"),
            "capability_overlaps": values.get("capability_overlaps", []),
            "missing_capability_evidence": values.get("missing_capability_evidence", []),
            "source_only": True, "may_install": False,
            "may_write": False, "may_change_security_policy": False,
            "may_claim_owner_authenticated": False,
            "may_grant_capability": False,
            "requires_main_authenticated_owner": True,
            "requires_host_revision_check": True,
            "requires_package_integrity_and_rollback": True,
        }

    if (not isinstance(request, Mapping) or not isinstance(catalog, Mapping)
        or type(catalog.get("schema_version")) is not int
        or catalog.get("schema_version") != 1
        or catalog.get("system_of_record") != "INVENTHOR_MAIN"
        or not isinstance(host_snapshot_revision, str)
        or not 0 < len(host_snapshot_revision) <= 128
        or catalog.get("snapshot_revision") != host_snapshot_revision):
        return response("BLOCKED", "MAIN_CATALOG_SNAPSHOT_INVALID")
    now, captured = _timestamp(host_time_iso), _timestamp(catalog.get("captured_at"))
    if now is None or captured is None or not (-5 <= (now-captured).total_seconds() <= 120):
        return response("BLOCKED", "MAIN_CATALOG_STALE_OR_UNVERSIONED")

    if (request.get("schema_version") != 1
        or request.get("intent") != "OWNER_MODULE_REQUEST"
        or request.get("requester_role") != "OWNER"):
        return response("BLOCKED", "OWNER_INTENT_NOT_IDENTIFIED")
    pid, mid = request.get("project_id"), request.get("module_id")
    if not _valid_id(pid) or not _valid_id(mid):
        return response("BLOCKED", "INVALID_PROJECT_OR_MODULE_ID")
    requested = request.get("capabilities")
    if (not isinstance(requested, list) or not requested or len(requested) > 64
        or any(not isinstance(c, str) or not _CAP.fullmatch(c) for c in requested)
        or len(set(requested)) != len(requested)):
        return response("BLOCKED", "INVALID_CAPABILITY_DECLARATION")
    evidence = request.get("source_evidence_refs", [])
    if (not isinstance(evidence, list) or len(evidence) > 32
        or any(not isinstance(v, str) or not _REF.fullmatch(v) for v in evidence)):
        return response("BLOCKED", "INVALID_EVIDENCE_REFERENCES")
    if not isinstance(catalog.get("modules"), list) or len(catalog["modules"]) > 512:
        return response("BLOCKED", "INVALID_CATALOG_ROWS")

    # Catalog is host-owned; duplicate identity is a data-quality failure, not
    # permission to silently overwrite an existing module's implementation.
    known: dict[tuple[str, str], Mapping] = {}
    for row in catalog["modules"]:
        if not isinstance(row, Mapping):
            return response("BLOCKED", "INVALID_CATALOG_ROW")
        project, name = row.get("project_id"), row.get("module_id")
        caps = row.get("declared_capabilities")
        if (not _valid_id(project) or not _valid_id(name)
            or not isinstance(caps, list) or len(caps) > 64
            or any(not isinstance(c, str) or not _CAP.fullmatch(c) for c in caps)
            or len(set(caps)) != len(caps)):
            return response("BLOCKED", "INVALID_CATALOG_ROW")
        key = (project, name.casefold())
        if key in known:
            return response("BLOCKED", "DUPLICATE_CANONICAL_MODULE")
        known[key] = row

    present = known.get((pid, mid.casefold()))
    overlaps: list[dict] = []
    for (p, m), row in known.items():
        if p == pid and m != mid.casefold():
            same = sorted(set(requested) & set(row["declared_capabilities"]))
            if same:
                overlaps.append({
                    "existing_module_id": row["module_id"],
                    "capabilities": same,
                    "next_action": "REVIEW_OWNER_PREFERRED_CAPABILITY_ROUTE",
                })
    overlaps.sort(key=lambda x: x["existing_module_id"].casefold())
    proposed = {
        "project_id": pid,
        "module_id": mid,
        "requested_capabilities": sorted(requested),
        "source_evidence_reference_count": len(evidence),
        "new_module": present is None,
        "owner_has_final_product_choice": True,
    }
    if present is not None:
        existing_capabilities = set(present["declared_capabilities"])
        new = sorted(set(requested) - existing_capabilities)
        return response(
            "REVIEW_EXISTING_MODULE_EXTENSION", "NO_DUPLICATE_MODULE_CREATION",
            proposed=proposed,
            existing_module={"module_id": present["module_id"],
                             "existing_capabilities": sorted(existing_capabilities)},
            missing_capability_evidence=new, capability_overlaps=overlaps,
        )
    return response(
        "OWNER_CHOICE_READY_FOR_HOST_VALIDATION",
        "CUSTOM_MODULE_CATEGORY_NOT_RESTRICTED",
        proposed=proposed,
        missing_capability_evidence=sorted(requested) if not evidence else [],
        capability_overlaps=overlaps,
    )
