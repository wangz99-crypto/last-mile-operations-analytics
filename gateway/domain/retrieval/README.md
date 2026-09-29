# Last-Mile SOP retrieval: exact lookup, lexical and embedding baselines

This package loads the active `1.0-demo` corpus: **8 SOP documents and 25 stable
sections**. The registry, frozen artifact manifest, contract schema and existing
Markdown under `gateway/domain/` remain the policy authority. Nothing is copied
into the legacy IT knowledge base. The core package has only standard-library
dependencies; it imports neither the deterministic engine nor an application.
Phase 2D provides an explicitly constructed optional embedding adapter.

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

Required exact lookup is distinct from supplemental ranked search. Phase 2C adds
the lexical baseline described below, without replacing or changing Phase 2A.
A ranked result cannot repair a missing required identity by choosing a nearby
section. No generic context sections are added by exact retrieval.

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

## Phase 2C: supplemental lexical search

The boundary is `Deterministic Rules -> Exact Required Lookup -> Supplemental
Ranked Retrieval`. The lexical retriever does not execute the rules, call exact
lookup automatically, or select/change business decisions. It searches the same
verified SectionStore at canonical section identity; there are no additional
chunks, embeddings, models, network calls or legacy IT retrieval changes.

```python
from gateway.domain.retrieval import LexicalRetriever, SectionStore

retriever = LexicalRetriever(SectionStore.load())
response = retriever.search("qualifying scan history evidence", top_k=10)
if response.status == "ABSTAIN":
    print(response.abstention_reason)
else:
    for record in response.results:
        print(record.identity, record.rank, record.score)
```

`LexicalSearchResponse` and its `LexicalResult` records are frozen dataclasses.
The response exposes `status` (`RETRIEVED` or `ABSTAIN`), `results`, `top_score`,
`abstention_reason` and the `abstained` property. Each result has `identity`,
one-based `rank`, `score`, `text`, `content_hash`, `source_path` and
`retrieval_method="LEXICAL_BM25"`. The raw top score remains a diagnostic even when
the response abstains; abstention returns no support records. No confidence,
eligibility, action state or priority is inferred from scores.

`top_k` must be a positive integer (not a boolean); requests larger than the
corpus return at most the positive-scoring sections. There is no padding with
unmatched sections. All sections in a search use one policy version.

### Fixed scoring and abstention configuration

Each indexed text is exactly `title + LF + section_title + LF + text`, using
readable document/section titles and the Markdown section body once each, with
equal field weights. Policy IDs, stable section IDs, backlinks, file paths,
question text, Gold labels and rationales are not injected as extra keywords.
Identifiers occurring naturally in the original body are left untouched.

Tokenization is `re.findall(r"[a-z0-9]+", text.lower())`: ASCII alphanumeric runs,
with punctuation and underscores as separators. There is no stop-word list,
stemming, synonym expansion or query rewriting. Repeated document tokens count
toward term frequency; repeated query tokens contribute once. Query terms are
summed in sorted order for deterministic floating-point evaluation.

With `N` sections, section frequency `df`, term frequency `tf`, section token
length `dl` and mean section length `avgdl`:

```text
idf = ln(1 + (N - df + 0.5) / (df + 0.5))
score = sum(idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl)))
k1 = 1.5
b = 0.75
```

These standard BM25 defaults were fixed before Development evaluation. Results
sort by descending score, then ascending `(policy_id, version, section_id)` for
exact ties. No score rounding affects ranking. Scores are retrieval diagnostics,
not similarity-based business confidence or evidence of policy authority.

The general abstention threshold is **minimum top score 1.0**, chosen as a simple
initial lexical-evidence floor before evaluation, not calibrated to a particular
question. Empty token sequences, no positive overlap, or a top score below 1.0
return `ABSTAIN`. Equality is accepted. There is no margin test or hardcoded
negative-question rule. This criterion cannot reliably establish semantic scope:
an unsupported query can still overlap ordinary policy words. Such false support
is retained and reported rather than corrected by special-casing a known query.

### Development-only evaluation and freeze candidate

Run the pinned evaluator from repository root:

```powershell
python -B gateway/domain/evaluation/retrieval/evaluate_development.py
```

The CLI accepts no question-path or split arguments. It reads only
`evaluation/retrieval/DEVELOPMENT_MANIFEST.json` and these direct Development files:
RQ003, RQ006, RQ009, RQ012, RQ015, RQ016, RQ019, RQ022, RQ025, RQ026, RQ029, RQ032,
RQ035, RQ038 and RQ041. There is no recursive question discovery. It rejects other
IDs, paths, subdirectories, symlinks or splits before accepting a dataset.
All manifest entries are checked before opening any question file; all file
hashes and the aggregate receipt are checked before question contents are parsed.
Alternate roots in the loader API exist for temporary copied-fixture tests;
they enforce the same exact inventory and pinned receipt.

The manifest must identify an OWNER_REVIEWED, frozen DEVELOPMENT set. The receipt
is SHA-256 over UTF-8 records `question_id + TAB + lowercase file SHA-256 + LF`,
sorted by question ID and including the final LF. It must equal:

```text
4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00
```

Local `.gitattributes` marks only the imported question JSON files and Development
manifest as `-text`, preserving their reviewed bytes across Git checkouts. It
does not change their contents or the receipt. The retriever is initialized from
SectionStore only; evaluation passes it query text and depth 10, never Gold,
required-section labels or reviewer rationales.

Metrics use the first unique returned section identities. ANSWERABLE denominators
exclude the negative case: Hit@1/3 uses Gold relevance; MRR@10 uses the first Gold
rank within ten, with misses/abstentions equal to zero. Required coverage at
1/3/5/10 uses the separate required set. Both question-macro coverage and pooled
section-micro coverage are reported. Full required-set success at 3/5/10 is
aggregated only over questions with more than one required section; per-question
full-set indicators are also retained for single-required cases. NEGATIVE rows
retain empty Gold/required sets, null answerable metrics, and explicit correct
abstention/false-support indicators.

Artifacts are written exclusively to `artifacts/retrieval_dev_lexical_baseline/`:

- `DEVELOPMENT_RESULTS.json`: deterministic full per-question rankings, scores,
  relevance/required identities, metrics, abstention and observed failure details.
- `DEVELOPMENT_REPORT.md`: aggregates with denominators and every missed reported
  target. Partial top-1 coverage on multi-required questions is identified as
  unavoidable, not automatically a ranking defect.
- `RUN_MANIFEST.json`: verified input receipt/hashes, corpus section hashes,
  exact configuration, code base commit, candidate source-file hashes and output
  hashes. It explicitly qualifies uncommitted candidate code rather than claiming
  that the base commit contains it. Existing artifacts are never overwritten.

The configuration is a **candidate awaiting owner review**, not final. Development
is used for method development; it does not establish held-out performance or an
AI improvement claim. No private HELD_OUT question, manifest, catalog, label,
rationale or result is accessed. No held-out evaluation is run. The default
constants and threshold are not changed after seeing this baseline's results.

Focused Phase 2C tests:

```powershell
python -B -m unittest discover -s gateway/domain/tests -p 'test_lexical_retrieval.py' -v
python -B -m unittest discover -s gateway/domain/tests -p 'test_retrieval_development_evaluation.py' -v
```

## Phase 2D: optional sentence-embedding baseline

Exact lookup resolves identities already declared by the deterministic engine.
BM25 ranks sections by lexical overlap. The optional embedding adapter ranks the
same sections by cosine similarity. Both ranked methods are supplemental: neither
changes exact lookup, rule decisions, policy authority or business readiness.
Phase 2C BM25 v0 and its historical artifacts remain unchanged.

The owner-frozen model is **`BAAI/bge-small-en-v1.5`**, matching
`gateway/configs/server.example.yaml`. The owner selected it after the original
MiniLM preference was found to differ from repository configuration. No second
model is evaluated. The runtime uses the repository's existing optional
`gateway/requirements-embeddings.txt` (`sentence-transformers==3.0.1` plus torch).
Install those dependencies in a separate virtual environment when running the
real adapter. They are unnecessary for deterministic execution, SectionStore,
exact retrieval, BM25 or the ordinary unit tests.

```python
from gateway.domain.retrieval import SectionStore
from gateway.domain.retrieval.embedding_retriever import EmbeddingRetriever

retriever = EmbeddingRetriever(SectionStore.load())  # Explicit model initialization.
response = retriever.search("qualifying scan history evidence", top_k=10)
for record in response.results:
    print(record.identity, record.rank, record.score)
```

Neither `import gateway.domain.retrieval` nor importing the embedding module
loads SentenceTransformer, torch, NumPy, model weights or network resources.
`SentenceTransformerBackend` imports the optional runtime only when explicitly
constructed; a missing dependency raises `EmbeddingDependencyError` with the
optional requirements path. No silent zero-vector substitute is provided.

### Frozen model and vector configuration

- CPU, one torch compute thread; model evaluation mode.
- Exactly 25 stable sections from the verified single-version SectionStore,
  ordered by `(policy_id, version, section_id)`. No additional chunks, legacy
  IT corpus, vector database, metadata boosts or external vector service.
- Each section input is exactly readable `title + LF + section_title + LF + text`.
  Natural identifiers in the original body remain intact. Metadata IDs, filenames,
  labels, rationales and synonyms are not injected.
- Original query strings are passed directly, independently of document encoding.
  **No BGE query instruction, prefix or rewriting** is added. The backend explicitly
  passes `prompt=""` for both documents and queries, disabling model default prompts.
- SentenceTransformer `normalize_embeddings=True`, float32 encode precision,
  batch size 32. The model's own pooling/tokenization/maximum sequence length are
  retained and recorded; no custom pooling or model-length tuning is applied.
- The adapter validates and L2 normalizes the vectors in Python float precision,
  then computes cosine as `math.fsum` of elementwise products. The 25-row matrix
  is encoded once per retriever instance and stored in memory. Nonfinite, zero,
  malformed or inconsistent vectors raise `EmbeddingVectorError`.
- `top_k=10`; positive integer overrides are supported by the search API, capped
  at 25. The evaluator always uses 10. Once support is accepted, ranking includes
  all sections, without per-result score filtering. Scores are not rounded before
  descending ranking; exact ties use ascending canonical identity.
- **Minimum top cosine similarity 0.30**, fixed a priori. Blank queries abstain
  without encoding; a top score below 0.30 abstains with no returned support.
  Equality is accepted. There is no margin test or question-specific exception.

Frozen `EmbeddingResult` objects expose `identity`, `rank`, `score`, `text`,
`content_hash`, `source_path` and `retrieval_method="EMBEDDING_COSINE"`.
The frozen response exposes `status`, `results`, `top_score`, `abstention_reason`
and `abstained`, analogous to the lexical API. Cosine score is a retrieval
diagnostic, **not confidence**, probability, policy authority or business readiness.
No business field is derived from similarity.

The backend resolves a Hugging Face model revision before loading, downloads only
the chosen model's inference files into the ignored `.cache/phase2d-model/`, and
loads that exact local snapshot with remote code disabled. Runtime metadata records
the resolved revision, file hashes, package versions, actual CPU device, dimension,
pooling, sequence limit and whether model files/weights were downloaded by that
construction. It omits absolute cache paths and private machine identifiers.
The repository dependency file and model name do not pin every dependency or a
permanent revision; recorded versions/hashes identify this run, and cross-runtime
byte-identical model output is not claimed.

### Development evaluation and owner review

```powershell
python -B gateway/domain/evaluation/retrieval/evaluate_embedding_development.py
```

Use the Python executable from the optional runtime environment. The CLI accepts
no arguments, arbitrary question directory or split. It reuses the unchanged
Phase 2C frozen Development loader and evaluation/metric functions, including all
custody protections and the same 15 IDs and receipt documented above. The
retriever receives only question text and `top_k=10`; labels/rationale never enter
the index or query encoding. The same 14 ANSWERABLE / 1 NEGATIVE denominators and
Gold-versus-required-section distinctions apply.

New artifacts are written only to `artifacts/retrieval_dev_embedding_baseline/`:
`DEVELOPMENT_RESULTS.json`, `DEVELOPMENT_REPORT.md` and `RUN_MANIFEST.json`.
An existing output directory is refused before model initialization. The report
retains every failure and compares all metrics with the read-only historical
Phase 2C results, without re-running BM25. The manifest records configuration,
runtime identity, input/code/output hashes and preserved Phase 2C artifact hashes.
The base commit is distinguished from the uncommitted candidate source hashes.

This is **DEVELOPMENT only**, not evidence of held-out superiority. No HELD_OUT
question, result, private authoring material or Gold is accessed. Configuration is
frozen before seeing results. No model/threshold sweep or post-result tuning is
allowed in this baseline. Stop after the first valid baseline for owner review.
A future query-instruction or threshold experiment must be separately labeled
Development tuning and must not overwrite either baseline.

### Offline tests and separate manual model smoke

```powershell
python -B -m unittest discover -s gateway/domain/tests -p 'test_embedding*.py' -v
```

These tests use injected deterministic encoders and an isolated standard-library
subprocess. They require no network, downloaded weights, GPU or vLLM. Phase 2A/2C
and deterministic regression commands above remain unchanged.

For an explicitly manual smoke check **after provisioning the model**, outside
ordinary CI and without evaluating any question set:

```python
from gateway.domain.retrieval import SectionStore
from gateway.domain.retrieval.embedding_retriever import (
    EmbeddingRetriever, SentenceTransformerBackend,
)

# Supply the resolved revision recorded in RUN_MANIFEST.json for exact cache lookup.
backend = SentenceTransformerBackend(revision="<recorded-model-revision>", local_files_only=True)
retriever = EmbeddingRetriever(SectionStore.load(), encoder=backend)
assert retriever.embedding_dimension == 384
assert retriever.search("   ").abstained
print(retriever.search("synthetic retrieval smoke query").status)
```
