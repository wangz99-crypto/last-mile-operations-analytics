"""Small V1 input validation and dependency-scoped quarantine, not an ETL layer."""
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .policy import timestamp


class CanonicalInputError(ValueError):
    def __init__(self, findings):
        self.findings = findings
        super().__init__("Canonical input rejected; inspect findings")


def shape_errors(value, spec, defs, path):
    """Apply the frozen record schema, returning field paths (no coercion)."""
    if "$ref" in spec:
        return shape_errors(value, defs[spec["$ref"].split("/")[-1]], defs, path)
    if "anyOf" in spec:
        return [] if any(not shape_errors(value, b, defs, path) for b in spec["anyOf"]) else [path]
    checks = {"object": isinstance(value, dict), "array": isinstance(value, list),
              "string": isinstance(value, str), "boolean": type(value) is bool,
              "null": value is None, "integer": type(value) is int,
              "number": type(value) in (int, float)}
    if spec.get("type") and not checks[spec["type"]]:
        return [path]
    errors = []
    if "enum" in spec and value not in spec["enum"]:
        errors.append(path)
    if isinstance(value, str):
        if len(value) < spec.get("minLength", 0) or ("pattern" in spec and not re.search(spec["pattern"], value)):
            errors.append(path)
        if spec.get("format") == "date-time":
            try:
                timestamp(value)
            except (ValueError, TypeError):
                errors.append(path)
    if isinstance(value, dict):
        props = spec.get("properties", {})
        errors.extend(f"{path}.{k}" for k in spec.get("required", []) if k not in value)
        errors.extend(f"{path}.{k}" for k in value if k not in props and spec.get("additionalProperties") is False)
        for k, v in value.items():
            if k in props:
                errors.extend(shape_errors(v, props[k], defs, f"{path}.{k}"))
    return sorted(set(errors))


def finding(path, code, requirements, reason, scope="CATEGORY"):
    return dict(path=path, code=code, scope=scope, requirement_ids=list(requirements), reason=reason)


def event_identity(row):
    if isinstance(row, dict):
        parts = tuple(row.get(k) for k in ("snapshot_id", "source_system", "event_id"))
        if all(isinstance(v, str) and v for v in parts):
            return parts
    return None


def event_value(row, name):
    """Comparison only: valid UTC representations of one instant are equivalent.

    Missing, null and invalid values remain distinct; source records are untouched.
    """
    if name not in row:
        return ("missing",)
    value = row[name]
    if name == "event_time":
        try:
            return ("utc", timestamp(value))
        except (ValueError, TypeError):
            pass
    return ("json", json.dumps(value, sort_keys=True, separators=(",", ":")))


def duplicate_dependencies(rows, changed, ctx, policy):
    """Only conflicting fields used by a decision invalidate that dependency."""
    codes = [r.get("event_code") for r in rows]
    unknown_code = any(code not in policy.schema["$defs"]["event_code"]["enum"] for code in codes)
    core_changed = bool(changed & {"event_time", "event_code", "shipment_id"})
    requirements = set()
    if core_changed and (unknown_code or any(code in policy.registry["qualifying_physical_scans"] for code in codes)):
        requirements.add("E-STALE")
    if (core_changed or "attempt_id" in changed) and (unknown_code or "ATTEMPT_FAILED" in codes):
        requirements.add("E-FAILED")
    if core_changed and (unknown_code or any(code in ("ADDRESS_EXCEPTION", "ADDRESS_CLEARED") for code in codes)):
        requirements.add("E-ADDRESS")
    if "shipment_id" in changed:
        requirements.add("E-IDENTITY")
    if any(code in ("DELIVERED", "CANCELLED") for code in codes):
        status = ctx.shipment.get("current_status")
        # A conflicting closure/open event, or a closure contradicting current
        # status, cannot be discarded to restore a ready open-shipment result.
        if ("event_code" in changed or status in policy.registry["open_statuses"]
                or (status == "CANCELLED" and "DELIVERED" in codes)
                or (status == "DELIVERED" and "CANCELLED" in codes)):
            requirements.add("E-STATUS")
        if "event_time" in changed:
            valid_times = []
            for row in rows:
                try:
                    valid_times.append(ctx.as_of is not None and timestamp(ctx.shipment.get("created_at")) <= timestamp(row.get("event_time")) <= ctx.as_of)
                except (ValueError, TypeError):
                    valid_times.append(False)
            if not all(valid_times):
                requirements.add("E-STATUS")
    return requirements


@dataclass
class Context:
    index: int
    shipment: dict
    as_of: object
    events: list = field(default_factory=list)
    history: bool = False
    global_findings: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    informational_findings: list = field(default_factory=list)
    invalid_fields: set = field(default_factory=set)
    scan_uncertain: bool = False
    attempts_invalid: bool = False
    address_invalid: bool = False
    conflicting_requirements: set = field(default_factory=set)


def validate_input(manifest, reference, data, profile, policy):
    if profile not in ("CANONICAL", "RAW_VALIDATION_CASE"):
        raise ValueError("Unknown input profile")
    if not isinstance(data, dict) or set(data) != {"shipments", "tracking_events", "history_declarations"}:
        raise ValueError("Input must contain exactly the three snapshot tables")
    if any(not isinstance(data[k], list) for k in data) or not data["shipments"]:
        raise ValueError("Snapshot tables must be arrays with at least one shipment")
    defs = policy.schema["$defs"]
    findings, structural, global_context = [], [], []
    manifest_errors = shape_errors(manifest, defs["manifest"], defs, "manifest")
    if manifest_errors:
        global_context.append(finding("manifest", "INVALID_SNAPSHOT_CONTEXT", ["E-IDENTITY"], "Invalid snapshot manifest", "SHIPMENT"))
        structural.extend(manifest_errors)
    try:
        as_of = timestamp(manifest.get("as_of"))
    except (AttributeError, ValueError, TypeError):
        as_of = None
    snapshot = manifest.get("snapshot_id") if isinstance(manifest, dict) else None
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
    if not isinstance(manifest, dict) or manifest.get("checksum") != digest:
        global_context.append(finding("manifest.checksum", "SNAPSHOT_CHECKSUM_MISMATCH", ["E-IDENTITY"], "Input checksum differs from frozen snapshot", "SHIPMENT"))
    if not policy.active(reference, as_of):
        global_context.append(finding("policy", "INVALID_POLICY_CONTEXT", ["E-POLICY-CONTEXT"], "Bundle/version/checksum/effective interval unavailable or invalid", "SHIPMENT"))
    findings.extend(global_context)
    def key(row):
        if not isinstance(row, dict):
            return None
        parts = (row.get("snapshot_id"), row.get("shipment_id"))
        return parts if all(isinstance(x, str) and x for x in parts) else None
    counts = Counter(key(s) for s in data["shipments"])
    contexts = []
    for i, raw in enumerate(data["shipments"]):
        s = raw if isinstance(raw, dict) else {}
        ctx = Context(i, s, as_of, global_findings=list(global_context))
        path = f"input.shipments[{i}]"
        errors = shape_errors(raw, defs["shipment"], defs, path)
        structural.extend(errors)
        ctx.invalid_fields = {e.removeprefix(path + ".") for e in errors}
        if key(s) is None or s.get("snapshot_id") != snapshot or counts[key(s)] != 1:
            f = finding(path, "INVALID_SHIPMENT_IDENTITY", ["E-IDENTITY"], "Invalid, duplicated or cross-snapshot shipment identity", "SHIPMENT")
            ctx.global_findings.append(f); findings.append(f); structural.append(path)
        known_statuses = policy.registry["open_statuses"] + policy.registry["closed_statuses"]
        if s.get("current_status") not in known_statuses:
            f = finding(path + ".current_status", "UNKNOWN_SHIPMENT_STATUS", ["E-STATUS"], "Unknown canonical shipment status", "SHIPMENT")
            ctx.global_findings.append(f); findings.append(f)
        for error in errors:
            if error.endswith(".current_status"):
                continue
            req = "E-LATE" if error.endswith(".promised_delivery_at") else "E-IDENTITY"
            if error.endswith(".delivered_at"):
                req = "E-STATUS"
            f = finding(error, "INVALID_SHIPMENT_FIELD", [req], "Canonical shipment shape violation", "SHIPMENT" if req == "E-STATUS" else "CATEGORY")
            findings.append(f); ctx.findings.append(f)
            if req == "E-STATUS":
                ctx.global_findings.append(f)
        contexts.append(ctx)
    event_groups = defaultdict(list)
    for j, row in enumerate(data["tracking_events"]):
        identity = event_identity(row)
        if identity is not None:
            event_groups[identity].append((j, row))
    for table, contract in (("tracking_events", "tracking_event"), ("history_declarations", "history_declaration")):
        for j, raw in enumerate(data[table]):
            path = f"input.{table}[{j}]"
            row = raw if isinstance(raw, dict) else {}
            errors = shape_errors(raw, defs[contract], defs, path)
            structural.extend(errors)
            group, changed = [(j, row)], set()
            if table == "tracking_events" and event_identity(row) is not None:
                group = event_groups[event_identity(row)]
                if len(group) > 1:
                    structural.append(path)  # Canonical uniqueness stays strict.
                    if j != group[0][0]:
                        continue
                    fields = {name for _, version in group for name in version}
                    changed = {name for name in fields if len({event_value(version, name) for _, version in group}) > 1}
            matches = [c for c in contexts if any(key(version) is not None and key(version) == key(c.shipment) for _, version in group)]
            if not matches:
                f = finding(path, "BROKEN_SNAPSHOT_REFERENCE", ["E-IDENTITY"], "Record does not belong to a shipment in this snapshot", "SHIPMENT")
                findings.append(f); structural.append(path)
                for c in contexts:
                    c.global_findings.append(f)
                continue
            for c in matches:
                if table == "history_declarations":
                    declarations = [h for h in data[table] if key(h) == key(c.shipment)]
                    c.history = not errors and len(declarations) == 1 and row.get("history_complete") is True
                    if len(declarations) != 1:
                        structural.append(path)
                    continue
                if len(group) > 1 and not changed:
                    f = finding(path, "DUPLICATE_EVENT_IDENTITY", [],
                                f"Identical source event {event_identity(row)!r} delivered {len(group)} times; processed once.",
                                "SHIPMENT")
                    c.findings.append(f); findings.append(f)
                    c.informational_findings.append(f)
                if changed:
                    requirements = duplicate_dependencies([v for _, v in group], changed, c, policy)
                    c.conflicting_requirements.update(requirements)
                    c.scan_uncertain |= "E-STALE" in requirements
                    c.attempts_invalid |= "E-FAILED" in requirements
                    c.address_invalid |= "E-ADDRESS" in requirements
                    global_requirements = requirements & {"E-IDENTITY", "E-STATUS"}
                    for index, _ in group:
                        f = finding(f"input.tracking_events[{index}]", "CONFLICTING_EVENT_IDENTITY",
                                    sorted(requirements), "Same event identity has conflicting fields: " + ", ".join(sorted(changed)),
                                    "SHIPMENT" if global_requirements else "CATEGORY")
                        c.findings.append(f); findings.append(f)
                        if global_requirements:
                            c.global_findings.append(dict(f, scope="SHIPMENT", requirement_ids=sorted(global_requirements)))
                        if not requirements and index == group[0][0]:
                            # One warning per identity; findings keep every row.
                            c.informational_findings.append(f)
                    if changed & {"event_time", "event_code", "shipment_id"}:
                        continue  # No version supplies an authoritative core event.
                    # Retain only agreed fields for independent calculations;
                    # disputed values remain solely in the unchanged raw input.
                    row = {name: value for name, value in group[0][1].items() if name not in changed}
                code = row.get("event_code")
                attempt_bad = code == "ATTEMPT_FAILED" and (not isinstance(row.get("attempt_id"), str) or not row["attempt_id"])
                if attempt_bad and "attempt_id" not in changed:
                    structural.append(path + ".attempt_id")
                    c.attempts_invalid = True
                    f = finding(path + ".attempt_id", "MISSING_ATTEMPT_ID", ["E-FAILED"], "ATTEMPT_FAILED requires a nonempty attempt_id")
                    c.findings.append(f); findings.append(f)
                # attempt_id alone is irrelevant to physical-scan time or address ordering.
                core_errors = [e for e in errors if not e.endswith(".attempt_id") and not e.endswith(".facility_id")]
                valid_time = True
                try:
                    when = timestamp(row.get("event_time")); created = timestamp(c.shipment.get("created_at"))
                    valid_time = c.as_of is not None and created <= when <= c.as_of
                except (ValueError, TypeError):
                    valid_time = False
                if core_errors or not valid_time:
                    reqs = []
                    if code in policy.registry["qualifying_physical_scans"] or code not in defs["event_code"]["enum"]:
                        c.scan_uncertain = True; reqs.append("E-STALE")
                    if code == "ATTEMPT_FAILED" or code not in defs["event_code"]["enum"]:
                        c.attempts_invalid = True; reqs.append("E-FAILED")
                    if code in ("ADDRESS_EXCEPTION", "ADDRESS_CLEARED") or code not in defs["event_code"]["enum"]:
                        c.address_invalid = True; reqs.append("E-ADDRESS")
                    c.conflicting_requirements.update(reqs)
                    f = finding(path, "INVALID_EVENT", reqs, "Invalid event fields, identity or event time; dependent facts quarantined")
                    c.findings.append(f); findings.append(f)
                    continue
                c.events.append((j, row, not attempt_bad))
    for c in contexts:
        s = c.shipment; path = f"input.shipments[{c.index}]"
        declarations = [h for h in data["history_declarations"] if key(h) is not None and key(h) == key(s)]
        if len(declarations) != 1:
            structural.append("input.history_declarations")
        if not c.history:
            f = finding("input.history_declarations", "INCOMPLETE_HISTORY", ["E-STALE", "E-FAILED", "E-ADDRESS"], "Relevant history is absent, invalid or explicitly incomplete")
            c.findings.append(f); findings.append(f)
        delivered = s.get("delivered_at")
        if delivered is not None and "delivered_at" not in c.invalid_fields:
            try:
                delivered_time = timestamp(delivered)
                created = timestamp(s.get("created_at"))
                valid_delivery = c.as_of is not None and created <= delivered_time <= c.as_of
            except (ValueError, TypeError):
                valid_delivery = False
            if not valid_delivery:
                f = finding(path + ".delivered_at", "INVALID_DELIVERY_TIME", ["E-STATUS"], "Closure timestamp lies outside the valid snapshot interval", "SHIPMENT")
                c.global_findings.append(f); findings.append(f)
        closure_events = [e for _, e, _ in c.events if e["event_code"] in ("DELIVERED", "CANCELLED")]
        open_status = s.get("current_status") in policy.registry["open_statuses"]
        conflict = open_status and (delivered is not None or bool(closure_events))
        if s.get("current_status") == "CANCELLED" and (delivered is not None or any(e["event_code"] == "DELIVERED" for e in closure_events)):
            conflict = True
        if s.get("current_status") == "DELIVERED" and any(e["event_code"] == "CANCELLED" for e in closure_events):
            conflict = True
        if conflict:
            f = finding(path + ".current_status", "OPEN_CLOSED_STATUS_CONFLICT", ["E-STATUS"], "Current status contradicts closure timestamp/event facts", "SHIPMENT")
            c.global_findings.append(f); findings.append(f)
    # Canonical shape/identity must pass before operational evaluation; raw keeps findings.
    if profile == "CANONICAL" and structural:
        raise CanonicalInputError([finding(p, "CANONICAL_SHAPE_OR_IDENTITY", [], "Canonical record validation failed") for p in sorted(set(structural))] + findings)
    return contexts, findings
