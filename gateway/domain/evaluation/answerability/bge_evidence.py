"""Strict stored BGE evidence, B1.1 reconstruction and retrieval-only diagnostics."""
from dataclasses import asdict, dataclass
from fractions import Fraction
import math

from .answerability_contracts import (
    ActiveBundle, FrozenRetrievalResult, RankedEvidence, identity, make_gate_input, require,
)
from .answerability_scoring import deterministic_json_bytes, metric
from .development_loader import IDS, MANIFEST_SHA256, RECEIPT, sha256
from ...retrieval.section_store import section_content_hash

MODEL = "BAAI/bge-small-en-v1.5"
REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
FROZEN_CONFIGURATION = {
    "retrieval_method": "EMBEDDING_COSINE", "model_id": MODEL,
    "model_selection": "Owner-frozen repository-configured model; one model only",
    "device": "cpu", "normalize_embeddings": True,
    "similarity": "normalized dot product; math.fsum over unit vectors",
    "top_k": 10, "section_count": 25,
    "searchable_fields": ["title", "section_title", "text"], "field_joiner": "LF",
    "query_transformation": "none; original question text", "query_instruction": "",
    "document_instruction": "", "pooling": "unmodified model snapshot configuration",
    "encode_batch_size": 32, "encode_precision": "float32", "cpu_threads": 1,
    "vector_validation": "finite nonzero rows; L2 normalize in Python float precision",
    "abstention": {"minimum_top_score": 0.30, "comparison": "top_score < threshold",
                   "also_abstain": ["blank query"], "margin": None},
    "candidate_filter": "all sections; threshold applies to top score for the whole response",
    "tie_breaking": "score descending, then (policy_id, version, section_id) ascending; no rounding",
    "score_meaning": "retrieval diagnostic; not confidence, probability, authority or business readiness",
}


def validate_configuration(config, revision, dimension):
    # Deterministic bytes distinguish bool/int and preserve the recorded numeric representation.
    require(deterministic_json_bytes(config) == deterministic_json_bytes(FROZEN_CONFIGURATION),
            "frozen BGE configuration differs")
    require(revision == REVISION, "wrong model revision")
    require(type(dimension) is int and dimension == 384, "wrong embedding dimension")


@dataclass(frozen=True, slots=True)
class Query:
    """External association only; search receives text and top_k, not this envelope."""
    question_id: str
    text: str
    file_sha256: str


def validate_queries(queries):
    require(type(queries) is tuple and all(type(q) is Query for q in queries), "typed query tuple required")
    require(tuple(q.question_id for q in queries) == IDS, "exact ordered AQ001-AQ040 required")


def exact_keys(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), f"invalid {label} fields")


def section_map(store):
    sections = {s.identity: s for s in store.sections}
    require(len(sections) == len(store.sections) == 25, "exactly 25 unique sections required")
    return sections


def capture_response(query, response, sections):
    """Copy actual result text/hash/score unchanged; titles come from the same verified record."""
    results = []
    for item in response.results:
        require(item.identity in sections, "unknown returned section identity")
        section = sections[item.identity]
        require(item.retrieval_method == "EMBEDDING_COSINE" and item.source_path == section.source_path,
                "unexpected result provenance")
        results.append({"rank": item.rank, "policy_id": item.identity[0], "version": item.identity[1],
                        "section_id": item.identity[2], "document_title": section.title,
                        "section_title": section.section_title, "section_body": item.text,
                        "cosine_score": item.score, "section_content_sha256": item.content_hash})
    return {"question_id": query.question_id, "question": query.text,
            "question_text_sha256": sha256(query.text.encode("utf-8")), "question_file_sha256": query.file_sha256,
            "retrieval_status": response.status, "result_count": len(response.results),
            "top_score": response.top_score, "retriever_abstention_reason": response.abstention_reason,
            "results": results}


def reconstruct_gate_input(row, query, bundle, sections):
    """Validate stored response, then explicitly build the existing B1.1 allowlist. No candidate call."""
    exact_keys(row, ("question_id", "question", "question_text_sha256", "question_file_sha256",
                     "retrieval_status", "result_count", "top_score", "retriever_abstention_reason", "results"), "question")
    require(row["question_id"] == query.question_id and row["question"] == query.text,
            "question association/text differs")
    require(row["question_text_sha256"] == sha256(query.text.encode("utf-8"))
            and row["question_file_sha256"] == query.file_sha256, "question hash binding differs")
    require(type(row["results"]) is list and len(row["results"]) <= 10, "invalid result depth")
    require(type(row["result_count"]) is int and row["result_count"] == len(row["results"]), "result count differs")
    top = row["top_score"]
    require(type(top) in (int, float) and math.isfinite(top) and -1 <= top <= 1, "invalid top score")
    ranked = []
    for item in row["results"]:
        exact_keys(item, ("rank", "policy_id", "version", "section_id", "document_title", "section_title",
                          "section_body", "cosine_score", "section_content_sha256"), "ranked result")
        canonical = identity((item["policy_id"], item["version"], item["section_id"]))
        require(canonical in sections, "unknown section identity")
        section = sections[canonical]
        require((item["document_title"], item["section_title"], item["section_body"]) ==
                (section.title, section.section_title, section.text), "section text/title differs from corpus")
        require(item["section_content_sha256"] == section.content_hash ==
                section_content_hash(*canonical, item["section_title"], item["section_body"]),
                "section content hash mismatch")
        ranked.append(RankedEvidence(item["rank"], *canonical, item["document_title"], item["section_title"],
                                     item["section_body"], item["cosine_score"]))
    if ranked:
        require(row["retrieval_status"] == "RETRIEVED" and row["retriever_abstention_reason"] is None,
                "nonempty response status/reason inconsistent")
        require(top == ranked[0].cosine_score, "top_score differs from rank 1")
    else:
        require(row["retrieval_status"] == "ABSTAIN", "empty response must record retriever abstention")
        if query.text.strip():
            require(top < 0.30 and row["retriever_abstention_reason"] == "TOP_SCORE_BELOW_THRESHOLD",
                    "invalid threshold abstention metadata")
        else:
            require(top == 0.0 and row["retriever_abstention_reason"] == "EMPTY_QUERY", "invalid blank-query metadata")
    return make_gate_input(query.text, FrozenRetrievalResult(tuple(ranked), bundle))


def make_package(rows, bundle):
    return {"schema_version": "answerability-development-bge-evidence-v0",
            "development_manifest_sha256": MANIFEST_SHA256, "development_receipt": RECEIPT,
            "configuration": FROZEN_CONFIGURATION, "model_revision": REVISION, "embedding_dimension": 384,
            "active_bundle": asdict(bundle), "questions": rows}


def validate_package(package, queries, store, bundle):
    validate_queries(queries)
    exact_keys(package, ("schema_version", "development_manifest_sha256", "development_receipt", "configuration",
                         "model_revision", "embedding_dimension", "active_bundle", "questions"), "evidence package")
    require(package["schema_version"] == "answerability-development-bge-evidence-v0", "unknown evidence schema")
    require(package["development_manifest_sha256"] == MANIFEST_SHA256
            and package["development_receipt"] == RECEIPT, "wrong DEVELOPMENT custody")
    validate_configuration(package["configuration"], package["model_revision"], package["embedding_dimension"])
    require(package["active_bundle"] == asdict(bundle), "active authority differs")
    require(ActiveBundle(**package["active_bundle"]) == bundle, "invalid active metadata")
    rows = package["questions"]
    require(type(rows) is list and len(rows) == 40, "40 question results required")
    require(all(type(row) is dict for row in rows), "question result objects required")
    require(tuple(row.get("question_id") for row in rows) == IDS, "missing/duplicate/unknown or unordered question ID")
    sections = section_map(store)
    return tuple(reconstruct_gate_input(row, query, bundle, sections) for row, query in zip(rows, queries))


def retrieval_metrics(cases, package):
    """Gold is consulted only after retrieval; no gate decisions/accuracy/eligibility."""
    require(len(cases) == 40 and tuple(c.question_id for c in cases) == IDS, "invalid scoring inventory")
    rows = package["questions"]
    require(tuple(r["question_id"] for r in rows) == IDS, "invalid response inventory")
    allows = [(c, r) for c, r in zip(cases, rows) if c.expected_gate == "ALLOW"]
    abstains = [r for c, r in zip(cases, rows) if c.expected_gate == "ABSTAIN"]
    require(len(allows) == len(abstains) == 20, "fixed 20/20 denominators required")
    multi = sum(len(c.required_support_sections) > 1 for c, _ in allows)
    require(multi > 0, "multi-required denominator cannot be zero")
    ranked = [(c, tuple((e["policy_id"], e["version"], e["section_id"]) for e in r["results"])) for c, r in allows]
    metrics = {f"hit_at_{k}": metric(sum(bool(set(ids[:k]) & set(c.gold_support_sections)) for c, ids in ranked), 20)
               for k in (1, 3)}
    reciprocal = [next((Fraction(1, rank) for rank, ref in enumerate(ids[:10], 1)
                        if ref in c.gold_support_sections), Fraction()) for c, ids in ranked]
    metrics["mrr_at_10"] = metric(sum(reciprocal, Fraction()), 20)
    for k in (3, 5, 10):
        found = [len(set(ids[:k]) & set(c.required_support_sections)) for c, ids in ranked]
        metrics[f"required_macro_coverage_at_{k}"] = metric(
            sum((Fraction(n, len(c.required_support_sections)) for n, (c, _) in zip(found, ranked)), Fraction()), 20)
        metrics[f"required_micro_coverage_at_{k}"] = metric(sum(found), sum(len(c.required_support_sections) for c, _ in ranked))
        metrics[f"multi_required_full_at_{k}"] = metric(sum(
            len(c.required_support_sections) > 1 and set(c.required_support_sections) <= set(ids[:k]) for c, ids in ranked), multi)
    def diagnostics(items):
        return {"question_count": len(items), "retriever_abstention_count": sum(r["retrieval_status"] == "ABSTAIN" for r in items),
                "returned_evidence_response_count": sum(r["retrieval_status"] == "RETRIEVED" for r in items)}
    return {"label": "RETRIEVAL DIAGNOSTICS ONLY; NOT ANSWERABILITY-GATE ACCURACY",
            "gold_allow_count": 20, "gold_abstain_count": 20, "allow_retrieval": metrics,
            "overall_response_diagnostics": diagnostics(rows), "gold_abstain_response_diagnostics": diagnostics(abstains)}
