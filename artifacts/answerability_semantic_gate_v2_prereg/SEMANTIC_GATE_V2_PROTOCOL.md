# SEMANTIC_MATERIAL_SUPPORT_V2 preregistration protocol

Status: PRE_REGISTERED_NOT_EVALUATED. Review: CANDIDATE_AWAITING_OWNER_REVIEW.
Base commit / V1 failure tag: 3c721fc0b3f06a38ed715e800e3896de3ccc80ed /
answerability-semantic-model-v0.1-qualification-failed.
V1 remains OWNER_REVIEWED / QUALIFICATION_FAILED and is never modified or rerun here.

## Permitted motivation and unchanged semantics
Only the owner-reviewed synthetic failure taxonomy motivates the new interface:
zero valid final GateOutputs in 12 primary outputs, five prohibited code-fenced
outputs, seven noncanonical references, byte-identical repeated outputs for the
three preregistered repetitions, and zero DEVELOPMENT semantic exposure.
No new semantic heuristic is derived from V1 raw output, case wording, or real
DEVELOPMENT failures. No benchmark phrase dictionary or case-specific rule exists.

The objective is unchanged: determine whether supplied active-policy evidence
supports every material ask without unsupported assumptions, outside knowledge,
or unresolved policy authority/context. The semantic instruction prefix and
schema decision-consistency clauses are inherited unchanged from frozen V1.
ALLOW / SUPPORTED_BY_ACTIVE_POLICY requires resolved context and every ask SUPPORTED.
ABSTAIN / INSUFFICIENT_POLICY_SUPPORT requires resolved context, at least one
UNSUPPORTED ask, and no CONTEXT_UNRESOLVED ask.
ABSTAIN / UNRESOLVED_POLICY_CONTEXT requires unresolved governing context or at
least one CONTEXT_UNRESOLVED ask; ordinary weak support does not create a context conflict.
Support may be single-section or joint synthesis. Partial support is insufficient.
Relevance, cosine scores, rank, common practice and outside knowledge are not proof.

## Interface and boundary
The same exact B1.1 GateInput is the only accepted input. Its original question,
active-bundle metadata, all supplied evidence fields, unrounded scores and full
rank order (up to ten) are preserved. No benchmark object, ID, label, required or
Gold support, difficulty, rationale, review metadata or prior result is retained.
The user message is byte-identical to the V1 GateInput allowlist serialization.
Only the system prompt and model-facing output schema change.

The model outputs supporting_evidence_ranks, never canonical identity strings.
Rank lookup uses only the exact supplied GateInput. No new retrieval or corpus
lookup, fuzzy matching, title matching, guessing, semantic repair or evidence
substitution is permitted. The internal audit records each ask index, selected
rank and exact canonical identity/reference. The canonical assessment passes
through the unchanged V1 consistency parser; the external output remains exactly
the frozen GateOutput. Invalid output remains a candidate error, never ABSTAIN.

Require 1-8 material asks. Eight is an output-size safeguard, not a semantic rule;
asks must not be omitted or merged to force validity. An unrepresentable complete
assessment is an interface failure, not permission to ALLOW or silently ABSTAIN.
SUPPORTED requires nonempty strictly ascending, unique supplied integer ranks.
UNSUPPORTED and CONTEXT_UNRESOLVED require empty rank lists.

## Generation requirement and non-execution
JSON_SCHEMA_CONSTRAINED_DECODING (or equivalently strict token-level generation)
is mandatory. PROMPT_ONLY_STRICT_JSON does not satisfy V2. No decoder has been
selected, installed, imported or tested. SemanticGateV2.decide raises
CONSTRAINED_DECODER_IMPLEMENTATION_REQUIRED. Request construction is data only.
Post-generation fence stripping, regex cleanup, JSON repair, LLM correction,
schema-fixing or quality retries are forbidden. No score/confidence field or
retrieval-score threshold is added. No BGE/BM25/RRF/exact lookup is performed.

The sole future target remains Qwen/Qwen2.5-1.5B-Instruct revision
989aa7980e4cf806f80c7fef2b1adb7bc71aa306 on frozen Windows CPU/Transformers/FP32.
A2 does not initialize it, select a decoder, install dependencies, create a fresh
qualification suite, or execute semantic inference. Subsequent execution depends
on separate decoder/runtime qualification and owner authorization.

## Fresh suite and integrity
V1's already-exposed qualification suite is historical engineering evidence only;
it cannot serve as authoritative V2 qualification, including one-for-one paraphrases.
Only a coverage blueprint exists. Fresh scenario text, entities, values, evidence,
labels and fresh IDs must be authored after the V2 candidate freeze.

Tests use opaque interface fixtures and fake outputs only, not a new capability suite.
An isolated process blocks model/decoder/retrieval imports, network, V1 qualification
payloads and real benchmark/private file access. Inventory/schema/provenance checks
reject embedded case/result records in preregistration artifacts. This is a preventive
access/provenance guard, not a content comparison that opens forbidden old cases.
Standard-library schema probes cover the explicitly used JSON Schema keywords;
no external validator or real decoder capability is claimed. See mapping/decoder docs
for schema limitations. Historical changes are checked with Git; no old question or
raw output is parsed to author this candidate. No commit/tag/DEVELOPMENT/HELD_OUT.
