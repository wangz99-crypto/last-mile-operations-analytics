# Phase 2A: exact Last-Mile SOP section retrieval

This package loads the active `1.0-demo` corpus: **8 SOP documents and 25 stable
sections**. The registry, frozen artifact manifest, contract schema and existing
Markdown under `gateway/domain/` remain the policy authority. Nothing is copied
into the legacy IT knowledge base. The package has only standard-library
dependencies; it imports neither the deterministic engine nor an application.

The architecture remains:

`Structured Facts -> Deterministic Rules -> SOP Retrieval -> LLM Explanation -> Human Review`

Phase 2A implements only the SOP retrieval step. There are no embeddings, vector
database, model/LLM calls, network requests, FastAPI integration or semantic search.
Retrieval does not classify shipments, calculate times, count attempts, select
rules, determine eligibility or change action state or priority. The engine has
already declared its exact `expected_sections`. Retrieval resolves those identities
and returns their verified text, or explicitly fails.

## Citation identity and API

The only citation identity is `(policy_id, version, section_id)`. Paths, content
hashes and presentation ranks are metadata, never policy identity or confidence.
Each call uses exactly one version; mixed-version requests fail before resolution.

From repository root:

```python
from gateway.domain.retrieval import (
    SectionStore, collect_required_sections,
    retrieve_required_sections, retrieve_case_sections,
)

store = SectionStore.load()  # Optional root=Path(...) is a domain artifact root.
section = store.get(
    policy_id="SOP-02", version="1.0-demo", section_id="late-escalate",
)
assert section.identity == ("SOP-02", "1.0-demo", "late-escalate")

refs = [
    {"policy_id": "SOP-02", "version": "1.0-demo", "section_id": "late-escalate"},
    {"policy_id": "SOP-02", "version": "1.0-demo", "section_id": "late-escalate"},
]
resolved = store.resolve_many(refs)
assert len(resolved) == 1
assert resolved[0].section == section
assert resolved[0].request_indices == (0, 1)

records = retrieve_required_sections(refs, store=store)
assert records[0].retrieval_method == "EXACT_POLICY_SECTION"
assert records[0].rank == 1
```

When `gateway/domain` is on `PYTHONPATH`, the same API is available as `retrieval`.
Construct active stores with `SectionStore.load(root=...)`, which validates the
entire corpus before returning a store. Reuse a loaded store as an immutable
in-memory snapshot; reload explicitly to check files again. There is no automatic
refresh or fallback version.

API return types and ordering:

- `SectionStore.get(*, policy_id, version, section_id)` returns a frozen
  `SectionRecord` with identity, document/section titles, inherited exception
  coverage and effective interval, demo flag, section rule/evidence backlinks,
  domain-relative POSIX `source_path`, `content_hash` and `text`. Collection fields
  are tuples; the store's index is read-only.
- `SectionStore.resolve_many(section_refs)` returns a tuple of `ResolvedSection`
  objects containing `section`, `identity` and every zero-based `request_indices`.
  References must be exact three-key mappings or three-string identity tuples.
  Extra keys, omitted components, free-form text and padded strings are rejected.
  Identical identities are deduplicated in first-request order. An empty request
  returns an empty tuple. All requested identities must resolve; there is no
  partial success result.
- `store.sections` is the immutable registry-ordered section inventory.
  `store.document_count`, `store.section_count` and `store.versions` report actual
  indexed values, without artificial minimums.
- `retrieve_required_sections(expected_sections, *, store=None)` returns a tuple
  of frozen `RetrievalRecord` objects: `identity`, `text`, `content_hash`,
  `source_path`, `retrieval_method`, one-based `rank`, `request_indices` and
  `requested_by`. If omitted, `store` is loaded and validated on that call.
  `rank` is just first-request presentation order; no similarity score is computed.

## Declared section union for a shipment result

The case helper accepts **one element of `triage_snapshot(...)["results"]`**, not
raw shipment facts or the full results envelope:

```python
result = engine_output["results"][0]  # Already computed by the deterministic engine.
required = collect_required_sections(result)
records = retrieve_case_sections(result, store=store)
```

`collect_required_sections(triage_result)` returns a tuple of frozen
`RequiredSection(identity, requested_by)` records. The union follows assessment
order, then each assessment's declared section order. `requested_by` preserves
each requesting assessment's zero-based `assessment_index`, `exception_type` and
original `rule_ids` as an immutable tuple. Repeated requests in one assessment
produce one requester; distinct assessments remain distinct even when their
category and rule IDs match.

`retrieve_case_sections(triage_result, *, store=None)` resolves that exact union
and attaches its provenance to each retrieval record. Its `request_indices`
refer to positions in the collected union; `requested_by` points back to the
original assessments. Neither helper mutates the deterministic output. No fields
outside `assessments` are read, and only `exception_type`, `rule_ids` and
`expected_sections` are read within an assessment. Categories and rule IDs are
copied solely as provenance; they never generate additional section requests.
SOP-08 is retrieved only when explicitly requested, just like every other SOP.

Required exact lookup is distinct from any future supplemental ranked search.
Such search is outside Phase 2A and could not repair a missing required identity
by choosing a nearby section. No generic context sections are added here.

## Integrity and section hashes

The loader first checks raw registry and schema bytes against
`policy/artifact_manifest.json`, then verifies every registry-declared SOP's raw
SHA-256 **before parsing or indexing it**. The manifest is the existing trusted
file-checksum authority and excludes itself, as in the frozen artifact contract.
The loader does not update it or offer a checksum bypass.

The filesystem and manifest SOP inventories must equal the registry inventory.
Metadata is parsed with duplicate-key rejection. Each document must have a
heading, the fictional-policy notice, exactly one JSON metadata block, and the
declared stable H2 sections. Metadata and heading order must match the registry;
every identity occurs once. Policy ID, bundle version, effective interval, demo
label and exception coverage are checked. Rule and evidence backlinks are checked
in both directions against registry support/failure-guidance mappings and schema
ID inventories. These are structural checks, not business-rule evaluation.

`text` contains exactly the Markdown body after its stable H2 heading, up to the
next stable H2 or end of file. The heading and document preamble are excluded;
readable section title comes from metadata. Nested Markdown and fenced-code
contents remain intact. Only CRLF/CR line endings become LF: leading/trailing
blank lines, trailing spaces, indentation and the final newline are preserved.

Each section's derived `content_hash` is lowercase SHA-256 over UTF-8 bytes of:

```text
policy_id + "\n" +
version + "\n" +
section_id + "\n" +
section_title + "\n" +
normalized_section_body
```

`section_content_hash(policy_id, version, section_id, section_title, body)` exposes
this algorithm. No extra newline is appended to the payload. This runtime hash
is retrieval metadata; it does not replace the raw artifact checksum or become
policy authority. A file line-ending change still invalidates the raw checksum,
even if the normalized section hash would remain the same.

## Failure behavior and validation

`RetrievalError` is the common exception base:

- `SectionIntegrityError`: missing/corrupt files, malformed metadata, duplicate or
  inconsistent identities, unregistered sections, wrong policy/version, invalid
  checksums or inconsistent backlinks. No partially loaded store is returned.
- `InvalidSectionReferenceError`: malformed exact references, mixed versions or
  an invalid case-helper input contract.
- `SectionNotFoundError`: one or more exact required identities are unavailable;
  its `identities` tuple names the unresolved requests. No substitute is returned.

Tests mutate only temporary copies of runtime artifacts. Some mutation tests
rehash the **temporary** manifest to exercise structural errors beyond the checksum
gate, or measure an isolated body change. Real frozen files are never edited.
Synthetic engine results exercise the retrieval round trip. A fresh isolated
Python process with site packages disabled exercises loading and retrieval,
rejecting non-stdlib dependencies, network activity and non-runtime artifact reads.

Run from repository root (PowerShell):

```powershell
python -B -m unittest discover -s gateway/domain/tests -p 'test_section_store.py' -v
python -B -m unittest discover -s gateway/domain/tests -p 'test_exact_retrieval.py' -v
$env:PYTHONPATH = 'gateway/domain'
python -B -m unittest discover -s gateway/domain/tests -p 'test_engine*.py' -v
python -B -m unittest discover -s gateway/domain/tests -p 'test_contracts.py' -v
python -B gateway/domain/validate_contracts.py
python -B -m unittest discover -s gateway/domain/tests -p 'test_post_1b2_comparison.py' -v
python -B gateway/domain/evaluation/compare_development.py
python -B gateway/domain/evaluation/post_1b2/compare_post_1b2.py
```

The historical expectations remain:

```text
Frozen legacy Development strict comparison: 14/18
Post-1B.2 versioned Development regression: 18/18
```

The legacy CLI intentionally returns exit code 1 for five diagnostic migrations
across C04, D15, D16 and D17; the original legacy conformance test retains those
historical expectations. Phase 2A changes no engine behavior, frozen Gold, legacy
comparator or private held-out artifacts and performs no private comparison.
