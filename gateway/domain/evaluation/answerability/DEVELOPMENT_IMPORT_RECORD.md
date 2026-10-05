# Phase 2H-B1 DEVELOPMENT import record

Import verification date: 2026-10-04. This records custody only, not a candidate evaluation.

| Field | Verified value |
| --- | --- |
| Benchmark version | `answerability-benchmark-v0.1` |
| Owner benchmark status | `OWNER_REVIEWED / FROZEN` |
| Protocol tag | `answerability-protocol-v0.1-pre-benchmark` |
| Verified pre-change HEAD and protocol tag target | `347ce9f3ff37bd73f4750cde01562f0573a2b4ab` |
| Pre-change Git status | Empty |
| Source DEVELOPMENT manifest SHA-256 | `cae8a072192cad67b58e7d366afa9210972d672faa2e17047f2742e75a8499c2` |
| Imported DEVELOPMENT manifest SHA-256 | `cae8a072192cad67b58e7d366afa9210972d672faa2e17047f2742e75a8499c2` |
| Source and recomputed imported receipt | `9913c3028119f708a19ad762efda5f86b80b1f78c624eddbd632d6129e5b802d` |
| Receipt algorithm | `ANSWERABILITY_MANIFEST_RECEIPT_V1` |
| Frozen blueprint provenance, owner supplied; not opened for this import | `bd3bc55cda23adfdd2d6ec6de22188f993ce3c64516a446a3fb471b051a344bc` |
| Question count | 40, exactly AQ001 through AQ040 |
| Class counts | 20 ALLOW / 20 ABSTAIN |
| ALLOW support shape | 14 SINGLE_SECTION / 6 MULTI_SECTION |
| ABSTAIN reasons | 16 INSUFFICIENT_POLICY_SUPPORT / 4 UNRESOLVED_POLICY_CONTEXT |
| Hard negatives | 16 ABSTAIN |
| Review status | All 40 OWNER_REVIEWED |
| ALLOW document coverage | All eight SOPs |
| Custody verification | PASS |
| Source question bytes preserved | PASS, 40/40 |
| Source manifest bytes preserved | PASS |
| Phase 2H HELD_OUT accessed / imported | NO / NO |
| Phase 2G private evidence accessed | NO |
| BGE / BM25 / RRF run | NO / NO / NO |
| Real DEVELOPMENT retrieval or gate evaluated | NO |

The only private source reads for this import were the exact authorized
`DEVELOPMENT_MANIFEST.json` at the authoring workspace root and its 40 explicit
`development/AQnnn.json` entries resolved under the authorized `benchmark/`
root. No recursive authoring inventory, alternate split discovery, blueprint,
owner-review notes or unrelated authoring files were opened.

Before copying questions, the manifest's raw hash, exact entry IDs/paths,
regular-file status, path confinement, all 40 raw file hashes and aggregate
receipt passed. Absolute, drive-qualified, UNC, traversal, duplicate and
symlink/reparse paths are rejected. Questions were read as bytes for hashing;
question JSON was parsed only after the full custody check succeeded.

The imported manifest is `DEVELOPMENT_MANIFEST.json` beside this record.
Its unchanged paths resolve to `development/AQ001.json` through
`development/AQ040.json`. Binary exclusive-create writes preserved all bytes;
post-copy equality and a second imported custody verification both passed.
The receipt hashes the UTF-8 concatenation of ID-sorted records:
`question_id + TAB + filename + TAB + sha256 + LF`, including the final LF.

The root `.gitattributes` adds only 41 exact-path `-text` rules for this
manifest and these questions. `git check-attr` and filtered-versus-raw
`git hash-object` checks confirm Git preserves their bytes even with the
repository's `core.autocrlf=true`. No ignore policy was broadened.

Normal evaluation reads only this repository's pinned DEVELOPMENT copy.
Every load verifies the manifest hash, all question hashes, receipt, exact
inventory, schema, reviewed status, classes, reason distribution, support
shape, required subset, canonical active identities and empty ABSTAIN support.
Structural validation passed with 40 verified hashes, 20/20 classes and zero
retrieval or gate attempts. No actual-data baseline of any kind was executed.

The exact changed-file and SHA-256 inventory is
[DEVELOPMENT_HARNESS_SHA256.json](DEVELOPMENT_HARNESS_SHA256.json).
