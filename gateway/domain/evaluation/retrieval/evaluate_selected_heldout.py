"""Phase 2G-A: pre-exposure machinery; running this CLI belongs to Phase 2G-B.

Future import contract (no private manifest was consulted to define it): the
reserved root contains HELDOUT_MANIFEST.json and exactly its 30 direct JSON
question files. Manifest fields follow the public DEVELOPMENT manifest schema,
with HELD_OUT, 30/26/4 and the pre-exposure receipt below. Filenames are direct
basenames, not directory-prefixed paths. Import preparation must preserve question
bytes and their receipt; this loader never repairs or discovers alternative data.

The CLI has no options. Model/cache failures before reservation produce no run.
After exclusive reservation, the private manifest journals each search BEFORE it
starts, then its returned response BEFORE scoring. An interruption or failure
leaves the reservation and evidence in place; no automatic retry/resume exists.
Only a fully successful run publishes aggregate public evidence. A failed run
requires owner review, even if a crash made the last search's outcome uncertain.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

DOMAIN = Path(__file__).resolve().parents[2]
REPOSITORY = DOMAIN.parent.parent
BASE = Path(__file__).resolve().parent
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))

from evaluation.retrieval.retrieval_scoring import (
    COVERAGE_DEPTHS, FULL_SET_DEPTHS, TOP_K, aggregate_metrics,
    failure_observations, score_question, validate_scoring_question,
)
from retrieval import SectionStore
from retrieval.embedding_retriever import (
    EmbeddingRetriever, SentenceTransformerBackend, configuration,
)
from validate_contracts import validate_question

PRIVATE_INPUT = BASE / "private_heldout"
PRIVATE_OUTPUT = REPOSITORY / "artifacts/retrieval_heldout_bge_v0_private"
PUBLIC_SUMMARY = BASE / "HELDOUT_EVALUATION_SUMMARY.md"
PUBLIC_MANIFEST = BASE / "HELDOUT_RUN_MANIFEST.json"
MANIFEST_NAME = "HELDOUT_MANIFEST.json"
EXPECTED_RECEIPT = "57ebb2478204d765ca52dc11792fa36bc25a02f312536e49d2379dd18a348cb0"
QUESTION_COUNT, ANSWERABLE_COUNT, NEGATIVE_COUNT = 30, 26, 4
SERIALIZATION = "UTF-8; sorted question_id + TAB + lowercase file SHA-256 + LF; final LF included"
REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
PRE_HELDOUT_TAG = "retrieval-ranked-v0.1-pre-heldout"
PRE_HELDOUT_COMMIT = "d218143f0f900f493341ab1ed2e90e98c7ec47b4"
ENGINE_TAG = "deterministic-engine-v0.1-pre-heldout"
ENGINE_COMMIT = "a528023e64ef523ea91741d8574cc431e7bae8e3"
CORPUS_MANIFEST_SHA256 = "093b763fadfaadf7859d758722e21160390edeb4d0a4e0ce18a97401efcba77f"
PHASE_2D_MANIFEST = REPOSITORY / "artifacts/retrieval_dev_embedding_baseline/RUN_MANIFEST.json"
PHASE_2D_MANIFEST_SHA256 = "030cac0e71b3dc262f9e6b669853b44650bfc38b014a8bbea8f1e475fe1d2a9d"
SOURCE_PATHS = (
    "gateway/domain/evaluation/retrieval/evaluate_selected_heldout.py",
    "gateway/domain/evaluation/retrieval/retrieval_scoring.py",
    "gateway/domain/evaluation/retrieval/evaluate_development.py",
    "gateway/domain/evaluation/retrieval/RETRIEVER_SELECTION.md",
    "gateway/domain/evaluation/retrieval/RETRIEVER_FREEZE_RECORD.md",
    "gateway/domain/retrieval/embedding_retriever.py",
    "gateway/domain/retrieval/section_store.py",
    "gateway/domain/retrieval/__init__.py",
    "gateway/domain/validate_contracts.py",
    "gateway/domain/schemas/contracts.schema.json",
)


class HeldoutIntegrityError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise HeldoutIntegrityError(message)


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def read_json_bytes(blob):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise HeldoutIntegrityError("Non-finite JSON constant")
    return json.loads(blob, object_pairs_hook=unique, parse_constant=invalid)


def receipt(question_hashes):
    return sha256("".join(f"{identity}\t{digest}\n" for identity, digest in sorted(question_hashes.items())).encode("utf-8"))


def _no_links(path):
    # Inspect ancestors without traversing them. Reject Windows junctions and
    # other reparse points too, including a dangling link at a reserved output.
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not (
            getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ), "Links/reparse points are not permitted at the custody boundary")


@dataclass(frozen=True)
class _Protocol:
    """Internal synthetic-fixture seam; the production wrapper has no parameters."""
    receipt: str
    count: int = QUESTION_COUNT
    answerable: int = ANSWERABLE_COUNT
    negative: int = NEGATIVE_COUNT


@dataclass(frozen=True)
class HeldoutSet:
    questions: tuple[dict, ...]
    receipt: str
    manifest_sha256: str
    question_hashes: tuple[tuple[str, str], ...]


def _load_import(root, protocol):
    root = Path(root)
    _no_links(root)
    manifest_path = root / MANIFEST_NAME
    _no_links(manifest_path)
    require(manifest_path.is_file(), "A direct regular manifest is required")
    manifest_blob = manifest_path.read_bytes()
    manifest = read_json_bytes(manifest_blob)
    require(manifest["split"] == "HELD_OUT", "Only HELD_OUT is permitted")
    require(manifest["review_status"] == "OWNER_REVIEWED" and manifest["owner_reviewed"] is True
            and manifest["dataset_frozen"] is True, "Owner-reviewed/frozen manifest required")
    require(manifest["receipt_algorithm"] == "sha256" and manifest["receipt_serialization"] == SERIALIZATION,
            "Receipt algorithm/serialization differs")
    require(manifest["aggregate_receipt_sha256"] == protocol.receipt, "Frozen receipt differs")
    require(manifest["policy_bundle_id"] == "last-mile-exception-triage-demo"
            and manifest["policy_version"] == "1.0-demo" and manifest["contract_version"] == "1.0",
            "Policy/contract context differs")
    rows = manifest["questions"]
    require(isinstance(rows, list) and type(manifest["question_count"]) is int
            and manifest["question_count"] == len(rows) == protocol.count, "Expected exactly 30 questions")
    require(type(manifest["answerable_count"]) is int and type(manifest["negative_count"]) is int
            and manifest["answerable_count"] == protocol.answerable and manifest["negative_count"] == protocol.negative,
            "Expected 26 ANSWERABLE and 4 NEGATIVE")
    ids, names = set(), set()
    for row in rows:
        identity, filename = row["question_id"], row["filename"]
        require(isinstance(identity, str) and re.fullmatch(r"[A-Za-z0-9_-]+", identity), "Invalid question ID")
        require(identity.casefold() not in ids, "Duplicate question ID")
        ids.add(identity.casefold())
        require(isinstance(filename, str) and re.fullmatch(r"[A-Za-z0-9_-]+\.json", filename)
                and filename.casefold() != MANIFEST_NAME.casefold(), "Question must be a direct JSON basename")
        require(filename.casefold() not in names, "Duplicate question filename")
        names.add(filename.casefold())
        require(row["split"] == "HELD_OUT", "Only HELD_OUT records are permitted")
        require(row["kind"] in ("ANSWERABLE", "NEGATIVE"), "Unknown manifest kind")
        require(isinstance(row["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]), "Invalid SHA-256")
    require(sum(r["kind"] == "ANSWERABLE" for r in rows) == protocol.answerable
            and sum(r["kind"] == "NEGATIVE" for r in rows) == protocol.negative, "Manifest kind counts differ")
    require(receipt({r["question_id"]: r["sha256"] for r in rows}) == protocol.receipt,
            "Manifest aggregate receipt differs")
    # One immediate inventory, no glob/rglob, discovery or recursion. Validate
    # every entry/path before reading any question, including unlisted entries.
    entries = tuple(root.iterdir())
    require({p.name for p in entries} == {MANIFEST_NAME, *(r["filename"] for r in rows)}, "Inventory mismatch")
    for path in entries:
        _no_links(path)
        require(path.is_file() and path.resolve().parent == root.resolve(), "Only direct regular files are permitted")
    require(manifest["source_artifact_manifest_sha256"] == CORPUS_MANIFEST_SHA256
            == sha256((DOMAIN / "policy/artifact_manifest.json").read_bytes()), "Frozen corpus manifest differs")
    blobs, hashes = {}, {}
    rows = sorted(rows, key=lambda r: r["question_id"])
    for row in rows:
        identity = row["question_id"]
        blobs[identity] = (root / row["filename"]).read_bytes()
        hashes[identity] = sha256(blobs[identity])
        require(hashes[identity] == row["sha256"], "Question file hash differs")
    require(receipt(hashes) == protocol.receipt, "Computed aggregate receipt differs")
    # ALL raw hashes have passed before the first question JSON is parsed.
    questions = []
    for row in rows:
        question = read_json_bytes(blobs[row["question_id"]])
        require(question["split"] == "HELD_OUT", "Question split differs")
        validate_scoring_question(question)
        validate_question(question, DOMAIN)
        require(question["question_id"] == row["question_id"] and question["kind"] == row["kind"], "Question identity/kind differs")
        questions.append(question)
    return HeldoutSet(tuple(questions), protocol.receipt, sha256(manifest_blob), tuple(hashes.items()))


def load_heldout():
    """Production input, receipt, split and counts cannot be supplied by callers."""
    try:
        return _load_import(PRIVATE_INPUT, _Protocol(EXPECTED_RECEIPT))
    except HeldoutIntegrityError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HeldoutIntegrityError("Invalid private import; no evaluation started") from exc


def load_model_evidence():
    blob = PHASE_2D_MANIFEST.read_bytes()
    require(sha256(blob) == PHASE_2D_MANIFEST_SHA256, "Phase 2D model evidence changed")
    history = read_json_bytes(blob)
    require(history["configuration"] == configuration(), "Selected configuration changed")
    require(history["runtime"]["resolved_model_revision"] == REVISION, "Historical revision differs")
    return history


def validate_runtime(runtime, expected):
    require(runtime["requested_model_id"] == "BAAI/bge-small-en-v1.5"
            and runtime["requested_revision"] == runtime["resolved_model_revision"] == REVISION,
            "Exact model revision required")
    require(runtime["model_file_sha256"] == expected["model_file_sha256"], "Model-file hashes differ")
    require(runtime["device"] == "cpu" and runtime["embedding_dimension"] == 384
            and runtime["normalize_embeddings"] is True and runtime["similarity"] == "normalized dot product"
            and runtime["query_instruction"] == runtime["document_instruction"] == ""
            and runtime["cpu_threads"] == 1, "Frozen runtime configuration differs")
    require(runtime["pooling_configuration"] == expected["pooling_configuration"]
            and runtime["max_sequence_length"] == expected["max_sequence_length"], "Model pooling/truncation differs")
    require(runtime["model_download_occurred"] is False and runtime["weights_downloaded"] is False
            and runtime["downloaded_files"] == [], "Offline-only model construction required")


def create_selected_retriever():
    history = load_model_evidence()
    require(sha256((DOMAIN / "policy/artifact_manifest.json").read_bytes()) == CORPUS_MANIFEST_SHA256,
            "Frozen corpus manifest differs")
    store = SectionStore.load()
    require((store.document_count, store.section_count, store.versions) == (8, 25, ("1.0-demo",)), "Frozen corpus differs")
    require([dict(identity=list(s.identity), content_hash=s.content_hash) for s in sorted(store.sections, key=lambda s: s.identity)]
            == history["section_content_hashes"], "Frozen section identities/content differ")
    backend = SentenceTransformerBackend(revision=REVISION, local_files_only=True)
    validate_runtime(backend.metadata, history["runtime"])
    retriever = EmbeddingRetriever(store, encoder=backend)
    require(retriever.embedding_dimension == 384, "Expected 384 dimensions")
    return retriever


def verify_source_freeze():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPOSITORY)
    require(git("rev-list", "-n", "1", PRE_HELDOUT_TAG).decode().strip() == PRE_HELDOUT_COMMIT, "Retrieval tag moved")
    require(git("rev-list", "-n", "1", ENGINE_TAG).decode().strip() == ENGINE_COMMIT, "Engine tag moved")
    for path in SOURCE_PATHS[2:]:
        # Git may normalize line endings in source; compare Git blob identities.
        expected = git("rev-parse", f"{PRE_HELDOUT_TAG}:{path}").decode().strip()
        actual = git("hash-object", "--path=" + path, path).decode().strip()
        require(actual == expected, "Frozen retrieval/scoring dependency changed")
    return {path: sha256((REPOSITORY / path).read_bytes()) for path in SOURCE_PATHS}


def ensure_no_outputs(private_output, public_summary, public_manifest):
    for path in (private_output, public_summary, public_manifest):
        _no_links(path)
        require(not os.path.lexists(path), "Refusing existing evaluation output; owner review required")


def _write_new(path, blob):
    with path.open("xb") as stream:
        stream.write(blob)
        stream.flush()
        os.fsync(stream.fileno())


def _checkpoint(path, state):
    temporary = path.with_suffix(".json.pending")
    _write_new(temporary, json_bytes(state))
    os.replace(temporary, path)


def private_result(rows):
    """Private serializer input is deliberately separate from public output."""
    return {
        "run_type": "PRIMARY_SELECTED_BGE_V0_HELDOUT", "questions": rows,
        "metrics": aggregate_metrics(rows),
        "failures": [{"question_id": row["question_id"], "observations": notes}
                     for row in rows if (notes := failure_observations(row))],
    }


def _number(value):
    require(type(value) in (int, float) and math.isfinite(value), "Public metric must be finite numeric data")
    return value


def _nullable_number(value):
    return None if value is None else _number(value)


def _public_rate(value):
    return {"count": _number(value["count"]), "total": _number(value["total"]), "rate": _nullable_number(value["rate"])}


def public_metrics(metrics):
    """Recursive allowlist: do not copy even a nested dict from private data."""
    return {
        **{key: _number(metrics[key]) for key in ("answerable_count", "negative_count", "multi_required_question_count")},
        **{key: _public_rate(metrics[key]) for key in ("hit_at_1", "hit_at_3", "negative_correct_abstention", "negative_false_support")},
        "mrr_at_10": _nullable_number(metrics["mrr_at_10"]),
        "required_coverage_at_k": {str(k): {
            "macro_average": _nullable_number(metrics["required_coverage_at_k"][str(k)]["macro_average"]),
            "micro": _public_rate(metrics["required_coverage_at_k"][str(k)]["micro"])} for k in COVERAGE_DEPTHS},
        "full_required_set_success_at_k": {str(k): _public_rate(metrics["full_required_set_success_at_k"][str(k)]) for k in FULL_SET_DEPTHS},
    }


def _digest(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "Invalid public hash")
    return value


def public_manifest(state, runtime, sources, output_hash):
    require(state["status"] == "COMPLETE" and state["success_count"] == QUESTION_COUNT
            and state["error_count"] == 0 and state["completed_evaluation_attempts"] == 1,
            "Incomplete runs cannot publish success evidence")
    require(len(state["question_attempts"]) == QUESTION_COUNT
            and all(v["attempts"] == 1 and v["status"] == "SUCCESS" for v in state["question_attempts"].values()),
            "Each question must succeed exactly once")
    # Model-file names come from authenticated historical evidence, not input.
    expected = load_model_evidence()["runtime"]
    validate_runtime(runtime, expected)
    versions = {}
    for key in ("sentence-transformers", "transformers", "torch", "numpy", "huggingface-hub"):
        value = runtime["versions"][key]
        require(isinstance(value, str) and re.fullmatch(r"[0-9][A-Za-z0-9.+_-]*", value), "Invalid runtime version")
        versions[key] = value
    python_version = runtime["python_version"]
    require(isinstance(python_version, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", python_version), "Invalid Python version")
    date = datetime.fromisoformat(state["evaluation_started_utc"]).isoformat()
    return {
        "run_type": "PRIMARY_SELECTED_BGE_V0_HELDOUT", "selected_retriever": "BGE embedding v0",
        "pre_heldout_tag": PRE_HELDOUT_TAG, "pre_heldout_commit": PRE_HELDOUT_COMMIT,
        "evaluation_started_utc": date, "heldout_receipt_sha256": EXPECTED_RECEIPT,
        "question_count": QUESTION_COUNT, "answerable_count": ANSWERABLE_COUNT, "negative_count": NEGATIVE_COUNT,
        "baseline_run_sequence": 1, "completed_evaluation_attempts": 1,
        "per_question_attempts": 1, "success_count": 30, "error_count": 0,
        "configuration": configuration(), "model_revision": REVISION,
        "model_file_sha256": {name: _digest(runtime["model_file_sha256"][name]) for name in expected["model_file_sha256"]},
        "runtime_versions": versions, "python_version": python_version,
        "source_file_sha256": {path: _digest(sources[path]) for path in SOURCE_PATHS},
        "aggregate_output_sha256": _digest(output_hash),
        "output_receipt_serialization": "UTF-8; sorted private evidence basename + TAB + SHA-256 + LF; final LF included",
        "network_access_required": False, "post_heldout_tuning_performed": False,
        "model_or_threshold_sweep_performed": False, "secondary_retrievers_evaluated": False,
    }


def public_summary(result, manifest):
    safe = public_metrics(result["metrics"])
    # No private rows, IDs, labels, notes or paths are interpolated into Markdown.
    lines = ["# Selected BGE v0 primary HELDOUT evaluation", "",
             f"Frozen tag: `{PRE_HELDOUT_TAG}` at `{PRE_HELDOUT_COMMIT}`.",
             f"Evaluation started: {datetime.fromisoformat(manifest['evaluation_started_utc']).isoformat()}.",
             f"Model: BAAI/bge-small-en-v1.5, revision `{REVISION}`.",
             f"Verified receipt: `{EXPECTED_RECEIPT}`. Questions: 30 (26 ANSWERABLE, 4 NEGATIVE).",
             f"Questions with at least one recorded diagnostic failure: {len(result['failures'])}.", "",
             "Aggregate metrics use the frozen DEVELOPMENT definitions. Gold relevance and required-section coverage are separate.",
             "```json", json.dumps(safe, indent=2, sort_keys=True, allow_nan=False), "```", "",
             "No post-heldout tuning, model/threshold sweep, query instruction, rewriting, BM25 or RRF comparison preceded this primary result.",
             "Limitations: one small project-specific 30-question evaluation; four negatives do not establish a general safety rate.",
             "Cosine scores are retrieval diagnostics, not confidence or business accuracy. Cross-runtime identical embeddings are not claimed.", ""]
    return "\n".join(lines).encode("utf-8")


def _run(data, retriever, sources, private_output, public_summary_path, public_manifest_path):
    """Internal injected-fixture seam. Production validates data before calling."""
    ensure_no_outputs(private_output, public_summary_path, public_manifest_path)
    private_output.mkdir(parents=True, exist_ok=False)  # Exclusive run reservation.
    journal = private_output / "RUN_MANIFEST_PRIVATE.json"
    state = {
        "run_type": "PRIMARY_SELECTED_BGE_V0_HELDOUT", "status": "RESERVED",
        "baseline_run_sequence": 1, "completed_evaluation_attempts": 0,
        "evaluation_started_utc": datetime.now(timezone.utc).isoformat(),
        "heldout_receipt_sha256": data.receipt, "input_manifest_sha256": data.manifest_sha256,
        "question_sha256": dict(data.question_hashes), "source_file_sha256": sources,
        "pre_heldout_tag": PRE_HELDOUT_TAG, "pre_heldout_commit": PRE_HELDOUT_COMMIT,
        "configuration": configuration(), "model_revision": REVISION,
        "runtime": retriever.runtime_metadata,
        "question_attempts": {q["question_id"]: {"attempts": 0, "status": "PENDING"} for q in data.questions},
        "success_count": 0, "error_count": 0, "retrieval_results_produced": 0,
        "result_bearing_evaluation_attempts": 0, "private_retrieval_responses": {},
    }
    _write_new(journal, json_bytes(state))
    rows, active = [], None
    try:
        for question in data.questions:
            active = state["question_attempts"][question["question_id"]]
            active.update(attempts=1, status="SEARCHING")
            state["status"] = "RUNNING"
            _checkpoint(journal, state)
            # This is the sole query boundary: no ID, kind, labels or notes.
            response = retriever.search(question["question"], top_k=TOP_K)
            state["retrieval_results_produced"] += 1
            state["result_bearing_evaluation_attempts"] = 1
            active["status"] = "RETRIEVED"
            state["private_retrieval_responses"][question["question_id"]] = asdict(response)
            _checkpoint(journal, state)
            rows.append(score_question(question, response))
            active["status"] = "SUCCESS"
            state["success_count"] += 1
            _checkpoint(journal, state)
            active = None
        state["completed_evaluation_attempts"] = 1
        result = private_result(rows)
        result_blob = json_bytes(result)
        report_blob = ("# Private primary HELDOUT evidence\n\nComplete query, Gold, required-section, ranking and failure details follow.\n\n```json\n"
                       + result_blob.decode("utf-8") + "```\n").encode("utf-8")
        private_blobs = {"HELDOUT_RESULTS.json": result_blob, "HELDOUT_REPORT_PRIVATE.md": report_blob}
        state["output_sha256"] = {name: sha256(blob) for name, blob in private_blobs.items()}
        state["aggregate_output_sha256"] = receipt(state["output_sha256"])
        for name, blob in private_blobs.items():
            _write_new(private_output / name, blob)
        state["status"] = "COMPLETE"
        # Save success before publication; publication failure cannot cause a rerun.
        _checkpoint(journal, state)
        public = public_manifest(state, retriever.runtime_metadata, sources, state["aggregate_output_sha256"])
        _write_new(public_summary_path, public_summary(result, public))
        _write_new(public_manifest_path, json_bytes(public))
        return public
    except BaseException as exc:
        if active is not None and active["status"] != "SUCCESS":
            active["status"] = "ERROR"
            state["error_count"] += 1
        state["status"] = "ERROR"
        state["error"] = {"type": type(exc).__name__, "message": str(exc)}  # PRIVATE only.
        state["scored_questions"] = rows
        # If the filesystem itself failed, keep the last durable SEARCHING or
        # RETRIEVED record. Never remove the reservation or restart automatically.
        try:
            _checkpoint(journal, state)
        except OSError:
            pass
        raise


def main():
    if len(sys.argv) != 1:
        raise SystemExit("No arguments accepted; the selected retriever and private import are pinned")
    ensure_no_outputs(PRIVATE_OUTPUT, PUBLIC_SUMMARY, PUBLIC_MANIFEST)
    sources = verify_source_freeze()
    # Load/cache checks and corpus encoding precede exposure to question contents.
    retriever = create_selected_retriever()
    data = load_heldout()
    _run(data, retriever, sources, PRIVATE_OUTPUT, PUBLIC_SUMMARY, PUBLIC_MANIFEST)
    print("Primary selected-candidate evaluation recorded. Stop for owner review.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never emit a traceback containing private paths, labels or query text.
        raise SystemExit("Evaluation stopped; preserve any reserved run and review its private evidence. No automatic retry.") from None
