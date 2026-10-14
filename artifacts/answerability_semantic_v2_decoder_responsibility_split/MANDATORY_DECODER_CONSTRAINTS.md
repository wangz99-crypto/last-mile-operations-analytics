# Mandatory decoder subset and future contract derivation

The future DECODER_ENFORCEMENT_CONTRACT is a separate structural-generation artifact, NOT the authoritative schema. It is not produced or qualified in P. P2 must derive it deterministically, hash its bytes, freeze derivation code/version, and bind its complete ownership matrix before any new decoder result.

Both layers must enforce: one top-level JSON object; standard nested JSON syntax; no fences or prose prefix/suffix; known property names/object shape; required top-level fields; primitive field types; enum domains; material_asks array and item-object shape; required ask fields; supporting_evidence_ranks arrays and integer elements. Exact validation includes strict parsing, not just a schema library call. Reject duplicate keys and nonfinite constants; retain original bytes. These parser rules preserve the existing V2 interface.

Mandatory top-level keys: material_asks, policy_context_status, decision, reason_code. Required item keys: ask, support_status, supporting_evidence_ranks. decision/context/reason/status enum domains and all unconditional primitive/container types remain decoder-enforced. Finite enums already imply string types for fields without an explicit type keyword; do not widen them.

Frozen P2 derivation recipe:

1. Start from the exact immutable V2 schema and its raw SHA, never from decoder feedback.
2. Retain the unconditional structural spine: type, properties, required, additionalProperties, enum, items. Recursively project only schema-valued properties/items; preserve literal assertion values exactly. The original authoritative file is never changed.
3. Omit branch applicators oneOf/anyOf/allOf/if/then/else/contains and their complete scopes from the decoder contract. Never hoist branch-local const, enum, properties or required into unconditional conditions.
4. Other constraints (cardinalities, numeric bounds, uniqueness, text length/pattern and all branch logic) remain unchanged and mandatory at the exact validator; matrix rows identify each omission and justification.
5. No extra property-order, canonical whitespace, rank order, array cardinality or numeric lexical restriction is authorized in the decoder layer. P2 must prove the language relationship and preserve every mandatory subset constraint before freezing. If a future implementation needs a neutral serialization restriction, it requires explicit preregistration and justification before execution, not adaptive editing.

L_exact is the authoritative-schema language; L_decoder is the preventive-generation language. Require L_exact subseteq L_decoder for delegation, including permitted object key orders and numeric serializations. Dropping entire conjunctions relaxes generation, but flattening conditional branches could narrow it and is forbidden. No claim of an executed equivalence proof is made here.

JSON Schema integer semantics include numerically integral values such as 1.0; the unchanged V2 adapter rejects float/exponent tokens. Preserve that distinction: do not silently tighten the decoder contract and claim the full L_exact inclusion. Adapter token restrictions continue at the adapter. The finally accepted language also requires adapter success. This is existing adapter behavior, not semantic weakening or a new decoder rule.

A decoder that cannot enforce required fields, primitive types, enum domains or structure is unacceptable. There is no silent subset reduction after results. Every raw-schema constraint remains checked by the independent exact validator even when decoder-enforced.
