# Phase 2H-B3.2-A2.1-FR completion report

Outcome: **LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE**.
Review status: CANDIDATE_AWAITING_OWNER_REVIEW.

Base HEAD/tag: eaad53841caf73ad6933d7a7bf9612cea09376af /
answerability-semantic-v2-lmfe-v0.1-enablement-failed. Initial worktree clean.
Predecessor: answerability-semantic-v2-decoder-replacement-v0.1-pre-install ->
cfe69ac260fabac26b1b91fb9fec5f2bba5b8ded.

A2.1-F owner review and LMFE_IMPORT_VALIDATION_GUARD_INTERFERENCE classification
verified unchanged. Its formal FAILED outcome is preserved. FR establishes only
import/API compatibility; no capability or schema-conformance claim is made.

## Fixed process results

| ID | Validation | Result | Exit | Elapsed seconds |
| --- | --- | --- | --- | --- |
| I1 | interegular 0.3.3 import | PASS | 0 | 0.241877 |
| I2 | LMFE 0.11.3 import | PASS | 0 | 19.749436 |
| A1 | JsonSchemaParser symbol import | PASS | 0 | 6.837729 |
| A2 | Transformers prefix symbol import | PASS | 0 | 15.274932 |
| C1 | Combined imports and identities | PASS | 0 | 11.783678 |

Exactly 5 validation child processes, each a fresh process using:
C:/Users/zhewa/.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe.
Cwd: repository root. Environment overrides: PYTHONDONTWRITEBYTECODE=1,
HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, PIP_DISABLE_PIP_VERSION_CHECK=1.
Each artifact includes full stdout/stderr/exit/elapsed time. Distribution identities,
module/API source paths inside the frozen environment, symbol importability and
callability checks passed. The APIs were not instantiated or invoked.
Plan froze and was hashed before I1; all stages respected prerequisite passes.
Import/API retries = 0. No extra diagnostic import or execution after the fifth child.

## Runtime and network observations

I1 did not reach torch or platform subprocesses. I2/A1/A2/C1 imported torch and
recorded platform.machine, uname, win32_ver, _win32_ver and _syscmd_ver, each with
one `cmd.exe /c "ver"` invocation attributed to the platform call stack. Quoted
command lines executed normally. The historical subprocess-denial guard was not
reused or modified. No global socket/subprocess monkeypatch or denial was installed.

No unexpected subprocess activity beyond legitimate local platform/runtime probing.
Five validation children plus four local platform subprocesses were observed; one
additional administrative pip check ran. Do not interpret this as zero subprocesses.
I2/A1/A2/C1 recorded local gethostname. A2/C1 also recorded AF_INET6 socket creation
and loopback bind [::1]:0. These are local probes, not outbound network activity.
No connect/DNS resolution/outbound network observation; downloads = 0,
package-index access = 0, model-network access = 0. Validation code initiated none.
No protected benchmark/model-file opens or scientific calls were observed.

## Environment and historical integrity

Starting and ending complete 36-package identities match frozen A2.1-F exactly.
Additions = 0; removals = 0; version changes = 0; METADATA drift = 0; RECORD drift = 0.
Post-validation pip check PASS: No broken requirements found. Current read-only
inventory checked again at completion without importing dependencies still matches.
No installation, repair, package mutation or dependency selection.

A2.1-F artifact and source hashes unchanged; earlier 87 non-benchmark historical
hashes rechecked. Git tracked-change verification preserves A2.1-E, XGrammar
histories, R2/R1, Attempt 1/2, V2/V1, runtime, B3/B2, benchmark, retriever, policy
corpus and deterministic engine. No benchmark question bodies or private data read.

JsonSchemaParser constructions = 0; V2 parser constructions = 0; each M1-M8 = 0;
Qwen initialization = 0; tokenizer loading = 0; generate = 0; forward = 0;
semantic output = 0; DEVELOPMENT = 0; retrieval = 0; both HELD_OUT access flags false.
Fresh V2 semantic suite NOT YET AUTHORED. V2 PRE_REGISTERED_NOT_EVALUATED.
Decoder capability and parser conformance NOT_ASSESSED. No A2.1-G.

Offline plan/AST/fake-result tests: initial 9/10 with a test-only substring false
positive matching a read-only historical filename; corrected 10/10 before real
validation. No change to the runner or frozen plan after real results. No native
parser qualification tests. Both offline test results are preserved.

When the conversation resumed, the five process files, pip-check result and
RECOVERY_COMPLETE event were already saved. The unavailable old tool session was
not restarted; completion used those saved artifacts and read-only integrity checks.

## SHA-256 identities

- PRE_VALIDATION_PACKAGE_INVENTORY.json: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`
- POST_VALIDATION_PACKAGE_INVENTORY.json: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`
- IMPORT_API_VALIDATION_PLAN.json: `b36f44b215af7f28324e4a8b6ba16a6e51f550a66f849739663eaf78ba1b0d2f`
- IMPORT_API_RESULTS.json: `2c13e2fb419e0d3e85257c0f02e46d048ce7af96809dcba7c43b6a421a9168b4`
- LMFE_IMPORT_RECOVERY_OUTCOME.json: `bf25517ac8805d309533232a2b14647d68de12871a72bf3319cb55409d33da59`
- LMFE_IMPORT_RECOVERY_FREEZE_RECORD.md: `32de9d672233016347f4ae39cab404a471a819919b73510415819dd42537c885`
- gateway/domain/evaluation/answerability/recover_lmfe_imports.py: `110f64ea2d01bc3532f4d53c4d4fcf7ec1544f81970dd03c75a52aec526764d7`
- gateway/domain/tests/test_lmfe_import_recovery.py: `11eb0df7aca33555ce3badc69c9a7168e9e361f35d36dc219652f846bb6ed7bf`

FINAL_SHA256.json lists all artifact/source hashes except itself; its own hash is reported separately. CHANGED_FILES.json is the complete candidate path list. Initial owner status remains CANDIDATE_AWAITING_OWNER_REVIEW. No commit/tag, no staged environment/wheel/cache/model files. Stop for owner review.
