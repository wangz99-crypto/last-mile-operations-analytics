# Frozen V1 domain contract — Phase 1A-1

Contract version: `1.0`. Policy bundle: `last-mile-exception-triage-demo`, `1.0-demo`.
Authority: repository-root `PROJECT_SPEC.md`, approved final revision.

These are fictional demo operating policies, not real carrier/industry standards.
Only artifacts, shape/reference validation and offline tests exist in this phase.
No exception computation, aggregation, API, database loader, search, model or scoring is implemented.

## Inventory and placement

| Artifact | Purpose |
|---|---|
| `policy/policy_registry.json` | Canonical numeric constants, 17 rules, eight evidence requirements, scopes and SOP mappings |
| `policy/artifact_manifest.json` | SHA-256 checksums of the frozen JSON/Markdown contract artifacts, excluding this checksum file itself |
| `schemas/contracts.schema.json` | JSON Schema definitions for canonical data, enums, result/gold labels, fixtures and retrieval questions |
| `sops/last_mile/*.md` | Eight SOPs with 25 stable sections |
| `examples/*.example.json` | Two manually labeled, unscored schema examples, not the future 54-case dataset |
| `validate_contracts.py` | Offline structural validation, with no decision logic |
| `tests/test_contracts.py` | Focused stdlib tests; independent of legacy application imports/conftest |

SOPs deliberately live outside `gateway/kb`. The legacy application recursively loads all Markdown under that directory (`gateway/src/app.py`, `build_kb_index`), so the suggested `kb/last_mile` placement would change `/ask` behavior even without editing application code. A later retrieval phase can explicitly opt into this corpus. Do not move it into the legacy index now.

## Version, time and hashes

The first fictional bundle is effective on `[2026-09-26T00:00:00Z, infinity)`; JSON `effective_to: null` denotes an open end. This date is an artifact-authoring choice allowed by the specification, not a carrier fact. Every section inherits the same interval and bundle version. Future substantive contract changes require a new version and explicit compatibility review.

Canonical timestamps are UTC RFC3339 strings ending in `Z`; naive strings fail validation. Raw invalid/offset input belongs to the explicitly marked validation-case profile until a future normalization layer exists. No `ingested_at`, `source_cutoff` or coverage intervals are V1 record fields.

A fixture manifest checksum is SHA-256 of **only the `input` object**, serialized as UTF-8 JSON with sorted keys, separators `(',', ':')`, `ensure_ascii=False`, and no NaN/Infinity. Thus gold labels are not part of the shipment snapshot. The artifact manifest separately hashes entire file bytes, including examples/gold. Registry digest is the SHA-256 entry for `policy/policy_registry.json`; no self-referential embedded checksum is needed. Freeze a new manifest after an intentional reviewed edit, never merely to conceal a failing consistency check.

## Schema entry points and constraints

Use `schemas/contracts.schema.json#/$defs/<name>` as a schema entry point. Definitions are shared locally; no network resolution is required.

| Definition | Contract |
|---|---|
| `manifest` | snapshot ID, as-of, dataset version, input checksum |
| `shipment` | `PRIMARY KEY (snapshot_id, shipment_id)`; strict statuses, nullable carrier/facility/promise/delivered timestamp |
| `tracking_event` | key `(snapshot_id, source_system, event_id)`; composite shipment FK; strict event codes; failure requires attempt identity |
| `history_declaration` | composite shipment primary/FK, explicit boolean history completeness |
| `assessment`, `expected_result` | Independent category result/eligibility/state/evidence/blockers and aggregate labels; no computation |
| `shipment_blocker`, `category_blocker`, `warning` | Distinct typed scopes; warnings are not decisions; unknown categories retain local blockers |
| `fixture` | frozen input, policy reference, independently authored gold and provenance |
| `retrieval_question` | split/family, answerability, exact versioned section gold and reviewer rationale |

All canonical record keys must be present; use allowed null values rather than omitted columns. Foreign keys and uniqueness are represented by `x-primary-key` / `x-foreign-key` annotations and checked by the validator for canonical fixtures. Standard JSON Schema alone cannot enforce relational keys. Exactly three category assessments are required, once each. Evidence missing/conflicting IDs must refer to required evidence IDs. The validator checks structure, not whether a gold outcome is correct.

The lightweight validator supports only the schema keywords used here and rejects unsupported keywords rather than pretending to be a full JSON Schema engine. `ATTEMPT_FAILED` requiring non-null `attempt_id`, relational keys, exact category coverage and answerable/negative conditions have explicit structural checks. It does not import FastAPI, embeddings, providers, a rule engine or third-party schema packages.

## Input validation cases versus canonical records

The approved spec both defines strict enums and requires testing unknown/missing/conflicting inputs. Resolve these at the fixture boundary:

- `CANONICAL`: every row conforms to its canonical schema, has unique composite identity and valid FKs, and every shipment has an explicit history declaration. `history_complete: false` is valid data, not a schema failure.
- `RAW_VALIDATION_CASE`: rows remain raw JSON objects, with nonempty `expected_input_findings` describing invalid paths/reasons. This allows unknown event codes/statuses, missing attempt IDs, duplicate events, absent history declarations or broken snapshot references to reach future validation tests. These rows must never be silently treated as normalized records.
- The outer fixture manifest remains valid so the test itself is identifiable and reproducible. Invalid shipment-level snapshot identity can be represented in raw rows. Missing/invalid raw input is not made valid by this profile; it is intentionally preserved for a future validator.
- `expected_results[].input_shipment_index` is a zero-based row locator, useful when a deliberately invalid shipment ID cannot identify the case. It is not an operational identifier. Use null expected identity only where raw data lacks it. One expected result per input shipment is structurally required.

No ingestion, normalization, deduplication, timestamp arithmetic or evidence gate is performed here. Duplicate raw messages remain available to later deduplication tests.

## Decision and evidence boundaries

Constants are configured only in the registry. SOPs reference their symbolic names, not independently maintained numeric values. Tests assert approved values as regression expectations, not as another configuration source.

Each L/S/F rule lists category/decision inputs as `decision_dependency_ids` (renamed from `evidence_requirement_ids`). This metadata is not a mandatory checklist to copy into every Gold evidence object. Common evidence is identity/status/policy context; there is no blanket `E-HISTORY`. Late readiness does not require tracking history. Stale and attempt decisions need their relevant complete history; address state needs sufficient explicit marker history. A missing attempt ID does not invalidate a separately verified address marker.

Documented aggregation order is shipment-global blockers → any ready category → any review category → any monitor category → normal. This is a contract only; no function executes it. `READY_TO_ESCALATE` always stops at human review and never means permission to act.

An independently supported eligible subtype can support the combined failed/address category. Its gold `subtype_assessments` and `supported_triggers` name that scope; unresolved other subtypes remain visible. If both triggers are claimed, both need evidence. The two examples avoid inventing subtype outcomes when neither subtype is known active.

`assessment.evidence` is the evidence gate for an actionable or unresolved category decision, not all facts used to classify it. A valid FALSE or NOT_APPLICABLE category with NORMAL state may have NOT_APPLICABLE completeness and empty required/missing/conflicting IDs. Classification support remains in rule IDs, derived facts and fact references. MONITOR, READY_TO_ESCALATE and NEEDS_REVIEW require the evidence relevant to the active decision/review, including separately scoped subtype gaps where applicable. The validator checks declared contract consistency; it does not evaluate those dependencies or decide state.

Observed last-scan timestamp/gap may be manually labeled from the supplied events even when `history_complete` is false, per the spec's observed-event definition. These observed values do not establish that no later scan is missing; stale classification remains UNKNOWN. There is no change to the approved late/history dependency boundary.

## SOP metadata format and mappings

One fenced JSON metadata block per document. `policy_id`, `title`, `version`, `effective_from`, `effective_to`, `exception_types` and `demo_policy` are document-level values inherited by every retrievable section. Each `sections[]` item supplies stable `section_id`, section title, applicable `rule_ids` and `requirement_ids`. A heading `## <section_id>` marks the corresponding text. This yields complete identity `(policy_id, version, section_id)` without copying the full header into every paragraph.

Registry rule/evidence mappings separate `support_sections` from `failure_guidance_sections`. E-POLICY-CONTEXT uses SOP-05#common-evidence as support and SOP-07#missing-policy only as failure guidance; E-POLICY-SECTIONS uses SOP-06#handoff-boundary as support and SOP-07#missing-policy only on the corresponding failure. Other insufficient-evidence mappings follow the same distinction. Healthy/ready Gold citations must support the declared decision/output, not mechanically union all mappings. Failure guidance can explain an explicitly unresolved rule or evidence gap; it is never mandatory for healthy cases. Metadata backlinks enumerate the union of both roles, preserving traceability without making both mandatory citations. Cross-cutting context sections can legitimately have empty backlinks; they are guidance, not another decision rule. Rule decision sections plus applicable evidence sections and `SOP-06#handoff-boundary` form required readiness support. F-UNKNOWN records common `decision_dependency_ids`, `subtype_dependency_ids.FAILED_ATTEMPT = [E-FAILED]` and `subtype_dependency_ids.ADDRESS_EXCEPTION = [E-ADDRESS]`. Its structured `subtype_readiness_contract` requires any fully supported eligible subtype, names F-2/F-3 trigger rules and explicitly states that an unresolved other subtype does not block readiness. No prose parsing or unconditional union is needed.

Automated checks cover IDs, duplicate identities, mapped-section existence, metadata versions/intervals/labels, enum values, constant-reference existence, fixture shape/FKs and checksums. They do **not** establish prose entailment, semantic correctness of policy, or correctness of manual gold. Threshold prose, inequality direction, scope and absence-of-evidence interpretation require human review against the approved spec. Numeric constants are omitted from operational SOP prose to reduce drift without fragile natural-language parsing.

## Future evaluation authoring

Do not generate expected labels from the future implementation. Authors read the policy, manually check arithmetic, supply rationale and record reviewer status. The project owner may be the initial reviewer; disclose the lack of an independent second reviewer. The two examples are `example_only: true`, `split: EXAMPLE`, review status DRAFT, and must not count toward the 54 scored cases unless later approved.

The fixture contract supports all three classifications/states, eligibility, exact SOP sections, common/category evidence, missing/conflicting requirement IDs, global/local blockers, warnings and manual derived facts. Freeze 18 development and 36 initially held-out cases later and report separately. Passing 54 fixtures would demonstrate policy conformance, not real-world 100% accuracy.

Initially held-out inputs may be stored in the repository, but their Gold labels must remain outside the implementation-visible repository until the first held-out evaluation. Keep the combined input/Gold fixture contract for the evaluator; store input-only snapshot packets without dummy or exposed expected_results in the implementation repository. After the first held-out evaluation, runs following fixes must be labeled regression results, not a new blind held-out result. No scored dataset is created in this patch.

The retrieval-question contract allows ANSWERABLE with nonempty relevant `gold_sections` and a `required_sections` subset for multi-section answers. NEGATIVE must have empty gold/required sections and an OUT_OF_SCOPE, UNANSWERABLE or VERSION_CONFLICT reason. The gold policy version is the active policy against which a negative question should abstain; never invent a relevant section for it. No 45-question dataset or scoring code is created now.

## Offline commands

From repository root, with Python 3.11+:

```text
python -B gateway/domain/validate_contracts.py
python -B -m unittest discover -s gateway/domain/tests -p "test_*.py" -v
```

No package install, external service, GPU or model is required. The second command intentionally avoids the legacy `gateway/tests/conftest.py` and application imports. Root pytest configuration and CI deployment are unchanged in this phase.

## Clarifications frozen in this phase

1. Effective date and checksum serialization were unspecified; the concrete demo interval and hashing contracts above resolve them.
2. Strict canonical enums coexist with malformed-input evaluation via an explicit raw-fixture profile, not relaxed production enums.
3. Composite keys scope events and history to a snapshot; cross-snapshot records are never implicitly joined.
4. Address/attempt dependency separation and observed-versus-complete scan history are made explicit without changing approved thresholds or adding categories.
5. SOP placement is isolated from the recursive legacy KB loader. No old IT file, root README, application code, provider or deployment configuration was changed.

Remaining human work: review the prose and illustrative labels before promoting them into independently authored scored fixtures. Provider choice remains deferred. Structural validation does not replace this review or block the next deterministic-contract implementation preparation phase.
