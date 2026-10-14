"""Declaration inventory only. No decoder, validator, adapter or model execution."""
from copy import deepcopy
import hashlib
import json


SCHEMA_SHA256 = "6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e"
INSPECTED_KEYWORDS = frozenset("""
type properties required additionalProperties enum const items prefixItems
minItems maxItems uniqueItems contains minContains maxContains minimum maximum
exclusiveMinimum exclusiveMaximum minLength maxLength pattern oneOf anyOf allOf
if then else $ref
""".split())
ANNOTATIONS = frozenset({"$schema"})
DECODER_SPINE_KEYWORDS = frozenset({
    "type", "properties", "required", "additionalProperties", "enum", "items",
})
APPLICATORS = frozenset({"oneOf", "anyOf", "allOf", "if", "then", "else", "contains"})


def pointer_child(pointer, part):
    return pointer + "/" + str(part).replace("~", "~0").replace("/", "~1")


def inventory(raw):
    """Inventory each keyword occurrence at schema nodes, never validate an instance.

    Only the frozen schema is accepted. Unknown keywords fail the inventory rather
    than disappearing from ownership. Property names are not schema keywords.
    Each required/enum array is counted as one occurrence, with its complete value.
    """
    if hashlib.sha256(raw).hexdigest() != SCHEMA_SHA256:
        raise ValueError("Not the frozen V2 schema bytes")
    schema = json.loads(raw)
    records, nodes = [], []

    def visit(node, pointer="", branch=False):
        if type(node) is not dict:
            raise ValueError("Unexpected schema node shape")
        nodes.append({"pointer": pointer, "kind": "object", "conditional_scope": branch})
        for keyword in sorted(node):
            if keyword not in INSPECTED_KEYWORDS | ANNOTATIONS:
                raise ValueError("Uninventoried keyword: " + keyword)
            value = node[keyword]
            path = pointer_child(pointer, keyword)
            material = keyword not in ANNOTATIONS
            decoder = material and not branch and keyword in DECODER_SPINE_KEYWORDS
            owners = ["EXACT_VALIDATOR_ENFORCED"] if material else []
            if decoder:
                owners.insert(0, "DECODER_ENFORCED")
            records.append({
                "pointer": path, "schema_node_pointer": pointer, "keyword": keyword,
                "constraint_value": deepcopy(value), "materiality": "MATERIAL" if material else "ANNOTATION",
                "criticality": "CRITICAL" if material else "NONCRITICAL",
                "conditional_scope": branch, "enforcement_owners": owners,
                "decoder": "ENFORCED" if decoder else "NOT_ENFORCED",
                "exact_validator": "ENFORCED" if material else "DIALECT_METADATA",
                "justification": (
                    "Mandatory unconditional structural spine; also checked by the authoritative validator."
                    if decoder else
                    "Preserve branch-local meaning at the exact validator; never hoist branch constraints into the decoder."
                    if material and (branch or keyword in APPLICATORS) else
                    "Delegate this full constraint to the mandatory exact validator, without changing its criticality."
                    if material else "Frozen dialect declaration; not an instance constraint."
                ),
            })
            if keyword == "properties":
                for name in sorted(value):
                    visit(value[name], pointer_child(path, name), branch)
            elif keyword in {"items", "additionalProperties"} and isinstance(value, dict):
                visit(value, path, branch)
            elif keyword in {"oneOf", "anyOf", "allOf", "prefixItems"}:
                for index, child in enumerate(value):
                    visit(child, pointer_child(path, index), branch or keyword in APPLICATORS)
            elif keyword in {"if", "then", "else", "contains"}:
                visit(value, path, True)

    visit(schema)
    records.sort(key=lambda r: r["pointer"])
    nodes.sort(key=lambda n: n["pointer"])
    material = [r for r in records if r["materiality"] == "MATERIAL"]
    counts = {
        "schema_nodes": len(nodes), "keyword_occurrences": len(records),
        "material_schema_constraints": len(material),
        "decoder_owned_raw_constraints": sum("DECODER_ENFORCED" in r["enforcement_owners"] for r in material),
        "exact_validator_owned_raw_constraints": len(material),
        "adapter_owned_raw_constraints": 0,
        "multi_owned_raw_constraints": sum(len(r["enforcement_owners"]) > 1 for r in material),
        "unowned_material_constraints": sum(not r["enforcement_owners"] for r in material),
    }
    return {
        "schema_sha256": SCHEMA_SHA256,
        "counting_unit": "One material keyword occurrence at a schema node; list members retained in full value, not counted again. Container applicators/properties and their child constraints counted separately.",
        "schema_nodes": nodes, "constraints": records, "counts": counts,
        "absent_inspected_keywords": sorted(INSPECTED_KEYWORDS - {r["keyword"] for r in records}),
        "execution": "DECLARATION_INVENTORY_ONLY_NOT_INSTANCE_VALIDATION",
    }
