# Phase 2H-B3.2-A semantic gate preregistration review record

Status: **OWNER_REVIEWED / FROZEN**
Candidate: **SEMANTIC_MATERIAL_SUPPORT_V1**
Candidate status: **PRE_REGISTERED_NOT_EVALUATED**
Date: 2026-10-06
Model status: **MODEL_SELECTION_REQUIRED**

Owner: **Zhe Wang (Victor)**
Owner approval date: **2026-10-06**
Scientific owner review: **PASS**

Owner approval freezes this preregistration only. Candidate execution status remains
**PRE_REGISTERED_NOT_EVALUATED** and model qualification status remains
**MODEL_SELECTION_REQUIRED**. No scientific content or inference configuration was
changed, and no model qualification experiment was begun during finalization.

Base HEAD and tag were verified before implementation with a clean working tree:
`c6c8ed26ec439f6276de71f6ee121c7ddc7f1d8b` /
`answerability-dev-baselines-v0.1-pre-semantic`.
The prior B2 evidence tag remains `e2c363f150f5494b85bcf4de2e7800c57727d92a`.

## Scientific motivation and decision procedure

Frozen Round-1 aggregate ALLOW recall / correct abstention:
- Retrieval response: 20/20 and 0/20.
- Top-1 lexical 0.60: 1/20 and 20/20.
- Top-3 union lexical 0.60: 5/20 and 20/20.
- Eligible non-control baseline count: 0.

Retrieval presence was insufficiently selective and lexical coverage insufficiently
sensitive. These aggregate observations justify preregistering semantic support
reasoning; they do not establish semantic performance. No individual Round-1 failure
question text was inspected or used for authoring. No benchmark-specific phrase
rule, AQ-specific rule, DEVELOPMENT example, or new prompt variant was introduced.

ALLOW requires resolved governing context and support for all material asks,
possibly across several supplied sections. Partial support is insufficient.
ABSTAIN/INSUFFICIENT_POLICY_SUPPORT requires resolved context, an unsupported ask,
and no context-unresolved ask. ABSTAIN/UNRESOLVED_POLICY_CONTEXT requires an
unresolved governing context or an explicitly context-unresolved material ask.
This reason is narrow; missing substantive detail alone does not qualify.
Relevance, score, rank or shared wording alone never proves answerability.

Full frozen B2 evidence is preserved, up to ten returned sections in rank order.
The frozen B2 evidence hash remains
`1ba747fe7a6eaa97610d05fd3690048aa062723f87585e38725dd149b6a57a52`.
No retrieval or exact lookup is available to this candidate. GateInput is copied
through an explicit field allowlist; evaluator labels and metadata are excluded.
The strict internal assessment is adapted to the unchanged two-field B1.1 GateOutput.
Invalid JSON, references or consistency become candidate errors, never a repaired
ABSTAIN. Later eligibility remains >=18/20 ALLOW and >=18/20 correct abstention.

## Preregistered hashes

| Component | SHA-256 |
| --- | --- |
| Canonical prompt | `09126ca1ca4cff86f634b6297f64c436863acac7a73a588de1bd249dca3b62cc` |
| Candidate source / complete parser source | `c70218e37b4304b6424e830b7f8698f11c4385ebd214c4d2fce5f8f805055d71` |
| Raw assessment schema | `03cb63e32303549e6cba16f5215680d95e887a18cd43304ecd409d7d1624b72c` |
| Combined parser/schema receipt | `0ef12eacd0def66259414afdfb2c1a588984848a2a95c33cc21a4053d13c58c7` |
| Configuration schema | `b6be8e1a7cd723d0a50c439257706caadb19be3236020b6e91079b6ce9f04d35` |
| Synthetic test source | `a22dce4baebf0581f2e710e9bd756d3e0760506f163f2aaa4b271b268b09dd0b` |
| Protocol | `c410059778514feb89a73497b1b3956ba549a86f8bc5238f964acbaa79021ec2` |
| Model qualification | `b694a0602add488392415630d2a5f11a612dbd3f348961e0943026b210aac80a` |
| Registry | `974a01464f40dd58f9a8ddf1c2d2bc550a9a106443d6a761a9713175a1133827` |

The registry defines hash serialization and includes the full schemas. This record
has no circular self-hash requirement. Source, prompt and schemas are bound before
any real semantic DEVELOPMENT inference; none has occurred.

## Model qualification

Existing declarations name vLLM and `Qwen/Qwen2.5-1.5B-Instruct`, with no immutable
model revision/snapshot and a `vllm/vllm-openai:latest` service image. The existing
HTTP client is `httpx==0.27.2`; application defaults are observed provenance only,
not adopted experiment settings. No arbitrary model alias was chosen, no provider
was contacted, and the Codex model was not used as an experimental model.

**MODEL_SELECTION_REQUIRED**. Execution configuration is null; no provider transport
is implemented. `SemanticGate.decide` raises `ModelSelectionRequired`. Future
qualification must freeze explicit provider/model/revision/client/settings and be
separately authorized. Quality retry is forbidden; infrastructure retry is not
currently authorized and may never be used to improve an undesirable answer.

## Validation and exposure

84/84 tests passed: 45 new semantic synthetic tests and 39 frozen synthetic
scorer/boundary tests. Tests used fixed fake responses only. Provider/model/retrieval
imports, sockets, real DEVELOPMENT payloads, B2/B3 result payloads and private
material were blocked during tests. Tests establish parser/adapter/protocol behavior,
not semantic-model accuracy. The synthetic compatibility checks preserve frozen
candidate-error denominators and reject malformed or inconsistent decisions.

Frozen integrity verification covered all five B2 artifacts, six Round-1 artifacts,
and 110 protected source/file hashes using byte hashing, without parsing benchmark
question contents or individual Round-1 result payloads.

- Real DEVELOPMENT semantic calls: **0**.
- Real semantic model calls: **0**.
- Retrieval calls: **0**.
- External/LLM calls: **0**.
- HELD_OUT accessed: **false**.
- Phase 2H HELD_OUT accessed: **false**.
- Phase 2G private HELDOUT accessed: **false**.
- No final candidate selected; B4 has not begun.
- No commit or tag created.

Owner scientific review is complete; stop for final owner verification. The next
procedural step is separately authorized immutable
model/provider qualification and explicit configuration/adapter approval. This
preregistration does not authorize semantic DEVELOPMENT inference.
