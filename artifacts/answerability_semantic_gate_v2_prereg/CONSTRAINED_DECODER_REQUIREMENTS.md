# Constrained decoder implementation qualification requirements

Status: CONSTRAINED_DECODER_IMPLEMENTATION_REQUIRED.
Implementation, package/version and executable adapter: NOT SELECTED.
No decoder installation, runtime artifact, real model call or network discovery in A2.

Exactly one implementation must later be selected and frozen for local Windows,
CPU, Transformers and Qwen/Qwen2.5-1.5B-Instruct immutable revision
989aa7980e4cf806f80c7fef2b1adb7bc71aa306. Preserve FP32, original weights and the
frozen tokenizer/chat template. Verify runtime/dependency compatibility; do not
silently upgrade or substitute the frozen environment. Any needed runtime amendment
requires its own authorization and provenance, not an implicit A2 change.

Demonstrate greedy token-level constrained generation, dynamic JSON-schema support,
CPU/tokenizer compatibility, deterministic request construction, no network inference,
no hidden retries, no weight modification and no state leakage between requests.
Freeze exact package/source revision, dependency changes (if separately authorized),
configuration, supported schema keywords and request/schema hashes before model calls.

The constraint layer must generate the V2 structured object directly: no fences,
leading/trailing prose, unknown keys, invalid enums, wrong top-level structure or
primitive types. Document and test the actual decoder's handling of object properties,
additionalProperties=false, required, array bounds/items, integer limits, enum/const,
uniqueItems, pattern/minLength and conditional/combinator constraints in the V2 schema.
Do not claim enforcement merely because a JSON Schema declaration exists. Unsupported
features must be explicitly accounted for in implementation qualification, never
silently discarded. Parser membership/ordering/semantic checks remain authoritative.
Dynamic rank bounds are preferred; the authorized static 1-10 fallback still requires
strict adapter rejection above the actual evidence count. Empty evidence permits no
rank references. Integer lexical form and ascending order require parser checks as
documented in RANK_MAPPING_CONTRACT.md.

PROMPT_ONLY_STRICT_JSON is insufficient. No post-generation repair, fence stripping,
regex cleanup, LLM correction, fuzzy mapping or schema-fixing/quality retry is allowed.
Any rejected constrained output remains a candidate error. API/worker/timeout failures
must remain explicit, preserving attempt provenance; no hidden infrastructure retries.
Any future infrastructure retry requires separate advance authorization.

Prove these properties with decoder-specific tests before claiming compatibility.
A2's fake-output/schema declaration tests do not establish decoder/model capability.
No selection based on DEVELOPMENT performance; no DEVELOPMENT or HELD_OUT access.
