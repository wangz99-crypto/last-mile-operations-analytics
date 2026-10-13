# A2.1-FR import/API recovery protocol

Base HEAD/tag: `eaad53841caf73ad6933d7a7bf9612cea09376af` /
`answerability-semantic-v2-lmfe-v0.1-enablement-failed`. Initial working tree clean.
Predecessor tag resolves to `cfe69ac260fabac26b1b91fb9fec5f2bba5b8ded`.
A2.1-F remains OWNER_REVIEWED / LMFE_ENABLEMENT_FAILED, classified
LMFE_IMPORT_VALIDATION_GUARD_INTERFERENCE. Historical sources and artifacts are
read-only. No prior guard is imported, patched, or executed by this runner.

Starting state: exact 36-package frozen environment, inventory SHA-256
`00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`.
Compare complete versions and METADATA/RECORD identities before and after. No
installation, removal, repair or package selection is authorized. Decoder capability
and parser conformance remain NOT_ASSESSED regardless of successful symbol imports.

## Immutable execution plan

IMPORT_API_VALIDATION_PLAN.json contains every complete child source, exact frozen
Python path, cwd, offline/bytecode environment overrides, timeout, sequence and
budget. Its SHA is journaled as IMPORT_API_PLAN_FROZEN before VALIDATION_BEGIN.
It cannot change after results. There are at most five fresh validation processes:

1. I1: import interegular; require frozen-environment path and distribution 0.3.3.
2. I2: import lmformatenforcer; require frozen-environment path and distribution 0.11.3.
3. A1, only after I1+I2 PASS: import JsonSchemaParser symbol; do not instantiate.
4. A2, only after Stage A and A1 PASS: import Transformers prefix callback symbol;
   do not call it or load a tokenizer/model.
5. C1, only after A+B PASS: combined imports and identity/symbol checks; no construction.

Any failed/interrupted child stops progression. No retry or extra diagnostic import.
Each process saves executable, cwd, environment overrides, exit code, stdout,
stderr and elapsed time. One administrative pip check follows successful validation;
it is not one of the five import/API validations. No overall zero-subprocess claim.

## Observation boundary

The FR runner does not globally monkeypatch or deny sockets or subprocess APIs.
Audit/profile callbacks record ordinary Windows/runtime probing without interfering:
torch import; platform.machine/uname/win32_ver; quoted cmd.exe /c "ver"; local hostname
and loopback capability probes. Subprocess platform call stacks are recorded to
distinguish OS-version probing from unexpected activity. Observation results are
checked after each child exits, not by invalidating the import with a broad guard.

Code contains no intentional network/download, package mutation, model loading,
retrieval, benchmark access, parser construction or scientific API invocation.
Unexpected network, scientific-call or protected-file observations prevent acceptance.
HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1; bytecode writes disabled. Normal local
probes are not classified as external network access. No model weights are touched.

## Qualification boundaries

JsonSchemaParser constructions = 0; V2 constructions = 0; M1-M8 = 0;
Qwen initialization = 0; tokenizer loading = 0; generate/forward/semantic output = 0;
DEVELOPMENT/retrieval = 0; both HELD_OUT access flags false.
Fresh semantic suite remains NOT YET AUTHORED. No A2.1-G is authorized.

Success requires all five checks, unchanged complete package identity, pip check
PASS, no forbidden activity and zero retries; outcome is
LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE. Genuine import/API failure is
LMFE_IMPORT_RECOVERY_FAILED; unverifiable starting state is
LMFE_IMPORT_RECOVERY_BLOCKED. Never rewrite the historical A2.1-F FAILED outcome.

Offline fake-result/AST checks ran before any real validation. One initial test
assertion falsely matched a read-only historical filename as guard reuse; it was
corrected to inspect imports and the child prefix. Initial 9/10 and corrected 10/10
results are preserved. No runner or plan change followed real validation results.
