# A2.1-G structural-conformance owner freeze record

Status: OWNER_REVIEWED / LMFE_STRUCTURAL_CONFORMANCE_FAILED

Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-13
Scientific owner review: PASS — FAILED STRUCTURAL QUALIFICATION ACCEPTED
Primary failure classification: PARSER_TRAVERSAL_UNSUPPORTED_TYPE_NONE

## Final scientific adjudication

- Formal qualification outcome: LMFE_STRUCTURAL_CONFORMANCE_FAILED
- Core parser adjudication: FAILED BEFORE ACCEPT/REJECT COMPLETION
- Required-field enforcement capability: NOT_ASSESSED
- Specific offending schema feature: NOT_YET_ISOLATED
- Core score: 0/8 successfully adjudicated

LMFE 0.11.3 could instantiate `JsonSchemaParser` with the exact frozen V2 schema, but character traversal of all eight frozen core fixtures encountered `Unsupported type None` before structural acceptance/rejection could be adjudicated.

Therefore, LMFE 0.11.3 did not satisfy the frozen parser-level qualification contract for the exact V2 schema. This finding is scoped to lm-format-enforcer==0.11.3, the exact frozen V2 schema, the frozen parser configuration, and the current Python/runtime environment recorded in the qualification artifacts. It is not a conclusion about all LMFE versions or all schemas. No specific unsupported keyword has been established as causal. No claim is made that required fields were ignored or that required-field enforcement itself was adjudicated as failed.

## Preserved core results and triangulation

| Fixture | Parser construction | Traversal | JSON syntax | Frozen JSON Schema |
|---|---|---|---|---|
| M1 | PASS | ERROR: Unsupported type None | VALID | VALID |
| M2 | PASS | ERROR: Unsupported type None | VALID | INVALID |
| M3 | PASS | ERROR: Unsupported type None | VALID | INVALID |
| M4 | PASS | ERROR: Unsupported type None | VALID | INVALID |
| M5 | PASS | ERROR: Unsupported type None | VALID | INVALID |
| M6 | PASS | ERROR: Unsupported type None | VALID | INVALID |
| M7 | PASS | ERROR: Unsupported type None | VALID | INVALID |
| M8 | PASS | ERROR: Unsupported type None | VALID | INVALID |

None of these errors is REJECT or successful enforcement. The saved independent authoritative raw-schema validation confirms that fixture construction behaved as intended. The traversal error was observed in both the expected-valid and expected-invalid fixture groups; this does not isolate its cause.

## Frozen identities and configuration

Base commit: 8ccdacedd1b47de0471b534ac0b0e786e2c36299
Base tag: answerability-semantic-v2-lmfe-v0.2-imports-validated
Frozen V2 schema SHA-256: 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e

The schema, parser configuration, environment settings and CharacterLevelParserConfig values were not changed. No keyword removal, added type field, union rewrite, combinator flattening, alternate field ordering, array limit, alphabet or whitespace setting was tried. Any future schema adaptation requires separate architecture/candidate preregistration.

Extended probes preregistered: 38
Extended probes executed: 0
Extended status: NOT_RUN_DUE_TO_CORE_GATE_FAILURE
This preserves the preregistered hard stop.

## Preserved runtime and evidence

Saved pre/post package count: 36 / 36
Package additions: 0
Package removals: 0
Version drift: 0
METADATA drift: 0
RECORD drift: 0
Saved pip check: PASS
Pre/post complete inventory SHA-256: 00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d
Saved offline helper tests: 15/15 PASS

These findings were verified from saved evidence during finalization. Neither tests, pip check nor the real parser qualification were rerun.

Historical qualification counters:

- Core parser executions: 8
- Parser retries: 0
- Extended parser executions: 0
- Tokenizer loads: 0
- Qwen/model initialization: 0
- Generate: 0
- Forward: 0
- Semantic outputs: 0
- DEVELOPMENT semantic calls: 0
- Retrieval calls: 0
- Phase 2H HELD_OUT access: false
- Phase 2G private HELDOUT access: false
- Fresh V2 semantic suite: NOT YET AUTHORED
- V2 candidate: PRE_REGISTERED_NOT_EVALUATED

## Capability boundary

- LMFE import/API compatibility: ESTABLISHED
- LMFE exact-schema structural qualification: FAILED
- LMFE required-field enforcement specifically: NOT_ASSESSED
- LMFE Transformers integration qualification: NOT_RUN
- LMFE/Qwen decoder capability: NOT_ASSESSED

TRANSFORMERS STRUCTURAL SMOKE NOT AUTHORIZED

The mandatory pure-parser gate did not complete successfully. No Qwen generate budget was spent, and no Transformers smoke was begun.

## Owner-finalization activity and historical preservation

During owner finalization only this administrative record changed. Network activity, package mutation, real parser execution, extended probes, tokenizer loads, model calls, DEVELOPMENT calls, retrieval calls and both HELDOUT accesses were all zero/false. No semantic suite was authored.

All saved A2.1-G artifact hashes matched before this administrative edit. The helper and tests remain byte-identical to their execution-source receipt. All 57 F/FR historical receipt hashes were independently verified. Historical tracked Git state outside the established 28-file A2.1-G candidate is unchanged, covering A2.1-FR, A2.1-F, A2.1-E, XGrammar diagnostic, XGrammar Attempt 2, R2, R1, A2.1 Attempt 1, V2 preregistration, V1 qualification, runtime freeze, B3, B2, benchmark, retriever, policy corpus and deterministic engine. No benchmark/private contents were inspected or rehashed for this finalization.

## Administrative hash provenance

Previous freeze-record SHA-256: 839574ae4b16d5ed5e8eb7085dc80c1e9015742a820a0313b608145439aae454

The original ARTIFACT_SHA256.json is preserved byte-for-byte at SHA-256 15fd4b0b4e4a647d91e59fbb1759337fab8c83763fd0e340558db52c6fae96cc. Its entry for this freeze record identifies the earlier CANDIDATE_AWAITING_OWNER_REVIEW snapshot and is superseded for the final administrative record. All its other artifact/source entries remain current and verified. The outcome, report and integrity artifacts remain original pre-owner snapshots; this record supplies the authoritative owner-reviewed status without rewriting scientific evidence.

The final freeze-record SHA-256 is computed externally and reported in the completion response, avoiding a circular self-hash requirement. All other final artifact hashes are:

```text
15fd4b0b4e4a647d91e59fbb1759337fab8c83763fd0e340558db52c6fae96cc  ARTIFACT_SHA256.json
06409b2d6e94551db4dca3715fd8231a523d7ca6a7808e21963b228cb1d3c54e  CHANGED_FILES.json
992d5959789d81da2822b5995e83eb548332f50eb786ec4f8b765025ff127d68  CORE_CONFORMANCE_FIXTURES.json
22e113d1dcbfd7903adde6e9dc3d660afc2903e20423a2abd1ec69899a345f9b  CORE_CONFORMANCE_RESULTS.json
ee931c4851ec617f0b3295204de99cb39b6aa2ba037995ae81bb60d2eb84ece5  CRITICALITY_ASSESSMENT.json
9a84ee1f066aae1555197a82257a81cd5d52bb41689cf44d6fd97b3fb7149e83  EXECUTION_PROCESS.json
2c730ea791e975700193624dfee7d508e197b4ac674848c371e11cd36e0e7646  EXECUTION_SOURCE_RECEIPT.json
b23eb615192168489c1625768f388bb2c2869df79c5bc06bed8b4a1cca589f52  EXTENDED_CONFORMANCE_PLAN.json
6f064b1c5efb82fcaf90632fde0d53084e8743ca113674c0e94d0d85167a6f98  EXTENDED_CONFORMANCE_RESULTS.json
033438e69f8064cfce327931b37c56b363c909e3646746959e5c17766c152ffc  FINAL_INTEGRITY_VERIFICATION.json
a587399298977ac9b819486d813a533a27093b8cead25246e4fcfcc75c9abd6f  HISTORICAL_INTEGRITY_RECEIPT.json
7598d961aebcbc1e49611f6706c9b00427c4b35d5861ba6d59295499717c3d4b  LMFE_STRUCTURAL_CONFORMANCE_JOURNAL.jsonl
2591b1675d49e01ef305dfb8c6304e808140abe89f09479fed8b5b564ce4516e  LMFE_STRUCTURAL_CONFORMANCE_OUTCOME.json
c2973f5b1bd45de4bf156505ae3acb76402e6078b94c6ab7f853039dffbbda38  LMFE_STRUCTURAL_CONFORMANCE_PROTOCOL.md
b2bb867bbf814df55b45904668f39aa4d4f681b131e462a555b183387c0ac6c1  LMFE_STRUCTURAL_CONFORMANCE_REPORT.md
10f42b17d0c1d07133f8f0704789a614f8926083d70d4793852444c47d723719  MATERIAL_SCHEMA_FEATURE_MATRIX.json
7e30c986fc913539d3f38e6017cf74264448392e0afca8c5e0e419ee94c7e274  OFFLINE_TEST_RESULTS.json
cbb4baed5d6402a8d8e3e379f8d313566dc587d49df4d27314e06e9411c628b5  PARSER_CONFIGURATION.json
00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d  POST_VALIDATION_PACKAGE_INVENTORY.json
1d56a882a8ad6529b27140946b1070a0783ce4051b49024a88b070628f99fcf9  POST_VALIDATION_PIP_CHECK.json
00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d  PRE_VALIDATION_PACKAGE_INVENTORY.json
d289fae162386793d42eb9a9e1325da691e6b4b026dafffac9f686495f08aef8  RUNTIME_OBSERVATIONS.json
fc2dd87b0ccb03b72db0b5104c56e153129fc452a1a5943106000d74a3f852d4  SCHEMA_PARSER_TRIANGULATION.json
6e82fd86e4ea8d98eef47327d4d4ea362f2b0e795ef76c16728a2a412a974a70  V2_SCHEMA_KEYWORD_INVENTORY.json
```

Unchanged helper/test source hashes:

```text
45cc57a9534a56fef5834fffd422e618e2bb0574adaed90ac019ab4072d66bc0  gateway/domain/evaluation/answerability/qualify_lmfe_structure.py
7b0675b7b09576dde885d6534847400be23135f7a7f65201e98238cfb94cd2e7  gateway/domain/tests/test_lmfe_structural_conformance.py
```

## Git review scope

The candidate remains exactly 28 files: 25 A2.1-G artifacts, helper, tests and the existing exact artifact-path .gitattributes additions. No historical/private file, wheel, environment, model or cache is staged. The finalization updates only this record within that candidate. No commit or tag is authorized or created.

`git status --short` (same 28-file candidate after staging this administrative update):

```text
M  .gitattributes
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/ARTIFACT_SHA256.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/CHANGED_FILES.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/CORE_CONFORMANCE_FIXTURES.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/CORE_CONFORMANCE_RESULTS.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/CRITICALITY_ASSESSMENT.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXECUTION_PROCESS.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXECUTION_SOURCE_RECEIPT.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXTENDED_CONFORMANCE_PLAN.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXTENDED_CONFORMANCE_RESULTS.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/FINAL_INTEGRITY_VERIFICATION.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/HISTORICAL_INTEGRITY_RECEIPT.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_FREEZE_RECORD.md
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_JOURNAL.jsonl
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_OUTCOME.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_PROTOCOL.md
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_REPORT.md
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/MATERIAL_SCHEMA_FEATURE_MATRIX.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/OFFLINE_TEST_RESULTS.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/PARSER_CONFIGURATION.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/POST_VALIDATION_PACKAGE_INVENTORY.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/POST_VALIDATION_PIP_CHECK.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/PRE_VALIDATION_PACKAGE_INVENTORY.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/RUNTIME_OBSERVATIONS.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/SCHEMA_PARSER_TRIANGULATION.json
A  artifacts/answerability_semantic_v2_lmfe_structural_conformance/V2_SCHEMA_KEYWORD_INVENTORY.json
A  gateway/domain/evaluation/answerability/qualify_lmfe_structure.py
A  gateway/domain/tests/test_lmfe_structural_conformance.py
```

`git diff --cached --name-only`:

```text
.gitattributes
artifacts/answerability_semantic_v2_lmfe_structural_conformance/ARTIFACT_SHA256.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/CHANGED_FILES.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/CORE_CONFORMANCE_FIXTURES.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/CORE_CONFORMANCE_RESULTS.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/CRITICALITY_ASSESSMENT.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXECUTION_PROCESS.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXECUTION_SOURCE_RECEIPT.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXTENDED_CONFORMANCE_PLAN.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/EXTENDED_CONFORMANCE_RESULTS.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/FINAL_INTEGRITY_VERIFICATION.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/HISTORICAL_INTEGRITY_RECEIPT.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_FREEZE_RECORD.md
artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_JOURNAL.jsonl
artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_OUTCOME.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_PROTOCOL.md
artifacts/answerability_semantic_v2_lmfe_structural_conformance/LMFE_STRUCTURAL_CONFORMANCE_REPORT.md
artifacts/answerability_semantic_v2_lmfe_structural_conformance/MATERIAL_SCHEMA_FEATURE_MATRIX.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/OFFLINE_TEST_RESULTS.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/PARSER_CONFIGURATION.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/POST_VALIDATION_PACKAGE_INVENTORY.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/POST_VALIDATION_PIP_CHECK.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/PRE_VALIDATION_PACKAGE_INVENTORY.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/RUNTIME_OBSERVATIONS.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/SCHEMA_PARSER_TRIANGULATION.json
artifacts/answerability_semantic_v2_lmfe_structural_conformance/V2_SCHEMA_KEYWORD_INVENTORY.json
gateway/domain/evaluation/answerability/qualify_lmfe_structure.py
gateway/domain/tests/test_lmfe_structural_conformance.py
```

Stop for final owner verification. Do not begin Transformers smoke.
