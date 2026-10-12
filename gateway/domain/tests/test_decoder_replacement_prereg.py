"""Offline preregistration consistency checks; never run a decoder or benchmark."""
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/answerability_semantic_v2_decoder_replacement_prereg"


def read(name):
    return json.loads((ART / name).read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReplacementPreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = read("REPLACEMENT_DECODER_REGISTRY.json")

    def test_exact_original_schema(self):
        schema = self.registry["schema"]
        self.assertEqual(schema["sha256"], "6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e")
        self.assertEqual(digest(ROOT / schema["path"]), schema["sha256"])
        self.assertFalse(schema["alteration_permitted"])

    def test_historical_owner_rejection_and_bytes(self):
        history = self.registry["historical_diagnosis"]
        self.assertEqual(history["status"], "OWNER_REVIEWED / DIAGNOSTIC_ESTABLISHED")
        self.assertEqual(history["exact_v2_xgrammar_0_2_8_suitability"], "REJECTED")
        self.assertEqual(digest(ROOT / history["freeze_record"]), history["sha256"])
        receipt = read("HISTORICAL_INTEGRITY_RECEIPT.json")
        self.assertEqual(receipt["file_count"], len(receipt["sha256"]))
        for path, expected in receipt["sha256"].items():
            with self.subTest(path=path):
                self.assertEqual(digest(ROOT / path), expected)

    def test_exactly_one_pinned_replacement(self):
        self.assertEqual(self.registry["replacement_candidates"], [{
            "distribution": "lm-format-enforcer", "version": "0.11.3",
            "python_package": "lmformatenforcer"}])
        self.assertEqual(self.registry["status"], "REPLACEMENT_DECODER_SELECTED_NOT_QUALIFIED")
        self.assertEqual(self.registry["capability"], "NOT_ASSESSED")
        self.assertEqual(self.registry["installation_status"], "INSTALLATION_NOT_AUTHORIZED")

    def test_release_metadata_identity_and_no_downloaded_package(self):
        identity = read("LMFE_PACKAGE_IDENTITY.json")
        metadata = read("PYPI_RELEASE_METADATA.json")
        self.assertEqual(identity["metadata_sha256"], digest(ART / "PYPI_RELEASE_METADATA.json"))
        self.assertEqual(identity["version"], metadata["info"]["version"])
        self.assertEqual(identity["requires_dist"], metadata["info"]["requires_dist"])
        self.assertEqual(identity["requires_python"], "<4.0,>=3.8")
        self.assertFalse(identity["package_installed"])
        self.assertFalse(identity["package_imported"])
        for file in identity["release_files"]:
            self.assertFalse(file["downloaded"])
            match = next(f for f in metadata["urls"] if f["filename"] == file["filename"])
            self.assertEqual(file["sha256"], match["digests"]["sha256"])

    def test_dependency_gap_not_silently_resolved(self):
        deps = read("LMFE_DEPENDENCY_REQUIREMENTS.json")
        self.assertEqual([e["requirement"] for e in deps["direct_dependencies"]],
                         ["pydantic>=1.10.8", "interegular>=0.3.2", "packaging", "pyyaml"])
        self.assertEqual(deps["missing_direct_dependencies"], ["interegular>=0.3.2"])
        self.assertIsNone(deps["installed_transitive_graph"]["interegular"]["declared_dependencies"])
        self.assertFalse(deps["target_package_installation_authorized"])
        self.assertEqual(deps["environment_drift"], 0)
        frozen = json.loads((ROOT / "artifacts/answerability_semantic_v2_xgrammar_diagnostic/POST_DIAGNOSTIC_PACKAGE_INVENTORY.json").read_bytes())
        self.assertEqual(read("ENVIRONMENT_METADATA_SNAPSHOT.json"), frozen)

    def test_all_historical_structural_cases_preregistered_only(self):
        gate = self.registry["conformance_gate"]
        self.assertEqual(gate["status"], "PREREGISTERED_NOT_EXECUTED")
        self.assertEqual(digest(ROOT / gate["fixture_source"]), gate["fixture_source_sha256"])
        fixtures = json.loads((ROOT / gate["fixture_source"]).read_bytes())["fixtures"]
        cases = gate["cases"]
        self.assertEqual(len(cases), 8)
        self.assertEqual([c["expected"] for c in cases], ["ACCEPT"] + ["REJECT"] * 7)
        for case, fixture in zip(cases, fixtures):
            self.assertEqual(case["fixture_id"], fixture["fixture_id"])
            self.assertEqual(case["text_sha256"], hashlib.sha256(fixture["text"].encode()).hexdigest())

    def test_feature_probe_coverage_includes_schema_composition(self):
        required = {"required", "enum", "const", "type:object", "additionalProperties",
                    "type:array", "items", "minItems", "maxItems", "type:integer",
                    "minimum", "maximum", "uniqueItems", "type:string", "minLength",
                    "pattern", "oneOf", "anyOf", "allOf", "if", "then", "else", "contains", "completion/EOS"}
        self.assertEqual(set(self.registry["conformance_gate"]["required_feature_probes"]), required)
        document = (ART / "STRUCTURAL_CONFORMANCE_GATE.md").read_text()
        for keyword in ("uniqueItems", "oneOf", "anyOf", "allOf", "contains", "EOS"):
            self.assertIn(keyword, document)

    def test_future_gate_blocks_premature_model_progression(self):
        gate = self.registry["conformance_gate"]
        self.assertTrue(gate["completion_requires_eos"])
        self.assertTrue(gate["core_failure_blocks_generation"])
        self.assertTrue(gate["feature_gap_blocks_full_schema_qualification"])
        self.assertTrue(gate["feature_gap_requires_owner_review"])
        self.assertEqual(gate["paths"], ["CHARACTER_PARSER", "TOKEN_ENFORCER_CALLBACK"])

    def test_runtime_and_adapter_boundary_frozen(self):
        runtime = self.registry["runtime"]
        self.assertEqual(runtime["revision"], "989aa7980e4cf806f80c7fef2b1adb7bc71aa306")
        self.assertEqual(runtime["frozen_repetition_penalty"], 1.0)
        self.assertEqual(len(self.registry["adapter_boundary"]), 4)
        self.assertFalse(self.registry["future_integration"]["executed"])

    def test_no_execution_installation_or_benchmark_authorized(self):
        self.assertEqual(set(self.registry["counters"].values()), {0})
        self.assertEqual(set(self.registry["quarantine"].values()), {False})
        self.assertEqual(self.registry["fresh_semantic_suite"], "NOT YET AUTHORED")
        for action in ("package installation", "pip version resolution", "decoder execution",
                       "parser conformance execution", "model initialization", "model generate",
                       "model forward", "DEVELOPMENT access", "HELD_OUT access", "retrieval",
                       "alternate decoder comparison", "fresh semantic suite authoring"):
            self.assertIn(action, self.registry["forbidden_actions"])

    def test_registry_artifact_hashes(self):
        for name, expected in self.registry["artifact_sha256"].items():
            with self.subTest(name=name):
                self.assertEqual(digest(ART / name), expected)

    def test_checks_did_not_import_model_or_decoder_packages(self):
        prohibited = {"lmformatenforcer", "xgrammar", "torch", "transformers", "tokenizers", "sentence_transformers"}
        self.assertFalse(prohibited.intersection(name.split(".")[0] for name in sys.modules))


if __name__ == "__main__":
    unittest.main()
