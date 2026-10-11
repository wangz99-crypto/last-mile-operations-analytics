# Phase 2H-B3.2-A2.1-D: schema enforcement diagnostic

Review status: CANDIDATE_AWAITING_OWNER_REVIEW.
Base: e085c96e5c80ce61bb833be78f36c62ee8ee5790 /
answerability-semantic-v2-decoder-v0.2-qualification-failed-nonconforming.
Initial worktree clean; historical R2 tag resolves to
4fea18a9c70b1b9536dd92d7f1a118ac3e02a32f.

This phase observes and localizes the missing required fields in saved Attempt-2
outputs. It does not repair, retune, repeat generation or qualify semantic capability.
Attempt 2 remains OWNER_REVIEWED / DECODER_QUALIFICATION_FAILED, with
NONCONFORMING_CONFIG and NOT_CONCLUSIVE clean decoder-capability judgment.

Enforce the exact Attempt-2 adapter, runner/test and V2 schema hashes. Use installed
XGrammar 0.2.8 and the unchanged R2-plus-XGrammar environment. No package changes.
Inspect actual compile call arguments and installed method definitions. Reproduce
the same original schema text and effective options; never vary any_order or rewrite
the schema. Load only frozen local tokenizer/config files; never load Qwen weights
or construct a model. Record compiler options, grammar and tokenizer identity.

Before native matching, freeze eight fixture strings and schema-based expectations:
M1 complete valid object, M2/M3/M4 individually missing each requested field,
M5 missing all three, M6/M7/M8 byte-identical saved S1/S2/S3 outputs. No extra fixture.
Use the supported accept_token path: tokenize M1-M5 without special tokens; replay
the saved generated token IDs for M6-M8. Require decoded body text to equal the
frozen string. Construct a fresh default GrammarMatcher per fixture. Feed body tokens
once, stopping on first rejection, then attempt one EOS token only if all body tokens
were accepted. Acceptance requires full-body completion plus EOS acceptance and
termination; merely accepting a prefix is insufficient. Record rejection position.
No real matcher retry or determinism repeat. Fake-matcher unit tests are separate.

Triangulate saved outputs with a standard strict JSON parser, the independent
validator implementing all keywords of this hash-locked V2 schema, and XGrammar.
The validator's limited scope is explicit; it is not a general JSON Schema library.
Capture native stderr warnings without interpreting successful compilation as
proof of correct enforcement.

Inspect installed HF integration and Transformers source statically for call-path,
processor lifecycle, container merging, termination, and repetition-penalty ordering.
Do not call model.generate, forward, or processor inference to inspect them. Distinguish
source/saved provenance from unrecorded per-token runtime state and object IDs.
Only concrete evidence supports ESTABLISHED defects. Do not infer that the penalty
caused missing fields. No fix, options sweep, reset, new smoke call or Attempt 3.

Choose exactly one primary localization: grammar compilation/required-field issue,
HF application-path issue, lifecycle issue, multiple established integration issues,
or inconclusive. Scope conclusions to the frozen schema/options/library combination.

Counters: model initialization, generate, forward, semantic outputs, DEVELOPMENT,
retrieval, package installation/change, model downloads all zero. Both HELD_OUT scopes
remain untouched. Fresh semantic suite remains NOT YET AUTHORED. Offline flags and
Python audit/profile guards prevent network/model/benchmark operations while allowing
normal local platform probes. Observe and preserve events; no blanket subprocess block.

Preserve every historical artifact and source byte. New writes only in this diagnostic
directory, diagnostic helper/tests, and exact artifact -text rules. No commit or tag.
