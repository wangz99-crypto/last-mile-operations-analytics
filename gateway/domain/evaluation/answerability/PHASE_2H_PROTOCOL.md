# Independent Scope / Answerability Evaluation — Phase 2H Protocol

Protocol version: **v0.1**, prepared for the Phase 2H-A1 owner freeze. Definitions,
denominators, eligibility floors and selection priorities are fixed here before
any Phase 2H benchmark or candidate result exists. This is a design document,
not an implementation or authorization to begin benchmark authoring. Normative
gate semantics and maximum inference inputs are in
[ANSWERABILITY_CONTRACT.md](ANSWERABILITY_CONTRACT.md).

## Provenance and fixed product boundary

| Anchor | Value |
| --- | --- |
| Phase 2G public result tag | `retrieval-heldout-v0.1-complete` |
| Phase 2G public result commit | `b4e93b05d83d89567ca30b4abf880589bda9c529` |
| Selected ranked retriever | BGE embedding v0 |
| Model / revision | `BAAI/bge-small-en-v1.5` / `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` |
| Corpus | `last-mile-exception-triage-demo`, `1.0-demo`, eight SOPs / 25 sections |
| Primary motivation | Strong answerable retrieval recall, but unreliable answerability/scope abstention |

The frozen [public aggregate result](../retrieval/HELDOUT_EVALUATION_SUMMARY.md)
provides motivation only: answerable Hit@3 **25/26**, negative correct abstention
**0/4**, negative false support **4/4**. It does not establish a remediation,
production readiness, general prevalence or universal performance.

Phase 2H adds a binary ALLOW/ABSTAIN gate **after frozen ranked retrieval** in
the supplemental question/guidance path. Structured facts -> deterministic
rules -> expected policy section IDs -> exact metadata lookup remains
authoritative and unaffected. Mandatory exact support is outside gate selection.
All BGE v0 settings remain fixed as specified in the contract, including the
original question, empty prefix, searchable text, normalization, cosine score,
`0.30` threshold, Top-10 depth, canonical tie-break and 25-section corpus.

## Quarantine and independent authoring

The prior retrieval evaluation package is historical test evidence. Phase 2H
must not access or use Phase 2G HELDOUT wording, Gold/required sections,
rationales, per-question rankings/scores/failure diagnoses, or Attempt #1
retrieval payloads. This prohibition includes deriving a feature, rule,
threshold, keyword, reason family, or new question from those cases. Public
aggregate results serve only the motivation above.

A future benchmark must be independently authored from the frozen policy
corpus, this answerability contract, and the declared product boundary. It must
not repurpose historical retrieval questions or be authored by inspecting
quarantined per-question results. Do not inspect old private cases even to
perform a cross-benchmark similarity check.

The future authoring workspace must be isolated from gate implementations and
candidate outputs. Authors/reviewers establish the policy support and labels
without using a candidate's decision or similarity score as their authority.
The implementation workspace receives only the separately authorized
DEVELOPMENT release; future HELD_OUT wording and labels remain with the owner
until the release conditions below are met. This document neither locates nor
creates that private workspace.

## Future benchmark composition — specification only

| Split | ALLOW | ABSTAIN | Total |
| --- | ---: | ---: | ---: |
| DEVELOPMENT | 20 | 20 | 40 |
| HELD_OUT | 20 | 20 | 40 |
| Total | 40 | 40 | 80 |

The intentional class balance is an **evaluation design**, not an estimate of
production query prevalence. No item wording, concrete question, hidden subtype
catalog, or benchmark record is authored in Phase 2H-A1.

Each split must contain straightforward and difficult items. Its ALLOW items
must collectively cover all eight SOP documents and include both single-section
and multi-section support, paraphrased operational questions, and questions
whose relevant section is not obvious from exact wording. Reviewers must
document that coverage before freezing the benchmark.

At least **10 of the 20 ABSTAIN items in each split** must be deliberately
near-domain hard negatives, hence at least half of all 40 ABSTAIN items. A hard
negative may use policy vocabulary, concern a neighboring operational topic, or
retrieve semantically similar text, while lacking sufficient authoritative
support for the requested substantive answer. Obvious unrelated questions must
not dominate. Difficulty comes from this semantic distinction, not from a
keyword list or an observed Phase 2G failure family. This specification provides
no concrete negative wording.

Before candidate evaluation, authors must review support correctness,
question clarity, multi-section needs, within-benchmark duplicates and close
cross-split paraphrases. Freeze both splits' counts, reviewed labels, record
schema, file inventory and byte hashes/receipts under owner control. Record
reviewer provenance, including any lack of an independent second reviewer.
Do not silently change labels or split membership after seeing gate results.

## Conceptual private benchmark record

This is a future record specification, not an extension to an existing runtime
schema and not a populated example:

| Field | Meaning / constraint | Gate inference access |
| --- | --- | --- |
| `question_id` | Stable unique benchmark identifier | Never |
| `split` | `DEVELOPMENT` or `HELD_OUT` | Never |
| `question` | Original nonempty user question text | Yes, unchanged |
| `expected_gate` | Exactly `ALLOW` or `ABSTAIN` | Never |
| `reason_code` | One of the three generic contract codes, consistent with the expected binary label | Never |
| `gold_support_sections` | Unique canonical support identities in the active frozen corpus | Never |
| `required_support_sections` | Unique minimal necessary support identities, subset of Gold support | Never |
| `authoring_rationale` | Private traceable explanation of the label and evidence sufficiency/absence | Never |
| `review_status` | Conceptually `DRAFT` or `OWNER_REVIEWED`; only owner-reviewed items may freeze | Never |

Each support identity uses `(policy_id, version, section_id)` and must resolve
exactly in the frozen active corpus. Identity uniqueness and policy-version
consistency apply to both lists.

For **ALLOW**, `gold_support_sections` and `required_support_sections` must both
be nonempty. Gold support identifies policy evidence genuinely supporting the
answer; the required subset contains the minimal evidence needed to support all
material requested claims. Reviewers must justify the required set, including
multi-section synthesis, before results exist. Do not make every merely related
section required. Support is judged against the full corpus, independently of
whether BGE retrieves it.

For **ABSTAIN**, both support lists must be exactly `[]`. The private rationale
must explain why the active bundle cannot fully substantiate the requested
answer. Do not annotate a topical neighbor as Gold support to justify a negative
label. `SUPPORTED_BY_ACTIVE_POLICY` pairs only with ALLOW; the other two reason
codes pair only with ABSTAIN.

The rationale and all annotation fields remain private evaluation evidence,
never gate inputs. Difficulty, benchmark family and reviewer notes, if later
recorded as private authoring metadata, are also prohibited at inference and
cannot create separate primary scoring denominators.

## Future inference and evaluation separation

For each authorized question, frozen BGE receives only original question text
and `top_k=10`. The gate receives only the maximum runtime information in the
contract: that text, the actual ranked sections, their canonical identities,
titles/bodies, unchanged scores and necessary active bundle metadata. No
benchmark envelope, labels, rationale, split or support list crosses either
inference boundary. The gate does not fetch additional sections or reorder the
frozen ranked result.

The evaluator records the gate's binary output before consulting labels for
scoring. The same frozen retrieval response supplies gated and ungated metrics;
an ABSTAIN decision cannot trigger a new retrieval attempt. Policy-authority
metadata is not a channel for hiding benchmark annotations.

Invalid/missing decisions or inconsistent decision/reason pairs are contract
errors. Record them explicitly; do not turn them into a correct ABSTAIN, drop
their Gold items, or add a third benchmark class. An incomplete/invalid run
cannot establish eligibility or be presented as a completed benchmark result.
The following metrics apply to complete valid runs with every frozen item
retained. Reason-code diagnostics never modify the binary denominators.

## Mandatory class-conditional metrics

Let `A` be all Gold ALLOW items and `B` all Gold ABSTAIN items in the split.
For each planned split, `|A| = 20` and `|B| = 20`.

| Metric | Frozen numerator / denominator |
| --- | --- |
| ALLOW recall | Gold ALLOW predicted ALLOW / all Gold ALLOW |
| False abstention rate | Gold ALLOW predicted ABSTAIN / all Gold ALLOW |
| Correct abstention rate | Gold ABSTAIN predicted ABSTAIN / all Gold ABSTAIN |
| False support rate | Gold ABSTAIN predicted ALLOW / all Gold ABSTAIN |

Report each numerator, denominator and rate. For a complete valid binary run,
ALLOW recall + false abstention rate = 1, and correct abstention rate + false
support rate = 1. Never report only the fraction of emitted ALLOW decisions
that look correct or collapse the tradeoff into a single aggregate score.

Balanced accuracy may be reported as a secondary descriptive metric only:
`(ALLOW recall + correct abstention rate) / 2`. It cannot replace any of the four
mandatory metrics, establish eligibility, or supersede the selection order.
No composite metric is required by this protocol.

## Gated end-to-end retrieval preservation

Use **all Gold ALLOW items**, not just those the gate lets through. Let:

- `g_i = 1` when the gate emits ALLOW, otherwise `0`.
- `R_i(k)` be the first `k` unique canonical identities in the unchanged frozen
  ranked response, preserving first occurrence and rank. An empty response gives
  the empty set; no extra retrieval supplies missing positions.
- `G_i` be the Gold support identities; `Q_i` the nonempty required support set.
- `N = |A|`, and `M = {i in A : |Q_i| > 1}`.

Gold/required sets in these formulas are evaluator-only, used after inference.

| Metric | Frozen formula / denominator |
| --- | --- |
| Gated Hit@1 and Hit@3 | `sum(i in A) g_i * 1[R_i(k) intersects G_i] / N`, for `k = 1, 3` |
| Gated required macro coverage @3/@5/@10 | `sum(i in A) g_i * (|R_i(k) intersect Q_i| / |Q_i|) / N` |
| Gated required micro coverage @3/@5/@10 | `sum(i in A) g_i * |R_i(k) intersect Q_i| / sum(i in A) |Q_i|` |
| Gated multi-required full-set success @3/@5/@10 | `sum(i in M) g_i * 1[Q_i is a subset of R_i(k)] / |M|` |

An incorrect ABSTAIN on a Gold ALLOW question contributes **zero success or
coverage**, while its question and required assignments remain in every
applicable denominator. It also remains in `M` when it has multiple required
sections. A gate-selected subset denominator is prohibited.

Report the corresponding ungated metrics on the **same responses and full Gold
ALLOW set**, obtained by setting every `g_i` to 1, so any loss caused by gating
is visible. Keep relevance (Gold hits) and required-evidence completeness
separate. Multi-required items are mandated in each future split; an unexpected
zero multi-required denominator is an invalid benchmark composition, not a
perfect or fabricated rate. None of these measures reuses Phase 2G questions.

## DEVELOPMENT eligibility and selection

Freeze the following eligibility floor before any candidate results:

```text
ALLOW recall >= 90%
correct abstention rate >= 90%
```

On the planned DEVELOPMENT split, this means **at least 18/20 in each class**,
using exact counts/rates rather than rounded display percentages. Both conditions
must hold in a complete valid run. A system that always abstains has zero ALLOW
recall and is ineligible; a system that always allows is also ineligible.

If no candidate meets both floors, **select no gate, do not expose Phase 2H
HELD_OUT, and return to DEVELOPMENT engineering**. Do not lower the floors after
seeing results or select solely by maximizing abstention.

Among eligible candidates, use this ordered priority:

1. Lower false support rate.
2. Higher ALLOW recall.
3. Simpler / more deterministic implementation.
4. Lower runtime and operational complexity.

Candidate comparisons must document implementation determinism and operational
cost under declared conditions; those descriptions must not be invented after
HELD_OUT exposure. Resolve any remaining tie using DEVELOPMENT evidence and
record the owner decision before freezing one selected candidate. Do not use
HELD_OUT as a tiebreaker. Secondary aggregate metrics do not change this order.

Report gated preservation metrics alongside these four class-conditional rates.
Their denominators and definitions are fixed above; this protocol does not
invent an additional result-dependent eligibility floor. Future DEVELOPMENT
engineering may compare gate implementations within the frozen boundary, but
cannot retune BGE v0 or use Phase 2G private evidence.

## HELD_OUT release and single selected-candidate rule

The new 40-question HELD_OUT split remains private until all of these exist:

1. The independently authored benchmark, labels, split and custody hashes are
   frozen under owner review.
2. Authorized DEVELOPMENT results are complete.
3. Exactly one gate implementation has been selected by the rule above.
4. That implementation and its full configuration are frozen.
5. Its evaluator/scorer and reporting definitions are frozen.
6. A selection commit/tag records those identities and the unchanged BGE anchor.

Only after these gates may a separately authorized first HELD_OUT run evaluate
the **one selected gate**. Do not run multiple candidates on HELD_OUT for
selection, adjust a threshold or rule from its cases, or feed results back into
the frozen DEVELOPMENT comparison. Preserve result-bearing partial evidence;
no silent retry or later relabeling as a first run is permitted. Any later change
requires a separately versioned post-heldout phase and explicit owner scope.

## Phase 2H-A1 review and stop point

Review these documents together for the following fixed properties:

- ALLOW requires full material authoritative support; multi-section synthesis
  is allowed; otherwise ABSTAIN. The primary decision is mutually exclusive.
- Runtime input excludes all benchmark identity/label/rationale/support-list
  metadata. Corpus-level Gold and limited runtime evidence are distinguished.
- Deterministic required exact lookup and BGE v0 remain unchanged.
- Historical Phase 2G private evidence is quarantined; public aggregates motivate
  the gate but do not define it.
- The independent 80-question, balanced benchmark and hard-negative minimum are
  specified without authoring any question.
- Class-conditional and gated end-to-end metrics retain their complete Gold
  denominators, including false abstentions.
- Both 90% DEVELOPMENT floors and the ordered selection rule precede results;
  no eligible candidate means no selection and no HELD_OUT exposure.
- The new HELD_OUT can evaluate only the already selected, frozen gate.

Only this protocol and the companion contract are created in Phase 2H-A1. No
gate, benchmark records, executable schema, scorer or model test is implemented;
no private HELDOUT is accessed, BGE run, or result-bearing evaluation performed.
Historical artifacts, policy and retrieval source remain unchanged. No automatic
commit is authorized. **Stop for owner review; do not begin Phase 2H-A2.**
