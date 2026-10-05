# Phase 2H-B1.1 DEVELOPMENT harness compatibility amendment

Status: **CANDIDATE_AWAITING_OWNER_REVIEW**

Harness: **v0.1.1 compatibility-amended before candidate/retrieval exposure**.

Original v0.1 was prepared 2026-10-04 against protocol commit
`347ce9f3ff37bd73f4750cde01562f0573a2b4ab` and subsequently owner-frozen at
`c8e73b77a9ef95e4d627766efefea3cabccf4f4a` /
`answerability-dev-harness-v0.1-pre-candidates`. That historical commit/tag is
unchanged. This v0.1.1 amendment remains uncommitted and awaits owner review.
See [DEVELOPMENT_HARNESS_AMENDMENT_V0_1_1.md](DEVELOPMENT_HARNESS_AMENDMENT_V0_1_1.md)
for the correction, before/after hashes and zero real retrieval/gate exposure.
No candidate has been selected or evaluated on the imported benchmark.

## Pinned source and custody

The runtime source is only the repository-local `DEVELOPMENT_MANIFEST.json`
and its 40 `development/AQnnn.json` paths. The frozen manifest SHA-256 is
`cae8a072192cad67b58e7d366afa9210972d672faa2e17047f2742e75a8499c2`; receipt is
`9913c3028119f708a19ad762efda5f86b80b1f78c624eddbd632d6129e5b802d`. See the
[import record](DEVELOPMENT_IMPORT_RECORD.md) for byte custody. Phase 2H
HELD_OUT was neither accessed nor imported, and no Phase 2G private data was
accessed. No private split is accepted as a runtime argument.

## Inference and external association

`GateInput` is a frozen, slotted dataclass with exactly `question`, `evidence`
and `active_bundle`. It preserves original question text. Evidence is an
immutable tuple of at most ten frozen `RankedEvidence` records containing
`rank`, `policy_id`, `version`, `section_id`, `title`, `section_title`, `body`
and unchanged `cosine_score`. Active metadata is a typed, frozen `ActiveBundle`
with `bundle_id`, `bundle_version`, `effective_from`, `effective_to`,
`manifest_sha256` and `registry_sha256`; the production entry checks these
against the pinned public authority. No arbitrary metadata dictionary exists.

The gate never receives question ID, split, expected decision, Gold reason,
difficulty, support shape, hard-negative status, Gold/required sections,
authoring rationale, review status, owner notes or benchmark family.
`EvaluationCase` and `RetrievalAssociation` remain evaluator-only. Association
uses question ID plus SHA-256 of the original question's UTF-8 text and is
validated before any gate call. The candidate protocol is only
`decide(GateInput) -> GateOutput`. This is an auditable API boundary, not an
operating-system sandbox for hostile Python plugins.

Supplied `FrozenRetrievalResult` records validate BGE model/revision, CPU,
25 sections, 384 dimensions, normalization, normalized dot product, 0.30
threshold, Top-10, no instruction and no rewriting. They reject duplicate
canonical identities, invalid ranks, excessive depth, nonfinite/out-of-range
scores, incorrect descending score order or canonical tie order. Per-item
scores use the complete cosine domain [-1, 1]; only the rank-1 score of a
nonempty response must meet the frozen whole-response threshold 0.30.
Lower-ranked returned evidence may be below 0.30, including negative scores,
and is preserved unchanged. No separate top_score field exists in the B1
input type; rank 1 supplies its unrounded response-level value. Production
also verifies that supplied identities belong to the active 25-section corpus.
Empty rankings are valid. No retrieval is executed by this harness. Typed
provenance does not by itself prove that an external producer actually ran BGE;
a later authorized baseline must preserve the frozen producer's evidence.

## Output and errors

`GateOutput` requires exactly ALLOW or ABSTAIN. Its reason is optional. ALLOW
may pair only with SUPPORTED_BY_ACTIVE_POLICY; ABSTAIN may pair with
INSUFFICIENT_POLICY_SUPPORT or UNRESOLVED_POLICY_CONTEXT. Strict dictionaries
with only these output fields are accepted and immediately copied into the
immutable output type; mutable candidate dictionaries are not retained.
Invalid outputs/pairings are not repaired. Inference runs once per question,
without retry, and outputs are collected before Gold scoring.

Missing associated output is MISSING_OUTPUT; invalid returned output is
MALFORMED_OUTPUT; candidate exceptions are CANDIDATE_EXCEPTION. Exceptions
retain only the stable code, not nondeterministic tracebacks/messages.
Errors have null predicted decision, fail binary correctness and gated
retrieval, remain in their original class denominators, and are separately
counted by code, Gold class and ID. They are never coerced to ABSTAIN or a third
class. Duplicate or unknown external result IDs fail loudly; missing retrieval
associations fail before any candidate call. Missing candidate observations
are explicitly scored as errors. A returned `None` is malformed; an absent
observation is missing.

## Scoring and eligibility

The primary metrics each retain denominator 20: ALLOW recall, false abstention
rate, correct abstention rate and false support rate. Valid opposite decisions
enter the corresponding error-rate numerator; contract errors enter neither
valid-decision numerator. Thus complementary rates can sum to less than one
for an invalid run. No item is silently excluded.

`meets_class_floors` requires at least 18 correct ALLOW and 18 correct ABSTAIN.
`valid_complete_run` requires zero candidate errors/missing outputs.
`eligible` is the conjunction, preserving the frozen protocol's requirement
that incomplete or invalid runs cannot establish eligibility. There is no
combined score or new threshold, and no candidate selection was performed.

Optional reason agreement is diagnostic only: correct binary/wrong compatible
reason stays binary-correct; wrong binary stays wrong. Agreement uses valid
emitted reasons, with its explicit count; omitted reasons are null, not
fabricated failures or successes. This never alters primary denominators.

For all 20 Gold ALLOW questions, both gated and ungated metrics use the same
supplied ranking: Hit@1/@3, required macro and micro coverage @3/@5/@10,
and multi-required full-set @3/@5/@10. Canonical identity is
`(policy_id, version, section_id)`, never a title. Gold ALLOW predicted ABSTAIN
or errored contributes zero gated success/coverage but remains in all applicable
denominators. Micro coverage retains every required assignment; multi-full
retains every multi-required item. The imported benchmark has six such items.
An empty multi-required denominator is rejected. Ungated metrics use the same
responses with the gate factor fixed to one.

Per-question rows contain the ID, Gold/predicted decision, binary correctness,
Gold/predicted reason, nullable reason correctness, stable candidate error and
retrieval count. ALLOW rows additionally contain required count and `gated` /
`ungated` objects with hit flags, required-found counts, coverage and nullable
multi-full flags. No question text/rationale is copied into score artifacts.

## Deterministic serialization

`deterministic_json_bytes` emits UTF-8, sorted keys, two-space indentation,
LF line endings and one final LF; nonfinite JSON constants are forbidden.
Rows and diagnostics are ID-sorted. Counts and coverage use exact integer /
Fraction arithmetic. Each metric stores `numerator`, `numerator_divisor`,
`denominator` and a twelve-decimal string `rate` rounded half-even. The exact
rate is `(numerator / numerator_divisor) / denominator`; ordinary counts have
divisor one, while macro coverage can have a fractional numerator. Eligibility
uses integer counts, never rounded strings. Timestamps/environment details
are excluded from score bytes. Reversed association order serializes identically.

## Historical v0.1 verification

The following 49-test result and pre-commit checks describe the historical B1
review. Current amendment verification is recorded below.

Focused unit tests: **49/49 PASS**, using Python 3.12.10 and stdlib
`unittest`. Scoring and candidate calls use entirely synthetic questions and
rankings, including tests of the production entry with a mocked synthetic
loader. Actual DEVELOPMENT files were used only for custody/structural checks.
No BGE, BM25, RRF, model initialization, model cache access or actual-data gate
baseline occurred. An isolated import test blocks socket events and verifies
that torch, transformers, sentence_transformers and huggingface_hub are absent.

```text
python -B -m unittest gateway.domain.tests.test_answerability_development_loader gateway.domain.tests.test_answerability_scoring gateway.domain.tests.test_answerability_evaluator_boundary -v
python -B -m gateway.domain.evaluation.answerability.evaluate_development_gate --validate-only
```

Structural loader validation: **PASS**, 40 input hashes, 20 ALLOW / 20 ABSTAIN,
matching receipt, zero retrieval/gate attempts. The CLI exposes only required
`--validate-only`, with abbreviation disabled. Redirect flags `--split`,
`--benchmark-dir`, `--manifest`, `--question-dir` are rejected before loading.
The programmatic production entry also has no path/split override.

Protected public file hashes: **52/52 unchanged**, including retrievers,
deterministic engine, policy corpus, original answerability protocol and
tracked Phase 2G evidence. The frozen 25 public section identities and all
eight SOP raw hashes passed validation. Git byte-preservation checks passed
for all 41 imported files. `git diff --check` passed; the index is empty.
Changed paths contain no HELD/heldout/held_out benchmark artifacts and no
model cache/weights. No commit or tag was created; Phase 2H-B2 was not begun.

## Source and test SHA-256

These hashes describe the review candidate's current raw working-tree bytes.

| File | SHA-256 of current raw bytes |
| --- | --- |
| `gateway/domain/evaluation/answerability/answerability_contracts.py` | `493e58d9be1e0758213a8c889c0a3119aa7189f71bbdb3082c8bf5cd116f78b0` |
| `gateway/domain/evaluation/answerability/answerability_scoring.py` | `b2fbdd4241328172909da11aa7959570b9f0ad6e8d35ee6123d93db140e73cf2` |
| `gateway/domain/evaluation/answerability/development_loader.py` | `be53712203cea92a956ab6d4d0b0c20f74b74c27825fadcc6e2c7079ced5b498` |
| `gateway/domain/evaluation/answerability/evaluate_development_gate.py` | `ba67767dacb232143ab95cb536371512294e43d65aa934da6665cf5d1e9e4e5e` |
| `gateway/domain/tests/_answerability_fixtures.py` | `c0fcdb98647a3530b18eddc0e2502282dc77a06b24155a349b554b6f2d95d7c0` |
| `gateway/domain/tests/test_answerability_development_loader.py` | `ea6f09720113c2c1971a46cab3621e1515479dc34a0dbfa0165dbf8549529201` |
| `gateway/domain/tests/test_answerability_evaluator_boundary.py` | `d36d94a64b18f448d12d6a08d2c031eac112cca8649f49435a5b8a7182667865` |
| `gateway/domain/tests/test_answerability_scoring.py` | `2d5bfc0de5663145555be4accfcd9e1414d940ee5baafd293e8ea09c83d3e246` |

The complete 53-file byte inventory (including all questions, manifest,
`.gitattributes`, the import/freeze/amendment records and tests) is in
[DEVELOPMENT_HARNESS_SHA256.json](DEVELOPMENT_HARNESS_SHA256.json). The inventory
excludes itself to avoid a circular digest; its hash is reported separately
at completion. It also records the 52 unchanged protected public hashes.

## Historical v0.1 pre-commit Git review scope (preserved)

`git diff --name-only` contains only `.gitattributes`; all new B1 files are
untracked. Full `git status --short --untracked-files=all`:

```text
 M .gitattributes
?? gateway/domain/evaluation/answerability/DEVELOPMENT_HARNESS_FREEZE_RECORD.md
?? gateway/domain/evaluation/answerability/DEVELOPMENT_HARNESS_SHA256.json
?? gateway/domain/evaluation/answerability/DEVELOPMENT_IMPORT_RECORD.md
?? gateway/domain/evaluation/answerability/DEVELOPMENT_MANIFEST.json
?? gateway/domain/evaluation/answerability/answerability_contracts.py
?? gateway/domain/evaluation/answerability/answerability_scoring.py
?? gateway/domain/evaluation/answerability/development/AQ001.json
?? gateway/domain/evaluation/answerability/development/AQ002.json
?? gateway/domain/evaluation/answerability/development/AQ003.json
?? gateway/domain/evaluation/answerability/development/AQ004.json
?? gateway/domain/evaluation/answerability/development/AQ005.json
?? gateway/domain/evaluation/answerability/development/AQ006.json
?? gateway/domain/evaluation/answerability/development/AQ007.json
?? gateway/domain/evaluation/answerability/development/AQ008.json
?? gateway/domain/evaluation/answerability/development/AQ009.json
?? gateway/domain/evaluation/answerability/development/AQ010.json
?? gateway/domain/evaluation/answerability/development/AQ011.json
?? gateway/domain/evaluation/answerability/development/AQ012.json
?? gateway/domain/evaluation/answerability/development/AQ013.json
?? gateway/domain/evaluation/answerability/development/AQ014.json
?? gateway/domain/evaluation/answerability/development/AQ015.json
?? gateway/domain/evaluation/answerability/development/AQ016.json
?? gateway/domain/evaluation/answerability/development/AQ017.json
?? gateway/domain/evaluation/answerability/development/AQ018.json
?? gateway/domain/evaluation/answerability/development/AQ019.json
?? gateway/domain/evaluation/answerability/development/AQ020.json
?? gateway/domain/evaluation/answerability/development/AQ021.json
?? gateway/domain/evaluation/answerability/development/AQ022.json
?? gateway/domain/evaluation/answerability/development/AQ023.json
?? gateway/domain/evaluation/answerability/development/AQ024.json
?? gateway/domain/evaluation/answerability/development/AQ025.json
?? gateway/domain/evaluation/answerability/development/AQ026.json
?? gateway/domain/evaluation/answerability/development/AQ027.json
?? gateway/domain/evaluation/answerability/development/AQ028.json
?? gateway/domain/evaluation/answerability/development/AQ029.json
?? gateway/domain/evaluation/answerability/development/AQ030.json
?? gateway/domain/evaluation/answerability/development/AQ031.json
?? gateway/domain/evaluation/answerability/development/AQ032.json
?? gateway/domain/evaluation/answerability/development/AQ033.json
?? gateway/domain/evaluation/answerability/development/AQ034.json
?? gateway/domain/evaluation/answerability/development/AQ035.json
?? gateway/domain/evaluation/answerability/development/AQ036.json
?? gateway/domain/evaluation/answerability/development/AQ037.json
?? gateway/domain/evaluation/answerability/development/AQ038.json
?? gateway/domain/evaluation/answerability/development/AQ039.json
?? gateway/domain/evaluation/answerability/development/AQ040.json
?? gateway/domain/evaluation/answerability/development_loader.py
?? gateway/domain/evaluation/answerability/evaluate_development_gate.py
?? gateway/domain/tests/_answerability_fixtures.py
?? gateway/domain/tests/test_answerability_development_loader.py
?? gateway/domain/tests/test_answerability_evaluator_boundary.py
?? gateway/domain/tests/test_answerability_scoring.py
```

Proposed commit, after owner approval: `Freeze Phase 2H development evaluator harness`.
Proposed tag, after owner approval: `answerability-dev-harness-v0.1-pre-candidates`.
Stop at owner review; this record does not grant candidate-run authorization.

## Current v0.1.1 amendment verification

Full B1 suite plus seven synthetic regressions: **56/56 PASS**. The exact
0.8 / 0.2 reconstruction passes; top <0.30 nonempty responses fail, and empty
responses remain valid. Dataclass fields/defaults are identical; scorer,
evaluator and loader bytes are unchanged. Three synthetic score artifacts
are byte-identical before/after. DEVELOPMENT custody passes with 40 unchanged
question hashes and the same manifest/receipt. All 52 protected public
source hashes match B1. Real DEVELOPMENT BGE queries, model initializations
and real gate invocations remain zero; neither phase's private heldout was
accessed. No B2 evidence exists.

The exact five-file amendment scope, changed source/test before/after hashes
and regression names are in the amendment record. The index is empty.
Proposed commit: `Correct frozen BGE evidence validation`.
Proposed new tag: `answerability-dev-harness-v0.1.1-pre-candidates`.
The original v0.1 tag must remain at its historical commit. Stop for owner
review; this amendment does not authorize a B2 run.
