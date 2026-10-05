"""Registered Round-1 gates over saved DEVELOPMENT evidence; no retrieval path."""
import argparse
from collections import Counter
from contextlib import AbstractContextManager
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from .answerability_contracts import (
    ALLOW, ABSTAIN, ActiveBundle, CandidateObservation, ContractError, FrozenRetrievalResult,
    GateInput, RankedEvidence, RetrievalAssociation, parse_gate_output, require,
)
from .answerability_scoring import deterministic_json_bytes, metric, score_results, validate_associations
from .development_loader import ROOT, IDS, MANIFEST_SHA256, RECEIPT, load_development, safe_regular_file, sha256, strict_json
from .gates import baseline_gates as gates

REPO = ROOT.parents[3]
BASE_COMMIT = "e2c363f150f5494b85bcf4de2e7800c57727d92a"
BASE_TAG = "answerability-dev-evidence-v0.1-pre-candidates"
HARNESS_COMMIT = "e017a61ac160e9541356d7bc862c9d3b73061789"
HARNESS_TAG = "answerability-dev-harness-v0.1.1-pre-candidates"
B2 = REPO / "artifacts/answerability_dev_bge_evidence_v0"
OUTPUT = REPO / "artifacts/answerability_dev_gate_baselines_v0"
B2_HASHES = {
    "DEVELOPMENT_BGE_EVIDENCE.json": "1ba747fe7a6eaa97610d05fd3690048aa062723f87585e38725dd149b6a57a52",
    "DEVELOPMENT_RETRIEVAL_METRICS.json": "06ca57166401e6aaef726faa2d558ce698c5dddcb12749c39e814f9098a0933c",
    "ATTEMPT_JOURNAL.jsonl": "36ffeabce5cc978830aa87b0041604b77f9a445b060e943dd9393bcba699b101",
    "EVIDENCE_FREEZE_RECORD.md": "234bfa45f628ddc072b64cc27553cdd04938b25dd05e9e3cf13f0d9fe61620c3",
    "RUN_MANIFEST.json": "e8f98481f60203d8f366a6cc73ac7947a6b72c6582b082a6a35d2199cb43ca06",
}
SOURCE_PATHS = (
    "gateway/domain/evaluation/answerability/gates/baseline_gates.py",
    "gateway/domain/evaluation/answerability/evaluate_baseline_gates.py",
    "gateway/domain/tests/test_answerability_baseline_gates.py",
)
OUTPUT_NAMES = ("BASELINE_REGISTRY.json", "BASELINE_RESULTS.json", "BASELINE_REPORT.md",
                "RUN_MANIFEST.json", "EVALUATION_JOURNAL.jsonl", "BASELINE_REVIEW_RECORD.md")
TEST_MODULES = (
    "gateway.domain.tests.test_answerability_baseline_gates",
    "gateway.domain.tests.test_answerability_development_loader",
    "gateway.domain.tests.test_answerability_scoring",
    "gateway.domain.tests.test_answerability_evaluator_boundary",
)


class ExecutionProhibited(BaseException):
    """Fatal boundary violation; never downgraded to an ordinary candidate error."""


class NoRetrievalGuard(AbstractContextManager):
    """Block imports and calls (including already imported code), plus network/data access."""
    def __init__(self):
        self.active = False
        self.violations = []

    def deny(self, operation):
        self.violations.append(operation)
        raise ExecutionProhibited(operation)

    def find_spec(self, fullname, path=None, target=None):
        prefixes = ("gateway.domain.retrieval", "sentence_transformers", "transformers", "torch",
                    "huggingface_hub", "openai", "anthropic")
        if self.active and any(fullname == p or fullname.startswith(p + ".") for p in prefixes):
            self.deny("prohibited import: " + fullname)

    def profile(self, frame, event, arg):
        if self.active and event == "call":
            path = frame.f_code.co_filename.lower().replace("\\", "/")
            if "/gateway/domain/retrieval/" in path or any(
                "/" + name + "/" in path for name in ("sentence_transformers", "transformers", "torch", "huggingface_hub", "openai", "anthropic")
            ):
                self.deny("prohibited retrieval/model call: " + frame.f_code.co_name)

    def audit(self, event, args):
        if not self.active:
            return
        if event.startswith("socket.") and event != "socket.gethostname":
            self.deny("prohibited socket operation: " + event)
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = os.fsdecode(args[0]).lower().replace("\\", "/")
            if any(part in path for part in ("heldout", "held_out", "/phase2d-model/", "last-mile-answerability-eval-authoring")):
                self.deny("prohibited private/model file access")

    def __enter__(self):
        require(not self.active, "guard already active")
        self.old_profile = sys.getprofile()
        self.active = True
        sys.meta_path.insert(0, self)
        sys.addaudithook(self.audit)
        sys.setprofile(self.profile)
        return self

    def __exit__(self, *args):
        self.active = False
        sys.setprofile(self.old_profile)
        sys.meta_path.remove(self)


def file_hash(path):
    return sha256(Path(path).read_bytes())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO).decode("utf-8").strip()


def verify_b2():
    payloads = {name: safe_regular_file(B2, name).read_bytes() for name in B2_HASHES}
    for name, expected in B2_HASHES.items():
        require(sha256(payloads[name]) == expected, "frozen B2 artifact changed: " + name)
    return payloads


def verify_protected(manifest):
    hashes = {**manifest["protected_source_sha256"], **manifest["b2_source_sha256"], **manifest["policy_corpus_sha256"]}
    # Historical HELDOUT provenance is not relevant to DEVELOPMENT; do not open it.
    permitted = {p: h for p, h in hashes.items() if not any(t in p.lower() for t in ("heldout", "held_out"))}
    for name, expected in permitted.items():
        require(file_hash(REPO / name) == expected, "frozen source changed: " + name)
    return permitted


def reconstruct_inputs(package, cases, file_hashes):
    require(tuple(c.question_id for c in cases) == IDS, "exact ordered DEVELOPMENT cases required")
    rows = package["questions"]
    require(len(rows) == 40 and tuple(r["question_id"] for r in rows) == IDS, "evidence inventory differs")
    bundle = ActiveBundle(**package["active_bundle"])
    values, retrievals = [], []
    for case, row in zip(cases, rows):
        require(row["question"] == case.question and row["question_text_sha256"] == sha256(case.question.encode("utf-8"))
                and row["question_file_sha256"] == file_hashes[case.question_id], "evidence question binding differs")
        ranked = tuple(RankedEvidence(e["rank"], e["policy_id"], e["version"], e["section_id"],
                                      e["document_title"], e["section_title"], e["section_body"], e["cosine_score"])
                       for e in row["results"])
        frozen = FrozenRetrievalResult(ranked, bundle)
        values.append(GateInput(case.question, ranked, bundle))
        retrievals.append(RetrievalAssociation(case.question_id, row["question_text_sha256"], frozen))
    validate_associations(cases, tuple(retrievals))
    return tuple(values), tuple(retrievals)


def load_frozen_evidence():
    """No caller-supplied path, split, model, retriever or alternate evidence source."""
    payloads = verify_b2()
    manifest = strict_json(payloads["RUN_MANIFEST.json"])
    protected = verify_protected(manifest)
    cases = load_development()
    package = strict_json(payloads["DEVELOPMENT_BGE_EVIDENCE.json"])
    require(deterministic_json_bytes(package) == payloads["DEVELOPMENT_BGE_EVIDENCE.json"], "noncanonical B2 serialization")
    require(package["development_manifest_sha256"] == MANIFEST_SHA256 and package["development_receipt"] == RECEIPT,
            "B2 DEVELOPMENT custody differs")
    values, retrievals = reconstruct_inputs(package, cases, manifest["development_file_sha256"])
    require(manifest["attempt_count"] == 40 and manifest["question_attempts"] == dict.fromkeys(IDS, 1), "historical attempts differ")
    return cases, values, retrievals, protected


def make_registry(source_hash):
    stopword_bytes = ("\n".join(sorted(gates.STOPWORDS)) + "\n").encode("utf-8")
    descriptions = (
        "Always ALLOW with SUPPORTED_BY_ACTIVE_POLICY; sanity control only.",
        "Always ABSTAIN with INSUFFICIENT_POLICY_SUPPORT; sanity control only.",
        "ALLOW iff at least one frozen section is present; inspect no question or evidence text.",
        "ALLOW iff distinct informative question-token coverage in rank 1 title/body is at least 3/5.",
        "ALLOW iff distinct informative question-token coverage in the union of available ranks 1-3 title/body is at least 3/5.",
    )
    candidates = []
    for index, candidate_id in enumerate(gates.IDS):
        lexical = index >= 3
        config = {
            "candidate_id": candidate_id, "candidate_type": "SANITY_CONTROL" if index < 2 else "BASELINE",
            "control_only": index < 2, "selection_eligible": index >= 2,
            "algorithm_description": descriptions[index],
            "tokenizer": {"normalization": "text.lower()", "regex": gates.TOKEN_PATTERN, "distinct_tokens": True} if lexical else None,
            "stopword_list": sorted(gates.STOPWORDS) if lexical else None,
            "stopword_list_sha256": sha256(stopword_bytes) if lexical else None,
            "stopword_hash_format": "sorted UTF-8 words, one per LF line, final LF" if lexical else None,
            "coverage_threshold": {"numerator": 3, "denominator": 5, "decimal": "0.60"} if lexical else None,
            "evidence_depth": (0, 0, 10, 1, 3)[index],
            "evidence_fields": ["section_title", "body"] if lexical else [],
            "empty_informative_question": "ABSTAIN" if lexical else "not applicable",
            "score_weighting": False, "query_rewriting": False,
            "allow_reason": "SUPPORTED_BY_ACTIVE_POLICY", "abstain_reason": "INSUFFICIENT_POLICY_SUPPORT",
        }
        candidates.append({**config, "source_file_sha256": source_hash,
                           "configuration_sha256": sha256(deterministic_json_bytes(config))})
    return {"schema_version": "answerability-gate-baseline-registry-v0",
            "registry_status": "PRE_REGISTERED_BEFORE_DEVELOPMENT_GATE_RESULTS",
            "candidate_order": list(gates.IDS), "candidates": candidates}


def infer_inputs(candidate, inputs):
    """No IDs, case records, Gold, metadata bags or evaluator closures cross this boundary."""
    require(type(inputs) is tuple and len(inputs) == 40 and all(type(v) is GateInput for v in inputs), "40 GateInputs required")
    outputs = []
    for value in inputs:
        try:
            raw = candidate.decide(value)
        except Exception:
            outputs.append((None, "CANDIDATE_EXCEPTION"))
            continue
        try:
            output = parse_gate_output(raw)
        except (ContractError, TypeError):
            outputs.append((None, "MALFORMED_OUTPUT"))
        else:
            outputs.append((output, None))
    return tuple(outputs)


def associate_outputs(ids, outputs):
    require(len(ids) == len(outputs) == 40 and len(set(ids)) == 40, "40 unique outputs required")
    return tuple(CandidateObservation(qid, output=value, error=error) for qid, (value, error) in zip(ids, outputs))


def infer_all(inputs, registry, journal):
    """Finish ALL inference before any Gold-based scoring or diagnostic read."""
    outputs = []
    for spec in registry["candidates"]:
        journal.record("CANDIDATE_STARTED", candidate_id=spec["candidate_id"])
        result = infer_inputs(gates.BaselineGate(spec["candidate_id"]), inputs)
        # Save actual outputs durably before scoring. There is no retry path.
        journal.record("CANDIDATE_COMPLETED", candidate_id=spec["candidate_id"],
                       outputs=[{"output": asdict(value) if value else None, "error": error} for value, error in result])
        outputs.append(result)
    return tuple(outputs)


def selection_eligible(spec, score):
    return bool(not spec["control_only"] and spec["selection_eligible"] and score["eligible"])


def secondary_metrics(score):
    rows = score["questions"]
    recalls = [Fraction(score["primary"][key]["numerator"], 20) for key in ("allow_recall", "correct_abstention_rate")]
    f1s = []
    for label in (ALLOW, ABSTAIN):
        tp = sum(r["gold_decision"] == label == r["predicted_decision"] for r in rows)
        fp = sum(r["gold_decision"] != label and r["predicted_decision"] == label for r in rows)
        fn = sum(r["gold_decision"] == label and r["predicted_decision"] != label for r in rows)
        f1s.append(Fraction(2 * tp, 2 * tp + fp + fn))
    return {"overall_accuracy": metric(sum(r["binary_correct"] for r in rows), 40),
            "balanced_accuracy": metric(sum(recalls), 2), "macro_f1": metric(sum(f1s), 2),
            "reason_code_agreement": score["reason_diagnostic"]["agreement"],
            "candidate_error_count": score["errors"]["count"],
            "semantics": "descriptive only; errors count as incorrect and false negatives; reason denominator uses frozen scorer"}


def diagnostic_metadata():
    manifest = strict_json(safe_regular_file(ROOT, "DEVELOPMENT_MANIFEST.json").read_bytes())
    require(file_hash(ROOT / "DEVELOPMENT_MANIFEST.json") == MANIFEST_SHA256, "DEVELOPMENT manifest differs")
    metadata = {}
    for entry in manifest["entries"]:
        data = safe_regular_file(ROOT, entry["filename"]).read_bytes()
        require(sha256(data) == entry["sha256"], "diagnostic question hash differs")
        row = strict_json(data)
        metadata[entry["question_id"]] = {key: row[key] for key in ("difficulty_band", "support_shape", "hard_negative")}
    return metadata


def breakdowns(score, metadata):
    rows = score["questions"]
    definitions = {
        "gold_class": ((ALLOW, ABSTAIN), lambda r: r["gold_decision"]),
        "abstain_reason": (("INSUFFICIENT_POLICY_SUPPORT", "UNRESOLVED_POLICY_CONTEXT"),
                           lambda r: r["gold_reason_code"] if r["gold_decision"] == ABSTAIN else None),
        "difficulty": (("DIRECT", "PARAPHRASE", "INDIRECT_OPERATIONAL"), lambda r: metadata[r["question_id"]]["difficulty_band"]),
        "allow_support_shape": (("SINGLE_SECTION", "MULTI_SECTION"),
                                lambda r: metadata[r["question_id"]]["support_shape"] if r["gold_decision"] == ALLOW else None),
        "hard_negative": (("true", "false"), lambda r: str(metadata[r["question_id"]]["hard_negative"]).lower()),
    }
    result = {}
    for name, (labels, group) in definitions.items():
        result[name] = {}
        for label in labels:
            selected = [r for r in rows if group(r) == label]
            result[name][label] = {"question_count": len(selected), "binary_correct_count": sum(r["binary_correct"] for r in selected),
                                   "binary_accuracy": metric(sum(r["binary_correct"] for r in selected), len(selected)) if selected else None,
                                   "candidate_error_count": sum(r["candidate_error"] is not None for r in selected)}
    return result


def failure_lists(score):
    rows = score["questions"]
    return {"false_abstentions": [r["question_id"] for r in rows if r["gold_decision"] == ALLOW and r["predicted_decision"] == ABSTAIN],
            "false_supports": [r["question_id"] for r in rows if r["gold_decision"] == ABSTAIN and r["predicted_decision"] == ALLOW],
            "candidate_errors": score["errors"]["question_ids"],
            "wrong_reason_only": [r["question_id"] for r in rows if r["binary_correct"] and r["reason_correct"] is False]}


def build_results(cases, retrievals, inputs, registry, raw_outputs, metadata):
    require(len(raw_outputs) == len(registry["candidates"]) == 5, "all five candidates required")
    candidates = []
    for spec, raw in zip(registry["candidates"], raw_outputs):
        observations = associate_outputs(tuple(c.question_id for c in cases), raw)
        score = score_results(cases, retrievals, observations)
        lexical = []
        if spec["candidate_id"] in gates.IDS[3:]:
            for case, value, observation in zip(cases, inputs, observations):
                counts = gates.lexical_counts(value, spec["evidence_depth"])
                lexical.append({"question_id": case.question_id, **asdict(counts),
                                "coverage": {"numerator": counts.coverage.numerator, "denominator": counts.coverage.denominator},
                                "decision": observation.output.decision if observation.output else None})
        candidates.append({"candidate_id": spec["candidate_id"], "control_only": spec["control_only"],
                           "selection_eligible_before_scoring": spec["selection_eligible"], "eligible": selection_eligible(spec, score),
                           "score": score, "secondary": secondary_metrics(score), "breakdowns": breakdowns(score, metadata),
                           "failure_ids": failure_lists(score), "lexical_diagnostics": lexical})
    return {"schema_version": "answerability-development-gate-baselines-v0", "candidate_order": list(gates.IDS),
            "question_order": [c.question_id for c in cases], "registry_sha256": sha256(deterministic_json_bytes(registry)),
            "b2_evidence_sha256": B2_HASHES["DEVELOPMENT_BGE_EVIDENCE.json"], "candidates": candidates,
            "eligible_baseline_count": sum(c["eligible"] for c in candidates), "candidate_selected": None}


def write_once(path, data):
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    require(Path(path).read_bytes() == data, "output readback differs")
    return sha256(data)


class Journal:
    def __init__(self, path):
        self.stream = Path(path).open("xb")

    def record(self, event, **payload):
        data = {"event": event, "utc": datetime.now(timezone.utc).isoformat(), **payload}
        self.stream.write((json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8"))
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


def run_tests():
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise ContractError("synthetic/unit tests failed before evaluation:\n" + stream.getvalue())
    return {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
            "modules": list(TEST_MODULES), "candidate_evaluations_on_real_development": 0}


def formatted_metric(value):
    if value is None:
        return "not applicable"
    return f"{value['numerator']}/{value['numerator_divisor']} divided by {value['denominator']} = {value['rate']}"


def render_report(results, registry, sources, test_result):
    lines = ["# Phase 2H-B3 DEVELOPMENT gate baselines, Round 1", "",
             "Status: CANDIDATE_AWAITING_OWNER_REVIEW", "",
             "Purpose: evaluate the five owner-specified deterministic assumptions against frozen DEVELOPMENT evidence.",
             "No candidate is selected. These are DEVELOPMENT observations, not HELD_OUT claims.", "",
             f"Base: `{BASE_COMMIT}` / `{BASE_TAG}`.",
             f"DEVELOPMENT: AQ001-AQ040, 20 ALLOW / 20 ABSTAIN; receipt `{RECEIPT}`.",
             f"B2 evidence SHA-256: `{B2_HASHES['DEVELOPMENT_BGE_EVIDENCE.json']}`.",
             f"Pre-evaluation registry SHA-256: `{sha256(deterministic_json_bytes(registry))}`.",
             f"Pre-evaluation tests: {test_result['tests_run']} passed, zero failures/errors.", "",
             "## Pre-evaluation source hashes", ""]
    lines.extend(f"- `{p}`: `{h}`" for p, h in sources.items())
    lines.extend(["", "## Results", "",
                  "Each candidate consumed the same 40 frozen GateInputs exactly once. Errors remain in fixed denominators.",
                  "Eligibility requires both >=18/20 class successes and structural validity; controls are always ineligible.",
                  "Secondary metrics and reason agreement are descriptive only.", ""])
    for candidate in results["candidates"]:
        score = candidate["score"]
        lines.extend([f"### {candidate['candidate_id']}", "",
                      f"Control only: {candidate['control_only']}. Eligible: {candidate['eligible']}.", "",
                      "| Primary metric | Exact value and rate |", "| --- | --- |"])
        lines.extend(f"| {key} | {formatted_metric(value)} |" for key, value in score["primary"].items())
        lines.extend(["", "| Secondary metric | Exact value and rate |", "| --- | --- |"])
        lines.extend(f"| {key} | {formatted_metric(candidate['secondary'][key])} |" for key in
                     ("overall_accuracy", "balanced_accuracy", "macro_f1", "reason_code_agreement"))
        lines.extend([f"| candidate_error_count | {score['errors']['count']} |", "",
                      "Gated retrieval: Gold ALLOW denominator remains 20, required sections 26, multi-required questions 6.",
                      "False ABSTAIN contributes zero; metrics are not conditional on predicted ALLOW.", "",
                      "| Gated retrieval metric | Exact value and rate |", "| --- | --- |"])
        lines.extend(f"| {key} | {formatted_metric(value)} |" for key, value in score["retrieval"]["gated"].items())
        lines.extend(["", "| Diagnostic group | Subgroup | Binary correct / total |", "| --- | --- | --- |"])
        for group, values in candidate["breakdowns"].items():
            lines.extend(f"| {group} | {label} | {value['binary_correct_count']}/{value['question_count']} |" for label, value in values.items())
        lines.extend(["", "Failure IDs (post-inference diagnostics only):", ""])
        lines.extend(f"- {key}: {', '.join(value) if value else 'none'}" for key, value in candidate["failure_ids"].items())
        lines.append("")
    next_step = ("Seek separate owner authorization for Phase 2H-B3.2 - Semantic Gate Engineering on DEVELOPMENT."
                 if results["eligible_baseline_count"] == 0 else "Stop for owner-reviewed candidate selection; do not select automatically or begin B4.")
    lines.extend([f"Eligible baseline count: **{results['eligible_baseline_count']}**.", "",
                  "No threshold sweep or candidate change occurred after registration/evaluation began. No retrieval, model initialization,",
                  "external/LLM calls, Phase 2H HELD_OUT or Phase 2G private HELDOUT access occurred. Historical B2 retrieval total remains 40.",
                  "Candidate source/configuration hashes were checked again after inference and output generation.",
                  "Per-question lexical counts, exact rational coverage, decisions and all scored rows are in BASELINE_RESULTS.json.",
                  "The journal preserves registration order and each candidate's actual outputs before scoring.", "",
                  "Procedural next step only: " + next_step, "", "No commit or tag created. Stop for owner review.", ""])
    return "\n".join(lines).encode("utf-8")


def preconditions():
    require(git("rev-parse", "HEAD") == BASE_COMMIT and git("rev-list", "-n", "1", BASE_TAG) == BASE_COMMIT,
            "B2 anchor differs")
    require(git("rev-list", "-n", "1", HARNESS_TAG) == HARNESS_COMMIT, "historical B1.1 tag differs")
    require(not os.path.lexists(OUTPUT), "refuse existing B3 output directory")
    status = subprocess.check_output(["git", "status", "--short", "--untracked-files=all"], cwd=REPO).decode("utf-8")
    require(all(line[3:] in (*SOURCE_PATHS, ".gitattributes") for line in status.splitlines()), "unexpected B3 source changes")
    return status


def run_round():
    """The production path runs once, refuses overwrite and preserves any failed partial run."""
    journal = None
    with NoRetrievalGuard() as guard:
        status = preconditions()
        cases, inputs, retrievals, protected = load_frozen_evidence()
        tests = run_tests()  # Only synthetic candidate inference; loader-only integrity tests may read DEVELOPMENT.
        sources = {name: file_hash(REPO / name) for name in SOURCE_PATHS}
        registry = make_registry(sources[SOURCE_PATHS[0]])
        registry_bytes = deterministic_json_bytes(registry)
        registry_hash = sha256(registry_bytes)
        OUTPUT.mkdir(exist_ok=False)
        journal = Journal(OUTPUT / "EVALUATION_JOURNAL.jsonl")
        try:
            journal.record("PRECONDITION_VERIFIED", base_commit=BASE_COMMIT, base_tag=BASE_TAG,
                           historical_harness_commit=HARNESS_COMMIT, initial_clean_worktree_verified_before_implementation=True)
            journal.record("B2_EVIDENCE_VERIFIED", b2_sha256=B2_HASHES, development_receipt=RECEIPT, gate_input_count=len(inputs))
            journal.record("SYNTHETIC_TESTS_PASSED", **tests)
            write_once(OUTPUT / "BASELINE_REGISTRY.json", registry_bytes)
            journal.record("BASELINES_REGISTERED", source_sha256=sources, registry_sha256=registry_hash,
                           configurations={c["candidate_id"]: {"configuration_sha256": c["configuration_sha256"],
                                                               "coverage_threshold": c["coverage_threshold"],
                                                               "evidence_depth": c["evidence_depth"]} for c in registry["candidates"]})
            # Integrity point: all candidate definitions and config bytes are now immutable.
            for name, expected in sources.items():
                require(file_hash(REPO / name) == expected, "source changed after registration")
            journal.record("DEVELOPMENT_EVALUATION_STARTED", candidate_count=5, question_count=40, expected_gate_calls=200)
            raw_outputs = infer_all(inputs, registry, journal)
            journal.record("DEVELOPMENT_EVALUATION_COMPLETED", gate_calls=200, retries=0,
                           candidate_errors=sum(error is not None for output in raw_outputs for _, error in output))
            # No diagnostic metadata is read until every candidate has finished.
            results = build_results(cases, retrievals, inputs, registry, raw_outputs, diagnostic_metadata())
            results_bytes = deterministic_json_bytes(results)
            require(deterministic_json_bytes(strict_json(results_bytes)) == results_bytes, "result serialization differs")
            for name, expected in sources.items():
                require(file_hash(REPO / name) == expected, "post-result source changed")
            require(make_registry(sources[SOURCE_PATHS[0]]) == registry, "registered configuration changed")
            verify_b2()
            require(verify_protected(strict_json((B2 / "RUN_MANIFEST.json").read_bytes())) == protected, "protected inventory changed")
            report = render_report(results, registry, sources, tests)
            review = report.replace(b"# Phase 2H-B3 DEVELOPMENT gate baselines, Round 1",
                                    b"# Phase 2H-B3 Round-1 baseline review record", 1)
            hashes = {"BASELINE_REGISTRY.json": registry_hash,
                      "BASELINE_RESULTS.json": write_once(OUTPUT / "BASELINE_RESULTS.json", results_bytes),
                      "BASELINE_REPORT.md": write_once(OUTPUT / "BASELINE_REPORT.md", report),
                      "BASELINE_REVIEW_RECORD.md": write_once(OUTPUT / "BASELINE_REVIEW_RECORD.md", review)}
            journal.record("ARTIFACTS_WRITTEN", output_sha256=hashes,
                           pending_final_manifest="RUN_MANIFEST.json follows journal closure; no circular self-hashes")
            journal.close()
            journal = None
            hashes["EVALUATION_JOURNAL.jsonl"] = file_hash(OUTPUT / "EVALUATION_JOURNAL.jsonl")
            require(not guard.violations, "prohibited execution attempted")
            manifest = {
                "run_type": "PHASE_2H_DEVELOPMENT_GATE_BASELINES_ROUND_1", "status": "CANDIDATE_AWAITING_OWNER_REVIEW",
                "base_commit": BASE_COMMIT, "base_tag": BASE_TAG, "historical_harness_commit": HARNESS_COMMIT,
                "benchmark": "answerability-benchmark-v0.1", "development_receipt": RECEIPT,
                "development_manifest_sha256": MANIFEST_SHA256, "b2_artifact_sha256": B2_HASHES,
                "candidate_count": 5, "control_count": 2, "selection_eligible_baseline_count_before_scoring": 3,
                "eligible_baseline_count": results["eligible_baseline_count"], "candidate_selected": None,
                "question_count": 40, "class_counts": {ALLOW: 20, ABSTAIN: 20}, "gate_calls": 200,
                "candidate_question_attempts": {candidate_id: dict.fromkeys(IDS, 1) for candidate_id in gates.IDS},
                "candidate_errors": {c["candidate_id"]: c["score"]["errors"]["count"] for c in results["candidates"]},
                "retrieval_calls": 0, "historical_b2_retrieval_calls": 40, "model_initializations": 0,
                "external_model_calls": 0, "network_calls": 0, "held_out_accessed": False,
                "phase_2h_held_out_accessed": False, "phase_2g_private_heldout_accessed": False,
                "post_result_tuning": False, "threshold_sweep": False, "retries": 0,
                "pre_evaluation_tests": tests, "source_sha256": sources, "protected_source_sha256": protected,
                "registry_sha256_before_evaluation": registry_hash,
                "configuration_sha256": {c["candidate_id"]: c["configuration_sha256"] for c in registry["candidates"]},
                "guard": "retrieval/model import and call block; socket and private-data audit block", "guard_violations": [],
                "initial_clean_worktree_verified_before_implementation": True, "git_status_at_run": status,
                "output_sha256": hashes, "manifest_self_hash_excluded": True,
                "completed_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
            }
            write_once(OUTPUT / "RUN_MANIFEST.json", deterministic_json_bytes(manifest))
            require({p.name for p in OUTPUT.iterdir()} == set(OUTPUT_NAMES), "output inventory differs")
            for name, expected in hashes.items():
                require(file_hash(OUTPUT / name) == expected, "final output differs")
            return results
        except BaseException as exc:
            if journal is not None:
                journal.record("FAILED_STOP_NO_RETRY", exception_type=type(exc).__name__)
                journal.close()
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="One registered DEVELOPMENT-only gate baseline round; no retrieval.", allow_abbrev=False)
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args(argv)
    results = run_round()
    print(json.dumps({"eligible_baseline_count": results["eligible_baseline_count"], "retrieval_calls": 0,
                      "candidate_results": [{"candidate_id": c["candidate_id"], "primary": c["score"]["primary"],
                                             "eligible": c["eligible"]} for c in results["candidates"]]}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
