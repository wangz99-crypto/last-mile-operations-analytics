"""Exact, candidate-independent DEVELOPMENT scoring. No retrieval execution."""
from collections import Counter
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import json

from .answerability_contracts import (
    ALLOW, ABSTAIN, CandidateObservation, ContractError, EvaluationCase,
    RetrievalAssociation, parse_gate_output, require,
)


def metric(numerator, denominator):
    """Macro sums can be fractional; retain their exact rational numerator."""
    require(type(denominator) is int and denominator > 0, "empty metric denominator")
    numerator = Fraction(numerator)
    with localcontext() as context:
        context.prec = 50
        rate = Decimal(numerator.numerator) / Decimal(numerator.denominator * denominator)
        displayed = format(rate.quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN), "f")
    return {"numerator": numerator.numerator, "numerator_divisor": numerator.denominator,
            "denominator": denominator, "rate": displayed}


def deterministic_json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def validate_associations(cases, retrievals):
    require(type(cases) is tuple and all(type(c) is EvaluationCase for c in cases), "typed case tuple required")
    require(len(cases) == 40 and len({c.question_id for c in cases}) == 40, "40 unique cases required")
    require(Counter(c.expected_gate for c in cases) == {ALLOW: 20, ABSTAIN: 20}, "20/20 classes required")
    require(any(len(c.required_support_sections) > 1 for c in cases), "multi-required denominator is empty")
    require(type(retrievals) is tuple, "retrieval association tuple required")
    indexed = {}
    expected = {c.question_id: c for c in cases}
    for item in retrievals:
        require(type(item) is RetrievalAssociation, "typed retrieval association required")
        require(item.question_id in expected, "unknown retrieval question ID")
        require(item.question_id not in indexed, "duplicate retrieval question ID")
        original = expected[item.question_id].question.encode("utf-8")
        require(item.question_sha256 == hashlib.sha256(original).hexdigest(), "retrieval question text binding differs")
        item.result.__post_init__()
        indexed[item.question_id] = item.result
    require(set(indexed) == set(expected), "missing retrieval result")
    return indexed


def _retrieval_metrics(case, retrieval, enabled):
    gold, required = set(case.gold_support_sections), set(case.required_support_sections)
    ranked = tuple(e.identity for e in retrieval.evidence)
    found = {k: set(ranked[:k]) if enabled else set() for k in (1, 3, 5, 10)}
    row = {f"hit_at_{k}": bool(found[k] & gold) for k in (1, 3)}
    for k in (3, 5, 10):
        count = len(found[k] & required)
        row[f"required_found_at_{k}"] = count
        row[f"required_coverage_at_{k}"] = metric(count, len(required))
        row[f"multi_required_full_at_{k}"] = required <= found[k] if len(required) > 1 else None
    return row


def _aggregate_retrieval(rows):
    count = len(rows)
    multi_count = sum(row["required_count"] > 1 for row in rows)
    result = {}
    for mode in ("gated", "ungated"):
        values = {f"hit_at_{k}": metric(sum(r[mode][f"hit_at_{k}"] for r in rows), count) for k in (1, 3)}
        for k in (3, 5, 10):
            found = [r[mode][f"required_found_at_{k}"] for r in rows]
            values[f"required_macro_coverage_at_{k}"] = metric(
                sum((Fraction(n, r["required_count"]) for n, r in zip(found, rows)), Fraction()), count)
            values[f"required_micro_coverage_at_{k}"] = metric(sum(found), sum(r["required_count"] for r in rows))
            values[f"multi_required_full_at_{k}"] = metric(
                sum(r[mode][f"multi_required_full_at_{k}"] is True for r in rows), multi_count)
        result[mode] = values
    return result


def score_results(cases, retrievals, observations):
    retrieved = validate_associations(cases, retrievals)
    require(type(observations) is tuple, "candidate observation tuple required")
    ids = {c.question_id for c in cases}
    outputs = {}
    for observation in observations:
        require(type(observation) is CandidateObservation, "typed candidate observation required")
        require(observation.question_id in ids, "unknown candidate question ID")
        require(observation.question_id not in outputs, "duplicate candidate question ID")
        outputs[observation.question_id] = observation
    rows = []
    for case in sorted(cases, key=lambda c: c.question_id):
        observation = outputs.get(case.question_id)
        error, output = None, None
        if observation is None or (observation.output is None and observation.error is None):
            error = "MISSING_OUTPUT"
        elif observation.error is not None:
            error = observation.error
        else:
            try:
                output = parse_gate_output(observation.output)
            except (ContractError, TypeError):
                error = "MALFORMED_OUTPUT"
        decision = output.decision if output else None
        reason = output.reason_code if output else None
        retrieval = retrieved[case.question_id]
        row = {"question_id": case.question_id, "gold_decision": case.expected_gate,
               "predicted_decision": decision, "binary_correct": decision == case.expected_gate,
               "gold_reason_code": case.reason_code, "predicted_reason_code": reason,
               "reason_correct": (reason == case.reason_code) if reason is not None else None,
               "candidate_error": error, "retrieval_result_count": len(retrieval.evidence)}
        if case.expected_gate == ALLOW:
            row["required_count"] = len(case.required_support_sections)
            row["gated"] = _retrieval_metrics(case, retrieval, decision == ALLOW)
            row["ungated"] = _retrieval_metrics(case, retrieval, True)
        rows.append(row)
    count = lambda gold, predicted: sum(r["gold_decision"] == gold and r["predicted_decision"] == predicted for r in rows)
    primary = {"allow_recall": metric(count(ALLOW, ALLOW), 20),
               "false_abstention_rate": metric(count(ALLOW, ABSTAIN), 20),
               "correct_abstention_rate": metric(count(ABSTAIN, ABSTAIN), 20),
               "false_support_rate": metric(count(ABSTAIN, ALLOW), 20)}
    errors = [r for r in rows if r["candidate_error"] is not None]
    reason_rows = [r for r in rows if r["reason_correct"] is not None]
    floors = count(ALLOW, ALLOW) >= 18 and count(ABSTAIN, ABSTAIN) >= 18
    return {"schema_version": "answerability-development-score-v0.1", "question_count": 40,
            "class_counts": {ALLOW: 20, ABSTAIN: 20}, "primary": primary,
            "valid_complete_run": not errors, "meets_class_floors": floors, "eligible": floors and not errors,
            "errors": {"count": len(errors), "question_ids": [r["question_id"] for r in errors],
                       "by_code": dict(sorted(Counter(r["candidate_error"] for r in errors).items())),
                       "by_gold_class": {c: sum(r["gold_decision"] == c for r in errors) for c in (ALLOW, ABSTAIN)}},
            "reason_diagnostic": {"emitted_valid_reason_count": len(reason_rows),
                                  "agreement": metric(sum(r["reason_correct"] for r in reason_rows), len(reason_rows)) if reason_rows else None},
            "retrieval": _aggregate_retrieval([r for r in rows if r["gold_decision"] == ALLOW]),
            "questions": rows}
