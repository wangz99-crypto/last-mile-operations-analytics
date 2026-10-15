# Accelerated Direct-Regex FSM Acceptance Recovery — Freeze Record

Status: OWNER_REVIEWED / DIRECT_REGEX_RECOVERY_FAILED
Owner: Zhe Wang (Victor)
Owner approval date: 2026-10-15
Scientific review: PASS — RECOVERY FAILURE ACCEPTED
Formal outcome: DIRECT_REGEX_RECOVERY_FAILED
Primary failure classification: FROZEN_TERMINALITY_GATE_FAILED
Root-cause status: NON_EOS_TRANSITIONS_FROM_ACCEPTING_STATE_ESTABLISHED
Exact underlying cause: NOT_YET_ISOLATED
Recorded execution symptom (unchanged): FINAL_ALLOWED_TOKEN_SET_NOT_SINGLETON_EOS
Recorded UTC: 2026-10-15T20:02:49.216783+00:00

## Frozen provenance

Base commit: bc1fd59e175dd7136447392055789811dd4e194c
Base tag: answerability-semantic-v2_1-direct-regex-v0.1-harness-failed
Entry Git status: clean (recorded before recovery changes).
Historical owner status: OWNER_REVIEWED / DIRECT_REGEX_CANDIDATE_FAILED
Historical failure classification: FSM_ACCEPTANCE_HARNESS_EOS_SEMANTICS_ERROR
All 16 frozen historical artifact/source identities in the oracle remain byte-identical. The historical failed run is preserved without relabeling or edits.

Contract SHA-256: 768b9147e77f1dcc9dfd13b9dc4a6f9a2dad0ea6ad498219341fee0c43166198
Regex SHA-256: 3ec42de4a205e599789575954494ad2004beedcc49e2ed550ef865b591dc1482
Regex derivation rules SHA-256: 013d980ebb25e5c6104ac3e75ca790c7eda408528247fbeb71d35ee2d79f8796
Helper SHA-256: 3050703ed4c6321180deb1a59326cf1873413babbc1a9313dba37d04bd5825a0
Test SHA-256: 7393faa04180c948f1705e5d5f761659eb9e10d5a82c794fbe2011a4a85259f3
Oracle SHA-256: 62538b7ccf3b0260a9a1b6b37639aa93aa36803656cffc1d783fa9ce403c1baf
Oracle/helper frozen UTC: 2026-10-15T03:23:12.765691+00:00
Execution started UTC: 2026-10-15T03:23:34.542626+00:00
Execution finished UTC: 2026-10-15T03:23:57.975181+00:00
Pre-execution mock-only tests: 3/3 PASS. No further decoder tests were run during result aggregation.

## Acceptance semantics and observed result

The frozen oracle advances only non-EOS content tokens, then requires is_finished() == true and get_tokens() == [eos_token_id] exactly. It stops without advance(EOS). EOS denotes permitted termination, not an ordinary next-state transition.

34/34 recovered positive fixtures traversed all content tokens successfully and reached a final state. Their tokenizations matched the historical token IDs exactly. EOS token 151645 was present in every final allowed-token list. However, each list contained 423 tokens, so none met the frozen singleton requirement: ACCEPT 0, REJECT 34, ERROR 0. Full allowed lists are retained in RECOVERY_RESULTS.json. No post-result edit, retry, trimming, or alternate oracle was applied.

The historical administrative assertion that EOS was the sole allowed token remains preserved in the old record. The new measured full lists do not support that assertion for this recovery. The owner-reviewed interpretation is that guide.is_finished() == true does not universally imply guide.get_tokens() == [EOS] for outlines_core. An accepting/final state may still have non-EOS outgoing transitions. This recovery failure is not a harness exception: the frozen V0.1 decoder implementation failed to establish terminal-only behavior after a complete contract-valid output. Non-EOS transitions from an accepting state are established; the exact underlying cause is NOT_YET_ISOLATED. Missing end-of-input anchoring has NOT been established, and no terminality diagnostic was performed.

Direct-regex textual expressivity: NOT_DISPROVEN.
Frozen V0.1 FSM qualification: FAILED.
Direct-regex architecture in general: NOT_REJECTED.
Decoder qualification: NOT_ESTABLISHED.
This V0.1 failure is not generalized to all direct-regex implementations.

Historical expected-REJECT fixtures: 30/30 correct, carried forward; zero re-executions.
Historical textual qualification: 64/64 PASS, carried forward; zero textual reruns.
Combined result: 30/64 correct; false accepts 0; false rejects 34 under the frozen oracle; errors 0.
Decoder-owned coverage: all 18 rule pairs represented; 0/18 qualified because each associated positive failed the exact terminal predicate.

M1: historical textual ACCEPT; recovery traversal successful, final state true, EOS present among 423 tokens, recovery REJECT.
M2–M8: historical correct REJECT, carried forward unchanged.
U+0000 (STRING_NUL): historical JSON PASS, contract PASS, textual regex ACCEPT; recovery traversal successful, final state true, EOS present among 423 tokens; exact-singleton check FAIL; recovery REJECT. The fixture and regex were not changed.

## Environment and counters

Package inventories: 64 before and after; identical to one another and the verified historical environment. Additions 0; removals 0; version drift 0; METADATA/RECORD drift 0; pip check PASS before and after. No package installation or mutation.
Recovery FSM fixture executions 34; retries 0; historical reject reruns 0; textual regex reruns 0; regex derivations 0; advance(EOS) calls 0.
Frozen local tokenizer loads 1; Index reconstructions 1. No tokenizer reload during aggregation.
Model initialization 0; generate 0; forward 0; DEVELOPMENT 0; retrieval 0.
Phase 2H HELD_OUT access false; Phase 2G private HELDOUT access false.
Fresh V2.1 semantic suite: NOT YET AUTHORED.
Recorded socket events: socket construction, IPv6 loopback bind (::1, 0), and gethostname. No remote connect/download is recorded.
Exact-validator qualification: NOT BEGUN.

## Artifact scope and Git review

Exactly seven recovery artifacts, one helper, and one narrowly scoped test. No .gitattributes changes. Recovery artifacts remain ignored and unstaged; helper and test remain untracked. No commit or tag was created. FINAL_SHA256.json remains the unchanged pre-owner-review hash receipt. Its FREEZE_RECORD.md entry identifies the prior administrative bytes (SHA-256 1ad8afe2991e6a0b1b6bdd6cf6c6a21a77c340ca8c73994203a97ed9bd500323); only that administrative entry is superseded by this owner-reviewed record. All other entries remain current. The finalized freeze-record SHA-256 is reported externally to avoid a circular self-hash.

Git status --short:
```text
?? gateway/domain/evaluation/answerability/recover_direct_regex_acceptance.py
?? gateway/domain/tests/test_direct_regex_acceptance_recovery.py
```
Git diff --name-only: empty.
Git diff --cached --name-only: empty.

Owner finalization changed only this administrative record. All raw recovery results, combined receipt, protocol, oracle, environment receipt, regex, helper logic, tests, and historical artifacts remain byte-identical.

Finalization counters: package mutation 0; tokenizer loads 0; Index constructions 0; FSM executions 0; fixture reruns 0; model initialization 0; generate 0; forward 0; DEVELOPMENT 0; retrieval 0; Phase 2H HELD_OUT access false; Phase 2G private HELDOUT access false. Historical execution counters above are unchanged. No tests or diagnostics were rerun. No commit or tag was created. Terminality diagnostic and exact-validator qualification were not begun.
