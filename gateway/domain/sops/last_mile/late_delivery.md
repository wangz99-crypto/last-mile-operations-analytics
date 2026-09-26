# Late Delivery

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-02",
  "title": "Late Delivery",
  "version": "1.0-demo",
  "effective_from": "2026-09-26T00:00:00Z",
  "effective_to": null,
  "exception_types": [
    "LATE_DELIVERY"
  ],
  "demo_policy": true,
  "sections": [
    {
      "section_id": "late-boundaries",
      "section": "Late Boundaries",
      "rule_ids": [
        "L-0"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "late-monitor",
      "section": "Late Monitor",
      "rule_ids": [
        "L-1"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "late-escalate",
      "section": "Late Escalate",
      "rule_ids": [
        "L-2"
      ],
      "requirement_ids": []
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## late-boundaries

Late detection is as_of > promised_delivery_at on an open shipment; at equality it is not late. Compare exact elapsed seconds, round only for display. Missing/invalid promise is late-category UNKNOWN. Complete tracking history is not a dependency.

## late-monitor

A confirmed late shipment below LATE_ESCALATE_HOURS is not yet escalation-eligible. With dependent evidence complete, monitor; otherwise review only the dependent late decision.

## late-escalate

At hours_overdue >= LATE_ESCALATE_HOURS, the late trigger is eligible. Require common identity/status/policy context, E-LATE and E-POLICY-SECTIONS. A missing scan or attempt history does not block a fully evidenced late handoff. Draft only for human review.
