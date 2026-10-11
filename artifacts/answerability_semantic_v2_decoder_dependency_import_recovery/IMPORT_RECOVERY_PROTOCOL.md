# R2 dependency import recovery protocol

This attempt validates only the exact installed state left by R1. R1 remains permanently
OWNER_REVIEWED / DEPENDENCY_ENABLEMENT_FAILED, classification IMPORT_VALIDATION_HARNESS_INTERFERENCE.
No package install/uninstall/repair/version change, decoder execution, model load, retrieval,
benchmark access or new suite authoring is authorized.

Five independent fresh Python children run once each, in this frozen order:
annotated_types, typing_inspection, pydantic_core, pydantic, tvm_ffi.
Only if all five pass, one combined fresh child imports all five in that same order.
Maximum six import-validation children; no retries. Each has a fixed 120-second timeout.
The separate post-validation pip check process is not an import-validation child.

Every child uses the frozen venv Python, -I -B, and the venv root as cwd. The exact script,
working directory, environment overrides, target metadata identities, timeout and source hash
are frozen in IMPORT_VALIDATION_PLAN.json before execution. No temporary script is needed.
The child receives only target module/identity metadata, no repository data or model path.

The old broad subprocess guard is neither imported nor patched. A profile callback observes
platform calls, and an audit callback records subprocess/socket/prohibited file-open events;
these observers never deny operations or replace subprocess/socket APIs. Ordinary hostname
and Windows/platform probes are permitted. The script requests no network operation.

PASS per child requires exit 0, complete imports, paths inside the frozen venv, exact frozen
distribution/version/METADATA/RECORD identities, no forbidden modules/content accessed.
A missing module-level version is recorded as null and does not fail a valid distribution.
Stage A failure forbids Stage B; preserve all output/tracebacks. Post-inventory must match
exactly and pip check must pass. Success establishes dependency imports only, not XGrammar
or V2 semantic capability. No decoder install/import/schema/smoke steps follow.
