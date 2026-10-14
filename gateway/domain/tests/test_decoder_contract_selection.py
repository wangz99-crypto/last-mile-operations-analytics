"""Offline P2P3 declaration checks; never compile or execute a decoder."""
import ast
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import unittest

from gateway.domain.evaluation.answerability.derive_decoder_contract import (
    derive, digest, selection_outcome, verify_frozen,
)

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/answerability_semantic_v2_1_decoder_contract_selection"
P1 = ROOT / "artifacts/answerability_semantic_v2_decoder_responsibility_split"


def read(path):
    return json.loads(path.read_bytes())


class DecoderContractSelectionTests(unittest.TestCase):
    def test_p1_accounting_and_exact_reproduction(self):
        rules = read(ART / "DECODER_CONTRACT_DERIVATION_RULES.json")
        for name, expected in rules["source_sha256"].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected)
        raw = (ROOT / "artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json").read_bytes()
        matrix = read(P1 / "STRUCTURAL_ENFORCEMENT_MATRIX.json")
        contract, trace, delegated = derive(raw, matrix, rules)
        self.assertEqual(contract, read(ART / "DECODER_ENFORCEMENT_CONTRACT.json"))
        self.assertEqual(trace, read(ART / "DECODER_CONTRACT_DERIVATION_TRACE.json")["rows"])
        self.assertEqual(delegated, read(ART / "VALIDATOR_ONLY_CONSTRAINTS.json")["rows"])
        self.assertEqual((len(trace), len(contract["constraints"]), len(delegated)), (64, 18, 46))
        self.assertEqual(len({r["constraint_id"] for r in trace}), 64)
        self.assertEqual(len(matrix["adapter_obligations"]), 6)
        self.assertTrue(all("EXACT_VALIDATOR_ENFORCED" in r["p1_ownership"] for r in trace))
        self.assertEqual(read(ART / "VALIDATOR_ONLY_CONSTRAINTS.json")["adapter_migration_count"], 0)

    def test_freeze_precedes_research_and_rejects_mutation(self):
        receipt = read(ART / "CONTRACT_FREEZE_RECEIPT.json")
        events = receipt["events"]
        self.assertEqual([e["event"] for e in events[:3]], ["DERIVATION_RULES_FROZEN", "DECODER_ENFORCEMENT_CONTRACT_FROZEN", "CANDIDATE_INSPECTION_STARTED"])
        times = [datetime.fromisoformat(e["utc"]) for e in events]
        self.assertEqual(times, sorted(times))
        requests = read(ART / "CANDIDATE_DEPENDENCY_METADATA.json")["network_requests"]
        self.assertTrue(all(datetime.fromisoformat(r["utc"]) > times[2] for r in requests))
        frozen = {n: (ART / n).read_bytes() for n in receipt["freeze_hashes"]}
        verify_frozen(frozen, receipt["freeze_hashes"])
        for name in frozen:
            changed = dict(frozen)
            changed[name] += b" "
            with self.assertRaises(ValueError):
                verify_frozen(changed, receipt["freeze_hashes"])
        self.assertEqual(digest((ROOT / "gateway/domain/evaluation/answerability/derive_decoder_contract.py").read_bytes()), receipt["derivation_helper_sha256"])

    def test_projection_preserves_predicates_and_delegation(self):
        contract = read(ART / "DECODER_ENFORCEMENT_CONTRACT.json")
        rows = {r["constraint_id"]: r for r in read(ART / "DECODER_CONTRACT_DERIVATION_TRACE.json")["rows"]}
        kept = {c["constraint_id"] for c in contract["constraints"]}
        for c in contract["constraints"]:
            raw = rows[c["constraint_id"]]
            self.assertIn("DECODER_ENFORCED", raw["p1_ownership"])
            if c["predicate"] in {"type", "enum", "required"}:
                self.assertEqual(c["value"], raw["raw_constraint"])
            elif c["predicate"] == "additionalProperties":
                self.assertIs(raw["raw_constraint"], False)
                self.assertIs(c["value"]["allowed"], False)
            else:
                self.assertIn(c["predicate"], {"items", "properties"})
                self.assertNotEqual(c["value"], raw["raw_constraint"])
        delegated = read(ART / "VALIDATOR_ONLY_CONSTRAINTS.json")["rows"]
        self.assertFalse(kept & {r["pointer"] for r in delegated})
        self.assertEqual(kept, {k for k, r in rows.items() if r["decoder_contract_representation"] is not None})
        self.assertFalse(contract["serialization"]["order_or_whitespace_semantics"])

    def test_m1_m8_expectations_preserve_p1_evidence(self):
        fixtures = read(ART / "CORE_FIXTURE_EXPECTATIONS.json")["fixtures"]
        old = read(P1 / "M1_M8_TREATMENT.json")["fixtures"]
        self.assertEqual([f["id"] for f in fixtures], ["M" + str(i) for i in range(1, 9)])
        self.assertEqual([f["decoder_contract_expected"] for f in fixtures], ["ACCEPT"] + ["REJECT"] * 7)
        for f, prior in zip(fixtures, old):
            self.assertEqual(f["raw_sha256"], prior["raw_sha256"])
            self.assertEqual(f["required_field_violations"], prior["missing_required_top_level_fields"])
            self.assertEqual(bool(f["required_field_violations"]), f["decoder_contract_expected"] == "REJECT")

    def test_known_incompatibility_blocks_selection(self):
        matrix = read(ART / "OUTLINES_CORE_CONTRACT_CAPABILITY_MATRIX.json")
        rows = matrix["rows"]
        self.assertEqual({r["constraint_id"] for r in rows}, {c["constraint_id"] for c in read(ART / "DECODER_ENFORCEMENT_CONTRACT.json")["constraints"]})
        self.assertEqual(selection_outcome(rows), "DECODER_CANDIDATE_SELECTION_BLOCKED")
        bad = [r for r in rows if r["support_classification"] == "STATICALLY_UNSUPPORTED"]
        self.assertEqual([r["constraint_id"] for r in bad], ["/properties/material_asks/items/properties/ask/type"])
        self.assertTrue(all(r["direct_p4_probe"] for r in rows))
        modified = deepcopy(rows)
        modified[0]["support_classification"] = "AMBIGUOUS"
        del modified[0]["direct_p4_probe"]
        with self.assertRaises(ValueError):
            selection_outcome(modified)
        self.assertEqual(matrix["outcome"], "DECODER_CANDIDATE_SELECTION_BLOCKED")

    def test_static_only_boundary(self):
        matrix = read(ART / "OUTLINES_CORE_CONTRACT_CAPABILITY_MATRIX.json")
        self.assertTrue(all(v == 0 for v in matrix["activity"].values()))
        self.assertFalse(matrix["quarantine"]["phase_2h_held_out_access"])
        self.assertFalse(matrix["quarantine"]["phase_2g_private_heldout_access"])
        self.assertEqual(matrix["quarantine"]["fresh_v2_1_semantic_suite"], "NOT YET AUTHORED")
        source = (ROOT / "gateway/domain/evaluation/answerability/derive_decoder_contract.py").read_text(encoding="utf-8")
        imports = []
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imports.extend(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        self.assertEqual(set(imports), {"copy", "hashlib", "json"})
        metadata = read(ART / "CANDIDATE_DEPENDENCY_METADATA.json")
        for key in ["package_installations", "package_imports", "package_downloads", "pip_resolver_invocations"]:
            self.assertEqual(metadata[key], 0)


if __name__ == "__main__":
    unittest.main()
