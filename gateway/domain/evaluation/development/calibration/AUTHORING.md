# Phase 1A-2 development Gold dataset

Exactly 18 synthetic single-shipment DEVELOPMENT fixtures use frozen PROJECT_SPEC.md
sections 6–9 and policy bundle 1.0-demo. The original location is retained to avoid
moving approved artifacts: C01–C12 are the calibration cases; D13–D18 complete the
visible development set. These are not held-out results or production evidence.

C01–C12 are OWNER_REVIEWED by project owner Zhe Wang. AI assistance was used during
artifact authoring. The owner manually reviewed their inputs, arithmetic, rule
selection, evidence dependencies, SOP sections, blockers and aggregate outcomes
against the frozen written policy and approved them. Promotion changes provenance
only; inputs, checksums, facts and all business outcomes remain unchanged.

D13–D18 also have explicit AI-assisted artifact-author provenance and are now
OWNER_REVIEWED by Zhe Wang before Phase 1B implementation. The owner reviewed their
inputs, arithmetic, rule selection, evidence dependencies, SOP sections, blockers
and aggregate outcomes against the frozen policy. This promotion changes provenance
only. No independent second human reviewer has yet reviewed the set. Owner review
is not represented as independent second review.

The author selected rules, evidence, sections, states, priorities, facts and
rationales directly from the written policy. Arithmetic was checked manually;
serialization only copies explicit labels, creates field references and hashes
input JSON. No operational implementation was used to obtain expected results.
Each fixture records its detailed reasoning and provenance. No unresolved policy
ambiguity was encountered in these 18 scenarios.

All as_of values are 2026-10-01T12:00:00Z, after the bundle effective date. Identifiers,
carriers and facilities are fictional; no customer PII is present. No fixture
requires optional-facility warnings because its supplied facilities are explicit.

| ID | Purpose | Manually expected aggregate / priority |
|---|---|---|
| C01 | Promise equality and exactly 24-hour scan gap: neither strict detection boundary crossed | NORMAL / LOW |
| C02 | Consistent on-time delivered shipment: all categories not applicable | NORMAL / LOW |
| C03 | Late by 86399 seconds (23h59m59s), just below eligibility | MONITOR / LOW |
| C04 | Late by 24 hours; incomplete history leaves stale and failed/address unresolved | READY_TO_ESCALATE / HIGH |
| C05 | Scan gap 86401 seconds, stale for one second | MONITOR / LOW |
| C06 | Scan gap 48 hours; missing promise remains a local late gap | READY_TO_ESCALATE / HIGH |
| C07 | Two distinct messages share one valid attempt ID | MONITOR / LOW |
| C08 | Two distinct valid failed attempts reach exact eligibility threshold | READY_TO_ESCALATE / HIGH |
| C09 | Current explicit address notice with complete common/address/policy evidence | READY_TO_ESCALATE / HIGH |
| C10 | Canonical open status contradicts valid delivered facts: global D-STATUS blocker | NEEDS_REVIEW / MEDIUM |
| C11 | Raw unknown status rejected by canonical schema: global D-STATUS blocker | NEEDS_REVIEW / MEDIUM |
| C12 | One shipment has independently ready late and stale assessments | READY_TO_ESCALATE / HIGH |
| D13 | PRE_TRANSIT with complete empty scans follows S-PRE, not stale | NORMAL / LOW |
| D14 | Later explicit ADDRESS_CLEARED ends address-only activity | NORMAL / LOW |
| D15 | Equal-time contradictory address markers remain unknown; late is independently ready | READY_TO_ESCALATE / HIGH |
| D16 | Known eligible late trigger lacks carrier packet evidence; local E-IDENTITY gap | NEEDS_REVIEW / HIGH |
| D17 | RAW null attempt_id leaves failed count unknown; canonical schema still rejects it | NEEDS_REVIEW / MEDIUM |
| D18 | BOTH independently supported failed-attempt and address triggers | READY_TO_ESCALATE / HIGH |

For C03, 86399/3600 hours is represented as 23.99972222222222; for C05,
86401/3600 as 24.00027777777778 and one-second age as 0.0002777777777777778.
The timestamps preserve exact seconds; these decimal labels are not display-rounded
threshold inputs. C06/C12 stale age is 24 hours, although their scan gap is 48 hours:
the stale age origin is last qualifying scan plus 24 hours.

C10 uses valid canonical shapes with contradictory operational facts; structural
validation must accept its input shape without proving its Gold. C11 deliberately
uses RAW_VALIDATION_CASE with a finding, preserving the invalid status. Neither
case asserts that invalid global status establishes any active category. Valid
observed scan/history facts remain visible, while is_open and active ages are null.

C12 has one input and one expected shipment result. Its two ready category evidence
sets share common IDs and sections; an eventual output union must retain E-LATE and
E-STALE with the common and policy IDs without counting the shipment twice. The
frozen schema has no separate output-union field; no extra schema or aggregation
code is introduced. This expectation is also recorded in C12's rationale.

D13 does not substitute zero for an absent scan or gap. D14 uses only the explicit
later clear marker; there are zero failed attempts, so F-0 applies. D15 never orders
equal timestamps by event ID/list position. Its E-ADDRESS conflicting_ids and local
blocker retain the conflict; the frozen F-UNKNOWN mapping cites missing-facts for
unresolved marker ordering. Its unrelated late readiness remains supported.

D16 preserves L-2 TRUE and eligible while E-IDENTITY packet evidence is incomplete.
Carrier null does not invalidate composite identity or create D-CONTEXT. The shared
common_evidence gap is not a shipment-global blocker; only the dependent late packet
is blocked. D17 retains a malformed earlier failed message, but an independently
valid later scan establishes the observed latest scan; the invalid event is not used
for arithmetic or a failed count. Complete marker history still establishes address
inactive. No attempt is fabricated or raw input silently normalized.

D18 explicitly declares F-2 and F-3, both subtype assessments and both E-FAILED and
E-ADDRESS dependencies. Shared sections appear once; one shipment/result retains
both triggers. Its combined age starts at the first failed attempt (24 hours ago),
earlier than the active address episode (one hour ago). No operational union or
aggregation function is implemented.

The added validator guard only checks the author's declared MONITOR/READY rules
against declared required IDs and normal support sections. Structured F-UNKNOWN
subtype mappings use declared eligible trigger rules to select supported branches;
the unresolved other subtype does not become a mandatory dependency. NEEDS_REVIEW
can declare only its local unresolved dependency. The guard cannot establish that
an author selected the right rule, state, arithmetic or policy interpretation.

Run the domain structural validator and stdlib unittest discovery from repository
root. They validate all 18 fixture structures/checksums plus the two unchanged
examples; they do not execute triage or score prediction correctness. The frozen
Phase 1A-1 artifact manifest remains unchanged; each calibration fixture has its own
input checksum. C01–C12 keep dataset_version calibration-v1; D13–D18 use
development-v1. The validator discovers all JSON fixtures under development; the
tests enforce exactly these 18 IDs and OWNER_REVIEWED provenance for all 18.

Phase 1B compares this frozen, implementation-visible Gold to independently computed
engine outputs using the separate evaluation/compare_development.py harness. Gold
is loaded for comparison only after the engine returns. Passing results describe
DEVELOPMENT policy conformance, not held-out or production accuracy. These results
do not change the provenance of labels authored before implementation.

No held-out Gold is included. Future held-out input-only packets may be visible in
the repository; their Gold must remain outside the implementation-visible repository
until the first held-out evaluation. Runs after fixes following that evaluation
are regression results, not a new blind held-out result. Neither the 54-case set
nor any retrieval-question dataset is created in this phase.
