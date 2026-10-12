# Phase 2H-B3.2-A2.1-F completion report

Formal outcome: **LMFE_ENABLEMENT_FAILED**. Review: **CANDIDATE_AWAITING_OWNER_REVIEW**.
Both packages installed; required import/API validation failed under the external
wrapper. Capability remains NOT_ASSESSED; no structural qualification occurred.

Base HEAD/tag: cfe69ac260fabac26b1b91fb9fec5f2bba5b8ded /
answerability-semantic-v2-decoder-replacement-v0.1-pre-install. Initial Git status clean.
A2.1-E remains OWNER_REVIEWED / REPLACEMENT_DECODER_SELECTED_NOT_QUALIFIED.

Schema SHA: 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e.

## Acquisition and dependency validation

Two exact wheels downloaded from files.pythonhosted.org; zero reused. One exact
interegular 0.3.3 PyPI metadata response retrieved; LMFE release metadata reused
from A2.1-E. External wheelhouse:
C:/Users/zhewa/AppData/Local/Temp/phase2h-lmfe-wheelhouse.
No source distribution, alternative release, resolver choice or model download.

- interegular-0.3.3-py37-none-any.whl: SHA-256 `b0c07007d48c89d6d19f7204972d369b2a77222722e126b6aa63aa721dc3b19c` — MATCH.
- lm_format_enforcer-0.11.3-py3-none-any.whl: SHA-256 `cf586350875def1ae7a8fba84fcbbfc8371424b6c9d05c1fcba70aa233fbf06f` — MATCH.

Wheel METADATA (all declared requirements):

- interegular 0.3.3; Requires-Python `>=3.7`; Requires-Dist `[]`.
- lm-format-enforcer 0.11.3; Requires-Python `>=3.8,<4.0`; Requires-Dist `['interegular (>=0.3.2)', 'packaging', 'pydantic (>=1.10.8)', 'pyyaml']`.

Resolved graph: pydantic>=1.10.8 -> existing 2.13.5; interegular>=0.3.2 ->
authorized 0.3.3; packaging -> existing 26.3; pyyaml -> existing 6.0.3.
Interegular declares no dependencies. No unexpected mandatory dependency exists.
Both Python constraints accept 3.12.10.

An initial pre-install helper compared ordered raw dependency strings and falsely
blocked equivalent parentheses/order from wheel metadata. Its failure artifact
was retained; normalized requirement comparison was tested and corrected before
any mutation. The lock then froze exactly once before INSTALL_BEGIN; it has not
changed. This was not an installation or import retry.

## Installation and payload evidence

Commands (each once, in this order):

```text
C:\Users\zhewa\.virtualenvs\llm-rag-semantic-qwen25-1p5b\Scripts\python.exe -B -m pip install --no-deps --no-index --no-cache-dir --disable-pip-version-check C:\Users\zhewa\AppData\Local\Temp\phase2h-lmfe-wheelhouse\interegular-0.3.3-py37-none-any.whl
```

```text
C:\Users\zhewa\.virtualenvs\llm-rag-semantic-qwen25-1p5b\Scripts\python.exe -B -m pip install --no-deps --no-index --no-cache-dir --disable-pip-version-check C:\Users\zhewa\AppData\Local\Temp\phase2h-lmfe-wheelhouse\lm_format_enforcer-0.11.3-py3-none-any.whl
```

Both commands returned 0. Pre/post pip check: PASS, no broken requirements.
Only additions: interegular 0.3.3 and lm-format-enforcer 0.11.3. Package count 34 -> 36.
Pre-existing removals/version changes/METADATA drift/RECORD drift: all zero.
XGrammar 0.2.8 remains installed. Post-import inventory still matches post-install.
Installed payload verification passed for all 11 interegular and 24 LMFE wheel
payload files (wheel RECORD is intentionally replaced by pip's installed RECORD).
Installed hashed RECORD entries also passed digest and size checks. Installer-added
metadata and unhashed RECORD entries are separately listed in the payload receipt.

## Failed import/API validation

One fresh child process. Interegular import PASS. LMFE import FAILED_EXTERNAL_GUARD.
The failure was in torch's Windows platform probe: the wrapper did not recognize
`cmd.exe /c "ver"` with its quoted argument and raised Unexpected import subprocess.
The saved trace and audit observations establish this immediate blocker. No claim
is made that LMFE itself is incompatible or that its schema support failed.
JsonSchemaParser API: NOT_REACHED. Transformers prefix function API: NOT_REACHED.
No wrapper correction, import retry, installation retry, package repair or removal
followed this failure. No additional API probing was performed.
Import observations: local socket.gethostname and attempted OS-version subprocess;
no socket connect/DNS/bind or outbound network operation; no prohibited data open.

## Verification, counts and preserved boundaries

Offline helper tests: initial 14/14 PASS; after pre-install dependency syntax fix,
15/15 PASS. These are deterministic plan/hash/lock/diff/API guard tests only.
They did not detect the quoted command guard limitation. No parser test was run.

Qwen initialization 0; generate 0; forward 0; semantic outputs 0; V2 parser
constructions 0; V2 parser conformance 0; M1/M2/M3/M4/M5/M6/M7/M8 each 0;
DEVELOPMENT access/semantic calls 0; retrieval 0; Phase 2H HELD_OUT false;
Phase 2G private HELDOUT false. Fresh V2 semantic suite NOT YET AUTHORED.
V2 PRE_REGISTERED_NOT_EVALUATED. No A2.1-G. No commit or tag.

All historical tracked files unchanged before exact new .gitattributes additions;
87 saved historical hashes additionally verified. Protected benchmark/private
question contents were not inspected. Git verification covers unchanged A2.1-E,
XGrammar, Attempt 2, R2/R1/Attempt 1, V2/V1, runtime, B3/B2, benchmark, retriever,
corpus and deterministic engine. All new artifacts belong to this directory;
only the new helper/test and exact artifact attributes are added outside it.

## Key SHA-256 receipts

- LMFE_DEPENDENCY_LOCK.json: `b0cb52383361032b83c5b7e05b3397a72a7fcea02f970f1e3811e6105d89856c`
- PRE_ENABLE_PACKAGE_INVENTORY.json: `cdceeb15b9185ebd2cb102202b1fa738cf4ddd6f13b2aee95278672f6dfcbf62`
- POST_ENABLE_PACKAGE_INVENTORY.json: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`
- POST_IMPORT_PACKAGE_INVENTORY.json: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`
- LMFE_INSTALLED_PAYLOAD_VERIFICATION.json: `fba95e315998bce68cbf87e4876bf47c4d2620e30c07b1730749274475bbf1e4`
- LMFE_IMPORT_PROCESS.json: `c03fcaf4baee227814b8e2f42a654e75fde186e53c87752d2eb2513362c38efe`
- LMFE_IMPORT_API_RESULTS.json: `5b5a9b0307262dacd2202016ea282719ea3e92553754b05017bcbaa9f844f1e8`
- gateway/domain/evaluation/answerability/enable_lmfe.py: `0f935eed2064bf028619cd8909b0410532840886e0928d33959364620b2c9346`
- gateway/domain/tests/test_lmfe_enablement.py: `2394fa7b0576cd64c5a86278aaf7c94f6370b8969315410d0b5a8f43960d02e7`

FINAL_SHA256.json inventories all final artifacts and helper/test source hashes; its self hash is reported externally to avoid circularity. CHANGED_FILES.json records the complete candidate path list. Stop for owner review; do not retry imports or begin conformance.
