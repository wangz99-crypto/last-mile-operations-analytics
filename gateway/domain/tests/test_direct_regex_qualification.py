"""Offline freeze/coverage checks; no runtime candidate import."""
import json
from pathlib import Path
import unittest
from gateway.domain.evaluation.answerability.direct_regex_qualification import derive, sha

ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/"artifacts/answerability_semantic_v2_1_direct_regex_decoder"

class DirectRegexFreezeTests(unittest.TestCase):
    def test_deterministic_contract_derivation(self):
        rules=json.loads((ART/"REGEX_DERIVATION_RULES.json").read_bytes())
        regex,trace=derive((ROOT/rules["source"]).read_bytes(),rules)
        self.assertEqual(regex.encode(),(ART/"DECODER_ENFORCEMENT_REGEX.txt").read_bytes())
        self.assertEqual(trace,json.loads((ART/"REGEX_PROVENANCE_TRACE.json").read_bytes())["rows"])
    def test_frozen_identities(self):
        receipt=json.loads((ART/"REGEX_FREEZE_RECEIPT.json").read_bytes())
        for name,expected in receipt["freeze_hashes"].items():
            self.assertEqual(sha((ROOT/name).read_bytes()),expected)
        self.assertTrue(receipt["direct_regex_contract_frozen"])
    def test_complete_coverage_and_historical_bytes(self):
        fixtures=json.loads((ART/"STRUCTURAL_FIXTURES.json").read_bytes())
        rows={f["id"]:f for f in fixtures["fixtures"]}
        self.assertEqual(len(fixtures["coverage"]),18)
        for c in fixtures["coverage"]:
            self.assertEqual(rows[c["positive"]]["expected"],"ACCEPT")
            self.assertEqual(rows[c["violating"]]["expected"],"REJECT")
        old=json.loads((ROOT/"artifacts/answerability_semantic_v2_lmfe_structural_conformance/CORE_CONFORMANCE_FIXTURES.json").read_bytes())
        for f in old["fixtures"]:
            self.assertEqual(rows[f["fixture_id"]]["text"].encode(),f["text"].encode())
            self.assertEqual(rows[f["fixture_id"]]["input_sha256"],f["input_sha256"])
        self.assertIn("\\u0000",rows["STRING_NUL"]["text"])

if __name__=="__main__": unittest.main()
