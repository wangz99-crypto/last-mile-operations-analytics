"""Synthetic, model-free tests for the BR initialization boundary."""
import ast
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gateway.domain.evaluation.answerability import semantic_transformers_runtime as runtime
from gateway.domain.evaluation.answerability.answerability_contracts import (
    ActiveBundle, ContractError, GateInput, RankedEvidence,
)


def gate_input():
    bundle = ActiveBundle("last-mile-exception-triage-demo", "1.0-demo",
                          "2026-01-01T00:00:00Z", None, "0" * 64, "1" * 64)
    evidence = tuple(RankedEvidence(rank, "SOP-01", "1.0-demo", section,
                                   "Synthetic workshop", "Latch instructions", "Close the latch.", score)
                     for rank, section, score in ((1, "latch-check", 0.8), (2, "label-check", 0.5)))
    return GateInput("Which latch needs checking?", evidence, bundle)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.snapshot = (Path(self.temp.name) / "models--Qwen--Qwen2.5-1.5B-Instruct"
                         / "snapshots" / runtime.MODEL_REVISION)
        self.snapshot.mkdir(parents=True)
        self.spec = runtime.RuntimeSpec(runtime.MODEL_REPOSITORY, runtime.MODEL_REVISION,
                                        str(self.snapshot), "cpu", "float32", None)

    def inventory(self, config=None):
        for name, data in {"config.json": json.dumps(config or {"model_type": "qwen2"}).encode(),
                           "tokenizer_config.json": b"{}", "tokenizer.json": b"{}",
                           "model.safetensors": b"synthetic fixture; not model weights"}.items():
            (self.snapshot / name).write_bytes(data)
        entries = [{"relative_path": p.name, "byte_size": p.stat().st_size,
                    "sha256": runtime.file_sha256(p)} for p in sorted(self.snapshot.iterdir())]
        raw = json.dumps({"repository": runtime.MODEL_REPOSITORY, "revision": runtime.MODEL_REVISION,
                          "snapshot_path": str(self.snapshot), "files": entries}).encode()
        path = Path(self.temp.name) / "inventory.json"
        path.write_bytes(raw)
        return path, hashlib.sha256(raw).hexdigest()

    def test_exact_identity_cpu_fp32(self):
        self.assertEqual(self.spec.device, "cpu")
        self.assertEqual(self.spec.weight_dtype, "float32")

    def test_reject_mutable_missing_and_wrong_revision(self):
        for value in ("main", "latest", "", None, "a" * 40):
            with self.subTest(value=value), self.assertRaises(runtime.RuntimeBoundaryError):
                replace(self.spec, revision=value)

    def test_reject_other_repository(self):
        with self.assertRaises(runtime.RuntimeBoundaryError):
            replace(self.spec, repository="another/repository")

    def test_reject_non_cpu(self):
        for value in ("cuda", "mps", "directml", "rocm"):
            with self.subTest(value=value), self.assertRaises(runtime.RuntimeBoundaryError):
                replace(self.spec, device=value)

    def test_reject_non_fp32(self):
        for value in ("float16", "bfloat16", "int8", "int4"):
            with self.subTest(value=value), self.assertRaises(runtime.RuntimeBoundaryError):
                replace(self.spec, weight_dtype=value)

    def test_reject_quantization(self):
        for value in (False, "NONE", "int8", {"load_in_4bit": True}):
            with self.subTest(value=value), self.assertRaises(runtime.RuntimeBoundaryError):
                replace(self.spec, quantization=value)

    def test_reject_snapshot_identity_mismatch(self):
        for value in ("relative/snapshot", str(self.snapshot.parent / ("b" * 40))):
            with self.subTest(value=value), self.assertRaises(runtime.RuntimeBoundaryError):
                replace(self.spec, snapshot_path=value)

    def test_verify_inventory(self):
        path, digest = self.inventory()
        self.assertEqual(len(runtime.verify_snapshot(self.spec, path, digest)["files"]), 4)

    def test_inventory_receipt_mismatch(self):
        path, _ = self.inventory()
        with self.assertRaises(runtime.RuntimeBoundaryError):
            runtime.verify_snapshot(self.spec, path, "0" * 64)

    def test_model_file_mutation(self):
        path, digest = self.inventory()
        (self.snapshot / "model.safetensors").write_bytes(b"changed")
        with self.assertRaises(runtime.RuntimeBoundaryError):
            runtime.verify_snapshot(self.spec, path, digest)

    def test_reject_incomplete_inventory(self):
        path, digest = self.inventory()
        (self.snapshot / "extra.bin").write_bytes(b"extra")
        with self.assertRaises(runtime.RuntimeBoundaryError):
            runtime.verify_snapshot(self.spec, path, digest)

    def test_reject_traversal(self):
        path, _ = self.inventory()
        value = json.loads(path.read_bytes())
        value["files"][0]["relative_path"] = "../escape"
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        with self.assertRaises(runtime.RuntimeBoundaryError):
            runtime.verify_snapshot(self.spec, path, hashlib.sha256(raw).hexdigest())

    def test_reject_quantized_snapshot(self):
        path, digest = self.inventory({"model_type": "qwen2", "quantization_config": {}})
        with self.assertRaises(runtime.RuntimeBoundaryError):
            runtime.verify_snapshot(self.spec, path, digest)

    def test_explicit_offline_required(self):
        path, digest = self.inventory()
        with patch.dict(os.environ, {"HF_HUB_OFFLINE": "0", "TRANSFORMERS_OFFLINE": "0"}), \
                self.assertRaises(runtime.RuntimeBoundaryError):
            runtime.load_cpu_fp32(self.spec, path, digest)

    def test_message_content_and_rank_order_preserved(self):
        tokenizer = SimpleNamespace(apply_chat_template=Mock(return_value=[10, 20]))
        value = gate_input()
        self.assertEqual(runtime.render_gate_input(tokenizer, value), [10, 20])
        args, kwargs = tokenizer.apply_chat_template.call_args
        self.assertEqual(args[0], list(runtime.build_messages(value)))
        self.assertEqual(kwargs, {"tokenize": True, "add_generation_prompt": True})
        payload = json.loads(args[0][1]["content"])
        self.assertEqual([e["rank"] for e in payload["evidence"]], [1, 2])

    def test_benchmark_objects_rejected(self):
        tokenizer = SimpleNamespace(apply_chat_template=Mock())
        for field in ("question_id", "expected_gate", "gold_support_sections", "required_support_sections",
                      "difficulty", "hard_negative", "review_status", "round1_result"):
            with self.subTest(field=field), self.assertRaises(ContractError):
                runtime.render_gate_input(tokenizer, {"question": "Synthetic workshop?", field: "forbidden"})
        tokenizer.apply_chat_template.assert_not_called()

    def test_richer_gate_input_subclass_rejected(self):
        class RichInput(GateInput):
            pass
        value = gate_input()
        tokenizer = SimpleNamespace(apply_chat_template=Mock())
        with self.assertRaises(ContractError):
            runtime.render_gate_input(tokenizer, RichInput(value.question, value.evidence, value.active_bundle))
        tokenizer.apply_chat_template.assert_not_called()

    def test_generation_and_forward_guard(self):
        class Module:
            def _call_impl(self):
                self.fail_if_called = True
        class Mixin:
            def generate(self):
                self.fail_if_called = True
        fake_torch = SimpleNamespace(nn=SimpleNamespace(Module=Module))
        with runtime.initialization_only(fake_torch, Mixin):
            with self.assertRaises(runtime.RuntimeBoundaryError):
                Module()._call_impl()
            with self.assertRaises(runtime.RuntimeBoundaryError):
                Mixin().generate()

    def test_failure_has_no_fallback_or_retry(self):
        path, digest = self.inventory()
        with patch.object(runtime, "verify_snapshot", side_effect=OSError("synthetic failure")) as verify:
            with self.assertRaisesRegex(OSError, "synthetic failure"):
                runtime.load_cpu_fp32(self.spec, path, digest)
        verify.assert_called_once()

    def test_parameter_device_and_dtype_validation(self):
        parameter = SimpleNamespace(device="cpu", dtype="torch.float32", numel=lambda: 7)
        model = SimpleNamespace(named_parameters=lambda: [("test", parameter)], named_buffers=lambda: [],
                                is_quantized=False)
        self.assertEqual(runtime.inspect_parameters(model)["unique_parameter_elements"], 7)
        for device, dtype in (("cuda:0", "torch.float32"), ("cpu", "torch.float16")):
            parameter.device, parameter.dtype = device, dtype
            with self.subTest(device=device, dtype=dtype), self.assertRaises(runtime.RuntimeBoundaryError):
                runtime.inspect_parameters(model)

    def test_context_margin_and_no_truncation(self):
        self.assertEqual(runtime.require_context_capacity(12000, 4096, 32768), 16672)
        for args in ((32768, 1, 32768), (0, 1, 100), (True, 1, 100), (99, 1, 100)):
            with self.subTest(args=args), self.assertRaises(runtime.RuntimeBoundaryError):
                runtime.require_context_capacity(*args)

    def test_no_generation_or_retrieval_path(self):
        tree = ast.parse(Path(runtime.__file__).read_text(encoding="utf-8"))
        calls = [node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        self.assertFalse(set(calls) & {"generate", "forward", "retrieve", "search", "decide"})
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any(any(word in name for word in ("retrieval", "benchmark", "evaluation_loader"))
                             for name in imports))

    def test_frozen_semantic_hashes(self):
        runtime.verify_preregistration(Path(__file__).resolve().parents[3])


if __name__ == "__main__":
    unittest.main()
