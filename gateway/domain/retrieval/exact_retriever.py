"""Resolve only sections explicitly requested by deterministic output."""
from collections.abc import Mapping
from dataclasses import dataclass, replace

from .section_store import InvalidSectionReferenceError, SectionStore, _requested_identities


@dataclass(frozen=True, slots=True)
class AssessmentRequest:
    assessment_index: int
    exception_type: str
    rule_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RequiredSection:
    identity: tuple[str, str, str]
    requested_by: tuple[AssessmentRequest, ...]


@dataclass(frozen=True, slots=True)
class RetrievalRecord:
    identity: tuple[str, str, str]
    text: str
    content_hash: str
    source_path: str
    rank: int
    request_indices: tuple[int, ...]
    requested_by: tuple[AssessmentRequest, ...] = ()
    retrieval_method: str = "EXACT_POLICY_SECTION"


def retrieve_required_sections(expected_sections, *, store=None):
    """Resolve all references or raise; rank is presentation order, never confidence."""
    store = SectionStore.load() if store is None else store
    return tuple(RetrievalRecord(item.identity, item.section.text, item.section.content_hash,
                                 item.section.source_path, rank, item.request_indices)
                 for rank, item in enumerate(store.resolve_many(expected_sections), 1))


def collect_required_sections(triage_result):
    """Union declared sections of ONE shipment result, retaining assessment provenance."""
    if not isinstance(triage_result, Mapping) or not isinstance(triage_result.get("assessments"), (list, tuple)):
        raise InvalidSectionReferenceError("Expected one deterministic shipment result with assessments")
    required, all_identities = {}, []
    for index, assessment in enumerate(triage_result["assessments"]):
        if not isinstance(assessment, Mapping) or not {"exception_type", "rule_ids", "expected_sections"} <= assessment.keys():
            raise InvalidSectionReferenceError(f"Assessment {index} lacks declared sections or provenance")
        category, rules = assessment["exception_type"], assessment["rule_ids"]
        if not isinstance(category, str) or not category or not isinstance(rules, (list, tuple)) or not all(isinstance(r, str) and r for r in rules):
            raise InvalidSectionReferenceError(f"Assessment {index} has invalid provenance")
        requester = AssessmentRequest(index, category, tuple(rules))
        identities = _requested_identities(assessment["expected_sections"])
        all_identities.extend(identities)
        for identity in identities:
            requesters = required.setdefault(identity, [])
            if requester not in requesters:
                requesters.append(requester)
    _requested_identities(all_identities)  # Enforce one version across all assessments.
    return tuple(RequiredSection(identity, tuple(requesters)) for identity, requesters in required.items())


def retrieve_case_sections(triage_result, *, store=None):
    """Exact-resolve the declared union; never inspect shipment facts or select rules."""
    required = collect_required_sections(triage_result)
    records = retrieve_required_sections([item.identity for item in required], store=store)
    return tuple(replace(record, requested_by=item.requested_by) for record, item in zip(records, required))
