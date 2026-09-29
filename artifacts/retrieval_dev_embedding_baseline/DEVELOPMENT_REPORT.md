# Phase 2D DEVELOPMENT embedding baseline

DEVELOPMENT only: the same frozen 15 questions and 25 stable SOP sections as Phase 2C.
No HELD_OUT question/result was accessed and no HELD_OUT evaluation occurred.
This is a baseline, not an improvement claim; it awaits owner review.
The model, original-query encoding, fields, normalization and 0.30 threshold were frozen before seeing Phase 2D results.
No model sweep, threshold sweep, query instruction, query rewriting or post-result tuning was performed.
Cosine similarity is a retrieval diagnostic, not confidence, probability, policy authority or business readiness.

Verified DEVELOPMENT receipt: `4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00`.
Model: `BAAI/bge-small-en-v1.5`, matching the repository configuration and the owner's explicit selection.

## Comparison with untouched BM25 v0

BM25 values below are read from historical Phase 2C artifacts; BM25 was not rerun or retuned for this comparison.
ANSWERABLE denominator: 14. NEGATIVE denominator: 1. Multi-required denominator: 3.

| Metric | BM25 v0 | Embedding baseline |
| --- | --- | --- |
| Hit@1 | 11/14 (0.785714) | 9/14 (0.642857) |
| Hit@3 | 11/14 (0.785714) | 12/14 (0.857143) |
| Negative correct abstention | 0/1 (0.000000) | 0/1 (0.000000) |
| Negative false support | 1/1 (1.000000) | 1/1 (1.000000) |
| MRR@10 | 0.792857 | 0.776786 |
| Required coverage@1, macro | 0.678571 | 0.535714 |
| Required coverage@1, micro | 11/17 (0.647059) | 9/17 (0.529412) |
| Required coverage@3, macro | 0.714286 | 0.857143 |
| Required coverage@3, micro | 12/17 (0.705882) | 15/17 (0.882353) |
| Required coverage@5, macro | 0.750000 | 0.928571 |
| Required coverage@5, micro | 13/17 (0.764706) | 16/17 (0.941176) |
| Required coverage@10, macro | 0.785714 | 1.000000 |
| Required coverage@10, micro | 14/17 (0.823529) | 17/17 (1.000000) |
| Multi-required full set@3 | 1/3 (0.333333) | 3/3 (1.000000) |
| Multi-required full set@5 | 2/3 (0.666667) | 3/3 (1.000000) |
| Multi-required full set@10 | 3/3 (1.000000) | 3/3 (1.000000) |

The single negative observation is not a general safety estimate. These Development results do not establish held-out superiority.

## Per-question metrics

| ID | Kind | First relevant rank | Hit@1 | Hit@3 | RR@10 | Abstained |
| --- | --- | --- | --- | --- | --- | --- |
| RQ003 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ006 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ009 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ012 | ANSWERABLE | 2 | False | True | 0.5 | False |
| RQ015 | ANSWERABLE | 8 | False | False | 0.125 | False |
| RQ016 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ019 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ022 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ025 | ANSWERABLE | 4 | False | False | 0.25 | False |
| RQ026 | ANSWERABLE | 2 | False | True | 0.5 | False |
| RQ029 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ032 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ035 | ANSWERABLE | 2 | False | True | 0.5 | False |
| RQ038 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ041 | NEGATIVE | None | None | None | None | False |

Every ranking, unrounded cosine score, Gold/required identity, coverage metric, abstention reason and negative outcome is retained in DEVELOPMENT_RESULTS.json.

## Failures

All missed reported targets are retained using the unchanged Phase 2C failure rubric.
Partial top-1 required coverage is unavoidable for multi-required questions and is not by itself a ranking defect.

### RQ009

- Required coverage@1: 1/2; absent: [('SOP-02', '1.0-demo', 'late-monitor')].

### RQ012

- First relevant rank: 2; top result ('SOP-05', '1.0-demo', 'stale-evidence') is not Gold-relevant.
- Required coverage@1: 0/1; absent: [('SOP-03', '1.0-demo', 'stale-monitor')].

### RQ015

- First relevant rank: 8; top result ('SOP-03', '1.0-demo', 'scan-scope') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-03', '1.0-demo', 'stale-monitor')].
- Required coverage@3: 0/1; absent: [('SOP-03', '1.0-demo', 'stale-monitor')].
- Required coverage@5: 0/1; absent: [('SOP-03', '1.0-demo', 'stale-monitor')].

### RQ019

- Required coverage@1: 1/2; absent: [('SOP-04', '1.0-demo', 'repeated-attempts')].

### RQ025

- First relevant rank: 4; top result ('SOP-04', '1.0-demo', 'attempt-counting') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-05', '1.0-demo', 'attempt-address-evidence')].
- Required coverage@3: 0/1; absent: [('SOP-05', '1.0-demo', 'attempt-address-evidence')].

### RQ026

- First relevant rank: 2; top result ('SOP-06', '1.0-demo', 'handoff-boundary') is not Gold-relevant.
- Required coverage@1: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].

### RQ029

- Required coverage@1: 1/2; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].

### RQ035

- First relevant rank: 2; top result ('SOP-06', '1.0-demo', 'handoff-boundary') is not Gold-relevant.
- Required coverage@1: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].

### RQ041

- Unsupported negative query returned ('SOP-06', '1.0-demo', 'handoff-boundary') with score 0.619689; no abstention.

## Frozen configuration

```json
{
  "abstention": {
    "also_abstain": [
      "blank query"
    ],
    "comparison": "top_score < threshold",
    "margin": null,
    "minimum_top_score": 0.3
  },
  "candidate_filter": "all sections; threshold applies to top score for the whole response",
  "cpu_threads": 1,
  "device": "cpu",
  "document_instruction": "",
  "encode_batch_size": 32,
  "encode_precision": "float32",
  "field_joiner": "LF",
  "model_id": "BAAI/bge-small-en-v1.5",
  "model_selection": "Owner-frozen repository-configured model; one model only",
  "normalize_embeddings": true,
  "pooling": "unmodified model snapshot configuration",
  "query_instruction": "",
  "query_transformation": "none; original question text",
  "retrieval_method": "EMBEDDING_COSINE",
  "score_meaning": "retrieval diagnostic; not confidence, probability, authority or business readiness",
  "searchable_fields": [
    "title",
    "section_title",
    "text"
  ],
  "section_count": 25,
  "similarity": "normalized dot product; math.fsum over unit vectors",
  "tie_breaking": "score descending, then (policy_id, version, section_id) ascending; no rounding",
  "top_k": 10,
  "vector_validation": "finite nonzero rows; L2 normalize in Python float precision"
}
```

## Runtime identity and reproducibility

```json
{
  "cache_scope": "dedicated Phase 2D model cache; absolute machine path omitted",
  "cpu_threads": 1,
  "device": "cpu",
  "document_instruction": "",
  "downloaded_files": [
    "1_Pooling/config.json",
    "config.json",
    "config_sentence_transformers.json",
    "model.safetensors",
    "modules.json",
    "sentence_bert_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt"
  ],
  "embedding_dimension": 384,
  "max_sequence_length": 512,
  "model_download_occurred": true,
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
  "model_id_is_not_a_repository_pinned_revision": true,
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
  "reproducibility_limit": "Revision and downloaded-file hashes are recorded for this run, but dependency versions and the default main revision are not all pinned in repository requirements; cross-runtime byte-identical embeddings are not claimed.",
  "requested_model_id": "BAAI/bge-small-en-v1.5",
  "requested_revision": "main",
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
  "weights_downloaded": true
}
```

Only the 25 sections are embedded, once per retriever instance, in canonical identity order. Queries are encoded independently.
There is no extra chunking, vector database, IT corpus, metadata keyword injection or automatic exact-lookup substitution.
The model's own tokenizer/pooling and sequence-length limit are retained. Input strings receive no application-level query transformation.
Model revision/file hashes and runtime versions identify this run; full cross-runtime byte-level reproducibility is not claimed.
The base commit does not contain the uncommitted candidate: RUN_MANIFEST.json records source hashes and output hashes separately.
Phase 2C inputs, implementation and historical artifacts remain unchanged. Stop for owner review after this first valid baseline.
