"""Phase 2E: fixed equal-weight RRF over the authorized DEVELOPMENT import."""
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

if __package__:
    from . import evaluate_embedding_development as phase2d
else:
    import evaluate_embedding_development as phase2d
baseline = phase2d.baseline
from retrieval import LexicalRetriever, SectionStore
from retrieval.embedding_retriever import EmbeddingRetriever, SentenceTransformerBackend, configuration as embedding_configuration
from retrieval.hybrid_rrf_retriever import HybridRRFRetriever, configuration

BGE_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
OUTPUT = baseline.REPOSITORY / "artifacts/retrieval_dev_hybrid_rrf_baseline"
SOURCE_PATHS = phase2d.SOURCE_PATHS + (
    "gateway/domain/retrieval/hybrid_rrf_retriever.py",
    "gateway/domain/evaluation/retrieval/evaluate_hybrid_development.py",
    "gateway/domain/tests/test_hybrid_rrf_retrieval.py",
    "gateway/domain/tests/test_hybrid_development_evaluation.py",
    "gateway/domain/retrieval/README.md", ".gitattributes",
)


def expected_embedding_metrics():
    rate = baseline.rate
    return {
        "answerable_count": 14, "negative_count": 1, "multi_required_question_count": 3,
        "hit_at_1": rate(9, 14), "hit_at_3": rate(12, 14), "mrr_at_10": 0.7767857142857143,
        "required_coverage_at_k": {str(k): {"macro_average": macro, "micro": rate(count, 17)}
            for k, macro, count in ((1, 0.5357142857142857, 9), (3, 0.8571428571428571, 15),
                                    (5, 0.9285714285714286, 16), (10, 1.0, 17))},
        "full_required_set_success_at_k": {str(k): rate(3, 3) for k in (3, 5, 10)},
        "negative_correct_abstention": rate(0, 1), "negative_false_support": rate(1, 1),
    }


def load_history(lexical_directory=phase2d.HISTORY, embedding_directory=phase2d.OUTPUT):
    """Verify only the six named, tracked DEVELOPMENT artifacts; never discover files."""
    bm25_metrics, bm25_hashes = phase2d.load_history(lexical_directory)
    blobs = {name: (embedding_directory / name).read_bytes() for name in (
        "DEVELOPMENT_RESULTS.json", "DEVELOPMENT_REPORT.md", "RUN_MANIFEST.json")}
    result = baseline.read_json_bytes(blobs["DEVELOPMENT_RESULTS.json"])
    manifest = baseline.read_json_bytes(blobs["RUN_MANIFEST.json"])
    baseline.require(manifest["historical_bm25_artifact_sha256"] == bm25_hashes, "Phase 2C hashes differ from Phase 2D history")
    for name in ("DEVELOPMENT_RESULTS.json", "DEVELOPMENT_REPORT.md"):
        baseline.require(baseline.sha256(blobs[name]) == manifest["output_sha256"][name], "Phase 2D historical artifact hash differs")
    baseline.require(result["evaluation_type"] == manifest["run_type"] == "DEVELOPMENT_EMBEDDING_BASELINE",
                     "Unexpected Phase 2D historical method")
    baseline.require(result["development_receipt_sha256"] == manifest["development_receipt_sha256"] == baseline.EXPECTED_RECEIPT,
                     "Historical embedding DEVELOPMENT receipt differs")
    baseline.require(result["configuration"] == manifest["configuration"] == embedding_configuration(),
                     "Historical embedding configuration differs")
    runtime = manifest["runtime"]
    baseline.require(result["runtime"] == runtime and runtime["requested_model_id"] == "BAAI/bge-small-en-v1.5"
                     and runtime["resolved_model_revision"] == BGE_REVISION and runtime["device"] == "cpu"
                     and runtime["normalize_embeddings"] is True and runtime["query_instruction"] == "",
                     "Historical BGE model/revision/runtime differs")
    baseline.require(result["metrics"] == expected_embedding_metrics(), "Historical Phase 2D metrics differ")
    return {
        "metrics": {"bm25": bm25_metrics, "embedding": result["metrics"]},
        "artifact_sha256": {"bm25": bm25_hashes, "embedding": {name: baseline.sha256(blob) for name, blob in blobs.items()}},
        "embedding_runtime": runtime,
    }


def build_retriever(store, history):
    # No unconstrained main revision, network fallback or substitute model. A
    # missing exact snapshot stops this run before any Development search.
    backend = SentenceTransformerBackend(revision=BGE_REVISION, local_files_only=True)
    runtime = backend.metadata
    baseline.require(runtime["requested_revision"] == runtime["resolved_model_revision"] == BGE_REVISION,
                     "Exact Phase 2D BGE revision could not be loaded")
    baseline.require(runtime["model_file_sha256"] == history["embedding_runtime"]["model_file_sha256"],
                     "Loaded BGE file hashes differ from Phase 2D")
    for key in ("requested_model_id", "device", "embedding_dimension", "normalize_embeddings", "similarity",
                "pooling_configuration", "max_sequence_length", "query_instruction", "document_instruction", "cpu_threads"):
        baseline.require(runtime[key] == history["embedding_runtime"][key], f"BGE runtime configuration changed: {key}")
    lexical = LexicalRetriever(store)
    embedding = EmbeddingRetriever(store, encoder=backend)
    metadata = embedding.runtime_metadata
    metadata["model_id_is_not_a_repository_pinned_revision"] = False
    metadata["evaluation_revision_pinned"] = True
    metadata["reproducibility_limit"] = "This evaluation pins the exact model revision and verifies Phase 2D model-file hashes. Dependency versions are recorded but not all repository-pinned; byte-identical embeddings across arbitrary runtimes are not claimed."
    return HybridRRFRetriever(lexical, embedding), metadata


def evaluate(development, retriever, runtime):
    responses = []
    class RecordingSearch:
        def search(self, query, top_k):
            response = retriever.search(query, top_k=top_k)
            responses.append(response)
            return response
    # The existing evaluator validates custody before calling search, passes
    # only query/depth, and owns all scoring, aggregates and failure semantics.
    result = baseline.evaluate(development, RecordingSearch())
    result.update(evaluation_type="DEVELOPMENT_HYBRID_RRF_BASELINE", configuration=configuration(), runtime=runtime)
    for row, response in zip(result["questions"], responses):
        fused = {record.identity: record for record in response.results}
        for record in row["ranked_sections"]:
            source = fused[tuple(record["identity"])]
            record.update(bm25_rank=source.bm25_rank, embedding_rank=source.embedding_rank)
        row["component_statuses"] = {"bm25": response.bm25_status, "embedding": response.embedding_status}
        row["component_abstention_reasons"] = {"bm25": response.bm25_abstention_reason, "embedding": response.embedding_abstention_reason}
        row["component_rankings"] = {"bm25": [asdict(record) for record in response.bm25_results],
                                     "embedding": [asdict(record) for record in response.embedding_results]}
    return result


def report_markdown(result):
    systems = [result["historical_metrics"]["bm25"], result["historical_metrics"]["embedding"], result["metrics"]]
    def rate(value):
        return f"{value['count']}/{value['total']} ({value['rate']:.6f})"
    lines = ["# Phase 2E DEVELOPMENT equal-weight RRF baseline", "",
        "DEVELOPMENT only: 15 frozen questions (14 ANSWERABLE, 1 NEGATIVE) over the same verified 25 stable SOP sections.",
        "No HELD_OUT material was accessed or evaluated. One negative observation is not a safety estimate.",
        "RRF parameters were fixed before evaluation: k=60, weights 1.0/1.0, component depths 10/10, final top_k=10.",
        "No weight search, RRF-k search, model search, threshold tuning or post-result tuning was performed.",
        "Raw component scores are not fused. Original queries are passed to both components without an instruction or rewriting.",
        "RRF score is not confidence, probability, authority, evidence completeness, action state, priority or readiness.",
        "These are observed Development differences, not a claim that the hybrid is superior.", "",
        f"Verified DEVELOPMENT receipt: `{result['development_receipt_sha256']}`.",
        f"Exact BGE revision: `{BGE_REVISION}`. Historical results are verified read-only evidence; live components produce the hybrid ranks.", "",
        "## All frozen metrics", "", "| Metric | BM25 v0 | BGE embedding v0 | Equal-weight RRF hybrid v0 |",
        "| --- | --- | --- | --- |"]
    def table(label, values):
        lines.append("| " + label + " | " + " | ".join(values) + " |")
    for key, label in (("hit_at_1", "Hit@1"), ("hit_at_3", "Hit@3")):
        table(label, [rate(m[key]) for m in systems])
    table("MRR@10", [f"{m['mrr_at_10']:.6f}" for m in systems])
    for k in baseline.COVERAGE_DEPTHS:
        table(f"Required coverage@{k}, macro", [f"{m['required_coverage_at_k'][str(k)]['macro_average']:.6f}" for m in systems])
        table(f"Required coverage@{k}, micro", [rate(m["required_coverage_at_k"][str(k)]["micro"]) for m in systems])
    for k in baseline.FULL_SET_DEPTHS:
        table(f"Multi-required full set@{k}", [rate(m["full_required_set_success_at_k"][str(k)]) for m in systems])
    for key, label in (("negative_correct_abstention", "Negative correct abstention"), ("negative_false_support", "Negative false support")):
        table(label, [rate(m[key]) for m in systems])
    lines += ["", "The full-set denominator is the three questions with more than one required section.", "",
        "## Per-question diagnostics", "",
        "| ID | First relevant rank | Hit@1 | Hit@3 | RR@10 | Hybrid abstained | BM25 status | BGE status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in result["questions"]:
        lines.append(f"| {row['question_id']} | {row['first_relevant_rank']} | {row['hit_at_1']} | {row['hit_at_3']} | {row['reciprocal_rank_at_10']} | {row['abstained']} | {row['component_statuses']['bm25']} | {row['component_statuses']['embedding']} |")
    lines += ["", "DEVELOPMENT_RESULTS.json retains original queries, every fused identity and unrounded RRF score, both contributing ranks, full component top-10 rankings/statuses/reasons, Gold and required sections, all coverage metrics and negative outcomes.",
        "The component rank lists include candidates outside the final top 10 so movements remain inspectable without inferring hidden causes.", "",
        "## Failures", "", "All failures use the unchanged Phase 2C rubric. Partial top-1 coverage is unavoidable for multi-required questions and is not by itself a defect."]
    for failure in result["failures"]:
        lines += ["", "### " + failure["question_id"], ""] + ["- " + item for item in failure["observations"]]
    lines += ["", "## Frozen configuration", "", "```json", json.dumps(result["configuration"], indent=2, sort_keys=True), "```",
        "", "## Runtime identity", "", "```json", json.dumps(result["runtime"], indent=2, sort_keys=True), "```", "",
        "RUN_MANIFEST.json records historical artifact hashes, input and source hashes, the current base commit and frozen output hashes.",
        "Uncommitted candidate source is distinguished from the base commit. Cross-runtime byte-identical embedding vectors are not claimed.",
        "No new hybrid threshold, chunks, vector database or raw-score blending is used. Both components must abstain for hybrid abstention.",
        "Phase 2C/2D artifact bytes remain unchanged. Stop after this first valid baseline for owner review.", ""]
    return "\n".join(lines)


def write_artifacts(result, development, store, history, output=OUTPUT):
    current = baseline.load_development()
    baseline.require((current.receipt, current.manifest_sha256, current.question_hashes) ==
                     (development.receipt, development.manifest_sha256, development.question_hashes), "Development inputs changed")
    baseline.require(load_history()["artifact_sha256"] == history["artifact_sha256"], "Historical baseline artifact bytes changed")
    baseline.require(len(result["questions"]) == 15 and tuple(row["question_id"] for row in result["questions"]) == baseline.QUESTION_IDS,
                     "A complete first Development run is required")
    results_bytes = baseline.json_bytes(result)
    report_bytes = report_markdown(result).encode("utf-8")
    manifest = {
        "run_type": "DEVELOPMENT_HYBRID_RRF_BASELINE", "configuration_status": "CANDIDATE_AWAITING_OWNER_REVIEW",
        "baseline_run_sequence": 1, "completed_evaluation_attempts": 1,
        "question_attempts": {identity: 1 for identity in baseline.QUESTION_IDS}, "success_count": 15, "error_count": 0,
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=baseline.REPOSITORY).decode().strip(),
        "code_commit_scope": "Base commit; uncommitted candidate identified by source_file_sha256",
        "git_status_at_evaluation": subprocess.check_output(["git", "status", "--short"], cwd=baseline.REPOSITORY).decode().strip(),
        "source_file_sha256": {p: baseline.sha256((baseline.REPOSITORY / p).read_bytes()) for p in SOURCE_PATHS},
        "development_receipt_verified": True, "development_receipt_sha256": development.receipt,
        "development_manifest_sha256": development.manifest_sha256, "receipt_serialization": baseline.SERIALIZATION,
        "question_sha256": dict(development.question_hashes), "question_ids": list(baseline.QUESTION_IDS),
        "section_content_hashes": [{"identity": s.identity, "content_hash": s.content_hash} for s in sorted(store.sections, key=lambda s: s.identity)],
        "artifact_manifest_sha256": baseline.sha256((baseline.DOMAIN / "policy/artifact_manifest.json").read_bytes()),
        "document_count": store.document_count, "section_count": store.section_count, "versions": store.versions,
        "configuration_frozen_before_results": True, "configuration": result["configuration"],
        "component_configurations": {"bm25": baseline.configuration(top_k=10), "embedding": embedding_configuration()},
        "historical_bm25_artifact_sha256": history["artifact_sha256"]["bm25"],
        "historical_bge_artifact_sha256": history["artifact_sha256"]["embedding"], "historical_artifacts_unchanged": True,
        "bge_revision": BGE_REVISION, "runtime": result["runtime"],
        "output_sha256": {"DEVELOPMENT_RESULTS.json": baseline.sha256(results_bytes), "DEVELOPMENT_REPORT.md": baseline.sha256(report_bytes)},
        "held_out_accessed": False, "held_out_evaluated": False, "weight_search_performed": False,
        "rrf_k_search_performed": False, "threshold_search_performed": False, "model_search_performed": False,
        "post_result_tuning_performed": False, "implementation_bug_rerun": False,
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in (("DEVELOPMENT_RESULTS.json", results_bytes), ("DEVELOPMENT_REPORT.md", report_bytes), ("RUN_MANIFEST.json", baseline.json_bytes(manifest))):
        with (output / name).open("xb") as stream:
            stream.write(data)


def main():
    if len(sys.argv) != 1:
        raise SystemExit("This evaluator accepts no arguments; only the pinned DEVELOPMENT import is allowed")
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite existing RRF artifacts: {OUTPUT}")
    development = baseline.load_development()
    history = load_history()
    store = SectionStore.load()
    baseline.require((store.document_count, store.section_count, store.versions) == (8, 25, ("1.0-demo",)), "Unexpected active corpus")
    print("Frozen Phase 2E configuration before model initialization and evaluation:", flush=True)
    print(json.dumps(configuration(), indent=2, sort_keys=True), flush=True)
    retriever, runtime = build_retriever(store, history)
    result = evaluate(development, retriever, runtime)
    result["historical_metrics"] = history["metrics"]
    write_artifacts(result, development, store, history)
    print(json.dumps(result["metrics"], indent=2, sort_keys=True))
    print("Development failure IDs: " + ", ".join(row["question_id"] for row in result["failures"]))
    print(f"First RRF baseline frozen for owner review. Artifacts: {OUTPUT}")


if __name__ == "__main__":
    main()
