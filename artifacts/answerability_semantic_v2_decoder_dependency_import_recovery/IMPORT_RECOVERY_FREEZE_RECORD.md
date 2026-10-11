# R2 dependency import recovery freeze record

Review status: **OWNER_REVIEWED / DEPENDENCIES_ENABLED_AWAITING_DECODER_REQUALIFICATION**
Owner: **Zhe Wang (Victor)**
Owner approval date: **2026-10-11**
Scientific owner review: **PASS**
Outcome: **DEPENDENCIES_ENABLED_AWAITING_DECODER_REQUALIFICATION**
Base: b5ac4a77447849d9fb5adc7427b69e4c3e14a52f / answerability-semantic-v2-deps-v0.1-enablement-failed.
Independent imports 5/5 PASS; combined import PASS; six processes; zero retries.
Starting and final environment byte-identical inventories; zero package drift; pip check PASS.
R1 remains OWNER_REVIEWED / DEPENDENCY_ENABLEMENT_FAILED, IMPORT_VALIDATION_HARNESS_INTERFERENCE.
XGrammar uninstalled/unimported; no model activity, retrieval, benchmark access or new suite.
This establishes dependency import compatibility only; decoder capability remains NOT_ASSESSED.

## Owner-approved interpretation and boundaries

A2.1-R installation completed successfully, but its required import validation was
invalidated by the overly broad guard. Its permanent historical status remains
OWNER_REVIEWED / DEPENDENCY_ENABLEMENT_FAILED, classification
IMPORT_VALIDATION_HARNESS_INTERFERENCE. A2.1-R2 corrected import validation established
dependency compatibility without modifying the installed environment. R2 does not
retrospectively change R1 or establish decoder or semantic-model capability.

Exact preserved dependency set: apache-tvm-ffi==0.1.14.post1, pydantic==2.13.5,
pydantic-core==2.46.5, annotated-types==0.8.0, typing-inspection==0.4.4,
typing-extensions==4.16.0. No package changes occurred during finalization.

annotated_types independent import = PASS; typing_inspection independent import = PASS;
pydantic_core independent import = PASS; pydantic independent import = PASS;
tvm_ffi independent import = PASS; combined five-module import = PASS.
Independent import processes = 5; combined import processes = 1;
total validation processes = 6; import retries = 0.

During valid R2 execution, tvm_ffi transitively importing torch was observed.
platform.machine(), uname() and win32_ver() probing were observed and permitted.
Socket.gethostname observations are expected local platform behavior. No network
connection, DNS-resolution request for external access, package-index access or download
was observed. No unexpected subprocess launches occurred inside the import-validation
child processes. The six intentionally isolated child Python validation processes are
part of the experiment; this is not a claim of zero overall child processes.

Starting packages = 33; post-validation package additions = 0; removals = 0;
version changes = 0; METADATA drift = 0; RECORD drift = 0.
391 previously installed dependency payload files verified; pip check = PASS.
The pre/post inventory bytes and hashes are identical. Saved-result reproduction = PASS;
17/17 offline harness tests PASS during finalization, without real import validation.

XGrammar installed = false; XGrammar import calls = 0; schema compilation = NOT_RUN;
HF integration = NOT_RUN; structural smoke = NOT_RUN; decoder capability = NOT_ASSESSED.
Qwen model initialization = 0; generate = 0; forward = 0; semantic outputs = 0;
DEVELOPMENT semantic calls = 0; retrieval = 0; Phase 2H HELD_OUT access = false;
Phase 2G private HELDOUT access = false; fresh V2 suite = NOT YET AUTHORED.

Finalization network calls = 0; downloads = 0; package installs = 0; uninstalls = 0;
upgrades/downgrades/repairs = 0; dependency imports = 0; model calls = 0.
Only saved/offline evidence was used. No real import, model or decoder execution reran.
Only this record changed; all scientific artifacts, runner/tests and historical frozen
sources retain their bytes. No other artifact requires this record's final hash.

| Artifact | SHA-256 |
| --- | --- |
| COMBINED_IMPORT_RESULT.json | `e655007e8577b4cf119305571aec5163d8790d3e7fa560e97272accdf915e1fc` |
| HARNESS_TEST_RESULTS.json | `100869af0939eabecc9ee9b81a114eff8a49f06ac265e1d5e9731d1ab8a07e56` |
| IMPORT_PROCESS_01.json | `9fd0d7a9cb976ad5eaa5102f2b8f105de45e0f15c576e121bec08730aa7f9734` |
| IMPORT_PROCESS_02.json | `bf7d09668481cfa3da22fb88980513336080155d9f99f38c59a62e054fd0257d` |
| IMPORT_PROCESS_03.json | `19346279576b50b3ee462fc259fa0f1799cd3adfdf414c734bc088635dc7f091` |
| IMPORT_PROCESS_04.json | `b68351295c9c1ca701db3755a716686e5d7f0a10cffb9d663b91cdfba02e8e06` |
| IMPORT_PROCESS_05.json | `1b98908ec04220a99ed865aedccd8b5932166b3a9684946deef6394d69d26ad1` |
| IMPORT_PROCESS_06.json | `e655007e8577b4cf119305571aec5163d8790d3e7fa560e97272accdf915e1fc` |
| IMPORT_RECOVERY_JOURNAL.jsonl | `df84c62d5bfc44cba1d6861dc385be7f75d1afe4e99ebe3dacd37f5200c9d643` |
| IMPORT_RECOVERY_PROTOCOL.md | `d73549524db1f4f2df6614fea8b93e629980ef80317087c60b9da6c25ba6d609` |
| IMPORT_RECOVERY_REPORT.md | `e74005710bbd5ce4dd168dc0d2d2fbb3653bfab8436ca4239fe3d07512d71b28` |
| IMPORT_VALIDATION_PLAN.json | `d38b9159b06210512310d8c7c183cb0748c2e4444712d32a861189571a551308` |
| INDEPENDENT_IMPORT_RESULTS.json | `48303fe8b3b510e673c77a9d0a572a2e464a4510c2b2cdeec4a63c03856f235a` |
| POST_VALIDATION_PACKAGE_INVENTORY.json | `92333d1c105214e8393e82f5423e2b7dee2ba8bbb73a00464285beeab80a8016` |
| POST_VALIDATION_PIP_CHECK.json | `65861dea5f37f05143b7b53a691d59b4b07e0953a7145ba7f98e6091950eb1f9` |
| PRE_VALIDATION_PACKAGE_INVENTORY.json | `92333d1c105214e8393e82f5423e2b7dee2ba8bbb73a00464285beeab80a8016` |
| RECOVERY_OUTCOME.json | `dc823ffce3925b52a40236d6851ca4bf61556fbe8dcf836a7e01079945b13f2d` |
| STARTING_ENVIRONMENT_RECEIPT.json | `c2ab2ae8216a982b2b9d7b995a198d0ff2f4c2f302468952c5197642dca5e82f` |

Runner source SHA: `c243d4bf143e43a1cd77a2d609191a17c8019cd0e0c9445f23dc578f228562e5`.
Test source SHA: `4f38fcc5a343f8592d1cf14d9fdb725fa64b097719315c016b28b69b91ccd70f`.
No self-hash/circular dependency. Final record hash reported separately. No commit/tag.
