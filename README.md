# Last-Mile Operations Analytics & Decision Support

Turn shipment exceptions into consistent, policy-backed actions with traceable SOP evidence and human-controlled escalation.

Built for operations teams handling late deliveries, stale tracking, failed delivery attempts and address issues. This portfolio workspace shows **what needs attention, why, and which operating policy supports the recommendation**.

## Try the workspace

From the repository root, using Python 3.11+:

```bash
python -m venv .venv
# Windows PowerShell: .venv/Scripts/Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r gateway/requirements.txt
python -m uvicorn src.portfolio:app --app-dir gateway --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. No GPU, model weights, embedding dependencies or API key is required for this public synthetic demo. This dedicated app does not start the older gateway's knowledge-base/model lifecycle.

1. Start with the compact **Operations overview**: action distribution, shipments affected by review gaps, and the longest-running confirmed issues. Each chart includes its metric definition and drills into the same 10-shipment queue.
2. Filter by priority, review needs or escalation readiness; search by shipment ID.
3. DEMO-001 is selected automatically, showing a supported overdue-delivery action alongside unresolved checks. Select any row to see its recommended action, priority, top two reasons and **What happens next?**
4. Expand **Why this is supported** for verified SOP sections, or **Decision details** for the complete rule trace.
5. Prepare a local handoff brief for a ready action and record a **Human review** decision. Review progress survives shipment switching within this page, but resets on reload. Nothing is sent or saved to an operational system.

| Synthetic shipments | Operational story |
|---|---|
| DEMO-001 / DEMO-006 | Late delivery at escalation and monitoring stages; unrelated gaps remain visible. |
| DEMO-002 / DEMO-007 | Stale tracking at monitoring and escalation stages. |
| DEMO-003 / DEMO-008 | Multiple failed attempts with an active address notice, and a single failed attempt. |
| DEMO-004 / DEMO-009 / DEMO-010 | Missing promise, missing attempt identity and conflicting address notices require review. |
| DEMO-005 | A normal shipment provides a comparison. |

All cases use a **fixed snapshot time**, synthetic facts and fictional policy. They do not track real shipments. Inputs reuse the public illustrative examples and add small, documented variations; no evaluation question or benchmark label is used.

## Evidence before action

```text
Shipment facts -> Deterministic business rules -> Exact SOP sections
               -> Evidence-backed explanation -> Human review
```

- **Consistent triage:** business rules produce the recommendation, not a model response.
- **Operational visibility:** summarize the same engine results, identify information gaps and drill into the underlying shipment. All totals describe designed synthetic scenarios, not representative business performance.
- **Traceable evidence:** stable policy/version/section identities connect every rule assessment to real SOP text. Integrity failures prevent the recommendation.
- **Defined boundaries:** a scoped reimbursement coverage example demonstrates an unsupported policy request. It is not a general-purpose question-answering classifier.
- **Human control:** readiness is distinct from operational approval. There is no carrier contact, refund, shipment mutation or production action integration.

The default UI is an operations workspace. The separate **Engineering** page at `/engineering` contains the engineering detail and evaluation lessons.

## Evaluation-driven design

**Structured output does not guarantee correct reasoning.** The constrained small-model runtime passed its structural smoke recovery. The subsequent frozen 12-case semantic qualification failed: final-decision accuracy was 5/12, structural acceptance 9/12, and supported-evidence coverage 37.50%.

The owner-reviewed `SEMANTIC_MATERIAL_SUPPORT_V2_1` candidate using Qwen2.5-1.5B is **rejected for DEVELOPMENT evaluation**. It is not used by this workspace. This measured limitation informs the architecture: deterministic business rules and human review retain decision responsibility. It does not invalidate every possible semantic architecture.

The scientific core, policy bundle and historical evaluation artifacts remain frozen. This sprint does not rerun qualification, introduce a model, or expose DEVELOPMENT/HELD_OUT data.

## Implementation and verification

FastAPI + plain HTML/CSS/JavaScript, following the existing stack; no frontend build system or new UI framework.

- `gateway/src/portfolio.py`: public demo routes and standalone app.
- `gateway/src/triage_demo.py`: allowlisted synthetic inputs, unchanged `triage_snapshot`, verified `SectionStore`, and `retrieve_case_sections` integration.
- `gateway/src/ui/templates/portfolio.html` and `gateway/src/ui/static/portfolio.*`: responsive queue, collapsed evidence, next steps and local human-review interactions.
- `gateway/src/ui/templates/engineering.html`: separate engineering and evaluation page.
- `GET /api/triage/queue`: computes the 10 allowlisted shipment summaries, ordered by priority and longest known exception age. Unknown age is never treated as zero.
- `POST /api/triage/analyze`: accepts **only** a predefined `case_id`; arbitrary shipment input and arbitrary questions are not supported.
- The existing gateway app also serves the portfolio at `/`; its former UI is preserved at `/gateway`. `/ask` and its existing authentication/response contract are unchanged.

Offline tests that do not read benchmark data (PowerShell, from repo root):

```powershell
python -m pip install pytest
$env:PYTHONPATH = "gateway;."
$env:DISABLE_EMBEDDINGS = "1"
python -m pytest gateway/tests gateway/domain/tests/test_engine.py gateway/domain/tests/test_engine_diagnostics.py gateway/domain/tests/test_section_store.py gateway/domain/tests/test_exact_retrieval.py
node --check gateway/src/ui/static/portfolio.js
```

Full scientific evaluation commands are deliberately not part of demo startup or this verification scope. See [portfolio implementation notes](docs/PORTFOLIO.md) for boundaries and checks.

## Deeper project history

- [Original gateway README, preserved verbatim](docs/GATEWAY_REFERENCE.md): earlier tool-first RAG architecture, routes, deployment notes and research commands. Its older live deployment is not evidence that this new sprint is deployed.
- [Domain contract](gateway/domain/CONTRACTS.md) and [engine implementation](gateway/domain/engine/IMPLEMENTATION.md).
- [Policy retrieval interfaces](gateway/domain/retrieval/README.md).
- [Original project specification](PROJECT_SPEC.md).

Public UI improvements do not supersede these scientific records. No private benchmark or research-artifact directory is served by the demo.
