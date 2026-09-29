"""Ranks-only RRF over the unchanged lexical and embedding section retrievers."""
from dataclasses import dataclass
from types import MappingProxyType

from .section_store import RetrievalError, section_identity

RRF_K = 60
BM25_WEIGHT = 1.0
EMBEDDING_WEIGHT = 1.0
COMPONENT_DEPTH = 10
DEFAULT_TOP_K = 10


class HybridIntegrityError(RetrievalError, ValueError):
    """Component corpora, returned identities or metadata are inconsistent."""


def configuration():
    return {
        "retrieval_method": "HYBRID_RRF", "fusion_method": "Reciprocal Rank Fusion",
        "rrf_k": RRF_K, "bm25_weight": BM25_WEIGHT, "embedding_weight": EMBEDDING_WEIGHT,
        "bm25_component_depth": COMPONENT_DEPTH, "embedding_component_depth": COMPONENT_DEPTH,
        "top_k": DEFAULT_TOP_K, "formula": "sum(weight / (60 + component_rank) for components containing the identity)",
        "component_ranks": "one-based returned positions; first occurrence only; duplicate positions are not compressed",
        "candidate_set": "union of identities returned by non-abstaining components",
        "query_transformation": "none; original query passed to both components",
        "abstention": "both components ABSTAIN; no additional hybrid threshold or margin",
        "raw_component_scores_used": False,
        "tie_breaking": "RRF score descending, then canonical identity ascending; no rounding",
        "score_meaning": "retrieval diagnostic only; not confidence, probability, authority, completeness or business state",
    }


def _metadata(record):
    return record.text, record.content_hash, record.source_path


def _corpus(component):
    # Both frozen adapters already expose their immutable indexed SectionRecord
    # tuple internally. Read it without changing their public API or behavior.
    sections = getattr(component, "_sections", ())
    if len(sections) != 25:
        raise HybridIntegrityError("Each component must index the same 25-section store")
    records = {}
    for section in sections:
        identity = section_identity(section.identity)
        if identity in records:
            raise HybridIntegrityError("Duplicate canonical corpus identity")
        records[identity] = section
    if len({identity[1] for identity in records}) != 1:
        raise HybridIntegrityError("A single policy version is required")
    return records


@dataclass(frozen=True, slots=True)
class ComponentRank:
    identity: tuple[str, str, str]
    rank: int
    content_hash: str
    source_path: str


@dataclass(frozen=True, slots=True)
class HybridRRFResult:
    identity: tuple[str, str, str]
    rank: int
    score: float
    text: str
    content_hash: str
    source_path: str
    bm25_rank: int | None
    embedding_rank: int | None
    retrieval_method: str = "HYBRID_RRF"


@dataclass(frozen=True, slots=True)
class HybridRRFResponse:
    status: str
    results: tuple[HybridRRFResult, ...]
    top_score: float
    abstention_reason: str | None
    bm25_status: str
    embedding_status: str
    bm25_results: tuple[ComponentRank, ...]
    embedding_results: tuple[ComponentRank, ...]
    bm25_abstention_reason: str | None
    embedding_abstention_reason: str | None

    @property
    def abstained(self):
        return self.status == "ABSTAIN"


class HybridRRFRetriever:
    """Inject two frozen components built from one verified SectionStore.

    The component indexed snapshots must match. Results are validated against
    that common snapshot before combining any ranks. No model or file is loaded.
    """

    def __init__(self, lexical_retriever, embedding_retriever):
        lexical, embedding = _corpus(lexical_retriever), _corpus(embedding_retriever)
        if lexical.keys() != embedding.keys():
            raise HybridIntegrityError("Component canonical corpus inventories differ")
        for identity, section in lexical.items():
            other = embedding[identity]
            if (_metadata(section), section.title, section.section_title) != (_metadata(other), other.title, other.section_title):
                raise HybridIntegrityError(f"Inconsistent component corpus metadata: {identity}")
        self._sections = tuple(lexical[key] for key in sorted(lexical))
        self._corpus = MappingProxyType(lexical)
        self._lexical = lexical_retriever
        self._embedding = embedding_retriever

    @property
    def section_count(self):
        return len(self._sections)

    def _ranks(self, response):
        if response.status not in ("RETRIEVED", "ABSTAIN"):
            raise HybridIntegrityError("Invalid component response status")
        if response.status == "ABSTAIN":
            if response.results:
                raise HybridIntegrityError("An abstaining component cannot return support")
            return ()
        if not response.results or len(response.results) > COMPONENT_DEPTH:
            raise HybridIntegrityError("Retrieved component must return between 1 and 10 records")
        unique = {}
        for rank, record in enumerate(response.results, 1):
            identity = section_identity(record.identity)
            if identity not in self._corpus:
                raise HybridIntegrityError(f"Component returned an identity outside its corpus: {identity}")
            # Validate even duplicate occurrences before discarding them. A
            # conflicting duplicate must not be silently accepted.
            if _metadata(record) != _metadata(self._corpus[identity]):
                raise HybridIntegrityError(f"Inconsistent returned component metadata: {identity}")
            unique.setdefault(identity, ComponentRank(identity, rank, record.content_hash, record.source_path))
        return tuple(unique.values())

    def search(self, query, top_k=DEFAULT_TOP_K):
        if not isinstance(query, str):
            raise TypeError("Query must be a string")
        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        bm25 = self._lexical.search(query, top_k=COMPONENT_DEPTH)
        embedding = self._embedding.search(query, top_k=COMPONENT_DEPTH)
        left, right = self._ranks(bm25), self._ranks(embedding)
        left_ranks = {record.identity: record.rank for record in left}
        right_ranks = {record.identity: record.rank for record in right}
        scores = []
        for identity in left_ranks.keys() | right_ranks.keys():
            score = (BM25_WEIGHT / (RRF_K + left_ranks[identity]) if identity in left_ranks else 0.0)
            score += (EMBEDDING_WEIGHT / (RRF_K + right_ranks[identity]) if identity in right_ranks else 0.0)
            scores.append((score, identity))
        scores.sort(key=lambda item: (-item[0], item[1]))
        results = tuple(HybridRRFResult(identity, rank, score, * _metadata(self._corpus[identity]),
                                        left_ranks.get(identity), right_ranks.get(identity))
                        for rank, (score, identity) in enumerate(scores[:top_k], 1))
        return HybridRRFResponse(
            "RETRIEVED" if scores else "ABSTAIN", results, scores[0][0] if scores else 0.0,
            None if scores else "BOTH_COMPONENTS_ABSTAIN", bm25.status, embedding.status, left, right,
            bm25.abstention_reason, embedding.abstention_reason,
        )
