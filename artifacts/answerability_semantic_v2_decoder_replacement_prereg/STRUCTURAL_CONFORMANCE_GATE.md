# Mandatory future pure structural conformance gate

Status: PREREGISTERED_NOT_EXECUTED. This document authorizes no parser execution,
package installation, model inference, or semantic-suite authoring.

## Exact historical strings

Reuse byte-exact text fields from
`artifacts/answerability_semantic_v2_xgrammar_diagnostic/MATCHER_DIAGNOSTIC_FIXTURES.json`
(SHA-256 `3519ecfb0cd1e215af9d550ed219eff48d02a6fb2ebc3918c7f74425a6390e29`).
Verify both the container hash and every text_sha256 before future use. Do not
repair, regenerate, normalize, or reinterpret historical S1/S2/S3 strings.

| Fixture | Required future result |
| --- | --- |
| M1_VALID_COMPLETE | ACCEPT |
| M2_MISSING_DECISION | REJECT |
| M3_MISSING_POLICY_CONTEXT | REJECT |
| M4_MISSING_REASON | REJECT |
| M5_MISSING_ALL_THREE | REJECT |
| M6_ATTEMPT2_S1_RAW | REJECT |
| M7_ATTEMPT2_S2_RAW | REJECT |
| M8_ATTEMPT2_S3_RAW | REJECT |

ACCEPT requires acceptance of the entire exact string as a complete object and
permitted termination/EOS. Valid-prefix acceptance is insufficient. REJECT means
the full string cannot terminate as an accepted document: record the first rejected
character/token, or explicit end-of-input/EOS refusal. Do not count a schema
validator rejecting a string as proof the decoder itself prevented that string.

Exercise both native character-parser progression and token-enforcer/callback
paths, using a fresh state for each case. Future tokenizer-only work may use the
frozen local tokenizer without model initialization, after separate authorization.
Record tokenization, exact parser arguments, all parser configuration and environment
overrides, completion state, EOS allowance, errors, and case counts. No generation,
model forward, sampling or logits from a model is needed.

## Schema feature probes required before capability judgment

Run the untouched full schema, testing interactions as well as individual features.
For each row require valid controls and invalid counterparts. These are probe
specifications, not a newly authored semantic qualification suite.

| Feature | Future positive and negative boundary checks |
| --- | --- |
| required | Root four fields and nested ask/status/rank fields present versus each omitted; parent requirements survive every branch |
| enum / const | Every declared value accepted in a consistent branch; unknown and wrong-case values rejected; branch const mismatches rejected |
| type: object | Root/nested objects versus arrays, strings, numbers, null and booleans |
| additionalProperties | Known keys accepted; unknown root and nested keys rejected |
| type: array / items | material_asks and supporting_evidence_ranks arrays versus scalar/null; every item type checked |
| minItems / maxItems | asks 1 and 8 versus 0 and 9; rank-array 10 versus 11 where otherwise applicable; conditional empty/nonempty constraints |
| integer | Rank integers versus string, boolean, null and fractional values; characterize integral decimal/exponent spellings separately from adapter's strict JSON-integer rule |
| minimum / maximum | Ranks 1 and 10 versus 0, -1 and 11; record decoder enforcement even if numeric-domain support is not claimed |
| uniqueItems | Unique ranks versus duplicates; report gaps explicitly, even though adapter also rejects invalid references |
| string / minLength / pattern | Nonempty ask with a non-whitespace character versus empty or whitespace-only ask; test the frozen pattern without substituting a regex |
| oneOf | Exercise all three decision branches; zero-match or multiply-matching objects must not be accepted; preserve parent requirements in each branch |
| anyOf | Unresolved branch through each allowed context/ask route; reject when neither route holds |
| allOf / if / then / else | SUPPORTED requires references; other statuses require empty references; enforce intersection with parent object and item restrictions |
| contains | Insufficient branch requires an UNSUPPORTED ask; unresolved ask route requires CONTEXT_UNRESOLVED; reject absence of the required witness |
| completion / EOS | Complete valid objects terminate; missing fields, truncated values and invalid objects cannot terminate; alternate permitted whitespace/key ordering must not lose constraints |

Record ENFORCED / NOT_ENFORCED / UNSUPPORTED / ERROR / NOT_TESTED per feature,
with exact inputs, expected results, native observations and immutable receipts.
Do not assume draft 2020-12 completeness from package metadata. Unsupported or
unenforced generation rules must remain explicit unresolved qualification findings.
Any core M1-M8 failure blocks progression to model generation. Any additional feature
gap blocks a claim of full-schema qualification and requires owner review before
progression; do not simplify the schema, add decoder heuristics, or silently assign
a newly discovered gap to the adapter to declare a pass.

## Unchanged adapter responsibilities

The deterministic adapter continues to enforce actual evidence-count rank bounds,
strict integer/reference handling, exact rank-to-canonical-identity mapping,
cross-field status/reference consistency and final GateOutput consistency.
Existing overlap with schema constraints remains intentional. Decoder acceptance
is not semantic correctness; parser rejection is not a Gold-favorable ABSTAIN.
No scientific output repair or malformed-output retry is permitted.
