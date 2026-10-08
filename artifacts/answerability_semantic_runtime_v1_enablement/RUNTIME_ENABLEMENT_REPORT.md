# Phase 2H-B3.2-BR runtime enablement report

Outcome: **RUNTIME_ENABLED_AWAITING_QUALIFICATION**
Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**
Model capability: **NOT_ASSESSED**
Candidate: **SEMANTIC_MATERIAL_SUPPORT_V1 / PRE_REGISTERED_NOT_EVALUATED**

## Anchors and scope

The pre-run working tree was clean. HEAD and
`answerability-semantic-model-v0.1-qualification-blocked` both resolved to
`2c28f67aded58e8331149a7af8ab5b18af48ce02`.
`answerability-semantic-gate-v0.1-pre-model` resolved to
`4b13cb72482da6fd1109aa5f5ee4b7dbcaaf8c87`.
Attempt 1 remains OWNER_REVIEWED / QUALIFICATION_BLOCKED, with capability
NOT_ASSESSED and zero model calls. Its five artifacts are unchanged.
All seven preregistration files, schema/receipt hashes, 110 protected source/files,
five B2 artifacts and six Round-1 artifacts passed integrity checks.
B2 evidence remains
`1ba747fe7a6eaa97610d05fd3690048aa062723f87585e38725dd149b6a57a52`.
No benchmark question bodies were parsed; integrity access was byte hashing only.

This phase implements the owner's explicit local Windows CPU Transformers runtime
change. It does not change the model target or qualify semantic capability.

## Immutable model and original snapshot

- Repository: `Qwen/Qwen2.5-1.5B-Instruct`.
- Immutable revision: `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Current-revision resolution count: 1. Every snapshot operation used that SHA.
- Snapshot path: `C:\Users\zhewa\.virtualenvs\llm-rag-semantic-qwen25-1p5b\hf-cache\models--Qwen--Qwen2.5-1.5B-Instruct\snapshots\989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Complete snapshot: 10 files, 3,098,973,447 bytes.
- All files have SHA-256/size inventory; LFS SHA-256 and ordinary Git blob identities
  independently matched the remote inventory at this immutable commit.
- Representation: original unquantized snapshot. Files were not transformed.
- Model weights remain outside the repository. No model/cache/venv is staged.

## Runtime identity and load verification

Dedicated environment: `C:\Users\zhewa\.virtualenvs\llm-rag-semantic-qwen25-1p5b\Scripts\python.exe`.
Installed CPython: 3.12.10; no new Python distribution installed.
Platform: Windows-11-10.0.26200-SP0; architecture: AMD64.
CPU: AMD Ryzen AI 5 430 w/ Radeon 840M; 4 physical / 8 logical cores.
System RAM: 16,436,219,904 bytes.
Observed AMD Radeon 840M graphics was not used.

| Dependency | Exact version |
| --- | --- |
| accelerate | 1.15.0 |
| huggingface_hub | 0.36.2 |
| safetensors | 0.8.0 |
| tokenizers | 0.22.2 |
| torch | 2.14.0+cpu |
| transformers | 4.57.6 |

DEPENDENCY_RECEIPT.txt pins all 28 installed distributions, including pip.
Sanitized wheel archive hashes and the two installation report hashes are in the
journal. Dependencies did not change after the import-compatible receipt was written.
The CPU torch build has no CUDA runtime. No vLLM, GGUF, llama.cpp, ONNX, DirectML,
ROCm, quantization or remote inference was used.

Actual model initialization count: **1**. Tokenizer load count: **2** (one alongside
model initialization; a second tokenizer-only context process, with model reload blocked).
Every one of 1,543,714,304 unique parameter
elements is on CPU in torch.float32; the 64 floating buffer elements are also FP32.
Missing, unexpected and mismatched weight keys and loading errors were all empty.
Attention implementation: eager. Threads: 4 intra-op / 1 inter-op; seed: 0;
deterministic algorithms enabled. This is an initialization result, not a claim
of empirically verified generation determinism.

The loader verifies the snapshot file inventory and frozen semantic hashes before
loading, requires offline flags and the exact repository/revision, and forbids
module forward calls and GenerationMixin.generate during the smoke test.
The helper implements initialization and tokenization, with no semantic-generation
entry point. BR does not invoke the returned model for inference.
Runtime adapter SHA: `f998897ad45d36ef5ca894da8ba07406d8c2c004e72ca29620d908b80713ba2f`.
Runtime test source SHA: `b52c077f6f4db55243df909d42692fcfa9f842d49ed13a864793c6c8323641e2`.
Python source keeps normal repository text handling; these are raw current-source hashes.

## Chat template, output mode and future configuration

The exact snapshot tokenizer loaded successfully. Its unchanged effective template
SHA-256 is `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.
The receipt includes the template itself and tokenizer file hashes. Requests use the
frozen semantic messages unchanged, preserve rank order, and apply the template with
`tokenize=True, add_generation_prompt=True`; no tools or custom template are provided.

Structured-output mode: **PROMPT_ONLY_STRICT_JSON**. No authorized native JSON-schema
constraining layer is configured. Future output must pass the unchanged semantic
parser; no repair prompt, repair LLM or quality retry exists.

The unexecuted proposal is CPU/float32, do_sample=false, num_beams=1,
max_new_tokens=4096, seed=0, four CPU threads and one inter-op thread.
Temperature=1.0 and top_p=1.0 are recorded effective config values; both are
NOT_APPLICABLE_UNDER_GREEDY_DECODING. The full resolved GenerationConfig is recorded.
Proposed timeout is 600 seconds, to be enforced by a future isolated worker;
that timeout worker is not implemented or exercised in BR. Quality retries are
FORBIDDEN (0); infrastructure retries are NOT_AUTHORIZED (0) for future semantic calls.
This is a backend proposal, not an owner-approved instance of the historical
provider-oriented configuration schema. A later qualification must explicitly map
its greedy-parameter and JSON-schema post-validation semantics without changing
that frozen schema. No generation was executed to prepare these configuration data.

## Context-window check

Declared model context limit: **32,768 tokens**.
Tokenizer declared maximum: 131,072.
Effective limit used: 32,768.
The complete canonical prompt/schema, active-bundle metadata, 8192-character
synthetic question and ten largest public section payloads measured
**9,405 input tokens**.
Reserved output: **4,096 tokens**.
Remaining margin: **19,267 tokens**.

The question contract has no explicit maximum. This measured synthetic stress test
is a conditional adequacy result, not a universal upper bound for arbitrary questions.
Future requests must be measured individually and rejected explicitly when over
budget; evidence must not be truncated. No actual DEVELOPMENT question lengths
were inspected or tokenized.

The synthetic question can be reconstructed with CPython 3.12.10:

```python
rng = random.Random(0)
prefix = 'Synthetic length-only stress input; no answer is requested: '
question = prefix + ''.join(
    rng.choice(string.ascii_letters + string.digits + ' ')
    for _ in range(8192 - len(prefix))
)
```

For corpus size selection, each section's full readable payload is serialized as
sorted, indent-2 UTF-8 JSON with final LF, using rank=10 and score=0.99; tokenize
without special tokens, select the largest ten, tie by canonical identity. The
selected identities/counts are saved in the context receipt. Assemble GateInput in
that order with ranks 1..10 and synthetic scores `0.99 - rank * 0.001`, then use the
frozen build_messages and exact tokenizer template. These synthetic scores provide
field shape only. SectionStore was used for public corpus reading, with zero query
retrieval calls; no Gold or benchmark object was used.

## Network and infrastructure provenance

Two pip installation operations used the official PyTorch CPU index and PyPI;
their reports contain 27 selected distribution records, some from cache.
Exact raw pip HTTP request/download counts were not instrumented and are not
inferred from package counts. No browsing or alternate-model discovery occurred.

Hugging Face resolution occurred once. There were three snapshot download operations:

1. The initial external observer omitted the same-repository resolve-cache redirect
   path and stopped before acquisition completed. Its recorded boundary observed
   2 GET and 4 HEAD requests to huggingface.co.
2. The redirect was verified at the same immutable SHA. The next cache operation
   stopped with OSError, after 5 GET and 9 HEAD sends to huggingface.co. The precise
   original OSError detail was not captured; its root cause is not claimed.
3. A single Windows cache writer completed the same snapshot with symlink support
   reported false: 7 GET and 13 HEAD sends to huggingface.co, plus one GET to
   us.aws.cdn.hf.co. Ten final snapshot files total 3,098,973,447 bytes.

These are explicitly scoped observer counts, not a uniform wire-level total.
All interruption events remain in the journal; no model/revision/dependency fallback
occurred and no downloaded model bytes were edited to satisfy hashes.

The first offline load wrapper also stopped during Transformers optional-package
availability detection before tokenizer or model loading. Its import observer was
corrected to permit availability probes. The exact trace and correction are recorded;
actual AutoModelForCausalLM.from_pretrained calls were instrumented separately and
occurred once. This was not a weight-loading or model-capability failure.

Offline load and tokenizer phases allowed only local socket construction/hostname
and loopback bind probes. Each successful phase observed one socket construction,
one gethostname and one loopback bind; no connection or external DNS request occurred.
No dependency upgrade or runtime/config change followed actual weight initialization.

## Tests, counters and review boundary

**107/107 PASS**: 23 new model-free runtime tests plus 84 existing synthetic
semantic/scorer/boundary tests. They cover exact identity, CPU/FP32, inventory checks,
no fallback, metadata exclusion, rank/message preservation, no generation/forward
path, context rejection and frozen semantic hashes. Initial sandbox test execution
failed on temporary-directory permissions; unchanged tests passed outside it.
Model imports, sockets, private paths and real benchmark payloads were blocked in tests.

- Actual model initialization: 1; successful: 1.
- model.generate calls: 0; model forward calls: 0; semantic output calls: 0.
- DEVELOPMENT semantic calls: 0; retrieval calls: 0; alternate-model attempts: 0.
- Phase 2H HELD_OUT access: false; Phase 2G private HELDOUT access: false.
- No 12+3 qualification suite or capability evaluation; no B3.2-C, eligibility or B4.
- No commit or tag created. Stop for owner review.

## Artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| RUNTIME_ENABLEMENT_PROTOCOL.md | `953a10e51fdf4fd9361ec913e3f05bb1cf236ed1dab9b62b7ee59e44cf930139` |
| MODEL_SNAPSHOT_IDENTITY.json | `3acdf19d51a5b6d639ea78b3b897176e9a02818d960b1e82fffbb91ef65e6323` |
| MODEL_FILE_INVENTORY.json | `bd997774f25c307eb4421488607110f011592250e0bd82b2a096b3a7cf17b4fb` |
| LOCAL_RUNTIME_IDENTITY.json | `36e76d539a878a106ddcc843db8db48c4e2e468737f97e628eb853d22c643a76` |
| DEPENDENCY_RECEIPT.txt | `1e91e941011fb18a0c33b0cc3a1ba4b7452a1bc5cddcb72cefb5ac07db4caabd` |
| CHAT_TEMPLATE_RECEIPT.json | `a3922fabdfd4118b9ee974539c9bb2ad57447984dad3711cf0375058822e11c2` |
| CONTEXT_WINDOW_QUALIFICATION.json | `557ff3a3fdee5f52b068459da35851d37bf7ea501bd2a48a57f133113a4eca76` |
| PROPOSED_INFERENCE_CONFIG.json | `0b8807810fe4b8c73d14f64cf2567890d9ed9d6b2a0b07adad5d073415b5d8fc` |
| RUNTIME_ENABLEMENT_JOURNAL.jsonl | `e054616916099ca34081c0ab239945aa5e29663a29bd3b15728b8ac3497aea06` |

This report is hashed by RUNTIME_FREEZE_RECORD.md. That record has no self-hash;
its final digest is reported separately. The journal binds the eight already-written
scientific artifacts; it does not require a circular hash of downstream documents.
Expected Git scope is these eleven BR artifacts, the new runtime helper and its tests,
and eleven exact .gitattributes entries. No private artifacts, weights, caches,
credentials, installation reports or virtual environments belong in the candidate.
