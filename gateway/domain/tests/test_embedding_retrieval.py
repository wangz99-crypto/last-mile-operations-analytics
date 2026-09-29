"""Offline embedding contract tests: fake vectors, no optional runtime or weights."""
import builtins
from dataclasses import FrozenInstanceError, asdict, replace
import math
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from retrieval import LexicalRetriever, SectionStore, retrieve_required_sections
from retrieval.embedding_retriever import (
    EmbeddingDependencyError, EmbeddingRetriever, EmbeddingVectorError,
    SentenceTransformerBackend, configuration,
)


class FakeEncoder:
    def __init__(self, matrix=None, query=(1.0, 0.0)):
        self.matrix = matrix if matrix is not None else [(1.0, 0.0)] * 25
        self.query = query
        self.calls = []

    def encode(self, texts):
        self.calls.append(tuple(texts))
        return self.matrix if len(texts) == 25 else [self.query]


class EmbeddingRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = SectionStore.load()
        cls.sections = tuple(sorted(cls.store.sections, key=lambda s: s.identity))

    def retriever(self, **kwargs):
        self.encoder = FakeEncoder(**kwargs)
        return EmbeddingRetriever(self.store, encoder=self.encoder)

    def test_exactly_25_identities_indexed_once(self):
        r = self.retriever()
        self.assertEqual((r.section_count, r.embedding_dimension), (25, 2))
        self.assertEqual(len(self.encoder.calls), 1)
        for query in ("first", "second"):
            results = r.search(query, top_k=100).results
            self.assertEqual([x.identity for x in results], [s.identity for s in self.sections])
        self.assertEqual([len(call) for call in self.encoder.calls], [25, 1, 1])

    def test_searchable_text_is_exact_three_field_join(self):
        self.retriever()
        self.assertEqual(self.encoder.calls[0], tuple(s.title + "\n" + s.section_title + "\n" + s.text for s in self.sections))

    def test_metadata_does_not_enter_encoder_input(self):
        changed = [replace(s, policy_id="META", section_id=f"meta-{i:02d}", rule_ids=("RULESECRET",),
                           requirement_ids=("REQSECRET",), source_path="SECRETFILE", exception_types=("SECRETCLASS",))
                   for i, s in enumerate(self.sections)]
        encoder = FakeEncoder()
        EmbeddingRetriever(SectionStore({s.identity: s for s in changed}), encoder=encoder)
        self.assertEqual(encoder.calls[0], tuple(s.title + "\n" + s.section_title + "\n" + s.text for s in self.sections))

    def test_canonical_order_independent_of_store_order(self):
        a, b = FakeEncoder(), FakeEncoder()
        forward = EmbeddingRetriever(self.store, encoder=a)
        reverse = EmbeddingRetriever(SectionStore({s.identity: s for s in reversed(self.sections)}), encoder=b)
        self.assertEqual(a.calls, b.calls)
        self.assertEqual(forward.search("query"), reverse.search("query"))

    def test_normalized_cosine_not_vector_magnitude(self):
        r = self.retriever(matrix=[(0, 5), (3, 4), (2, 0)] + [(-1, 0)] * 22, query=(7, 0))
        results = r.search("query").results
        self.assertEqual([x.identity for x in results[:3]], [self.sections[i].identity for i in (2, 1, 0)])
        self.assertEqual([x.score for x in results[:3]], [1.0, 0.6, 0.0])

    def test_ties_are_canonical_and_scores_are_not_rounded(self):
        r = self.retriever()
        self.assertEqual([x.identity for x in r.search("query").results], [s.identity for s in self.sections[:10]])
        r = self.retriever(matrix=[(0.4, math.sqrt(0.84)), (0.400000000001, math.sqrt(1 - 0.400000000001 ** 2))] + [(0, 1)] * 23)
        self.assertEqual(r.search("query").results[0].identity, self.sections[1].identity)

    def test_repeated_search_identical(self):
        r = self.retriever()
        self.assertEqual(r.search("unaltered query"), r.search("unaltered query"))

    def test_original_query_including_whitespace_passed_directly(self):
        r = self.retriever()
        query = "  ORIGINAL Query?!\n"
        r.search(query)
        self.assertEqual(self.encoder.calls[-1], (query,))

    def test_real_encode_explicitly_disables_default_prompts(self):
        backend = object.__new__(SentenceTransformerBackend)
        backend._model = Mock()
        backend.encode((" original ",))
        backend._model.encode.assert_called_once_with([" original "], device="cpu", normalize_embeddings=True,
            prompt="", batch_size=32, precision="float32", convert_to_numpy=True, show_progress_bar=False)

    def test_top_k_behavior(self):
        r = self.retriever()
        all_results = r.search("query", top_k=100).results
        for k in (1, 3, 5, 10, 25, 100):
            self.assertEqual(r.search("query", top_k=k).results, all_results[:k])
        for k in (0, -1, True, 1.5, None):
            with self.subTest(k=k), self.assertRaises(ValueError):
                r.search("query", top_k=k)
        with self.assertRaises(TypeError):
            r.search(None)

    def test_blank_query_abstains_without_encoding(self):
        r = self.retriever()
        for query in ("", " \t\r\n"):
            response = r.search(query)
            self.assertTrue(response.abstained)
            self.assertEqual((response.results, response.top_score, response.abstention_reason), ((), 0.0, "EMPTY_QUERY"))
        self.assertEqual(len(self.encoder.calls), 1)

    def test_below_threshold_abstains(self):
        for value in (-1.0, 0.0, 0.299999):
            r = self.retriever(query=(value, math.sqrt(1 - value ** 2)))
            response = r.search("synthetic query")
            self.assertTrue(response.abstained)
            self.assertEqual(response.results, ())
            self.assertEqual(response.abstention_reason, "TOP_SCORE_BELOW_THRESHOLD")

    def test_threshold_equality_accepted_without_margin(self):
        r = self.retriever(query=(0.30, math.sqrt(0.91)))
        response = r.search("synthetic query")
        self.assertEqual(response.top_score, 0.30)
        self.assertFalse(response.abstained)
        self.assertIsNone(response.abstention_reason)

    def test_frozen_records_have_canonical_metadata_not_business_fields(self):
        response = self.retriever().search("query")
        for rank, (record, section) in enumerate(zip(response.results, self.sections), 1):
            self.assertEqual((record.identity, record.rank, record.text, record.content_hash, record.source_path),
                             (section.identity, rank, section.text, section.content_hash, section.source_path))
            self.assertEqual(record.retrieval_method, "EMBEDDING_COSINE")
            self.assertEqual(set(asdict(record)), {"identity", "rank", "score", "text", "content_hash", "source_path", "retrieval_method"})
            with self.assertRaises(FrozenInstanceError):
                record.score = 0
        with self.assertRaises(FrozenInstanceError):
            response.status = "ABSTAIN"

    def test_invalid_section_matrices_fail_clearly(self):
        for matrix in (None, [], [(1, 0)] * 24, [(1, 0)] * 26, [1] * 25, [()] * 25,
                       [(0, 0)] * 25, [(float("nan"), 1)] * 25, [(float("inf"), 1)] * 25,
                       [("bad", 1)] * 25, [(True, 1)] * 25, [(1j, 1)] * 25, [(10 ** 400, 1)] * 25,
                       [(1, 0)] * 24 + [(1, 0, 0)]):
            with self.subTest(matrix=repr(matrix)[:50]), self.assertRaises(EmbeddingVectorError):
                self.retriever(matrix=matrix) if matrix is not None else EmbeddingRetriever(self.store, encoder=Mock(encode=Mock(return_value=None)))

    def test_invalid_query_vectors_fail_clearly(self):
        for query in ((), (0, 0), (1,), (1, 2, 3), (float("nan"), 1), (float("inf"), 1), ("bad", 1)):
            with self.subTest(query=query), self.assertRaises(EmbeddingVectorError):
                self.retriever(query=query).search("valid text")

    def test_query_matrix_row_count_validated(self):
        r = self.retriever()
        self.encoder.encode = Mock(return_value=[(1, 0), (0, 1)])
        with self.assertRaisesRegex(EmbeddingVectorError, "Expected 1 embedding rows"):
            r.search("query")

    def test_single_version_and_25_section_requirement_before_model_load(self):
        mixed = [replace(self.sections[0], version="other")] + list(self.sections[1:])
        for sections in ([], self.sections[:24], mixed):
            with patch("retrieval.embedding_retriever.SentenceTransformerBackend") as backend:
                with self.assertRaises(ValueError):
                    EmbeddingRetriever(SectionStore({s.identity: s for s in sections}))
                backend.assert_not_called()

    def test_duplicate_section_identity_rejected(self):
        malformed = SectionStore({i: self.sections[0] for i in range(25)})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            EmbeddingRetriever(malformed, encoder=FakeEncoder())

    def test_missing_optional_dependency_only_fails_when_explicitly_requested(self):
        original = builtins.__import__
        def guarded(name, *args, **kwargs):
            if name == "sentence_transformers":
                raise ImportError("synthetic missing optional package")
            return original(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=guarded):
            self.assertTrue(self.retriever().search("query").results)
            with self.assertRaisesRegex(EmbeddingDependencyError, "requirements-embeddings.txt"):
                SentenceTransformerBackend()

    def test_exact_lookup_and_bm25_unchanged(self):
        query = "qualifying physical scan complete history stale escalation"
        refs = [self.sections[0].identity]
        before = tuple(asdict(s) for s in self.store.sections)
        exact = retrieve_required_sections(refs, store=self.store)
        lexical = LexicalRetriever(self.store).search(query)
        self.retriever().search(query)
        self.assertEqual(retrieve_required_sections(refs, store=self.store), exact)
        self.assertEqual(LexicalRetriever(self.store).search(query), lexical)
        self.assertEqual(tuple(asdict(s) for s in self.store.sections), before)

    def test_configuration_and_injected_metadata_are_not_model_claims(self):
        config = configuration()
        self.assertEqual((config["model_id"], config["device"], config["top_k"], config["abstention"]["minimum_top_score"]),
                         ("BAAI/bge-small-en-v1.5", "cpu", 10, 0.30))
        self.assertEqual(config["query_instruction"], "")
        config["abstention"]["minimum_top_score"] = 99
        self.assertEqual(configuration()["abstention"]["minimum_top_score"], 0.30)
        r = self.retriever()
        self.assertEqual(r.runtime_metadata, {"backend": "injected; no real model identity claimed"})

    def test_isolated_import_and_fake_backend_need_only_stdlib_no_network(self):
        code = r'''
import builtins, sys
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guarded(name, globals=None, locals=None, fromlist=(), level=0):
    if not level and name.split('.')[0] not in sys.stdlib_module_names | {'retrieval'}:
        raise AssertionError('Forbidden dependency: ' + name)
    return original(name, globals, locals, fromlist, level)
builtins.__import__ = guarded
def audit(event, args):
    if event.startswith('socket.') or event == 'subprocess.Popen':
        raise AssertionError('Network and subprocess forbidden')
    if event == 'open' and isinstance(args[0], str):
        path = args[0].replace('\\', '/')
        if any(part in path for part in ('/evaluation/', '/examples/', '/artifacts/', '/kb/', '/.cache/')):
            raise AssertionError('Forbidden non-runtime input')
sys.addaudithook(audit)
import retrieval
from retrieval.embedding_retriever import EmbeddingRetriever
assert not any(x in sys.modules for x in ('sentence_transformers', 'torch', 'numpy', 'engine'))
class Encoder:
    def encode(self, texts):
        return [(1.0, 0.0)] * len(texts)
r = EmbeddingRetriever(retrieval.SectionStore.load(), encoder=Encoder())
assert r.section_count == 25 and len(r.search('synthetic query').results) == 10
assert not any(x in sys.modules for x in ('sentence_transformers', 'torch', 'numpy', 'engine'))
print('OK')
'''
        result = subprocess.run([sys.executable, "-I", "-B", "-S", "-c", code, str(DOMAIN)], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), "OK")


if __name__ == "__main__":
    unittest.main()
