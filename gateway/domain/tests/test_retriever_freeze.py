"""Read-only freeze checks against named public DEVELOPMENT evidence; no model."""
import builtins
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

DOMAIN = Path(__file__).resolve().parents[1]
REPOSITORY = DOMAIN.parent.parent
BASE = DOMAIN / "evaluation/retrieval"
SELECTION = BASE / "RETRIEVER_SELECTION.md"
FREEZE = BASE / "RETRIEVER_FREEZE_RECORD.md"
RECEIPT = "4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00"
REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
COMMITS = {
    "phase_2c": "a81814d4478bbd0c1dffd98f0dce37988cd29031",
    "phase_2d": "212284b964b2ea867464574c66d9e587c4785231",
    "phase_2e": "df69b489b24f410946de35a3cbbc922b6f044e72",
}
FOLDERS = {
    "bm25": "retrieval_dev_lexical_baseline",
    "bge": "retrieval_dev_embedding_baseline",
    "rrf": "retrieval_dev_hybrid_rrf_baseline",
}
NAMES = ("DEVELOPMENT_RESULTS.json", "DEVELOPMENT_REPORT.md", "RUN_MANIFEST.json")
EVIDENCE_FILES = tuple(REPOSITORY / "artifacts" / folder / name for folder in FOLDERS.values() for name in NAMES)


def document(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"^```json\n(.*?)^```", text, re.M | re.S)
    if len(blocks) != 1:
        raise ValueError("Each freeze document must have one explicit JSON identity/configuration block")
    return text, json.loads(blocks[0])


def table(text, heading):
    section = text.split(heading + "\n", 1)[1].split("\n##", 1)[0]
    rows = [tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            for line in section.splitlines() if line.startswith("|")]
    if any(len(row) != 2 for row in rows) or len(dict(rows[2:])) != len(rows[2:]):
        raise ValueError("Expected a complete two-column table without duplicate keys")
    return dict(rows[2:])


def historical_artifacts(key):
    # Fixed named paths only: no recursive discovery or manifest-directed opens.
    directory = REPOSITORY / "artifacts" / FOLDERS[key]
    blobs = {name: (directory / name).read_bytes() for name in NAMES}
    manifest = json.loads(blobs["RUN_MANIFEST.json"])
    result = json.loads(blobs["DEVELOPMENT_RESULTS.json"])
    for name in NAMES[:2]:
        if hashlib.sha256(blobs[name]).hexdigest() != manifest["output_sha256"][name]:
            raise ValueError(f"Frozen {key} artifact checksum differs: {name}")
    if result["development_receipt_sha256"] != RECEIPT or manifest["development_receipt_sha256"] != RECEIPT:
        raise ValueError("Historical Development receipt differs")
    return result, manifest, {name: hashlib.sha256(blob).hexdigest() for name, blob in blobs.items()}


class RetrieverFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection_text, cls.selection = document(SELECTION)
        cls.freeze_text, cls.freeze = document(FREEZE)
        cls.history = {key: historical_artifacts(key) for key in FOLDERS}
        cls.config = cls.freeze["configuration"]

    def test_selection_record_exists_and_is_development_only(self):
        self.assertTrue(SELECTION.is_file())
        self.assertEqual(self.selection["selection_scope"], "DEVELOPMENT_ONLY")
        self.assertEqual(self.selection["selection_date"], "2026-09-30")
        self.assertEqual(self.selection["pre_selection_worktree"], "CLEAN")

    def test_freeze_record_exists_and_identifies_eventual_owner_commit(self):
        self.assertTrue(FREEZE.is_file())
        self.assertEqual(self.freeze["freeze_date"], "2026-09-30")
        pending = self.freeze["retrieval_freeze_commit"]
        self.assertTrue(pending is None or re.fullmatch(r"[0-9a-f]{40}", pending))
        self.assertIn("eventual owner commit containing this record", self.freeze["retrieval_freeze_commit_status"])

    def test_selected_method_is_existing_bge_v0(self):
        self.assertEqual(self.selection["selected_ranked_retriever"], "BGE embedding v0")
        self.assertEqual(self.freeze["selected_ranked_retriever"], "BGE embedding v0")
        self.assertEqual(self.freeze["retrieval_method"], "EMBEDDING_COSINE")
        self.assertEqual(self.config["retrieval_method"], "EMBEDDING_COSINE")

    def test_exact_model_id(self):
        self.assertEqual(self.config["model_id"], "BAAI/bge-small-en-v1.5")
        self.assertEqual(self.config["model_id"], self.history["bge"][1]["runtime"]["requested_model_id"])

    def test_exact_revision(self):
        self.assertEqual(self.freeze["model_revision"], REVISION)
        self.assertEqual(self.freeze["model_revision"], self.history["bge"][1]["runtime"]["resolved_model_revision"])
        self.assertIn("rather than resolve an unconstrained future main revision", self.freeze_text)

    def test_threshold_and_existing_candidate_filter(self):
        self.assertEqual(self.config["abstention"]["minimum_top_score"], 0.30)
        self.assertEqual(self.config["abstention"]["comparison"], "top_score < threshold")
        self.assertIsNone(self.config["abstention"]["margin"])
        self.assertEqual(self.config["candidate_filter"], self.history["bge"][0]["configuration"]["candidate_filter"])

    def test_original_query_no_instruction_or_rewrite(self):
        self.assertEqual(self.config["query_instruction"], "")
        self.assertEqual(self.config["document_instruction"], "")
        self.assertEqual(self.config["query_transformation"], "none; original question text")
        self.assertEqual(table(self.freeze_text, "## Exact selected configuration")["Query instruction / prefix"], "None; empty prompt")

    def test_searchable_fields_match_phase2d(self):
        self.assertEqual(self.config["searchable_fields"], ["title", "section_title", "text"])
        self.assertEqual(self.config["field_joiner"], "LF")
        self.assertEqual(self.config["searchable_fields"], self.history["bge"][0]["configuration"]["searchable_fields"])

    def test_normalized_cosine_cpu_dimension_and_full_configuration(self):
        self.assertTrue(self.config["normalize_embeddings"])
        self.assertEqual(self.config["similarity"], "normalized dot product; math.fsum over unit vectors")
        self.assertEqual(self.config["device"], "cpu")
        self.assertEqual(self.freeze["embedding_dimension"], 384)
        self.assertEqual(self.config, self.history["bge"][0]["configuration"])
        self.assertEqual(self.config, self.history["bge"][1]["configuration"])

    def test_top_k_and_unrounded_canonical_ties(self):
        self.assertEqual(self.config["top_k"], 10)
        self.assertEqual(self.config["tie_breaking"], "score descending, then (policy_id, version, section_id) ascending; no rounding")

    def test_development_receipt_and_baseline_commits(self):
        for record in (self.selection, self.freeze):
            self.assertEqual(record["development_receipt_sha256"], RECEIPT)
            self.assertEqual(record["phase_commits"], COMMITS)
        self.assertEqual(self.freeze["deterministic_engine_frozen_tag"], "deterministic-engine-v0.1-pre-heldout")
        self.assertEqual(self.freeze["deterministic_engine_frozen_commit"], "a528023e64ef523ea91741d8574cc431e7bae8e3")

    def check_documented_artifacts(self, key):
        rows = table(self.freeze_text, "## Selection source artifacts and SHA-256")
        result, manifest, hashes = self.history[key]
        for name, digest in hashes.items():
            self.assertEqual(rows[f"artifacts/{FOLDERS[key]}/{name}"], digest)
        self.assertEqual(result["configuration"], manifest["configuration"])

    def test_phase2d_historical_artifact_hashes(self):
        self.check_documented_artifacts("bge")

    def test_phase2c_historical_artifact_hashes(self):
        self.check_documented_artifacts("bm25")
        config = self.history["bm25"][0]["configuration"]
        self.assertEqual((config["k1"], config["b"], config["abstention"]["minimum_top_score"], config["top_k"]), (1.5, 0.75, 1.0, 10))

    def test_phase2e_historical_artifact_hashes(self):
        self.check_documented_artifacts("rrf")
        config = self.history["rrf"][0]["configuration"]
        self.assertEqual((config["rrf_k"], config["bm25_weight"], config["embedding_weight"]), (60, 1.0, 1.0))
        self.assertEqual((config["bm25_component_depth"], config["embedding_component_depth"], config["top_k"]), (10, 10, 10))
        self.assertEqual(self.history["rrf"][1]["bge_revision"], REVISION)

    def test_historical_hash_links_and_exact_nine_artifact_inventory(self):
        self.assertEqual(self.history["bge"][1]["historical_bm25_artifact_sha256"], self.history["bm25"][2])
        self.assertEqual(self.history["rrf"][1]["historical_bm25_artifact_sha256"], self.history["bm25"][2])
        self.assertEqual(self.history["rrf"][1]["historical_bge_artifact_sha256"], self.history["bge"][2])
        self.assertEqual(set(table(self.freeze_text, "## Selection source artifacts and SHA-256")),
                         {path.relative_to(REPOSITORY).as_posix() for path in EVIDENCE_FILES})

    def test_all_selection_metric_values_match_tracked_artifacts(self):
        titles = {"bm25": "BM25 v0", "bge": "BGE embedding v0", "rrf": "Equal-weight RRF hybrid v0"}
        for key, title in titles.items():
            metrics = self.history[key][0]["metrics"]
            rows = table(self.selection_text, "### " + title)
            expected = {}
            for field, label in (("hit_at_1", "Hit@1"), ("hit_at_3", "Hit@3"),
                                 ("negative_correct_abstention", "Negative correct abstention"), ("negative_false_support", "Negative false support")):
                value = metrics[field]
                expected[label] = f"{value['count']}/{value['total']}"
            expected["MRR@10"] = f"{metrics['mrr_at_10']:.6f}"
            for k in (1, 3, 5, 10):
                value = metrics["required_coverage_at_k"][str(k)]
                expected[f"Required coverage@{k} (macro)"] = f"{value['macro_average']:.2%}"
                expected[f"Required coverage@{k} (micro)"] = f"{value['micro']['count']}/{value['micro']['total']}"
            for k in (3, 5, 10):
                value = metrics["full_required_set_success_at_k"][str(k)]
                expected[f"Multi-required full set@{k}"] = f"{value['count']}/{value['total']}"
            with self.subTest(method=key):
                self.assertEqual(rows, expected)

    def test_negative_limitation_is_explicit_and_unrepaired(self):
        self.assertIn("0/1 for BM25, BGE and RRF", self.selection_text)
        for text in (self.selection_text, self.freeze_text):
            self.assertIn("not demonstrated to be a reliable scope/answerability detector", text)
            self.assertIn("not a safety or production estimate", text)
        for key in FOLDERS:
            metrics = self.history[key][0]["metrics"]
            self.assertEqual(metrics["negative_correct_abstention"]["count"], 0)
            self.assertEqual(metrics["negative_false_support"]["count"], 1)

    def test_project_specific_rationale_keeps_exact_lookup_and_tradeoffs(self):
        self.assertIn("project-specific engineering selection", self.selection_text)
        self.assertIn("BGE is not claimed to be universally superior", self.selection_text)
        self.assertIn("No synthetic overall score or metric weights", self.selection_text)
        self.assertIn("Mandatory policy support already uses deterministic exact required-section lookup", self.selection_text)
        self.assertIn("BM25 has stronger Hit@1", self.selection_text)
        self.assertIn("lowest MRR", self.selection_text)

    def test_recorded_runtime_and_model_file_hashes_match_phase2d(self):
        runtime = self.history["bge"][1]["runtime"]
        rows = table(self.freeze_text, "## Frozen Phase 2D runtime identity")
        self.assertEqual(rows["Python"], runtime["python_version"])
        for key, value in runtime["versions"].items():
            self.assertEqual(rows[key], value)
        self.assertEqual(table(self.freeze_text, "## Exact model-file SHA-256 from Phase 2D"), runtime["model_file_sha256"])

    def test_corpus_is_same_verified_25_section_inventory(self):
        corpus = self.freeze["corpus"]
        self.assertEqual((corpus["document_count"], corpus["section_count"], corpus["policy_version"]), (8, 25, "1.0-demo"))
        self.assertEqual(corpus["policy_bundle_id"], "last-mile-exception-triage-demo")
        self.assertEqual(corpus["artifact_manifest_sha256"], self.history["bge"][1]["artifact_manifest_sha256"])
        expected = {" / ".join(row["identity"]): row["content_hash"] for row in self.history["bge"][1]["section_content_hashes"]}
        self.assertEqual(len(expected), 25)
        self.assertEqual(table(self.freeze_text, "## Verified 25-section corpus identity"), expected)

    def test_explicit_future_revision_boundary_and_unopened_custody(self):
        self.assertIn("Any future change to the embedding model, model revision, query instruction, searchable fields, threshold, normalization, similarity, top-k evaluation depth, candidate filtering, tie-breaking, or retrieval method constitutes a new retriever revision and must not retroactively redefine this frozen configuration.", self.freeze_text)
        self.assertIn("The frozen retriever configuration was selected using only DEVELOPMENT results. Retrieval HELD_OUT remained unopened during method selection.", self.freeze_text)
        for record in (self.selection, self.freeze):
            self.assertFalse(record["held_out_opened_during_selection"])
            self.assertFalse(record["post_baseline_tuning_performed"])

    def test_only_explicit_development_paths_required(self):
        self.assertEqual(len(EVIDENCE_FILES), 9)
        for path in EVIDENCE_FILES + (SELECTION, FREEZE):
            self.assertTrue(path.is_relative_to(REPOSITORY))
            self.assertNotRegex(path.as_posix().lower(), r"held_?out|private|authoring|\.cache")

    def test_offline_read_boundary_in_isolated_process(self):
        result = subprocess.run([sys.executable, "-I", "-B", "-S", str(Path(__file__).resolve()), "--offline-check"],
                                cwd=REPOSITORY, capture_output=True, text=True, check=True)
        self.assertIn("OFFLINE FREEZE CHECKS PASSED", result.stdout)


def offline_check():
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split(".")[0] in {"sentence_transformers", "transformers", "torch", "numpy", "huggingface_hub", "retrieval"}:
            raise AssertionError("Model/retriever imports are forbidden in freeze tests")
        return original(name, *args, **kwargs)
    builtins.__import__ = guarded
    allowed = {path.resolve() for path in EVIDENCE_FILES + (SELECTION, FREEZE, Path(__file__))}
    def audit(event, args):
        if event.startswith("socket.") or event == "subprocess.Popen":
            raise AssertionError("Network and model subprocesses are forbidden")
        if event == "open" and isinstance(args[0], str):
            path = Path(args[0]).resolve()
            if path.is_relative_to(REPOSITORY) and path not in allowed:
                raise AssertionError("Only the named freeze records and nine Development artifacts may be read")
    sys.addaudithook(audit)
    tests = unittest.defaultTestLoader.loadTestsFromTestCase(RetrieverFreezeTests)
    suite = unittest.TestSuite(test for test in tests if test._testMethodName != "test_offline_read_boundary_in_isolated_process")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("OFFLINE FREEZE CHECKS PASSED")


if __name__ == "__main__":
    if sys.argv[1:] == ["--offline-check"]:
        offline_check()
    else:
        unittest.main()
