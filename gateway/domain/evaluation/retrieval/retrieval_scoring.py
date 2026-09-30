"""Split-neutral scoring with the frozen Phase 2C metric definitions.

Only validation and the per-question scorer are reproduced here. The pure
aggregate and failure functions are reused unchanged from the historical module.
The DEVELOPMENT parity tests protect both the metrics and diagnostic wording.
"""
from evaluation.retrieval.evaluate_development import (
    COVERAGE_DEPTHS, FULL_SET_DEPTHS, TOP_K, aggregate_metrics, failure_observations,
)
from retrieval.section_store import section_identity


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_scoring_question(question):
    require(isinstance(question, dict) and question.get("split") in ("DEVELOPMENT", "HELD_OUT"), "Invalid scoring split")
    require(question.get("example_only") is False, "Examples cannot be scored")
    require(question.get("kind") in ("ANSWERABLE", "NEGATIVE"), "Unknown question kind")
    require(isinstance(question.get("question"), str) and bool(question["question"].strip()), "Question text is required")
    gold = tuple(section_identity(ref) for ref in question["gold_sections"])
    required = tuple(section_identity(ref) for ref in question["required_sections"])
    require(len(gold) == len(set(gold)) and len(required) == len(set(required)), "Duplicate relevance/required identities")
    require(set(required) <= set(gold), "Required sections must be a subset of Gold relevance")
    if question["kind"] == "NEGATIVE":
        require(not gold and not required, "Negative questions must not have fabricated sections")
    else:
        require(bool(gold) and bool(required), "Answerable questions require relevant and required sections")


def score_question(question, response):
    """First unique identities, maximum depth ten; relevance is not coverage."""
    validate_scoring_question(question)
    require(response.status in ("RETRIEVED", "ABSTAIN"), "Unexpected retrieval status")
    require(not response.abstained or not response.results, "Abstention cannot return support records")
    require(response.abstained or bool(response.results), "Retrieved status requires results")
    unique = {}
    for record in response.results:
        identity = section_identity(record.identity)
        unique.setdefault(identity, record)
    ranked = list(unique.items())[:TOP_K]
    identities = [identity for identity, _ in ranked]
    gold = [section_identity(ref) for ref in question["gold_sections"]]
    required = [section_identity(ref) for ref in question["required_sections"]]
    first = next((rank for rank, identity in enumerate(identities, 1) if identity in gold), None)
    answerable = question["kind"] == "ANSWERABLE"
    return {
        "question_id": question["question_id"], "kind": question["kind"], "query": question["question"],
        "ranked_sections": [dict(identity=identity, rank=rank, score=record.score,
                                  retrieval_method=record.retrieval_method, content_hash=record.content_hash,
                                  source_path=record.source_path) for rank, (identity, record) in enumerate(ranked, 1)],
        "gold_sections": gold, "required_sections": required, "first_relevant_rank": first,
        "hit_at_1": first == 1 if answerable else None,
        "hit_at_3": first is not None and first <= 3 if answerable else None,
        "reciprocal_rank_at_10": (1 / first if first is not None else 0.0) if answerable else None,
        "required_coverage_at_k": {str(k): {"retrieved": len(set(identities[:k]) & set(required)),
            "total": len(required), "fraction": len(set(identities[:k]) & set(required)) / len(required)}
            for k in COVERAGE_DEPTHS} if answerable else None,
        "multi_required_section_question": len(required) > 1,
        "full_required_set_success_at_k": {str(k): set(required) <= set(identities[:k]) for k in FULL_SET_DEPTHS} if answerable else None,
        "abstained": response.abstained, "abstention_reason": response.abstention_reason,
        "top_score": response.top_score,
        "negative_correctness": response.abstained if not answerable else None,
        "negative_false_support": not response.abstained if not answerable else None,
    }
