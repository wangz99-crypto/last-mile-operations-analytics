# Qwen Structural Smoke Eager Runtime Recovery

Status: OWNER_REVIEWED / QWEN_STRUCTURAL_SMOKE_RECOVERY_PASS
Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-16
Scientific review: PASS — END-TO-END MODEL STRUCTURAL RUNTIME ESTABLISHED
Outcome: QWEN_STRUCTURAL_SMOKE_RECOVERY_PASS
Base: b696dc6c521c05ad79b32256975d0a10a21644de
Tag: answerability-semantic-v2_1-qwen-smoke-v0.1-runtime-failed
Run type: RECOVERY_RUN_AFTER_NON_RESULT_BEARING_RUNTIME_FAILURE
Historical outcome remains QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED: attempted generate=1, observed forward=1, completed=0.
Recovery mode: PYTORCH_FORCE_EAGER_FOR_OUTLINES_MASK_RUNTIME; torch.compiler.set_stance("force_eager") only.

Counts:
```json
{
  "preflight_PASS": 3,
  "completed_generations": 3,
  "JSON_parse_PASS": 3,
  "exact_schema_PASS": 3,
  "adapter_PASS": 3,
  "combined_structural_accept": 3
}
```
Recovery counters:
```json
{
  "DEVELOPMENT_access": 0,
  "downloads": 0,
  "forward": 337,
  "generate": 3,
  "mask_preflight_calls": 3,
  "model_initialization": 1,
  "package_mutations": 0,
  "repairs": 0,
  "retries": 0,
  "retrieval": 0,
  "timeouts": 0,
  "tokenizer_loads": 1
}
```
Cumulative attempted generate calls: 4

Semantic correctness: NOT_EVALUATED. All reused fixtures remain EXCLUDED_FROM_SEMANTIC_QUALIFICATION. Fresh formal suite: NOT YET AUTHORED.
DEVELOPMENT access=0; retrieval=0; Phase 2H HELD_OUT=false; Phase 2G private HELDOUT=false.
Environment integrity: True; frozen historical/helper inputs unchanged: True; installed execution source bytes unchanged: True.
Per-call raw bytes are recorded before structural processing; no repair, retry, configuration change or semantic scoring. Full model/snapshot/config/source identities and failure traceback (if any) are in RUNTIME_IDENTITY.json. No commit, tag, compiler installation or package mutation. Stop for owner review.

## Owner-reviewed qualification scope

The historical attempt remains OWNER_REVIEWED / QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED. Its evidence is neither rewritten nor superseded. Historical attempted generate calls=1, completed generations=0. Recovery attempted generate calls=3, completed generations=3. Cumulative attempted generate calls=4. This recovery is not the first model execution.

Frozen recovery evidence: eager mask preflight=3/3 PASS; model initializations=1; tokenizer loads=1; generate calls=3; measured forward calls=337; completed generations=3/3; JSON parse=3/3 PASS; exact frozen schema=3/3 PASS; adapter=3/3 PASS; COMBINED_STRUCTURAL_ACCEPT=3/3; retries=0; repairs=0; timeouts=0. Semantic correctness=NOT_EVALUATED.

Sole runtime recovery mechanism: torch==2.14.0+cpu; official torch compiler stance=force_eager, scoped to the installed masking function preflight and generation execution. Its purpose is to bypass the installed outlines_core Torch mask kernel's torch.compile / Inductor native compilation path. Compiler installation=0; compiler invocation required by recovery=0. This is an execution-mode change only, not a change to model semantics, generation hyperparameters, decoder language, exact schema, adapter, or smoke fixtures.

Model: Qwen/Qwen2.5-1.5B-Instruct; revision=989aa7980e4cf806f80c7fef2b1adb7bc71aa306; device=CPU; dtype=FP32. The local ten-file snapshot verification is preserved. Chat-template SHA-256=cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f.

Frozen generation configuration: greedy; num_beams=1; max_new_tokens=512; repetition_penalty=1.0; seed=0. Requested-vs-actual=67/67 MATCH for every recovery generation. No generation parameters changed.

Frozen smoke fixtures SHA-256=3abf857514394cbbab8ea2b2f3f14095ffe917b8dd16906f5d97b6120ac598a6. All three remain EXCLUDED_FROM_SEMANTIC_QUALIFICATION and must not be reused as formal semantic qualification cases.

Structural component statuses: direct-regex decoder=QUALIFIED; exact validator=QUALIFIED; combined structural pipeline=QUALIFIED; Qwen constrained-generation structural runtime=QUALIFIED. This checkpoint establishes runtime/structure only. It does not establish material-support judgment quality, ALLOW/ABSTAIN accuracy, reason-code accuracy, evidence semantic correctness, or DEV eligibility.

Saved environment evidence is preserved: package additions=0; package removals=0; version drift=0; pip check before=PASS; pip check after=PASS; downloads=0; external network connections=0. Local loopback probing remains non-external.

Phase 2H DEVELOPMENT access=0; retrieval executions=0; Phase 2H HELD_OUT=false; Phase 2G private HELDOUT=false. Fresh V2.1 semantic qualification suite=NOT YET AUTHORED.

Owner finalization changed only this administrative owner-review record and the dependent FINAL_SHA256.json. Recovery preflight, protocol, runtime identity, raw generations, structural results, helper, fixtures and historical records retain their exact bytes. No model or qualification rerun, semantic-suite authoring, package operation, commit or tag occurred during finalization.
