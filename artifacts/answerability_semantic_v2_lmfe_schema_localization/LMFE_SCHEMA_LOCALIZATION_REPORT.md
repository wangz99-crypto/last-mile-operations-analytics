# Phase 2H-B3.2-A2.1-GD completion report

Status: CANDIDATE_AWAITING_OWNER_REVIEW
Primary outcome: **LMFE_SCHEMA_SHAPE_INCOMPATIBILITY_ESTABLISHED**
Confidence: **ESTABLISHED** for the localized dispatch paths below.

## Base and immutable history

HEAD and `answerability-semantic-v2-lmfe-v0.3-structural-conformance-failed` both resolve to `bc8b6371e84b0a98662ab3eaf12183b232f04213`. The pre-phase working tree was clean. Predecessor `answerability-semantic-v2-lmfe-v0.2-imports-validated` remains `8ccdacedd1b47de0471b534ac0b0e786e2c36299`.

A2.1-G remains OWNER_REVIEWED / LMFE_STRUCTURAL_CONFORMANCE_FAILED, classification PARSER_TRAVERSAL_UNSUPPORTED_TYPE_NONE. Its eight constructors passed; eight traversals errored; successful adjudications remain 0/8. Required-field capability remains NOT_ASSESSED. G's original NOT_YET_ISOLATED snapshot was not rewritten; this separate GD evidence provides localization. Owner freeze-record SHA remains `29e0fffca5e5c965dd31d7b4cc479441d1f8d94506a911ae124ecdd28074c883`.

Implementation: lm-format-enforcer==0.11.3. Exact original V2 schema SHA-256: `6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e`. No schema, library, helper or configuration repair occurred.

## Schema inventory

Total schema nodes: **42**. Nodes lacking explicit type: **36**. Every node's stable JSON Pointer, literal parent pointer, nearest schema parent, keys, type, keyword presence and additionalProperties value is saved in SCHEMA_NODE_INVENTORY.json. Categories overlap:

- $ref plus siblings: 0
- $ref-only: 0
- additionalProperties schema object: 0
- allOf-only: 0
- anyOf-only: 0
- const-only: 13
- empty schema {}: 0
- enum-only: 5
- explicit scalar/object/array type: 6
- if/then/else node: 1
- missing type: 36
- nested items schema: 4
- oneOf-only: 0
- type as array / union: 0

Missing type alone is not causal: enum-only and const-only controls exercised their frozen prefixes without this error. No absent $ref/empty/union-only shapes were invented or tested.

## Original first-error localization

Established offending branch properties:

1. `/oneOf/0/properties/material_asks`:

```json
{
  "items": {
    "properties": {
      "support_status": {
        "const": "SUPPORTED"
      }
    }
  }
}
```

2. `/oneOf/1/properties/material_asks`:

```json
{
  "contains": {
    "properties": {
      "support_status": {
        "const": "UNSUPPORTED"
      }
    }
  },
  "items": {
    "properties": {
      "support_status": {
        "enum": [
          "SUPPORTED",
          "UNSUPPORTED"
        ]
      }
    }
  }
}
```

The parent `/properties/material_asks` has `type: array`. However, LMFE's `_merge_object_schemas` copies a parent property only when the property name is absent from a oneOf branch. It retains the branch's existing untyped items/contains property instead of incorporating the parent typed-array definition.

When ObjectParsingState consumes the colon after `material_asks`, it dispatches that untyped branch-property object. Its `type` resolves to None; items/contains alone do not select a parser branch. `get_parser` falls through to `raise Exception("Unsupported type " + str(value_schema.type))`.

Exact installed file: `C:\Users\zhewa\.virtualenvs\llm-rag-semantic-qwen25-1p5b\Lib\site-packages\lmformatenforcer\jsonschemaparser.py`
Source SHA-256: `6bc4a8a10621c6d38d70ebb5ae1dc21aaa98c0454a2e80be1896586f10dccf94`

Stable locations:

- JsonSchemaParser original dict to JsonSchemaObject: lines 42-46; initial dispatch line 51.
- `_merge_object_schemas`: lines 162-172, particularly existing-property check lines 164-168.
- oneOf dispatch: lines 205-210.
- ObjectParsingState property selection/dispatch: lines 338-353.
- `get_parser` terminal exception: **line 269**.
- JsonSchemaObject `type` defaults to None in `external/jsonschemaobject.py`; it does not infer a dispatch type merely from properties/items/conditional extras.

Evidence is triangulated without rerunning G: saved G error positions are all the colon immediately after material_asks; frozen helper/source is inspected; D14 reproduces the overlapping-property oneOf path and the same colon failure; unchanged exact branch subtrees T03/T04 directly reach the same fallback. Runtime dispatch trace records incoming schema objects, type=None, library merge state, source lines and exceptions. The full V2 schema was never instantiated during GD.

## Additional exact-subtree findings and limits

A second dispatch route is established independently for the item subtree: `/properties/material_asks/items` has an explicit object type plus allOf, but `get_parser` handles allOf first (lines 184-188) and dispatches its first child without retaining parent type/properties. `/properties/material_asks/items/allOf/0` contains only if/then/else, represented in LMFE extras; its type is None and the same fallback occurs. D11/D12 and unchanged subtrees T06/T07 reproduce this. T11's unchanged typed array constructs, then its opening bracket dispatches the item and raises.

This additional subtree route is **not attributed to G's first errors**, which occurred earlier at the material_asks colon. Other direct-entry subtrees T05/T08/T09/T10/T12 also raise the same error, but direct-entry failure alone does not make them additional causes of that historical first exception. We therefore choose schema-shape incompatibility rather than claim multiple independent causes of the original first error. LOCALIZATION_OUTCOME.json records evidence confidence and scope per finding.

No claim is made that all oneOf/allOf schemas fail, that required fields were ignored, that a short control prefix proves conformance, or that semantic capability has been assessed. This is scoped to the exact implementation, shapes, parser configuration and runtime.

## Frozen diagnostic probes

Plan SHA-256: `8afee1ca31501111ad8107567282e083359c77bc2cd3b87a911abcda54bc1074`.
The LOCALIZATION_PROBE_PLAN_FROZEN journal event precedes every native probe. Fixed count: **26 = 14 minimal fragments + 12 exact subtrees**. Each probe executed once, in frozen order, with no additions, replacements or retries.

| Probe | Source JSON Pointer (root = empty) | Constructor | Prefix traversal | Exception |
|---|---|---|---|---|
| D01 | `/properties/material_asks/items/properties/ask` | PASS | PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION | None in frozen prefix |
| D02 | `/properties/material_asks/items/properties/supporting_evidence_ranks/items` | PASS | PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION | None in frozen prefix |
| D03 | `/properties/material_asks/items/properties/supporting_evidence_ranks` | PASS | PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION | None in frozen prefix |
| D04 | `/properties/decision` | PASS | PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION | None in frozen prefix |
| D05 | `/oneOf/0/properties/decision` | PASS | PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION | None in frozen prefix |
| D06 | `/oneOf/0` | ERROR | NOT_STARTED | Unsupported type None |
| D07 | `/oneOf/0/properties/material_asks` | ERROR | NOT_STARTED | Unsupported type None |
| D08 | `/oneOf/2/anyOf/1/properties/material_asks` | ERROR | NOT_STARTED | Unsupported type None |
| D09 | `/properties/material_asks/items/allOf/0/then/properties/supporting_evidence_ranks` | ERROR | NOT_STARTED | Unsupported type None |
| D10 | `/properties/material_asks/items/allOf/0/else/properties/supporting_evidence_ranks` | ERROR | NOT_STARTED | Unsupported type None |
| D11 | `/properties/material_asks/items/allOf/0` | ERROR | NOT_STARTED | Unsupported type None |
| D12 | `/properties/material_asks/items` | ERROR | NOT_STARTED | Unsupported type None |
| D13 | `/oneOf/2` | ERROR | NOT_STARTED | Unsupported type None |
| D14 | `` | PASS | ERROR | Unsupported type None |
| T01 | `/properties/decision` | PASS | PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION | None in frozen prefix |
| T02 | `/oneOf/0/properties/decision` | PASS | PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION | None in frozen prefix |
| T03 | `/oneOf/0/properties/material_asks` | ERROR | NOT_STARTED | Unsupported type None |
| T04 | `/oneOf/1/properties/material_asks` | ERROR | NOT_STARTED | Unsupported type None |
| T05 | `/oneOf/2/anyOf/1/properties/material_asks` | ERROR | NOT_STARTED | Unsupported type None |
| T06 | `/properties/material_asks/items` | ERROR | NOT_STARTED | Unsupported type None |
| T07 | `/properties/material_asks/items/allOf/0` | ERROR | NOT_STARTED | Unsupported type None |
| T08 | `/properties/material_asks/items/allOf/0/if` | ERROR | NOT_STARTED | Unsupported type None |
| T09 | `/properties/material_asks/items/allOf/0/then/properties/supporting_evidence_ranks` | ERROR | NOT_STARTED | Unsupported type None |
| T10 | `/properties/material_asks/items/allOf/0/else/properties/supporting_evidence_ranks` | ERROR | NOT_STARTED | Unsupported type None |
| T11 | `/properties/material_asks` | PASS | ERROR | Unsupported type None |
| T12 | `/oneOf/2` | ERROR | NOT_STARTED | Unsupported type None |

19 probes reached the target exception: 17 during construction and 2 during traversal. Seven short prefixes encountered no target exception; these are not acceptance/qualification verdicts. All 26 incoming constructor argument hashes match the planned schema structures. All 26 input dictionaries retained their pre-call structure. No fixture was repaired. No exact subtree was modified.

## Helper-path result

The frozen G factory passes `JsonSchemaParser(json.loads(SCHEMA.read_bytes()), config=None)` directly. Raw bytes -> JSON parse -> unchanged in-memory structure -> library constructor -> internal JsonSchemaObject -> internal dispatch. Its traversal checks allowed-character membership before add_character. HELPER_PATH_RECEIPT.json preserves AST/source identity and historical error context. GD constructor-entry traces independently verify every diagnostic argument.

Result: **NO_SCHEMA_TRANSFORMATION_INTRODUCED_BY_PROJECT_HELPER**. The localized failure is in LMFE dispatch/merge behavior for these shapes. No project helper defect is established. Neither G nor any helper was repaired; lack of a helper defect does not imply support for the full V2 schema.

## Validation and boundaries

- Offline deterministic tests: **12/12 PASS**, before native diagnostics; no native parser imported in those tests.
- Pre/post package count: 36/36. Additions/removals/version/METADATA/RECORD drift: all 0.
- Both inventory SHA-256: `00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d`.
- Post-localization pip check: PASS.
- Installed LMFE Python-source hashes unchanged, alongside complete distribution inventory.
- Historical G plus F/FR receipt: 82 raw hashes verified; all historical tracked Git state unchanged outside new GD scope. This preserves E, XGrammar diagnostic/Attempt 2, R2/R1, V2/V1, runtime, B3/B2, benchmark, retriever, corpus and deterministic engine. No benchmark/private content inspection.
- Native diagnostic executions: 26. Retries: 0. G M1-M8 reruns: 0. Extended conformance probes: 0. Full V2 parser calls: 0.
- Tokenizer loads/prefix integration/prefix-tree construction/Qwen initialization/model initialization/generate/forward/semantic outputs: 0.
- DEVELOPMENT: 0; retrieval: 0; Phase 2H HELD_OUT: false; Phase 2G private HELDOUT: false.
- Fresh V2 semantic suite: NOT YET AUTHORED. V2 remains PRE_REGISTERED_NOT_EVALUATED.
- Observed import-time events: local socket.gethostname and cmd.exe /c "ver" only. No remote/DNS/connect/download activity observed. No forbidden calls or protected opens. No package mutation, monkeypatch or external service call.

## Source identities and owner review

Helper SHA-256: `36083e7a506a41082f8cbb62a82222169f970c66e3bdb7320c2bb75600bd616d`
Tests SHA-256: `415dafa6f90d6e667419bbdbb3df41346492c79946bad7fc867742f8a57f5ee7`

All artifact hashes are in ARTIFACT_SHA256.json (self-hash excluded to avoid circularity; reported in completion response). CHANGED_FILES.json contains the complete candidate. Git review contains only GD evidence, helper/tests and exact artifact -text entries; Python stays normal text. No wheels, caches, models, environment or private files are included.

No commit/tag. No repairs. No schema adaptation. No Transformers smoke or new decoder selection. Stop for owner review; any later engineering action requires separate authorization/preregistration.
