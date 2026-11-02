"""Advisory diff auditor for INVENTHOR's protected native host entrypoints.

Accepts a LIST OF CHANGED PATHS (e.g., GitHub PR diff). Does not read the
owner PC, acquire a lease, mutate code, revert changes or approve a release.
A changed entrypoint is an architectural review trigger, NOT an instruction
to forbid an owner's feature request or to blindly delete a necessary fix.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
import sys

_SOURCE_ONLY = "SOURCE_DIFF_ONLY_NOT_OWNER_PC_OR_NATIVE_VERIFICATION"
_DRIVE = re.compile(r"^[A-Za-z]:")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_FROZEN_BASENAMES = frozenset({
    "mainactivity.java", "mainactivity.kt",
    "operatorcoreactivity.java", "operatorcoreactivity.kt",
    "mainwindow.xaml", "mainwindow.xaml.cs",
    "app.xaml", "app.xaml.cs",
})
_CORE_REVIEW_BASENAMES = frozenset({
    "operatorworker.cs", "plugincatalog.cs", "taskengine.cs",
    "program.cs", "androidmanifest.xml",
})


class CoreBoundaryInputInvalid(ValueError):
    """A supplied diff cannot be trusted even as a list of relative paths."""


@dataclass(frozen=True)
class HostTouch:
    path: str
    classification: str
    required_next_action: str


@dataclass(frozen=True)
class ProtectedHostDiffAdvice:
    disposition: str
    touches: tuple[HostTouch, ...]
    frozen_entrypoints_touched: int
    core_host_paths_touched: int
    source_class: str = _SOURCE_ONLY
    native_owner_lease_verified: bool = False
    owner_pc_current_sources_verified: bool = False
    safe_to_merge_or_deploy: bool = False
    automatic_revert_allowed: bool = False


def _relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise CoreBoundaryInputInvalid("INVALID_CHANGED_PATH")
    if _CONTROL.search(value):
        raise CoreBoundaryInputInvalid("INVALID_CHANGED_PATH")
    # Windows, Android and GitHub path separators are accepted for review,
    # but ambiguous/absolute/traversal paths must fail closed.
    path = value.replace("\\", "/")
    if (path.startswith("/") or _DRIVE.match(path)
        or any(part in ("", ".", "..") for part in path.split("/"))):
        raise CoreBoundaryInputInvalid("NON_CANONICAL_CHANGED_PATH")
    return path


def inspect_protected_host_diff(changed_paths: tuple[str, ...]) -> ProtectedHostDiffAdvice:
    """Classify one supplied source diff, NEVER assert native installed status.

    The five existing systems are not replaced. Gateway/Aggregator/Tree
    adapter work can proceed outside frozen native entrypoints; even a
    necessary entrypoint bug fix requires native review, not auto-deletion.
    """
    if not isinstance(changed_paths, tuple):
        raise CoreBoundaryInputInvalid("CHANGED_PATHS_TUPLE_REQUIRED")
    seen: set[str] = set()
    touches: list[HostTouch] = []
    frozen = 0
    reviewed = 0
    for raw in changed_paths:
        path = _relative_path(raw)
        normalized = path.casefold()
        if normalized in seen:
            raise CoreBoundaryInputInvalid("DUPLICATE_CHANGED_PATH")
        seen.add(normalized)
        basename = normalized.rsplit("/", 1)[-1]
        if basename in _FROZEN_BASENAMES:
            frozen += 1
            touches.append(HostTouch(
                path, "PROTECTED_NATIVE_ENTRYPOINT_TOUCHED",
                "REVIEW_EXACT_DIFF_AND_MOVE_FEATURE_LOGIC_TO_EXISTING_GATEWAY_AGGREGATOR_TREE",
            ))
        elif (basename in _CORE_REVIEW_BASENAMES
              or basename.startswith("mainwindow.")):
            reviewed += 1
            touches.append(HostTouch(
                path, "CORE_HOST_OR_EXTENSION_REVIEW_REQUIRED",
                "VERIFY_EXISTING_CORE_INTERFACE_AND_NATIVE_CODEX_LEASE_BEFORE_REFACTOR",
            ))
        else:
            touches.append(HostTouch(
                path, "NO_PROTECTED_ENTRYPOINT_NAME_MATCH",
                "NORMAL_SOURCE_REVIEW_ONLY",
            ))
    return ProtectedHostDiffAdvice(
        disposition=(
            "PROTECTED_ENTRYPOINT_REVIEW_REQUIRED" if frozen else
            "CORE_HOST_REVIEW_REQUIRED" if reviewed else
            "NO_PROTECTED_PATHS_IN_SUPPLIED_DIFF"
        ),
        touches=tuple(touches),
        frozen_entrypoints_touched=frozen,
        core_host_paths_touched=reviewed,
    )


# Patch hunks provide evidence of WHERE a host change occurred. They are
# never a code-semantics proof, a rollback instruction or permission to edit.
_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$")
_MAX_PATCH_BYTES = 262144
_MAX_PATCH_FILES = 128
_MAX_HUNKS = 1024


@dataclass(frozen=True)
class HostHunkEvidence:
    path: str
    old_start_line: int
    new_start_line: int
    context: str
    added_lines: int
    removed_lines: int
    review_signals: tuple[str, ...]
    source_class: str = _SOURCE_ONLY


def inspect_protected_host_hunks(
    patches: tuple[tuple[str, str | None], ...],
) -> tuple[HostHunkEvidence, ...]:
    """Inspect the supplied PR patch, not the owner's installed native files.

    Each path is checked using the same frozen-host policy as the ordinary
    filename audit. A missing/truncated/binary patch is REQUIRES_MANUAL_DIFF,
    never silently treated as zero changes. Signals identify review targets;
    they do not establish that particular code should be deleted or moved.
    """
    if not isinstance(patches, tuple) or len(patches) > _MAX_PATCH_FILES:
        raise CoreBoundaryInputInvalid("INVALID_PATCH_FILE_LIST")
    names: list[str] = []
    for item in patches:
        if not isinstance(item, tuple) or len(item) != 2:
            raise CoreBoundaryInputInvalid("INVALID_PATCH_ENTRY")
        names.append(item[0])
    review = inspect_protected_host_diff(tuple(names))
    output: list[HostHunkEvidence] = []
    for (raw_path, patch), touch in zip(patches, review.touches):
        if touch.classification == "NO_PROTECTED_ENTRYPOINT_NAME_MATCH":
            continue
        path = _relative_path(raw_path)
        if patch is None:
            output.append(HostHunkEvidence(
                path, 0, 0, "PATCH_UNAVAILABLE", 0, 0,
                ("REQUIRES_MANUAL_DIFF",),
            ))
            continue
        if not isinstance(patch, str) or len(patch.encode("utf-8")) > _MAX_PATCH_BYTES:
            raise CoreBoundaryInputInvalid("INVALID_OR_OVERSIZE_PATCH")
        if "\x00" in patch:
            raise CoreBoundaryInputInvalid("INVALID_OR_OVERSIZE_PATCH")
        # GitHub PR patch payloads are hunk-only. Lines before the first @@
        # may be diff metadata and must never count as an inspected hunk.
        start = None
        context = ""
        added: list[str] = []
        removed = 0
        def flush() -> None:
            if start is None:
                return
            positive = "\n".join(added)
            signals: list[str] = []
            if re.search(r"<[A-Za-z][^\n>]*\bx:Name\s*=", positive):
                signals.append("NAMED_NATIVE_UI_ELEMENT_ADDED")
            if re.search(
                r'\b(?:Click|TextChanged|PreviewKeyDown|SelectionChanged)\s*=\s*"',
                positive,
            ):
                signals.append("NATIVE_UI_EVENT_HOOK_ADDED")
            if "CoreTransportFactory.Create(" in positive:
                signals.append("CORE_TRANSPORT_WIRING_TOUCHED")
            if "pluginCatalog.Load(" in positive:
                signals.append("LEGACY_PLUGIN_LOADER_CALL_REMAINS")
            if "HeartbeatFresh" in positive:
                signals.append("LIVE_STATUS_FRESHNESS_MAPPING_TOUCHED")
            if not signals:
                signals.append("HOST_BEHAVIOR_CHANGE_REVIEW")
            output.append(HostHunkEvidence(
                path, start[0], start[1], context[:160],
                len(added), removed, tuple(signals),
            ))
        for line in patch.splitlines():
            match = _HUNK.match(line)
            if match:
                flush()
                if len(output) >= _MAX_HUNKS:
                    raise CoreBoundaryInputInvalid("TOO_MANY_PATCH_HUNKS")
                start = (int(match.group(1)), int(match.group(2)))
                context = match.group(3).strip()
                added = []
                removed = 0
                continue
            if start is not None:
                if line.startswith("+") and not line.startswith("+++"):
                    added.append(line[1:])
                elif line.startswith("-") and not line.startswith("---"):
                    removed += 1
        flush()
        if start is None:
            output.append(HostHunkEvidence(
                path, 0, 0, "NO_PARSABLE_HUNKS", 0, 0,
                ("REQUIRES_MANUAL_DIFF",),
            ))
        if len(output) > _MAX_HUNKS:
            raise CoreBoundaryInputInvalid("TOO_MANY_PATCH_HUNKS")
    return tuple(output)


def main() -> int:
    """Read a JSON array of PR changed filenames from stdin; print advice."""
    try:
        paths = json.load(sys.stdin)
        if not isinstance(paths, list):
            raise CoreBoundaryInputInvalid("EXPECTED_JSON_ARRAY")
        result = inspect_protected_host_diff(tuple(paths))
    except (CoreBoundaryInputInvalid, ValueError, TypeError) as exc:
        print(json.dumps({
            "disposition": "INVALID_DIFF_INPUT",
            "reason": str(exc),
            "source_class": _SOURCE_ONLY,
        }, sort_keys=True))
        return 2
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True, indent=2))
    # Advisory only: a native owner-reviewed migration may legitimately
    # touch core. Enforce actual merges via the existing trusted host.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
