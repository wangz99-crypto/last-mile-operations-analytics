"""RRF contract checks with deterministic component doubles; no ML runtime."""
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
import subprocess
import sys
import unittest

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from retrieval import LexicalResult, LexicalSearchResponse, LexicalRetriever, SectionStore, retrieve_required_sections
from retrieval.hybrid_rrf_retriever import HybridIntegrityError, HybridRRFRetriever, configuration


class FakeComponent:
    def __init__(self, store, positions=(), scores=None):
        self._sections = tuple(sorted(store.sections, key=lambda s: s.identity))
        self.calls = []
        records = []
        for rank, position in enumerate(positions, 1):
            s = self._sections[position]
            records.append(LexicalResult(s.identity, rank, scores[rank - 1] if scores else 1.0,
                                        s.text, s.content_hash, s.source_path))
        self.response = LexicalSearchResponse("RETRIEVED" if records else "ABSTAIN", tuple(records), 1.0 if records else 0.0,
                                              None if records else "FAKE_COMPONENT_ABSTENTION")

    def search(self, query, top_k):
        self.calls.append((query, top_k))
        return self.response


class HybridRRFRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = SectionStore.load()
        cls.sections = tuple(sorted(cls.store.sections, key=lambda s: s.identity))

    def hybrid(self, left=(0, 1), right=(1, 2), left_scores=None, right_scores=None):
        self.left = FakeComponent(self.store, left, left_scores)
        self.right = FakeComponent(self.store, right, right_scores)
        return HybridRRFRetriever(self.left, self.right)

    def test_fixed_k_equal_weights_formula_and_shared_contribution(self):
        r = self.hybrid().search("query")
        values = {x.identity: x for x in r.results}
        self.assertEqual(values[self.sections[1].identity].score, 1 / 62 + 1 / 61)
        self.assertEqual(values[self.sections[0].identity].score, 1 / 61)
        self.assertEqual(values[self.sections[2].identity].score, 1 / 62)
        self.assertEqual(r.results[0].identity, self.sections[1].identity)
        cfg = configuration()
        self.assertEqual((cfg["rrf_k"], cfg["bm25_weight"], cfg["embedding_weight"]), (60, 1.0, 1.0))
        cfg["rrf_k"] = 99
        self.assertEqual(configuration()["rrf_k"], 60)

    def test_raw_scores_do_not_change_fusion(self):
        normal = self.hybrid().search("query")
        unusual = self.hybrid(left_scores=(float("nan"), -1e100), right_scores=(1e200, float("inf"))).search("query")
        self.assertEqual(normal, unusual)

    def test_raw_scores_are_not_even_read(self):
        r = self.hybrid()
        class RankOnlyRecord:
            def __init__(self, source):
                self.identity, self.text, self.content_hash, self.source_path = source.identity, source.text, source.content_hash, source.source_path
            @property
            def score(self):
                raise AssertionError("Raw scores must not be read")
        self.left.response = replace(self.left.response, results=tuple(RankOnlyRecord(x) for x in self.left.response.results))
        self.assertTrue(r.search("query").results)

    def test_canonical_tie_breaking(self):
        response = self.hybrid(left=(1, 0), right=(0, 1)).search("query")
        self.assertEqual(response.results[0].score, response.results[1].score)
        self.assertEqual([r.identity for r in response.results], [s.identity for s in self.sections[:2]])

    def test_no_rounding_before_ordering(self):
        response = self.hybrid(left=tuple(range(9, -1, -1)), right=()).search("query")
        self.assertEqual([r.identity for r in response.results], [self.sections[i].identity for i in range(9, -1, -1)])
        self.assertEqual(response.results[8].score, 1 / 69)
        self.assertEqual(response.results[9].score, 1 / 70)
        self.assertEqual(round(response.results[8].score, 2), round(response.results[9].score, 2))

    def test_final_depth_uses_union_without_padding(self):
        r = self.hybrid(left=tuple(range(10)), right=tuple(range(10, 20)))
        all_results = r.search("query", top_k=100).results
        self.assertEqual(len(all_results), 20)
        for k in (1, 3, 5, 10, 15, 100):
            self.assertEqual(r.search("query", top_k=k).results, all_results[:k])
        self.assertTrue(all(depth == 10 for _, depth in self.left.calls + self.right.calls))

    def test_original_query_unchanged_and_depth_ten_to_both(self):
        query = "  Original Query?!\n"
        self.hybrid().search(query, top_k=1)
        self.assertEqual(self.left.calls, [(query, 10)])
        self.assertEqual(self.right.calls, [(query, 10)])

    def test_invalid_query_and_top_k_fail_before_components(self):
        r = self.hybrid()
        for k in (0, -1, True, 1.2, None):
            with self.assertRaises(ValueError):
                r.search("query", top_k=k)
        with self.assertRaises(TypeError):
            r.search(None)
        self.assertEqual(self.left.calls + self.right.calls, [])

    def test_either_component_can_abstain(self):
        for left, right, ranks in (((0,), (), (1, None)), ((), (0,), (None, 1))):
            response = self.hybrid(left, right).search("query")
            self.assertFalse(response.abstained)
            self.assertEqual(response.top_score, 1 / 61)
            self.assertEqual((response.results[0].bm25_rank, response.results[0].embedding_rank), ranks)
            self.assertIn("ABSTAIN", (response.bm25_status, response.embedding_status))

    def test_both_abstain_and_blank_query_still_passed_to_components(self):
        response = self.hybrid((), ()).search(" \t ")
        self.assertTrue(response.abstained)
        self.assertEqual((response.results, response.top_score, response.abstention_reason), ((), 0.0, "BOTH_COMPONENTS_ABSTAIN"))
        self.assertEqual((response.bm25_status, response.embedding_status), ("ABSTAIN", "ABSTAIN"))
        self.assertEqual(self.left.calls, [(" \t ", 10)])
        self.assertEqual(self.right.calls, self.left.calls)

    def test_no_new_hybrid_threshold_or_margin(self):
        response = self.hybrid((0,), ()).search("unsupported synthetic query")
        self.assertEqual(response.status, "RETRIEVED")
        self.assertLess(response.top_score, 0.03)
        self.assertEqual(response.results[0].score, 1 / 61)

    def test_duplicate_identity_has_only_first_component_contribution(self):
        response = self.hybrid((0, 0, 1), ()).search("query")
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.results[0].score, 1 / 61)
        self.assertEqual(response.results[1].score, 1 / 63)
        self.assertEqual([r.rank for r in response.bm25_results], [1, 3])

    def test_conflicting_duplicate_metadata_rejected(self):
        r = self.hybrid((0, 0), ())
        a, b = self.left.response.results
        self.left.response = replace(self.left.response, results=(a, replace(b, content_hash="wrong")))
        with self.assertRaises(HybridIntegrityError):
            r.search("query")

    def test_shared_returned_metadata_mismatch_rejected(self):
        for field in ("text", "content_hash", "source_path"):
            r = self.hybrid((0,), (0,))
            self.right.response = replace(self.right.response, results=(replace(self.right.response.results[0], **{field: "different"}),))
            with self.subTest(field=field), self.assertRaises(HybridIntegrityError):
                r.search("query")

    def test_same_25_section_corpus_required(self):
        for mode in ("count", "identity", "text", "title", "version", "duplicate"):
            a, b = FakeComponent(self.store), FakeComponent(self.store)
            sections = list(b._sections)
            if mode == "count": sections.pop()
            elif mode == "duplicate": sections[0] = sections[1]
            elif mode == "identity": sections[0] = replace(sections[0], section_id="other")
            elif mode == "version": sections[0] = replace(sections[0], version="other")
            else: sections[0] = replace(sections[0], **{mode: "different"})
            b._sections = tuple(sections)
            with self.subTest(mode=mode), self.assertRaises(HybridIntegrityError):
                HybridRRFRetriever(a, b)

    def test_unknown_returned_identity_rejected(self):
        r = self.hybrid((0,), ())
        self.left.response = replace(self.left.response, results=(replace(self.left.response.results[0], identity=("SOP-99", "1.0-demo", "unknown")),))
        with self.assertRaises(HybridIntegrityError):
            r.search("query")

    def test_invalid_component_response_contract_rejected(self):
        for status, records in (("UNKNOWN", ()), ("RETRIEVED", ()), ("ABSTAIN", (0,)), ("RETRIEVED", tuple(range(11)))):
            r = self.hybrid(records, ())
            self.left.response = replace(self.left.response, status=status)
            with self.subTest(status=status, records=records), self.assertRaises(HybridIntegrityError):
                r.search("query")

    def test_frozen_results_expose_ranks_not_business_fields(self):
        response = self.hybrid().search("query")
        result = response.results[0]
        self.assertEqual((result.bm25_rank, result.embedding_rank, result.retrieval_method), (2, 1, "HYBRID_RRF"))
        self.assertEqual(set(asdict(result)), {"identity", "rank", "score", "text", "content_hash", "source_path", "bm25_rank", "embedding_rank", "retrieval_method"})
        for target, field, value in ((result, "score", 0), (response, "status", "ABSTAIN"), (response.bm25_results[0], "rank", 5)):
            with self.assertRaises(FrozenInstanceError):
                setattr(target, field, value)

    def test_complete_component_rankings_retained_beyond_final_depth(self):
        response = self.hybrid(left=(0, 1, 2), right=(2, 3, 4)).search("query", top_k=1)
        self.assertEqual(len(response.results), 1)
        self.assertEqual([r.identity for r in response.bm25_results], [self.sections[i].identity for i in (0, 1, 2)])
        self.assertEqual([r.identity for r in response.embedding_results], [self.sections[i].identity for i in (2, 3, 4)])

    def test_repeated_search_and_store_order_identical(self):
        r = self.hybrid()
        first = r.search("query")
        self.assertEqual(first, r.search("query"))
        self.right._sections = tuple(reversed(self.right._sections))
        self.assertEqual(first, HybridRRFRetriever(self.left, self.right).search("query"))

    def test_exact_bm25_and_embedding_behavior_remains_unchanged(self):
        from retrieval.embedding_retriever import EmbeddingRetriever
        class Encoder:
            def encode(self, texts): return [(1.0, 0.0)] * len(texts)
        lexical = LexicalRetriever(self.store)
        embedding = EmbeddingRetriever(self.store, encoder=Encoder())
        refs = [self.sections[0].identity]
        before = (retrieve_required_sections(refs, store=self.store), lexical.search("scan history"), embedding.search("scan history"))
        self.hybrid().search("scan history")
        after = (retrieve_required_sections(refs, store=self.store), lexical.search("scan history"), embedding.search("scan history"))
        self.assertEqual(before, after)

    def test_isolated_stdlib_import_fake_path_no_network_or_evaluation_reads(self):
        code = r'''
import builtins,sys
sys.path.insert(0,sys.argv[1])
original=builtins.__import__
def guarded(name,globals=None,locals=None,fromlist=(),level=0):
    if not level and name.split('.')[0] not in sys.stdlib_module_names | {'retrieval'}:
        raise AssertionError('Forbidden dependency: '+name)
    return original(name,globals,locals,fromlist,level)
builtins.__import__=guarded
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen': raise AssertionError('No network/process')
    if event=='open' and isinstance(args[0],str):
        path=args[0].replace('\\','/')
        if any(part in path for part in ('/evaluation/','/artifacts/','/.cache/','/kb/')): raise AssertionError('Forbidden input')
sys.addaudithook(audit)
from retrieval import SectionStore,LexicalResult,LexicalSearchResponse
from retrieval.hybrid_rrf_retriever import HybridRRFRetriever
store=SectionStore.load()
class Fake:
    _sections=store.sections
    def search(self,query,top_k):
        s=self._sections[0]
        return LexicalSearchResponse('RETRIEVED',(LexicalResult(s.identity,1,999,s.text,s.content_hash,s.source_path),),999,None)
r=HybridRRFRetriever(Fake(),Fake())
assert r.search('query').results[0].score==2/61
assert not any(x in sys.modules for x in ('sentence_transformers','torch','numpy','engine'))
print('OK')
'''
        run = subprocess.run([sys.executable, "-I", "-B", "-S", "-c", code, str(DOMAIN)], capture_output=True, text=True, check=True)
        self.assertEqual(run.stdout.strip(), "OK")


if __name__ == "__main__":
    unittest.main()
