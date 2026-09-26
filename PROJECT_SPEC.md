# Last-Mile Exception Triage
## Evidence-Backed Delivery Exception Triage & Escalation

Status: **approved in principle with the final V1 revisions below; this phase remains documentation-only**.

Prepared: 2026-09-26. Repository inspected: `llm-internal-assistant`, local HEAD `11a0299`.

This document specifies future behavior. It does not claim that the repository already implements it. All shipment examples, event codes, thresholds, SOPs, and operating policies below are fictional demo artifacts, not carrier standards or policies of a real logistics company. No new implementation, benchmark result, production deployment, or business impact is claimed.

## 1. Project Summary

Build an operations-first decision-support workflow for a Last-Mile Operations Coordinator / Data Operations Specialist. It identifies open shipments needing attention, determines rule-based action states, presents supporting SOP sections, and prepares a factual handoff for human review.

**Structured Facts → Deterministic Rules → SOP Retrieval → LLM Explanation → Human Review**

**Evidence dependencies are category-specific. Missing information blocks only decisions that depend on it unless the issue invalidates the shipment-level assessment itself.**

The project should demonstrate reproducible operations metrics, explicit policy implementation, evidence quality, and measured usefulness of AI explanation. Preserve the FastAPI application and useful gateway infrastructure; replace the IT incident domain incrementally. A small read-only dataset and eight versioned SOPs are sufficient for V1. A microservice rewrite or agent framework is unnecessary.

## 2. Problem Statement

An operations coordinator must reconcile shipment promises, tracking history, and operating procedures to decide which shipments require attention. A generic chatbot can produce plausible prose without establishing whether a shipment is overdue, whether tracking is stale, or whether the evidence for escalation is complete.

| Operational problem | V1 response | Evidence of usefulness to collect later |
|---|---|---|
| Open shipments compete for attention | Deterministic exception queue and explicit action states | Correct queue membership and ordering |
| Timing and attempt calculations are inconsistent | One versioned calculation contract and evaluation timestamp | Boundary and replay tests |
| Procedures are difficult to locate | Stable SOP section references and constrained retrieval | Section-level retrieval relevance |
| Escalations lack required information | Visible evidence checklist and blocking reasons | Correct missing-information behavior |
| AI explanations may add unsupported details | Verified fact packet, grounded drafting, human review | Unsupported-claim rate and task success |

Business-value hypotheses are reduced review effort and better handoff completeness. They must be tested; do not describe them as achieved savings.

## 3. Primary User and Job-to-be-Done

**Primary user:** Last-Mile Operations Coordinator / Data Operations Specialist.

**Job:** “At a known data snapshot, show me which open shipments need attention, why each was flagged, which procedure applies, and what evidence is missing so I can prepare a handoff for a human decision.”

The coordinator inspects an overview, filters a queue, reviews shipment facts and rules, opens the supporting SOP, and optionally requests an explanation/handoff draft. They remain responsible for deciding what to do outside the application. A demo administrator may load approved fixtures and policy versions; that is not authority to approve operational actions.

## 4. Product Boundary

| Inside V1 | Outside V1 |
|---|---|
| Synthetic, non-PII shipment snapshots and tracking events | Live carrier integration or customer records |
| Three named delivery exception categories | General logistics assistance or additional exception categories |
| Read-only calculations, queue, and evidence checks | Shipment mutations, refunds, carrier messages, or action approval |
| Fictional, versioned operating policies | Assertions about real carrier SLAs or industry thresholds |
| SOP retrieval and explanation of verified results | Model-selected facts, thresholds, classifications, or priorities |
| Human-review-only handoff draft | Autonomous execution or a dispatch button |

`READY_TO_ESCALATE` means **the demo policy's escalation conditions and required evidence are satisfied and the case is ready for human review**. It never means approved, sent, resolved, or executed. The data-quality review status described below is a review reason, not a fourth exception category.

## 5. V1 Workflow

| Step | Owner | Contract |
|---|---|---|
| 1. Select snapshot | Coordinator / application | Freeze `snapshot_id`, `as_of`, `dataset_version`, and policy bundle version for the run |
| 2. Validate inputs | Deterministic layer | Validate snapshot-scoped IDs/joins, event chronology, status consistency, and explicit `history_complete`; scope findings to the decisions they affect |
| 3. Compute facts | Deterministic layer | Compute elapsed durations, last qualifying scan, unique attempts, and provenance references |
| 4. Evaluate rules | Deterministic layer | Evaluate each of the three categories as true, false, unknown, or not applicable; attach rule IDs |
| 5. Resolve policies | Deterministic resolver + retrieval | Rule IDs map to exact applicable SOP sections; retrieve those sections and search permitted supplemental guidance |
| 6. Check evidence | Deterministic layer | Check each category’s required fields and policy sections; separate shipment blockers, category blockers, and warnings before aggregation |
| 7. Display queue/detail | Application | Show facts, state, evidence gaps, and SOP independently of model availability |
| 8. Prepare brief on request | LLM or deterministic template | Explain the frozen packet; never write back decision fields |
| 9. Human review | Coordinator | Read/copy a draft; all operational contact, approvals, and changes remain outside this application |

An unavailable LLM leaves steps 1–7 operational. An unavailable or conflicting policy bundle blocks readiness instead of using an invented rule. A ranked-search miss must not erase a verified shipment fact or become an implicit business decision.

## 6. Data Model

Approved V1 storage is a small SQLite database loaded from versioned synthetic CSV/JSON fixtures. This supports inspectable SQL metrics without adding a service. Keep raw fixtures immutable; do not persist every derived field as source truth.

### 6.1 `shipments` — one row per shipment per snapshot

| Field | Type / constraint | Why V1 needs it |
|---|---|---|
| `snapshot_id` | Nonempty string; foreign key to dataset manifest | Frozen evaluation context and first component of shipment identity |
| `shipment_id` | Nonempty synthetic string; unique within snapshot | Second component of shipment identity; no real tracking numbers |
| `carrier` | Controlled fictional identifier; nullable input | Handoff identity and overview dimension; absence blocks readiness |
| `origin_facility_id` | Nullable synthetic identifier | Facility grouping; optional and never a proxy for cause |
| `created_at` | UTC timestamp | Basic temporal validation and dataset cohort provenance |
| `promised_delivery_at` | Nullable UTC timestamp | Late rule and on-time cohort; missing means unknown, not on time |
| `delivered_at` | Nullable UTC timestamp | Delivered-on-time calculation and status consistency |
| `current_status` | `PRE_TRANSIT`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `EXCEPTION`, `DELIVERED`, `CANCELLED` | Explicit open/closed partition at the snapshot |
| `source_system` | Controlled demo source identifier | Provenance and handoff evidence |

Define `PRIMARY KEY (snapshot_id, shipment_id)`. Every shipment join and provenance reference must carry both components; the same shipment may appear in multiple immutable snapshots.

Open statuses are the first four values. `DELIVERED` and `CANCELLED` are closed. A failed attempt is an event, not a terminal shipment state. Unknown statuses must be flagged, not coerced into an open/closed value.

Do not require `order_id`: shipment identity is sufficient and order-level analysis is out of scope. Defer `service_level` and `destination_region`: V1 has one carrier-neutral demo threshold policy, and neither changes a rule. Add them later only for a defined analytical requirement. Do not include names, addresses, phone numbers, coordinates, or free-text customer notes.

### 6.2 `tracking_events` — canonical demo events

| Field | Type / constraint | Why V1 needs it |
|---|---|---|
| `snapshot_id` | Nonempty string | Snapshot context; part of the composite shipment foreign key |
| `event_id` | Nonempty string unique within `(snapshot_id, source_system)` | Snapshot-scoped deduplication and fact citations |
| `shipment_id` | With `snapshot_id`, foreign key to `shipments(snapshot_id, shipment_id)` | Timeline of the correct shipment snapshot |
| `event_time` | UTC timestamp | Event ordering and elapsed-time calculations |
| `event_code` | Canonical enum below | Stable deterministic rules, not arbitrary carrier text |
| `attempt_id` | Required for `ATTEMPT_FAILED`; nullable otherwise | Count physical attempts rather than duplicated event rows |
| `facility_id` | Optional identifier | Display observed scan location without interpreting causality |
| `source_system` | Controlled identifier | Traceability and deduplication namespace |

Canonical codes: `LABEL_CREATED`, `ACCEPTED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `ATTEMPT_FAILED`, `ADDRESS_EXCEPTION`, `ADDRESS_CLEARED`, `DELIVERED`, `CANCELLED`. These are invented demo codes. No real-carrier mapping is claimed. Unknown codes are preserved as validation findings; they do not silently become qualifying scans.

Qualifying physical scans: `ACCEPTED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `ATTEMPT_FAILED`, `DELIVERED`. Address notices, label creation, and cancellation do not reset the tracking inactivity clock. Event identity is `(snapshot_id, source_system, event_id)`; identical duplicates are deduplicated within that snapshot, and conflicting duplicates block only dependent calculations unless they invalidate shipment status or identity. `attempt_id` is distinct per physical attempt within `(snapshot_id, shipment_id)`; repeated messages for one attempt count once. Two failure events without attempt identity do not prove two attempts.

### 6.3 Snapshot and policy inputs

| Entity | Required fields | Contract |
|---|---|---|
| Dataset manifest | `snapshot_id` (primary key), `as_of`, `dataset_version`, checksum | Immutable synthetic snapshot representing what was known at this frozen evaluation state |
| Shipment history declaration | `snapshot_id`, `shipment_id`, `history_complete` | Composite primary/foreign key to the shipment snapshot; boolean explicitly states whether its tracking history is complete, including a complete empty history |
| Policy bundle | `bundle_id`, `version`, `effective_from`, `effective_to`, checksum | Exactly one approved bundle effective at as-of; contains numeric thresholds, rule IDs, evidence registry, SOP mappings |
| Optional `facilities` | `facility_id`, `facility_name` | Small lookup for readable facility filters; omit if IDs suffice; region is unnecessary in V1 |

V1 evaluates only events included in the selected immutable fixture, with valid `event_time <= as_of`. Fixture membership represents what was known; no ingestion clock is needed. Re-running the same snapshot, dataset version and policy version reproduces the same deterministic result. Do not combine status from one snapshot with events from another. Corrections require a new immutable fixture/version. Missing `history_complete` is unknown, never implicitly true, and affects only history-dependent decisions.

**Future enhancement, outside V1:** `ingested_at`, `source_cutoff`, coverage start/end intervals, delayed-event reconciliation and detailed historical replay. They are not V1 schema fields, gates, or required evaluation cases.

### 6.4 Derived facts and data quality

| Derived field | Definition / missing behavior |
|---|---|
| `is_open` | Determined by validated status; null on unknown/conflicting status |
| `hours_overdue` | For open shipments with a valid promise: `max(0, (as_of - promised_delivery_at) / 3600)`; otherwise null |
| `last_scan_time` | Maximum time among observed qualifying scans; null if none |
| `hours_since_last_scan` | `(as_of - last_scan_time) / 3600`; null if unavailable; never substitute zero or creation time |
| `failed_attempt_count` | Count distinct valid `attempt_id` values on observed `ATTEMPT_FAILED` events; null if necessary history/identities are incomplete |
| `address_exception_active` | Latest address marker is `ADDRESS_EXCEPTION`; `ADDRESS_CLEARED` later in time clears it; same-time contradictory markers yield unknown |
| `exception_started_at` | See category definitions below; null where time cannot be established |
| `exception_age_hours` | Nonnegative elapsed hours since the category became active; null remains visibly unknown |
| `fact_refs` | `(snapshot_id, shipment_id)` field paths and `(snapshot_id, source_system, event_id)` references supporting each fact |

Use exact seconds for comparisons and round only for display. Offset-aware input is normalized to UTC; naive timestamps are rejected rather than guessed. V1 uses elapsed hours, with no weekend/holiday/business-hours adjustment. Delivered/status conflicts, future or pre-creation events, unknown status, and contradictory duplicates produce specific findings. Quarantine invalid events from arithmetic and block the dependent category only; invalid shipment identity, invalid snapshot context, or unknown/conflicting open/closed status are shipment-level blockers. Keep unresolved findings visible; do not silently drop contradictions or erase independently supported ready categories.

An exception is a computed snapshot result, not a persisted workflow ticket in V1. Stable identity is `(snapshot_id, shipment_id, exception_type)`. No ticket assignment, notification lifecycle, or resolution workflow is required.

## 7. Exception Taxonomy

Exactly three categories; multiple may apply to one shipment.

| Enum / display | Detection | Exception age origin | Resolution in this demo |
|---|---|---|---|
| `LATE_DELIVERY` / Late Delivery | Open and `as_of > promised_delivery_at` | Promise timestamp | Shipment becomes validly closed; a later snapshot correction is visible as a revision |
| `STALE_TRACKING` / Stale Tracking | Open, valid qualifying scan exists, elapsed time strictly greater than stale threshold | Last qualifying scan + stale threshold | New qualifying scan brings age within threshold, or shipment closes |
| `FAILED_ATTEMPT_ADDRESS` / Failed Delivery Attempt / Address Exception | Open and at least one valid failed attempt or an active address notice | First failed attempt or start of current uninterrupted address-exception episode, whichever relevant active trigger is earlier | Failure history stays relevant until closure; address-only trigger clears on an explicit later `ADDRESS_CLEARED` |

The third category has factual subtypes `FAILED_ATTEMPT`, `ADDRESS_EXCEPTION`, or `BOTH`; these do not add categories. V1 deliberately does not infer that movement after a failed attempt resolved its historical risk. This conservative V1 lifecycle is approved: no cooldown windows, inferred recovery, or carrier-specific rules.

Incomplete input can leave a category `UNKNOWN`. Show confirmed categories plus an assessment warning linked to the unknown category’s blocker; unknown is not false and does not cancel an independently ready category. A shipment with no confirmed category but material missing facts belongs in the review queue with “classification incomplete,” not a fabricated fourth category. Valid closed shipments have no active V1 exceptions; historically late deliveries may still affect the on-time KPI.

## 8. Deterministic Rule Matrix

### 8.1 Approved fictional policy constants

These values are **approved fictional V1 demo-policy defaults**, not real carrier/industry rules or tuned benchmark results. Apply uniformly across fictional carriers in V1.

| Constant | Approved demo value | Meaning / equality behavior |
|---|---:|---|
| `LATE_ESCALATE_HOURS` | 24 elapsed hours | Late detection uses `> 0`; escalation eligibility starts at `>= 24` |
| `STALE_DETECT_HOURS` | 24 elapsed hours | A scan gap of exactly 24 hours is not stale; `> 24` is stale |
| `STALE_ESCALATE_HOURS` | 48 elapsed hours | Escalation eligibility at `>= 48` since the last qualifying scan |
| `FAILED_ATTEMPTS_ESCALATE` | 2 unique failed attempts | One failure is monitored; two or more are eligible |
| `ADDRESS_ACTIVE_ESCALATES` | true | An explicit unresolved address exception is eligible immediately; never infer the actual address defect |

SOP prose must reference these constants and match the structured registry. A policy-version consistency check fails if thresholds or evidence requirements disagree. SOP text and model output cannot silently override the registry.

### 8.2 Rules before the evidence gate

`eligible` below is a boolean/null computed by rules. It is not permission to act. Each category owns its classification, eligibility, required evidence, blockers, and action state. L/S/F rows affect only their category; global D rows are explicitly shipment-scoped.

| Rule ID | Condition | Detection / eligibility | Initial operational disposition | Required SOP section |
|---|---|---|---|---|
| `D-CONTEXT` | Invalid composite shipment identity/snapshot context, or required policy bundle unavailable/ambiguous | Whole assessment cannot be established | Shipment-level `NEEDS_REVIEW` | `SOP-07#missing-facts` / `missing-policy`, if available |
| `D-STATUS` | Status unknown or contradicted by delivered/event facts | Open/closed assessment invalid | Shipment-level `NEEDS_REVIEW` | `SOP-07#data-conflicts` |
| `D-CLOSED` | Valid closed shipment | No active categories; ineligible | `NORMAL`, excluded from open queue | `SOP-01#scope` |
| `L-UNKNOWN` | Open; promise missing/invalid | Late unknown, eligible null | `NEEDS_REVIEW` | `SOP-07#missing-facts` |
| `L-0` | Open; `as_of <= promise` | Late false | No late action | `SOP-02#late-boundaries` |
| `L-1` | `0 < overdue < 24h` | Late true, eligible false | `MONITOR` | `SOP-02#late-monitor` |
| `L-2` | `overdue >= 24h` | Late true, eligible true | Ready candidate; apply evidence gate | `SOP-02#late-escalate` |
| `S-UNKNOWN` | Open in-network status without a qualifying scan, or incomplete history relevant to last scan | Stale unknown, eligible null | `NEEDS_REVIEW` | `SOP-07#missing-facts` |
| `S-PRE` | Valid `PRE_TRANSIT`, complete empty physical-scan history | Stale not applicable | No stale action; late still evaluated | `SOP-03#scan-scope` |
| `S-0` | Gap `<= 24h` | Stale false | No stale action | `SOP-03#scan-scope` |
| `S-1` | `24h < gap < 48h` | Stale true, eligible false | `MONITOR` | `SOP-03#stale-monitor` |
| `S-2` | `gap >= 48h` | Stale true, eligible true | Ready candidate; apply evidence gate | `SOP-03#stale-escalate` |
| `F-UNKNOWN` | Incomplete attempt history, missing attempt IDs, or unknown address-marker ordering | Affected subtype/count unknown; preserve any independently verified trigger | Category `NEEDS_REVIEW` unless an independent subtype’s escalation evidence is complete; report unresolved subtype warning | `SOP-07#missing-facts` |
| `F-0` | Complete history: zero failures and no active address notice | Failed/address false | No failed/address action | `SOP-04#attempt-counting` |
| `F-1` | One failure, address known inactive | Failed/address true, eligible false | `MONITOR` | `SOP-04#single-attempt` |
| `F-2` | At least two distinct failures | Failed/address true, eligible true | Ready candidate; apply evidence gate | `SOP-04#repeated-attempts` |
| `F-3` | Explicit address notice active | Failed/address true, eligible true | Ready candidate; apply evidence gate | `SOP-04#address-notices` |

Run independent rules; do not pick one category with a keyword router. Where a row depends on missing information, do not fall through to a normal row. Closed-status consistency is validated before `D-CLOSED`. A confirmed address trigger may coexist with unknown attempt history: address-based readiness depends on the verified current address state, not attempt counts. Likewise, complete repeat-attempt evidence does not require address evidence unless that address decision is also claimed. Keep unverified subtypes visible and out of the supported escalation scope; do not assert a full subtype assessment when facts are unknown.

### 8.3 Escalation evidence registry

Every requirement is machine-readable with a stable ID and SOP reference. Common evidence covers identity, status and policy context; history is required only for decisions that depend on it. Missing evidence cannot be completed by the LLM.

| Requirement | Applies to / blocker scope | Completeness condition |
|---|---|---|
| `E-IDENTITY` | Common to escalation packets | Composite shipment identity, carrier, source and valid snapshot/as-of. Invalid identity/context is global; missing carrier/source blocks packet readiness for each dependent category without erasing known facts |
| `E-STATUS` | Common / shipment-level | Open/closed status established without conflicting closure facts |
| `E-POLICY-CONTEXT` | Common / shipment-level | Exactly one approved active bundle, with valid version/checksum; absence or ambiguous bundle selection invalidates the assessment |
| `E-LATE` | Late category only | Valid promise and deterministic overdue calculation with field references; **complete tracking history is not required** |
| `E-STALE` | Stale category only | Last qualifying event ID/time/code, computed gap, explicit `history_complete = true`, and no scan-history conflict affecting inactivity |
| `E-FAILED` | Failed-attempt decision only | Complete attempt history (`history_complete = true`), distinct attempt identities, valid failure events/times, and deduplicated count |
| `E-ADDRESS` | Address decision only | Explicit current address-exception state, supporting notice and marker ordering sufficient to establish no later clearance in the frozen snapshot. With incomplete marker history, state is unknown; do not demand attempt identities or a literal customer address |
| `E-POLICY-SECTIONS` | Each supported category/decision | Exact decision and corresponding `SOP-05` evidence sections plus `SOP-06#handoff-boundary`, matching approved version/checksum; missing sections block only the decisions needing them |

V1 uses one explicit `history_complete` declaration rather than coverage intervals. It supports absence-dependent checks for scans, attempts and address clearance; its absence/false value never blocks an independently valid late decision. An invalid attempt identity can block the failed-attempt calculation while leaving explicit address-marker state valid. A conflict affecting current open/closed status is genuinely global.

Within the combined failed-attempt/address category, each claimed escalation trigger needs its own evidence. A fully evidenced eligible trigger can support category readiness while another subtype remains unknown; list that unresolved subtype as a warning and exclude it from the escalation basis. If claiming both triggers, include evidence for both. No additional category or recovery rule is introduced.

`evidence_completeness = COMPLETE | INCOMPLETE | NOT_APPLICABLE` is reported per category and, when needed, per decision/subtype. Complete evidence for the supported escalation basis does not imply all shipment information is complete. Report missing/conflicting item IDs and requirement counts separately; never call the ratio confidence. A missing optional facility or unavailable LLM draft is not required evidence. A monitoring decision with missing evidence on which it depends becomes category `NEEDS_REVIEW`, not a shipment-global veto.

## 9. Action-State Matrix

| Category state | Deterministic meaning | User-facing next step |
|---|---|---|
| `NORMAL` | Applicable category assessment known false/not applicable with no dependent blocker | No action for this category |
| `MONITOR` | Confirmed exception; eligibility not reached; evidence for this decision complete | Monitor under cited policy |
| `NEEDS_REVIEW` | Category decision depends on missing/conflicting facts or policy support, with no independently supported ready trigger | Verify named gaps; no readiness claim for this decision |
| `READY_TO_ESCALATE` | At least one verified eligible trigger with complete dependent evidence and policy support | Human reviews the supported escalation basis; unresolved unrelated findings remain visible |

**Category evaluation order:** validate dependent facts → detect → determine eligibility → verify dependent evidence/policy support → assign category state. Each category retains its own classification, eligibility, requirements, blockers and state. Missing facts do not remove a confirmed trigger or become a claim that an unrelated decision is invalid.

| Finding scope | Examples | Effect |
|---|---|---|
| Shipment-level blocker | Invalid `(snapshot_id, shipment_id)`, invalid snapshot context, unknown/conflicting open/closed status, required policy bundle unavailable or ambiguous | Invalidates whole assessment; aggregate `NEEDS_REVIEW` regardless of category candidates |
| Category-level blocker | Missing promise for late; incomplete scan history for stale; missing attempt identity for failed-attempt decision; unresolved address-marker state; missing category-specific SOP section | Blocks only dependent category/decision; another independently ready category remains ready |
| Warning | Optional facility absent; supplemental search unavailable; unrelated category/subtype unknown alongside a ready category | Visible diagnostic with scope and references; never independently changes state. An unknown still has its actual local blocker, not just a warning |

**Shipment aggregation, in order:**

1. Any shipment-level blocker → `NEEDS_REVIEW`.
2. Otherwise any category `READY_TO_ESCALATE` → `READY_TO_ESCALATE`.
3. Otherwise any category `NEEDS_REVIEW` → `NEEDS_REVIEW`.
4. Otherwise any category `MONITOR` → `MONITOR`.
5. Otherwise → `NORMAL`.

| Example (not a measured result) | Category outcomes | Aggregate / brief scope |
|---|---|---|
| 24h overdue; valid identity/status/promise/policy; tracking history incomplete | Late ready; stale and failed/address unknown/review | Ready for **late delivery only**; retain tracking/attempt warnings and gaps |
| Promise missing; complete scan history proves 48h gap; other required evidence valid | Late review; stale ready | Ready for **stale tracking only**; missing promise remains visible |
| Valid late candidate but open/closed status conflicts | Whole assessment invalid | Needs review; no category can authorize a ready shipment packet |
| One failed attempt with complete history; other categories normal | Failed/address monitor | Monitor |

**Priority is separate:** `HIGH` if any verified escalation trigger is met, including a category-blocked candidate; `MEDIUM` for remaining `NEEDS_REVIEW`; `LOW` for remaining `MONITOR`/`NORMAL`. Do not call a trigger verified when invalid global facts undermine it. Unknown risk does not justify inventing a high-risk fact. Queue sort: `NEEDS_REVIEW` and `READY_TO_ESCALATE` in an attention group, then priority high-to-low, oldest known exception age, then shipment ID. Show unknown-age records in a dedicated subgroup rather than treating null as zero. State filters remain explicit.

Recompute on a new immutable snapshot. Human review does not edit rule output; changed evidence requires an attributable fixture/version. No “approved” or “sent” state is introduced. A ready brief names only independently supported categories/triggers and separately discloses unresolved findings.

## 10. SOP / Knowledge Model

Eight short fictional SOPs; no IT runbooks in the active last-mile index. These are planned documents, not created in this phase.

| Policy ID / proposed file | Purpose | Stable sections to author |
|---|---|---|
| `SOP-01` / `exception_classification.md` | Scope, categories, state aggregation | `scope`, `taxonomy`, `state-precedence` |
| `SOP-02` / `late_delivery.md` | Promise comparison and late handling | `late-boundaries`, `late-monitor`, `late-escalate` |
| `SOP-03` / `tracking_inactivity.md` | Qualifying scans and elapsed-time policy | `scan-scope`, `stale-monitor`, `stale-escalate` |
| `SOP-04` / `failed_attempt_address.md` | Attempt identity, repeated failures, address notices | `attempt-counting`, `single-attempt`, `repeated-attempts`, `address-notices` |
| `SOP-05` / `escalation_evidence.md` | Machine-checkable required evidence | `common-evidence`, `late-evidence`, `stale-evidence`, `attempt-address-evidence` |
| `SOP-06` / `carrier_handoff.md` | Human-readable draft content and boundary | `handoff-fields`, `handoff-boundary` |
| `SOP-07` / `insufficient_evidence.md` | Nulls, contradictions, abstention | `missing-facts`, `data-conflicts`, `missing-policy` |
| `SOP-08` / `operations_audit.md` | Reproducibility, provenance, no-PII logging | `decision-record`, `revision-history`, `data-minimization` |

| Metadata | Requirement |
|---|---|
| `policy_id`, `title`, `version` | Required; proposed first versions `1.0-demo` |
| `effective_date`, `effective_to` | UTC validity interval `[effective_date, effective_to)`; approved date to be chosen with fixtures |
| `exception_type` | Array of the three allowed types; cross-cutting policies explicitly cover all |
| `section_id`, `section` | Stable machine ID and readable heading, required on every retrievable unit |
| `rule_ids`, `requirement_ids` | Links to structured rule/evidence registry where applicable |
| `demo_policy`, `content_hash`, `source_path` | Required label `demo_policy: true`, immutable content identity, displayable source |

Chunk by section first. If a section needs subchunks, retain the same section identity and ordered subchunk IDs. Citation identity is `(policy_id, version, section_id)`, not a filename, score, or transient numeric chunk index. Never mix policy versions in one explanation. At an effective-date boundary choose the new interval; overlapping active bundle versions block the whole assessment; a section-specific registry/text mismatch blocks only decisions depending on that section.

## 11. RAG Responsibilities

| RAG should retrieve | RAG must not decide |
|---|---|
| Applicable SOP sections and supporting passages | Whether a shipment is late or open |
| Escalation evidence requirements as published explanations | Elapsed hours, attempt counts, thresholds, priority, or action state |
| Handling of missing facts and special cases within the three categories | Carrier facts, missing tracking events, or root cause |
| Human handoff and audit guidance | Permission to contact a carrier or approve an action |

Rules deterministically produce required section IDs. Resolve these by exact metadata lookup before drafting. Use ranked search only for relevant supplemental SOP passages and SOP questions, filtered by approved bundle/version/type. Search ranking must not substitute an incompatible SOP for the required one. In a corpus of eight documents, direct lookup may outperform semantic retrieval for case handling; evaluate that possibility rather than adding RAG for appearance.

Return ranked section identities, supporting excerpts, retrieval method, and timing. Similarity scores are retrieval diagnostics, not business confidence. On a search miss, label support unavailable; attempt exact required-section lookup if not already resolved and report this fallback separately. If mandatory category sections remain unavailable, only dependent category decisions become `NEEDS_REVIEW`; an unavailable required policy bundle is a shipment-level blocker. Never invent a procedure or erase another category’s independently supported readiness. Supplemental-search failure with mandatory support intact does not change the rule state.

## 12. LLM Responsibilities and Prohibited Behaviors

| Permitted | Prohibited |
|---|---|
| Summarize the provided verified facts | Calculate SLA status, durations, counts, KPIs, or thresholds |
| Explain supplied rule IDs/outcomes in plain language | Choose or change classifications, states, priority, or evidence requirements |
| Summarize retrieved and version-verified SOP excerpts | Invent events, addresses, shipment details, or policy text |
| Compose a handoff draft naming gaps and citations | Infer unsupported causes such as weather, driver error, or facility overload |
| State that a human must review | Approve actions, contact carriers, issue refunds, or alter shipments |

Input is an immutable fact/rule/evidence packet plus permitted SOP excerpts, not a request for the model to reason from raw operational data. Output is a constrained explanation object containing text blocks with `fact_refs` and `policy_refs`. It has no writable decision fields or execution tools. Drafts distinguish supported escalation categories/triggers from unresolved category blockers and warnings; aggregate readiness never implies every category is complete.

Validate the response schema, referenced IDs, required human-review notice, and supplied numeric/entity values. These checks do not prove semantic entailment; manually evaluate claim support and adversarial prompts before making quality claims. On invalid, unsupported, missing-policy, or failed model output, suppress the generated draft and display a deterministic template of verified facts and gaps. Do not change the triage state merely because generation failed.

Treat SOP passages as evidence, not executable instructions. Exclude arbitrary user instructions from the drafting contract. Fixed templates must also avoid unsupported inference. No confidence percentage is shown. V1 needs at most one generation call per requested brief; no model call for overview or queue construction and no autonomous retry loop.

## 13. Proposed UI

### 13.1 Operations Overview

Layout: snapshot/as-of and demo-policy banner → KPI cards → carrier/facility/type filters → exception queue. No chat box on the landing page. Each KPI reveals numerator, denominator, exclusions, and window on demand.

| KPI | Exact proposed definition | Missing/overlap behavior |
|---|---|---|
| On-Time Delivery Rate | Among valid, non-cancelled shipments whose promise lies in selected `[window_start, window_end)` with `window_end <= as_of`: delivered-at `<=` promise / eligible shipments | Due but still open shipments stay in denominator and are not on time; missing/invalid promises or conflicting statuses excluded with explicit counts; zero denominator → N/A |
| Open Exception Rate | Unique valid open shipments with at least one confirmed active category / all valid open shipments | Multiple categories count once in headline; unknown-only cases remain in denominator and have a separate assessment-incomplete count |
| Ready-to-Escalate Cases | Unique open shipments with aggregate state `READY_TO_ESCALATE` | Not sum of category rows; ready shipments with unrelated review categories remain counted, with unresolved-category badges shown separately |
| Median Exception Age | Median of per-shipment maximum age among confirmed active categories in valid open shipments | Null-only ages excluded with count; not incident resolution time or MTTR |

On-time exclusions use status at the selected snapshot: cancelled shipments are excluded regardless of cancellation timing. Label this simplified demo convention and count exclusions; do not claim a real carrier SLA measure. Missing carrier/facility groups display `UNKNOWN` without silently dropping rows. Facility means **origin facility**, not inferred responsibility for an exception. Exception-type breakdowns can overlap and must not be summed as unique shipments.

Display data-quality/coverage counts next to KPIs so incomplete data cannot appear as good performance. Overall cards use carrier/facility filters; type filters apply to exception views, not the on-time denominator. Label the different populations. Freeze snapshot and policy context across all views.

### 13.2 Exception Queue

One row per `(snapshot_id, shipment_id)`: shipment ID, carrier, origin facility, category badges/states, maximum known exception age, priority, aggregate action state, category-scoped missing-evidence counts, snapshot time. Include non-normal cases plus material assessment-incomplete records; hide valid closed/normal rows by default. Selecting a row opens detail. Filters and sorting must be deterministic and show result counts.

### 13.3 Exception Detail

| Panel | Required content |
|---|---|
| 1. Verified Shipment Facts | Source fields, observed event timeline, as-of, computed durations, fact references; nulls remain visible |
| 2. Triggered Rules | Every relevant rule ID, input operands, exact comparison, policy version; distinguish false/unknown/not applicable |
| 3. Action State | Per-category and aggregate state, eligibility and blocking reasons; priority separate |
| 4. Applicable SOP | Required section citations, version, effective date, supporting excerpts; no decorative unrelated citations |
| 5. Evidence Completeness | Present, missing, and conflicting required items; where each item should come from |
| 6. Handoff Brief | Generate on request; label LLM vs template; verified context, rule rationale, SOP support, missing items, human-review request |
| 7. Human Review Boundary | Persistent “Draft only. Human review required. Nothing has been sent or changed.” |

Provide “Generate draft” and “Copy draft”; do not provide send, approve, refund, reschedule, or carrier-contact controls. A shipment-global blocker prevents an escalation-ready brief. A category-local blocker limits only that category: another ready category may have a scoped escalation brief, with unrelated gaps clearly disclosed. Show text states and blockers rather than relying on color alone.

## 14. Response / Triage Object Schema

Retain the existing envelope concept (`request_id`, status, timing, sources, metadata) but introduce a versioned domain object. Do not force it into the legacy confidence-based `answer` contract. The approved migration introduces a versioned `/triage` path/contract while retaining legacy `/ask` temporarily; retire legacy surfaces only after the new workflow is stable.

| Path | Type / enum | Authority / invariant |
|---|---|---|
| `schema_version` | `triage.v1` | Explicit response contract |
| `status`, `request_id` | Transport status and request ID | Transport failure is not `NORMAL` |
| `meta` | Snapshot ID, as-of, data/policy/code versions, checksums | Same immutable context for facts, metrics, retrieval and brief |
| `triage.snapshot_id`, `triage.shipment_id` | Strings | Composite source identity; snapshot must equal `meta.snapshot_id` |
| `triage.facts` | Source values, derived values, `fact_refs` | Deterministic; unknown values null |
| `triage.assessments[]` | Exactly three category assessments | Each owns `exception_type`, classification `result: TRUE / FALSE / UNKNOWN / NOT_APPLICABLE`, rule IDs, operands, `escalation_eligible` boolean/null, `evidence`, `blockers[]`, and `action_state`; combined category also identifies supported/unknown subtype decisions |
| `triage.active_exception_types[]` | Subset of three enums | Only confirmed categories, no duplicates |
| `triage.action_state` | Four allowed states | Deterministic aggregate, never model-generated |
| `triage.priority` | LOW / MEDIUM / HIGH | Deterministic separate field |
| `triage.common_evidence` | Identity/status/policy-context items and missing/conflicting refs | Shared dependencies only; no blanket tracking-history requirement |
| `triage.assessments[].evidence` | Completeness for supported decision, required/missing/conflicting items and counts | Category/decision-scoped; not overwritten by unrelated evidence gaps |
| `triage.assessments[].blockers[]` | Stable code, dependent decision, field/section refs, reason | Local blockers; unknown subtype blockers remain visible even if an independent subtype supports readiness |
| `triage.shipment_blockers[]` | Stable code, field/context refs, reason | Only genuinely global blockers; cannot contain an unrelated category evidence gap |
| `triage.ready_categories[]` | Subset of three enums | Independently ready categories; brief scope also identifies supported subtype triggers |
| `sources[]` | Policy ID/version/section, excerpt, hash, retrieval method/rank | Version verified; score optional and not confidence |
| `explanation` | `status`, `engine`, text blocks, fact/policy refs | Separate LLM/template artifact; reject decision mutations |
| `review_boundary` | `human_review_required: true`, `actions_executed: []` | Constant boundary; readiness never populates actions |
| `timings_ms`, `usage`, `warnings[]` | Phase durations, call/token counts, scoped warning diagnostics | Warnings link category/blocker refs when relevant and do not independently change state; real measurements only |

Illustrative fragment only, **not a measured response**. Assume valid common identity/status/policy evidence and late-specific SOP support; detailed rule operands, evidence references, and source excerpts are omitted for brevity. Incomplete tracking history does not invalidate late readiness.

```json
{
  "schema_version": "triage.v1",
  "status": "ok",
  "request_id": "illustration-only",
  "meta": {
    "snapshot_id": "demo-snapshot-01",
    "as_of": "2026-09-26T12:00:00Z",
    "dataset_version": "demo-v1",
    "policy_bundle_version": "1.0-demo"
  },
  "triage": {
    "snapshot_id": "demo-snapshot-01",
    "shipment_id": "DEMO-SHP-001",
    "facts": {
      "current_status": "IN_TRANSIT",
      "promised_delivery_at": "2026-09-25T12:00:00Z",
      "hours_overdue": 24,
      "carrier": "DEMO-CARRIER",
      "history_complete": false
    },
    "active_exception_types": [
      "LATE_DELIVERY"
    ],
    "action_state": "READY_TO_ESCALATE",
    "priority": "HIGH",
    "shipment_blockers": [],
    "common_evidence": {
      "completeness": "COMPLETE"
    },
    "ready_categories": [
      "LATE_DELIVERY"
    ],
    "assessments": [
      {
        "exception_type": "LATE_DELIVERY",
        "result": "TRUE",
        "escalation_eligible": true,
        "action_state": "READY_TO_ESCALATE",
        "evidence": {
          "completeness": "COMPLETE",
          "missing_items": []
        },
        "blockers": []
      },
      {
        "exception_type": "STALE_TRACKING",
        "result": "UNKNOWN",
        "escalation_eligible": null,
        "action_state": "NEEDS_REVIEW",
        "evidence": {
          "completeness": "INCOMPLETE",
          "missing_items": [
            "E-STALE:history_complete"
          ]
        },
        "blockers": [
          {
            "code": "INCOMPLETE_SCAN_HISTORY",
            "dependent_decision": "STALE_TRACKING"
          }
        ]
      },
      {
        "exception_type": "FAILED_ATTEMPT_ADDRESS",
        "result": "UNKNOWN",
        "escalation_eligible": null,
        "action_state": "NEEDS_REVIEW",
        "evidence": {
          "completeness": "INCOMPLETE",
          "missing_items": [
            "E-FAILED:history_complete",
            "E-ADDRESS:marker_state"
          ]
        },
        "blockers": [
          {
            "code": "INCOMPLETE_ATTEMPT_ADDRESS_HISTORY",
            "dependent_decision": "FAILED_ATTEMPT_ADDRESS"
          }
        ]
      }
    ]
  },
  "warnings": [
    {
      "code": "UNRESOLVED_OTHER_CATEGORIES",
      "categories": [
        "STALE_TRACKING",
        "FAILED_ATTEMPT_ADDRESS"
      ],
      "message": "Late-delivery readiness is independently supported; other categories require review."
    }
  ],
  "explanation": {
    "status": "NOT_REQUESTED",
    "engine": null
  },
  "review_boundary": {
    "human_review_required": true,
    "actions_executed": []
  }
}
```

Identity, duration, category, threshold, and evidence fields are validated server-side. The model cannot replace this object. Schema validity alone does not count as successful triage.

## 15. Evaluation Strategy

Design and freeze policy, labels, and scoring before application implementation. No results are asserted here. Use fixed clocks and immutable snapshots. Ground truth is independently authored from the written policy, never obtained by running the implementation being scored.

### A. Policy-Conformance Cases — 54 synthetic scenarios

| Primary bucket | Count | Required coverage |
|---|---:|---|
| Normal / closed controls | 8 | In-transit on time; pre-transit; valid delivered/cancelled; no active exception |
| Late delivery | 10 | Exactly promise, one second after, just below/at 24h, missing promise, overdue but blocked |
| Stale tracking | 10 | Exactly/just above 24h, just below/at 48h, physical vs administrative events, recovery scan |
| Failed attempt / address | 10 | One/two unique attempts, repeated messages, missing identity, explicit address clear, unresolved address |
| Data quality / policy support | 10 | Missing scan, explicit incomplete history, contradictory closure, duplicate conflict, unknown code, invalid/future timestamp, missing/overlapping policy |
| Multiple simultaneous categories | 6 | Category-local blockers versus shipment-global veto; ready late with missing tracking history; ready stale with missing promise; priorities and unique-shipment counts |
| **Total** | **54** | Buckets are primary assignments; cases may cover several edges |

Create 18 development and 36 held-out cases, stratified by bucket and grouped by scenario family. Do not split trivial timestamp variants of the same scenario across sets. Include timezone-offset equivalence, composite snapshot-key isolation, immutable-fixture reproducibility, explicit history completeness, and policy-version boundaries across these buckets. V1 has no ingestion-cutoff test cases. The small sample is a starting evaluation, not a production guarantee.

| Label field | Independent expected content |
|---|---|
| `expected_assessments` | Three true/false/unknown/not-applicable category labels with rationale |
| `expected_action_states` | Per-category and aggregate state |
| `expected_priority` | LOW/MEDIUM/HIGH with explicit trigger |
| `expected_policy_sections` | Exact policy/version/section tuple set |
| `expected_evidence` | Common and category/decision completeness plus missing/conflicting requirement IDs |
| `expected_blockers_and_warnings` | Shipment-global blockers, category-local blockers, and scoped warnings separately labeled |
| `expected_facts` | Manually checked durations, event references, attempt counts, age |

The project owner may serve as the initial policy owner and label reviewer. Author expected outcomes from the written policy independently of the evaluated implementation; an independent worksheet may assist arithmetic but must not import that implementation. Review labels before coding, record rationales and author/reviewer identity, and disclose when one person holds both roles. A second human reviewer is desirable but not an implementation blocker. Fix policy ambiguity before scoring; preserve any later adjudication history.

Report category-label exact match, aggregate/per-category action-state accuracy, expected-section exact match, evidence-gap precision/recall, and false-ready cases. A valid closed case must not enter the open exception queue. Engineering acceptance target: all 54 approved deterministic fixtures conform, with zero false-ready outcomes. Report the 18 development and 36 initially held-out cases separately, including first held-out results and subsequent regression results after fixes. Even a future 54/54 pass means policy-conformance/regression success on these synthetic fixtures, **not real-world 100% operational accuracy**; no such result is asserted here. Test SQL KPIs against separately hand-counted fixture cohorts, including zero denominators and multi-category deduplication.

### B. RAG Evaluation — 45 SOP questions

Five answerable questions for each of eight SOPs (40), plus five unanswerable/out-of-scope/version-conflict questions. Include paraphrases, near-neighbor sections, evidence requirements, and insufficient-information procedures. Gold labels identify **sections and versions**, not only documents. Related wording variants stay in one split. Proposed split: 15 development (14 answerable, one negative), 30 held-out (26 answerable, four negative).

| Metric | Definition |
|---|---|
| Hit@1 | Fraction of answerable questions whose first unique returned section is in the gold relevant-section set |
| Hit@3 | Fraction with a gold relevant section among the first three unique returned sections |
| MRR | Mean reciprocal rank of the first relevant section in a fixed top-10 unique-section list; missing → 0 |
| Required-section coverage | For questions needing multiple sections, retrieved required sections / gold required sections; report full-set success separately |
| Negative-query behavior | Correct abstention rate and false-support rate on the five negative questions; do not assign fabricated gold sections |

Deduplicate subchunks to section identity before ranking. Publish the retrieval depth and method consistently for all systems. Report ranked search separately from exact policy lookup or fallback; never count a hardcoded expected section as a ranked-search success. Retain failures with returned sections, gold labels, and reason. Tune only on development data. An embedding/similarity score is not an evaluation outcome.

### C. End-to-End Evaluation

Run the 36 held-out policy cases through the actual application path with no injected expected decisions, forced source files, or scenario overrides. A fixture selector may select input data only. Run the deterministic end-to-end workflow with template handoffs across all 36 held-out cases. For initial human claim-level LLM evaluation, preselect a stratified subset of approximately 15 of these held-out cases, covering the three categories, normal/review outcomes, ready-with-unrelated-gaps, global blockers, and multi-category cases. Start with one recorded generation per selected case when a model is available; no hosted or paid provider is required yet. Report invalid-input cases as explicit expected review/rejection outcomes, not silently skipped cases. Dataset-load failures count as unsuccessful runs.

**Task Success Rate (TSR)** = number of cases passing **all** applicable requirements below / total scheduled cases in the explicitly identified evaluation run. Report deterministic workflow TSR over all 36 separately from LLM-subset TSR/claim quality over the approximately 15 selected cases. Do not extrapolate subset results to all 36; if generation is deferred, report it as not run.

| Requirement | Pass condition |
|---|---|
| Classification | Complete set of confirmed categories and unknown states matches adjudicated gold |
| Action state | Aggregate and per-category states correct; no unsupported readiness |
| SOP support | Every required decision/evidence claim has the correct active SOP section; expected missing-support cases explicitly abstain |
| Missing-information behavior | Exact mandatory gaps/conflicts surfaced at the correct scope; unrelated gaps do not erase ready categories; no field invented or null treated as normal |
| Factuality | All material operational statements supported by provided facts or cited SOP; numbers match deterministic packet |
| Human boundary | No approval, executed action, unsupported root cause, or assertion that a draft was sent |

Score explanation support by atomized claims with human review; automated schema/reference checks are necessary but insufficient. A model judge may later assist, but is not sole ground truth. Preserve rubrics and disagreement adjudication. Report raw numerators/denominators and uncertainty intervals for proportions; do not overinterpret small-sample differences. Begin with one recorded generation per selected subset case/configuration. Add repeated generations only if observed stochastic behavior materially affects results; document the trigger, selected cases, repeat count and reporting method. Three generations for every held-out case are not a V1 requirement. Separate AI drafting results from template results rather than merging fallback wins into “LLM accuracy.”

Security/failure checks include instruction-like SOP content, requests to ignore policy or send messages, stale policy versions, missing provider, and malformed generated output. No live external-action tools should be available to any configuration.

## 16. Baseline Comparison Plan

Document now; implement and measure later. Do not assume custom code wins.

| Baseline | Planned configuration | Comparison purpose / caveat |
|---|---|---|
| Rules + search only | Same deterministic rules, exact section lookup plus simple search, template handoff, no LLM | Establish whether generation improves usability at all; may be strongest on correctness/cost |
| RAG-only assistant | Same frozen shipment packet and SOP corpus, model asked for sandboxed triage output without executable business-rule tools | Experimental comparator only; its decisions never control the product; test the value of deterministic rules |
| Tool-first workflow | Proposed deterministic triage/evidence gates, exact SOP support plus constrained retrieval, LLM explanation | Test incremental usefulness and quality of the proposed product |
| Managed RAG, e.g. Amazon Bedrock Knowledge Bases | Proposed managed retrieval adapter using the same approved SOP sections and rules; feasibility/configuration to be verified before implementation | Compare managed retrieval to local retrieval with decision logic held fixed; do not attribute rule-engine benefits to the provider |

Two tracks avoid confounding: **retrieval track** holds queries, gold sections, corpus, policy version and retrieval depth fixed; **workflow track** holds shipment snapshots, written policy, test cases and scoring rubric fixed. For the RAG-only experimental arm, the absence of executable rules is the intentional difference. Where possible use the same generation model/settings across LLM arms. If a provider requires different processing or a different model, publish that difference and avoid claiming a clean causal comparison.

| Metric | Reporting contract |
|---|---|
| Task success | TSR with numerator, denominator, failures and model/template mode |
| Escalation correctness | Precision/recall for gold-ready shipment cases, aggregate-state accuracy, false-ready count |
| Citation support | Supported material policy claims / material policy claims requiring citation; no claims → N/A, not 100% |
| Unsupported-claim rate | Unsupported factual/policy claims / all material factual/policy claims; also fraction of cases containing any unsupported claim |
| Latency | p50/p95 measured end-to-end and by phase; document hardware, concurrency, warm/cold conditions |
| LLM calls | Actual generation calls per case and per draft; embeddings and retrieval requests separately counted |
| Cost | Actual request/token/provider charges when available; separately report indexing and inference, and local compute assumptions |

Use identical test splits and the same preselected LLM subset across comparable generation arms; log configurations and corpus checksums. Keep 36-case deterministic and approximately 15-case human-reviewed generation denominators separate. Price estimates must be labeled and dated when later gathered; missing billing is unknown, not zero. No paid provider, cloud account, live credentials, or model download is needed to approve this document. Managed-provider selection and spending require a later human decision.

## 17. Existing Repository Migration Map

Recommendations are grounded in inspected code, not automatic acceptance of a generic migration checklist. All changes in this table are **future work**.

| Existing location / behavior | Decision | Reason and proposed treatment |
|---|---|---|
| `gateway/src/app.py`: FastAPI routes, settings, request IDs | Keep foundation | Existing server is sufficient; add narrowly scoped domain modules/routes instead of rebuilding service infrastructure |
| `gateway/src/app.py`: tool-first early return | Keep concept; redesign inputs | Deterministic work can precede/avoid generation, but shipment triage should be invoked by shipment selection, not English keyword intent |
| `make_ok_envelope`, `make_err_envelope` | Keep structured-envelope concept | Introduce versioned `/triage` while temporarily retaining `/ask`; retire legacy surfaces only after the new workflow is stable. Do not retain confidence as a business field or silently change legacy clients |
| `auth_user`, API-key roles | Keep interface; correct demo privilege behavior | Current demo mode grants admin when no key is provided; not suitable as the new coordinator's default authorization |
| `gateway/src/ui/demo_page.py`: demo admin cookie | Replace behavior | Automatically issuing admin credentials to visitors undermines role separation; public synthetic demo should be read-only and non-admin |
| `write_audit` and request timing in `app.py` | Keep mechanism; extend coverage | Local JSONL is adequate for a demo; several scenario returns precede audit calls. Record every assessment/error path with snapshot, rule/policy versions and result, without raw sensitive text |
| Prometheus counters/histogram and `/health` | Keep; adapt labels/readiness | Distinguish rules, retrieval, and generation timing. Health currently indicates process response, not dataset/policy availability |
| `/kb_status` in `app.py` | Redesign truthfulness | Current counts use `max(files, 1)` / `max(chunks, 1)`; expose real zero/unavailable values rather than presentation-oriented nonzero counts |
| `gateway/src/tools/incident_tool.py`, `data/incidents.json` | Replace domain adapter/data | Two local IT incidents are a useful fixture pattern but do not represent shipment histories; replace with validated synthetic shipment/event snapshots |
| `gateway/src/tools/runbook_tool.py` | Replace | Fixed SEV2 checklist must become versioned rule/evidence policy, not a renamed hardcoded logistics answer |
| Root `tools/runbook_tool.py` | Retire after import check | Duplicate IT tool exists; current app imports `src.tools.runbook_tool`. Avoid maintaining two domain implementations |
| `gateway/src/tools/router.py` keyword rules | Replace on core workflow | IT/SEV English matches are irrelevant to structured shipment selection; three categories require independent evaluation |
| `_semantic_route_tool`, intent embeddings | Reassess later | Adds no necessary value to a queue-driven V1; reserve for a later measured SOP-question UX, never operational classification |
| `gateway/kb/` IT documents | Replace active corpus | Author eight versioned logistics SOPs; archive IT material outside the active retrieval index, not relabel severity terminology |
| Scenario constants / `scenario_id`, `force_file`, forced tools | Remove from evaluation and new product path | They choose answer paths/documents in advance. New demo selector may choose only fixture IDs, then run the real pipeline |
| `keyword_topk`, `QUERY_FILE_BOOST`, 480-character chunks | Redesign section identity now; reassess search later | File boosts encode IT demo preferences; arbitrary slices weaken section citations. Eight SOPs allow exact lookup and simple search as a baseline |
| SentenceTransformer + in-memory cosine matrix | Reassess after baseline | Could remain a small optional retrieval adapter; a vector database or reranker is not a prerequisite |
| `safe_parse_ui_json`, fixed `confidence` values | Replace confidence contract; retain useful parsing lessons | Output parsing does not validate factual support; use typed explanation blocks and evidence checks, not fabricated probability |
| `gateway/src/ui/templates/demo.html` | Replace UX within existing mount | Current page mixes scripted scenario runner and free-form question modes; preserve simple HTML delivery but build overview/queue/detail |
| `gateway/eval/retrieval_eval.py`, `eval_set.json` | Replace evaluation design | Fifteen IT questions score filenames using copied keyword logic and document deduplication; new suite needs independent policy labels and stable section-level gold |
| `gateway/tests/test_api.py` | Keep test infrastructure; replace domain assumptions | Seven tests cover health/access/contracts and mocked tools/model; tests expecting confidence >0.9 must become evidence/state assertions |
| `gateway/tests/conftest.py`, `pytest.ini` | Keep no-network test approach; strengthen isolation | Disable embeddings/provider access explicitly, freeze clock, isolate audit files/state, verify actual domain behavior without mocking the rule result |
| `gateway/test_demo.py` | Replace smoke scenarios | Current script submits predetermined scenario IDs; new smoke path must select shipments and assert boundary/packet contracts |
| `.github/workflows/ci.yml` | Keep and expand incrementally | Existing CPU-only pytest job is suitable; add policy/schema/KPI tests without requiring cloud/model calls |
| `docker-compose.yml`, `gateway/Dockerfile` | Reassess runtime defaults | Compose currently requires GPU-backed vLLM; gateway Dockerfile installs embedding dependencies. Core rules/SQL/demo should run without GPU or model downloads |
| `gateway/requirements*.txt` | Keep lean API base; reassess optional ML dependencies | Separate optional retrieval/generation tooling from deterministic workflow requirements |
| `gateway/configs/server.example.yaml`, `render.yaml`, settings loader | Redesign domain config carefully | Preserve explicit settings; inspected Render file is environment-style text despite `.yaml` suffix, and loader does not implement all listed environment overrides. Verify deployment contract before claiming portability |
| `README.md`, `CLAUDE.md` | Update only in a later approved phase | Current IT/enterprise/demo descriptions would become stale; this phase expressly leaves them unchanged |
| `.gitignore` | Reassess narrowly during implementation | Existing artifact/secret patterns are useful; `*.jsonl` ignores all such files, so tracked evaluation fixtures need a deliberate format/location |

### Files inspected for this specification

Inspection includes the preceding repository review in this task plus targeted rereads for this specification. Source files and configuration structure were read; credentials are not reproduced.

- `README.md`, `CLAUDE.md`, `.gitignore`, `pytest.ini`, `.github/workflows/ci.yml`.
- `docker-compose.yml`, `gateway/Dockerfile`, `gateway/requirements.txt`, `gateway/requirements-embeddings.txt`, `gateway/configs/render.yaml`.
- `gateway/src/app.py`, `gateway/src/tools/router.py`, `gateway/src/tools/incident_tool.py`, `gateway/src/tools/runbook_tool.py`, `tools/runbook_tool.py`, `gateway/src/tools/data/incidents.json`.
- `gateway/src/ui/demo_page.py`, `gateway/src/ui/templates/demo.html`.
- `gateway/tests/test_api.py`, `gateway/tests/conftest.py`, `gateway/test_demo.py`.
- `gateway/eval/retrieval_eval.py`, `gateway/eval/eval_set.json`.
- `gateway/kb/product_overview.md`, `gateway/kb/audit_and_access.md`, `gateway/kb/knowledge_usage_guidelines.md`, `gateway/kb/escalation_policy.md`.

The tracked-file inventory was also inspected, including remaining KB files and configuration paths. Files merely inventoried are not claimed as fully read. No API test, model call, or deployment was performed for this documentation phase.

## 18. V1 Non-Goals

- ETA prediction, route optimization, demand forecasting, or predictive delay models.
- Additional exception categories beyond late delivery, stale tracking, and failed attempt/address exception.
- Autonomous carrier contact, customer messaging, refunds, shipment modification, rescheduling, or operational action approval.
- Customer PII, real addresses, or production carrier credentials/data.
- Multi-agent architecture, microservice rewrite, distributed orchestration, or model training merely for architectural complexity.
- Unsupported root-cause speculation or claims that demo policies represent carrier standards.
- A general chat assistant, ticket management system, or full historical SLA/compliance platform.
- Production-readiness claims, invented accuracy/cost savings, or assumed superiority over managed RAG.

## 19. Risks and Open Questions

### Assumptions

V1 uses a small synthetic single-tenant dataset, UTC elapsed-hour arithmetic, one immutable snapshot per run, explicit `history_complete` declarations only for dependent decisions, a single approved demo policy bundle, and no real operational integration. SQLite, a simple FastAPI-hosted UI, and English-first SOPs/interface/briefs are approved. The dataset should contain a useful mix of normal and exception cases without presenting its synthetic prevalence as business reality.

### Approval decision record

The project owner approved the specification in principle with this final revision. Decisions below replace earlier pending-approval language; no approval is inferred from silence. The current task remains specification-only.

| ID | Status | Approved decision / remaining boundary |
|---|---|---|
| A1 | Approved | Fictional defaults: late >=24h; stale detected >24h and eligible >=48h; two unique failed attempts; explicit unresolved address exception eligible |
| A2 | Approved | Failed-attempt history remains relevant until closure; address clears only on a later explicit `ADDRESS_CLEARED`; no inferred recovery, cooldown, or carrier rules |
| A3 | Modified as requested | Category-specific evidence and blockers; shipment-global blockers first, then any ready category, then review, monitor, normal. Unrelated unknowns remain visible without cancelling readiness |
| A4 | Approved with simplified V1 snapshot model | Composite shipment identity; immutable fixtures with `snapshot_id`, `as_of`, `dataset_version`, `event_time`, explicit `history_complete`; detailed ingestion/replay infrastructure deferred |
| A5 | Approved | Promise-cohort OTD including due-open shipments; cancelled-at-snapshot excluded; overlapping categories deduplicated as specified |
| A6 | Approved | SQLite, immutable synthetic fixtures, simple FastAPI-hosted UI, English-first |
| A7 | Approved | Project owner may be initial policy owner/reviewer; independent-from-code expected labels required; lack of a second human reviewer disclosed rather than blocking implementation |
| A8 | Deferred | No hosted model or paid provider required yet; provider selection/spending remains a later decision, not a deterministic-workflow blocker |
| A9 | Approved | Introduce versioned `/triage` path/contract; retain legacy `/ask` temporarily; retire legacy surfaces only after the new workflow is stable |
| A10 | Approved | Public demo read-only/non-admin; explicit credentials for administration; no default admin cookie |

Remaining deferred choices are provider/runtime selection and any paid-service budget under A8. Fixture dates and concrete content can be authored within the approved policy; they do not reopen A1–A7/A9–A10. Approval of the design does not authorize application-code edits in this documentation-only task.

### Material risks and mitigations

| Risk | Mitigation / remaining limitation |
|---|---|
| Fictional policy mistaken for real operating guidance | Demo labels in data, SOPs, UI, exports and README when later updated |
| High scores from labels copied from code or from scenario shortcuts | Independent policy labels, held-out families, same real pipeline, input-only fixture selection |
| Small or synthetic test set hides poor generalization | Publish composition/failures; no production claim; later human task study |
| Missing data improves apparent KPIs | Visible denominator/exclusion/unknown counts, no zero-filled timestamps |
| Data and policy snapshots disagree | Frozen versions, hashes, effective intervals, deterministic support gate |
| Citation exists but does not support a claim | Claim-level human scoring; schema/ID checks alone are insufficient |
| Model outage or hallucination | Core triage without model; suppress invalid draft and use explicit template fallback |
| Unnecessary RAG complexity | Exact SOP lookup and rules-only baseline first; retain semantic search only if measured useful |
| No real-user impact evidence | Label benefits as hypotheses; later observe coordinator-like tasks and report time/completeness honestly |

## 20. Phase 1 Implementation Plan

**This is a future plan, not authorization to implement during the current documentation phase.** A1–A7 and A9–A10 are recorded above as approved or modified by the project owner. They need not be re-approved before the separately requested implementation. A8 remains deferred; begin with the deterministic no-model workflow and seek a provider/budget decision only when needed.

| Order | Deliverable in a separately requested implementation phase | Acceptance / review gate |
|---|---|---|
| 1 | Freeze policy registry, eight SOP outlines/sections, data contract and KPI definitions | Apply approved demo defaults; owner verifies registry/SOP consistency |
| 2 | Independently author 54 scenarios and 45 retrieval questions with gold labels | Owner review with single-reviewer limitation disclosed if applicable; fixed dev/test families; no application-generated ground truth |
| 3 | Load synthetic fixtures into SQLite and expose deterministic data-quality/SQL metrics | Hand-counted KPI reconciliation, reproducible snapshots, no PII |
| 4 | Implement pure triage rules and evidence gates in a small domain module behind existing FastAPI app | Policy-conformance suite and boundary tests; no LLM dependency |
| 5 | Implement versioned `/triage` API and exact SOP section resolver; retain `/ask` temporarily | Composite identity, permissions, true readiness, full audit coverage; missing sections block only dependent decisions |
| 6 | Build overview, queue and detail in existing UI infrastructure | Same snapshot/filters across views; no send/approve controls; correct nulls and multi-category behavior |
| 7 | Establish rules + search/template baseline | Publish real results and failure examples before claiming AI improvement |
| 8 | Optionally add one-call explanation adapter after A8 | Immutable decision packet, supported citations, template fallback, human-boundary checks |
| 9 | Execute separated policy/RAG/end-to-end evaluations | Report 18 development/36 initial held-out conformance separately; deterministic E2E on 36; initial LLM claim review on approximately 15 with one generation each when available; no invented improvements |
| 10 | Update README/demo docs and decide next experiments | Accurately describe implemented scope; defer managed RAG comparison until feasibility/budget approval |

Proposed future module boundaries are modest: data access/validation, pure domain rules, metrics queries, SOP resolver, and explanation adapter, all within the existing gateway. Do not reorganize unrelated routes or replace the server framework. Phase 1's first usable milestone is the deterministic operations workflow with evidence-backed template handoff; generative polish is not a blocker.

Current revision completion criterion: only `PROJECT_SPEC.md` changes in the repository; source code, README, fixtures, dependencies, and deployment settings remain unchanged.
