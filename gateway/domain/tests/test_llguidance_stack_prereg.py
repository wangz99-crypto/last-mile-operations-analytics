"""Offline record checks only; never import or execute a decoder or schema validator."""
import ast
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
RECORDS = ROOT / "artifacts/answerability_semantic_v2_llguidance_stack_prereg"
SCHEMA_SHA = "6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e"


def read(name):
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LLGuidancePreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read("PREREGISTERED_STACK.json")

    def test_only_owner_selected_stack(self):
        self.assertEqual(self.plan["grammar_engine"]["name"], "llguidance")
        self.assertEqual(self.plan["grammar_engine"]["version"], "1.9.1")
        self.assertEqual(self.plan["future_integration"]["name"], "outlines")
        self.assertEqual(self.plan["future_integration"]["version"], "1.3.3")
        self.assertEqual(self.plan["future_integration"]["backend"], "llguidance")
        self.assertEqual(self.plan["alternate_candidates"], [])

    def test_release_wheel_identities(self):
        for name, version, filename, sha in [
            ("llguidance", "1.9.1", "llguidance-1.9.1-cp39-abi3-win_amd64.whl",
             "8aaa55958adb4871016700e9140543ccbd9d6b5136d0a1756a114af706cc50c1"),
            ("outlines", "1.3.3", "outlines-1.3.3-py3-none-any.whl",
             "0e185dd5a0cfeb62e0268018972d3c22bb9b7d43db3dc1f39f3b754175a82c54"),
        ]:
            with self.subTest(name=name):
                obj = read(name.upper() + "_PACKAGE_IDENTITY.json")
                self.assertEqual((obj["name"], obj["version"]), (name, version))
                self.assertEqual(obj["selected_wheel"]["filename"], filename)
                self.assertEqual(obj["selected_wheel"]["digests"]["sha256"], sha)
                self.assertFalse(obj["wheel_downloaded"])

    def test_exact_schema_bytes_and_candidate(self):
        self.assertEqual(self.plan["schema_sha256"], SCHEMA_SHA)
        self.assertEqual(digest(ROOT / self.plan["schema_path"]), SCHEMA_SHA)
        self.assertEqual(self.plan["semantic_candidate"], "SEMANTIC_MATERIAL_SUPPORT_V2")
        self.assertEqual(self.plan["semantic_candidate_status"], "PRE_REGISTERED_NOT_EVALUATED")
        self.assertFalse(self.plan["schema_modifications_permitted"])

    def test_historical_rejections_and_byte_integrity(self):
        history = read("HISTORICAL_INTEGRITY_RECEIPT.json")
        self.assertEqual(history["history"]["LMFE"]["exact_schema_suitability"], "REJECTED")
        self.assertEqual(history["history"]["LMFE"]["helper_causality"], "NOT_CAUSAL")
        self.assertEqual(history["history"]["XGrammar"]["exact_schema_suitability"], "REJECTED")
        for name, sha in history["sha256"].items():
            with self.subTest(name=name):
                self.assertEqual(digest(ROOT / name), sha)

    def test_no_oneof_coercion_or_lenient_relaxation(self):
        self.assertIs(self.plan["coerce_one_of"], False)
        self.assertIs(self.plan["lenient"], False)
        self.assertIs(self.plan["external_reference_resolution"], False)

    def test_core_fixture_identity_and_expectations(self):
        path = ROOT / self.plan["core_fixture_path"]
        self.assertEqual(digest(path), self.plan["core_fixture_sha256"])
        original = json.loads(path.read_text(encoding="utf-8"))["fixtures"]
        self.assertEqual([f["fixture_id"] for f in original], [f"M{i}" for i in range(1, 9)])
        self.assertEqual([f["expected"] for f in original], ["ACCEPT"] + ["REJECT"] * 7)
        for recorded, frozen in zip(self.plan["core_gate"], original):
            self.assertEqual(recorded, {k: frozen[k] for k in recorded})
            self.assertEqual(hashlib.sha256(frozen["text"].encode()).hexdigest(), recorded["input_sha256"])

    def test_known_risk_pointers_exist_without_schema_conversion(self):
        self.assertEqual(self.plan["known_risk_pointers"], [
            "/oneOf/0/properties/material_asks", "/oneOf/1/properties/material_asks",
            "/properties/material_asks/items", "/properties/material_asks/items/allOf/0",
        ])
        schema = json.loads((ROOT / self.plan["schema_path"]).read_text(encoding="utf-8"))
        for pointer in self.plan["known_risk_pointers"]:
            node = schema
            for part in pointer.strip("/").split("/"):
                node = node[int(part)] if isinstance(node, list) else node[part]
            self.assertIsInstance(node, dict)

    def test_mandatory_ladder_order(self):
        self.assertEqual(self.plan["ladder"], ["K0", "K1", "K2", "K3", "K4", "K5", "L", "M"])
        self.assertTrue(self.plan["every_earlier_mandatory_gate_must_pass"])
        self.assertTrue(self.plan["critical_warning_owner_review_required"])
        self.assertFalse(self.plan["errors_are_reject"])

    def test_no_tokenizer_or_model_before_pure_gates(self):
        tokenizer = self.plan["tokenizer_boundary"]
        self.assertEqual(tokenizer["earliest_after"], ["K1", "K2", "K3"])
        for name in ["load_in_this_phase", "network", "model_initialization"]:
            self.assertFalse(tokenizer[name])
        self.assertEqual(self.plan["outlines_boundary"]["after"], ["K1", "K2", "K3", "K4", "K5"])
        self.assertEqual(self.plan["model_boundary"]["after"], ["K1", "K2", "K3", "K4", "K5", "L"])

    def test_frozen_model_identity_and_future_budget(self):
        model = self.plan["model_boundary"]
        self.assertEqual(model["model"], "Qwen/Qwen2.5-1.5B-Instruct")
        self.assertEqual(model["revision"], "989aa7980e4cf806f80c7fef2b1adb7bc71aa306")
        self.assertEqual(model["repetition_penalty"], 1.0)
        self.assertEqual(model["generate_calls"], 3)
        self.assertEqual(model["quality_retries"], 0)
        self.assertEqual(model["schema_repair_retries"], 0)

    def test_zero_execution_and_quarantine_record(self):
        counts = read("PHASE_ACCOUNTING.json")
        for key, value in counts.items():
            if isinstance(value, (int, bool)):
                self.assertEqual(value, 0, key)
        self.assertEqual(counts["fresh_v2_semantic_qualification_suite"], "NOT YET AUTHORED")

    def test_dependency_classifications_cover_every_declared_edge(self):
        graph = read("DECLARED_DEPENDENCY_GRAPH.json")
        allowed = {"ALREADY_SATISFIED", "MISSING", "VERSION_CONFLICT", "OPTIONAL_NOT_REQUIRED_YET"}
        for package in ["llguidance", "outlines"]:
            original = read(package.upper() + "_PACKAGE_IDENTITY.json")["requires_dist"] or []
            entries = graph[package]["declared_direct_edges"]
            self.assertEqual([e["requirement"] for e in entries], original)
            for entry in entries:
                self.assertIn(entry["status"], allowed)
                if entry["status"] == "MISSING" and not entry["metadata_exact_pin"] and entry["distribution"] != "llguidance":
                    self.assertEqual(entry["version_selection"], "VERSION_SELECTION_PENDING_OWNER_AUTHORIZATION")

    def test_runtime_inventory_no_selected_packages(self):
        inv = read("ENVIRONMENT_METADATA_SNAPSHOT.json")
        self.assertEqual(len(inv["packages"]), 36)
        self.assertNotIn("llguidance", inv["packages"])
        self.assertNotIn("outlines", inv["packages"])
        self.assertEqual(inv["packages"]["xgrammar"]["version"], "0.2.8")
        self.assertEqual(inv["packages"]["lm-format-enforcer"]["version"], "0.11.3")

    def test_source_blocker_is_not_a_measured_qualification(self):
        matrix = read("JSON_SCHEMA_CAPABILITY_MATRIX.json")
        self.assertEqual(matrix["outcome"], "LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED")
        self.assertFalse(matrix["qualification_failure_claimed"])
        self.assertEqual(set(matrix["blocker_keywords"]), {"uniqueItems", "contains", "if", "then", "else"})
        for key in matrix["blocker_keywords"]:
            feature = matrix["features"][key]
            self.assertTrue(feature["present"])
            self.assertEqual(feature["criticality"], "CRITICAL")
            self.assertEqual(feature["qualification"], "NOT_EXECUTED")
        self.assertFalse(self.plan["progression_authorized"])

    def test_material_keyword_inventory_matches_raw_schema(self):
        matrix = read("JSON_SCHEMA_CAPABILITY_MATRIX.json")["features"]
        schema = json.loads((ROOT / self.plan["schema_path"]).read_text(encoding="utf-8"))
        for key, entry in matrix.items():
            for pointer in entry["pointers"]:
                node = schema
                for part in pointer.strip("/").split("/"):
                    part = part.replace("~1", "/").replace("~0", "~")
                    node = node[int(part)] if isinstance(node, list) else node[part]
                self.assertIsNotNone(node, key)
            self.assertEqual(entry["present"], bool(entry["pointers"]))

    def test_offline_test_import_surface(self):
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module)
        self.assertEqual(set(modules), {"ast", "hashlib", "json", "pathlib", "unittest"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
