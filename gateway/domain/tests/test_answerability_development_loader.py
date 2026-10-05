import copy
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gateway.domain.evaluation.answerability import development_loader as loader
from gateway.domain.evaluation.answerability.answerability_contracts import ContractError, ABSTAIN, INSUFFICIENT
from gateway.domain.tests._answerability_fixtures import IDENTITIES, record, temporary_directory


class DevelopmentLoaderTests(unittest.TestCase):
    def test_valid_frozen_development_loads_without_evaluation(self):
        cases = loader.load_development()
        self.assertEqual([c.question_id for c in cases], list(loader.IDS))
        self.assertEqual(sum(c.expected_gate == "ALLOW" for c in cases), 20)
        self.assertEqual(sum(c.expected_gate == "ABSTAIN" for c in cases), 20)

    def test_wrong_manifest_hash_rejected_before_json_parsing(self):
        with temporary_directory() as root:
            (root/"DEVELOPMENT_MANIFEST.json").write_bytes(b"invalid JSON")
            with patch.object(loader, "strict_json", side_effect=AssertionError("must not parse")):
                with self.assertRaisesRegex(ContractError, "manifest hash"):
                    loader._verified_bytes(root, root)

    def test_changed_question_hash_rejected_before_question_parsing(self):
        with temporary_directory() as root:
            (root/"DEVELOPMENT_MANIFEST.json").write_bytes((loader.ROOT/"DEVELOPMENT_MANIFEST.json").read_bytes())
            (root/"development").mkdir()
            (root/"development/AQ001.json").write_bytes(b"invalid changed question bytes")
            with patch.object(loader, "strict_json", wraps=loader.strict_json) as parse:
                with self.assertRaisesRegex(ContractError, "question hash"):
                    loader._verified_bytes(root, root)
                self.assertEqual(parse.call_count, 1)  # manifest only

    def test_missing_question_fails_loudly(self):
        with temporary_directory() as root:
            (root/"DEVELOPMENT_MANIFEST.json").write_bytes((loader.ROOT/"DEVELOPMENT_MANIFEST.json").read_bytes())
            with self.assertRaises(FileNotFoundError):
                loader._verified_bytes(root, root)

    def _manifest(self):
        return loader.strict_json((loader.ROOT/"DEVELOPMENT_MANIFEST.json").read_bytes())

    def test_duplicate_id_and_path_rejected(self):
        manifest = self._manifest()
        manifest["entries"][1] = copy.deepcopy(manifest["entries"][0])
        with self.assertRaisesRegex(ContractError, "duplicate"):
            loader.validate_entries(manifest)

    def test_missing_extra_and_unknown_entries_rejected(self):
        for mutation in (lambda e: e.pop(), lambda e: e.append(dict(e[0])),
                         lambda e: e[0].update(question_id="AQ041", filename="development/AQ041.json")):
            manifest = self._manifest()
            mutation(manifest["entries"])
            with self.assertRaises(ContractError):
                loader.validate_entries(manifest)

    def test_unsafe_paths_rejected(self):
        for path in ("../AQ001.json", "/AQ001.json", "C:/AQ001.json", "C:AQ001.json",
                     "//server/share/AQ001.json", "development/../AQ001.json",
                     "development\\AQ001.json", "development//AQ001.json", "./development/AQ001.json"):
            with self.subTest(path=path):
                manifest = self._manifest()
                manifest["entries"][0]["filename"] = path
                with self.assertRaises(ContractError):
                    loader.validate_entries(manifest)

    def test_non_regular_file_rejected(self):
        with temporary_directory() as root:
            (root/"directory").mkdir()
            with self.assertRaisesRegex(ContractError, "regular file"):
                loader.safe_regular_file(root, "directory")

    def test_link_and_windows_reparse_points_rejected(self):
        for mode, attrs in ((stat.S_IFLNK, 0), (stat.S_IFDIR, stat.FILE_ATTRIBUTE_REPARSE_POINT)):
            info = SimpleNamespace(st_mode=mode, st_file_attributes=attrs)
            with patch.object(loader.Path, "lstat", return_value=info):
                with self.assertRaisesRegex(ContractError, "symlink/reparse"):
                    loader.safe_regular_file(loader.ROOT, "development/AQ001.json")

    def test_strict_json_duplicate_keys_nonfinite_and_encoding(self):
        for data in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'\xff'):
            with self.assertRaises(ContractError):
                loader.strict_json(data)

    def validate(self, item):
        entry = {"question_id": "AQ001", "expected_gate": item["expected_gate"]}
        return loader.validate_record(item, entry, frozenset(IDENTITIES))

    def test_synthetic_valid_record(self):
        self.assertEqual(self.validate(record()).question, "Synthetic structural fixture?")

    def test_wrong_split_rejected(self):
        item = record()
        item["split"] = "NOT_DEVELOPMENT"
        with self.assertRaisesRegex(ContractError, "DEVELOPMENT"):
            self.validate(item)

    def test_unreviewed_rejected(self):
        item = record()
        item["review_status"] = "DRAFT"
        with self.assertRaisesRegex(ContractError, "owner review"):
            self.validate(item)

    def test_empty_allow_gold_rejected(self):
        item = record()
        item["gold_support_sections"] = item["required_support_sections"] = []
        with self.assertRaisesRegex(ContractError, "empty ALLOW"):
            self.validate(item)

    def test_nonempty_abstain_gold_rejected(self):
        item = record()
        item.update(expected_gate=ABSTAIN, reason_code=INSUFFICIENT, support_shape="NOT_APPLICABLE")
        with self.assertRaisesRegex(ContractError, "ABSTAIN support"):
            self.validate(item)

    def test_required_subset_duplicates_and_unknown_identity_rejected(self):
        for field, value in (("required_support_sections", [dict(zip(("policy_id", "version", "section_id"), IDENTITIES[1]))]),
                             ("gold_support_sections", record()["gold_support_sections"] * 2),
                             ("required_support_sections", [{"policy_id": "SOP-99", "version": "1.0-demo", "section_id": "unknown"}])):
            item = record()
            item[field] = value
            with self.assertRaises(ContractError):
                self.validate(item)

    def test_record_schema_shape_reason_and_metadata_types_rejected(self):
        for updates in ({"extra": 1}, {"support_shape": "MULTI_SECTION"}, {"hard_negative": "false"},
                        {"reason_code": INSUFFICIENT}, {"authoring_rationale": ""}):
            item = record()
            item.update(updates)
            with self.assertRaises(ContractError):
                self.validate(item)

    def test_pinned_loader_has_no_redirect_arguments(self):
        with self.assertRaises(TypeError):
            loader.load_development("untrusted-path")


if __name__ == "__main__":
    unittest.main()
