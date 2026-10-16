# Qwen Three-Call Structural Smoke

Status: OWNER_REVIEWED / QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED
Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-15
Scientific review: PASS — RUNTIME FAILURE ACCEPTED, STRUCTURAL RESULT NOT OBTAINED
Primary failure classification: OUTLINES_CORE_TORCH_MASK_INDUCTOR_TOOLCHAIN_UNAVAILABLE
Runtime classification: INFRASTRUCTURE_RUNTIME_FAILURE_BEFORE_STRUCTURED_OUTPUT
Outcome: QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED

Base: c044cc3d9f4e15c147b7b5dade7647f24c05d707
Tag: answerability-semantic-v2_1-structure-v0.1-qualified

Counts:
```json
{
  "generation_completed": 0,
  "JSON_parse_PASS": 0,
  "exact_schema_PASS": 0,
  "adapter_PASS": 0,
  "combined_structural_accept": 0
}
```
Counters:
```json
{
  "DEVELOPMENT_access": 0,
  "downloads": 0,
  "forward": 1,
  "generate": 1,
  "model_initialization": 1,
  "package_mutations": 0,
  "repairs": 0,
  "retries": 0,
  "retrieval": 0,
  "timeouts": 0,
  "tokenizer_loads": 1
}
```
Semantic correctness: NOT_EVALUATED. No semantic labels, scoring, repair, retry or tuning.
Fresh formal V2.1 semantic qualification suite: NOT YET AUTHORED.
Both HELDOUT sets accessed: false. DEVELOPMENT access: 0. Retrieval: 0.
Environment integrity: True. Frozen sources unchanged: True. Fixtures/protocol unchanged: True.

Requested and observed effective configuration, all source/model hashes, per-call raw outputs and structural dispositions are recorded in the adjacent JSON artifacts. No commit or tag.

## Execution stop and attempt accounting

SMOKE-01: one generate invocation, one observed causal-LM forward, then runtime failure before a completed output. The traceback identifies Outlines' Torch bitmask kernel invoking Torch Inductor, which reports `InvalidCxxCompiler: Compiler: cl is not found.` This is runtime/infrastructure failure, not evidence of schema or adapter rejection. No environment repair, fallback or retry occurred.
SMOKE-02 and SMOKE-03: NOT_RUN_AFTER_RUNTIME_FAILURE. Three calls were authorized; one was attempted and two remain unexecuted. Generation completions=0; JSON/schema/adapter executions=0, PASS counts=0; combined accepts=0. These are not three structural failures. RAW_GENERATIONS retains an empty completed-output list; the original traceback and counters remain unchanged in RUNTIME_IDENTITY.

## Frozen identity and conformance

Model: Qwen/Qwen2.5-1.5B-Instruct
Revision: 989aa7980e4cf806f80c7fef2b1adb7bc71aa306
CPU, FP32; all 10 local snapshot files matched frozen hashes before loading.
Chat template SHA-256: cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f
Fixture file SHA-256: 3abf857514394cbbab8ea2b2f3f14095ffe917b8dd16906f5d97b6120ac598a6
Decoder: DECODER_ENFORCEMENT_REGEX_V2_1_V0_1
Exact validator: jsonschema==4.26.0 / Draft202012Validator, referencing==0.37.0.

Frozen effective configuration: do_sample=false, num_beams=1, max_new_tokens=512, repetition_penalty=1.0; seed=0, deterministic algorithms=true, 4 Torch threads and 1 interop thread. Inactive greedy sampling parameters remain temperature=1.0, top_p=1.0, top_k=50. Timeout=600 seconds. The entire requested configuration is recorded alongside the actual config. All serialized parameters matched for the sole attempted call before its forward pass. Calls 2/3 have no actual config observation because they were not executed.

Package additions/removals/version drift=0; all 64 package METADATA/RECORD identities unchanged; pip check pre/post=PASS. Socket audit recorded gethostname, socket construction and one IPv6 loopback bind to [::1]:0 only; no outbound connect, DNS resolution, download or network fallback. No package mutation.

All previous artifacts, frozen source identities and current pre-call fixture/protocol bytes remained unchanged. Only seven smoke artifacts and one new execution helper were created. The artifact directory remains ignored under existing repository rules. No files staged, no commit, no tag. Stop for owner review; no fresh semantic qualification suite authored or executed.

## Owner-reviewed disposition

Formal outcome remains QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED. No result-bearing raw generation completed. SMOKE-01 = runtime failure; SMOKE-02 = NOT_RUN; SMOKE-03 = NOT_RUN. Model initializations=1, tokenizer loads=1, generate calls attempted=1, measured forward calls=1, completed generations=0, generation retries=0, repairs=0, timeouts=0. JSON parse=NOT_RUN; exact-schema validation=NOT_RUN; adapter=NOT_RUN; combined structural accepts=0; semantic correctness=NOT_EVALUATED.

Established runtime cause: outlines==1.3.3, outlines_core==0.2.14, runtime tensor library=torch. The path was OutlinesCoreLogitsProcessor -> outlines_core.kernels.torch.apply_token_bitmask_inplace -> torch-compiled masking kernel. TorchInductor attempted native compilation and Windows C++ compiler `cl` was unavailable.

This attempt is not classified as decoder structural failure, JSON failure, exact-schema failure, adapter failure, or semantic-model failure. No limitation of Qwen semantic capability, the direct-regex decoder language, the exact validator, or the adapter is inferred from this infrastructure failure before structured output.

Previously qualified structural components retain their status: direct-regex decoder=QUALIFIED; exact validator=QUALIFIED; combined structural pipeline=QUALIFIED; adapter=UNCHANGED. No component qualification was rerun. Model/revision, CPU/FP32, chat template, generation configuration and fixtures retain their frozen identities. Requested-vs-actual configuration=67/67 MATCH for the sole attempted call. All three smoke fixtures remain EXCLUDED_FROM_SEMANTIC_QUALIFICATION.

Historical package additions=0, removals=0, version drift=0; pip check before/after=PASS; downloads=0; external network connections=0. The saved local IPv6 loopback probe is recorded separately and is not external network activity. These are preserved execution receipts; no model or package operation was performed during owner finalization.

Phase 2H DEVELOPMENT access=0; retrieval executions=0; Phase 2H HELD_OUT=false; Phase 2G private HELDOUT=false. Fresh V2.1 semantic qualification suite=NOT YET AUTHORED.

Owner finalization changed only this administrative record and its dependent FINAL_SHA256.json. Raw generations, runtime identity, structural results, smoke fixtures, protocol, helper and all historical frozen sources remain byte-identical. No generation, retry, compiler installation, Outlines source edit, runtime recovery, commit or tag occurred during finalization.
