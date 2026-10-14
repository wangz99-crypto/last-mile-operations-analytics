# Authoritative exact-validator contract

The immutable schema, SHA-256 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e, remains the sole raw structural acceptance contract. All 64 material keyword occurrences are mandatory, including the 18 preventive decoder-owned occurrences and 46 validator-only occurrences. Full pointers, values and criticality are in STRUCTURAL_ENFORCEMENT_MATRIX.json. No constraint is downgraded because grammar enforcement is difficult.

Standard strict JSON parsing must succeed on preserved raw UTF-8 bytes, consuming one complete object with no commentary/fences. Reject duplicate keys/nonfinite values according to the existing interface; no coercion, key dropping, defaults, repair or data reserialization may replace the raw evidence. Full exact-schema validation then runs on that unmodified parsed object using the original branch/conditional semantics and declared dialect. Remote schema/reference access is forbidden.

The decoder grammar cannot substitute for this validator. oneOf/anyOf/allOf, if/then/else, contains, uniqueItems and every other delegated constraint stay mandatory before the adapter. JSON parse failure or exact-schema rejection produces STRUCTURAL_INVALID, no retries, no adapter and no semantic evaluation. Unexpected exceptions remain candidate errors, not valid rejection evidence.

Validator implementation/version/provenance is NOT_SELECTED_NOT_QUALIFIED. The previous triangulation oracle is not automatically selected or qualified. Before future P6 execution, separately freeze exact implementation, dependencies, dialect configuration, strict parse configuration, immutable fixtures and source hashes. P6 must independently demonstrate every assigned constraint with positives and negatives; production use requires P7 integration qualification as well.

The count unit is one keyword occurrence, retaining complete list/object values; nested branch members are counted as distinct occurrences only at their schema nodes. The $schema declaration is inventoried as non-material dialect metadata. This prevents false coverage from counting a keyword name only once while missing its branch-local uses.
