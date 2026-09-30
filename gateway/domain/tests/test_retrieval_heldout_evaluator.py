"""Custody revision tests: synthetic temporary imports and DEVELOPMENT parity only."""
import builtins
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from evaluation.retrieval import evaluate_selected_heldout as h
from evaluation.retrieval import evaluate_development as old
from evaluation.retrieval import retrieval_scoring as scoring
from retrieval import SectionStore
from retrieval.embedding_retriever import EmbeddingResult, EmbeddingSearchResponse

A = ("SOP-02", "1.0-demo", "late-escalate")
B = ("SOP-05", "1.0-demo", "late-evidence")
X = ("SOP-08", "1.0-demo", "decision-record")


def ref(identity):
    return dict(zip(("policy_id", "version", "section_id"), identity))


def synthetic_question(index=0):
    negative = index >= 26
    return dict(question_id=f"SYNTHETIC_{index:03d}", contract_version="1.0", example_only=False,
                split="HELD_OUT", question=f"  Synthetic query {index}; preserve whitespace.  ",
                kind="NEGATIVE" if negative else "ANSWERABLE", negative_reason="OUT_OF_SCOPE" if negative else None,
                gold_policy_version="1.0-demo", gold_sections=[] if negative else [ref(A), ref(B)],
                required_sections=[] if negative else [ref(B)], category="synthetic", difficulty="EASY",
                question_family="synthetic-only", reviewer_rationale="SYNTHETIC PRIVATE RATIONALE")


def response(identities=(A, B, X), abstain=False):
    records = () if abstain else tuple(EmbeddingResult(i, n, 0.8 - n / 100, "synthetic body", "hash", "synthetic.md")
                                       for n, i in enumerate(identities, 1))
    return EmbeddingSearchResponse("ABSTAIN" if abstain else "RETRIEVED", records, 0.1 if abstain else 0.8,
                                  "TOP_SCORE_BELOW_THRESHOLD" if abstain else None)


def offline_runtime():
    runtime = copy.deepcopy(h.load_model_evidence()["runtime"])
    runtime.update(requested_revision=h.REVISION, model_download_occurred=False, weights_downloaded=False, downloaded_files=[])
    return runtime


class FakeRetriever:
    def __init__(self, fail_at=None):
        self.calls = []
        self.fail_at = fail_at
        self.runtime_metadata = offline_runtime()

    def search(self, query, *, top_k):
        self.calls.append((query, top_k))
        if len(self.calls) == self.fail_at:
            raise RuntimeError("SYNTHETIC PRIVATE FAILURE")
        return response()


class HeldoutEvaluatorTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        # Protect every ordinary test against accidental real private-path I/O.
        self.forbidden = (str(h.PRIVATE_INPUT).casefold(), str(h.PRIVATE_OUTPUT).casefold())
        for method in ("open", "iterdir"):
            original = getattr(Path, method)
            def guarded(path, *args, _original=original, **kwargs):
                text = str(path).casefold()
                if any(text == p or text.startswith(p + os.sep) for p in self.forbidden):
                    raise AssertionError("Real private input/output access forbidden in tests")
                return _original(path, *args, **kwargs)
            self.enterContext(patch.object(Path, method, guarded))
        self.enterContext(patch.object(socket, "socket", side_effect=AssertionError("No network in tests")))
        importer = builtins.__import__
        def no_model(name, *args, **kwargs):
            if name.split(".")[0] in ("sentence_transformers", "transformers", "torch", "huggingface_hub"):
                raise AssertionError("Optional model imports forbidden in tests")
            return importer(name, *args, **kwargs)
        self.enterContext(patch.object(builtins, "__import__", no_model))

    def fixture(self, filename_for=None):
        root = self.root / f"synthetic-import-{len(list(self.root.iterdir()))}"
        root.mkdir()
        questions = [synthetic_question(i) for i in range(30)]
        rows = []
        for i, question in enumerate(questions):
            filename = filename_for(i) if filename_for else f"fixture_{i:03d}.json"
            blob = h.json_bytes(question)
            path = root.joinpath(*filename.replace("\\", "/").split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
            rows.append(dict(question_id=question["question_id"], filename=filename, sha256=h.sha256(blob),
                             split="HELD_OUT", kind=question["kind"]))
        digest = h.receipt({r["question_id"]: r["sha256"] for r in rows})
        manifest = dict(split="HELD_OUT", review_status="OWNER_REVIEWED", owner_reviewed=True, dataset_frozen=True,
                        receipt_algorithm="sha256", receipt_serialization=h.SERIALIZATION, aggregate_receipt_sha256=digest,
                        policy_bundle_id="last-mile-exception-triage-demo", policy_version="1.0-demo", contract_version="1.0",
                        question_count=30, answerable_count=26, negative_count=4, questions=rows,
                        source_artifact_manifest_sha256=h.CORPUS_MANIFEST_SHA256)
        (root / h.MANIFEST_NAME).write_bytes(h.json_bytes(manifest))
        return root, h._Protocol(digest)

    def edit_manifest(self, root, change):
        path = root / h.MANIFEST_NAME
        manifest = json.loads(path.read_bytes())
        change(manifest)
        path.write_bytes(h.json_bytes(manifest))

    def reject_before_parse(self, root, protocol, message=None):
        with patch.object(h, "validate_question") as parser:
            with self.assertRaisesRegex(h.HeldoutIntegrityError, message or "."):
                h._load_import(root, protocol)
            parser.assert_not_called()

    def output_paths(self):
        return self.root / "private-results", self.root / "summary.md", self.root / "public-manifest.json"

    def run_fake(self, retriever=None):
        root, protocol = self.fixture()
        data = h._load_import(root, protocol)
        retriever = retriever or FakeRetriever()
        paths = self.output_paths()
        sources = {p: "0" * 64 for p in h.SOURCE_PATHS}
        return data, retriever, sources, paths

    def test_pinned_production_protocol_and_no_loader_arguments(self):
        self.assertEqual(h.EXPECTED_RECEIPT, "57ebb2478204d765ca52dc11792fa36bc25a02f312536e49d2379dd18a348cb0")
        self.assertEqual((h.QUESTION_COUNT, h.ANSWERABLE_COUNT, h.NEGATIVE_COUNT), (30, 26, 4))
        self.assertFalse(inspect.signature(h.load_heldout).parameters)
        with patch.object(h, "_load_import", return_value="sentinel") as loader:
            self.assertEqual(h.load_heldout(), "sentinel")
        loader.assert_called_once_with(h.PRIVATE_INPUT, h._Protocol(h.EXPECTED_RECEIPT, 30, 26, 4))

    def test_synthetic_manifest_directed_import_and_receipt_serialization(self):
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m["questions"].reverse())
        data = h._load_import(root, protocol)
        self.assertEqual(len(data.questions), 30)
        payload = "".join(f"{i}\t{digest}\n" for i, digest in data.question_hashes).encode("utf-8")
        self.assertEqual(h.sha256(payload), protocol.receipt)
        self.assertNotEqual(h.sha256(payload[:-1]), protocol.receipt)
        self.assertEqual(h.receipt(dict(reversed(data.question_hashes))), protocol.receipt)

    def test_production_rejects_synthetic_receipt_without_reading_questions(self):
        root, _ = self.fixture()
        with patch.object(h, "PRIVATE_INPUT", root), patch.object(h, "validate_question") as parser:
            with self.assertRaisesRegex(h.HeldoutIntegrityError, "Frozen receipt"):
                h.load_heldout()
            parser.assert_not_called()

    def test_exactly_thirty_and_kind_counts_required_before_parse(self):
        for key, value in (("question_count", 29), ("question_count", 31), ("answerable_count", 25), ("negative_count", 5)):
            root, protocol = self.fixture()
            self.edit_manifest(root, lambda m: m.update({key: value}))
            with self.subTest(key=key, value=value):
                self.reject_before_parse(root, protocol)
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m["questions"].pop())
        self.reject_before_parse(root, protocol, "exactly 30")

    def test_split_and_review_status_are_required(self):
        for key, value in (("split", "DEVELOPMENT"), ("owner_reviewed", False), ("dataset_frozen", False),
                           ("review_status", "DRAFT"), ("receipt_algorithm", "md5"), ("receipt_serialization", "no LF")):
            root, protocol = self.fixture()
            self.edit_manifest(root, lambda m: m.update({key: value}))
            with self.subTest(key=key):
                self.reject_before_parse(root, protocol)
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m["questions"][-1].update(split="DEVELOPMENT"))
        self.reject_before_parse(root, protocol, "HELD_OUT")

    def test_traversal_absolute_drive_unc_and_alternate_stream_paths_rejected(self):
        for name in ("../outside.json", "a/../../question.json", "a/../question.json", "a\\..\\question.json",
                     "C:/question.json", "C:\\question.json", "C:question.json", "/question.json", "\\question.json",
                     "\\\\server\\share\\question.json", "//server/share/question.json", "\\\\?\\C:\\question.json",
                     "q.json:stream", h.MANIFEST_NAME):
            root, protocol = self.fixture()
            self.edit_manifest(root, lambda m: m["questions"][-1].update(filename=name))
            with self.subTest(name=name):
                self.reject_before_parse(root, protocol)

    def test_nested_manifest_relative_json_paths_accepted(self):
        root, protocol = self.fixture(lambda i: f"synthetic_batch/lane_{i % 3}/fixture_{i:03d}.json")
        data = h._load_import(root, protocol)
        self.assertEqual(len(data.questions), 30)
        self.assertEqual(h.receipt(dict(data.question_hashes)), protocol.receipt)
        path = h.resolve_question_path(root, "synthetic_batch/lane_0/fixture_000.json")
        self.assertEqual(path, (root / "synthetic_batch/lane_0/fixture_000.json").resolve())

    def test_multiple_depths_and_direct_basename_share_one_import(self):
        def filename(i):
            return "synthetic_level/" * (i % 4) + f"fixture_{i:03d}.json"
        root, protocol = self.fixture(filename)
        data = h._load_import(root, protocol)
        self.assertEqual(len(data.questions), 30)
        self.assertTrue((root / "fixture_000.json").is_file())
        self.assertTrue((root / "synthetic_level/synthetic_level/synthetic_level/fixture_003.json").is_file())

    def test_windows_relative_separators_preserve_the_manifest_entry(self):
        root, protocol = self.fixture(lambda i: f"synthetic_batch\\lane\\fixture_{i:03d}.json")
        original = (root / h.MANIFEST_NAME).read_bytes()
        data = h._load_import(root, protocol)
        self.assertEqual(len(data.questions), 30)
        self.assertEqual((root / h.MANIFEST_NAME).read_bytes(), original)
        self.assertEqual(h.resolve_question_path(root, "synthetic_batch\\lane\\fixture_000.json"),
                         (root / "synthetic_batch/lane/fixture_000.json").resolve())

    def test_ambiguous_normalization_invalid_suffix_and_device_names_rejected(self):
        for name in ("", None, 12, "./q.json", "a/./q.json", "a//q.json", "a\\\\q.json", "a/q.json/",
                     "a /q.json", "a./q.json", "q.json ", "q.JSON", "q.txt", ".json", "a\x00/q.json",
                     "NUL.json", "CON/q.json", "a/COM1.json", "a/?q.json", "a/q*.json"):
            with self.subTest(name=name), self.assertRaises(h.HeldoutIntegrityError):
                h._manifest_relative_parts(name)

    def test_resolved_path_escape_rejected_even_after_lexical_validation(self):
        root, _ = self.fixture()
        question = root / "fixture_000.json"
        outside = self.root / "synthetic-outside.json"
        outside.write_bytes(b"synthetic outside sentinel")
        original = Path.resolve
        def redirected(path, *args, **kwargs):
            return outside if path == question else original(path, *args, **kwargs)
        with patch.object(Path, "resolve", redirected), self.assertRaisesRegex(h.HeldoutIntegrityError, "strictly inside"):
            h.resolve_question_path(root, "fixture_000.json")

    def test_duplicate_separator_and_case_aliases_rejected(self):
        root, protocol = self.fixture(lambda i: f"synthetic_batch/lane/fixture_{i:03d}.json")
        for name in ("synthetic_batch\\lane\\fixture_000.json", "SYNTHETIC_BATCH/lane/fixture_000.json"):
            self.edit_manifest(root, lambda m: m["questions"][-1].update(filename=name))
            with self.subTest(name=name):
                self.reject_before_parse(root, protocol, "Duplicate question filename")

    def test_conflicting_directory_spelling_rejected(self):
        root, protocol = self.fixture(lambda i: f"synthetic_batch/fixture_{i:03d}.json")
        self.edit_manifest(root, lambda m: m["questions"][-1].update(filename="SYNTHETIC_BATCH/fixture_029.json"))
        self.reject_before_parse(root, protocol, "Ambiguous path spelling")

    def test_question_path_must_resolve_to_regular_file(self):
        root, protocol = self.fixture()
        question = root / "fixture_000.json"
        question.unlink()
        question.mkdir()
        self.reject_before_parse(root, protocol, "regular file")

    def test_file_directory_path_collision_rejected(self):
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m["questions"][-1].update(filename="fixture_000.json/child.json"))
        self.reject_before_parse(root, protocol, "both a file and a directory")

    def test_duplicate_ids_and_filenames_rejected(self):
        for key in ("question_id", "filename"):
            root, protocol = self.fixture()
            self.edit_manifest(root, lambda m: m["questions"][-1].update({key: m["questions"][0][key]}))
            self.reject_before_parse(root, protocol, "Duplicate")

    def test_inventory_missing_extra_and_subdirectories_rejected(self):
        for kind in ("missing", "extra", "directory"):
            root, protocol = self.fixture()
            if kind == "missing":
                (root / "fixture_000.json").unlink()
            elif kind == "extra":
                (root / "extra.json").write_text("must not parse", encoding="utf-8")
            else:
                (root / "nested").mkdir()
                (root / "nested/secret.json").write_text("synthetic; must not read", encoding="utf-8")
            self.reject_before_parse(root, protocol, "Inventory")

    def test_no_glob_or_recursive_discovery(self):
        root, protocol = self.fixture()
        with patch.object(Path, "glob", side_effect=AssertionError("glob forbidden")), \
             patch.object(Path, "rglob", side_effect=AssertionError("recursion forbidden")):
            self.assertEqual(len(h._load_import(root, protocol).questions), 30)

    def test_inventory_visits_only_manifest_implied_directories(self):
        root, protocol = self.fixture(lambda i: f"synthetic_batch/lane_{i % 2}/fixture_{i:03d}.json")
        authorized = {root, root / "synthetic_batch", root / "synthetic_batch/lane_0", root / "synthetic_batch/lane_1"}
        original, visits = Path.iterdir, []
        def listed(path):
            self.assertIn(path, authorized)
            visits.append(path)
            return original(path)
        with patch.object(Path, "iterdir", listed), patch.object(Path, "glob", side_effect=AssertionError("No discovery")), \
             patch.object(Path, "rglob", side_effect=AssertionError("No recursive discovery")):
            h._load_import(root, protocol)
        self.assertEqual(set(visits), authorized)
        self.assertEqual(len(visits), len(authorized))

    def test_unlisted_nested_entries_rejected_without_opening_or_descending(self):
        for extra_kind in ("file", "directory"):
            root, protocol = self.fixture(lambda i: f"synthetic_batch/lane/fixture_{i:03d}.json")
            extra = root / "synthetic_batch/lane/unlisted"
            if extra_kind == "file":
                extra.write_bytes(b"synthetic unlisted sentinel")
            else:
                extra.mkdir()
                (extra / "unlisted.json").write_bytes(b"synthetic unlisted sentinel")
            original, reads = Path.read_bytes, []
            original_iterdir = Path.iterdir
            def read(path):
                reads.append(path)
                return original(path)
            def listed(path):
                self.assertNotEqual(path, extra)
                return original_iterdir(path)
            with patch.object(Path, "read_bytes", read), patch.object(Path, "iterdir", listed):
                self.reject_before_parse(root, protocol, "Inventory")
            self.assertEqual(reads, [root / h.MANIFEST_NAME])

    def test_missing_listed_file_does_not_use_a_same_basename_elsewhere(self):
        root, protocol = self.fixture(lambda i: f"synthetic_batch/lane/fixture_{i:03d}.json")
        path = root / "synthetic_batch/lane/fixture_000.json"
        # An unlisted alternative is not a recovery mechanism.
        (root / "fixture_000.json").write_bytes(path.read_bytes())
        path.unlink()
        self.reject_before_parse(root, protocol, "Inventory")

    def test_only_manifest_authorized_question_files_are_opened(self):
        root, protocol = self.fixture(lambda i: f"synthetic_batch/lane/fixture_{i:03d}.json")
        manifest = json.loads((root / h.MANIFEST_NAME).read_bytes())
        allowed = {(root / row["filename"]).resolve() for row in manifest["questions"]}
        original, reads = Path.read_bytes, []
        def read(path):
            if path != root / h.MANIFEST_NAME and path != h.DOMAIN / "policy/artifact_manifest.json":
                self.assertIn(path, allowed)
                reads.append(path)
            return original(path)
        with patch.object(Path, "read_bytes", read):
            h._load_import(root, protocol)
        self.assertEqual(set(reads), allowed)
        self.assertEqual(len(reads), 30)

    def test_synthetic_import_preserves_manifest_structure_bytes_and_receipt(self):
        source, protocol = self.fixture(lambda i: f"synthetic_batch/lane_{i % 2}/fixture_{i:03d}.json")
        imported = self.root / "synthetic-import-copy"
        imported.mkdir()
        manifest_blob = (source / h.MANIFEST_NAME).read_bytes()
        manifest = json.loads(manifest_blob)
        (imported / h.MANIFEST_NAME).write_bytes(manifest_blob)
        for row in manifest["questions"]:
            destination = imported / row["filename"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            blob = (source / row["filename"]).read_bytes()
            destination.write_bytes(blob)
            self.assertEqual(destination.read_bytes(), blob)
        data = h._load_import(imported, protocol)
        self.assertEqual((imported / h.MANIFEST_NAME).read_bytes(), manifest_blob)
        self.assertEqual(data.manifest_sha256, h.sha256(manifest_blob))
        self.assertEqual(data.receipt, protocol.receipt)
        self.assertEqual(dict(data.question_hashes), {row["question_id"]: row["sha256"] for row in manifest["questions"]})

    def test_path_layout_does_not_change_receipt_semantics(self):
        flat, flat_protocol = self.fixture()
        nested, nested_protocol = self.fixture(lambda i: f"synthetic_batch/lane/fixture_{i:03d}.json")
        before, after = h._load_import(flat, flat_protocol), h._load_import(nested, nested_protocol)
        self.assertEqual(before.receipt, after.receipt)
        self.assertEqual(before.questions, after.questions)
        self.assertEqual(before.question_hashes, after.question_hashes)
        self.assertNotEqual(before.manifest_sha256, after.manifest_sha256)

    def test_nested_file_and_directory_symlinks_rejected_before_question_read(self):
        for target_kind in ("file", "directory"):
            for mode in ("symlink", "junction"):
                root, protocol = self.fixture(lambda i: f"synthetic_batch/lane/fixture_{i:03d}.json")
                target = root / ("synthetic_batch/lane/fixture_000.json" if target_kind == "file" else "synthetic_batch/lane")
                original, original_read, reads = Path.lstat, Path.read_bytes, []
                def fake_lstat(path):
                    if path == target:
                        return SimpleNamespace(st_mode=stat.S_IFLNK if mode == "symlink" else stat.S_IFDIR,
                                               st_file_attributes=0x400 if mode == "junction" else 0)
                    return original(path)
                def read(path):
                    reads.append(path)
                    return original_read(path)
                with self.subTest(target=target_kind, mode=mode), patch.object(Path, "lstat", fake_lstat), \
                     patch.object(Path, "read_bytes", read):
                    self.reject_before_parse(root, protocol, "Links/reparse")
                self.assertEqual(reads, [root / h.MANIFEST_NAME])

    def test_symlinks_and_windows_reparse_points_rejected(self):
        for target_kind in ("root", "manifest", "question", "ancestor"):
            for mode in ("symlink", "junction"):
                root, protocol = self.fixture()
                target = {"root": root, "manifest": root / h.MANIFEST_NAME,
                          "question": root / "fixture_000.json", "ancestor": root.parent}[target_kind]
                original = Path.lstat
                def fake_lstat(path):
                    if path == target:
                        return SimpleNamespace(st_mode=stat.S_IFLNK if mode == "symlink" else stat.S_IFDIR,
                                               st_file_attributes=0x400 if mode == "junction" else 0)
                    return original(path)
                with self.subTest(target=target_kind, mode=mode), patch.object(Path, "lstat", fake_lstat):
                    self.reject_before_parse(root, protocol, "Links/reparse")

    def test_all_hashes_verified_before_any_question_parse(self):
        root, protocol = self.fixture()
        path = root / "fixture_029.json"
        path.write_bytes(b"not even valid JSON")
        with patch.object(h, "read_json_bytes", wraps=h.read_json_bytes) as parse:
            self.reject_before_parse(root, protocol, "file hash differs")
            self.assertEqual(parse.call_count, 1)  # Manifest only, no question.

    def test_changed_manifest_hash_cannot_bypass_frozen_receipt(self):
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m["questions"][-1].update(sha256="0" * 64))
        self.reject_before_parse(root, protocol, "aggregate receipt")
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m.update(aggregate_receipt_sha256="0" * 64))
        self.reject_before_parse(root, protocol, "Frozen receipt")

    def test_non_lowercase_hash_and_duplicate_json_key_rejected(self):
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m["questions"][0].update(sha256="A" * 64))
        self.reject_before_parse(root, protocol, "SHA-256")
        with self.assertRaisesRegex(h.HeldoutIntegrityError, "Duplicate"):
            h.read_json_bytes(b'{"split":"HELD_OUT","split":"HELD_OUT"}')
        with self.assertRaises(h.HeldoutIntegrityError):
            h.read_json_bytes(b'{"value":NaN}')

    def test_frozen_corpus_manifest_required(self):
        root, protocol = self.fixture()
        self.edit_manifest(root, lambda m: m.update(source_artifact_manifest_sha256="0" * 64))
        self.reject_before_parse(root, protocol, "corpus manifest")

    def test_question_identity_kind_split_and_labels_validated_after_hashes(self):
        for key, value in (("question_id", "DIFFERENT"), ("kind", "NEGATIVE"), ("split", "DEVELOPMENT"),
                           ("required_sections", []), ("gold_policy_version", "wrong")):
            root, _ = self.fixture()
            path = root / "fixture_000.json"
            q = json.loads(path.read_bytes())
            q[key] = value
            path.write_bytes(h.json_bytes(q))
            def update(m):
                m["questions"][0]["sha256"] = h.sha256(path.read_bytes())
                m["aggregate_receipt_sha256"] = h.receipt({r["question_id"]: r["sha256"] for r in m["questions"]})
            self.edit_manifest(root, update)
            protocol = h._Protocol(json.loads((root / h.MANIFEST_NAME).read_bytes())["aggregate_receipt_sha256"])
            with self.subTest(key=key), self.assertRaises(ValueError):
                h._load_import(root, protocol)

    def test_frozen_development_full_row_aggregate_and_failure_parity(self):
        development = old.load_development()  # Sole use of Development questions: parity.
        identities = tuple(s.identity for s in SectionStore.load().sections)
        for mode in ("rotating", "abstain", "reversed"):
            class DeterministicFake:
                def search(self, query, *, top_k):
                    self_test.assertEqual(top_k, 10)
                    offset = int(hashlib.sha256(query.encode()).hexdigest()[:4], 16) % len(identities)
                    ordered = identities[offset:] + identities[:offset]
                    if mode == "reversed":
                        ordered = tuple(reversed(ordered))
                    return response((ordered[0],) + ordered, abstain=mode == "abstain")
            self_test = self
            before = old.evaluate(development, DeterministicFake())
            rows = [scoring.score_question(q, DeterministicFake().search(q["question"], top_k=10)) for q in development.questions]
            after = h.private_result(rows)
            with self.subTest(mode=mode):
                self.assertEqual(after["questions"], before["questions"])
                self.assertEqual(after["metrics"], before["metrics"])
                self.assertEqual(after["failures"], before["failures"])

    def test_gold_relevance_is_separate_from_required_coverage(self):
        q = synthetic_question()
        row = scoring.score_question(q, response((A, A, X, B)))
        self.assertTrue(row["hit_at_1"])
        self.assertEqual(row["required_coverage_at_k"]["1"]["fraction"], 0)
        self.assertEqual(row["required_coverage_at_k"]["3"]["fraction"], 1)
        self.assertEqual([r["rank"] for r in row["ranked_sections"]], [1, 2, 3])
        q["split"] = "DEVELOPMENT"
        self.assertEqual(row, old.score_question(q, response((A, A, X, B))))

    def test_multi_required_denominator_and_maximum_unique_depth(self):
        q = synthetic_question()
        q["required_sections"] = [ref(A), ref(B)]
        row = scoring.score_question(q, response((A, X, B)))
        self.assertEqual(row["required_coverage_at_k"]["1"]["fraction"], 0.5)
        self.assertEqual(scoring.aggregate_metrics([row])["full_required_set_success_at_k"]["3"],
                         dict(count=1, total=1, rate=1))
        many = tuple(("SYNTHETIC", "v", str(i)) for i in range(11))
        self.assertEqual(len(scoring.score_question(q, response(many))["ranked_sections"]), 10)

    def test_query_only_calls_original_text_top_ten_and_one_attempt(self):
        data, retriever, sources, paths = self.run_fake()
        h._run(data, retriever, sources, *paths)
        self.assertEqual(retriever.calls, [(q["question"], 10) for q in data.questions])
        state = json.loads((paths[0] / "RUN_MANIFEST_PRIVATE.json").read_bytes())
        self.assertEqual((state["baseline_run_sequence"], state["completed_evaluation_attempts"],
                          state["success_count"], state["error_count"]), (1, 1, 30, 0))
        self.assertTrue(all(v == dict(attempts=1, status="SUCCESS") for v in state["question_attempts"].values()))

    def test_labels_are_only_scored_after_retrieval_response(self):
        data, retriever, sources, paths = self.run_fake()
        flag = {"returned": False}
        class GuardedQuestion(dict):
            def __getitem__(self, key):
                if key in ("kind", "gold_sections", "required_sections", "reviewer_rationale"):
                    self_test.assertTrue(flag["returned"])
                return super().__getitem__(key)
        self_test = self
        data = h.HeldoutSet(tuple(GuardedQuestion(q) for q in data.questions), data.receipt, data.manifest_sha256, data.question_hashes)
        original_search = retriever.search
        original_score = h.score_question
        def search(query, *, top_k):
            flag["returned"] = True
            return original_search(query, top_k=top_k)
        def score(q, r):
            result = original_score(q, r)
            flag["returned"] = False
            return result
        with patch.object(retriever, "search", search), patch.object(h, "score_question", score):
            h._run(data, retriever, sources, *paths)

    def test_exact_revision_and_local_only_factory_without_real_model(self):
        backend = SimpleNamespace(metadata=offline_runtime())
        fake = SimpleNamespace(embedding_dimension=384)
        with patch.object(h, "SentenceTransformerBackend", return_value=backend) as factory, \
             patch.object(h, "EmbeddingRetriever", return_value=fake) as constructor:
            self.assertIs(h.create_selected_retriever(), fake)
        factory.assert_called_once_with(revision="5c38ec7c405ec4b44b94cc5a9bb96e735b38267a", local_files_only=True)
        self.assertIs(constructor.call_args.kwargs["encoder"], backend)

    def test_wrong_revision_and_model_file_hash_stop_before_encoding(self):
        for field in ("resolved_model_revision", "requested_revision", "model_file_sha256"):
            runtime = offline_runtime()
            runtime[field] = {"model.safetensors": "0" * 64} if field == "model_file_sha256" else "main"
            with self.subTest(field=field), patch.object(h, "SentenceTransformerBackend", return_value=SimpleNamespace(metadata=runtime)), \
                 patch.object(h, "EmbeddingRetriever") as encode, \
                 self.assertRaisesRegex(h.HeldoutIntegrityError, "Model-file hashes" if field == "model_file_sha256" else "model revision"):
                h.create_selected_retriever()
            encode.assert_not_called()

    def test_wrong_device_dimension_prefix_or_download_rejected(self):
        expected = h.load_model_evidence()["runtime"]
        for field, value in (("device", "cuda"), ("embedding_dimension", 768), ("query_instruction", "prefix"),
                             ("model_download_occurred", True), ("weights_downloaded", True), ("downloaded_files", ["config.json"])):
            runtime = offline_runtime()
            runtime[field] = value
            with self.subTest(field=field), self.assertRaises(h.HeldoutIntegrityError):
                h.validate_runtime(runtime, expected)

    def test_missing_cache_does_not_fallback_or_download(self):
        with patch.object(h, "SentenceTransformerBackend", side_effect=RuntimeError("missing cache")) as factory, \
             patch.object(h, "EmbeddingRetriever") as encode, self.assertRaisesRegex(RuntimeError, "missing cache"):
            h.create_selected_retriever()
        self.assertEqual(factory.call_count, 1)
        encode.assert_not_called()

    def test_existing_outputs_refuse_before_model_or_private_input_read(self):
        paths = self.output_paths()
        for index in range(3):
            path = paths[index]
            if index == 0:
                path.mkdir()
            else:
                path.write_text("preexisting", encoding="utf-8")
            with self.subTest(index=index), patch.object(h, "PRIVATE_OUTPUT", paths[0]), \
                 patch.object(h, "PUBLIC_SUMMARY", paths[1]), patch.object(h, "PUBLIC_MANIFEST", paths[2]), \
                 patch.object(sys, "argv", ["harness"]), patch.object(h, "create_selected_retriever") as model, \
                 patch.object(h, "load_heldout") as loader, self.assertRaisesRegex(h.HeldoutIntegrityError, "existing"):
                h.main()
            model.assert_not_called()
            loader.assert_not_called()
            path.rmdir() if index == 0 else path.unlink()

    def test_no_cli_overrides(self):
        for option in ("--input", "--split", "--model", "--threshold", "--top-k"):
            with patch.object(sys, "argv", ["harness", option, "value"]), \
                 patch.object(h, "load_heldout") as loader, patch.object(h, "create_selected_retriever") as model, self.assertRaises(SystemExit):
                h.main()
            loader.assert_not_called()
            model.assert_not_called()

    def test_pre_search_infrastructure_failure_creates_no_attempt(self):
        paths = self.output_paths()
        with patch.object(h, "PRIVATE_OUTPUT", paths[0]), patch.object(h, "PUBLIC_SUMMARY", paths[1]), \
             patch.object(h, "PUBLIC_MANIFEST", paths[2]), patch.object(sys, "argv", ["harness"]), \
             patch.object(h, "verify_source_freeze", return_value={}), \
             patch.object(h, "create_selected_retriever", side_effect=RuntimeError("cache unavailable")), \
             patch.object(h, "load_heldout") as loader, self.assertRaises(RuntimeError):
            h.main()
        loader.assert_not_called()
        self.assertTrue(all(not p.exists() for p in paths))

    def test_mid_run_failure_is_journaled_and_cannot_restart(self):
        data, retriever, sources, paths = self.run_fake(FakeRetriever(fail_at=2))
        with self.assertRaises(RuntimeError):
            h._run(data, retriever, sources, *paths)
        state = json.loads((paths[0] / "RUN_MANIFEST_PRIVATE.json").read_bytes())
        self.assertEqual((state["success_count"], state["error_count"], state["retrieval_results_produced"],
                          state["completed_evaluation_attempts"], state["result_bearing_evaluation_attempts"]), (1, 1, 1, 0, 1))
        self.assertEqual(sum(v["attempts"] for v in state["question_attempts"].values()), 2)
        self.assertFalse(paths[1].exists() or paths[2].exists())
        with self.assertRaisesRegex(h.HeldoutIntegrityError, "existing"):
            h._run(data, retriever, sources, *paths)
        self.assertEqual(len(retriever.calls), 2)

    def test_search_is_durably_recorded_before_call_and_response_before_scoring(self):
        data, retriever, sources, paths = self.run_fake()
        journal = paths[0] / "RUN_MANIFEST_PRIVATE.json"
        def search(query, *, top_k):
            state = json.loads(journal.read_bytes())
            self.assertEqual(state["question_attempts"][data.questions[0]["question_id"]], dict(attempts=1, status="SEARCHING"))
            return response()
        def bad_score(q, r):
            state = json.loads(journal.read_bytes())
            self.assertEqual(state["retrieval_results_produced"], 1)
            self.assertIn(q["question_id"], state["private_retrieval_responses"])
            raise ValueError("synthetic scorer interruption")
        with patch.object(retriever, "search", search), patch.object(h, "score_question", bad_score), self.assertRaises(ValueError):
            h._run(data, retriever, sources, *paths)
        state = json.loads(journal.read_bytes())
        self.assertEqual(state["result_bearing_evaluation_attempts"], 1)
        self.assertEqual(state["error_count"], 1)

    def test_publication_failure_preserves_completed_evaluation_and_blocks_retry(self):
        data, retriever, sources, paths = self.run_fake()
        with patch.object(h, "public_summary", side_effect=OSError("publication failed")), self.assertRaises(OSError):
            h._run(data, retriever, sources, *paths)
        state = json.loads((paths[0] / "RUN_MANIFEST_PRIVATE.json").read_bytes())
        self.assertEqual((state["completed_evaluation_attempts"], state["success_count"], state["error_count"]), (1, 30, 0))
        self.assertEqual(state["status"], "ERROR")
        self.assertTrue((paths[0] / "HELDOUT_RESULTS.json").is_file())
        with self.assertRaises(h.HeldoutIntegrityError):
            h._run(data, retriever, sources, *paths)

    def test_public_and_private_serializers_are_separate_and_public_is_allowlisted(self):
        data, retriever, sources, paths = self.run_fake()
        public = h._run(data, retriever, sources, *paths)
        private = json.loads((paths[0] / "HELDOUT_RESULTS.json").read_bytes())
        self.assertEqual(private["questions"][0]["query"], data.questions[0]["question"])
        self.assertTrue(private["questions"][0]["gold_sections"])
        private["metrics"]["question"] = "PRIVATE INJECTION"
        private["metrics"]["hit_at_1"]["gold_sections"] = "PRIVATE INJECTION"
        private["metrics"]["required_coverage_at_k"]["1"]["micro"]["rationale"] = "PRIVATE INJECTION"
        public_blob = h.json_bytes(public) + h.public_summary(private, public)
        for needle in ("PRIVATE INJECTION", "SYNTHETIC_000", "Synthetic query", "SYNTHETIC PRIVATE RATIONALE", str(paths[0]),
                       '"gold_sections"', '"required_sections"', '"reviewer_rationale"', "late-escalate"):
            self.assertNotIn(needle.encode(), public_blob)
        self.assertEqual(set(p.name for p in paths[0].iterdir()),
                         {"HELDOUT_RESULTS.json", "HELDOUT_REPORT_PRIVATE.md", "RUN_MANIFEST_PRIVATE.json"})
        hashes = {name: h.sha256((paths[0] / name).read_bytes()) for name in ("HELDOUT_RESULTS.json", "HELDOUT_REPORT_PRIVATE.md")}
        self.assertEqual(public["aggregate_output_sha256"], h.receipt(hashes))

    def test_public_serializer_rejects_private_text_in_numeric_metric(self):
        result = h.private_result([scoring.score_question(synthetic_question(), response())])
        result["metrics"]["hit_at_1"]["count"] = "SYNTHETIC PRIVATE TEXT"
        with self.assertRaises(h.HeldoutIntegrityError):
            h.public_metrics(result["metrics"])

    def test_import_in_fresh_process_has_no_model_network_or_private_io(self):
        code = r'''
import builtins, pathlib, socket, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('sentence_transformers', 'transformers', 'torch', 'huggingface_hub'):
        raise AssertionError('Model import')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
def audit(event, args):
    if event in ('open', 'os.listdir', 'os.scandir'):
        value = str(args[0]).replace('\\', '/').lower()
        if '/private_heldout' in value or '/retrieval_heldout_bge_v0_private' in value:
            raise AssertionError('Private I/O')
    if event.startswith('socket.'):
        raise AssertionError('Network')
sys.addaudithook(audit)
from evaluation.retrieval import evaluate_selected_heldout
assert 'sentence_transformers' not in sys.modules
print('import safe')
'''
        env = dict(os.environ, PYTHONPATH=str(DOMAIN), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-B", "-c", code], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "import safe")

    def test_frozen_dependencies_and_tags_verify_without_model_or_private_io(self):
        sources = h.verify_source_freeze()
        self.assertEqual(set(sources), set(h.SOURCE_PATHS))
        self.assertTrue(all(len(value) == 64 for value in sources.values()))


if __name__ == "__main__":
    unittest.main()
