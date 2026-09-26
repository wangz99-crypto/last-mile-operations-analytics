# Phase 1B deterministic domain engine

The input-only entry point is `triage_snapshot(manifest=..., policy=..., input=...,
input_profile=...)`. The optional `bundle` accepts a loaded Policy for isolated
tests. It returns `validation_findings` and `results`; there is no rationale,
Gold provenance, model output or transport/API behavior. Canonical shape/identity
failures raise CanonicalInputError carrying explicit findings. Raw inputs are not
coerced or mutated; invalid dependencies are quarantined while independent valid
facts remain available. Findings distinguish invalid input from operational gaps.

- policy.py: structured registry/schema, runtime artifact hashes and exact section
  availability; no SOP prose interpretation, fixture or evaluation reads.
- validation.py: schema fields, keys, raw findings, time validity, status conflicts
  and dependency-scoped event quarantine.
- facts.py: exact UTC timedeltas, observed scan, unique valid attempt identities,
  explicit address marker ordering, active origins/ages and references.
- rules.py: independent L/S/F classification, subtype support, packet evidence,
  local blockers and normal/failure section roles.
- triage.py: global/closed rules, warnings, aggregate precedence and priority.

Configured thresholds and operators come from the registry. Timedeltas are compared
directly; floating-point hour values are output representations, never decision
inputs. No weekend, cooldown, recovery or carrier-specific rules are added.
Incomplete history does not block late. A missing attempt_id does not erase its
otherwise valid scan time/code or independent address markers. Invalid core event
identity, time or code is excluded from dependent arithmetic and reported. Repeated
messages with distinct event IDs and the same valid attempt ID count once.

Phase 1B.1 preserves the separate source-event identity rule. CANONICAL input still
rejects every duplicate (snapshot_id, source_system, event_id). RAW_VALIDATION_CASE
groups that identity: identical content is one event, with no duplicate-only blocker.
Object-key order and equivalent valid UTC timestamp spellings are semantically equal
for comparison; raw records are never rewritten. Missing/null/invalid values remain
distinct. Identical repeated malformed events still retain their original defect.

Conflicting versions generate CONFLICTING_EVENT_IDENTITY findings referencing each
source row. No conflicting core time/code/target version enters arithmetic. A dispute
only about attempt_id blocks E-FAILED while agreed scan facts remain usable; address
history remains independent. Conflicting marker/time/code facts block their relevant
requirements, including all dependencies implicated by the versions. Conflicts that
undermine shipment attribution or open/closed status are global. Optional facility
differences remain visible findings but do not invent a decision dependency. Only
agreed fields are exposed to independent calculations; disputed values remain in the
raw input. Missing/conflicting evidence IDs and subtype warnings retain their scope.

For one confirmed non-eligible failure plus unknown address state, composition uses
F-1 as provenance for the confirmed failed-attempt condition alongside F-UNKNOWN for
the unresolved address decision. F-1 alone still requires known inactive address for
its complete MONITOR disposition; the combined result remains TRUE / eligibility
null / NEEDS_REVIEW. No escalation trigger is added. Its sections include normal F-1
support and relevant evidence support plus F-UNKNOWN failure guidance; the subtype
evidence stays independent. This output-composition clarification does not change
registry thresholds, dependencies, policy, schema or any DEVELOPMENT Gold.

Section support is resolved by exact registry identity and verified SOP file bytes.
Missing/corrupt required sections block only dependent active decisions. Registry
or schema checksum/bundle/effective-interval failures are global policy failures.
The artifact manifest is read for runtime checksums only; the engine never opens
examples or evaluation fixtures. Unavailable runtime files fail the call rather
than silently using another policy.

The DEVELOPMENT comparison is separate (`evaluation/compare_development.py`). It
projects input fields, runs the engine, then separately loads Gold. It compares all
operational fields exactly with only these representation normalizations:

1. Lists of assessments, references, IDs, sections, warnings and blockers are
   order-insensitive; entries and duplicates are retained, not collapsed.
2. Gold rationale is absent from runtime results. Author explanatory blocker
   `reason` and warning `message` text can differ from deterministic templates;
   codes, scopes, requirement IDs, field references and all decisions remain exact.

There is no threshold tolerance, ignored missing dependency, rewritten subtype,
or substitution of expected values. Runtime invalid-input findings must include
each authored expected_input_findings path; additional operational findings (e.g.
incomplete history) are allowed because that Gold list describes raw invalid input.
Passing the 18 visible cases establishes DEVELOPMENT conformance only.
