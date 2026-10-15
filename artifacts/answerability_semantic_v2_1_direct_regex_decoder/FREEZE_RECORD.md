# Direct-regex enablement and structural qualification

Status: OWNER_REVIEWED / DIRECT_REGEX_CANDIDATE_FAILED
Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-14
Scientific review: PASS — FAILED RUN ACCEPTED WITH HARNESS ERROR ESTABLISHED
Formal outcome: DIRECT_REGEX_CANDIDATE_FAILED
Failure classification: FSM_ACCEPTANCE_HARNESS_EOS_SEMANTICS_ERROR
Positive-fixture error classification: HARNESS_POST_ACCEPTANCE_EOS_ADVANCE_ERROR (not FSM_REJECT)
Direct-regex semantic-language compatibility: SUPPORTED BY CURRENT EVIDENCE
Direct-regex FSM qualification: INCONCLUSIVE DUE TO HARNESS ERROR
Decoder qualification: NOT YET ESTABLISHED
The formal historical outcome remains DIRECT_REGEX_CANDIDATE_FAILED; the run is not relabeled qualified.

Base HEAD/tag answerability-semantic-v2_1-outlines-jsonschema-v0.1-selection-blocked = 1d14c85f15ed615ec224d7b07339bbceccbba2bb; entry working tree clean. The historical JSON Schema backend rejection remains unchanged and is distinct from this direct-regex path.

## Frozen derivation

Contract SHA: 768b9147e77f1dcc9dfd13b9dc4a6f9a2dad0ea6ad498219341fee0c43166198.
Original P2P3 derivation-rules SHA: ea6e491ba295328bae66651230da39c87159ee06cc3eb4b2d146bbe066cc029e.
Both remain unchanged. Accounting remains 64 material / 18 decoder / 46 validator-only / 0 unowned / 6 adapter responsibilities.

Regex identity: DECODER_ENFORCEMENT_REGEX_V2_1_V0_1.
Regex SHA: 3ec42de4a205e599789575954494ad2004beedcc49e2ed550ef865b591dc1482.
New derivation-rules SHA: 013d980ebb25e5c6104ac3e75ca790c7eda408528247fbeb71d35ee2d79f8796.
The rules preceded derivation; regex, trace, fixtures and helper/test hashes were frozen before installation or runtime outcomes. V_contract subset V_regex follows by structural induction, preserving all string values with ordinary Unicode, short escapes and uXXXX escapes. Lexical property ordering and canonical integer/key/enum spelling are serialization-only. No delegated validator condition was added.

An early tool-output escaping interpretation was mistaken; literal byte inspection confirmed the frozen fragments were correct. No blocked outcome was written and no rule bytes changed. The correction is preserved in REGEX_FREEZE_RECEIPT.json.

## Installation and execution

Exact candidate: outlines==1.3.3 + outlines_core==0.2.14. A dry-run resolver with every existing package constrained selected 28 additions, including the Transformers extra. Exact versions/wheel URLs/SHA-256 and the full report are in DEPENDENCY_LOCK.json. All 28 local wheels were verified, then installed once using --no-deps --no-index. No resolver-driven mutation occurred.

Existing 36 packages: zero version/removal/raw METADATA/RECORD drift. Post-install total: 64 packages. Pip check passed before and after installation; post-execution raw inventory still equals the post-install inventory. The historical inventory used normalized text hashes; matching that original method confirms 36/36 identities unchanged. Raw-byte hashes are used for this phase's pre/post comparison.

Import/API validation passed for Transformers integration, OutlinesCoreBackend.get_regex_logits_processor, OutlinesCoreLogitsProcessor, Vocabulary, Index and Guide. Tokenizer loaded exactly once from the frozen local Qwen/Qwen2.5-1.5B-Instruct revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306, offline; five tokenizer/config file hashes verified. The official vocabulary factory and direct-regex processor were constructed without a Transformers model wrapper. No Qwen weights were opened; no model initialized, forwarded or generated.

## Owner-established EOS acceptance semantics

Scientific owner review establishes the following implementation semantics for outlines_core==0.2.14. A valid completed sequence is represented by:

```python
guide.is_finished() == True
guide.get_tokens() == [eos_token_id]
```

Calling guide.advance(eos_token_id) after reaching a finished state is NOT the acceptance operation. The official outlines-core 0.2.14 implementation/test suite expects that call to raise ValueError because no further state transition exists. This implementation/test-suite finding is recorded from the owner's scientific review; no source research, import, tokenizer reload or FSM verification was performed during finalization.

Owner-reviewed accounting:

- textual regex qualification = 64/64 PASS
- expected-accept FSM fixtures = 34
- reached final state = 34/34
- EOS sole allowed token = 34/34
- post-final advance(EOS) errors = 34/34
- expected-reject FSM fixtures = 30
- correctly rejected = 30/30

Provenance distinction: the saved runner directly recorded final_state=true and EOS membership as ALLOWED for all 34 positive fixtures; it did not save the complete allowed-token list. The sole-token interpretation above is the owner-established implementation semantics and review finding, not a newly executed measurement. The original raw result records remain byte-identical.

M1 textual = PASS; M1 reached FSM final state = true; M1 EOS allowed = true; M1 historical run disposition = ERROR due to invalid post-final advance(EOS). M2-M8 historical FSM results remain correct REJECT.

U+0000 retains JSON parse PASS, Decoder Enforcement Contract PASS and regex textual language ACCEPT. The FSM reached a valid terminal state and exposed EOS as allowed termination; the historical harness then incorrectly advanced EOS. These errors do not demonstrate a semantic-language inability to represent the frozen contract.

## Results and their limits

Offline freeze/coverage checks: 3/3 PASS. Independent textual checks: 64/64 expected results, zero errors, false accepts or false rejects. M1 ACCEPT; M2-M8 REJECT, preserving historical raw bytes. All 18 decoder rules received positive/violating probes; properties/items association operators were exercised jointly with their child predicates.

Actual FSM fixtures: 64, each once. 30 expected rejects succeeded. All 34 expected accepts completed traversal, reached a final state and reported EOS allowed. The runner then explicitly called advance(EOS), which raised ValueError for token 151645 at state 46336. These are preserved as 34 ERROR results, not REJECT and not retroactively repaired PASS. Historical fully qualified rule count remains 0/18 because the recorded qualification attempt contains harness errors; empirically exercised rules = 18/18. This is not a finding that the 18 semantic constraints failed. Decoder qualification is NOT YET ESTABLISHED. Classified false accepts = 0; classified false rejects = 0; those counts do not erase the errors. Core M1 = ERROR, M2-M8 = expected REJECT.

U+0000: JSON parse PASS, neutral contract PASS, textual regex ACCEPT; actual token traversal complete, final state true, EOS allowed, followed by the same explicit EOS-advance ERROR. Thus the prior textual Unicode restriction is absent, but complete FSM qualification is not claimed.

The EOS advancement step was in this phase's runner. The inspected release wrapper already contains a final-state/accepts_tokens guard around advance (its source references issue 227); the model-free runner instead advanced EOS unconditionally after observing terminal acceptance. This distinction prevents attributing the failed attempt to an inability of the regex to express the contract. No corrective execution, new diagnostic run or relabeling occurred. Raw results, runner source and runner SHA are retained in STRUCTURAL_RESULTS.json.

Validator-only examples were textually accepted as permitted. DELEGATED_UNIQUE covers duplicate ranks; DELEGATED_CONDITIONAL covers delegated decision/reason/support consistency. The fixture named DELEGATED_CONTAINS actually tests delegated supported-rank minItems, not an isolated contains condition; its original identifier/bytes are preserved and no contains-specific success is claimed. Exact validator remains NOT_YET_SELECTED_NOT_QUALIFIED. No combined two-layer qualification.

## Counters and quarantine

Package additions = 28; total mutations including additions = 28; existing-package mutations/removals = 0. Decoder root import attempts = 4 across two processes (outlines 2, outlines_core 2). Scientific regex compilations = 2 (Python textual engine 1; core Index 1). JSON Schema compiler calls = 0. Logits processor constructions = 1. Tokenizer loads = 1. FSM fixture executions = 64. Fixture retries = 0.

Model initialization = 0; forward = 0; generate = 0; DEVELOPMENT = 0; retrieval = 0. Phase 2H HELD_OUT access = false; Phase 2G private HELDOUT access = false. Fresh V2.1 semantic suite = NOT YET AUTHORED. Dependency resolution/wheel-download networking was authorized; runtime external network access was blocked, and socket capability probes are recorded. No post-result tuning, repair or rerun.

276 named historical hashes verified unchanged. All prior tracked sources, artifacts, benchmark and corpus paths remain untouched; no benchmark/private question contents were opened. Only 13 requested artifacts, one helper, one test and exact .gitattributes entries form this candidate. Wheel/cache contents remain ignored and unstaged.

## Owner finalization scope and hash provenance

Only this administrative freeze record changed. Owner finalization verified all 64 installed package identities and raw METADATA/RECORD hashes against the post-install receipt; all 28 authorized additions and their dependency-lock identities are unchanged. No reinstall, uninstall or package mutation occurred. Frozen contract, regex, derivation rules, fixtures, helper/tests, raw structural/Unicode results and historical outcomes remain byte-identical.

Counters during owner finalization: package mutation = 0; regex derivation = 0; FSM executions = 0; tokenizer loads = 0; model initialization = 0; generate = 0; forward = 0; DEVELOPMENT = 0; retrieval = 0; both Phase 2H HELD_OUT and Phase 2G private HELDOUT access = false. Fresh V2.1 semantic suite = NOT YET AUTHORED. No recovery was begun.

FINAL_SHA256.json remains unchanged at SHA-256 9ae565c02697e5abbf72f842a1001898f2109939bed66110694a09f405682692. Its FREEZE_RECORD.md hash d5b6892310406603f6c2a14c5685dfec57864e92c46925032df6b6c5c0e7956b identifies the superseded pre-owner administrative record. All other receipt entries remain current. The finalized administrative record hash is reported externally; no circular self-hash or receipt rewrite is introduced.

Owner finalization complete. No commit or tag. The historical run remains failed, and no recovery or new phase is authorized by this administrative update.

## Preserved pre-owner Git review

`git status --short`:

```text
M  .gitattributes
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/DECODER_ENFORCEMENT_REGEX.txt
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/DEPENDENCY_LOCK.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/DIRECT_REGEX_PROTOCOL.md
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/ENVIRONMENT_RECEIPT.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/FINAL_SHA256.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/FREEZE_RECORD.md
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/OUTCOME.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/REGEX_DERIVATION_RULES.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/REGEX_FREEZE_RECEIPT.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/REGEX_PROVENANCE_TRACE.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/STRUCTURAL_FIXTURES.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/STRUCTURAL_RESULTS.json
A  artifacts/answerability_semantic_v2_1_direct_regex_decoder/UNICODE_REGRESSION_RESULT.json
A  gateway/domain/evaluation/answerability/direct_regex_qualification.py
A  gateway/domain/tests/test_direct_regex_qualification.py
```

`git diff --cached --name-only`:

```text
.gitattributes
artifacts/answerability_semantic_v2_1_direct_regex_decoder/DECODER_ENFORCEMENT_REGEX.txt
artifacts/answerability_semantic_v2_1_direct_regex_decoder/DEPENDENCY_LOCK.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/DIRECT_REGEX_PROTOCOL.md
artifacts/answerability_semantic_v2_1_direct_regex_decoder/ENVIRONMENT_RECEIPT.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/FINAL_SHA256.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/FREEZE_RECORD.md
artifacts/answerability_semantic_v2_1_direct_regex_decoder/OUTCOME.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/REGEX_DERIVATION_RULES.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/REGEX_FREEZE_RECEIPT.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/REGEX_PROVENANCE_TRACE.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/STRUCTURAL_FIXTURES.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/STRUCTURAL_RESULTS.json
artifacts/answerability_semantic_v2_1_direct_regex_decoder/UNICODE_REGRESSION_RESULT.json
gateway/domain/evaluation/answerability/direct_regex_qualification.py
gateway/domain/tests/test_direct_regex_qualification.py
```

All 15 byte-bound artifact/source staged blobs match worktree bytes; all 15 exact rules resolve to text: unset. Git diff --cached --check passed. No unstaged/untracked files or staged cache/weights/private data. This review listing covers 13 artifacts, one helper, one test and .gitattributes.
