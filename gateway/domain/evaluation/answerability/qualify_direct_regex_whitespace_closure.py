"""Frozen V0.1 qualification by exhaustive JSON-whitespace suffix closure."""
from collections import deque, Counter
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
ART = ROOT / "artifacts/answerability_semantic_v2_1_whitespace_closure"
OLD = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_decoder"
DIAG = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_v02"
BASE = "9c4ccf2c347e86abc0abd4f97a3aca78635650f0"
TAG = "answerability-semantic-v2_1-direct-regex-v0.3-terminality-inconclusive"
JSON_WS = frozenset((0x20, 0x09, 0x0A, 0x0D))


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(name, value, exclusive=False):
    with (ART / name).open("xb" if exclusive else "wb") as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode())


def classify(raw, special):
    if special:
        return "SPECIAL_TOKEN"
    if not raw:
        return "EMPTY_TOKEN"
    return "JSON_WHITESPACE_ONLY" if all(byte in JSON_WS for byte in raw) else "NON_WHITESPACE"


def reachable(start, adjacency):
    visited, queue = set(), deque([start])
    while queue:
        state = queue.popleft()
        if state in visited:
            continue
        visited.add(state)
        queue.extend(sorted(adjacency.get(state, set()) - visited))
    return visited


def analyze_graph(roots, nodes, edges):
    """Pure saved-graph analysis; no tokenizer, Index, Guide or model calls."""
    adjacency = {state: set() for state in nodes}
    reverse = {state: set() for state in nodes}
    for edge in edges:
        source, destination = edge["source_state"], edge["destination_state"]
        adjacency[source].add(destination)
        reverse[destination].add(source)
    all_reach = {state: reachable(state, adjacency) for state in nodes}
    remaining, components = set(nodes), []
    while remaining:
        start = min(remaining)
        component = {other for other in all_reach[start] if start in all_reach[other]}
        remaining -= component
        if len(component) > 1 or start in adjacency[start]:
            cycle_edges = [e for e in edges if e["source_state"] in component and e["destination_state"] in component]
            components.append({"states": sorted(component), "internal_edge_count": len(cycle_edges),
                               "all_edges_JSON_WHITESPACE_ONLY": all(e["classification"] == "JSON_WHITESPACE_ONLY" for e in cycle_edges)})
    eos_nodes = {state for state, node in nodes.items() if node["is_final"] and node["eos_allowed"]}
    can_terminate = set()
    for state in sorted(eos_nodes):
        can_terminate |= reachable(state, reverse)
    proofs = []
    for root in roots:
        states = all_reach[root]
        region_edges = [e for e in edges if e["source_state"] in states]
        counts = Counter(e["classification"] for e in region_edges)
        final_eos = all(not nodes[s]["is_final"] or nodes[s]["eos_allowed"] for s in states)
        terminates = states <= can_terminate
        passed = (nodes[root]["is_final"] and nodes[root]["eos_allowed"] and final_eos and terminates
                  and all(e["classification"] == "JSON_WHITESPACE_ONLY" for e in region_edges))
        proofs.append({"root_state": root, "reachable_states": sorted(states), "non_eos_transition_count": len(region_edges),
                       "class_counts": dict(counts), "all_accepting_states_allow_eos": final_eos,
                       "eos_reachable_from_all_continuation_states": terminates, "closure_pass": passed})
    return {"root_proofs": proofs, "cyclic_components": components,
            "cycle_internal_edges": sum(x["internal_edge_count"] for x in components),
            "all_states_can_reach_eos": set(nodes) <= can_terminate,
            "closure_pass": bool(proofs) and all(x["closure_pass"] for x in proofs)}


def self_check():
    assert classify(b" \t\r\n", False) == "JSON_WHITESPACE_ONLY"
    assert classify(b"", False) == "EMPTY_TOKEN"
    assert classify(b" ", True) == "SPECIAL_TOKEN"
    assert classify("\u00a0".encode(), False) == "NON_WHITESPACE"
    assert classify(b"\x0b", False) == "NON_WHITESPACE"
    assert classify(b" A", False) == "NON_WHITESPACE"
    nodes = {1: {"is_final": True, "eos_allowed": True}, 2: {"is_final": True, "eos_allowed": True}}
    edges = [{"source_state": 1, "destination_state": 2, "classification": "JSON_WHITESPACE_ONLY"},
             {"source_state": 2, "destination_state": 2, "classification": "JSON_WHITESPACE_ONLY"}]
    assert analyze_graph([1, 2], nodes, edges)["closure_pass"]
    assert analyze_graph([1], nodes, edges)["cycle_internal_edges"] == 1
    edges[1]["classification"] = "NON_WHITESPACE"
    assert not analyze_graph([1], nodes, edges)["closure_pass"]
    edges[1]["classification"] = "JSON_WHITESPACE_ONLY"
    nodes[2]["eos_allowed"] = False
    assert not analyze_graph([1], nodes, edges)["closure_pass"]


def prepare():
    self_check()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASE
    assert subprocess.check_output(["git", "rev-list", "-n", "1", TAG], cwd=ROOT, text=True).strip() == BASE
    if ART.exists():
        raise RuntimeError("Refuse existing qualification directory")
    diagnostic = read(DIAG / "TERMINALITY_DIAGNOSTIC.json")
    frozen = dict(diagnostic["immutable_inputs_sha256"])
    for name, digest in frozen.items():
        assert sha(ROOT / name) == digest, name
    for path in list(DIAG.iterdir()) + [Path(__file__)]:
        if path.is_file():
            frozen[path.relative_to(ROOT).as_posix()] = sha(path)
    assert sha(DIAG / "FINAL_RECORD.md") == "652dd77f00ba2ee72529e7a892854b73955ea6085cdf9f7bd87ed3d03d47a31f"
    assert "OWNER_REVIEWED / DIRECT_REGEX_TERMINALITY_DIAGNOSTIC_INCONCLUSIVE" in (DIAG / "FINAL_RECORD.md").read_text(encoding="utf-8")
    fixtures = read(OLD / "STRUCTURAL_FIXTURES.json")
    previous = read(OLD / "STRUCTURAL_RESULTS.json")
    negatives = [f["id"] for f in fixtures["fixtures"] if f["expected"] == "REJECT"]
    positives = [f["id"] for f in fixtures["fixtures"] if f["expected"] == "ACCEPT"]
    old_rows = {x["id"]: x for x in previous["FSM"]["rows"]}
    assert len(positives) == 34 and len(negatives) == 30
    assert all(old_rows[i]["result"] == "REJECT" and old_rows[i]["traversal"] == "REJECT" for i in negatives)
    assert previous["textual_matches"] == 64 and previous["textual_errors"] == 0
    ART.mkdir()
    protocol = """# Frozen V0.1 JSON Whitespace Closure Qualification

Freeze this protocol, the contract-aligned oracle, helper, and exact historical identities before execution. No regex/contract/package mutation. No V0.2 or end-anchor insertion. No model construction, forward, generation, benchmark/retrieval access, or exact-validator qualification.

Traverse each of the frozen 34 positive fixtures exactly once using one local frozen tokenizer and one V0.1 Index. Verify identical historical token IDs and input bytes. Observe the final state, final-state flag and EOS membership; never advance EOS. Errors remain errors. Reduce the resulting final states to sorted unique roots.

Deterministically traverse the full finite non-EOS transition graph from those roots. Visit each state once globally, share overlapping subgraphs, and compute a separate reachability proof for each root. Sort states/token IDs, track visited states, record every edge and its exact Vocabulary transition bytes, destination and destination final-state flag. Do not normalize token text. Empty, non-EOS special tokens, and non-whitespace tokens fail the closure gate. EOS is termination metadata, never whitespace.

The sole whitespace byte set is {0x20,0x09,0x0A,0x0D}. Classification uses non-empty exact UTF-8 bytes of the same string supplied to the official Outlines Vocabulary constructor; no Unicode whitespace predicate or regex shorthand. Record token spellings and special-token flags separately.

All reachable non-EOS edges must be JSON_WHITESPACE_ONLY. All accepting continuation states must allow EOS, and every reachable continuation state must have a path to an accepting EOS opportunity. Resolve graph cycles by strongly connected components; loops pass only with whitespace-only internal edges. Operational implication: MODEL_MAY_EMIT_TRAILING_WHITESPACE_UNTIL_STOP_LIMIT. This is a runtime-efficiency concern, not semantic expansion.

The frozen corrected oracle accepts a complete positive iff content traversal passes, its state is final, EOS is allowed, and exhaustive continuation closure contains only JSON whitespace. A singleton [EOS] list is not required. Preserve every earlier outcome under its historical oracle.

Carry forward historical 64/64 textual results and 30 correct negative FSM results without rerun. Their invalid paths were rejected during traversal; this new oracle changes only the treatment of already-accepting valid-object states with whitespace-only suffix closure and cannot broaden those structurally invalid fixture paths. Combine 34 current positives and 30 historical negatives, and evaluate all 18 frozen rule-pair associations.

Any non-whitespace edge gives DIRECT_REGEX_V0_1_WHITESPACE_CLOSURE_FAILED. Empty/special anomalies also fail the required closure gate. Unresolved exhaustive traversal or runtime errors give DIRECT_REGEX_V0_1_WHITESPACE_CLOSURE_INCONCLUSIVE. Environment/provenance failure gives DIRECT_REGEX_V0_1_CLOSURE_QUALIFICATION_BLOCKED. Only all gates passing yields DIRECT_REGEX_V0_1_DECODER_QUALIFIED. No retries, repair, automatic V0.2, or another recovery.

Save pre/post raw package-version/METADATA/RECORD inventories and pip-check results in QUALIFICATION_RECEIPT.json. Keep exactly the seven authorized artifacts and this one helper. Checkpoint partial execution; never overwrite an earlier attempted run. Stop for owner review; no commit or tag.
"""
    (ART / "WHITESPACE_CLOSURE_PROTOCOL.md").write_bytes(protocol.encode())
    save("CONTRACT_ALIGNED_ORACLE.json", {
        "identity": "V0_1_CONTRACT_ALIGNED_JSON_WHITESPACE_CLOSURE_ORACLE", "status": "FROZEN_BEFORE_QUALIFICATION",
        "frozen_utc": now(), "base_commit": BASE, "base_tag": TAG, "entry_git_status": "clean before this helper was created",
        "helper_sha256": sha(__file__), "protocol_sha256": sha(ART / "WHITESPACE_CLOSURE_PROTOCOL.md"),
        "immutable_inputs_sha256": frozen, "json_whitespace_bytes": sorted(JSON_WS),
        "positive_ids": positives, "historical_negative_ids": negatives,
        "conditions": ["A: All content tokens traverse successfully", "B: Resulting state is final", "C: EOS is allowed",
                       "D: Exhaustive reachable non-EOS edges are non-empty exact JSON whitespace bytes, never non-EOS special tokens",
                       "E: No non-whitespace semantic continuation is reachable; termination remains available"],
        "singleton_eos_required": False, "advance_eos_forbidden": True, "retries": 0,
        "scope": "Frozen 34 positive fixture states; exhaustive finite token graph closure from all unique roots. No inference about unvisited roots.",
        "pre_execution_pure_checks": "PASS: exact bytes, empty/special handling, non-JSON Unicode/vertical-tab rejection, synthetic whitespace cycle, downstream non-whitespace and missing-termination rejection. No real FSM or regex execution."}, exclusive=True)
    print("Oracle frozen", sha(ART / "CONTRACT_ALIGNED_ORACLE.json"), "helper", sha(__file__))


def execute():
    if (ART / "QUALIFICATION_RECEIPT.json").exists():
        raise RuntimeError("Refuse overwrite or retry")
    oracle = read(ART / "CONTRACT_ALIGNED_ORACLE.json")
    for name, digest in oracle["immutable_inputs_sha256"].items():
        assert sha(ROOT / name) == digest, name
    assert sha(__file__) == oracle["helper_sha256"]
    assert sha(ART / "WHITESPACE_CLOSURE_PROTOCOL.md") == oracle["protocol_sha256"]
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASE
    q = {"status": "STARTED", "started_utc": now(), "oracle_sha256": sha(ART / "CONTRACT_ALIGNED_ORACLE.json"),
         "helper_sha256": sha(__file__), "counters": {"tokenizer_loads": 0, "Index_constructions": 0, "positive_fixture_executions": 0,
         "negative_fixture_reruns": 0, "textual_fixture_reruns": 0, "graph_states_expanded": 0, "graph_edges_inspected": 0,
         "eos_advance_calls": 0, "retries": 0, "package_mutations": 0, "model_initialization": 0, "generate": 0,
         "forward": 0, "DEVELOPMENT": 0, "retrieval": 0}, "socket_events": [],
         "phase_2h_held_out_access": False, "phase_2g_private_heldout_access": False,
         "fresh_v2_1_semantic_suite": "NOT YET AUTHORED", "exact_validator_qualification": "NOT_BEGUN"}
    states = {"status": "STARTED", "rows": [], "unique_accepting_states": []}
    graph = {"status": "NOT_STARTED", "roots": [], "states": [], "edges": []}
    def checkpoint():
        save("QUALIFICATION_RECEIPT.json", q)
        save("ACCEPTING_STATE_INVENTORY.json", states)
        save("WHITESPACE_CLOSURE_GRAPH.json", graph)
    checkpoint()
    before = inventory()
    q["environment"] = {"pre": {"packages": before, "pip_check": pip_check()}}
    checkpoint()
    try:
        if before != read(DIAG / "TERMINALITY_DIAGNOSTIC.json")["environment"]["post"]["packages"] or q["environment"]["pre"]["pip_check"]["returncode"] != 0:
            q["status"] = "DIRECT_REGEX_V0_1_CLOSURE_QUALIFICATION_BLOCKED"
            return
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                          PYTHONDONTWRITEBYTECODE="1", OUTLINES_CACHE_DIR=str(ROOT / ".cache/phase2h-direct-regex-runtime"))
        def guard(event, args):
            if event.startswith("socket."):
                q["socket_events"].append({"event": event, "args": str(args)})
                if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "socket.sendto"}:
                    raise RuntimeError("Offline closure forbids outbound socket operations")
                if event == "socket.bind" and str(args[1][0]) not in {"::1", "127.0.0.1"}:
                    raise RuntimeError("Non-loopback bind forbidden")
            if event == "open" and isinstance(args[0], str) and args[0].lower().endswith((".safetensors", "pytorch_model.bin")):
                raise RuntimeError("Model weights forbidden")
        sys.addaudithook(guard)
        from outlines_core import Guide
        from outlines.backends.outlines_core import OutlinesCoreBackend
        from outlines.models.transformers import TransformerTokenizer
        from transformers import AutoTokenizer
        assert metadata.version("outlines_core") == "0.2.14" and metadata.version("outlines") == "1.3.3"
        historical = read(OLD / "STRUCTURAL_RESULTS.json")
        old_rows = {x["id"]: x for x in historical["FSM"]["rows"]}
        fixture_set = read(OLD / "STRUCTURAL_FIXTURES.json")
        fixtures = {x["id"]: x for x in fixture_set["fixtures"]}
        identity = historical["FSM"]["tokenizer_identity"]
        snapshot = Path(identity["snapshot_path"])
        for name, digest in identity["files_sha256"].items():
            assert sha(snapshot / name) == digest, name
        q["tokenizer_identity"] = identity
        c = q["counters"]
        c["tokenizer_loads"] += 1
        checkpoint()
        tok = AutoTokenizer.from_pretrained(str(snapshot), revision=identity["revision"], local_files_only=True, trust_remote_code=False, use_fast=True)
        wrapped = TransformerTokenizer(tok)
        eos = wrapped.eos_token_id
        assert eos == historical["FSM"]["eos_token_id"]
        vocab = wrapped.get_vocab()
        strings = {tid: wrapped.convert_token_to_string(token) for token, tid in vocab.items()}
        spellings = {tid: token for token, tid in vocab.items()}
        special_ids = set(tok.all_special_ids)
        q["special_token_policy"] = {"eos_id": eos, "all_special_ids": sorted(special_ids),
                                     "eos": "Termination metadata; never advanced/classified as whitespace",
                                     "other_special": "SPECIAL_TOKEN; unexpected if reachable; fails closure"}
        vocabulary = OutlinesCoreBackend.create_outlines_core_vocabulary(vocab, eos, wrapped.eos_token, wrapped.convert_token_to_string)
        backend = object.__new__(OutlinesCoreBackend)
        backend.vocabulary, backend.eos_token_id, backend.tensor_library_name = vocabulary, eos, "torch"
        c["Index_constructions"] += 1
        checkpoint()
        index = backend.get_regex_logits_processor((OLD / "DECODER_ENFORCEMENT_REGEX.txt").read_bytes().decode("utf-8")).index
        for fid in oracle["positive_ids"]:
            f = fixtures[fid]
            row = {"fixture_id": fid, "fixture_sha256": f["input_sha256"], "result": "STARTED", "eos_token_id": eos}
            states["rows"].append(row)
            c["positive_fixture_executions"] += 1
            checkpoint()
            try:
                assert hashlib.sha256(f["text"].encode()).hexdigest() == f["input_sha256"]
                ids = tok.encode(f["text"], add_special_tokens=False)
                assert ids == old_rows[fid]["tokenization"]["token_ids"]
                assert tok.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) == f["text"]
                row.update(token_ids=ids, token_count=len(ids), historical_tokenization_identical=True)
                guide = Guide(index)
                advanced = 0
                for tid in ids:
                    if tid == eos:
                        raise ValueError("EOS inside frozen content")
                    if tid not in guide.get_tokens():
                        row.update(rejected_token_id=tid, rejected_position=advanced)
                        break
                    guide.advance(token_id=tid, return_tokens=False)
                    advanced += 1
                row.update(content_tokens_advanced=advanced, content_traversal="PASS" if advanced == len(ids) else "REJECT",
                           final_state=guide.get_state(), is_finished=bool(guide.is_finished()), eos_allowed=eos in guide.get_tokens(),
                           result="AWAITING_CLOSURE" if advanced == len(ids) and guide.is_finished() and eos in guide.get_tokens() else "REJECT")
            except Exception as exc:
                row.update(result="ERROR", error=repr(exc), traceback=traceback.format_exc())
            checkpoint()
        roots = sorted({r["final_state"] for r in states["rows"] if r.get("content_traversal") == "PASS" and r.get("is_finished")})
        states.update(status="CONTENT_TRAVERSAL_COMPLETE", unique_accepting_states=roots)
        graph.update(status="TRAVERSING", roots=roots)
        nodes, queue, scheduled = {}, deque(roots), set(roots)
        while queue:
            source = queue.popleft()
            allowed = sorted(index.get_allowed_tokens(source))
            node = {"state": source, "is_final": bool(index.is_final_state(source)), "eos_allowed": eos in allowed,
                    "allowed_token_count": len(allowed), "non_eos_token_count": len([t for t in allowed if t != eos])}
            nodes[source] = node
            graph["states"].append(node)
            c["graph_states_expanded"] += 1
            for tid in allowed:
                if tid == eos:
                    continue
                raw = strings[tid].encode("utf-8")
                destination = index.get_next_state(source, tid)
                if destination is None:
                    raise RuntimeError("Allowed non-EOS token lacks a transition")
                graph["edges"].append({"source_state": source, "token_id": tid, "exact_token_bytes_hex": raw.hex(),
                                       "byte_length": len(raw), "vocabulary_string": strings[tid], "token_spelling": spellings[tid],
                                       "is_special_token": tid in special_ids, "classification": classify(raw, tid in special_ids),
                                       "destination_state": destination, "destination_final": bool(index.is_final_state(destination))})
                c["graph_edges_inspected"] += 1
                if destination not in scheduled:
                    scheduled.add(destination)
                    queue.append(destination)
            checkpoint()
        graph["analysis"] = analyze_graph(roots, nodes, graph["edges"])
        graph.update(status="EXHAUSTIVELY_RESOLVED", class_counts=dict(Counter(e["classification"] for e in graph["edges"])),
                     reachable_state_count=len(nodes), non_eos_transition_count=len(graph["edges"]),
                     operational_implication="MODEL_MAY_EMIT_TRAILING_WHITESPACE_UNTIL_STOP_LIMIT" if graph["analysis"]["cyclic_components"] else "NO_REACHABLE_CYCLE")
        proofs = {x["root_state"]: x for x in graph["analysis"]["root_proofs"]}
        for row in states["rows"]:
            if row["result"] == "AWAITING_CLOSURE":
                row["whitespace_closure_pass"] = proofs[row["final_state"]]["closure_pass"]
                row["result"] = "ACCEPT" if row["whitespace_closure_pass"] else "REJECT"
        states["status"] = "ADJUDICATED"
        q["positive_counts"] = {kind: sum(x["result"] == kind for x in states["rows"]) for kind in ["ACCEPT", "REJECT", "ERROR"]}
        q["historical_negative_carry_forward"] = [{"fixture_id": fid, "expected": "REJECT", "result": old_rows[fid]["result"],
                                                   "historical_content_traversal": old_rows[fid]["traversal"], "rerun": False} for fid in oracle["historical_negative_ids"]]
        q["carry_forward_basis"] = "The corrected oracle changes only already-accepting contract-valid object states with whitespace-only closure. Every carried negative was rejected during content traversal; no structurally invalid path is broadened."
        assert all(x["result"] == "REJECT" and x["historical_content_traversal"] == "REJECT" for x in q["historical_negative_carry_forward"])
        q["historical_textual"] = {"correct": 64, "total": 64, "rerun": False, "source_sha256": sha(OLD / "STRUCTURAL_RESULTS.json")}
        q["combined"] = {"total": 64, "correct": 30 + q["positive_counts"]["ACCEPT"], "false_accepts": 0,
                         "false_rejects": q["positive_counts"]["REJECT"], "errors": q["positive_counts"]["ERROR"]}
        by_id = {x["fixture_id"]: x for x in states["rows"]}
        q["rule_coverage"] = [{**x, "positive_result": by_id[x["positive"]]["result"], "negative_result": old_rows[x["violating"]]["result"],
                               "qualified": by_id[x["positive"]]["result"] == "ACCEPT" and old_rows[x["violating"]]["result"] == "REJECT"} for x in fixture_set["coverage"]]
        q["M1_and_U+0000"] = {fid: {"historical_textual": next(x for x in historical["textual"] if x["id"] == fid), "current": by_id[fid]} for fid in ["M1", "STRING_NUL"]}
        passed = (q["positive_counts"]["ACCEPT"] == 34 and graph["analysis"]["closure_pass"]
                  and len(q["rule_coverage"]) == 18 and all(x["qualified"] for x in q["rule_coverage"]))
        q["status"] = "DIRECT_REGEX_V0_1_DECODER_QUALIFIED" if passed else "DIRECT_REGEX_V0_1_WHITESPACE_CLOSURE_FAILED"
        if q["positive_counts"]["ERROR"]:
            q["status"] = "DIRECT_REGEX_V0_1_WHITESPACE_CLOSURE_INCONCLUSIVE"
        q["contract_alignment"] = "TRAILING_WHITESPACE_ONLY_CONTINUATION_IS_CONTRACT_COMPATIBLE" if passed else "NOT_ESTABLISHED"
        q["proof_scope"] = "Exhaustive non-EOS graph closure for all unique accepting states reached by the 34 frozen contract-valid fixtures. Not a claim about unvisited roots or exact-validator qualification."
    except Exception as exc:
        q.update(status="DIRECT_REGEX_V0_1_WHITESPACE_CLOSURE_INCONCLUSIVE", error=repr(exc), traceback=traceback.format_exc())
    finally:
        after = inventory()
        q["environment"]["post"] = {"packages": after, "pip_check": pip_check(),
                                      "additions": sorted(set(after) - set(before)), "removals": sorted(set(before) - set(after)),
                                      "drift": {k: {"before": v, "after": after.get(k)} for k, v in before.items() if after.get(k) != v}}
        q["environment"]["unchanged"] = before == after
        changes = [name for name, digest in oracle["immutable_inputs_sha256"].items() if sha(ROOT / name) != digest]
        q["frozen_identity_changes"] = changes
        if before != after or q["environment"]["post"]["pip_check"]["returncode"] != 0 or changes:
            q["status"] = "DIRECT_REGEX_V0_1_CLOSURE_QUALIFICATION_BLOCKED"
        q["finished_utc"] = now()
        checkpoint()
        print(q["status"], json.dumps(q.get("positive_counts")), "states", len(graph["states"]), "edges", len(graph["edges"]))
        if q.get("error"):
            print(q["error"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--prepare"]:
        prepare()
    elif sys.argv[1:] == ["--execute"]:
        execute()
    else:
        raise SystemExit("Use --prepare or --execute; no retries.")
