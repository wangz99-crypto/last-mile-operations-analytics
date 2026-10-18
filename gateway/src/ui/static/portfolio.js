"use strict";
const $ = id => document.getElementById(id);
const stateNames = {NORMAL: "Normal", MONITOR: "Monitor", NEEDS_REVIEW: "Needs review", READY_TO_ESCALATE: "Ready to escalate"};
const actionExplanations = {
  NORMAL: "No action is needed based on the current shipment facts.",
  MONITOR: "Keep watching. The issue has not yet met the operating rule for further action.",
  NEEDS_REVIEW: "A person needs to check missing or conflicting facts before deciding what to do.",
  READY_TO_ESCALATE: "The evidence supports a human review for further action by the responsible operations team. Nothing is sent automatically."
};
const issueNames = {"Late delivery":"Overdue delivery", "Stale tracking":"No recent tracking update", "Failed attempt / address":"Delivery attempt / address issue"};
const issueName = value => issueNames[value] || value;
const decisionNames = {LATE_DELIVERY:"Delivery timing", STALE_TRACKING:"Tracking inactivity", FAILED_ATTEMPT:"Failed delivery attempts", ADDRESS_EXCEPTION:"Address status"};
const unconfirmedNames = {"Late delivery":"Delivery timing needs review", "Stale tracking":"Tracking history needs review", "Failed attempt / address":"Attempt / address facts need review"};
const supportNames = {"Ready basis verified; other gaps":"Supported; other gaps remain", "Review gaps":"Facts need review", "No active exception":"No active issue", "Complete":"Complete"};
let queue = [], filter = "all", selectedId = null, analysis = null, requestVersion = 0;
let overview = null;
const reviews = new Map();
function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
function date(value) {
  return value ? new Intl.DateTimeFormat("en-GB", {day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",timeZone:"UTC",hour12:false}).format(new Date(value)) + " UTC" : "Not provided";
}
function jump(id) {
  $(id).scrollIntoView({behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block:"start"});
}
async function jsonRequest(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(url, {...options, signal:controller.signal});
    if (!response.ok) throw new Error("Verified analysis is unavailable. No recommendation was issued. Please try again.");
    return await response.json();
  } finally { clearTimeout(timeout); }
}
function visibleRows() {
  const query = $("shipment-search").value.trim().toLowerCase();
  return queue.filter(row => (filter === "all" || filter === row.priority || filter === row.action_state ||
    (filter === "unreviewed" && !reviews.has(row.case_id)) ||
    (filter.startsWith("gap:") && row.review_gaps.some(gap=>gap.group === filter.slice(4))) ||
    (filter === "unknown-age" && row.unconfirmed_start_checks.length > 0)) && row.shipment_id.toLowerCase().includes(query));
}
function metricBar(label, value, proportion, onClick, type = "") {
  const button = el("button",null,"metric-bar " + type); button.type = "button";
  const head = el("span",null,"metric-bar-head"); head.append(el("span",label),el("strong",value));
  const track = el("span",null,"metric-bar-track"), fill = el("span",null,"metric-bar-fill");
  track.setAttribute("aria-hidden","true"); fill.style.width = `${Math.max(0,Math.min(100,proportion*100))}%`;
  track.append(fill); button.append(head,track); button.addEventListener("click",onClick); return button;
}
function setQueueFilter(value, fromOverview = false) {
  filter = value;
  if (fromOverview) $("shipment-search").value = "";
  for (const button of document.querySelectorAll("[data-filter]")) button.setAttribute("aria-pressed",String(button.dataset.filter === filter));
  applyFilter();
  if (analysis) renderDetail(analysis);
  if (fromOverview) jump("workspace");
}
function renderOverview() {
  if (!overview) return;
  const total = overview.shipment_count;
  $("action-chart").replaceChildren(...overview.action_status.map(item=>{
    const button = metricBar(stateNames[item.state],`${item.case_ids.length} / ${total}`,item.case_ids.length / (total || 1),()=>setQueueFilter(item.state,true));
    button.dataset.metricFilter = item.state; button.disabled = !item.case_ids.length; return button;
  }));
  $("gap-chart").replaceChildren(...overview.review_gaps.map(item=>{
    const button = metricBar(item.label,`${item.case_ids.length} / ${total}`,item.case_ids.length / (total || 1),()=>setQueueFilter("gap:" + item.group,true),"gap");
    button.dataset.metricFilter = "gap:" + item.group; return button;
  }));
  if (!overview.review_gaps.length) $("gap-chart").append(el("p","No review gaps in this snapshot.","metric-note"));
  const maxAge = overview.longest_confirmed[0]?.age_hours || 1;
  $("age-chart").replaceChildren(...overview.longest_confirmed.map(item=>{
    const button = metricBar(item.shipment_id,`${Number(item.age_hours.toFixed(1))}h`,item.age_hours/maxAge,()=>{
      $("shipment-search").value = ""; setQueueFilter("all"); loadShipment(item.case_id);
    });
    button.setAttribute("aria-label",`${item.shipment_id}: ${issueName(item.label)}, ${item.age_hours} hours. Open shipment.`);
    button.title = issueName(item.label); return button;
  }));
  $("unknown-age").textContent = `${overview.unconfirmed_start_case_ids.length} shipments have unconfirmed issue start times`;
  $("unknown-age").disabled = !overview.unconfirmed_start_case_ids.length;
  $("age-overlap").textContent = `${overview.known_and_unconfirmed_case_ids.length} of these also appear in the known-age ranking. Different checks can have different certainty.`;
  $("overview-status").textContent = "Full snapshot. Click a bar to explore the underlying shipments; queue filters do not change these totals.";
  $("overview-status").className = "footnote"; $("overview-charts").hidden = false;
}
$("unknown-age").addEventListener("click",()=>setQueueFilter("unknown-age",true));
$("reset-drilldown").addEventListener("click",()=>{ $("shipment-search").value = ""; setQueueFilter("all"); });
function renderQueue() {
  $("count-all").textContent = queue.length;
  $("count-ready").textContent = queue.filter(row=>row.action_state === "READY_TO_ESCALATE").length;
  $("count-review").textContent = queue.filter(row=>row.action_state === "NEEDS_REVIEW").length;
  $("count-reviewed").textContent = reviews.size;
  const gap = overview?.review_gaps.find(item=>"gap:" + item.group === filter);
  $("drilldown-context").hidden = filter === "all";
  $("drilldown-label").textContent = gap ? "Review gap: " + gap.label : filter === "unknown-age" ? "Shipments with unconfirmed issue start times" : "Queue view: " + (stateNames[filter] || (filter === "HIGH" ? "High priority" : "Not reviewed locally"));
  for (const button of document.querySelectorAll("[data-metric-filter]")) button.setAttribute("aria-pressed",String(button.dataset.metricFilter === filter));
  const visible = visibleRows();
  $("queue-caption").textContent = `${visible.length} of ${queue.length} shipments. Select a shipment to review.`;
  $("queue-empty").hidden = visible.length > 0;
  $("queue-rows").replaceChildren();
  for (const item of visible) {
    const row = el("tr"); row.dataset.caseId = item.case_id;
    row.classList.toggle("selected", item.case_id === selectedId);
    const identity = el("td"), button = el("button", item.shipment_id, "shipment-link");
    button.setAttribute("aria-label", "Review " + item.shipment_id);
    button.setAttribute("aria-pressed", String(item.case_id === selectedId));
    identity.append(button);
    if (reviews.has(item.case_id)) identity.append(el("small", "Reviewed locally", "reviewed-label"));
    const exception = el("td");
    const firstIssue = item.exceptions[0];
    exception.append(el("span", firstIssue ? (item.unconfirmed_exceptions.includes(firstIssue) ? unconfirmedNames[firstIssue] : issueName(firstIssue)) : "No active issue"));
    if (item.exceptions.length > 1) exception.append(el("small", `+ ${item.exceptions.length - 1} more · View details`, "issue-more"));
    const priority = el("td"); priority.append(el("span", item.priority, "queue-priority " + item.priority.toLowerCase()));
    const action = el("td"); action.append(el("span", stateNames[item.action_state], "state-pill " + (item.action_state === "NEEDS_REVIEW" ? "review" : "")));
    const age = el("td", item.age_hours == null ? (item.action_state === "NORMAL" ? "Not applicable" : "Unknown") : `${Number(item.age_hours.toFixed(1))}h`);
    row.append(identity, exception, priority, action, age, el("td", supportNames[item.evidence_status] || item.evidence_status));
    row.addEventListener("click", ()=>loadShipment(item.case_id));
    $("queue-rows").append(row);
  }
}
function clearSelection() {
  selectedId = null; analysis = null; requestVersion++;
  $("result").hidden = true; $("detail-error").hidden = true;
  $("selected-title").textContent = "Select a shipment to start";
  $("detail-status").textContent = "Choose any shipment in the queue to see its recommended action and next steps.";
}
function applyFilter() {
  if (!visibleRows().some(row=>row.case_id === selectedId)) clearSelection();
  renderQueue();
}
for (const button of document.querySelectorAll("[data-filter]")) {
  button.addEventListener("click",()=>setQueueFilter(button.dataset.filter));
}
$("shipment-search").addEventListener("input", applyFilter);
$("clear-filters").addEventListener("click",()=>{
  $("shipment-search").value = "";
  document.querySelector('[data-filter="all"]').click();
});
function resetPanels() {
  for (const id of ["policy-panel", "decision-panel", "facts-panel"]) $(id).open = false;
  $("change-panel").hidden = true; $("change").setAttribute("aria-expanded", "false");
  $("brief-panel").hidden = true; $("handoff-brief").value = "";
}
function renderFacts(packet) {
  const shipment = packet.input.shipments[0];
  $("facts-summary").textContent = shipment.shipment_id + " / " + shipment.carrier;
  const rows = [["Carrier",shipment.carrier],["Reference time",date(packet.manifest.as_of)],["Delivery promise",date(shipment.promised_delivery_at)],["Shipment status",shipment.current_status.replaceAll("_"," ")],["Tracking history",packet.input.history_declarations[0].history_complete ? "Declared complete" : "Incomplete"]];
  $("facts").replaceChildren();
  for (const [label,value] of rows) { const cell = el("div"); cell.append(el("dt",label),el("dd",value)); $("facts").append(cell); }
  const events = el("div",null,"event-facts"); events.append(el("dt","Recorded events"));
  for (const event of [...packet.input.tracking_events].sort((a,b)=>a.event_time.localeCompare(b.event_time))) events.append(el("dd",`${event.event_code.replaceAll("_"," ")} / ${date(event.event_time)}${event.attempt_id ? " / " + event.attempt_id : ""}`));
  $("facts").append(events); $("raw-case").textContent = JSON.stringify(packet,null,2);
}
function renderDetail(data) {
  analysis = data; const result = data.result, summary = data.summary;
  $("selected-title").textContent = summary.shipment_id;
  $("action-state").textContent = stateNames[result.aggregate_action_state];
  $("action-explanation").textContent = actionExplanations[result.aggregate_action_state];
  $("priority").textContent = "PRIORITY / " + result.priority;
  $("top-reasons").replaceChildren(...summary.top_reasons.map(reason=>el("li",reason)));
  $("next-steps").replaceChildren(...summary.next_steps.map(step=>el("li",step)));
  const ready = result.aggregate_action_state === "READY_TO_ESCALATE";
  $("prepare-brief").hidden = !ready;
  $("next-note").textContent = ready ? "Prepare the supported scope, review the gaps, then hand off through your operational system. This demo does not send anything." : "This is a fixed snapshot. Corrected or new source facts must come from the operational system; re-running here checks the same data.";
  $("assessments").replaceChildren();
  for (const a of data.assessments) {
    const row = el("div",null,"assessment"), head = el("div",null,"assessment-head"), list = el("ul");
    const matchingCodes = new Set(summary.review_gaps.filter(g=>"gap:" + g.group === filter && g.exception_type === a.exception_type).map(g=>g.code));
    row.classList.toggle("focused-gap",matchingCodes.size > 0);
    head.append(el("h4",issueName(a.label)),el("span",stateNames[a.action_state],"state-pill" + (a.action_state === "NEEDS_REVIEW" ? " review" : "")));
    for (const reason of a.explanations) list.append(el("li",reason));
    for (const blocker of a.blockers) {
      const item = el("li","Review needed: " + blocker.reason,"blocker");
      if (matchingCodes.has(blocker.code)) item.append(el("strong"," Selected gap affects: " + (decisionNames[blocker.dependent_decision] || blocker.dependent_decision),"gap-impact"));
      list.append(item);
    }
    row.append(head,list); $("assessments").append(row);
  }
  $("raw-result").textContent = JSON.stringify({validation_findings:data.validation_findings,result},null,2);
  $("evidence-count").textContent = `${data.evidence.length} policy sections explain this decision`;
  $("evidence").replaceChildren();
  for (const evidence of data.evidence) {
    const item = el("details",null,"evidence-item"), heading = el("summary");
    heading.append(el("span",evidence.policy_id,"evidence-id"),el("strong",evidence.section_title));
    item.append(heading,el("p",evidence.why,"evidence-why"),el("div",evidence.text.trim(),"policy-text"),el("p",`${evidence.section_id} / ${evidence.version}`,"footnote"));
    const trace = el("details"); trace.append(el("summary","Source identity"),el("pre",`${evidence.source_path}\nSHA-256: ${evidence.content_hash}\nRules: ${evidence.rule_ids.join(", ")}`));
    item.append(trace); $("evidence").append(item);
  }
  resetPanels(); renderFacts(data.packet);
  const focusedGap = summary.review_gaps.find(g=>"gap:" + g.group === filter);
  $("gap-focus").hidden = !focusedGap;
  if (focusedGap) {
    $("gap-focus").textContent = "Selected gap: " + focusedGap.label + ". Highlighted checks need review; independent supported actions remain valid.";
    $("decision-panel").open = true;
  }
  $("human-action").value = result.aggregate_action_state;
  $("review-status").textContent = reviews.get(data.case_id) || "No human decision recorded.";
  $("result").hidden = false;
  $("detail-status").textContent = "Three checks complete. Review the next action below.";
}
async function loadShipment(caseId, rerun = false, scrollToDetail = true) {
  selectedId = caseId; analysis = null; const version = ++requestVersion;
  $("result").hidden = true; $("detail-error").hidden = true;
  $("selected-title").textContent = queue.find(row=>row.case_id === caseId).shipment_id;
  $("detail-status").textContent = "Checking shipment facts and supporting policy...";
  renderQueue();
  if (scrollToDetail) jump("selected-shipment");
  try {
    const data = await jsonRequest("/api/triage/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({case_id:caseId})});
    if (version !== requestVersion) return;
    if (rerun) reviews.delete(caseId);
    queue = queue.map(row=>row.case_id === caseId ? data.summary : row);
    renderDetail(data); renderQueue();
  } catch (error) {
    if (version !== requestVersion) return;
    $("detail-error").textContent = "Analysis unavailable. No recommendation is shown. Select the shipment again to retry.";
    $("detail-error").hidden = false; $("detail-status").textContent = "Unable to verify the selected shipment.";
  }
}
$("analyze").addEventListener("click",()=>{ if (selectedId) loadShipment(selectedId,true); });
function recordReview(message) {
  if (!analysis) return;
  reviews.set(analysis.case_id,message);
  $("review-status").textContent = message; renderQueue();
}
$("approve").addEventListener("click",()=>{ if (analysis) recordReview("Approved locally: " + stateNames[analysis.result.aggregate_action_state] + ". Nothing sent or saved to a server."); });
$("change").addEventListener("click",()=>{
  $("change-panel").hidden = !$("change-panel").hidden;
  $("change").setAttribute("aria-expanded",String(!$("change-panel").hidden));
});
$("save-action").addEventListener("click",()=>{
  if (!analysis) return;
  recordReview("Human override recorded locally: " + stateNames[$("human-action").value] + ". System recommendation unchanged; no operational action taken.");
  $("change-panel").hidden = true; $("change").setAttribute("aria-expanded","false");
});
$("escalate").addEventListener("click",()=>{
  if (!analysis) return;
  if (analysis.result.aggregate_action_state !== "READY_TO_ESCALATE") {
    $("review-status").textContent = "Not ready for policy-supported escalation. Review the gaps or monitoring conditions first. Nothing sent."; return;
  }
  recordReview("Marked locally for human escalation handoff. Only independently supported categories may be included. Nothing sent or saved to a server.");
});
$("prepare-brief").addEventListener("click",()=>{
  if (!analysis || analysis.result.aggregate_action_state !== "READY_TO_ESCALATE") return;
  const lines = ["DRAFT ONLY - HUMAN REVIEW REQUIRED",analysis.summary.shipment_id,"Snapshot: " + analysis.summary.as_of,"Supported escalation scope:"];
  for (const a of analysis.assessments.filter(a=>a.action_state === "READY_TO_ESCALATE")) {
    lines.push(a.label + ": " + a.explanations.join(" "));
    lines.push("Policy: " + a.expected_sections.map(s=>s.policy_id + "/" + s.section_id + "@" + s.version).join(", "));
  }
  lines.push("Unresolved facts (not part of the ready basis):");
  const gaps = analysis.assessments.flatMap(a=>a.blockers.map(b=>a.label + ": " + b.reason));
  lines.push(...(gaps.length ? gaps : ["None identified in this snapshot."]),"Nothing sent, saved to a server, or changed in an operational system.");
  $("handoff-brief").value = lines.join("\n"); $("brief-panel").hidden = false;
});
(async()=>{
  try {
    const data = await jsonRequest("/api/triage/queue"); queue = data.items;
    overview = data.overview; renderOverview();
    $("snapshot-time").textContent = "Snapshot / " + date(data.as_of);
    renderQueue();
    const featured = queue.find(row => row.shipment_id === "DEMO-001");
    if (featured && !selectedId && filter === "all" && !$("shipment-search").value.trim()) {
      await loadShipment(featured.case_id, false, false);
    }
  } catch (error) {
    $("queue-error").textContent = "The verified queue is unavailable. Reload to try again; no cached recommendations are shown.";
    $("queue-error").hidden = false; $("queue-caption").textContent = "Queue unavailable";
    $("snapshot-time").textContent = "Snapshot unavailable";
    $("overview-status").textContent = "Snapshot metrics unavailable. No cached totals are shown.";
    $("overview-charts").hidden = true;
  }
})();
