"""Offline artifact tests; intentionally never import the application or a rule engine."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("domain_contract_validation", ROOT / "validate_contracts.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class ContractTests(unittest.TestCase):
    def example(self):
        return v.read_json(ROOT / "examples/normal.example.json")

    def rehash(self, example):
        example["manifest"]["checksum"] = hashlib.sha256(v.canonical_bytes(example["input"])).hexdigest()
        return example

    def test_registry_and_sop_integrity(self):
        registry, sections = v.validate_bundle(ROOT)
        self.assertEqual(len(registry["rules"]), 17)
        self.assertEqual(len(registry["evidence_requirements"]), 8)
        self.assertEqual(len(sections), 25)

    def test_approved_thresholds_and_boundaries(self):
        reg = v.read_json(ROOT / "policy/policy_registry.json")
        expected = {"LATE_ESCALATE_HOURS": (24, ">="), "STALE_DETECT_HOURS": (24, ">"),
                    "STALE_ESCALATE_HOURS": (48, ">="), "FAILED_ATTEMPTS_ESCALATE": (2, ">="),
                    "ADDRESS_ACTIVE_ESCALATES": (True, "enabled")}
        self.assertEqual({k:(x["value"],x["operator"]) for k,x in reg["thresholds"].items()}, expected)
        self.assertIn("as_of > promised_delivery_at", reg["late_detection_contract"])

    def test_rule_and_requirement_inventory(self):
        reg = v.read_json(ROOT / "policy/policy_registry.json")
        self.assertEqual({x["rule_id"] for x in reg["rules"]}, set("D-CONTEXT D-STATUS D-CLOSED L-UNKNOWN L-0 L-1 L-2 S-UNKNOWN S-PRE S-0 S-1 S-2 F-UNKNOWN F-0 F-1 F-2 F-3".split()))
        self.assertEqual({x["requirement_id"] for x in reg["evidence_requirements"]}, set("E-IDENTITY E-STATUS E-POLICY-CONTEXT E-LATE E-STALE E-FAILED E-ADDRESS E-POLICY-SECTIONS".split()))

    def test_late_dependencies_do_not_include_history(self):
        reg = v.read_json(ROOT / "policy/policy_registry.json")
        late = next(x for x in reg["evidence_requirements"] if x["requirement_id"] == "E-LATE")
        self.assertNotIn("history_complete", late["depends_on"])
        for rule in reg["rules"]:
            if rule["rule_id"].startswith("L-"):
                self.assertFalse(set(rule["decision_dependency_ids"]) & {"E-STALE", "E-FAILED", "E-ADDRESS"})

    def test_scan_codes(self):
        reg = v.read_json(ROOT / "policy/policy_registry.json")
        self.assertEqual(set(reg["qualifying_physical_scans"]), {"ACCEPTED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "ATTEMPT_FAILED", "DELIVERED"})

    def test_unknown_enums_rejected(self):
        for name in ("exception_type", "subtype", "assessment_result", "action_state", "priority", "completeness", "shipment_status", "event_code"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                v.validate_shape("UNRECOGNIZED", name)

    def test_composite_keys_are_represented(self):
        defs = v.schema_document()["$defs"]
        self.assertEqual(defs["shipment"]["x-primary-key"], ["snapshot_id", "shipment_id"])
        self.assertEqual(defs["tracking_event"]["x-primary-key"], ["snapshot_id", "source_system", "event_id"])
        for name in ("tracking_event", "history_declaration"):
            self.assertEqual(defs[name]["x-foreign-key"]["fields"], ["snapshot_id", "shipment_id"])

    def test_two_unscored_examples_validate(self):
        examples = list((ROOT / "examples").glob("*.example.json"))
        self.assertEqual(len(examples), 2)
        for path in examples:
            value = v.read_json(path)
            self.assertTrue(value["example_only"])
            self.assertEqual(value["split"], "EXAMPLE")
            v.validate_fixture(value)

    def test_duplicate_composite_key_rejected(self):
        x = self.example()
        x["input"]["shipments"].append(copy.deepcopy(x["input"]["shipments"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate composite shipment"):
            v.validate_fixture(self.rehash(x))

    def test_cross_snapshot_foreign_key_rejected(self):
        x = self.example()
        x["input"]["tracking_events"][0]["snapshot_id"] = "ANOTHER-SNAPSHOT"
        with self.assertRaisesRegex(ValueError, "foreign key"):
            v.validate_fixture(self.rehash(x))

    def test_duplicate_event_identity_rejected(self):
        x = self.example()
        x["input"]["tracking_events"].append(copy.deepcopy(x["input"]["tracking_events"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate event"):
            v.validate_fixture(self.rehash(x))

    def test_missing_attempt_identity_rejected_in_canonical_input(self):
        event = self.example()["input"]["tracking_events"][0]
        event["event_code"] = "ATTEMPT_FAILED"
        with self.assertRaisesRegex(ValueError, "attempt_id"):
            v.validate_shape(event, "tracking_event")

    def test_raw_profile_preserves_invalid_event(self):
        x = self.example()
        x["input_profile"] = "RAW_VALIDATION_CASE"
        x["input"]["tracking_events"][0]["event_code"] = "UNKNOWN_CARRIER_CODE"
        x["expected_input_findings"] = [{"path":"input.tracking_events[0].event_code","reason":"Unknown event code"}]
        # Gold semantics deliberately not recalculated: this tests profile shape only.
        v.validate_fixture(self.rehash(x))
        x["expected_input_findings"] = []
        with self.assertRaisesRegex(ValueError, "declare expected"):
            v.validate_fixture(x)

    def test_deferred_fields_rejected(self):
        for field in ("ingested_at", "source_cutoff", "coverage_start_at", "coverage_end_at"):
            row = copy.deepcopy(self.example()["input"]["tracking_events"][0])
            row[field] = "2026-09-27T12:00:00Z"
            with self.subTest(field=field), self.assertRaises(ValueError):
                v.validate_shape(row, "tracking_event")

    def test_all_three_gold_categories_required(self):
        x = self.example()
        x["expected_results"][0]["assessments"][1] = copy.deepcopy(x["expected_results"][0]["assessments"][0])
        with self.assertRaisesRegex(ValueError, "each category"):
            v.validate_fixture(x)

    def test_scope_types_do_not_accept_category_blocker_as_global(self):
        x = v.read_json(ROOT / "examples/late_with_gaps.example.json")
        blocker = x["expected_results"][0]["assessments"][1]["blockers"][0]
        with self.assertRaises(ValueError):
            v.validate_shape(blocker, "shipment_blocker")

    def test_input_checksum_detects_drift(self):
        x = self.example()
        x["input"]["shipments"][0]["carrier"] = "CHANGED"
        with self.assertRaisesRegex(ValueError, "checksum"):
            v.validate_fixture(x)

    def question(self):
        return {"question_id":"CONTRACT-TEST", "contract_version":"1.0", "example_only":True, "split":"EXAMPLE",
                "question":"Which boundary applies to a handoff?", "kind":"ANSWERABLE", "negative_reason":None,
                "gold_policy_version":"1.0-demo", "gold_sections":[{"policy_id":"SOP-06","version":"1.0-demo","section_id":"handoff-boundary"}],
                "required_sections":[], "category":"handoff", "difficulty":"EASY", "question_family":"test-only", "reviewer_rationale":"Contract test only, not a scored question."}

    def test_answerable_question_requires_real_section(self):
        x = self.question()
        v.validate_question(x)
        x["gold_sections"][0]["section_id"] = "not-a-section"
        with self.assertRaisesRegex(ValueError, "Unknown gold"):
            v.validate_question(x)

    def test_negative_question_has_no_fabricated_gold(self):
        x = self.question()
        x.update(kind="NEGATIVE", negative_reason="OUT_OF_SCOPE", gold_sections=[])
        v.validate_question(x)
        x["gold_sections"] = self.question()["gold_sections"]
        with self.assertRaisesRegex(ValueError, "fabricate gold"):
            v.validate_question(x)

    def test_naive_and_impossible_timestamps_rejected(self):
        for stamp in ("2026-09-27T12:00:00", "2026-02-30T12:00:00Z"):
            manifest = self.example()["manifest"]
            manifest["as_of"] = stamp
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                v.validate_shape(manifest, "manifest")

    def test_metadata_mutations_rejected_structurally(self):
        for mutation in ("version", "unknown_rule", "missing_section", "demo_label", "duplicate_section"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "domain"
                shutil.copytree(ROOT, root)
                path = root / "sops/last_mile/late_delivery.md"
                text = path.read_text(encoding="utf-8")
                if mutation == "version":
                    text = text.replace('"version": "1.0-demo"', '"version": "wrong"')
                elif mutation == "unknown_rule":
                    text = text.replace('"L-0"', '"UNKNOWN-RULE"')
                elif mutation == "missing_section":
                    text = text.replace('## late-boundaries', '## missing-section')
                elif mutation == "demo_label":
                    text = text.replace('"demo_policy": true', '"demo_policy": false')
                else:
                    text = text.replace('late-monitor', 'late-boundaries')
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    v.validate_bundle(root, check_hashes=False)

    def test_unknown_schema_keyword_fails_closed(self):
        doc = copy.deepcopy(v.schema_document())
        doc["$defs"]["priority"]["unsupportedConstraint"] = True
        with self.assertRaisesRegex(ValueError, "Unsupported schema"):
            v.validate_shape("HIGH", "priority", doc)

    def test_policy_support_and_failure_guidance_are_separate(self):
        reg = v.read_json(ROOT / "policy/policy_registry.json")
        requirements = {x["requirement_id"]: x for x in reg["evidence_requirements"]}
        for identity in ("E-POLICY-CONTEXT", "E-POLICY-SECTIONS"):
            item = requirements[identity]
            self.assertTrue(item["support_sections"])
            self.assertFalse(any(x["policy_id"] == "SOP-07" for x in item["support_sections"]))
            self.assertEqual([x["section_id"] for x in item["failure_guidance_sections"]], ["missing-policy"])
        for item in reg["rules"] + reg["evidence_requirements"]:
            self.assertNotIn("required_sop_sections", item)

    def test_f_unknown_dependencies_are_machine_readable(self):
        reg = v.read_json(ROOT / "policy/policy_registry.json")
        rule = next(x for x in reg["rules"] if x["rule_id"] == "F-UNKNOWN")
        self.assertFalse({"E-FAILED", "E-ADDRESS"} & set(rule["decision_dependency_ids"]))
        self.assertEqual(rule["subtype_dependency_ids"], {"FAILED_ATTEMPT": ["E-FAILED"], "ADDRESS_EXCEPTION": ["E-ADDRESS"]})
        self.assertEqual(rule["subtype_readiness_contract"]["combination"], "ANY_FULLY_SUPPORTED_ELIGIBLE_SUBTYPE")
        self.assertIs(rule["subtype_readiness_contract"]["unresolved_other_subtype_blocks_readiness"], False)

    def test_unconditional_subtype_union_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "domain"
            shutil.copytree(ROOT, root)
            path = root / "policy/policy_registry.json"
            reg = v.read_json(path)
            rule = next(x for x in reg["rules"] if x["rule_id"] == "F-UNKNOWN")
            rule["decision_dependency_ids"].append("E-ADDRESS")
            path.write_text(json.dumps(reg), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not union"):
                v.validate_bundle(root, check_hashes=False)

    def test_normal_evidence_is_not_classification_dependency_inventory(self):
        registry = v.read_json(ROOT / "policy/policy_registry.json")
        assessment = self.example()["expected_results"][0]["assessments"][0]
        for result in ("FALSE", "NOT_APPLICABLE"):
            assessment["result"] = result
            v.validate_assessment_semantics(assessment, registry)
        assessment["evidence"]["required_ids"] = ["E-LATE"]
        with self.assertRaisesRegex(ValueError, "empty IDs"):
            v.validate_assessment_semantics(assessment, registry)

    def test_active_decisions_cannot_omit_the_evidence_gate(self):
        registry = v.read_json(ROOT / "policy/policy_registry.json")
        assessment = self.example()["expected_results"][0]["assessments"][0]
        for state in ("MONITOR", "READY_TO_ESCALATE", "NEEDS_REVIEW"):
            assessment["action_state"] = state
            with self.subTest(state=state), self.assertRaises(ValueError):
                v.validate_assessment_semantics(assessment, registry)

    def test_healthy_gold_rejects_failure_only_citation(self):
        registry = v.read_json(ROOT / "policy/policy_registry.json")
        ready = v.read_json(ROOT / "examples/late_with_gaps.example.json")["expected_results"][0]["assessments"][0]
        normal = self.example()["expected_results"][0]["assessments"][0]
        for assessment in (normal, ready):
            assessment["expected_sections"].append({"policy_id":"SOP-07", "version":"1.0-demo", "section_id":"missing-policy"})
            with self.subTest(state=assessment["action_state"]), self.assertRaisesRegex(ValueError, "failure-guidance"):
                v.validate_assessment_semantics(assessment, registry)

    def test_unresolved_gold_can_cite_applicable_failure_guidance(self):
        registry = v.read_json(ROOT / "policy/policy_registry.json")
        gap_case = v.read_json(ROOT / "examples/late_with_gaps.example.json")
        for assessment in gap_case["expected_results"][0]["assessments"][1:]:
            v.validate_assessment_semantics(assessment, registry)

    def test_example_business_outcomes_are_preserved(self):
        normal = self.example()["expected_results"][0]
        self.assertEqual(normal["aggregate_action_state"], "NORMAL")
        self.assertTrue(all(a["action_state"] == "NORMAL" for a in normal["assessments"]))
        late = v.read_json(ROOT / "examples/late_with_gaps.example.json")["expected_results"][0]
        self.assertEqual(late["aggregate_action_state"], "READY_TO_ESCALATE")
        self.assertEqual([a["action_state"] for a in late["assessments"]], ["READY_TO_ESCALATE", "NEEDS_REVIEW", "NEEDS_REVIEW"])
        self.assertEqual({w["exception_type"] for w in late["warnings"]}, {"STALE_TRACKING", "FAILED_ATTEMPT_ADDRESS"})

    def calibration(self, identity):
        return v.read_json(ROOT / "evaluation/development/calibration" / (identity + ".json"))

    def test_eighteen_development_fixtures_validate_with_review_provenance(self):
        paths = sorted((ROOT / "evaluation/development").rglob("*.json"))
        self.assertEqual([p.stem for p in paths], [f"C{i:02d}" for i in range(1, 13)] + [f"D{i}" for i in range(13, 19)])
        for path in paths:
            with self.subTest(case=path.stem):
                x = v.read_json(path)
                self.assertEqual(x["fixture_id"], path.stem)
                self.assertEqual(x["split"], "DEVELOPMENT")
                self.assertFalse(x["example_only"])
                self.assertEqual(x["gold_provenance"]["review_status"], "OWNER_REVIEWED")
                self.assertEqual(x["gold_provenance"]["reviewer"], "Zhe Wang")
                self.assertEqual(x["gold_provenance"]["method"], "INDEPENDENT_WRITTEN_POLICY")
                self.assertIn("artifact-author", x["gold_provenance"]["author"])
                self.assertEqual(len(x["input"]["shipments"]), 1)
                self.assertEqual(len(x["expected_results"]), 1)
                self.assertTrue(x["expected_results"][0]["rationale"])
                v.validate_fixture(x)

    def test_under_specified_ready_late_gold_rejected(self):
        x = self.calibration("C04")
        x["expected_results"][0]["assessments"][0]["evidence"]["required_ids"].remove("E-LATE")
        with self.assertRaisesRegex(ValueError, "decision dependencies"):
            v.validate_fixture(x)

    def test_under_specified_monitor_gold_rejected(self):
        for identity, index, dependency in [("C03", 0, "E-LATE"), ("C05", 1, "E-STALE"), ("C07", 2, "E-ADDRESS")]:
            x = self.calibration(identity)
            x["expected_results"][0]["assessments"][index]["evidence"]["required_ids"].remove(dependency)
            with self.subTest(case=identity), self.assertRaisesRegex(ValueError, "decision dependencies"):
                v.validate_fixture(x)

    def test_active_gold_requires_rule_and_evidence_support_sections(self):
        for identity, index in [("C03", 0), ("C04", 0), ("C09", 2)]:
            original = self.calibration(identity)
            sections = original["expected_results"][0]["assessments"][index]["expected_sections"]
            for omitted in range(len(sections)):
                x = copy.deepcopy(original)
                x["expected_results"][0]["assessments"][index]["expected_sections"].pop(omitted)
                with self.subTest(case=identity, section=sections[omitted]), self.assertRaisesRegex(ValueError, "normal support sections"):
                    v.validate_fixture(x)

    def test_correct_ready_and_approved_late_gap_example_validate(self):
        v.validate_fixture(self.calibration("C04"))
        v.validate_fixture(v.read_json(ROOT / "examples/late_with_gaps.example.json"))

    def test_supported_subtype_does_not_require_unresolved_other_dependency(self):
        registry = v.read_json(ROOT / "policy/policy_registry.json")
        for identity, other in [("C08", "E-ADDRESS"), ("C09", "E-FAILED")]:
            # Contract-only mutation of author declarations, not an input-derived label.
            a = self.calibration(identity)["expected_results"][0]["assessments"][2]
            a["rule_ids"].append("F-UNKNOWN")
            self.assertNotIn(other, a["evidence"]["required_ids"])
            v.validate_assessment_semantics(a, registry)
            a["supported_triggers"] = []
            with self.assertRaisesRegex(ValueError, "declared supported trigger"):
                v.validate_assessment_semantics(a, registry)

    def test_both_declared_subtype_triggers_require_both_dependencies(self):
        registry = v.read_json(ROOT / "policy/policy_registry.json")
        a = self.calibration("C08")["expected_results"][0]["assessments"][2]
        a["rule_ids"] += ["F-UNKNOWN", "F-3"]
        a["supported_triggers"].append("F-3")
        a["expected_sections"].append({"policy_id":"SOP-04", "version":"1.0-demo", "section_id":"address-notices"})
        with self.assertRaisesRegex(ValueError, "decision dependencies"):
            v.validate_assessment_semantics(a, registry)
        a["evidence"]["required_ids"].append("E-ADDRESS")
        v.validate_assessment_semantics(a, registry)

    def test_review_gold_can_describe_only_local_unresolved_dependency(self):
        x = self.calibration("C06")
        x["expected_results"][0]["assessments"][0]["evidence"]["required_ids"] = ["E-LATE"]
        v.validate_fixture(x)

    def test_raw_unknown_status_is_still_rejected_as_canonical(self):
        x = self.calibration("C11")
        v.validate_fixture(x)
        x["input_profile"] = "CANONICAL"
        x["expected_input_findings"] = []
        with self.assertRaisesRegex(ValueError, "unknown enum"):
            v.validate_fixture(x)

    def test_raw_null_attempt_identity_is_still_rejected_as_canonical(self):
        x = self.calibration("D17")
        v.validate_fixture(x)
        x["input_profile"] = "CANONICAL"
        x["expected_input_findings"] = []
        with self.assertRaisesRegex(ValueError, "requires attempt_id"):
            v.validate_fixture(x)

    def test_both_fixture_requires_each_claimed_dependency_and_decision_section(self):
        original = self.calibration("D18")
        v.validate_fixture(original)
        for dependency in ("E-FAILED", "E-ADDRESS"):
            x = copy.deepcopy(original)
            x["expected_results"][0]["assessments"][2]["evidence"]["required_ids"].remove(dependency)
            with self.subTest(dependency=dependency), self.assertRaisesRegex(ValueError, "decision dependencies"):
                v.validate_fixture(x)
        for decision_section in ("repeated-attempts", "address-notices"):
            x = copy.deepcopy(original)
            a = x["expected_results"][0]["assessments"][2]
            a["expected_sections"] = [s for s in a["expected_sections"] if s["section_id"] != decision_section]
            with self.subTest(section=decision_section), self.assertRaisesRegex(ValueError, "normal support sections"):
                v.validate_fixture(x)


if __name__ == "__main__":
    unittest.main()
