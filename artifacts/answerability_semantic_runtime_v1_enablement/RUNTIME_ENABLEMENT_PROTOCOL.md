# Phase 2H-B3.2-BR runtime enablement protocol

Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**.

This is the owner-authorized replacement runtime for the sole unchanged target
`Qwen/Qwen2.5-1.5B-Instruct`: local Windows, CPU, Hugging Face Transformers,
original unquantized snapshot, loaded as FP32. Attempt 1 remains the immutable
owner-reviewed QUALIFICATION_BLOCKED checkpoint. BR does not assess model capability.

Base HEAD/tag: `2c28f67aded58e8331149a7af8ab5b18af48ce02` /
`answerability-semantic-model-v0.1-qualification-blocked`.
Semantic preregistration tag: `answerability-semantic-gate-v0.1-pre-model` /
`4b13cb72482da6fd1109aa5f5ee4b7dbcaaf8c87`.

Use installed CPython 3.12.10 and a dedicated environment at
`C:/Users/zhewa/.virtualenvs/llm-rag-semantic-qwen25-1p5b`.
Resolve dependencies without benchmark input, record all exact versions before
loading the model, and do not upgrade them after initialization. CPU PyTorch comes
from its official CPU wheel index; the other runtime dependencies come from PyPI.
No virtual environment, cache, pip report or weight is committed.

Resolve the authorized model repository's current commit once, then download only
that immutable SHA. Keep the snapshot in the dedicated external environment's
model cache. Record every downloaded file's path, byte size and SHA-256.
No alternate model, revision comparison or remote inference is permitted.

Load tokenizer/config/weights offline from the verified snapshot with
`local_files_only=True`, `trust_remote_code=False`, CPU placement, FP32 dtype and
safetensors. No quantization, offload, GPU, vLLM or alternate backend is permitted.
Record all parameter device/dtype counts. A mandatory load failure stops BR.

No model forward pass, generate call, semantic output, retrieval, real DEVELOPMENT
GateInput or synthetic capability evaluation is authorized. Load-time checks and
tokenizer-only synthetic stress construction are permitted. Frozen semantic prompt,
parser, registry and GateInput remain unchanged. Preserve their message contents
and evidence rank order when applying the snapshot's existing chat template.

Context validation uses only the canonical prompt, synthetic question and frozen
public policy corpus. The question contract has no explicit length maximum, so
there can be no universal finite context guarantee. Predeclare an 8192-character
synthetic question, choose the ten largest public section payloads by tokenizer
length (without Gold or retrieval), reserve 4096 output tokens and require a positive
remaining context margin. Record the assumption, measured tokens and corpus hashes;
do not inspect actual DEVELOPMENT question lengths. Oversized future inputs must
fail explicitly rather than truncate evidence.

Propose future greedy decoding on CPU FP32: do_sample=false, num_beams=1,
max_new_tokens=4096. Temperature/top_p have no sampling effect under greedy decoding;
record their exact effective values and that limitation. Record an explicit seed,
timeout proposal and zero quality/infrastructure retries. These settings are a
candidate for later qualification and owner review, not permission to generate.
Without an authorized constrained decoder, use PROMPT_ONLY_STRICT_JSON followed
by the frozen parser; no output repair or retry for quality.

Allowed outcomes: RUNTIME_ENABLED_AWAITING_QUALIFICATION or RUNTIME_ENABLEMENT_BLOCKED.
No claim of QUALIFIED. Stop after runtime artifacts, non-semantic tests and integrity
checks. Do not run the 12+3 qualification, B3.2-C, B4 or HELD_OUT. Do not commit or tag.
