"""Entirely synthetic questions/rankings; no benchmark record is used for scoring."""
from contextlib import contextmanager
from dataclasses import replace
import hashlib
from pathlib import Path
import shutil
import tempfile

from gateway.domain.evaluation.answerability.answerability_contracts import (
    ABSTAIN, ALLOW, SUPPORTED, INSUFFICIENT, ActiveBundle, CandidateObservation,
    EvaluationCase, FrozenRetrievalResult, GateOutput, RankedEvidence, RetrievalAssociation,
)

BUNDLE = ActiveBundle("last-mile-exception-triage-demo", "1.0-demo", "2026-09-26T00:00:00Z", None,
                      "093b763fadfaadf7859d758722e21160390edeb4d0a4e0ce18a97401efcba77f",
                      "a9d50558f1654281212d45c27ec9e419f788364bf086d4c63b2cf1dcd6eed768")
IDENTITIES = tuple(("SOP-01", "1.0-demo", f"synthetic-{chr(97+i)}") for i in range(10))


def evidence(depth=10):
    return tuple(RankedEvidence(i+1, *IDENTITIES[i], "Synthetic document", "Synthetic section",
                                "Synthetic policy body only.", 0.9-i*0.05) for i in range(depth))


def fixture():
    cases, retrievals, observations = [], [], []
    for i in range(40):
        allow = i < 20
        refs = (IDENTITIES[0], IDENTITIES[5]) if i < 6 else (IDENTITIES[0],)
        case = EvaluationCase(f"TEST{i+1:03d}", f"Synthetic policy request number {i+1}.",
                              ALLOW if allow else ABSTAIN, SUPPORTED if allow else INSUFFICIENT,
                              refs if allow else (), refs if allow else ())
        cases.append(case)
        retrievals.append(RetrievalAssociation(case.question_id, hashlib.sha256(case.question.encode()).hexdigest(),
                                               FrozenRetrievalResult(evidence(), BUNDLE)))
        observations.append(CandidateObservation(case.question_id, GateOutput(case.expected_gate, case.reason_code)))
    return tuple(cases), tuple(retrievals), tuple(observations)


def changed_outputs(observations, replacements):
    return tuple(replace(o, output=replacements.get(i, o.output)) for i, o in enumerate(observations))


def record():
    ref = dict(zip(("policy_id", "version", "section_id"), IDENTITIES[0]))
    return {"question_id": "AQ001", "split": "DEVELOPMENT", "question": "Synthetic structural fixture?",
            "expected_gate": ALLOW, "reason_code": SUPPORTED, "difficulty_band": "DIRECT",
            "support_shape": "SINGLE_SECTION", "hard_negative": False,
            "gold_support_sections": [ref], "required_support_sections": [dict(ref)],
            "authoring_rationale": "Synthetic structural rationale.", "review_status": "OWNER_REVIEWED"}


@contextmanager
def temporary_directory():
    parent = Path(tempfile.gettempdir()).resolve()
    directory = Path(tempfile.mkdtemp(prefix="phase2hb1-test-", dir=parent)).resolve()
    try:
        yield directory
    finally:
        # Verify the final absolute target before recursive cleanup on Windows.
        if directory.parent != parent or not directory.name.startswith("phase2hb1-test-"):
            raise RuntimeError("unsafe temporary cleanup target")
        shutil.rmtree(directory)
