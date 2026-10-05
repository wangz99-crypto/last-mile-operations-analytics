"""Round-1 synthetic candidates and orchestration; never evaluate a real AQ input."""
from contextlib import redirect_stderr
from dataclasses import asdict, fields, replace
from fractions import Fraction
import importlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from gateway.domain.evaluation.answerability import evaluate_baseline_gates as runner
from gateway.domain.evaluation.answerability.gates import baseline_gates as gates
from gateway.domain.evaluation.answerability.answerability_contracts import (
    ALLOW, ABSTAIN, SUPPORTED, INSUFFICIENT, UNRESOLVED, CandidateObservation, ContractError,
    GateInput, GateOutput, make_gate_input,
)
from gateway.domain.evaluation.answerability.answerability_scoring import deterministic_json_bytes, score_results
from gateway.domain.tests._answerability_fixtures import BUNDLE, evidence, fixture, temporary_directory


def value(question="alpha beta gamma delta epsilon", bodies=("alpha beta gamma",)):
    ranked = tuple(replace(item, section_title="neutral", body=body) for item, body in zip(evidence(len(bodies)), bodies))
    return GateInput(question, ranked, BUNDLE)


def synthetic_round():
    cases, retrievals, observations = fixture()
    cases = tuple(replace(c, question_id=qid, reason_code=UNRESOLVED if i >= 36 else c.reason_code)
                  for i, (c, qid) in enumerate(zip(cases, runner.IDS)))
    retrievals = tuple(replace(r, question_id=qid) for r, qid in zip(retrievals, runner.IDS))
    inputs = tuple(make_gate_input(c.question, r.result) for c, r in zip(cases, retrievals))
    metadata = {c.question_id: {"difficulty_band": ("DIRECT", "PARAPHRASE", "INDIRECT_OPERATIONAL")[i % 3],
                               "support_shape": "MULTI_SECTION" if i < 6 else "SINGLE_SECTION" if i < 20 else "NOT_APPLICABLE",
                               "hard_negative": 20 <= i < 36} for i, c in enumerate(cases)}
    return cases, retrievals, inputs, metadata


class CandidateTests(unittest.TestCase):
    def test_always_allow_and_reason(self):
        for v in (value(), value(bodies=())):
            self.assertEqual(gates.BaselineGate(gates.IDS[0]).decide(v), GateOutput(ALLOW, SUPPORTED))

    def test_always_abstain_and_reason(self):
        for v in (value(), value(bodies=())):
            self.assertEqual(gates.BaselineGate(gates.IDS[1]).decide(v), GateOutput(ABSTAIN, INSUFFICIENT))

    def test_response_baseline_only_uses_presence(self):
        gate = gates.BaselineGate(gates.IDS[2])
        self.assertEqual(gate.decide(value("unrelated query", ("other text",))).decision, ALLOW)
        self.assertEqual(gate.decide(value(bodies=())).decision, ABSTAIN)

    def test_lowercase_regex_punctuation_and_numbers(self):
        self.assertEqual(gates.tokens("ALPHA_beta, C++ 12.34! don't"), frozenset({"alpha", "beta", "c", "12", "34", "don", "t"}))

    def test_exact_stopwords_and_no_domain_additions(self):
        expected = "a an the and or but if then is are was were be been being to of in on for with at by from as it this that these those i me my we our you your he she they them their do does did can could would should may might will what which who whom whose how when where why"
        self.assertEqual(gates.STOPWORDS, frozenset(expected.split()))
        self.assertEqual(gates.tokens(expected), frozenset())
        self.assertEqual(gates.tokens("neutral domain vocabulary"), frozenset({"neutral", "domain", "vocabulary"}))

    def test_distinct_tokens_not_frequency_weighted(self):
        counts = gates.lexical_counts(value("alpha alpha alpha beta", ("alpha alpha",)), 1)
        self.assertEqual((counts.informative_question_token_count, counts.matched_token_count, counts.coverage), (2, 1, Fraction(1, 2)))

    def test_empty_informative_question_abstains(self):
        for query in ("the and CAN", "... !!!"):
            for candidate in gates.IDS[3:]:
                self.assertEqual(gates.BaselineGate(candidate).decide(value(query)).decision, ABSTAIN)

    def test_empty_evidence_abstains(self):
        for candidate in gates.IDS[2:]:
            self.assertEqual(gates.BaselineGate(candidate).decide(value(bodies=())).decision, ABSTAIN)

    def test_title_and_body_included(self):
        v = value("alpha beta gamma", ("beta gamma",))
        v = replace(v, evidence=(replace(v.evidence[0], section_title="alpha"),))
        self.assertEqual(gates.lexical_counts(v, 1).coverage, 1)

    def test_document_title_ids_version_and_bundle_excluded(self):
        v = value("synthetic document sop 01 demo", ("neutral",))
        self.assertEqual(gates.lexical_counts(v, 1).matched_token_count, 0)

    def test_top1_only(self):
        v = value(bodies=("alpha", "beta gamma delta epsilon"))
        self.assertEqual(gates.lexical_counts(v, 1).coverage, Fraction(1, 5))
        self.assertEqual(gates.BaselineGate(gates.IDS[3]).decide(v).decision, ABSTAIN)

    def test_top3_union_and_exclude_rank4(self):
        v = value(bodies=("alpha", "beta", "gamma", "delta epsilon"))
        counts = gates.lexical_counts(v, 3)
        self.assertEqual((counts.coverage, counts.evidence_depth_used), (Fraction(3, 5), 3))
        self.assertEqual(gates.BaselineGate(gates.IDS[4]).decide(v).decision, ALLOW)

    def test_top3_uses_only_present_sections(self):
        self.assertEqual(gates.lexical_counts(value(bodies=("alpha", "beta")), 3).evidence_depth_used, 2)

    def test_coverage_exact_599_below_threshold(self):
        self.assertFalse(gates.CoverageCounts(1000, 599, 1).passes)
        self.assertFalse(gates.CoverageCounts(5, 2, 1).passes)

    def test_coverage_exact_60_and_above_allow(self):
        self.assertTrue(gates.CoverageCounts(5, 3, 1).passes)
        self.assertTrue(gates.CoverageCounts(5, 4, 1).passes)
        for candidate in gates.IDS[3:]:
            self.assertEqual(gates.BaselineGate(candidate).decide(value()).decision, ALLOW)
            self.assertEqual(gates.BaselineGate(candidate).decide(value(bodies=("alpha beta",))).decision, ABSTAIN)

    def test_scores_do_not_weight_lexical_coverage(self):
        v = value(bodies=("alpha", "beta", "gamma"))
        changed = replace(v, evidence=tuple(replace(e, cosine_score=s) for e, s in zip(v.evidence, (0.30, -0.2, -0.9))))
        self.assertEqual(gates.lexical_counts(v, 3), gates.lexical_counts(changed, 3))

    def test_candidate_objects_have_no_case_reference_or_closure(self):
        candidate = gates.BaselineGate(gates.IDS[3])
        self.assertEqual([f.name for f in fields(candidate)], ["candidate_id"])
        self.assertFalse(hasattr(candidate, "__dict__"))
        self.assertIsNone(candidate.decide.__func__.__closure__)
        self.assertIsNone(gates.lexical_counts.__closure__)
        self.assertNotIn("load_development", vars(gates))
        self.assertNotIn("EvaluationCase", vars(gates))

    def test_gate_input_has_no_ids_gold_or_metadata(self):
        v = value()
        self.assertEqual(set(asdict(v)), {"question", "evidence", "active_bundle"})
        forbidden = {"question_id", "split", "expected_gate", "reason_code", "gold_support_sections", "required_support_sections",
                     "difficulty_band", "support_shape", "hard_negative", "authoring_rationale", "review_status", "owner"}
        def walk(node):
            if isinstance(node, dict):
                self.assertFalse(forbidden & set(node))
                for child in node.values(): walk(child)
            elif isinstance(node, (list, tuple)):
                for child in node: walk(child)
        walk(asdict(v))
        with self.assertRaises(ContractError): gates.BaselineGate(gates.IDS[0]).decide(asdict(v))

    def test_deterministic_outputs(self):
        for candidate_id in gates.IDS:
            gate = gates.BaselineGate(candidate_id)
            self.assertEqual(gate.decide(value()), gate.decide(value()))

    def test_no_extra_candidate(self):
        with self.assertRaises(ContractError): gates.BaselineGate("NEW_CANDIDATE")


class LoaderAndGuardTests(unittest.TestCase):
    def test_frozen_hashes_and_reconstruction_accepted_without_inference(self):
        with runner.NoRetrievalGuard(), patch.object(gates.BaselineGate, "decide", side_effect=AssertionError("no actual candidate run")):
            cases, values, retrievals, protected = runner.load_frozen_evidence()
        self.assertEqual(len(cases), len(values))
        self.assertEqual(len(values), 40)
        self.assertEqual(sum(c.expected_gate == ALLOW for c in cases), 20)
        self.assertTrue(protected)
        self.assertEqual(tuple(c.question_id for c in cases), runner.IDS)

    def test_changed_evidence_or_provenance_rejected(self):
        original = Path.read_bytes
        for name in runner.B2_HASHES:
            def read(path):
                data = original(path)
                return data + b" " if path == runner.B2/name else data
            with self.subTest(name=name), patch.object(Path, "read_bytes", read):
                with self.assertRaisesRegex(ContractError, "frozen B2 artifact changed"):
                    runner.verify_b2()

    def test_arbitrary_evidence_path_rejected(self):
        with self.assertRaises(TypeError): runner.load_frozen_evidence(Path("other"))
        with self.assertRaises(TypeError): runner.load_frozen_evidence(path=Path("other"))
        for flag in ("--evidence", "--manifest", "--split", "--run-more"):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): runner.main(["--run", flag, "other"])

    def test_model_imports_and_retrieval_imports_blocked(self):
        for module in ("sentence_transformers", "gateway.domain.retrieval.embedding_retriever", "openai"):
            with runner.NoRetrievalGuard(), self.assertRaises(runner.ExecutionProhibited):
                importlib.import_module(module)

    def test_already_imported_retriever_call_is_blocked(self):
        def search():
            raise AssertionError("body must never run")
        search.__code__ = search.__code__.replace(co_filename="/gateway/domain/retrieval/section_store.py")
        with runner.NoRetrievalGuard(), self.assertRaises(runner.ExecutionProhibited): search()

    def test_socket_and_private_access_blocked(self):
        guard = runner.NoRetrievalGuard()
        with guard:
            with self.assertRaises(runner.ExecutionProhibited): guard.audit("socket.connect", (None, ("192.0.2.1", 443)))
            with self.assertRaises(runner.ExecutionProhibited): guard.audit("open", ("synthetic/held_out/forbidden.json", "r", 0))
        self.assertEqual(len(guard.violations), 2)

    def test_existing_output_directory_refused(self):
        with temporary_directory() as directory, patch.object(runner, "OUTPUT", directory), patch.object(runner, "git", side_effect=[runner.BASE_COMMIT, runner.BASE_COMMIT, runner.HARNESS_COMMIT]):
            with self.assertRaisesRegex(ContractError, "refuse existing"): runner.preconditions()


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.retrievals, self.inputs, self.metadata = synthetic_round()
        self.registry = runner.make_registry("0" * 64)

    def test_registry_exact_order_controls_thresholds_hashes(self):
        self.assertEqual(self.registry["candidate_order"], list(gates.IDS))
        self.assertEqual(self.registry["registry_status"], "PRE_REGISTERED_BEFORE_DEVELOPMENT_GATE_RESULTS")
        for i, spec in enumerate(self.registry["candidates"]):
            self.assertEqual(spec["control_only"], i < 2)
            self.assertEqual(spec["selection_eligible"], i >= 2)
            config = {k: v for k, v in spec.items() if k not in ("source_file_sha256", "configuration_sha256")}
            self.assertEqual(spec["configuration_sha256"], runner.sha256(deterministic_json_bytes(config)))
            if i >= 3: self.assertEqual(spec["coverage_threshold"], {"numerator": 3, "denominator": 5, "decimal": "0.60"})

    def test_candidate_receives_only_inputs_once(self):
        received = []
        class Stub:
            def decide(self, item):
                received.append(item)
                return GateOutput(ALLOW, SUPPORTED)
        outputs = runner.infer_inputs(Stub(), self.inputs)
        self.assertEqual(received, list(self.inputs))
        self.assertEqual(len(outputs), 40)

    def test_missing_and_duplicate_output_rejected(self):
        outputs = tuple((GateOutput(ALLOW, SUPPORTED), None) for _ in range(40))
        for ids, raw in ((runner.IDS, outputs[:-1]), (runner.IDS[:-1] + (runner.IDS[0],), outputs)):
            with self.assertRaises(ContractError): runner.associate_outputs(ids, raw)

    def test_candidate_errors_and_malformed_outputs_no_retry(self):
        class Stub:
            calls = 0
            def decide(self, item):
                self.calls += 1
                if self.calls == 1: raise RuntimeError("synthetic failure")
                return {"decision": "invalid"}
        stub = Stub()
        raw = runner.infer_inputs(stub, self.inputs)
        self.assertEqual(stub.calls, 40)
        score = score_results(self.cases, self.retrievals, runner.associate_outputs(runner.IDS, raw))
        self.assertEqual(score["errors"]["count"], 40)
        self.assertEqual(score["primary"]["allow_recall"]["denominator"], 20)

    def _score(self, allow_correct, abstain_correct):
        observations = []
        for i, case in enumerate(self.cases):
            decision = (ALLOW if i < allow_correct else ABSTAIN) if i < 20 else (ABSTAIN if i - 20 < abstain_correct else ALLOW)
            observations.append(CandidateObservation(case.question_id, GateOutput(decision, SUPPORTED if decision == ALLOW else INSUFFICIENT)))
        return score_results(self.cases, self.retrievals, tuple(observations))

    def test_eligibility_exact_18_18_and_17_fails(self):
        spec = self.registry["candidates"][2]
        self.assertTrue(runner.selection_eligible(spec, self._score(18, 18)))
        self.assertFalse(runner.selection_eligible(spec, self._score(17, 20)))
        self.assertFalse(runner.selection_eligible(spec, self._score(20, 17)))

    def test_controls_never_selection_eligible(self):
        perfect = self._score(20, 20)
        self.assertTrue(perfect["eligible"])
        for spec in self.registry["candidates"][:2]: self.assertFalse(runner.selection_eligible(spec, perfect))

    def test_gated_metrics_keep_all_gold_allow_denominators(self):
        score = self._score(0, 20)
        gated = score["retrieval"]["gated"]
        self.assertEqual(gated["hit_at_1"]["numerator"], 0)
        self.assertEqual(gated["hit_at_1"]["denominator"], 20)
        self.assertEqual(gated["required_micro_coverage_at_10"]["denominator"], 26)
        self.assertEqual(gated["multi_required_full_at_10"]["denominator"], 6)

    def test_secondary_metrics_control_sanity(self):
        result = runner.secondary_metrics(self._score(20, 0))
        self.assertEqual(result["overall_accuracy"]["rate"], "0.500000000000")
        self.assertEqual(result["balanced_accuracy"]["rate"], "0.500000000000")
        self.assertEqual(result["macro_f1"]["rate"], "0.333333333333")

    def test_breakdowns_and_wrong_reason_only(self):
        score = self._score(20, 20)
        breakdown = runner.breakdowns(score, self.metadata)
        self.assertEqual(breakdown["abstain_reason"][UNRESOLVED]["question_count"], 4)
        self.assertEqual(breakdown["abstain_reason"][UNRESOLVED]["binary_correct_count"], 4)
        self.assertEqual(runner.failure_lists(score)["wrong_reason_only"], list(runner.IDS[-4:]))
        self.assertEqual(breakdown["allow_support_shape"]["MULTI_SECTION"]["question_count"], 6)

    def test_results_deterministic_and_all_inference_before_scoring(self):
        events = []
        class Journal:
            def record(self, event, **payload): events.append(event)
        with patch.object(runner, "score_results", side_effect=AssertionError("no scoring during inference")):
            raw = runner.infer_all(self.inputs, self.registry, Journal())
        result = runner.build_results(self.cases, self.retrievals, self.inputs, self.registry, raw, self.metadata)
        repeated = runner.build_results(self.cases, self.retrievals, self.inputs, self.registry, raw, self.metadata)
        data = deterministic_json_bytes(result)
        self.assertEqual(data, deterministic_json_bytes(repeated))
        self.assertEqual(data, deterministic_json_bytes(json.loads(data)))
        self.assertTrue(data.endswith(b"\n"))
        self.assertNotIn(b"\r", data)
        self.assertEqual(len(result["candidates"]), 5)
        self.assertEqual(events.count("CANDIDATE_COMPLETED"), 5)
        self.assertEqual(len(result["candidates"][3]["lexical_diagnostics"]), 40)

    def test_full_synthetic_pipeline_registration_journal_hashes_no_retrieval(self):
        with temporary_directory() as directory:
            output = directory / "synthetic-round"
            with (patch.object(runner, "OUTPUT", output), patch.object(runner, "preconditions", return_value=""),
                  patch.object(runner, "load_frozen_evidence", return_value=(self.cases, self.inputs, self.retrievals, {})),
                  patch.object(runner, "run_tests", return_value={"tests_run": 1, "failures": 0, "errors": 0}),
                  patch.object(runner, "verify_b2"), patch.object(runner, "verify_protected", return_value={}),
                  patch.object(runner, "diagnostic_metadata", return_value=self.metadata)):
                result = runner.run_round()
            self.assertEqual({p.name for p in output.iterdir()}, set(runner.OUTPUT_NAMES))
            journal = [json.loads(line) for line in (output / "EVALUATION_JOURNAL.jsonl").read_bytes().splitlines()]
            events = [row["event"] for row in journal]
            self.assertLess(events.index("BASELINES_REGISTERED"), events.index("DEVELOPMENT_EVALUATION_STARTED"))
            self.assertLess(events.index("DEVELOPMENT_EVALUATION_STARTED"), events.index("CANDIDATE_COMPLETED"))
            manifest = json.loads((output / "RUN_MANIFEST.json").read_bytes())
            for name, wanted in manifest["output_sha256"].items(): self.assertEqual(runner.file_hash(output/name), wanted)
            self.assertEqual(manifest["gate_calls"], 200)
            self.assertEqual(manifest["retrieval_calls"], 0)
            self.assertEqual(manifest["model_initializations"], 0)
            self.assertEqual(manifest["candidate_question_attempts"], {candidate: dict.fromkeys(runner.IDS, 1) for candidate in gates.IDS})
            registered = journal[events.index("BASELINES_REGISTERED")]
            self.assertEqual(registered["registry_sha256"], runner.file_hash(output / "BASELINE_REGISTRY.json"))
            with self.assertRaises(FileExistsError): runner.write_once(output / "BASELINE_RESULTS.json", b"overwrite")

    def test_failed_partial_synthetic_run_is_preserved_and_not_retried(self):
        with temporary_directory() as directory:
            output = directory / "failed-synthetic-round"
            with (patch.object(runner, "OUTPUT", output), patch.object(runner, "preconditions", return_value=""),
                  patch.object(runner, "load_frozen_evidence", return_value=(self.cases, self.inputs, self.retrievals, {})),
                  patch.object(runner, "run_tests", return_value={"tests_run": 1, "failures": 0, "errors": 0}),
                  patch.object(runner, "infer_all", side_effect=RuntimeError("synthetic stop")) as infer):
                with self.assertRaisesRegex(RuntimeError, "synthetic stop"): runner.run_round()
            self.assertEqual(infer.call_count, 1)
            self.assertTrue((output / "BASELINE_REGISTRY.json").exists())
            self.assertFalse((output / "BASELINE_RESULTS.json").exists())
            journal = [json.loads(line) for line in (output / "EVALUATION_JOURNAL.jsonl").read_bytes().splitlines()]
            self.assertEqual(journal[-1]["event"], "FAILED_STOP_NO_RETRY")


if __name__ == "__main__":
    unittest.main()
