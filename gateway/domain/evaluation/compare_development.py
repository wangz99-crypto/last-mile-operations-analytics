"""Implementation-visible DEVELOPMENT comparison, never imported by the engine."""
import copy
import json
from pathlib import Path
import sys

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from engine import triage_snapshot


def input_packet(path):
    # Projection before the call: fixture labels never cross the engine boundary.
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: copy.deepcopy(value[k]) for k in ("manifest", "policy", "input", "input_profile")}


def normalize(value):
    """Order-insensitive sets and author-vs-engine explanatory text only.

    No classification, gate, rule, blocker code, scope, reference or numeric value
    is dropped, rounded, filled in or inferred. All list entries remain present.
    """
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in sorted(value.items()) if k not in ("rationale", "reason", "message")}
    if isinstance(value, list):
        return sorted((normalize(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    return value


def differences(actual, gold, path="$", out=None):
    out = [] if out is None else out
    if isinstance(actual, dict) and isinstance(gold, dict):
        for key in sorted(actual.keys() | gold.keys()):
            if key not in actual or key not in gold:
                out.append(f"{path}.{key}: actual={actual.get(key)!r}; gold={gold.get(key)!r} (key mismatch)")
            else:
                differences(actual[key], gold[key], f"{path}.{key}", out)
    elif isinstance(actual, list) and isinstance(gold, list):
        if len(actual) != len(gold):
            out.append(f"{path}: actual length={len(actual)}; gold length={len(gold)}")
        for i, (a, g) in enumerate(zip(actual, gold)):
            differences(a, g, f"{path}[{i}]", out)
    elif actual != gold or (isinstance(actual, bool) != isinstance(gold, bool)):
        out.append(f"{path}: actual={actual!r}; gold={gold!r}")
    return out


def compare_case(path):
    actual = triage_snapshot(**input_packet(path))
    # Gold loaded separately, only after deterministic output has been produced.
    labeled = json.loads(Path(path).read_text(encoding="utf-8"))
    if labeled["gold_provenance"]["review_status"] != "OWNER_REVIEWED":
        raise ValueError(f"{path}: DEVELOPMENT Gold requires owner review")
    diffs = differences(normalize(actual["results"]), normalize(labeled["expected_results"]))
    finding_paths = {f["path"] for f in actual["validation_findings"]}
    for f in labeled["expected_input_findings"]:
        if f["path"] not in finding_paths:
            diffs.append(f"validation_findings: missing authored invalid path {f['path']}")
    return actual, diffs


def main():
    paths = sorted((DOMAIN / "evaluation/development").rglob("*.json"))
    expected_ids = [f"C{i:02d}" for i in range(1, 13)] + [f"D{i}" for i in range(13, 19)]
    if [p.stem for p in paths] != expected_ids:
        raise ValueError("DEVELOPMENT inventory must be exactly the frozen 18 IDs")
    failed = []
    for path in paths:
        _, diffs = compare_case(path)
        print(f"{path.stem}: {'FAIL' if diffs else 'PASS'}")
        if diffs:
            failed.append(path.stem)
            for diff in diffs:
                print("  " + diff)
    print(f"DEVELOPMENT conformance: {len(paths)-len(failed)}/{len(paths)} passed; failed IDs: {failed}")
    print("Implementation-visible policy conformance only; not held-out or production accuracy.")
    return bool(failed)


if __name__ == "__main__":
    sys.exit(main())
