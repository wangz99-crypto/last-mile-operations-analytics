"""One frozen python-jsonschema candidate and synthetic two-layer qualification."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

from recover_direct_regex_acceptance import inventory, pip_check

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
ART = ROOT / "artifacts/answerability_semantic_v2_1_exact_validator"
OLD = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_decoder"
CLOSURE = ROOT / "artifacts/answerability_semantic_v2_1_whitespace_closure"
SPLIT = ROOT / "artifacts/answerability_semantic_v2_decoder_responsibility_split"
SCHEMA = ROOT / "artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json"
SCHEMA_SHA = "6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e"
BASE = "b3bb919e3d38ab733f775413c08fd3ecb7da08f2"
TAG = "answerability-semantic-v2_1-direct-regex-v0.4-qualified"
ITEM = "/properties/material_asks/items"
RANKS = ITEM + "/properties/supporting_evidence_ranks"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(name, value, exclusive=False):
    with (ART / name).open("xb" if exclusive else "wb") as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode())


def strict_parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("Nonfinite JSON constant")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def synthetic_input(count):
    from gateway.domain.evaluation.answerability.answerability_contracts import ActiveBundle, RankedEvidence, GateInput
    bundle = ActiveBundle("last-mile-exception-triage-demo", "1.0-demo", "2026-01-01T00:00:00Z", None, "0" * 64, "1" * 64)
    evidence = tuple(RankedEvidence(i, "SOP-90", "1.0-demo", "unit-" + str(i), "Synthetic structural fixture",
                                   "Opaque section " + str(i), "Opaque structural payload " + str(i), 0.95 - i * 0.01)
                     for i in range(1, count + 1))
    return GateInput("Synthetic structural interface input.", evidence, bundle)


def fixtures_and_matrix():
    historical = {x["id"]: x for x in read(OLD / "STRUCTURAL_FIXTURES.json")["fixtures"]}
    fixtures = []
    def add(fid, value=None, raw=None, expected="ACCEPT", combined=None, targets=(), count=10, note=""):
        if raw is None:
            raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        encoded = raw.encode("utf-8")
        fixtures.append({"id": fid, "raw_utf8_hex": encoded.hex(), "raw_text": raw,
                         "raw_sha256": hashlib.sha256(encoded).hexdigest(), "validator_expected": expected,
                         "combined_expected": combined, "evidence_count": count, "target_pointers": list(targets), "note": note})
    base = strict_parse(historical["M1"]["text"].encode())
    for fid in ["M" + str(i) for i in range(1, 9)]:
        add(fid, raw=historical[fid]["text"], expected="ACCEPT" if fid == "M1" else "REJECT",
            combined="COMBINED_STRUCTURAL_ACCEPT" if fid == "M1" else "DECODER_STRUCTURAL_REJECT",
            targets=["/required"], note="Exact frozen historical bytes; validator-only submission separate from combined early exit.")
    for number in range(1, 19):
        fid = "R%02d_NEG" % number
        coverage = read(OLD / "STRUCTURAL_FIXTURES.json")["coverage"][number - 1]
        assert coverage["violating"] == fid
        add(fid, raw=historical[fid]["text"], expected="REJECT", targets=[coverage["constraint_id"]],
            note="Frozen decoder-invalid fixture submitted only to exact validator; no combined rerun.")
    for fid in ["DELEGATED_UNIQUE", "DELEGATED_CONTAINS", "DELEGATED_CONDITIONAL"]:
        add(fid, raw=historical[fid]["text"], expected="REJECT", combined="EXACT_SCHEMA_REJECT",
            targets=[RANKS + "/uniqueItems"] if fid == "DELEGATED_UNIQUE" else [ITEM + "/allOf", "/oneOf"],
            note="Frozen delegated plan bytes. Historical names are retained; actual rejecting paths are recorded, not inferred from the name.")
    def ask(status, ranks):
        return {"ask": "Synthetic structural requirement", "support_status": status, "supporting_evidence_ranks": ranks}
    variants = {
        "POS_INSUFFICIENT": {"decision": "ABSTAIN", "reason_code": "INSUFFICIENT_POLICY_SUPPORT", "policy_context_status": "RESOLVED", "material_asks": [ask("UNSUPPORTED", []), ask("SUPPORTED", [1])]},
        "POS_UNRESOLVED_CONTEXT": {"decision": "ABSTAIN", "reason_code": "UNRESOLVED_POLICY_CONTEXT", "policy_context_status": "UNRESOLVED", "material_asks": [ask("UNSUPPORTED", [])]},
        "POS_UNRESOLVED_ASK": {"decision": "ABSTAIN", "reason_code": "UNRESOLVED_POLICY_CONTEXT", "policy_context_status": "RESOLVED", "material_asks": [ask("CONTEXT_UNRESOLVED", [])]},
        "POS_BOUNDS": dict(deepcopy(base), material_asks=[ask("SUPPORTED", list(range(1, 11))) for _ in range(8)]),
    }
    for fid, value in variants.items():
        add(fid, value, combined="COMBINED_STRUCTURAL_ACCEPT", note="Positive branch/boundary witness, no semantic inference.")
    add("POS_NUL", raw=historical["STRING_NUL"]["text"], combined="COMBINED_STRUCTURAL_ACCEPT")
    add("POS_JSON_WHITESPACE", raw=" \t\n" + historical["M1"]["text"] + "\r\n", combined="COMBINED_STRUCTURAL_ACCEPT",
        note="Raw bytes preserved; no stripping before decoder, JSON parse or adapter.")
    def change(fid, original, path, value, target, expected="REJECT", combined="EXACT_SCHEMA_REJECT", count=10):
        obj = deepcopy(original)
        node = obj
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        add(fid, obj, expected=expected, combined=combined, targets=[target], count=count,
            note="Deterministic structural probe; combinator interactions are not claimed to be isolated causes.")
    mutations = [
        ("ASK_EMPTY", ["material_asks", 0, "ask"], "", ITEM + "/properties/ask/minLength"),
        ("ASK_WHITESPACE", ["material_asks", 0, "ask"], " \t\r\n", ITEM + "/properties/ask/pattern"),
        ("ASKS_EMPTY", ["material_asks"], [], "/properties/material_asks/minItems"),
        ("ASKS_NINE", ["material_asks"], [ask("SUPPORTED", [1]) for _ in range(9)], "/properties/material_asks/maxItems"),
        ("RANK_ZERO", ["material_asks", 0, "supporting_evidence_ranks"], [0], RANKS + "/items/minimum"),
        ("RANK_ELEVEN", ["material_asks", 0, "supporting_evidence_ranks"], [11], RANKS + "/items/maximum"),
        ("RANKS_ELEVEN", ["material_asks", 0, "supporting_evidence_ranks"], list(range(1, 12)), RANKS + "/maxItems"),
        ("THEN_EMPTY", ["material_asks", 0, "supporting_evidence_ranks"], [], ITEM + "/allOf/0/then/properties/supporting_evidence_ranks/minItems"),
    ]
    for fid, path, value, target in mutations:
        change(fid, base, path, value, target)
    change("ELSE_NONEMPTY", variants["POS_INSUFFICIENT"], ["material_asks", 0, "supporting_evidence_ranks"], [1], ITEM + "/allOf/0/else/properties/supporting_evidence_ranks/maxItems")
    change("INSUFFICIENT_MISSING_TARGET", variants["POS_INSUFFICIENT"], ["material_asks"], [ask("SUPPORTED", [1])], "/oneOf/1/properties/material_asks/contains")
    change("UNRESOLVED_MISSING_TARGET", variants["POS_UNRESOLVED_ASK"], ["material_asks"], [ask("UNSUPPORTED", [])], "/oneOf/2/anyOf/1/properties/material_asks/contains")
    for branch, original in [(0, base), (1, variants["POS_INSUFFICIENT"]), (2, variants["POS_UNRESOLVED_CONTEXT"])]:
        change("BRANCH_%d_DECISION" % branch, original, ["decision"], "ABSTAIN" if branch == 0 else "ALLOW", "/oneOf/%d/properties/decision/const" % branch)
        change("BRANCH_%d_REASON" % branch, original, ["reason_code"], "UNRESOLVED_POLICY_CONTEXT" if branch == 0 else "SUPPORTED_BY_ACTIVE_POLICY", "/oneOf/%d/properties/reason_code/const" % branch)
    change("ALLOW_CONTEXT", base, ["policy_context_status"], "UNRESOLVED", "/oneOf/0/properties/policy_context_status/const")
    change("ALLOW_UNSUPPORTED", base, ["material_asks"], [ask("UNSUPPORTED", [])], "/oneOf/0/properties/material_asks/items/properties/support_status/const")
    change("INSUFFICIENT_CONTEXT", variants["POS_INSUFFICIENT"], ["policy_context_status"], "UNRESOLVED", "/oneOf/1/properties/policy_context_status/const")
    change("INSUFFICIENT_STATUS", variants["POS_INSUFFICIENT"], ["material_asks"], [ask("UNSUPPORTED", []), ask("CONTEXT_UNRESOLVED", [])], "/oneOf/1/properties/material_asks/items/properties/support_status/enum")
    change("ADAPTER_ABSENT_RANK", base, ["material_asks", 0, "supporting_evidence_ranks"], [2], RANKS + "/items/maximum", expected="ACCEPT", combined="ADAPTER_STRUCTURAL_REJECT", count=1)
    change("ADAPTER_UNSORTED", base, ["material_asks", 0, "supporting_evidence_ranks"], [2, 1], RANKS + "/uniqueItems", expected="ACCEPT", combined="ADAPTER_STRUCTURAL_REJECT", count=2)
    material = [x for x in read(SPLIT / "FROZEN_SCHEMA_CONSTRAINT_INVENTORY.json")["constraints"] if x["materiality"] == "MATERIAL"]
    matrix = []
    for row in material:
        pointer = row["pointer"]
        if pointer.startswith("/oneOf/0"):
            positive = ["M1"]
        elif pointer.startswith("/oneOf/1"):
            positive = ["POS_INSUFFICIENT"]
        elif pointer.startswith("/oneOf/2"):
            positive = ["POS_UNRESOLVED_CONTEXT", "POS_UNRESOLVED_ASK"]
        elif "/else" in pointer:
            positive = ["POS_INSUFFICIENT", "POS_UNRESOLVED_ASK"]
        else:
            positive = ["M1", "POS_INSUFFICIENT", "POS_UNRESOLVED_ASK", "POS_BOUNDS"]
        negatives = [f["id"] for f in fixtures if f["validator_expected"] == "REJECT" and any(
            target == pointer or target.startswith(pointer + "/") or pointer.startswith(target + "/") for target in f["target_pointers"])]
        matrix.append({"constraint_id": pointer, "keyword": row["keyword"], "owners": row["enforcement_owners"],
                       "planned_positive_witnesses": positive, "planned_negative_witnesses": negatives,
                       "coverage_relationship": "Actual original-validator keyword dispatch at this exact schema pointer; then/else witnessed by executed selected-branch descendants. Combinator effects may be joint; no isolated-causality claim."})
    assert len(matrix) == 64
    return {"scope": "Synthetic structural probes only; not a fresh semantic suite", "fixtures": fixtures}, {"status": "FROZEN_PROBE_PLAN", "rows": matrix}


def resolve(schema):
    from jsonschema.validators import validator_for
    from jsonschema import Draft202012Validator
    from referencing import Registry
    from referencing.exceptions import NoSuchResource
    def deny_reference(uri):
        raise NoSuchResource(ref=uri)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    cls = validator_for(schema, default=None)
    if cls is not Draft202012Validator:
        raise RuntimeError("Declared schema draft not exactly supported")
    return cls, cls(schema, registry=Registry(retrieve=deny_reference), format_checker=None)


def prepare():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASE
    assert subprocess.check_output(["git", "rev-list", "-n", "1", TAG], cwd=ROOT, text=True).strip() == BASE
    assert sha(SCHEMA) == SCHEMA_SHA
    assert "OWNER_REVIEWED / DIRECT_REGEX_V0_1_DECODER_QUALIFIED" in (CLOSURE / "FINAL_RECORD.md").read_text(encoding="utf-8")
    frozen = dict(read(CLOSURE / "CONTRACT_ALIGNED_ORACLE.json")["immutable_inputs_sha256"])
    for name, digest in frozen.items():
        assert sha(ROOT / name) == digest, name
    paths = list(CLOSURE.iterdir()) + [SCHEMA, SPLIT / "FROZEN_SCHEMA_CONSTRAINT_INVENTORY.json", SPLIT / "ADAPTER_RESPONSIBILITY_CONTRACT.md",
             Path(__file__), ROOT / "gateway/domain/evaluation/answerability/gates/semantic_gate_v2.py",
             ROOT / "gateway/domain/evaluation/answerability/gates/semantic_gate.py", ROOT / "gateway/domain/evaluation/answerability/answerability_contracts.py"]
    for path in paths:
        if path.is_file():
            frozen[path.relative_to(ROOT).as_posix()] = sha(path)
    if ART.exists():
        raise RuntimeError("Refuse existing phase directory")
    ART.mkdir()
    packages = inventory()
    identity = {"status": "PACKAGE_IDENTITY_FROZEN_BEFORE_SCHEMA_CHECK", "frozen_package_utc": now(), "base_commit": BASE, "base_tag": TAG,
                "entry_git_status": "clean before new helper creation", "package": "jsonschema", "version": metadata.version("jsonschema"),
                "referencing_version": metadata.version("referencing"), "pre_environment": {"packages": packages, "pip_check": pip_check()},
                "schema_sha256": SCHEMA_SHA, "draft": read(SCHEMA)["$schema"], "helper_sha256": sha(__file__), "immutable_inputs_sha256": frozen,
                "configuration": {"format_checker": None, "format_reason": "No format keyword in authoritative schema; no implicit checker",
                                  "reference_resolution": "Empty referencing Registry with deny-all external retrieval; local references supported; no $ref present in frozen inventory",
                                  "parser": "stdlib json.loads over unchanged UTF-8 bytes; duplicate keys/nonfinite constants rejected; leading/trailing JSON whitespace accepted",
                                  "validator": "Unmodified stock validator_for(schema, default=None); explicitly require Draft202012Validator; no substitute schema/type checker/coercion"}}
    save("VALIDATOR_IDENTITY.json", identity, exclusive=True)
    schema = read(SCHEMA)
    try:
        cls, _ = resolve(schema)
        identity["validator_class"] = cls.__module__ + "." + cls.__name__
        try:
            cls.check_schema(schema)
            identity["schema_check"] = "SCHEMA_CHECK_PASS"
        except Exception as exc:
            from jsonschema import SchemaError
            identity.update(schema_check="SCHEMA_CHECK_FAIL" if isinstance(exc, SchemaError) else "SCHEMA_CHECK_ERROR", error=repr(exc))
            raise
        assert identity["pre_environment"]["pip_check"]["returncode"] == 0
    except Exception as exc:
        identity.update(status="EXACT_VALIDATOR_SELECTION_BLOCKED", error=repr(exc))
        save("VALIDATOR_IDENTITY.json", identity)
        print(identity["status"], identity["error"])
        return
    fixtures, matrix = fixtures_and_matrix()
    save("VALIDATOR_FIXTURES.json", fixtures, exclusive=True)
    save("CONSTRAINT_COVERAGE_MATRIX.json", matrix, exclusive=True)
    protocol = """# Exact validator and combined structural qualification

Sole candidate: installed python-jsonschema; freeze exact installed package inventory, draft/class, untouched authoritative raw schema, configuration, helper, fixture expectations and coverage plan before any fixture validation. No package mutation. check_schema must pass first. No remote reference resolution, format-checker inference, schema substitution or repair.

Use standard strict JSON parsing on preserved bytes, with duplicate/nonfinite rejection and legal JSON whitespace. For validator-only probes run the actual stock Draft202012Validator on the full original schema. Capture full nested errors and exact keyword-dispatch pointers through read-only Python profiling; do not wrap/replace validator functions or modify validation semantics. then/else coverage is evidenced by execution within the selected branch. Coverage requires every material pointer to have a planned witness actually executed there with the expected fixture verdict. Container/combinator and branch effects are interaction-aware, never claimed as isolated causes.

All frozen fixture expectations, targets, synthetic GateInput counts and raw byte hashes precede results. Reuse historical M1-M8 and Rxx/delegated raw bytes; author only deterministic synthetic structural variants. Record absent actual keywords instead of inventing tests for substitute schemas. Every advanced class present needs empirical evidence; directed negative error paths accompany dispatch coverage.

Run combined fixtures independently in order: unchanged V0.1 decoder FSM language (using the already-qualified JSON-whitespace closure evidence) -> strict standard JSON parse -> same exact raw-schema validator -> unchanged V2 canonicalize/adapter -> frozen GateOutput. Decoder rejection skips later layers; exact rejection yields STRUCTURAL_INVALID, adapter NOT_RUN, semantic NOT_RUN, no repair. Exceptions are separate ERROR dispositions, never REJECT. Actual combined adapter checks use original raw bytes, synthetic evidence only, and preserve rank bindings/decision. Record all four required paths.

The decoder is frozen, qualified, and not researched or modified here. One local tokenizer and one Index integrate it; closure proof is reused only for observed terminal states with matching allowed-token identities and destinations under identical regex/tokenizer/environment. An unknown end state blocks acceptance; no new closure research or fallback. Never require sole EOS or advance EOS. No model initialization, generation, forward, retrieval, DEVELOPMENT or either HELD_OUT. Fresh semantic suite remains NOT YET AUTHORED.

One validator-only pass plus one combined pass for designated fixtures, explicitly separate counts. No automatic retries or post-result tuning. Preserve partial results. Inventory/pip check before/after, unchanged historical files, adapter and decoder hashes. Final success requires 64/64 actual material-pointer coverage, expected validator results, advanced cases and all four combined paths, with zero errors and package drift. No commit/tag or Qwen smoke.
"""
    (ART / "VALIDATOR_PROTOCOL.md").write_bytes(protocol.encode())
    identity.update(status="FROZEN_BEFORE_RESULT_BEARING_FIXTURES", frozen_utc=now(), fixtures_sha256=sha(ART / "VALIDATOR_FIXTURES.json"),
                    coverage_plan_sha256=sha(ART / "CONSTRAINT_COVERAGE_MATRIX.json"), protocol_sha256=sha(ART / "VALIDATOR_PROTOCOL.md"),
                    fixture_count=len(fixtures["fixtures"]), combined_fixture_count=sum(f["combined_expected"] is not None for f in fixtures["fixtures"]))
    save("VALIDATOR_IDENTITY.json", identity)
    print("FROZEN", identity["version"], identity["validator_class"], identity["schema_check"], "fixtures", identity["fixture_count"])


def validate_with_trace(validator, schema, value):
    locations = {}
    def index(node, path=""):
        if isinstance(node, dict):
            locations[id(node)] = path
            for key, child in node.items():
                index(child, path + "/" + key.replace("~", "~0").replace("/", "~1"))
        elif isinstance(node, list):
            for i, child in enumerate(node):
                index(child, path + "/" + str(i))
    index(schema)
    codes = {function.__code__: keyword for keyword, function in validator.VALIDATORS.items()}
    visited = set()
    def profile(frame, event, arg):
        if event == "call" and frame.f_code in codes:
            node = frame.f_locals.get("schema")
            if id(node) in locations:
                visited.add(locations[id(node)] + "/" + codes[frame.f_code])
    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        errors = list(validator.iter_errors(value))
    finally:
        sys.setprofile(previous)
    for pointer in list(visited):
        for branch in ["then", "else"]:
            marker = "/" + branch + "/"
            if marker in pointer:
                visited.add(pointer.split(marker, 1)[0] + "/" + branch)
    def error_record(error):
        return {"keyword": error.validator, "schema_path": list(error.absolute_schema_path), "instance_path": list(error.absolute_path),
                "message": error.message, "context": [error_record(child) for child in error.context]}
    return {"result": "REJECT" if errors else "ACCEPT", "errors": [error_record(e) for e in errors], "visited_constraint_pointers": sorted(visited)}


def execute():
    if (ART / "QUALIFICATION_RECEIPT.json").exists():
        raise RuntimeError("Refuse overwrite/retry")
    identity = read(ART / "VALIDATOR_IDENTITY.json")
    assert identity["status"] == "FROZEN_BEFORE_RESULT_BEARING_FIXTURES"
    assert sha(__file__) == identity["helper_sha256"] and sha(SCHEMA) == SCHEMA_SHA
    assert sha(ART / "VALIDATOR_FIXTURES.json") == identity["fixtures_sha256"]
    assert sha(ART / "CONSTRAINT_COVERAGE_MATRIX.json") == identity["coverage_plan_sha256"]
    for name, digest in identity["immutable_inputs_sha256"].items():
        assert sha(ROOT / name) == digest, name
    q = {"status": "STARTED", "started_utc": now(), "identity_sha256": sha(ART / "VALIDATOR_IDENTITY.json"),
         "counters": {"validator_only_attempts": 0, "combined_attempts": 0, "tokenizer_loads": 0, "Index_constructions": 0,
                      "repair": 0, "retry": 0, "package_mutations": 0, "model_initialization": 0, "generate": 0, "forward": 0,
                      "DEVELOPMENT": 0, "retrieval": 0, "eos_advance_calls": 0},
         "phase_2h_held_out_access": False, "phase_2g_private_heldout_access": False, "fresh_semantic_suite": "NOT YET AUTHORED", "socket_events": []}
    vr, cr = {"rows": []}, {"rows": []}
    matrix = read(ART / "CONSTRAINT_COVERAGE_MATRIX.json")
    def checkpoint():
        save("QUALIFICATION_RECEIPT.json", q)
        save("VALIDATOR_RESULTS.json", vr)
        save("COMBINED_PIPELINE_RESULTS.json", cr)
    checkpoint()
    before = inventory()
    try:
        assert before == identity["pre_environment"]["packages"], "Environment changed since freeze"
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", PYTHONDONTWRITEBYTECODE="1",
                          OUTLINES_CACHE_DIR=str(ROOT / ".cache/phase2h-direct-regex-runtime"))
        def guard(event, args):
            if event.startswith("socket."):
                q["socket_events"].append({"event": event, "args": str(args)})
                if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "socket.sendto"}:
                    raise RuntimeError("Offline qualification forbids outbound operations")
                if event == "socket.bind" and str(args[1][0]) not in {"::1", "127.0.0.1"}:
                    raise RuntimeError("Non-loopback bind forbidden")
            if event == "open" and isinstance(args[0], str) and args[0].lower().endswith((".safetensors", "pytorch_model.bin")):
                raise RuntimeError("Model weight access forbidden")
        sys.addaudithook(guard)
        schema = read(SCHEMA)
        cls, validator = resolve(schema)
        assert cls.__module__ + "." + cls.__name__ == identity["validator_class"]
        fixtures = read(ART / "VALIDATOR_FIXTURES.json")["fixtures"]
        for f in fixtures:
            row = {"fixture_id": f["id"], "expected": f["validator_expected"], "result": "STARTED", "mode": "VALIDATOR_ONLY"}
            vr["rows"].append(row)
            q["counters"]["validator_only_attempts"] += 1
            checkpoint()
            try:
                raw = bytes.fromhex(f["raw_utf8_hex"])
                assert hashlib.sha256(raw).hexdigest() == f["raw_sha256"]
                value = strict_parse(raw)
                row["JSON_parse"] = "PASS"
                row.update(validate_with_trace(validator, schema, value))
                row["matches_expectation"] = row["result"] == row["expected"]
            except Exception as exc:
                row.update(result="ERROR", error=repr(exc), traceback=traceback.format_exc(), matches_expectation=False)
            checkpoint()
        by_id = {r["fixture_id"]: r for r in vr["rows"]}
        for coverage in matrix["rows"]:
            witnesses = coverage["planned_positive_witnesses"] + coverage["planned_negative_witnesses"]
            coverage["observed_witnesses"] = [fid for fid in witnesses if by_id[fid]["matches_expectation"] and coverage["constraint_id"] in by_id[fid].get("visited_constraint_pointers", [])]
            coverage["covered"] = bool(coverage["observed_witnesses"])
        matrix.update(status="RESULT_BEARING_COVERAGE", frozen_plan_sha256=identity["coverage_plan_sha256"],
                      covered_count=sum(r["covered"] for r in matrix["rows"]), total=64)
        save("CONSTRAINT_COVERAGE_MATRIX.json", matrix)
        vr["correct"] = sum(r["matches_expectation"] for r in vr["rows"])
        vr["errors"] = sum(r["result"] == "ERROR" for r in vr["rows"])
        q["validator_qualified"] = vr["correct"] == len(fixtures) and matrix["covered_count"] == 64
        if not q["validator_qualified"]:
            q["status"] = "EXACT_VALIDATOR_QUALIFICATION_FAILED"
            return
        from outlines_core import Guide
        from outlines.backends.outlines_core import OutlinesCoreBackend
        from outlines.models.transformers import TransformerTokenizer
        from transformers import AutoTokenizer
        from gateway.domain.evaluation.answerability.gates import semantic_gate_v2 as adapter
        from gateway.domain.evaluation.answerability.answerability_contracts import ContractError
        historical = read(OLD / "STRUCTURAL_RESULTS.json")
        token_identity = historical["FSM"]["tokenizer_identity"]
        snapshot = Path(token_identity["snapshot_path"])
        for name, digest in token_identity["files_sha256"].items():
            assert sha(snapshot / name) == digest
        q["tokenizer_identity"] = token_identity
        q["counters"]["tokenizer_loads"] += 1
        checkpoint()
        tok = AutoTokenizer.from_pretrained(str(snapshot), revision=token_identity["revision"], local_files_only=True, trust_remote_code=False, use_fast=True)
        wrapped = TransformerTokenizer(tok)
        eos = wrapped.eos_token_id
        vocabulary = OutlinesCoreBackend.create_outlines_core_vocabulary(wrapped.get_vocab(), eos, wrapped.eos_token, wrapped.convert_token_to_string)
        backend = object.__new__(OutlinesCoreBackend)
        backend.vocabulary, backend.eos_token_id, backend.tensor_library_name = vocabulary, eos, "torch"
        q["counters"]["Index_constructions"] += 1
        checkpoint()
        index = backend.get_regex_logits_processor((OLD / "DECODER_ENFORCEMENT_REGEX.txt").read_bytes().decode()).index
        closure = read(CLOSURE / "WHITESPACE_CLOSURE_GRAPH.json")
        qualified_states = {n["state"] for n in closure["states"]}
        # Verify correspondence of the existing proof to this same frozen Index;
        # no new root or closure search is permitted or performed here.
        for state in qualified_states:
            saved_edges = [e for e in closure["edges"] if e["source_state"] == state]
            assert set(index.get_allowed_tokens(state)) == {e["token_id"] for e in saved_edges} | {eos}
            assert index.is_final_state(state)
            assert all(index.get_next_state(state, e["token_id"]) == e["destination_state"] for e in saved_edges)
        for f in fixtures:
            if f["combined_expected"] is None:
                continue
            row = {"fixture_id": f["id"], "expected": f["combined_expected"], "disposition": "STARTED", "raw_sha256": f["raw_sha256"],
                   "decoder": "NOT_RUN", "JSON_parse": "NOT_RUN", "exact_validator": "NOT_RUN", "adapter": "NOT_RUN",
                   "semantic_evaluation": "NOT_RUN", "repair": 0, "generation_retry": 0}
            cr["rows"].append(row)
            q["counters"]["combined_attempts"] += 1
            checkpoint()
            try:
                raw = bytes.fromhex(f["raw_utf8_hex"])
                guide = Guide(index)
                ids = tok.encode(raw.decode('utf-8'), add_special_tokens=False)
                traversed = 0
                for tid in ids:
                    if tid == eos:
                        raise ValueError("EOS inside raw content")
                    if tid not in guide.get_tokens():
                        break
                    guide.advance(token_id=tid, return_tokens=False)
                    traversed += 1
                row.update(token_count=len(ids), content_tokens_advanced=traversed, final_state=guide.get_state())
                if traversed != len(ids) or not guide.is_finished() or eos not in guide.get_tokens():
                    row.update(decoder="REJECT", disposition="DECODER_STRUCTURAL_REJECT")
                else:
                    assert guide.get_state() in qualified_states, "Unknown accepting state: no new decoder research authorized"
                    row["decoder"] = "ACCEPT"
                    try:
                        value = strict_parse(raw)
                        row["JSON_parse"] = "PASS"
                    except (ValueError, UnicodeError) as exc:
                        row.update(JSON_parse="FAIL", disposition="JSON_PARSE_FAILED", parse_error=repr(exc))
                    if row["JSON_parse"] == "PASS":
                        assessment = validate_with_trace(validator, schema, value)
                        row["exact_validator"] = assessment["result"]
                        row["exact_schema_errors"] = assessment["errors"]
                        if assessment["result"] == "REJECT":
                            row.update(disposition="EXACT_SCHEMA_REJECT", structural_status="STRUCTURAL_INVALID")
                        else:
                            gate_input = synthetic_input(f["evidence_count"])
                            try:
                                canonical = adapter.canonicalize(raw, gate_input)
                                row.update(adapter="ACCEPT", disposition="COMBINED_STRUCTURAL_ACCEPT", gate_output=asdict(canonical.gate_output()),
                                           rank_bindings=[asdict(b) for b in canonical.rank_bindings])
                                assert row["gate_output"] == {"decision": value["decision"], "reason_code": value["reason_code"]}
                                for binding in canonical.rank_bindings:
                                    assert binding.canonical_identity == gate_input.evidence[binding.evidence_rank - 1].identity
                            except ContractError as exc:
                                row.update(adapter="REJECT", disposition="ADAPTER_STRUCTURAL_REJECT", adapter_error=str(exc), structural_status="STRUCTURAL_INVALID")
                row["matches_expectation"] = row["disposition"] == row["expected"]
            except Exception as exc:
                row.update(disposition="ERROR", error=repr(exc), traceback=traceback.format_exc(), matches_expectation=False)
            checkpoint()
        required = ["DECODER_STRUCTURAL_REJECT", "EXACT_SCHEMA_REJECT", "ADAPTER_STRUCTURAL_REJECT", "COMBINED_STRUCTURAL_ACCEPT"]
        q["four_path_counts"] = {path: sum(row["disposition"] == path for row in cr["rows"]) for path in required}
        cr["correct"] = sum(r["matches_expectation"] for r in cr["rows"])
        cr["errors"] = sum(r["disposition"] == "ERROR" for r in cr["rows"])
        q["status"] = "EXACT_VALIDATOR_AND_COMBINED_STRUCTURE_QUALIFIED" if cr["correct"] == len(cr["rows"]) and all(q["four_path_counts"].values()) else "COMBINED_STRUCTURE_QUALIFICATION_FAILED"
    except Exception as exc:
        q.update(status="COMBINED_STRUCTURE_QUALIFICATION_FAILED" if q.get("validator_qualified") else "EXACT_VALIDATOR_QUALIFICATION_FAILED",
                 error=repr(exc), traceback=traceback.format_exc())
    finally:
        after = inventory()
        q["environment"] = {"pre": identity["pre_environment"], "post": {"packages": after, "pip_check": pip_check()},
                            "additions": sorted(set(after) - set(before)), "removals": sorted(set(before) - set(after)),
                            "drift": {n: {"before": v, "after": after.get(n)} for n, v in before.items() if after.get(n) != v},
                            "unchanged": before == after}
        q["frozen_identity_changes"] = [name for name, digest in identity["immutable_inputs_sha256"].items() if sha(ROOT / name) != digest]
        if before != after or q["environment"]["post"]["pip_check"]["returncode"] != 0 or q["frozen_identity_changes"]:
            q["status"] = "COMBINED_STRUCTURE_QUALIFICATION_FAILED" if q.get("validator_qualified") else "EXACT_VALIDATOR_QUALIFICATION_FAILED"
            q["integrity_failure"] = True
        q["finished_utc"] = now()
        checkpoint()
        print(q["status"], "validator", vr.get("correct"), "/", len(vr["rows"]), "coverage", matrix.get("covered_count"), "combined", cr.get("correct"), "/", len(cr["rows"]))
        if q.get("error"):
            print(q["error"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--prepare"]:
        prepare()
    elif sys.argv[1:] == ["--execute"]:
        execute()
    else:
        raise SystemExit("Use --prepare then --execute; no retries.")
