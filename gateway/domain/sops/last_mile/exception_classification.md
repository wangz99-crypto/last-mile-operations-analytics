# Exception Classification Policy

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-01",
  "title": "Exception Classification Policy",
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
      "section_id": "scope",
      "section": "Scope",
      "rule_ids": [
        "D-CLOSED"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "taxonomy",
      "section": "Taxonomy",
      "rule_ids": [],
      "requirement_ids": []
    },
    {
      "section_id": "state-precedence",
      "section": "State Precedence",
      "rule_ids": [],
      "requirement_ids": []
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## scope

Only open PRE_TRANSIT, IN_TRANSIT, OUT_FOR_DELIVERY or EXCEPTION shipments enter active triage. Consistent DELIVERED/CANCELLED shipments have no active V1 exceptions. Validate global context/status first. Stop at human review; never contact carriers, modify shipments or approve actions.

## taxonomy

Use only LATE_DELIVERY, STALE_TRACKING and FAILED_ATTEMPT_ADDRESS. Multiple categories may coexist. Failed/address subtypes are FAILED_ATTEMPT, ADDRESS_EXCEPTION or BOTH. TRUE/FALSE/UNKNOWN/NOT_APPLICABLE are distinct; missing facts are not false.

## state-precedence

Each category owns classification, eligibility, evidence and blockers. A shipment-global blocker yields NEEDS_REVIEW. Otherwise use any READY_TO_ESCALATE, then any NEEDS_REVIEW, then any MONITOR, otherwise NORMAL. An unrelated unknown remains visible but cannot cancel an independently ready category. HIGH priority requires a verified eligibility trigger, MEDIUM applies to remaining review cases, LOW to remaining monitor/normal cases. Readiness is not operational approval.
