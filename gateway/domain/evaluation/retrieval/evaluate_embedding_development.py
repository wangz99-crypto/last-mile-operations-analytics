"""Phase 2D: one owner-frozen model, original queries, pinned DEVELOPMENT only."""
import json
from pathlib import Path
import subprocess
import sys

# Support both the direct script and module entry points without a new input CLI.
if __package__:
    from . import evaluate_development as baseline
else:
    import evaluate_development as baseline
from retrieval.embedding_retriever import EmbeddingRetriever, MODEL_ID, configuration

OUTPUT = baseline.REPOSITORY / "artifacts/retrieval_dev_embedding_baseline"
HISTORY = baseline.REPOSITORY / "artifacts/retrieval_dev_lexical_baseline"
SOURCE_PATHS = (
    "gateway/domain/retrieval/embedding_retriever.py",
    "gateway/domain/evaluation/retrieval/evaluate_embedding_development.py",
    "gateway/domain/retrieval/section_store.py", "gateway/domain/retrieval/exact_retriever.py",
    "gateway/domain/retrieval/lexical_retriever.py", "gateway/domain/retrieval/__init__.py",
    "gateway/domain/evaluation/retrieval/evaluate_development.py", "gateway/domain/validate_contracts.py",
    "gateway/requirements-embeddings.txt",
)


def load_history(directory=HISTORY):
    """Read only the three named public DEVELOPMENT BM25 artifacts."""
    blobs = {name: (directory / name).read_bytes() for name in (
        "DEVELOPMENT_RESULTS.json", "DEVELOPMENT_REPORT.md", "RUN_MANIFEST.json")}
    result = baseline.read_json_bytes(blobs["DEVELOPMENT_RESULTS.json"])
    manifest = baseline.read_json_bytes(blobs["RUN_MANIFEST.json"])
    baseline.require(result["evaluation_type"] == "DEVELOPMENT_LEXICAL_BASELINE"
                     and result["development_receipt_sha256"] == baseline.EXPECTED_RECEIPT,
                     "Historical BM25 result must use the same frozen Development set")
    baseline.require(result["configuration"] == baseline.configuration(top_k=10), "Historical BM25 configuration differs")
    for name in ("DEVELOPMENT_RESULTS.json", "DEVELOPMENT_REPORT.md"):
        baseline.require(baseline.sha256(blobs[name]) == manifest["output_sha256"][name], "Historical BM25 artifact hash differs")
    metrics = result["metrics"]
    baseline.require((metrics["answerable_count"], metrics["negative_count"], metrics["hit_at_1"]["count"],
                      metrics["hit_at_3"]["count"], metrics["negative_correct_abstention"]["count"]) == (14, 1, 11, 11, 0)
                     and abs(metrics["mrr_at_10"] - 0.7928571428571428) < 1e-12,
                     "Historical BM25 metrics differ from the frozen baseline")
    return metrics, {name: baseline.sha256(blob) for name, blob in blobs.items()}


def evaluate(development, retriever):
    # Reuse all Phase 2C custody checks, query-only calls, scoring, aggregates and
    # failure semantics. Only method metadata changes; BM25 is never executed.
    result = baseline.evaluate(development, retriever)
    result.update(evaluation_type="DEVELOPMENT_EMBEDDING_BASELINE", configuration=configuration(),
                  runtime=retriever.runtime_metadata)
    return result


def report_markdown(result):
    m, old = result["metrics"], result["historical_bm25_metrics"]
    lines = ["# Phase 2D DEVELOPMENT embedding baseline", "",
        "DEVELOPMENT only: the same frozen 15 questions and 25 stable SOP sections as Phase 2C.",
        "No HELD_OUT question/result was accessed and no HELD_OUT evaluation occurred.",
        "This is a baseline, not an improvement claim; it awaits owner review.",
        "The model, original-query encoding, fields, normalization and 0.30 threshold were frozen before seeing Phase 2D results.",
        "No model sweep, threshold sweep, query instruction, query rewriting or post-result tuning was performed.",
        "Cosine similarity is a retrieval diagnostic, not confidence, probability, policy authority or business readiness.", "",
        f"Verified DEVELOPMENT receipt: `{result['development_receipt_sha256']}`.",
        f"Model: `{MODEL_ID}`, matching the repository configuration and the owner's explicit selection.", "",
        "## Comparison with untouched BM25 v0", "",
        "BM25 values below are read from historical Phase 2C artifacts; BM25 was not rerun or retuned for this comparison.",
        "ANSWERABLE denominator: 14. NEGATIVE denominator: 1. Multi-required denominator: 3.", "",
        "| Metric | BM25 v0 | Embedding baseline |", "| --- | --- | --- |"]
    for key, label in (("hit_at_1", "Hit@1"), ("hit_at_3", "Hit@3"),
                       ("negative_correct_abstention", "Negative correct abstention"), ("negative_false_support", "Negative false support")):
        def display(v):
            return f"{v['count']}/{v['total']} ({v['rate']:.6f})"
        lines.append(f"| {label} | {display(old[key])} | {display(m[key])} |")
    lines.append(f"| MRR@10 | {old['mrr_at_10']:.6f} | {m['mrr_at_10']:.6f} |")
    for k in baseline.COVERAGE_DEPTHS:
        a, b = old["required_coverage_at_k"][str(k)], m["required_coverage_at_k"][str(k)]
        lines.append(f"| Required coverage@{k}, macro | {a['macro_average']:.6f} | {b['macro_average']:.6f} |")
        lines.append(f"| Required coverage@{k}, micro | {display(a['micro'])} | {display(b['micro'])} |")
    for k in baseline.FULL_SET_DEPTHS:
        lines.append(f"| Multi-required full set@{k} | {display(old['full_required_set_success_at_k'][str(k)])} | {display(m['full_required_set_success_at_k'][str(k)])} |")
    lines += ["", "The single negative observation is not a general safety estimate. These Development results do not establish held-out superiority.",
        "", "## Per-question metrics", "",
        "| ID | Kind | First relevant rank | Hit@1 | Hit@3 | RR@10 | Abstained |",
        "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in result["questions"]:
        lines.append(f"| {row['question_id']} | {row['kind']} | {row['first_relevant_rank']} | {row['hit_at_1']} | {row['hit_at_3']} | {row['reciprocal_rank_at_10']} | {row['abstained']} |")
    lines += ["", "Every ranking, unrounded cosine score, Gold/required identity, coverage metric, abstention reason and negative outcome is retained in DEVELOPMENT_RESULTS.json.",
        "", "## Failures", "",
        "All missed reported targets are retained using the unchanged Phase 2C failure rubric.",
        "Partial top-1 required coverage is unavoidable for multi-required questions and is not by itself a ranking defect."]
    for failure in result["failures"]:
        lines += ["", "### " + failure["question_id"], ""] + ["- " + note for note in failure["observations"]]
    lines += ["", "## Frozen configuration", "", "```json", json.dumps(result["configuration"], indent=2, sort_keys=True), "```",
        "", "## Runtime identity and reproducibility", "", "```json", json.dumps(result["runtime"], indent=2, sort_keys=True), "```", "",
        "Only the 25 sections are embedded, once per retriever instance, in canonical identity order. Queries are encoded independently.",
        "There is no extra chunking, vector database, IT corpus, metadata keyword injection or automatic exact-lookup substitution.",
        "The model's own tokenizer/pooling and sequence-length limit are retained. Input strings receive no application-level query transformation.",
        "Model revision/file hashes and runtime versions identify this run; full cross-runtime byte-level reproducibility is not claimed.",
        "The base commit does not contain the uncommitted candidate: RUN_MANIFEST.json records source hashes and output hashes separately.",
        "Phase 2C inputs, implementation and historical artifacts remain unchanged. Stop for owner review after this first valid baseline.", ""]
    return "\n".join(lines)


def write_artifacts(result, development, store, historical_hashes, output=OUTPUT):
    # Recheck custody after encoding and before freezing outputs.
    current = baseline.load_development()
    baseline.require((current.receipt, current.manifest_sha256, current.question_hashes) ==
                     (development.receipt, development.manifest_sha256, development.question_hashes),
                     "Development inputs changed during evaluation")
    _, current_history = load_history()
    baseline.require(current_history == historical_hashes, "Phase 2C artifacts changed during evaluation")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=baseline.REPOSITORY).decode().strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=baseline.REPOSITORY).decode().strip()
    result_bytes = baseline.json_bytes(result)
    report_bytes = report_markdown(result).encode("utf-8")
    manifest = {
        "run_type": "DEVELOPMENT_EMBEDDING_BASELINE", "configuration_status": "CANDIDATE_AWAITING_OWNER_REVIEW",
        "baseline_run_sequence": 1, "completed_evaluation_attempts": 1,
        "question_attempts": {identity: 1 for identity in baseline.QUESTION_IDS}, "success_count": 15, "error_count": 0,
        "configuration_frozen_before_results": True, "configuration": result["configuration"], "runtime": result["runtime"],
        "code_commit": commit, "code_commit_scope": "Base commit; uncommitted candidate identified by source_file_sha256",
        "git_status_at_evaluation": status,
        "source_file_sha256": {p: baseline.sha256((baseline.REPOSITORY / p).read_bytes()) for p in SOURCE_PATHS},
        "development_receipt_verified": True, "development_receipt_sha256": development.receipt,
        "receipt_serialization": baseline.SERIALIZATION, "development_manifest_sha256": development.manifest_sha256,
        "question_sha256": dict(development.question_hashes), "question_ids": list(baseline.QUESTION_IDS),
        "document_count": store.document_count, "section_count": store.section_count, "versions": store.versions,
        "section_content_hashes": [{"identity": s.identity, "content_hash": s.content_hash}
                                   for s in sorted(store.sections, key=lambda s: s.identity)],
        "artifact_manifest_sha256": baseline.sha256((baseline.DOMAIN / "policy/artifact_manifest.json").read_bytes()),
        "historical_bm25_artifact_sha256": historical_hashes, "historical_bm25_unchanged": True,
        "output_sha256": {"DEVELOPMENT_RESULTS.json": baseline.sha256(result_bytes), "DEVELOPMENT_REPORT.md": baseline.sha256(report_bytes)},
        "held_out_accessed": False, "held_out_evaluated": False,
        "model_search_performed": False, "threshold_search_performed": False, "post_result_tuning_performed": False,
        "query_instruction_added": False, "implementation_bug_rerun": False,
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, content in (("DEVELOPMENT_RESULTS.json", result_bytes), ("DEVELOPMENT_REPORT.md", report_bytes),
                          ("RUN_MANIFEST.json", baseline.json_bytes(manifest))):
        with (output / name).open("xb") as stream:
            stream.write(content)


def main():
    if len(sys.argv) != 1:
        raise SystemExit("This evaluator accepts no arguments; only the pinned Development import is allowed")
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite existing Development embedding artifacts: {OUTPUT}")
    development = baseline.load_development()
    historical_metrics, historical_hashes = load_history()
    store = baseline.SectionStore.load()
    baseline.require((store.document_count, store.section_count, store.versions) == (8, 25, ("1.0-demo",)), "Unexpected active corpus")
    print("Frozen Phase 2D configuration before model initialization or Development evaluation:", flush=True)
    print(json.dumps(configuration(), indent=2, sort_keys=True), flush=True)
    retriever = EmbeddingRetriever(store)
    result = evaluate(development, retriever)
    result["historical_bm25_metrics"] = historical_metrics
    write_artifacts(result, development, store, historical_hashes)
    print(json.dumps(result["metrics"], indent=2, sort_keys=True))
    print("Development failure IDs: " + ", ".join(row["question_id"] for row in result["failures"]))
    print(f"First baseline frozen for owner review. Artifacts: {OUTPUT}")


if __name__ == "__main__":
    main()
