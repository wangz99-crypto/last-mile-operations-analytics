"""Phase 2C: only the pinned 15-question DEVELOPMENT import; no discovery CLI."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

DOMAIN = Path(__file__).resolve().parents[2]
REPOSITORY = DOMAIN.parent.parent
BASE = Path(__file__).resolve().parent
OUTPUT = REPOSITORY / "artifacts/retrieval_dev_lexical_baseline"
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from retrieval import LexicalRetriever, SectionStore
from retrieval.lexical_retriever import configuration
from retrieval.section_store import section_identity
from validate_contracts import validate_question

QUESTION_IDS = ("RQ003", "RQ006", "RQ009", "RQ012", "RQ015", "RQ016", "RQ019", "RQ022",
                "RQ025", "RQ026", "RQ029", "RQ032", "RQ035", "RQ038", "RQ041")
EXPECTED_RECEIPT = "4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00"
SERIALIZATION = "UTF-8; sorted question_id + TAB + lowercase file SHA-256 + LF; final LF included"
TOP_K = 10
COVERAGE_DEPTHS = (1, 3, 5, 10)
FULL_SET_DEPTHS = (3, 5, 10)


class DevelopmentIntegrityError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DevelopmentIntegrityError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_json_bytes(data):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid_constant(value):
        raise DevelopmentIntegrityError(f"Invalid JSON constant: {value}")
    return json.loads(data, object_pairs_hook=unique_keys, parse_constant=invalid_constant)


def development_receipt(question_hashes):
    payload = "".join(f"{identity}\t{digest}\n" for identity, digest in sorted(question_hashes.items()))
    return sha256(payload.encode("utf-8"))


@dataclass(frozen=True, slots=True)
class DevelopmentSet:
    questions: tuple[dict, ...]
    receipt: str
    manifest_sha256: str
    question_hashes: tuple[tuple[str, str], ...]


def _load_development(base):
    """No glob/rglob, manifest-directed paths, arbitrary split or recursive search."""
    base = Path(base)
    manifest_path = base / "DEVELOPMENT_MANIFEST.json"
    directory = base / "development"
    require(not base.is_symlink() and not manifest_path.is_symlink() and not directory.is_symlink(),
            "Development input paths may not be symlinks")
    manifest_bytes = manifest_path.read_bytes()
    manifest = read_json_bytes(manifest_bytes)
    require(manifest["split"] == "DEVELOPMENT", "Only DEVELOPMENT manifests are permitted")
    require(manifest["review_status"] == "OWNER_REVIEWED" and manifest["owner_reviewed"] is True
            and manifest["dataset_frozen"] is True, "Development set must be owner-reviewed and frozen")
    require(manifest["receipt_algorithm"] == "sha256" and manifest["receipt_serialization"] == SERIALIZATION,
            "Unexpected Development receipt algorithm or serialization")
    require(manifest["aggregate_receipt_sha256"] == EXPECTED_RECEIPT, "Unrecognized frozen Development receipt")
    require(manifest["policy_bundle_id"] == "last-mile-exception-triage-demo" and manifest["policy_version"] == "1.0-demo"
            and manifest["contract_version"] == "1.0", "Unexpected Development policy/contract context")
    rows = manifest["questions"]
    require(manifest["question_count"] == len(rows) == 15, "Expected exactly 15 Development records")
    require([row["question_id"] for row in rows] == list(QUESTION_IDS), "Unexpected Development question IDs or order")
    # Validate EVERY manifest path and split before opening ANY question file.
    for identity, row in zip(QUESTION_IDS, rows):
        require(row["split"] == "DEVELOPMENT", f"{identity}: only DEVELOPMENT records are permitted")
        require(row["filename"] == f"development/{identity}.json", f"{identity}: unapproved question path")
        require(isinstance(row["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]), "Invalid file SHA-256")
    require(sorted(p.name for p in directory.iterdir()) == [identity + ".json" for identity in QUESTION_IDS],
            "Development directory must contain exactly the 15 authorized files, without subdirectories")
    blobs, hashes = {}, {}
    for identity, row in zip(QUESTION_IDS, rows):
        path = directory / (identity + ".json")
        require(path.is_file() and not path.is_symlink() and path.resolve().parent == directory.resolve(),
                f"{identity}: question must be a direct regular file")
        blobs[identity] = path.read_bytes()
        hashes[identity] = sha256(blobs[identity])
        require(hashes[identity] == row["sha256"], f"{identity}: frozen file hash differs")
    receipt = development_receipt(hashes)
    require(receipt == EXPECTED_RECEIPT, "Frozen Development aggregate receipt differs")
    require(sha256((DOMAIN / "policy/artifact_manifest.json").read_bytes()) == manifest["source_artifact_manifest_sha256"],
            "Development source artifact manifest differs")
    questions = []
    for identity, row in zip(QUESTION_IDS, rows):
        question = read_json_bytes(blobs[identity])
        validate_development_question(question)
        validate_question(question, DOMAIN)
        require(question["question_id"] == identity and question["kind"] == row["kind"], "Question identity/kind differs from manifest")
        require(question["gold_policy_version"] == manifest["policy_version"], "Question policy version differs from manifest")
        questions.append(question)
    require(manifest["answerable_count"] == sum(q["kind"] == "ANSWERABLE" for q in questions) == 14
            and manifest["negative_count"] == sum(q["kind"] == "NEGATIVE" for q in questions) == 1,
            "Development kind counts differ")
    return DevelopmentSet(tuple(questions), receipt, sha256(manifest_bytes), tuple(hashes.items()))


def load_development(base=BASE):
    """The CLI always uses BASE. Alternate roots support isolated copied-fixture tests."""
    try:
        return _load_development(base)
    except DevelopmentIntegrityError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise DevelopmentIntegrityError(f"Invalid Development import: {exc}") from exc


def validate_development_question(question):
    require(isinstance(question, dict) and question.get("split") == "DEVELOPMENT", "Only DEVELOPMENT questions are permitted")
    require(question.get("example_only") is False, "Examples are not Development questions")
    require(question.get("kind") in ("ANSWERABLE", "NEGATIVE"), "Unknown question kind")
    require(isinstance(question.get("question"), str) and bool(question["question"].strip()), "Question text is required")
    gold = tuple(section_identity(ref) for ref in question["gold_sections"])
    required = tuple(section_identity(ref) for ref in question["required_sections"])
    require(len(gold) == len(set(gold)) and len(required) == len(set(required)), "Duplicate relevance/required identities")
    require(set(required) <= set(gold), "Required sections must be a subset of Gold relevance")
    if question["kind"] == "NEGATIVE":
        require(not gold and not required, "Negative questions must not have fabricated sections")
    else:
        require(bool(gold) and bool(required), "Answerable Development questions require relevant and required sections")


def score_question(question, response):
    """Pure metrics over first unique returned identities, at a maximum depth of 10."""
    validate_development_question(question)
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
    row = {
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
    return row


def rate(count, total):
    return {"count": count, "total": total, "rate": count / total if total else None}


def aggregate_metrics(rows):
    answerable = [row for row in rows if row["kind"] == "ANSWERABLE"]
    negative = [row for row in rows if row["kind"] == "NEGATIVE"]
    multi = [row for row in answerable if row["multi_required_section_question"]]
    n = len(answerable)
    return {
        "answerable_count": n, "negative_count": len(negative), "multi_required_question_count": len(multi),
        "hit_at_1": rate(sum(row["hit_at_1"] for row in answerable), n),
        "hit_at_3": rate(sum(row["hit_at_3"] for row in answerable), n),
        "mrr_at_10": sum(row["reciprocal_rank_at_10"] for row in answerable) / n if n else None,
        "required_coverage_at_k": {str(k): {
            "macro_average": sum(row["required_coverage_at_k"][str(k)]["fraction"] for row in answerable) / n if n else None,
            "micro": rate(sum(row["required_coverage_at_k"][str(k)]["retrieved"] for row in answerable),
                          sum(row["required_coverage_at_k"][str(k)]["total"] for row in answerable))}
            for k in COVERAGE_DEPTHS},
        "full_required_set_success_at_k": {str(k): rate(sum(row["full_required_set_success_at_k"][str(k)] for row in multi), len(multi))
                                            for k in FULL_SET_DEPTHS},
        "negative_correct_abstention": rate(sum(row["negative_correctness"] for row in negative), len(negative)),
        "negative_false_support": rate(sum(row["negative_false_support"] for row in negative), len(negative)),
    }


def failure_observations(row):
    if row["kind"] == "NEGATIVE":
        if row["negative_correctness"]:
            return []
        top = row["ranked_sections"][0]
        return [f"Unsupported negative query returned {top['identity']} with score {top['score']:.6f}; no abstention."]
    observations = []
    if row["abstained"]:
        observations.append(f"Answerable query abstained: {row['abstention_reason']}; top score {row['top_score']:.6f}.")
    elif not row["hit_at_1"]:
        observations.append(f"First relevant rank: {row['first_relevant_rank']}; top result {row['ranked_sections'][0]['identity']} is not Gold-relevant.")
    if not row["hit_at_3"]:
        observations.append("No Gold-relevant section within the first three unique results.")
    for k in COVERAGE_DEPTHS:
        coverage = row["required_coverage_at_k"][str(k)]
        if coverage["fraction"] < 1:
            returned = {tuple(item["identity"]) for item in row["ranked_sections"][:k]}
            missing = [identity for identity in row["required_sections"] if tuple(identity) not in returned]
            observations.append(f"Required coverage@{k}: {coverage['retrieved']}/{coverage['total']}; absent: {missing}.")
    return observations


def evaluate(development, retriever):
    require(development.receipt == EXPECTED_RECEIPT, "Evaluation requires the verified frozen Development receipt")
    require(tuple(q["question_id"] for q in development.questions) == QUESTION_IDS, "Evaluation requires exactly the 15 authorized IDs")
    for question in development.questions:
        validate_development_question(question)
    rows = []
    for question in development.questions:
        # The ranking API receives ONLY query text and fixed depth, never labels or rationale.
        response = retriever.search(question["question"], top_k=TOP_K)
        rows.append(score_question(question, response))
    return {
        "evaluation_type": "DEVELOPMENT_LEXICAL_BASELINE", "configuration_status": "CANDIDATE_AWAITING_OWNER_REVIEW",
        "development_receipt_sha256": development.receipt, "configuration": configuration(top_k=TOP_K),
        "metrics": aggregate_metrics(rows), "questions": rows,
        "failures": [{"question_id": row["question_id"], "observations": notes}
                     for row in rows if (notes := failure_observations(row))],
    }


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def report_markdown(result):
    m = result["metrics"]
    lines = ["# Phase 2C DEVELOPMENT lexical baseline", "",
        "Method-development results on 15 frozen DEVELOPMENT questions only. No HELD_OUT evaluation was performed.",
        "This is a baseline, not an AI improvement or business-accuracy claim. Configuration awaits owner review.", "",
        f"Verified Development receipt: `{result['development_receipt_sha256']}`.",
        "Corpus: 8 SOP documents / 25 stable sections / version 1.0-demo. Exact required lookup remains separate.", "",
        f"Hit@1: {m['hit_at_1']['count']}/{m['answerable_count']} ({m['hit_at_1']['rate']:.6f}).",
        f"Hit@3: {m['hit_at_3']['count']}/{m['answerable_count']} ({m['hit_at_3']['rate']:.6f}).",
        f"MRR@10: {m['mrr_at_10']:.6f} (ANSWERABLE denominator {m['answerable_count']}).", "",
        "| Depth | Required coverage, macro mean | Required coverage, micro count/rate |",
        "| --- | --- | --- |"]
    for k in COVERAGE_DEPTHS:
        coverage = m["required_coverage_at_k"][str(k)]
        micro = coverage["micro"]
        lines.append(f"| {k} | {coverage['macro_average']:.6f} | {micro['count']}/{micro['total']} ({micro['rate']:.6f}) |")
    lines += ["", f"Full required-set success uses only the {m['multi_required_question_count']} questions with more than one required section."]
    for k in FULL_SET_DEPTHS:
        value = m["full_required_set_success_at_k"][str(k)]
        lines.append(f"- Top {k}: {value['count']}/{value['total']} ({value['rate']:.6f}).")
    a, f = m["negative_correct_abstention"], m["negative_false_support"]
    lines += ["", f"NEGATIVE correct abstention: {a['count']}/{a['total']} ({a['rate']:.6f}).",
              f"NEGATIVE false-support rate: {f['count']}/{f['total']} ({f['rate']:.6f}).",
              "The single negative case provides only one Development observation, not a general safety estimate.", "",
              "## Per-question metrics", "", "| ID | Kind | First relevant rank | Hit@1 | Hit@3 | RR@10 | Abstained |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in result["questions"]:
        lines.append(f"| {row['question_id']} | {row['kind']} | {row['first_relevant_rank']} | {row['hit_at_1']} | {row['hit_at_3']} | {row['reciprocal_rank_at_10']} | {row['abstained']} |")
    lines += ["", "Full ranked identities, scores, Gold relevance and required-set metrics are in DEVELOPMENT_RESULTS.json.", "",
              "## Observed failures", "",
              "Every missed reported target is listed: Hit@1/3, complete required coverage at any reported depth, or negative abstention.",
              "Partial top-1 coverage is unavoidable for multi-required questions; it is recorded without implying a ranking defect.",
              "Descriptions report returned ranks and absent sections, without inferring hidden causes."]
    for failure in result["failures"]:
        lines += ["", "### " + failure["question_id"], ""] + ["- " + note for note in failure["observations"]]
    lines += ["", "## Configuration freeze candidate", "",
              "The fixed defaults were selected before running this evaluation; no search over parameters or post-result tuning was performed.",
              "Searchable fields are readable document title, readable section title and section body, each once, with no metadata keyword boosts.",
              "Scores are lexical retrieval diagnostics, not business confidence. No stemming, synonyms, embeddings, models or query rewriting.",
              "", "```json", json.dumps(result["configuration"], indent=2, sort_keys=True), "```", "",
              "RUN_MANIFEST.json records the base code commit, uncommitted-code qualification, source hashes and output hashes.",
              "Owner review is required before treating this configuration as final. No HELD_OUT question or result was accessed.", ""]
    return "\n".join(lines)


def write_artifacts(result, development, store, output=OUTPUT):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY).decode().strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=REPOSITORY).decode().strip()
    code_paths = ("gateway/domain/retrieval/lexical_retriever.py", "gateway/domain/retrieval/section_store.py",
                  "gateway/domain/retrieval/exact_retriever.py", "gateway/domain/retrieval/__init__.py",
                  "gateway/domain/evaluation/retrieval/evaluate_development.py", "gateway/domain/validate_contracts.py")
    results_bytes = json_bytes(result)
    report_bytes = report_markdown(result).encode("utf-8")
    manifest = {
        "run_type": "DEVELOPMENT_LEXICAL_BASELINE", "configuration_status": "CANDIDATE_AWAITING_OWNER_REVIEW",
        "code_commit": commit, "code_commit_scope": "Base commit; uncommitted candidate code is identified by source_file_sha256",
        "git_status_at_evaluation": status, "source_file_sha256": {p: sha256((REPOSITORY / p).read_bytes()) for p in code_paths},
        "configuration": result["configuration"], "development_receipt_verified": True,
        "development_receipt_sha256": development.receipt, "receipt_serialization": SERIALIZATION,
        "development_manifest_sha256": development.manifest_sha256,
        "question_sha256": dict(development.question_hashes), "question_ids": list(QUESTION_IDS),
        "document_count": store.document_count, "section_count": store.section_count, "versions": store.versions,
        "section_content_hashes": [{"identity": section.identity, "content_hash": section.content_hash} for section in store.sections],
        "artifact_manifest_sha256": sha256((DOMAIN / "policy/artifact_manifest.json").read_bytes()),
        "output_sha256": {"DEVELOPMENT_RESULTS.json": sha256(results_bytes), "DEVELOPMENT_REPORT.md": sha256(report_bytes)},
        "held_out_accessed": False, "held_out_evaluated": False, "parameter_search_performed": False,
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, content in (("DEVELOPMENT_RESULTS.json", results_bytes), ("DEVELOPMENT_REPORT.md", report_bytes),
                          ("RUN_MANIFEST.json", json_bytes(manifest))):
        with (output / name).open("xb") as stream:
            stream.write(content)


def main():
    # No input-location or split arguments: the production entry point is pinned.
    if len(sys.argv) != 1:
        raise SystemExit("This evaluator accepts no arguments; only the pinned Development import is allowed")
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite existing Development artifacts: {OUTPUT}")
    development = load_development()
    store = SectionStore.load()
    require((store.document_count, store.section_count, store.versions) == (8, 25, ("1.0-demo",)), "Unexpected active corpus")
    result = evaluate(development, LexicalRetriever(store))
    write_artifacts(result, development, store)
    print(json.dumps(result["metrics"], indent=2, sort_keys=True))
    print("Development failure IDs: " + ", ".join(row["question_id"] for row in result["failures"]))
    print(f"Candidate awaiting owner review. Artifacts: {OUTPUT}")


if __name__ == "__main__":
    main()
