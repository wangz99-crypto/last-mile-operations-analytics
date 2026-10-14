# LLGuidance stack preregistration record

Phase: 2H-B3.2-A2.1-I. Date: 2026-10-13 (America/New_York).
Owner status: **OWNER_REVIEWED / LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED**.
Outcome: **LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED**.

Base HEAD/tag: baae21265e1ec192f0ddf047f7dd8b3377647c8b / answerability-semantic-v2-lmfe-v0.4-schema-incompatibility. Initial Git status was clean.

Sole selected grammar engine llguidance==1.9.1 is SELECTED_NOT_INSTALLED / NOT_QUALIFIED / CAPABILITY_NOT_ASSESSED. Future integration outlines==1.3.3 with llguidance remains SELECTED_FOR_FUTURE_INTEGRATION / NOT_INSTALLED / NOT_QUALIFIED. No alternate stack/version was investigated or selected after this blocker.

Official wheel identities match the owner-provided hashes and Python/Windows tags fit. However, official versioned source recognizes but does not implement critical V2 uniqueItems, contains and if/then/else constraints. Its strict path rejects known unimplemented keys; relaxing lenient mode would not preserve V2. This fundamentally contradicts the required unchanged-schema stack and triggers the authorized BLOCKED outcome before any package or decoder execution. It is not a measured qualification failure. oneOf/allOf support remains partial/conditional independently of this blocker.

V2: SEMANTIC_MATERIAL_SUPPORT_V2 / PRE_REGISTERED_NOT_EVALUATED.
Exact schema SHA-256: 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e.
Fresh semantic qualification suite: NOT YET AUTHORED.

The conditional K0-K5/L/M ladder, immutable M1-M8 identities, known-risk pointers, critical feature matrix, coerce_one_of=false and lenient=false are recorded for review. They do not authorize progression. Exact future Outlines API paths and dependency closure remain pending a separately authorized phase, and the current blocker prevents K0.

Offline preregistration checks: 16/16 PASS; no package/model imports, socket/subprocess events or file-allowlist violations during the successful guarded check. An initial offline test wrapper stopped before tests on importlib's bytecode-cache lookup; direct loading of the unchanged test source completed under the same strict guard. No decoder/parser/model was executed by either check wrapper.
Test SHA-256: d30df23eeb9a7d98b451fad14e2337125609c1279135efc32ebabeb8efc684f4.
No new runtime helper was implemented.

Historical integrity: 249 explicitly named historical files hashed, prior GD receipt 82/82 matches; protected remaining groups verified through unchanged tracked Git state without opening benchmark/B2 bodies. LMFE and XGrammar owner-reviewed exact-schema rejection conclusions preserved. Frozen 36-package inventory remains unchanged, including distribution METADATA/RECORD hashes. Neither selected package is present.

All execution counters in PHASE_ACCOUNTING.json are zero: package install/removal/mutation; selected decoder imports; grammar compile/validate; matcher construction/execution; tokenizer load; Qwen init/generate/forward; semantic outputs; DEVELOPMENT; retrieval. Phase 2H HELD_OUT and Phase 2G private HELDOUT access are false. Only authoritative metadata/source network reads occurred; 19 successful direct requests are receipted, plus web-tool inspections whose transport/cache request count is not inferred. No wheel/model/source-tree download or package resolver.

FINAL_SHA256.json records final artifact/test/attributes hashes, excluding its own hash to avoid self-reference; its SHA is reported in the completion response. Git scope: exact preregistration artifacts, one offline test and exact artifact-path -text rules only. No commit or tag.

STOP for final owner verification. No enablement, schema adaptation, alternate version selection or structural qualification is authorized.

## Final owner approval — 2026-10-13

Owner: Zhe Wang (Victor).
Owner approval date: 2026-10-13.
Scientific owner review: **PASS — STATIC INCOMPATIBILITY BLOCK ACCEPTED**.
Final owner status: **OWNER_REVIEWED / LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED**.
Primary blocking classification: **FROZEN_V2_SCHEMA_USES_UNIMPLEMENTED_LLGUIDANCE_1_9_1_KEYWORDS**.

This is a preregistration/static-compatibility outcome, NOT a decoder qualification failure.

| Interpretation | Final value |
| --- | --- |
| Formal outcome | LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED |
| llguidance package/runtime compatibility | NOT_ASSESSED |
| Exact frozen-schema structural capability | NOT_ASSESSED BY EXECUTION |
| Static exact-schema compatibility | BLOCKED |
| Capability | NOT_ASSESSED |
| Decoder qualification executions | 0 |

Selected implementation identity remains llguidance==1.9.1; future integration candidate remains outlines==1.3.3. Neither was installed or executed. Earlier Python/wheel-tag compatibility observations are metadata checks only, not package/runtime qualification. SEMANTIC_MATERIAL_SUPPORT_V2 remains PRE_REGISTERED_NOT_EVALUATED.

## Accepted official-source finding

The saved official v1.9.1 source declares an explicit implemented-keyword set in parser/src/json/schema.rs, lines 16-49. It includes anyOf, oneOf, allOf, $ref, const, enum, type, items, prefixItems, minItems, maxItems, properties, additionalProperties, required, minLength, maxLength, pattern, minimum and maximum, among others. It does not list **uniqueItems, contains, if, then, else** as implemented.

The saved release-source identity is SHA-256 3b043d701153560437e423f28b1924779323ea960c5e80761e3a461dd39001bb. Source URLs, request identities and other relevant hashes remain in UPSTREAM_SOURCE_RECEIPT.json. This finalization used those saved findings; no new network/source request or package execution occurred.

The dispatch rule in shared_context.rs lines 128-135 distinguishes recognized JSON Schema keywords from implemented/annotation keywords; context_simple/draft.rs lines 102-114 recognizes the unsupported keywords for V2's draft. schema.rs lines 617-630 collects unimplemented valid keys. With default/strict **lenient=false**, it returns an error rather than treating those constraints as implemented. Hence exact frozen V2 cannot be preregistered as fully preserved by llguidance 1.9.1 strict compilation. This conclusion is static, not an observed execution result.

Frozen schema SHA-256: **6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e**. Its material use of all five keywords is unchanged:

- uniqueItems: /properties/material_asks/items/properties/supporting_evidence_ranks/uniqueItems
- contains: /oneOf/1/properties/material_asks/contains and /oneOf/2/anyOf/1/properties/material_asks/contains
- if/then/else: /properties/material_asks/items/allOf/0

The following remain NOT AUTHORIZED: lenient=true; ignoring uniqueItems, contains or if/then/else; rewriting the frozen schema; removing unsupported constraints; coercing unsupported keywords. Warnings or ignored constraints do not establish exact-schema enforcement. No silent semantic weakening occurred. coerce_one_of=false remains unchanged.

## Preserved accounting and evidence

All following counters remain zero for this phase and for finalization: package installations/removals/mutations; llguidance imports; Outlines imports; grammar compilations/validations; matcher constructions/executions; tokenizer loads; Qwen initialization; generate; forward; semantic outputs; DEVELOPMENT; retrieval. Phase 2H HELD_OUT access=false; Phase 2G private HELDOUT access=false. Fresh V2 semantic qualification suite=NOT YET AUTHORED.

Finalization network activity=0; no resolver, package API check, grammar qualification, new semantic suite or model activity. Existing **16/16 offline preregistration checks PASS** is preserved byte-for-byte and verified from its saved result; the checks were not rerun. They establish record integrity only, not llguidance capability.

The current frozen 36-package inventory was recomputed using standard-library distribution metadata reads only and matches the recorded inventory, including every distribution version and METADATA/RECORD hash. Inventory SHA remains 00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d. Package drift=0; llguidance and Outlines remain absent. XGrammar and LMFE historical environment unchanged.

All 249 named historical artifact/source hashes reverified. GD, G, FR, F, E, XGrammar diagnostic and Attempt 2, R2/R1, original qualification and V2 preregistration remain unchanged. V1 qualification, runtime freeze, B3, B2, benchmark, retriever, policy corpus and deterministic engine retain unchanged tracked Git identity; their benchmark/private contents were not opened. Only this administrative record changes during finalization.

## Engineering consequence and next-phase boundary

**llguidance==1.9.1 exact-schema qualification/install path is NOT AUTHORIZED.** Static source analysis already establishes unimplemented material V2 keywords under strict compilation. Do not spend package-mutation, tokenizer or Qwen budget on this candidate.

Do not select a fourth decoder. A later phase requires a separately preregistered architectural decision about constrained-generation responsibility versus deterministic exact-schema validation. This freeze record authorizes no new architecture or experiment.

## Final hash provenance

Original candidate record SHA-256: de2c52c9c52ed609f5ec08295f61482094df1b416fa1840213f68bfb61ef20cb.
Original FINAL_SHA256.json preserved SHA-256: 6e8dea24dd46c0146ca3d33e9fdf3df095912e9e5bbb820fc27b31a0ceed36fe.

FINAL_SHA256.json is the unchanged pre-owner candidate snapshot. Only its PREREGISTRATION_RECORD.md entry is superseded by this owner-finalized record. Every other entry remains current. Earlier report/protocol/registry owner-status fields are preserved as pre-owner snapshots; this record is authoritative for final approval, interpretation and prohibition of progression. The final record's own SHA is reported externally to avoid circular self-hashing.

Unchanged final artifact hashes (all other 22 artifacts):

```text
b3ff25bf07a7aca29a5bc3426db85dff6f18d80974e6bc1152016307dab542d7  COMPLETION_REPORT.md
f51f3c57f7a8e830426adcaa7877812f51957fa8cd990382c33bc0430142fc89  DECLARED_DEPENDENCY_GRAPH.json
bb261c47b0ef8794f7f4f6fa13530586b2e387fa1178fcd6ea68b85e03570692  ENVIRONMENT_COMPATIBILITY_MATRIX.json
00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d  ENVIRONMENT_METADATA_SNAPSHOT.json
7b21fc185ea9989f20893149bb4a1fa70d274f8cacc8d8c8a966c95499a061d1  FINAL_ENVIRONMENT_VERIFICATION.json
6e8dea24dd46c0146ca3d33e9fdf3df095912e9e5bbb820fc27b31a0ceed36fe  FINAL_SHA256.json
7747e882ea63628d5ce31de0e315044c40bb2ed85080599632b23bc45235eec2  FUTURE_STRUCTURAL_GATE.md
76321c74aca3b8bb665ba1c554caa1d924bcbb5ed795ee8214221d84698e7897  GIT_REVIEW.json
47b6cee57b5251f630ac83bd575f5f3cc0677fd0e2fb92cb41bd23e1dcf7c387  HISTORICAL_INTEGRITY_RECEIPT.json
10ddd36eb3cada03a5d09d0bc122e72cbd548832d3ef5651753408f5d6e63aad  INTEGRATION_STACK_CONTRACT.md
9bd262000fb3d76b14d7ec17491d583a1d5d074808ec09163b57001c9430a2c7  JSON_SCHEMA_CAPABILITY_MATRIX.json
da0f069186390525b655a4f5009e708652d5af1ff0f83ec456ca4a4d262a7895  KNOWN_RISK_SCHEMA_SHAPES.md
a4c74eb7df4b3390afb11438fb7823afd4546dcaf6691d477ee4c847a898e24c  LLGUIDANCE_PACKAGE_IDENTITY.json
6a50b94ce0b5d5a25bda5de91fbec010003231e8bf47f7277e8f41daefc88b1e  LLGUIDANCE_STACK_PREREG_PROTOCOL.md
b19396f1b73ca70bb87d680e49423d4a4ce3a47490b315429024e7013f9905d5  NETWORK_SCOPE_SUMMARY.json
04de17a448b54137fec3b1a7fdf6bc944dfe3fa88b14d15ea525ea81f8d03bca  OFFLINE_TEST_RESULTS.json
8d38adb9e3ff4e31f5c687be3f634ea2569085f3250c959096618e167d8af32f  OUTLINES_PACKAGE_IDENTITY.json
560e70dc074dc4fbc6e4a4cae70cc93d1cdd843cde9439cf9372ca8dd38d73a7  PHASE_ACCOUNTING.json
0768db98e661118b3e4c2d8a3096090596617b44070114444db503c2c63bb03d  PREREGISTERED_STACK.json
4cf1e11e920f471f7fa492ea8c5d9f5770bf02dec2b4587e4045cd0613b26a97  RELEASE_METADATA_RECEIPT.json
422dff9c61b53ac7a44fd2ff768ecf0a1088adf5e744405818e9e2423f93f444  STACK_SELECTION_RECORD.md
cb71264da54d3ee2f77c038411df1065291e0bb0e84d4b382db496b23c202398  UPSTREAM_SOURCE_RECEIPT.json
```

Unchanged source/test hashes (no new runtime helper):

```text
36083e7a506a41082f8cbb62a82222169f970c66e3bdb7320c2bb75600bd616d  gateway/domain/evaluation/answerability/localize_lmfe_schema.py
45cc57a9534a56fef5834fffd422e618e2bb0574adaed90ac019ab4072d66bc0  gateway/domain/evaluation/answerability/qualify_lmfe_structure.py
2d7aef05951544a4ac99c7a49b6c614a711691077f323d6b7e1d2de350f4f07b  gateway/domain/evaluation/answerability/xgrammar_v2_decoder.py
ffe40fc052f6c25484d0abdf60411c1317873c1965e38c94860d6c88781181f9  gateway/domain/evaluation/answerability/xgrammar_v2_smoke.py
d30df23eeb9a7d98b451fad14e2337125609c1279135efc32ebabeb8efc684f4  gateway/domain/tests/test_llguidance_stack_prereg.py
415dafa6f90d6e667419bbdbb3df41346492c79946bad7fc867742f8a57f5ee7  gateway/domain/tests/test_lmfe_schema_localization.py
7b0675b7b09576dde885d6534847400be23135f7a7f65201e98238cfb94cd2e7  gateway/domain/tests/test_lmfe_structural_conformance.py
```

.gitattributes worktree SHA-256: 96b2e4c11896217034186407456cce4eda7bbcb77b1dce7396583ed86bad3617. Its 23 exact artifact-path -text rules are unchanged. No general JSON/artifact/source rule was introduced during finalization.

## Final Git review

The same 25-file preregistration candidate remains staged: 23 phase artifacts, one offline test and .gitattributes. Only this owner administrative record changes relative to the entry candidate. No wheel, model, package, cache, private data or historical file is staged by this finalization. No commit or tag.

`git status --short` (verified again after staging this record):

```text
M  .gitattributes
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/COMPLETION_REPORT.md
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/DECLARED_DEPENDENCY_GRAPH.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/ENVIRONMENT_COMPATIBILITY_MATRIX.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/ENVIRONMENT_METADATA_SNAPSHOT.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/FINAL_ENVIRONMENT_VERIFICATION.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/FINAL_SHA256.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/FUTURE_STRUCTURAL_GATE.md
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/GIT_REVIEW.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/HISTORICAL_INTEGRITY_RECEIPT.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/INTEGRATION_STACK_CONTRACT.md
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/JSON_SCHEMA_CAPABILITY_MATRIX.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/KNOWN_RISK_SCHEMA_SHAPES.md
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/LLGUIDANCE_PACKAGE_IDENTITY.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/LLGUIDANCE_STACK_PREREG_PROTOCOL.md
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/NETWORK_SCOPE_SUMMARY.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/OFFLINE_TEST_RESULTS.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/OUTLINES_PACKAGE_IDENTITY.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/PHASE_ACCOUNTING.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/PREREGISTERED_STACK.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/PREREGISTRATION_RECORD.md
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/RELEASE_METADATA_RECEIPT.json
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/STACK_SELECTION_RECORD.md
A  artifacts/answerability_semantic_v2_llguidance_stack_prereg/UPSTREAM_SOURCE_RECEIPT.json
A  gateway/domain/tests/test_llguidance_stack_prereg.py
```

`git diff --cached --name-only`:

```text
.gitattributes
artifacts/answerability_semantic_v2_llguidance_stack_prereg/COMPLETION_REPORT.md
artifacts/answerability_semantic_v2_llguidance_stack_prereg/DECLARED_DEPENDENCY_GRAPH.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/ENVIRONMENT_COMPATIBILITY_MATRIX.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/ENVIRONMENT_METADATA_SNAPSHOT.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/FINAL_ENVIRONMENT_VERIFICATION.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/FINAL_SHA256.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/FUTURE_STRUCTURAL_GATE.md
artifacts/answerability_semantic_v2_llguidance_stack_prereg/GIT_REVIEW.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/HISTORICAL_INTEGRITY_RECEIPT.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/INTEGRATION_STACK_CONTRACT.md
artifacts/answerability_semantic_v2_llguidance_stack_prereg/JSON_SCHEMA_CAPABILITY_MATRIX.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/KNOWN_RISK_SCHEMA_SHAPES.md
artifacts/answerability_semantic_v2_llguidance_stack_prereg/LLGUIDANCE_PACKAGE_IDENTITY.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/LLGUIDANCE_STACK_PREREG_PROTOCOL.md
artifacts/answerability_semantic_v2_llguidance_stack_prereg/NETWORK_SCOPE_SUMMARY.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/OFFLINE_TEST_RESULTS.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/OUTLINES_PACKAGE_IDENTITY.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/PHASE_ACCOUNTING.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/PREREGISTERED_STACK.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/PREREGISTRATION_RECORD.md
artifacts/answerability_semantic_v2_llguidance_stack_prereg/RELEASE_METADATA_RECEIPT.json
artifacts/answerability_semantic_v2_llguidance_stack_prereg/STACK_SELECTION_RECORD.md
artifacts/answerability_semantic_v2_llguidance_stack_prereg/UPSTREAM_SOURCE_RECEIPT.json
gateway/domain/tests/test_llguidance_stack_prereg.py
```

Stop for final owner verification. Do not install, qualify, select another decoder, change schema or begin another architecture phase.
