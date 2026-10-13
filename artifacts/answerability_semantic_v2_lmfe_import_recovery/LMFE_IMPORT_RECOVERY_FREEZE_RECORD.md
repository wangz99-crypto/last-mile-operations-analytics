# A2.1-FR import/API recovery evidence freeze

Review status: **OWNER_REVIEWED / LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE**.
Owner: **Zhe Wang (Victor)**.
Owner approval date: **2026-10-12**.
Scientific owner review: **PASS**.
Outcome: **LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE**.
LMFE import/API compatibility: **ESTABLISHED**.
LMFE structural conformance: **NOT_ASSESSED**.
LMFE decoder capability: **NOT_ASSESSED**.

Base HEAD/tag: `eaad53841caf73ad6933d7a7bf9612cea09376af` /
`answerability-semantic-v2-lmfe-v0.1-enablement-failed`.
Initial worktree clean. Predecessor pre-install tag resolves to
`cfe69ac260fabac26b1b91fb9fec5f2bba5b8ded`.

Starting package count = 36; final package count = 36. Pre/post FR inventories
are **BYTE-IDENTICAL**. The exact starting environment matched frozen A2.1-F.
Pre/post inventory
SHA-256: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`.
interegular==0.3.3 and lm-format-enforcer==0.11.3 remain installed, alongside all
34 pre-existing packages. Additions/removals/version/METADATA/RECORD drift = 0.
Post-validation pip check: PASS. No package mutation or reinstall occurred.

Validation-plan SHA-256:
`b36f44b215af7f28324e4a8b6ba16a6e51f550a66f849739663eaf78ba1b0d2f`.
IMPORT_API_PLAN_FROZEN preceded all child validations. Exact plan and execution
source hashes remained unchanged throughout. I1, I2, A1, A2 and C1 each ran once,
in separate fresh frozen-Python processes, each exit code 0. Retries = 0.
Both package identities and environment-contained module paths passed. Both API
symbols were imported and checked for availability without construction/invocation.

| Preserved validation | Result |
| --- | --- |
| I1 interegular import | PASS |
| I2 lmformatenforcer import | PASS |
| A1 JsonSchemaParser symbol import | PASS |
| A2 build_transformers_prefix_allowed_tokens_fn symbol import | PASS |
| C1 combined import/API validation | PASS |

The imported APIs are lmformatenforcer.JsonSchemaParser and
lmformatenforcer.integrations.transformers.build_transformers_prefix_allowed_tokens_fn.
Prefix-function constructions = 0. Importability does not establish structural
correctness. No additional validation process ran during owner finalization.

The new FR runner observes rather than denies ordinary platform probing. I2/A1/A2/C1
transitively imported torch and reached platform.machine/uname/win32_ver and a
legitimate `cmd.exe /c "ver"` subprocess. A2/C1 additionally recorded local IPv6
socket construction and bind to [::1]:0. Local hostname calls also occurred.
No unexpected subprocess activity beyond legitimate local platform/runtime probing.
No outbound network observations, downloads, package-index or model-network access.
There were five validation children, four local platform subprocesses, and one
administrative pip-check child; this is not an overall zero-subprocess experiment.

JsonSchemaParser constructions = 0; V2 parser constructions = 0; each M1-M8 = 0;
Qwen initialization = 0; tokenizer loading = 0; generate = 0; forward = 0;
semantic outputs = 0; DEVELOPMENT = 0; retrieval = 0;
Phase 2H HELD_OUT access = false; Phase 2G private HELDOUT access = false.
Fresh V2 semantic suite: NOT YET AUTHORED. V2: PRE_REGISTERED_NOT_EVALUATED.
Decoder capability and parser conformance remain NOT_ASSESSED. A2.1-G not begun.

Offline fake-result/AST checks: 10/10 PASS. An initial test-only false positive
(9/10) matched a historical filename used for hashing; the assertion was corrected
before real validation. Both test results are retained. No real import was retried.

A2.1-F remains OWNER_REVIEWED / LMFE_ENABLEMENT_FAILED because its required import
validation was invalidated by guard interference. Its failure classification remains
LMFE_IMPORT_VALIDATION_GUARD_INTERFERENCE: installation succeeded, but required
import/API validation was interrupted by the external guard. FR establishes import/API
compatibility under the corrected boundary; it does not rewrite A2.1-F or establish
schema enforcement. All A2.1-F files/source, earlier historical hashes and Git-tracked
scientific assets remain unchanged. Benchmark question bodies were not inspected.

Five process artifacts and the terminal journal/outcome were already complete when
the conversation resumed. Completion used saved results; no process was restarted.
Final read-only metadata inventory still matched the frozen state.

## Owner finalization and hash provenance

Only this administrative freeze record changed during finalization. All process
outputs, observations, validation plan, journal, outcome, test results, runner/test
source and historical artifacts remain byte-identical. The saved 10/10 PASS result
was checked, not rerun. Saved pre/post inventories and pip-check result were checked;
no live dependency imports, pip checks or package operations were performed.
A2.1-F file/source hashes and 87 earlier non-benchmark historical hashes were
reverified offline. All other historical tracked scientific assets remain unchanged.

Finalization activity: network calls = 0; downloads = 0; package installs = 0;
package uninstalls = 0; package repairs = 0; package mutation = 0;
real import/API validations = 0; parser constructions = 0; model calls = 0.
No DEVELOPMENT or HELD_OUT access. No tokenizer loading, prefix-function
construction, M1-M8 execution, Qwen initialization or A2.1-G work.

The original FINAL_SHA256.json remains unchanged, SHA-256:
`eb5820b489823d8508fa7add2a7a1de90863107eabbc4c7b4d927cfdaa1c95fc`.
Its original freeze-record hash
`32de9d672233016347f4ae39cab404a471a819919b73510415819dd42537c885`
is superseded only by the final owner-record SHA reported at completion. Every
other receipt entry remains valid. This record does not hash itself, avoiding a
circular requirement. Pre-review labels in other unchanged artifacts are historical;
this owner record is the authoritative final review status.

Helper source SHA-256:
`110f64ea2d01bc3532f4d53c4d4fcf7ec1544f81970dd03c75a52aec526764d7`.
Test source SHA-256:
`11eb0df7aca33555ce3badc69c9a7168e9e361f35d36dc219652f846bb6ed7bf`.

Python source/tests retain normal text attributes. No wheel, venv, cache or model
file is staged. No commit or tag. Owner finalization is complete; no A2.1-G or
further import/API validation is authorized by this record.
