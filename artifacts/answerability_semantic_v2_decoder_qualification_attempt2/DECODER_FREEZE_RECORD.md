# Attempt 2 decoder freeze record - final owner review

Status: **OWNER_REVIEWED / DECODER_QUALIFICATION_FAILED**.
Owner: **Zhe Wang (Victor)**.
Owner approval date: **2026-10-11**.
Scientific review: **PASS — FAILED ATTEMPT ACCEPTED WITH EXECUTION-CONFIG DEVIATION**.

Formal protocol outcome: **DECODER_QUALIFICATION_FAILED**.
Scientific interpretation: **FAILED ATTEMPT WITH EXECUTION-CONFIG DEVIATION**.
Clean decoder capability judgment: **NOT_CONCLUSIVE**.
Execution integrity: **NONCONFORMING_CONFIG**.
Specific deviation: **repetition_penalty 1.1 executed instead of frozen 1.0**.

**DECODER CAPABILITY NOT CONCLUSIVELY ASSESSED BY A CLEAN FROZEN-CONFIG RUN**.

The attempt formally failed structural acceptance, but the result is not sufficient
for a clean decoder-capability conclusion because the executed generation
configuration deviated from the frozen configuration. This record is the final
owner-reviewed interpretation; earlier reports and summary files are preserved as
pre-review historical evidence and do not override this interpretation.

Base commit: `4fea18a9c70b1b9536dd92d7f1a118ac3e02a32f`.
Base tag: `answerability-semantic-v2-deps-v0.2-imports-validated`.
No relabeling as qualified, no new commit or tag.

## Preserved structural results

| Case | JSON | Frozen schema | Adapter |
| --- | --- | --- | --- |
| S1 | PASS | FAIL | FAIL |
| S2 | PASS | FAIL | FAIL |
| S3 | PASS | FAIL | FAIL |

Structural acceptance: **0/3**. All three outputs omitted `decision`,
`policy_context_status`, and `reason_code`. Their original text and token records
remain unchanged. No missing fields were added, and no JSON was repaired.

## Configuration deviation and limits of interpretation

Frozen repetition_penalty = **1.0**.
Executed repetition_penalty = **1.1**.

This was an unauthorized deviation from the frozen structural-smoke execution
configuration. No rerun or parameter correction occurred after observing the result.
The attempt must not be treated as a clean decoder-capability qualification.
A causal relationship between this penalty deviation and the missing fields has
not been established. This result does not establish that XGrammar cannot enforce
the V2 schema. The exact grammar/integration behavior has not yet been independently
diagnosed. No such diagnosis was conducted during finalization.

## Preserved infrastructure evidence

XGrammar installed version = **0.2.8**.
Saved dependency state = **intact**; pre-existing package drift = **0**.
Saved pre-install, post-install and final pip check = **PASS**.
XGrammar import/API = **PASS**; tokenizer integration = **PASS**.
Exact schema compilation step = **completed**.
HF LogitsProcessor construction/integration step = **completed**.
These completed steps alone do not establish that runtime masking behaved correctly
while generating. The saved native oneOf/anyOf warning remains evidence, not a
conclusive diagnosis of decoder capability or of the missing-field cause.

All 33 prior package identities were preserved; the sole addition was XGrammar.
The post-install and final 34-package inventories remain byte-identical. No package
operation, real import validation, schema compilation or HF integration was rerun
for this administrative finalization. Previous non-model test results remain
114/114 PASS before generation and 114/114 PASS afterward; no tests reran here.

## Preserved call counts and quarantine

Model initialization = **1**; generate calls = **3**.
Retries = **0**; timeouts = **0**; unauthorized additional calls = **0**.
Additional finalization model initialization/generate calls = **0**.
DEVELOPMENT semantic calls = **0**; retrieval calls = **0**.
Phase 2H HELD_OUT access = **false**.
Phase 2G private HELDOUT access = **false**.
Fresh V2 semantic qualification suite = **NOT YET AUTHORED**.
No semantic accuracy scoring, output repair, schema/decoder modification or fresh
semantic suite was performed. Finalization network/download/package changes = **0**.

## Administrative finalization and source integrity

Only this administrative freeze record changes during finalization. All three raw
outputs, smoke config/suite, qualification results, model-call journal, package
inventories, API/schema/HF evidence, runner/tests and other artifacts retain their
pre-review hashes. This was verified against all entries of the pre-review hash
receipt before editing; after editing, only this record may differ.

Historical frozen repository sources remain unchanged relative to the base, except
the already staged narrow .gitattributes additions and new Attempt-2 source/tests
and evidence. The execution-critical sources below are preserved byte for byte.
This administrative operation reads saved evidence only and does not invoke runners,
tests, XGrammar, Transformers, a model, retrieval or benchmark loaders.

## Hash provenance

`FINAL_SHA256.json` remains the unmodified pre-owner-review receipt. Its SHA-256 is
`1e0ab553e0e96002a5cd7e68b801a1f4771d8f52d1f394533bf760f84456a1ab`.
Its DECODER_FREEZE_RECORD.md entry
`67bbec377c327fb0e697e7a3cf51bb980f708c43ebcedfb6143828ec60448a81`
identifies the superseded pre-review record, not these finalized bytes. Every other
receipt entry still matches. The finalized record SHA is reported separately in the
completion response; this record contains no self-hash and creates no circular hash
requirement. No other artifact explicitly requires an owner-review reference update.

All unchanged artifact and execution-source identities follow. The FINAL_SHA256.json
entry is included separately from its own contents.

| Path | SHA-256 |
| --- | --- |
| `.gitattributes` | `af19f58bd95fc12510b755bfba278092ba51f99c367a293c7abeff4b88e1f7ec` |
| `CHANGED_FILES.json` | `fd61ad80196367dee0ec2c9fcf8f01bc6f7f371664947b3cb02d5e4c304e67c0` |
| `DECODER_API_RESULTS.json` | `485cf80560a3c1deac82f8acff77cbe58ddc6adbf1f65a62e36eb40eac0edaf7` |
| `DECODER_IDENTITY.json` | `dd498ef0c043a134f39fbc53f50dd6922fb4458bcd30b6a012f878a899fdf5f0` |
| `DECODER_QUALIFICATION_JOURNAL.jsonl` | `9a728a44d912b7334e224aa20e93d7bc317c051eadcde564dd913d185ec4f3f8` |
| `DECODER_QUALIFICATION_PROTOCOL.md` | `dbbb3e3d4cb0b522802bd1bca7b6ddb00129e6975f78f2c32856c5da4c06f4af` |
| `DECODER_QUALIFICATION_REPORT.md` | `d2aac4ce58faebae90a93b60a17d4d35493169a4f074909bc228e13a57355568` |
| `EFFECTIVE_GENERATION_CONFIG.json` | `714d86ccd4838d37174cfd0d771bac03d315afd310fd90a66673dc89e461e5a0` |
| `EXECUTION_CONFIG_CONFORMANCE.json` | `91fb2163fcf5d1943b111d6f7db31d2537455a12764ed799e7bca822d5211c2e` |
| `EXECUTION_SOURCE_RECEIPT.json` | `d7a13ca5d2fad08f39185e20f3c521568d6d86d3c95309587e259e9331477305` |
| `FINAL_PACKAGE_INVENTORY.json` | `cdceeb15b9185ebd2cb102202b1fa738cf4ddd6f13b2aee95278672f6dfcbf62` |
| `FINAL_PIP_CHECK.json` | `65861dea5f37f05143b7b53a691d59b4b07e0953a7145ba7f98e6091950eb1f9` |
| `FINAL_SHA256.json` | `1e0ab553e0e96002a5cd7e68b801a1f4771d8f52d1f394533bf760f84456a1ab` |
| `FROZEN_V2_VERIFICATION.json` | `c83e6b5eb8de19b8ef2e5760f541b0893146f3da89e37f34b41d092fedce0b4a` |
| `FUNCTIONAL_PROBE_PROCESS.json` | `7ae73d60be0322fc33808f9cb1f70c65d08d9411bcc36050537065c41249fd86` |
| `GENERATION_OBSERVATIONS.json` | `80317041c60b3b63dfbb3ac8d611e7455f8990ac80d9ce400d4330ba4311f88f` |
| `GENERATION_PROCESS.json` | `3b5470deb31b4ecfce97acf2588e1908979a918a3d8df8f9dfb5c52b52b82271` |
| `HF_INTEGRATION_RESULT.json` | `a59c629a28802971f12137a33af253569fb7a316eace1f58f413752bb966da31` |
| `HISTORICAL_INTEGRITY.json` | `b18136a8317bf80fb557520889b5cbb22efd7c6032fe13a0d96e2448729674e6` |
| `INSTALLED_PACKAGE_INTEGRITY.json` | `738ed6a5b262b1d69156a8021d5c80319ce0d26aab715c3925e79afbbf9fe346` |
| `INSTALL_RESULT.json` | `a59213c9ec42892aba5f2acff4f738d7e99a29bf7e6acd2737608e7fa7129310` |
| `MODEL_FILE_VERIFICATION.json` | `bc11edd5233f6cdb4727219b46aa2e4a135a82860374e34ba8530649168cf07f` |
| `MODEL_INITIALIZATION_RESULT.json` | `e4e401833a345aee0b44ec27d3bfffeb5d5be1f2bba7b4844d3f612d2a3907ab` |
| `POST_GENERATION_TEST_RESULTS.json` | `63a366f3df7e4ffeb0f0904e906f02893630193de2cebc787d05946f6b447189` |
| `POST_INSTALL_PACKAGE_INVENTORY.json` | `cdceeb15b9185ebd2cb102202b1fa738cf4ddd6f13b2aee95278672f6dfcbf62` |
| `POST_INSTALL_PIP_CHECK.json` | `65861dea5f37f05143b7b53a691d59b4b07e0953a7145ba7f98e6091950eb1f9` |
| `PRE_GENERATION_TEST_INITIAL_RESULT.json` | `4d8b016e0e2ca3818c675ebebb61ae5eb43878c87ecafc6a44ce7f0d2a4a88cf` |
| `PRE_GENERATION_TEST_RESULTS.json` | `e04ebe7256c744480ae2cab56623819ee278ffa4e03e8e781216c6c7ad73d35e` |
| `PRE_INSTALL_PACKAGE_INVENTORY.json` | `92333d1c105214e8393e82f5423e2b7dee2ba8bbb73a00464285beeab80a8016` |
| `PRE_INSTALL_PIP_CHECK.json` | `65861dea5f37f05143b7b53a691d59b4b07e0953a7145ba7f98e6091950eb1f9` |
| `PROBE_OBSERVATIONS.json` | `46517fab885afed8f58f1593ed23f963a4fcf9373ea28dfb3b3320da9f6bd314` |
| `QUALIFICATION_SUMMARY.json` | `dd933c2c9c4d094b16f3a617e877c45d35c2932d5cb57a05e268b62d4e71870f` |
| `RAW_STRUCTURAL_OUTPUTS.jsonl` | `330e8a9d08e4f78b8ac3fb98cc301afba238b86f2805654a4fb8ea09b235d036` |
| `SAVED_RESULT_RECOMPUTATION.json` | `8b16a17c63c5c04c410513cc4217d639f9e36c4239aee0da6b489adc942009bd` |
| `SCHEMA_COMPILATION_RESULT.json` | `cbbf1917d6dfe1d8ca307a853855757c20ddaba82f5fda0a8040286d99014dcb` |
| `STRUCTURAL_FAILURE_AUDIT.json` | `232d4c5db7c6d686504d64d51a410fb194895f2184b940f8271dfb1bbf4e24ee` |
| `STRUCTURAL_SMOKE_CONFIG.json` | `0bbedc2f2ad1165d04cb12f8a738378fcef466e5bf9d2013ee4ddded59bc6e61` |
| `STRUCTURAL_SMOKE_RESULTS.json` | `6b2996cfc395d518798dcdfa4709ac7fb75b822eaab4572b33214b5e37e21a56` |
| `STRUCTURAL_SMOKE_SUITE.json` | `43e241c3923d6d814bd1d8f29790a52bb690805fb3066b4f96b4d4e213718d2b` |
| `TOKENIZER_INTEGRATION_RESULT.json` | `6e85edcfc388d62df641b28a35601f2e1233ac2d83031554a0cb5b9b1ed9f8b6` |
| `WHEEL_CUSTODY.json` | `733c6732e7608655e587b0bdaaafb9331a843f5e8cd53c05cff2db7d3f86ac02` |
| `gateway/domain/evaluation/answerability/xgrammar_v2_decoder.py` | `2d7aef05951544a4ac99c7a49b6c614a711691077f323d6b7e1d2de350f4f07b` |
| `gateway/domain/evaluation/answerability/xgrammar_v2_smoke.py` | `ffe40fc052f6c25484d0abdf60411c1317873c1965e38c94860d6c88781181f9` |
| `gateway/domain/tests/test_xgrammar_v2_decoder.py` | `4e846070e2c0e0955720b0d7373165b316984954121893687bdc251b536e8c61` |

No commit. No tag. No decoder qualification rerun. Stop after final owner-review record and Git verification.
