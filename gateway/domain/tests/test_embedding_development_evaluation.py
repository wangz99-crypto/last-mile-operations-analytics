"""Embedding evaluator custody and shared-rubric tests, without any real model."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

DOMAIN = Path(__file__).resolve().parents[1]
BASE = DOMAIN / "evaluation/retrieval"
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
import evaluate_embedding_development as embedding
from retrieval.embedding_retriever import EmbeddingRetriever
from test_embedding_retrieval import FakeEncoder


class EmbeddingDevelopmentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = embedding.baseline.load_development()
        cls.store = embedding.baseline.SectionStore.load()

    def test_reuses_unchanged_evaluation_semantics_and_query_only_calls(self):
        retriever = EmbeddingRetriever(self.store, encoder=FakeEncoder())
        spy = Mock(wraps=retriever)
        spy.runtime_metadata = retriever.runtime_metadata
        result = embedding.evaluate(self.data, spy)
        self.assertEqual(spy.search.call_count, 15)
        for call, question in zip(spy.search.call_args_list, self.data.questions):
            self.assertEqual(call.args, (question["question"],))
            self.assertEqual(call.kwargs, {"top_k": 10})
        expected = embedding.baseline.evaluate(self.data, retriever)
        for key in ("metrics", "questions", "failures", "development_receipt_sha256"):
            self.assertEqual(result[key], expected[key])
        self.assertEqual(result["evaluation_type"], "DEVELOPMENT_EMBEDDING_BASELINE")
        self.assertEqual(result["configuration"]["model_id"], "BAAI/bge-small-en-v1.5")

    def test_bad_receipt_rejected_before_search(self):
        from dataclasses import replace
        retriever = Mock()
        with self.assertRaises(embedding.baseline.DevelopmentIntegrityError):
            embedding.evaluate(replace(self.data, receipt="invalid"), retriever)
        retriever.search.assert_not_called()

    def test_historical_artifacts_are_read_only_and_metrics_match(self):
        metrics, hashes = embedding.load_history()
        self.assertEqual((metrics["hit_at_1"]["count"], metrics["hit_at_3"]["count"]), (11, 11))
        self.assertAlmostEqual(metrics["mrr_at_10"], 0.7928571428571428)
        self.assertEqual(set(hashes), {"DEVELOPMENT_RESULTS.json", "DEVELOPMENT_REPORT.md", "RUN_MANIFEST.json"})
        self.assertNotEqual(embedding.OUTPUT, embedding.HISTORY)

    def test_cli_rejects_arbitrary_input_or_split_before_loading(self):
        with patch.object(sys, "argv", ["evaluate_embedding_development.py", "--split", "anything"]), \
             patch.object(embedding.baseline, "load_development") as loader, patch.object(embedding, "EmbeddingRetriever") as model:
            with self.assertRaisesRegex(SystemExit, "no arguments"):
                embedding.main()
            loader.assert_not_called()
            model.assert_not_called()

    def test_existing_artifact_directory_refused_before_loading(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(embedding, "OUTPUT", Path(temporary)), \
             patch.object(sys, "argv", ["evaluate_embedding_development.py"]), patch.object(embedding, "EmbeddingRetriever") as model:
            with self.assertRaisesRegex(SystemExit, "Refusing to overwrite"):
                embedding.main()
            model.assert_not_called()

    def test_invalid_import_stops_before_model_initialization(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(embedding, "OUTPUT", Path(temporary) / "absent"), \
             patch.object(sys, "argv", ["evaluate_embedding_development.py"]), \
             patch.object(embedding.baseline, "load_development", side_effect=ValueError("invalid custody")), \
             patch.object(embedding, "EmbeddingRetriever") as model:
            with self.assertRaisesRegex(ValueError, "invalid custody"):
                embedding.main()
            model.assert_not_called()

    def test_report_and_artifacts_retain_failures_and_valid_hashes(self):
        retriever = EmbeddingRetriever(self.store, encoder=FakeEncoder(query=(0, 1)))
        result = embedding.evaluate(self.data, retriever)
        history, hashes = embedding.load_history()
        result["historical_bm25_metrics"] = history
        # All 14 synthetic answerable searches abstain; the report must retain all.
        self.assertEqual(len(result["failures"]), 14)
        self.assertEqual(result["metrics"]["negative_correct_abstention"]["count"], 1)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "test-results"
            embedding.write_artifacts(result, self.data, self.store, hashes, output)
            manifest = embedding.baseline.read_json_bytes((output / "RUN_MANIFEST.json").read_bytes())
            for name, digest in manifest["output_sha256"].items():
                self.assertEqual(embedding.baseline.sha256((output / name).read_bytes()), digest)
            self.assertEqual(manifest["historical_bm25_artifact_sha256"], hashes)
            report = (output / "DEVELOPMENT_REPORT.md").read_text(encoding="utf-8")
            self.assertIn("not an improvement claim", report)
            self.assertIn("No model sweep", report)
            self.assertIn("not confidence", report)
            for failure in result["failures"]:
                self.assertIn("### " + failure["question_id"], report)
            with self.assertRaises(FileExistsError):
                embedding.write_artifacts(result, self.data, self.store, hashes, output)
        self.assertEqual(embedding.load_history()[1], hashes)


if __name__ == "__main__":
    unittest.main()
