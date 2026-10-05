"""One offline BGE pass over pinned DEVELOPMENT. Never implements or invokes a gate."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import ipaddress
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys

from .answerability_contracts import ActiveBundle, require
from .answerability_scoring import deterministic_json_bytes
from .development_loader import ROOT, IDS, MANIFEST_SHA256, RECEIPT, load_development, sha256, strict_json
from .bge_evidence import (
    MODEL, REVISION, FROZEN_CONFIGURATION, Query, capture_response, make_package,
    reconstruct_gate_input, retrieval_metrics, section_map, validate_configuration, validate_package, validate_queries,
)
from ...retrieval.embedding_retriever import (
    DEFAULT_CACHE, MODEL_FILES, EmbeddingRetriever, SentenceTransformerBackend, configuration,
)
from ...retrieval.section_store import SectionStore

REPO = ROOT.parents[3]
BASE_COMMIT = "e017a61ac160e9541356d7bc862c9d3b73061789"
BASE_TAG = "answerability-dev-harness-v0.1.1-pre-candidates"
HISTORICAL_COMMIT = "c8e73b77a9ef95e4d627766efefea3cabccf4f4a"
HISTORICAL_TAG = "answerability-dev-harness-v0.1-pre-candidates"
RETRIEVER_SHA = "4da7a8ccf26ca5987a9a37479466064e9acf526503b385116845b6daf52576d0"
OUTPUT = REPO / "artifacts/answerability_dev_bge_evidence_v0"
SOURCE_PATHS = (
    "gateway/domain/evaluation/answerability/bge_evidence.py",
    "gateway/domain/evaluation/answerability/generate_development_evidence.py",
    "gateway/domain/tests/test_answerability_bge_evidence.py",
)
OUTPUT_NAMES = ("DEVELOPMENT_BGE_EVIDENCE.json", "DEVELOPMENT_RETRIEVAL_METRICS.json",
                "RUN_MANIFEST.json", "EVIDENCE_FREEZE_RECORD.md", "ATTEMPT_JOURNAL.jsonl")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO).decode("utf-8")


def file_hash(path):
    return sha256(Path(path).read_bytes())


def verify_hashes(hashes):
    for name, expected in hashes.items():
        require(file_hash(REPO / name) == expected, f"frozen file differs: {name}")


def preflight():
    require(not os.path.lexists(OUTPUT), "refuse existing B2 evidence directory")
    require(git("rev-parse", "HEAD").strip() == BASE_COMMIT, "wrong base commit")
    require(git("rev-list", "-n", "1", BASE_TAG).strip() == BASE_COMMIT, "B1.1 tag differs")
    require(git("rev-list", "-n", "1", HISTORICAL_TAG).strip() == HISTORICAL_COMMIT, "historical tag differs")
    status = git("status", "--short", "--untracked-files=all")
    require(all(line[3:] in (*SOURCE_PATHS, ".gitattributes") for line in status.splitlines()), "unexpected pre-run changes")
    prior_path = REPO / "artifacts/retrieval_dev_embedding_baseline/RUN_MANIFEST.json"
    require(file_hash(prior_path) == "030cac0e71b3dc262f9e6b669853b44650bfc38b014a8bbea8f1e475fe1d2a9d",
            "historical model/source custody record differs")
    prior = strict_json(prior_path.read_bytes())
    verify_hashes(prior["source_file_sha256"])
    require(file_hash(REPO / "gateway/domain/retrieval/embedding_retriever.py") == RETRIEVER_SHA,
            "frozen embedding source differs")
    validate_configuration(configuration(), REVISION, 384)
    require(configuration() == prior["configuration"], "Phase 2D configuration differs")
    inventory = strict_json((ROOT / "DEVELOPMENT_HARNESS_SHA256.json").read_bytes())
    protected = {**inventory["sha256"], **inventory["protected_public_file_sha256_unchanged"], **prior["source_file_sha256"]}
    # Only these newly authorized byte-preservation rules may change outside new B2 files.
    protected.pop(".gitattributes", None)
    verify_hashes(protected)
    protected["gateway/domain/evaluation/answerability/DEVELOPMENT_HARNESS_SHA256.json"] = file_hash(ROOT / "DEVELOPMENT_HARNESS_SHA256.json")
    cases = load_development()  # Every load revalidates all 40 files and the frozen receipt.
    manifest = strict_json((ROOT / "DEVELOPMENT_MANIFEST.json").read_bytes())
    file_hashes = {e["question_id"]: e["sha256"] for e in manifest["entries"]}
    queries = tuple(Query(c.question_id, c.question, file_hashes[c.question_id]) for c in cases)
    store = SectionStore.load()
    require((store.document_count, store.section_count, store.versions) == (8, 25, ("1.0-demo",)), "corpus inventory differs")
    sections = [{"identity": list(s.identity), "content_hash": s.content_hash}
                for s in sorted(store.sections, key=lambda s: s.identity)]
    require(sections == prior["section_content_hashes"], "frozen section hashes differ")
    policy_root = REPO / "gateway/domain/policy"
    registry = strict_json((policy_root / "policy_registry.json").read_bytes())
    bundle = ActiveBundle(registry["bundle_id"], registry["bundle_version"], registry["effective_from"],
                          registry["effective_to"], file_hash(policy_root / "artifact_manifest.json"),
                          file_hash(policy_root / "policy_registry.json"))
    snapshot = DEFAULT_CACHE / "models--BAAI--bge-small-en-v1.5" / "snapshots" / REVISION
    expected_model_hashes = prior["runtime"]["model_file_sha256"]
    require(set(expected_model_hashes) == set(MODEL_FILES), "model inventory differs")
    model_hashes = {name: file_hash(snapshot / name) for name in sorted(MODEL_FILES)}
    require(model_hashes == expected_model_hashes, "cached frozen model checksum mismatch")
    provenance = {
        "base_commit": BASE_COMMIT, "base_tag": BASE_TAG, "historical_b1_commit": HISTORICAL_COMMIT,
        "historical_b1_tag": HISTORICAL_TAG, "benchmark": "answerability-benchmark-v0.1",
        "development_manifest_sha256": MANIFEST_SHA256, "development_receipt": RECEIPT,
        "development_file_sha256": file_hashes, "development_hashes_verified": 40,
        "development_class_counts": {"ALLOW": 20, "ABSTAIN": 20},
        "git_status_at_run": status, "initial_clean_precondition_verified_before_B2_implementation": True,
        "retriever": "BGE embedding v0", "retriever_source_sha256": RETRIEVER_SHA,
        "configuration": configuration(), "model": MODEL, "model_revision": REVISION,
        "device": "cpu", "dimension": 384, "threshold": 0.30, "threshold_scope": "whole-response/top-score",
        "top_k": 10, "question_transformation": "none", "additional_retrieval": "none",
        "model_local_provenance": {"snapshot": snapshot.relative_to(REPO).as_posix(), "local_files_only": True,
                                   "model_file_sha256": model_hashes, "phase_2d_manifest_sha256": file_hash(prior_path)},
        "section_content_hashes": sections, "protected_source_sha256": protected,
        "b2_source_sha256": {p: file_hash(REPO / p) for p in SOURCE_PATHS},
        "policy_corpus_sha256": {p: h for p, h in protected.items() if "/policy/" in p or "/sops/" in p},
        "gate_implemented": False, "gate_evaluated": False, "gate_invocations": 0,
        "parameter_search": False, "phase_2h_held_out_accessed": False, "phase_2g_private_heldout_accessed": False,
        "post_result_tuning": False, "prior_real_phase_2h_retrieval_attempts": 0,
    }
    return cases, queries, store, bundle, provenance


def create_output_directory(path):
    require(not os.path.lexists(path), "refuse existing evidence directory")
    Path(path).mkdir(exist_ok=False)


def write_once(path, data):
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    require(Path(path).read_bytes() == data, "artifact readback differs")
    return sha256(data)


def audit_safe(value):
    if type(value) is float and not math.isfinite(value):
        return {"invalid_nonfinite_float": repr(value)}
    if isinstance(value, (tuple, list)):
        return [audit_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: audit_safe(v) for k, v in value.items()}
    return value


class AttemptJournal:
    """Append-only durable attempt/response receipt; contains no Gold or gate decisions."""
    def __init__(self, path):
        self.stream = Path(path).open("xb")
        self.attempts = {}
        self.returned = 0

    def record(self, event, **payload):
        data = (json.dumps(audit_safe({"event": event, **payload}), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        self.stream.write(data)
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


class OfflineSocketAudit:
    """Execution guard: permit local capability probes, never remote access/download fallback."""
    def __init__(self, journal):
        self.journal = journal
        self.events = []
        self.active = True

    @staticmethod
    def loopback(host):
        if host == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except (ValueError, TypeError):
            return False

    def __call__(self, event, args):
        if not self.active or not event.startswith("socket."):
            return
        destination = None
        allowed = event in ("socket.__new__", "socket.gethostname")
        if event == "socket.bind":
            destination = args[1]
            allowed = isinstance(destination, tuple) and self.loopback(destination[0])
        elif event in ("socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"):
            destination = args[0]
            allowed = self.loopback(destination)
        elif event in ("socket.connect", "socket.connect_ex", "socket.sendto"):
            destination = args[-1]
        record = {"operation": event, "destination": destination, "allowed": allowed}
        if event == "socket.__new__":
            record["family_type_protocol"] = [int(v) for v in args[1:4]]
        self.events.append(record)
        self.journal.record("socket_event", **record)
        require(allowed, f"blocked unexpected network operation: {event}, destination={destination!r}")


def run_queries(queries, retriever, store, bundle, journal):
    validate_queries(queries)
    rows, sections = [], section_map(store)
    for query in queries:
        require(query.question_id not in journal.attempts, "no query retries allowed")
        journal.record("query_attempt", question_id=query.question_id, question_text_sha256=sha256(query.text.encode("utf-8")))
        journal.attempts[query.question_id] = 1
        response = retriever.search(query.text, top_k=10)  # The only inference call; no ID or annotation crosses it.
        journal.returned += 1
        journal.record("retriever_returned", question_id=query.question_id, response=asdict(response))
        row = capture_response(query, response, sections)
        reconstruct_gate_input(row, query, bundle, sections)
        rows.append(row)
    return rows


def freeze_record(provenance, metrics, hashes):
    metric_lines = "\n".join(f"| {name} | {m['numerator']}/{m['numerator_divisor']} divided by {m['denominator']} | {m['rate']} |"
                             for name, m in metrics["allow_retrieval"].items())
    artifact_lines = "\n".join(f"| `{name}` | `{value}` |" for name, value in sorted(hashes.items()))
    return f'''# Phase 2H-B2 DEVELOPMENT BGE evidence review candidate

Status: **CANDIDATE_AWAITING_OWNER_REVIEW**

Purpose: preserve one actual frozen BGE v0 response for each of the 40 frozen
DEVELOPMENT questions. Every future B3 candidate must consume these exact
evidence bytes. No candidate was implemented or evaluated; B3 has not begun.

Base: `{BASE_COMMIT}` / `{BASE_TAG}`.
Historical B1: `{HISTORICAL_COMMIT}` / `{HISTORICAL_TAG}`.
Both historical tags remain unchanged. The initial repository was clean before
B2 implementation; the exact authorized source changes at execution are in the
run manifest. No automatic commit or tag is made.

DEVELOPMENT manifest SHA-256: `{MANIFEST_SHA256}`.
DEVELOPMENT receipt: `{RECEIPT}`. All 40 hashes were revalidated by the pinned
B1.1 loader. No private authoring workspace was used.

Model: `{MODEL}` at exact revision `{REVISION}`, CPU, 384 dimensions.
The ten model files matched frozen Phase 2D hashes before initialization.
Offline environment controls and local_files_only=True were applied. Runtime
versions, local model provenance, socket events and zero downloads are recorded
in RUN_MANIFEST.json. No fallback model/revision/network was used.

The frozen eight-document / 25-section corpus uses readable document title +
LF + readable section title + LF + body. Original question text is encoded
without an instruction, rewrite or augmentation. Normalized vectors and frozen
normalized dot product are unchanged. The 0.30 threshold applies only to the
highest score for the entire response. Top-10 ordering is descending unrounded
score, then ascending canonical (policy_id, version, section_id). All actual
returned tail scores, including those below 0.30, are preserved; no filtering,
padding, deduplication, reranking or extra retrieval occurred.

Exactly one logical run completed: AQ001-AQ040 each queried once, 40 attempts,
40 successful responses, zero errors and zero retries. The append-only journal
durably records each attempt and actual response. Integrity validation and
GateInput reconstruction passed for all 40 stored rows without invoking a gate.
Evidence includes original question and externally associated ID/file/text
hashes; the reconstructed GateInput contains only original question, ranked
evidence and permitted active bundle metadata, with no evaluator annotations.

Serialization: UTF-8, sorted keys, two-space JSON indentation and final LF.
Python float JSON representations round-trip the exact stored binary64 scores;
no authoritative score is rounded. Evidence contains no timestamps. Environment
and run timestamps are separate. Serialization and all invariants were checked
from stored bytes without a second retrieval run.

## RETRIEVAL DIAGNOSTICS ONLY - NOT ANSWERABILITY-GATE ACCURACY

Gold ALLOW denominator: 20. Exact metrics use rational arithmetic. The displayed
decimal strings have 12 places; they do not change ranking or denominators.

| Metric | Exact numerator and denominator | Rate |
| --- | --- | --- |
{metric_lines}

Overall retrieval responses: `{json.dumps(metrics['overall_response_diagnostics'], sort_keys=True)}`.
Gold ABSTAIN retrieval responses: `{json.dumps(metrics['gold_abstain_response_diagnostics'], sort_keys=True)}`.
These counts are retriever behavior, not gate correctness or gate eligibility.

## Evidence hashes

| Artifact | SHA-256 |
| --- | --- |
{artifact_lines}

RUN_MANIFEST.json records this record's hash and those above; its own hash is
reported at completion, avoiding circular hashes. Sources, policy bytes and
25 canonical section hashes are recorded there as well. No B1.1 source,
retriever, policy, benchmark, Gold/required annotations or historical evidence
changed. No BM25/RRF, gate, parameter search, result-driven tuning, second run,
Phase 2H HELD_OUT access or Phase 2G private HELDOUT access occurred.

Stop for owner review. Proposed commit: `Freeze Phase 2H development BGE evidence`.
Proposed tag: `answerability-dev-evidence-v0.1-pre-candidates`.
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args(argv)
    cases, queries, store, bundle, provenance = preflight()
    create_output_directory(OUTPUT)
    journal = AttemptJournal(OUTPUT / "ATTEMPT_JOURNAL.jsonl")
    audit = OfflineSocketAudit(journal)
    started = datetime.now(timezone.utc).isoformat()
    stage = "model_initialization"
    try:
        journal.record("run_started", base_commit=BASE_COMMIT, real_queries_before_run=0, started_utc=started)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        sys.addaudithook(audit)
        backend = SentenceTransformerBackend(cache_folder=DEFAULT_CACHE, revision=REVISION, local_files_only=True)
        runtime = backend.metadata
        require(runtime["requested_revision"] == runtime["resolved_model_revision"] == REVISION, "runtime revision differs")
        require(runtime["device"] == "cpu" and runtime["embedding_dimension"] == 384, "runtime device/dimension differs")
        require(runtime["model_file_sha256"] == provenance["model_local_provenance"]["model_file_sha256"], "loaded model custody differs")
        require(not runtime["model_download_occurred"] and not runtime["weights_downloaded"]
                and not runtime["downloaded_files"], "unexpected model download")
        stage = "corpus_encoding"
        retriever = EmbeddingRetriever(store, encoder=backend)
        require(retriever.embedding_dimension == 384 and retriever.section_count == 25, "retriever shape differs")
        journal.record("model_ready", revision=REVISION, device="cpu", dimension=384, downloads=0)
        stage = "query_execution"
        rows = run_queries(queries, retriever, store, bundle, journal)
        require(journal.attempts == dict.fromkeys(IDS, 1) and journal.returned == 40, "attempt inventory differs")
        stage = "artifact_validation"
        package = make_package(rows, bundle)
        validate_package(package, queries, store, bundle)
        evidence_bytes = deterministic_json_bytes(package)
        stored = strict_json(evidence_bytes)
        validate_package(stored, queries, store, bundle)
        require(deterministic_json_bytes(stored) == evidence_bytes, "evidence serialization is not stable")
        for original, parsed in zip(rows, stored["questions"]):
            require(original["top_score"].hex() == parsed["top_score"].hex(), "top score changed in serialization")
            require([e["cosine_score"].hex() for e in original["results"]] ==
                    [e["cosine_score"].hex() for e in parsed["results"]], "stored score precision changed")
        metrics = retrieval_metrics(cases, stored)
        verify_hashes(provenance["protected_source_sha256"])
        verify_hashes(provenance["b2_source_sha256"])
        hashes = {"DEVELOPMENT_BGE_EVIDENCE.json": write_once(OUTPUT / "DEVELOPMENT_BGE_EVIDENCE.json", evidence_bytes),
                  "DEVELOPMENT_RETRIEVAL_METRICS.json": write_once(OUTPUT / "DEVELOPMENT_RETRIEVAL_METRICS.json", deterministic_json_bytes(metrics))}
        journal.record("completed", query_attempts=40, responses=40, gate_invocations=0)
        audit.active = False
        journal.close()
        hashes["ATTEMPT_JOURNAL.jsonl"] = file_hash(OUTPUT / "ATTEMPT_JOURNAL.jsonl")
        hashes["EVIDENCE_FREEZE_RECORD.md"] = write_once(OUTPUT / "EVIDENCE_FREEZE_RECORD.md", freeze_record(provenance, metrics, hashes).encode("utf-8"))
        manifest = {**provenance, "run_type": "PHASE_2H_DEVELOPMENT_BGE_EVIDENCE", "status": "COMPLETE",
                    "evidence_status": "CANDIDATE_AWAITING_OWNER_REVIEW", "baseline_run_sequence": 1,
                    "completed_retrieval_runs": 1, "question_count": 40, "attempt_count": 40,
                    "question_attempts": journal.attempts, "success_count": 40, "error_count": 0,
                    "started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
                    "runtime": runtime, "platform": platform.platform(), "offline_environment": {
                        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
                    "socket_events": audit.events, "download_count": 0, "model_initializations": 1,
                    "gate_input_reconstructions": 40, "gate_input_boundary_verified": True,
                    "output_sha256": hashes.copy(), "manifest_self_hash_excluded": True}
        hashes["RUN_MANIFEST.json"] = write_once(OUTPUT / "RUN_MANIFEST.json", deterministic_json_bytes(manifest))
        require(all(file_hash(OUTPUT / name) == h for name, h in hashes.items()), "final artifact hash differs")
        print(deterministic_json_bytes({"status": "COMPLETE", "attempt_count": 40, "output_sha256": hashes,
                                        "metrics": metrics}).decode("utf-8"))
        return 0
    except BaseException as exc:
        audit.active = False
        failure = {"status": "FAILED_STOP_NO_RETRY", "stage": stage, "base_commit": BASE_COMMIT,
                   "started_utc": started, "failed_utc": datetime.now(timezone.utc).isoformat(),
                   "question_attempts": journal.attempts, "attempt_count": sum(journal.attempts.values()),
                   "returned_responses": journal.returned, "exception_type": type(exc).__name__,
                   "exception": str(exc), "socket_events": audit.events, "provenance": provenance}
        try:
            if not journal.stream.closed:
                journal.record("failed_stop_no_retry", stage=stage, exception_type=type(exc).__name__, exception=str(exc))
                journal.close()
            failure["journal_sha256"] = file_hash(OUTPUT / "ATTEMPT_JOURNAL.jsonl")
            write_once(OUTPUT / "FAILED_ATTEMPT.json", deterministic_json_bytes(failure))
        finally:
            print(deterministic_json_bytes(failure).decode("utf-8"), file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
