# Phase 2H-B3.2-A2.1-D completion report

Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**.
Primary localization: **GRAMMAR_COMPILATION_OR_REQUIRED_FIELD_ENFORCEMENT_ISSUE**.
Evidence confidence: **ESTABLISHED**.
Specific classification: **GRAMMAR_REQUIRED_FIELD_ENFORCEMENT_FAILURE**.

With the exact frozen schema and Attempt-2 compilation parameters, the pure native
matcher accepted a material_asks-only object and all three saved Attempt-2 raw outputs,
including their EOS termination. These objects fail the original schema's required-key
constraints. The complete valid M1 object was instead rejected. This reproduces a
constraint-enforcement defect without a model or logits-processing invocation.

Scope is this exact schema/options/installed-library combination. This does not claim
that XGrammar cannot enforce every V2 representation or every possible schema. No
option variation, schema rewrite, decoder change or fix was attempted.

## Base and preserved history (items 1-4)

Base HEAD/tag: `e085c96e5c80ce61bb833be78f36c62ee8ee5790` /
`answerability-semantic-v2-decoder-v0.2-qualification-failed-nonconforming`.
Initial worktree clean. Historical R2 tag remains
`answerability-semantic-v2-deps-v0.2-imports-validated` ->
`4fea18a9c70b1b9536dd92d7f1a118ac3e02a32f`.

All 41 Attempt-2 artifacts retain their bytes, including the owner-reviewed record.
Attempt 2 remains OWNER_REVIEWED / DECODER_QUALIFICATION_FAILED,
NONCONFORMING_CONFIG, clean capability judgment NOT_CONCLUSIVE. Its frozen penalty
was 1.0 and executed penalty 1.1. The new diagnostic does not rewrite that history or
retroactively convert it into a clean frozen-config generation run.

Installed XGrammar = **0.2.8**, Transformers = **4.57.6**. The complete 34-package
inventory matches the frozen post-Attempt-2 state before and after this diagnostic.
Installed XGrammar hashed payloads and the inspected Transformers generation sources
also match their RECORD identities. No packages were installed or changed.

Exact schema SHA:
`6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.
All three required Attempt-2 execution-source hashes matched before and after.

## Required fields and actual compilation arguments (items 5-7)

Root type = object. Root additionalProperties = false.
Properties = decision, material_asks, policy_context_status, reason_code.
Required list, in its original order:
material_asks, policy_context_status, decision, reason_code

Attempt-2 compile_exact checks the schema SHA, decodes UTF-8, constructs
GrammarCompiler(tokenizer_info), and passes that exact text as the single positional
schema argument to compile_json_schema. There are no keyword overrides. The actual
installed method definitions, hash-verified call AST and diagnostic runtime signature
binding establish the following values; they are not guesses from generic defaults:

| Argument | Effective value |
| --- | --- |
| schema | Exact frozen schema text, unmodified |
| any_whitespace | true |
| indent | null |
| separators | null |
| strict_mode | true |
| max_whitespace_cnt | null |
| any_order | **false** |

Compiler constructor: max_threads=8, cache_enabled=true, cache_limit_bytes=-1.
TokenizerInfo.from_huggingface receives the frozen local Qwen2TokenizerFast and
vocab_size=151936. Snapshot revision:
`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
Tokenizer/config and vocabulary hashes match Attempt 2. Only tokenizer files were
loaded; no Qwen weights were opened and no model was constructed.

Native compilation count=1. Compiler warning: overlapping/non-provably-disjoint
oneOf branches fall back to anyOf semantics. The warning alone is not a proven
root-cause diagnosis. The emitted grammar and its hash are preserved in
COMPILED_GRAMMAR.ebnf and GRAMMAR_COMPILATION_RECEIPT.json.

## Frozen matcher fixtures and results (items 8-16)

M1-M8 strings and expected structural outcomes were frozen before native execution.
M1-M5 were tokenized without special tokens. M6-M8 replay the exact saved generated
token IDs, separating the last EOS from the body; decoded body bytes must equal the
saved text. Each fixture has one fresh default matcher, one forward pass through
its body tokens, and one EOS check if all body tokens are accepted. No retry/reset.
Acceptance requires body completion, accepted stop token and terminated state.

| Fixture | Expected | Actual | Body complete | EOS accepted | First rejected token index (0-based) |
| --- | --- | --- | --- | --- | --- |
| M1_VALID_COMPLETE | ACCEPT | REJECT | False | None | 9 |
| M2_MISSING_DECISION | REJECT | REJECT | False | None | 26 |
| M3_MISSING_POLICY_CONTEXT | REJECT | REJECT | False | None | 9 |
| M4_MISSING_REASON | REJECT | REJECT | False | None | 9 |
| M5_MISSING_ALL_THREE | REJECT | ACCEPT | True | True | None |
| M6_ATTEMPT2_S1_RAW | REJECT | ACCEPT | True | True | None |
| M7_ATTEMPT2_S2_RAW | REJECT | ACCEPT | True | True | None |
| M8_ATTEMPT2_S3_RAW | REJECT | ACCEPT | True | True | None |

M2-M4 rejection does not by itself prove the missing-field rule was enforced: valid
M1 was also rejected. M5 and the saved raw outputs are decisive counterexamples to
required-field enforcement because they are fully accepted and terminated despite
missing the required root keys.

| Saved output | Standard JSON parser | Exact original schema validator | Pure XGrammar matcher |
| --- | --- | --- | --- |
| S1 | PASS | FAIL | ACCEPT |
| S2 | PASS | FAIL | ACCEPT |
| S3 | PASS | FAIL | ACCEPT |

The independent validator implements every keyword used in the hash-locked original
schema; unsupported keywords fail the guard. It is the preserved Attempt-2 validator,
not a decoder-derived schema or repair operation. No general-purpose JSON Schema
library conformance claim is made. Direct root required-key comparison independently
confirms the three omissions: decision, policy_context_status, reason_code.

## Call path and processor lifecycle (items 17-19)

For S1, S2 and S3, the hash-verified worker passes
`logits_processor=[LogitsProcessor(grammar)]` directly to model.generate.
Caller container = builtins.list; custom processor count = 1; class =
xgrammar.contrib.hf.LogitsProcessor. The constructor runs inside the per-case worker,
so each generation gets a new stateful processor. The compiled grammar is shared;
processor/matcher state is not intentionally reused. Numeric object IDs were not
recorded and cannot be reconstructed. No saved per-token mask/callback telemetry
establishes historical runtime masking correctness.

| Edge | Classification | Evidence |
| --- | --- | --- |
| frozen schema -> compiler | VERIFIED | Frozen source/hash checks and exact original schema argument |
| compiler -> compiled grammar | VERIFIED | Saved completed step and current exact-options native compilation |
| compiled grammar -> native HF processor | VERIFIED | Frozen constructor path and saved integration artifact |
| processor -> generate argument | VERIFIED | Explicit one-element list in the executed worker source |
| prepared processor -> historical per-token masking | NOT_VERIFIED | No saved per-token callback/mask trace |

The local XGrammar HF documentation requires a new processor for each generate call.
The Attempt-2 source follows that lifecycle. Each new object starts with empty matchers,
no token bitmask, prefilled=false, batch_size=0, and lazily initializes its matcher(s).
No explicit reset was needed on this fresh-instance path. GrammarMatcher has reset(),
but the HF wrapper has additional state and no exposed reset method; a matcher-only
reset is not a documented substitute for new wrapper construction. No concrete
PROCESSOR_STATE_LIFECYCLE_MISMATCH was established. No reset was added or executed.

Transformers keeps the supplied non-None custom list, then merges it into a new
LogitsProcessorList by object reference. Matching default processor types may be
replaced by custom ones; XGrammar and repetition penalty are distinct types. No
clearing, dropping or deep-copying path was found for XGrammar under the saved config.
The source dispatches the prepared list into the generation loop and applies it before
selection. This static source evidence is not an instrumented historical runtime trace.

## Termination and repetition penalty (items 20-21)

Saved max_new_tokens=512; configured EOS IDs=[151645,151643]. All three outputs ended
with token 151645 while the required root fields were missing:

| Case | Generated tokens | Termination | Last token | Below 512 |
| --- | ---: | --- | ---: | --- |
| S1 | 45 | EOS | 151645 | True |
| S2 | 81 | EOS | 151645 | True |
| S3 | 43 | EOS | 151645 | True |

Transformers adds RepetitionPenaltyLogitsProcessor to the default list before merging
the custom XGrammar processor. LogitsProcessorList applies processors in order. With
do_sample=false, watermarking_config=null and renormalize_logits=false, no corresponding
later transformation overwrites the mask. Thus penalty=1.1 acts before XGrammar, not
after its mask, and cannot resurrect tokens from a later-applied grammar mask. A
positive finite multiply/divide also preserves negative infinity. This is source-level
ordering analysis, not a saved-mask observation.

**CONFIG DEVIATION CONFIRMED; CAUSAL ROLE NOT ESTABLISHED.**
The matcher counterexamples require no repetition-penalty processor or model at all.
This localizes the grammar issue independently; it does not claim which process
caused the model to select these exact saved strings or prove runtime masking correct.

## Localization and confidence (items 22-24)

Exactly one primary outcome:
**GRAMMAR_COMPILATION_OR_REQUIRED_FIELD_ENFORCEMENT_ISSUE**.

- ESTABLISHED: this compiled grammar accepts M5 and M6-M8 without required fields.
- ESTABLISHED: this compiled grammar rejects complete, schema-valid M1.
- ESTABLISHED: emitted grammar has root -> root_case_2 -> root_case_2_case_1,
  where a material_asks-only object can close and its value is generic JSON.
  That branch does not require the other three root keys.
- SUPPORTED_BUT_NOT_PROVEN: compilation of composition branches appears not to retain
  enclosing constraint intersections. Exact native converter implementation cause
  has not been independently traced. The warning alone is not sufficient proof.
- No concrete HF-list application defect or processor-state lifecycle defect was
  established. Historical per-token masking remains unverified.

Any separately authorized recovery must establish complete original-schema conformance,
including required fields and valid complete objects, before generation. This phase
establishes a defect to address, not a particular parameter/schema/library fix.
No options were varied; no repair, new structural smoke or Attempt 3 was performed.

## Counters, tests and integrity (items 25-31)

Qwen model initialization=0; generate=0; forward=0; semantic outputs=0.
DEVELOPMENT semantic calls=0; retrieval=0. Phase 2H HELD_OUT access=false;
Phase 2G private HELDOUT access=false. Fresh semantic suite=NOT YET AUTHORED.
Packages installed/changed=0; model downloads/network access=0. One local tokenizer
load, one compilation and exactly eight native matcher fixtures; retries=0.
Python audit/profile observed no model/benchmark access or external DNS/connect.
Observed local probes: socket.gethostname, socket construction, IPv6 loopback bind
[::1]:0 and cmd.exe /c ver. These are not remote access. This is Python audit evidence,
not an OS-wide packet capture.

Pre/post diagnostic deterministic tests: **17/17 PASS** each. Native matcher/model calls
inside tests=0. An initial test-only guard incorrectly classified string.replace as
Path.replace; its initial 16/17 result and correction are preserved. Neither the
frozen inputs nor diagnostic execution behavior changed, and native execution had
not started. The native matcher experiment was run only once. Post-checks use saved
results, hashes and fake matcher tests, not a second native run.

Attempt-2 artifacts, source/test hashes, schema, frozen fixtures, package inventory
and all inspected installed payload identities remain unchanged. Before adding new
.gitattributes rules, tracked git diff HEAD was empty. All historical R2/R1/Attempt1,
V2/V1/runtime/B3/B2/benchmark/retriever/corpus/engine artifacts and sources remain
unchanged. No benchmark question contents were inspected.

## Final hashes and Git scope (items 32-35)

FINAL_SHA256.json contains all diagnostic artifact and helper/test hashes except its
own; its receipt hash is reported separately, avoiding circular hashes. Complete
changed paths are in CHANGED_FILES.json. New .gitattributes rules are exact per-artifact
-text entries; Python files retain normal text handling. No venv, cache, model weights
or private files belong to the staged candidate. No commit or tag. STOP for owner review.
