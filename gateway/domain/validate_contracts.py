"""Offline artifact/shape validation only. No operational calculations or scoring."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def schema_document(root=ROOT):
    return read_json(root / "schemas/contracts.schema.json")


def validate_shape(value, name, document=None):
    """Validate the documented local JSON Schema subset, never resolve network refs.

    Not a general JSON Schema implementation. Unsupported keywords fail closed.
    Relational keys and conditional constraints are checked separately below.
    """
    doc = schema_document() if document is None else document
    supported = {"$ref", "type", "properties", "required", "additionalProperties", "items",
                 "minItems", "maxItems", "enum", "const", "minLength", "pattern", "minimum",
                 "format", "anyOf", "description", "x-primary-key", "x-foreign-key"}

    def visit(item, spec, path):
        require(not set(spec) - supported, f"Unsupported schema keywords at {path}: {set(spec)-supported}")
        if "$ref" in spec:
            target = spec["$ref"]
            require(target.startswith("#/$defs/") and target[8:] in doc["$defs"], f"Nonlocal/unknown ref: {target}")
            visit(item, doc["$defs"][target[8:]], path)
            return
        if "anyOf" in spec:
            for branch in spec["anyOf"]:
                try:
                    visit(item, branch, path)
                    break
                except ValueError:
                    pass
            else:
                raise ValueError(f"{path}: no anyOf branch matches")
        typ = spec.get("type")
        checks = {"object": lambda: isinstance(item, dict), "array": lambda: isinstance(item, list),
                  "string": lambda: isinstance(item, str), "boolean": lambda: type(item) is bool,
                  "integer": lambda: type(item) is int, "number": lambda: type(item) in (int, float),
                  "null": lambda: item is None}
        if typ is not None:
            require(typ in checks and checks[typ](), f"{path}: expected {typ}")
        if "const" in spec:
            require(type(item) is type(spec["const"]) and item == spec["const"], f"{path}: wrong constant")
        if "enum" in spec:
            require(item in spec["enum"], f"{path}: unknown enum {item!r}")
        if isinstance(item, dict):
            require(set(spec.get("required", [])) <= item.keys(), f"{path}: missing required fields")
            props = spec.get("properties", {})
            if spec.get("additionalProperties") is False:
                require(not item.keys() - props.keys(), f"{path}: unknown fields {item.keys()-props.keys()}")
            for key, val in item.items():
                if key in props:
                    visit(val, props[key], f"{path}.{key}")
        if isinstance(item, list):
            require(len(item) >= spec.get("minItems", 0), f"{path}: too few items")
            require(len(item) <= spec.get("maxItems", len(item)), f"{path}: too many items")
            for i, val in enumerate(item):
                if "items" in spec:
                    visit(val, spec["items"], f"{path}[{i}]")
        if isinstance(item, str):
            require(len(item) >= spec.get("minLength", 0), f"{path}: too short")
            if "pattern" in spec:
                require(re.search(spec["pattern"], item) is not None, f"{path}: pattern mismatch")
            if "format" in spec:
                require(spec["format"] == "date-time", "Unsupported format")
                try:
                    dt = datetime.fromisoformat(item.replace("Z", "+00:00"))
                except ValueError as exc:
                    raise ValueError(f"{path}: invalid timestamp") from exc
                require("T" in item and dt.tzinfo is not None, f"{path}: timezone required")
        if "minimum" in spec:
            require(item >= spec["minimum"], f"{path}: below minimum")
    require(name in doc["$defs"], f"Unknown contract: {name}")
    visit(value, doc["$defs"][name], name)
    if name == "tracking_event" and value["event_code"] == "ATTEMPT_FAILED":
        require(value["attempt_id"] is not None, "ATTEMPT_FAILED requires attempt_id in canonical input")


def unique(values, label):
    require(len(values) == len(set(values)), f"Duplicate {label}")


def section_key(value):
    return (value["policy_id"], value["version"], value["section_id"])


def read_sop(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", text, re.S)
    require(len(blocks) == 1, f"{path}: exactly one metadata block required")
    metadata = json.loads(blocks[0])
    headings = re.findall(r"^## ([a-z][a-z0-9-]*)$", text, re.M)
    require(headings == [s["section_id"] for s in metadata["sections"]], f"{path}: section headings/metadata differ")
    require("Fictional demo operating policy. Not real carrier or industry standards." in text,
            f"{path}: fictional policy disclaimer missing")
    return metadata, text


def validate_bundle(root=ROOT, check_hashes=True):
    registry = read_json(root / "policy/policy_registry.json")
    doc = schema_document(root)
    require(registry["demo_policy"] is True, "Registry must be demo_policy")
    require(registry["effective_to"] is None or registry["effective_to"] > registry["effective_from"], "Invalid bundle interval")
    rules = {r["rule_id"]: r for r in registry["rules"]}
    requirements = {e["requirement_id"]: e for e in registry["evidence_requirements"]}
    require(len(rules) == len(registry["rules"]), "Duplicate rule IDs")
    require(len(requirements) == len(registry["evidence_requirements"]), "Duplicate evidence IDs")
    require(set(rules) == set(doc["$defs"]["rule_id"]["enum"]), "Rule inventory mismatch")
    require(set(requirements) == set(doc["$defs"]["requirement_id"]["enum"]), "Evidence inventory mismatch")
    require(set(registry["open_statuses"] + registry["closed_statuses"]) == set(doc["$defs"]["shipment_status"]["enum"]), "Status inventory mismatch")
    require(set(registry["qualifying_physical_scans"]) <= set(doc["$defs"]["event_code"]["enum"]), "Unknown scan code")
    sections = {}
    policy_ids = []
    for sop in registry["sops"]:
        path = root / sop["path"]
        require(path.resolve().is_relative_to(root.resolve()), "SOP path escapes artifact root")
        meta, _ = read_sop(path)
        require(meta["policy_id"] == sop["policy_id"], "Policy ID mismatch")
        require(meta["version"] == registry["bundle_version"], "SOP version mismatch")
        require(meta["effective_from"] == registry["effective_from"] and meta["effective_to"] == registry["effective_to"], "SOP interval mismatch")
        require(meta["demo_policy"] is True, "SOP demo label missing")
        require(bool(meta["title"]), "SOP title missing")
        require(set(meta["exception_types"]) <= set(doc["$defs"]["exception_type"]["enum"]), "Unknown SOP coverage")
        require([s["section_id"] for s in meta["sections"]] == sop["section_ids"], "SOP section inventory mismatch")
        policy_ids.append(meta["policy_id"])
        for sec in meta["sections"]:
            key = (meta["policy_id"], meta["version"], sec["section_id"])
            require(key not in sections, f"Duplicate section identity {key}")
            require(set(sec["rule_ids"]) <= rules.keys(), "Unknown rule in SOP metadata")
            require(set(sec["requirement_ids"]) <= requirements.keys(), "Unknown evidence ID in SOP metadata")
            require(bool(sec["section"]), "Section title missing")
            sections[key] = sec
    unique(policy_ids, "SOP policy IDs")
    for kind, entries, id_field, backlink in [("rule",rules.values(),"rule_id","rule_ids"),
                                             ("evidence",requirements.values(),"requirement_id","requirement_ids")]:
        for entry in entries:
            require("required_sop_sections" not in entry, "Ambiguous legacy section mapping")
            support = entry["support_sections"]
            guidance = entry["failure_guidance_sections"]
            require(bool(support or guidance), f"Unmapped {kind}")
            support_keys = [section_key(x) for x in support]
            guidance_keys = [section_key(x) for x in guidance]
            unique(support_keys + guidance_keys, "section mapping roles")
            require(all(x[0] != "SOP-07" for x in support_keys), "Insufficient-evidence guidance cannot be normal support")
            for target in support + guidance:
                key = section_key(target)
                require(key in sections, f"Missing SOP section: {key}")
                require(entry[id_field] in sections[key][backlink], f"Missing reciprocal {kind} metadata")
            if kind == "rule":
                require("evidence_requirement_ids" not in entry, "Ambiguous legacy dependency field")
                require(set(entry["decision_dependency_ids"]) <= requirements.keys(), "Unknown rule decision dependency")
                if entry["rule_id"] == "F-UNKNOWN":
                    require(set(entry["decision_dependency_ids"]) == {"E-IDENTITY", "E-STATUS", "E-POLICY-CONTEXT", "E-POLICY-SECTIONS"}, "F-UNKNOWN common dependencies must not union subtype requirements")
                    require(entry.get("subtype_dependency_ids") == {"FAILED_ATTEMPT": ["E-FAILED"], "ADDRESS_EXCEPTION": ["E-ADDRESS"]}, "F-UNKNOWN subtype dependency mapping invalid")
                    require(entry.get("subtype_readiness_contract") == {
                        "combination": "ANY_FULLY_SUPPORTED_ELIGIBLE_SUBTYPE",
                        "common_dependency_ids_field": "decision_dependency_ids",
                        "eligible_trigger_rule_ids": {"FAILED_ATTEMPT": "F-2", "ADDRESS_EXCEPTION": "F-3"},
                        "unresolved_other_subtype_blocks_readiness": False}, "F-UNKNOWN subtype readiness contract invalid")
                    for subtype, trigger in entry["subtype_readiness_contract"]["eligible_trigger_rule_ids"].items():
                        require(set(rules[trigger]["decision_dependency_ids"]) == set(entry["decision_dependency_ids"] + entry["subtype_dependency_ids"][subtype]), "Eligible subtype trigger dependency mismatch")
                require(set(entry["constant_refs"]) <= registry["thresholds"].keys(), "Unknown constant reference")
                require(entry["scope"] in ("SHIPMENT", "CATEGORY"), "Invalid rule scope")
                if entry["scope"] == "CATEGORY":
                    validate_shape(entry["exception_type"], "exception_type", doc)
    # Check backlinks in both directions; a failure mapping remains a backlink,
    # not an unconditional successful-output citation requirement.
    for key, sec in sections.items():
        for ids, entries in [(sec["rule_ids"], rules), (sec["requirement_ids"], requirements)]:
            for identity in ids:
                mapped = entries[identity]["support_sections"] + entries[identity]["failure_guidance_sections"]
                require(key in {section_key(x) for x in mapped}, "Orphan SOP backlink")
    if check_hashes:
        manifest = read_json(root / "policy/artifact_manifest.json")
        for name, digest in manifest["sha256"].items():
            path = root / name
            require(path.resolve().is_relative_to(root.resolve()), "Manifest path escapes root")
            require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"Artifact checksum mismatch: {name}")
    return registry, sections


def validate_assessment_semantics(assessment, registry):
    """Check declared Gold contract semantics only; do not compute any decision."""
    evidence = assessment["evidence"]
    inactive = assessment["result"] in ("FALSE", "NOT_APPLICABLE") and assessment["action_state"] == "NORMAL"
    if evidence["completeness"] == "NOT_APPLICABLE":
        require(inactive, "NOT_APPLICABLE evidence is only valid for inactive NORMAL assessments")
        require(not any(evidence[k] for k in ("required_ids", "missing_ids", "conflicting_ids")), "NOT_APPLICABLE evidence must have empty IDs")
    if assessment["action_state"] in ("MONITOR", "READY_TO_ESCALATE", "NEEDS_REVIEW"):
        require(evidence["completeness"] != "NOT_APPLICABLE" and bool(evidence["required_ids"]), "Active decision/review requires relevant evidence")
    rules = {r["rule_id"]: r for r in registry["rules"]}
    requirements = {e["requirement_id"]: e for e in registry["evidence_requirements"]}
    declared_rules = [rules[x] for x in assessment["rule_ids"]]
    declared_evidence = [requirements[x] for x in evidence["required_ids"]]
    support = {section_key(x) for e in declared_rules + declared_evidence for x in e["support_sections"]}
    if assessment["action_state"] in ("MONITOR", "READY_TO_ESCALATE"):
        dependencies = {x for rule in declared_rules for x in rule["decision_dependency_ids"]}
        for rule in declared_rules:
            if "subtype_dependency_ids" in rule:
                # Use the author's declared supported trigger, never infer a
                # subtype from raw facts or union the unresolved other branch.
                triggers = rule["subtype_readiness_contract"]["eligible_trigger_rule_ids"]
                selected = [subtype for subtype, trigger in triggers.items()
                            if trigger in assessment["supported_triggers"]
                            and trigger in assessment["rule_ids"]]
                require(bool(selected), "Active subtype uncertainty requires a declared supported trigger rule")
                for subtype in selected:
                    dependencies.update(rule["subtype_dependency_ids"][subtype])
        require(dependencies <= set(evidence["required_ids"]), "Active Gold omits declared decision dependencies")
        require(support <= {section_key(x) for x in assessment["expected_sections"]},
                "Active Gold omits normal support sections")
    # A declared unresolved rule or gap can explain failure guidance. Do not
    # infer failure conditions from shipment data or require citation unions.
    guidance = {section_key(x) for e in declared_rules for x in e["failure_guidance_sections"]}
    gaps = set(evidence["missing_ids"] + evidence["conflicting_ids"])
    guidance.update(section_key(x) for identity in gaps for x in requirements[identity]["failure_guidance_sections"])
    if inactive or not (assessment["action_state"] == "NEEDS_REVIEW" or assessment["blockers"] or gaps):
        guidance = set()
    require(all(section_key(x) in support | guidance for x in assessment["expected_sections"]), "Unsupported or unconditional failure-guidance citation in Gold")


def validate_fixture(value, root=ROOT):
    doc = schema_document(root)
    validate_shape(value, "fixture", doc)
    require(value["example_only"] == (value["split"] == "EXAMPLE"), "Example/split mismatch")
    inp = value["input"]
    require(hashlib.sha256(canonical_bytes(inp)).hexdigest() == value["manifest"]["checksum"], "Snapshot input checksum mismatch")
    registry, sections = validate_bundle(root, check_hashes=False)
    require(value["policy"] == {"bundle_id":registry["bundle_id"],"bundle_version":registry["bundle_version"]}, "Unknown fixture policy version")
    if value["input_profile"] == "CANONICAL":
        require(not value["expected_input_findings"], "Canonical input cannot declare invalid-input findings")
        snapshot = value["manifest"]["snapshot_id"]
        keys = []
        for row in inp["shipments"]:
            validate_shape(row, "shipment", doc)
            require(row["snapshot_id"] == snapshot, "Shipment/manifest snapshot mismatch")
            keys.append((row["snapshot_id"],row["shipment_id"]))
        unique(keys, "composite shipment keys")
        event_keys, history_keys = [], []
        for table, contract in [("tracking_events","tracking_event"),("history_declarations","history_declaration")]:
            for row in inp[table]:
                validate_shape(row, contract, doc)
                key = (row["snapshot_id"],row["shipment_id"])
                require(key in keys, f"Broken composite foreign key in {table}")
                if table == "tracking_events":
                    event_keys.append((row["snapshot_id"],row["source_system"],row["event_id"]))
                else:
                    history_keys.append(key)
        unique(event_keys,"event identities")
        unique(history_keys,"history identities")
        require(set(keys) == set(history_keys), "Canonical shipments require explicit history declaration")
    else:
        require(bool(value["expected_input_findings"]), "Raw validation case must declare expected invalid input")
    targets = []
    for expected in value["expected_results"]:
        index = expected["input_shipment_index"]
        require(index < len(inp["shipments"]), "Gold target row index out of bounds")
        targets.append(index)
        if value["input_profile"] == "CANONICAL":
            row = inp["shipments"][index]
            require((expected["snapshot_id"],expected["shipment_id"]) == (row["snapshot_id"],row["shipment_id"]), "Gold/source identity mismatch")
        types = [a["exception_type"] for a in expected["assessments"]]
        require(set(types) == set(doc["$defs"]["exception_type"]["enum"]), "Gold must cover each category exactly once")
        for assessment in expected["assessments"]:
            validate_assessment_semantics(assessment, registry)
            for target in assessment["expected_sections"]:
                require(section_key(target) in sections, "Unknown expected SOP section")
            require(all(b["exception_type"] == assessment["exception_type"] for b in assessment["blockers"]), "Category blocker attached to wrong category")
        for evidence in [expected["common_evidence"]]+[a["evidence"] for a in expected["assessments"]]:
            for field in ("required_ids","missing_ids","conflicting_ids"):
                unique(evidence[field],field)
            require(set(evidence["missing_ids"]+evidence["conflicting_ids"]) <= set(evidence["required_ids"]), "Evidence gap must reference a required item")
    unique(targets,"gold row targets")
    require(set(targets) == set(range(len(inp["shipments"]))), "Each input shipment needs a gold target")
    # Deliberately do not calculate facts, decide eligibility/state, or score gold correctness.


def validate_question(value, root=ROOT):
    validate_shape(value, "retrieval_question", schema_document(root))
    require(value["example_only"] == (value["split"] == "EXAMPLE"), "Question split mismatch")
    registry, sections = validate_bundle(root, check_hashes=False)
    require(value["gold_policy_version"] == registry["bundle_version"], "Unknown gold policy version")
    if value["kind"] == "ANSWERABLE":
        require(bool(value["gold_sections"]) and value["negative_reason"] is None, "Answerable question needs gold sections")
    else:
        require(not value["gold_sections"] and not value["required_sections"] and value["negative_reason"] is not None, "Negative question cannot fabricate gold sections")
    gold = [section_key(x) for x in value["gold_sections"]]
    needed = [section_key(x) for x in value["required_sections"]]
    unique(gold, "gold sections")
    unique(needed, "required sections")
    require(set(needed) <= set(gold), "Required sections must be relevant")
    require(set(gold) <= sections.keys(), "Unknown gold section/version")


def main():
    registry, sections = validate_bundle()
    examples = sorted((ROOT / "examples").glob("*.example.json"))
    for path in examples:
        validate_fixture(read_json(path))
    development = sorted((ROOT / "evaluation/development").rglob("*.json"))
    for path in development:
        validate_fixture(read_json(path))
    print(f"Validated {len(registry['rules'])} rules, {len(registry['evidence_requirements'])} evidence requirements, "
          f"{len(registry['sops'])} SOPs/{len(sections)} sections, {len(examples)} unscored examples, "
          f"{len(development)} DEVELOPMENT fixtures.")
    print("Structural consistency only; no triage execution, evaluation scoring, or semantic proof of SOP prose.")


if __name__ == "__main__":
    main()
