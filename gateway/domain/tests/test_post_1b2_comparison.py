"""Guard the post-heldout Development migration; no private held-out reads."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

DOMAIN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "post_1b2_comparison", DOMAIN / "evaluation/post_1b2/compare_post_1b2.py")
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class Post1B2ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.document = comparison.load_overrides()

    def fixture(self, identity):
        return json.loads((comparison.CALIBRATION / (identity + ".json")).read_text(encoding="utf-8"))

    def test_versioned_regression_and_legacy_differences_remain_distinct(self):
        counts = {}
        for identity in comparison.EXPECTED_IDS:
            with self.subTest(fixture=identity):
                path = comparison.CALIBRATION / (identity + ".json")
                original_bytes = path.read_bytes()
                actual, diffs = comparison.compare_case(path, self.document)
                legacy_actual, legacy_diffs = comparison.legacy.compare_case(path)
                self.assertEqual(diffs, [])
                self.assertEqual(actual, legacy_actual)
                self.assertEqual(path.read_bytes(), original_bytes)
                if legacy_diffs:
                    counts[identity] = len(legacy_diffs)
                    self.assertTrue(all(".dependent_decision:" in diff for diff in legacy_diffs))
        self.assertEqual(counts, {"C04": 2, "D15": 1, "D16": 1, "D17": 1})

    def test_copy_changes_only_the_five_diagnostic_fields(self):
        before_document = copy.deepcopy(self.document)
        count = 0
        for identity in comparison.EXPECTED_IDS:
            labeled = self.fixture(identity)
            original = copy.deepcopy(labeled)
            migrated = comparison.apply_overrides(labeled, self.document)
            self.assertEqual(labeled, original)
            # Raw comparison includes prose, input, provenance and list order too.
            diffs = comparison.legacy.differences(migrated, labeled)
            self.assertTrue(all(".dependent_decision:" in diff for diff in diffs))
            count += len(diffs)
        self.assertEqual(count, 5)
        self.assertEqual(self.document, before_document)

    def test_invalid_override_inventory_and_metadata_fail_closed(self):
        variants = []
        value = copy.deepcopy(self.document); value["overrides"].pop(); variants.append(value)
        value = copy.deepcopy(self.document); value["overrides"].append(copy.deepcopy(value["overrides"][0])); variants.append(value)
        for key, invalid in (("field_path", "/expected_results/0/priority"), ("fixture_id", "C05"),
                             ("migration_version", "1B.3"), ("new_phase_1b2_value", "PACKET"),
                             ("old_frozen_value", "FAILED_ATTEMPT"), ("rationale", ""),
                             ("assessment_category", "LATE_DELIVERY")):
            value = copy.deepcopy(self.document); value["overrides"][0][key] = invalid; variants.append(value)
        value = copy.deepcopy(self.document); value["overrides"][0]["result"] = "TRUE"; variants.append(value)
        value = copy.deepcopy(self.document); value["migration_version"] = "1B.3"; variants.append(value)
        value = copy.deepcopy(self.document); value["evaluation_role"] = "BLIND_HELDOUT"; variants.append(value)
        value = copy.deepcopy(self.document); value["ignored_fields"] = ["priority"]; variants.append(value)
        for value in variants:
            with self.subTest(document=value), self.assertRaises(ValueError):
                comparison.validate_overrides(value)

    def test_selector_mismatch_and_ambiguity_fail_closed(self):
        original = self.fixture("C04")
        for key, invalid in (("code", "UNKNOWN"), ("scope", "SHIPMENT"),
                             ("exception_type", "LATE_DELIVERY"), ("field_refs", ["other"]),
                             ("requirement_ids", ["E-ADDRESS"])):
            value = copy.deepcopy(self.document)
            value["overrides"][0]["blocker_selector"][key] = invalid
            with self.subTest(key=key), self.assertRaises(ValueError):
                comparison.apply_overrides(original, value)
        ambiguous = copy.deepcopy(original)
        blockers = ambiguous["expected_results"][0]["assessments"][2]["blockers"]
        blockers.append(copy.deepcopy(blockers[0]))
        with self.assertRaisesRegex(ValueError, "uniquely"):
            comparison.apply_overrides(ambiguous, self.document)

    def test_old_value_and_pointer_are_checked_against_frozen_gold(self):
        for mode in ("stale", "reordered"):
            labeled = self.fixture("C04")
            blockers = labeled["expected_results"][0]["assessments"][2]["blockers"]
            if mode == "stale":
                blockers[0]["dependent_decision"] = "FAILED_ATTEMPT"
            else:
                blockers.reverse()
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                comparison.apply_overrides(labeled, self.document)

    def test_unreviewed_or_non_development_gold_is_rejected(self):
        for key, invalid in (("fixture_id", "H01"), ("split", "HELDOUT"), ("review_status", "DRAFT")):
            labeled = self.fixture("C04")
            if key == "review_status":
                labeled["gold_provenance"][key] = invalid
            else:
                labeled[key] = invalid
            with self.subTest(key=key), self.assertRaises(ValueError):
                comparison.apply_overrides(labeled, self.document)

    def test_every_protected_operational_field_still_produces_a_difference(self):
        path = comparison.CALIBRATION / "D16.json"
        actual, diffs = comparison.compare_case(path, self.document)
        self.assertEqual(diffs, [])
        mutations = [
            (("results", 0, "assessments", 0, "result"), "FALSE"),
            (("results", 0, "assessments", 0, "escalation_eligible"), False),
            (("results", 0, "assessments", 0, "action_state"), "READY_TO_ESCALATE"),
            (("results", 0, "assessments", 0, "rule_ids"), ["L-1"]),
            (("results", 0, "assessments", 0, "supported_triggers"), []),
            (("results", 0, "assessments", 0, "evidence", "missing_ids"), []),
            (("results", 0, "assessments", 0, "expected_sections"), []),
            (("results", 0, "aggregate_action_state"), "NORMAL"),
            (("results", 0, "priority"), "LOW"),
            (("results", 0, "derived_facts", "hours_overdue"), 0),
            (("results", 0, "assessments", 0, "blockers", 0, "dependent_decision"), "LATE_DELIVERY"),
            (("results", 0, "assessments", 0, "blockers", 0, "code"), "UNKNOWN"),
            (("results", 0, "assessments", 0, "blockers", 0, "field_refs"), []),
            (("results", 0, "assessments", 0, "blockers", 0, "requirement_ids"), []),
            (("results", 0, "unexpected_field"), "must not disappear"),
        ]
        for keys, value in mutations:
            changed = copy.deepcopy(actual)
            target = changed
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value
            with self.subTest(path=keys), patch.object(comparison.legacy, "triage_snapshot", return_value=changed):
                _, diffs = comparison.compare_case(path, self.document)
                self.assertTrue(diffs)

    def test_missing_keys_and_duplicate_entries_still_fail(self):
        path = comparison.CALIBRATION / "D16.json"
        actual, _ = comparison.compare_case(path, self.document)
        for mode in ("missing_key", "duplicate_blocker"):
            changed = copy.deepcopy(actual)
            if mode == "missing_key":
                del changed["results"][0]["priority"]
            else:
                blockers = changed["results"][0]["assessments"][0]["blockers"]
                blockers.append(copy.deepcopy(blockers[0]))
            with self.subTest(mode=mode), patch.object(comparison.legacy, "triage_snapshot", return_value=changed):
                self.assertTrue(comparison.compare_case(path, self.document)[1])

    def test_authored_invalid_input_findings_are_still_required(self):
        path = comparison.CALIBRATION / "D17.json"
        actual, _ = comparison.compare_case(path, self.document)
        actual["validation_findings"] = []
        with patch.object(comparison.legacy, "triage_snapshot", return_value=actual):
            _, diffs = comparison.compare_case(path, self.document)
        self.assertTrue(any("missing authored invalid path" in diff for diff in diffs))

    def test_other_paths_are_rejected_before_reading_or_running_engine(self):
        with patch.object(Path, "read_text", side_effect=AssertionError("unexpected read")), \
                patch.object(comparison.legacy, "triage_snapshot", side_effect=AssertionError("unexpected run")):
            for name in ("H01.json", "C04.actual.json", "../../other/C04.json"):
                with self.subTest(path=name), self.assertRaises(ValueError):
                    comparison.compare_case(comparison.CALIBRATION / name, self.document)


if __name__ == "__main__":
    unittest.main()
