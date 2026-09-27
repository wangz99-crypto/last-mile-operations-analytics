"""Independent category decisions, scoped evidence gates and exact section support."""
from .policy import COMMON, TYPES, section_key, sections_unique


def evidence(required=(), missing=(), conflicting=(), inactive=False):
    return dict(completeness="NOT_APPLICABLE" if inactive else ("INCOMPLETE" if missing or conflicting else "COMPLETE"),
                required_ids=sorted(set(required)), missing_ids=sorted(set(missing)), conflicting_ids=sorted(set(conflicting)))


def blocker(code, category, reason, fields, requirements, *, dependent_decision=None):
    return dict(code=code, scope="CATEGORY", exception_type=category, dependent_decision=dependent_decision or category,
                reason=reason, field_refs=fields, requirement_ids=list(requirements))


def assessment(category, rules, result, eligible, policy, required=None, missing=(), conflicting=(), blockers=(),
               subtype=None, subtypes=(), triggers=(), packet_context=None):
    inactive = result in ("FALSE", "NOT_APPLICABLE")
    required = [] if inactive else (policy.dependencies(rules) if required is None else list(required))
    missing, conflicting, blockers = list(missing), list(conflicting), list(blockers)
    if not inactive and packet_context is not None:
        packet_missing, packet_blocks = packet_gaps(packet_context, category)
        required.extend(packet_missing)
        missing.extend(packet_missing)
        blockers.extend(packet_blocks)
    if result == "UNKNOWN" or rules == ["F-UNKNOWN"]:
        sections = policy.sections(rules, failure=True)
    else:
        sections = policy.sections(rules, required)
        if "F-UNKNOWN" in rules and eligible is None:
            sections += policy.sections(["F-UNKNOWN"], failure=True)
    unavailable = [s for s in sections if section_key(s) not in policy.available_sections]
    if unavailable and not inactive:
        required.append("E-POLICY-SECTIONS"); missing.append("E-POLICY-SECTIONS")
        blockers.append(blocker("MISSING_POLICY_SECTIONS", category, "Required exact policy sections unavailable or checksum invalid",
                                ["policy.sections"], ["E-POLICY-SECTIONS"]))
        sections += policy.sections([], ["E-POLICY-SECTIONS"], failure=True)
    sections = sections_unique([s for s in sections if section_key(s) in policy.available_sections])
    gate = evidence(required, missing, conflicting, inactive)
    state = "NORMAL" if inactive else ("NEEDS_REVIEW" if result == "UNKNOWN" or missing or conflicting
                                        else ("READY_TO_ESCALATE" if eligible else "MONITOR"))
    return dict(exception_type=category, result=result, escalation_eligible=eligible, action_state=state,
                rule_ids=list(rules), expected_sections=sections, evidence=gate, blockers=blockers,
                subtype=subtype, subtype_assessments=list(subtypes), supported_triggers=list(triggers))


def packet_gaps(ctx, category):
    missing, blocks = [], []
    for field in ("carrier", "source_system"):
        value = ctx.shipment.get(field)
        if not isinstance(value, str) or not value:
            missing.append("E-IDENTITY")
            blocks.append(blocker("MISSING_CARRIER" if field == "carrier" else "MISSING_SOURCE", category,
                                  f"Missing {field} blocks the dependent packet, not known classification",
                                  [f"input.shipments[{ctx.index}].{field}"], ["E-IDENTITY"],
                                  dependent_decision="LATE_DELIVERY_PACKET" if category == TYPES[0] else "PACKET"))
    return missing, blocks


def event_conflict_code(ctx, requirement):
    if any(f["code"] == "INVALID_EVENT" and requirement in f["requirement_ids"] for f in ctx.findings):
        return "INVALID_EVENT"
    return "CONFLICTING_EVENT_IDENTITY"


def late(ctx, facts, policy):
    category = TYPES[0]
    if facts.overdue is None:
        b = blocker("MISSING_PROMISE", category, "Missing or invalid promise", [f"input.shipments[{ctx.index}].promised_delivery_at"], ["E-LATE"])
        return assessment(category, ["L-UNKNOWN"], "UNKNOWN", None, policy, missing=["E-LATE"], blockers=[b], packet_context=ctx)
    if facts.overdue.total_seconds() == 0:
        return assessment(category, ["L-0"], "FALSE", False, policy)
    eligible = policy.meets("LATE_ESCALATE_HOURS", facts.overdue)
    rule = "L-2" if eligible else "L-1"
    return assessment(category, [rule], "TRUE", eligible, policy, triggers=[rule] if eligible else [], packet_context=ctx)


def stale(ctx, facts, policy):
    category = TYPES[1]
    if not ctx.history or ctx.scan_uncertain:
        if "E-STALE" in ctx.conflicting_requirements:
            fields = [f["path"] for f in ctx.findings if "E-STALE" in f["requirement_ids"]]
            b = blocker(event_conflict_code(ctx, "E-STALE"), category, "Invalid or conflicting scan evidence affects inactivity", fields, ["E-STALE"])
            return assessment(category, ["S-UNKNOWN"], "UNKNOWN", None, policy, conflicting=["E-STALE"], blockers=[b], packet_context=ctx)
        b = blocker("INCOMPLETE_SCAN_HISTORY", category, "Scan history is incomplete or invalid for inactivity", ["history_complete"], ["E-STALE"])
        return assessment(category, ["S-UNKNOWN"], "UNKNOWN", None, policy, missing=["E-STALE"], blockers=[b], packet_context=ctx)
    if facts.scan_gap is None:
        if ctx.shipment.get("current_status") == "PRE_TRANSIT":
            return assessment(category, ["S-PRE"], "NOT_APPLICABLE", False, policy)
        b = blocker("MISSING_QUALIFYING_SCAN", category, "No valid qualifying scan in in-network history", ["input.tracking_events"], ["E-STALE"])
        return assessment(category, ["S-UNKNOWN"], "UNKNOWN", None, policy, missing=["E-STALE"], blockers=[b], packet_context=ctx)
    if not policy.meets("STALE_DETECT_HOURS", facts.scan_gap):
        return assessment(category, ["S-0"], "FALSE", False, policy)
    eligible = policy.meets("STALE_ESCALATE_HOURS", facts.scan_gap)
    rule = "S-2" if eligible else "S-1"
    return assessment(category, [rule], "TRUE", eligible, policy, triggers=[rule] if eligible else [], packet_context=ctx)


def failed_address(ctx, facts, policy):
    category = TYPES[2]
    count, address = facts.output["failed_attempt_count"], facts.output["address_exception_active"]
    mapping = policy.rules["F-UNKNOWN"]["subtype_dependency_ids"]
    trigger_rules = policy.rules["F-UNKNOWN"]["subtype_readiness_contract"]["eligible_trigger_rule_ids"]
    failed_eligible = policy.meets("FAILED_ATTEMPTS_ESCALATE", count) if count is not None else None
    address_eligible = policy.meets("ADDRESS_ACTIVE_ESCALATES", address) if address is not None else None
    unknown, blocks, gaps, conflicts = [], [], [], []
    failed_conflict = "E-FAILED" in ctx.conflicting_requirements
    address_conflict = facts.address_conflict or "E-ADDRESS" in ctx.conflicting_requirements
    if count is None:
        unknown.append("FAILED_ATTEMPT")
        (conflicts if failed_conflict else gaps).extend(mapping["FAILED_ATTEMPT"])
        invalid_ids = [f for f in ctx.findings if f["code"] == "MISSING_ATTEMPT_ID"]
        conflict_refs = [f["path"] for f in ctx.findings if "E-FAILED" in f["requirement_ids"]]
        blocks.append(blocker(event_conflict_code(ctx, "E-FAILED") if failed_conflict else ("MISSING_ATTEMPT_ID" if invalid_ids else "INCOMPLETE_ATTEMPT_HISTORY"), category,
                              "Attempt history or physical attempt identity is incomplete, invalid or conflicting",
                              conflict_refs if failed_conflict else ([f["path"] for f in invalid_ids] or ["history_complete"]), mapping["FAILED_ATTEMPT"],
                              dependent_decision="FAILED_ATTEMPT"))
    if address is None:
        unknown.append("ADDRESS_EXCEPTION")
        if address_conflict:
            conflicts += mapping["ADDRESS_EXCEPTION"]
            fields = [f"input.tracking_events[{i}].{field}" for i, e, _ in ctx.events
                      if e["event_code"] in ("ADDRESS_EXCEPTION", "ADDRESS_CLEARED") for field in ("event_time", "event_code")]
            if "E-ADDRESS" in ctx.conflicting_requirements:
                fields = [f["path"] for f in ctx.findings if "E-ADDRESS" in f["requirement_ids"]]
            blocks.append(blocker(event_conflict_code(ctx, "E-ADDRESS") if "E-ADDRESS" in ctx.conflicting_requirements else "CONFLICTING_ADDRESS_MARKERS",
                                  category, "Invalid or conflicting address marker evidence", fields, mapping["ADDRESS_EXCEPTION"],
                                  dependent_decision="ADDRESS_EXCEPTION"))
        else:
            gaps += mapping["ADDRESS_EXCEPTION"]
            blocks.append(blocker("UNKNOWN_ADDRESS_STATE", category, "Incomplete or invalid marker history", ["history_complete"], mapping["ADDRESS_EXCEPTION"],
                                  dependent_decision="ADDRESS_EXCEPTION"))
    subtype_rows = {
        "FAILED_ATTEMPT": dict(subtype="FAILED_ATTEMPT", result="UNKNOWN" if count is None else ("TRUE" if count > 0 else "FALSE"),
                               escalation_eligible=failed_eligible, evidence=evidence(mapping["FAILED_ATTEMPT"],
                                   mapping["FAILED_ATTEMPT"] if count is None and not failed_conflict else [],
                                   mapping["FAILED_ATTEMPT"] if failed_conflict else [])),
        "ADDRESS_EXCEPTION": dict(subtype="ADDRESS_EXCEPTION", result="UNKNOWN" if address is None else ("TRUE" if address else "FALSE"),
                                  escalation_eligible=address_eligible, evidence=evidence(mapping["ADDRESS_EXCEPTION"],
                                      mapping["ADDRESS_EXCEPTION"] if address is None and not address_conflict else [],
                                      mapping["ADDRESS_EXCEPTION"] if address_conflict else []))}
    active = []
    if count is not None and count > 0:
        active.append("FAILED_ATTEMPT")
    if address:
        active.append("ADDRESS_EXCEPTION")
    subtype = "BOTH" if len(active) == 2 else (active[0] if active else None)
    triggers = [trigger_rules[name] for name, eligible in (("FAILED_ATTEMPT", failed_eligible), ("ADDRESS_EXCEPTION", address_eligible)) if eligible]
    if triggers:
        supported = []
        unsupported = []
        for trigger in triggers:
            refs = policy.sections([trigger], policy.dependencies([trigger]))
            (supported if all(section_key(s) in policy.available_sections for s in refs) else unsupported).append(trigger)
        # If only one eligible basis has its policy support, it can still be
        # ready. Keep the other candidate explicitly blocked in its subtype.
        basis = supported or triggers
        if supported and unsupported:
            for name, trigger in trigger_rules.items():
                if trigger in unsupported:
                    subtype_rows[name]["evidence"] = evidence(mapping[name] + ["E-POLICY-SECTIONS"], ["E-POLICY-SECTIONS"])
                    b = blocker("MISSING_POLICY_SECTIONS", category, "Other eligible subtype lacks required section support",
                                ["policy.sections"], ["E-POLICY-SECTIONS"], dependent_decision=name)
                    blocks.append(b)
        rule_ids = basis + (["F-UNKNOWN"] if unknown else [])
        # The escalation basis includes only supported eligible triggers. Unknown
        # other-subtype gaps remain in subtype rows/blockers, outside its gate.
        required = policy.dependencies(basis)
        return assessment(category, rule_ids, "TRUE", True, policy, required=required,
                          blockers=blocks, subtype=subtype,
                          subtypes=[subtype_rows[n] for n in active + unknown], triggers=basis, packet_context=ctx)
    if unknown:
        required = (policy.dependencies(["F-UNKNOWN"]) + gaps + conflicts) if len(unknown) == 2 else gaps + conflicts
        # F-1 records the confirmed non-eligible attempt condition only; its
        # complete MONITOR disposition still requires known inactive address.
        rules = (["F-1"] if "FAILED_ATTEMPT" in active and failed_eligible is False else []) + ["F-UNKNOWN"]
        return assessment(category, rules, "TRUE" if active else "UNKNOWN", None, policy, required=required,
                          missing=gaps, conflicting=conflicts, blockers=blocks, subtype=subtype,
                          subtypes=list(subtype_rows.values()) if len(unknown) == 1 else [], packet_context=ctx)
    if count == 0 and not address:
        return assessment(category, ["F-0"], "FALSE", False, policy)
    return assessment(category, ["F-1"], "TRUE", False, policy,
                      subtype=subtype, subtypes=list(subtype_rows.values()), packet_context=ctx)
