# Attempt 2 qualification review record

Status: **OWNER_REVIEWED / QUALIFICATION_FAILED**
Owner: **Zhe Wang (Victor)**
Owner approval date: **2026-10-09**
Scientific owner review: **PASS — FAILED QUALIFICATION ACCEPTED**
Outcome: **QUALIFICATION_FAILED**
Candidate: **SEMANTIC_MATERIAL_SUPPORT_V1**
Model: `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
Runtime: owner-frozen CPU / FP32 / Transformers; no quantization.
Base: `a36fda5958492ca326f944642fe252b5d41442b7`. Historical preregistration, blocked Attempt 1 and BR unchanged.
This outcome concerns only the frozen synthetic suite; no DEVELOPMENT gate has run.
The candidate qualification failed under the frozen prompt/parser/runtime/configuration.
Binary correctness and reason-code correctness are formally 0/12 under the frozen
qualification scorer because no primary output produced a valid GateOutput.
These values must not be interpreted as twelve valid semantic decisions that were
all substantively incorrect. Semantic decision accuracy is not interpretable from
valid GateOutputs in this attempt.

| Frozen qualification metric | Unchanged result | Unchanged requirement |
| --- | --- | --- |
| Structured output validity | 7/12 | 12/12 |
| Supplied-section reference validity | 0/12 | 12/12 |
| Internal consistency | 7/12 | 12/12 |
| Binary correctness | 0/12 formal score | >=11/12 |
| Reason-code correctness | 0/12 formal score | >=11/12 |
| Critical binary correctness | 0/6 formal score | 6/6 |

These unchanged mandatory criteria require QUALIFICATION_FAILED.

Failure taxonomy remains:

- Q3, Q4, Q5, Q10, Q12: invalid strict JSON caused by prohibited Markdown code fencing.
- Q1, Q2, Q6, Q7, Q8, Q9, Q11: invalid/noncanonical supplied-section references.

All critical cases Q3, Q4, Q7, Q8, Q11 and Q12 failed to produce valid GateOutputs.
No qualification credit is assigned by reinterpreting raw semantic content.
No fences were stripped, references normalized or mapped, or saved outputs repaired.

For each of Q2, Q7 and Q11, primary and duplicate raw bytes are identical, and the
five raw semantic diagnostic fields are 5/5 identical: decision, reason_code,
policy_context_status, material-ask support-status pattern and supporting-section
identity values. All three pairs remain invalid under the frozen parser. The saved
determinism artifact therefore has no valid-GateOutput semantic comparison; raw-field
agreement does not override failure or add a retrospective eligibility criterion.

Historical Attempt-2 model initialization count=1; primary generate calls=12;
determinism duplicate calls=3; total generate calls=15. Timeouts=0;
infrastructure failures=0; quality retries=0; infrastructure retries=0.
Additional model initializations during owner finalization=0; additional generate calls=0.
DEVELOPMENT semantic calls=0; DEVELOPMENT eligibility metrics calculated=false;
retrieval calls=0. New network requests/downloads during finalization=0.
Phase 2H HELD_OUT accessed=false; Phase 2G private HELDOUT accessed=false.
No DEVELOPMENT question was opened for this finalization. No B3.2-C or revised
semantic candidate was begun.
Source SHA: `913f974c6b69df76fed217131d2238758d89597acfcb9aea1bf5058c88eba322`. Test source SHA: `31d4ef320f6c006ea0d0c32f7b55c4f32f912eac8aa15b8423c983fa5bbbe9fd`.

| Artifact | SHA-256 |
| --- | --- |
| QUALIFICATION_PROTOCOL.md | `e69cd231d63346c49bebef7077a8645b90af1cbec80f6ba040267988168f5075` |
| INFERENCE_CONFIG.json | `4eeb39c086b9f0e60f10fc0ea0d03eeb67b401b0e3876854b8cc138b0b910db9` |
| SYNTHETIC_QUALIFICATION_SUITE.json | `b320a1af101f07d11a9fd42254c6b0c680a9b95ebcdff80de735c89f79e2c508` |
| SYNTHETIC_QUALIFICATION_RESULTS.json | `c6c6db9f3b5c9287acbbba8951520cfb12b2e912222b7192f2b62b14772f1a21` |
| RAW_MODEL_OUTPUTS.jsonl | `e86228c5f6bb80e3dd9e1083a8242558970fbacb96b70435acdc2747fa1a4b0a` |
| DETERMINISM_REPORT.json | `540992230c2636ed1ddfc958dcbc90cf72c19332eacfe7a1075502ef79e3dc9d` |
| QUALIFICATION_JOURNAL.jsonl | `c8754c489aac3709345a3e88669e5926e3ad692cfe0c5bcb3d647954fb81dd19` |
| MODEL_QUALIFICATION_REPORT.md | `9441b2a82d1e49fb892d796a6419110f7dd6171e4f6e102ae8309450ab3d00ff` |

Only this administrative owner-review record changed during finalization. The eight
scientific artifact hashes above and the runner/test hashes remain unchanged. No
other Attempt-2 artifact contains this record's hash, so no dependent update is needed.
No self hash. Stop for final owner verification; do not commit, tag, begin B3.2-C
or begin a revised semantic candidate.
