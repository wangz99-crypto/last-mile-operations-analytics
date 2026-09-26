# Insufficient Evidence

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-07",
  "title": "Insufficient Evidence",
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
      "section_id": "missing-facts",
      "section": "Missing Facts",
      "rule_ids": [
        "D-CONTEXT",
        "L-UNKNOWN",
        "S-UNKNOWN",
        "F-UNKNOWN"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "data-conflicts",
      "section": "Data Conflicts",
      "rule_ids": [
        "D-STATUS"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "missing-policy",
      "section": "Missing Policy",
      "rule_ids": [
        "D-CONTEXT"
      ],
      "requirement_ids": [
        "E-POLICY-CONTEXT",
        "E-POLICY-SECTIONS"
      ]
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## missing-facts

Missing facts remain null/UNKNOWN. Associate each gap with its dependent decision. Missing promise blocks late; missing scan history blocks stale; missing attempt identity blocks the attempt decision. Do not cancel an independently ready category. Missing optional facility is a warning. Invalid shipment identity/snapshot context is global.

## data-conflicts

Conflicting open/closed status invalidates the whole assessment. Other invalid events or duplicate conflicts block only dependent decisions unless identity/status is undermined. Preserve conflicts visibly. Do not silently discard conflicting evidence and label it normal.

## missing-policy

Unavailable or ambiguous required bundle is shipment-global. Missing/inconsistent required category sections block dependent decisions only. Exact active policy/version/section support is required; similarity scores do not establish policy authority. Supplemental-search misses are warnings when required support exists.
