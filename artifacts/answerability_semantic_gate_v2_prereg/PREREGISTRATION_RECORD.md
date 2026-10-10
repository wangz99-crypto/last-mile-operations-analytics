# V2 semantic candidate preregistration review record

Status: **OWNER_REVIEWED / FROZEN**
Owner: **Zhe Wang (Victor)**
Owner approval date: **2026-10-09**
Scientific owner review: **PASS**
Model capability under V2: **NOT_ASSESSED**
Candidate: **SEMANTIC_MATERIAL_SUPPORT_V2 / PRE_REGISTERED_NOT_EVALUATED**
Base HEAD and V1 failure tag: `3c721fc0b3f06a38ed715e800e3896de3ccc80ed` /
`answerability-semantic-model-v0.1-qualification-failed`. Initial working tree clean.
Parent: SEMANTIC_MATERIAL_SUPPORT_V1 / OWNER_REVIEWED / QUALIFICATION_FAILED.
Frozen runtime tag: answerability-semantic-runtime-v0.1-pre-qualification ->
a36fda5958492ca326f944642fe252b5d41442b7. V1 preregistration tag:
answerability-semantic-gate-v0.1-pre-model -> 4b13cb72482da6fd1109aa5f5ee4b7dbcaaf8c87.

Only the owner-reviewed aggregate synthetic failure families motivate V2:
5/12 code-fenced primary outputs, 7/12 noncanonical references, 0/12 valid GateOutputs,
and three byte-identical repeat pairs. V1 DEVELOPMENT semantic exposure was zero.
No old case wording/raw output or real DEVELOPMENT content was inspected for design.

The semantic standard is unchanged: ALLOW only for resolved context plus all asks
supported; insufficient ABSTAIN for resolved context plus an unsupported ask with
no unresolved-context ask; unresolved ABSTAIN for unresolved authority/context or
an ask depending on it. Relevance is not support; partial support is insufficient.
No outside knowledge, new thresholds or benchmark-specific rules are permitted.

New interface: token-level constrained JSON plus strictly ascending unique supplied
integer ranks, mapped exactly to canonical identities. Non-supported asks have empty
rank lists. One to eight asks is an interface bound. The final GateOutput and frozen
V1 semantic consistency parser remain unchanged; no semantic repair is performed.

Constrained decoder: **CONSTRAINED_DECODER_IMPLEMENTATION_REQUIRED**; none selected,
installed or invoked. Future target remains Qwen/Qwen2.5-1.5B-Instruct at revision
989aa7980e4cf806f80c7fef2b1adb7bc71aa306, Windows local CPU Transformers FP32, no quantization.
Fresh authoritative V2 qualification suite: **NOT YET AUTHORED**.
V1 Q1–Q12 MUST NOT be reused as the authoritative V2 qualification suite.
The future suite must be newly authored after V2 candidate freeze, use new scenarios
and evidence, not be a one-to-one paraphrase of V1 cases, and test only the frozen
generic capability families. The blueprint contains coverage and future stringent
criteria only; no fresh case text, labels or evidence.

Tests: 91/91 PASS (52 V2 interface/schema/guard tests plus 39 frozen scorer/boundary tests).
Leakage guard: PASS; access/provenance and no-payload inventory checks, not old-case
content comparison. Model/decoder/retrieval imports, network and quarantined payload
reads were blocked in isolated tests. No constrained-decoder capability is claimed.
Real model calls=0; model initialization=0; generate=0; forward=0; decoder-library
model calls=0; DEVELOPMENT semantic calls=0; retrieval=0; network=0; installations=0.
Both Phase 2H HELD_OUT and Phase 2G private HELDOUT accessed=false.
All 157 historical tracked paths remain unchanged; V1 and runtime anchor receipts match.

Candidate source SHA: `a83ebe3b6841e5cd810633c68ba4efc76ed8d6daeee1cbb62899e317133e9219`.
Synthetic test source SHA: `727abe69a2d0bcf6723277efd83f44a2adc3f500a3b2873e204e43241c4a8ca4`.
Adapter/parser receipt SHA: `ea36a48dc9d8b3bb97b6198957a0f5c46d7a90bca895f2364e8f4f080b74e64e`.

| Artifact | SHA-256 |
| --- | --- |
| SEMANTIC_GATE_V2_PROTOCOL.md | `d823f713a042f695854c46eea4a8ad533aab75fb11f057f031d6a7a6b60d325f` |
| SEMANTIC_PROMPT_V2.txt | `1b36fbf92f120f77bfb9d2af55409ed48e43341956f7e06fae83777f4937f35e` |
| RAW_ASSESSMENT_SCHEMA_V2.json | `6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e` |
| RANK_MAPPING_CONTRACT.md | `b62c5e7647dc21749832b75fb1ea6f168ede8f56ab3f81a4c007fe00f1830f6a` |
| CONSTRAINED_DECODER_REQUIREMENTS.md | `aea2fbe93165afef76f641d11c5fbea7b54e2c72109e3e2d82dfad2018f34900` |
| FRESH_QUALIFICATION_BLUEPRINT.md | `efa5d6abd9255610eb40cd1abf80c3e4a9c9708c259b8d2788238f61ec63f15e` |
| SEMANTIC_GATE_V2_REGISTRY.json | `c51d7f92e714421797f51bf1571cb8ee6f50b47352aad7867c1786d818a37ec2` |

No record self-hash or circular hash dependency. Administrative owner finalization only; scientific artifacts and execution states unchanged.
Stop for final owner verification. No commit/tag,
decoder selection/installation, actual fresh suite authoring or model execution.
