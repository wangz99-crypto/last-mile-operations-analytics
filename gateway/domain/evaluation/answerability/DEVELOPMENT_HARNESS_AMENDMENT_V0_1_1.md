# Phase 2H-B1.1 - Pre-Exposure BGE Compatibility Amendment

Status: **CANDIDATE_AWAITING_OWNER_REVIEW**

Harness: **v0.1.1 compatibility-amended before candidate/retrieval exposure**.
Prepared 2026-10-04. This is a compatibility correction discovered before any
real Phase 2H DEVELOPMENT retrieval, not result-driven tuning.

## Immutable historical anchor and exposure state

Historical B1 commit: `c8e73b77a9ef95e4d627766efefea3cabccf4f4a`.
Historical B1 tag: `answerability-dev-harness-v0.1-pre-candidates`.
Both still resolve to that commit; no commit, tag or history was rewritten.
The pre-amendment working tree was clean and the B2 output directory did not
exist. The historical v0.1 source, documentation and inventory remain available
at that commit/tag. This document does not declare v0.1.1 frozen.

| State | Before correction | After correction |
| --- | --- | --- |
| Real Phase 2H DEVELOPMENT BGE queries | 0 | 0 |
| Real model initializations | 0 | 0 |
| Real gate/candidate invocations | 0 | 0 |
| Phase 2H HELD_OUT accessed | NO | NO |
| Phase 2G private HELDOUT accessed | NO | NO |
| B2 evidence directory created | NO | NO |
| Retrieval behavior changed | NO | NO |
| GateInput / GateOutput schema changed | NO | NO |
| Scoring changed | NO | NO |
| Benchmark changed | NO | NO |

The original B1 suite includes synthetic stub candidate calls; those are unit
fixtures, not real gate evaluations. No model or candidate received an AQ
question. Actual DEVELOPMENT was loaded only for custody/structural validation.

## Root cause and exact correction

Frozen BGE applies 0.30 to the highest score for the whole response. Once the
response qualifies, ranks 2-10 may be below 0.30; there is no per-item cutoff.
Original B1 incorrectly reused that response threshold as every item's lower
bound. The pre-run synthetic 0.8 / 0.2 reproduction therefore failed at rank 2.

Only two validation locations change in `answerability_contracts.py`:

1. A numeric, finite returned score is accepted over the complete mathematical
   cosine domain `[-1.0, 1.0]`. Booleans, non-numbers, nonfinite values and values
   outside that domain remain invalid. No empirical tolerance or new threshold
   is introduced, and no score is rounded, clamped or rewritten.
2. After existing rank, identity and descending-unrounded-score/tie-order
   validation, nonempty evidence requires its rank-1 score to be `>= 0.30`.
   Ranks 2-10 have no 0.30 floor. Empty evidence remains valid.

The unchanged B1 result representation has no separate `top_score` or response
status field. Its response-level score is exactly the stored rank-1 score;
there is no second score representation to reconcile here. Raw retriever
`top_score` metadata is outside this B1 type. A future evidence adapter must
verify any explicitly supplied raw `top_score` against rank 1 before constructing
this type. No adapter or B2 evidence is introduced by this amendment.

Rank sequence, maximum depth 10, canonical identities, uniqueness, descending
unrounded ordering and canonical tie-breaking are unchanged. No evidence is
filtered, deduplicated, fabricated or reordered. GateInput still consists only
of original question, immutable returned evidence and allowed active metadata.
No ID, split, labels, Gold/required support, rationale, difficulty, support shape,
hard-negative or review metadata enters the candidate boundary.

## Tests and preservation evidence

Full original B1 suite plus seven new regressions: **56/56 PASS**.
The original 49 tests remain; only the erroneous assertion that an individual
0.29 item is invalid was removed from the existing malformed-evidence loop.
The new response-level test rejects a nonempty response headed by that score.
All unrelated assertions and protections remain.

Exact new regression test names:

- `test_regression_top_0_8_tail_0_2_reconstructs_gate_input`
- `test_multiple_below_threshold_tails_include_negative_cosine`
- `test_nonempty_top_below_threshold_rejected_without_rounding`
- `test_top_equal_threshold_and_full_cosine_domain_accepted`
- `test_empty_frozen_abstention_reconstructs_gate_input`
- `test_complete_invalid_cosine_domain_rejected`
- `test_below_threshold_tails_preserve_ranking_guards`

The exact 0.8 / 0.2 GateInput path now succeeds without dropping its tail.
The 0.75 / 0.42 / 0.29 / 0.10 / -0.05 response succeeds unchanged. A top score
of 0.29 or the immediately preceding float below 0.30 fails; equality 0.30
passes. Empty evidence with valid bundle metadata passes. NaN, both infinities,
values immediately outside [-1,1], non-numbers and booleans fail. Incorrect
ranking, duplicate identity and reversed canonical ties still fail.

```text
python -B -m unittest gateway.domain.tests.test_answerability_development_loader gateway.domain.tests.test_answerability_scoring gateway.domain.tests.test_answerability_evaluator_boundary -v
python -B -m gateway.domain.evaluation.answerability.evaluate_development_gate --validate-only
```

All dataclass field declarations, annotations and defaults were compared by AST
before/after and are identical, including GateInput, GateOutput, RankedEvidence,
ActiveBundle and FrozenRetrievalResult. Original boundary-isolation tests pass.
The scorer, evaluator, loader and scoring tests retain identical raw byte hashes.
All four class denominators, error semantics, complete-run eligibility and both
18/20 floors, Hit@1/@3, coverage and multi-required scoring remain unchanged.

Three previously valid, entirely synthetic scoring cases serialize byte-for-byte
identically before and after this validation amendment:

| Synthetic scenario | Identical before/after serialized score SHA-256 |
| --- | --- |
| complete | `d86c49d40ea17ac67ea482dcf30c8c987335e61d5875af6c2f5682cdb9f9ca65` |
| errors | `748aeac18f6bd17209c42480c9e8b0c485a54d6ffde7bbdf98e418d640e14037` |
| wrong_decisions | `93ee81a4e738c84cc4c0b3dc93c11da545bb1283033fae928ea0438072fe7eab` |

## Custody and protected sources

DEVELOPMENT manifest SHA-256:
`cae8a072192cad67b58e7d366afa9210972d672faa2e17047f2742e75a8499c2`.

Recomputed receipt:
`9913c3028119f708a19ad762efda5f86b80b1f78c624eddbd632d6129e5b802d`.

Pinned loader: PASS, 40/40 hashes unchanged, AQ001-AQ040, 20 ALLOW / 20 ABSTAIN,
all OWNER_REVIEWED. No benchmark JSON, Gold or required set was edited.

Frozen embedding retriever SHA-256:
`4da7a8ccf26ca5987a9a37479466064e9acf526503b385116845b6daf52576d0`.

All 52 public hashes protected by the B1 inventory remain unchanged, including
retrieval sources, all policy/SOP files, the deterministic engine and historical
public evidence. No private authoring or heldout files were used. No query,
model/revision, normalization, section text, threshold, top_k or retriever
configuration changed. No BGE/BM25/RRF run or real retrieval metrics occurred.

## Changed source/test hashes

| File | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `gateway/domain/evaluation/answerability/answerability_contracts.py` | `8ab0e6f417b6c3d32a42d31aa5c05426af3fd0c7171ca4e66a9d0cc72a15b7f3` | `493e58d9be1e0758213a8c889c0a3119aa7189f71bbdb3082c8bf5cd116f78b0` |
| `gateway/domain/tests/test_answerability_evaluator_boundary.py` | `32ae0c07bb9efdda84d7c4ae683969c7749e32fc9e42111eda6a5c30f12b6217` | `d36d94a64b18f448d12d6a08d2c031eac112cca8649f49435a5b8a7182667865` |

Hashes describe current raw working-tree bytes. The updated
[SHA-256 inventory](DEVELOPMENT_HARNESS_SHA256.json) records the amendment and
current harness record, while preserving historical v0.1 inventory provenance.
The inventory excludes itself to avoid circular hashing.

## Owner review and Git scope

Only five files change: two executable/test files above, this new amendment,
the linked [harness freeze record](DEVELOPMENT_HARNESS_FREEZE_RECORD.md), and
the SHA-256 inventory. No `.gitattributes`, retrieval, policy, engine, AQ or B2
file changes. The index remains empty.

Expected final `git status --short` (verified at completion):

```text
 M gateway/domain/evaluation/answerability/DEVELOPMENT_HARNESS_FREEZE_RECORD.md
 M gateway/domain/evaluation/answerability/DEVELOPMENT_HARNESS_SHA256.json
 M gateway/domain/evaluation/answerability/answerability_contracts.py
 M gateway/domain/tests/test_answerability_evaluator_boundary.py
?? gateway/domain/evaluation/answerability/DEVELOPMENT_HARNESS_AMENDMENT_V0_1_1.md
```

`git diff --name-only` contains the four modified tracked files above; the new
amendment appears as untracked in status. No commit or tag was created.
Proposed commit: `Correct frozen BGE evidence validation`.
Proposed new tag: `answerability-dev-harness-v0.1.1-pre-candidates`.
Stop for owner review. Do not begin B2 without its separate authorization.
