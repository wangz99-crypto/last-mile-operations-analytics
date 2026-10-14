# Stack selection and static stop

Outcome: **LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED**
Owner status: CANDIDATE_AWAITING_OWNER_REVIEW.

Sole selected grammar engine: llguidance==1.9.1, SELECTED_NOT_INSTALLED / NOT_QUALIFIED / CAPABILITY_NOT_ASSESSED. Sole future HF integration: outlines==1.3.3 with llguidance backend, SELECTED_FOR_FUTURE_INTEGRATION / NOT_INSTALLED / NOT_QUALIFIED. No alternative version or decoder was selected.

The initial rationale is architectural fit only: compatible Python/Windows wheel metadata and documented schema/grammar/matcher interfaces. It is not measured V2 performance. Static release-source review then established a hard contradiction with exact V2 enforcement: uniqueItems, contains and if/then/else are known keywords absent from the implementation whitelist. Strict mode rejects known unimplemented keys. These constraints are material in V2; enabling lenient behavior would weaken the target. Therefore preregistration cannot authorize progression. No compiler or matcher was run and no structural-qualification failure is claimed.

The two owner-provided wheel hashes match official PyPI metadata. This is a semantic-support blocker, not a release identity/platform mismatch. All future gates are preserved as a conditional specification for review; K0 and subsequent work are NOT authorized. Stop for owner disposition. Do not install, rewrite V2 or shop for a replacement.

Historical LMFE 0.11.3 suitability remains REJECTED for the exact frozen schema; GD confidence ESTABLISHED, helper NOT_CAUSAL. Historical XGrammar 0.2.8 exact-schema suitability remains REJECTED. Neither result is generalized to every schema, and neither package was removed.
