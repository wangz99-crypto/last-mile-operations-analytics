"""Supplemental section-level BM25. No labels, business decisions or external services."""
from collections import Counter
from dataclasses import dataclass
import math
import re
from types import MappingProxyType

from .section_store import SectionStore

K1 = 1.5
B = 0.75
MIN_TOP_SCORE = 1.0
DEFAULT_TOP_K = 10
TOKEN_PATTERN = r"[a-z0-9]+"


def tokenize(text):
    """Lowercase ASCII alphanumeric runs; punctuation/underscores delimit tokens."""
    if not isinstance(text, str):
        raise TypeError("Query/text must be a string")
    return tuple(re.findall(TOKEN_PATTERN, text.lower()))


def configuration(*, top_k=DEFAULT_TOP_K):
    return {
        "retrieval_method": "LEXICAL_BM25",
        "tokenizer": {"pattern": TOKEN_PATTERN, "normalization": "str.lower", "punctuation": "split",
                      "stop_words": [], "stemming": False, "query_rewriting": False},
        "searchable_fields": ["title", "section_title", "text"],
        "field_joiner": "LF", "field_weights": "equal; each field included once",
        "query_term_frequency": "binary; unique query tokens summed in sorted order",
        "k1": K1, "b": B,
        "idf": "ln(1 + (N - df + 0.5) / (df + 0.5))",
        "term_score": "idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))",
        "abstention": {"minimum_top_score": MIN_TOP_SCORE, "comparison": "top_score < threshold",
                       "also_abstain": ["empty token sequence", "no positive lexical overlap"], "margin": None},
        "candidate_filter": "score > 0; threshold applies to top score for the whole response",
        "tie_breaking": "score descending, then (policy_id, version, section_id) ascending",
        "top_k": top_k, "score_meaning": "retrieval diagnostic only; not business confidence",
    }


@dataclass(frozen=True, slots=True)
class LexicalResult:
    identity: tuple[str, str, str]
    rank: int
    score: float
    text: str
    content_hash: str
    source_path: str
    retrieval_method: str = "LEXICAL_BM25"


@dataclass(frozen=True, slots=True)
class LexicalSearchResponse:
    status: str
    results: tuple[LexicalResult, ...]
    top_score: float
    abstention_reason: str | None

    @property
    def abstained(self):
        return self.status == "ABSTAIN"


class LexicalRetriever:
    """Index an immutable verified SectionStore; metadata IDs are never keywords."""

    def __init__(self, store: SectionStore):
        sections = tuple(sorted(store.sections, key=lambda section: section.identity))
        if not sections or len({section.version for section in sections}) != 1:
            raise ValueError("Lexical retrieval requires a nonempty, single-version section store")
        if len({section.identity for section in sections}) != len(sections):
            raise ValueError("Duplicate canonical section identities")
        counts = [Counter(tokenize("\n".join((section.title, section.section_title, section.text))))
                  for section in sections]
        self._sections = sections
        self._frequencies = tuple(MappingProxyType(dict(count)) for count in counts)
        self._lengths = tuple(sum(count.values()) for count in counts)
        self._average_length = sum(self._lengths) / len(sections)
        if self._average_length == 0:
            raise ValueError("Lexical corpus has no searchable tokens")
        document_frequencies = Counter(token for count in counts for token in count)
        self._idf = MappingProxyType({token: math.log1p((len(sections) - df + 0.5) / (df + 0.5))
                                      for token, df in document_frequencies.items()})

    @property
    def section_count(self):
        return len(self._sections)

    def search(self, query, top_k=DEFAULT_TOP_K):
        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        terms = sorted(set(tokenize(query)))
        if not terms:
            return LexicalSearchResponse("ABSTAIN", (), 0.0, "EMPTY_QUERY")
        scored = []
        for section, frequencies, length in zip(self._sections, self._frequencies, self._lengths):
            normalization = K1 * (1 - B + B * length / self._average_length)
            score = sum(self._idf[term] * frequencies[term] * (K1 + 1) / (frequencies[term] + normalization)
                        for term in terms if term in frequencies)
            if score > 0:
                scored.append((score, section))
        scored.sort(key=lambda item: (-item[0], item[1].identity))
        if not scored:
            return LexicalSearchResponse("ABSTAIN", (), 0.0, "NO_LEXICAL_OVERLAP")
        top_score = scored[0][0]
        if top_score < MIN_TOP_SCORE:
            return LexicalSearchResponse("ABSTAIN", (), top_score, "TOP_SCORE_BELOW_THRESHOLD")
        records = tuple(LexicalResult(section.identity, rank, score, section.text,
                                      section.content_hash, section.source_path)
                        for rank, (score, section) in enumerate(scored[:top_k], 1))
        return LexicalSearchResponse("RETRIEVED", records, top_score, None)
