"""B2 synthetic integrity tests: never load a model or an actual AQ question."""
import copy
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, replace
from fractions import Fraction
import io
import json
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gateway.domain.evaluation.answerability import bge_evidence as evidence
from gateway.domain.evaluation.answerability import generate_development_evidence as runner
from gateway.domain.evaluation.answerability.answerability_contracts import (
    ALLOW, ABSTAIN, SUPPORTED, INSUFFICIENT, ContractError, EvaluationCase, GateInput,
)
from gateway.domain.evaluation.answerability.answerability_scoring import deterministic_json_bytes, metric
from gateway.domain.evaluation.answerability.development_loader import IDS, strict_json
from gateway.domain.retrieval.embedding_retriever import EmbeddingResult, EmbeddingSearchResponse
from gateway.domain.retrieval.section_store import section_content_hash
from gateway.domain.tests._answerability_fixtures import BUNDLE, temporary_directory


def synthetic_fixture():
    sections = []
    for i in range(25):
        canonical = ("SOP-01", "1.0-demo", f"synthetic-{i:02d}")
        body, title = f"Synthetic evidence body {i}.\n", f"Synthetic section {i}"
        sections.append(SimpleNamespace(identity=canonical, title="Synthetic document", section_title=title,
                                        text=body, content_hash=section_content_hash(*canonical, title, body),
                                        source_path="synthetic-only"))
    store = SimpleNamespace(sections=tuple(sections))
    mapping = evidence.section_map(store)
    returned = tuple(EmbeddingResult(s.identity, i+1, 0.8 if i == 0 else 0.2, s.text, s.content_hash, s.source_path)
                     for i, s in enumerate(sections[:10]))
    response = EmbeddingSearchResponse("RETRIEVED", returned, 0.8, None)
    queries = tuple(evidence.Query(qid, f"  Synthetic question {i+1}?\n", "0"*64) for i, qid in enumerate(IDS))
    rows = [evidence.capture_response(q, response, mapping) for q in queries]
    cases = []
    for i, q in enumerate(queries):
        refs = (sections[0].identity, sections[5].identity) if i < 6 else (sections[0].identity,)
        cases.append(EvaluationCase(q.question_id, q.text, ALLOW if i < 20 else ABSTAIN,
                                    SUPPORTED if i < 20 else INSUFFICIENT, refs if i < 20 else (), refs if i < 20 else ()))
    return tuple(cases), queries, store, copy.deepcopy(evidence.make_package(rows, BUNDLE)), response


class BGEStoredEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.queries, self.store, self.package, self.response = synthetic_fixture()

    def validate(self):
        return evidence.validate_package(self.package, self.queries, self.store, BUNDLE)

    def test_valid_configuration_and_package(self):
        self.assertEqual(len(self.validate()), 40)

    def test_wrong_model_rejected(self):
        self.package["configuration"]["model_id"] = "other"
        with self.assertRaises(ContractError): self.validate()

    def test_wrong_revision_rejected(self):
        self.package["model_revision"] = "main"
        with self.assertRaises(ContractError): self.validate()

    def test_wrong_device_and_dimension_rejected(self):
        self.package["configuration"]["device"] = "cuda"
        with self.assertRaises(ContractError): self.validate()
        self.package["configuration"]["device"] = "cpu"
        self.package["embedding_dimension"] = 768
        with self.assertRaises(ContractError): self.validate()

    def test_wrong_threshold_rejected(self):
        self.package["configuration"]["abstention"]["minimum_top_score"] = 0.31
        with self.assertRaises(ContractError): self.validate()

    def test_wrong_depth_configuration_rejected(self):
        self.package["configuration"]["top_k"] = 5
        with self.assertRaises(ContractError): self.validate()

    def test_query_transformations_rejected(self):
        for key in ("query_transformation", "query_instruction", "document_instruction"):
            original = self.package["configuration"][key]
            self.package["configuration"][key] = "added text"
            with self.assertRaises(ContractError): self.validate()
            self.package["configuration"][key] = original

    def test_unknown_configuration_field_rejected(self):
        self.package["configuration"]["fallback"] = "other"
        with self.assertRaises(ContractError): self.validate()

    def test_duplicate_question_rejected(self):
        self.package["questions"][1] = copy.deepcopy(self.package["questions"][0])
        with self.assertRaises(ContractError): self.validate()

    def test_missing_question_rejected(self):
        self.package["questions"].pop()
        with self.assertRaises(ContractError): self.validate()

    def test_unknown_or_reordered_question_rejected(self):
        self.package["questions"][0]["question_id"] = "UNKNOWN"
        with self.assertRaises(ContractError): self.validate()
        self.package["questions"][0]["question_id"] = IDS[0]
        self.package["questions"].reverse()
        with self.assertRaises(ContractError): self.validate()

    def test_duplicate_section_rejected(self):
        result = copy.deepcopy(self.package["questions"][0]["results"][0])
        result.update(rank=2, cosine_score=0.2)
        self.package["questions"][0]["results"][1] = result
        with self.assertRaises(ContractError): self.validate()

    def test_invalid_rank_rejected(self):
        for rank in (0, 3, True):
            self.package["questions"][0]["results"][1]["rank"] = rank
            with self.assertRaises(ContractError): self.validate()

    def test_excessive_depth_rejected(self):
        row = self.package["questions"][0]
        row["results"].append(copy.deepcopy(row["results"][-1]))
        row["result_count"] = 11
        with self.assertRaises(ContractError): self.validate()

    def test_nonfinite_and_out_of_domain_scores_rejected(self):
        for score in (math.nan, math.inf, -math.inf, -1.001, 1.001, True, "0.2"):
            self.package["questions"][0]["results"][1]["cosine_score"] = score
            with self.subTest(score=score), self.assertRaises(ContractError): self.validate()

    def test_low_ranked_scores_retained_without_filter(self):
        value = self.validate()[0]
        self.assertEqual(len(value.evidence), 10)
        self.assertEqual([r.cosine_score for r in value.evidence], [0.8]+[0.2]*9)

    def test_negative_tail_retained(self):
        self.package["questions"][0]["results"][-1]["cosine_score"] = -0.2
        self.assertEqual(self.validate()[0].evidence[-1].cosine_score, -0.2)

    def test_top_below_threshold_rejected(self):
        for score in (0.29, math.nextafter(0.3, -math.inf)):
            self.package["questions"][0]["top_score"] = score
            self.package["questions"][0]["results"][0]["cosine_score"] = score
            with self.assertRaises(ContractError): self.validate()

    def test_top_equal_threshold_accepted(self):
        row = self.package["questions"][0]
        row["top_score"] = row["results"][0]["cosine_score"] = 0.30
        self.assertEqual(self.validate()[0].evidence[0].cosine_score, 0.30)

    def test_explicit_top_score_must_match_rank_1_exactly(self):
        self.package["questions"][0]["top_score"] = math.nextafter(0.8, math.inf)
        with self.assertRaisesRegex(ContractError, "top_score differs"): self.validate()

    def test_empty_abstention_and_inconsistent_metadata(self):
        row = self.package["questions"][0]
        row.update(results=[], result_count=0, retrieval_status="ABSTAIN", top_score=0.29,
                   retriever_abstention_reason="TOP_SCORE_BELOW_THRESHOLD")
        self.assertEqual(self.validate()[0].evidence, ())
        for updates in ({"top_score": 0.3}, {"retrieval_status": "RETRIEVED"}, {"retriever_abstention_reason": None}):
            old = row.copy()
            row.update(updates)
            with self.assertRaises(ContractError): self.validate()
            row.update(old)

    def test_unknown_section_rejected(self):
        self.package["questions"][0]["results"][0]["section_id"] = "unknown"
        with self.assertRaises(ContractError): self.validate()

    def test_section_hash_mismatch_rejected(self):
        self.package["questions"][0]["results"][0]["section_content_sha256"] = "0"*64
        with self.assertRaisesRegex(ContractError, "content hash"): self.validate()

    def test_section_text_title_changes_rejected(self):
        for field in ("document_title", "section_title", "section_body"):
            old = self.package["questions"][0]["results"][0][field]
            self.package["questions"][0]["results"][0][field] = "changed"
            with self.assertRaises(ContractError): self.validate()
            self.package["questions"][0]["results"][0][field] = old

    def test_order_and_canonical_ties_rejected(self):
        results = self.package["questions"][0]["results"]
        results[1], results[2] = results[2], results[1]
        results[1]["rank"], results[2]["rank"] = 2, 3
        with self.assertRaises(ContractError): self.validate()
        results[1], results[2] = results[2], results[1]
        results[1]["rank"], results[2]["rank"] = 2, 3
        results[2]["cosine_score"] = 0.21
        with self.assertRaises(ContractError): self.validate()

    def test_gate_input_boundary_preserves_only_allowlisted_fields(self):
        value = self.validate()[0]
        self.assertIs(type(value), GateInput)
        self.assertEqual(value.question, self.queries[0].text)
        self.assertEqual(set(asdict(value)), {"question", "evidence", "active_bundle"})
        forbidden = {"question_id", "split", "expected_gate", "reason_code", "gold_support_sections",
                     "required_support_sections", "difficulty_band", "support_shape", "hard_negative",
                     "authoring_rationale", "review_status", "owner_notes"}
        def walk(node):
            if isinstance(node, dict):
                self.assertFalse(forbidden & set(node))
                for v in node.values(): walk(v)
            elif isinstance(node, (tuple, list)):
                for v in node: walk(v)
        walk(asdict(value))
        self.package["questions"][0]["expected_gate"] = ALLOW
        with self.assertRaisesRegex(ContractError, "question fields"): self.validate()

    def test_question_text_and_custody_binding_rejected(self):
        row = self.package["questions"][0]
        for field in ("question", "question_text_sha256", "question_file_sha256"):
            old = row[field]
            row[field] = "changed"
            with self.assertRaises(ContractError): self.validate()
            row[field] = old

    def test_deterministic_serialization_preserves_float_bits(self):
        data = deterministic_json_bytes(self.package)
        parsed = strict_json(data)
        self.assertEqual(data, deterministic_json_bytes(parsed))
        self.assertTrue(data.endswith(b"\n"))
        self.assertNotIn(b"\r", data)
        for before, after in zip(self.package["questions"][0]["results"], parsed["questions"][0]["results"]):
            self.assertEqual(before["cosine_score"].hex(), after["cosine_score"].hex())

    def test_retrieval_only_metrics_exact_denominators(self):
        result = evidence.retrieval_metrics(self.cases, self.package)
        metrics = result["allow_retrieval"]
        self.assertEqual(metrics["hit_at_1"], metric(20, 20))
        self.assertEqual(metrics["hit_at_3"], metric(20, 20))
        self.assertEqual(metrics["mrr_at_10"], metric(20, 20))
        for k in (3, 5):
            self.assertEqual(metrics[f"required_macro_coverage_at_{k}"], metric(17, 20))
            self.assertEqual(metrics[f"required_micro_coverage_at_{k}"], metric(20, 26))
            self.assertEqual(metrics[f"multi_required_full_at_{k}"], metric(0, 6))
        self.assertEqual(metrics["multi_required_full_at_10"], metric(6, 6))
        forbidden = {"allow_recall", "correct_abstention_rate", "false_support_rate", "false_abstention_rate", "eligible"}
        self.assertFalse(forbidden & set(metrics))
        self.assertEqual(result["gold_abstain_response_diagnostics"]["returned_evidence_response_count"], 20)

    def test_mrr_and_empty_allow_response_keep_all_denominators(self):
        reference = self.store.sections[1].identity
        cases = (replace(self.cases[0], gold_support_sections=(reference,), required_support_sections=(reference,)),)+self.cases[1:]
        metrics = evidence.retrieval_metrics(cases, self.package)["allow_retrieval"]
        self.assertEqual(metrics["mrr_at_10"], metric(Fraction(39, 2), 20))
        self.package["questions"][0].update(results=[], result_count=0, top_score=0.2, retrieval_status="ABSTAIN",
                                             retriever_abstention_reason="TOP_SCORE_BELOW_THRESHOLD")
        metrics = evidence.retrieval_metrics(self.cases, self.package)["allow_retrieval"]
        self.assertEqual(metrics["mrr_at_10"], metric(19, 20))
        self.assertEqual(metrics["required_micro_coverage_at_10"], metric(24, 26))
        self.assertEqual(metrics["multi_required_full_at_10"], metric(5, 6))


class EvidenceRunPlumbingTests(unittest.TestCase):
    def test_output_directory_and_files_cannot_be_overwritten(self):
        with temporary_directory() as root:
            directory = root/"evidence"
            runner.create_output_directory(directory)
            runner.write_once(directory/"sentinel", b"original\n")
            with self.assertRaises(ContractError): runner.create_output_directory(directory)
            with self.assertRaises(FileExistsError): runner.write_once(directory/"sentinel", b"changed")
            self.assertEqual((directory/"sentinel").read_bytes(), b"original\n")

    def test_once_per_question_and_only_original_text_top_k(self):
        _, queries, store, _, response = synthetic_fixture()
        received = []
        class Stub:
            def search(self, text, *, top_k):
                received.append((text, top_k))
                return response
        with temporary_directory() as root:
            journal = runner.AttemptJournal(root/"journal.jsonl")
            try:
                rows = runner.run_queries(queries, Stub(), store, BUNDLE, journal)
                self.assertEqual(journal.attempts, dict.fromkeys(IDS, 1))
                self.assertEqual(len(rows), 40)
            finally: journal.close()
        self.assertEqual(received, [(q.text, 10) for q in queries])

    def test_failed_attempt_preserved_without_retry(self):
        cases, queries, store, _, response = synthetic_fixture()
        class Stub:
            embedding_dimension = 384
            section_count = 25
            calls = 0
            def search(self, text, *, top_k):
                self.calls += 1
                if self.calls == 2: raise OSError("synthetic I/O failure")
                return response
        stub = Stub()
        metadata = {"requested_revision": evidence.REVISION, "resolved_model_revision": evidence.REVISION,
                    "device": "cpu", "embedding_dimension": 384, "model_file_sha256": {},
                    "model_download_occurred": False, "weights_downloaded": False, "downloaded_files": []}
        provenance = {"model_local_provenance": {"model_file_sha256": {}}}
        with temporary_directory() as root:
            output = root/"synthetic-run"
            with (patch.object(runner, "OUTPUT", output),
                  patch.object(runner, "preflight", return_value=(cases, queries, store, BUNDLE, provenance)),
                  patch.object(runner, "SentenceTransformerBackend", return_value=SimpleNamespace(metadata=metadata)),
                  patch.object(runner, "EmbeddingRetriever", return_value=stub),
                  patch.object(runner.sys, "addaudithook"),
                  patch.dict(runner.os.environ), redirect_stderr(io.StringIO())):
                with self.assertRaisesRegex(OSError, "synthetic I/O failure"):
                    runner.main(["--run"])
            failure = json.loads((output/"FAILED_ATTEMPT.json").read_text(encoding="utf-8"))
            journal = [json.loads(line) for line in (output/"ATTEMPT_JOURNAL.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(failure["attempt_count"], 2)
            self.assertEqual(failure["returned_responses"], 1)
            self.assertEqual(stub.calls, 2)
            self.assertEqual(sum(row["event"] == "retriever_returned" for row in journal), 1)
            self.assertFalse((output/"DEVELOPMENT_BGE_EVIDENCE.json").exists())

    def test_full_synthetic_run_writes_and_verifies_all_artifacts(self):
        cases, queries, store, _, response = synthetic_fixture()
        class Stub:
            embedding_dimension = 384
            section_count = 25
            def search(self, text, *, top_k): return response
        metadata = {"requested_revision": evidence.REVISION, "resolved_model_revision": evidence.REVISION,
                    "device": "cpu", "embedding_dimension": 384, "model_file_sha256": {},
                    "model_download_occurred": False, "weights_downloaded": False, "downloaded_files": []}
        provenance = {"model_local_provenance": {"model_file_sha256": {}}, "protected_source_sha256": {},
                      "b2_source_sha256": {}, "gate_invocations": 0}
        with temporary_directory() as root:
            output = root/"synthetic-run"
            with (patch.object(runner, "OUTPUT", output),
                  patch.object(runner, "preflight", return_value=(cases, queries, store, BUNDLE, provenance)),
                  patch.object(runner, "SentenceTransformerBackend", return_value=SimpleNamespace(metadata=metadata)),
                  patch.object(runner, "EmbeddingRetriever", return_value=Stub()),
                  patch.object(runner.sys, "addaudithook"),
                  patch.dict(runner.os.environ), redirect_stdout(io.StringIO())):
                self.assertEqual(runner.main(["--run"]), 0)
            self.assertEqual({p.name for p in output.iterdir()}, set(runner.OUTPUT_NAMES))
            manifest = strict_json((output/"RUN_MANIFEST.json").read_bytes())
            self.assertEqual(manifest["attempt_count"], 40)
            self.assertEqual(manifest["question_attempts"], dict.fromkeys(IDS, 1))
            self.assertEqual(manifest["gate_invocations"], 0)
            for name, expected in manifest["output_sha256"].items():
                self.assertEqual(runner.file_hash(output/name), expected)

    def test_socket_guard_allows_capability_probe_and_records_block(self):
        events = []
        journal = SimpleNamespace(record=lambda event, **record: events.append((event, record)))
        guard = runner.OfflineSocketAudit(journal)
        guard("socket.__new__", (None, 23, 1, 0))
        guard("socket.gethostname", ())
        guard("socket.bind", (None, ("::1", 0, 0, 0)))
        for event, args in (("socket.getaddrinfo", ("remote.invalid", 443)),
                            ("socket.connect", (None, ("192.0.2.1", 443))),
                            ("socket.connect_ex", (None, ("192.0.2.1", 443))),
                            ("socket.bind", (None, ("0.0.0.0", 0)))):
            with self.assertRaises(ContractError): guard(event, args)
            self.assertFalse(events[-1][1]["allowed"])
            self.assertEqual(events[-1][1]["operation"], event)


if __name__ == "__main__":
    unittest.main()
