# P2P3 candidate selection

Outcome: **DECODER_CANDIDATE_SELECTION_BLOCKED**. Owner review pending.

The sole inspected stack is outlines==1.3.3 with its release-required outlines_core==0.2.14 backend. The implementation-neutral contract was frozen before capability inspection; its five immutable hashes and ordered events are in CONTRACT_FREEZE_RECEIPT.json. No contract, derivation rule or ownership decision was changed after inspection.

## Established incompatibility

The mandatory ask string type must retain all contract-permitted JSON string values. At the pinned core release, the generic string language excludes U+0000 and has no Unicode escape branch. A string containing U+0000 therefore has no legal serialization in that language: a literal NUL is not valid JSON, and its required escape is unsupported. This establishes a semantic-value restriction at `/properties/material_asks/items/properties/ask/type`. This is static source reasoning, not a compiled-regex test or runtime qualification. It does not claim all Outlines uses or all releases fail.

Release-specific source, line references, source response hashes, all 18 classifications and frozen future probe definitions are retained in the matrix and dependency metadata. One mandatory rule is STATICALLY_UNSUPPORTED; the other 17 remain REQUIRES_RUNTIME_QUALIFICATION. Compiler acceptance and actual masking are untested. Fixed property order, limited whitespace and canonical integer spelling are separately neutral; they do not excuse the string-value loss.

No custom string override, replacement schema, contract weakening, second decoder or fallback was introduced. Candidate capability research stopped on the established incompatibility. Later work only recorded previously obtained metadata and verified local records.

## Dependency and runtime boundary

Official PyPI metadata pins outlines_core==0.2.14. Windows CPython 3.12 wheel metadata is compatible with the frozen target; the inspected Transformers integration accepts an existing model/tokenizer without a hard CUDA, vLLM or Linux requirement. CPU FP32 execution is NOT_ASSESSED.

The recorded declared dependency graph has 39 nodes and 59 edges. Seven absent unpinned dependencies remain DEPENDENCY_VERSION_SELECTION_PENDING: cloudpickle, datasets, diskcache, genson, jsonschema, pillow and sentencepiece. Their unresolved transitive edges are explicit. Existing versions are observations, not newly authorized pins. No complete install lock is claimed, no resolver ran, and no package was installed or downloaded. The 36-package frozen environment has zero drift.

Exact-schema validator implementation: NOT_YET_SELECTED_NOT_QUALIFIED. No exact validator was selected merely because jsonschema is a declared dependency.

## Procedural stop

The accelerated P4 installation/import/pure-contract qualification route is conditional on a selected candidate; that condition failed. All 18 targeted probe specifications remain unexecuted. Direct pure-backend testing must be established before any future tokenizer/model use. No fresh V2.1 semantic suite has been authored. Stop for owner review; no P4, alternate decoder research, commit or tag is authorized by this result.
