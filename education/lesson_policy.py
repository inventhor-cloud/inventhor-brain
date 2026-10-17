"""INVENTHOR Main teaching-first lesson step adviser (source reference only).

Main owns learner profiles, curriculum authority, verified evaluations,
encrypted persistence and progression. This deterministic helper provides a
finite *recommendation*. It never grades free-text answers, teaches a topic,
schedules a reminder, creates an Organizer task or marks learning completed.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

SUBJECTS = frozenset({"german", "english", "mathematics", "science"})
PHASES = frozenset({"ASSESS", "EXPLAIN", "GUIDED", "INDEPENDENT", "REVIEW"})
REVIEW_DELAY = timedelta(hours=24)


@dataclass(frozen=True)
class LearnerObservation:
    observation_id: str
    learner_id: str
    lesson_id: str
    topic_id: str
    question_id: str
    phase: str
    correct: bool
    hinted: bool
    novel_question: bool
    at_utc: str
    # A host-only input. Untrusted clients must not set this themselves.
    host_attested: bool = False


@dataclass(frozen=True)
class LessonContext:
    learner_id: str
    lesson_id: str
    topic_id: str
    subject: str
    phase: str
    now_utc: str
    profile_authorized: bool = False
    guardian_authorized: bool = False
    is_child: bool = False
    curriculum_verified: bool = False
    observations: tuple[LearnerObservation, ...] = ()


@dataclass(frozen=True)
class LessonAdvice:
    status: str
    next_step: str | None
    reason: str
    mastery_review_candidate: bool = False
    review_not_before_hours: int | None = None
    may_write_progress: bool = False
    may_mark_mastered: bool = False
    may_execute: bool = False
    source_only: bool = True


def _time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def propose_teaching_step(context: LessonContext) -> LessonAdvice:
    """Select one pedagogical action; all decisions require Main revalidation."""
    def block(reason: str) -> LessonAdvice:
        return LessonAdvice("BLOCKED", None, reason)
    def propose(step: str, reason: str, *, candidate: bool = False,
                delay: int | None = None) -> LessonAdvice:
        return LessonAdvice("SOURCE_ADVICE_ONLY", step, reason, candidate, delay)

    if not isinstance(context, LessonContext):
        return block("INVALID_CONTEXT")
    ids = (context.learner_id, context.lesson_id, context.topic_id)
    if any(not isinstance(i, str) or not 0 < len(i.strip()) <= 128 for i in ids):
        return block("INVALID_LEARNER_SCOPE")
    if context.profile_authorized is not True:
        return block("PROFILE_AUTHORIZATION_REQUIRED")
    if type(context.is_child) is not bool or type(context.guardian_authorized) is not bool:
        return block("INVALID_GUARDIAN_POLICY")
    if context.is_child and not context.guardian_authorized:
        return block("GUARDIAN_AUTHORIZATION_REQUIRED")
    if context.subject not in SUBJECTS:
        return block("UNSUPPORTED_SUBJECT")
    if context.phase not in PHASES:
        return block("INVALID_PHASE")
    if context.curriculum_verified is not True:
        return block("CURRICULUM_VERIFICATION_REQUIRED")
    now = _time(context.now_utc)
    if now is None:
        return block("HOST_CLOCK_REQUIRED")
    if not isinstance(context.observations, (tuple, list)) or len(context.observations) > 64:
        return block("INVALID_OBSERVATIONS")

    evidence: list[tuple[LearnerObservation, datetime]] = []
    seen = set()
    for item in context.observations:
        if not isinstance(item, LearnerObservation):
            return block("INVALID_OBSERVATION")
        if (item.learner_id, item.lesson_id, item.topic_id) != ids:
            return block("CROSS_LEARNER_OR_LESSON_EVIDENCE")
        if (not all(isinstance(x, str) and 0 < len(x.strip()) <= 128
                    for x in (item.observation_id, item.question_id))
            or item.observation_id in seen):
            return block("DUPLICATE_OR_MISSING_EVIDENCE_ID")
        seen.add(item.observation_id)
        if (item.phase not in PHASES - {"EXPLAIN"}
            or item.host_attested is not True
            or type(item.correct) is not bool or type(item.hinted) is not bool
            or type(item.novel_question) is not bool):
            return block("UNVERIFIED_EVALUATION")
        t = _time(item.at_utc)
        if t is None or t > now + timedelta(minutes=2):
            return block("INVALID_EVIDENCE_TIME")
        evidence.append((item, t))
    if any(evidence[i][1] > evidence[i+1][1] for i in range(len(evidence)-1)):
        return block("OUT_OF_ORDER_EVIDENCE")

    def last(phase: str) -> LearnerObservation | None:
        return next((e for e, _ in reversed(evidence) if e.phase == phase), None)

    if context.phase == "ASSESS":
        recent = last("ASSESS")
        if recent is None:
            return propose("ASSESS_BASELINE", "UNKNOWN_LEVEL")
        if recent.correct and not recent.hinted and recent.novel_question:
            return propose("INDEPENDENT_PRACTICE", "BASELINE_NEEDS_TRANSFER_CHECK")
        return propose("EXPLAIN_SMALL_CONCEPT", "INITIAL_GAP")

    if context.phase == "EXPLAIN":
        return propose("EXPLAIN_WITH_EXAMPLE", "TEACH_CONCEPT_BEFORE_RETRY")

    if context.phase == "GUIDED":
        recent = last("GUIDED")
        if recent is None:
            return propose("GUIDED_EXAMPLE", "GUIDED_PRACTICE_NOT_STARTED")
        if not recent.correct:
            return propose("RETEACH_DIFFERENT_EXAMPLE", "ERROR_NEEDS_EXPLANATION")
        if recent.hinted:
            return propose("GUIDED_EXAMPLE", "REDUCE_HINTS")
        return propose("INDEPENDENT_PRACTICE", "GUIDED_SUCCESS_NOT_MASTERY")

    if context.phase == "INDEPENDENT":
        recent = last("INDEPENDENT")
        if recent is None:
            return propose("INDEPENDENT_PRACTICE", "TRANSFER_NOT_TESTED")
        if not recent.correct:
            return propose("RETEACH_DIFFERENT_EXAMPLE", "INDEPENDENT_GAP")
        if recent.hinted or not recent.novel_question:
            return propose("INDEPENDENT_PRACTICE", "NOVEL_HINT_FREE_ANSWER_REQUIRED")
        return propose("SPACED_REVIEW", "ONE_SUCCESS_NOT_MASTERY", delay=24)

    # REVIEW: must be independent on a new item *and* checked after >=24h.
    independent = [(o, t) for o, t in evidence
                   if o.phase == "INDEPENDENT" and o.correct
                   and not o.hinted and o.novel_question]
    if not independent:
        return propose("INDEPENDENT_PRACTICE", "INDEPENDENT_EVIDENCE_MISSING")

    start, start_at = independent[0]
    if now - start_at < REVIEW_DELAY:
        remaining = int((REVIEW_DELAY - (now - start_at)).total_seconds() // 3600) + 1
        return propose("WAIT_SPACED_REVIEW", "REVIEW_NOT_DUE", delay=remaining)
    reviews = [(o, t) for o, t in evidence if o.phase == "REVIEW"]
    if not reviews:
        return propose("REVIEW_DIFFERENT_EXAMPLE", "SPACED_REVIEW_DUE")
    recent, at = reviews[-1]
    if not recent.correct:
        return propose("RETEACH_DIFFERENT_EXAMPLE", "FORGOTTEN_AT_REVIEW")
    if recent.hinted or not recent.novel_question:
        return propose("REVIEW_DIFFERENT_EXAMPLE", "UNASSISTED_REVIEW_REQUIRED")
    if at - start_at < REVIEW_DELAY or recent.question_id == start.question_id:
        return propose("REVIEW_DIFFERENT_EXAMPLE", "DISTINCT_DELAYED_REVIEW_REQUIRED")
    return propose("REQUEST_MAIN_MASTERY_REVIEW",
                   "INDEPENDENT_AND_DELAYED_EVIDENCE",
                   candidate=True)
