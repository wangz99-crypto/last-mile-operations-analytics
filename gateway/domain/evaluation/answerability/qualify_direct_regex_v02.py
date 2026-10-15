"""One-shot, preregistered V0.1 terminality diagnosis; conditional V0.2 only."""
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from datetime import datetime, timezone

from recover_direct_regex_acceptance import inventory, pip_check, accept_content

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_v02"
OLD = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_decoder"
REC = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_recovery"
BASE = "80ab1c2acf5d6dad4cc4cb5c903f23bc6f86b725"
TAG = "answerability-semantic-v2_1-direct-regex-v0.2-recovery-failed"
SUFFIXES = [
    {"id": "PROSE", "class": "alphabetic prose", "suffix": "hello"},
    {"id": "SECOND_OBJECT", "class": "second JSON object", "suffix": "{}"},
    {"id": "PUNCTUATION", "class": "punctuation", "suffix": "!"},
]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(name, value, exclusive=False):
    with (ART / name).open("xb" if exclusive else "wb") as stream:
        stream.write((json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode())


def anchors(regex):
    """Record unescaped end assertions outside character classes; no regex execution."""
    found, i, in_class = [], 0, False
    while i < len(regex):
        c = regex[i]
        if c == "\\":
            if not in_class and i + 1 < len(regex) and regex[i + 1] in "zZ":
                found.append({"offset": i, "assertion": regex[i:i + 2]})
            i += 2
            continue
        if c == "[" and not in_class:
            in_class = True
        elif c == "]" and in_class:
            in_class = False
        elif c == "$" and not in_class:
            found.append({"offset": i, "assertion": "$"})
        i += 1
    return {"classification": "END_ANCHOR_ABSENT" if not found else "UNRESOLVED",
            "end_assertions": found, "byte_count": len(regex.encode()),
            "exact_suffix_repr": repr(regex[-32:]),
            "method": "Inspected exact UTF-8 regex; scanned escaping/character classes for $, \\z, \\Z. No assertion found means no global end assertion. No inference from token count."}


def prepare():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASE
    assert subprocess.check_output(["git", "rev-list", "-n", "1", TAG], cwd=ROOT, text=True).strip() == BASE
    if ART.exists():
        raise RuntimeError("Refuse existing phase directory")
    old_oracle = read(REC / "CORRECTED_ACCEPTANCE_ORACLE.json")
    identities = dict(old_oracle["historical_inputs_sha256"])
    for name, expected in identities.items():
        assert sha(ROOT / name) == expected, name
    for path in list(REC.iterdir()) + [Path(__file__), Path(__file__).with_name("recover_direct_regex_acceptance.py")]:
        if path.is_file():
            identities[path.relative_to(ROOT).as_posix()] = sha(path)
    assert "OWNER_REVIEWED / DIRECT_REGEX_CANDIDATE_FAILED" in (OLD / "FREEZE_RECORD.md").read_text(encoding="utf-8")
    assert "OWNER_REVIEWED / DIRECT_REGEX_RECOVERY_FAILED" in (REC / "FREEZE_RECORD.md").read_text(encoding="utf-8")
    raw = (OLD / "DECODER_ENFORCEMENT_REGEX.txt").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "3ec42de4a205e599789575954494ad2004beedcc49e2ed550ef865b591dc1482"
    fixture_set = read(OLD / "STRUCTURAL_FIXTURES.json")
    ART.mkdir()
    save("TERMINALITY_DIAGNOSTIC.json", {
        "status": "PREREGISTERED_NOT_EXECUTED", "preregistered_utc": now(),
        "base_commit": BASE, "base_tag": TAG, "entry_git_status": "clean before new helper creation",
        "helper_sha256": sha(__file__), "immutable_inputs_sha256": identities,
        "static_inspection": anchors(raw.decode("utf-8")),
        "diagnostic_fixture_ids": ["M1", "STRING_NUL"],
        "plan": {"root_cause_gate": "A: END_ANCHOR_ABSENT (or independently established ineffective global anchor) AND B: at least one non-empty non-JSON-whitespace allowed token with an actual next state, in each of the two diagnostic fixtures. Otherwise INCONCLUSIVE; no V0.2.",
                 "token_classification": "Classify every non-EOS allowed token by the exact string conversion used to build Vocabulary. JSON whitespace is only space/TAB/CR/LF. Record all IDs and all classified representations. Query Index.get_next_state without advancing the diagnostic Guide.",
                 "representative_sample": "Lowest eight token IDs, plus lowest ID in each present empty/JSON-whitespace/non-whitespace class; selection sorted, deduplicated. Exhaustive classification establishes absence as well as presence.",
                 "transformation": "V0.2 bytes = b'(?:' + exact V0.1 bytes + b')\\z'; no other change.",
                 "monotonicity": "Adding a globally scoped end-of-haystack assertion can only remove matches: L(V0.2) subseteq L(V0.1). Historical negative carry-forward is conditional on byte-exact transformation.",
                 "positive_fixture_ids": [x["id"] for x in fixture_set["fixtures"] if x["expected"] == "ACCEPT"],
                 "suffix_probe_base": "M1", "suffix_probes": SUFFIXES,
                 "suffix_method": "Use the saved V0.2 M1 accepting state; independently tokenize each suffix and query transitions from that state. No EOS advance; no repetition of the base fixture.",
                 "freeze": "Save derivation/regex/helper/fixture hashes before V0.2 Index construction or execution.",
                 "no_retry": True, "no_post_execution_helper_edits": True},
        "release_facts": {"version": "outlines_core==0.2.14", "source": "https://raw.githubusercontent.com/dottxt-ai/outlines-core/0.2.14/src/index.rs",
                          "facts": ["Index::new uses DFA::new and universal_start_state(Anchored::Yes) (lines 104-105).", "Final-state detection and ordinary token transitions coexist (lines 117-143).", "EOS is inserted into final-state allowed transitions (lines 170-175), but next_state on EOS returns None (lines 216-219).", "Start anchoring is not end-of-input anchoring; a final state need not expose only EOS."],
                          "api_inspection": "Read installed Index/Guide method documentation without constructing any Index, Guide, tokenizer or model."},
        "rows": [], "counters": {"tokenizer_loads": 0, "v01_Index_constructions": 0, "v02_Index_constructions": 0,
                                   "v01_diagnostic_fixture_executions": 0, "v02_positive_fixture_executions": 0,
                                   "suffix_probes": 0, "negative_fixture_reruns": 0, "textual_64_reruns": 0,
                                   "retries": 0, "package_mutations": 0, "model_initialization": 0,
                                   "generate": 0, "forward": 0, "DEVELOPMENT": 0, "retrieval": 0,
                                   "eos_advance_calls": 0},
        "phase_2h_held_out_access": False, "phase_2g_private_heldout_access": False,
        "fresh_v2_1_semantic_suite": "NOT YET AUTHORED", "socket_events": []}, exclusive=True)
    print("Preregistered", sha(ART / "TERMINALITY_DIAGNOSTIC.json"), "helper", sha(__file__))


def execute():
    d = read(ART / "TERMINALITY_DIAGNOSTIC.json")
    assert d["status"] == "PREREGISTERED_NOT_EXECUTED", "No retry"
    assert sha(__file__) == d["helper_sha256"]
    for name, digest in d["immutable_inputs_sha256"].items():
        assert sha(ROOT / name) == digest, name
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASE
    prereg_sha = sha(ART / "TERMINALITY_DIAGNOSTIC.json")
    d.update(status="STARTED", started_utc=now(), preregistration_sha256=prereg_sha)
    c = d["counters"]
    def checkpoint():
        save("TERMINALITY_DIAGNOSTIC.json", d)
    checkpoint()
    before = inventory()
    d["environment"] = {"pre": {"packages": before, "pip_check": pip_check()}}
    checkpoint()
    assert before == read(REC / "ENVIRONMENT_RECEIPT.json")["post"]["packages"]
    assert d["environment"]["pre"]["pip_check"]["returncode"] == 0
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      PYTHONDONTWRITEBYTECODE="1", OUTLINES_CACHE_DIR=str(ROOT / ".cache/phase2h-direct-regex-runtime"))
    def guard(event, args):
        if event.startswith("socket."):
            d["socket_events"].append({"event": event, "args": str(args)})
            if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "socket.sendto"}:
                raise RuntimeError("Offline runtime: outbound socket operations forbidden")
            if event == "socket.bind" and str(args[1][0]) not in {"::1", "127.0.0.1"}:
                raise RuntimeError("Non-loopback bind forbidden")
        if event == "open" and isinstance(args[0], str) and args[0].lower().endswith((".safetensors", "pytorch_model.bin")):
            raise RuntimeError("Model weights forbidden")
    sys.addaudithook(guard)
    q = None
    try:
        from outlines_core import Guide
        from outlines.backends.outlines_core import OutlinesCoreBackend
        from outlines.models.transformers import TransformerTokenizer
        from transformers import AutoTokenizer
        assert metadata.version("outlines_core") == "0.2.14" and metadata.version("outlines") == "1.3.3"
        historical = read(OLD / "STRUCTURAL_RESULTS.json")
        previous = {x["id"]: x for x in historical["FSM"]["rows"]}
        fs = read(OLD / "STRUCTURAL_FIXTURES.json")
        fixtures = {x["id"]: x for x in fs["fixtures"]}
        identity = historical["FSM"]["tokenizer_identity"]
        snapshot = Path(identity["snapshot_path"])
        for name, digest in identity["files_sha256"].items():
            assert sha(snapshot / name) == digest
        d["tokenizer_identity"] = identity
        c["tokenizer_loads"] += 1
        checkpoint()
        tok = AutoTokenizer.from_pretrained(str(snapshot), revision=identity["revision"], local_files_only=True, trust_remote_code=False, use_fast=True)
        wrapped = TransformerTokenizer(tok)
        eos = wrapped.eos_token_id
        assert eos == historical["FSM"]["eos_token_id"]
        vocab = wrapped.get_vocab()
        # Identical string conversion to the official frozen backend vocabulary.
        strings = {token_id: wrapped.convert_token_to_string(token) for token, token_id in vocab.items()}
        vocabulary = OutlinesCoreBackend.create_outlines_core_vocabulary(vocab, eos, wrapped.eos_token, wrapped.convert_token_to_string)
        backend = object.__new__(OutlinesCoreBackend)
        backend.vocabulary, backend.eos_token_id, backend.tensor_library_name = vocabulary, eos, "torch"
        raw = (OLD / "DECODER_ENFORCEMENT_REGEX.txt").read_bytes()
        c["v01_Index_constructions"] += 1
        checkpoint()
        index = backend.get_regex_logits_processor(raw.decode("utf-8")).index
        for fid in d["diagnostic_fixture_ids"]:
            f = fixtures[fid]
            ids = tok.encode(f["text"], add_special_tokens=False)
            assert ids == previous[fid]["tokenization"]["token_ids"]
            assert hashlib.sha256(f["text"].encode()).hexdigest() == f["input_sha256"]
            row = {"fixture_id": fid, "fixture_sha256": f["input_sha256"], "token_count": len(ids), "token_ids": ids, "status": "STARTED"}
            d["rows"].append(row)
            c["v01_diagnostic_fixture_executions"] += 1
            checkpoint()
            guide = Guide(index)
            row.update(accept_content(guide, ids, eos))
            assert row["all_content_token_advances_successful"] and row["is_finished"]
            state = guide.get_state()
            row["accepting_state"] = state
            non_eos = sorted(x for x in guide.get_tokens() if x != eos)
            row["non_eos_allowed_token_ids"] = non_eos
            classified = []
            for token_id in non_eos:
                value = strings[token_id]
                empty = not value
                whitespace = bool(value) and all(ch in " \t\r\n" for ch in value)
                next_state = index.get_next_state(state, token_id)
                classified.append({"token_id": token_id, "string": value, "string_repr": repr(value),
                                   "utf8_hex": value.encode("utf-8").hex(), "empty": empty,
                                   "json_whitespace_only": whitespace, "unicode_whitespace_only": value.isspace(),
                                   "non_empty_non_whitespace": bool(value) and not whitespace,
                                   "next_state": next_state, "next_state_available": next_state is not None})
            row["all_non_eos_token_classification"] = classified
            sample = set(non_eos[:8])
            for key in ["empty", "json_whitespace_only", "non_empty_non_whitespace"]:
                matching = [x["token_id"] for x in classified if x[key]]
                if matching:
                    sample.add(min(matching))
            row["representative_sample"] = [x for x in classified if x["token_id"] in sample]
            row["meaningful_non_eos_continuations"] = sum(x["non_empty_non_whitespace"] and x["next_state_available"] for x in classified)
            row["class_counts"] = {key: sum(x[key] for x in classified) for key in ["empty", "json_whitespace_only", "non_empty_non_whitespace", "next_state_available"]}
            row["status"] = "DIAGNOSED"
            checkpoint()
        gate_a = d["static_inspection"]["classification"] == "END_ANCHOR_ABSENT"
        gate_b = all(x["meaningful_non_eos_continuations"] > 0 for x in d["rows"])
        d["root_cause_gate"] = {"A": gate_a, "B": gate_b, "passed": gate_a and gate_b}
        d["status"] = "V0_1_END_OF_INPUT_ENFORCEMENT_MISSING" if gate_a and gate_b else "DIRECT_REGEX_TERMINALITY_DIAGNOSTIC_INCONCLUSIVE"
        checkpoint()
        if not (gate_a and gate_b):
            d["final_outcome"] = "DIRECT_REGEX_TERMINALITY_DIAGNOSTIC_INCONCLUSIVE"
            d["v02_authorized"] = False
            return
        d["v02_authorized"] = True
        # Sole permitted transformation, with byte-exact inner expression.
        new_raw = b"(?:" + raw + b")\\z"
        with (ART / "V0_2_REGEX.txt").open("xb") as stream:
            stream.write(new_raw)
        derivation = {"identity": "DECODER_ENFORCEMENT_REGEX_V2_1_V0_2", "frozen_utc": now(),
                      "root_cause": d["status"], "diagnostic_sha256": sha(ART / "TERMINALITY_DIAGNOSTIC.json"),
                      "v01_regex_sha256": hashlib.sha256(raw).hexdigest(), "v02_regex_sha256": sha(ART / "V0_2_REGEX.txt"),
                      "transformation": "b'(?:' + exact V0.1 bytes + b')\\z'", "no_other_changes": True,
                      "helper_sha256": sha(__file__), "fixtures_sha256": sha(OLD / "STRUCTURAL_FIXTURES.json"),
                      "positive_fixture_ids": d["plan"]["positive_fixture_ids"], "suffix_probes": SUFFIXES,
                      "monotonicity": {"established": True, "claim": "L(V0.2) subseteq L(V0.1)", "proof": d["plan"]["monotonicity"]}}
        assert new_raw[3:-3] == raw
        save("V0_2_DERIVATION_RECORD.json", derivation, exclusive=True)
        q = {"status": "STARTED", "started_utc": now(), "derivation_sha256": sha(ART / "V0_2_DERIVATION_RECORD.json"), "rows": [], "suffix_probes": []}
        save("V0_2_QUALIFICATION_RESULTS.json", q, exclusive=True)
        c["v02_Index_constructions"] += 1
        checkpoint()
        index2 = backend.get_regex_logits_processor(new_raw.decode("utf-8")).index
        final_states = {}
        for fid in derivation["positive_fixture_ids"]:
            c["v02_positive_fixture_executions"] += 1
            row = {"fixture_id": fid, "expected": "ACCEPT", "result": "STARTED"}
            q["rows"].append(row)
            save("V0_2_QUALIFICATION_RESULTS.json", q)
            checkpoint()
            try:
                ids = tok.encode(fixtures[fid]["text"], add_special_tokens=False)
                assert ids == previous[fid]["tokenization"]["token_ids"]
                g = Guide(index2)
                row.update(token_ids=ids, token_count=len(ids), **accept_content(g, ids, eos))
                final_states[fid] = g.get_state()
            except Exception as exc:
                row.update(result="ERROR", error=repr(exc), traceback=traceback.format_exc())
            save("V0_2_QUALIFICATION_RESULTS.json", q)
        for probe in SUFFIXES:
            c["suffix_probes"] += 1
            probe_row = dict(probe, expected="REJECT", result="STARTED")
            q["suffix_probes"].append(probe_row)
            save("V0_2_QUALIFICATION_RESULTS.json", q)
            try:
                state = final_states["M1"]
                ids = tok.encode(probe["suffix"], add_special_tokens=False)
                assert ids and eos not in ids
                trace = []
                for token_id in ids:
                    next_state = index2.get_next_state(state, token_id)
                    trace.append({"state": state, "token_id": token_id, "next_state": next_state})
                    if next_state is None:
                        break
                    state = next_state
                probe_row.update(token_ids=ids, trace=trace, result="REJECT" if next_state is None else "PERMITTED")
            except Exception as exc:
                probe_row.update(result="ERROR", error=repr(exc))
            save("V0_2_QUALIFICATION_RESULTS.json", q)
        q["positive_counts"] = {k: sum(x["result"] == k for x in q["rows"]) for k in ["ACCEPT", "REJECT", "ERROR"]}
        q["historical_negative_carry_forward"] = {"count": 30, "rerun": False, "basis": "Language narrowing proof; historical negative results byte-identical."}
        q["coverage"] = [{**x, "qualified": next(r for r in q["rows"] if r["fixture_id"] == x["positive"])["result"] == "ACCEPT" and previous[x["violating"]]["result"] == "REJECT"} for x in fs["coverage"]]
        q["U+0000"] = {"historical_json_contract_textual": next(x for x in historical["textual"] if x["id"] == "STRING_NUL"), "v02_fsm": next(x for x in q["rows"] if x["fixture_id"] == "STRING_NUL"), "v02_textual_serialization": "Accepted by Index regex traversal if content traversed and final state reached; no separate regex-engine test."}
        positive_ok = q["positive_counts"]["ACCEPT"] == 34
        suffix_ok = all(x["result"] == "REJECT" for x in q["suffix_probes"])
        q["status"] = "DIRECT_REGEX_V0_2_DECODER_QUALIFIED" if positive_ok and suffix_ok else "DIRECT_REGEX_V0_2_QUALIFICATION_FAILED"
        if any(x["result"] == "PERMITTED" for x in q["suffix_probes"]):
            q["status"] = "DIRECT_REGEX_V0_2_TERMINALITY_FAILED"
        q["finished_utc"] = now()
        d["final_outcome"] = q["status"]
        save("V0_2_QUALIFICATION_RESULTS.json", q)
    except Exception as exc:
        d.update(error=repr(exc), traceback=traceback.format_exc(), final_outcome="DIRECT_REGEX_V0_2_QUALIFICATION_FAILED" if (ART / "V0_2_REGEX.txt").exists() else "DIRECT_REGEX_TERMINALITY_DIAGNOSTIC_INCONCLUSIVE")
    finally:
        after = inventory()
        d["environment"]["post"] = {"packages": after, "pip_check": pip_check(),
                                      "additions": sorted(set(after) - set(before)), "removals": sorted(set(before) - set(after)),
                                      "drift": {k: {"before": v, "after": after.get(k)} for k, v in before.items() if after.get(k) != v}}
        d["environment"]["unchanged"] = before == after
        d["finished_utc"] = now()
        if before != after or d["environment"]["post"]["pip_check"]["returncode"] != 0:
            d["environment_integrity_failure"] = True
        for name, digest in d["immutable_inputs_sha256"].items():
            assert sha(ROOT / name) == digest, name
        checkpoint()
        print(d.get("final_outcome"), json.dumps(c))
        if d.get("error"):
            print(d["error"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--prepare"]:
        prepare()
    elif sys.argv[1:] == ["--execute"]:
        execute()
    else:
        raise SystemExit("Specify --prepare or --execute; execution cannot be repeated.")
