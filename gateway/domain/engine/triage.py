"""Public input-only entry point; deterministic snapshot orchestration."""
from .facts import derive
from .policy import COMMON, TYPES, Policy
from .rules import assessment, evidence, failed_address, late, packet_gaps, stale
from .validation import validate_input


def aggregate(assessments, shipment_blockers):
    states = {a["action_state"] for a in assessments}
    if shipment_blockers:
        state = "NEEDS_REVIEW"
    else:
        state = next((s for s in ("READY_TO_ESCALATE", "NEEDS_REVIEW", "MONITOR") if s in states), "NORMAL")
    verified = not shipment_blockers and any(a["escalation_eligible"] is True for a in assessments)
    return state, "HIGH" if verified else ("MEDIUM" if state == "NEEDS_REVIEW" else "LOW")


def triage_snapshot(*, manifest, policy, input, input_profile="CANONICAL", bundle=None):
    """Accept only snapshot data and structured policy, never a labeled fixture.

    Returns validation_findings and results (no Gold rationale/provenance).
    A canonical shape/identity failure raises CanonicalInputError with findings;
    RAW_VALIDATION_CASE retains malformed values and isolates their dependencies.
    """
    bundle = Policy.load() if bundle is None else bundle
    contexts, findings = validate_input(manifest, policy, input, input_profile, bundle)
    results = []
    for ctx in contexts:
        facts = derive(ctx, bundle)
        global_blocks = []
        for f in ctx.global_findings:
            fields = [f["path"]]
            if f["code"] == "OPEN_CLOSED_STATUS_CONFLICT":
                if ctx.shipment.get("delivered_at") is not None:
                    fields.append(f"input.shipments[{ctx.index}].delivered_at")
                fields += [f"input.tracking_events[{i}].event_code" for i, e, _ in ctx.events
                           if e["event_code"] in ("DELIVERED", "CANCELLED")]
            global_blocks.append(dict(code=f["code"], scope="SHIPMENT", reason=f["reason"],
                                      field_refs=fields, requirement_ids=f["requirement_ids"]))
        missing, _ = packet_gaps(ctx, TYPES[0])
        common_conflicts = []
        for f in ctx.global_findings:
            (common_conflicts if f["code"] in ("OPEN_CLOSED_STATUS_CONFLICT", "CONFLICTING_EVENT_IDENTITY") else missing).extend(f["requirement_ids"])
        common = evidence(COMMON, missing, common_conflicts)
        if global_blocks:
            rules = ["D-STATUS"] if any("E-STATUS" in b["requirement_ids"] for b in global_blocks) else ["D-CONTEXT"]
            required = sorted({e for b in global_blocks for e in b["requirement_ids"]})
            assessments = [assessment(t, rules, "UNKNOWN", None, bundle, required=required,
                                      missing=[e for e in missing if e in required], conflicting=common_conflicts) for t in TYPES]
        elif facts.output["is_open"] is False:
            assessments = [assessment(t, ["D-CLOSED"], "NOT_APPLICABLE", False, bundle) for t in TYPES]
        else:
            assessments = [late(ctx, facts, bundle), stale(ctx, facts, bundle), failed_address(ctx, facts, bundle)]
        warnings = []
        if not global_blocks:
            for a in assessments:
                if a["result"] == "UNKNOWN" or "F-UNKNOWN" in a["rule_ids"]:
                    warnings.append(dict(code="UNRESOLVED_CATEGORY", scope="CATEGORY", exception_type=a["exception_type"],
                                         message="Unresolved category/subtype retains local blockers; independently supported readiness is preserved.",
                                         related_blocker_codes=[b["code"] for b in a["blockers"]]))
                elif a["action_state"] == "READY_TO_ESCALATE" and a["blockers"]:
                    warnings.append(dict(code="UNSUPPORTED_SUBTYPE", scope="CATEGORY", exception_type=a["exception_type"],
                                         message="Only independently supported subtype triggers form the ready basis.",
                                         related_blocker_codes=[b["code"] for b in a["blockers"]]))
            if ctx.shipment.get("origin_facility_id") is None:
                warnings.append(dict(code="OPTIONAL_FACILITY_MISSING", scope="SHIPMENT", exception_type=None,
                                     message="Optional origin facility is absent.", related_blocker_codes=[]))
        state, priority = aggregate(assessments, global_blocks)
        results.append(dict(input_shipment_index=ctx.index, snapshot_id=ctx.shipment.get("snapshot_id"),
                            shipment_id=ctx.shipment.get("shipment_id"), assessments=assessments,
                            aggregate_action_state=state, priority=priority, common_evidence=common,
                            shipment_blockers=global_blocks, warnings=warnings, derived_facts=facts.output))
    return dict(validation_findings=findings, results=results)
