# Phase 2H-B3 DEVELOPMENT gate baselines, Round 1

Status: CANDIDATE_AWAITING_OWNER_REVIEW

Purpose: evaluate the five owner-specified deterministic assumptions against frozen DEVELOPMENT evidence.
No candidate is selected. These are DEVELOPMENT observations, not HELD_OUT claims.

Base: `e2c363f150f5494b85bcf4de2e7800c57727d92a` / `answerability-dev-evidence-v0.1-pre-candidates`.
DEVELOPMENT: AQ001-AQ040, 20 ALLOW / 20 ABSTAIN; receipt `9913c3028119f708a19ad762efda5f86b80b1f78c624eddbd632d6129e5b802d`.
B2 evidence SHA-256: `1ba747fe7a6eaa97610d05fd3690048aa062723f87585e38725dd149b6a57a52`.
Pre-evaluation registry SHA-256: `9fa84e37ab4d990aef8da3588f5ea590d6b43c648b7f2b19b861ac9b7e8c5117`.
Pre-evaluation tests: 95 passed, zero failures/errors.

## Pre-evaluation source hashes

- `gateway/domain/evaluation/answerability/gates/baseline_gates.py`: `50074e9c04f7d4437f418db7ce71824f9b9c03ec34e3fc567f96d809ae2fe308`
- `gateway/domain/evaluation/answerability/evaluate_baseline_gates.py`: `f5ca4595a475e47f3ea140377922e90719ad3112891d5c7087395a0b262e5c69`
- `gateway/domain/tests/test_answerability_baseline_gates.py`: `3917be00ba53f7412a91ed41d53ee73c33b577465944260afa26d6b0d6782e66`

## Results

Each candidate consumed the same 40 frozen GateInputs exactly once. Errors remain in fixed denominators.
Eligibility requires both >=18/20 class successes and structural validity; controls are always ineligible.
Secondary metrics and reason agreement are descriptive only.

### CONTROL_ALWAYS_ALLOW

Control only: True. Eligible: False.

| Primary metric | Exact value and rate |
| --- | --- |
| allow_recall | 20/1 divided by 20 = 1.000000000000 |
| false_abstention_rate | 0/1 divided by 20 = 0.000000000000 |
| correct_abstention_rate | 0/1 divided by 20 = 0.000000000000 |
| false_support_rate | 20/1 divided by 20 = 1.000000000000 |

| Secondary metric | Exact value and rate |
| --- | --- |
| overall_accuracy | 20/1 divided by 40 = 0.500000000000 |
| balanced_accuracy | 1/1 divided by 2 = 0.500000000000 |
| macro_f1 | 2/3 divided by 2 = 0.333333333333 |
| reason_code_agreement | 20/1 divided by 40 = 0.500000000000 |
| candidate_error_count | 0 |

Gated retrieval: Gold ALLOW denominator remains 20, required sections 26, multi-required questions 6.
False ABSTAIN contributes zero; metrics are not conditional on predicted ALLOW.

| Gated retrieval metric | Exact value and rate |
| --- | --- |
| hit_at_1 | 14/1 divided by 20 = 0.700000000000 |
| hit_at_3 | 19/1 divided by 20 = 0.950000000000 |
| required_macro_coverage_at_3 | 18/1 divided by 20 = 0.900000000000 |
| required_micro_coverage_at_3 | 22/1 divided by 26 = 0.846153846154 |
| multi_required_full_at_3 | 3/1 divided by 6 = 0.500000000000 |
| required_macro_coverage_at_5 | 19/1 divided by 20 = 0.950000000000 |
| required_micro_coverage_at_5 | 24/1 divided by 26 = 0.923076923077 |
| multi_required_full_at_5 | 4/1 divided by 6 = 0.666666666667 |
| required_macro_coverage_at_10 | 20/1 divided by 20 = 1.000000000000 |
| required_micro_coverage_at_10 | 26/1 divided by 26 = 1.000000000000 |
| multi_required_full_at_10 | 6/1 divided by 6 = 1.000000000000 |

| Diagnostic group | Subgroup | Binary correct / total |
| --- | --- | --- |
| gold_class | ALLOW | 20/20 |
| gold_class | ABSTAIN | 0/20 |
| abstain_reason | INSUFFICIENT_POLICY_SUPPORT | 0/16 |
| abstain_reason | UNRESOLVED_POLICY_CONTEXT | 0/4 |
| difficulty | DIRECT | 6/10 |
| difficulty | PARAPHRASE | 8/16 |
| difficulty | INDIRECT_OPERATIONAL | 6/14 |
| allow_support_shape | SINGLE_SECTION | 14/14 |
| allow_support_shape | MULTI_SECTION | 6/6 |
| hard_negative | true | 0/16 |
| hard_negative | false | 20/24 |

Failure IDs (post-inference diagnostics only):

- false_abstentions: none
- false_supports: AQ021, AQ022, AQ023, AQ024, AQ025, AQ026, AQ027, AQ028, AQ029, AQ030, AQ031, AQ032, AQ033, AQ034, AQ035, AQ036, AQ037, AQ038, AQ039, AQ040
- candidate_errors: none
- wrong_reason_only: none

### CONTROL_ALWAYS_ABSTAIN

Control only: True. Eligible: False.

| Primary metric | Exact value and rate |
| --- | --- |
| allow_recall | 0/1 divided by 20 = 0.000000000000 |
| false_abstention_rate | 20/1 divided by 20 = 1.000000000000 |
| correct_abstention_rate | 20/1 divided by 20 = 1.000000000000 |
| false_support_rate | 0/1 divided by 20 = 0.000000000000 |

| Secondary metric | Exact value and rate |
| --- | --- |
| overall_accuracy | 20/1 divided by 40 = 0.500000000000 |
| balanced_accuracy | 1/1 divided by 2 = 0.500000000000 |
| macro_f1 | 2/3 divided by 2 = 0.333333333333 |
| reason_code_agreement | 16/1 divided by 40 = 0.400000000000 |
| candidate_error_count | 0 |

Gated retrieval: Gold ALLOW denominator remains 20, required sections 26, multi-required questions 6.
False ABSTAIN contributes zero; metrics are not conditional on predicted ALLOW.

| Gated retrieval metric | Exact value and rate |
| --- | --- |
| hit_at_1 | 0/1 divided by 20 = 0.000000000000 |
| hit_at_3 | 0/1 divided by 20 = 0.000000000000 |
| required_macro_coverage_at_3 | 0/1 divided by 20 = 0.000000000000 |
| required_micro_coverage_at_3 | 0/1 divided by 26 = 0.000000000000 |
| multi_required_full_at_3 | 0/1 divided by 6 = 0.000000000000 |
| required_macro_coverage_at_5 | 0/1 divided by 20 = 0.000000000000 |
| required_micro_coverage_at_5 | 0/1 divided by 26 = 0.000000000000 |
| multi_required_full_at_5 | 0/1 divided by 6 = 0.000000000000 |
| required_macro_coverage_at_10 | 0/1 divided by 20 = 0.000000000000 |
| required_micro_coverage_at_10 | 0/1 divided by 26 = 0.000000000000 |
| multi_required_full_at_10 | 0/1 divided by 6 = 0.000000000000 |

| Diagnostic group | Subgroup | Binary correct / total |
| --- | --- | --- |
| gold_class | ALLOW | 0/20 |
| gold_class | ABSTAIN | 20/20 |
| abstain_reason | INSUFFICIENT_POLICY_SUPPORT | 16/16 |
| abstain_reason | UNRESOLVED_POLICY_CONTEXT | 4/4 |
| difficulty | DIRECT | 4/10 |
| difficulty | PARAPHRASE | 8/16 |
| difficulty | INDIRECT_OPERATIONAL | 8/14 |
| allow_support_shape | SINGLE_SECTION | 0/14 |
| allow_support_shape | MULTI_SECTION | 0/6 |
| hard_negative | true | 16/16 |
| hard_negative | false | 4/24 |

Failure IDs (post-inference diagnostics only):

- false_abstentions: AQ001, AQ002, AQ003, AQ004, AQ005, AQ006, AQ007, AQ008, AQ009, AQ010, AQ011, AQ012, AQ013, AQ014, AQ015, AQ016, AQ017, AQ018, AQ019, AQ020
- false_supports: none
- candidate_errors: none
- wrong_reason_only: AQ033, AQ034, AQ035, AQ036

### BASELINE_RETRIEVAL_RESPONSE

Control only: False. Eligible: False.

| Primary metric | Exact value and rate |
| --- | --- |
| allow_recall | 20/1 divided by 20 = 1.000000000000 |
| false_abstention_rate | 0/1 divided by 20 = 0.000000000000 |
| correct_abstention_rate | 0/1 divided by 20 = 0.000000000000 |
| false_support_rate | 20/1 divided by 20 = 1.000000000000 |

| Secondary metric | Exact value and rate |
| --- | --- |
| overall_accuracy | 20/1 divided by 40 = 0.500000000000 |
| balanced_accuracy | 1/1 divided by 2 = 0.500000000000 |
| macro_f1 | 2/3 divided by 2 = 0.333333333333 |
| reason_code_agreement | 20/1 divided by 40 = 0.500000000000 |
| candidate_error_count | 0 |

Gated retrieval: Gold ALLOW denominator remains 20, required sections 26, multi-required questions 6.
False ABSTAIN contributes zero; metrics are not conditional on predicted ALLOW.

| Gated retrieval metric | Exact value and rate |
| --- | --- |
| hit_at_1 | 14/1 divided by 20 = 0.700000000000 |
| hit_at_3 | 19/1 divided by 20 = 0.950000000000 |
| required_macro_coverage_at_3 | 18/1 divided by 20 = 0.900000000000 |
| required_micro_coverage_at_3 | 22/1 divided by 26 = 0.846153846154 |
| multi_required_full_at_3 | 3/1 divided by 6 = 0.500000000000 |
| required_macro_coverage_at_5 | 19/1 divided by 20 = 0.950000000000 |
| required_micro_coverage_at_5 | 24/1 divided by 26 = 0.923076923077 |
| multi_required_full_at_5 | 4/1 divided by 6 = 0.666666666667 |
| required_macro_coverage_at_10 | 20/1 divided by 20 = 1.000000000000 |
| required_micro_coverage_at_10 | 26/1 divided by 26 = 1.000000000000 |
| multi_required_full_at_10 | 6/1 divided by 6 = 1.000000000000 |

| Diagnostic group | Subgroup | Binary correct / total |
| --- | --- | --- |
| gold_class | ALLOW | 20/20 |
| gold_class | ABSTAIN | 0/20 |
| abstain_reason | INSUFFICIENT_POLICY_SUPPORT | 0/16 |
| abstain_reason | UNRESOLVED_POLICY_CONTEXT | 0/4 |
| difficulty | DIRECT | 6/10 |
| difficulty | PARAPHRASE | 8/16 |
| difficulty | INDIRECT_OPERATIONAL | 6/14 |
| allow_support_shape | SINGLE_SECTION | 14/14 |
| allow_support_shape | MULTI_SECTION | 6/6 |
| hard_negative | true | 0/16 |
| hard_negative | false | 20/24 |

Failure IDs (post-inference diagnostics only):

- false_abstentions: none
- false_supports: AQ021, AQ022, AQ023, AQ024, AQ025, AQ026, AQ027, AQ028, AQ029, AQ030, AQ031, AQ032, AQ033, AQ034, AQ035, AQ036, AQ037, AQ038, AQ039, AQ040
- candidate_errors: none
- wrong_reason_only: none

### BASELINE_TOP1_LEXICAL_60

Control only: False. Eligible: False.

| Primary metric | Exact value and rate |
| --- | --- |
| allow_recall | 1/1 divided by 20 = 0.050000000000 |
| false_abstention_rate | 19/1 divided by 20 = 0.950000000000 |
| correct_abstention_rate | 20/1 divided by 20 = 1.000000000000 |
| false_support_rate | 0/1 divided by 20 = 0.000000000000 |

| Secondary metric | Exact value and rate |
| --- | --- |
| overall_accuracy | 21/1 divided by 40 = 0.525000000000 |
| balanced_accuracy | 21/20 divided by 2 = 0.525000000000 |
| macro_f1 | 958/1239 divided by 2 = 0.386602098467 |
| reason_code_agreement | 17/1 divided by 40 = 0.425000000000 |
| candidate_error_count | 0 |

Gated retrieval: Gold ALLOW denominator remains 20, required sections 26, multi-required questions 6.
False ABSTAIN contributes zero; metrics are not conditional on predicted ALLOW.

| Gated retrieval metric | Exact value and rate |
| --- | --- |
| hit_at_1 | 1/1 divided by 20 = 0.050000000000 |
| hit_at_3 | 1/1 divided by 20 = 0.050000000000 |
| required_macro_coverage_at_3 | 1/1 divided by 20 = 0.050000000000 |
| required_micro_coverage_at_3 | 1/1 divided by 26 = 0.038461538462 |
| multi_required_full_at_3 | 0/1 divided by 6 = 0.000000000000 |
| required_macro_coverage_at_5 | 1/1 divided by 20 = 0.050000000000 |
| required_micro_coverage_at_5 | 1/1 divided by 26 = 0.038461538462 |
| multi_required_full_at_5 | 0/1 divided by 6 = 0.000000000000 |
| required_macro_coverage_at_10 | 1/1 divided by 20 = 0.050000000000 |
| required_micro_coverage_at_10 | 1/1 divided by 26 = 0.038461538462 |
| multi_required_full_at_10 | 0/1 divided by 6 = 0.000000000000 |

| Diagnostic group | Subgroup | Binary correct / total |
| --- | --- | --- |
| gold_class | ALLOW | 1/20 |
| gold_class | ABSTAIN | 20/20 |
| abstain_reason | INSUFFICIENT_POLICY_SUPPORT | 16/16 |
| abstain_reason | UNRESOLVED_POLICY_CONTEXT | 4/4 |
| difficulty | DIRECT | 5/10 |
| difficulty | PARAPHRASE | 8/16 |
| difficulty | INDIRECT_OPERATIONAL | 8/14 |
| allow_support_shape | SINGLE_SECTION | 1/14 |
| allow_support_shape | MULTI_SECTION | 0/6 |
| hard_negative | true | 16/16 |
| hard_negative | false | 5/24 |

Failure IDs (post-inference diagnostics only):

- false_abstentions: AQ001, AQ002, AQ004, AQ005, AQ006, AQ007, AQ008, AQ009, AQ010, AQ011, AQ012, AQ013, AQ014, AQ015, AQ016, AQ017, AQ018, AQ019, AQ020
- false_supports: none
- candidate_errors: none
- wrong_reason_only: AQ033, AQ034, AQ035, AQ036

### BASELINE_TOP3_UNION_LEXICAL_60

Control only: False. Eligible: False.

| Primary metric | Exact value and rate |
| --- | --- |
| allow_recall | 5/1 divided by 20 = 0.250000000000 |
| false_abstention_rate | 15/1 divided by 20 = 0.750000000000 |
| correct_abstention_rate | 20/1 divided by 20 = 1.000000000000 |
| false_support_rate | 0/1 divided by 20 = 0.000000000000 |

| Secondary metric | Exact value and rate |
| --- | --- |
| overall_accuracy | 25/1 divided by 40 = 0.625000000000 |
| balanced_accuracy | 5/4 divided by 2 = 0.625000000000 |
| macro_f1 | 62/55 divided by 2 = 0.563636363636 |
| reason_code_agreement | 21/1 divided by 40 = 0.525000000000 |
| candidate_error_count | 0 |

Gated retrieval: Gold ALLOW denominator remains 20, required sections 26, multi-required questions 6.
False ABSTAIN contributes zero; metrics are not conditional on predicted ALLOW.

| Gated retrieval metric | Exact value and rate |
| --- | --- |
| hit_at_1 | 5/1 divided by 20 = 0.250000000000 |
| hit_at_3 | 5/1 divided by 20 = 0.250000000000 |
| required_macro_coverage_at_3 | 5/1 divided by 20 = 0.250000000000 |
| required_micro_coverage_at_3 | 6/1 divided by 26 = 0.230769230769 |
| multi_required_full_at_3 | 1/1 divided by 6 = 0.166666666667 |
| required_macro_coverage_at_5 | 5/1 divided by 20 = 0.250000000000 |
| required_micro_coverage_at_5 | 6/1 divided by 26 = 0.230769230769 |
| multi_required_full_at_5 | 1/1 divided by 6 = 0.166666666667 |
| required_macro_coverage_at_10 | 5/1 divided by 20 = 0.250000000000 |
| required_micro_coverage_at_10 | 6/1 divided by 26 = 0.230769230769 |
| multi_required_full_at_10 | 1/1 divided by 6 = 0.166666666667 |

| Diagnostic group | Subgroup | Binary correct / total |
| --- | --- | --- |
| gold_class | ALLOW | 5/20 |
| gold_class | ABSTAIN | 20/20 |
| abstain_reason | INSUFFICIENT_POLICY_SUPPORT | 16/16 |
| abstain_reason | UNRESOLVED_POLICY_CONTEXT | 4/4 |
| difficulty | DIRECT | 7/10 |
| difficulty | PARAPHRASE | 9/16 |
| difficulty | INDIRECT_OPERATIONAL | 9/14 |
| allow_support_shape | SINGLE_SECTION | 4/14 |
| allow_support_shape | MULTI_SECTION | 1/6 |
| hard_negative | true | 16/16 |
| hard_negative | false | 9/24 |

Failure IDs (post-inference diagnostics only):

- false_abstentions: AQ004, AQ005, AQ006, AQ007, AQ008, AQ009, AQ010, AQ011, AQ012, AQ014, AQ015, AQ016, AQ017, AQ019, AQ020
- false_supports: none
- candidate_errors: none
- wrong_reason_only: AQ033, AQ034, AQ035, AQ036

Eligible baseline count: **0**.

No threshold sweep or candidate change occurred after registration/evaluation began. No retrieval, model initialization,
external/LLM calls, Phase 2H HELD_OUT or Phase 2G private HELDOUT access occurred. Historical B2 retrieval total remains 40.
Candidate source/configuration hashes were checked again after inference and output generation.
Per-question lexical counts, exact rational coverage, decisions and all scored rows are in BASELINE_RESULTS.json.
The journal preserves registration order and each candidate's actual outputs before scoring.

Procedural next step only: Seek separate owner authorization for Phase 2H-B3.2 - Semantic Gate Engineering on DEVELOPMENT.

No commit or tag created. Stop for owner review.
