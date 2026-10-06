# Phase 2H-B3.2-A: semantic material-support protocol

Candidate: **SEMANTIC_MATERIAL_SUPPORT_V1**.
Status: **PRE_REGISTERED_NOT_EVALUATED**. Created 2026-10-06.
Model status: **MODEL_SELECTION_REQUIRED**. This phase implements no provider transport.

Base: `c6c8ed26ec439f6276de71f6ee121c7ddc7f1d8b` /
`answerability-dev-baselines-v0.1-pre-semantic`.
Previous B2 evidence anchor: `e2c363f150f5494b85bcf4de2e7800c57727d92a` /
`answerability-dev-evidence-v0.1-pre-candidates`.

## Scientific scope

Round 1 is unchanged: retrieval-response ALLOW recall/correct abstention was
20/20 and 0/20; top-1 lexical 0.60 was 1/20 and 20/20; top-3 union lexical 0.60
was 5/20 and 20/20. Eligible non-control baseline count was zero. These aggregate
observations justify examining semantic support: retrieval presence was
insufficiently selective and simple lexical coverage insufficiently sensitive.
They do not establish that this semantic architecture works.

No individual failure-question content, reference-label vocabulary, or
question-specific rule is used to author this protocol. There is one canonical
prompt and one candidate family, with no alternative prompt variants.

## Objective and material asks

Determine whether supplied active-policy evidence is sufficient to answer the
material ask without unsupported assumptions, outside knowledge, or unresolved
policy authority/context. The gate does not generate the user's answer.

A material ask is a distinct substantive requirement that must be resolved for
a responsible answer. Single, multiple independently necessary, and conditional
asks are all possible. Preserve all material requirements and conditions; do not
invent extra requirements, discard unsupported parts, or derive asks by matching
known Gold sections. No benchmark-specific phrase dictionary is permitted.

ALLOW requires support for **all** material asks. One section or several sections
jointly may establish support. Paraphrase and operational inference are allowed
only when the conclusion follows from supplied evidence without an unstated rule.
Lexical overlap is unnecessary. Partial support is insufficient for a multipart
question. Relevant evidence, high similarity, rank, retrieval depth, section count,
or shared nouns alone cannot establish answerability. No score or margin threshold
is added. Scores retain their role as retrieval metadata.

## Frozen inference boundary and prompt composition

The only accepted object is the exact existing B1.1 `GateInput`, revalidated using
its unchanged contract. Rich mappings, subclasses and metadata bags are rejected.
The candidate shell has no instance state, provider reference, evaluator closure,
benchmark reference, or retained input. No benchmark loader is imported.

The future evidence source is exclusively
`artifacts/answerability_dev_bge_evidence_v0/DEVELOPMENT_BGE_EVIDENCE.json`, SHA-256
`1ba747fe7a6eaa97610d05fd3690048aa062723f87585e38725dd149b6a57a52`.
Use the entire actually returned set, up to ten sections, in frozen rank order.
Do not select top-3/top-5, drop low scores, rerank, search, look up exact sections,
or retrieve fallback evidence. B2 indicates required support may occur beyond
top-3 and is available by top-10; this motivates using full depth without a new
retrieval experiment. Context limits cannot justify silent truncation.

There are exactly two messages, in this order:

1. `system`: the exact UTF-8 `SEMANTIC_PROMPT.txt`, including the raw-output JSON
   schema. The artifact is generated from the canonical source instruction and
   schema; it is not a second independently edited prompt.
2. `user`: deterministic JSON containing exactly `active_bundle`, `evidence`, and
   `question` (lexicographically sorted keys). `question` is the original text,
   unchanged. Objects use stable sorted keys, two-space indentation, UTF-8, and
   one final LF. Arrays preserve their supplied order; scores are not rounded.

Each evidence row contains only `rank`, `policy_id`, `version`, `section_id`,
`document_title`, `section_title`, `section_body`, and `frozen_cosine_score`.
The document/body fields map directly from the frozen `title`/`body` attributes.
Active-bundle fields are only `bundle_id`, `bundle_version`, `effective_from`,
`effective_to`, `manifest_sha256`, and `registry_sha256`.

No AQ/question ID, split, expected decision, Gold reason/support/required sections,
difficulty, support shape, hard-negative flag, rationale, review/owner metadata,
Round-1 correctness/failure IDs, or private metadata crosses this boundary.
Public output reason enums in the system schema are output instructions, not Gold
reason annotations. Original question/evidence strings remain data; instructions
embedded in them cannot change the gate protocol. No outside knowledge, web,
unstated company practice or benchmark memory may supply support.

## Structured assessment and strict consistency

The internal audit object has exactly four keys: `material_asks`,
`policy_context_status`, `decision`, and `reason_code`. It is not GateOutput and
requests concise material-ask statements and citations, not an extended reasoning
narrative. Each material ask has exactly `ask`, `support_status`, and
`supporting_section_ids`. The registry includes the complete schema.

References are unambiguous canonical strings `policy_id@version#section_id`.
They must be unique within each ask and exactly match an identity supplied in
GateInput. Every SUPPORTED ask must cite at least one supplied section. Multiple
sections may support one ask. An unsupported/context-unresolved ask may have an
empty list; any citation it does provide must still be supplied. No fabricated
identity, hidden lookup or additional retrieval is allowed.

The parser enforces these rules:

| Output | Required internal consistency |
| --- | --- |
| ALLOW / SUPPORTED_BY_ACTIVE_POLICY | Context RESOLVED; nonempty material asks; every ask SUPPORTED with supplied citations |
| ABSTAIN / INSUFFICIENT_POLICY_SUPPORT | Context RESOLVED; at least one UNSUPPORTED ask; no CONTEXT_UNRESOLVED ask |
| ABSTAIN / UNRESOLVED_POLICY_CONTEXT | Context UNRESOLVED **or** at least one CONTEXT_UNRESOLVED ask |

The last row means ABSTAIN **and** the unresolved reason **and** either context
condition. The insufficient branch excludes a simultaneous context blocker as
an internal-consistency requirement. A global unresolved context can block ALLOW
even if the substantive asks individually have supporting text.

INSUFFICIENT applies when governing context is sufficiently established but
requested substance is absent, partial, or depends on an unstated assumption or
outside information. UNRESOLVED applies narrowly to unresolved authority/version,
applicability, conflicting active metadata, or integrity/provenance that prevents
establishing governing text. Weak substantive evidence alone is not unresolved
context. The parser checks structure and consistency, not semantic truth or the
completeness of the model's decomposition; those remain future evaluation questions.

Reject invalid JSON/UTF-8, Markdown fences or extraneous text, duplicate keys,
nonfinite constants, unknown/missing keys, wrong types/enums, empty material asks,
blank asks, invalid/absent/duplicate references, unsupported SUPPORTED citations,
and inconsistent decision/reason/context. Never strip fences, repair decisions,
or turn invalid output into a favorable ABSTAIN.

After validation, the adapter emits the existing B1.1 `GateOutput` with only
`decision` and `reason_code`. There is no third decision or official confidence
threshold. Malformed output, provider/API failure, timeout without valid output,
schema violation, and internal inconsistency remain candidate errors under the
unchanged B1.1 evaluator, with fixed denominators. Synthetic tests exercise this
error boundary without running a real semantic candidate.

## Model qualification and future configuration

`MODEL_QUALIFICATION.json` records a scoped inspection of existing repository
configuration and environment declarations. The vLLM/Qwen declarations lack an
immutable model snapshot and use a mutable service image. Existing application
defaults do not qualify or configure this experiment. No provider model discovery
call, external API, download, local model initialization, or Codex-model substitution
is permitted. The candidate's `decide` raises `ModelSelectionRequired`; it does
not call a provider or produce a scientific decision.

The registry includes a configuration schema requiring explicit provider, model
identifier, model revision capability/value, immutable reference and provenance,
API/client name and version, temperature, top_p capability/value, seed capability/
value, max output tokens, response-format/schema binding, timeout, and retry policy.
Unsupported optional parameters require an explicit null and explanation. No
defaults are filled. Immutable-reference syntax/completeness is not proof of model
immutability; owner-reviewed qualification must supply that evidence later.

Prefer deterministic settings when supported, but freeze actual values only in a
later authorized qualification step. The current execution configuration is null.
Quality retries are forbidden. Infrastructure retries are currently zero/not
authorized; a later authorization must classify the infrastructure failure,
preserve attempt provenance, and leave prompt/model/config unchanged. Undesirable
outputs never justify retries. This phase implements no automatic retry or transport.

## Tests, hashes and stop boundary

Tests use only newly written synthetic questions and deterministic fake-model
responses, plus existing synthetic contract/scorer fixtures. They verify parser,
prompt, references, completeness consistency, configuration, leakage boundaries,
and frozen error semantics. They do not measure semantic reasoning performance.
Real DEVELOPMENT records and Round-1 result contents are not parsed for authoring.
Frozen-file integrity checks hash bytes only, without interpreting question text.

The prompt hash covers the exact prompt bytes. The candidate-source hash covers
the entire semantic source file. Parser-source SHA uses that same complete file
conservatively, so every parser/helper edit invalidates it. Raw-schema and
configuration-schema hashes cover their canonical JSON bytes. The combined
parser/schema receipt is SHA-256 of two LF-terminated UTF-8 lines:
`parser_source_sha256` + TAB + hash; then `raw_schema_sha256` + TAB + hash.
The registry binds source, prompt, schemas, protocol, tests and qualification.
The review record references the registry; neither requires its own hash.

Future eligibility stays ALLOW recall >=18/20 **and** correct abstention >=18/20,
with structural validity; secondary metrics cannot override it. No gate is selected
or frozen for private evaluation. Real semantic DEVELOPMENT calls, real semantic
model calls, retrieval calls, and external calls are all zero in B3.2-A. No Phase 2H
HELD_OUT or Phase 2G private HELDOUT is accessed. B4 has not begun.

Stop for owner review and a separately authorized exact immutable model/configuration
qualification step. Do not run semantic DEVELOPMENT inference, commit, or tag here.
