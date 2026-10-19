"""Evidence-aware read-only module/capability inventory for existing Main Organizer.

Consumes independently supplied Main catalog and Windows Operator observation
snapshots. It neither discovers local files nor creates a second registry/router.
"PASS" is an unverified host-supplied CLAIM, not runtime attestation; Main/Quality
Factory must validate the referenced evidence before permitting any action.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
import re

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_CAP = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_STATES = frozenset(("ACTIVE", "INACTIVE", "MISSING", "ERROR"))
_RESULTS = frozenset(("PASS", "FAIL", "UNKNOWN"))
_MAX_ITEMS = 512


def _identity(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _iso(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def _capabilities(value: object, *, nonempty: bool = False) -> tuple[str, ...] | None:
    if (not isinstance(value, list) or len(value) > 64
        or (nonempty and not value)
        or any(not isinstance(c, str) or not _CAP.fullmatch(c) for c in value)):
        return None
    if len(set(value)) != len(value):
        return None
    return tuple(value)


def review_module_inventory(catalog: object, observations: object, *,
                            host_snapshot_revision: str, host_time_iso: str,
                            project_id: str | None = None) -> dict:
    """Return deterministic coverage and ownership gaps, never write authorization.

    All evidence is *referenced*, not verified in this pure function.
    Both source snapshots must be pinned to the same caller-declared host revision.
    """
    def answer(status: str, reason: str = "", modules: list[dict] | None = None,
               issues: list[dict] | None = None) -> dict:
        return {
            "status": status, "reason": reason,
            "modules": modules or [], "issues": issues or [],
            "summary": {
                "catalog_modules": len(modules or []),
                "reported_complete": sum(m["status"] == "REPORTED_COMPLETE"
                                         for m in modules or []),
                "needs_review": sum(m["status"] != "REPORTED_COMPLETE"
                                    for m in modules or []),
                "ambiguous_capabilities": sum(i["reason"] == "AMBIGUOUS_CAPABILITY_OWNER"
                                              for i in issues or []),
            },
            "state": "SOURCE_REFERENCE_ONLY",
            "evidence_trust": "UNATTESTED_HOST_REFERENCES",
            "may_execute": False, "may_install": False,
            "may_claim_live_verified": False,
            "may_update_registry": False, "may_take_ownership": False,
            "requires_main_snapshot_attestation": True,
            "requires_quality_factory_evidence_verification": True,
        }

    if (not isinstance(catalog, Mapping) or not isinstance(observations, Mapping)
        or not isinstance(host_snapshot_revision, str)
        or not host_snapshot_revision or len(host_snapshot_revision) > 128
        or (project_id is not None and not _identity(project_id))):
        return answer("BLOCKED", "INVALID_INVENTORY_ENVELOPE")

    if (type(catalog.get("schema_version")) is not int or
        type(observations.get("schema_version")) is not int or
        catalog.get("schema_version") != 1 or observations.get("schema_version") != 1 or
        catalog.get("system_of_record") != "INVENTHOR_MAIN" or
        observations.get("source") != "WINDOWS_OPERATOR" or
        catalog.get("snapshot_revision") != host_snapshot_revision or
        observations.get("snapshot_revision") != host_snapshot_revision):
        return answer("BLOCKED", "UNPINNED_OR_UNTRUSTED_INVENTORY")

    now = _iso(host_time_iso)
    acquired = _iso(observations.get("captured_at"))
    if now is None or acquired is None:
        return answer("BLOCKED", "INVALID_INVENTORY_TIME")
    age_seconds = (now - acquired).total_seconds()
    if age_seconds < -5 or age_seconds > 120:
        return answer("BLOCKED", "STALE_INVENTORY_OBSERVATION")

    expected = catalog.get("modules")
    observed = observations.get("modules")
    if (not isinstance(expected, list) or not isinstance(observed, list)
        or len(expected) > _MAX_ITEMS or len(observed) > _MAX_ITEMS):
        return answer("BLOCKED", "INVALID_INVENTORY_ITEMS")

    known: dict[tuple[str, str], tuple[str, ...]] = {}
    live: dict[tuple[str, str], tuple[str, dict[str, tuple[str, str]], tuple[str, ...]]] = {}
    for entry in expected:
        if not isinstance(entry, Mapping):
            return answer("BLOCKED", "INVALID_CATALOG_MODULE")
        pid, mid = entry.get("project_id"), entry.get("module_id")
        caps = _capabilities(entry.get("declared_capabilities"), nonempty=True)
        if not _identity(pid) or not _identity(mid) or caps is None:
            return answer("BLOCKED", "INVALID_CATALOG_MODULE")
        key = (pid, mid.casefold())
        if key in known:
            return answer("BLOCKED", "DUPLICATE_CATALOG_MODULE")
        known[key] = caps

    for entry in observed:
        if not isinstance(entry, Mapping):
            return answer("BLOCKED", "INVALID_OPERATOR_OBSERVATION")
        pid, mid = entry.get("project_id"), entry.get("module_id")
        state = entry.get("status")
        capabilities = entry.get("capabilities")
        # Main READY / operatorConnected do not attest each loadable module.
        # An authenticated host must normalize its module heartbeat errors to
        # this per-project row; an absent field is NOT a clean health receipt.
        load_errors = entry.get("load_error_codes", [])
        if (not _identity(pid) or not _identity(mid) or not isinstance(state, str) or state not in _STATES
            or not isinstance(capabilities, list) or len(capabilities) > 64):
            return answer("BLOCKED", "INVALID_OPERATOR_OBSERVATION")
        if (not isinstance(load_errors, list) or len(load_errors) > 16
            or any(not isinstance(code, str) or not _CAP.fullmatch(code)
                   for code in load_errors)
            or len(set(load_errors)) != len(load_errors)):
            return answer("BLOCKED", "INVALID_MODULE_LOAD_ERRORS")
        key = (pid, mid.casefold())
        if key in live:
            return answer("BLOCKED", "DUPLICATE_OPERATOR_OBSERVATION")
        by_cap: dict[str, tuple[str, str]] = {}
        for item in capabilities:
            if not isinstance(item, Mapping):
                return answer("BLOCKED", "INVALID_CAPABILITY_EVIDENCE")
            name, result, evidence = (item.get("name"), item.get("result"),
                                      item.get("evidence_ref"))
            if (not isinstance(name, str) or not _CAP.fullmatch(name)
                or not isinstance(result, str) or result not in _RESULTS
                or (evidence is not None and
                    (not isinstance(evidence, str) or not _REF.fullmatch(evidence)))
                or name in by_cap):
                return answer("BLOCKED", "INVALID_CAPABILITY_EVIDENCE")
            # Only a PASS with an evidence reference is countable as reported.
            # Even then, a trusted host must independently validate the receipt.
            by_cap[name] = (result, evidence or "")
        live[key] = (state, by_cap, tuple(sorted(load_errors)))

    issues: list[dict] = []
    modules: list[dict] = []
    owners: dict[tuple[str, str], list[str]] = defaultdict(list)
    for (pid, mid), (state, evidence, load_errors) in live.items():
        if project_id is not None and pid != project_id:
            continue
        if (pid, mid) not in known:
            issues.append({"project_id": pid, "module_id": mid,
                           "reason": "UNREGISTERED_MODULE_OBSERVATION"})
            continue
        if state == "ACTIVE" and not load_errors:
            for cap, (result, receipt) in evidence.items():
                if result == "PASS" and receipt and cap in known[(pid, mid)]:
                    owners[(pid, cap)].append(mid)

    conflicts = {key: sorted(mids) for key, mids in owners.items() if len(mids) > 1}
    for (pid, cap), mids in sorted(conflicts.items()):
        issues.append({"project_id": pid, "capability": cap,
                       "module_ids": mids, "reason": "AMBIGUOUS_CAPABILITY_OWNER"})

    for (pid, mid), declared in sorted(known.items()):
        if project_id is not None and pid != project_id:
            continue
        observation = live.get((pid, mid))
        state, cap_results, load_errors = observation if observation else ("NOT_REPORTED", {}, ())
        passes = sorted(c for c in declared
                        if state == "ACTIVE" and not load_errors
                        and cap_results.get(c, ())[:1] == ("PASS",)
                        and cap_results[c][1])
        missing = sorted(set(declared) - set(passes))
        unexpected = sorted(set(cap_results) - set(declared))
        ambiguous = sorted(c for c in passes if (pid, c) in conflicts)
        status = ("NOT_REPORTED" if observation is None
                  else "RUNTIME_LOAD_BLOCKED" if load_errors
                  else "INACTIVE" if state != "ACTIVE"
                  else "AMBIGUOUS_OWNER" if ambiguous
                  else "REPORTED_COMPLETE" if not missing and not unexpected
                  else "PARTIAL_OR_UNVERIFIED")
        next_action = {
            "NOT_REPORTED": "REQUEST_FRESH_OPERATOR_INVENTORY",
            "RUNTIME_LOAD_BLOCKED": "REVIEW_OPERATOR_MODULE_LOAD_ISSUES",
            "INACTIVE": "INSPECT_MODULE_RUNTIME_STATE",
            "AMBIGUOUS_OWNER": "ASK_OWNER_TO_SELECT_CAPABILITY_ROUTE",
            "PARTIAL_OR_UNVERIFIED": "RUN_MISSING_CAPABILITY_QA_AND_VERIFY",
            "REPORTED_COMPLETE": "HOST_VALIDATE_REFERENCED_QA_EVIDENCE",
        }[status]
        modules.append({
            "project_id": pid, "module_id": mid, "status": status,
            "declared_count": len(declared), "reported_pass_count": len(passes),
            "missing_or_unverified": missing,
            "undeclared_observed": unexpected,
            "ambiguous_capabilities": ambiguous,
            "next_action": next_action,
            "coverage_basis": "CLAIM_WITH_EVIDENCE_REFERENCE_NOT_ATTESTED",
        })
        if observation is None:
            issues.append({"project_id": pid, "module_id": mid,
                           "reason": "MODULE_OBSERVATION_MISSING"})
        if load_errors:
            issues.append({"project_id": pid, "module_id": mid,
                           "reason": "MODULE_LOAD_ERRORS_REPORTED",
                           "error_codes": list(load_errors)})
        if unexpected:
            issues.append({"project_id": pid, "module_id": mid,
                           "reason": "UNDECLARED_CAPABILITY_CLAIM", "capabilities": unexpected})
        if missing:
            issues.append({"project_id": pid, "module_id": mid,
                           "reason": "CAPABILITY_EVIDENCE_MISSING", "capabilities": missing})

    return answer("SOURCE_COVERAGE_REVIEW", modules=modules, issues=issues)
