"""Pinned Development RRF evaluation and historical-evidence checks; no model."""
import copy
from dataclasses import replace
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

DOMAIN = Path(__file__).resolve().parents[1]
BASE = DOMAIN / "evaluation/retrieval"
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
import evaluate_hybrid_development as evaluation
from retrieval.hybrid_rrf_retriever import HybridRRFRetriever
from test_hybrid_rrf_retrieval import FakeComponent


class HybridDevelopmentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = evaluation.baseline.load_development()
        cls.store = evaluation.SectionStore.load()

    def retriever(self, positions=(0,)):
        return HybridRRFRetriever(FakeComponent(self.store, positions), FakeComponent(self.store, positions))

    def history_copy(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for key, source in (("lexical", evaluation.phase2d.HISTORY), ("embedding", evaluation.phase2d.OUTPUT)):
            (root / key).mkdir()
            for name in ("DEVELOPMENT_RESULTS.json", "DEVELOPMENT_REPORT.md", "RUN_MANIFEST.json"):
                shutil.copyfile(source / name, root / key / name)
        return root / "lexical", root / "embedding"

    def test_shared_metric_semantics_and_query_only_once(self):
        retriever = self.retriever()
        spy = Mock(wraps=retriever)
        actual = evaluation.evaluate(self.data, spy, {"backend": "fake"})
        expected = evaluation.baseline.evaluate(self.data, retriever)
        self.assertEqual(spy.search.call_count, 15)
        for call, q in zip(spy.search.call_args_list, self.data.questions):
            self.assertEqual(call.args, (q["question"],))
            self.assertEqual(call.kwargs, {"top_k": 10})
        for key in ("metrics", "failures", "development_receipt_sha256"):
            self.assertEqual(actual[key], expected[key])
        for row, original in zip(actual["questions"], expected["questions"]):
            for key in original.keys() - {"ranked_sections"}:
                self.assertEqual(row[key], original[key])
        self.assertEqual(actual["evaluation_type"], "DEVELOPMENT_HYBRID_RRF_BASELINE")

    def test_component_diagnostics_and_contributions_preserved(self):
        result = evaluation.evaluate(self.data, self.retriever(), {})
        for row in result["questions"]:
            self.assertEqual(row["component_statuses"], {"bm25": "RETRIEVED", "embedding": "RETRIEVED"})
            self.assertEqual(row["ranked_sections"][0]["bm25_rank"], 1)
            self.assertEqual(row["ranked_sections"][0]["embedding_rank"], 1)
            self.assertEqual(row["component_rankings"]["bm25"][0]["rank"], 1)
            self.assertEqual(row["component_rankings"]["embedding"][0]["rank"], 1)

    def test_bad_receipt_rejected_before_search(self):
        fake = Mock()
        with self.assertRaises(evaluation.baseline.DevelopmentIntegrityError):
            evaluation.evaluate(replace(self.data, receipt="wrong"), fake, {})
        fake.search.assert_not_called()

    def test_cli_rejects_arbitrary_split_path_or_parameters(self):
        for args in (("--split", "OTHER"), ("--directory", "outside"), ("--rrf-k", "20")):
            with patch.object(sys, "argv", ["evaluate_hybrid_development.py", *args]), \
                 patch.object(evaluation, "build_retriever") as build, patch.object(evaluation.baseline, "load_development") as loader:
                with self.assertRaisesRegex(SystemExit, "no arguments"):
                    evaluation.main()
                build.assert_not_called()
                loader.assert_not_called()

    def test_shared_loader_rejects_split_and_path_before_questions(self):
        for field, value in (("split", "OTHER"), ("filename", "../outside.json")):
            with tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / "DEVELOPMENT_MANIFEST.json"
                manifest = evaluation.baseline.read_json_bytes((BASE / target.name).read_bytes())
                manifest["questions"][0][field] = value
                target.write_bytes(evaluation.baseline.json_bytes(manifest))
                reads, original = [], Path.read_bytes
                def tracked(path):
                    reads.append(path.name)
                    return original(path)
                with patch.object(Path, "read_bytes", tracked), self.assertRaises(evaluation.baseline.DevelopmentIntegrityError):
                    evaluation.baseline.load_development(Path(temporary))
                self.assertEqual(reads, ["DEVELOPMENT_MANIFEST.json"])

    def test_both_historical_baselines_verified_read_only(self):
        before = evaluation.load_history()
        self.assertEqual(before["metrics"]["bm25"]["hit_at_1"]["count"], 11)
        self.assertEqual(before["metrics"]["embedding"], evaluation.expected_embedding_metrics())
        self.assertEqual(before["embedding_runtime"]["resolved_model_revision"], evaluation.BGE_REVISION)
        self.assertEqual(evaluation.load_history(), before)

    def test_corrupt_historical_artifacts_rejected_for_both_systems(self):
        for system in (0, 1):
            paths = self.history_copy()
            report = paths[system] / "DEVELOPMENT_REPORT.md"
            report.write_bytes(report.read_bytes() + b"corrupted")
            with self.subTest(system=system), self.assertRaisesRegex(evaluation.baseline.DevelopmentIntegrityError, "hash"):
                evaluation.load_history(*paths)

    def test_phase2c_hashes_must_match_phase2d_manifest(self):
        left, right = self.history_copy()
        path = right / "RUN_MANIFEST.json"
        manifest = evaluation.baseline.read_json_bytes(path.read_bytes())
        manifest["historical_bm25_artifact_sha256"]["RUN_MANIFEST.json"] = "0" * 64
        path.write_bytes(evaluation.baseline.json_bytes(manifest))
        with self.assertRaisesRegex(evaluation.baseline.DevelopmentIntegrityError, "Phase 2C hashes"):
            evaluation.load_history(left, right)

    def test_historical_embedding_semantics_checked_beyond_output_hashes(self):
        for mode in ("receipt", "configuration", "revision", "metrics"):
            left, right = self.history_copy()
            result = evaluation.baseline.read_json_bytes((right / "DEVELOPMENT_RESULTS.json").read_bytes())
            manifest = evaluation.baseline.read_json_bytes((right / "RUN_MANIFEST.json").read_bytes())
            if mode == "receipt": result["development_receipt_sha256"] = manifest["development_receipt_sha256"] = "wrong"
            elif mode == "configuration":
                result["configuration"]["top_k"] = manifest["configuration"]["top_k"] = 5
            elif mode == "revision":
                result["runtime"]["resolved_model_revision"] = manifest["runtime"]["resolved_model_revision"] = "0" * 40
            else: result["metrics"]["hit_at_1"]["count"] = 14
            raw = evaluation.baseline.json_bytes(result)
            (right / "DEVELOPMENT_RESULTS.json").write_bytes(raw)
            manifest["output_sha256"]["DEVELOPMENT_RESULTS.json"] = evaluation.baseline.sha256(raw)
            (right / "RUN_MANIFEST.json").write_bytes(evaluation.baseline.json_bytes(manifest))
            with self.subTest(mode=mode), self.assertRaises(evaluation.baseline.DevelopmentIntegrityError):
                evaluation.load_history(left, right)

    def test_factory_pins_revision_and_reuses_same_store(self):
        history = evaluation.load_history()
        backend = Mock()
        backend.metadata = copy.deepcopy(history["embedding_runtime"])
        backend.metadata["requested_revision"] = evaluation.BGE_REVISION
        left, right = FakeComponent(self.store), FakeComponent(self.store)
        right.runtime_metadata = copy.deepcopy(backend.metadata)
        with patch.object(evaluation, "SentenceTransformerBackend", return_value=backend) as factory, \
             patch.object(evaluation, "LexicalRetriever", return_value=left) as lexical, \
             patch.object(evaluation, "EmbeddingRetriever", return_value=right) as embedding:
            retriever, runtime = evaluation.build_retriever(self.store, history)
            factory.assert_called_once_with(revision=evaluation.BGE_REVISION, local_files_only=True)
            lexical.assert_called_once_with(self.store)
            embedding.assert_called_once_with(self.store, encoder=backend)
            self.assertEqual(retriever.section_count, 25)
            self.assertTrue(runtime["evaluation_revision_pinned"])

    def test_wrong_revision_or_files_stop_before_components(self):
        history = evaluation.load_history()
        for mode in ("revision", "files"):
            metadata = copy.deepcopy(history["embedding_runtime"])
            metadata["requested_revision"] = evaluation.BGE_REVISION
            if mode == "revision": metadata["resolved_model_revision"] = "0" * 40
            else: metadata["model_file_sha256"]["model.safetensors"] = "wrong"
            with patch.object(evaluation, "SentenceTransformerBackend", return_value=Mock(metadata=metadata)), \
                 patch.object(evaluation, "EmbeddingRetriever") as component:
                with self.assertRaises(evaluation.baseline.DevelopmentIntegrityError):
                    evaluation.build_retriever(self.store, history)
                component.assert_not_called()

    def test_existing_output_refused_before_model_initialization(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(evaluation, "OUTPUT", Path(temporary)), \
             patch.object(sys, "argv", ["evaluate_hybrid_development.py"]), patch.object(evaluation, "build_retriever") as build:
            with self.assertRaisesRegex(SystemExit, "Refusing to overwrite"):
                evaluation.main()
            build.assert_not_called()

    def test_invalid_custody_stops_before_model_initialization(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(evaluation, "OUTPUT", Path(temporary) / "absent"), \
             patch.object(sys, "argv", ["evaluate_hybrid_development.py"]), \
             patch.object(evaluation.baseline, "load_development", side_effect=ValueError("bad custody")), \
             patch.object(evaluation, "build_retriever") as build:
            with self.assertRaisesRegex(ValueError, "bad custody"):
                evaluation.main()
            build.assert_not_called()

    def test_failure_records_output_hashes_and_history_preserved(self):
        history = evaluation.load_history()
        result = evaluation.evaluate(self.data, self.retriever(()), {"backend": "fake"})
        result["historical_metrics"] = history["metrics"]
        self.assertEqual(len(result["failures"]), 14)
        self.assertEqual(result["metrics"]["negative_correct_abstention"]["count"], 1)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "candidate"
            evaluation.write_artifacts(result, self.data, self.store, history, output)
            manifest = evaluation.baseline.read_json_bytes((output / "RUN_MANIFEST.json").read_bytes())
            for name, digest in manifest["output_sha256"].items():
                self.assertEqual(evaluation.baseline.sha256((output / name).read_bytes()), digest)
            report = (output / "DEVELOPMENT_REPORT.md").read_text(encoding="utf-8")
            for row in result["failures"]:
                self.assertIn("### " + row["question_id"], report)
            for text in ("BM25 v0", "BGE embedding v0", "Equal-weight RRF hybrid v0", "Raw component scores are not fused", "RRF score is not confidence"):
                self.assertIn(text, report)
            with self.assertRaises(FileExistsError):
                evaluation.write_artifacts(result, self.data, self.store, history, output)
        self.assertEqual(evaluation.load_history()["artifact_sha256"], history["artifact_sha256"])


if __name__ == "__main__":
    unittest.main()
