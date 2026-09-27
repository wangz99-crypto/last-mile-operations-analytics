"""Post-heldout Phase 1B.2 DEVELOPMENT regression; never a blind held-out score."""
import copy
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
EVALUATION = HERE.parent
if str(EVALUATION) not in sys.path:
    sys.path.insert(0, str(EVALUATION))
import compare_development as legacy

CALIBRATION = EVALUATION / "development/calibration"
OVERRIDES = HERE / "diagnostic_expectation_overrides.json"
EXPECTED_IDS = tuple([f"C{i:02d}" for i in range(1, 13)] + [f"D{i}" for i in range(13, 19)])
ROLE = "POST_HELDOUT_DEVELOPMENT_REGRESSION"
# Closed inventory of reviewed diagnostic migrations, not engine-derived labels.
# Tuple values: assessment category / blocker code / frozen value / new value.
REVIEWED = {
    ("C04", "/expected_results/0/assessments/2/blockers/0/dependent_decision"):
        ("FAILED_ATTEMPT_ADDRESS", "INCOMPLETE_ATTEMPT_HISTORY", "FAILED_ATTEMPT_ADDRESS", "FAILED_ATTEMPT"),
    ("C04", "/expected_results/0/assessments/2/blockers/1/dependent_decision"):
        ("FAILED_ATTEMPT_ADDRESS", "UNKNOWN_ADDRESS_STATE", "FAILED_ATTEMPT_ADDRESS", "ADDRESS_EXCEPTION"),
    ("D15", "/expected_results/0/assessments/2/blockers/0/dependent_decision"):
        ("FAILED_ATTEMPT_ADDRESS", "CONFLICTING_ADDRESS_MARKERS", "FAILED_ATTEMPT_ADDRESS", "ADDRESS_EXCEPTION"),
    ("D16", "/expected_results/0/assessments/0/blockers/0/dependent_decision"):
        ("LATE_DELIVERY", "MISSING_CARRIER", "LATE_DELIVERY", "LATE_DELIVERY_PACKET"),
    ("D17", "/expected_results/0/assessments/2/blockers/0/dependent_decision"):
        ("FAILED_ATTEMPT_ADDRESS", "MISSING_ATTEMPT_ID", "FAILED_ATTEMPT_ADDRESS", "FAILED_ATTEMPT"),
}
RECORD_FIELDS = {
    "fixture_id", "assessment_category", "blocker_selector", "field_path",
    "old_frozen_value", "new_phase_1b2_value", "rationale", "migration_version",
}
SELECTOR_FIELDS = {"code", "scope", "exception_type", "field_refs", "requirement_ids"}
TARGET_PATH = re.compile(r"/expected_results/(0|[1-9][0-9]*)/assessments/(0|[1-9][0-9]*)/blockers/(0|[1-9][0-9]*)/dependent_decision")


def validate_overrides(document):
    """Reject extra, missing, duplicate, stale or non-diagnostic migrations."""
    if not isinstance(document, dict) or set(document) != {"migration_version", "evaluation_role", "overrides"}:
        raise ValueError("Override document has unexpected fields")
    if document["migration_version"] != "1B.2" or document["evaluation_role"] != ROLE:
        raise ValueError("Overrides must identify the post-heldout Phase 1B.2 regression")
    records = document["overrides"]
    if not isinstance(records, list):
        raise ValueError("Overrides must be a list")
    seen = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            raise ValueError("Override record has unexpected fields")
        for key in RECORD_FIELDS - {"blocker_selector"}:
            if not isinstance(record[key], str) or not record[key].strip():
                raise ValueError(f"Override {key} must be a nonempty string")
        target = (record["fixture_id"], record["field_path"])
        if target not in REVIEWED or target in seen:
            raise ValueError(f"Unreviewed or duplicate override target: {target}")
        seen.add(target)
        selector = record["blocker_selector"]
        if not isinstance(selector, dict) or set(selector) != SELECTOR_FIELDS:
            raise ValueError(f"Incomplete or unexpected blocker selector: {target}")
        for key in ("field_refs", "requirement_ids"):
            if not isinstance(selector[key], list) or not selector[key] or not all(isinstance(v, str) and v for v in selector[key]):
                raise ValueError(f"Invalid blocker selector {key}: {target}")
        if (record["assessment_category"], selector["code"], record["old_frozen_value"], record["new_phase_1b2_value"]) != REVIEWED[target]:
            raise ValueError(f"Unreviewed migration values: {target}")
        if record["migration_version"] != "1B.2" or selector["scope"] != "CATEGORY" or selector["exception_type"] != record["assessment_category"]:
            raise ValueError(f"Invalid migration version or category selector: {target}")
    if seen != set(REVIEWED):
        raise ValueError("Override inventory must contain exactly the five reviewed migrations")
    return records


def load_overrides():
    document = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    validate_overrides(document)
    return document


def apply_overrides(labeled, document):
    """Return an in-memory copy; the only assignment is dependent_decision."""
    records = validate_overrides(document)
    if labeled["fixture_id"] not in EXPECTED_IDS or labeled["split"] != "DEVELOPMENT":
        raise ValueError("Only frozen DEVELOPMENT fixtures may use this migration")
    if labeled["gold_provenance"]["review_status"] != "OWNER_REVIEWED":
        raise ValueError("Frozen DEVELOPMENT Gold requires owner review")
    migrated = copy.deepcopy(labeled)
    for record in records:
        if record["fixture_id"] != labeled["fixture_id"]:
            continue
        # A JSON pointer into the original, unnormalized frozen fixture.
        match = TARGET_PATH.fullmatch(record["field_path"])
        if match is None:
            raise ValueError("Only assessment blocker dependent_decision paths are allowed")
        ri, ai, bi = map(int, match.groups())
        selector = record["blocker_selector"]
        matches = []
        for result_index, result in enumerate(migrated["expected_results"]):
            for assessment_index, assessment in enumerate(result["assessments"]):
                if assessment["exception_type"] != record["assessment_category"]:
                    continue
                for blocker_index, blocker in enumerate(assessment["blockers"]):
                    if all(blocker.get(key) == value for key, value in selector.items()):
                        matches.append((result_index, assessment_index, blocker_index))
        if matches != [(ri, ai, bi)]:
            raise ValueError(f"{record['fixture_id']}: blocker selector must uniquely match {record['field_path']}")
        blocker = migrated["expected_results"][ri]["assessments"][ai]["blockers"][bi]
        if blocker["dependent_decision"] != record["old_frozen_value"]:
            raise ValueError(f"{record['fixture_id']}: old frozen value does not match at {record['field_path']}")
        blocker["dependent_decision"] = record["new_phase_1b2_value"]
    return migrated


def compare_case(path, document=None):
    path = Path(path).resolve()
    if path.parent != CALIBRATION.resolve() or path.suffix != ".json" or path.stem not in EXPECTED_IDS:
        raise ValueError("This comparator accepts only the frozen 18 public DEVELOPMENT paths")
    # Keep the same input-only engine boundary as the unchanged legacy comparator.
    actual = legacy.triage_snapshot(**legacy.input_packet(path))
    labeled = json.loads(path.read_text(encoding="utf-8"))
    if labeled["fixture_id"] != path.stem:
        raise ValueError("Fixture identity must match its frozen file name")
    expected = apply_overrides(labeled, load_overrides() if document is None else document)
    # Exactly the legacy representation contract; no added exclusions or tolerance.
    diffs = legacy.differences(legacy.normalize(actual["results"]), legacy.normalize(expected["expected_results"]))
    finding_paths = {finding["path"] for finding in actual["validation_findings"]}
    for finding in labeled["expected_input_findings"]:
        if finding["path"] not in finding_paths:
            diffs.append(f"validation_findings: missing authored invalid path {finding['path']}")
    return actual, diffs


def main():
    print("Post-heldout Phase 1B.2 DEVELOPMENT regression (implementation-visible; not a blind held-out score).")
    print("Comparison contract: legacy list-order normalization and explanatory rationale/reason/message exclusions only;")
    print("all operational fields, including dependent_decision, remain compared. Authored invalid-input paths must be present.")
    paths = sorted((EVALUATION / "development").rglob("*.json"))
    if paths != [CALIBRATION / (identity + ".json") for identity in EXPECTED_IDS]:
        raise ValueError("DEVELOPMENT inventory must be exactly the frozen 18 paths")
    document = load_overrides()
    print("Applying exactly five reviewed dependent_decision migrations in memory.")
    failed = []
    for path in paths:
        _, diffs = compare_case(path, document)
        print(f"{path.stem}: {'FAIL' if diffs else 'PASS'}")
        if diffs:
            failed.append(path.stem)
            for diff in diffs:
                print("  " + diff)
    print(f"Post-1B.2 versioned Development regression: {len(paths) - len(failed)}/{len(paths)}")
    print(f"Failed IDs: {failed}")
    return bool(failed)


if __name__ == "__main__":
    sys.exit(main())
