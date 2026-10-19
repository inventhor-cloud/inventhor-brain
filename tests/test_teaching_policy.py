import unittest
from dataclasses import replace

from education.lesson_policy import (
    LessonContext, LearnerObservation, propose_teaching_step,
)


NOW = "2026-10-17T09:40:00+02:00"
YESTERDAY = "2026-10-16T08:40:00+02:00"


class TeachingFirstTests(unittest.TestCase):
    def context(self, **changes):
        state = dict(learner_id="adult-1", lesson_id="lesson-1", topic_id="de-dativ",
                     subject="german", phase="ASSESS", now_utc=NOW,
                     profile_authorized=True, curriculum_verified=True)
        state.update(changes)
        return LessonContext(**state)

    def observation(self, phase="INDEPENDENT", correct=True,
                    hinted=False, novel_question=True, at_utc=YESTERDAY,
                    question_id="question-1", observation_id="observation-1", **extra):
        data = dict(learner_id="adult-1", lesson_id="lesson-1", topic_id="de-dativ",
                    phase=phase, correct=correct, hinted=hinted,
                    novel_question=novel_question, at_utc=at_utc,
                    question_id=question_id, observation_id=observation_id,
                    host_attested=True)
        data.update(extra)
        return LearnerObservation(**data)

    def test_unknown_baseline_first_assessed(self):
        advice = propose_teaching_step(self.context())
        self.assertEqual(advice.next_step, "ASSESS_BASELINE")
        self.assertFalse(advice.may_mark_mastered)
        self.assertFalse(advice.may_write_progress)

    def test_wrong_baseline_calls_explanation(self):
        advice = propose_teaching_step(self.context(
            observations=(self.observation(phase="ASSESS", correct=False),)))
        self.assertEqual(advice.next_step, "EXPLAIN_SMALL_CONCEPT")

    def test_explanation_before_questions(self):
        self.assertEqual(propose_teaching_step(
            self.context(phase="EXPLAIN")).next_step, "EXPLAIN_WITH_EXAMPLE")

    def test_wrong_guided_solution_reteaches_different_example(self):
        advice = propose_teaching_step(self.context(
            phase="GUIDED", observations=(self.observation(phase="GUIDED", correct=False),)))
        self.assertEqual(advice.next_step, "RETEACH_DIFFERENT_EXAMPLE")

    def test_guided_success_with_hint_does_not_skip_independent_test(self):
        advice = propose_teaching_step(self.context(
            phase="GUIDED", observations=(self.observation(phase="GUIDED", hinted=True),)))
        self.assertEqual(advice.next_step, "GUIDED_EXAMPLE")

    def test_correct_guided_solution_moves_to_independent(self):
        advice = propose_teaching_step(self.context(
            phase="GUIDED", observations=(self.observation(phase="GUIDED"),)))
        self.assertEqual(advice.next_step, "INDEPENDENT_PRACTICE")

    def test_one_independent_success_only_asks_delayed_review(self):
        advice = propose_teaching_step(self.context(
            phase="INDEPENDENT", observations=(self.observation(),)))
        self.assertEqual(advice.next_step, "SPACED_REVIEW")
        self.assertEqual(advice.review_not_before_hours, 24)
        self.assertFalse(advice.mastery_review_candidate)

    def test_independent_error_reteaches(self):
        advice = propose_teaching_step(self.context(
            phase="INDEPENDENT", observations=(self.observation(correct=False),)))
        self.assertEqual(advice.next_step, "RETEACH_DIFFERENT_EXAMPLE")

    def test_independent_hint_is_not_independent(self):
        advice = propose_teaching_step(self.context(
            phase="INDEPENDENT", observations=(self.observation(hinted=True),)))
        self.assertEqual(advice.next_step, "INDEPENDENT_PRACTICE")

    def test_delayed_review_new_question_requires_main_verification(self):
        examples = (self.observation(),
                    self.observation(phase="REVIEW", at_utc=NOW,
                                     question_id="question-2", observation_id="observation-2"))
        advice = propose_teaching_step(self.context(phase="REVIEW", observations=examples))
        self.assertEqual(advice.next_step, "REQUEST_MAIN_MASTERY_REVIEW")
        self.assertTrue(advice.mastery_review_candidate)
        self.assertFalse(advice.may_mark_mastered)
        self.assertFalse(advice.may_execute)

    def test_repeat_of_same_question_is_not_mastery(self):
        examples = (self.observation(),
                    self.observation(phase="REVIEW", at_utc=NOW,
                                     question_id="question-1", observation_id="observation-2"))
        advice = propose_teaching_step(self.context(phase="REVIEW", observations=examples))
        self.assertFalse(advice.mastery_review_candidate)

    def test_early_review_is_not_mastery(self):
        examples = (self.observation(at_utc="2026-10-17T07:30:00+02:00"),
                    self.observation(phase="REVIEW", at_utc=NOW,
                                     question_id="question-2", observation_id="observation-2"))
        advice = propose_teaching_step(self.context(phase="REVIEW", observations=examples))
        self.assertEqual(advice.next_step, "WAIT_SPACED_REVIEW")

    def test_review_wrong_after_previous_success_reteaches(self):
        examples = (self.observation(),
                    self.observation(phase="REVIEW", at_utc=NOW, correct=False,
                                     question_id="question-2", observation_id="observation-2"))
        advice = propose_teaching_step(self.context(phase="REVIEW", observations=examples))
        self.assertEqual(advice.next_step, "RETEACH_DIFFERENT_EXAMPLE")

    def test_child_cannot_study_without_host_guardian_permission(self):
        ctx = self.context(is_child=True, guardian_authorized=False)
        self.assertEqual(propose_teaching_step(ctx).reason, "GUARDIAN_AUTHORIZATION_REQUIRED")
        ctx = replace(ctx, guardian_authorized=True)
        self.assertEqual(propose_teaching_step(ctx).status, "SOURCE_ADVICE_ONLY")

    def test_other_family_member_observation_is_rejected(self):
        advice = propose_teaching_step(self.context(
            phase="INDEPENDENT",
            observations=(self.observation(learner_id="other-child"),)))
        self.assertEqual(advice.reason, "CROSS_LEARNER_OR_LESSON_EVIDENCE")

    def test_ai_self_attestation_not_accepted_as_progress(self):
        advice = propose_teaching_step(self.context(
            phase="INDEPENDENT",
            observations=(self.observation(host_attested=False),)))
        self.assertEqual(advice.reason, "UNVERIFIED_EVALUATION")

    def test_math_science_english_use_same_main_policy_not_separate_brain(self):
        for subject in ("mathematics", "science", "english"):
            with self.subTest(subject=subject):
                self.assertEqual(propose_teaching_step(
                    self.context(subject=subject)).next_step, "ASSESS_BASELINE")

    def test_no_curriculum_or_host_clock_blocks(self):
        self.assertEqual(propose_teaching_step(
            self.context(curriculum_verified=False)).reason,
            "CURRICULUM_VERIFICATION_REQUIRED")
        self.assertEqual(propose_teaching_step(
            self.context(now_utc="not a timestamp")).reason,
            "HOST_CLOCK_REQUIRED")

    def test_duplicate_observation_prevents_double_counting(self):
        obs = self.observation()
        result = propose_teaching_step(self.context(
            phase="REVIEW", observations=(obs, obs)))
        self.assertEqual(result.reason, "DUPLICATE_OR_MISSING_EVIDENCE_ID")

    def test_reject_out_of_order_progress(self):
        a = self.observation(at_utc=NOW)
        b = self.observation(phase="REVIEW", observation_id="observation-2",
                             question_id="question-2", at_utc=YESTERDAY)
        result = propose_teaching_step(self.context(
            phase="REVIEW", observations=(a, b)))
        self.assertEqual(result.reason, "OUT_OF_ORDER_EVIDENCE")
