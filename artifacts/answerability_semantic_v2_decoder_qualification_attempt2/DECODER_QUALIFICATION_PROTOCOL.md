# XGrammar constrained decoder qualification, Attempt 2

Status: CANDIDATE_AWAITING_OWNER_REVIEW.
Base: 4fea18a9c70b1b9536dd92d7f1a118ac3e02a32f,
answerability-semantic-v2-deps-v0.2-imports-validated. Initial working tree clean.

Only XGrammar 0.2.8, cp312 Windows AMD64 wheel SHA-256
dbcf6718e049cbe429742cdb05f85c48135c2e389d45daeafb884af6994bb4a7
is authorized. Reuse the verified historical wheel bytes, copy outside the
repository, install with --no-deps --no-index --no-compile. No other package may
change. Compare all existing package versions, METADATA and RECORD hashes against
the approved R2 inventory before/after installation. Run pip check both times.

Qualification is sequential: fresh-process import/API verification, frozen local
Qwen tokenizer integration, exact V2 JSON Schema compilation, then construction
of the native XGrammar HF LogitsProcessor. Pass exact original schema text; no
keyword removal, rewriting, schema simplification, custom fallback or repair.
The schema SHA is 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e.

Local model identity: Qwen/Qwen2.5-1.5B-Instruct revision
989aa7980e4cf806f80c7fef2b1adb7bc71aa306, Windows CPU FP32, Transformers 4.57.6.
HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1. Preserve the frozen chat template.
Before these prerequisites pass, model initialization and generation are forbidden.
Socket and subprocess operations are observed; local platform probes are allowed.
Network DNS/connect operations are rejected during the functional probe. The
probe observes Python audit events, not operating-system-wide packet traffic.

Only after all prerequisite stages pass, author/freeze S1-S3 structural-only smoke
cases and their config; run deterministic tests; initialize the model once. The
prospective config is greedy decoding, CPU FP32, num_beams=1, max_new_tokens=512,
seed=0, per-call timeout=600 seconds, quality and infrastructure retries=0.
Exactly three calls maximum; no semantic correctness labels or scores. A is JSON
validity, B is exact frozen schema validity, C is separate adapter diagnostics.
All three A+B passes are necessary for DECODER_QUALIFIED.

Installed implementation import/API, tokenizer, schema or HF failures stop the
attempt as DECODER_QUALIFICATION_FAILED. Pre-functional wheel/environment custody
blockers are DECODER_QUALIFICATION_BLOCKED. Do not retry, tune, patch dependencies,
switch decoders or pretend later stages ran. Preserve raw process output/errors.

No fresh V2 semantic suite is authored. No DEVELOPMENT, HELD_OUT, historical private
question content or retrieval is accessed. No benchmark-specific authoring.
Historical sources/artifacts remain unchanged. No commit or tag is authorized.
