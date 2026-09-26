# Tracking Inactivity

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-03",
  "title": "Tracking Inactivity",
  "version": "1.0-demo",
  "effective_from": "2026-09-26T00:00:00Z",
  "effective_to": null,
  "exception_types": [
    "STALE_TRACKING"
  ],
  "demo_policy": true,
  "sections": [
    {
      "section_id": "scan-scope",
      "section": "Scan Scope",
      "rule_ids": [
        "S-PRE",
        "S-0"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "stale-monitor",
      "section": "Stale Monitor",
      "rule_ids": [
        "S-1"
      ],
      "requirement_ids": []
    },
    {
      "section_id": "stale-escalate",
      "section": "Stale Escalate",
      "rule_ids": [
        "S-2"
      ],
      "requirement_ids": []
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## scan-scope

Qualifying physical scan codes are the registry qualifying_physical_scans list. Labels, address notices/clearance and cancellation do not reset inactivity. Complete scan history and a valid last qualifying scan are needed to establish inactivity; never replace a missing scan with creation time or zero. Valid PRE_TRANSIT with complete empty scan history is not applicable. At gap <= STALE_DETECT_HOURS, tracking is not stale.

## stale-monitor

A gap strictly greater than STALE_DETECT_HOURS but below STALE_ESCALATE_HOURS is stale and not yet escalation-eligible. Monitor with E-STALE evidence complete; otherwise this category needs review.

## stale-escalate

At gap >= STALE_ESCALATE_HOURS, stale tracking is eligible. Require last qualifying event reference/time/code, gap, history_complete=true and no relevant scan conflict, plus common and policy-section evidence. A missing promise does not block this independent decision. A new qualifying scan may end staleness; do not infer a delay cause.
