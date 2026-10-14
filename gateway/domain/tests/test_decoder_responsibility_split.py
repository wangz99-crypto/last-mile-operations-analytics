"""Architecture record checks only; no raw-instance validator or decoder execution."""
import ast
import hashlib
import json
from pathlib import Path
import types
import unittest


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/answerability_semantic_v2_decoder_responsibility_split"
HELPER = ROOT / "gateway/domain/evaluation/answerability/preregister_responsibility_split.py"
SCHEMA_SHA = "6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ResponsibilitySplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read("ARCHITECTURE_REGISTRY.json")
        cls.inv = read("FROZEN_SCHEMA_CONSTRAINT_INVENTORY.json")
        cls.matrix = read("STRUCTURAL_ENFORCEMENT_MATRIX.json")

    def test_exact_schema_and_deterministic_inventory(self):
        raw = (ROOT / self.plan["schema_path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SCHEMA_SHA)
        module = types.ModuleType("declaration_inventory_only")
        exec(compile(HELPER.read_text(encoding="utf-8"), str(HELPER), "exec"), module.__dict__)
        self.assertEqual(module.inventory(raw), self.inv)
        self.assertEqual(module.inventory(raw), module.inventory(raw))
        with self.assertRaises(ValueError):
            module.inventory(raw + b" ")

    def test_full_keyword_occurrence_coverage_independently(self):
        schema = json.loads((ROOT / self.plan["schema_path"]).read_bytes())
        expected = {}
        # Independent complete JSON-tree traversal: property names in this frozen
        # schema do not collide with JSON Schema vocabulary names.
        keywords = set("type properties required additionalProperties enum const items prefixItems minItems maxItems uniqueItems contains minContains maxContains minimum maximum exclusiveMinimum exclusiveMaximum minLength maxLength pattern oneOf anyOf allOf if then else $ref $schema".split())

        def walk(value, pointer=""):
            if isinstance(value, dict):
                for key, child in value.items():
                    path = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
                    if key in keywords:
                        expected[path] = child
                    walk(child, path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, pointer + "/" + str(index))

        walk(schema)
        records = self.inv["constraints"]
        self.assertEqual(len(records), len({r["pointer"] for r in records}))
        self.assertEqual({r["pointer"]: r["constraint_value"] for r in records}, expected)
        self.assertEqual(len(expected), 65)
        self.assertEqual(self.inv["counts"]["material_schema_constraints"], 64)

    def test_no_material_constraint_unowned_or_downgraded(self):
        for row in self.matrix["raw_schema_constraints"]:
            self.assertTrue(row["enforcement_owners"], row["pointer"])
            self.assertEqual(row["criticality"], "CRITICAL")
            self.assertIn("EXACT_VALIDATOR_ENFORCED", row["enforcement_owners"])
        self.assertEqual(self.matrix["unowned_material_constraints_all_domains"], 0)
        self.assertEqual(len(self.matrix["raw_schema_constraints"]), 64)

    def test_required_fields_are_mandatory_at_both_layers(self):
        required = [r for r in self.matrix["raw_schema_constraints"] if r["keyword"] == "required"]
        self.assertEqual(len(required), 2)
        for row in required:
            self.assertEqual(set(row["enforcement_owners"]), {"DECODER_ENFORCED", "EXACT_VALIDATOR_ENFORCED"})
        self.assertEqual(set(required[0]["constraint_value"]) | set(required[1]["constraint_value"]),
                         {"decision", "policy_context_status", "reason_code", "material_asks", "ask", "support_status", "supporting_evidence_ranks"})

    def test_unconditional_types_and_enums_are_decoder_owned(self):
        rows = [r for r in self.matrix["raw_schema_constraints"] if r["keyword"] in {"type", "enum"} and not r["conditional_scope"]]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn("DECODER_ENFORCED", row["enforcement_owners"])
            self.assertIn("EXACT_VALIDATOR_ENFORCED", row["enforcement_owners"])

    def test_advanced_branch_constraints_delegate_without_dropping(self):
        for keyword in {"uniqueItems", "contains", "if", "then", "else", "oneOf", "allOf", "anyOf"}:
            rows = [r for r in self.matrix["raw_schema_constraints"] if r["keyword"] == keyword]
            self.assertTrue(rows, keyword)
            for row in rows:
                self.assertEqual(row["enforcement_owners"], ["EXACT_VALIDATOR_ENFORCED"])
                self.assertEqual(row["criticality"], "CRITICAL")
        for row in self.matrix["raw_schema_constraints"]:
            if row["conditional_scope"]:
                self.assertEqual(row["decoder"], "NOT_ENFORCED")

    def test_ownership_counts_and_separate_adapter_denominator(self):
        self.assertEqual(self.inv["counts"]["decoder_owned_raw_constraints"], 18)
        self.assertEqual(self.inv["counts"]["exact_validator_owned_raw_constraints"], 64)
        self.assertEqual(self.inv["counts"]["adapter_owned_raw_constraints"], 0)
        self.assertEqual(self.inv["counts"]["multi_owned_raw_constraints"], 18)
        self.assertEqual(len(self.matrix["exact_validator_only_pointers"]), 46)
        self.assertEqual(self.matrix["adapter_obligation_count"], 6)
        for row in self.matrix["adapter_obligations"]:
            self.assertEqual(row["enforcement_owners"], ["ADAPTER_ENFORCED"])

    def test_exact_validator_is_not_selected_or_implicitly_qualified(self):
        self.assertTrue(self.plan["all_raw_schema_constraints_exact_validator_required"])
        self.assertEqual(self.plan["validator_implementation"], "NOT_SELECTED_NOT_QUALIFIED")
        self.assertEqual(self.plan["adapter_preconditions"], ["decoder_PASS", "json_parse_PASS", "exact_schema_PASS"])

    def test_no_repair_and_no_retry(self):
        self.assertTrue(self.plan["no_post_generation_repair"])
        self.assertEqual(self.plan["generation_retries"], 0)
        self.assertEqual(self.plan["repair_retries"], 0)
        self.assertFalse(self.plan["adaptive_contract_changes"])
        self.assertFalse(self.plan["schema_rewriting"])

    def test_invalid_or_indeterminate_states_cannot_reach_adapter(self):
        graph = read("ACCEPTANCE_STATE_GRAPH.json")
        state = graph["entry"]
        visited = []
        while state in graph["states"]:
            visited.append(state)
            transitions = graph["states"][state]
            for outcome in ["REJECT", "ERROR", "NOT_RUN"]:
                with self.subTest(state=state, outcome=outcome):
                    terminal = transitions[outcome]
                    self.assertTrue(terminal["halt"])
                    self.assertEqual(terminal["semantic_evaluation"], "NOT_RUN")
                    self.assertFalse(terminal["repair"])
                    self.assertEqual(terminal["retries"], 0)
                    self.assertNotIn("next", terminal)
            state = transitions["PASS"]
        self.assertEqual(visited, ["DECODER_VERIFY", "JSON_PARSE", "EXACT_SCHEMA", "ADAPTER"])
        self.assertEqual(state, "COMBINED_STRUCTURAL_ACCEPT")

    def test_adapter_source_and_semantics_unchanged(self):
        history = read("HISTORICAL_INTEGRITY_RECEIPT.json")
        path = "gateway/domain/evaluation/answerability/gates/semantic_gate_v2.py"
        self.assertEqual(sha(ROOT / path), "a83ebe3b6841e5cd810633c68ba4efc76ed8d6daeee1cbb62899e317133e9219")
        self.assertEqual(sha(ROOT / path), history["sha256"][path])
        self.assertIn("deterministic_adapter_semantics", self.plan["semantic_invariance"])

    def test_distinct_identity_and_no_decoder_selection(self):
        self.assertEqual(self.plan["candidate_id"], "SEMANTIC_MATERIAL_SUPPORT_V2_1")
        self.assertEqual(self.plan["parent_candidate"], "SEMANTIC_MATERIAL_SUPPORT_V2")
        self.assertEqual(self.plan["owner_status"], "CANDIDATE_AWAITING_OWNER_REVIEW")
        self.assertIsNone(self.plan["decoder_implementation"])
        self.assertFalse(self.plan["executions_authorized_now"])

    def test_language_and_derivation_preregistration_only(self):
        self.assertEqual(self.plan["decoder_contract_status"], "P2_DERIVATION_AND_FREEZE_REQUIRED_NOT_CREATED")
        self.assertIn("L_exact subseteq L_decoder", self.plan["language_relationship"])
        self.assertIn("Do not hoist", self.plan["derivation_rules"]["no_hoisting"])
        self.assertIn("no result-dependent", self.plan["derivation_rules"]["proof_obligation"])

    def test_historical_m1_m8_bytes_and_required_defects(self):
        evidence = read("M1_M8_TREATMENT.json")
        path = ROOT / evidence["source"]
        self.assertEqual(sha(path), evidence["source_sha256"])
        fixtures = json.loads(path.read_text(encoding="utf-8"))["fixtures"]
        for row, old in zip(evidence["fixtures"], fixtures):
            self.assertEqual(row["raw_sha256"], hashlib.sha256(old["text"].encode()).hexdigest())
            expected = "ACCEPT" if row["id"] == "M1" else "REJECT"
            for key in ["decoder_expected", "exact_validator_expected", "combined_expected"]:
                self.assertEqual(row[key], expected)
            if row["id"] in {"M6", "M7", "M8"}:
                self.assertEqual(row["missing_required_top_level_fields"], ["decision", "policy_context_status", "reason_code"])

    def test_full_ladder_and_model_budget(self):
        for i, stage in enumerate(self.plan["future_ladder"], 1):
            self.assertEqual(stage["id"], f"P{i}")
            self.assertEqual(stage["predecessors"], [f"P{j}" for j in range(1, i)])
        self.assertEqual(len(self.plan["future_ladder"]), 11)
        model = self.plan["model_budget"]
        self.assertEqual(model["generate_calls"], 3)
        self.assertEqual(model["quality_retries"], model["repair_retries"])
        self.assertEqual(model["repair_retries"], 0)
        self.assertEqual(model["repetition_penalty"], 1.0)

    def test_zero_execution_and_benchmark_quarantine(self):
        counters = read("PHASE_ACCOUNTING.json")
        for key, value in counters.items():
            if isinstance(value, (int, bool)):
                self.assertEqual(value, 0, key)
        self.assertEqual(counters["fresh_semantic_suite"], "NOT YET AUTHORED")
        self.assertTrue(self.plan["benchmark_quarantine"])

    def test_all_named_history_bytes_unchanged(self):
        history = read("HISTORICAL_INTEGRITY_RECEIPT.json")
        for path, expected in history["sha256"].items():
            with self.subTest(path=path):
                self.assertEqual(sha(ROOT / path), expected)
        self.assertIn("NOT_ASSESSED", history["historical_outcomes"]["llguidance_1.9.1"])
        self.assertIn("NOT_CAUSAL", history["historical_outcomes"]["LMFE_0.11.3"])

    def test_helper_and_tests_import_only_record_tools(self):
        for path, allowed in [(HELPER, {"copy", "hashlib", "json"}), (Path(__file__), {"ast", "hashlib", "json", "pathlib", "types", "unittest"})]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            modules = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    modules.add(node.module)
            self.assertEqual(modules, allowed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
