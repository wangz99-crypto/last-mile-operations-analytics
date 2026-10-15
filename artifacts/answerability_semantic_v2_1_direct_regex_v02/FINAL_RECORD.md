# Accelerated Direct-Regex V0.2 — Terminality Diagnostic Final Record

Status: OWNER_REVIEWED / DIRECT_REGEX_TERMINALITY_DIAGNOSTIC_INCONCLUSIVE
Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-15
Scientific review: PASS — END-ANCHOR CORRECTION NOT AUTHORIZED
Final outcome: DIRECT_REGEX_TERMINALITY_DIAGNOSTIC_INCONCLUSIVE
Recorded UTC: 2026-10-15T20:18:19.992404+00:00

## Base and immutable evidence

Base commit: 80ab1c2acf5d6dad4cc4cb5c903f23bc6f86b725
Base tag: answerability-semantic-v2_1-direct-regex-v0.2-recovery-failed
Entry working tree: clean, verified before creating this phase's helper.
Historical initial status: OWNER_REVIEWED / DIRECT_REGEX_CANDIDATE_FAILED.
Historical recovery status: OWNER_REVIEWED / DIRECT_REGEX_RECOVERY_FAILED.
Both historical outcomes and all 25 recorded input/source identities are byte-identical. No prior failed result is relabeled.

Contract SHA-256: 768b9147e77f1dcc9dfd13b9dc4a6f9a2dad0ea6ad498219341fee0c43166198
V0.1 regex SHA-256: 3ec42de4a205e599789575954494ad2004beedcc49e2ed550ef865b591dc1482
V0.1 derivation rules SHA-256: 013d980ebb25e5c6104ac3e75ca790c7eda408528247fbeb71d35ee2d79f8796
Frozen recovery helper SHA-256: 3050703ed4c6321180deb1a59326cf1873413babbc1a9313dba37d04bd5825a0
New diagnostic helper SHA-256: e9e6b031f1f6543ab1d7dfbdc4ef6e37c0d219e7b115f71e03c8cdca94d00f8e
Pre-execution diagnostic preregistration SHA-256: 531a1da576e9dc1f1e7fa958e2c9c2508220ef16b63d2b87ee12de37e3ad1407
Preregistered UTC: 2026-10-15T20:16:01.283213+00:00
Execution started UTC: 2026-10-15T20:16:25.685757+00:00
Execution finished UTC: 2026-10-15T20:16:40.623327+00:00
Final diagnostic SHA-256: 9efec58ebfe5b2f0305e08c83fab65a94eed4a9b07b90bf89542771705ef7902

## Static and release-specific facts

The exact 1197-byte V0.1 expression contains no effective global end-of-input assertion: END_ANCHOR_ABSENT. It ends with the explicitly allowed JSON-whitespace repetition [ \t\r\n]*. This conclusion came from exact regex inspection, not from the 423-token observation.

The outlines_core 0.2.14 Index implementation builds a DFA with an anchored start, detects final states, enumerates ordinary token transitions, and adds EOS to final-state allowed tokens. Its next_state operation returns no transition for EOS. Thus final-state status need not imply a singleton EOS list, and start anchoring is not end-of-input anchoring.
Source: https://raw.githubusercontent.com/dottxt-ai/outlines-core/0.2.14/src/index.rs (104–143, 170–175, 216–219).

## Two-fixture diagnostic

Only M1 and STRING_NUL were executed, once each, using one shared V0.1 Index and one frozen local tokenizer load. Both token sequences matched historical token IDs.

| Fixture | Content tokens | Traversal | Accepting state | Allowed tokens | Non-EOS tokens | Non-empty JSON-whitespace-only | Non-empty non-whitespace | Actual next states available |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| M1 | 48 | PASS | true | 423 | 422 | 422 | 0 | 422 |
| STRING_NUL | 51 | PASS | true | 423 | 422 | 422 | 0 | 422 |

EOS 151645 was permitted in both states. Both observed accepting-state IDs were 46336; every classified non-EOS next-state ID was 384. IDs are observations for this Index construction, not cross-run identities. All 422 non-EOS token representations per fixture were exhaustively classified using exactly the string conversion used to build the backend Vocabulary. Every one contains only JSON space/TAB/CR/LF; no empty or non-whitespace token occurs. No extra transition was inferred merely from is_finished(). Index.get_next_state was queried without advancing EOS or re-executing either fixture.

Representative tokens include 197 = TAB (hex 09), 198 = LF (0a), 201 = CR (0d), 220 = space (20), and 256 = two spaces (2020). All IDs, representations, UTF-8 bytes, class labels, actual next-state availability, and deterministic samples are preserved in TERMINALITY_DIAGNOSTIC.json.

Root-cause condition A: true (end assertion absent).
Root-cause condition B: false (zero meaningful non-empty, non-whitespace continuations in either fixture).
Root-cause gate: FAILED.
V0_1_END_OF_INPUT_ENFORCEMENT_MISSING: NOT ESTABLISHED by the preregistered two-condition diagnostic.

The observed immediate non-EOS transitions are JSON-whitespace continuations, consistent with the frozen regex's explicit trailing-whitespace repetition. This does not establish the proposed end-of-input defect or justify the conditional correction. No claim is made about unexecuted suffixes, later paths, or an unconstructed V0.2 Index.

## Owner-reviewed contract interpretation (separate from historical outcome)

The frozen Decoder Enforcement Contract is defined over valid JSON value/object semantics. It does NOT require EOS to be the sole immediately allowed token after a complete JSON object. Legal trailing JSON whitespace is serialization-level behavior: by itself it creates neither a second top-level value, prose suffix, additional property, nor semantic output content.

Therefore guide.get_tokens() == [EOS] is NOT established as a necessary consequence of the frozen Decoder Enforcement Contract. The earlier sole-EOS recovery oracle is stricter than the contract unless non-whitespace continuation is reachable. This interpretation does not retroactively change either historical result or frozen qualification oracle.

Historical OWNER_REVIEWED / DIRECT_REGEX_CANDIDATE_FAILED and OWNER_REVIEWED / DIRECT_REGEX_RECOVERY_FAILED remain valid historical failed runs under their frozen qualification oracles. Neither historical record was rewritten.

Current capability interpretation:
- direct-regex textual qualification = 64/64 PASS (historical; not rerun)
- direct-regex semantic-value expressivity = SUPPORTED BY CURRENT EVIDENCE
- meaningful post-object suffix generation = NOT OBSERVED
- trailing JSON whitespace generation = OBSERVED
- V0.1 decoder qualification = NOT YET ESTABLISHED
- V0.1 decoder rejection = NOT ESTABLISHED

These observations cover the recorded immediate transitions; they do not prove transitive closure. A separate reachability check is still required to show that every possible non-EOS continuation path from every accepting state reached by a contract-valid complete object remains confined to legal RFC/JSON trailing whitespace until EOS. No such check occurred during owner finalization. V0.1 is not declared qualified.

## Conditional qualification not authorized

V0.2 authorized: false.
V0_2_REGEX.txt: NOT CREATED.
V0_2_DERIVATION_RECORD.json: NOT CREATED.
V0_2_QUALIFICATION_RESULTS.json: NOT CREATED.
No regex transformation or V0.2 freeze occurred. The preregistered monotonicity argument remains conditional; there is no V0.2 candidate to qualify or against which to carry forward negatives.

V0.2 positive executions: 0/34 (NOT RUN).
U+0000: historical JSON/contract/textual PASS retained; V0.1 diagnostic traversal PASS, accepting state true, EOS allowed, 422 whitespace-only continuations; no V0.2 result.
Historical 30 correct negatives remain unchanged and were not rerun; no new proof-based V0.2 carry-forward was claimed.
Suffix probes: 0/3 executed; the three planned classes remain unexecuted.
New combined 64-fixture qualification: NOT RUN / NOT ESTABLISHED.
New 18-rule qualification: NOT RUN / NOT ESTABLISHED.
Historical textual 64/64 PASS and recovery 30/64 correct remain historical only.
Decoder qualification remains NOT_ESTABLISHED. No V0.3 or further recovery was started.

## Environment, counters, and quarantine

64-package pre/post inventories are identical, including version and METADATA/RECORD hashes. Additions 0; removals 0; drift 0. pip check pre/post PASS. No package installation or mutation.
Counters: tokenizer loads 1; V0.1 Index constructions 1; V0.2 Index constructions 0; V0.1 diagnostic fixtures 2; V0.2 positive fixtures 0; negative reruns 0; textual 64-fixture reruns 0; suffix probes 0; retries 0; advance(EOS) 0.
Model initialization 0; generate 0; forward 0; DEVELOPMENT 0; retrieval 0.
Phase 2H HELD_OUT access false; Phase 2G private HELDOUT access false.
Fresh V2.1 semantic suite: NOT YET AUTHORED.
Exact-validator qualification: NOT BEGUN.
Runtime socket events: socket construction, loopback IPv6 bind (::1,0), gethostname; no outbound runtime connect or download recorded. Release-source research was read-only.
Pre-execution syntax and static-anchor checks passed without model/tokenizer/Index execution. No test or fixture rerun occurred after results.

## Artifact and Git scope

Only three of the six allowed artifact names were needed because the root-cause gate stopped the phase: TERMINALITY_DIAGNOSTIC.json, FINAL_RECORD.md, FINAL_SHA256.json. Conditional V0.2 artifacts were deliberately not created. One new helper; no test-file update, no historical source edits, no .gitattributes change.
FINAL_SHA256.json is preserved byte-for-byte as the pre-owner-review receipt (SHA-256 32aed4b3b6ac7267dc220c33d9c6cdde0789ad206bb8e8b7b5dda9984f5892b5). Its FINAL_RECORD.md entry refers to the original administrative record (SHA-256 7864885693509b7014c2122247b8e25d9dd554b3d8a260c7401ea025d1b086fe), superseded only by this owner-reviewed administrative revision. All diagnostic/helper receipt entries remain current and unchanged. The updated administrative-record hash is reported externally to avoid circularity.

Git status --short:
```text
?? gateway/domain/evaluation/answerability/qualify_direct_regex_v02.py
```
Git diff --name-only: empty.
Git diff --cached --name-only: empty.
New artifact directory remains ignored and unstaged. No commit or tag.

Owner finalization changed only FINAL_RECORD.md. Diagnostic evidence, current helper, frozen contract/regex/derivation, all historical records, environment evidence, and the original hash receipt remain byte-identical. The execution and environment counters above are preserved historical observations, not repeated checks.

During finalization: package mutation 0; tokenizer loads 0; Index constructions 0; fixture executions 0; model initialization 0; generate 0; forward 0; DEVELOPMENT 0; retrieval 0; Phase 2H HELD_OUT access false; Phase 2G private HELDOUT access false. No pip check or other tests were rerun; the recorded pre/post PASS results were verified from saved evidence.

Next scientific question, reserved for a separate narrow closure diagnostic:
> From every V0.1 accepting state reached by a contract-valid complete object, is every possible non-EOS continuation path restricted exclusively to RFC/JSON trailing whitespace until EOS?

Closure diagnostic: NOT BEGUN. V0.2: NOT CREATED. No \z added; V0.1 unchanged; no rerun of the 34 positives. No commit or tag. Stop after administrative owner finalization.
