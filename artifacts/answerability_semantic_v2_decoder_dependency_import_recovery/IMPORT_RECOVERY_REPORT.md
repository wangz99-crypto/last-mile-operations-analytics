# R2 dependency import validation recovery report

Outcome: **DEPENDENCIES_ENABLED_AWAITING_DECODER_REQUALIFICATION**
Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**

Base HEAD and tag: `b5ac4a77447849d9fb5adc7427b69e4c3e14a52f` /
`answerability-semantic-v2-deps-v0.1-enablement-failed`; initial working tree clean.
Historical blocked tag remains `36ccd603bd0bfba6ba5359bc39d3e6f4225db184`.
R1 owner record verified at SHA `7a426b0ab5902d1b0751744c5a7a6890b986af7b7ddbff42f49075411146fbe6`.
R1 remains permanently OWNER_REVIEWED / DEPENDENCY_ENABLEMENT_FAILED, classification
IMPORT_VALIDATION_HARNESS_INTERFERENCE. This separate R2 result does not rewrite it.

## Starting state and frozen plan

The complete 33-package inventory exactly matched frozen R1 post-install evidence,
including names, versions and METADATA/RECORD identities. The five new distributions'
391 installed wheel payload files matched the hash-verified frozen wheel files.
All 28 original runtime packages remain unchanged, including typing-extensions 4.16.0.
Python 3.12.10, Windows AMD64; exact executable:
C:/Users/zhewa/.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe.

Import modules were derived from installed distribution files. The new runner does not
reuse/patch the old harness. It observes platform/socket/subprocess activity without
blocking or monkeypatching it. Each child receives only a minimal import script and
module/identity metadata, runs -I -B from the venv root with the saved offline flags,
and has a fixed 120-second timeout. No benchmark/repository/model-loading module is
imported by the child. No temporary script files are used.

Plan SHA: `d38b9159b06210512310d8c7c183cb0748c2e4444712d32a861189571a551308`.
R2_IMPORT_PLAN_FROZEN precedes every import-validation event. Source/script/order/budget
were not changed after freezing. Five independent children run in the order below;
the sixth combined child ran only after all five passed.

## Import results

| Package | Module | Distribution version | Independent | Seconds |
| --- | --- | --- | --- | --- |
| annotated-types | annotated_types | 0.8.0 | PASS | 0.235 |
| typing-inspection | typing_inspection | 0.4.4 | PASS | 0.234 |
| pydantic-core | pydantic_core | 2.46.5 | PASS | 0.391 |
| pydantic | pydantic | 2.13.5 | PASS | 0.312 |
| apache-tvm-ffi | tvm_ffi | 0.1.14.post1 | PASS | 21.422 |

Combined import: PASS, exit 0, 3.172 seconds, same frozen order.
All six exit codes were 0; all stderr streams were empty. Every module path belonged
to the frozen venv and each distribution identity matched its frozen metadata/RECORD.
typing_inspection exposes no module __version__; distribution metadata proves 0.4.4.
Other module versions agree with their distribution versions. Original stdout/stderr,
paths, environment overrides, identity hashes and elapsed times are saved per process.
No genuine failure or traceback occurred. Import-validation processes=6, retries=0,
timeouts=0. The parent post-validation pip check is separate from this six-process budget.

The independent tvm_ffi and combined processes both transitively imported torch.
Both observed legitimate platform.machine(), uname(), win32_ver() and _win32_ver().
No subprocess launch was observed in these R2 children; the prior denied subprocess
path was not artificially reproduced. Each observed one socket.gethostname event;
no DNS resolution, socket connect, bind, external network or download event was observed.
Hostname/platform probing is permitted and is not model/network inference.

## Post-validation integrity and scope

Pre-validation inventory SHA:
`92333d1c105214e8393e82f5423e2b7dee2ba8bbb73a00464285beeab80a8016`.
Post-validation inventory SHA: identical.
Package additions=0; removals=0; version changes=0; METADATA/RECORD drift=0.
Post pip check: exit 0, No broken requirements found.
Saved-result recomputation reproduced all six PASS decisions without importing dependencies
again. Frozen plan/source hashes, event ordering and exact process count verified.
17 deterministic fake/offline harness tests passed before execution. No real dependency
imports were invoked by tests. R1 guard, artifacts and all earlier tracked historical
sources remain unchanged; Git diff checks exclude only new R2 files and exact attributes.

XGrammar installed=false; import=0; schema compilation/HF integration/structural smoke=NOT_RUN.
Qwen/tokenizer/model initialization=0; generate=0; forward=0; semantic output=0.
DEVELOPMENT semantic calls=0; retrieval=0; Phase 2H HELD_OUT access=false;
Phase 2G private HELDOUT access=false. Fresh V2 qualification suite NOT YET AUTHORED.
Network downloads=0; package-index access=0; model network access=0; installs/uninstalls/
upgrades/downgrades/repairs=0. No decoder qualification or semantic capability claim.

Only R2 scientific artifacts, runner/tests and exact artifact -text additions are proposed
for staging. No wheels, caches, venv/site-packages, model files, credentials or temporary
scripts are staged. Stop for owner review; no commit/tag or decoder qualification resumption.
