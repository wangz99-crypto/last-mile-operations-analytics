# A2.1-R dependency enablement protocol

Base: 36ccd603bd0bfba6ba5359bc39d3e6f4225db184 / answerability-semantic-v2-decoder-v0.1-qualification-blocked.
Only missing owner-pinned wheels may be added. No existing package may change or be reinstalled.
All wheel hashes, Python/platform tags and METADATA must pass before installation. Resolve mandatory
requirements with extras disabled; unexpected missing requirements block. Preserve typing-extensions
4.16.0 exactly. Freeze DEPENDENCY_LOCK.json and its journal hash before any installation; do not
revise that lock afterward. Install each explicit local wheel with --no-deps --no-index --no-cache-dir.
No source builds, alternate versions, optional extras, decoder install/import, schema compilation,
model initialization/generation, structural cases, semantic cases, retrieval or benchmark access.

Validate complete inventories including version and METADATA/RECORD identity; validate installed wheel
payload bytes; pre/post pip check; dependency-only imports; all applicable requirements of the saved
XGrammar wheel without importing it. New conflict, import error or package drift after installation is
FAILED; stop without repair. Missing/ambiguous preconditions are BLOCKED. Success enables dependencies
only and must remain awaiting decoder requalification and owner review.
