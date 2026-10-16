# Exact Validator and Combined Two-Layer Structural Qualification

Status: OWNER_REVIEWED / EXACT_VALIDATOR_AND_COMBINED_STRUCTURE_QUALIFIED
Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-15
Scientific review: PASS — COMPLETE STRUCTURAL PIPELINE QUALIFIED
Final outcome: EXACT_VALIDATOR_AND_COMBINED_STRUCTURE_QUALIFIED
Recorded UTC: 2026-10-16T03:02:18.686131+00:00

## Frozen base and schema

Base commit: b3bb919e3d38ab733f775413c08fd3ecb7da08f2
Base tag: answerability-semantic-v2_1-direct-regex-v0.4-qualified
Entry Git status: clean, verified before helper creation.
Decoder owner status: OWNER_REVIEWED / DIRECT_REGEX_V0_1_DECODER_QUALIFIED.
Decoder implementation: DECODER_ENFORCEMENT_REGEX_V2_1_V0_1.
Contract SHA-256: 768b9147e77f1dcc9dfd13b9dc4a6f9a2dad0ea6ad498219341fee0c43166198
Direct-regex V0.1 SHA-256: 3ec42de4a205e599789575954494ad2004beedcc49e2ed550ef865b591dc1482
Authoritative raw schema SHA-256: 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e
No schema normalization, substitute schema, regex change, V0.2, or further decoder research.
All 43 frozen input/source identities remain unchanged, including previous failed/inconclusive checkpoints and qualified decoder evidence.

## Exact validator identity and configuration

Sole family: python-jsonschema, installed package jsonschema==4.26.0.
Declared draft: https://json-schema.org/draft/2020-12/schema.
Resolved exact class: jsonschema.validators.Draft202012Validator.
referencing==0.37.0; jsonschema-specifications==2025.9.1; attrs==26.1.0; rpds-py==2026.9.1.
Installed package versions and raw METADATA/RECORD hashes were frozen before schema checking. No installation or mutation was required.
Schema self-validation: SCHEMA_CHECK_PASS, using the applicable class.check_schema mechanism before fixture qualification.
Class resolution: validator_for(schema, default=None), explicitly verified to be Draft202012Validator. No silent draft fallback, custom type checker, keyword replacement, or validator subclass.
Format checker: None, explicitly frozen; authoritative schema contains no format assertion.
Reference resolution: referencing Registry with external retrieval denied; no $ref occurs in the authoritative schema. Applicable bundled meta-schema validation succeeded locally. No substitute reference fixture/schema is used to claim absent-keyword coverage.

Parser: standard json.loads on original UTF-8 bytes, with duplicate-key and nonfinite-constant rejection; legal leading/trailing JSON whitespace is accepted. Raw evidence is preserved before parsing and passed unchanged to the adapter. No strip/rewrite/default/coercion/deduplication repair.

Package identity frozen UTC: 2026-10-15T20:43:19.806485+00:00
Validator/config/fixtures/coverage plan frozen UTC: 2026-10-15T20:43:21.155495+00:00
Result-bearing execution started UTC: 2026-10-15T20:43:51.794877+00:00
Execution finished UTC: 2026-10-15T20:44:02.620749+00:00
Identity SHA-256: 2f0ceabed7defa77b4d147cbbe07e422761e19fbadcd1fb1b0ffdba29d2f69aa
Helper SHA-256: a8c8d0c7727630eba4d2d0eb0161656010e7cfb69f3e3d84f003573b129f1ea3
Fixture SHA-256: 1be0d730372498f3bf080047b472911689593ee32bd31bf49a664b7f2bf45402
Frozen coverage-plan SHA-256: b6e0ed407ff607ee2534a01059d9a9c9a8a9303c41d5445c6aa3114f04e14d7b
The final coverage matrix adds only empirical observations to that frozen plan; reconstructing the plan reproduces its original hash.

## Validator qualification and coverage

Validator-only probes: 58/58 expected outcomes; 9 ACCEPT, 49 REJECT, 0 ERROR. All JSON parse stages PASS.
Positive raw-schema-valid branches include M1, resolved insufficient support, unresolved context, unresolved material ask, array/rank upper boundaries, U+0000, and legal document whitespace. Two raw-schema-valid adapter-negative fixtures are also accepted by the exact validator as expected.

Frozen P1 accounting: material constraints 64; decoder + validator 18; validator-only 46; validator total 64; unowned 0; separate adapter responsibilities 6.
Material constraint pointers covered by actual original-validator dispatch: 64/64; uncovered 0. Every row has a preregistered witness that actually executed at that pointer and produced its expected verdict.
Present material keyword classes (21): additionalProperties, allOf, anyOf, const, contains, else, enum, if, items, maxItems, maximum, minItems, minLength, minimum, oneOf, pattern, properties, required, then, type, uniqueItems.
Inspected absent keywords: $ref, exclusiveMaximum, exclusiveMinimum, maxContains, maxLength, minContains, prefixItems. Their absence is not presented as empirical qualification of those features.

Read-only Python profiling records the actual stock validator keyword function dispatch and original schema-node identity; no validation implementation was patched. then/else are witnessed through actual selected-branch descendant execution. Full nested error schema paths are saved. A branch/container/combinator observation is interaction-aware; this report does not manufacture isolated causality for every row.

Advanced result-bearing evidence:

| Class | Saved probe evidence | Outcome |
| --- | --- | --- |
| uniqueItems | DELEGATED_UNIQUE | Exact uniqueItems rejection |
| contains | INSUFFICIENT_MISSING_TARGET and UNRESOLVED_MISSING_TARGET | Nested contains rejections at both actual schema branches |
| if / then / else / allOf | THEN_EMPTY, ELSE_NONEMPTY, positive supported/unsupported cases | then minItems and else maxItems rejections; both positive branches accepted |
| oneOf / anyOf / const / enum | Branch-specific decision/reason/context/status mutations and positive branches | Expected whole-schema outcomes with nested interaction errors |
| Array bounds | ASKS_EMPTY, ASKS_NINE, RANKS_ELEVEN, POS_BOUNDS | minItems/maxItems rejections and valid upper-bound acceptance |
| Numeric bounds | RANK_ZERO, RANK_ELEVEN | minimum/maximum rejections |
| String bounds/pattern | ASK_EMPTY, ASK_WHITESPACE | minLength/pattern rejections |
| Type/required/properties/items/additionalProperties | Frozen R01–R18 negatives, M2–M8 and positive objects | Expected exact rejection/acceptance; pointer-level dispatch recorded |

The inherited DELEGATED_CONTAINS fixture name is preserved, but its actual then/minItems failure is not misreported as contains coverage. Dedicated missing-target probes supply the actual contains evidence. Frozen delegated fixtures are not repaired.

## Combined structural pipeline

Exactly: preserved raw bytes -> qualified frozen V0.1 decoder FSM -> strict standard JSON parse -> same exact raw-schema validator -> unchanged deterministic V2 canonicalize/adapter -> existing GateOutput.
Validator-only and combined passes are explicitly separate authorized tests, not retries.
Combined probes: 40/40 expected outcomes; 0 ERROR.

| Required path | Count | Evidence |
| --- | ---: | --- |
| A: DECODER_STRUCTURAL_REJECT | 7 | Frozen M2–M8; JSON, exact validator and adapter NOT_RUN |
| B: COMBINED_STRUCTURAL_ACCEPT | 7 | M1 and six positive variants including U+0000 and legal whitespace |
| C: EXACT_SCHEMA_REJECT | 24 | Decoder ACCEPT + JSON PASS + exact REJECT; adapter NOT_RUN |
| D: ADAPTER_STRUCTURAL_REJECT | 2 | Raw-schema-valid absent actual rank and unsorted ranks |

Exact-validator failures retain STRUCTURAL_INVALID with repair 0, generation retry 0, adapter NOT_RUN, semantic evaluation NOT_RUN. Unexpected errors are represented separately and never counted as valid rejection; none occurred. JSON_PARSE_FAILED remains distinct in the pipeline; no separate claim of empirical JSON_PARSE_FAILED path qualification is made because the four required paths are A–D.

Adapter unchanged SHA-256: a83ebe3b6841e5cd810633c68ba4efc76ed8d6daeee1cbb62899e317133e9219.
Its six responsibilities are retained: actual supplied-rank membership; exact integer-token semantics; unique strictly ascending ranks; exact rank-to-canonical evidence mapping; cross-field/status-reference consistency; existing GateOutput mapping. Successful synthetic bindings were checked against the exact supplied evidence identities and unchanged decision/reason values. ADAPTER_ABSENT_RANK was rejected for a rank absent from supplied GateInput; ADAPTER_UNSORTED was rejected for order. These are structural interface checks, not semantic model judgments.

Decoder integration reused the existing whitespace closure proof. One identical frozen tokenizer/regex Index was constructed; the two proof states' allowed IDs and destinations matched saved proof data. No new root/closure search, decoder modification, alternative decoder, or sole-EOS requirement. Original raw whitespace bytes remained intact through parse/adapter. advance(EOS) calls 0.

## Environment and quarantine

Pre/post inventory: 64 packages, byte-identical versions/METADATA/RECORD. Package additions 0; removals 0; existing version/file drift 0; package mutation 0; pip check pre/post PASS.
Tokenizer loads 1; Index constructions 1. Validator-only attempts 58; combined attempts 40; repair 0; retry 0.
Qwen model initialization 0; generate 0; forward 0; DEVELOPMENT 0; retrieval 0.
Phase 2H HELD_OUT access false; Phase 2G private HELDOUT access false.
Fresh V2.1 semantic suite: NOT YET AUTHORED.
Runtime socket observations: construction, loopback IPv6 bind (::1,0), gethostname; no outbound connect/download recorded. No Qwen smoke or semantic provider call.

## Artifact and Git scope

Exactly nine authorized artifacts and one new helper; no separate test source, extra administrative files, .gitattributes modification, source/benchmark/retriever changes, commit, or tag. The validation and combined probes are the focused qualification tests; no rerun occurred during final reporting.
FINAL_SHA256.json covers the other eight artifacts and the helper, excluding itself to avoid circularity.

Git status --short:
```text
?? gateway/domain/evaluation/answerability/qualify_exact_validator.py
```
Git diff --name-only: empty.
Git diff --cached --name-only: empty.
New artifacts remain ignored and unstaged.

Owner administrative review is finalized. All qualification evidence and scientific conclusions above are accepted unchanged. Only the owner-review fields in this record and its dependent FINAL_SHA256.json changed. The manifest is regenerated deterministically (sorted keys, two-space indentation, final LF), with only this record's digest updated and no circular self-hash.

Owner finalization performed saved-evidence and hash verification only: validator probes 0; combined probes 0; decoder qualification reruns 0; tokenizer/Index loads 0; package mutation 0; structural repair 0; generation retry 0; model initialization 0; generate 0; forward 0; DEVELOPMENT 0; retrieval 0; both HELD_OUT access flags false. Recorded pre/post pip-check PASS and historical execution counts remain unchanged; no tests or pip check were rerun. Schema bytes, decoder, adapter, all scientific artifacts and historical identities remain unchanged. No Qwen smoke, fresh semantic suite, subsequent phase, commit, or tag. Stop after owner finalization.
