"""One-shot recovery of final-state/EOS observation; never advance EOS."""
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import traceback

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_recovery"
HISTORY = ROOT / "artifacts/answerability_semantic_v2_1_direct_regex_decoder"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(name, value):
    (ART / name).write_bytes((json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode())


def inventory():
    result = {}
    for dist in metadata.distributions():
        name = dist.metadata["Name"].lower().replace("_", "-").replace(".", "-")
        result[name] = {"name": dist.metadata["Name"], "version": dist.version,
                        "metadata_sha256": sha(dist._path / "METADATA"),
                        "record_sha256": sha(dist._path / "RECORD") if (dist._path / "RECORD").exists() else None}
    return result


def pip_check():
    result = subprocess.run([sys.executable, "-B", "-m", "pip", "check", "--disable-pip-version-check"],
                            capture_output=True, text=True,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PIP_NO_INDEX="1"))
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def accept_content(guide, token_ids, eos_token_id):
    """Observe terminal acceptance, without attempting a transition on EOS."""
    advanced = 0
    for position, token_id in enumerate(token_ids):
        if token_id == eos_token_id:
            raise ValueError("Unexpected EOS inside a frozen content-token sequence")
        if token_id not in guide.get_tokens():
            return {"result": "REJECT", "all_content_token_advances_successful": False,
                    "content_advances": advanced, "rejected_position": position,
                    "rejected_token_id": token_id, "is_finished": guide.is_finished(),
                    "allowed_tokens_at_final_state": None, "eos_token_id": eos_token_id,
                    "eos_advance_calls": 0}
        guide.advance(token_id=token_id, return_tokens=False)
        advanced += 1
    finished = bool(guide.is_finished())
    allowed = list(guide.get_tokens())
    return {"result": "ACCEPT" if finished and allowed == [eos_token_id] else "REJECT",
            "all_content_token_advances_successful": True, "content_advances": advanced,
            "is_finished": finished, "allowed_tokens_at_final_state": allowed,
            "eos_token_id": eos_token_id, "eos_advance_calls": 0}


def main():
    if (ART / "RECOVERY_RESULTS.json").exists():
        raise RuntimeError("Refuse overwrite or recovery retry")
    oracle = read(ART / "CORRECTED_ACCEPTANCE_ORACLE.json")
    assert sha(Path(__file__)) == oracle["helper_sha256"], "Helper freeze mismatch"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == oracle["base_commit"]
    for name, expected in oracle["historical_inputs_sha256"].items():
        assert sha(ROOT / name) == expected, name
    fixtures = read(HISTORY / "STRUCTURAL_FIXTURES.json")
    historical = read(HISTORY / "STRUCTURAL_RESULTS.json")
    positives = [f for f in fixtures["fixtures"] if f["expected"] == "ACCEPT"]
    negatives = [f for f in fixtures["fixtures"] if f["expected"] == "REJECT"]
    assert [f["id"] for f in positives] == oracle["positive_fixture_ids"]
    assert [f["id"] for f in negatives] == oracle["carried_reject_fixture_ids"]
    assert len(positives) == 34 and len(negatives) == 30
    assert "STRING_NUL" in oracle["positive_fixture_ids"] and "M1" in oracle["positive_fixture_ids"]
    previous = {r["id"]: r for r in historical["FSM"]["rows"]}
    assert all(previous[f["id"]]["result"] == "REJECT" for f in negatives)
    assert historical["textual_matches"] == 64 and historical["textual_errors"] == 0
    before = inventory()
    historical_environment = read(HISTORY / "ENVIRONMENT_RECEIPT.json")["post_install"]["packages"]
    pre_check = pip_check()
    environment = {"pre": {"utc": datetime.now(timezone.utc).isoformat(), "packages": before,
                            "matches_historical_environment": before == historical_environment,
                            "pip_check": pre_check}, "post": None}
    save("ENVIRONMENT_RECEIPT.json", environment)
    result = {"status": "STARTED", "started_utc": datetime.now(timezone.utc).isoformat(),
              "helper_sha256": oracle["helper_sha256"], "oracle_sha256": sha(ART / "CORRECTED_ACCEPTANCE_ORACLE.json"),
              "rows": [], "counters": {"recovery_FSM_fixture_executions": 0, "retries": 0,
              "historical_reject_fixtures_rerun": 0, "textual_regex_reruns": 0, "regex_derivations": 0,
              "tokenizer_loads": 0, "Index_reconstructions": 0, "eos_advance_calls": 0,
              "package_mutations": 0, "model_initialization": 0, "generate": 0, "forward": 0,
              "DEVELOPMENT": 0, "retrieval": 0}, "socket_events": [],
              "phase_2h_held_out_access": False, "phase_2g_private_heldout_access": False,
              "fresh_v2_1_semantic_suite": "NOT YET AUTHORED"}
    def checkpoint():
        save("RECOVERY_RESULTS.json", result)
    checkpoint()
    if before != historical_environment or pre_check["returncode"] != 0:
        result.update(status="DIRECT_REGEX_RECOVERY_BLOCKED", reason="Frozen package provenance or pip check failed")
        checkpoint()
        return
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                      PYTHONDONTWRITEBYTECODE="1", OUTLINES_CACHE_DIR=str(ROOT / ".cache/phase2h-direct-regex-runtime"))
    def guard(event, args):
        if event.startswith("socket."):
            result["socket_events"].append({"event": event, "args": str(args)})
            if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "socket.sendto"}:
                raise RuntimeError("Offline recovery forbids external network operations: " + event)
            if event == "socket.bind" and str(args[1][0]) not in {"::1", "127.0.0.1"}:
                raise RuntimeError("Non-loopback bind forbidden")
        if event == "open" and isinstance(args[0], str) and args[0].lower().endswith((".safetensors", "pytorch_model.bin")):
            raise RuntimeError("Model-weight access forbidden")
    sys.addaudithook(guard)
    try:
        from outlines_core import Guide
        from outlines.backends.outlines_core import OutlinesCoreBackend
        from outlines.models.transformers import TransformerTokenizer
        import outlines.backends.outlines_core as backend_module
        def forbidden_schema(*args, **kwargs):
            raise RuntimeError("JSON Schema compiler path forbidden")
        backend_module.build_regex_from_schema = forbidden_schema
        from transformers import AutoTokenizer
        assert metadata.version("outlines") == "1.3.3" and metadata.version("outlines_core") == "0.2.14"
        token_identity = historical["FSM"]["tokenizer_identity"]
        snapshot = Path(token_identity["snapshot_path"])
        assert token_identity["revision"] == "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
        for name, expected in token_identity["files_sha256"].items():
            assert sha(snapshot / name) == expected, name
        result["tokenizer_identity"] = token_identity
        result["counters"]["tokenizer_loads"] += 1
        checkpoint()
        tok = AutoTokenizer.from_pretrained(str(snapshot), revision=token_identity["revision"],
                                           local_files_only=True, trust_remote_code=False, use_fast=True)
        wrapped = TransformerTokenizer(tok)
        assert wrapped.eos_token_id == historical["FSM"]["eos_token_id"]
        vocabulary = OutlinesCoreBackend.create_outlines_core_vocabulary(
            wrapped.get_vocab(), wrapped.eos_token_id, wrapped.eos_token, wrapped.convert_token_to_string)
        backend = object.__new__(OutlinesCoreBackend)
        backend.vocabulary = vocabulary
        backend.eos_token_id = wrapped.eos_token_id
        backend.tensor_library_name = "torch"
        result["counters"]["Index_reconstructions"] += 1
        checkpoint()
        processor = backend.get_regex_logits_processor((HISTORY / "DECODER_ENFORCEMENT_REGEX.txt").read_text())
        index = processor.index
        for fixture in positives:
            row = {"fixture_id": fixture["id"], "fixture_sha256": fixture["input_sha256"],
                   "expected": "ACCEPT", "result": "STARTED", "eos_token_id": wrapped.eos_token_id}
            result["rows"].append(row)
            result["counters"]["recovery_FSM_fixture_executions"] += 1
            checkpoint()
            try:
                assert hashlib.sha256(fixture["text"].encode()).hexdigest() == fixture["input_sha256"]
                ids = tok.encode(fixture["text"], add_special_tokens=False)
                row.update(token_count=len(ids), token_ids=ids,
                           historical_tokenization_identical=ids == previous[fixture["id"]]["tokenization"]["token_ids"])
                assert row["historical_tokenization_identical"], "Tokenization changed"
                assert tok.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) == fixture["text"]
                row.update(accept_content(Guide(index), ids, wrapped.eos_token_id))
            except Exception as exc:
                row.update(result="ERROR", error=type(exc).__name__ + ": " + str(exc), traceback=traceback.format_exc())
            checkpoint()
        result["positive_pass_count"] = sum(r["result"] == "ACCEPT" for r in result["rows"])
        result["positive_reject_count"] = sum(r["result"] == "REJECT" for r in result["rows"])
        result["positive_error_count"] = sum(r["result"] == "ERROR" for r in result["rows"])
        result["status"] = "RECOVERY_POSITIVES_PASS" if result["positive_pass_count"] == 34 else "DIRECT_REGEX_RECOVERY_FAILED"
    except Exception as exc:
        result.update(status="DIRECT_REGEX_RECOVERY_FAILED", error=type(exc).__name__ + ": " + str(exc), traceback=traceback.format_exc())
    finally:
        after = inventory()
        post_check = pip_check()
        environment["post"] = {"utc": datetime.now(timezone.utc).isoformat(), "packages": after,
                               "pip_check": post_check, "additions": sorted(set(after)-set(before)),
                               "removals": sorted(set(before)-set(after)),
                               "drift": {n: {"before": v, "after": after.get(n)} for n, v in before.items() if after.get(n) != v}}
        environment["unchanged"] = before == after
        save("ENVIRONMENT_RECEIPT.json", environment)
        if before != after or post_check["returncode"] != 0:
            result["status"] = "DIRECT_REGEX_RECOVERY_FAILED"
            result["environment_integrity_failure"] = True
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        checkpoint()
    print(result["status"], "executions", result["counters"]["recovery_FSM_fixture_executions"],
          "pass", result.get("positive_pass_count"), "errors", result.get("positive_error_count"))
    if result.get("error"):
        print(result["error"])


if __name__ == "__main__":
    main()
