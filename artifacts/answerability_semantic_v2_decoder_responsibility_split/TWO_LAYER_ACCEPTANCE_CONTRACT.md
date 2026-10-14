# Two-layer acceptance and failure boundaries

Raw structural validity = standard JSON parse PASS AND exact authoritative schema PASS.
COMBINED_STRUCTURAL_ACCEPT checkpoint = decoder constraints respected AND standard JSON parse PASS AND exact frozen schema PASS. This is the requested three-factor structural predicate; decoder acceptance alone is never sufficient.

After that checkpoint, the adapter must also pass before a final GateOutput or semantic scoring is eligible. If it rejects, final disposition becomes STRUCTURAL_INVALID with ADAPTER_STRUCTURAL_REJECT. Thus the final acceptance terminal in ACCEPTANCE_STATE_GRAPH.json includes adapter success; it does not redefine or weaken the three-factor raw structural predicate. Any earlier failure prevents adapter execution. Every nonaccepted disposition has semantic evaluation NOT_RUN and zero semantic accuracy credit.

Preserve raw bytes, full generation config, decoder result, JSON parse result, exact validator result, adapter result (including NOT_RUN), final structural disposition and any exception. Do not overwrite outputs. Decoder mask/acceptance verification errors are separate from intentional rejection. All indeterminate/error/NOT_RUN states fail closed without being counted as a valid REJECT.

NO POST-GENERATION REPAIR. No adding missing fields, dropping unknown keys, deduplicating/sorting arrays, rewriting enums/types/evidence ranks/conditionals, rewriting malformed JSON or retrying structural failure. generation retries=0; repair retries=0; quality retries=0. No fallback schema or result-dependent grammar edit. A changed policy requires a new preregistered version.

M1-M8 remain unchanged. M1 decoder/exact/combined ACCEPT. M2-M5 decoder/exact/combined REJECT for missing required fields. Inspection of the exact saved M6-M8 raw fixture objects found all lack decision, policy_context_status and reason_code; these are mandatory at both layers, hence all three layers must REJECT. M1_M8_TREATMENT.json binds fixture hashes and expected outcomes without executing any validator/matcher.

Future delegated probe designs (not authored raw cases, no execution):

- uniqueItems: retain otherwise-valid supported branch shape but repeat a rank. Decoder contract MAY ACCEPT; exact validator REJECT; combined REJECT; adapter NOT_RUN.
- contains: use the insufficient-support decision/context branch with no unsupported ask while preserving unconditional shapes/types/enums. Exact branch requirement must reject; decoder MAY ACCEPT. Account for oneOf coupling rather than claiming keyword-isolated causality.
- then: a SUPPORTED ask with an empty rank array, otherwise valid branch structure. Decoder MAY ACCEPT; exact conditional minItems rejects.
- else: an UNSUPPORTED or CONTEXT_UNRESOLVED ask with a nonempty rank array and otherwise consistent branch structure. Decoder MAY ACCEPT; exact conditional maxItems rejects.
- Positive counterparts: unique ranks, required witness for contains and correct empty/nonempty conditional arrays, with valid whole-schema branches. Decoder/exact/combined ACCEPT, subject to unchanged adapter success for final GateOutput.

Freeze actual structural fixtures later before qualification; no semantic questions or V1 paraphrases are authored here. P6 must test all assigned constraints, not just these examples. P7 must include decoder rejection, decoder+validator acceptance, decoder acceptance+validator rejection, and adapter rejection after upstream acceptance.
