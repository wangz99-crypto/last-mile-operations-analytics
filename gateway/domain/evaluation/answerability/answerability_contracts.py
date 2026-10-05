"""Candidate-independent, immutable inference types; no model imports."""
from dataclasses import dataclass
from datetime import datetime
import math
import re
from typing import Protocol

ALLOW = "ALLOW"
ABSTAIN = "ABSTAIN"
SUPPORTED = "SUPPORTED_BY_ACTIVE_POLICY"
INSUFFICIENT = "INSUFFICIENT_POLICY_SUPPORT"
UNRESOLVED = "UNRESOLVED_POLICY_CONTEXT"
REASONS = {ALLOW: frozenset({SUPPORTED}), ABSTAIN: frozenset({INSUFFICIENT, UNRESOLVED})}
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
MAX_DEPTH = 10
MIN_COSINE = 0.30


class ContractError(ValueError):
    """Invalid evidence or output; never repaired into a gate decision."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def text(value, label):
    require(type(value) is str and bool(value.strip()), f"{label}: nonempty string required")


def digest(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            "lowercase SHA-256 required")


def identity(value):
    require(type(value) is tuple and len(value) == 3, "canonical identity tuple required")
    patterns = (r"SOP-[0-9]{2}", r"[A-Za-z0-9][A-Za-z0-9._-]*", r"[a-z][a-z0-9-]*")
    require(all(type(v) is str and re.fullmatch(p, v) for v, p in zip(value, patterns)),
            "malformed canonical section identity")
    return value


def paired_reason(decision, reason):
    require(type(decision) is str and decision in REASONS, "invalid binary decision")
    require(reason is None or (type(reason) is str and reason in REASONS[decision]),
            "invalid decision/reason pairing")


@dataclass(frozen=True, slots=True)
class RankedEvidence:
    rank: int
    policy_id: str
    version: str
    section_id: str
    title: str
    section_title: str
    body: str
    cosine_score: float

    def __post_init__(self):
        require(type(self.rank) is int and 1 <= self.rank <= MAX_DEPTH, "invalid rank")
        identity(self.identity)
        for field in (self.title, self.section_title, self.body):
            text(field, "readable evidence")
        require(type(self.cosine_score) in (int, float) and math.isfinite(self.cosine_score)
                and -1.0 <= self.cosine_score <= 1.0, "invalid frozen cosine score")

    @property
    def identity(self):
        return self.policy_id, self.version, self.section_id


@dataclass(frozen=True, slots=True)
class ActiveBundle:
    bundle_id: str
    bundle_version: str
    effective_from: str
    effective_to: str | None
    manifest_sha256: str
    registry_sha256: str

    def __post_init__(self):
        require(self.bundle_id == "last-mile-exception-triage-demo"
                and self.bundle_version == "1.0-demo", "not the frozen active bundle")
        text(self.effective_from, "effective_from")
        dates = []
        for value in (self.effective_from, self.effective_to):
            if value is None:
                continue
            text(value, "effective timestamp")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ContractError("invalid effective timestamp") from exc
            require(parsed.tzinfo is not None, "effective timestamp needs timezone")
            dates.append(parsed)
        require(len(dates) >= 1 and (len(dates) == 1 or dates[0] < dates[1]),
                "invalid effective interval")
        digest(self.manifest_sha256)
        digest(self.registry_sha256)


def validate_evidence(evidence, bundle):
    require(type(bundle) is ActiveBundle, "typed active bundle required")
    require(type(evidence) is tuple and len(evidence) <= MAX_DEPTH, "maximum evidence depth is 10")
    require(all(type(e) is RankedEvidence for e in evidence), "typed ranked evidence required")
    require([e.rank for e in evidence] == list(range(1, len(evidence) + 1)), "rank sequence invalid")
    require(len({e.identity for e in evidence}) == len(evidence), "duplicate canonical identity")
    require(all(e.version == bundle.bundle_version for e in evidence), "mixed evidence versions")
    keys = [(-e.cosine_score, e.identity) for e in evidence]
    require(keys == sorted(keys), "frozen descending score/canonical tie order violated")
    # Frozen BGE thresholds the whole response by its top score, never each tail item.
    require(not evidence or evidence[0].cosine_score >= MIN_COSINE,
            "nonempty frozen response below top-score threshold")


@dataclass(frozen=True, slots=True)
class FrozenRetrievalResult:
    evidence: tuple[RankedEvidence, ...]
    bundle: ActiveBundle
    model: str = "BAAI/bge-small-en-v1.5"
    revision: str = MODEL_REVISION
    top_k: int = MAX_DEPTH
    device: str = "cpu"
    section_count: int = 25
    embedding_dimension: int = 384
    normalized: bool = True
    similarity: str = "normalized_dot_product"
    threshold: float = MIN_COSINE
    query_instruction: str = ""
    query_rewriting: bool = False

    def __post_init__(self):
        require(self.model == "BAAI/bge-small-en-v1.5" and self.revision == MODEL_REVISION
                and type(self.top_k) is int and self.top_k == MAX_DEPTH, "frozen retriever identity changed")
        require(self.device == "cpu" and type(self.section_count) is int and self.section_count == 25
                and type(self.embedding_dimension) is int and self.embedding_dimension == 384
                and self.normalized is True and self.similarity == "normalized_dot_product"
                and type(self.threshold) is float and self.threshold == MIN_COSINE
                and self.query_instruction == "" and self.query_rewriting is False,
                "frozen retrieval configuration changed")
        validate_evidence(self.evidence, self.bundle)


@dataclass(frozen=True, slots=True)
class GateInput:
    question: str
    evidence: tuple[RankedEvidence, ...]
    active_bundle: ActiveBundle

    def __post_init__(self):
        text(self.question, "original question")
        validate_evidence(self.evidence, self.active_bundle)


def make_gate_input(question, retrieval):
    """Accept text, never a benchmark record, ID, callback or metadata bag."""
    require(type(retrieval) is FrozenRetrievalResult, "typed frozen retrieval result required")
    return GateInput(question=question, evidence=retrieval.evidence, active_bundle=retrieval.bundle)


@dataclass(frozen=True, slots=True)
class GateOutput:
    decision: str
    reason_code: str | None = None

    def __post_init__(self):
        paired_reason(self.decision, self.reason_code)


def parse_gate_output(value):
    if type(value) is GateOutput:
        paired_reason(value.decision, value.reason_code)
        return value
    require(type(value) is dict and set(value) in ({"decision"}, {"decision", "reason_code"}),
            "output must contain only decision and optional reason_code")
    return GateOutput(**value)


class GateCandidate(Protocol):
    def decide(self, gate_input: GateInput) -> GateOutput: ...


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    """Evaluator-only annotations. This object must never cross into decide()."""
    question_id: str
    question: str
    expected_gate: str
    reason_code: str
    gold_support_sections: tuple[tuple[str, str, str], ...]
    required_support_sections: tuple[tuple[str, str, str], ...]

    def __post_init__(self):
        text(self.question_id, "question ID")
        text(self.question, "question")
        paired_reason(self.expected_gate, self.reason_code)
        require(self.reason_code is not None, "Gold reason required")
        for refs in (self.gold_support_sections, self.required_support_sections):
            require(type(refs) is tuple, "immutable support identities required")
            for ref in refs:
                identity(ref)
            require(len(set(refs)) == len(refs), "duplicate support identity")
        require(set(self.required_support_sections) <= set(self.gold_support_sections), "required not subset of Gold")
        if self.expected_gate == ALLOW:
            require(bool(self.required_support_sections) and bool(self.gold_support_sections), "empty ALLOW support")
        else:
            require(not self.required_support_sections and not self.gold_support_sections, "nonempty ABSTAIN support")


@dataclass(frozen=True, slots=True)
class RetrievalAssociation:
    """Evaluator-only binding, never passed to a gate."""
    question_id: str
    question_sha256: str
    result: FrozenRetrievalResult

    def __post_init__(self):
        text(self.question_id, "question ID")
        digest(self.question_sha256)
        require(type(self.result) is FrozenRetrievalResult, "typed frozen result required")


@dataclass(frozen=True, slots=True)
class CandidateObservation:
    question_id: str
    output: object = None
    error: str | None = None

    def __post_init__(self):
        text(self.question_id, "question ID")
        require(self.error is None or self.error in ("CANDIDATE_EXCEPTION", "MALFORMED_OUTPUT"),
                "unknown candidate error")
        require(self.error is None or self.output is None, "error cannot also have an output")
