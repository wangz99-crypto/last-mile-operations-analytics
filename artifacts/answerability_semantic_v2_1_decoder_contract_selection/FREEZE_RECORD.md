# P2P3 contract freeze and candidate selection

Status: OWNER_REVIEWED / DECODER_CANDIDATE_SELECTION_BLOCKED

Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-14
Scientific review: PASS — CONTRACT FROZEN, CANDIDATE STATICALLY BLOCKED

Primary candidate: outlines==1.3.3; outlines_core==0.2.14.
Integration path: JSON Schema backend.
Primary blocking classification: OUTLINES_CORE_JSON_SCHEMA_STRING_LANGUAGE_NARROWING.
Candidate result: REJECTED FOR JSON-SCHEMA-BACKEND PATH.
DIRECT REGEX BACKEND = NOT_ASSESSED.
This result must not be generalized to all Outlines/outlines-core usage.

Contract frozen before candidate inspection = true.
V_exact ⊆ V_decoder derivation = ESTABLISHED.
The authoritative contract and derivation rules remain unchanged.

Formal outcome: **DECODER_CANDIDATE_SELECTION_BLOCKED**.
Contract derivation succeeded; the sole decoder candidate was not selected or qualified.

Base HEAD and tag `answerability-semantic-v2_1-responsibility-split-v0.1-pre-contract` both resolve to `4458c5efefc020b9a4f86fcff6c41cce1f668e19`. Entry Git status was clean.
P1 owner status verified: OWNER_REVIEWED / RESPONSIBILITY_SPLIT_PREREGISTERED.
Implementation: SEMANTIC_MATERIAL_SUPPORT_V2_1. Raw schema remains authoritative with SHA-256 `6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.

## Scientific barrier

Contract: DECODER_ENFORCEMENT_CONTRACT_V2_1_V0_1, NON_AUTHORITATIVE_DECODER_CONTRACT.
Rules frozen at 2026-10-14T18:53:51.971690+00:00.
Contract frozen at 2026-10-14T18:55:10.522938+00:00.
Candidate inspection started at 2026-10-14T18:55:34.622467+00:00.
First recorded external metadata response: 2026-10-14T18:56:44.752083+00:00.
The receipt preserves ordered events and five original hashes; all five remain unchanged after candidate research.

64 source constraints / 64 trace rows; 18 decoder-owned represented; 46 validator-only delegated; 0 unowned; 0 lost; 6 adapter responsibilities; 0 adapter migrations.
V_exact subset V_decoder is established by structural derivation: retain unconditional predicates, recursively retain property/element scopes, and remove whole delegated assertions without inversion or hoisting. Serialization is not an extra semantic constraint.
M1 expected ACCEPT; M2-M8 expected REJECT because each has a frozen decoder-owned required-field violation. These are declarations, not executed conformance results.

## Candidate result and limits

Sole stack: outlines==1.3.3 + outlines_core==0.2.14, through the JSON Schema backend. Candidate capability remains: 17 rules = REQUIRES_RUNTIME_QUALIFICATION; 1 rule = STATICALLY_UNSUPPORTED for the selected JSON-Schema backend path; zero runtime PASS claims.
The candidate's generic JSON-string generation language cannot represent all semantic string values permitted by the frozen Decoder Enforcement Contract, including U+0000 where allowed by the authoritative contract. This establishes the static blocking cause for this integration path; it is not a runtime-generation causal experiment.

- fixed property ordering = serialization-only / not causal
- whitespace canonicalization = serialization-only / not causal
- integer canonicalization = serialization-only / not causal
- generic string value restriction = SEMANTIC_VALUE_RESTRICTION / CAUSAL

The candidate was blocked without contract edits or alternative decoder research. DIRECT REGEX BACKEND = NOT_ASSESSED; no conclusion about that path is authorized.

Pinned release metadata, file hashes, source URLs, dependency graph and Windows CPython wheel compatibility are in CANDIDATE_DEPENDENCY_METADATA.json. Seven unpinned missing dependencies remain DEPENDENCY_VERSION_SELECTION_PENDING; no complete resolved installation lock is claimed. CPU FP32 execution remains NOT_ASSESSED. No mandatory CUDA/vLLM/Linux requirement was established in the inspected Transformers entrypoint.
Exact-schema validator: NOT_YET_SELECTED_NOT_QUALIFIED.
Future P4 is conditional on candidate selection, so it is not authorized by this blocked result. All 18 direct probe definitions are unexecuted.

## Activity and quarantine

Package installs/removals/mutations = 0. Outlines/core imports = 0. Candidate grammar/regex compilation = 0. Logits processor construction = 0. Tokenizer loads = 0. Qwen initialization = 0. Generate = 0. Forward = 0. Exact-schema validation executions = 0. DEVELOPMENT = 0. Retrieval = 0.
Phase 2H HELD_OUT access = false. Phase 2G private HELDOUT access = false. Fresh V2.1 semantic suite = NOT YET AUTHORED.
17 successful official PyPI/GitHub metadata/source requests are recorded; network activity is not claimed to be zero. Package/model downloads = 0. Source responses were inspected as text and never executed. No further candidate capability research followed the incompatibility finding.

## Verification and provenance

Focused offline tests: 6/6 PASS, 0 errors/failures/skips; no prohibited import/network/process/quarantine attempts during tests. These checks do not establish decoder capability. See OFFLINE_TEST_RESULTS.json.
276/276 prior named historical hashes verified unchanged. P1's 22 additional receipt entries plus finalized owner record verified unchanged; historical FINAL_SHA256 is preserved, including its superseded pre-owner administrative hash. Current P1 owner-record SHA is `a98fe04d0e5f3ee7604c034adae5635d8c579b031929acd44facfdeda5782bf4`.
XGrammar, LMFE, llguidance, V2/V2.1 definitions and adapter histories remain intact. Runtime metadata inventory is unchanged: 36 packages, zero drift. Benchmark, retriever, policy corpus and deterministic engine are protected by unchanged tracked Git identity; benchmark/private contents were not opened.

Pre-owner artifact hashes and helper/test worktree hashes are preserved in FINAL_SHA256.json, whose unchanged SHA-256 is `0b4506846168afb978660c84b9d12fd899b471981e8fadd81b57f792fc241ea7`. Its FREEZE_RECORD.md entry (`ac0c8bade367e197bda09d2e325072c6c244813dc12836328187a3900cfaf008`) identifies the superseded pre-owner administrative record, not the finalized bytes. Only this administrative freeze record was authorized to change; the receipt itself was not rewritten. Every other receipt entry remains valid. The finalized record hash is reported externally to avoid a circular self-hash. The 12 scientific artifacts and the two new hash-bound helper/test source files receive 14 exact-path -text rules. This preserves source identities across fresh checkouts. The .gitattributes file itself retains normal Git text handling.

## Frozen Phase A hashes

- `CORE_FIXTURE_EXPECTATIONS.json`: `14710f087bfd539038057da376a925e0423bfca7a4fd396ac30dd2ce478c34e3`
- `DECODER_CONTRACT_DERIVATION_RULES.json`: `ea6e491ba295328bae66651230da39c87159ee06cc3eb4b2d146bbe066cc029e`
- `DECODER_CONTRACT_DERIVATION_TRACE.json`: `f1a667780a09c03b928542b1d54f6f4538efb2bf18271258a7a4347f3a6a8ea6`
- `DECODER_ENFORCEMENT_CONTRACT.json`: `768b9147e77f1dcc9dfd13b9dc4a6f9a2dad0ea6ad498219341fee0c43166198`
- `VALIDATOR_ONLY_CONSTRAINTS.json`: `ba702eee48c216166c5e358c754c3b84f780e59d0e7a755fadc290aa746dda63`

## New source hashes

- `gateway/domain/evaluation/answerability/derive_decoder_contract.py`: `65be424feaa153f9e792fbd0376b5fc1c84dcbd876183fefaac4079df35bff7c`
- `gateway/domain/tests/test_decoder_contract_selection.py`: `ae2085a2f8ea521662b4f26129c2325bcc5cf378240e780cc06c672051addc0d`

## Complete candidate file inventory

- `.gitattributes`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/CANDIDATE_DEPENDENCY_METADATA.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/CANDIDATE_SELECTION_RECORD.md`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/CONTRACT_FREEZE_RECEIPT.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/CORE_FIXTURE_EXPECTATIONS.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_CONTRACT_DERIVATION_RULES.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_CONTRACT_DERIVATION_TRACE.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_ENFORCEMENT_CONTRACT.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/FINAL_SHA256.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/FREEZE_RECORD.md`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/OFFLINE_TEST_RESULTS.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/OUTLINES_CORE_CONTRACT_CAPABILITY_MATRIX.json`
- `artifacts/answerability_semantic_v2_1_decoder_contract_selection/VALIDATOR_ONLY_CONSTRAINTS.json`
- `gateway/domain/evaluation/answerability/derive_decoder_contract.py`
- `gateway/domain/tests/test_decoder_contract_selection.py`

Owner finalization preserved the existing 6/6 offline checks without rerunning them and reverified 276/276 named historical hashes. During finalization: package installs = 0; decoder imports = 0; decoder executions = 0; tokenizer loads = 0; model initialization = 0; generate = 0; forward = 0; DEVELOPMENT = 0; retrieval = 0; both HELD_OUT access flags = false. Fresh V2.1 semantic suite = NOT YET AUTHORED. No candidate research, alternative selection, installation, runtime execution or network request occurred during finalization.

Only this administrative freeze record changed. No commit or tag created. Owner finalization is complete; no next phase was started.

## Preserved preregistration Git review snapshot

`git status --short`:

```text
M  .gitattributes
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/CANDIDATE_DEPENDENCY_METADATA.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/CANDIDATE_SELECTION_RECORD.md
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/CONTRACT_FREEZE_RECEIPT.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/CORE_FIXTURE_EXPECTATIONS.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_CONTRACT_DERIVATION_RULES.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_CONTRACT_DERIVATION_TRACE.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_ENFORCEMENT_CONTRACT.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/FINAL_SHA256.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/FREEZE_RECORD.md
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/OFFLINE_TEST_RESULTS.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/OUTLINES_CORE_CONTRACT_CAPABILITY_MATRIX.json
A  artifacts/answerability_semantic_v2_1_decoder_contract_selection/VALIDATOR_ONLY_CONSTRAINTS.json
A  gateway/domain/evaluation/answerability/derive_decoder_contract.py
A  gateway/domain/tests/test_decoder_contract_selection.py
```

`git diff --cached --name-only`:

```text
.gitattributes
artifacts/answerability_semantic_v2_1_decoder_contract_selection/CANDIDATE_DEPENDENCY_METADATA.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/CANDIDATE_SELECTION_RECORD.md
artifacts/answerability_semantic_v2_1_decoder_contract_selection/CONTRACT_FREEZE_RECEIPT.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/CORE_FIXTURE_EXPECTATIONS.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_CONTRACT_DERIVATION_RULES.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_CONTRACT_DERIVATION_TRACE.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/DECODER_ENFORCEMENT_CONTRACT.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/FINAL_SHA256.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/FREEZE_RECORD.md
artifacts/answerability_semantic_v2_1_decoder_contract_selection/OFFLINE_TEST_RESULTS.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/OUTLINES_CORE_CONTRACT_CAPABILITY_MATRIX.json
artifacts/answerability_semantic_v2_1_decoder_contract_selection/VALIDATOR_ONLY_CONSTRAINTS.json
gateway/domain/evaluation/answerability/derive_decoder_contract.py
gateway/domain/tests/test_decoder_contract_selection.py
```

Staged blobs equal worktree bytes for all 14 byte-bound files. All 14 exact rules resolve to text: unset. The CRLF-preserved test file triggers the default Git trailing-CR whitespace warning; the check passes with per-command core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol. No file bytes were changed to suppress that warning. No changed path is outside the 15-file candidate scope.
