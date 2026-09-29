"""Pinned DEVELOPMENT receipt/boundary tests and independent metric examples."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
spec = importlib.util.spec_from_file_location("retrieval_development_evaluation", DOMAIN / "evaluation/retrieval/evaluate_development.py")
evaluation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = evaluation
spec.loader.exec_module(evaluation)
from retrieval import LexicalResult, LexicalSearchResponse

A = ("SOP-02", "1.0-demo", "late-escalate")
B = ("SOP-05", "1.0-demo", "late-evidence")
C = ("SOP-06", "1.0-demo", "handoff-boundary")
X = ("SOP-08", "1.0-demo", "decision-record")


def question(gold=(A,), required=(A,), kind="ANSWERABLE"):
    return dict(question_id="UNIT", split="DEVELOPMENT", example_only=False, question="Synthetic metric check",
                kind=kind, gold_sections=list(gold), required_sections=list(required))


def response(identities=(), abstain=False):
    records = tuple(LexicalResult(identity, i, 5.0, "test", "hash", "test.md") for i, identity in enumerate(identities, 1))
    return LexicalSearchResponse("ABSTAIN" if abstain else "RETRIEVED", records, 0.0 if abstain else 5.0,
                                 "NO_LEXICAL_OVERLAP" if abstain else None)


class RetrievalDevelopmentEvaluationTests(unittest.TestCase):
    def copied_development(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        shutil.copyfile(evaluation.BASE / "DEVELOPMENT_MANIFEST.json", base / "DEVELOPMENT_MANIFEST.json")
        shutil.copytree(evaluation.BASE / "development", base / "development")
        return base

    def change_manifest(self, base, change):
        path = base / "DEVELOPMENT_MANIFEST.json"
        value = json.loads(path.read_bytes())
        change(value)
        path.write_bytes(evaluation.json_bytes(value))

    def test_frozen_import_receipt_and_exact_ids(self):
        data = evaluation.load_development()
        self.assertEqual(data.receipt, "4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00")
        self.assertEqual(tuple(q["question_id"] for q in data.questions), evaluation.QUESTION_IDS)
        self.assertEqual(evaluation.development_receipt(dict(reversed(data.question_hashes))), data.receipt)
        payload = "".join(identity + "\t" + digest + "\n" for identity, digest in data.question_hashes).encode("utf-8")
        self.assertEqual(evaluation.sha256(payload), data.receipt)
        self.assertNotEqual(evaluation.sha256(payload[:-1]), data.receipt)

    def test_changed_file_and_recomputed_manifest_still_cannot_change_receipt(self):
        base = self.copied_development()
        path = base / "development/RQ003.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(evaluation.DevelopmentIntegrityError, "file hash differs"):
            evaluation.load_development(base)
        self.change_manifest(base, lambda m: m["questions"][0].update(sha256=evaluation.sha256(path.read_bytes())))
        with self.assertRaisesRegex(evaluation.DevelopmentIntegrityError, "aggregate receipt differs"):
            evaluation.load_development(base)

    def test_review_freeze_and_receipt_metadata_are_required(self):
        for key, value in (("owner_reviewed", False), ("dataset_frozen", False), ("review_status", "DRAFT"),
                           ("aggregate_receipt_sha256", "0" * 64), ("receipt_algorithm", "md5"), ("receipt_serialization", "no LF")):
            base = self.copied_development()
            self.change_manifest(base, lambda m: m.update({key: value}))
            with self.subTest(field=key), self.assertRaises(evaluation.DevelopmentIntegrityError):
                evaluation.load_development(base)

    def test_non_development_manifest_or_row_rejected_before_question_read(self):
        for mode in ("manifest", "row"):
            base = self.copied_development()
            if mode == "manifest":
                self.change_manifest(base, lambda m: m.update(split="HELD_OUT"))
            else:
                self.change_manifest(base, lambda m: m["questions"][-1].update(split="HELD_OUT"))
            read = Path.read_bytes
            reads = []
            def tracked(path):
                reads.append(path.name)
                return read(path)
            with self.subTest(mode=mode), patch.object(Path, "read_bytes", tracked), self.assertRaisesRegex(evaluation.DevelopmentIntegrityError, "DEVELOPMENT"):
                evaluation.load_development(base)
            self.assertEqual(reads, ["DEVELOPMENT_MANIFEST.json"])

    def test_unapproved_manifest_path_is_rejected_before_opening_any_question(self):
        for filename in ("../outside.json", "development/nested/RQ041.json", "C:/outside.json"):
            base = self.copied_development()
            self.change_manifest(base, lambda m: m["questions"][-1].update(filename=filename))
            read = Path.read_bytes
            reads = []
            def tracked(path):
                reads.append(path.name)
                return read(path)
            with self.subTest(filename=filename), patch.object(Path, "read_bytes", tracked), self.assertRaisesRegex(evaluation.DevelopmentIntegrityError, "unapproved question path"):
                evaluation.load_development(base)
            self.assertEqual(reads, ["DEVELOPMENT_MANIFEST.json"])

    def test_no_recursive_or_arbitrary_question_discovery(self):
        base = self.copied_development()
        with patch.object(Path, "glob", side_effect=AssertionError("No glob")), patch.object(Path, "rglob", side_effect=AssertionError("No recursion")):
            self.assertEqual(len(evaluation.load_development(base).questions), 15)
            (base / "development/nested").mkdir()
            (base / "development/nested/UNAUTHORIZED.json").write_text("not read", encoding="utf-8")
            with self.assertRaisesRegex(evaluation.DevelopmentIntegrityError, "exactly the 15"):
                evaluation.load_development(base)

    def test_wrong_inventory_id_and_missing_file_are_rejected(self):
        for mode in ("identity", "missing"):
            base = self.copied_development()
            if mode == "identity":
                self.change_manifest(base, lambda m: m["questions"][-1].update(question_id="UNAUTHORIZED"))
            else:
                (base / "development/RQ041.json").unlink()
            with self.subTest(mode=mode), self.assertRaises(evaluation.DevelopmentIntegrityError):
                evaluation.load_development(base)

    def test_metrics_reject_non_development_split_without_ranking(self):
        value = question()
        value["split"] = "HELD_OUT"  # Synthetic boundary marker; no private file is read.
        with self.assertRaisesRegex(evaluation.DevelopmentIntegrityError, "DEVELOPMENT"):
            evaluation.score_question(value, response((A,)))

    def test_multi_section_required_metrics_and_unique_ranks(self):
        row = evaluation.score_question(question(gold=(A, B), required=(A, B)), response((X, X, A, A, B)))
        self.assertEqual([r["rank"] for r in row["ranked_sections"]], [1, 2, 3])
        self.assertEqual(row["first_relevant_rank"], 2)
        self.assertEqual((row["hit_at_1"], row["hit_at_3"], row["reciprocal_rank_at_10"]), (False, True, 0.5))
        self.assertEqual(row["required_coverage_at_k"]["1"]["fraction"], 0)
        self.assertEqual(row["required_coverage_at_k"]["3"]["fraction"], 1)
        self.assertTrue(row["full_required_set_success_at_k"]["3"])
        partial = evaluation.score_question(question(gold=(A, B), required=(A, B)), response((A, X)))
        self.assertEqual(partial["required_coverage_at_k"]["10"]["fraction"], 0.5)
        self.assertFalse(partial["full_required_set_success_at_k"]["10"])

    def test_gold_relevance_is_distinct_from_required_coverage(self):
        row = evaluation.score_question(question(gold=(A, B), required=(B,)), response((A, X)))
        self.assertTrue(row["hit_at_1"])
        self.assertEqual(row["reciprocal_rank_at_10"], 1)
        self.assertEqual(row["required_coverage_at_k"]["10"]["fraction"], 0)

    def test_abstained_answerable_and_absent_gold_are_zero(self):
        for returned in (response(abstain=True), response((X,))):
            row = evaluation.score_question(question(), returned)
            self.assertEqual((row["hit_at_1"], row["hit_at_3"], row["reciprocal_rank_at_10"]), (False, False, 0.0))
            self.assertIsNone(row["first_relevant_rank"])
            self.assertEqual(row["required_coverage_at_k"]["10"]["fraction"], 0)

    def test_negative_abstention_and_false_support_without_fabricated_gold(self):
        q = question(gold=(), required=(), kind="NEGATIVE")
        correct = evaluation.score_question(q, response(abstain=True))
        incorrect = evaluation.score_question(q, response((A,)))
        self.assertTrue(correct["negative_correctness"])
        self.assertFalse(correct["negative_false_support"])
        self.assertFalse(incorrect["negative_correctness"])
        self.assertTrue(incorrect["negative_false_support"])
        self.assertEqual(correct["gold_sections"], [])
        self.assertIsNone(correct["hit_at_1"])
        self.assertIsNone(correct["required_coverage_at_k"])
        metrics = evaluation.aggregate_metrics([correct, incorrect])
        self.assertEqual(metrics["negative_correct_abstention"]["rate"], 0.5)
        self.assertEqual(metrics["negative_false_support"]["rate"], 0.5)
        with self.assertRaises(evaluation.DevelopmentIntegrityError):
            evaluation.score_question(question(kind="NEGATIVE"), response(abstain=True))

    def test_aggregate_denominators_macro_micro_and_multi_required(self):
        rows = [evaluation.score_question(question(), response((A,))),
                evaluation.score_question(question(gold=(A, B, C), required=(A, B, C)), response((X, A))),
                evaluation.score_question(question(gold=(), required=(), kind="NEGATIVE"), response(abstain=True))]
        metrics = evaluation.aggregate_metrics(rows)
        self.assertEqual((metrics["answerable_count"], metrics["negative_count"], metrics["multi_required_question_count"]), (2, 1, 1))
        self.assertEqual(metrics["hit_at_1"]["rate"], 0.5)
        self.assertEqual(metrics["hit_at_3"]["rate"], 1)
        self.assertEqual(metrics["mrr_at_10"], 0.75)
        self.assertAlmostEqual(metrics["required_coverage_at_k"]["3"]["macro_average"], 2 / 3)
        self.assertEqual(metrics["required_coverage_at_k"]["3"]["micro"]["rate"], 0.5)
        self.assertEqual(metrics["full_required_set_success_at_k"]["3"], {"count": 0, "total": 1, "rate": 0.0})

    def test_mrr_does_not_reach_beyond_ten_unique_results(self):
        irrelevant = tuple(("TEST", "1.0-demo", str(i)) for i in range(10))
        row = evaluation.score_question(question(), response(irrelevant + (A,)))
        self.assertIsNone(row["first_relevant_rank"])
        self.assertEqual(row["reciprocal_rank_at_10"], 0)

    def test_evaluation_passes_only_queries_and_fixed_depth_to_retriever(self):
        data = evaluation.load_development()
        before = copy.deepcopy(data.questions)
        calls = []
        class QueryOnlyRetriever:
            def search(self, query, *, top_k):
                calls.append((query, top_k))
                return response(abstain=True)
        result = evaluation.evaluate(data, QueryOnlyRetriever())
        self.assertEqual(calls, [(q["question"], 10) for q in data.questions])
        self.assertEqual(data.questions, before)
        self.assertEqual(len(result["questions"]), 15)
        self.assertEqual(evaluation.json_bytes(result), evaluation.json_bytes(evaluation.evaluate(data, QueryOnlyRetriever())))
        self.assertEqual(len(result["failures"]), 14)

    def test_failure_observations_preserve_missing_required_and_negative_error(self):
        row = evaluation.score_question(question(gold=(A, B), required=(B,)), response((A,)))
        self.assertTrue(any("coverage@10" in note for note in evaluation.failure_observations(row)))
        negative = evaluation.score_question(question(gold=(), required=(), kind="NEGATIVE"), response((X,)))
        self.assertTrue(any("Unsupported negative" in note for note in evaluation.failure_observations(negative)))


if __name__ == "__main__":
    unittest.main()
