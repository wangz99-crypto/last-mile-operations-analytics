# XGrammar schema-enforcement diagnostic - final owner review

Review status: **OWNER_REVIEWED / DIAGNOSTIC_ESTABLISHED**.
Owner: **Zhe Wang (Victor)**.
Owner approval date: **2026-10-11**.
Scientific owner review: **PASS**.

Approved primary outcome:
**GRAMMAR_COMPILATION_OR_REQUIRED_FIELD_ENFORCEMENT_ISSUE**.
Evidence confidence: **ESTABLISHED**.
Specific classification: **GRAMMAR_REQUIRED_FIELD_ENFORCEMENT_FAILURE**.

XGrammar 0.2.8 suitability for this exact frozen V2 schema: **REJECTED**.
Scope: **this exact implementation/version/schema/compiler path only**.
This is not a claim that XGrammar generally cannot enforce JSON Schema, nor that all
XGrammar versions are incompatible. No replacement decoder has been selected.

Base: `e085c96e5c80ce61bb833be78f36c62ee8ee5790` /
`answerability-semantic-v2-decoder-v0.2-qualification-failed-nonconforming`.
This record is the final owner-reviewed interpretation. Pre-review diagnostic reports,
results, journals and receipts remain preserved historical evidence.

## Frozen diagnostic identity

Decoder implementation: **xgrammar==0.2.8**.
Schema: **exact frozen V2 schema**.
Schema SHA-256:
`6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.

| Compile parameter | Actual value |
| --- | --- |
| any_order | false |
| strict_mode | true |
| any_whitespace | true |
| indent | null |
| separators | null |
| max_whitespace_cnt | null |

No schema substitution or override occurred. The original schema text and the same
installed compilation path were used. Root required fields remain material_asks,
policy_context_status, decision and reason_code.

## Preserved matcher evidence

| Fixture | Description | Expected | Actual |
| --- | --- | --- | --- |
| M1_VALID_COMPLETE | Complete valid object | ACCEPT | REJECT |
| M2_MISSING_DECISION | Missing decision | REJECT | REJECT |
| M3_MISSING_POLICY_CONTEXT | Missing policy_context_status | REJECT | REJECT |
| M4_MISSING_REASON | Missing reason_code | REJECT | REJECT |
| M5_MISSING_ALL_THREE | Missing all three requested required fields | REJECT | ACCEPT |
| M6_ATTEMPT2_S1_RAW | Exact historical S1 raw output | REJECT | ACCEPT |
| M7_ATTEMPT2_S2_RAW | Exact historical S2 raw output | REJECT | ACCEPT |
| M8_ATTEMPT2_S3_RAW | Exact historical S3 raw output | REJECT | ACCEPT |

No fixture was repaired, reinterpreted or rerun. M5-M8 were accepted as complete bodies
and accepted EOS, not merely as valid prefixes. Saved S1-S3 triangulation remains:
standard JSON parser PASS / exact frozen schema validator FAIL / XGrammar ACCEPT.

The decisive incompatibility evidence is not merely M1. The decisive evidence is that
the compiled grammar accepted objects omitting required frozen-schema properties,
including M5 and the three historical structural-smoke outputs. The emitted grammar
contains the root -> root_case_2 -> root_case_2_case_1 path allowing termination after
material_asks without the other required top-level fields. The corresponding value
production accepts generic JSON content. This branch evidence remains unchanged.

**Required-field enforcement for the exact frozen V2 schema is not reliable under
this XGrammar 0.2.8 compile path.**

## Preserved HF and repetition-penalty findings

A fresh HF processor was constructed for each historical generation call. No established
processor reuse/reset defect or lifecycle defect was found. Historical per-token masking
was not independently recorded. Saved generations ended by EOS, not max-new-token
exhaustion. Unproven integration hypotheses are not promoted to established findings.

**CONFIG DEVIATION CONFIRMED; CAUSAL ROLE NOT ESTABLISHED.**
Attempt 2 required repetition_penalty=1.0 and executed repetition_penalty=1.1.
This remains an unauthorized historical configuration deviation. Neither missing
fields nor pure matcher behavior is attributed to repetition penalty. The pure matcher
diagnostic involved no Qwen generation. The exact native conversion mechanism remains
supported but not proven; no new implementation-level diagnosis was run here.

## Scientific consequence and candidate preservation

A clean Attempt 3 using xgrammar==0.2.8 + the exact frozen V2 schema + the same compile
path is **NOT AUTHORIZED**. Pure matcher diagnostics already established failure of
the required structural contract independently of model generation. No further
semantic/model call budget may be spent on this implementation configuration under
this approval. No Attempt 3 is started, and no replacement decoder is selected or installed.

**SEMANTIC_MATERIAL_SUPPORT_V2 remains PRE_REGISTERED_NOT_EVALUATED**.
Its semantic rules and original frozen schema remain unchanged. This diagnostic rejects
the decoder implementation for that schema; it does not reject V2 semantics.
The fresh V2 semantic qualification suite remains **NOT YET AUTHORED**.

Attempt 2 remains permanently **OWNER_REVIEWED / DECODER_QUALIFICATION_FAILED**,
with execution integrity **NONCONFORMING_CONFIG** and clean decoder capability judgment
**NOT_CONCLUSIVE**. Frozen penalty=1.0; executed penalty=1.1. This diagnostic and its
owner approval do not rewrite Attempt-2 artifacts or retroactively create a clean
frozen-config generation evaluation.

## Counters and saved-only revalidation

A2.1-D model initialization=0; generate=0; forward=0; semantic output calls=0.
DEVELOPMENT semantic calls=0; retrieval=0.
Phase 2H HELD_OUT access=false; Phase 2G private HELDOUT access=false.
Package installation=0; package mutation=0; model downloads=0.
Additional finalization model/matcher calls=0. No Qwen or diagnostic runner was imported
or executed during owner finalization. No package operation or network call was made.

Existing pre- and post-diagnostic deterministic tests remain **17/17 PASS** each.
Saved fixture hashes, M1-M8 result/expectation pairs, completion/EOS evidence, raw-output
triangulation, package inventory equality and execution counters were checked offline.
No native matcher diagnostic or model inference was repeated; no test rerun was needed.

All 41 Attempt-2 artifacts remain byte-identical. R2 recovery, R1 failed enablement,
A2.1 Attempt 1, V2 preregistration, V1 qualification, runtime freeze, B3/B2, benchmark,
retriever, policy corpus and deterministic engine remain unchanged. Historical integrity
is supported by exact saved receipts and the unchanged Git candidate scope relative to
the frozen base. No benchmark question bodies were opened.

## Administrative change and hash provenance

Only this diagnostic freeze/owner-review record changes during finalization. Diagnostic
fixtures/results, triangulation, call-path/lifecycle/logits-order analysis, grammar,
journal, helper/tests and all other diagnostic evidence retain their previous hashes.
The two execution source hashes and original V2 schema SHA were explicitly rechecked.

FINAL_SHA256.json remains the unmodified pre-owner-review receipt, SHA-256:
`91e3651b515c23c4af2c09673d21418c9e4cd72a4073aa2871507ed34d047d41`.
Its XGRAMMAR_DIAGNOSTIC_FREEZE_RECORD.md entry
`12bffd7b82f58be23ac04f13b740f1b18a15f31b5937daeb5c2c66d72e803cc8`
identifies the superseded pre-review record, not these finalized bytes. Every other
entry continues to match. The final record SHA is reported separately in the completion
response. There is no circular self-hash requirement, and no other evidence is rewritten.

All unchanged diagnostic artifacts and source identities follow. The receipt's own hash
is listed separately from its contents; the final owner record deliberately omits its
own hash.

| Path | SHA-256 |
| --- | --- |
| `.gitattributes` | `863573bc1d73b80ecd100d85f8320a6f58f9de3e243fca43128033641251c00d` |
| `ATTEMPT2_CALL_PATH_RECEIPT.json` | `a1d5244a57b5cdd1363d88a5eb90ce78a3e550c5d3af686bd3181765b2dd3eda` |
| `ATTEMPT2_COMPILATION_PARAMETERS.json` | `7213a70c5062e426b3fc2e598d5fd25034e7a5c2163bd3560b281285279f117d` |
| `ATTEMPT2_INTEGRITY_RECEIPT.json` | `6f266fa373749fa79d7bd54dbd79905372460b36ad1ee58dec683712cd137917` |
| `CHANGED_FILES.json` | `ef9313a1bf0045dbe547328d1b4bc55804f611129188ccef102c84fb4968c0ad` |
| `COMPILED_GRAMMAR.ebnf` | `d95207f2c0e52f88641274619fba0fe31b74887215f3e99a0f4051b5e3970429` |
| `DIAGNOSTIC_EXECUTION_OBSERVATIONS.json` | `4e6eec7dcfded74f0d8dfe9b79c8012cedef6c4a7465afd6aa2a95e38cd0cc4f` |
| `DIAGNOSTIC_OUTCOME.json` | `ccc4dfa2f5806c7378ae2467f53037a0a703e204fbf77794a92785652fce6b36` |
| `DIAGNOSTIC_PROCESS.json` | `aa9d023a7abdfa83340da1b9c67b7a8e6a3ac7b16709286282fc5c4f12f2218f` |
| `DIAGNOSTIC_SOURCE_RECEIPT.json` | `4e054ef0b5962e26a8cf35da5db5217864ccf06b06dac5c69b0b7172536806c5` |
| `FINAL_INTEGRITY_VERIFICATION.json` | `c22bb04ed386781721d0ed1f90b6a3a555685985ccfc6b66f660a3628a3249a0` |
| `FINAL_SHA256.json` | `91e3651b515c23c4af2c09673d21418c9e4cd72a4073aa2871507ed34d047d41` |
| `GENERATION_TERMINATION_ANALYSIS.json` | `63c5bebff174b58dbd4040365d5153c38430600e93f619dc4918ea5a03f0c7d5` |
| `GRAMMAR_COMPILATION_RECEIPT.json` | `1e8b62f96d364d4ae4358e815ae626c878b67df5920d2ae8261753afd65cb3e2` |
| `GRAMMAR_LOCALIZATION_EVIDENCE.json` | `c060d5ba79d2248c4b2a99be3ec8da755fd622dfb01cd6ebbd1181c433473b82` |
| `HF_PROCESSOR_PATH_ANALYSIS.json` | `f14baa29062ac1a9a2575086f019d756031d04dec360d5c8153d50847fa5c819` |
| `INSTALLED_SOURCE_INTEGRITY.json` | `c2c31023b35b78cc986ecece330c1294035cfb36439d0252bc3f0de15faa0f54` |
| `LOCAL_SOURCE_EVIDENCE.json` | `2f2da5f6f1a9ced475570f851d5d21abbbee6c5b7f6c652f61c16b648b9fc548` |
| `LOGITS_PROCESSOR_ORDER_ANALYSIS.json` | `b97bf03aa0ddc9b325c06c277d38439b6b37aab52ac0a224696f443068e16069` |
| `MATCHER_DIAGNOSTIC_FIXTURES.json` | `3519ecfb0cd1e215af9d550ed219eff48d02a6fb2ebc3918c7f74425a6390e29` |
| `MATCHER_DIAGNOSTIC_RESULTS.json` | `fd4edc436bed7d03a7f7223b81dddc4e6d57b355e2a64809c29e6ec8a4ac109f` |
| `POST_DIAGNOSTIC_PACKAGE_INVENTORY.json` | `cdceeb15b9185ebd2cb102202b1fa738cf4ddd6f13b2aee95278672f6dfcbf62` |
| `POST_DIAGNOSTIC_TEST_RESULTS.json` | `0e1a1eec824c858878ce0e4d8868e49e0cbb7fbab5160b14081c703158760026` |
| `PRE_DIAGNOSTIC_PACKAGE_INVENTORY.json` | `cdceeb15b9185ebd2cb102202b1fa738cf4ddd6f13b2aee95278672f6dfcbf62` |
| `PRE_DIAGNOSTIC_TEST_INITIAL_RESULT.json` | `d282474d2271f4236901e92673b08ddd65359ef68e54e7dab582402eff6e5bca` |
| `PRE_DIAGNOSTIC_TEST_RESULTS.json` | `9800a2b0495fe5e08f58daac2a0c54b71ee213278f85466ff0be01183b4d84ee` |
| `PROCESSOR_LIFECYCLE_ANALYSIS.json` | `6fb84e12514374e0e4b527983bce133f3cd162c1c2885f1e37543ca55c0f3732` |
| `RAW_OUTPUT_TRIANGULATION.json` | `c7041796595c5f31f9505ba19a03e9c454acd7663a88e018e1c56a78fff0b9b3` |
| `SCHEMA_REQUIRED_FIELD_RECEIPT.json` | `419945e1620bb46a92d95de3bb2fbe406f938e191355dc54940d09687c089187` |
| `XGRAMMAR_DIAGNOSTIC_JOURNAL.jsonl` | `c42cc392406eeb66e4aa3c34a677dce9e4dd5ac85bc0d3b450b1fc08193f66ce` |
| `XGRAMMAR_DIAGNOSTIC_PROTOCOL.md` | `81564f82e9b2ce4e91ff5644922aeded0e0b32c48fb48685905f921c4da2d60f` |
| `XGRAMMAR_DIAGNOSTIC_REPORT.md` | `2176bcb690638e10251bbf195bad1df9b5a4d0113912e40a7255b35d2882806e` |
| `gateway/domain/evaluation/answerability/diagnose_xgrammar_v2.py` | `be85e4730bd556befcca12604b240958d09e95cd0b917f7db56584fdfa509e9b` |
| `gateway/domain/tests/test_xgrammar_v2_diagnostic.py` | `990da864ddabb3d62d161499a9eab0fc476cb8b1b6a3b90a9432ea87b5ac8e9b` |

No commit. No tag. No matcher/model rerun. No decoder replacement or Attempt 3. Stop after final Git and hash verification.
