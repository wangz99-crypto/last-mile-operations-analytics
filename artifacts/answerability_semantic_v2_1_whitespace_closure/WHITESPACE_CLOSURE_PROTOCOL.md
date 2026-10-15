# Frozen V0.1 JSON Whitespace Closure Qualification

Freeze this protocol, the contract-aligned oracle, helper, and exact historical identities before execution. No regex/contract/package mutation. No V0.2 or end-anchor insertion. No model construction, forward, generation, benchmark/retrieval access, or exact-validator qualification.

Traverse each of the frozen 34 positive fixtures exactly once using one local frozen tokenizer and one V0.1 Index. Verify identical historical token IDs and input bytes. Observe the final state, final-state flag and EOS membership; never advance EOS. Errors remain errors. Reduce the resulting final states to sorted unique roots.

Deterministically traverse the full finite non-EOS transition graph from those roots. Visit each state once globally, share overlapping subgraphs, and compute a separate reachability proof for each root. Sort states/token IDs, track visited states, record every edge and its exact Vocabulary transition bytes, destination and destination final-state flag. Do not normalize token text. Empty, non-EOS special tokens, and non-whitespace tokens fail the closure gate. EOS is termination metadata, never whitespace.

The sole whitespace byte set is {0x20,0x09,0x0A,0x0D}. Classification uses non-empty exact UTF-8 bytes of the same string supplied to the official Outlines Vocabulary constructor; no Unicode whitespace predicate or regex shorthand. Record token spellings and special-token flags separately.

All reachable non-EOS edges must be JSON_WHITESPACE_ONLY. All accepting continuation states must allow EOS, and every reachable continuation state must have a path to an accepting EOS opportunity. Resolve graph cycles by strongly connected components; loops pass only with whitespace-only internal edges. Operational implication: MODEL_MAY_EMIT_TRAILING_WHITESPACE_UNTIL_STOP_LIMIT. This is a runtime-efficiency concern, not semantic expansion.

The frozen corrected oracle accepts a complete positive iff content traversal passes, its state is final, EOS is allowed, and exhaustive continuation closure contains only JSON whitespace. A singleton [EOS] list is not required. Preserve every earlier outcome under its historical oracle.

Carry forward historical 64/64 textual results and 30 correct negative FSM results without rerun. Their invalid paths were rejected during traversal; this new oracle changes only the treatment of already-accepting valid-object states with whitespace-only suffix closure and cannot broaden those structurally invalid fixture paths. Combine 34 current positives and 30 historical negatives, and evaluate all 18 frozen rule-pair associations.

Any non-whitespace edge gives DIRECT_REGEX_V0_1_WHITESPACE_CLOSURE_FAILED. Empty/special anomalies also fail the required closure gate. Unresolved exhaustive traversal or runtime errors give DIRECT_REGEX_V0_1_WHITESPACE_CLOSURE_INCONCLUSIVE. Environment/provenance failure gives DIRECT_REGEX_V0_1_CLOSURE_QUALIFICATION_BLOCKED. Only all gates passing yields DIRECT_REGEX_V0_1_DECODER_QUALIFIED. No retries, repair, automatic V0.2, or another recovery.

Save pre/post raw package-version/METADATA/RECORD inventories and pip-check results in QUALIFICATION_RECEIPT.json. Keep exactly the seven authorized artifacts and this one helper. Checkpoint partial execution; never overwrite an earlier attempted run. Stop for owner review; no commit or tag.
