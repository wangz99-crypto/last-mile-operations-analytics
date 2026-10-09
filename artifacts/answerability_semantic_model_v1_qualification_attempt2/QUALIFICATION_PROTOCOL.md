# Attempt 2 synthetic semantic qualification protocol

Status: CANDIDATE_AWAITING_OWNER_REVIEW. One offline CPU/FP32 Qwen snapshot,
one frozen canonical prompt/parser, no DEVELOPMENT, no retrieval, no private data.
Twelve synthetic workshop cases Q1-Q12, followed by Q2/Q7/Q11 once each.
Expectations and synthetic categories remain evaluator-only. The worker receives
only contract-compatible GateInput. No case IDs, categories or labels enter messages.

The exact suite/config and runner/test source hashes are bound before model load.
Structured validity, supplied-reference validity and internal consistency each
require 12/12; binary and reason correctness each require >=11/12; critical binary
Q3/Q4/Q7/Q8/Q11/Q12 requires 6/6. Invalid parser output never becomes ABSTAIN.
Diagnostic shape/reference/consistency checks cannot emit a GateOutput; the frozen
parser alone does so. Binary/reason correctness requires a valid frozen parse.
All primary cases retain denominator 12; incomplete runs have no capability verdict.
Duplicates are diagnostic only, never extra accuracy cases or a new eligibility rule.

A persistent isolated spawned worker loads the model once. The parent imposes a
600-second deadline per preparation/generation operation, terminates a timed-out
worker, preserves completed raw outputs, and stops with QUALIFICATION_INCOMPLETE.
No worker replacement, infrastructure retry, quality retry or second pass is allowed.
Per-request exact chat-template tokenization checks input + 4096 against 32768;
the frozen helper conservatively requires positive remaining margin. No truncation.
Startup also has a 600-second infrastructure deadline, separately identified.

Generation is greedy, one beam, max_new_tokens=4096, seed 0 in the frozen runtime.
The full proposed GenerationConfig is used without scientific changes. Inert library
temperature/top_p values are 1.0; their scientific treatment is not applicable to
greedy decoding. PROMPT_ONLY_STRICT_JSON is strict parser post-validation, not native
constrained decoding. The original provider-oriented configuration is explicitly
mapped without changing its frozen schema. No generation/output repair is allowed.

Raw text is tokenizer.decode(new tokens, skip_special_tokens=True,
clean_up_tokenization_spaces=False), with all generated token IDs separately retained.
Raw UTF-8 byte length/hash, token counts, request/config hashes, duration, stop status,
strict parser result and GateOutput are recorded once per call and fsynced immediately.
EOS and output-limit stops are distinguished. A transport/timeout failure has null
raw text and unknown unavailable token counts; no fabricated output is substituted.

Outbound socket operations and benchmark/private file reads are blocked and recorded.
Socket construction, hostname reading and loopback-only bind probes are allowed.
No network fallback/download/package installation is authorized. Historic files are
hash-checked only, outside model execution; no benchmark question is parsed.
Artifacts refuse overwrite; the journal/raw custody files append only. Post-run
reproduction uses saved raw bytes and the frozen parser, never another model call.
Stop after artifacts, hash validation and non-model tests; do not commit or tag.
