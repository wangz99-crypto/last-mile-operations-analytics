"""Frozen-contract direct-regex derivation and pure structural qualification helpers."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json

CONTRACT_SHA = "768b9147e77f1dcc9dfd13b9dc4a6f9a2dad0ea6ad498219341fee0c43166198"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def scope_key(scope):
    return tuple(step.get("field", "*") for step in scope)


def literal(text):
    special = set(r"\.^$|?*+()[]{}")
    return "".join("\\" + ch if ch in special else ch for ch in text)


def derive(contract_bytes, rules):
    if sha(contract_bytes) != CONTRACT_SHA:
        raise ValueError("Contract identity mismatch")
    contract = json.loads(contract_bytes)
    rows = contract["constraints"]
    if len(rows) != 18:
        raise ValueError("Expected 18 decoder constraints")
    nodes = {}
    for row in rows:
        node = nodes.setdefault(scope_key(row["scope"]), {})
        if row["predicate"] in node:
            raise ValueError("Duplicate scoped predicate")
        node[row["predicate"]] = row
    used, trace = set(), []
    ws = rules["whitespace_pattern"]

    def render(path):
        node = nodes[path]
        allowed = {"type", "properties", "additionalProperties", "required", "enum", "items"}
        if set(node) - allowed:
            raise ValueError("Unsupported predicate")
        for row in node.values():
            used.add(row["constraint_id"])
            trace.append({"constraint_id": row["constraint_id"], "scope": row["scope"],
                          "predicate": row["predicate"], "contract_value": row["value"],
                          "derivation": rules["mapping"].get("type_" + str(row["value"]) if row["predicate"] == "type" else row["predicate"], rules["mapping"].get("type_array_and_items"))})
        if "enum" in node:
            if set(node) != {"enum"}:
                raise ValueError("Unexpected enum conjunction")
            return "(?:" + "|".join(literal(json.dumps(x)) for x in node["enum"]["value"]) + ")"
        typ = node["type"]["value"]
        if typ == "object":
            if set(node) != {"type", "properties", "additionalProperties", "required"}:
                raise ValueError("Unexpected object predicates")
            names = node["properties"]["value"]["declared_property_names"]
            if set(names) != set(node["required"]["value"]):
                raise ValueError("Optional field structure not supported by these rules")
            extra = node["additionalProperties"]["value"]
            if extra["allowed"] or set(extra["declared_property_names"]) != set(names):
                raise ValueError("Unexpected property boundary")
            fields = [literal(json.dumps(name)) + ws + ":" + ws + render(path + (name,)) for name in sorted(names)]
            return r"\{" + ws + (ws + "," + ws).join(fields) + ws + r"\}"
        if typ == "array":
            if set(node) != {"type", "items"}:
                raise ValueError("Unexpected array predicates")
            item = render(path + ("*",))
            return r"\[" + ws + "(?:" + item + "(?:" + ws + "," + ws + item + ")*)?" + ws + r"\]"
        if set(node) != {"type"}:
            raise ValueError("Unexpected primitive predicates")
        if typ == "string":
            return rules["string_pattern"]
        if typ == "integer":
            return rules["integer_pattern"]
        raise ValueError("Unknown primitive type")

    regex = ws + render(()) + ws
    if used != {r["constraint_id"] for r in rows}:
        raise ValueError("Unrepresented contract predicate")
    return regex, sorted(trace, key=lambda r: r["constraint_id"])


def parse_json(text):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("Duplicate key")
            obj[key] = value
        return obj
    def invalid_constant(value):
        raise ValueError("Non-finite JSON constant: " + value)
    return json.loads(text, parse_float=Decimal, parse_constant=invalid_constant, object_pairs_hook=pairs)


def contract_violations(value, contract):
    """Independent interpreter of ONLY the 18 neutral contract predicates."""
    def values(scope):
        current = [value]
        for step in scope:
            following = []
            for obj in current:
                if "field" in step and isinstance(obj, dict) and step["field"] in obj:
                    following.append(obj[step["field"]])
                elif "each_array_element" in step and isinstance(obj, list):
                    following.extend(obj)
            current = following
        return current
    failures = []
    for row in contract["constraints"]:
        key, target = row["predicate"], row["value"]
        for obj in values(row["scope"]):
            ok = True
            if key == "type":
                if target == "integer":
                    ok = type(obj) is int or isinstance(obj, Decimal) and obj.is_finite() and obj == obj.to_integral_value()
                else:
                    ok = isinstance(obj, {"object": dict, "array": list, "string": str}[target])
            elif key == "enum":
                ok = obj in target
            elif key == "required" and isinstance(obj, dict):
                ok = set(target).issubset(obj)
            elif key == "additionalProperties" and isinstance(obj, dict):
                ok = set(obj).issubset(target["declared_property_names"])
            # properties/items are scope association operators; child rows enforce values.
            if not ok:
                failures.append(row["constraint_id"])
                break
    return failures


def build_fixtures(contract, historical):
    base = {"decision": "ALLOW", "material_asks": [{"ask": "Synthetic structural item", "support_status": "SUPPORTED", "supporting_evidence_ranks": [1]}], "policy_context_status": "RESOLVED", "reason_code": "SUPPORTED_BY_ACTIVE_POLICY"}
    fixtures, coverage = [], []
    def add(fid, obj=None, text=None, expected="ACCEPT", category="structural", targets=None):
        if text is None:
            text = json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        fixtures.append({"id": fid, "text": text, "input_sha256": sha(text.encode("utf-8")), "expected": expected, "category": category, "targets": targets or []})
    for old in historical["fixtures"]:
        if sha(old["text"].encode()) != old["input_sha256"]:
            raise ValueError("Historical raw bytes changed")
        add(old["fixture_id"], text=old["text"], expected=old["expected"], category="historical")
    for i, row in enumerate(contract["constraints"], 1):
        cid, pred = row["constraint_id"], row["predicate"]
        pos, neg = "R%02d_POS" % i, "R%02d_NEG" % i
        add(pos, base, targets=[cid])
        obj = deepcopy(base)
        path = scope_key(row["scope"])
        target = obj
        parent, last = None, None
        for part in path:
            parent, last = target, 0 if part == "*" else part
            target = target[last]
        if pred == "additionalProperties": target["unexpected_probe"] = True
        elif pred == "required": del target[row["value"][0]]
        elif pred == "enum": parent[last] = "NOT_A_DECLARED_ENUM"
        elif pred == "properties":
            child = "decision" if not path else "ask"
            target[child] = 7
        elif pred == "items": target.append("WRONG_ITEM_SHAPE")
        elif pred == "type":
            wrong = {"object": [], "array": {}, "string": 7, "integer": True}[row["value"]]
            if parent is None: obj = wrong
            else: parent[last] = wrong
        add(neg, obj, expected="REJECT", targets=[cid])
        coverage.append({"constraint_id": cid, "positive": pos, "violating": neg, "association_note": "properties/items have no independent exclusion predicate; a wrong child exercises the association jointly with its child type/domain rule" if pred in {"properties", "items"} else None})
    for name, value in [("NUL", chr(0)), ("UNIT_SEPARATOR", chr(31)), ("UNICODE", "\u4e2d\u6587\U0001f600"), ("QUOTE", '"'), ("BACKSLASH", chr(92)), ("NEWLINE", chr(10)), ("EMPTY", ""), ("LONE_SURROGATE", chr(0xD800))]:
        obj = deepcopy(base);obj["material_asks"][0]["ask"] = value
        add("STRING_" + name, obj, category="unicode")
    obj=deepcopy(base);obj["material_asks"][0]["ask"]="\u4e2d\u6587\U0001f600"
    add("STRING_RAW_UNICODE",text=json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",", ":")),category="unicode")
    obj=deepcopy(base);obj["material_asks"][0]["supporting_evidence_ranks"]=[1,1]
    add("DELEGATED_UNIQUE",obj,category="validator_only")
    obj=deepcopy(base);obj["material_asks"][0]["supporting_evidence_ranks"]=[]
    add("DELEGATED_CONTAINS",obj,category="validator_only")
    obj=deepcopy(base);obj["decision"]="ABSTAIN"
    add("DELEGATED_CONDITIONAL",obj,category="validator_only")
    obj=deepcopy(base);obj["material_asks"]=[]
    add("EMPTY_ASK_ARRAY",obj,category="contract_relaxation")
    obj=deepcopy(base);obj["material_asks"][0]["supporting_evidence_ranks"]=[-1,0,123456789012345678901234567890]
    add("UNBOUNDED_INTEGERS",obj,category="contract_relaxation")
    add("WHITESPACE",text=json.dumps(base,sort_keys=True,indent=2),category="serialization")
    canonical=json.dumps(base,sort_keys=True,separators=(",", ":"))
    for fid,text in [("PROSE","answer:"+canonical),("TRAILING_OBJECT",canonical+canonical),("DUPLICATE_KEY",canonical.replace('{"decision":"ALLOW",','{"decision":"ALLOW","decision":"ALLOW",',1)),("RAW_NUL",canonical.replace('Synthetic structural item',chr(0))),("INVALID_ESCAPE",canonical.replace('Synthetic structural item',chr(92)+'q'))]:
        add(fid,text=text,expected="REJECT",category="parse_boundary")
    return {"fixtures":fixtures,"coverage":coverage,"fixture_policy":"Frozen before outcomes; exact historical bytes; no benchmark questions; every fixture executes once per language layer; errors distinct from rejection."}


def textual_results(regex, contract, fixtures):
    import re
    engine = re.compile(regex)
    rows=[]
    for f in fixtures["fixtures"]:
        row={"id":f["id"],"expected":f["expected"],"input_sha256":f["input_sha256"]}
        try:
            value=parse_json(f["text"]);row["json_parse"]="PASS"
            violations=contract_violations(value,contract)
            row["contract"]="PASS" if not violations else "FAIL"
            row["contract_violations"]=violations
        except (ValueError,TypeError) as exc:
            row.update(json_parse="FAIL",contract="NOT_APPLICABLE",parse_error=str(exc))
        try: row["regex"]="ACCEPT" if engine.fullmatch(f["text"]) else "REJECT"
        except Exception as exc: row.update(regex="ERROR",regex_error=type(exc).__name__+": "+str(exc))
        row["matches_expectation"]=row["regex"]==f["expected"]
        rows.append(row)
    return rows
