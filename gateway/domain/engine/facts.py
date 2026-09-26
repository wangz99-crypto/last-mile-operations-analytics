"""Exact UTC arithmetic and evidence-scoped facts from validated snapshot records."""
from dataclasses import dataclass
from datetime import timedelta

from .policy import TYPES, iso, timestamp


@dataclass
class Facts:
    output: dict
    overdue: object
    scan_gap: object
    address_conflict: bool


def derive(ctx, policy):
    s = ctx.shipment
    status_valid = not any("E-STATUS" in f["requirement_ids"] for f in ctx.global_findings)
    is_open = s.get("current_status") in policy.registry["open_statuses"] if status_valid else None
    overdue = None
    promise = s.get("promised_delivery_at")
    if is_open and promise is not None and "promised_delivery_at" not in ctx.invalid_fields and ctx.as_of is not None:
        overdue = max(timedelta(0), ctx.as_of - timestamp(promise))
    scans = [e for _, e, _ in ctx.events if e["event_code"] in policy.registry["qualifying_physical_scans"]]
    latest = max(scans, key=lambda e: (timestamp(e["event_time"]), e["source_system"], e["event_id"]), default=None)
    scan_time = timestamp(latest["event_time"]) if latest else None
    gap = ctx.as_of - scan_time if ctx.as_of is not None and scan_time is not None else None
    attempts = [e for _, e, valid_attempt in ctx.events if e["event_code"] == "ATTEMPT_FAILED" and valid_attempt]
    count = len({e["attempt_id"] for e in attempts}) if ctx.history and not ctx.attempts_invalid else None
    markers = [e for _, e, _ in ctx.events if e["event_code"] in ("ADDRESS_EXCEPTION", "ADDRESS_CLEARED")]
    address, address_start, conflict = None, None, False
    if ctx.history and not ctx.address_invalid:
        if not markers:
            address = False
        else:
            newest = max(timestamp(e["event_time"]) for e in markers)
            last_codes = {e["event_code"] for e in markers if timestamp(e["event_time"]) == newest}
            conflict = len(last_codes) > 1
            if not conflict:
                address = "ADDRESS_EXCEPTION" in last_codes
                if address:
                    clears = [timestamp(e["event_time"]) for e in markers if e["event_code"] == "ADDRESS_CLEARED"]
                    last_clear = max(clears) if clears else None
                    episode = [timestamp(e["event_time"]) for e in markers if e["event_code"] == "ADDRESS_EXCEPTION"
                               and (last_clear is None or timestamp(e["event_time"]) > last_clear)]
                    address_start = min(episode)
    starts = dict.fromkeys(TYPES)
    if is_open:
        if overdue is not None and overdue > timedelta(0):
            starts[TYPES[0]] = timestamp(promise)
        if gap is not None and ctx.history and not ctx.scan_uncertain and policy.meets("STALE_DETECT_HOURS", gap):
            starts[TYPES[1]] = scan_time + policy.threshold("STALE_DETECT_HOURS")
        active_origins = []
        if count is not None and count > 0:
            active_origins.append(min(timestamp(e["event_time"]) for e in attempts))
        if address_start is not None:
            active_origins.append(address_start)
        starts[TYPES[2]] = min(active_origins) if active_origins else None
    refs = []
    def ref(kind, field, event_id=None, source=None):
        if all(isinstance(s.get(k), str) and s[k] for k in ("snapshot_id", "shipment_id")):
            refs.append(dict(snapshot_id=s["snapshot_id"], shipment_id=s["shipment_id"], record_type=kind,
                             field=field, event_id=event_id, source_system=source))
    for field in ("shipment_id", "carrier", "source_system", "current_status", "promised_delivery_at", "delivered_at"):
        ref("shipment", field)
    ref("manifest", "as_of")
    ref("history_declaration", "history_complete")
    for _, e, _ in ctx.events:
        for field in ("event_time", "event_code", "attempt_id"):
            ref("tracking_event", field, e["event_id"], e["source_system"])
    output = dict(is_open=is_open, hours_overdue=overdue.total_seconds()/3600 if overdue is not None else None,
                  last_scan_time=iso(scan_time) if scan_time else None,
                  hours_since_last_scan=gap.total_seconds()/3600 if gap is not None else None,
                  failed_attempt_count=count, address_exception_active=address,
                  exception_started_at={k: iso(v) if v else None for k, v in starts.items()},
                  exception_age_hours={k: (ctx.as_of-v).total_seconds()/3600 if v is not None and ctx.as_of is not None else None for k, v in starts.items()},
                  fact_refs=refs)
    return Facts(output, overdue, gap, conflict)
