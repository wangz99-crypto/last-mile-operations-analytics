# Conditional future structural gates — not authorized to execute

Current outcome LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED prevents entry to this ladder. The definitions preserve the owner's intended controls; they do not override the blocker.

| Step | Mandatory condition |
| --- | --- |
| K0 | Separately authorize exact packages/dependency versions and enable runtime; preserve inventories and existing packages. |
| K1 | LLMatcher.grammar_from_json_schema with the exact frozen schema and no project preprocessing must construct grammar. This API may wrap a schema without fully compiling it, so its return alone is insufficient. |
| K2 | LLMatcher.validate_grammar_with_warnings (or release-equivalent API) must report no error. Record every warning. Its is_error boolean must not be interpreted backwards. No tokenizer needed for this API's optional-tokenizer form; runtime must confirm signature. |
| K3 | Compile/validate both exact oneOf/material_asks shapes and the item/allOf conditional shapes without semantic weakening. |
| K4 | After K1-K3 pass, use frozen local tokenizer only if required; triangulate unchanged M1-M8 through standard JSON, frozen authoritative schema validator and llguidance matcher. |
| K5 | Qualify all present material constraints in JSON_SCHEMA_CAPABILITY_MATRIX.json; all critical constraints must pass. |
| L | Only after K1-K5 pass, separately freeze dependency closure and exact release-specific Outlines/llguidance/HF API paths, then qualify integration. |
| M | Only after K1-K5 and L pass, frozen Qwen CPU FP32 structural smoke: exactly 3 generate calls; 0 quality retries; 0 schema-repair retries; repetition_penalty=1.0. |

A compilation/validation or exact-semantics failure in a future authorized qualification yields LLGUIDANCE_STRUCTURAL_CONFORMANCE_FAILED and stops before model use. That outcome has NOT occurred in this phase. Warnings affecting required, oneOf, allOf, properties, additionalProperties, enums, array cardinality, uniqueness, primitive types, conditionals or contains prevent automatic progression pending owner review. No lenient/coercion fallback.

Core expectations: M1 complete valid object ACCEPT; M2 missing decision REJECT; M3 missing policy_context_status REJECT; M4 missing reason_code REJECT; M5 missing all three REJECT; M6/M7/M8 historical XGrammar S1/S2/S3 raw objects REJECT. Original fixture bytes/hashes are referenced in PREREGISTERED_STACK.json. Do not repair, replace or regenerate them.

LLMatcher is token-oriented and its 1.9.1 constructor requires LLTokenizer. Compilation/validation differs from token/string acceptance. After K1-K3 only, tokenizer may come from the immutable local Qwen snapshot, offline. No model initialization, forward or generate during K stages. Before running M1-M8, freeze exact installed API acceptance semantics: error state, accepting, stopped, EOS validity, rejection before EOS and complete input consumption must remain separate observations. Exceptions/internal error states are ERROR, never evidence of REJECT. A partial prefix or stopped state alone is not acceptance. Runtime API details must be verified and recorded before execution, not guessed here.

For each fixture report JSON validity, authoritative raw-schema validity, matcher acceptance/error, and expected result. K5 covers type, properties, required, additionalProperties, enum, const, items, minItems, maxItems, uniqueItems, minimum, maximum, minLength, pattern, oneOf, anyOf, allOf, if/then/else, contains wherever present. exclusiveMinimum/exclusiveMaximum/maxLength/$ref are inventoried as absent in this exact schema. All present material constraints are CRITICAL; failure before deterministic adapter processing rejects the stack. No remote/external reference fetching is allowed if future reference qualification becomes relevant.
