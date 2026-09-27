"""Offline exact SOP section retrieval; no decision, network or model authority."""
from .section_store import (
    InvalidSectionReferenceError, ResolvedSection, RetrievalError,
    SectionIntegrityError, SectionNotFoundError, SectionRecord, SectionStore,
    section_content_hash,
)
from .exact_retriever import (
    AssessmentRequest, RequiredSection, RetrievalRecord, collect_required_sections,
    retrieve_case_sections, retrieve_required_sections,
)

__all__ = [
    "SectionStore", "SectionRecord", "ResolvedSection", "RetrievalError",
    "SectionIntegrityError", "SectionNotFoundError", "InvalidSectionReferenceError",
    "section_content_hash", "AssessmentRequest", "RequiredSection", "RetrievalRecord",
    "collect_required_sections", "retrieve_required_sections", "retrieve_case_sections",
]
