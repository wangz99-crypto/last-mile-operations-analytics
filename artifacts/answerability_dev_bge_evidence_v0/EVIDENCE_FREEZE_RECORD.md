# Phase 2H-B2 DEVELOPMENT BGE frozen evidence

Status: **OWNER_REVIEWED / FROZEN**

Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-05
Scientific owner review: **PASS**

The owner accepted the existing retrieval evidence and scientific conclusions
as-is. No retrieval rerun occurred after owner review. No gate evaluation or
HELD_OUT access occurred during this finalization. B3 has not begun.

Purpose: preserve one actual frozen BGE v0 response for each of the 40 frozen
DEVELOPMENT questions. Every future B3 candidate must consume these exact
evidence bytes. No candidate was implemented or evaluated; B3 has not begun.

Base: `e017a61ac160e9541356d7bc862c9d3b73061789` / `answerability-dev-harness-v0.1.1-pre-candidates`.
Historical B1: `c8e73b77a9ef95e4d627766efefea3cabccf4f4a` / `answerability-dev-harness-v0.1-pre-candidates`.
Both historical tags remain unchanged. The initial repository was clean before
B2 implementation; the exact authorized source changes at execution are in the
run manifest. No automatic commit or tag is made.

DEVELOPMENT manifest SHA-256: `cae8a072192cad67b58e7d366afa9210972d672faa2e17047f2742e75a8499c2`.
DEVELOPMENT receipt: `9913c3028119f708a19ad762efda5f86b80b1f78c624eddbd632d6129e5b802d`. All 40 hashes were revalidated by the pinned
B1.1 loader. No private authoring workspace was used.

Model: `BAAI/bge-small-en-v1.5` at exact revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, CPU, 384 dimensions.
The ten model files matched frozen Phase 2D hashes before initialization.
Offline environment controls and local_files_only=True were applied. Runtime
versions, local model provenance, socket events and zero downloads are recorded
in RUN_MANIFEST.json. No fallback model/revision/network was used.

The frozen eight-document / 25-section corpus uses readable document title +
LF + readable section title + LF + body. Original question text is encoded
without an instruction, rewrite or augmentation. Normalized vectors and frozen
normalized dot product are unchanged. The 0.30 threshold applies only to the
highest score for the entire response. Top-10 ordering is descending unrounded
score, then ascending canonical (policy_id, version, section_id). All actual
returned tail scores, including those below 0.30, are preserved; no filtering,
padding, deduplication, reranking or extra retrieval occurred.

Exactly one logical run completed: AQ001-AQ040 each queried once, 40 attempts,
40 successful responses, zero errors and zero retries. The append-only journal
durably records each attempt and actual response. Integrity validation and
GateInput reconstruction passed for all 40 stored rows without invoking a gate.
Evidence includes original question and externally associated ID/file/text
hashes; the reconstructed GateInput contains only original question, ranked
evidence and permitted active bundle metadata, with no evaluator annotations.

Serialization: UTF-8, sorted keys, two-space JSON indentation and final LF.
Python float JSON representations round-trip the exact stored binary64 scores;
no authoritative score is rounded. Evidence contains no timestamps. Environment
and run timestamps are separate. Serialization and all invariants were checked
from stored bytes without a second retrieval run.

## RETRIEVAL DIAGNOSTICS ONLY - NOT ANSWERABILITY-GATE ACCURACY

Gold ALLOW denominator: 20. Exact metrics use rational arithmetic. The displayed
decimal strings have 12 places; they do not change ranking or denominators.

| Metric | Exact numerator and denominator | Rate |
| --- | --- | --- |
| hit_at_1 | 14/1 divided by 20 | 0.700000000000 |
| hit_at_3 | 19/1 divided by 20 | 0.950000000000 |
| mrr_at_10 | 199/12 divided by 20 | 0.829166666667 |
| required_macro_coverage_at_3 | 18/1 divided by 20 | 0.900000000000 |
| required_micro_coverage_at_3 | 22/1 divided by 26 | 0.846153846154 |
| multi_required_full_at_3 | 3/1 divided by 6 | 0.500000000000 |
| required_macro_coverage_at_5 | 19/1 divided by 20 | 0.950000000000 |
| required_micro_coverage_at_5 | 24/1 divided by 26 | 0.923076923077 |
| multi_required_full_at_5 | 4/1 divided by 6 | 0.666666666667 |
| required_macro_coverage_at_10 | 20/1 divided by 20 | 1.000000000000 |
| required_micro_coverage_at_10 | 26/1 divided by 26 | 1.000000000000 |
| multi_required_full_at_10 | 6/1 divided by 6 | 1.000000000000 |

Overall retrieval responses: `{"question_count": 40, "retriever_abstention_count": 0, "returned_evidence_response_count": 40}`.
Gold ABSTAIN retrieval responses: `{"question_count": 20, "retriever_abstention_count": 0, "returned_evidence_response_count": 20}`.
These counts are retriever behavior, not gate correctness or gate eligibility.

## Evidence hashes

| Artifact | SHA-256 |
| --- | --- |
| `ATTEMPT_JOURNAL.jsonl` | `36ffeabce5cc978830aa87b0041604b77f9a445b060e943dd9393bcba699b101` |
| `DEVELOPMENT_BGE_EVIDENCE.json` | `1ba747fe7a6eaa97610d05fd3690048aa062723f87585e38725dd149b6a57a52` |
| `DEVELOPMENT_RETRIEVAL_METRICS.json` | `06ca57166401e6aaef726faa2d558ce698c5dddcb12749c39e814f9098a0933c` |

RUN_MANIFEST.json records this record's hash and those above; its own hash is
reported at completion, avoiding circular hashes. Sources, policy bytes and
25 canonical section hashes are recorded there as well. No B1.1 source,
retriever, policy, benchmark, Gold/required annotations or historical evidence
changed. No BM25/RRF, gate, parameter search, result-driven tuning, second run,
Phase 2H HELD_OUT access or Phase 2G private HELDOUT access occurred.

Stop for final owner verification. No commit or tag has been created. Proposed commit: `Freeze Phase 2H development BGE evidence`.
Proposed tag: `answerability-dev-evidence-v0.1-pre-candidates`.
