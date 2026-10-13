# Phase 2H-B3.2-A2.1-G completion report

Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**.

Formal outcome: **LMFE_STRUCTURAL_CONFORMANCE_FAILED**. Core exact outcomes: **0/8**. Eight fresh top-level parsers were successfully constructed; all eight fixture traversals raised `Exception: Unsupported type None`. No fixture reached a completed native ACCEPT or REJECT. Exceptions were not credited as expected rejection. This is a failed core traversal qualification, not a constructor/environment block. Extended qualification did not run.

## Frozen entry state

- HEAD/tag `answerability-semantic-v2-lmfe-v0.2-imports-validated`: `8ccdacedd1b47de0471b534ac0b0e786e2c36299`; initial Git status clean.
- Predecessor `answerability-semantic-v2-lmfe-v0.1-enablement-failed`: `eaad53841caf73ad6933d7a7bf9612cea09376af`, unchanged.
- FR historical status: OWNER_REVIEWED / LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE. Import/API compatibility ESTABLISHED; conformance and decoder capability NOT_ASSESSED at entry. FR evidence was not edited.
- LMFE 0.11.3; interegular 0.3.3; pydantic 2.13.5; packaging 26.3; PyYAML 6.0.3. Complete frozen inventory: 36 distributions.
- Frozen exact V2 schema SHA-256: `6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.
- Pre-inventory SHA-256: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`.
- Post-inventory SHA-256: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`.
- Package additions/removals/version changes/METADATA-RECORD drift: 0/0/0/0. Saved post-run pip check: PASS.

## Configuration and native acceptance

Class: `lmformatenforcer.JsonSchemaParser`. Pass `json.loads(exact_original_schema_bytes)` with `config=None`; default `existing_stack=None`, `num_consecutive_whitespaces=0`. No schema transformation or configuration override.

All four environment variables were absent: LMFE_STRICT_JSON_FIELD_ORDER, LMFE_MAX_CONSECUTIVE_WHITESPACES, LMFE_MAX_JSON_ARRAY_LENGTH, LMFE_DEFAULT_ALPHABET.

Effective configuration:

```json
{
  "alphabet": "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{};:,./<>? `'\"",
  "force_json_field_order": false,
  "max_consecutive_whitespaces": 12,
  "max_json_array_length": 20
}
```

For each exact Unicode character, check membership in `get_allowed_characters()` then transition through `add_character()`. Accept only after complete input consumption with final `can_end()` true. No artificial EOS. Errors remain errors. Positions below are zero-based character positions at the exception, not disallowed-character positions; completion results are unavailable (`null`) because traversal failed.

## Core gate and triangulation

Core fixture artifact SHA-256: `992d5959789d81da2822b5995e83eb548332f50eb786ec4f8b765025ff127d68`.

The journal proves schema inventory and fixture/config freezes preceded the execution launch and all M1-M8 calls. Historical S1/S2/S3 strings were copied byte-exactly; no repaired fields, normalized text or easier replacement M1 was used.

| Fixture | Expected | JSON | Frozen schema | LMFE | Exception character position |
|---|---|---|---|---|---|
| M1 | ACCEPT | VALID | VALID | ERROR | 35 |
| M2 | REJECT | VALID | INVALID | ERROR | 16 |
| M3 | REJECT | VALID | INVALID | ERROR | 35 |
| M4 | REJECT | VALID | INVALID | ERROR | 35 |
| M5 | REJECT | VALID | INVALID | ERROR | 16 |
| M6 | REJECT | VALID | INVALID | ERROR | 19 |
| M7 | REJECT | VALID | INVALID | ERROR | 19 |
| M8 | REJECT | VALID | INVALID | ERROR | 19 |

The independent oracle confirmed M1 valid and M2-M8 invalid under the original raw schema; all eight are syntactically valid JSON. The authoritative oracle is the frozen exact-keyword validator, SHA `ffe40fc052f6c25484d0abdf60411c1317873c1965e38c94860d6c88781181f9`, isolated as two pure function ASTs without running historical model imports. It is not described as a general JSON Schema implementation. Native parser results were never post-filtered or repaired.

## Extended gate and material features

Status: **NOT_RUN_DUE_TO_CORE_GATE_FAILURE**. Executed: **0**. The 38-probe plan was frozen before native core execution, SHA-256 `b23eb615192168489c1625768f388bb2c2869df79c5bc06bed8b4a1cca589f52`. No adaptive probes, alternate configuration or further native calls followed the failure.

| Keyword | Criticality | Result |
|---|---|---|
| $schema | ANNOTATION | DIALECT_ANNOTATION |
| additionalProperties | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| allOf | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| anyOf | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| const | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| contains | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| else | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| enum | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| exclusiveMaximum | NOT_APPLICABLE | NOT_APPLICABLE |
| exclusiveMinimum | NOT_APPLICABLE | NOT_APPLICABLE |
| if | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| items | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| maxItems | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| maxLength | NOT_APPLICABLE | NOT_APPLICABLE |
| maximum | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| minItems | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| minLength | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| minimum | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| oneOf | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| pattern | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| properties | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| required | CRITICAL | INCOMPLETE_OR_MISMATCH |
| then | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| type | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |
| uniqueItems | CRITICAL | NOT_RUN_DUE_TO_CORE_GATE_FAILURE |

All present raw-schema constraints are critical: violating them can admit output rejected before adapter processing. The core required-field gate is incomplete/mismatched due to traversal exceptions. No invalid object was accepted to completion, so this run does not establish an individually ignored keyword or justify a keyword-specific MATERIAL_SCHEMA_FEATURE_UNENFORCED claim. Specific enforcement/root cause is not independently isolated. The observed exception is preserved without speculative causal attribution. Extended features are unassessed. `$schema` is an annotation; absent keywords are not probed.

Actual-evidence-count checks, rank identity mapping, semantic support reasoning and GateOutput conversion remain the unchanged adapter's responsibility. No semantic accuracy was scored.

## Counts, boundaries and observations

- Core parser fixture executions: 8; fresh top-level parsers: 8; extended: 0; retries: 0. Internal immutable state clones are not extra fixture executions.
- Offline helper tests before M1: **15/15 PASS**, native parser calls in those tests: 0.
- Tokenizer loads/prefix integration calls/prefix-tree builds/model initialization/Qwen initialization/generate/forward/semantic outputs: all 0.
- DEVELOPMENT semantic calls: 0; retrieval calls: 0; Phase 2H HELD_OUT access: false; Phase 2G private HELDOUT access: false.
- Fresh V2 semantic suite: **NOT YET AUTHORED**. V2 candidate: PRE_REGISTERED_NOT_EVALUATED.
- Package installations/removals/mutations/downloads: 0.
- Observed socket event: one local `socket.gethostname`; no DNS resolution, connect, bind, remote network request or download observed. Observed import-time subprocess: `C:\windows\system32\cmd.exe /c "ver"`. No broad execution-wrapper blocking or environment repair.
- Runtime observations show no protected-file opens or forbidden scientific calls. Pip check ran subsequently as the required administrative integrity check.

## Integrity and review

All historical tracked Git files remained unchanged before adding only this phase's exact artifact attributes. F/FR raw receipt hashes, original schema/oracle, parser config/fixtures and execution-source hashes were rechecked. This includes unchanged historical Git state for E, XGrammar D/Attempt 2, R2/R1/Attempt 1, V2/V1, runtime freeze, B3/B2, benchmark, retriever, corpus and engine. No benchmark or private content inspection was used for this verification.

Execution source SHA-256:

- Helper: `45cc57a9534a56fef5834fffd422e618e2bb0574adaed90ac019ab4072d66bc0`.
- Offline tests: `7b0675b7b09576dde885d6534847400be23135f7a7f65201e98238cfb94cd2e7`.

`ARTIFACT_SHA256.json` provides all final artifact hashes, excluding its own self-hash; the completion response provides that receipt's hash. `CHANGED_FILES.json` lists the complete phase candidate. The execution source receipt records pre-run hashes and is unchanged. Exact artifact-path `-text` rules preserve evidence bytes; Python helper/tests retain ordinary text handling. No wheels, venv, model, cache or private file is part of the candidate. No commit or tag was created. Stop for owner review; Transformers structural smoke was not begun.
