# A2.1-GD owner-reviewed localization freeze record

Status: OWNER_REVIEWED / LMFE_SCHEMA_SHAPE_INCOMPATIBILITY_ESTABLISHED

Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-13
Scientific owner review: PASS
Primary localization outcome: LMFE_SCHEMA_SHAPE_INCOMPATIBILITY_ESTABLISHED
Evidence confidence: ESTABLISHED

Implementation suitability: LMFE 0.11.3 suitability for exact frozen V2 schema = REJECTED

## Frozen scope and identity

Implementation: lm-format-enforcer==0.11.3
Base commit: bc8b6371e84b0a98662ab3eaf12183b232f04213
Base tag: answerability-semantic-v2-lmfe-v0.3-structural-conformance-failed
Predecessor tag: answerability-semantic-v2-lmfe-v0.2-imports-validated
Predecessor target: 8ccdacedd1b47de0471b534ac0b0e786e2c36299

Exact frozen V2 schema SHA-256: 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e
Frozen probe-plan SHA-256: 8afee1ca31501111ad8107567282e083359c77bc2cd3b87a911abcda54bc1074

This disposition is specific to LMFE 0.11.3, the exact frozen V2 schema, frozen parser configuration and recorded runtime. It does not establish that LMFE generally cannot support oneOf or allOf. Schema bytes and settings remain unchanged. No explicit type was added, oneOf flattened, allOf rewritten, or LMFE-compatible dialect created. Such an adaptation would be a separately preregistered candidate/schema architecture.

## Immutable A2.1-G history

A2.1-G remains permanently OWNER_REVIEWED / LMFE_STRUCTURAL_CONFORMANCE_FAILED.
Primary failure: PARSER_TRAVERSAL_UNSUPPORTED_TYPE_NONE.
M1-M8 parser construction: PASS for every case.
M1-M8 traversal: ERROR: Unsupported type None for every case.
Successful structural adjudications: 0/8.
Required-field enforcement capability: NOT_ASSESSED.

G freeze-record SHA-256 remains 29e0fffca5e5c965dd31d7b4cc479441d1f8d94506a911ae124ecdd28074c883. GD localizes G's failure; it does not rewrite G, credit errors as REJECT, or retrospectively claim required-field enforcement was evaluated.

## Established primary path

```text
exact frozen V2 schema
-> oneOf branch processing/merge
-> branch-local material_asks schema retained
-> branch definition lacks explicit type
-> parent material_asks type: array is not available in that dispatch node
-> parser reaches material_asks value after colon
-> LMFE dispatch receives type=None
-> jsonschemaparser.py get_parser failure at line 269
-> Unsupported type None
```

Offending branch-property pointers:

- /oneOf/0/properties/material_asks
- /oneOf/1/properties/material_asks

The parent typed-array definition is /properties/material_asks. LMFE's _merge_object_schemas copies only missing properties; it does not incorporate the parent property's type into an already-present branch-local definition. ObjectParsingState dispatches that retained definition at the material_asks colon.

Exact installed source: C:/Users/zhewa/.virtualenvs/llm-rag-semantic-qwen25-1p5b/Lib/site-packages/lmformatenforcer/jsonschemaparser.py
Source SHA-256: 6bc4a8a10621c6d38d70ebb5ae1dc21aaa98c0454a2e80be1896586f10dccf94

- _merge_object_schemas: lines 162-172; existing-property check at lines 167-168.
- oneOf processing: lines 205-210.
- ObjectParsingState.add_character property selection/dispatch: lines 339-353.
- get_parser terminal exception: line 269, `raise Exception("Unsupported type " + str(value_schema.type))`.

Saved G error-position context, frozen source inspection, D14 minimal reproduction and T03/T04 unchanged subtree probes establish this path. Site-packages were not changed and no probe was rerun during finalization.

## Independent allOf incompatibility

An item-level allOf conditional subtree independently reproduces Unsupported type None. Exact pointers are /properties/material_asks/items and /properties/material_asks/items/allOf/0. LMFE dispatches the allOf child before the parent explicit object type; the conditional-only child has no dispatchable type. D11/D12 and T06/T07/T11 preserve the evidence.

Primary G first-failure path = oneOf/material_asks path.
Independent additional incompatibility = allOf conditional subtree.

The allOf finding is independently ESTABLISHED as an incompatible shape, but is not claimed to have caused G's first observed colon failure. That failure occurred before the array-item path was reached. The original diagnostic primary outcome remains unchanged.

## Project-helper finding

PARSER_DRIVING_HELPER_DEFECT = NOT_ESTABLISHED

The project helper passed the parsed frozen schema structure without project-side structural rewriting. The frozen factory directly passes JsonSchemaParser(json.loads(SCHEMA.read_bytes()), config=None). Diagnostic constructor-entry hashes matched all frozen probe argument structures, and all 26 input dictionaries remained structurally unchanged after their library calls.

Project helper = NOT_CAUSAL for the established type=None schema-shape failures.

No helper repair is authorized or performed.

## Preserved diagnostic evidence

- Schema nodes: 42
- Nodes without explicit type: 36
- Frozen minimal diagnostic probes: 14
- Exact-schema subtree probes: 12
- Total historical GD diagnostic executions: 26
- Target-error probes: 19
- Short-prefix probes not triggering target error: 7
- Probe retries: 0
- A2.1-G reruns: 0
- Extended qualification reruns: 0

The seven non-triggering short prefixes are not structural qualification PASS. No general capability inference is drawn from them. Original plan, probe order, results, journal, dispatch trace and source receipts remain byte-identical.

## Final capability disposition and engineering consequence

LMFE import/API compatibility = ESTABLISHED
LMFE exact-schema parser compatibility = REJECTED
LMFE suitability for frozen V2 structural contract = REJECTED
LMFE Transformers/Qwen qualification = NOT_RUN

A2.1-G recovery using the same LMFE 0.11.3 + exact frozen V2 schema is NOT AUTHORIZED.

Reason: reproducible schema-shape incompatibilities were localized in the decoder implementation, not a project helper defect.

TRANSFORMERS STRUCTURAL SMOKE NOT AUTHORIZED

No Qwen calls should be spent on this decoder/schema combination. No alternate decoder was selected or installed during finalization.

## Counters, quarantine and environment

Tokenizer loads = 0
Qwen/model initialization = 0
Generate = 0
Forward = 0
Semantic outputs = 0
DEVELOPMENT = 0
Retrieval = 0
Phase 2H HELD_OUT access = false
Phase 2G private HELDOUT access = false
Fresh V2 semantic suite = NOT YET AUTHORED
V2 candidate remains PRE_REGISTERED_NOT_EVALUATED.

Saved package count before/after = 36/36
Package additions = 0
Package removals = 0
Version drift = 0
METADATA drift = 0
RECORD drift = 0
Saved pip check = PASS
Saved offline tests = 12/12 PASS
Pre/post inventory SHA-256 = 00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d

These results were verified from saved evidence. No tests, pip check, localization probes or qualification were rerun during owner finalization. Installed LMFE Python source hashes were read-only verified against the saved receipt.

## Historical and finalization integrity

All 82 historical receipt hashes match. Historical tracked Git state outside the established GD candidate is unchanged, covering A2.1-G, FR, F, E, XGrammar diagnostic and Attempt 2, R2, R1, V2 preregistration, V1 qualification, runtime freeze, B3 baselines, B2 evidence, benchmark, retriever, policy corpus and deterministic engine. Benchmark/private contents were not inspected or rehashed for this verification.

Owner-finalization activity: network = 0; package mutation = 0; localization probes = 0; parser qualification reruns = 0; tokenizer loads = 0; model calls = 0. No repair, schema adaptation or decoder installation occurred. Only this administrative freeze record changed.

## Hash provenance

Previous candidate freeze-record SHA-256: a2fc5913a979369f49bfa26329ba34a359fb00365797620193234c9608ccc6bc

The original ARTIFACT_SHA256.json remains byte-identical at SHA-256 fe1fc3751ffe68b300e5aef9c3fa62d6b162141dbabb426e5c75e7925fa9d0d2. Its freeze-record entry refers to the original CANDIDATE_AWAITING_OWNER_REVIEW snapshot and is superseded for this final administrative record. Every other artifact/source hash remains current and verified. Original outcome/report/integrity files retain their pre-owner snapshot status; this administrative record is authoritative for owner approval and suitability disposition.

The final freeze-record SHA-256 is reported externally in the completion response to avoid circular self-hashing. All other final artifact hashes:

```text
fe1fc3751ffe68b300e5aef9c3fa62d6b162141dbabb426e5c75e7925fa9d0d2  ARTIFACT_SHA256.json
7a4e06b45ced8d3d4e62e2d55ff9f61639dc3cd4001e97541aadd1339761a01e  CHANGED_FILES.json
d7b579ab862ef739d7dbe065ac943ee2b2f178021fc3a63a05351c00e5375abc  EXACT_SCHEMA_SUBTREE_RESULTS.json
aca9cddf2e16b1e92f8be94a45c9c98d4e606049582823d371cc96596e8fb17a  EXECUTION_PROCESS.json
02279d957228125618e8fa6a16ae0570ae805cd3c717963de348736a94136be6  EXECUTION_SOURCE_RECEIPT.json
0ed53c68ef7d6c7fdd1ccbce7f724edc795944ba6e85f45175c6adff4e81c312  FINAL_INTEGRITY_VERIFICATION.json
25858f9a783e153341c804ca7eeff404890526b00da7abb5c5bcbb0735ad7597  HELPER_PATH_RECEIPT.json
db455b1e2794cd0ecc0a9ba301883f5a8b00a3f5076e8ccad7a436d548ebcc25  HISTORICAL_INTEGRITY_RECEIPT.json
2597b8a7020d9c4b51118705cb24009f0c813935a2155f32481871ef14210ae8  INSTALLED_SOURCE_RECEIPT.json
8134643b82b842bd706bb6f34eb00660016b0ff4a0d980d2f4532a44c5a276a4  LMFE_DISPATCH_TRACE.json
25b26a2a225d096d7275b81318a319f5e8a351efb306d3cd256c1e69ac49efdb  LMFE_SCHEMA_LOCALIZATION_JOURNAL.jsonl
87ee75d0c8cf462fa664c15c40b2b1fade12f45d0349d2414a1fcc876aa64a3d  LMFE_SCHEMA_LOCALIZATION_PROTOCOL.md
5f44611faf221b9f1b42520d6445e364c571692aef99553f6506eb08e9c032a8  LMFE_SCHEMA_LOCALIZATION_REPORT.md
d48926e37c828cce3d67ba9ee87dbbcfe894900db1e79ca95d7b1e0139e25cc0  LMFE_SOURCE_PATH_ANALYSIS.json
fd93fbedfbb861a0314531b8c9eabcd51eff06ace4b38b150d83fe6df51c7223  LOCALIZATION_OUTCOME.json
8afee1ca31501111ad8107567282e083359c77bc2cd3b87a911abcda54bc1074  LOCALIZATION_PROBE_PLAN.json
b9c7b88e3cd667d447ed49e614de3b356ddd355b30ab7cb80d0ac54c243c2622  LOCALIZATION_PROBE_RESULTS.json
712310866d0ede587ebdf6de8c825c4a2892edb3c8fb9e2c0043b6f9d599e3a9  OFFLINE_TEST_RESULTS.json
cbb4baed5d6402a8d8e3e379f8d313566dc587d49df4d27314e06e9411c628b5  PARSER_CONFIGURATION.json
00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d  POST_LOCALIZATION_PACKAGE_INVENTORY.json
1d56a882a8ad6529b27140946b1070a0783ce4051b49024a88b070628f99fcf9  POST_LOCALIZATION_PIP_CHECK.json
00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d  PRE_LOCALIZATION_PACKAGE_INVENTORY.json
df2f9afd1dd60b8306c6ae41e68982dde682309bd78b93e73b5ed847b27a90c8  RUNTIME_OBSERVATIONS.json
0b49706cc3cde044eec03d023756a72912b64f8f2da73ef12060b9d140bab1d5  SCHEMA_NODE_INVENTORY.json
```

Unchanged execution helper/test hashes:

```text
36083e7a506a41082f8cbb62a82222169f970c66e3bdb7320c2bb75600bd616d  gateway/domain/evaluation/answerability/localize_lmfe_schema.py
415dafa6f90d6e667419bbdbb3df41346492c79946bad7fc867742f8a57f5ee7  gateway/domain/tests/test_lmfe_schema_localization.py
```

## Git review

The candidate remains the same 28 files: 25 GD artifacts, diagnostic helper/tests, and exact artifact-path .gitattributes entries. No historical/private artifacts, wheels, package environment, models or caches are staged. Only this record was updated within the candidate during owner finalization.

`git status --short` (same candidate after staging this administrative update):

```text
M  .gitattributes
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/ARTIFACT_SHA256.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/CHANGED_FILES.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/EXACT_SCHEMA_SUBTREE_RESULTS.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/EXECUTION_PROCESS.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/EXECUTION_SOURCE_RECEIPT.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/FINAL_INTEGRITY_VERIFICATION.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/HELPER_PATH_RECEIPT.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/HISTORICAL_INTEGRITY_RECEIPT.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/INSTALLED_SOURCE_RECEIPT.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_DISPATCH_TRACE.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_FREEZE_RECORD.md
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_JOURNAL.jsonl
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_PROTOCOL.md
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_REPORT.md
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SOURCE_PATH_ANALYSIS.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LOCALIZATION_OUTCOME.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LOCALIZATION_PROBE_PLAN.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/LOCALIZATION_PROBE_RESULTS.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/OFFLINE_TEST_RESULTS.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/PARSER_CONFIGURATION.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/POST_LOCALIZATION_PACKAGE_INVENTORY.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/POST_LOCALIZATION_PIP_CHECK.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/PRE_LOCALIZATION_PACKAGE_INVENTORY.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/RUNTIME_OBSERVATIONS.json
A  artifacts/answerability_semantic_v2_lmfe_schema_localization/SCHEMA_NODE_INVENTORY.json
A  gateway/domain/evaluation/answerability/localize_lmfe_schema.py
A  gateway/domain/tests/test_lmfe_schema_localization.py
```

`git diff --cached --name-only`:

```text
.gitattributes
artifacts/answerability_semantic_v2_lmfe_schema_localization/ARTIFACT_SHA256.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/CHANGED_FILES.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/EXACT_SCHEMA_SUBTREE_RESULTS.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/EXECUTION_PROCESS.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/EXECUTION_SOURCE_RECEIPT.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/FINAL_INTEGRITY_VERIFICATION.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/HELPER_PATH_RECEIPT.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/HISTORICAL_INTEGRITY_RECEIPT.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/INSTALLED_SOURCE_RECEIPT.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_DISPATCH_TRACE.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_FREEZE_RECORD.md
artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_JOURNAL.jsonl
artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_PROTOCOL.md
artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SCHEMA_LOCALIZATION_REPORT.md
artifacts/answerability_semantic_v2_lmfe_schema_localization/LMFE_SOURCE_PATH_ANALYSIS.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/LOCALIZATION_OUTCOME.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/LOCALIZATION_PROBE_PLAN.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/LOCALIZATION_PROBE_RESULTS.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/OFFLINE_TEST_RESULTS.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/PARSER_CONFIGURATION.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/POST_LOCALIZATION_PACKAGE_INVENTORY.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/POST_LOCALIZATION_PIP_CHECK.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/PRE_LOCALIZATION_PACKAGE_INVENTORY.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/RUNTIME_OBSERVATIONS.json
artifacts/answerability_semantic_v2_lmfe_schema_localization/SCHEMA_NODE_INVENTORY.json
gateway/domain/evaluation/answerability/localize_lmfe_schema.py
gateway/domain/tests/test_lmfe_schema_localization.py
```

No commit or tag. Stop for final owner verification. Do not repair this combination, begin Transformers smoke, or select/install another decoder.
