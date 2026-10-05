"""Candidate-independent entry point. CLI exposes structural validation only."""
import argparse
import sys

from .answerability_contracts import (
    ActiveBundle, CandidateObservation, ContractError, make_gate_input, parse_gate_output, require,
)
from .answerability_scoring import deterministic_json_bytes, score_results, validate_associations
from .development_loader import active_policy_identities, load_development, validation_summary


def _evaluate_cases(cases, retrievals, candidate):
    """Shared orchestration for the pinned entry and entirely synthetic unit fixtures."""
    retrieved = validate_associations(cases, retrievals)
    observations = []
    for case in sorted(cases, key=lambda c: c.question_id):
        gate_input = make_gate_input(case.question, retrieved[case.question_id])
        try:
            raw = candidate.decide(gate_input)
        except Exception:
            # No retry, exception repr, traceback, benchmark metadata or fabricated decision.
            observations.append(CandidateObservation(case.question_id, error="CANDIDATE_EXCEPTION"))
            continue
        try:
            # Snapshot immediately: do not retain a candidate's mutable dictionary.
            output = parse_gate_output(raw)
        except (ContractError, TypeError):
            observations.append(CandidateObservation(case.question_id, error="MALFORMED_OUTPUT"))
        else:
            observations.append(CandidateObservation(case.question_id, output=output))
    # Only after inference, consult Gold annotations to score the collected outputs.
    return score_results(cases, retrievals, tuple(observations))


def evaluate_development(candidate, retrievals):
    """Future candidate entry: supplied results, pinned repository DEVELOPMENT, no path arguments.

    Phase 2H-B1 exercises this entry only with a synthetic mocked loader. No real
    rankings or candidate evaluation are produced in this phase.
    """
    cases = load_development()
    retrieved = validate_associations(cases, retrievals)
    identities = active_policy_identities()
    authority = ActiveBundle(
        "last-mile-exception-triage-demo", "1.0-demo", "2026-09-26T00:00:00Z", None,
        "093b763fadfaadf7859d758722e21160390edeb4d0a4e0ce18a97401efcba77f",
        "a9d50558f1654281212d45c27ec9e419f788364bf086d4c63b2cf1dcd6eed768",
    )
    for result in retrieved.values():
        require(result.bundle == authority, "supplied active authority differs from frozen corpus")
        require(all(e.identity in identities for e in result.evidence), "supplied section outside active corpus")
    return _evaluate_cases(cases, retrievals, candidate)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate pinned DEVELOPMENT custody; no candidate/model run.",
                                     allow_abbrev=False)
    parser.add_argument("--validate-only", action="store_true", required=True)
    parser.parse_args(argv)
    sys.stdout.buffer.write(deterministic_json_bytes(validation_summary()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
