"""Post-heldout root-cause tests built from synthetic inputs, with no Gold reads."""
import copy
import unittest

from test_engine import event, packet, seal
from engine import triage_snapshot
from engine.policy import Policy
from engine.validation import validate_input
from validate_contracts import validate_assessment_semantics, validate_shape


class EngineDiagnosticTests(unittest.TestCase):
    def run_packet(self, value):
        output = triage_snapshot(**seal(value))
        for result in output["results"]:
            validate_shape(dict(result, rationale="Synthetic output shape check"), "expected_result")
            for assessment in result["assessments"]:
                validate_assessment_semantics(assessment, Policy.load().registry)
                gate = assessment["evidence"]
                self.assertLessEqual(set(gate["missing_ids"] + gate["conflicting_ids"]), set(gate["required_ids"]))
        return output

    def test_invalid_observed_scans_are_conflicting_and_quarantined(self):
        for time in ("malformed", "2026-10-02T12:00:00Z", "2026-09-26T23:59:59Z"):
            with self.subTest(time=time):
                x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
                x["input"]["shipments"][0]["promised_delivery_at"] = "2026-09-30T12:00:00Z"
                x["input"]["tracking_events"].append(event("INVALID", time))
                before = copy.deepcopy(seal(x))
                actual = self.run_packet(x); result = actual["results"][0]; stale = result["assessments"][1]
                self.assertEqual(x, before)
                self.assertEqual((stale["rule_ids"], stale["result"], stale["escalation_eligible"], stale["action_state"]),
                                 (["S-UNKNOWN"], "UNKNOWN", None, "NEEDS_REVIEW"))
                self.assertEqual(stale["evidence"]["missing_ids"], [])
                self.assertEqual(stale["evidence"]["conflicting_ids"], ["E-STALE"])
                self.assertEqual(stale["blockers"][0]["code"], "INVALID_EVENT")
                self.assertEqual(stale["blockers"][0]["dependent_decision"], "STALE_TRACKING")
                self.assertEqual(stale["blockers"][0]["field_refs"], ["input.tracking_events[1]"])
                self.assertEqual(result["derived_facts"]["last_scan_time"], "2026-10-01T10:00:00Z")
                self.assertEqual(result["derived_facts"]["hours_since_last_scan"], 2)
                self.assertEqual(result["derived_facts"]["failed_attempt_count"], 0)
                self.assertFalse(result["derived_facts"]["address_exception_active"])
                self.assertEqual([a["action_state"] for a in result["assessments"]], ["READY_TO_ESCALATE", "NEEDS_REVIEW", "NORMAL"])
                self.assertEqual((result["aggregate_action_state"], result["priority"]), ("READY_TO_ESCALATE", "HIGH"))
                self.assertFalse(result["shipment_blockers"])
                self.assertEqual([(w["code"], w["exception_type"]) for w in result["warnings"]], [("UNRESOLVED_CATEGORY", "STALE_TRACKING")])

    def test_absent_and_incomplete_history_are_missing_evidence(self):
        for absent in (True, False):
            with self.subTest(absent=absent):
                x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
                if absent:
                    x["input"]["history_declarations"] = []
                else:
                    x["input"]["history_declarations"][0]["history_complete"] = False
                result = self.run_packet(x)["results"][0]
                for a, missing in zip(result["assessments"][1:], (["E-STALE"], ["E-ADDRESS", "E-FAILED"])):
                    self.assertEqual(a["evidence"]["missing_ids"], missing)
                    self.assertEqual(a["evidence"]["conflicting_ids"], [])
                    self.assertEqual((a["result"], a["action_state"]), ("UNKNOWN", "NEEDS_REVIEW"))
                self.assertEqual([(b["dependent_decision"], b["requirement_ids"], b["scope"]) for b in result["assessments"][2]["blockers"]],
                                 [("FAILED_ATTEMPT", ["E-FAILED"], "CATEGORY"), ("ADDRESS_EXCEPTION", ["E-ADDRESS"], "CATEGORY")])

    def test_invalid_failed_event_preserves_independently_ready_address(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["tracking_events"] += [event("INVALID", "2026-10-02T12:00:00Z", "ATTEMPT_FAILED", "A"),
                                           event("ADDRESS", "2026-10-01T11:00:00Z", "ADDRESS_EXCEPTION")]
        result = self.run_packet(x)["results"][0]; a = result["assessments"][2]
        self.assertIsNone(result["derived_facts"]["failed_attempt_count"])
        self.assertEqual(result["derived_facts"]["last_scan_time"], "2026-10-01T10:00:00Z")
        self.assertEqual(result["assessments"][1]["evidence"]["conflicting_ids"], ["E-STALE"])
        self.assertEqual((a["action_state"], a["supported_triggers"]), ("READY_TO_ESCALATE", ["F-3"]))
        self.assertNotIn("E-FAILED", a["evidence"]["required_ids"])
        failed = next(s for s in a["subtype_assessments"] if s["subtype"] == "FAILED_ATTEMPT")
        self.assertEqual((failed["evidence"]["missing_ids"], failed["evidence"]["conflicting_ids"]), ([], ["E-FAILED"]))
        self.assertEqual((a["blockers"][0]["code"], a["blockers"][0]["dependent_decision"]), ("INVALID_EVENT", "FAILED_ATTEMPT"))

    def test_invalid_address_event_preserves_independently_ready_attempts(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["tracking_events"] += [event("F1", "2026-10-01T08:00:00Z", "ATTEMPT_FAILED", "A"),
            event("F2", "2026-10-01T09:00:00Z", "ATTEMPT_FAILED", "B"), event("INVALID", "malformed", "ADDRESS_EXCEPTION")]
        result = self.run_packet(x)["results"][0]; a = result["assessments"][2]
        self.assertIsNone(result["derived_facts"]["address_exception_active"])
        self.assertEqual(result["derived_facts"]["failed_attempt_count"], 2)
        self.assertEqual(result["assessments"][1]["action_state"], "NORMAL")
        self.assertEqual((a["action_state"], a["supported_triggers"]), ("READY_TO_ESCALATE", ["F-2"]))
        self.assertNotIn("E-ADDRESS", a["evidence"]["required_ids"])
        address = next(s for s in a["subtype_assessments"] if s["subtype"] == "ADDRESS_EXCEPTION")
        self.assertEqual((address["evidence"]["missing_ids"], address["evidence"]["conflicting_ids"]), ([], ["E-ADDRESS"]))
        self.assertEqual((a["blockers"][0]["code"], a["blockers"][0]["dependent_decision"]), ("INVALID_EVENT", "ADDRESS_EXCEPTION"))

    def test_packet_gaps_merge_with_unknown_history_dependencies(self):
        for fields in (("source_system",), ("carrier",), ("source_system", "carrier")):
            with self.subTest(fields=fields):
                x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
                x["input"]["history_declarations"] = []
                x["input"]["shipments"][0]["promised_delivery_at"] = "2026-09-30T12:00:00Z"
                for field in fields:
                    del x["input"]["shipments"][0][field]
                result = self.run_packet(x)["results"][0]
                self.assertFalse(result["shipment_blockers"])
                self.assertEqual((result["aggregate_action_state"], result["priority"]), ("NEEDS_REVIEW", "HIGH"))
                self.assertEqual((result["assessments"][0]["result"], result["assessments"][0]["escalation_eligible"]), ("TRUE", True))
                for a, missing, decision in zip(result["assessments"],
                        (["E-IDENTITY"], ["E-IDENTITY", "E-STALE"], ["E-ADDRESS", "E-FAILED", "E-IDENTITY"]),
                        ("LATE_DELIVERY_PACKET", "PACKET", "PACKET")):
                    self.assertEqual(a["action_state"], "NEEDS_REVIEW")
                    self.assertEqual(a["evidence"]["missing_ids"], missing)
                    self.assertEqual(a["evidence"]["conflicting_ids"], [])
                    blocks = [b for b in a["blockers"] if b["requirement_ids"] == ["E-IDENTITY"]]
                    self.assertEqual(len(blocks), len(fields))
                    self.assertTrue(all(b["dependent_decision"] == decision and b["scope"] == "CATEGORY" for b in blocks))
                self.assertEqual({w["exception_type"] for w in result["warnings"]}, {"STALE_TRACKING", "FAILED_ATTEMPT_ADDRESS"})

    def test_packet_gaps_block_known_ready_triggers_locally(self):
        for field in ("carrier", "source_system"):
            for trigger, index in (("L-2", 0), ("S-2", 1), ("F-2", 2), ("F-3", 2)):
                with self.subTest(field=field, trigger=trigger):
                    x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
                    if trigger == "L-2":
                        x["input"]["shipments"][0]["promised_delivery_at"] = "2026-09-30T12:00:00Z"
                    elif trigger == "S-2":
                        x["input"]["tracking_events"][0]["event_time"] = "2026-09-29T12:00:00Z"
                    elif trigger == "F-2":
                        x["input"]["tracking_events"] += [event("F1", "2026-10-01T08:00:00Z", "ATTEMPT_FAILED", "A"),
                                                         event("F2", "2026-10-01T09:00:00Z", "ATTEMPT_FAILED", "B")]
                    else:
                        x["input"]["tracking_events"].append(event("ADDRESS", "2026-10-01T11:00:00Z", "ADDRESS_EXCEPTION"))
                    healthy = self.run_packet(x)["results"][0]
                    self.assertEqual(healthy["assessments"][index]["action_state"], "READY_TO_ESCALATE")
                    x["input"]["shipments"][0][field] = None
                    result = self.run_packet(x)["results"][0]; a = result["assessments"][index]
                    self.assertEqual((a["result"], a["escalation_eligible"], a["action_state"]), ("TRUE", True, "NEEDS_REVIEW"))
                    self.assertEqual(a["rule_ids"], [trigger]); self.assertEqual(a["supported_triggers"], [trigger])
                    self.assertEqual(a["evidence"]["missing_ids"], ["E-IDENTITY"])
                    self.assertEqual(a["blockers"][0]["dependent_decision"], "LATE_DELIVERY_PACKET" if index == 0 else "PACKET")
                    self.assertEqual(result["derived_facts"], healthy["derived_facts"])
                    self.assertEqual((result["aggregate_action_state"], result["priority"]), ("NEEDS_REVIEW", "HIGH"))
                    self.assertFalse(result["shipment_blockers"])
                    for i, inactive in enumerate(result["assessments"]):
                        if i != index:
                            self.assertEqual(inactive, healthy["assessments"][i])

    def test_packet_gap_and_address_conflict_keep_subtype_evidence_independent(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["shipments"][0]["source_system"] = None
        x["input"]["tracking_events"] += [event("F", "2026-10-01T08:00:00Z", "ATTEMPT_FAILED", "A"),
            event("A", "2026-10-01T11:00:00Z", "ADDRESS_EXCEPTION"), event("C", "2026-10-01T11:00:00Z", "ADDRESS_CLEARED")]
        result = self.run_packet(x)["results"][0]; a = result["assessments"][2]
        self.assertEqual((a["result"], a["escalation_eligible"], a["action_state"]), ("TRUE", None, "NEEDS_REVIEW"))
        self.assertEqual(a["rule_ids"], ["F-1", "F-UNKNOWN"]); self.assertEqual(a["supported_triggers"], [])
        self.assertEqual(a["evidence"]["required_ids"], ["E-ADDRESS", "E-IDENTITY"])
        self.assertEqual(a["evidence"]["missing_ids"], ["E-IDENTITY"])
        self.assertEqual(a["evidence"]["conflicting_ids"], ["E-ADDRESS"])
        self.assertEqual([(b["dependent_decision"], b["requirement_ids"]) for b in a["blockers"]],
                         [("ADDRESS_EXCEPTION", ["E-ADDRESS"]), ("PACKET", ["E-IDENTITY"])])
        self.assertEqual(a["subtype_assessments"][0]["evidence"]["completeness"], "COMPLETE")
        self.assertEqual(a["subtype_assessments"][1]["evidence"]["required_ids"], ["E-ADDRESS"])

    def test_unknown_promise_and_missing_scan_merge_packet_gaps(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["shipments"][0].update(promised_delivery_at=None, carrier=None)
        x["input"]["tracking_events"] = []
        late, stale, failed = self.run_packet(x)["results"][0]["assessments"]
        self.assertEqual(late["evidence"]["missing_ids"], ["E-IDENTITY", "E-LATE"])
        self.assertEqual([b["dependent_decision"] for b in late["blockers"]], ["LATE_DELIVERY", "LATE_DELIVERY_PACKET"])
        self.assertEqual(stale["evidence"]["missing_ids"], ["E-IDENTITY", "E-STALE"])
        self.assertEqual([b["dependent_decision"] for b in stale["blockers"]], ["STALE_TRACKING", "PACKET"])
        self.assertEqual(failed["evidence"]["completeness"], "NOT_APPLICABLE")
        self.assertEqual(failed["blockers"], [])

    def test_missing_attempt_identity_remains_missing_and_subtype_local(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["tracking_events"].append(event("NO_ID", "2026-10-01T11:00:00Z", "ATTEMPT_FAILED"))
        result = self.run_packet(x)["results"][0]; a = result["assessments"][2]
        self.assertEqual(a["evidence"]["missing_ids"], ["E-FAILED"])
        self.assertEqual(a["evidence"]["conflicting_ids"], [])
        self.assertEqual((a["blockers"][0]["dependent_decision"], a["blockers"][0]["requirement_ids"]), ("FAILED_ATTEMPT", ["E-FAILED"]))
        self.assertEqual(result["assessments"][1]["action_state"], "NORMAL")
        self.assertEqual(result["derived_facts"]["hours_since_last_scan"], 1)

    def test_informational_diagnostics_preserve_existing_unresolved_warnings(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["history_declarations"] = []
        x["input"]["tracking_events"].append(event("SECOND", "2026-10-01T11:00:00Z"))
        baseline = self.run_packet(x)["results"][0]
        x["input"]["tracking_events"] += [copy.deepcopy(x["input"]["tracking_events"][0]),
                                           dict(x["input"]["tracking_events"][1], facility_id="OTHER")]
        result = self.run_packet(x)["results"][0]
        informational = [w for w in result["warnings"] if w["scope"] == "SHIPMENT"]
        self.assertEqual([w["code"] for w in informational], ["DUPLICATE_EVENT_IDENTITY", "CONFLICTING_EVENT_IDENTITY"])
        self.assertTrue(all(w["exception_type"] is None and w["related_blocker_codes"] == [] for w in informational))
        result["warnings"] = [w for w in result["warnings"] if w["scope"] != "SHIPMENT"]
        self.assertEqual(result, baseline)

    def test_facility_conflict_keeps_agreed_fields_and_no_authoritative_facility(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["shipments"][0]["promised_delivery_at"] = "2026-09-30T12:00:00Z"
        baseline = self.run_packet(x)["results"][0]
        x["input"]["tracking_events"] += [dict(x["input"]["tracking_events"][0], facility_id=f) for f in ("OTHER", "OTHER")]
        before = copy.deepcopy(seal(x))
        contexts, findings = validate_input(x["manifest"], x["policy"], x["input"], x["input_profile"], Policy.load())
        self.assertEqual(len(contexts[0].events), 1)
        agreed = contexts[0].events[0][1]
        self.assertNotIn("facility_id", agreed)
        self.assertEqual((agreed["event_time"], agreed["event_code"]), ("2026-10-01T10:00:00Z", "IN_TRANSIT"))
        self.assertEqual(len(findings), 3)
        self.assertTrue(all(f["requirement_ids"] == [] for f in findings))
        result = self.run_packet(x)["results"][0]
        self.assertEqual(x, before)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(result["warnings"][0]["code"], "CONFLICTING_EVENT_IDENTITY")
        result["warnings"] = []
        self.assertEqual(result, baseline)

    def test_informational_warning_does_not_override_global_blockers(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["shipments"][0]["current_status"] = "UNKNOWN"
        baseline = self.run_packet(x)["results"][0]
        x["input"]["tracking_events"].append(copy.deepcopy(x["input"]["tracking_events"][0]))
        result = self.run_packet(x)["results"][0]
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(result["warnings"][0]["scope"], "SHIPMENT")
        self.assertEqual((result["aggregate_action_state"], result["priority"]), ("NEEDS_REVIEW", "MEDIUM"))
        result["warnings"] = []
        self.assertEqual(result, baseline)

    def test_identical_invalid_duplicate_preserves_original_conflict(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        invalid = event("INVALID", "2026-10-02T12:00:00Z")
        x["input"]["tracking_events"] += [invalid, copy.deepcopy(invalid)]
        actual = self.run_packet(x); result = actual["results"][0]
        self.assertEqual([f["code"] for f in actual["validation_findings"]], ["DUPLICATE_EVENT_IDENTITY", "INVALID_EVENT"])
        self.assertEqual(result["assessments"][1]["evidence"]["conflicting_ids"], ["E-STALE"])
        self.assertEqual([b["code"] for b in result["assessments"][1]["blockers"]], ["INVALID_EVENT"])
        self.assertEqual([w["code"] for w in result["warnings"]], ["DUPLICATE_EVENT_IDENTITY", "UNRESOLVED_CATEGORY"])

    def test_distinct_duplicate_identities_each_emit_one_warning(self):
        x = packet(); x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["tracking_events"] += [event("F1", "2026-10-01T08:00:00Z", "ATTEMPT_FAILED", "A"),
                                         event("F2", "2026-10-01T09:00:00Z", "ATTEMPT_FAILED", "B")]
        baseline = self.run_packet(x)["results"][0]
        x["input"]["tracking_events"] += [copy.deepcopy(e) for e in x["input"]["tracking_events"][1:] for _ in range(2)]
        result = self.run_packet(x)["results"][0]
        self.assertEqual([w["code"] for w in result["warnings"]], ["DUPLICATE_EVENT_IDENTITY"] * 2)
        self.assertEqual(len({w["message"] for w in result["warnings"]}), 2)
        result["warnings"] = []
        self.assertEqual(result, baseline)


if __name__ == "__main__":
    unittest.main()
