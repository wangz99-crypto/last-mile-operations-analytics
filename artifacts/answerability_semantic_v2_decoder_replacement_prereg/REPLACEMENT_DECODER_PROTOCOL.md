# Phase 2H-B3.2-A2.1-E replacement decoder preregistration

Review status: CANDIDATE_AWAITING_OWNER_REVIEW. Recorded 2026-10-12.

Exactly one replacement is selected: distribution `lm-format-enforcer==0.11.3`,
Python package `lmformatenforcer`. Status: REPLACEMENT_DECODER_SELECTED_NOT_QUALIFIED.
Capability: NOT_ASSESSED. Installation: INSTALLATION_NOT_AUTHORIZED.

The base commit is `6e05245a6f7971ab05101bc2b24de42180a614cd`, resolved from
`answerability-semantic-v2-xgrammar-v0.2-required-field-failure`. The working tree
was clean before metadata capture and artifact creation.

## Historical boundary

The owner-reviewed XGrammar 0.2.8 diagnostic remains
OWNER_REVIEWED / DIAGNOSTIC_ESTABLISHED, with outcome
GRAMMAR_COMPILATION_OR_REQUIRED_FIELD_ENFORCEMENT_ISSUE and evidence ESTABLISHED.
Suitability for the exact frozen V2 schema/compiler path remains REJECTED.
No historical result, raw string, schema, source, or journal is changed. This
selection does not broaden the historical finding to other versions or schemas.

## Frozen scientific boundary

Use the original `RAW_ASSESSMENT_SCHEMA_V2.json` without reduction, replacement,
rewriting, or removal of composition rules. Its SHA-256 is
`6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.
The deterministic V2 adapter retains actual evidence-count rank bounds, exact
rank-to-canonical-identity mapping, cross-field status/reference consistency,
and final GateOutput consistency. No semantic heuristic is moved into a decoder.
The original prompt, schema, rank mapping, model weights and runtime stay frozen.

Model: Qwen/Qwen2.5-1.5B-Instruct.
Revision: `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
Runtime: Windows / CPU / FP32 / Transformers. No tokenizer or model is loaded now.

## Ordered future authorization boundaries

1. Owner review of this preregistration; no execution is authorized by selection.
2. Separately authorized dependency enablement must pin and verify missing
   dependency versions and distribution hashes, preserve the frozen environment,
   and record package inventory changes. No pip resolution occurs in this phase.
3. Separately authorized pure parser/token-enforcer qualification must execute
   the complete STRUCTURAL_CONFORMANCE_GATE.md against the exact original schema.
   Passing the core missing-field cases alone does not establish full compatibility.
4. Model generation requires separate authorization after structural findings
   have been reviewed. A structural pass does not automatically authorize inference.

Future HF integration is the package's
`lmformatenforcer.integrations.transformers.build_transformers_prefix_allowed_tokens_fn`
with the exact frozen tokenizer and `JsonSchemaParser` over the frozen schema.
Attach the returned callback as `prefix_allowed_tokens_fn`. This describes the
intended path; no callback, parser, tokenizer, or decoder is constructed now.
Before later execution, explicitly record parser configuration, environment
overrides, tokenizer identity, callback lifecycle, EOS behavior, and full effective
generation configuration. Frozen repetition_penalty must remain 1.0; do not inherit
the historical model-local 1.1 override silently. No defaults may weaken schema rules.

No post-generation repair, regex cleanup, JSON fixing, quality retry, malformed
output retry, model weight modification, or alternate decoder is authorized.
There is no runtime comparison, bake-off, benchmark access, retrieval, or semantic
evaluation in E. The fresh V2 semantic qualification suite is NOT YET AUTHORED;
V1 Q1-Q12 are not reused. The conformance document defines structural probes only.

## Current phase accounting

Model initialization = 0; generate = 0; forward = 0; decoder execution = 0;
parser/token-enforcer conformance executions = 0; package installation = 0;
DEVELOPMENT access/calls = 0; retrieval = 0; Phase 2H HELD_OUT access = false;
Phase 2G private HELDOUT access = false. Public PyPI release metadata was read;
no wheel, source distribution, model, or weights were downloaded. Installed
distribution metadata was read without importing target decoder/model packages.
No commit or tag is authorized.
