# Phase 1B.2 post-heldout Development regression

This expectation layer was created **after the initial held-out evaluation**.
It tests the new Phase 1B.2 diagnostic contract on the 18 implementation-visible
Development cases. It is not the original pre-heldout Development Gold, a new
blind held-out evaluation, or evidence of production accuracy. No private Gold
is loaded and no private post-fix held-out regression is performed by these tools.

The original owner-reviewed fixtures under `../development/calibration/` remain
unchanged. Their provenance and pre-heldout expectations are historical evidence;
rewriting them would erase the distinction between that baseline and a diagnostic
contract adopted after held-out feedback. The legacy strict comparator remains
unchanged and is expected to report **14/18**, with exactly five diagnostic
differences across C04, D15, D16 and D17.

Phase 1B.2 gives blockers a more precise `dependent_decision`: failed-attempt and
address dependencies name their respective subtype, while packet-only gaps name
the dependent packet. The existing engine defines `LATE_DELIVERY_PACKET` for late
packets and `PACKET` for other category packets. Only `LATE_DELIVERY_PACKET` is
needed by the five observed Development differences; no extra `PACKET` override
is invented. Category-level dependencies otherwise retain their category name.

The sibling location `evaluation/post_1b2/` was explicitly approved for this task.
The unchanged legacy comparator, structural validator and contract tests recursively
treat every JSON under `evaluation/development/` as a fixture. Putting the override
JSON there would invalidate their frozen 18-fixture inventory. Keeping this layer
alongside that tree preserves all existing tools and their meaning.

## Exact migration inventory

Every record in `diagnostic_expectation_overrides.json` includes the fixture ID,
assessment category, complete blocker selector, JSON pointer into the original
frozen fixture, old value, new value, rationale and migration version `1B.2`.
All five pointers end in `/dependent_decision`.

| Fixture | Assessment | Blocker code | Old frozen value | Phase 1B.2 value |
| --- | --- | --- | --- | --- |
| C04 | FAILED_ATTEMPT_ADDRESS | INCOMPLETE_ATTEMPT_HISTORY | FAILED_ATTEMPT_ADDRESS | FAILED_ATTEMPT |
| C04 | FAILED_ATTEMPT_ADDRESS | UNKNOWN_ADDRESS_STATE | FAILED_ATTEMPT_ADDRESS | ADDRESS_EXCEPTION |
| D15 | FAILED_ATTEMPT_ADDRESS | CONFLICTING_ADDRESS_MARKERS | FAILED_ATTEMPT_ADDRESS | ADDRESS_EXCEPTION |
| D16 | LATE_DELIVERY | MISSING_CARRIER | LATE_DELIVERY | LATE_DELIVERY_PACKET |
| D17 | FAILED_ATTEMPT_ADDRESS | MISSING_ATTEMPT_ID | FAILED_ATTEMPT_ADDRESS | FAILED_ATTEMPT |

These are the exact five differences reproduced by the unchanged legacy comparator
against the existing Phase 1B.2 engine. This task adds no engine changes. The new
layer does not inherit the frozen fixtures' pre-heldout label provenance; it is
an explicit post-heldout contract migration.

## Comparison contract

`compare_post_1b2.py` accepts only the original 18 public Development paths. It
projects only manifest, policy, input and input_profile into the existing engine.
After the engine returns, it separately loads frozen Gold and makes a deep copy
in memory. It verifies the closed five-record inventory, migration version,
category, unique blocker selector, exact JSON pointer and old frozen value before
assigning the new `dependent_decision`. Missing, extra, duplicate, stale, ambiguous
or non-diagnostic overrides fail closed. It never writes fixtures or changes
actual engine output.

It reuses the unchanged legacy `normalize` and `differences` functions, with the
same explicit representation rules: list order is immaterial, but all entries
and duplicates remain; author explanatory `rationale`, blocker `reason` and warning
`message` text are excluded. The CLI prints these exclusions. No new field is
ignored. All operational values, key presence and list cardinality remain strict,
including `dependent_decision`, result, eligibility, action_state, rule_ids,
supported_triggers, evidence IDs, SOP sections, aggregate state, priority and
derived facts. There is no numeric tolerance. Inputs and all other frozen fields
remain unchanged in the copied fixture as well as on disk.

As in the legacy comparator, every authored `expected_input_findings` path must
occur in runtime validation findings. Additional operational findings are allowed;
the authored list describes invalid input and is not a complete expected runtime
diagnostic stream. The migration does not change this rule.

The legacy and versioned comparisons answer different historical contract
questions. Their expected results are:

```text
Frozen legacy Development strict comparison: 14/18
Post-1B.2 versioned Development regression: 18/18
```

Run from repository root (PowerShell):

```powershell
$env:PYTHONPATH = 'gateway/domain'
python -B -m unittest discover -s gateway/domain/tests -p 'test_engine*.py' -v
python -B -m unittest discover -s gateway/domain/tests -p 'test_contracts.py' -v
python -B gateway/domain/validate_contracts.py
python -B gateway/domain/evaluation/compare_development.py
python -B gateway/domain/evaluation/post_1b2/compare_post_1b2.py
python -B -m unittest discover -s gateway/domain/tests -p 'test_post_1b2_comparison.py' -v
```

The legacy CLI intentionally exits 1 for the four diagnostic-contract mismatches;
the versioned CLI exits 0 only when all 18 match and prints exact differences
otherwise. The existing legacy conformance test also retains its historical
expectations. Do not weaken either comparator to obtain a passing result.

## Preservation boundary

The base commit is `a528023e64ef523ea91741d8574cc431e7bae8e3`.
The frozen annotated tag `deterministic-engine-v0.1-pre-heldout` has object ID
`56e1f6129526f53d326d5481f0ca85e424be9804` and resolves to that base commit.
Neither the tag nor the initial run artifacts are part of the migration.
Integrity verification hashes initial run bytes without parsing their content;
private held-out Gold is outside this task's reads.

Before/after SHA-256 verification checks the exact local bytes of the frozen
Development files, initial run artifacts, pre-existing implementation/test changes
and legacy tools. On this Windows checkout, the 18 fixture files already use CRLF
while the frozen Git blobs use LF; they match the tag after only that checkout
line-ending conversion. Preserve those existing local bytes as well as the tag.
