# Accelerated direct-regex acceptance recovery

Recover only the owner-established FSM_ACCEPTANCE_HARNESS_EOS_SEMANTICS_ERROR. Preserve historical OWNER_REVIEWED / DIRECT_REGEX_CANDIDATE_FAILED; never rewrite its artifacts or reclassify that historical run as qualified.

Reuse the exact 64 frozen fixtures: execute only 34 expected ACCEPT fixtures, once each. Carry forward all 30 historical correct REJECT results including M2-M8. Do not rerun textual regex qualification or derive/change the regex, contract or fixtures. Original package versions and raw METADATA/RECORD must match; pip check before/after. No package mutation.

Corrected acceptance: advance every non-EOS content token; after the last token require is_finished() == true and get_tokens() exactly [eos_token_id]; STOP. Never advance EOS. Invalid transition or terminal condition is REJECT; exceptions remain ERROR. No retries, no post-execution helper/regex/fixture/tokenization edits.

Use the same frozen local Qwen tokenizer revision and historical vocabulary/Index construction, offline. Compare all recovered token ID sequences to the saved historical tokenization before traversal. One tokenizer reload is necessary because the historical process is no longer alive. No Qwen model initialization, model weights, forward or generate.

Freeze helper and corrected oracle identities before recovery FSM execution. A small unit test uses only synthetic Guide doubles and saved partition metadata; it does not invoke a decoder or rerun the 64 textual tests.

Combine 34 recovered ACCEPTs with 30 unchanged historical REJECTs only after execution. Require 64/64 correct, zero errors/false accepts/false rejects, U+0000 and M1 recovery, M2-M8 carried results, 18/18 frozen-rule coverage, unchanged package environment, zero retries/model calls. Otherwise preserve failed or blocked provenance and STOP without tuning.

No DEVELOPMENT/retrieval or either HELD_OUT source access. Fresh V2.1 semantic suite NOT YET AUTHORED. Exact-validator qualification is outside scope. Only seven requested artifacts, one helper and one narrow test. No commit or tag.
