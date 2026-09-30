# Ranked retriever selection — Phase 2F

Selection date: **2026-09-30**. Selected supplemental ranked retriever: **BGE embedding v0**.

This is a project-specific engineering selection from frozen DEVELOPMENT evidence, made before retrieval HELD_OUT exposure. It selects the already measured Phase 2D v0 implementation and configuration; it introduces no new retrieval configuration or tuning. BGE is not claimed to be universally superior.

## Selection identity

The working tree was clean before this task. The current committed Phase 2E baseline is `df69b489b24f410946de35a3cbbc922b6f044e72`.
Phase 2C and Phase 2D commit identities, the selection boundary, and the frozen receipt are recorded below.

```json
{
  "selection_date": "2026-09-30",
  "selection_scope": "DEVELOPMENT_ONLY",
  "selected_ranked_retriever": "BGE embedding v0",
  "phase_commits": {
    "phase_2c": "a81814d4478bbd0c1dffd98f0dce37988cd29031",
    "phase_2d": "212284b964b2ea867464574c66d9e587c4785231",
    "phase_2e": "df69b489b24f410946de35a3cbbc922b6f044e72"
  },
  "development_receipt_sha256": "4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00",
  "pre_selection_worktree": "CLEAN",
  "held_out_opened_during_selection": false,
  "post_baseline_tuning_performed": false
}
```

The deterministic engine tag `deterministic-engine-v0.1-pre-heldout` still resolves to `a528023e64ef523ea91741d8574cc431e7bae8e3`.

## Frozen DEVELOPMENT evidence

All nine tracked baseline artifacts were verified before writing this record. Results/report SHA-256 values match their run manifests; the manifests share the same frozen Development receipt. Historical model/configuration identities and the Phase 2C/2D hash links recorded by later runs also verify. No historical artifact was edited and no real baseline was rerun.

The denominator is 14 ANSWERABLE questions, with one separate NEGATIVE. Required coverage is the question-macro average; pooled section-micro counts are shown separately. Multi-required full-set success uses only the three questions requiring more than one section. MRR is displayed to six decimal places and percentages to two; exact values remain in the source JSON.

### BM25 v0

| Metric | Value |
| --- | --- |
| Hit@1 | 11/14 |
| Hit@3 | 11/14 |
| MRR@10 | 0.792857 |
| Required coverage@1 (macro) | 67.86% |
| Required coverage@1 (micro) | 11/17 |
| Required coverage@3 (macro) | 71.43% |
| Required coverage@3 (micro) | 12/17 |
| Required coverage@5 (macro) | 75.00% |
| Required coverage@5 (micro) | 13/17 |
| Required coverage@10 (macro) | 78.57% |
| Required coverage@10 (micro) | 14/17 |
| Multi-required full set@3 | 1/3 |
| Multi-required full set@5 | 2/3 |
| Multi-required full set@10 | 3/3 |
| Negative correct abstention | 0/1 |
| Negative false support | 1/1 |

### BGE embedding v0

| Metric | Value |
| --- | --- |
| Hit@1 | 9/14 |
| Hit@3 | 12/14 |
| MRR@10 | 0.776786 |
| Required coverage@1 (macro) | 53.57% |
| Required coverage@1 (micro) | 9/17 |
| Required coverage@3 (macro) | 85.71% |
| Required coverage@3 (micro) | 15/17 |
| Required coverage@5 (macro) | 92.86% |
| Required coverage@5 (micro) | 16/17 |
| Required coverage@10 (macro) | 100.00% |
| Required coverage@10 (micro) | 17/17 |
| Multi-required full set@3 | 3/3 |
| Multi-required full set@5 | 3/3 |
| Multi-required full set@10 | 3/3 |
| Negative correct abstention | 0/1 |
| Negative false support | 1/1 |

### Equal-weight RRF hybrid v0

| Metric | Value |
| --- | --- |
| Hit@1 | 9/14 |
| Hit@3 | 11/14 |
| MRR@10 | 0.737075 |
| Required coverage@1 (macro) | 53.57% |
| Required coverage@1 (micro) | 9/17 |
| Required coverage@3 (macro) | 71.43% |
| Required coverage@3 (micro) | 13/17 |
| Required coverage@5 (macro) | 85.71% |
| Required coverage@5 (micro) | 15/17 |
| Required coverage@10 (macro) | 100.00% |
| Required coverage@10 (micro) | 17/17 |
| Multi-required full set@3 | 3/3 |
| Multi-required full set@5 | 3/3 |
| Multi-required full set@10 | 3/3 |
| Negative correct abstention | 0/1 |
| Negative false support | 1/1 |

## Architectural rationale

Mandatory policy support already uses deterministic exact required-section lookup. That lookup remains authoritative for required policy identities and cannot be replaced by a semantically nearby ranked result. Ranked search is supplemental context for explanation and human review.

For this role, useful multi-section recall and required-section coverage at practical context depths are the primary engineering considerations. No synthetic overall score or metric weights are introduced; all first-rank metrics and limitations remain visible.

- BGE v0 has the highest Development Hit@3 (12/14), required coverage@3 (85.71%) and required coverage@5 (92.86%). It reaches complete required coverage@10 and complete multi-required full-set success already at depth 3.
- BM25 has stronger Hit@1 (11/14) and MRR@10 (0.792857), and remains a valuable historical baseline. Its supporting-section coverage is lower.
- Equal-weight RRF does not offer a better Development tradeoff than BGE: it retains complete coverage@10 and multi-required coverage but has lower Hit@3, lower coverage@3/@5, and the lowest MRR (0.737075) of the three.

The selected method is BGE alone with the existing Phase 2D v0 settings. No BM25 fallback or RRF layer is added. The evidence supports this project-specific selection; it does not establish general superiority or held-out performance.

## Known negative-abstention limitation — preserved

All three ranked systems falsely supported the single DEVELOPMENT negative question. Negative correct abstention is **0/1 for BM25, BGE and RRF**, and false support is **1/1 for each**. Score threshold alone is not demonstrated to be a reliable scope/answerability detector. One Development negative is not a safety or production estimate.

The BGE threshold remains 0.30. The known negative is not special-cased; no scope classifier, query rule, learned abstention rule, BM25 fallback or RRF repair is introduced. Frozen HELD_OUT negatives remain capable of testing this weakness.

## Freeze and custody

No tuning occurred after the three baseline evaluations or during selection. Retrieval HELD_OUT remained unopened during method selection. No private question, manifest, catalog, rationale or Gold was accessed, inferred or evaluated.

Selection source paths and exact SHA-256 values are recorded in [RETRIEVER_FREEZE_RECORD.md](RETRIEVER_FREEZE_RECORD.md), together with the selected configuration, 25-section corpus identity, runtime versions and exact model-file hashes.

This task ends before HELD_OUT release. The owner will review and separately commit the selection/freeze records; no commit or pre-heldout tag is created by this task.
