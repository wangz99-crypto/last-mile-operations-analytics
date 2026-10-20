# Portfolio Operations Exception Console

Base: `bf563c37eb387c4dcfb245a17b86819ccedca5df`, tag `answerability-semantic-v2_1-qwen-v0.1-semantic-failed`. Entry worktree was clean.

## Runtime boundary

The independent FastAPI app `src.portfolio:app` is the smallest no-model launch path. The same router mounts in the original gateway. The former root UI is now `/gateway`, including its existing demo cookie behavior. Existing `/ask` logic is unchanged.

Public endpoints expose only predefined synthetic cases, their live deterministic analysis, and exact public policy sections. They deliberately need no API key: there is no private data, upload, arbitrary query, persistence or external action behind them. Do not extend these endpoints to operational data without authentication and an appropriate service boundary.

The API first verifies the full public SOP corpus, then calls `triage_snapshot`, then resolves the result's exact section references with `retrieve_case_sections`. It does not query BGE or execute semantic inference. Explanations map triggered rule IDs to readable statements; raw trace remains available. Retrieval rank is not presented as confidence.

The late case reuses `late_with_gaps.example.json` input. Normal uses `normal.example.json` input. The remaining cases are small deterministic variations of the normal public example. The 10 shipments cover ready actions, monitoring, missing facts, conflicting notices and normal operation. The missing-attempt-identity example uses the engine's existing `RAW_VALIDATION_CASE` profile to preserve its dependency-scoped blocker. Only manifest, policy, input and input_profile enter the engine; illustrative expected labels are not used. All input checksums are computed from the supplied facts.

`GET /api/triage/queue` runs these same inputs through the engine and exact policy resolver. Queue action state and priority are engine outputs, not presentation overrides. The queue contains three ready, three needs-review, three monitoring and one normal shipment. Known age is the longest confirmed exception duration; for example, a 30-hour scan gap has six hours of stale-exception age after the 24-hour detection boundary. Unknown ages stay unknown. The queue sorts by priority, descending known age, then shipment ID.

## Honest demo interactions

- Operations overview uses the queue's existing engine outputs, not an independent mock data source. It remains a full-snapshot summary when the queue is filtered or human review is recorded locally. Chart clicks clear any search text, filter the underlying membership, or open a ranked shipment. Gap drill-down opens decision details and highlights the affected judgment without changing independently supported actions.

## Overview metric definitions

| Metric | Grain and computation | Limits |
|---|---|---|
| Action status | One overall engine state per shipment; 3 ready, 3 review, 3 monitor, 1 normal. Shipment-wide blockers take precedence, otherwise ready > review > monitor > normal. | Counts only the fixed synthetic snapshot; local review does not change recommendations. |
| Review gaps | Unique shipments per affected-judgment group, deduplicated within group. Address 2, attempt history/identity 2, promise 1, tracking history 1. | Four distinct shipments across six memberships. Groups overlap; gaps neither prove an exception nor necessarily block a whole shipment. |
| Longest confirmed issue | One row per shipment with a TRUE check and known engine-derived age; take the maximum, tie-break by type, then sort shipments by age and ID. Six ranked shipments: 24, 24, 22, 6, 6, 3 hours. | Excludes unknown ages and normal checks. This is neither queue waiting time nor staff performance. |
| Unknown-start disclosure | Unique shipments with at least one TRUE or UNKNOWN issue check lacking a start: four. | DEMO-001 also has a confirmed 24-hour issue and appears in the ranking. Unresolved checks do not prove that an issue exists. |

The ten scenarios demonstrate metric definition, aggregation and drill-down. They are not a representative operational sample. No time series, root-cause claim or realized ROI is inferred.

## Local interaction boundaries

- Temporary owner reading aid: `/zh` and `/zh/engineering` reuse the English templates and APIs with a Chinese display-only translation script (`portfolio_zh.js`). English routes do not load it. Raw JSON, SOP source text, source identities and scientific values remain unchanged; the page labels this boundary and links back to English. This is a removable preview, not a separate localized scientific release.

- On initial queue load, DEMO-001 is selected and analyzed automatically without moving the reader's scroll position. Other rows remain selectable, and selection still clears when a filter excludes it. The automatic choice does not record human approval or send an action.

- The first screen explains delivery issues without assuming logistics knowledge. Queue labels use delivery issue, next step, issue age and policy support; an optional action guide explains the four unchanged engine states. Multi-issue rows show the first check plus a remaining count, with all checks retained in decision details. Unconfirmed checks are labeled as needing review rather than asserted as established problems.
- The coverage example is introduced as a missing operating-rule scenario. The main page explains the LLM experiment's purpose and measured boundary; `/engineering` retains the scientific detail. These are presentation changes, not new semantic capabilities.

- Approve, change action and escalate update page-local review state. There is no action API, browser storage or external-system write. Review decisions survive shipment switching, support the unreviewed filter and reset on page reload. A successful explicit re-run clears only that shipment's local review decision; it rechecks the same fixed facts.
- A handoff brief includes only independently ready categories and their exact policy references, with unresolved facts listed separately. It is a local draft requiring human review, not a sent escalation.
- The selected shipment starts with action, priority and two reasons. Evidence, decision details and facts are collapsed by default. Next steps reflect actual blockers or action state, without modifying engine rules.
- The policy coverage card is one predefined reimbursement-amount question for bundle `1.0-demo`. The public corpus specifies exception handling and handoff, not an amount. The card quotes `SOP-06 / handoff-boundary`, which prohibits issuing refunds. That boundary is not proof of general semantic abstention, and no arbitrary question input is offered.
- Engineering metrics live on `/engineering` as a static, labeled summary of the owner-reviewed experiment, not a fresh or live evaluation. The workflow links to this page without displaying research scores. The full scientific artifacts remain untouched and are not mounted as static assets.
- Failed HTTP analysis clears prior results and reports unavailability. A late response for a previously selected case cannot overwrite the current case. All policy text is rendered as text, not executable HTML.

## Cross-platform policy-byte preservation

The public artifact manifest freezes CRLF file bytes. Git stores these text blobs
with LF, so a default Linux checkout previously failed the policy checksum check
and the queue returned 503. Thirteen exact-path `.gitattributes` rules now specify
`text eol=crlf` for the manifest-listed public files. Policy content, manifest
hashes and runtime integrity enforcement are unchanged. No evaluation artifact
is covered by these new rules.

A fresh public-runtime checkout with `core.autocrlf=false` and `core.eol=lf`
matched all 13 frozen file hashes and loaded 25 sections and all 10 shipments.
This checks deployment byte portability rather than rerunning any model or
scientific evaluation.

## Verification scope

Use existing gateway tests plus the input-only engine, engine diagnostics, section-store and exact-retrieval suites. These suites use public runtime policy and synthetic inputs rather than DEVELOPMENT or HELD_OUT data. Do not run broad evaluation discovery as a substitute. Portfolio tests compare real API results to the unchanged engine, verify exact evidence and hashes, reject arbitrary inputs, and check fail-closed behavior when policy integrity fails.

There is no frontend bundler, configured lint pipeline or type-check pipeline. Check JavaScript with `node --check`, Python syntax, route tests, and browser interaction/layout checks. Docker copies only the public domain runtime directories, not domain evaluation files. The original gateway Docker image still includes its historical optional embedding dependencies; use the standalone local app for a model-free portfolio preview.

Deferred: operational persistence, authentication for real shipment data, carrier integrations, production deployment, free-form questions, a replacement semantic model, and all new research/evaluation. The existing scientific result is a measured boundary, not a claim of production readiness.

## Sprint verification results

- Selected existing gateway/domain suites plus portfolio tests after overview integration: **98 passed, 100 subtests passed**. One dependency deprecation warning from Starlette/AnyIO; no failing test. Overview checks cover membership, within-group deduplication, cross-group overlap, one longest issue per shipment and unknown-start exclusions.
- Plain-language follow-up: all **18 existing portfolio tests passed**, JavaScript syntax passed, and desktop/mobile copy and rendering were checked. No additional model or benchmark execution.
- Python syntax and JavaScript `node --check`: PASS. No bundler/linter/type checker is configured. Docker build was not executed because Docker is unavailable on this host.
- Browser checks include priority/review/ready filters, shipment search and empty-state recovery, actual missing-identity next steps, collapsed evidence, scoped handoff draft, local review persistence on shipment switching, and blocked escalation for a non-ready shipment. Desktop and mobile layout checks cover the queue and selected shipment. Engineering remains separately navigable.
- Existing README preserved in GATEWAY_REFERENCE.md with original checkout bytes; content also matches the base Git file after line-ending normalization.
- No tracked domain/scientific-core files changed. No DEVELOPMENT/HELD_OUT reads or model qualification runs were part of these checks.
- Tests and local preview required execution outside the Windows sandbox: the sandbox blocked asyncio's local socketpair. An isolated repository `.venv` holds only gateway/test dependencies; the frozen semantic-model environment was not modified.
