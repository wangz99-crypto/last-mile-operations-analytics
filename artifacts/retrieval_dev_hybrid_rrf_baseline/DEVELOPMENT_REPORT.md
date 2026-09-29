# Phase 2E DEVELOPMENT equal-weight RRF baseline

DEVELOPMENT only: 15 frozen questions (14 ANSWERABLE, 1 NEGATIVE) over the same verified 25 stable SOP sections.
No HELD_OUT material was accessed or evaluated. One negative observation is not a safety estimate.
RRF parameters were fixed before evaluation: k=60, weights 1.0/1.0, component depths 10/10, final top_k=10.
No weight search, RRF-k search, model search, threshold tuning or post-result tuning was performed.
Raw component scores are not fused. Original queries are passed to both components without an instruction or rewriting.
RRF score is not confidence, probability, authority, evidence completeness, action state, priority or readiness.
These are observed Development differences, not a claim that the hybrid is superior.

Verified DEVELOPMENT receipt: `4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00`.
Exact BGE revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`. Historical results are verified read-only evidence; live components produce the hybrid ranks.

## All frozen metrics

| Metric | BM25 v0 | BGE embedding v0 | Equal-weight RRF hybrid v0 |
| --- | --- | --- | --- |
| Hit@1 | 11/14 (0.785714) | 9/14 (0.642857) | 9/14 (0.642857) |
| Hit@3 | 11/14 (0.785714) | 12/14 (0.857143) | 11/14 (0.785714) |
| MRR@10 | 0.792857 | 0.776786 | 0.737075 |
| Required coverage@1, macro | 0.678571 | 0.535714 | 0.535714 |
| Required coverage@1, micro | 11/17 (0.647059) | 9/17 (0.529412) | 9/17 (0.529412) |
| Required coverage@3, macro | 0.714286 | 0.857143 | 0.714286 |
| Required coverage@3, micro | 12/17 (0.705882) | 15/17 (0.882353) | 13/17 (0.764706) |
| Required coverage@5, macro | 0.750000 | 0.928571 | 0.857143 |
| Required coverage@5, micro | 13/17 (0.764706) | 16/17 (0.941176) | 15/17 (0.882353) |
| Required coverage@10, macro | 0.785714 | 1.000000 | 1.000000 |
| Required coverage@10, micro | 14/17 (0.823529) | 17/17 (1.000000) | 17/17 (1.000000) |
| Multi-required full set@3 | 1/3 (0.333333) | 3/3 (1.000000) | 3/3 (1.000000) |
| Multi-required full set@5 | 2/3 (0.666667) | 3/3 (1.000000) | 3/3 (1.000000) |
| Multi-required full set@10 | 3/3 (1.000000) | 3/3 (1.000000) | 3/3 (1.000000) |
| Negative correct abstention | 0/1 (0.000000) | 0/1 (0.000000) | 0/1 (0.000000) |
| Negative false support | 1/1 (1.000000) | 1/1 (1.000000) | 1/1 (1.000000) |

The full-set denominator is the three questions with more than one required section.

## Per-question diagnostics

| ID | First relevant rank | Hit@1 | Hit@3 | RR@10 | Hybrid abstained | BM25 status | BGE status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RQ003 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ006 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ009 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ012 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ015 | 5 | False | False | 0.2 | False | RETRIEVED | RETRIEVED |
| RQ016 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ019 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ022 | 3 | False | True | 0.3333333333333333 | False | RETRIEVED | RETRIEVED |
| RQ025 | 2 | False | True | 0.5 | False | RETRIEVED | RETRIEVED |
| RQ026 | 7 | False | False | 0.14285714285714285 | False | RETRIEVED | RETRIEVED |
| RQ029 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ032 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ035 | 7 | False | False | 0.14285714285714285 | False | RETRIEVED | RETRIEVED |
| RQ038 | 1 | True | True | 1.0 | False | RETRIEVED | RETRIEVED |
| RQ041 | None | None | None | None | False | RETRIEVED | RETRIEVED |

DEVELOPMENT_RESULTS.json retains original queries, every fused identity and unrounded RRF score, both contributing ranks, full component top-10 rankings/statuses/reasons, Gold and required sections, all coverage metrics and negative outcomes.
The component rank lists include candidates outside the final top 10 so movements remain inspectable without inferring hidden causes.

## Failures

All failures use the unchanged Phase 2C rubric. Partial top-1 coverage is unavoidable for multi-required questions and is not by itself a defect.

### RQ009

- Required coverage@1: 1/2; absent: [('SOP-02', '1.0-demo', 'late-boundaries')].

### RQ015

- First relevant rank: 5; top result ('SOP-03', '1.0-demo', 'scan-scope') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-03', '1.0-demo', 'stale-monitor')].
- Required coverage@3: 0/1; absent: [('SOP-03', '1.0-demo', 'stale-monitor')].

### RQ019

- Required coverage@1: 1/2; absent: [('SOP-04', '1.0-demo', 'repeated-attempts')].

### RQ022

- First relevant rank: 3; top result ('SOP-04', '1.0-demo', 'attempt-counting') is not Gold-relevant.
- Required coverage@1: 0/1; absent: [('SOP-05', '1.0-demo', 'stale-evidence')].
- Required coverage@3: 0/1; absent: [('SOP-05', '1.0-demo', 'stale-evidence')].

### RQ025

- First relevant rank: 2; top result ('SOP-04', '1.0-demo', 'single-attempt') is not Gold-relevant.
- Required coverage@1: 0/1; absent: [('SOP-05', '1.0-demo', 'attempt-address-evidence')].

### RQ026

- First relevant rank: 7; top result ('SOP-06', '1.0-demo', 'handoff-boundary') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].
- Required coverage@3: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].
- Required coverage@5: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].

### RQ029

- Required coverage@1: 1/2; absent: [('SOP-08', '1.0-demo', 'data-minimization')].

### RQ035

- First relevant rank: 7; top result ('SOP-01', '1.0-demo', 'state-precedence') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].
- Required coverage@3: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].
- Required coverage@5: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].

### RQ041

- Unsupported negative query returned ('SOP-02', '1.0-demo', 'late-monitor') with score 0.031754; no abstention.

## Frozen configuration

```json
{
  "abstention": "both components ABSTAIN; no additional hybrid threshold or margin",
  "bm25_component_depth": 10,
  "bm25_weight": 1.0,
  "candidate_set": "union of identities returned by non-abstaining components",
  "component_ranks": "one-based returned positions; first occurrence only; duplicate positions are not compressed",
  "embedding_component_depth": 10,
  "embedding_weight": 1.0,
  "formula": "sum(weight / (60 + component_rank) for components containing the identity)",
  "fusion_method": "Reciprocal Rank Fusion",
  "query_transformation": "none; original query passed to both components",
  "raw_component_scores_used": false,
  "retrieval_method": "HYBRID_RRF",
  "rrf_k": 60,
  "score_meaning": "retrieval diagnostic only; not confidence, probability, authority, completeness or business state",
  "tie_breaking": "RRF score descending, then canonical identity ascending; no rounding",
  "top_k": 10
}
```

## Runtime identity

```json
{
  "cache_scope": "dedicated Phase 2D model cache; absolute machine path omitted",
  "cpu_threads": 1,
  "device": "cpu",
  "document_instruction": "",
  "downloaded_files": [],
  "embedding_dimension": 384,
  "evaluation_revision_pinned": true,
  "max_sequence_length": 512,
  "model_download_occurred": false,
  "model_file_sha256": {
    "1_Pooling/config.json": "d1caf60c96f5fba2157c0c26b76d80818fad6cf0b8eb5e73ec372ff9818eba5c",
    "config.json": "094f8e891b932f2000c92cfc663bac4c62069f5d8af5b5278c4306aef3084750",
    "config_sentence_transformers.json": "940d5f50db195fa6e5e6a4f122c095f77880de259d74b14a65779ed48bdd7c56",
    "model.safetensors": "3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad",
    "modules.json": "84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf",
    "sentence_bert_config.json": "84e39fda68ccbff05bfa723ae9c0e70e23e2ec373b76e0f8c6e71af72a693cbf",
    "special_tokens_map.json": "b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3",
    "tokenizer.json": "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66",
    "tokenizer_config.json": "9261e7d79b44c8195c1cada2b453e55b00aeb81e907a6664974b4d7776172ab3",
    "vocab.txt": "07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3"
  },
  "model_id_is_not_a_repository_pinned_revision": false,
  "normalize_embeddings": true,
  "pooling_configuration": {
    "include_prompt": true,
    "pooling_mode_cls_token": true,
    "pooling_mode_lasttoken": false,
    "pooling_mode_max_tokens": false,
    "pooling_mode_mean_sqrt_len_tokens": false,
    "pooling_mode_mean_tokens": false,
    "pooling_mode_weightedmean_tokens": false,
    "word_embedding_dimension": 384
  },
  "python_version": "3.12.10",
  "query_instruction": "",
  "reproducibility_limit": "This evaluation pins the exact model revision and verifies Phase 2D model-file hashes. Dependency versions are recorded but not all repository-pinned; byte-identical embeddings across arbitrary runtimes are not claimed.",
  "requested_model_id": "BAAI/bge-small-en-v1.5",
  "requested_revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a",
  "resolved_model_revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a",
  "revision_pinned_for_this_load": true,
  "similarity": "normalized dot product",
  "truncation": "unmodified SentenceTransformer tokenizer/model maximum; no additional chunking",
  "versions": {
    "huggingface-hub": "0.36.2",
    "numpy": "2.5.3",
    "sentence-transformers": "3.0.1",
    "torch": "2.14.0",
    "transformers": "4.57.6"
  },
  "weights_downloaded": false
}
```

RUN_MANIFEST.json records historical artifact hashes, input and source hashes, the current base commit and frozen output hashes.
Uncommitted candidate source is distinguished from the base commit. Cross-runtime byte-identical embedding vectors are not claimed.
No new hybrid threshold, chunks, vector database or raw-score blending is used. Both components must abstain for hybrid abstention.
Phase 2C/2D artifact bytes remain unchanged. Stop after this first valid baseline for owner review.
