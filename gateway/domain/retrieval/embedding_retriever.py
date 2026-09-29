"""Optional section-level sentence embeddings; no model loads at import time."""
from dataclasses import dataclass
import math
from numbers import Real
from pathlib import Path
import re

from .section_store import RetrievalError, SectionStore

MODEL_ID = "BAAI/bge-small-en-v1.5"
MIN_COSINE_SIMILARITY = 0.30
DEFAULT_TOP_K = 10
SECTION_COUNT = 25
MODEL_FILES = (
    "config.json", "config_sentence_transformers.json", "model.safetensors",
    "modules.json", "sentence_bert_config.json", "special_tokens_map.json",
    "tokenizer.json", "tokenizer_config.json", "vocab.txt", "1_Pooling/config.json",
)
DEFAULT_CACHE = Path(__file__).resolve().parents[3] / ".cache/phase2d-model"


class EmbeddingDependencyError(RetrievalError, ImportError):
    """The explicitly requested optional embedding runtime is unavailable."""


class EmbeddingVectorError(RetrievalError, ValueError):
    """An encoder produced invalid, zero or dimensionally inconsistent vectors."""


def configuration():
    return {
        "retrieval_method": "EMBEDDING_COSINE", "model_id": MODEL_ID,
        "model_selection": "Owner-frozen repository-configured model; one model only",
        "device": "cpu", "normalize_embeddings": True,
        "similarity": "normalized dot product; math.fsum over unit vectors",
        "top_k": DEFAULT_TOP_K, "section_count": SECTION_COUNT,
        "searchable_fields": ["title", "section_title", "text"], "field_joiner": "LF",
        "query_transformation": "none; original question text", "query_instruction": "",
        "document_instruction": "", "pooling": "unmodified model snapshot configuration",
        "encode_batch_size": 32, "encode_precision": "float32", "cpu_threads": 1,
        "vector_validation": "finite nonzero rows; L2 normalize in Python float precision",
        "abstention": {"minimum_top_score": MIN_COSINE_SIMILARITY,
                       "comparison": "top_score < threshold", "also_abstain": ["blank query"], "margin": None},
        "candidate_filter": "all sections; threshold applies to top score for the whole response",
        "tie_breaking": "score descending, then (policy_id, version, section_id) ascending; no rounding",
        "score_meaning": "retrieval diagnostic; not confidence, probability, authority or business readiness",
    }


class SentenceTransformerBackend:
    """Explicit real-model factory. Imports/downloads are confined to construction.

    Resolve one revision before loading; download only this model's inference
    files. The pinned local snapshot is then loaded without remote code/network.
    ``local_files_only`` is useful for a separate manual offline smoke check.
    """

    def __init__(self, *, cache_folder=DEFAULT_CACHE, revision=None, local_files_only=False):
        try:
            from sentence_transformers import SentenceTransformer
            from huggingface_hub import HfApi, snapshot_download, try_to_load_from_cache
            import torch
        except ImportError as exc:
            raise EmbeddingDependencyError(
                "Embedding retrieval requires the optional runtime: install gateway/requirements-embeddings.txt"
            ) from exc
        from importlib.metadata import version
        import hashlib
        import platform

        cache = Path(cache_folder)
        if local_files_only:
            marker = try_to_load_from_cache(MODEL_ID, "modules.json", revision=revision or "main", cache_dir=cache)
            if not isinstance(marker, str):
                raise EmbeddingDependencyError("Embedding model snapshot is not cached; provision this model explicitly first")
            resolved = Path(marker).parent.name
        else:
            resolved = HfApi().model_info(MODEL_ID, revision=revision or "main", token=False).sha
        if not isinstance(resolved, str) or not re.fullmatch(r"[0-9a-f]{40}", resolved):
            raise EmbeddingDependencyError("Unable to identify an exact embedding model revision")
        cached_before = {
            name for name in MODEL_FILES
            if isinstance(try_to_load_from_cache(MODEL_ID, name, revision=resolved, cache_dir=cache), str)
        }
        snapshot = Path(snapshot_download(
            MODEL_ID, revision=resolved, cache_dir=cache, allow_patterns=list(MODEL_FILES),
            local_files_only=local_files_only, token=False,
        ))
        for name in ("modules.json", "config.json", "model.safetensors", "1_Pooling/config.json", "tokenizer_config.json"):
            if not (snapshot / name).is_file():
                raise EmbeddingDependencyError(f"Embedding model snapshot is incomplete: missing {name}")
        torch.set_num_threads(1)
        self._model = SentenceTransformer(str(snapshot), device="cpu", local_files_only=True, trust_remote_code=False)
        self._model.eval()
        present = {name for name in MODEL_FILES if (snapshot / name).is_file()}
        self.metadata = {
            "requested_model_id": MODEL_ID, "requested_revision": revision or "main",
            "resolved_model_revision": resolved, "revision_pinned_for_this_load": True,
            "model_id_is_not_a_repository_pinned_revision": True,
            "versions": {name: version(name) for name in (
                "sentence-transformers", "transformers", "torch", "numpy", "huggingface-hub")},
            "python_version": platform.python_version(), "device": str(self._model.device),
            "embedding_dimension": self._model.get_sentence_embedding_dimension(),
            "normalize_embeddings": True, "similarity": "normalized dot product",
            "model_download_occurred": bool(present - cached_before),
            "weights_downloaded": "model.safetensors" not in cached_before,
            "downloaded_files": sorted(present - cached_before),
            "model_file_sha256": {name: hashlib.sha256((snapshot / name).read_bytes()).hexdigest() for name in sorted(present)},
            "cache_scope": "dedicated Phase 2D model cache; absolute machine path omitted",
            "pooling_configuration": self._model[1].get_config_dict(),
            "max_sequence_length": self._model.max_seq_length,
            "truncation": "unmodified SentenceTransformer tokenizer/model maximum; no additional chunking",
            "query_instruction": "", "document_instruction": "", "cpu_threads": torch.get_num_threads(),
            "reproducibility_limit": "Revision and downloaded-file hashes are recorded for this run, but dependency versions and the default main revision are not all pinned in repository requirements; cross-runtime byte-identical embeddings are not claimed.",
        }

    def encode(self, texts):
        # Explicit empty prompt suppresses model default prompts for BOTH sides.
        # Preserve the supplied strings exactly; never strip or rewrite a query.
        return self._model.encode(
            list(texts), device="cpu", normalize_embeddings=True, prompt="",
            batch_size=32, precision="float32", convert_to_numpy=True, show_progress_bar=False,
        )


def _unit_matrix(value, *, rows, dimension=None):
    try:
        matrix = tuple(tuple(row) for row in value)
    except TypeError as exc:
        raise EmbeddingVectorError("Encoder must return a two-dimensional matrix") from exc
    if len(matrix) != rows:
        raise EmbeddingVectorError(f"Expected {rows} embedding rows, received {len(matrix)}")
    expected = dimension if dimension is not None else len(matrix[0])
    if expected < 1 or any(len(row) != expected for row in matrix):
        raise EmbeddingVectorError("Embedding dimensions are empty or inconsistent")
    normalized = []
    for row in matrix:
        if any(isinstance(item, bool) or not isinstance(item, Real) for item in row):
            raise EmbeddingVectorError("Embedding values must be real numbers")
        try:
            values = tuple(float(item) for item in row)
        except (OverflowError, ValueError) as exc:
            raise EmbeddingVectorError("Embedding values must be representable as finite floats") from exc
        if not all(math.isfinite(item) for item in values):
            raise EmbeddingVectorError("Embedding values must be finite")
        norm = math.hypot(*values)
        if not math.isfinite(norm) or norm == 0:
            raise EmbeddingVectorError("Embedding vector must have a finite nonzero norm")
        normalized.append(tuple(item / norm for item in values))
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    identity: tuple[str, str, str]
    rank: int
    score: float
    text: str
    content_hash: str
    source_path: str
    retrieval_method: str = "EMBEDDING_COSINE"


@dataclass(frozen=True, slots=True)
class EmbeddingSearchResponse:
    status: str
    results: tuple[EmbeddingResult, ...]
    top_score: float
    abstention_reason: str | None

    @property
    def abstained(self):
        return self.status == "ABSTAIN"


class EmbeddingRetriever:
    def __init__(self, store: SectionStore, *, encoder=None):
        sections = tuple(sorted(store.sections, key=lambda section: section.identity))
        if len(sections) != SECTION_COUNT:
            raise ValueError("Embedding retrieval requires exactly 25 stable SOP sections")
        if len({section.version for section in sections}) != 1:
            raise ValueError("Embedding retrieval requires a single-version section store")
        if len({section.identity for section in sections}) != SECTION_COUNT:
            raise ValueError("Duplicate canonical section identities")
        self._sections = sections
        self._encoder = SentenceTransformerBackend() if encoder is None else encoder
        texts = tuple("\n".join((section.title, section.section_title, section.text)) for section in sections)
        self._matrix = _unit_matrix(self._encoder.encode(texts), rows=SECTION_COUNT)
        self.embedding_dimension = len(self._matrix[0])

    @property
    def section_count(self):
        return len(self._sections)

    @property
    def runtime_metadata(self):
        from copy import deepcopy
        return deepcopy(getattr(self._encoder, "metadata", {"backend": "injected; no real model identity claimed"}))

    def search(self, query, top_k=DEFAULT_TOP_K):
        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        if not isinstance(query, str):
            raise TypeError("Query must be a string")
        if not query.strip():
            return EmbeddingSearchResponse("ABSTAIN", (), 0.0, "EMPTY_QUERY")
        vector = _unit_matrix(self._encoder.encode((query,)), rows=1, dimension=self.embedding_dimension)[0]
        scored = [(math.fsum(a * b for a, b in zip(row, vector)), section)
                  for row, section in zip(self._matrix, self._sections)]
        scored.sort(key=lambda item: (-item[0], item[1].identity))
        top_score = scored[0][0]
        if top_score < MIN_COSINE_SIMILARITY:
            return EmbeddingSearchResponse("ABSTAIN", (), top_score, "TOP_SCORE_BELOW_THRESHOLD")
        results = tuple(EmbeddingResult(section.identity, rank, score, section.text, section.content_hash, section.source_path)
                        for rank, (score, section) in enumerate(scored[:top_k], 1))
        return EmbeddingSearchResponse("RETRIEVED", results, top_score, None)
