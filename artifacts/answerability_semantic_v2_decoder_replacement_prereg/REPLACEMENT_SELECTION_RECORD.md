# Sole replacement selection

Status: REPLACEMENT_DECODER_SELECTED_NOT_QUALIFIED.
Review: CANDIDATE_AWAITING_OWNER_REVIEW.
Capability: NOT_ASSESSED. Installation: INSTALLATION_NOT_AUTHORIZED.

The owner specified `lm-format-enforcer==0.11.3` (`lmformatenforcer`). No other
replacement candidate was selected, installed, inspected for comparison, or run.
The historical XGrammar rejection remains unchanged.

The exact release's [PyPI metadata](https://pypi.org/pypi/lm-format-enforcer/0.11.3/json)
and release description provide the selection evidence. The saved raw response
and LMFE_PACKAGE_IDENTITY.json distinguish release-file identity from downloading
or installing those files. Only public metadata was retrieved.

| Architectural consideration | Evidence and limit |
| --- | --- |
| Native JSON Schema parser | Release description documents JsonSchemaParser; exact V2 support remains untested |
| Hugging Face integration | Documents build_transformers_prefix_allowed_tokens_fn with tokenizer and parser |
| Required/optional fields | Claimed by release description; no enforcement conclusion yet |
| Python 3.12 | Requires-Python <4.0,>=3.8 and explicit Python 3.12 classifier; frozen 3.12.10 satisfies metadata |
| CPU compatibility | Platform-independent py3-none-any wheel and Python token-filtering architecture support selection as a CPU candidate; Windows CPU runtime compatibility has NOT been tested |
| Weights unchanged | Intended callback restricts token choices; no weight conversion or modification is planned or performed |

No runtime accuracy or decoder capability comparison was made. Architecture
claims justify preregistration only. In particular, schema composition, required
properties, numeric constraints and uniqueItems must be tested explicitly later.

Exact direct Requires-Dist declarations:

- pydantic>=1.10.8: installed 2.13.5, declaration satisfied.
- interegular>=0.3.2: MISSING; no exact dependency version selected.
- packaging: installed 26.3, declaration satisfied.
- pyyaml: installed 6.0.3, declaration satisfied.

LMFE itself is absent. The installed direct/transitive metadata graph and inactive
extra markers are recorded in LMFE_DEPENDENCY_REQUIREMENTS.json. Missing
interegular's transitive graph is unresolved because no exact release is selected;
this is not a resolved install plan. A later owner-authorized enablement phase must
pin its version, inspect that exact release metadata, and verify all dependencies
and distribution hashes without drifting existing packages. No pip resolver ran.
Frozen environment: 34 packages, package metadata/RECORD drift = 0.

Fresh V2 semantic qualification suite: NOT YET AUTHORED. The next procedural step
is owner review of this preregistration, followed only if authorized by dependency
enablement and separate pure structural qualification before any model generation.
