"""Section-store integrity tests; mutations affect temporary runtime copies only."""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from retrieval import (
    InvalidSectionReferenceError, SectionIntegrityError, SectionNotFoundError,
    SectionStore, section_content_hash,
)

LATE = "sops/last_mile/late_delivery.md"
REGISTRY = "policy/policy_registry.json"
MANIFEST = "policy/artifact_manifest.json"


class SectionStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = SectionStore.load()
        cls.registry = json.loads((DOMAIN / REGISTRY).read_text(encoding="utf-8"))

    def copied_bundle(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in ("policy", "schemas", "sops"):
            shutil.copytree(DOMAIN / name, root / name)
        return root

    def rehash_copy(self, root, name):
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        manifest["sha256"][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
        (root / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")

    def write_sop_copy(self, root, text):
        (root / LATE).write_bytes(text.encode("utf-8"))
        self.rehash_copy(root, LATE)

    def change_metadata(self, root, change):
        text = (root / LATE).read_text(encoding="utf-8")
        block = re.search(r"```json\n(.*?)\n```", text, re.S)
        metadata = json.loads(block[1])
        change(metadata)
        self.write_sop_copy(root, text[:block.start(1)] + json.dumps(metadata, indent=2) + text[block.end(1):])

    def test_inventory_and_every_registry_identity_resolve(self):
        self.assertEqual((self.store.document_count, self.store.section_count, self.store.versions), (8, 25, ("1.0-demo",)))
        expected = [(sop["policy_id"], self.registry["bundle_version"], section)
                    for sop in self.registry["sops"] for section in sop["section_ids"]]
        self.assertEqual(len(set(expected)), 25)
        self.assertEqual([section.identity for section in self.store.sections], expected)
        for sop in self.registry["sops"]:
            for section_id in sop["section_ids"]:
                with self.subTest(policy=sop["policy_id"], section=section_id):
                    section = self.store.get(policy_id=sop["policy_id"], version="1.0-demo", section_id=section_id)
                    self.assertEqual(section.source_path, sop["path"])
                    self.assertEqual(section.effective_from, self.registry["effective_from"])
                    self.assertEqual(section.effective_to, self.registry["effective_to"])
                    self.assertIs(section.demo_policy, True)

    def test_record_and_inventory_are_readonly(self):
        section = self.store.get(policy_id="SOP-02", version="1.0-demo", section_id="late-escalate")
        with self.assertRaises(FrozenInstanceError):
            section.text = "invented policy"
        with self.assertRaises(TypeError):
            self.store._sections[section.identity] = section
        with self.assertRaises(FrozenInstanceError):
            self.store._sections = {}
        self.assertIsInstance(section.rule_ids, tuple)
        self.assertIsInstance(section.requirement_ids, tuple)
        self.assertIsInstance(section.exception_types, tuple)

    def test_inventory_does_not_inflate_empty_values(self):
        empty = SectionStore({})
        self.assertEqual((empty.document_count, empty.section_count, empty.versions), (0, 0, ()))

    def test_unknown_section_policy_and_version_fail(self):
        for identity in (("SOP-02", "1.0-demo", "late-escalat"), ("SOP-99", "1.0-demo", "late-escalate"),
                         ("SOP-02", "2.0-demo", "late-escalate")):
            with self.subTest(identity=identity), self.assertRaises(SectionNotFoundError) as caught:
                self.store.get(**dict(zip(("policy_id", "version", "section_id"), identity)))
            self.assertEqual(caught.exception.identities, (identity,))

    def test_mixed_versions_are_rejected_before_resolution(self):
        refs = [("SOP-02", "1.0-demo", "late-escalate"), ("SOP-03", "2.0-demo", "stale-escalate")]
        with self.assertRaisesRegex(InvalidSectionReferenceError, "Mixed policy versions"):
            self.store.resolve_many(refs)

    def test_exact_references_only(self):
        invalid = ["late delivery", ["SOP-02", "1.0-demo", "late-escalate"],
                   {"policy_id": "SOP-02", "section_id": "late-escalate"},
                   {"policy_id": "SOP-02", "version": "1.0-demo", "section_id": "late-escalate", "rank": 1},
                   ("SOP-02", "1.0-demo", "late-escalate "), ("SOP-02", None, "late-escalate")]
        for ref in invalid:
            with self.subTest(ref=ref), self.assertRaises(InvalidSectionReferenceError):
                self.store.resolve_many([ref])
        for refs in (None, "SOP-02", {}):
            with self.subTest(refs=refs), self.assertRaises(InvalidSectionReferenceError):
                self.store.resolve_many(refs)

    def test_order_and_all_duplicate_request_positions_are_preserved(self):
        first = ("SOP-03", "1.0-demo", "stale-escalate")
        second = ("SOP-02", "1.0-demo", "late-escalate")
        resolved = self.store.resolve_many([first, second, first, first, second])
        self.assertEqual([item.identity for item in resolved], [first, second])
        self.assertEqual([item.request_indices for item in resolved], [(0, 2, 3), (1, 4)])
        self.assertEqual(self.store.resolve_many([]), ())

    def test_missing_required_identity_returns_no_partial_result(self):
        missing = ("SOP-02", "1.0-demo", "late-escalation")
        with self.assertRaises(SectionNotFoundError) as caught:
            self.store.resolve_many([("SOP-02", "1.0-demo", "late-escalate"), missing])
        self.assertEqual(caught.exception.identities, (missing,))

    def test_corrupt_file_fails_checksum_before_metadata_parsing(self):
        root = self.copied_bundle()
        (root / LATE).write_bytes(b"not Markdown or metadata")
        with self.assertRaisesRegex(SectionIntegrityError, "checksum mismatch.*late_delivery"):
            SectionStore.load(root)

    def test_registry_schema_and_manifest_checksums_fail_closed(self):
        for name in (REGISTRY, "schemas/contracts.schema.json"):
            root = self.copied_bundle()
            with (root / name).open("ab") as stream:
                stream.write(b" ")
            with self.subTest(name=name), self.assertRaisesRegex(SectionIntegrityError, "checksum mismatch"):
                SectionStore.load(root)
        root = self.copied_bundle()
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        del manifest["sha256"][LATE]
        (root / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(SectionIntegrityError):
            SectionStore.load(root)

    def test_missing_and_extra_sop_documents_fail_closed(self):
        for mode in ("missing", "extra"):
            root = self.copied_bundle()
            if mode == "missing":
                (root / LATE).unlink()
            else:
                shutil.copyfile(root / LATE, root / "sops/last_mile/another_policy.md")
            with self.subTest(mode=mode), self.assertRaisesRegex(SectionIntegrityError, "document inventory"):
                SectionStore.load(root)

    def test_malformed_and_duplicate_json_metadata_fail_with_valid_file_checksum(self):
        for replacement in ('{"policy_id":', '{"policy_id":"SOP-02","policy_id":"SOP-02"}', '[]', '{"sections":null}'):
            root = self.copied_bundle()
            text = (root / LATE).read_text(encoding="utf-8")
            text = re.sub(r"(?<=```json\n).*?(?=\n```)", lambda _: replacement, text, count=1, flags=re.S)
            self.write_sop_copy(root, text)
            with self.subTest(metadata=replacement), self.assertRaises(SectionIntegrityError):
                SectionStore.load(root)

    def test_wrong_policy_version_and_inherited_metadata_fail_closed(self):
        for key, value in (("policy_id", "SOP-99"), ("version", "2.0-demo"), ("demo_policy", False),
                           ("effective_from", "2020-01-01T00:00:00Z"), ("effective_to", "2030-01-01T00:00:00Z"),
                           ("exception_types", ["UNKNOWN"]), ("title", "")):
            root = self.copied_bundle()
            self.change_metadata(root, lambda metadata: metadata.update({key: value}))
            with self.subTest(field=key), self.assertRaises(SectionIntegrityError):
                SectionStore.load(root)

    def test_missing_extra_and_malformed_section_headings_fail_closed(self):
        for mode in ("missing", "extra", "malformed"):
            root = self.copied_bundle()
            text = (root / LATE).read_text(encoding="utf-8")
            if mode == "missing":
                text = text[:text.index("## late-escalate")]
            elif mode == "extra":
                text += "\n## undeclared-section\n\nUnapproved section.\n"
            else:
                text += "\n## Unstable heading\n\nUnapproved section.\n"
            self.write_sop_copy(root, text)
            with self.subTest(mode=mode), self.assertRaises(SectionIntegrityError):
                SectionStore.load(root)

    def test_registry_section_mismatch_and_duplicate_identity_fail_closed(self):
        for mode in ("section_mismatch", "duplicate_document", "duplicate_section"):
            root = self.copied_bundle()
            registry = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
            if mode == "section_mismatch":
                registry["sops"][1]["section_ids"][-1] = "late-escalation"
            elif mode == "duplicate_document":
                registry["sops"].append(registry["sops"][1])
            else:
                registry["sops"][1]["section_ids"].append("late-escalate")
            (root / REGISTRY).write_text(json.dumps(registry), encoding="utf-8")
            self.rehash_copy(root, REGISTRY)
            with self.subTest(mode=mode), self.assertRaises(SectionIntegrityError):
                SectionStore.load(root)

    def test_section_backlinks_checked_in_both_directions(self):
        for mode in ("missing", "orphan", "unknown", "registry"):
            root = self.copied_bundle()
            if mode == "registry":
                registry = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
                rule = next(rule for rule in registry["rules"] if rule["rule_id"] == "L-2")
                rule["support_sections"][0]["section_id"] = "late-monitor"
                (root / REGISTRY).write_text(json.dumps(registry), encoding="utf-8")
                self.rehash_copy(root, REGISTRY)
            else:
                values = {"missing": [], "orphan": ["L-2", "L-1"], "unknown": ["UNKNOWN"]}[mode]
                self.change_metadata(root, lambda metadata: metadata["sections"][2].update(rule_ids=values))
            with self.subTest(mode=mode), self.assertRaisesRegex(SectionIntegrityError, "backlinks"):
                SectionStore.load(root)

    def test_runtime_section_hash_payload_and_repeated_loads(self):
        repeated = SectionStore.load()
        self.assertEqual(self.store.sections, repeated.sections)
        section = self.store.get(policy_id="SOP-02", version="1.0-demo", section_id="late-escalate")
        body = (DOMAIN / LATE).read_text(encoding="utf-8").split("## late-escalate\n", 1)[1]
        payload = "SOP-02\n1.0-demo\nlate-escalate\nLate Escalate\n" + body
        self.assertEqual(section.content_hash, hashlib.sha256(payload.encode("utf-8")).hexdigest())
        self.assertEqual(section.text, body)
        self.assertTrue(body.startswith("\n") and body.endswith("\n"))
        self.assertRegex(section.content_hash, r"\A[0-9a-f]{64}\Z")

    def test_changed_body_changes_only_its_section_hash(self):
        root = self.copied_bundle()
        text = (root / LATE).read_text(encoding="utf-8")
        self.write_sop_copy(root, text + "\nAdditional **temporary test text**.  \n")
        changed = SectionStore.load(root)
        changed_ids = [old.identity for old, new in zip(self.store.sections, changed.sections) if old.content_hash != new.content_hash]
        self.assertEqual(changed_ids, [("SOP-02", "1.0-demo", "late-escalate")])
        changed_section = changed.get(policy_id="SOP-02", version="1.0-demo", section_id="late-escalate")
        self.assertTrue(changed_section.text.endswith("**.  \n"))  # Preserve Markdown hard-break spaces.

    def test_line_endings_normalized_only_for_section_hash(self):
        root = self.copied_bundle()
        original = (root / LATE).read_bytes()
        lf = original.replace(b"\r\n", b"\n")
        # Exercise an actual byte change on both Windows and LF checkouts.
        changed = lf if b"\r\n" in original else lf.replace(b"\n", b"\r\n")
        (root / LATE).write_bytes(changed)
        with self.assertRaisesRegex(SectionIntegrityError, "checksum mismatch"):
            SectionStore.load(root)
        self.rehash_copy(root, LATE)
        self.assertEqual(self.store.sections, SectionStore.load(root).sections)
        self.assertEqual(section_content_hash("P", "V", "S", "T", "\r\nbody\r\n"),
                         section_content_hash("P", "V", "S", "T", "\nbody\n"))
        self.assertNotEqual(section_content_hash("P", "V", "S", "T", "body  \n"),
                            section_content_hash("P", "V", "S", "T", "body\n"))

    def test_nested_markdown_and_fenced_headings_remain_in_section_body(self):
        root = self.copied_bundle()
        text = (root / LATE).read_text(encoding="utf-8")
        appended = "\n### Nested detail\n\n```text\n## example-only\n```\n"
        self.write_sop_copy(root, text + appended)
        store = SectionStore.load(root)
        self.assertEqual(store.section_count, 25)
        section = store.get(policy_id="SOP-02", version="1.0-demo", section_id="late-escalate")
        self.assertTrue(section.text.endswith(appended))


if __name__ == "__main__":
    unittest.main()
