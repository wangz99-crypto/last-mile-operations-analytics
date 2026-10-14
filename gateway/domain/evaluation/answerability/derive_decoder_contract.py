"""P2P3 offline declaration derivation and freeze guards; no decoder execution."""
from copy import deepcopy
import hashlib
import json


SCHEMA_SHA = "6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def scope(pointer):
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.split("/")[1:]]
    result, index = [], 0
    while index < len(parts):
        part = parts[index]
        if part == "properties" and index + 1 < len(parts):
            result.append({"field": parts[index + 1]})
            index += 2
        elif part == "items":
            result.append({"each_array_element": True})
            index += 1
        else:
            raise ValueError("Cannot hoist a branch into the decoder contract")
    return result


def derive(raw_schema, matrix, rules):
    if digest(raw_schema) != SCHEMA_SHA:
        raise ValueError("Frozen schema mismatch")
    rows = sorted(matrix["raw_schema_constraints"], key=lambda row: row["pointer"])
    if len(rows) != 64 or len({r["pointer"] for r in rows}) != 64:
        raise ValueError("Incomplete or duplicate source constraints")
    if len(matrix["adapter_obligations"]) != 6:
        raise ValueError("Adapter separation mismatch")
    contracts, trace, delegated = [], [], []
    schema = json.loads(raw_schema)
    for row in rows:
        if "EXACT_VALIDATOR_ENFORCED" not in row["enforcement_owners"]:
            raise ValueError("Lost authoritative ownership")
        reference = None
        if "DECODER_ENFORCED" in row["enforcement_owners"]:
            keyword = row["keyword"]
            if keyword not in {"type", "properties", "items", "enum", "required", "additionalProperties"}:
                raise ValueError("Unrecognized decoder-owned predicate")
            node = schema
            for part in row["schema_node_pointer"].split("/")[1:]:
                part = part.replace("~1", "/").replace("~0", "~")
                node = node[int(part)] if isinstance(node, list) else node[part]
            value = deepcopy(row["constraint_value"])
            if keyword == "properties":
                value = {"declared_property_names": sorted(value), "child_predicates": "Separate owned rows at their field scopes; omitted children remain validator-only."}
            elif keyword == "items":
                value = {"quantifier": "every array element", "child_predicates": "Separate owned rows at the element scope; no copied delegated assertions."}
            elif keyword == "additionalProperties":
                if value is not False:
                    raise ValueError("Unexpected additionalProperties declaration")
                value = {"allowed": False, "declared_property_names": sorted(node["properties"])}
            reference = "/constraints/" + str(len(contracts))
            contracts.append({"constraint_id": row["pointer"], "scope": scope(row["schema_node_pointer"]), "predicate": keyword, "value": value})
        elif row["enforcement_owners"] == ["EXACT_VALIDATOR_ENFORCED"]:
            delegated.append(deepcopy(row))
        else:
            raise ValueError("Unexpected ownership")
        trace.append({
            "constraint_id": row["pointer"], "json_pointer": row["pointer"],
            "keyword": row["keyword"], "raw_constraint": deepcopy(row["constraint_value"]),
            "p1_ownership": row["enforcement_owners"], "decoder_contract_representation": reference,
            "validator_delegation": "MANDATORY_EXACT_VALIDATOR_ENFORCED",
            "adapter_relation": "No raw-schema ownership transfer; six adapter obligations remain separate.",
        })
    if (len(contracts), len(delegated)) != (18, 46):
        raise ValueError("Frozen P1 ownership accounting mismatch")
    contract = {
        "contract_id": "DECODER_ENFORCEMENT_CONTRACT_V2_1_V0_1",
        "authority": "NON_AUTHORITATIVE_DECODER_CONTRACT",
        "authoritative_schema_sha256": SCHEMA_SHA,
        "candidate_id": "SEMANTIC_MATERIAL_SUPPORT_V2_1",
        "semantic_domain": rules["semantic_domain"],
        "predicate_semantics": {
            "scope": "Apply to present values at each field/array-element path. Required predicates separately enforce presence. No implicit defaults.",
            "type": "JSON value type; integer means mathematical integral number, never boolean.",
            "properties": "Declare field scopes; their predicates are separate conjunctions. Unknown properties are governed by additionalProperties.",
            "items": "Apply owned element predicates to every member, including vacuous satisfaction on empty arrays; no cardinality restriction.",
            "enum": "Value membership in the exact frozen finite domain.",
            "required": "All listed property names must be present in the object at scope.",
            "additionalProperties": "No key outside the declared property names at the scope.",
        },
        "constraints": contracts,
        "serialization": deepcopy(rules["serialization_policy"]),
        "parse_boundary": deepcopy(matrix["parse_boundary_obligations"]),
        "adapter_obligations": "Not part of this contract; all six remain exclusively at the unchanged adapter.",
        "prohibited": ["semantic strengthening", "delegated constraint approximation", "post-generation repair", "structural retry"],
        "inclusion_argument": rules["inclusion_argument"],
    }
    return contract, trace, delegated


def verify_frozen(current_bytes, expected_hashes):
    if set(current_bytes) != set(expected_hashes):
        raise ValueError("Freeze file-set mismatch")
    for name, expected in expected_hashes.items():
        if digest(current_bytes[name]) != expected:
            raise ValueError("Frozen contract changed: " + name)


def selection_outcome(capability_rows):
    if len(capability_rows) != 18 or len({r["constraint_id"] for r in capability_rows}) != 18:
        raise ValueError("Candidate matrix must cover all 18 constraints")
    allowed = {"STATICALLY_SUPPORTED", "STATICALLY_UNSUPPORTED", "REQUIRES_RUNTIME_QUALIFICATION", "AMBIGUOUS"}
    for row in capability_rows:
        if row["support_classification"] not in allowed:
            raise ValueError("Unknown candidate classification")
        if row["support_classification"] == "AMBIGUOUS" and not row.get("direct_p4_probe"):
            raise ValueError("Ambiguity requires a frozen direct probe")
    if any(row["support_classification"] == "STATICALLY_UNSUPPORTED" for row in capability_rows):
        return "DECODER_CANDIDATE_SELECTION_BLOCKED"
    return "P2P3_CONTRACT_FROZEN_CANDIDATE_SELECTED"
