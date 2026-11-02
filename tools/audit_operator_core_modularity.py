#!/usr/bin/env python3
"""Read-only static audit of Operator's dependency on legacy optional modules.

Usage (on the owner's approved native checkout):
    python tools/audit_operator_core_modularity.py /path/to/inventhor-operator-core

This examines source text only, not installed Windows state, dependency graph
completeness, native Organizer lease, QA verdict or deployment authorization.
Run a real zero-plugin-directory smoke test separately, on the trusted host.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
import re


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    line: int
    note: str


# Production-path signatures observed at 2026-10-26 Operator PR #3 SHA
# 37ff1010aa5f55240a4324eafe5b3d5d45270e49.
# These are regression indicators, not a full dataflow or native runtime test.
PATTERNS: tuple[tuple[str, str, str, str], ...] = (
    (
        "windows/src/Inventhor.Operator.Service/OperatorWorker.cs",
        r"pluginCatalog\s*\.\s*Load\s*\(\s*modulesRoot\s*\)",
        "SERVICE_LOADS_LEGACY_PLUGIN_CATALOG",
        "Core worker obtains its runtime executors/transports from plugin root.",
    ),
    (
        "windows/src/Inventhor.Operator.Service/OperatorWorker.cs",
        r"plugins\s*\.\s*Where\s*\(\s*p\s*=>\s*p\.Executor",
        "CORE_EXECUTORS_FROM_PLUGINS",
        "Core execution path is populated exclusively from legacy plugin objects.",
    ),
    (
        "windows/src/Inventhor.Operator.Service/OperatorWorker.cs",
        r"plugins\s*\.\s*Where\s*\(\s*p\s*=>\s*p\.Transport",
        "CORE_TRANSPORTS_FROM_PLUGINS",
        "Brain/Operator transport is launched from legacy plugin objects.",
    ),
    (
        "windows/src/Inventhor.Operator.Service/Program.cs",
        r"AddSingleton\s*<\s*PluginCatalog\s*>",
        "CORE_SERVICE_REGISTERS_LEGACY_CATALOG",
        "Native service still registers legacy runtime plugin discovery.",
    ),
    (
        "windows/src/Inventhor.Operator.Core/TaskEngine.cs",
        r"\bCAPABILITY_UNAVAILABLE\b",
        "CORE_TASK_ENGINE_FAILS_IF_NO_EXECUTOR",
        "Check native empty-plugin core-operation acceptance, not just heartbeat.",
    ),
    (
        "windows/bootstrap/Build-Deploy-V2_1.ps1",
        r"(?i)===\s*BUILD MODULES\s*===",
        "DEPLOY_PUBLISHES_LEGACY_MODULE_SET",
        "Installer/build path explicitly publishes old module packages.",
    ),
    (
        "windows/bootstrap/Build-Deploy-V2_1.ps1",
        r"(?i)modules\s*\)\.Count\s*-lt\s*16",
        "DEPLOY_REQUIRES_SIXTEEN_MODULES",
        "Legacy module count is an unacceptable core release gate.",
    ),
    (
        "windows/bootstrap/Build-Deploy-V2_1.ps1",
        r"(?i)capabilities\s*\)\.Count\s*-lt\s*41",
        "DEPLOY_REQUIRES_LEGACY_CAPABILITY_COUNT",
        "Legacy module capability counts are an unacceptable core release gate.",
    ),
    (
        "windows/src/Inventhor.Operator.Desktop/MainWindow.Modules.cs",
        r'EnterRoute\s*\(\s*"operator:modules"\s*\)',
        "DESKTOP_EXPOSES_LEGACY_MODULE_CENTER",
        "Legacy module UI route must not remain in the final five-system product.",
    ),
)

MANDATORY_FILES = tuple(sorted({entry[0] for entry in PATTERNS}))


def audit_source(root: Path) -> dict:
    """Deterministic read-only check. Missing sources make the result UNKNOWN."""
    findings: list[Finding] = []
    missing: list[str] = []
    if not root.is_dir():
        return {"status": "SOURCE_UNAVAILABLE", "checked_files": 0,
                "missing_files": list(MANDATORY_FILES),
                "findings": [], "native_clean_boot_verified": False}
    sources: dict[str, str] = {}
    for name in MANDATORY_FILES:
        path = root / name
        try:
            if not path.is_file():
                raise OSError("missing")
            sources[name] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            missing.append(name)
    for name, pattern, code, note in PATTERNS:
        if name not in sources:
            continue
        match = re.search(pattern, sources[name], flags=re.MULTILINE)
        if match:
            findings.append(Finding(
                code=code, path=name,
                line=sources[name].count("\n", 0, match.start()) + 1,
                note=note,
            ))
    return {
        "status": ("SOURCE_INCOMPLETE" if missing else
                   "SOURCE_COUPLING_DETECTED" if findings else
                   "STATIC_SOURCE_SIGNATURES_CLEAN_NATIVE_VALIDATION_REQUIRED"),
        "checked_files": len(sources),
        "missing_files": missing,
        "findings": [asdict(item) for item in findings],
        "native_clean_boot_verified": False,
        "owner_scope": "INVENTHOR,OPERATOR,ORGANIZER,STUDIO_DESIGN,QA_FACTORY",
        "native_organizer_updated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operator_source_root", type=Path)
    args = parser.parse_args()
    report = audit_source(args.operator_source_root)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"].startswith("STATIC_SOURCE_SIGNATURES_CLEAN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
