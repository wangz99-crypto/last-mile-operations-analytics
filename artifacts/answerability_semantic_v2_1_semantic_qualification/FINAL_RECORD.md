# Phase 2H V2.1 Fresh Semantic Qualification — Final Record

Status: `OWNER_REVIEWED / SEMANTIC_V2_1_QUALIFICATION_FAILED`
Formal outcome: `SEMANTIC_V2_1_QUALIFICATION_FAILED`
Candidate: `SEMANTIC_MATERIAL_SUPPORT_V2_1`
Completion record date: 2026-10-17.
Owner: `Zhe Wang (Victor)`
Owner approval date: `2026-10-17`
Scientific review: `PASS — CANDIDATE FAILED PRE-REGISTERED SEMANTIC QUALIFICATION`
Final candidate disposition: `QWEN2_5_1P5B_V2_1_SEMANTIC_CANDIDATE_REJECTED`
Reason: `FAILED_PRE_REGISTERED_SEMANTIC_QUALIFICATION`
DEVELOPMENT evaluation: `NOT_AUTHORIZED`.

## Base, authoring and freeze

Base commit: `8af43e5853f006d412823b7fc780bf5a2e43e92e`. Tag: `answerability-semantic-v2_1-qwen-smoke-v0.2-recovery-pass`. Entry Git status was clean; both identities remain unchanged.
The decoder, exact-validator/combined-structure, and Qwen eager-recovery checkpoints were owner-reviewed before this phase. Their historical evidence and frozen source identities remain unchanged.
Exactly 12 fresh cases: four supported, four insufficient-support, four unresolved-context; six single-ask and six two-ask cases, with 18 Gold asks including eight supported asks. Each GateInput contains ten directly constructed public-policy sections; no retrieval occurred.
Authoring used the active frozen public policy bundle, GateInput and semantic definitions. No prior qualification/smoke fixture files or model outputs were read during authoring. Prior conversation smoke text was present in historical context, as disclosed before freezing, and was not used for case construction.
Suite froze at `2026-10-16T19:19:20.470397+00:00` with `FRESH_V2_1_SEMANTIC_SUITE_FROZEN`, before model initialization. Post-freeze freshness audit compared 12 cases with 12 V1 and three smoke cases (180 pairs): exact duplicates 0, one-to-one paraphrases 0.

## Runtime and attempt accounting

Model `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`; CPU, FP32, local ten-file snapshot verified. Chat-template SHA: `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.
Frozen generation: greedy, num_beams=1, max_new_tokens=512, repetition_penalty=1.0, seed=0; deterministic algorithms, four Torch threads and one interop thread. All twelve requested-vs-actual checks matched 67/67 fields.
Runtime: torch 2.14.0+cpu, Outlines 1.3.3, outlines_core 0.2.14; official `torch.compiler.set_stance("force_eager")`. Decoder `DECODER_ENFORCEMENT_REGEX_V2_1_V0_1`; exact validator jsonschema 4.26.0 / Draft202012Validator / referencing 0.37.0; deterministic adapter unchanged.
Execution: `2026-10-16T19:22:07.274743+00:00` through `2026-10-16T19:53:46.725638+00:00`. Model initialization 1; tokenizer load 1; Index construction 1; formal generation calls 12; completed generations 12; measured forward calls 2182. Retries 0, repairs 0, timeouts 0; no infrastructure failure.
No model, tokenizer, decoder or retrieval execution occurred during scoring/final-record completion. The execution artifact retains its historical EXECUTION_COMPLETE_AWAITING_MANUAL_SCORING status; the scored outcome is recorded here and in SEMANTIC_SCORES.json.

## Structural and semantic results

JSON PASS 11/12; exact-schema PASS 9/12; adapter PASS 9/12; COMBINED_STRUCTURAL_ACCEPT 9/12. Q01/Q02 have inconsistent ABSTAIN/SUPPORTED_BY_ACTIVE_POLICY pairings and were rejected by the exact schema, with adapter NOT_RUN. Q04 ended at 512 tokens without EOS and with an incomplete object; decoder structural rejection prevented JSON/schema/adapter execution. This was a completed token-limited generation, not an infrastructure failure.
Every raw output was saved before structural processing. No output was repaired, completed or regenerated.

| Metric | Observed | Frozen requirement | Result |
|---|---:|---:|---|
| Combined structure | 9/12 | 12/12 | FAIL |
| Final decision exact | 5/12 | at least 10/12 | FAIL |
| Supported-class decision | 1/4 | at least 3/4 | FAIL |
| Insufficient-class decision | 0/4 | at least 3/4 | FAIL |
| Unresolved-class decision | 4/4 | at least 3/4 | PASS |
| Literal reason-code exact in parseable raw fields | 3/12 | at least 10/12 | FAIL |
| Material-ask recall | 12/18 (66.67%) | at least 90% | FAIL |
| Material-ask precision | 12/29 (41.38%) | at least 90% | FAIL |
| Incorrect/unsupported citations from complete JSON outputs (primary metric) | 84 | 0 | FAIL |
| Supported-ask evidence coverage | 3/8 (37.50%) | at least 90% | FAIL |
| Retries / repairs | 0 / 0 | 0 / 0 | PASS |

Literal reason accuracy includes Q01/Q02, whose matching reason text is part of rejected raw objects, not valid GateOutputs. Accepted-GateOutput reason accuracy is separately 1/12. Q09-Q12 correctly abstain as binary decisions but use the wrong insufficient-support reason and resolved context.
Owner-reviewed evidence-grounding accounting: the primary metric is 84 unsupported/incorrect citation occurrences from complete JSON outputs. Complete JSON does not imply schema-valid or semantically correct output. An additional 57 citation-like references in the incomplete Q04 prefix are `DIAGNOSTIC_ONLY` and are excluded from the primary citation metric. Complete outputs alone violate the frozen zero-incorrect-citations requirement. SEMANTIC_SCORES.json remains byte-identical as historical scoring evidence; its combined 141-occurrence field is not the owner-reviewed primary metric. This administrative clarification does not repair or rescore any output.
Q04 has no completed decision and earns no decision credit. Its seven complete ask strings and 67 visible rank numerals were inspected as explicitly marked forensic spans, without completing JSON or passing repaired data to any pipeline layer. The primary precision denominator includes all 29 observed asks. Complete-JSON-only precision is a separate diagnostic 12/22 (54.55%), not a replacement denominator.
Manual semantic-equivalence and evidence-grounding judgments were applied by the agent in this session under the frozen rubric; no second model/API judge was invoked. All ask match decisions, Gold and generated asks, citation-by-citation rationale and negative-class evidence behavior are recorded in SEMANTIC_SCORES.json for owner review. Genuine noncanonical supporting evidence was credited where justified (including Q08 rank 5).
All twelve cases have detailed semantic disposition FAIL; this case summary adds no qualification threshold. Structural and decision/reason failures already establish the formal outcome independently of manual ask/citation judgments.

| Case | Gold class | Generated decision | Generated reason | Decision correct | Reason literal correct | Ask matches / emitted | Bad citations | Structural disposition | Semantic |
|---|---|---|---|---|---|---:|---:|---|---|
| Q01 | SUPPORTED_BY_ACTIVE_POLICY | ABSTAIN | SUPPORTED_BY_ACTIVE_POLICY | False | True | 0 / 3 | 30 | EXACT_SCHEMA_REJECT | FAIL |
| Q02 | SUPPORTED_BY_ACTIVE_POLICY | ABSTAIN | SUPPORTED_BY_ACTIVE_POLICY | False | True | 0 / 5 | 10 | EXACT_SCHEMA_REJECT | FAIL |
| Q03 | SUPPORTED_BY_ACTIVE_POLICY | ALLOW | SUPPORTED_BY_ACTIVE_POLICY | True | True | 2 / 2 | 2 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q04 | SUPPORTED_BY_ACTIVE_POLICY | UNAVAILABLE | UNAVAILABLE | False | False | 0 / 7 | 57 DIAGNOSTIC_ONLY (excluded from primary metric) | DECODER_STRUCTURAL_REJECT | FAIL |
| Q05 | INSUFFICIENT_POLICY_SUPPORT | ALLOW | SUPPORTED_BY_ACTIVE_POLICY | False | False | 1 / 1 | 10 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q06 | INSUFFICIENT_POLICY_SUPPORT | ALLOW | SUPPORTED_BY_ACTIVE_POLICY | False | False | 1 / 1 | 10 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q07 | INSUFFICIENT_POLICY_SUPPORT | ALLOW | SUPPORTED_BY_ACTIVE_POLICY | False | False | 1 / 2 | 5 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q08 | INSUFFICIENT_POLICY_SUPPORT | ALLOW | SUPPORTED_BY_ACTIVE_POLICY | False | False | 2 / 2 | 17 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q09 | UNRESOLVED_POLICY_CONTEXT | ABSTAIN | INSUFFICIENT_POLICY_SUPPORT | True | False | 0 / 1 | 0 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q10 | UNRESOLVED_POLICY_CONTEXT | ABSTAIN | INSUFFICIENT_POLICY_SUPPORT | True | False | 1 / 1 | 0 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q11 | UNRESOLVED_POLICY_CONTEXT | ABSTAIN | INSUFFICIENT_POLICY_SUPPORT | True | False | 2 / 2 | 0 | COMBINED_STRUCTURAL_ACCEPT | FAIL |
| Q12 | UNRESOLVED_POLICY_CONTEXT | ABSTAIN | INSUFFICIENT_POLICY_SUPPORT | True | False | 2 / 2 | 0 | COMBINED_STRUCTURAL_ACCEPT | FAIL |

## Integrity and quarantine

Package additions 0, removals 0, version/METADATA/RECORD drift 0; pre/post inventories match for all 64 packages. Saved pip checks before/after PASS. Installed execution-source and historical-source integrity checks PASS. Downloads 0; external network connections 0. Socket observations were gethostname, socket construction, and IPv6 loopback bind to ::1:0 only.
Phase 2H DEVELOPMENT access 0; retrieval 0; Phase 2H HELD_OUT access false; Phase 2G private HELDOUT access false. No benchmark questions were used. No package mutation or external calls during finalization.
Suite, Gold, thresholds, prompt, generation configuration, raw schema, decoder, validator and adapter were not changed after freezing. Historical failed/qualified checkpoints remain preserved. No tuning, model selection, recovery, additional qualification call or DEVELOPMENT evaluation followed these results.

## Owner-reviewed capability interpretation and helper provenance

Structural runtime was previously qualified in smoke recovery. Formal semantic structural robustness FAILED this 12-case qualification; semantic decision quality FAILED; material-ask identification FAILED; evidence grounding FAILED. The structural semantic-qualification gate required 12/12 and failed at 9/12. This disposition applies to the frozen candidate/model/configuration; it does not establish that the entire V2.1 architecture is invalid.

The suite receipt froze at `2026-10-16T19:19:20.470397+00:00` and does not itself list the helper. The subsequent pre-call FRESHNESS_AUDIT.json, recorded at `2026-10-16T19:21:51.122754+00:00`, explicitly records `execution_helper_frozen_before_model_initialization=true` and helper SHA `b2f9b916eb4d9c0e29d526a77dac29a3b276a3ffef02cd7cf8bf0e55a26525c5`. Execution began at `2026-10-16T19:22:07.274743+00:00`; its helper SHA and the current final helper SHA match that pre-call identity exactly.

Provenance result: `PRE_CALL_HELPER_HASH_FROZEN_AND_UNCHANGED`. No post-exposure helper edit was found, so no post-execution scoring-implementation-edit classification is applicable. All 17 frozen source identities and the generation-relevant Suite, Gold, prompt, GateInputs, thresholds, configuration, decoder, validator, adapter and saved raw outputs remain unchanged. Manual scoring/finalization did not change the helper or rerun model calls.

During this owner finalization, model initialization, tokenizer loads, generate, forward, decoder execution, retrieval, package mutation, downloads and external network activity were all 0. DEVELOPMENT access was 0 and both HELD_OUT accesses remained false. Only this administrative record and its dependent hash-manifest entry changed; the eight other artifacts and execution helper retain their prior bytes. Historical execution counters and outcomes remain as recorded above.

## Artifact hashes

The following eight artifacts existed before final-record completion and were verified byte-identical. FINAL_SHA256.json covers these, this final record, and the one execution helper. It excludes itself to avoid a circular hash requirement.

| Artifact | SHA-256 |
|---|---|
| FRESHNESS_AUDIT.json | `ce305dba39fe6ee174c8101f4bb14225582f16fda9caf1f1ce8d8ba3d59042c9` |
| QUALIFICATION_GOLD.json | `971e2617f69c9d6ebc4b3eafe51f0394c4759247bc8963ef4bd9c7bd7f58ae61` |
| QUALIFICATION_PROTOCOL.md | `2625040df5fabab42d12f158ec9d39d35ba7a735978dd343a64688be3b37b55d` |
| QUALIFICATION_SUITE.json | `28dd6bc1d7a561ac350284c3e5df5b92979960b591d39609dd202c1de1aa360c` |
| RAW_GENERATIONS.json | `6ad5884bbb694bd5e5feb5cbbe6e1b1ce642d8659ef885b1cc38dacb159a5d3e` |
| SEMANTIC_SCORES.json | `82ac2ba593048d37059f1620a43cbc25646c2660ac745dcdd028a7cfd7635ee4` |
| STRUCTURAL_RESULTS.json | `8bb68eb885388503afb2b45b960b2779c42411f62694fc111d3462f7b0ef8337` |
| SUITE_FREEZE_RECEIPT.json | `dfe41f7c858ccbdf8f0fc4dce95f265c4537ffb135bad62cc85fa8139ef43080` |
| gateway/domain/evaluation/answerability/run_fresh_semantic_qualification.py | `b2f9b916eb4d9c0e29d526a77dac29a3b276a3ffef02cd7cf8bf0e55a26525c5` |

## Git and owner boundary

Only one untracked execution helper is visible in ordinary Git status:
```text
?? gateway/domain/evaluation/answerability/run_fresh_semantic_qualification.py
```
All ten requested artifacts are local/ignored under artifacts/answerability_semantic_v2_1_semantic_qualification/. No focused test or other helper was created. Tracked-file diff and staged-file list are empty. No commit or tag was made.
Owner scientific review is complete. Stop after administrative finalization. No further execution, rerun of this suite against this candidate, DEVELOPMENT evaluation, or silent replacement-model selection is authorized.
