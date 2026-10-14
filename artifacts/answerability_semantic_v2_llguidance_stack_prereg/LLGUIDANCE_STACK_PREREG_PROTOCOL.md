# Phase 2H-B3.2-A2.1-I preregistration protocol

Status: CANDIDATE_AWAITING_OWNER_REVIEW.
Outcome: LLGUIDANCE_STACK_PREREGISTRATION_BLOCKED, from static official release-source incompatibility. No executable qualification candidate is released.

Base HEAD and tag answerability-semantic-v2-lmfe-v0.4-schema-incompatibility both resolve to baae21265e1ec192f0ddf047f7dd8b3377647c8b. Entry working tree and index were clean.

The sole stack is llguidance==1.9.1 followed, only if structurally qualified, by outlines==1.3.3 using llguidance. Candidate SEMANTIC_MATERIAL_SUPPORT_V2 stays PRE_REGISTERED_NOT_EVALUATED. Exact schema: artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json; SHA-256 6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e.

Freeze the original bytes. No normalization, reordering, explicit-type insertion, flattening, conditional rewriting, keyword removal, Pydantic translation or project-specific decoder schema. Internal conversion inside the selected implementation is behavior under test and must be recorded. No coerce_one_of or lenient mode; both false via API options, never schema injection. No oneOf-to-anyOf relaxation. Compiler-proven equivalence must preserve exact semantics and remains subject to qualification.

llguidance support is not assumed complete. oneOf/allOf support is partial/conditional. The static blocker is documented in JSON_SCHEMA_CAPABILITY_MATRIX.json: uniqueItems, contains, if, then, else. No V2 schema compile/validation or package import occurred to verify it dynamically.

Future sequence, presently blocked: K0 package/runtime enablement; K1 unchanged-schema grammar construction; K2 grammar validation and warnings; K3 exact known-risk subtree compilation/validation; K4 M1-M8 pure matcher gate; K5 every material feature; L Outlines/Transformers integration; M exactly three structural model calls. Every earlier mandatory gate must pass. Critical semantic warnings require owner review; errors never count as expected REJECT. See FUTURE_STRUCTURAL_GATE.md and PREREGISTERED_STACK.json.

No fresh semantic suite, V1 question reuse/paraphrase, DEVELOPMENT contents, retrieval, or either HELD_OUT corpus. No benchmark-derived prompt/rule changes. This phase permits only official metadata/source inspection, environment metadata comparison, documentation and offline preregistration checks. No package mutation, resolver, tokenizer or model activity; no commit/tag.

Missing dependencies remain VERSION_SELECTION_PENDING_OWNER_AUTHORIZATION unless release metadata directly fixes a version. Dependency closure and Outlines release API paths must be frozen in a separately authorized phase before integration installation/execution. No main-branch API assumption.
