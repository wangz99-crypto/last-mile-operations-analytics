from contextlib import redirect_stderr
from dataclasses import FrozenInstanceError, asdict, replace
import io
import subprocess
import sys
import unittest
from unittest.mock import patch

from gateway.domain.evaluation.answerability.answerability_contracts import (
    ALLOW, ABSTAIN, SUPPORTED, INSUFFICIENT, UNRESOLVED, ContractError,
    FrozenRetrievalResult, GateInput, GateOutput, make_gate_input, parse_gate_output,
)
from gateway.domain.evaluation.answerability import evaluate_development_gate as evaluator
from gateway.domain.tests._answerability_fixtures import BUNDLE, IDENTITIES, evidence, fixture


class EvaluatorBoundaryTests(unittest.TestCase):
    def test_gate_input_exact_allowlist_and_nested_immutability(self):
        value = make_gate_input("  Original question?\n", FrozenRetrievalResult(evidence(), BUNDLE))
        self.assertEqual(value.question, "  Original question?\n")
        self.assertEqual(set(asdict(value)), {"question", "evidence", "active_bundle"})
        self.assertFalse(hasattr(value, "__dict__"))
        forbidden = {"question_id", "split", "expected_gate", "reason_code", "difficulty_band", "support_shape",
                     "hard_negative", "gold_support_sections", "required_support_sections", "authoring_rationale",
                     "rationale", "review_status", "owner_notes", "benchmark_family"}
        def check_keys(node):
            if isinstance(node, dict):
                self.assertFalse(forbidden & set(node))
                for child in node.values():
                    check_keys(child)
            elif isinstance(node, (tuple, list)):
                for child in node:
                    check_keys(child)
        check_keys(asdict(value))
        for target, field, new in ((value, "question", "change"), (value.evidence[0], "body", "change"),
                                   (value.active_bundle, "bundle_version", "change")):
            with self.assertRaises(FrozenInstanceError):
                setattr(target, field, new)
        with self.assertRaises(TypeError):
            GateInput(question="test", evidence=(), active_bundle=BUNDLE, question_id="secret")
        with self.assertRaises(ContractError):
            make_gate_input({"question": "test", "expected_gate": ALLOW}, FrozenRetrievalResult((), BUNDLE))

    def test_gate_output_valid_pairs_and_optional_reason(self):
        for decision, reason in ((ALLOW, SUPPORTED), (ABSTAIN, INSUFFICIENT), (ABSTAIN, UNRESOLVED),
                                 (ALLOW, None), (ABSTAIN, None)):
            self.assertEqual(parse_gate_output({"decision": decision, "reason_code": reason}), GateOutput(decision, reason))
        self.assertEqual(parse_gate_output({"decision": ALLOW}), GateOutput(ALLOW))

    def test_malformed_gate_outputs_are_rejected(self):
        for raw in ({"decision": ALLOW, "reason_code": INSUFFICIENT}, {"decision": ABSTAIN, "reason_code": SUPPORTED},
                    {"decision": "allow"}, {"decision": "ERROR"}, {"decision": ALLOW, "extra": True},
                    {}, None, [], {"decision": True}, {"decision": ALLOW, "reason_code": []}):
            with self.subTest(raw=raw), self.assertRaises(ContractError):
                parse_gate_output(raw)

    def test_invalid_evidence_rank_depth_duplicates_and_identity(self):
        ranked = evidence()
        invalid = (ranked[::-1], (ranked[1],), ranked+(ranked[0],),
                   (ranked[0], replace(ranked[0], rank=2)), list(ranked))
        for items in invalid:
            with self.assertRaises(ContractError):
                FrozenRetrievalResult(items, BUNDLE)
        for updates in ({"rank": True}, {"rank": 0}, {"policy_id": "bad"}, {"version": " "},
                        {"section_id": "../bad"}, {"cosine_score": float("nan")},
                        {"cosine_score": 0.29}, {"cosine_score": float("inf")}, {"cosine_score": True}):
            with self.assertRaises(ContractError):
                replace(ranked[0], **updates)

    def test_descending_scores_and_canonical_ties(self):
        ranked = evidence(2)
        ties = (ranked[0], replace(ranked[1], cosine_score=ranked[0].cosine_score))
        FrozenRetrievalResult(ties, BUNDLE)
        with self.assertRaises(ContractError):
            FrozenRetrievalResult(tuple(replace(e, rank=i+1) for i, e in enumerate(reversed(ties))), BUNDLE)
        with self.assertRaises(ContractError):
            FrozenRetrievalResult((ranked[0], replace(ranked[1], cosine_score=0.95)), BUNDLE)

    def test_frozen_configuration_cannot_change(self):
        value = FrozenRetrievalResult(evidence(), BUNDLE)
        for updates in ({"model": "other"}, {"revision": "other"}, {"top_k": 5}, {"device": "cuda"},
                        {"normalized": False}, {"threshold": 0.31}, {"query_instruction": "prefix"},
                        {"query_rewriting": True}, {"section_count": 24}, {"embedding_dimension": 768}):
            with self.assertRaises(ContractError):
                replace(value, **updates)
        for updates in ({"effective_from": None}, {"effective_from": "2026-01-01"},
                        {"effective_to": "2020-01-01T00:00:00Z"}, {"registry_sha256": "bad"}):
            with self.assertRaises(ContractError):
                replace(BUNDLE, **updates)

    def test_synthetic_boundary_calls_once_with_no_gold(self):
        cases, retrievals, _ = fixture()
        received = []
        class Stub:
            def decide(self, value):
                received.append(value)
                return GateOutput(ALLOW)
        result = evaluator._evaluate_cases(cases, retrievals, Stub())
        self.assertEqual(len(received), 40)
        self.assertTrue(all(type(x) is GateInput for x in received))
        self.assertEqual(result["primary"]["allow_recall"]["numerator"], 20)
        self.assertEqual(result["primary"]["false_support_rate"]["numerator"], 20)

    def test_candidate_exceptions_and_malformed_outputs_no_retry(self):
        cases, retrievals, _ = fixture()
        class Stub:
            attempts = 0
            def decide(self, value):
                self.attempts += 1
                if self.attempts == 1:
                    raise RuntimeError("synthetic exception")
                return {"decision": "invalid"}
        stub = Stub()
        result = evaluator._evaluate_cases(cases, retrievals, stub)
        self.assertEqual(stub.attempts, 40)
        self.assertEqual(result["errors"]["by_code"], {"CANDIDATE_EXCEPTION": 1, "MALFORMED_OUTPUT": 39})

    def test_mutable_candidate_output_is_snapshotted(self):
        cases, retrievals, _ = fixture()
        class Stub:
            calls = 0
            reused = {"decision": ALLOW}
            def decide(self, value):
                self.calls += 1
                self.reused["decision"] = ALLOW if self.calls <= 20 else ABSTAIN
                return self.reused
        result = evaluator._evaluate_cases(cases, retrievals, Stub())
        self.assertTrue(result["eligible"])

    def test_bad_retrieval_inventory_fails_before_candidate_call(self):
        cases, retrievals, _ = fixture()
        class Stub:
            def decide(self, value):
                raise AssertionError("must not call")
        with self.assertRaisesRegex(ContractError, "missing retrieval"):
            evaluator._evaluate_cases(cases, retrievals[:-1], Stub())

    def test_production_entry_orchestration_uses_synthetic_mocked_loader_only(self):
        cases, retrievals, _ = fixture()
        class Stub:
            def decide(self, value):
                return GateOutput(ABSTAIN)
        with (patch.object(evaluator, "load_development", return_value=cases) as load,
              patch.object(evaluator, "active_policy_identities", return_value=frozenset(IDENTITIES))):
            result = evaluator.evaluate_development(Stub(), retrievals)
        load.assert_called_once_with()
        self.assertEqual(result["primary"]["correct_abstention_rate"]["numerator"], 20)

    def test_cli_redirects_and_abbreviations_rejected_before_load(self):
        for flag in ("--split", "--benchmark-dir", "--manifest", "--question-dir", "--validate"):
            with self.subTest(flag=flag), patch.object(evaluator, "validation_summary") as load:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    evaluator.main(["--validate-only", flag, "untrusted-path"])
                self.assertEqual(error.exception.code, 2)
                load.assert_not_called()
        with self.assertRaises(TypeError):
            evaluator.evaluate_development(None, (), manifest="untrusted-path")

    def test_imports_need_no_model_or_network(self):
        code = '''import sys
def guard(event, args):
    if event.startswith("socket."):
        raise RuntimeError("network access forbidden")
sys.addaudithook(guard)
import gateway.domain.evaluation.answerability.evaluate_development_gate
assert not {"torch", "transformers", "sentence_transformers", "huggingface_hub"}.intersection(sys.modules)
'''
        completed = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
