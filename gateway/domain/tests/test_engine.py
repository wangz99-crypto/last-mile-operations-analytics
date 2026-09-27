"""Input-only tests: no fixture/Gold reads, no application or external service."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from engine import CanonicalInputError, triage_snapshot
from engine.policy import Policy
from engine.triage import aggregate
from validate_contracts import validate_assessment_semantics


def event(identity, time, code="IN_TRANSIT", attempt=None):
    return dict(snapshot_id="UNIT", shipment_id="S1", event_id=identity,
                event_time=time, event_code=code, attempt_id=attempt,
                source_system="TEST", facility_id="FACILITY")


def packet():
    return dict(manifest=dict(snapshot_id="UNIT", as_of="2026-10-01T12:00:00Z", dataset_version="unit", checksum=""),
                policy=dict(bundle_id="last-mile-exception-triage-demo", bundle_version="1.0-demo"),
                input=dict(shipments=[dict(snapshot_id="UNIT", shipment_id="S1", carrier="FICTIONAL", origin_facility_id="FACILITY",
                    created_at="2026-09-27T00:00:00Z", promised_delivery_at="2026-10-02T12:00:00Z", delivered_at=None,
                    current_status="IN_TRANSIT", source_system="TEST")],
                    tracking_events=[event("SCAN", "2026-10-01T10:00:00Z")],
                    history_declarations=[dict(snapshot_id="UNIT", shipment_id="S1", history_complete=True)]))


def seal(x):
    x["manifest"]["checksum"] = hashlib.sha256(json.dumps(x["input"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return x


class EngineTests(unittest.TestCase):
    def run_packet(self, x, bundle=None):
        return triage_snapshot(**seal(x), bundle=bundle)

    def assert_informational_only(self, actual, single, code, paths, scope):
        # Assert the newly required diagnostic exactly, then retain the previous
        # full-output equality check for every other field (including warnings).
        findings = actual["validation_findings"]
        self.assertEqual([{**f, "reason": "checked below"} for f in findings],
                         [dict(path=p, code=code, scope=scope, requirement_ids=[], reason="checked below") for p in paths])
        self.assertTrue(all(f["reason"] for f in findings))
        expected = copy.deepcopy(single)
        expected["validation_findings"] = findings
        first = findings[0]
        expected["results"][0]["warnings"].append(dict(code=code, scope="SHIPMENT", exception_type=None,
            message=f"{first['path']}: {first['reason']}", related_blocker_codes=[]))
        self.assertEqual(actual, expected)

    def test_exact_time_boundaries_without_rounded_hours(self):
        for promise, eligible, state in [("2026-09-30T12:00:00.000001Z", False, "MONITOR"),
                                          ("2026-09-30T12:00:00Z", True, "READY_TO_ESCALATE"),
                                          ("2026-10-01T12:00:00Z", False, "NORMAL")]:
            x=packet(); x["input"]["shipments"][0]["promised_delivery_at"]=promise
            a=self.run_packet(x)["results"][0]["assessments"][0]
            with self.subTest(promise=promise):
                self.assertEqual((a["escalation_eligible"], a["action_state"]), (eligible,state))
        for time, rule in [("2026-09-30T12:00:00Z","S-0"), ("2026-09-30T11:59:59.999999Z","S-1"), ("2026-09-29T12:00:00Z","S-2")]:
            x=packet(); x["input"]["tracking_events"][0]["event_time"]=time
            with self.subTest(scan=time):
                self.assertEqual(self.run_packet(x)["results"][0]["assessments"][1]["rule_ids"],[rule])

    def test_threshold_values_and_operators_come_from_registry(self):
        p=Policy.load(); p=copy.deepcopy(p)
        p.registry["thresholds"]["LATE_ESCALATE_HOURS"].update(value=12, operator=">")
        x=packet(); x["input"]["shipments"][0]["promised_delivery_at"]="2026-10-01T00:00:00Z"
        self.assertEqual(self.run_packet(x,p)["results"][0]["assessments"][0]["rule_ids"],["L-1"])
        p.registry["thresholds"]["LATE_ESCALATE_HOURS"]["operator"]=">="
        self.assertEqual(self.run_packet(x,p)["results"][0]["assessments"][0]["rule_ids"],["L-2"])

    def test_repeat_messages_deduplicate_attempt_identity_not_event_count(self):
        x=packet(); x["input"]["tracking_events"] += [event("F1","2026-10-01T09:00:00Z","ATTEMPT_FAILED","A"), event("F2","2026-10-01T09:00:00Z","ATTEMPT_FAILED","A")]
        r=self.run_packet(x)["results"][0]
        self.assertEqual(r["derived_facts"]["failed_attempt_count"],1)
        self.assertEqual(r["assessments"][2]["rule_ids"],["F-1"])
        x["input"]["tracking_events"][-1]["attempt_id"]="B"
        r=self.run_packet(x)["results"][0]
        self.assertEqual(r["derived_facts"]["failed_attempt_count"],2)
        self.assertEqual(r["assessments"][2]["rule_ids"],["F-2"])

    def test_identical_duplicate_identity_preserves_single_event_facts(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        single=self.run_packet(x)
        repeated=copy.deepcopy(x["input"]["tracking_events"][0])
        # Key order and equivalent valid UTC spelling are not content conflicts.
        repeated["event_time"]="2026-10-01T10:00:00.000000Z"
        x["input"]["tracking_events"].append(dict(reversed(list(repeated.items()))))
        seal(x); original=copy.deepcopy(x)
        actual=triage_snapshot(**x)
        self.assert_informational_only(actual,single,"DUPLICATE_EVENT_IDENTITY",["input.tracking_events[0]"],"SHIPMENT")
        self.assertIn("processed once",actual["results"][0]["warnings"][0]["message"])
        self.assertEqual(x,original)

    def test_identical_duplicate_failed_event_is_one_source_event_and_attempt(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        x["input"]["tracking_events"].append(event("FAILED","2026-10-01T11:00:00Z","ATTEMPT_FAILED","A"))
        single=self.run_packet(x)
        x["input"]["tracking_events"] += [copy.deepcopy(x["input"]["tracking_events"][-1]) for _ in range(2)]
        actual=self.run_packet(x)
        self.assert_informational_only(actual,single,"DUPLICATE_EVENT_IDENTITY",["input.tracking_events[1]"],"SHIPMENT")
        result=actual["results"][0]
        self.assertEqual(result["derived_facts"]["failed_attempt_count"],1)
        self.assertEqual(result["assessments"][2]["action_state"],"MONITOR")
        self.assertFalse(result["assessments"][2]["blockers"])

    def test_canonical_duplicate_identity_rejected_even_when_identical(self):
        for conflicting in (False,True):
            x=packet(); duplicate=copy.deepcopy(x["input"]["tracking_events"][0])
            if conflicting: duplicate["event_time"]="2026-10-01T11:00:00Z"
            x["input"]["tracking_events"].append(duplicate)
            with self.subTest(conflicting=conflicting),self.assertRaises(CanonicalInputError):
                self.run_packet(x)

    def test_conflicting_duplicate_scan_quarantines_versions_and_preserves_late(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        x["input"]["shipments"][0]["promised_delivery_at"]="2026-09-30T12:00:00Z"
        conflicting=copy.deepcopy(x["input"]["tracking_events"][0]); conflicting["event_time"]="2026-10-01T11:00:00Z"
        x["input"]["tracking_events"].append(conflicting)
        for _ in range(2):
            actual=self.run_packet(x); result=actual["results"][0]
            conflicts=[f for f in actual["validation_findings"] if f["code"]=="CONFLICTING_EVENT_IDENTITY"]
            self.assertEqual({f["path"] for f in conflicts},{"input.tracking_events[0]","input.tracking_events[1]"})
            self.assertTrue(all(f["requirement_ids"]==["E-STALE"] and f["scope"]=="CATEGORY" for f in conflicts))
            self.assertIsNone(result["derived_facts"]["last_scan_time"])
            self.assertIsNone(result["derived_facts"]["hours_since_last_scan"])
            self.assertEqual(result["assessments"][1]["evidence"]["conflicting_ids"],["E-STALE"])
            self.assertEqual(result["assessments"][0]["action_state"],"READY_TO_ESCALATE")
            self.assertEqual(result["assessments"][2]["action_state"],"NORMAL")
            self.assertEqual(result["aggregate_action_state"],"READY_TO_ESCALATE")
            self.assertFalse(result["shipment_blockers"])
            x["input"]["tracking_events"].reverse()

    def test_conflicting_attempt_id_preserves_agreed_scan_and_ready_address(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        first=event("FAIL","2026-10-01T11:00:00Z","ATTEMPT_FAILED","A")
        second=dict(first,attempt_id="B")
        x["input"]["tracking_events"] += [first,second,event("ADDR","2026-10-01T11:30:00Z","ADDRESS_EXCEPTION")]
        actual=self.run_packet(x); r=actual["results"][0]; a=r["assessments"][2]
        self.assertEqual(r["derived_facts"]["hours_since_last_scan"],1)
        self.assertIsNone(r["derived_facts"]["failed_attempt_count"])
        self.assertEqual(r["assessments"][1]["action_state"],"NORMAL")
        self.assertEqual(a["action_state"],"READY_TO_ESCALATE")
        self.assertEqual(a["supported_triggers"],["F-3"])
        self.assertEqual(a["evidence"]["completeness"],"COMPLETE")
        self.assertNotIn("E-FAILED",a["evidence"]["required_ids"])
        failed=next(s for s in a["subtype_assessments"] if s["subtype"]=="FAILED_ATTEMPT")
        self.assertEqual(failed["evidence"]["conflicting_ids"],["E-FAILED"])
        self.assertTrue(r["warnings"])

    def test_conflicting_event_codes_block_union_of_dependent_decisions_only(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        first=event("CONFLICT","2026-10-01T11:00:00Z","ATTEMPT_FAILED","A")
        second=dict(first,event_code="ADDRESS_EXCEPTION",attempt_id=None)
        x["input"]["tracking_events"] += [first,second]
        actual=self.run_packet(x); r=actual["results"][0]
        self.assertIsNone(r["derived_facts"]["failed_attempt_count"])
        self.assertIsNone(r["derived_facts"]["address_exception_active"])
        self.assertEqual(r["assessments"][0]["action_state"],"NORMAL")
        self.assertEqual(r["assessments"][1]["action_state"],"NEEDS_REVIEW")
        self.assertEqual(r["assessments"][2]["evidence"]["conflicting_ids"],["E-ADDRESS","E-FAILED"])
        self.assertFalse(r["shipment_blockers"])

    def test_conflicting_closure_version_cannot_be_dropped_to_restore_ready(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        x["input"]["shipments"][0]["promised_delivery_at"]="2026-09-30T12:00:00Z"
        x["input"]["tracking_events"].append(dict(x["input"]["tracking_events"][0],event_code="DELIVERED"))
        actual=self.run_packet(x); r=actual["results"][0]
        self.assertEqual(r["aggregate_action_state"],"NEEDS_REVIEW")
        self.assertEqual(r["priority"],"MEDIUM")
        self.assertIsNone(r["derived_facts"]["is_open"])
        self.assertEqual(r["common_evidence"]["conflicting_ids"],["E-STATUS"])
        self.assertTrue(any(f["code"]=="CONFLICTING_EVENT_IDENTITY" and f["scope"]=="SHIPMENT" for f in actual["validation_findings"]))

    def test_same_event_identity_claiming_two_shipments_blocks_both_identities(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        x["input"]["shipments"].append(dict(x["input"]["shipments"][0],shipment_id="S2"))
        x["input"]["history_declarations"].append(dict(snapshot_id="UNIT",shipment_id="S2",history_complete=True))
        x["input"]["tracking_events"].append(dict(x["input"]["tracking_events"][0],shipment_id="S2"))
        for r in self.run_packet(x)["results"]:
            self.assertEqual(r["aggregate_action_state"],"NEEDS_REVIEW")
            self.assertEqual(r["common_evidence"]["conflicting_ids"],["E-IDENTITY"])

    def test_non_decision_field_conflict_is_visible_without_dependent_blocker(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        single=self.run_packet(x)
        x["input"]["tracking_events"].append(dict(x["input"]["tracking_events"][0],facility_id="OTHER"))
        actual=self.run_packet(x)
        self.assert_informational_only(actual,single,"CONFLICTING_EVENT_IDENTITY",
                                       ["input.tracking_events[0]","input.tracking_events[1]"],"CATEGORY")
        self.assertIn("facility_id",actual["results"][0]["warnings"][0]["message"])
        self.assertTrue(actual["validation_findings"])
        self.assertTrue(all(not f["requirement_ids"] for f in actual["validation_findings"]))

    def test_address_order_episode_and_scan_independence(self):
        x=packet(); x["input"]["tracking_events"] += [event("A1","2026-10-01T07:00:00Z","ADDRESS_EXCEPTION"),
            event("C","2026-10-01T08:00:00Z","ADDRESS_CLEARED"), event("A2","2026-10-01T09:00:00Z","ADDRESS_EXCEPTION"),
            event("A3","2026-10-01T11:00:00Z","ADDRESS_EXCEPTION")]
        r=self.run_packet(x)["results"][0]
        self.assertEqual(r["derived_facts"]["exception_started_at"]["FAILED_ATTEMPT_ADDRESS"],"2026-10-01T09:00:00Z")
        self.assertEqual(r["derived_facts"]["hours_since_last_scan"],2)
        x["input"]["tracking_events"].append(event("C2","2026-10-01T11:00:00Z","ADDRESS_CLEARED"))
        r=self.run_packet(x)["results"][0]
        self.assertIsNone(r["derived_facts"]["address_exception_active"])
        self.assertEqual(r["assessments"][2]["evidence"]["conflicting_ids"],["E-ADDRESS"])
        self.assertFalse(r["shipment_blockers"])

    def test_address_ready_survives_invalid_attempt_identity(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        x["input"]["tracking_events"] += [event("BAD","2026-10-01T11:00:00Z","ATTEMPT_FAILED"), event("A","2026-10-01T11:30:00Z","ADDRESS_EXCEPTION")]
        r=self.run_packet(x)["results"][0]; a=r["assessments"][2]
        self.assertEqual(a["action_state"],"READY_TO_ESCALATE")
        self.assertEqual(a["supported_triggers"],["F-3"])
        self.assertNotIn("E-FAILED",a["evidence"]["required_ids"])
        self.assertTrue(a["blockers"]); self.assertTrue(r["warnings"])
        self.assertIsNone(r["derived_facts"]["failed_attempt_count"])
        self.assertEqual(r["derived_facts"]["hours_since_last_scan"],1)

    def test_failed_ready_survives_unknown_address_and_retains_warning(self):
        x=packet(); x["input"]["tracking_events"] += [event("F1","2026-10-01T08:00:00Z","ATTEMPT_FAILED","A"),
            event("F2","2026-10-01T09:00:00Z","ATTEMPT_FAILED","B"), event("A","2026-10-01T11:00:00Z","ADDRESS_EXCEPTION"),
            event("C","2026-10-01T11:00:00Z","ADDRESS_CLEARED")]
        r=self.run_packet(x)["results"][0]; a=r["assessments"][2]
        self.assertEqual(a["action_state"],"READY_TO_ESCALATE")
        self.assertEqual(a["supported_triggers"],["F-2"])
        self.assertNotIn("E-ADDRESS",a["evidence"]["required_ids"])
        self.assertTrue(r["warnings"])

    def test_one_failure_with_unknown_address_is_review_not_false_or_ready(self):
        x=packet(); x["input"]["tracking_events"] += [event("F","2026-10-01T08:00:00Z","ATTEMPT_FAILED","A"),
            event("A","2026-10-01T11:00:00Z","ADDRESS_EXCEPTION"), event("C","2026-10-01T11:00:00Z","ADDRESS_CLEARED")]
        result=self.run_packet(x)["results"][0]; a=result["assessments"][2]
        self.assertEqual((a["result"],a["action_state"]),("TRUE","NEEDS_REVIEW"))
        self.assertIsNone(a["escalation_eligible"])
        self.assertEqual(a["rule_ids"],["F-1","F-UNKNOWN"])
        self.assertEqual(a["supported_triggers"],[])
        self.assertEqual(result["aggregate_action_state"],"NEEDS_REVIEW")
        self.assertTrue(all(row["action_state"] != "READY_TO_ESCALATE" for row in result["assessments"]))
        self.assertEqual(a["evidence"]["required_ids"],["E-ADDRESS"])
        self.assertEqual(a["evidence"]["conflicting_ids"],["E-ADDRESS"])
        failed,address=a["subtype_assessments"]
        self.assertEqual((failed["result"],failed["escalation_eligible"],failed["evidence"]["completeness"]),("TRUE",False,"COMPLETE"))
        self.assertEqual(address["evidence"]["conflicting_ids"],["E-ADDRESS"])
        self.assertEqual({(s["policy_id"],s["section_id"]) for s in a["expected_sections"]},
                         {("SOP-04","single-attempt"),("SOP-05","attempt-address-evidence"),("SOP-07","missing-facts")})
        validate_assessment_semantics(a,Policy.load().registry)

    def test_missing_packet_source_is_local_raw_gap(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        x["input"]["shipments"][0].update(source_system=None,promised_delivery_at="2026-09-30T12:00:00Z")
        r=self.run_packet(x)["results"][0]
        self.assertFalse(r["shipment_blockers"])
        self.assertEqual((r["assessments"][0]["result"],r["assessments"][0]["escalation_eligible"]),("TRUE",True))
        self.assertEqual((r["aggregate_action_state"],r["priority"]),("NEEDS_REVIEW","HIGH"))

    def test_canonical_raw_shape_boundary_and_no_mutation(self):
        x=packet(); x["input"]["tracking_events"].append(event("BAD","2026-10-01T11:00:00Z","ATTEMPT_FAILED"))
        seal(x); before=copy.deepcopy(x)
        with self.assertRaises(CanonicalInputError):
            triage_snapshot(**x)
        self.assertEqual(x,before)
        x["input_profile"]="RAW_VALIDATION_CASE"; before=copy.deepcopy(x)
        output=triage_snapshot(**x)
        self.assertEqual(x,before)
        self.assertIn("input.tracking_events[1].attempt_id",[f["path"] for f in output["validation_findings"]])

    def test_invalid_time_quarantines_only_dependent_event(self):
        x=packet(); x["input_profile"]="RAW_VALIDATION_CASE"
        x["input"]["shipments"][0]["promised_delivery_at"]="2026-09-30T12:00:00Z"
        x["input"]["tracking_events"].append(event("FUTURE","2026-10-02T12:00:00Z","ATTEMPT_FAILED","A"))
        r=self.run_packet(x)["results"][0]
        self.assertEqual(r["derived_facts"]["last_scan_time"],"2026-10-01T10:00:00Z")
        self.assertIsNone(r["derived_facts"]["failed_attempt_count"])
        self.assertEqual(r["assessments"][0]["action_state"],"READY_TO_ESCALATE")
        self.assertEqual(r["assessments"][1]["action_state"],"NEEDS_REVIEW")

    def test_bad_context_global_and_no_other_snapshot_join(self):
        for change in ("checksum","foreign_key","policy"):
            x=packet(); seal(x)
            if change=="checksum": x["manifest"]["checksum"]="0"*64
            elif change=="foreign_key":
                x["input_profile"]="RAW_VALIDATION_CASE"; x["input"]["tracking_events"][0]["snapshot_id"]="WRONG"; seal(x)
            else: x["policy"]["bundle_version"]="unknown"
            r=triage_snapshot(**x)["results"][0]
            with self.subTest(change=change):
                self.assertTrue(r["shipment_blockers"])
                self.assertEqual(r["aggregate_action_state"],"NEEDS_REVIEW")
                self.assertEqual(r["priority"],"MEDIUM")

    def test_missing_section_blocks_only_supported_category(self):
        p=Policy.load(); p.available_sections.remove(("SOP-02","1.0-demo","late-escalate"))
        x=packet(); x["input"]["shipments"][0]["promised_delivery_at"]="2026-09-30T12:00:00Z"
        x["input"]["tracking_events"][0]["event_time"]="2026-09-29T12:00:00Z"
        r=self.run_packet(x,p)["results"][0]
        self.assertEqual(r["assessments"][0]["action_state"],"NEEDS_REVIEW")
        self.assertEqual(r["assessments"][0]["evidence"]["missing_ids"],["E-POLICY-SECTIONS"])
        self.assertEqual(r["assessments"][1]["action_state"],"READY_TO_ESCALATE")
        self.assertEqual(r["aggregate_action_state"],"READY_TO_ESCALATE")

    def test_aggregate_precedence_and_priority(self):
        def a(state,eligible=False): return dict(action_state=state,escalation_eligible=eligible)
        cases=[([a("READY_TO_ESCALATE",True),a("NEEDS_REVIEW")],[],("READY_TO_ESCALATE","HIGH")),
               ([a("MONITOR"),a("NEEDS_REVIEW")],[],("NEEDS_REVIEW","MEDIUM")),
               ([a("NEEDS_REVIEW",True)],[],("NEEDS_REVIEW","HIGH")),
               ([a("READY_TO_ESCALATE",True)],[{"scope":"SHIPMENT"}],("NEEDS_REVIEW","MEDIUM")),
               ([a("MONITOR"),a("NORMAL")],[],("MONITOR","LOW"))]
        for assessments,blocks,expected in cases:
            self.assertEqual(aggregate(assessments,blocks),expected)

    def test_one_missing_subtype_section_does_not_cancel_other_ready_basis(self):
        p=Policy.load(); p.available_sections.remove(("SOP-04","1.0-demo","repeated-attempts"))
        x=packet(); x["input"]["tracking_events"] += [event("F1","2026-10-01T08:00:00Z","ATTEMPT_FAILED","A"),
            event("F2","2026-10-01T09:00:00Z","ATTEMPT_FAILED","B"),event("ADDR","2026-10-01T11:00:00Z","ADDRESS_EXCEPTION")]
        r=self.run_packet(x,p)["results"][0]; a=r["assessments"][2]
        self.assertEqual(a["action_state"],"READY_TO_ESCALATE")
        self.assertEqual(a["supported_triggers"],["F-3"])
        self.assertNotIn("E-FAILED",a["evidence"]["required_ids"])
        self.assertEqual(a["subtype_assessments"][0]["evidence"]["missing_ids"],["E-POLICY-SECTIONS"])
        self.assertTrue(r["warnings"])

    def test_invalid_closure_timestamp_cannot_authorize_closed_normal(self):
        x=packet(); x["input"]["shipments"][0].update(current_status="DELIVERED",delivered_at="2026-10-02T12:00:00Z")
        r=self.run_packet(x)["results"][0]
        self.assertIsNone(r["derived_facts"]["is_open"])
        self.assertEqual(r["aggregate_action_state"],"NEEDS_REVIEW")

    def test_independent_shipments_do_not_share_attempts_or_global_blockers(self):
        x=packet()
        s=copy.deepcopy(x["input"]["shipments"][0]); s.update(shipment_id="S2",promised_delivery_at="2026-09-30T12:00:00Z")
        x["input"]["shipments"].append(s)
        x["input"]["history_declarations"].append(dict(snapshot_id="UNIT",shipment_id="S2",history_complete=True))
        x["input"]["shipments"][0].update(current_status="UNKNOWN")
        x["input_profile"]="RAW_VALIDATION_CASE"
        e=event("SECOND","2026-10-01T10:00:00Z");e["shipment_id"]="S2";x["input"]["tracking_events"].append(e)
        r=self.run_packet(x)["results"]
        self.assertEqual([v["aggregate_action_state"] for v in r],["NEEDS_REVIEW","READY_TO_ESCALATE"])
        self.assertFalse(r[1]["shipment_blockers"])
        self.assertEqual(len(r),2)

    def test_input_order_and_repeated_runs_are_deterministic(self):
        x=packet(); x["input"]["tracking_events"] += [event("F1","2026-10-01T08:00:00Z","ATTEMPT_FAILED","A"),event("F2","2026-10-01T09:00:00Z","ATTEMPT_FAILED","B")]
        first=self.run_packet(x)
        self.assertEqual(first,self.run_packet(x))
        x["input"]["tracking_events"].reverse()
        second=self.run_packet(x)
        for r in (first["results"][0],second["results"][0]):
            r["derived_facts"]["fact_refs"].sort(key=lambda ref:json.dumps(ref,sort_keys=True))
        self.assertEqual(first,second)

    def test_engine_input_and_runtime_reads_are_gold_isolated(self):
        x=seal(packet())
        with self.assertRaises(TypeError):
            triage_snapshot(**x, expected_results=[])
        original=Path.read_text
        reads=[]
        def tracked(path,*args,**kwargs):
            self.assertNotIn("evaluation",path.parts)
            self.assertNotIn("examples",path.parts)
            reads.append(path)
            return original(path,*args,**kwargs)
        with patch.object(Path,"read_text",tracked):
            triage_snapshot(**x)
        self.assertTrue(reads)
        for p in (DOMAIN/"engine").glob("*.py"):
            tree=ast.parse(p.read_text(encoding="utf-8"))
            imports=[node.module or "" for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
            self.assertFalse(any("evaluation" in name for name in imports))
            self.assertNotIn("expected_results",p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
