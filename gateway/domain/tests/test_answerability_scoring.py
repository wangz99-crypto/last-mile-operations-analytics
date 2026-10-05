from dataclasses import replace
from fractions import Fraction
import unittest

from gateway.domain.evaluation.answerability.answerability_contracts import (
    ALLOW, ABSTAIN, UNRESOLVED, CandidateObservation, ContractError, GateOutput,
)
from gateway.domain.evaluation.answerability.answerability_scoring import (
    deterministic_json_bytes, metric, score_results,
)
from gateway.domain.tests._answerability_fixtures import fixture, changed_outputs


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.retrievals, self.outputs = fixture()

    def score(self, outputs=None, retrievals=None, cases=None):
        return score_results(self.cases if cases is None else cases,
                             self.retrievals if retrievals is None else retrievals,
                             self.outputs if outputs is None else outputs)

    def test_primary_exact_counts_and_denominators(self):
        outputs = changed_outputs(self.outputs, {0: GateOutput(ABSTAIN), 20: GateOutput(ALLOW), 21: GateOutput(ALLOW)})
        primary = self.score(outputs)["primary"]
        for key, count in (("allow_recall", 19), ("false_abstention_rate", 1),
                           ("correct_abstention_rate", 18), ("false_support_rate", 2)):
            self.assertEqual(primary[key], metric(count, 20))
        self.assertEqual(primary["allow_recall"]["rate"], "0.950000000000")

    def test_eligibility_18_18(self):
        outputs = changed_outputs(self.outputs, {0: GateOutput(ABSTAIN), 1: GateOutput(ABSTAIN),
                                                20: GateOutput(ALLOW), 21: GateOutput(ALLOW)})
        self.assertTrue(self.score(outputs)["eligible"])

    def test_eligibility_17_20(self):
        outputs = changed_outputs(self.outputs, {i: GateOutput(ABSTAIN) for i in range(3)})
        self.assertFalse(self.score(outputs)["eligible"])

    def test_eligibility_20_17(self):
        outputs = changed_outputs(self.outputs, {i: GateOutput(ALLOW) for i in range(20, 23)})
        self.assertFalse(self.score(outputs)["eligible"])

    def test_errors_keep_denominators_and_do_not_become_abstain(self):
        outputs = list(self.outputs)
        outputs[0] = CandidateObservation(outputs[0].question_id, {"decision": "MAYBE"})
        outputs[20] = CandidateObservation(outputs[20].question_id, error="CANDIDATE_EXCEPTION")
        del outputs[21]
        score = self.score(tuple(outputs))
        self.assertEqual(score["primary"]["allow_recall"], metric(19, 20))
        self.assertEqual(score["primary"]["correct_abstention_rate"], metric(18, 20))
        self.assertEqual(score["primary"]["false_support_rate"], metric(0, 20))
        self.assertEqual(score["primary"]["false_abstention_rate"], metric(0, 20))
        self.assertTrue(score["meets_class_floors"])
        self.assertFalse(score["eligible"])
        self.assertFalse(score["valid_complete_run"])
        self.assertEqual(score["errors"]["count"], 3)
        self.assertEqual(score["errors"]["by_gold_class"], {ALLOW: 1, ABSTAIN: 2})
        self.assertEqual(score["errors"]["by_code"], {"MISSING_OUTPUT": 1, "MALFORMED_OUTPUT": 1, "CANDIDATE_EXCEPTION": 1})
        row = score["questions"][0]
        self.assertIsNone(row["predicted_decision"])
        self.assertFalse(row["binary_correct"])
        self.assertFalse(row["gated"]["hit_at_1"])

    def test_all_missing_outputs_are_explicit_failures(self):
        score = self.score(())
        self.assertEqual(score["errors"]["count"], 40)
        self.assertEqual(score["primary"]["correct_abstention_rate"], metric(0, 20))
        self.assertEqual(score["retrieval"]["gated"]["hit_at_1"], metric(0, 20))

    def test_wrong_valid_reason_preserves_binary_correctness(self):
        score = self.score(changed_outputs(self.outputs, {20: GateOutput(ABSTAIN, UNRESOLVED)}))
        row = score["questions"][20]
        self.assertTrue(row["binary_correct"])
        self.assertFalse(row["reason_correct"])
        self.assertIsNone(row["candidate_error"])
        self.assertEqual(score["primary"]["correct_abstention_rate"], metric(20, 20))
        self.assertEqual(score["reason_diagnostic"]["agreement"], metric(39, 40))

    def test_wrong_binary_any_valid_reason_remains_failure(self):
        row = self.score(changed_outputs(self.outputs, {0: GateOutput(ABSTAIN, UNRESOLVED)}))["questions"][0]
        self.assertFalse(row["binary_correct"])
        self.assertFalse(row["reason_correct"])

    def test_reason_not_emitted_is_not_fabricated(self):
        outputs = tuple(replace(o, output=GateOutput(o.output.decision)) for o in self.outputs)
        score = self.score(outputs)
        self.assertIsNone(score["reason_diagnostic"]["agreement"])
        self.assertTrue(all(r["reason_correct"] is None for r in score["questions"]))

    def test_abstain_zeroes_gated_metrics_but_preserves_all_denominators(self):
        score = self.score(changed_outputs(self.outputs, {0: GateOutput(ABSTAIN)}))
        gated, ungated = score["retrieval"]["gated"], score["retrieval"]["ungated"]
        self.assertEqual(gated["hit_at_1"], metric(19, 20))
        self.assertEqual(ungated["hit_at_1"], metric(20, 20))
        self.assertEqual(gated["required_micro_coverage_at_10"], metric(24, 26))
        self.assertEqual(gated["required_macro_coverage_at_10"], metric(19, 20))
        self.assertEqual(gated["multi_required_full_at_10"], metric(5, 6))
        for key, value in score["questions"][0]["gated"].items():
            if "coverage" in key:
                self.assertEqual(value["numerator"], 0)
            else:
                self.assertFalse(value)

    def test_macro_micro_and_multi_at_each_depth(self):
        scored = self.score()["retrieval"]["gated"]
        for k in (3, 5):
            self.assertEqual(scored[f"required_macro_coverage_at_{k}"], metric(17, 20))
            self.assertEqual(scored[f"required_micro_coverage_at_{k}"], metric(20, 26))
            self.assertEqual(scored[f"multi_required_full_at_{k}"], metric(0, 6))
        self.assertEqual(scored["required_macro_coverage_at_10"], metric(20, 20))
        self.assertEqual(scored["required_micro_coverage_at_10"], metric(26, 26))
        self.assertEqual(scored["multi_required_full_at_10"], metric(6, 6))

    def test_multi_complete_at_3_and_5_boundaries(self):
        for rank in (3, 5):
            cases = tuple(replace(c, gold_support_sections=(c.gold_support_sections[0], self.retrievals[0].result.evidence[rank-1].identity),
                                  required_support_sections=(c.gold_support_sections[0], self.retrievals[0].result.evidence[rank-1].identity))
                          if i < 6 else c for i, c in enumerate(self.cases))
            scored = self.score(cases=cases)["retrieval"]["gated"]
            for k in (3, 5, 10):
                self.assertEqual(scored[f"multi_required_full_at_{k}"], metric(6 if k >= rank else 0, 6))

    def test_identity_not_title_controls_scoring(self):
        retrievals = tuple(replace(r, result=replace(r.result, evidence=tuple(
            replace(e, title="Same title", section_title="Same title", section_id="other-"+e.section_id)
            for e in r.result.evidence))) for r in self.retrievals)
        self.assertEqual(self.score(retrievals=retrievals)["retrieval"]["gated"]["hit_at_3"], metric(0, 20))

    def test_empty_rankings_are_valid_zero_hits(self):
        retrievals = tuple(replace(r, result=replace(r.result, evidence=())) for r in self.retrievals)
        self.assertEqual(self.score(retrievals=retrievals)["retrieval"]["ungated"]["hit_at_3"], metric(0, 20))

    def test_missing_duplicate_unknown_external_associations(self):
        for retrievals in (self.retrievals[:-1], self.retrievals+(self.retrievals[0],),
                           (replace(self.retrievals[0], question_id="UNKNOWN"),)+self.retrievals[1:]):
            with self.assertRaises(ContractError):
                self.score(retrievals=retrievals)
        for outputs in (self.outputs+(self.outputs[0],), (replace(self.outputs[0], question_id="UNKNOWN"),)+self.outputs[1:]):
            with self.assertRaises(ContractError):
                self.score(outputs)

    def test_wrong_text_binding_rejected(self):
        with self.assertRaisesRegex(ContractError, "text binding"):
            self.score(retrievals=(replace(self.retrievals[0], question_sha256="0"*64),)+self.retrievals[1:])

    def test_invalid_class_or_empty_multi_denominators_rejected(self):
        with self.assertRaises(ContractError):
            self.score(cases=self.cases[:-1])
        cases = tuple(replace(c, required_support_sections=c.required_support_sections[:1]) for c in self.cases)
        with self.assertRaisesRegex(ContractError, "multi-required"):
            self.score(cases=cases)

    def test_deterministic_json_is_independent_of_input_order(self):
        original = deterministic_json_bytes(self.score())
        reversed_score = score_results(tuple(reversed(self.cases)), tuple(reversed(self.retrievals)), tuple(reversed(self.outputs)))
        self.assertEqual(original, deterministic_json_bytes(reversed_score))
        self.assertTrue(original.endswith(b"\n"))
        self.assertNotIn(b"\r", original)
        self.assertEqual(metric(Fraction(1, 3), 20)["rate"], "0.016666666667")
        self.assertEqual(metric(Fraction(1, 3), 20)["numerator_divisor"], 3)


if __name__ == "__main__":
    unittest.main()
