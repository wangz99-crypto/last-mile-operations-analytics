# Escalation Evidence

Fictional demo operating policy. Not real carrier or industry standards.

```json
{
  "policy_id": "SOP-05",
  "title": "Escalation Evidence",
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
      "section_id": "common-evidence",
      "section": "Common Evidence",
      "rule_ids": [],
      "requirement_ids": [
        "E-IDENTITY",
        "E-STATUS",
        "E-POLICY-CONTEXT"
      ]
    },
    {
      "section_id": "late-evidence",
      "section": "Late Evidence",
      "rule_ids": [],
      "requirement_ids": [
        "E-LATE"
      ]
    },
    {
      "section_id": "stale-evidence",
      "section": "Stale Evidence",
      "rule_ids": [],
      "requirement_ids": [
        "E-STALE"
      ]
    },
    {
      "section_id": "attempt-address-evidence",
      "section": "Attempt Address Evidence",
      "rule_ids": [],
      "requirement_ids": [
        "E-FAILED",
        "E-ADDRESS"
      ]
    }
  ]
}
```

Policy values are authoritative in `../../policy/policy_registry.json`; constant names below are references, not independently configured thresholds. Section metadata inherits the document policy ID, title, version, interval, coverage and demo label.

## common-evidence

Common dependencies are E-IDENTITY, E-STATUS and E-POLICY-CONTEXT. Invalid composite identity, snapshot context, status or required bundle can invalidate the shipment. Missing carrier/source blocks dependent packets, not known classification. There is no common E-HISTORY gate.

## late-evidence

E-LATE requires a valid promise, overdue value and field provenance. Late readiness does NOT require complete tracking history. Resolve decision/evidence sections and the handoff boundary under E-POLICY-SECTIONS.

## stale-evidence

E-STALE requires qualifying scan identity/time/code, gap, history_complete=true and no conflict relevant to inactivity. Missing this evidence blocks stale decisions, not an independent late decision.

## attempt-address-evidence

E-FAILED depends on valid complete attempt history and identity. E-ADDRESS depends on explicit current address-marker state and sufficient marker history, not attempt IDs. A supported eligible subtype can make FAILED_ATTEMPT_ADDRESS ready while another subtype stays unknown; disclose it and exclude it from the escalation basis. Claiming both triggers requires evidence for both. Completeness describes the supported decision, not all possible shipment information.
