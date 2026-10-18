// Temporary reading aid, loaded only by /zh routes. Engine and source evidence stay unchanged.
(() => {
  "use strict";
  const copy = {
    "SUMMARY → DIAGNOSE → DRILL DOWN → ACT":"汇总 → 诊断 → 下钻 → 行动",
    "Operations overview":"运营概览",
    "FULL SNAPSHOT · CLICK TO EXPLORE":"完整快照 · 点击可下钻",
    "The 10 shipments are designed synthetic scenarios for demonstrating the analysis workflow; they are not a representative operational sample.":"这 10 个订单是专门设计的模拟场景，用于演示分析流程，不是具有代表性的真实业务样本。",
    "Loading snapshot metrics...":"正在计算快照指标……",
    "Action status":"处理状态分布",
    "Unit: shipment · one overall action each":"统计单位：订单 · 每单只有一个总体建议状态",
    "Review gaps":"待核实的信息",
    "Unit: shipments affected per gap group":"统计单位：每类缺口影响的订单数",
    "A gap may affect one judgment without blocking the whole shipment.":"信息缺口可能只影响某一项判断，不一定阻塞整票订单。",
    "Longest-running confirmed issues":"持续最久的已确认问题",
    "Unit: shipment · longest confirmed issue age":"统计单位：订单 · 取已确认问题的最长持续时间",
    "How this metric is defined":"这个指标怎么算？",
    "Count distinct shipments by the engine's overall action. Shipment-wide blockers require review; otherwise the order is ready to escalate, needs review, monitor, then normal.":"按引擎给出的总体建议状态统计不同订单。有整票级阻碍时先要求核实；否则按“可升级审核 → 需核实 → 观察 → 正常”的顺序选取适用状态。",
    "Counts describe this full synthetic snapshot only. Queue filters and local human decisions do not change the engine's recommendations.":"只描述这份完整模拟快照。下方列表筛选和本页人工意见不会改变引擎建议或这些总数。",
    "Group actual review blockers by the judgment they affect: delivery promise, tracking history, attempt history/identity, or address state. Count each shipment once per group, even if multiple blockers apply.":"按实际阻碍所影响的判断分组：送达承诺、物流历史、派送历史/编号、地址状态。一个订单在同组中最多计一次，即使有多个阻碍。",
    "A shipment can appear in several groups; do not add these counts as a shipment total. Gaps do not establish a root cause or prove that an issue occurred.":"同一订单可出现在多组，不能把各组数量直接相加当作订单总数。信息缺口也不能证明根本原因，或证明某个异常已经发生。",
    "For each shipment, take the longest engine-derived age among confirmed issues with a known start. Sort longest first, then shipment ID. Normal checks and unknown ages are excluded.":"每个订单只取已确认、且起点已知的问题中的最长时长。按时长降序、再按订单号排序；正常检查和未知时长不参加排名。",
    "Unknown starts count shipments with at least one unresolved or confirmed issue check whose start cannot be established. They can overlap the ranking; an unresolved check is not proof of an issue. This is not queue waiting time, backlog or team performance.":"未知起点统计：至少一项待确认或已确认的问题检查无法确定起始时间的订单。它们可同时出现在已知时长排名中；待确认不等于已发生异常。这不是排队时长、积压或团队绩效。",
    "Delivery promise missing or invalid":"承诺送达时间缺失或无效",
    "Tracking history incomplete":"物流历史不完整",
    "Attempt history / identity incomplete":"派送历史或尝试编号不完整",
    "Address state unresolved":"地址状态未明确",
    "Other facts need review":"其他事实待核实",
    "No review gaps in this snapshot.":"本快照没有待核实的信息缺口。",
    "Full snapshot. Click a bar to explore the underlying shipments; queue filters do not change these totals.":"基于完整快照。点击条形图查看对应订单；列表筛选不会改变概览总数。",
    "Snapshot metrics unavailable. No cached totals are shown.":"无法获取快照指标，不显示旧的缓存总数。",
    "Shipments with unconfirmed issue start times":"至少一项问题起始时间无法确认的订单",
    "Show all shipments":"显示全部订单",
    "Delivery timing":"送达时间判断",
    "Tracking inactivity":"物流长期未更新判断",
    "Failed delivery attempts":"派送失败判断",
    "Address status":"地址状态判断",
    "Last Mile | Operations Exception Console":"最后一公里配送｜异常处理工作台（临时中文）",
    "Engineering | Last-Mile Exception Triage":"工程设计与评估｜临时中文预览",
    "Skip to exception queue":"跳到配送问题列表",
    "LAST MILE":"最后一公里配送",
    "OPERATIONS CONSOLE":"运营工作台",
    "Delivery issue queue":"配送问题列表",
    "Engineering":"工程与评估",
    "Synthetic workspace":"模拟数据演示",
    "FROM DISPATCH TO DOORSTEP":"从发货到送达",
    "Know what needs attention.":"知道哪些订单需要处理。",
    "Know what to do next.":"知道下一步该做什么。",
    "One queue for delivery issues that need attention. See which shipments need help, what the operating rules recommend, and what a person should do next.":"把需要关注的配送问题放在同一个列表里：先看哪些订单需要处理，再看操作规则建议怎么做，最后由人决定下一步。",
    "Review delivery issues":"查看配送问题",
    "YOUR REVIEW WORKFLOW":"你的处理流程",
    "Find the issue.":"发现问题。",
    "Check the reason.":"核对依据。",
    "Decide the next step.":"决定下一步。",
    "The system checks facts against operating rules.":"系统根据订单事实检查是否符合操作规则。",
    "A person approves any further action.":"是否采取后续行动，由人审核。",
    "OPERATIONS WORKSPACE":"运营工作区",
    "Exception queue":"配送异常列表",
    "Delivery issues that need attention.":"这些配送问题需要关注。",
    "Each shipment is checked for overdue delivery, missing tracking updates, and delivery attempt or address problems. The system prioritizes the work and shows the next step supported by the operating rules.":"系统检查每个订单是否逾期、是否缺少近期物流更新、是否存在派送尝试或地址问题，再按优先级排序，给出有操作规则支持的下一步。",
    "Shipments":"订单总数",
    "Ready to escalate":"可提交人工升级审核",
    "Need review":"需要核实",
    "Needs review":"需要核实",
    "Reviewed locally":"本页已复核",
    "Fixed synthetic snapshot. Counts and recommendations are computed from shipment facts. Local review progress resets on reload.":"使用固定时间点的模拟数据；数量和建议由订单事实计算得出。刷新页面会清空本页复核记录。",
    "What do the actions mean?":"这四种处理状态是什么意思？",
    "Normal":"正常",
    "Monitor":"继续观察",
    "No action needed right now.":"目前不需要采取行动。",
    "Keep watching. The issue has not reached the next action threshold.":"继续关注，还没有达到需要进一步处理的规则条件。",
    "Some required facts are missing, unclear, or conflicting.":"必要的信息缺失、不清楚，或相互矛盾，需要人工核实。",
    "The operating rules support sending this case for human escalation review.":"已符合操作规则，可以提交给人工审核是否交由相关团队进一步处理。“升级”不是自动执行，也不是软件升级。",
    "All shipments":"全部订单",
    "High priority":"高优先级",
    "Not reviewed locally":"本页尚未复核",
    "Find shipment":"查找订单",
    "e.g. DEMO-003":"例如 DEMO-003",
    "Shipment":"订单",
    "Delivery issue":"配送问题",
    "Priority":"优先级",
    "Next step":"建议下一步",
    "Issue age":"问题持续时间",
    "Policy support":"规则与事实依据",
    "Overdue delivery":"已超过承诺送达时间",
    "No recent tracking update":"近期没有物流扫描更新",
    "Delivery attempt / address issue":"派送尝试或地址问题",
    "Delivery timing needs review":"送达时间信息待核实",
    "Tracking history needs review":"物流历史待核实",
    "Attempt / address facts need review":"派送尝试或地址信息待核实",
    "No active issue":"当前无异常",
    "Supported; other gaps remain":"当前行动有依据；其他信息仍有缺口",
    "Facts need review":"事实需要核实",
    "Complete":"所需依据完整",
    "HIGH":"高",
    "MEDIUM":"中",
    "LOW":"低",
    "Unknown":"未知",
    "Not applicable":"不适用",
    "No shipments match these filters.":"没有符合筛选条件的订单。",
    "Clear filters":"清除筛选",
    "Sorted by priority, then longest known issue age: time since the issue met the operating rule, not since the shipment was created. Unknown means the start time cannot be confirmed. Policy support shows whether the recommendation has the facts and operating rules it needs.":"先按优先级排序，再按已知问题持续时间排序。持续时间从问题满足异常规则时算起，不是订单创建后的总时长。“未知”表示无法确认起点。最后一列说明建议是否具备所需事实和规则依据。",
    "SELECTED SHIPMENT":"当前选中订单",
    "Select a shipment to start":"请选择一个订单",
    "Back to queue":"返回列表",
    "Choose any shipment in the queue to see its recommended action and next steps.":"点击列表中的订单，查看建议动作与下一步。",
    "RECOMMENDED ACTION":"建议动作",
    "No action is needed based on the current shipment facts.":"根据目前的订单事实，无需额外处理。",
    "Keep watching. The issue has not yet met the operating rule for further action.":"继续观察，目前还未达到需要进一步处理的规则条件。",
    "A person needs to check missing or conflicting facts before deciding what to do.":"需要先由人核实缺失或矛盾的信息，再决定如何处理。",
    "The evidence supports a human review for further action by the responsible operations team. Nothing is sent automatically.":"现有依据足以提交人工审核，决定是否交给负责的运营团队进一步处理。系统不会自动发送任何请求。",
    "Delivery is overdue long enough for the operating rules to call for further action.":"逾期时长已经达到操作规则要求进一步处理的条件。",
    "Other checks still need facts. The supported issue can move forward without treating those gaps as resolved.":"其他检查仍缺少信息。有充分依据的这项问题可以继续处理，但不能把其他信息缺口当成已经解决。",
    "The required shipment facts and written operating rules support this next step.":"所需订单事实和书面操作规则均支持这一步行动。",
    "The delivery promise has not been missed.":"尚未超过承诺送达时间。",
    "Delivery is overdue, but has not reached the policy escalation threshold.":"已逾期，但尚未达到规则要求升级处理的时长。",
    "The delivery promise is missing or invalid; lateness cannot be established.":"承诺送达时间缺失或无效，无法确认是否逾期。",
    "The last physical scan is within the policy tracking window.":"最近一次包裹扫描仍在规则允许的时间范围内。",
    "Tracking is stale, but has not reached the policy escalation threshold.":"物流更新已有一段时间未出现，但尚未达到升级处理条件。",
    "There has been no package scan for long enough that the operating rules call for further action.":"包裹长时间没有扫描记录，已达到规则要求进一步处理的条件。",
    "Tracking history is incomplete or invalid; inactivity cannot be established.":"物流历史不完整或无效，无法确认是否长时间没有更新。",
    "Tracking inactivity does not apply to this pre-transit shipment.":"订单尚未进入运输阶段，不适用运输中无更新的检查。",
    "Complete history shows no failed attempts or active address issue.":"完整历史中没有派送失败或未解决的地址问题。",
    "One distinct failed attempt is recorded; the policy calls for monitoring.":"记录了一次独立的派送失败，规则要求继续观察。",
    "Distinct failed attempts meet the policy escalation threshold.":"不同派送尝试的失败次数达到升级处理条件。",
    "An unresolved address notice meets the policy escalation condition.":"尚未解决的地址异常符合升级处理条件。",
    "An attempt or address decision remains unresolved; independent evidence is preserved.":"派送尝试或地址判断仍待核实；其他独立、有效的依据仍然保留。",
    "Scan history is incomplete or invalid for inactivity":"扫描历史不完整或无效，无法判断是否长时间无更新",
    "Attempt history or physical attempt identity is incomplete, invalid or conflicting":"派送历史或每次实际派送的编号缺失、无效或冲突",
    "Incomplete or invalid marker history":"地址状态记录不完整或无效",
    "Current facts do not yet meet a supported escalation condition.":"目前的事实尚不支持升级处理。",
    "No active exception is established across the three checks.":"三类检查均未确认存在当前异常。",
    "The current facts do not call for exception escalation.":"目前的事实不需要升级处理。",
    "MOVE THE WORK FORWARD":"接下来怎么处理",
    "What happens next?":"下一步做什么？",
    "Prepare handoff brief":"准备交接摘要",
    "Human review":"人工审核",
    "Escalate after approval":"审核通过后交由相关团队处理",
    "Find missing attempt identity":"补查缺失的派送尝试编号",
    "Confirm delivery promise":"确认承诺送达时间",
    "Resolve conflicting address notices":"核实相互矛盾的地址通知",
    "Review missing or conflicting facts":"核实缺失或冲突的信息",
    "Review source history":"检查原始历史记录",
    "Re-run triage with corrected facts":"补全或更正事实后重新检查",
    "Keep under monitoring":"继续观察",
    "Check for updated shipment facts":"查看是否有新的订单信息",
    "Re-run triage when facts change":"信息更新后重新检查",
    "Continue routine tracking":"继续常规跟踪",
    "Review if facts change":"信息变化时再核实",
    "No escalation recommended":"不建议升级处理",
    "Prepare the supported scope, review the gaps, then hand off through your operational system. This demo does not send anything.":"先写清楚哪些问题有依据，再检查信息缺口；审核后通过实际业务系统交接。本演示不会发送任何内容。",
    "This is a fixed snapshot. Corrected or new source facts must come from the operational system; re-running here checks the same data.":"这里是固定数据快照。补全或更新的信息应来自实际业务系统；在本页重新运行仍会检查同一份数据。",
    "Draft for human review":"供人工审核的草稿",
    "Prepared from verified ready categories only. Nothing sent or saved.":"仅汇总具备充分依据的可处理问题；没有发送或保存。",
    "THIS SESSION ONLY":"仅在当前页面有效",
    "Confirm the recommendation or record your own review decision.":"确认系统建议，或记录你自己的审核决定。",
    "Approve recommendation":"认可此建议",
    "Change action":"更改人工处理意见",
    "Mark for escalation":"标记待升级处理",
    "Your selected action":"你选择的处理意见",
    "Apply locally":"仅在本页应用",
    "No human decision recorded.":"尚未记录人工决定。",
    "Demo controls only. Nothing is sent to a carrier or saved to a server. The system recommendation stays unchanged. Local review progress resets on reload.":"这些只是演示操作：不会发送给承运商，也不会保存到服务器。系统原建议不变；刷新页面会清空本地审核记录。",
    "Why this is supported":"为什么有依据？",
    "These are the operating instructions behind the checks. SOP means standard operating procedure: the written rules for handling a delivery issue, including what information is needed.":"SOP 指标准操作流程，即处理配送问题的书面规则，以及处理前需要具备哪些信息。以下保留可核验的英文 SOP 原文；临时中文说明不替代正式依据。",
    "Decision details":"判断详情",
    "All three checks and any unresolved facts":"三类检查结果及仍未核实的信息",
    "View rule trace":"查看原始规则执行记录（英文标识）",
    "Shipment facts":"订单事实",
    "View raw case data":"查看原始数据（保留英文）",
    "Re-run triage":"重新检查",
    "This demo rechecks the same fixed snapshot; editing source facts is not connected.":"本演示重新检查同一份固定快照，没有接入修改源数据的功能。",
    "Three checks complete. Review the next action below.":"三类检查已完成，请查看下方建议动作。",
    "Checking shipment facts and supporting policy...":"正在核对订单事实和操作规则……",
    "Carrier":"承运商",
    "Reference time":"快照时间",
    "Delivery promise":"承诺送达时间",
    "Shipment status":"订单状态",
    "Tracking history":"物流历史",
    "Declared complete":"已声明完整",
    "Incomplete":"不完整",
    "Not provided":"未提供",
    "Recorded events":"已记录事件",
    "Source identity":"原文标识与校验值",
    "WHEN THE RULES DO NOT HAVE AN ANSWER":"规则没有答案时怎么办",
    "What if the policy does not cover the question?":"如果操作规则没有覆盖这个问题呢？",
    "For example: “How much money should the customer receive for this delivery problem?”":"例如：“这次配送问题应该赔给客户多少钱？”",
    "Policy support not available":"缺少规则依据",
    "The demo operating rules do not say how much money to pay. This example flags the missing rule for a person to review, rather than inventing an amount.":"演示规则没有规定赔付金额，因此明确提示人工核实，不会编造一个金额。",
    "Available policy evidence":"规则中已有的内容",
    "How to handle delivery problems":"如何处理配送问题",
    "What to check before asking a team to take further action":"交由团队进一步处理前需要核实什么",
    "Missing policy support":"规则没有说明的内容",
    "Reimbursement amount":"赔付金额",
    "About this coverage example":"这个示例的范围",
    "One predefined question for the frozen demo policy. It is not a general-purpose question-answering capability. No refund amount is inferred.":"这是针对固定演示规则的一个预设问题，并非通用问答功能。系统没有推断任何退款金额。",
    "SOP-06 / handoff-boundary: draft only; human review required; do not issue refunds.":"SOP-06 / handoff-boundary：只准备草稿，必须人工审核，不执行退款。",
    "LESS ASSEMBLY. MORE CLARITY.":"少翻资料，更清楚地处理问题",
    "From scattered facts to a reviewable next step.":"把零散事实整理成可审核的下一步。",
    "ONE REVIEW":"一次检查",
    "Check 3 delivery issue types together":"一次检查三类配送问题",
    "Check overdue deliveries, missing tracking updates and delivery attempt or address problems together.":"同时查看逾期、物流更新缺失，以及派送尝试或地址问题。",
    "CONSISTENT NEXT STEPS":"一致的处理标准",
    "Apply the same operating rules every time":"每次都按同一套操作规则判断",
    "See why each shipment needs monitoring, review or escalation.":"知道为什么要继续观察、核实信息，或提交进一步处理。",
    "NO POLICY HUNTING":"不用来回找规则",
    "See the exact rule behind each recommendation":"直接查看每项建议对应的具体规则",
    "Open the exact SOP sections behind every ready recommendation.":"展开即可查看支持处理建议的原始 SOP 段落。",
    "SAFE HANDOFFS":"边界清楚的交接",
    "Escalate only what is supported; keep gaps visible":"只交接有依据的问题，保留未解决的信息缺口",
    "Prepare a local brief without losing unresolved facts. Keep unsupported requests, such as this reimbursement example, with a human.":"整理交接摘要时保留待核实信息。缺乏规则支持的请求（如赔付金额）仍交由人处理。",
    "Why not let the AI decide?":"为什么不让 AI 直接决定？",
    "We tested that approach. The small model did not reliably judge whether policy evidence truly supported an answer, so this demo keeps business decisions rule-based and human-reviewed.":"我们测试过这种做法。这个小模型无法可靠判断规则文本是否真正支持某个答案，所以本演示用确定性规则作业务判断，并由人审核最终行动。",
    "See evaluation":"查看评估结果",
    "LAST MILE / Evidence before action.":"最后一公里配送 / 先有依据，再采取行动。",
    "Synthetic shipments. Fictional demo operating policy. Not carrier or industry standards.":"模拟订单与虚构演示规则，不代表真实承运商或行业标准。",
    "ENGINEERING / EVALUATION":"工程设计 / 评估",
    "Back to the delivery issue queue":"返回配送问题列表",
    "Design decision":"设计决策",
    "Rules decide operational state.":"由确定性规则判断业务状态。",
    "Policy sections provide traceable evidence.":"由具体规则段落提供可追溯的依据。",
    "The LLM was tested as a semantic judge and failed qualification.":"曾测试大语言模型能否判断语义支持关系，但它没有通过资格评估。",
    "Therefore, humans retain final action authority.":"因此，最终是否执行行动仍由人决定。",
    "Structured output does not guarantee correct reasoning.":"输出格式正确，不代表推理正确。",
    "We evaluated the small model before delegating policy decisions to it. It did not meet the pre-registered semantic-support thresholds. This portfolio design keeps business rules deterministic and final operational decisions with a human.":"在让小模型负责规则判断前，我们先进行了评估。它没有达到预先登记的语义支持判断标准，因此保留确定性业务规则，并把最终操作决定交给人。",
    "What this workspace runs":"当前工作台实际运行什么",
    "Structured synthetic shipment facts":"结构化的模拟订单事实",
    "Python deterministic triage engine":"Python 确定性异常分流引擎",
    "Exact SOP section lookup from rule references":"按规则引用精确查找 SOP 段落",
    "Rule-based explanations and human review":"基于规则的解释与人工审核",
    "No LLM or embedding model runs in this workspace.":"本工作台不会运行大语言模型或向量嵌入模型。",
    "What the experiments established":"实验验证了什么",
    "✓ Deterministic execution and policy evidence lookup":"✓ 确定性规则执行与依据查找",
    "✓ Decoder, exact schema validator and adapter qualification":"✓ 解码器、精确结构校验器与适配器通过资格验证",
    "✓ End-to-end constrained model runtime in smoke tests":"✓ 端到端受约束模型运行通过冒烟测试",
    "✗ Small-model semantic support judgment":"✗ 小模型的语义支持判断未通过",
    "✗ Reliable semantic evidence grounding":"✗ 未达到可靠的语义证据关联能力",
    "Runtime qualification is distinct from consistent structural success: the subsequent 12-case semantic suite passed structure in 9/12 cases.":"能成功运行不代表每次输出都合格：后续 12 个语义测试案例中，9 个通过结构检查。",
    "Frozen experiment: Qwen2.5-1.5B semantic qualification":"已冻结实验：Qwen2.5-1.5B 语义资格评估",
    "Candidate rejected for DEVELOPMENT evaluation.":"该候选方案未获准进入 DEVELOPMENT 评估。",
    "The result applies to this frozen candidate/model/configuration, not to every possible architecture.":"此结果只适用于这套冻结的候选方案、模型和配置，不代表所有架构都会失败。",
    "Fresh synthetic qualification · 12 cases, not a production accuracy estimate":"新编合成资格测试：12 个案例，不是生产环境准确率估计",
    "Measure":"指标",
    "Observed":"结果",
    "Final decision":"最终决策正确数",
    "Supported / insufficient / unresolved decision":"支持充分 / 支持不足 / 上下文未解决：各类正确数",
    "Material-ask recall / precision":"实质问题识别：召回率 / 精确率",
    "Supported-evidence coverage":"支持证据覆盖率",
    "Owner-reviewed result: semantic qualification failed. No model tuning or new evaluation is part of this portfolio sprint.":"负责人审核后的结论：语义资格评估失败。本作品集改版没有调参，也没有重新评估模型。",
    "Architecture and implementation details":"架构与实现细节",
    "FastAPI serves plain HTML, CSS and JavaScript. Analysis uses the existing":"FastAPI 提供原生 HTML、CSS 和 JavaScript 页面。分析使用现有的",
    ",":"、",
    "and":"和",
    "interfaces. Policy hashes and stable section identities are checked before recommendations are returned. Retrieval errors stop analysis instead of substituting policy text.":"接口。返回建议前会校验规则文件哈希和稳定段落标识；查找失败时停止分析，不会替换或编造规则文本。",
    "The separate research stack includes BGE embeddings, lexical retrieval, RRF, constrained decoding and JSON Schema Draft 2020-12 validation. Those experiments remain frozen; they are not invoked by this demo.":"独立研究部分包括 BGE 向量嵌入、词法检索、RRF 排名融合、受约束解码，以及 JSON Schema Draft 2020-12 校验。这些实验保持冻结，本演示不运行它们。",
    "Structured facts → deterministic rules → exact SOP retrieval → evidence-aware presentation → human review.":"结构化事实 → 确定性规则 → 精确 SOP 查找 → 展示依据 → 人工审核。",
    "Portfolio prototype. Public synthetic data only.":"作品集原型，仅使用公开模拟数据。",
    "DRAFT ONLY - HUMAN REVIEW REQUIRED":"仅为草稿，必须人工审核",
    "Supported escalation scope:":"有依据、可以提交进一步处理的范围：",
    "Unresolved facts (not part of the ready basis):":"仍待核实的信息（不属于已获支持的处理依据）：",
    "None identified in this snapshot.":"当前快照未发现信息缺口。",
    "Nothing sent, saved to a server, or changed in an operational system.":"没有发送、保存到服务器或改变实际业务系统中的任何内容。",
    "Late delivery":"逾期配送",
    "Stale tracking":"长时间无物流更新",
    "Failed attempt / address":"派送尝试或地址问题",
    "Marked locally for human escalation handoff. Only independently supported categories may be included. Nothing sent or saved to a server.":"已在本页标记，等待人工升级交接。只包含有独立依据的问题，没有发送或保存到服务器。",
    "Not ready for policy-supported escalation. Review the gaps or monitoring conditions first. Nothing sent.":"尚不具备有规则依据的升级条件，请先核实缺口或继续观察。没有发送任何内容。",
    "Loading fixed shipment snapshot...":"正在加载固定订单快照……",
    "Loading queue...":"正在加载列表……",
    "Analysis unavailable. No recommendation is shown. Select the shipment again to retry.":"分析暂不可用，不显示建议。可重新选择订单再试。",
    "Unable to verify the selected shipment.":"无法核验当前订单。",
    "The verified queue is unavailable. Reload to try again; no cached recommendations are shown.":"无法获取已核验的列表，请刷新重试；不会显示旧的缓存建议。",
    "Queue unavailable":"列表不可用",
    "Snapshot unavailable":"快照不可用"
  };
  function translate(text) {
    const value = text.trim();
    if (copy[value]) return text.replace(value, copy[value]);
    let m;
    if ((m = value.match(/^(\d+) of (\d+) shipments\. Select a shipment to review\.$/))) return `显示 ${m[1]} / ${m[2]} 个订单，点击可查看详情。`;
    if ((m = value.match(/^\+ (\d+) more · View details$/))) return `另有 ${m[1]} 项检查 · 查看详情`;
    if ((m = value.match(/^(\d+) policy sections explain this decision$/))) return `${m[1]} 个规则段落解释这一判断`;
    if ((m = value.match(/^(\d+(?:\.\d+)?)h$/))) return `${m[1]} 小时`;
    if ((m = value.match(/^(\d+) shipments have unconfirmed issue start times$/))) return `${m[1]} 个订单至少有一项问题起始时间无法确认`;
    if ((m = value.match(/^(\d+) of these also appear in the known-age ranking\. Different checks can have different certainty\.$/))) return `其中 ${m[1]} 个订单也出现在已知时长排名中。同一订单的不同检查可以有不同的确定程度。`;
    if (value.startsWith("Review gap: ")) return "当前缺口筛选：" + translate(value.slice(12));
    if (value.startsWith("Queue view: ")) return "当前列表：" + translate(value.slice(12));
    if (value.startsWith("Selected gap affects: ")) return " 选中缺口影响：" + translate(value.slice(22));
    if ((m = value.match(/^Selected gap: (.*)\. Highlighted checks need review; independent supported actions remain valid\.$/))) return "当前缺口：" + translate(m[1]) + "。高亮检查需要核实，其他独立且有依据的行动仍然有效。";
    if (value.startsWith("PRIORITY / ")) return "优先级 / " + translate(value.slice(11));
    if (value.startsWith("Snapshot / ")) return "快照时间 / " + value.slice(11);
    if (value.startsWith("Review needed: ")) return "需要核实：" + translate(value.slice(15));
    if (value.startsWith("Referenced by the evaluated rules for ")) return "以下是本项检查所引用的规则段落（保留英文原文供核验）。";
    if ((m = value.match(/^Approved locally: (.*)\. Nothing sent or saved to a server\.$/))) return `已在本页认可：${translate(m[1])}。没有发送或保存到服务器。`;
    if ((m = value.match(/^Human override recorded locally: (.*)\. System recommendation unchanged; no operational action taken\.$/))) return `已在本页记录人工意见：${translate(m[1])}。系统原建议不变，没有实际执行。`;
    for (const arrow of [" ↑", " →"]) if (value.endsWith(arrow) && copy[value.slice(0,-2)]) return copy[value.slice(0,-2)] + arrow;
    return text;
  }
  const excluded = "script,style,pre,.policy-text,.evidence-id";
  function translateTree(root) {
    if (root.nodeType === Node.TEXT_NODE) {
      if (!root.parentElement?.closest(excluded)) {
        const result = translate(root.nodeValue);
        if (result !== root.nodeValue) root.nodeValue = result;
      }
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE || root.matches(excluded)) return;
    for (const child of [...root.childNodes]) translateTree(child);
    for (const key of ["placeholder", "aria-label"]) {
      const value = root.getAttribute(key);
      if (value && copy[value]) root.setAttribute(key, copy[value]);
    }
  }
  document.title = translate(document.title);
  const note = document.createElement("aside");
  note.style.cssText = "padding:12px 6%;background:#fff3d6;color:#5a451b;font-size:13px;line-height:1.7";
  note.append("临时中文阅读版 · 仅帮助理解，英文作品集不变。SOP 原文、原始数据及技术标识保留英文。 ");
  const english = document.createElement("a");
  english.href = location.pathname.endsWith("/engineering") ? "/engineering" : "/";
  english.textContent = "返回英文版 ↗";
  note.append(english); document.body.prepend(note);
  translateTree(document.body);
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === "characterData") translateTree(record.target);
      else for (const node of record.addedNodes) translateTree(node);
    }
  });
  observer.observe(document.body, {childList:true, subtree:true, characterData:true});
  document.addEventListener("click", event => {
    if (!event.target.closest("#prepare-brief")) return;
    const box = document.getElementById("handoff-brief");
    box.value = box.value.split("\n").map(line => {
      if (line.startsWith("Snapshot: ")) return "快照时间：" + line.slice(10);
      if (line.startsWith("Policy: ")) return "规则引用：" + line.slice(8);
      const separator = line.indexOf(": ");
      return separator > 0 ? translate(line.slice(0,separator)) + "：" + translate(line.slice(separator+2)) : translate(line);
    }).join("\n");
  });
})();
