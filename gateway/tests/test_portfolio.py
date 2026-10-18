"""Portfolio routes use real engine results and public policy only."""
import hashlib
import copy
import json
import sys

from fastapi.testclient import TestClient
import pytest

from domain.engine import triage_snapshot
from domain.retrieval import SectionIntegrityError, SectionStore
from src.portfolio import app
from src import triage_demo

client = TestClient(app)


@pytest.mark.parametrize("case_id,state,priority", [
    ("late", "READY_TO_ESCALATE", "HIGH"), ("stale", "MONITOR", "LOW"),
    ("address", "READY_TO_ESCALATE", "HIGH"), ("missing", "NEEDS_REVIEW", "MEDIUM"),
    ("normal", "NORMAL", "LOW"),
    ("late-monitor", "MONITOR", "LOW"), ("stale-ready", "READY_TO_ESCALATE", "HIGH"),
    ("attempt-one", "MONITOR", "LOW"), ("attempt-missing", "NEEDS_REVIEW", "MEDIUM"),
    ("address-conflict", "NEEDS_REVIEW", "MEDIUM"),
])
def test_live_engine_result_and_exact_evidence(case_id, state, priority):
    response = client.post("/api/triage/analyze", json={"case_id": case_id})
    assert response.status_code == 200
    data = response.json()
    actual = triage_snapshot(**triage_demo.case_packet(case_id))
    assert data["result"] == actual["results"][0]
    assert (data["result"]["aggregate_action_state"], data["result"]["priority"]) == (state, priority)
    assert data["model_used"] is False
    expected = {tuple(s[k] for k in ("policy_id", "version", "section_id"))
                for a in actual["results"][0]["assessments"] for s in a["expected_sections"]}
    store = SectionStore.load()
    assert expected == {(s["policy_id"], s["version"], s["section_id"]) for s in data["evidence"]}
    for s in data["evidence"]:
        real = store.get(**{k: s[k] for k in ("policy_id", "version", "section_id")})
        assert s["text"] == real.text
        assert s["content_hash"] == real.content_hash


def test_catalog_is_input_only_and_sealed():
    catalog = client.get("/api/triage/cases").json()
    assert catalog["synthetic"] is True
    assert len(catalog["cases"]) == 10
    for item in catalog["cases"]:
        packet = item["packet"]
        assert set(packet) == {"manifest", "policy", "input", "input_profile"}
        payload = json.dumps(packet["input"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        assert packet["manifest"]["checksum"] == hashlib.sha256(payload.encode()).hexdigest()


def test_no_arbitrary_input_or_action_endpoint():
    assert client.post("/api/triage/analyze", json={"case_id": "unknown"}).status_code == 404
    assert client.post("/api/triage/analyze", json={"case_id": "late", "input": {}}).status_code == 422
    assert client.post("/api/triage/analyze", json={"question": "invent a rule"}).status_code == 422
    assert client.post("/api/triage/escalate", json={"case_id": "late"}).status_code == 404


def test_integrity_failure_never_returns_recommendation(monkeypatch):
    def broken():
        raise SectionIntegrityError("corrupt public policy")
    monkeypatch.setattr(triage_demo.SectionStore, "load", broken)
    response = client.post("/api/triage/analyze", json={"case_id": "late"})
    assert response.status_code == 503
    assert "result" not in response.json()
    queue_response = client.get("/api/triage/queue")
    assert queue_response.status_code == 503
    assert "items" not in queue_response.json()


def test_coverage_is_scoped_and_uses_real_boundary():
    coverage = client.post("/api/triage/analyze", json={"case_id": "late"}).json()["coverage_demo"]
    assert coverage["label"] == "Policy Coverage Demo"
    assert "predefined" in coverage["scope"]
    section = SectionStore.load().get(policy_id="SOP-06", version="1.0-demo", section_id="handoff-boundary")
    assert coverage["boundary_text"] == section.text
    assert "issue refunds" in section.text


def test_portfolio_assets_and_legacy_route():
    homepage = client.get("/").text
    assert "Exception queue" in homepage
    assert "Qwen" not in homepage
    assert "5 / 12" not in homepage
    engineering = client.get("/engineering")
    assert engineering.status_code == 200
    assert "5 / 12" in engineering.text
    for name in ("portfolio.css", "portfolio.js"):
        assert client.get("/portfolio-assets/" + name).status_code == 200
    assert client.get("/portfolio-assets/RAW_GENERATIONS.json").status_code == 404
    from src.app import app as gateway_app
    gateway = TestClient(gateway_app)
    assert "Exception queue" in gateway.get("/").text
    assert "Internal Assistant" in gateway.get("/gateway").text


def test_runtime_imports_no_model_libraries():
    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules
    assert "sentence_transformers" not in sys.modules


def test_queue_is_unique_sorted_and_matches_live_results():
    response = client.get("/api/triage/queue")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == len({row["shipment_id"] for row in items}) == 10
    assert [row["priority"] for row in items] == ["HIGH"] * 3 + ["MEDIUM"] * 3 + ["LOW"] * 4
    for row in items:
        detail = client.post("/api/triage/analyze", json={"case_id": row["case_id"]}).json()
        assert row == detail["summary"]
        assert 1 <= len(row["top_reasons"]) <= 2
        assert len(row["next_steps"]) == 3
        ages = [v for v in detail["result"]["derived_facts"]["exception_age_hours"].values() if v is not None]
        assert row["age_hours"] == (max(ages) if ages else None)
    assert next(row for row in items if row["case_id"] == "stale")["age_hours"] == 6
    assert next(row for row in items if row["case_id"] == "missing")["age_hours"] is None


def test_review_steps_are_scoped_to_real_blockers():
    data = triage_demo.analyze_case("attempt-missing")
    assert data["packet"]["input_profile"] == "RAW_VALIDATION_CASE"
    assert data["summary"]["next_steps"][0] == "Find missing attempt identity"
    assert "MISSING_ATTEMPT_ID" in {b["code"] for a in data["assessments"] for b in a["blockers"]}
    assert triage_demo.analyze_case("address-conflict")["summary"]["next_steps"][0] == "Resolve conflicting address notices"
    assert triage_demo.analyze_case("missing")["summary"]["next_steps"][0] == "Confirm delivery promise"
    assert triage_demo.analyze_case("late")["summary"]["evidence_status"] == "Ready basis verified; other gaps"


def test_overview_membership_and_unknown_age_overlap():
    data = client.get("/api/triage/queue").json()
    overview = data["overview"]
    assert overview["shipment_count"] == 10
    assert [len(group["case_ids"]) for group in overview["action_status"]] == [3, 3, 3, 1]
    memberships = [case for group in overview["action_status"] for case in group["case_ids"]]
    assert len(memberships) == len(set(memberships)) == 10
    gaps = {group["group"]: set(group["case_ids"]) for group in overview["review_gaps"]}
    assert gaps == {"promise": {"missing"}, "tracking": {"late"},
                    "attempt": {"late", "attempt-missing"}, "address": {"late", "address-conflict"}}
    # A ready overall action and multiple local gaps legitimately coexist.
    assert "late" in overview["action_status"][0]["case_ids"]
    assert sum(map(len, gaps.values())) == 6
    assert len(set.union(*gaps.values())) == 4
    assert [row["age_hours"] for row in overview["longest_confirmed"]] == [24, 24, 22, 6, 6, 3]
    assert overview["known_and_unconfirmed_case_ids"] == ["late"]
    assert set(overview["unconfirmed_start_case_ids"]) == {"late", "missing", "attempt-missing", "address-conflict"}
    assert "normal" not in overview["unconfirmed_start_case_ids"]
    for row in overview["longest_confirmed"]:
        result = triage_demo.analyze_case(row["case_id"])["result"]
        assessment = next(a for a in result["assessments"] if a["exception_type"] == row["exception_type"])
        assert assessment["result"] == "TRUE"
        assert row["age_hours"] == result["derived_facts"]["exception_age_hours"][row["exception_type"]]


def test_overview_deduplicates_blockers_and_uses_one_longest_issue_per_shipment():
    row = copy.deepcopy(triage_demo.analyze_case("late")["summary"])
    row["review_gaps"].extend(copy.deepcopy(row["review_gaps"]))
    row["confirmed_issues"].append({"exception_type": "STALE_TRACKING", "label": "Stale tracking", "age_hours": 6})
    result = triage_demo.operations_overview([row])
    assert all(group["case_ids"] == ["late"] for group in result["review_gaps"])
    assert len(result["longest_confirmed"]) == 1
    assert result["longest_confirmed"][0]["age_hours"] == 24
    assert triage_demo.operations_overview([])["longest_confirmed"] == []
