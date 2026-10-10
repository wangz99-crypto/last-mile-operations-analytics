# A2.1-R decoder dependency enablement report

Outcome: **DEPENDENCY_ENABLEMENT_FAILED**
Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**
This is an unsuccessful dependency-import validation, not a decoder capability result.

Base HEAD/tag: `36ccd603bd0bfba6ba5359bc39d3e6f4225db184` /
`answerability-semantic-v2-decoder-v0.1-qualification-blocked`; initial worktree clean.
V2 tag resolves to `4c3d715ccf4f2026387ebf5599f36f7e234081f1`.
Owner-reviewed Attempt 1 record SHA remains
`f0884be52d33f27288c3cf176216130ae067add36ae595fa035b2743702c8afc`.
No blocked history, V2 preregistration, V1, B2/B3, benchmark, evaluator/scorer,
retriever, policy corpus or deterministic-engine tracked file was modified.

## Exact enablement performed

Python 3.12.10 / Windows AMD64. Frozen torch 2.14.0+cpu, transformers 4.57.6,
huggingface_hub 0.36.2, tokenizers 0.22.2, safetensors 0.8.0 and accelerate 1.15.0
remain unchanged. All 28 pre-existing packages retain their versions and METADATA/RECORD
identity. Only five authorized packages were added:
annotated-types 0.8.0; apache-tvm-ffi 0.1.14.post1; pydantic-core 2.46.5;
typing-inspection 0.4.4; pydantic 2.13.5, in that metadata-derived topological order.

Existing typing-extensions 4.16.0 was preserved, never downloaded/reinstalled. Its
METADATA/RECORD identity is recorded in both complete inventories and the lock.
Verified mandatory edges: apache-tvm-ffi -> typing-extensions>=4.13;
pydantic -> annotated-types>=0.6.0, pydantic-core==2.46.5,
typing-extensions>=4.14.1, typing-inspection>=0.4.2;
pydantic-core -> typing-extensions>=4.14.1;
typing-inspection -> typing-extensions>=4.15.0; annotated-types -> none.
Optional cpp/email/timezone extras are inactive; no ninja/email-validator/tzdata added.
No unexpected mandatory dependency appeared.

All five exact wheel filename/version/platform/SHA identities and METADATA were verified
before installation. Wheels reside in the recorded external temporary wheelhouse.
DEPENDENCY_PLAN_FROZEN precedes DEPENDENCY_INSTALLATION_STARTED in the append-only journal.
Lock SHA: `6bfdf48fe7268d55656661641a9ebdc28e2582fed53a4ee602af6422d79a7934`.
All five installations used explicit verified local wheels, --no-deps --no-index
--no-cache-dir --disable-pip-version-check; no index resolver, source build or reinstall.
Installed payloads matched 391 wheel member files (excluding install-generated RECORD).
Pre and post pip check both exited 0: No broken requirements found.
Pre inventory SHA: `b8ac490eca8b3ee4dd4e5dacf139f296020627b04ccd2579228d9a0f0891878a`.
Post inventory SHA: `92333d1c105214e8393e82f5423e2b7dee2ba8bbb73a00464285beeab80a8016`.

## Import failure and stopping boundary

Import names came from each wheel's top-level __init__.py path:
annotated_types, tvm_ffi, pydantic_core, typing_inspection, pydantic.
The one dependency-import subprocess exited 1 at tvm_ffi -> torch -> platform.machine()
-> CPython Windows version detection -> subprocess.Popen. The external audit wrapper
rejected every subprocess as a prospective build/helper. This guard was too broad for
ordinary Windows version probing. The saved traceback establishes this wrapper cause;
it does not establish dependency incompatibility. No build was observed executing.

The batch did not emit a completed per-module success/path/version receipt. Modules after
tvm_ffi were not reached; no complete import-success claim is made. Installed versions
and paths can be read from package metadata, but do not substitute for successful imports.
The original stderr and empty stdout are retained in DEPENDENCY_IMPORT_RESULTS.json.
The task classifies post-install import failure as FAILED and forbids repair in the same
run: no guard modification, import retry, alternative configuration or rollback occurred.
All five installed dependencies remain in the environment for owner review.

Saved XGrammar wheel metadata was checked offline after the stop, without import/install:
all six applicable mandatory requirements resolve to installed exact versions:
apache-tvm-ffi 0.1.14.post1, pydantic 2.13.5, torch 2.14.0+cpu,
transformers 4.57.6, numpy 2.5.3, typing-extensions 4.16.0.
This metadata satisfaction does not override the failed import acceptance criterion.
XGrammar installed=false; XGrammar import/API, schema compilation and structural smoke
remain NOT_RUN. No S1-S3 or fresh V2 semantic cases were authored.

## Checks, network and counters

15 focused offline tests passed before installation. One earlier sandbox run passed 14
and errored on temporary-fixture permissions; the identical tests passed 15/15 after
explicit escalation. No model/benchmark tests were executed. Runtime checks verified
exact pins, yanked/wrong wheel rejection, SHA enforcement, dependency closure, preserved
typing-extensions, lock immutability, no-deps/no-index plan, drift checks and decoder absence.

Five unique wheels were acquired. One initial apache-tvm-ffi transfer completed but could
not be saved because a sandbox temporary directory was invisible to the network process.
That unverified in-memory copy was lost. The wheelhouse was relocated outside the repo
before lock freeze; the same exact wheel was acquired again and verified. Total wheel
transfers=6 (apache-tvm-ffi=2; other four=1 each), verified saved copies=5. Six release
metadata fetches and six wheel fetches, all to exact approved PyPI/files.pythonhosted.org
sources; these are high-level acquisition counts, not wire-level redirect telemetry.
No alternate version, XGrammar wheel, model weight, sdist or optional-extra download.
Network installation/inference=0. Source/lock pins never changed due to results.

Qwen initialization=0; generate=0; forward=0; semantic output=0;
DEVELOPMENT semantic calls=0; retrieval=0; HELD_OUT access=false.
Fresh V2 qualification suite NOT YET AUTHORED. Dependency import attempt=1; retry=0;
installation retries=0; package repairs=0. Decoder capability NOT_ASSESSED.

Only new evidence, helper/tests and exact artifact attributes are proposed for staging.
No wheelhouse, wheel, venv, package files, cache, model or credential is staged.
Stop for owner review; no commit/tag and no decoder qualification resumption.
