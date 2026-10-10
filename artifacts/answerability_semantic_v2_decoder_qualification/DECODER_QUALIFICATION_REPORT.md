# A2.1 constrained decoder qualification report

Outcome: **DECODER_QUALIFICATION_BLOCKED**
Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**

Base tag `answerability-semantic-gate-v0.2-pre-decoder` resolves to
`4c3d715ccf4f2026387ebf5599f36f7e234081f1`, equal to HEAD; initial worktree clean.
All three historical tags matched. V2 scientific hashes and final owner record matched
the frozen commit; no V2 preregistration artifact was modified.

## Blocking evidence

The exact authorized `xgrammar-0.2.8-cp312-cp312-win_amd64.whl` was downloaded once
from PyPI/files.pythonhosted.org (1,115,212 bytes). SHA-256:
`dbcf6718e049cbe429742cdb05f85c48135c2e389d45daeafb884af6994bb4a7`.
Its METADATA declares two active requirements absent from the frozen environment:
`apache-tvm-ffi>=0.1.11` and `pydantic`.
The owner's sections 7-8 require stopping rather than choosing missing dependency
versions. No installation was attempted; installed XGrammar/module version is null.
All existing package versions are identical in pre-install and final inventories.
There is no post-install inventory because there was no installation.
No competing decoder/version was inspected, installed or benchmarked.

## Runtime and execution boundary

Python 3.12.10 / Windows AMD64 and all frozen dependency versions verified.
All 10 local model-file hashes verified without initialization:
Qwen/Qwen2.5-1.5B-Instruct, revision
`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`; intended Windows CPU Transformers FP32,
no quantization. Tokenizer files share this snapshot identity; tokenizer was not loaded,
so runtime vocabulary size is NOT_ASSESSED. Chat-template SHA verified:
`cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`.
Frozen V2 schema SHA verified:
`6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.

XGrammar import/API checks, schema compilation and HF LogitsProcessor integration:
NOT_ATTEMPTED. No adapter/runner source was introduced after the pre-install blocker.
Smoke configuration/suite were not created or frozen; their hashes are N/A.
No STRUCTURAL_SMOKE_SUITE_FROZEN, installation, compilation or model events are claimed.

| Smoke | JSON validity | Schema validity | Adapter diagnostic |
| --- | --- | --- | --- |
| S1 | NOT_RUN | NOT_RUN | NOT_RUN |
| S2 | NOT_RUN | NOT_RUN | NOT_RUN |
| S3 | NOT_RUN | NOT_RUN | NOT_RUN |

Model/tokenizer initialization=0; generate=0; timeouts=0; execution infrastructure
failures=0; retries=0. One pre-install dependency blocker, with two missing requirements.
Raw outputs are empty. Structural acceptance=0; invalid outputs=0; Markdown/prefix/suffix
violations=0; these zero counts represent no execution, not structural qualification.
Fresh V2 semantic qualification suite remains NOT YET AUTHORED; capability NOT_ASSESSED.
DEVELOPMENT semantic calls=0; retrieval=0; both HELD_OUT boundaries accessed=false.

## Network, checks and integrity

Only two acquisition requests were made: the exact PyPI 0.2.8 release metadata to
locate the authorized wheel, then its exact files.pythonhosted.org URL. Wheel downloads=1;
dependency/model downloads=0; package installations=0. No inference network access.
The acquisition script is temporary ignored material and is not staged.

Pre-generation decoder tests and post-generation tests: NOT_REACHED because the package
precondition blocked before implementation/initialization. No smoke result recomputation
is possible: there are no generated outputs. Offline receipt verification rechecks the
wheel identity/declared requirements against the saved inventory and reproduces BLOCKED;
empty results/raw-output counts agree. No model rerun.
All preexisting tracked files were unchanged before adding exact new artifact attributes;
final historical diff check excludes only .gitattributes. No old question, case, raw output
or held-out content was inspected. Only new blocked-run evidence and narrow attributes
are proposed for staging; wheel/cache/venv/model/credentials are excluded.

Stop for owner review. A separate owner decision would be required to pin and authorize
missing dependencies. No automatic dependency selection, decoder fallback, commit or tag.
