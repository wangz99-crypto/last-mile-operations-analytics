# A2.1-G: pure LMFE character-parser qualification

Status at preregistration: CANDIDATE_AWAITING_OWNER_REVIEW. No semantic qualification is authorized.

Base HEAD and `answerability-semantic-v2-lmfe-v0.2-imports-validated` both resolve to `8ccdacedd1b47de0471b534ac0b0e786e2c36299`. Git status was empty before this phase created its helper. Historical failed enablement tag remains at `eaad53841caf73ad6933d7a7bf9612cea09376af`. FR is OWNER_REVIEWED / LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE: import/API compatibility established, structural conformance and decoder capability not assessed at entry.

## Frozen target and environment

Use the exact original schema bytes at `artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json`, SHA-256 `6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`. Passing `json.loads` of these bytes preserves the original schema structure and field order; no transformation, simplification, Pydantic substitute, repair, or LMFE-specific schema is permitted.

Use the frozen Windows Python 3.12.10 semantic environment. The complete 36-distribution inventory must equal frozen FR SHA-256 `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`. This includes lm-format-enforcer 0.11.3, interegular 0.3.3, pydantic 2.13.5, packaging 26.3 and PyYAML 6.0.3. Installation or package mutation is forbidden.

`PARSER_CONFIGURATION.json` records installed source hashes and all effective defaults. All four LMFE environment overrides are absent. Pass `config=None`; effective field-order forcing is false, consecutive-whitespace maximum is 12, default array maximum is 20, and alphabet is the exact installed `COMPLETE_ALPHABET`. No override or post-result configuration change is authorized.

## Installed API and acceptance

Import only the public `JsonSchemaParser` class from `lmformatenforcer`. Its constructor accepts `json_schema`, optional `config`, optional `existing_stack`, and `num_consecutive_whitespaces`. Each fixture starts with the original schema, `config=None`, no existing stack, and whitespace count zero.

Installed source specifies `get_allowed_characters()`, `add_character(character)` returning the next immutable parser state, and `can_end()`. Before every transition, test the exact next Unicode character against the allowed characters. Reject at the first disallowed character. Accept only after consuming the entire exact text without exceptions AND observing final `can_end() == True`. No artificial end token is appended. Record zero-based character position and UTF-8 byte offset, completion state, exception and elapsed time. Exceptions are ERROR, never credited as expected rejection.

A fresh top-level parser is constructed for each fixture. Internal state clones created by the library during traversal do not constitute retries or additional fixture executions. No tokenizer, prefix tree, HF integration, model, generation, or forward call is allowed. Import-time module loading is not tokenizer/model initialization; runtime observations separately watch actual calls and protected file access. Observation does not monkeypatch subprocess/platform/socket behavior.

## Freeze order and core gate

The journal records configuration freeze, completed deterministic keyword inventory, then core fixture freeze and extended-plan freeze, all before native parser execution. Offline helper tests must pass and source hashes must be frozen before M1.

Core fixture texts are copied exactly from the already frozen diagnostic fixture container. M1 is the complete valid object; M2/M3/M4 omit decision/context/reason respectively; M5 omits all three; M6/M7/M8 are exact historical Attempt-2 S1/S2/S3 raw strings. Each text has an independent UTF-8 SHA-256 and lengths. Neither fixture contents nor expectations may change after freeze.

Exactly eight core fixture executions are budgeted, with zero retries. Expected outcomes are ACCEPT, REJECT, REJECT, REJECT, REJECT, REJECT, REJECT, REJECT. Complete these eight core measurements and do not start extended measurements unless all eight match. If the parser cannot be instantiated without mutation, preserve the constructor failure and report BLOCKED without further construction attempts. A traversal error or acceptance mismatch is a failed core result.

## Independent triangulation

Every executed fixture receives standard JSON parsing, independent frozen raw-schema validation, and native LMFE traversal. The authoritative validator is the existing frozen exact-schema keyword interpreter from `xgrammar_v2_smoke.py`, SHA-256 `ffe40fc052f6c25484d0abdf60411c1317873c1965e38c94860d6c88781181f9`. Only its two pure function ASTs are compiled; its module imports/model runner are not executed. This is not represented as a general JSON Schema implementation. Its keyword guard covers every keyword used in the frozen schema. Oracle results describe the input independently; they never repair or filter LMFE results.

## Conditional extended plan and criticality

The complete deterministic extended plan is frozen before core execution and cannot be adapted to results. It supplies valid and invalid probes for every material keyword where meaningful. Stop at the first critical extended mismatch; never add fixtures after exposure. If the core gate fails, extended results must be NOT_RUN_DUE_TO_CORE_GATE_FAILURE.

All materially present raw-schema constraints are CRITICAL because violating them can admit an object rejected before adapter processing. Required fields and forbidden unknown properties are critical. `$schema` is an annotation. Absent exclusive bounds and maxLength are not tested. Eleven-rank tests necessarily overlap array length, uniqueness and rank-domain constraints; no isolated causal attribution is claimed. Disjoint oneOf branches cannot support a multiply-matching valid fixture.

Actual evidence-count bounds, rank-to-policy identity mapping, semantic support judgment and final GateOutput transformation remain adapter responsibilities. No semantic accuracy is evaluated. No hidden retrieval or exact lookup occurs.

## Outcomes and preservation

QUALIFIED requires core 8/8, all planned critical extended probes matching, consistent triangulation, zero retries and no drift or model calls. FAILED means any core mismatch or critical extended failure. BLOCKED is reserved for inability to begin valid qualification under the frozen contract/environment, including constructor failure. Do not proceed to Transformers, Qwen, a new version, configuration, schema, or semantic suite after failure.

Capture post inventory and pip check. Preserve raw results, observations and append-only journal. All historical tracked state must remain unchanged. Final reporting and exact artifact-path Git attributes may be added after execution; execution helper, tests, config, fixtures and historical evidence must retain their pre-execution hashes. Python files remain normal text. No commit/tag. No DEVELOPMENT or either HELDOUT access. Fresh V2 semantic suite remains NOT YET AUTHORED.
