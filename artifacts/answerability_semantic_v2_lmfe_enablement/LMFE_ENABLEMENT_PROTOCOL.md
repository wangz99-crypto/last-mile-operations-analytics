# Phase 2H-B3.2-A2.1-F installation scope and execution record

This phase authorizes installation and import/API validation only. It does not
authorize parser conformance, M1-M8, Qwen/tokenizer initialization, generation,
semantic qualification, DEVELOPMENT or HELD_OUT access. No A2.1-G work is authorized.

Base: `cfe69ac260fabac26b1b91fb9fec5f2bba5b8ded`.
Tag: `answerability-semantic-v2-decoder-replacement-v0.1-pre-install`.
HEAD matched the tag and the worktree was clean before helper/test creation.
A2.1-E is OWNER_REVIEWED / REPLACEMENT_DECODER_SELECTED_NOT_QUALIFIED.
The sole replacement remains lm-format-enforcer==0.11.3; capability NOT_ASSESSED.

Authorized wheels only:

| Package | Wheel | SHA-256 |
| --- | --- | --- |
| interegular==0.3.3 | interegular-0.3.3-py37-none-any.whl | b0c07007d48c89d6d19f7204972d369b2a77222722e126b6aa63aa721dc3b19c |
| lm-format-enforcer==0.11.3 | lm_format_enforcer-0.11.3-py3-none-any.whl | cf586350875def1ae7a8fba84fcbbfc8371424b6c9d05c1fcba70aa233fbf06f |

Each wheel is hash-checked before metadata inspection and again before installation.
The wheelhouse is outside the repository. No source distribution, alternate version,
resolver-selected dependency or model file is downloaded. The frozen lock records
filenames, versions, hashes and installation order before INSTALL_BEGIN.

Install interegular then LMFE from local wheel paths, using --no-deps --no-index
--no-cache-dir --disable-pip-version-check. Pre/post inventories record complete
distribution versions plus METADATA and RECORD hashes. All pre-existing 34 packages
must remain identical. Only the two authorized additions are permitted.

Installed wheel payloads and RECORD hashes are verified before import. Import/API
validation uses one fresh Python child, offline HF settings, no bytecode writes,
and an external observation/denial guard. Its execution source is hash-frozen in
EXECUTION_SOURCE_RECEIPT.json. Import validation is not capability qualification.

The guard allows socket construction, local hostname queries and loopback binds;
it blocks outbound activity and protected data/model paths. It prohibits parser
construction and scientific call paths. OS-version subprocess matching was too
narrow for the actual quoted Windows command; the resulting failure is preserved,
not corrected or retried after observing the import failure.

Outcome rules: no-install identity/dependency issues block enablement; failures
after mutation produce LMFE_ENABLEMENT_FAILED. No installation or import retry,
repair, fallback version, decoder comparison, or structural qualification follows
a genuine execution failure. The final recorded outcome for this run is FAILED.

The frozen V2 schema remains byte-identical, SHA-256
`6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`.
V2 remains PRE_REGISTERED_NOT_EVALUATED; fresh suite NOT YET AUTHORED.
Historical XGrammar evidence remains ESTABLISHED, with exact-schema suitability
REJECTED and outcome GRAMMAR_COMPILATION_OR_REQUIRED_FIELD_ENFORCEMENT_ISSUE.
