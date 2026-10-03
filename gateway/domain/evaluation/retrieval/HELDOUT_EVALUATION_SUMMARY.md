# Selected BGE v0 primary HELDOUT evaluation

Frozen tag: `retrieval-ranked-v0.1-pre-heldout` at `d218143f0f900f493341ab1ed2e90e98c7ec47b4`.
Evaluation started: 2026-10-03T18:59:35.564124+00:00.
Model: BAAI/bge-small-en-v1.5, revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
Verified receipt: `57ebb2478204d765ca52dc11792fa36bc25a02f312536e49d2379dd18a348cb0`. Questions: 30 (26 ANSWERABLE, 4 NEGATIVE).
Questions with at least one recorded diagnostic failure: 14.

Aggregate metrics use the frozen DEVELOPMENT definitions. Gold relevance and required-section coverage are separate.
```json
{
  "answerable_count": 26,
  "full_required_set_success_at_k": {
    "10": {
      "count": 5,
      "rate": 1.0,
      "total": 5
    },
    "3": {
      "count": 3,
      "rate": 0.6,
      "total": 5
    },
    "5": {
      "count": 5,
      "rate": 1.0,
      "total": 5
    }
  },
  "hit_at_1": {
    "count": 21,
    "rate": 0.8076923076923077,
    "total": 26
  },
  "hit_at_3": {
    "count": 25,
    "rate": 0.9615384615384616,
    "total": 26
  },
  "mrr_at_10": 0.8910256410256411,
  "multi_required_question_count": 5,
  "negative_correct_abstention": {
    "count": 0,
    "rate": 0.0,
    "total": 4
  },
  "negative_count": 4,
  "negative_false_support": {
    "count": 4,
    "rate": 1.0,
    "total": 4
  },
  "required_coverage_at_k": {
    "1": {
      "macro_average": 0.6730769230769231,
      "micro": {
        "count": 19,
        "rate": 0.6129032258064516,
        "total": 31
      }
    },
    "10": {
      "macro_average": 1.0,
      "micro": {
        "count": 31,
        "rate": 1.0,
        "total": 31
      }
    },
    "3": {
      "macro_average": 0.9230769230769231,
      "micro": {
        "count": 28,
        "rate": 0.9032258064516129,
        "total": 31
      }
    },
    "5": {
      "macro_average": 0.9615384615384616,
      "micro": {
        "count": 30,
        "rate": 0.967741935483871,
        "total": 31
      }
    }
  }
}
```

No post-heldout tuning, model/threshold sweep, query instruction, rewriting, BM25 or RRF comparison preceded this primary result.
Limitations: one small project-specific 30-question evaluation; four negatives do not establish a general safety rate.
Cosine scores are retrieval diagnostics, not confidence or business accuracy. Cross-runtime identical embeddings are not claimed.
