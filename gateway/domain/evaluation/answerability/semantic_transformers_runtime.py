"""Pinned offline CPU/FP32 initialization and tokenization; no inference transport."""
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from .gates.semantic_gate import build_messages

MODEL_REPOSITORY = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
PREREGISTRATION_HASHES = {
    "artifacts/answerability_semantic_gate_v1_prereg/SEMANTIC_PROMPT.txt":
        "09126ca1ca4cff86f634b6297f64c436863acac7a73a588de1bd249dca3b62cc",
    "artifacts/answerability_semantic_gate_v1_prereg/SEMANTIC_GATE_REGISTRY.json":
        "974a01464f40dd58f9a8ddf1c2d2bc550a9a106443d6a761a9713175a1133827",
    "gateway/domain/evaluation/answerability/gates/semantic_gate.py":
        "c70218e37b4304b6424e830b7f8698f11c4385ebd214c4d2fce5f8f805055d71",
}


class RuntimeBoundaryError(ValueError):
    """Invalid runtime provenance or an operation not authorized during BR."""


def require(condition, message):
    if not condition:
        raise RuntimeBoundaryError(message)


def file_sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def verify_preregistration(root):
    for name, expected in PREREGISTRATION_HASHES.items():
        require(file_sha256(Path(root) / name) == expected, "Frozen semantic file mismatch: " + name)


@dataclass(frozen=True, slots=True)
class RuntimeSpec:
    repository: str
    revision: str
    snapshot_path: str
    device: str
    weight_dtype: str
    quantization: None

    def __post_init__(self):
        require(self.repository == MODEL_REPOSITORY, "Sole model repository mismatch")
        require(self.revision == MODEL_REVISION, "Exact immutable model revision required")
        require(self.device == "cpu", "Only CPU is authorized")
        require(self.weight_dtype == "float32", "Only FP32 is authorized")
        require(self.quantization is None, "Quantization is forbidden")
        require(type(self.snapshot_path) is str, "Explicit snapshot path required")
        path = Path(self.snapshot_path)
        require(path.is_absolute() and path.name == MODEL_REVISION
                and path.parent.name == "snapshots"
                and path.parent.parent.name == "models--Qwen--Qwen2.5-1.5B-Instruct",
                "Snapshot identity/path mismatch")


def verify_snapshot(spec, inventory, expected_inventory_sha256):
    require(type(spec) is RuntimeSpec, "Exact RuntimeSpec required")
    spec.__post_init__()
    raw = Path(inventory).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_inventory_sha256, "Inventory receipt mismatch")
    data = json.loads(raw)
    require(data["repository"] == spec.repository and data["revision"] == spec.revision,
            "Inventory model identity mismatch")
    require(Path(data["snapshot_path"]) == Path(spec.snapshot_path), "Inventory snapshot path mismatch")
    entries = data["files"]
    require(type(entries) is list and entries, "Nonempty complete inventory required")
    names = [entry["relative_path"] for entry in entries]
    require(len(names) == len(set(names)), "Duplicate inventory path")
    root = Path(spec.snapshot_path)
    for entry in entries:
        name = PurePosixPath(entry["relative_path"])
        require(not name.is_absolute() and ".." not in name.parts and "\\" not in str(name)
                and ":" not in str(name), "Unsafe snapshot inventory path")
        path = root / str(name)
        require(path.is_file() and path.stat().st_size == entry["byte_size"], "Snapshot size mismatch")
        require(file_sha256(path) == entry["sha256"], "Snapshot SHA-256 mismatch")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    require(actual == set(names), "Snapshot inventory is incomplete")
    require({"config.json", "tokenizer_config.json", "tokenizer.json", "model.safetensors"}
            <= set(names), "Original model/tokenizer files missing")
    config = json.loads((root / "config.json").read_bytes())
    require(config.get("model_type") == "qwen2", "Unexpected model architecture")
    require("quantization_config" not in config, "Quantized model config forbidden")
    return data


@contextmanager
def initialization_only(torch_module, generation_mixin):
    """Prevent any module forward pass or generation inside the load smoke test."""
    def forbidden(*args, **kwargs):
        raise RuntimeBoundaryError("BR permits initialization/tokenization only")
    with patch.object(torch_module.nn.Module, "_call_impl", forbidden), \
            patch.object(generation_mixin, "generate", forbidden):
        yield


def inspect_parameters(model):
    counts = Counter()
    total = 0
    for _, parameter in model.named_parameters():
        require(str(parameter.device) == "cpu", "Model parameter is not on CPU")
        require(str(parameter.dtype) == "torch.float32", "Model parameter is not FP32")
        counts[(str(parameter.device), str(parameter.dtype))] += parameter.numel()
        total += parameter.numel()
    require(total > 0, "Empty model")
    require(not getattr(model, "is_quantized", False), "Quantized model forbidden")
    buffers = Counter()
    for _, buffer in model.named_buffers():
        require(str(buffer.device) == "cpu", "Model buffer is not on CPU")
        if buffer.is_floating_point():
            require(str(buffer.dtype) == "torch.float32", "Floating buffer is not FP32")
        buffers[str(buffer.dtype)] += buffer.numel()
    return {"unique_parameter_elements": total,
            "parameter_groups": [{"device": d, "dtype": t, "elements": n}
                                 for (d, t), n in sorted(counts.items())],
            "buffer_elements_by_dtype": dict(buffers), "quantized": False}


def load_cpu_fp32(spec, inventory, expected_inventory_sha256):
    """One verified local load; exceptions propagate without fallback or retry."""
    verify_snapshot(spec, inventory, expected_inventory_sha256)
    verify_preregistration(Path(__file__).resolve().parents[4])
    require(os.environ.get("HF_HUB_OFFLINE") == "1"
            and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "Offline flags required")
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    require(torch.version.cuda is None, "The frozen CPU-only PyTorch build is required")
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    kwargs = {"revision": MODEL_REVISION, "local_files_only": True,
              "trust_remote_code": False, "token": False}
    with initialization_only(torch, GenerationMixin):
        config = AutoConfig.from_pretrained(spec.snapshot_path, **kwargs)
        tokenizer = AutoTokenizer.from_pretrained(spec.snapshot_path, use_fast=True, **kwargs)
        require(bool(tokenizer.chat_template), "Snapshot chat template missing")
        model, loading_info = AutoModelForCausalLM.from_pretrained(
            spec.snapshot_path, config=config, dtype=torch.float32, device_map={"": "cpu"},
            low_cpu_mem_usage=True, use_safetensors=True, attn_implementation="eager",
            output_loading_info=True, **kwargs)
        require(not any(loading_info.get(key) for key in
                        ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")),
                "Snapshot weights did not load exactly")
        model.eval()
        receipt = inspect_parameters(model)
        receipt["loading_info"] = loading_info
    return model, tokenizer, config, receipt


def render_gate_input(tokenizer, gate_input):
    """Only frozen GateInput fields reach the exact tokenizer chat template."""
    messages = build_messages(gate_input)
    return tokenizer.apply_chat_template(list(messages), tokenize=True, add_generation_prompt=True)


def require_context_capacity(input_tokens, output_tokens, context_limit):
    require(all(type(n) is int and n > 0 for n in (input_tokens, output_tokens, context_limit)),
            "Explicit positive token counts required")
    margin = context_limit - input_tokens - output_tokens
    require(margin > 0, "Context budget exceeded; no truncation or smaller evidence depth")
    return margin
