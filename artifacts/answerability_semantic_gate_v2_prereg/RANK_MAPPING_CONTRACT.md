# V2 rank mapping contract

Input: exact frozen GateInput plus strict raw JSON text/UTF-8 bytes.
Output: immutable canonical assessment and ordered RankBinding audit records;
only its frozen GateOutput is externally scored.

Reject duplicate JSON keys, nonfinite values, malformed UTF-8/JSON, prose/fences,
unknown or missing keys, bad enums, empty/blank asks and ask counts outside 1-8.
Each supporting_evidence_ranks value must be a list of exact integer tokens:
Python type(rank) is int, excluding booleans, floats, exponent notation, strings
and canonical identity strings. Each rank must be 1-10 and present in the actual
input's contiguous frozen rank list. Ranks must be strictly ascending; duplicates
or unsorted arrays are rejected, never deduplicated or sorted.
SUPPORTED requires at least one rank. Both other statuses require no ranks.
All ranks are validated before any accepted canonical assessment is returned.

For each material ask in model order and each rank in that ask's validated order:
look up GateInput.evidence at that exact rank; preserve its policy_id, version and
section_id tuple and serialize policy_id@version#section_id using the frozen V1
section_reference function. Record zero-based material_ask_index, evidence_rank,
canonical_identity tuple and canonical_reference string. Do not consult files,
indexes, corpus, retrievers, titles, string similarity or hidden sections.
Ask text, support status, decision, reason and context are copied unchanged.
The mapped object must pass frozen V1 parse_assessment; it is not semantically repaired.

Canonical JSON: UTF-8, ensure_ascii=false, sort_keys=true, indent=2,
allow_nan=false, final LF. Identical input and raw object give identical mapping,
canonical assessment bytes and audit bytes. The frozen two-field GateOutput is
returned by adapt_response; audit metadata never changes the scorer contract.

## Schema versus adapter guarantees
Static JSON Schema declares ranks integer 1-10, uniqueItems, status-dependent empty
or nonempty arrays, exact keys/enums and 1-8 asks. Per-input schema narrows the
maximum rank to actual evidence count; with zero evidence maxItems=0 forbids all
rank references. A future decoder may use the static 1-10 fallback only if the
adapter always enforces actual membership. Standard schema does not enforce
strictly ascending order here; the parser does. JSON Schema regards 1.0 as an
integer value, whereas the parser requires a lexical integer token and rejects
1.0 and 1e0. No claim is made that an unselected decoder implements every keyword.
Both the V2 parser and final frozen V1 semantic consistency check are mandatory.

## Adapter/parser receipt
UTF-8 concatenate in exactly this order, with a final LF:
candidate_source_sha256 + TAB + value + LF
v1_parser_source_sha256 + TAB + value + LF
raw_schema_sha256 + TAB + value + LF
rank_mapping_contract_sha256 + TAB + value + LF
SHA-256 of those bytes is parser_adapter_receipt_sha256. The source hashes cover
whole modules, conservatively binding prompt composition, input validation,
dynamic schema construction, strict parsing, mapping and semantic consistency.
No registry or record self-hash is included.
