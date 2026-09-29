# Phase 2C DEVELOPMENT lexical baseline

Method-development results on 15 frozen DEVELOPMENT questions only. No HELD_OUT evaluation was performed.
This is a baseline, not an AI improvement or business-accuracy claim. Configuration awaits owner review.

Verified Development receipt: `4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00`.
Corpus: 8 SOP documents / 25 stable sections / version 1.0-demo. Exact required lookup remains separate.

Hit@1: 11/14 (0.785714).
Hit@3: 11/14 (0.785714).
MRR@10: 0.792857 (ANSWERABLE denominator 14).

| Depth | Required coverage, macro mean | Required coverage, micro count/rate |
| --- | --- | --- |
| 1 | 0.678571 | 11/17 (0.647059) |
| 3 | 0.714286 | 12/17 (0.705882) |
| 5 | 0.750000 | 13/17 (0.764706) |
| 10 | 0.785714 | 14/17 (0.823529) |

Full required-set success uses only the 3 questions with more than one required section.
- Top 3: 1/3 (0.333333).
- Top 5: 2/3 (0.666667).
- Top 10: 3/3 (1.000000).

NEGATIVE correct abstention: 0/1 (0.000000).
NEGATIVE false-support rate: 1/1 (1.000000).
The single negative case provides only one Development observation, not a general safety estimate.

## Per-question metrics

| ID | Kind | First relevant rank | Hit@1 | Hit@3 | RR@10 | Abstained |
| --- | --- | --- | --- | --- | --- | --- |
| RQ003 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ006 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ009 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ012 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ015 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ016 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ019 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ022 | ANSWERABLE | 10 | False | False | 0.1 | False |
| RQ025 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ026 | ANSWERABLE | None | False | False | 0.0 | False |
| RQ029 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ032 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ035 | ANSWERABLE | None | False | False | 0.0 | False |
| RQ038 | ANSWERABLE | 1 | True | True | 1.0 | False |
| RQ041 | NEGATIVE | None | None | None | None | False |

Full ranked identities, scores, Gold relevance and required-set metrics are in DEVELOPMENT_RESULTS.json.

## Observed failures

Every missed reported target is listed: Hit@1/3, complete required coverage at any reported depth, or negative abstention.
Partial top-1 coverage is unavoidable for multi-required questions; it is recorded without implying a ranking defect.
Descriptions report returned ranks and absent sections, without inferring hidden causes.

### RQ009

- Required coverage@1: 1/2; absent: [('SOP-02', '1.0-demo', 'late-boundaries')].
- Required coverage@3: 1/2; absent: [('SOP-02', '1.0-demo', 'late-boundaries')].

### RQ019

- Required coverage@1: 1/2; absent: [('SOP-04', '1.0-demo', 'attempt-counting')].

### RQ022

- First relevant rank: 10; top result ('SOP-04', '1.0-demo', 'attempt-counting') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-05', '1.0-demo', 'stale-evidence')].
- Required coverage@3: 0/1; absent: [('SOP-05', '1.0-demo', 'stale-evidence')].
- Required coverage@5: 0/1; absent: [('SOP-05', '1.0-demo', 'stale-evidence')].
- Required coverage@10: 0/1; absent: [('SOP-05', '1.0-demo', 'stale-evidence')].

### RQ026

- First relevant rank: None; top result ('SOP-01', '1.0-demo', 'scope') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].
- Required coverage@3: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].
- Required coverage@5: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].
- Required coverage@10: 0/1; absent: [('SOP-06', '1.0-demo', 'handoff-fields')].

### RQ029

- Required coverage@1: 1/2; absent: [('SOP-08', '1.0-demo', 'data-minimization')].
- Required coverage@3: 1/2; absent: [('SOP-08', '1.0-demo', 'data-minimization')].
- Required coverage@5: 1/2; absent: [('SOP-08', '1.0-demo', 'data-minimization')].

### RQ035

- First relevant rank: None; top result ('SOP-05', '1.0-demo', 'attempt-address-evidence') is not Gold-relevant.
- No Gold-relevant section within the first three unique results.
- Required coverage@1: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].
- Required coverage@3: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].
- Required coverage@5: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].
- Required coverage@10: 0/1; absent: [('SOP-07', '1.0-demo', 'missing-policy')].

### RQ041

- Unsupported negative query returned ('SOP-08', '1.0-demo', 'revision-history') with score 4.967323; no abstention.

## Configuration freeze candidate

The fixed defaults were selected before running this evaluation; no search over parameters or post-result tuning was performed.
Searchable fields are readable document title, readable section title and section body, each once, with no metadata keyword boosts.
Scores are lexical retrieval diagnostics, not business confidence. No stemming, synonyms, embeddings, models or query rewriting.

```json
{
  "abstention": {
    "also_abstain": [
      "empty token sequence",
      "no positive lexical overlap"
    ],
    "comparison": "top_score < threshold",
    "margin": null,
    "minimum_top_score": 1.0
  },
  "b": 0.75,
  "candidate_filter": "score > 0; threshold applies to top score for the whole response",
  "field_joiner": "LF",
  "field_weights": "equal; each field included once",
  "idf": "ln(1 + (N - df + 0.5) / (df + 0.5))",
  "k1": 1.5,
  "query_term_frequency": "binary; unique query tokens summed in sorted order",
  "retrieval_method": "LEXICAL_BM25",
  "score_meaning": "retrieval diagnostic only; not business confidence",
  "searchable_fields": [
    "title",
    "section_title",
    "text"
  ],
  "term_score": "idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))",
  "tie_breaking": "score descending, then (policy_id, version, section_id) ascending",
  "tokenizer": {
    "normalization": "str.lower",
    "pattern": "[a-z0-9]+",
    "punctuation": "split",
    "query_rewriting": false,
    "stemming": false,
    "stop_words": []
  },
  "top_k": 10
}
```

RUN_MANIFEST.json records the base code commit, uncommitted-code qualification, source hashes and output hashes.
Owner review is required before treating this configuration as final. No HELD_OUT question or result was accessed.
