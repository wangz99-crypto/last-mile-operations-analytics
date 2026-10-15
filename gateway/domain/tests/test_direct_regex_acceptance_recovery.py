"""Synthetic Guide doubles and saved-fixture accounting only; no decoder runtime."""
import json
from pathlib import Path
import unittest
from gateway.domain.evaluation.answerability.recover_direct_regex_acceptance import accept_content

ROOT = Path(__file__).resolve().parents[3]
HISTORY = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_decoder"

class GuideDouble:
    def __init__(self, terminal=None, finished=True):
        self.advanced = []
        self.terminal = [99] if terminal is None else terminal
        self.finished = finished
    def get_tokens(self):
        return [11] if len(self.advanced) == 0 else [22] if len(self.advanced) == 1 else self.terminal
    def advance(self, token_id, return_tokens=False):
        if token_id == 99:
            raise AssertionError("EOS must never be advanced")
        self.advanced.append(token_id)
    def is_finished(self):
        return len(self.advanced) == 2 and self.finished

class RecoveryOracleTests(unittest.TestCase):
    def test_accept_stops_at_terminal_eos_observation(self):
        guide = GuideDouble()
        result = accept_content(guide, [11, 22], 99)
        self.assertEqual(result["result"], "ACCEPT")
        self.assertEqual(guide.advanced, [11, 22])
        self.assertEqual(result["allowed_tokens_at_final_state"], [99])
        self.assertEqual(result["eos_advance_calls"], 0)
    def test_exact_terminal_condition_and_error_boundary(self):
        for guide in [GuideDouble([99, 33]), GuideDouble([]), GuideDouble(finished=False)]:
            self.assertEqual(accept_content(guide, [11, 22], 99)["result"], "REJECT")
        self.assertEqual(accept_content(GuideDouble(), [11, 33], 99)["result"], "REJECT")
        with self.assertRaises(ValueError):
            accept_content(GuideDouble(), [11, 99], 99)
    def test_only_positive_partition_and_historical_rejects(self):
        fixtures = json.loads((HISTORY / "STRUCTURAL_FIXTURES.json").read_bytes())["fixtures"]
        prior = json.loads((HISTORY / "STRUCTURAL_RESULTS.json").read_bytes())
        positives = [f["id"] for f in fixtures if f["expected"] == "ACCEPT"]
        negatives = [f["id"] for f in fixtures if f["expected"] == "REJECT"]
        results = {r["id"]: r for r in prior["FSM"]["rows"]}
        self.assertEqual((len(positives), len(negatives)), (34, 30))
        self.assertIn("M1", positives)
        self.assertIn("STRING_NUL", positives)
        self.assertTrue(all(results[n]["result"] == "REJECT" for n in negatives))
        self.assertTrue(all("M" + str(i) in negatives for i in range(2, 9)))

if __name__ == "__main__": unittest.main()
