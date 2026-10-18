"""Public synthetic cases over the unchanged engine and exact policy-section store.

No evaluation datasets, model, arbitrary-question answering or operational writes.
"""
import copy
import hashlib
import json
from pathlib import Path

from domain.engine import triage_snapshot
from domain.engine.policy import Policy
from domain.retrieval import SectionStore, retrieve_case_sections

DOMAIN = Path(__file__).resolve().parents[1] / "domain"
CASES = (
    ("late", "Late delivery", "A missed promise, with gaps to keep visible.", "LATE_DELIVERY"),
    ("stale", "Stale tracking", "No physical scan for 30 hours.", "STALE_TRACKING"),
    ("address", "Failed attempt / address", "Two attempts and an unresolved address notice.", "FAILED_ATTEMPT_ADDRESS"),
    ("missing", "Missing delivery promise", "Incomplete facts require a human check.", "LATE_DELIVERY"),
    ("normal", "On track", "A healthy shipment for comparison.", "LATE_DELIVERY"),
    ("late-monitor", "Late delivery", "Six hours past the delivery promise.", "LATE_DELIVERY"),
    ("stale-ready", "Stale tracking", "No physical scan for 48 hours.", "STALE_TRACKING"),
    ("attempt-one", "Failed attempt", "One distinct attempt needs monitoring.", "FAILED_ATTEMPT_ADDRESS"),
    ("attempt-missing", "Attempt identity missing", "A failure event lacks its physical attempt ID.", "FAILED_ATTEMPT_ADDRESS"),
    ("address-conflict", "Conflicting address notices", "Simultaneous notices require a history review.", "FAILED_ATTEMPT_ADDRESS"),
)
LABELS = {"LATE_DELIVERY": "Late delivery", "STALE_TRACKING": "Stale tracking",
          "FAILED_ATTEMPT_ADDRESS": "Failed attempt / address"}
GAP_GROUPS = {
    "LATE_DELIVERY": ("promise", "Delivery promise missing or invalid"),
    "STALE_TRACKING": ("tracking", "Tracking history incomplete"),
    "FAILED_ATTEMPT": ("attempt", "Attempt history / identity incomplete"),
    "ADDRESS_EXCEPTION": ("address", "Address state unresolved"),
}
RULE_COPY = {
    "L-0": "The delivery promise has not been missed.",
    "L-1": "Delivery is overdue, but has not reached the policy escalation threshold.",
    "L-2": "Delivery is overdue long enough for the operating rules to call for further action.",
    "L-UNKNOWN": "The delivery promise is missing or invalid; lateness cannot be established.",
    "S-0": "The last physical scan is within the policy tracking window.",
    "S-1": "Tracking is stale, but has not reached the policy escalation threshold.",
    "S-2": "There has been no package scan for long enough that the operating rules call for further action.",
    "S-UNKNOWN": "Tracking history is incomplete or invalid; inactivity cannot be established.",
    "S-PRE": "Tracking inactivity does not apply to this pre-transit shipment.",
    "F-0": "Complete history shows no failed attempts or active address issue.",
    "F-1": "One distinct failed attempt is recorded; the policy calls for monitoring.",
    "F-2": "Distinct failed attempts meet the policy escalation threshold.",
    "F-3": "An unresolved address notice meets the policy escalation condition.",
    "F-UNKNOWN": "An attempt or address decision remains unresolved; independent evidence is preserved.",
    "D-CLOSED": "The shipment is closed and is outside active exception triage.",
    "D-CONTEXT": "Shipment or policy context could not be established.",
    "D-STATUS": "Shipment status is missing or conflicting.",
}


def case_packet(case_id):
    if case_id not in {row[0] for row in CASES}:
        raise KeyError(case_id)
    name = "late_with_gaps" if case_id == "late" else "normal"
    example = json.loads((DOMAIN / "examples" / f"{name}.example.json").read_text(encoding="utf-8"))
    # Only authorized input fields cross the engine boundary; illustrative labels are unused.
    packet = {k: copy.deepcopy(example[k]) for k in ("manifest", "policy", "input", "input_profile")}
    shipment = packet["input"]["shipments"][0]
    events = packet["input"]["tracking_events"]
    if case_id == "stale":
        events[0]["event_time"] = "2026-09-26T06:00:00Z"
    elif case_id == "address":
        for index, (time, code, attempt) in enumerate((
            ("2026-09-26T14:00:00Z", "ATTEMPT_FAILED", "DEMO-ATTEMPT-1"),
            ("2026-09-27T09:00:00Z", "ATTEMPT_FAILED", "DEMO-ATTEMPT-2"),
            ("2026-09-27T09:05:00Z", "ADDRESS_EXCEPTION", None),
        ), 2):
            events.append({**events[0], "event_id": f"EV-{index:03}", "event_time": time,
                           "event_code": code, "attempt_id": attempt})
    elif case_id == "missing":
        shipment["promised_delivery_at"] = None
    elif case_id == "late-monitor":
        shipment["promised_delivery_at"] = "2026-09-27T06:00:00Z"
    elif case_id == "stale-ready":
        shipment["created_at"] = "2026-09-24T00:00:00Z"
        events[0]["event_time"] = "2026-09-25T12:00:00Z"
    elif case_id in ("attempt-one", "attempt-missing"):
        if case_id == "attempt-missing":
            # The existing raw-validation path preserves malformed identity as a
            # scoped review blocker; canonical input correctly rejects it.
            packet["input_profile"] = "RAW_VALIDATION_CASE"
        events.append({**events[0], "event_id": "EV-002", "event_time": "2026-09-27T09:00:00Z",
                       "event_code": "ATTEMPT_FAILED",
                       "attempt_id": "DEMO-ATTEMPT-1" if case_id == "attempt-one" else None})
    elif case_id == "address-conflict":
        for index, code in enumerate(("ADDRESS_EXCEPTION", "ADDRESS_CLEARED"), 2):
            events.append({**events[0], "event_id": f"EV-{index:03}",
                           "event_time": "2026-09-27T09:00:00Z", "event_code": code})
    # Distinct shipment identities, including all event/history join keys.
    identity = f"DEMO-{next(i for i, row in enumerate(CASES, 1) if row[0] == case_id):03}"
    for collection in packet["input"].values():
        for row in collection:
            row["shipment_id"] = identity
    packet["manifest"]["checksum"] = hashlib.sha256(json.dumps(
        packet["input"], sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")).hexdigest()
    return packet


def case_catalog():
    return [{"id": key, "title": title, "description": description, "focus": focus,
             "packet": case_packet(key)} for key, title, description, focus in CASES]


def operational_summary(case_id, packet, result, assessments, sections):
    """Presentation of engine facts, not new classification or priority rules."""
    state = result["aggregate_action_state"]
    driving = [a for a in assessments if a["action_state"] == state]
    gaps = [a for a in assessments if a["blockers"]]
    reasons = [" ".join(a["explanations"]) for a in driving]
    if state == "READY_TO_ESCALATE":
        reasons = reasons[:1] + (["Other checks still need facts. The supported issue can move forward without treating those gaps as resolved."]
                                if gaps else ["The required shipment facts and written operating rules support this next step."])
        next_steps = ["Prepare handoff brief", "Human review", "Escalate after approval"]
    elif state == "NEEDS_REVIEW":
        blockers = [b for a in gaps for b in a["blockers"]]
        reasons += [b["reason"] for b in blockers]
        first = next(({
            "MISSING_ATTEMPT_ID": "Find missing attempt identity",
            "MISSING_PROMISE": "Confirm delivery promise",
            "CONFLICTING_ADDRESS_MARKERS": "Resolve conflicting address notices",
        }[b["code"]] for b in blockers if b["code"] in {
            "MISSING_ATTEMPT_ID", "MISSING_PROMISE", "CONFLICTING_ADDRESS_MARKERS"}), "Review missing or conflicting facts")
        next_steps = [first, "Review source history", "Re-run triage with corrected facts"]
    elif state == "MONITOR":
        reasons = reasons[:1] + ["Current facts do not yet meet a supported escalation condition."]
        next_steps = ["Keep under monitoring", "Check for updated shipment facts", "Re-run triage when facts change"]
    else:
        reasons = ["No active exception is established across the three checks.", "The current facts do not call for exception escalation."]
        next_steps = ["Continue routine tracking", "Review if facts change", "No escalation recommended"]
    ages = [value for value in result["derived_facts"]["exception_age_hours"].values() if value is not None]
    evidence_status = ("Ready basis verified; other gaps" if state == "READY_TO_ESCALATE" and gaps else
                       "Review gaps" if gaps else "No active exception" if state == "NORMAL" else "Complete")
    review_gaps = []
    for assessment in assessments:
        for blocker in assessment["blockers"]:
            group, label = GAP_GROUPS.get(blocker["dependent_decision"], ("other", "Other facts need review"))
            review_gaps.append({"group": group, "label": label, "code": blocker["code"],
                                "exception_type": assessment["exception_type"],
                                "dependent_decision": blocker["dependent_decision"]})
    age_by_type = result["derived_facts"]["exception_age_hours"]
    confirmed_issues = [{"exception_type": a["exception_type"], "label": a["label"],
                         "age_hours": age_by_type[a["exception_type"]]}
                        for a in assessments if a["result"] == "TRUE" and age_by_type[a["exception_type"]] is not None]
    unconfirmed_starts = [a["exception_type"] for a in assessments
                          if a["result"] in ("TRUE", "UNKNOWN") and age_by_type[a["exception_type"]] is None]
    return {"case_id": case_id, "shipment_id": result["shipment_id"],
            "review_gaps": review_gaps, "confirmed_issues": confirmed_issues,
            "unconfirmed_start_checks": unconfirmed_starts,
            "exceptions": [a["label"] for a in assessments if a["result"] in ("TRUE", "UNKNOWN")],
            "unconfirmed_exceptions": [a["label"] for a in assessments if a["result"] == "UNKNOWN"],
            "priority": result["priority"], "action_state": state,
            "age_hours": max(ages) if ages else None,
            "evidence_status": evidence_status, "section_count": len(sections),
            "as_of": packet["manifest"]["as_of"],
            "top_reasons": list(dict.fromkeys(reasons))[:2], "next_steps": next_steps}


def operations_overview(items):
    """Snapshot aggregates with explicit drill-down membership; no new triage rules."""
    states = ("READY_TO_ESCALATE", "NEEDS_REVIEW", "MONITOR", "NORMAL")
    actions = [{"state": state, "case_ids": [row["case_id"] for row in items if row["action_state"] == state]}
               for state in states]
    groups = {}
    for row in items:
        for gap in row["review_gaps"]:
            group = groups.setdefault(gap["group"], {"group": gap["group"], "label": gap["label"], "case_ids": set()})
            group["case_ids"].add(row["case_id"])
    gaps = [{**group, "case_ids": sorted(group["case_ids"])} for group in groups.values()]
    gaps.sort(key=lambda group: (-len(group["case_ids"]), group["group"]))
    longest = []
    for row in items:
        if row["confirmed_issues"]:
            issue = sorted(row["confirmed_issues"], key=lambda i: (-i["age_hours"], i["exception_type"]))[0]
            longest.append({"case_id": row["case_id"], "shipment_id": row["shipment_id"], **issue})
    longest.sort(key=lambda row: (-row["age_hours"], row["shipment_id"]))
    unknown_ids = [row["case_id"] for row in items if row["unconfirmed_start_checks"]]
    return {"shipment_count": len(items), "action_status": actions, "review_gaps": gaps,
            "longest_confirmed": longest, "unconfirmed_start_case_ids": unknown_ids,
            "known_and_unconfirmed_case_ids": [row["case_id"] for row in longest if row["case_id"] in unknown_ids]}


def exception_queue():
    items = [analyze_case(row[0])["summary"] for row in CASES]
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    items.sort(key=lambda row: (order[row["priority"]], row["age_hours"] is None,
                               -(row["age_hours"] or 0), row["shipment_id"]))
    return {"synthetic": True, "as_of": items[0]["as_of"], "items": items,
            "overview": operations_overview(items),
            "sort": "Priority, then longest known exception age, then shipment ID"}


def coverage_demo(store):
    # Explicit scoped exhibit tied to the verified bundle; not a semantic classifier.
    section = store.get(policy_id="SOP-06", version="1.0-demo", section_id="handoff-boundary")
    return {"label": "Policy Coverage Demo", "question": "What reimbursement amount should the customer receive?",
            "status": "POLICY SUPPORT NOT AVAILABLE",
            "explanation": "The active demo SOP does not specify a reimbursement amount. Human review required.",
            "scope": "One predefined coverage example for this fictional policy bundle. No arbitrary-question answerability is claimed.",
            "available": ["Delivery exception handling", "Escalation evidence and human handoff"],
            "missing": ["Reimbursement amount"], "section_id": section.section_id,
            "policy_id": section.policy_id, "boundary_text": section.text}


def analyze_case(case_id):
    packet = case_packet(case_id)
    # Verify the entire public corpus before emitting any policy-backed recommendation.
    store = SectionStore.load()
    bundle = Policy.load()
    output = triage_snapshot(**packet, bundle=bundle)
    result = output["results"][0]
    assessments = [{**a, "label": LABELS[a["exception_type"]],
                    "explanations": [RULE_COPY[r] for r in a["rule_ids"]]}
                   for a in result["assessments"]]
    sections = []
    for record in retrieve_case_sections(result, store=store):
        section = store.get(**dict(zip(("policy_id", "version", "section_id"), record.identity)))
        sections.append({"policy_id": section.policy_id, "version": section.version,
                         "section_id": section.section_id, "title": section.title,
                         "section_title": section.section_title, "text": record.text,
                         "content_hash": record.content_hash, "source_path": record.source_path,
                         "why": "Referenced by the evaluated rules for " + ", ".join(dict.fromkeys(
                             LABELS[r.exception_type] for r in record.requested_by)) + ".",
                         "rule_ids": list(dict.fromkeys(r for request in record.requested_by for r in request.rule_ids))})
    return {"case_id": case_id, "synthetic": True, "analysis_method": "DETERMINISTIC_RULES",
            "evidence_method": "EXACT_POLICY_SECTION", "model_used": False,
            "packet": packet, "summary": operational_summary(case_id, packet, result, assessments, sections),
            "result": result, "assessments": assessments, "evidence": sections,
            "validation_findings": output["validation_findings"], "coverage_demo": coverage_demo(store),
            "notice": "Fictional demo operating policy. Not real carrier or industry standards. Human review required."}
