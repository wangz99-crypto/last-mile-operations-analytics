# A2.1 decoder qualification freeze record

Review status: **OWNER_REVIEWED / DECODER_QUALIFICATION_BLOCKED**
Owner: **Zhe Wang (Victor)**
Owner approval date: **2026-10-10**
Scientific owner review: **PASS — BLOCKED OUTCOME ACCEPTED**
Candidate: **SEMANTIC_MATERIAL_SUPPORT_V2**
Decoder target: **xgrammar==0.2.8**
Decoder capability: **NOT_ASSESSED**
Outcome: **DECODER_QUALIFICATION_BLOCKED**
Base commit: `4c3d715ccf4f2026387ebf5599f36f7e234081f1`.
The blocked Attempt 1 outcome is owner-reviewed. Decoder is not qualified.
V2 semantic capability remains NOT_ASSESSED.
Missing required dependencies: apache-tvm-ffi>=0.1.11; pydantic.
No install/import/model/smoke execution. Fresh V2 qualification suite NOT YET AUTHORED.

## Owner-approved interpretation

This is an infrastructure/dependency enablement blocker, not a decoder capability
failure. The authorized XGrammar wheel was successfully acquired and verified, but
installation was not permitted because two declared required dependencies were absent
from the frozen runtime: `apache-tvm-ffi>=0.1.11` and `pydantic`. The phase protocol
required owner authorization before choosing versions for new dependencies. The run
therefore stopped before package installation; no XGrammar functional failure was observed.

Wheel: `xgrammar-0.2.8-cp312-cp312-win_amd64.whl`; size: 1115212 bytes.
Wheel SHA-256: `dbcf6718e049cbe429742cdb05f85c48135c2e389d45daeafb884af6994bb4a7`.
Runtime target unchanged: Qwen/Qwen2.5-1.5B-Instruct, revision
`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`; Python 3.12.10, Windows AMD64,
CPU, FP32, quantization NONE. Pre-install and final package inventories are identical.
All frozen package versions and V2 scientific artifacts remain unchanged.

XGrammar installed = false.
XGrammar import/API qualification = NOT_RUN.
V2 schema compilation = NOT_RUN.
HF LogitsProcessor integration = NOT_RUN.
Structural smoke suite authored = false; structural smoke config authored = false.
S1 = NOT_RUN; S2 = NOT_RUN; S3 = NOT_RUN.
Model initialization = 0; generate calls = 0; forward calls = 0;
decoder inference calls = 0; timeout count = 0;
execution-time infrastructure failures = 0; quality retries = 0;
infrastructure retries = 0; DEVELOPMENT semantic calls = 0;
retrieval calls = 0; alternate decoder attempts = 0; HELD_OUT access = false.
Fresh V2 semantic qualification suite remains NOT YET AUTHORED.

Attempt 1 network use was limited to sole-target release metadata/wheel acquisition:
XGrammar wheel downloads = 1; model downloads = 0; model network inference = 0;
alternate decoder downloads = 0. Finalization new network calls = 0;
finalization downloads/installations/model calls = 0.

Saved wheel metadata, dependency receipt, both package inventories and the phase
protocol reproduce DECODER_QUALIFICATION_BLOCKED offline. No qualification was resumed.
Only this freeze record changes for owner finalization; authoritative attempt artifacts
retain the hashes below. No other artifact requires this record's final hash.

| Artifact | SHA-256 |
| --- | --- |
| DECODER_DEPENDENCY_RECEIPT.txt | `d7431020413789aca461e51222d346f3591897c752fbe6723f6573db7f618797` |
| DECODER_IDENTITY.json | `6693e16e63f781f33f0a967d61f3389c76a33d0f5e32fb3acbee4d386c33956b` |
| DECODER_QUALIFICATION_JOURNAL.jsonl | `a6ccaa6a12ed69e55da962534aeddca6ff182cefa1dfcc9519728e0765b7c323` |
| DECODER_QUALIFICATION_REPORT.md | `4bb0c93a9d6926a431c2b884ff9b4133d526b6656d341533061ce774b52c50f3` |
| DECODER_SELECTION_PROTOCOL.md | `c5917499ac62b7a9b961d575328034dbea23e8b06536a46b448f44987600191b` |
| FINAL_PACKAGE_INVENTORY.json | `91cc35b9ba8098207769077085366b42cf059f3316df6d6d06bc647e8af0982d` |
| PRE_INSTALL_PACKAGE_INVENTORY.json | `91cc35b9ba8098207769077085366b42cf059f3316df6d6d06bc647e8af0982d` |
| RAW_STRUCTURAL_OUTPUTS.jsonl | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| STRUCTURAL_SMOKE_RESULTS.json | `7ea20c339823a8f2c5f6a71b8359e47772b22bb5e92c1b0bf698b63dfbb942bb` |

This record has no self-hash or circular dependency. Suite/config hashes are N/A because
the pre-install blocker stopped qualification before those artifacts were created.
The final record SHA is reported separately. Stop for final owner verification; no commit/tag, dependency installation or qualification resumption.
