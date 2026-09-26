# Failed Attempt & Address Exception

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-04",
  "title": "Failed Attempt & Address Exception",
  "version": "1.0-demo",
  "effective_from": "2026-09-26T00:00:00Z",
  "effective_to": null,
  "exception_types": [
    "FAILED_ATTEMPT_ADDRESS"
  ],
  "demo_policy": true,
  "sections": [
    {
      "section_id": "attempt-counting",
      "section": "Attempt Counting",
      "rule_ids": [
        "F-0"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "single-attempt",
      "section": "Single Attempt",
      "rule_ids": [
        "F-1"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "repeated-attempts",
      "section": "Repeated Attempts",
      "rule_ids": [
        "F-2"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "address-notices",
      "section": "Address Notices",
      "rule_ids": [
        "F-3"
      ],
      "requirement_ids": []
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## attempt-counting

Physical failed attempts require valid ATTEMPT_FAILED event references and distinct attempt_id values within a shipment snapshot. Duplicate messages for one attempt count once. Missing identity/history leaves the affected count unknown. Complete history with zero failures and inactive address state has no failed/address exception. Failed-attempt history remains relevant until closure.

## single-attempt

One valid failed attempt with address known inactive is a confirmed exception to monitor when dependent evidence is complete. Do not invent a second attempt or infer recovery from subsequent movement.

## repeated-attempts

At least FAILED_ATTEMPTS_ESCALATE unique valid failures meet eligibility. Require E-FAILED and common/policy-section evidence. Independent attempt-based readiness does not require address evidence unless an address decision is also claimed.

## address-notices

With ADDRESS_ACTIVE_ESCALATES enabled, an explicit unresolved ADDRESS_EXCEPTION is immediately eligible. Immediate eligibility is not final readiness: address-based readiness still requires applicable common evidence, E-ADDRESS, and E-POLICY-SECTIONS support. Only a later explicit ADDRESS_CLEARED clears it; contradictory simultaneous markers are unknown. Marker history must establish the current state; incomplete marker history cannot prove no later clearance. Attempt IDs are not required for address-only support. Do not invent an address defect, cooldown, carrier procedure or recovery.
