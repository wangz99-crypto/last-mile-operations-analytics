# Operations Audit

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-08",
  "title": "Operations Audit",
  "version": "1.0-demo",
  "effective_from": "2026-09-26T00:00:00Z",
  "effective_to": null,
  "exception_types": [
    "LATE_DELIVERY",
    "STALE_TRACKING",
    "FAILED_ATTEMPT_ADDRESS"
  ],
  "demo_policy": true,
  "sections": [
    {
      "section_id": "decision-record",
      "section": "Decision Record",
      "rule_ids": [],
      "requirement_ids": []
    },
    {
      "section_id": "revision-history",
      "section": "Revision History",
      "rule_ids": [],
      "requirement_ids": []
    },
    {
      "section_id": "data-minimization",
      "section": "Data Minimization",
      "rule_ids": [],
      "requirement_ids": []
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## decision-record

Record request/run identity, snapshot_id, as_of, dataset/policy/code versions, hashes, composite shipment identity, referenced events/sections, category outcomes, scoped evidence/blockers/warnings and aggregate state. Record measured timing/usage only when available. An explanation is separate from deterministic results.

## revision-history

Fixtures are immutable snapshots of what was known at their frozen state. Corrections require a new fixture/version. Repeat evaluations against the same snapshot/policy context. Detailed late-arrival ingestion and replay infrastructure is outside V1.

## data-minimization

Use synthetic shipment identifiers and fictional carriers. No customer names, literal addresses, phone numbers, coordinates or free-text customer notes. Keep factual provenance without raw sensitive text. Do not claim production compliance or real-world accuracy from synthetic tests.
