# Phase 2H-B3.2-A2.1 Attempt 2 completion report

Status: **CANDIDATE_AWAITING_OWNER_REVIEW**.
Outcome: **DECODER_QUALIFICATION_FAILED**. Structural acceptance: **0/3**.

All three calls finished with EOS and valid JSON. All three violate the exact V2
schema because they omit required top-level `decision`, `policy_context_status`
and `reason_code`. Adapter C independently rejects all three for invalid keys.
No repair, prompt/schema changes, retries or additional calls followed these results.
This is a structural failure report, not semantic answerability accuracy scoring.

## Execution configuration deviation (owner review required)

The final audit found `repetition_penalty=1.1`, inherited from the unchanged local
model `generation_config.json`, while the frozen runtime identity's complete
proposed generation configuration records `1.0`. The other config difference is
the explicitly authorized `max_new_tokens=512` (previously 4096).
The complete effective config was saved before S1. The suite/config and execution
source were frozen before model initialization, but the penalty discrepancy was
not caught by the pre-generation tests. This is one unauthorized scientific
configuration difference, not package drift. The actual files remain untouched.
No corrective run is authorized or performed. Do not describe this attempt as fully
conforming to the frozen runtime contract or as a qualified exact frozen candidate.

The three preserved outputs establish failure to enforce the exact schema in the
observed execution. They do not establish semantic accuracy, and this attempt does
not provide a fully protocol-conformant qualification of the requested runtime.

## Frozen base and custody (items 1-8)

HEAD/tag: `4fea18a9c70b1b9536dd92d7f1a118ac3e02a32f` /
`answerability-semantic-v2-deps-v0.2-imports-validated`; pre-run Git status clean.
Historical anchors resolved unchanged:

- `answerability-semantic-v2-deps-v0.1-enablement-failed`: `b5ac4a77447849d9fb5adc7427b69e4c3e14a52f`.
- `answerability-semantic-v2-decoder-v0.1-qualification-blocked`: `36ccd603bd0bfba6ba5359bc39d3e6f4225db184`.
- `answerability-semantic-gate-v0.2-pre-decoder`: `4c3d715ccf4f2026387ebf5599f36f7e234081f1`.

R2 owner status verified: OWNER_REVIEWED / DEPENDENCIES_ENABLED_AWAITING_DECODER_REQUALIFICATION.
The complete 33-package starting inventory exactly matches R2, including METADATA
and RECORD hashes. Python 3.12.10, torch 2.14.0+cpu, transformers 4.57.6,
huggingface_hub 0.36.2, tokenizers 0.22.2, safetensors 0.8.0, accelerate 1.15.0,
apache-tvm-ffi 0.1.14.post1, pydantic 2.13.5, pydantic-core 2.46.5,
annotated-types 0.8.0, typing-inspection 0.4.4, typing-extensions 4.16.0.
See PRE_INSTALL_PACKAGE_INVENTORY.json for all 33 identities.

The historical exact wheel was available in the ignored repository cache. Its
bytes were reused and copied to an external temporary directory before installation;
no download occurred. WHEEL_CUSTODY.json preserves both exact paths. Wheel:
`xgrammar-0.2.8-cp312-cp312-win_amd64.whl`; SHA-256:
`dbcf6718e049cbe429742cdb05f85c48135c2e389d45daeafb884af6994bb4a7`.
Installation used --no-deps --no-index --no-compile. The only added package is
xgrammar 0.2.8; 41 installed wheel payload files matched; METADATA/RECORD and
pip direct_url wheel identity were recorded. Existing package drift=0;
pre-install, post-install and final pip check all PASS. Final packages=34.

## API, tokenizer and schema (items 9-14)

Fresh-process import and all four required APIs PASS. Local frozen Qwen tokenizer
integration PASS, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`; model vocab
size 151936. Tokenizer vocabulary/config hashes are in TOKENIZER_INTEGRATION_RESULT.json.
All 10 model-file hashes matched before initialization.
Chat-template SHA: `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.
Exact schema SHA: `6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.
Original schema bytes were passed without rewriting. Compilation returned successfully,
and the native XGrammar HF LogitsProcessor was constructed and supplied to generate.
However, the native compiler warned that overlapping/non-provably-disjoint oneOf
branches fall back to anyOf semantics. Raw stderr is retained. Compilation success
is not equivalent to enforcement of the original schema. No custom fallback was used.

## Pre-generation freeze and tests (items 15-18)

Config SHA: `0bbedc2f2ad1165d04cb12f8a738378fcef466e5bf9d2013ee4ddded59bc6e61`.
Suite SHA: `43e241c3923d6d814bd1d8f29790a52bb690805fb3066b4f96b4d4e213718d2b`.
Both journal freezes precede model initialization. S1 single nonempty rank branch,
S2 multiple ask/rank fields, S3 empty rank branch; opaque interface symbols only,
no substantive policy scenarios or semantic Gold labels.
Greedy CPU FP32, beams=1, max_new_tokens=512, seed=0, per-call timeout=600 seconds,
quality/infrastructure retries=0; sampling controls recorded not applicable.
The runtime-penalty deviation is disclosed above.

Initial offline runner tests: 43/44 passed, one hash-check ordering error; corrected
before generation, without changing any frozen scientific input. Final pre-generation
suite: 114/114 PASS (44 new structural tests, 53 frozen V2 tests, 17 R2 tests).
Tests cover identity, drift rejection, schema bytes, fake compiler/API, no decoder
fallback/repair/retrieval, fixed case/call budget, immutability and raw serialization.
No target model was initialized by these tests.

## Calls and structural results (items 19-35)

Model initialized exactly once, Windows CPU FP32, unquantized. Three generate calls,
S1/S2/S3 exactly once; retries=0, timeouts=0, unauthorized calls=0. No fourth call.

| Case | Termination | A JSON | B exact schema | C adapter | Seconds | Output tokens |
| --- | --- | --- | --- | --- | ---: | ---: |
| S1 | EOS | PASS | FAIL | FAIL: invalid keys | 32.094 | 45 |
| S2 | EOS | PASS | FAIL | FAIL: invalid keys | 43.172 | 81 |
| S3 | EOS | PASS | FAIL | FAIL: invalid keys | 30.672 | 43 |

Structural acceptance=0/3; Markdown/prefix/suffix violations=0. Each raw record preserves
request/config hash, input/output token counts, token IDs, text, UTF-8 size/hash,
elapsed duration and termination. A/B/C results are linked by case ID in the results
artifact. Adapter failure is separately recorded, not substituted for schema failure.
No ALLOW/ABSTAIN/reason/support accuracy or other semantic score was calculated.

## Post-run verification and boundaries (items 36-45)

Saved raw records: exactly three, reparse and exact-schema validation reproduced all
results and the FAILED outcome. The independent validator implements all keywords
present in the hash-locked schema; a separate direct required-key audit confirms the
failures. It does not claim to implement every possible JSON Schema keyword.
Post-generation non-model tests: 114/114 PASS. Config/suite/source receipts unchanged;
final inventory exactly equals post-install inventory; final pip check PASS.
The effective-config comparison additionally identified the penalty deviation above.

This XGrammar implementation did not enforce the frozen structured interface in the
observed run. No conclusion about semantic answerability capability is made.
Fresh V2 semantic qualification suite remains NOT YET AUTHORED. DEVELOPMENT semantic
calls=0; retrieval calls=0. Phase 2H HELD_OUT access=false and Phase 2G private HELDOUT
access=false. No model files, alternate decoder or dependency downloads; XGrammar
was the sole installation. No post-result tuning or rerun occurred.

Python audit observations across pre-model probe and generation: socket.gethostname=2,
socket construction=2, IPv6 loopback bind [::1]:0=2, local cmd.exe /c ver probes=2.
No outbound DNS/connect operation was observed. Platform probes were allowed. This
is Python-level audit evidence, not an OS-wide packet-capture claim. All execution
was offline after reuse of the local wheel. Both observation artifacts are preserved.

Before .gitattributes administration, git diff HEAD was empty for tracked files.
R2, R1, Attempt 1, V2/V1, runtime, B3/B2, benchmarks, B1.1, retriever, policy corpus
and engine remain unchanged. V2 explicit hashes and parser receipt were reverified.
No benchmark question bodies were opened. Only new qualification source/tests,
Attempt-2 evidence and exact per-artifact .gitattributes rules are in the candidate.

## Integrity and Git review (items 46-49)

FINAL_SHA256.json lists every artifact hash except its own, plus all three new source/
test hashes and .gitattributes. Its own hash is reported separately; no circular hashes.
CHANGED_FILES.json records the complete candidate file list. Artifacts are force-added
only from this exact directory; wheel/venv/model cache/private material are excluded.
Final git status and staged-name verification are reported at completion.
No commit or tag. STOP for owner review; do not start fresh semantic qualification.
