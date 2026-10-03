# Scope and Answerability Contract — Phase 2H-A1

Contract version: **v0.1**. This document fixes the semantic and runtime boundary
for owner review before benchmark authoring or gate implementation. The companion
[Phase 2H protocol](PHASE_2H_PROTOCOL.md) fixes evaluation and selection. This
phase creates documentation only; it does not deploy a gate or create a Git tag.
After owner approval, changes require an explicitly versioned amendment and must
not retroactively redefine a frozen benchmark or result.

## Provenance and purpose

| Anchor | Frozen value |
| --- | --- |
| Phase 2G public result tag | `retrieval-heldout-v0.1-complete` |
| Phase 2G public result commit | `b4e93b05d83d89567ca30b4abf880589bda9c529` |
| Selected ranked retriever | BGE embedding v0 |
| Active policy bundle | `last-mile-exception-triage-demo`, version `1.0-demo` |
| Frozen corpus | Eight SOP documents, 25 stable sections |

The [public Phase 2G aggregate result](../retrieval/HELDOUT_EVALUATION_SUMMARY.md)
reports answerable Hit@3 = **25/26**, negative correct abstention = **0/4**, and
negative false support = **4/4**. These aggregates motivate a separate gate:
strong answerable retrieval recall does not establish reliable answerability or
scope abstention. They supply no case-level design signal, threshold, rule,
keyword, reason family, or benchmark question for Phase 2H.

The Scope / Answerability Gate decides whether the current frozen policy bundle
provides sufficient authoritative support to substantively answer the user's
policy question. Improving retrieval ranking is outside its responsibility.

## Product and pipeline boundary

The gate applies only to the **supplemental ranked question/guidance path**:

```text
Original user question
  -> Frozen BGE v0 ranked retrieval
  -> Top-k policy sections (at most 10)
  -> Scope / Answerability Gate
       -> ALLOW   -> evidence-backed explanation
       -> ABSTAIN -> unsupported-by-current-policy response
```

The authoritative deterministic path remains separate and unchanged:

```text
Structured facts
  -> deterministic rules
  -> expected policy section IDs
  -> exact metadata lookup
```

Mandatory deterministic support sections continue to use exact lookup. The gate
does not select, remove, replace, veto, or supplement that required section set;
does not alter rule outputs, eligibility, action state or priority; and does not
repair a missing exact identity with a ranked neighbor. Its decision concerns
the supplemental explanation only. `ALLOW` is not a shipment decision, an
operational authorization, or permission to override deterministic policy.

The gate does not reorder or rescore ranked sections. An allowed explanation
must trace its material claims to the permitted active policy evidence; an
abstaining response must not provide an unsupported substantive answer under
the cover of a disclaimer or a partial answer.

## Primary binary semantics

Every valid gate decision is exactly one of **`ALLOW`** or **`ABSTAIN`**. These
values are mutually exclusive. There is no third scored class and no
partial-ALLOW class. Reason codes are optional secondary diagnostics.

### ALLOW

`ALLOW` is justified only when the requested substantive answer can be **fully
and materially supported by the current frozen policy bundle**, with the
support established from the policy evidence available at the gate boundary.
Every claim material to answering the actual request must be traceable to that
evidence, including material qualifications and conditions.

Support may come from one section or multiple sections. Multi-section synthesis
is permitted when all material claims and the connections needed for the answer
are supported; one section need not contain the entire answer. Synthesis must
not invent an additional policy rule, authority, fact, exception, or assumption.
Supporting only part of a materially compound request is insufficient for an
ALLOW decision on the whole request.

None of the following alone establishes support: shared vocabulary, the same
operational domain, high BGE cosine similarity, a nearby policy topic, or a
plausible answer from general knowledge. A policy citation must substantiate the
claim, not merely be topically related to it.

### ABSTAIN

`ABSTAIN` is required when the requested substantive answer cannot be fully
supported from the currently active frozen policy bundle, or when the permitted
runtime evidence does not establish that support. This includes material
dependence on authority, facts, assumptions, or evidence unavailable in that
policy context. Unresolved support or unresolved authoritative context is not
permission to guess.

The governing test is:

> Can a careful reviewer trace the material answer claims to the active policy
> evidence without introducing unsupported information?

If the answer is no, or cannot be established from the permitted inputs, the
runtime decision is ABSTAIN. No fixed cosine-score threshold defines this
semantic target. Phase 2G HELDOUT failures do not define it either.

### Corpus-level target versus runtime evidence

Future benchmark authors label answerability against the **complete frozen
policy bundle**, independently of a retriever's output. A supported question
does not become Gold ABSTAIN merely because a retriever misses its support.

At inference, the gate has only the bounded inputs below. It cannot consult a
hidden Gold support list or fetch additional sections to complete its evidence.
If the corpus supports a Gold ALLOW question but the permitted retrieved
evidence is insufficient, a runtime ABSTAIN remains a false abstention against
that fixed Gold label and a failure for gated end-to-end retrieval. This
distinction prevents retrieval misses from silently changing the benchmark.

## Generic diagnostic reason codes

| Reason code | Valid decision | Meaning |
| --- | --- | --- |
| `SUPPORTED_BY_ACTIVE_POLICY` | `ALLOW` only | Available active policy evidence fully supports the material requested answer. |
| `INSUFFICIENT_POLICY_SUPPORT` | `ABSTAIN` only | Available active policy evidence does not fully support the material requested answer. |
| `UNRESOLVED_POLICY_CONTEXT` | `ABSTAIN` only | The authoritative active policy context cannot be established from the permitted inputs. |

If a reason code is emitted, exactly one code must agree with the binary
decision. Use `UNRESOLVED_POLICY_CONTEXT` when unresolved context prevents the
support assessment; otherwise use `INSUFFICIENT_POLICY_SUPPORT` for unsupported
answers. Do not create a detailed case taxonomy from historical HELDOUT cases.

The binary outcome determines the four primary metrics. Reason diagnostics must
not partition, exclude, or change their denominators. Reason agreement may be
reviewed separately; it cannot convert an incorrect binary decision into a
correct one. A malformed output or an invalid decision/reason pairing is a
contract error, not a new class or a silently repaired decision.

## Maximum runtime information

The inference boundary may carry only:

1. Original user question text, unchanged.
2. The frozen BGE v0 Top-10 ranked policy sections actually returned.
3. Their canonical identities: `(policy_id, version, section_id)`.
4. Their readable titles and section bodies.
5. Their frozen BGE cosine scores, in unchanged rank order.
6. Active bundle metadata needed to establish authoritative context, such as
   bundle identity/version, applicability/effective metadata, and integrity
   provenance. Metadata must not hide extra section bodies or benchmark labels.

This is a maximum, not a requirement to use every field. Policy scores describe
similarity, not authority or answer completeness. A gate may ignore scores as
answerability signals. Neither scores nor any value derived only from them
replaces the semantic support test.

The gate must never receive an evaluation question ID, Gold ALLOW/ABSTAIN label,
private rationale, Gold support section list, required support section list,
split, difficulty, benchmark family, or reviewer notes. The future evaluator
must construct the allowlisted inference input rather than pass a complete
benchmark record or a closure over it. An evaluator may associate an output with
its question ID outside the inference boundary; the gate must not see that ID.
Benchmark labels are available to the evaluator only after inference for scoring.

The maximum does not authorize another search, a reranker, external knowledge
retrieval, a full-corpus side channel, or access to authoring/evaluation files.
Canonical identities identify runtime evidence; a benchmark support list that
names those same identities is still prohibited inference information.

## Independently frozen retrieval

The [ranked retriever freeze record](../retrieval/RETRIEVER_FREEZE_RECORD.md)
remains authoritative. Phase 2H does not revise any retrieval behavior:

| Setting | Frozen value |
| --- | --- |
| Model | `BAAI/bge-small-en-v1.5` |
| Exact revision | `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` |
| Device / dimension | CPU / 384 |
| Corpus | Eight SOP documents / 25 stable sections / `1.0-demo` |
| Searchable text | Readable document title + LF + readable section title + LF + section body |
| Question | Original text; no prefix, instruction, rewriting or transformation |
| Embeddings | Normalized, with existing model-owned pooling/truncation unchanged |
| Similarity | Existing normalized dot product / cosine |
| Threshold | `0.30`; existing whole-response abstention behavior unchanged |
| Depth | `top_k = 10` |
| Tie-break | Descending unrounded similarity, then ascending canonical identity |
| Additional retrieval | None; no BM25/RRF, fallback, reranking or candidate filtering change |

Ignoring `0.30` as proof of answerability does not authorize bypassing or tuning
the retriever's threshold. Preserve the actual frozen response, including an
empty result set on retrieval abstention; do not expose fabricated or hidden
below-threshold results to the gate. An empty evidence set cannot justify ALLOW.
No Phase 2G HELDOUT information may tune this threshold or any new gate feature.

## Historical evaluation quarantine

The entire prior retrieval evaluation package is historical test evidence, not
a Phase 2H development dataset. Phase 2H development must not search for, open,
copy, inspect, infer from, or use Phase 2G HELDOUT question text, Gold sections,
required sections, rationales, per-question rankings, per-question cosine
scores, per-question failure diagnoses, or Attempt #1 retrieval payloads.

Only frozen public aggregates may be cited to motivate why a separate gate is
needed. Do not derive thresholds, rules, keywords, reason families, prompts or
new benchmark questions from quarantined cases, including remembered private
case details. The three generic reason codes above follow this contract rather
than a historical negative subtype taxonomy.

## Current-phase boundary

Phase 2H-A1 authors no gate, executable schema, benchmark question, model test,
or evaluation result. It changes no retrieval/scoring implementation, policy
corpus, Gold data, or historical artifact. The future benchmark and selection
rules are specified in [PHASE_2H_PROTOCOL.md](PHASE_2H_PROTOCOL.md); Phase 2H-A2
authoring requires a separate owner instruction after review.
