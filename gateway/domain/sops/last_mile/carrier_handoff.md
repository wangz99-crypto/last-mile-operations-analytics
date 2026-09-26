# Carrier Handoff

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-06",
  "title": "Carrier Handoff",
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
      "section_id": "handoff-fields",
      "section": "Handoff Fields",
      "rule_ids": [],
      "requirement_ids": []
    },
    {
      "section_id": "handoff-boundary",
      "section": "Handoff Boundary",
      "rule_ids": [],
      "requirement_ids": [
        "E-POLICY-SECTIONS"
      ]
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## handoff-fields

A draft contains snapshot/shipment identity, verified facts with references, supported categories/triggers, deterministic state/rule rationale, exact SOP version/section citations, and missing/conflicting items with scope. Separate shipment blockers, local blockers and warnings. LLM text cannot fill gaps or change a decision.

## handoff-boundary

Draft only. Human review required. Nothing has been sent or changed. A ready brief covers only independently supported categories/triggers. A shipment-global blocker prevents a ready brief; unrelated local gaps remain disclosed. Do not contact a carrier, approve actions, issue refunds, alter shipments or speculate about causes.
