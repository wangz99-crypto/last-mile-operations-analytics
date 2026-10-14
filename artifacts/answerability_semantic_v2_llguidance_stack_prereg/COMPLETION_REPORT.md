# Phase 2H-B3.2-A2.1-I completion report

**Outcome: LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED.** Owner status: CANDIDATE_AWAITING_OWNER_REVIEW. No decoder capability result was produced. Do not proceed to installation/qualification.

1. Base commit and tag: `baae21265e1ec192f0ddf047f7dd8b3377647c8b`, `answerability-semantic-v2-lmfe-v0.4-schema-incompatibility`; matched, clean precondition.
2. LMFE GD: OWNER_REVIEWED / LMFE_SCHEMA_SHAPE_INCOMPATIBILITY_ESTABLISHED, confidence ESTABLISHED, helper NOT_CAUSAL, exact V2 suitability REJECTED. Owner record SHA `2cefba8da7bb1cfc29d84b181d16bc6ccd068972bd0c168fc01712cbb898adb4`. XGrammar 0.2.8 exact-schema rejection also unchanged.
3. Frozen V2 schema SHA: `6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`. Candidate remains PRE_REGISTERED_NOT_EVALUATED; bytes unchanged.
4. Sole grammar engine: llguidance, SELECTED_NOT_INSTALLED / NOT_QUALIFIED / CAPABILITY_NOT_ASSESSED.
5. Exact version: 1.9.1.
6. Requires-Python: >=3.10.
7. Windows wheel: `llguidance-1.9.1-cp39-abi3-win_amd64.whl` (cp39-abi3-win_amd64).
8. Wheel SHA: `8aaa55958adb4871016700e9140543ccbd9d6b5136d0a1756a114af706cc50c1`; official metadata matches.
9. llguidance declares no mandatory dependency or extra in this release's PyPI metadata. No resolver run.
10. Windows AMD64 Python 3.12.10 matches both selected wheels' tags and Requires-Python. This does not establish semantic compatibility; release-source inspection blocks exact-schema enforcement. Frozen 36-package inventory unchanged.
11. Future integration layer: Outlines, llguidance backend only; not installed/qualified.
12. Exact Outlines version: 1.3.3.
13. Requires-Python: <3.14,>=3.10.
14. Wheel `outlines-1.3.3-py3-none-any.whl`; SHA `0e185dd5a0cfeb62e0268018972d3c22bb9b7d43db3dc1f39f3b754175a82c54`; metadata matches.
15. Outlines base dependencies: jinja2, cloudpickle, diskcache, pydantic>=2.0, jsonschema, pillow, typing_extensions, outlines_core==0.2.14, genson.
16. llguidance extra: llguidance (metadata unpinned; owner selection 1.9.1 retained).
17. transformers extra: accelerate, datasets, transformers, setuptools, sentencepiece.
18. All 71 declared Outlines edges and optional extras are classified in DECLARED_DEPENDENCY_GRAPH.json; table below lists base/intended future extras. Other extras remain OPTIONAL_NOT_REQUIRED_YET. No active declared version conflict. The unused test extra's numpy range would conflict with frozen numpy 2.5.3; test extras are not selected.
19. Missing: cloudpickle, diskcache, jsonschema, pillow, outlines-core, genson, datasets, sentencepiece, llguidance; Outlines itself absent. Only outlines_core==0.2.14 is directly pinned by dependency metadata. Other unpinned/ranged missing dependencies stay VERSION_SELECTION_PENDING_OWNER_AUTHORIZATION; no transitive resolution or missing-version choice.
20. oneOf: partial/conditional native support, not qualified. coerce_one_of=false. No assumption that all oneOf forms work or all fail.
21. allOf: partial/conditional native intersection support, not qualified. No flattening.
22. Exact risk pointers: /oneOf/0/properties/material_asks; /oneOf/1/properties/material_asks; /properties/material_asks/items; /properties/material_asks/items/allOf/0. Original schema untouched. Additional critical static blockers: uniqueItems, contains, if, then, else.
23. Future K1: exact bytes via LLMatcher.grammar_from_json_schema; construction success mandatory, not sufficient to establish compiled semantics.
24. Future K2: validate_grammar_with_warnings/equivalent; errors stop, warnings preserved, material warnings require owner review. K3 then qualifies unchanged known-risk subtrees before matcher/tokenizer activity.
25. Future K4: original M1 ACCEPT; M2-M8 REJECT. JSON/schema/matcher triangulation; errors distinct from REJECT; exact acceptance/EOS/stopped semantics must be frozen before execution.
26. Future K5: every present material schema constraint classified CRITICAL and must qualify; absent features inventoried. No remote reference fetch.
27. coerce_one_of=false, lenient=false; no weakening or alternate schema.
28. Tokenizer only after K1/K2/K3 pass, frozen local Qwen snapshot offline; model init/generate/forward stay zero in K stages. No tokenizer here.
29. Outlines/HF only after K1-K5; exact release-specific API paths and dependency closure must be frozen before installation/execution. Current static blocker prevents K0; no later step authorized.
30. Future model smoke conditional on all pure gates and L: Qwen/Qwen2.5-1.5B-Instruct revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306; CPU FP32; torch 2.14.0+cpu; transformers 4.57.6; repetition_penalty=1.0; exactly 3 generate calls; zero quality/schema-repair retries.
31. Package installs/removals/mutations = 0.
32. llguidance/Outlines imports = 0.
33. Grammar compilations/validations, matcher constructions/executions = 0.
34. Tokenizer loads = 0.
35. Model initialization = 0.
36. Generate/forward/semantic outputs = 0.
37. DEVELOPMENT = 0; no question bodies inspected.
38. Retrieval = 0.
39. Phase 2H HELD_OUT access = false; Phase 2G private HELDOUT access = false.
40. Fresh semantic qualification suite = NOT YET AUTHORED; no V1 Q1-Q12 reuse/paraphrase.
41. Offline preregistration checks = 16/16 PASS, zero failures/errors. This is not structural conformance. Initial test-wrapper bytecode-cache access stop and unchanged-source recovery are recorded transparently in OFFLINE_TEST_RESULTS.json; no decoder execution.
42. Network/source identities: RELEASE_METADATA_RECEIPT.json, UPSTREAM_SOURCE_RECEIPT.json and NETWORK_SCOPE_SUMMARY.json. 19 successful direct official metadata/source fetches; initial sandbox DNS failure and web-tool cache limitations recorded. No wheel/model/source-tree download, resolver, package execution or alternate-decoder search.
43. Historical integrity: 249 named historical file hashes preserved; previous GD receipt 82/82 match. Other frozen groups (V1/runtime/B3/B2/benchmark/retriever/corpus/engine) preserved by Git identity, without opening DEVELOPMENT/private contents. Environment metadata/RECORD inventory SHA remains `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`.
44. All final artifact hashes: FINAL_SHA256.json, with its own hash supplied separately in completion response (no circular self-hash).
45. No new runtime helper. Offline test `gateway/domain/tests/test_llguidance_stack_prereg.py` SHA `d30df23eeb9a7d98b451fad14e2337125609c1279135efc32ebabeb8efc684f4`; unchanged historical helper/test hashes are in HISTORICAL_INTEGRITY_RECEIPT.json.
46. Final `git status --short`: captured verbatim in GIT_REVIEW.json after exact-path staging.
47. Complete changed-file list and `git diff --cached --name-only`: GIT_REVIEW.json. Only this phase's preregistration artifacts, one offline test and exact .gitattributes entries; no commit/tag.

| Declared dependency | Group | Installed version | Classification |
| --- | --- | --- | --- |
| jinja2 | base | 3.1.6 | ALREADY_SATISFIED |
| cloudpickle | base | absent | MISSING |
| diskcache | base | absent | MISSING |
| pydantic>=2.0 | base | 2.13.5 | ALREADY_SATISFIED |
| jsonschema | base | absent | MISSING |
| pillow | base | absent | MISSING |
| typing_extensions | base | 4.16.0 | ALREADY_SATISFIED |
| outlines_core==0.2.14 | base | absent | MISSING |
| genson | base | absent | MISSING |
| accelerate | transformers | 1.15.0 | ALREADY_SATISFIED |
| datasets | transformers | absent | MISSING |
| transformers | transformers | 4.57.6 | ALREADY_SATISFIED |
| setuptools | transformers | 78.1.0 | ALREADY_SATISFIED |
| sentencepiece | transformers | absent | MISSING |
| llguidance | llguidance | absent | MISSING |

Official sources: [llguidance release](https://pypi.org/pypi/llguidance/1.9.1/json), [Outlines release](https://pypi.org/pypi/outlines/1.3.3/json), [versioned JSON schema compiler](https://github.com/guidance-ai/llguidance/blob/v1.9.1/parser/src/json/schema.rs), [keyword dispatch](https://github.com/guidance-ai/llguidance/blob/v1.9.1/parser/src/json/shared_context.rs), [recognized dialect keywords](https://github.com/guidance-ai/llguidance/blob/v1.9.1/parser/src/json/context_simple/draft.rs).

Static evidence boundary: source inspection supports a preregistration incompatibility finding; no installed binary was tested. Exact-version source hashes are receipted. No claim of measured LLGuidance structural failure or general decoder incapability is made.

Stop for owner review. The next procedural step is owner disposition of this static contradiction, not K0 enablement. No schema repair, alternate stack selection or new experiment is authorized.
