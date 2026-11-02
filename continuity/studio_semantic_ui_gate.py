"""Source-only semantic UI change review for the EXISTING Design Studio.

Brain advice for one bounded, reversible UI edit. Native Design Studio owns
the actual document, render, component hierarchy, history and undo; existing
Operator executes actions after authorized Organizer handoff. No new Studio,
queue, task, preview renderer, Factory, installer or UI process is created.
Claimed flags/hashes in a source packet are NOT authenticated native evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ALLOWED_OPS = frozenset({
    "UI_SET_TOKEN", "UI_SET_CONSTRAINT", "UI_MOVE_SURFACE",
    "UI_SHOW", "UI_HIDE", "UI_SET_VARIANT", "UI_REORDER",
    "UI_ADD_COMPONENT", "UI_REMOVE_COMPONENT", "UI_BIND_COMMAND",
    "UI_SET_RESPONSIVE_RULE",
})
_ALLOWED_PLATFORMS = frozenset({
    "WINDOWS_DESKTOP", "WINDOWS_TOUCH", "ANDROID_PHONE", "ANDROID_TABLET",
})
_MAX_AGE = timedelta(seconds=60)


class StudioUiReviewInvalid(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class SemanticUiEditSnapshot:
    existing_task_id: str
    project_id: str
    design_document_id: str
    native_task_revision: int
    previous_design_revision: int
    design_revision: int
    observed_at: datetime
    operation: str
    target_semantic_id: str
    intended_touched_ids: tuple[str, ...]
    observed_touched_ids: tuple[str, ...]
    before_manifest_sha256: str
    after_manifest_sha256: str
    preview_manifest_sha256: str
    preview_document_revision: int
    expected_platforms: tuple[str, ...]
    tested_platforms: tuple[str, ...]
    real_preview_observed: bool
    target_action_effect_observed: bool
    no_clipping_or_overlap_observed: bool
    focus_and_hit_targets_observed: bool
    localization_expansion_observed: bool
    undo_checkpoint_observed: bool


@dataclass(frozen=True)
class SemanticUiEditAdvice:
    task_id: str
    project_id: str
    document_id: str
    disposition: str
    next_action: str
    blockers: tuple[str, ...]
    source_class: str = "SOURCE_ONLY_SEMANTIC_UI_REVIEW_NOT_NATIVE_RENDER_QA"
    native_evidence_authenticated: bool = False
    preview_verified_by_native_host: bool = False
    design_applied: bool = False
    organizer_updated: bool = False
    may_execute: bool = False
    may_release: bool = False


def _id(value: object, name: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise StudioUiReviewInvalid("INVALID_" + name)
    return value


def _revision(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        raise StudioUiReviewInvalid("INVALID_" + name)
    return value


def _hash(value: object, name: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise StudioUiReviewInvalid("INVALID_" + name)
    return value


def _ids(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not 1 <= len(value) <= 16:
        raise StudioUiReviewInvalid("INVALID_" + name)
    for item in value:
        _id(item, name)
    if len(value) != len(set(value)):
        raise StudioUiReviewInvalid("DUPLICATE_" + name)
    return value


def _platforms(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not 1 <= len(value) <= 4:
        raise StudioUiReviewInvalid("INVALID_" + name)
    if not all(type(item) is str and item in _ALLOWED_PLATFORMS for item in value):
        raise StudioUiReviewInvalid("INVALID_" + name)
    if len(value) != len(set(value)):
        raise StudioUiReviewInvalid("INVALID_" + name)
    return value


def review_studio_semantic_ui_edit(
    snapshot: SemanticUiEditSnapshot, *, now: datetime,
    expected_task_id: str, expected_project_id: str,
    expected_document_id: str, expected_native_revision: int,
    approved_operation: str, approved_semantic_target_id: str,
    approved_touched_ids: tuple[str, ...],
) -> SemanticUiEditAdvice:
    """Review a claimed visible UI delta; never trust/execute claims as proof.

    This can request a native Studio preview/effect review, NOT approve a
    release or assert that a preview was truly rendered on the user's PC.
    approved_* must come independently from a fresh, trusted native Organizer
    scope, never from the untrusted edit snapshot itself. This pure source
    check cannot authenticate its caller or the native Organizer lease.
    """
    if not isinstance(snapshot, SemanticUiEditSnapshot):
        raise StudioUiReviewInvalid("SNAPSHOT_REQUIRED")
    for name, value in (
        ("TASK_ID", snapshot.existing_task_id),
        ("PROJECT_ID", snapshot.project_id),
        ("DOCUMENT_ID", snapshot.design_document_id),
        ("EXPECTED_TASK_ID", expected_task_id),
        ("EXPECTED_PROJECT_ID", expected_project_id),
        ("EXPECTED_DOCUMENT_ID", expected_document_id),
    ):
        _id(value, name)
    for name, value in (
        ("NATIVE_REVISION", snapshot.native_task_revision),
        ("EXPECTED_NATIVE_REVISION", expected_native_revision),
        ("PREVIOUS_DESIGN_REVISION", snapshot.previous_design_revision),
        ("DESIGN_REVISION", snapshot.design_revision),
        ("PREVIEW_REVISION", snapshot.preview_document_revision),
    ):
        _revision(value, name)
    if snapshot.existing_task_id != expected_task_id:
        raise StudioUiReviewInvalid("TASK_SCOPE_MISMATCH")
    if snapshot.project_id != expected_project_id:
        raise StudioUiReviewInvalid("PROJECT_SCOPE_MISMATCH")
    if snapshot.design_document_id != expected_document_id:
        raise StudioUiReviewInvalid("DOCUMENT_SCOPE_MISMATCH")
    if snapshot.native_task_revision != expected_native_revision:
        raise StudioUiReviewInvalid("STALE_ORGANIZER_REVISION")
    if not isinstance(snapshot.operation, str) or snapshot.operation not in _ALLOWED_OPS:
        raise StudioUiReviewInvalid("UNSUPPORTED_UI_OPERATION")
    if not isinstance(approved_operation, str) or approved_operation not in _ALLOWED_OPS:
        raise StudioUiReviewInvalid("INVALID_APPROVED_OPERATION")
    _id(snapshot.target_semantic_id, "SEMANTIC_TARGET")
    _id(approved_semantic_target_id, "APPROVED_SEMANTIC_TARGET")
    intended = _ids(snapshot.intended_touched_ids, "INTENDED_TARGETS")
    observed = _ids(snapshot.observed_touched_ids, "OBSERVED_TARGETS")
    approved = _ids(approved_touched_ids, "APPROVED_TARGETS")
    if approved_semantic_target_id not in approved:
        raise StudioUiReviewInvalid("APPROVED_TARGET_NOT_IN_SCOPE")
    if snapshot.operation != approved_operation:
        raise StudioUiReviewInvalid("UI_OPERATION_SCOPE_MISMATCH")
    if snapshot.target_semantic_id != approved_semantic_target_id:
        raise StudioUiReviewInvalid("SEMANTIC_TARGET_SCOPE_MISMATCH")
    expected = _platforms(snapshot.expected_platforms, "EXPECTED_PLATFORMS")
    tested = _platforms(snapshot.tested_platforms, "TESTED_PLATFORMS")
    for name, value in (
        ("BEFORE_MANIFEST", snapshot.before_manifest_sha256),
        ("AFTER_MANIFEST", snapshot.after_manifest_sha256),
        ("PREVIEW_MANIFEST", snapshot.preview_manifest_sha256),
    ):
        _hash(value, name)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise StudioUiReviewInvalid("AWARE_TIMESTAMPS_REQUIRED")
    stamp = snapshot.observed_at
    if not isinstance(stamp, datetime) or stamp.tzinfo is None or stamp.utcoffset() is None:
        raise StudioUiReviewInvalid("AWARE_TIMESTAMPS_REQUIRED")
    now_utc = now.astimezone(timezone.utc)
    stamp_utc = stamp.astimezone(timezone.utc)
    if stamp_utc > now_utc + timedelta(seconds=5) or now_utc - stamp_utc > _MAX_AGE:
        raise StudioUiReviewInvalid("STALE_OR_FUTURE_EDIT_OBSERVATION")

    for name in (
        "real_preview_observed", "target_action_effect_observed",
        "no_clipping_or_overlap_observed", "focus_and_hit_targets_observed",
        "localization_expansion_observed", "undo_checkpoint_observed",
    ):
        if type(getattr(snapshot, name)) is not bool:
            raise StudioUiReviewInvalid("INVALID_" + name.upper())

    blockers: list[str] = []
    def need(condition: bool, code: str) -> None:
        if not condition:
            blockers.append(code)

    need(snapshot.design_revision > snapshot.previous_design_revision,
         "DESIGN_REVISION_NOT_ADVANCED")
    need(snapshot.before_manifest_sha256 != snapshot.after_manifest_sha256,
         "NO_DOCUMENT_MANIFEST_CHANGE")
    need(snapshot.preview_manifest_sha256 == snapshot.after_manifest_sha256,
         "PREVIEW_OF_DIFFERENT_DOCUMENT")
    need(snapshot.preview_document_revision == snapshot.design_revision,
         "STALE_PREVIEW_REVISION")
    need(snapshot.target_semantic_id in intended, "SEMANTIC_TARGET_NOT_IN_SCOPE")
    need(snapshot.target_semantic_id in observed, "SEMANTIC_TARGET_NOT_CHANGED")
    need(set(observed) <= set(intended), "UNRELATED_COMPONENT_MUTATED")
    need(set(intended) <= set(approved), "UNAPPROVED_INTENDED_COMPONENT")
    need(set(observed) <= set(approved), "UNAPPROVED_OBSERVED_COMPONENT")
    need("WINDOWS_DESKTOP" in expected, "REQUIRED_WINDOWS_DESKTOP_NOT_EXPECTED")
    need(set(expected) <= set(tested), "RESPONSIVE_PLATFORM_NOT_TESTED")
    need(snapshot.real_preview_observed, "REAL_PREVIEW_NOT_OBSERVED")
    need(snapshot.target_action_effect_observed, "UI_ACTION_EFFECT_NOT_OBSERVED")
    need(snapshot.no_clipping_or_overlap_observed, "CLIPPING_OR_OVERLAP_NOT_CHECKED")
    need(snapshot.focus_and_hit_targets_observed, "FOCUS_OR_TOUCH_NOT_CHECKED")
    need(snapshot.localization_expansion_observed, "LOCALIZATION_NOT_CHECKED")
    need(snapshot.undo_checkpoint_observed, "UNDO_CHECKPOINT_NOT_OBSERVED")

    return SemanticUiEditAdvice(
        task_id=snapshot.existing_task_id,
        project_id=snapshot.project_id,
        document_id=snapshot.design_document_id,
        disposition="BLOCKED" if blockers else "NATIVE_STUDIO_REVIEW_REQUIRED",
        next_action=(
            "RECONCILE_EXACT_STUDIO_UI_DOCUMENT_AND_PREVIEW_EVIDENCE"
            if blockers else
            "REQUEST_EXISTING_STUDIO_NATIVE_RENDER_AND_ACTION_EFFECT_WITNESS"
        ),
        blockers=tuple(blockers),
    )
