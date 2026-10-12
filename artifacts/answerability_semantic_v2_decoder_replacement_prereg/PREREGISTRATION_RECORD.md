# Phase 2H-B3.2-A2.1-E preregistration record

Status: **OWNER_REVIEWED / REPLACEMENT_DECODER_SELECTED_NOT_QUALIFIED**.
Owner: **Zhe Wang (Victor)**.
Owner approval date: **2026-10-12**.
Scientific owner review: **PASS**.

Base commit: `6e05245a6f7971ab05101bc2b24de42180a614cd`.
Base tag: `answerability-semantic-v2-xgrammar-v0.2-required-field-failure`.
HEAD and tag matched; pre-run working tree was clean.

Historical XGrammar owner status: OWNER_REVIEWED / DIAGNOSTIC_ESTABLISHED.
Diagnosis: GRAMMAR_COMPILATION_OR_REQUIRED_FIELD_ENFORCEMENT_ISSUE.
Evidence: ESTABLISHED. Exact V2 schema/compiler path suitability: REJECTED.
All 87 files in HISTORICAL_INTEGRITY_RECEIPT.json match their frozen HEAD Git blobs
byte-for-byte. Historical artifacts, sources and receipts were not changed.

Sole replacement: **lm-format-enforcer==0.11.3**, package `lmformatenforcer`.
Status: **REPLACEMENT_DECODER_SELECTED_NOT_QUALIFIED**.
Capability: **NOT_ASSESSED**. Installation: **NOT_AUTHORIZED_IN_A2.1-E**.
Selection is based on release-metadata architectural compatibility claims only;
CPU compatibility is an untested inference from the Python token-filtering path
and platform-independent wheel. No decoder runtime comparison occurred.

Exact frozen schema SHA-256:
`6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.
No schema, semantic adapter, prompt, model, runtime, or historical evidence changed.

Python requirement: <4.0,>=3.8; explicit Python 3.12 classifier; frozen Python 3.12.10.
Direct requirements: pydantic>=1.10.8, interegular>=0.3.2, packaging, pyyaml.
Installed satisfying versions: pydantic 2.13.5, packaging 26.3, PyYAML 6.0.3.
Interegular is missing; its exact version and transitive dependencies remain
unresolved for later owner-authorized enablement. LMFE is also absent. No resolver,
package import, installation, wheel download, or source-distribution download ran.
Frozen environment metadata and RECORD inventory match before and after: 34 packages,
drift = 0. The installed transitive graph and inactive extras are preserved in
LMFE_DEPENDENCY_REQUIREMENTS.json.

The future gate preregisters M1 ACCEPT; M2-M5 REJECT; historical S1/S2/S3 (M6-M8)
REJECT, using exact existing strings. Complete-object and EOS acceptance are required,
not merely prefix acceptance. Required fields, enum/const, object/array structure,
additionalProperties, min/maxItems, integer rank type, numeric bounds, uniqueItems,
string constraints, oneOf/anyOf/allOf, conditional branches and contains all require
explicit qualification. Unsupported enforcement must be recorded and reviewed;
no silent assumption of full JSON Schema compatibility is permitted.

Future integration: JsonSchemaParser and build_transformers_prefix_allowed_tokens_fn
with the exact frozen tokenizer; no repair, cleanup or malformed-output retry.
The deterministic adapter boundary is unchanged. See STRUCTURAL_CONFORMANCE_GATE.md
for the mandatory future qualification and stopping rules.

V2 candidate status remains **PRE_REGISTERED_NOT_EVALUATED**.
Fresh V2 semantic qualification suite: **NOT YET AUTHORED**. No V1 cases reused.

## Preserved preregistration verification and accounting

Offline preregistration tests: **12/12 PASS**. These inspect saved artifacts and
hashes only. Network and subprocess operations were blocked during tests; none
were attempted. Decoder/model packages were not imported. These results are NOT
parser conformance results and do not qualify LMFE.

Model initialization = 0; generate = 0; forward = 0; decoder execution = 0;
parser conformance execution = 0; package installation = 0; DEVELOPMENT access/calls = 0;
retrieval = 0; Phase 2H HELD_OUT access = false; Phase 2G private HELDOUT access = false.
Only public release metadata was retrieved. A sandbox DNS failure preceded successful
metadata-only retrieval; neither operation installed or executed a package.

## Owner finalization verification and accounting

Only this administrative owner/freeze record changed during finalization. The
registry, protocol, selection record and other substantive preregistration artifacts
remain byte-identical snapshots of preregistration. Their original pending-review
labels are historical; this record is the authoritative final owner review status.
The original 12/12 offline check result and test source remain unchanged; no test
suite or parser qualification was rerun during finalization.

Read-only integrity verification reconfirmed the exact frozen V2 schema, all 87
historical files in HISTORICAL_INTEGRITY_RECEIPT.json, all unchanged preregistration
artifact hashes, and the frozen 34-package metadata/RECORD inventory. Package drift
and mutation = 0. LMFE and interegular remain absent; the exact interegular version
is NOT frozen by A2.1-E and belongs to later dependency enablement.

Finalization counters (distinct from earlier public metadata retrieval):
model initialization = 0; generate = 0; forward = 0; decoder execution = 0;
parser conformance execution = 0; package installation = 0; package mutation = 0;
DEVELOPMENT access/calls = 0; retrieval = 0; network activity = 0;
Phase 2H HELD_OUT access = false; Phase 2G private HELDOUT access = false.
Distribution metadata inspection did not import a decoder or model package.
An initial verification process stopped before edits when its audit guard blocked
platform.machine()'s local socket.gethostname call. No network operation occurred.
Verification then used sys/os metadata without hostname probing; no scientific
execution or test was retried. No alternate decoder bake-off, output repair,
model call, or fresh suite authoring occurred. No commit or tag was created.

## Hash provenance and next step

The original FINAL_SHA256.json remains byte-identical with SHA-256
`8cdc4680035e3883a0ba9767970eaebe88e4effe6d2fd31f4975023354576814`.
It preserves the preregistration-time receipt, including the prior administrative
record hash `55858ab8d57d68210f6bc67b55056a13cba9807fecf975c1bb594d2be96d1ddf`.
Only that record entry is superseded by the finalized record SHA reported at
completion. All other entries still match. This record does not embed its own hash,
so no circular hash requirement is created. The unchanged registry does not hash
this record. Historical XGrammar receipts and artifacts are unchanged.

Owner review of preregistration is complete. Dependency enablement requires a later
explicit authorization; it must select the missing dependency version separately.
Pure structural qualification also requires subsequent authorization before any
model generation. Installation and inference remain unauthorized in A2.1-E.
