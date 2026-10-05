"""Pinned DEVELOPMENT custody and structural validation; never discovers splits."""
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat

from .answerability_contracts import (
    ALLOW, ABSTAIN, SUPPORTED, INSUFFICIENT, UNRESOLVED,
    ContractError, EvaluationCase, digest, identity, require, text,
)

MANIFEST_SHA256 = "cae8a072192cad67b58e7d366afa9210972d672faa2e17047f2742e75a8499c2"
RECEIPT = "9913c3028119f708a19ad762efda5f86b80b1f78c624eddbd632d6129e5b802d"
RECEIPT_ALGORITHM = "ANSWERABILITY_MANIFEST_RECEIPT_V1"
PROTOCOL_COMMIT = "347ce9f3ff37bd73f4750cde01562f0573a2b4ab"
BLUEPRINT_SHA256 = "bd3bc55cda23adfdd2d6ec6de22188f993ce3c64516a446a3fb471b051a344bc"
IDS = tuple(f"AQ{i:03d}" for i in range(1, 41))
ROOT = Path(__file__).resolve().parent
POLICY_ROOT = ROOT.parents[1] / "policy"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def strict_json(data):
    def invalid_constant(value):
        raise ContractError(f"invalid JSON constant: {value}")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=invalid_constant)
    except (UnicodeError, ValueError) as exc:
        raise ContractError("invalid strict UTF-8 JSON") from exc


def validate_entries(manifest):
    require(type(manifest) is dict, "manifest object required")
    expected = {
        "benchmark_version": "answerability-benchmark-v0.1", "split": "DEVELOPMENT",
        "status": "OWNER_REVIEWED", "receipt_status": "FINAL", "frozen": True,
        "question_count": 40, "receipt_algorithm": RECEIPT_ALGORITHM,
        "aggregate_receipt": RECEIPT, "blueprint_sha256": BLUEPRINT_SHA256,
        "protocol_commit": PROTOCOL_COMMIT,
    }
    for key, value in expected.items():
        require(type(manifest.get(key)) is type(value) and manifest[key] == value,
                f"manifest {key} differs")
    entries = manifest.get("entries")
    require(type(entries) is list and len(entries) == 40, "exactly 40 entries required")
    ids, paths = set(), set()
    for entry in entries:
        require(type(entry) is dict and set(entry) ==
                {"question_id", "filename", "sha256", "expected_gate"}, "invalid entry schema")
        qid, filename = entry["question_id"], entry["filename"]
        text(qid, "entry ID")
        text(filename, "entry path")
        posix, windows = PurePosixPath(filename), PureWindowsPath(filename)
        require(not posix.is_absolute() and not windows.is_absolute() and not windows.drive
                and "\\" not in filename and ".." not in posix.parts
                and str(posix) == filename, "unsafe manifest path")
        require(qid in IDS and filename == f"development/{qid}.json", "unexpected DEVELOPMENT path/ID")
        require(qid not in ids and filename not in paths, "duplicate entry ID/path")
        require(entry["expected_gate"] in (ALLOW, ABSTAIN), "invalid manifest decision")
        digest(entry["sha256"])
        ids.add(qid)
        paths.add(filename)
    require(ids == set(IDS), "missing or unexpected manifest ID")
    return tuple(sorted(entries, key=lambda e: e["question_id"]))


def safe_regular_file(root, relative):
    """Reject links/reparse points on every component before reading file bytes."""
    root = Path(root).absolute()
    parts = PurePosixPath(relative).parts
    require(parts and not PureWindowsPath(relative).drive and not relative.startswith("/")
            and "\\" not in relative and all(p not in ("..", ".") for p in parts)
            and str(PurePosixPath(relative)) == relative, "unsafe relative path")
    target = root.joinpath(*parts)
    for part in reversed((target, *target.parents)):
        info = part.lstat()
        require(not stat.S_ISLNK(info.st_mode)
                and not (getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT),
                "symlink/reparse point rejected")
    require(target.resolve().is_relative_to(root.resolve()), "path escapes root")
    require(stat.S_ISREG(target.lstat().st_mode), "regular file required")
    return target


def _verified_bytes(manifest_root, question_root):
    """Import/test helper, still pinned to the ONE DEVELOPMENT manifest hash."""
    manifest_bytes = safe_regular_file(manifest_root, "DEVELOPMENT_MANIFEST.json").read_bytes()
    require(sha256(manifest_bytes) == MANIFEST_SHA256, "frozen manifest hash differs")
    entries = validate_entries(strict_json(manifest_bytes))
    payloads = []
    for entry in entries:
        data = safe_regular_file(question_root, entry["filename"]).read_bytes()
        require(sha256(data) == entry["sha256"], f"question hash differs: {entry['question_id']}")
        payloads.append((entry, data))
    receipt_bytes = "".join(f"{e['question_id']}\t{e['filename']}\t{sha256(data)}\n"
                            for e, data in payloads).encode("utf-8")
    require(sha256(receipt_bytes) == RECEIPT, "DEVELOPMENT receipt differs")
    # No question JSON has been parsed before every file and receipt passes.
    return manifest_bytes, tuple(payloads)


def active_policy_identities():
    """Validate the public 25-section corpus without importing retrieval/model code."""
    manifest_bytes = safe_regular_file(POLICY_ROOT, "artifact_manifest.json").read_bytes()
    require(sha256(manifest_bytes) == "093b763fadfaadf7859d758722e21160390edeb4d0a4e0ce18a97401efcba77f",
            "public policy manifest changed")
    manifest = strict_json(manifest_bytes)
    registry_bytes = safe_regular_file(POLICY_ROOT, "policy_registry.json").read_bytes()
    require(sha256(registry_bytes) == "a9d50558f1654281212d45c27ec9e419f788364bf086d4c63b2cf1dcd6eed768",
            "public registry changed")
    registry = strict_json(registry_bytes)
    identities = set()
    for sop in registry["sops"]:
        data = safe_regular_file(POLICY_ROOT.parent, sop["path"]).read_bytes()
        require(sha256(data) == manifest["sha256"][sop["path"]], "public SOP bytes changed")
        for section in sop["section_ids"]:
            identities.add(identity((sop["policy_id"], registry["bundle_version"], section)))
    require(len(identities) == 25 and len(registry["sops"]) == 8, "public corpus inventory differs")
    return frozenset(identities)


RECORD_FIELDS = frozenset({
    "question_id", "split", "question", "expected_gate", "reason_code", "difficulty_band",
    "support_shape", "hard_negative", "gold_support_sections", "required_support_sections",
    "authoring_rationale", "review_status",
})


def validate_record(record, entry, known_identities):
    require(type(record) is dict and set(record) == RECORD_FIELDS, "invalid DEVELOPMENT record schema")
    require(record["question_id"] == entry["question_id"], "record ID differs from manifest")
    require(record["expected_gate"] == entry["expected_gate"], "record decision differs from manifest")
    require(record["split"] == "DEVELOPMENT", "only DEVELOPMENT is allowed")
    require(record["review_status"] == "OWNER_REVIEWED", "owner review required")
    require(record["difficulty_band"] in ("DIRECT", "PARAPHRASE", "INDIRECT_OPERATIONAL"),
            "invalid difficulty annotation")
    require(type(record["hard_negative"]) is bool, "hard_negative must be boolean")
    text(record["authoring_rationale"], "authoring rationale")
    supports = []
    for field in ("gold_support_sections", "required_support_sections"):
        require(type(record[field]) is list, "support list required")
        refs = []
        for ref in record[field]:
            require(type(ref) is dict and set(ref) == {"policy_id", "version", "section_id"},
                    "invalid support identity fields")
            canonical = identity((ref["policy_id"], ref["version"], ref["section_id"]))
            require(canonical in known_identities, "unknown active support identity")
            refs.append(canonical)
        supports.append(tuple(refs))
    case = EvaluationCase(record["question_id"], record["question"], record["expected_gate"],
                          record["reason_code"], *supports)
    shape = ("MULTI_SECTION" if len(case.required_support_sections) > 1 else "SINGLE_SECTION")
    if case.expected_gate == ABSTAIN:
        shape = "NOT_APPLICABLE"
    else:
        require(not record["hard_negative"], "ALLOW cannot be hard_negative")
    require(record["support_shape"] == shape, "support_shape differs from required support")
    return case


def _load_verified(manifest_root, question_root):
    _, payloads = _verified_bytes(manifest_root, question_root)
    known = active_policy_identities()
    records = [strict_json(data) for _, data in payloads]
    cases = tuple(validate_record(record, entry, known)
                  for record, (entry, _) in zip(records, payloads))
    require(Counter(c.expected_gate for c in cases) == {ALLOW: 20, ABSTAIN: 20}, "class counts differ")
    require(Counter(c.reason_code for c in cases) ==
            {SUPPORTED: 20, INSUFFICIENT: 16, UNRESOLVED: 4}, "reason counts differ")
    require(Counter(r["support_shape"] for r in records) ==
            {"SINGLE_SECTION": 14, "MULTI_SECTION": 6, "NOT_APPLICABLE": 20}, "shape counts differ")
    require(sum(r["hard_negative"] for r in records) == 16, "hard-negative count differs")
    for decision, counts in ((ALLOW, (6, 8, 6)), (ABSTAIN, (4, 8, 8))):
        require(Counter(r["difficulty_band"] for r in records if r["expected_gate"] == decision) ==
                dict(zip(("DIRECT", "PARAPHRASE", "INDIRECT_OPERATIONAL"), counts)),
                "difficulty counts differ")
    require({ref[0] for c in cases for ref in c.gold_support_sections} ==
            {f"SOP-{n:02d}" for n in range(1, 9)}, "DEVELOPMENT ALLOW must cover all eight SOPs")
    return cases


def load_development():
    """Normal runtime entry: no split/path argument and no private workspace access."""
    return _load_verified(ROOT, ROOT)


def validation_summary():
    cases = load_development()
    return {"validation": "PASS", "question_count": len(cases), "allow_count": 20,
            "abstain_count": 20, "manifest_sha256": MANIFEST_SHA256,
            "receipt_algorithm": RECEIPT_ALGORITHM, "aggregate_receipt": RECEIPT,
            "question_hashes_verified": 40, "retrieval_attempts": 0, "gate_attempts": 0}
