"""Offline supplemental lexical retrieval tests; no evaluation data imports."""
from dataclasses import asdict, replace
import math
from pathlib import Path
import subprocess
import sys
import unittest

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from retrieval import LexicalRetriever, SectionStore, retrieve_required_sections
from retrieval.lexical_retriever import configuration, tokenize


class LexicalRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = SectionStore.load()
        cls.retriever = LexicalRetriever(cls.store)

    def synthetic_store(self, **changes):
        section = replace(self.store.sections[0], title="title", section_title="heading", **changes)
        return SectionStore({section.identity: section})

    def test_25_canonical_sections_indexed(self):
        self.assertEqual(self.retriever.section_count, 25)
        query = " ".join(section.title + " " + section.section_title + " " + section.text for section in self.store.sections)
        response = self.retriever.search(query, top_k=100)
        self.assertEqual(len(response.results), 25)
        self.assertEqual({record.identity for record in response.results}, {section.identity for section in self.store.sections})

    def test_tokenization_is_lowercase_punctuation_splitting_without_rewrite(self):
        self.assertEqual(tokenize("Delay, DELAY! E-FAILED; attempt_id 24h."),
                         ("delay", "delay", "e", "failed", "attempt", "id", "24h"))
        self.assertEqual(tokenize("deliver deliveries"), ("deliver", "deliveries"))
        self.assertEqual(tokenize("--- ..."), ())
        with self.assertRaises(TypeError):
            self.retriever.search(None)

    def test_repeated_search_and_reload_are_identical(self):
        query = "qualifying physical scan complete history stale escalation"
        first = self.retriever.search(query)
        self.assertFalse(first.abstained)
        self.assertEqual(self.retriever.search(query), first)
        self.assertEqual(LexicalRetriever(SectionStore.load()).search(query), first)
        self.assertEqual(self.retriever.search(query + " " + query.upper()), first)

    def test_canonical_tie_breaking_is_independent_of_store_order(self):
        body = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"
        source = replace(self.store.sections[0], title="title", section_title="heading", text=body)
        a = replace(source, policy_id="SOP-02", section_id="alpha")
        b = replace(source, policy_id="SOP-01", section_id="zulu")
        forward = LexicalRetriever(SectionStore({a.identity: a, b.identity: b})).search(body)
        reverse = LexicalRetriever(SectionStore({b.identity: b, a.identity: a})).search(body)
        self.assertFalse(forward.abstained)
        self.assertEqual(forward, reverse)
        self.assertEqual([r.identity for r in forward.results], [b.identity, a.identity])
        self.assertEqual(forward.results[0].score, forward.results[1].score)

    def test_empty_and_nonmatching_queries_abstain(self):
        for query, reason in (("", "EMPTY_QUERY"), (" !? ", "EMPTY_QUERY"), ("zzqvnonmatchingtoken", "NO_LEXICAL_OVERLAP")):
            with self.subTest(query=query):
                response = self.retriever.search(query)
                self.assertEqual(response.status, "ABSTAIN")
                self.assertEqual(response.results, ())
                self.assertEqual(response.abstention_reason, reason)
                self.assertEqual(response.top_score, 0.0)

    def test_low_positive_score_abstains_using_general_threshold(self):
        retriever = LexicalRetriever(self.synthetic_store(text="alpha"))
        response = retriever.search("alpha")
        self.assertEqual(response.status, "ABSTAIN")
        self.assertEqual(response.abstention_reason, "TOP_SCORE_BELOW_THRESHOLD")
        # One document, one occurrence, dl == avgdl: tf normalization cancels.
        self.assertAlmostEqual(response.top_score, math.log1p(0.5 / 1.5), places=14)
        self.assertGreater(response.top_score, 0)

    def test_searchable_fields_only_and_no_metadata_boosts(self):
        section = replace(self.store.sections[0], title="alpha bravo", section_title="charlie delta", text="echo foxtrot")
        metadata_changed = replace(section, policy_id="SECRETIDENTITY", section_id="HIDDENBOOST",
                                   rule_ids=("SECRETTERM",), requirement_ids=("SECRETREQUIREMENT",), source_path="SECRETFILE")
        original = LexicalRetriever(SectionStore({section.identity: section}))
        changed = LexicalRetriever(SectionStore({metadata_changed.identity: metadata_changed}))
        query = "alpha bravo charlie delta echo foxtrot"
        self.assertEqual(original.search(query).results[0].score, changed.search(query).results[0].score)
        self.assertEqual(changed.search("SECRETIDENTITY HIDDENBOOST SECRETTERM SECRETREQUIREMENT SECRETFILE").abstention_reason,
                         "NO_LEXICAL_OVERLAP")

    def test_top_k_and_invalid_depths(self):
        query = " ".join(section.text for section in self.store.sections)
        all_results = self.retriever.search(query, top_k=100).results
        for k in (1, 3, 5, 10, 100):
            self.assertEqual(self.retriever.search(query, top_k=k).results, all_results[:k])
        for k in (0, -1, 1.5, True, None):
            with self.subTest(top_k=k), self.assertRaises(ValueError):
                self.retriever.search(query, top_k=k)

    def test_metadata_and_exact_lookup_remain_unchanged(self):
        before = tuple(asdict(section) for section in self.store.sections)
        reference = dict(policy_id="SOP-02", version="1.0-demo", section_id="late-escalate")
        exact = retrieve_required_sections([reference], store=self.store)
        response = self.retriever.search("late delivery escalation evidence", top_k=10)
        self.assertEqual(tuple(asdict(section) for section in self.store.sections), before)
        self.assertEqual(retrieve_required_sections([reference], store=self.store), exact)
        for record in response.results:
            section = self.store.get(**dict(zip(("policy_id", "version", "section_id"), record.identity)))
            self.assertEqual((record.text, record.content_hash, record.source_path), (section.text, section.content_hash, section.source_path))
            self.assertEqual(record.retrieval_method, "LEXICAL_BM25")
            self.assertTrue(math.isfinite(record.score) and record.score > 0)
            self.assertFalse(hasattr(record, "confidence"))
            self.assertFalse(hasattr(record, "priority"))
            self.assertFalse(hasattr(record, "action_state"))

    def test_single_version_corpus_required(self):
        section = self.store.sections[0]
        other = replace(section, version="2.0-demo")
        with self.assertRaises(ValueError):
            LexicalRetriever(SectionStore({section.identity: section, other.identity: other}))
        with self.assertRaises(ValueError):
            LexicalRetriever(SectionStore({}))

    def test_configuration_captures_fixed_formula_and_abstention(self):
        config = configuration()
        self.assertEqual((config["k1"], config["b"], config["abstention"]["minimum_top_score"], config["top_k"]), (1.5, 0.75, 1.0, 10))
        self.assertEqual(config["searchable_fields"], ["title", "section_title", "text"])
        config["k1"] = 99
        self.assertEqual(configuration()["k1"], 1.5)

    def test_isolated_stdlib_only_without_network_or_evaluation_reads(self):
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
        raise AssertionError('No network or subprocess allowed')
    if event == 'open' and isinstance(args[0], str):
        value = args[0].replace('\\', '/')
        if any(part in value for part in ('/evaluation/', '/examples/', '/artifacts/', '/kb/')):
            raise AssertionError('No evaluation or legacy corpus reads')
sys.addaudithook(audit)
from retrieval import SectionStore, LexicalRetriever
retriever = LexicalRetriever(SectionStore.load())
assert retriever.section_count == 25
assert retriever.search('qualifying scan history evidence').results
assert 'engine' not in sys.modules
print('OK')
'''
        result = subprocess.run([sys.executable, "-I", "-B", "-S", "-c", code, str(DOMAIN)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), "OK")


if __name__ == "__main__":
    unittest.main()
