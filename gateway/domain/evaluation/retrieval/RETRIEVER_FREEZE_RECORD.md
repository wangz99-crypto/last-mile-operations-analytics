# Ranked retriever pre-heldout freeze record — Phase 2F

Freeze date: **2026-09-30**. Selected supplemental ranked retriever: **BGE embedding v0**.

This record freezes the existing Phase 2D implementation and measured configuration. Selection rationale and all three Development metric tables are in [RETRIEVER_SELECTION.md](RETRIEVER_SELECTION.md). No implementation, scoring rubric, threshold or query behavior is changed.

## Exact selected configuration

| Setting | Frozen value |
| --- | --- |
| Retrieval method | EMBEDDING_COSINE |
| Model | BAAI/bge-small-en-v1.5 |
| Exact model revision | 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a |
| Device | CPU |
| Corpus | 8 SOP documents / 25 verified stable sections / 1.0-demo |
| Section input | Readable document title + LF + readable section title + LF + section body |
| Query | Original question text exactly; no application-level transformation |
| Query instruction / prefix | None; empty prompt |
| Query rewriting | None |
| normalize_embeddings | true |
| Similarity | Normalized dot product / cosine |
| Embedding dimension | 384 |
| Minimum top cosine similarity | 0.30; below threshold abstains, equality is accepted |
| Blank query | ABSTAIN without encoding |
| top_k | 10 |
| Candidate filtering | All 25 sections; threshold applies to the top score for the whole response, with no per-result threshold |
| Tie breaking | Descending unrounded similarity, then ascending (policy_id, version, section_id) |
| Section chunking | None beyond the 25 stable sections |
| Additional ranked methods / fallback | None; no BM25 or RRF layer |

The exact Phase 2D configuration is reproduced below, including batch size, precision, normalization validation, CPU thread count and model-owned pooling. The model tokenizer/pooling and sequence-length limit remain unchanged. Natural identifiers in the original SOP body remain untouched; metadata IDs, filenames, Gold, rationales and added synonyms do not enter searchable text.

Future evaluation must explicitly request the exact revision recorded here, rather than resolve an unconstrained future main revision. The implementation is unchanged; this pins the snapshot already measured by Phase 2D. The recorded null retrieval_freeze_commit is intentional and will be filled by the eventual owner commit containing this record. The Phase 2E commit is the current baseline base, not the future freeze commit.

```json
{
  "freeze_date": "2026-09-30",
  "selected_ranked_retriever": "BGE embedding v0",
  "retrieval_method": "EMBEDDING_COSINE",
  "model_revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a",
  "embedding_dimension": 384,
  "development_receipt_sha256": "4f5ffc6c780419b31c2b810ccaa66bb39f1b06872266c13816ae06208e660e00",
  "phase_commits": {
    "phase_2c": "a81814d4478bbd0c1dffd98f0dce37988cd29031",
    "phase_2d": "212284b964b2ea867464574c66d9e587c4785231",
    "phase_2e": "df69b489b24f410946de35a3cbbc922b6f044e72"
  },
  "retrieval_freeze_commit": null,
  "retrieval_freeze_commit_status": "To be filled by the eventual owner commit containing this record; not the Phase 2E baseline commit.",
  "deterministic_engine_frozen_tag": "deterministic-engine-v0.1-pre-heldout",
  "deterministic_engine_frozen_commit": "a528023e64ef523ea91741d8574cc431e7bae8e3",
  "corpus": {
    "policy_bundle_id": "last-mile-exception-triage-demo",
    "policy_version": "1.0-demo",
    "document_count": 8,
    "section_count": 25,
    "canonical_identity": [
      "policy_id",
      "version",
      "section_id"
    ],
    "artifact_manifest_sha256": "093b763fadfaadf7859d758722e21160390edeb4d0a4e0ce18a97401efcba77f"
  },
  "configuration": {
    "abstention": {
      "also_abstain": [
        "blank query"
      ],
      "comparison": "top_score < threshold",
      "margin": null,
      "minimum_top_score": 0.3
    },
    "candidate_filter": "all sections; threshold applies to top score for the whole response",
    "cpu_threads": 1,
    "device": "cpu",
    "document_instruction": "",
    "encode_batch_size": 32,
    "encode_precision": "float32",
    "field_joiner": "LF",
    "model_id": "BAAI/bge-small-en-v1.5",
    "model_selection": "Owner-frozen repository-configured model; one model only",
    "normalize_embeddings": true,
    "pooling": "unmodified model snapshot configuration",
    "query_instruction": "",
    "query_transformation": "none; original question text",
    "retrieval_method": "EMBEDDING_COSINE",
    "score_meaning": "retrieval diagnostic; not confidence, probability, authority or business readiness",
    "searchable_fields": [
      "title",
      "section_title",
      "text"
    ],
    "section_count": 25,
    "similarity": "normalized dot product; math.fsum over unit vectors",
    "tie_breaking": "score descending, then (policy_id, version, section_id) ascending; no rounding",
    "top_k": 10,
    "vector_validation": "finite nonzero rows; L2 normalize in Python float precision"
  },
  "held_out_opened_during_selection": false,
  "post_baseline_tuning_performed": false
}
```

## Frozen Phase 2D runtime identity

These values are copied from the frozen Phase 2D RUN_MANIFEST.json, not inferred from the current machine or a new model run.

| Runtime field | Recorded value |
| --- | --- |
| Python | 3.12.10 |
| huggingface-hub | 0.36.2 |
| numpy | 2.5.3 |
| sentence-transformers | 3.0.1 |
| torch | 2.14.0 |
| transformers | 4.57.6 |
| Device | cpu |
| Embedding dimension | 384 |
| CPU threads | 1 |
| Maximum sequence length | 512 |
| Pooling | CLS token; unmodified model configuration |

Phase 2D recorded a request for main, resolved it to the exact revision above, pinned that load, and downloaded the recorded model files. This freeze retains that resolved revision; it does not authorize a new main resolution. No model was initialized or downloaded during Phase 2F. Dependency versions and model-file hashes identify the measured runtime; byte-identical embeddings across arbitrary runtimes are not claimed.

## Exact model-file SHA-256 from Phase 2D

| Model file | SHA-256 |
| --- | --- |
| 1_Pooling/config.json | d1caf60c96f5fba2157c0c26b76d80818fad6cf0b8eb5e73ec372ff9818eba5c |
| config.json | 094f8e891b932f2000c92cfc663bac4c62069f5d8af5b5278c4306aef3084750 |
| config_sentence_transformers.json | 940d5f50db195fa6e5e6a4f122c095f77880de259d74b14a65779ed48bdd7c56 |
| model.safetensors | 3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad |
| modules.json | 84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf |
| sentence_bert_config.json | 84e39fda68ccbff05bfa723ae9c0e70e23e2ec373b76e0f8c6e71af72a693cbf |
| special_tokens_map.json | b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3 |
| tokenizer.json | d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66 |
| tokenizer_config.json | 9261e7d79b44c8195c1cada2b453e55b00aeb81e907a6664974b4d7776172ab3 |
| vocab.txt | 07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3 |

## Selection source artifacts and SHA-256

All nine files below are tracked DEVELOPMENT-only evidence. Each results/report hash was verified against its own run manifest before this record was written. All runs share the frozen Development receipt above. The Phase 2D manifest verifies Phase 2C historical hashes; the Phase 2E manifest verifies both prior sets. Model and configuration identities were checked. Historical artifact bytes were not edited and real baselines were not rerun.

| Repository-relative artifact | SHA-256 |
| --- | --- |
| artifacts/retrieval_dev_embedding_baseline/DEVELOPMENT_REPORT.md | b79dd1551f76d16d4553774269d1496d1989f226e44b55b0a9511fe57fdaf93a |
| artifacts/retrieval_dev_embedding_baseline/DEVELOPMENT_RESULTS.json | 654747c85cfb2d18ebccc46c65583905e1b3a28a67be6ed041894ae193525407 |
| artifacts/retrieval_dev_embedding_baseline/RUN_MANIFEST.json | 030cac0e71b3dc262f9e6b669853b44650bfc38b014a8bbea8f1e475fe1d2a9d |
| artifacts/retrieval_dev_hybrid_rrf_baseline/DEVELOPMENT_REPORT.md | f711e9a732e5205d470c6cb50982e7fc21bb3427b7db200c98d43c8def79e22d |
| artifacts/retrieval_dev_hybrid_rrf_baseline/DEVELOPMENT_RESULTS.json | b5ab91a8067ecd60cbb1ff146ca70708fe03b5786d6b8bfd963bbf81921f7e0d |
| artifacts/retrieval_dev_hybrid_rrf_baseline/RUN_MANIFEST.json | 92fb8ee205929cabe1e1c3e18a926c997ba77f175517403407baeb19093e7860 |
| artifacts/retrieval_dev_lexical_baseline/DEVELOPMENT_REPORT.md | 891a4a3074e8152288672af3409950481dff634040fb5906ce3ef4f3f0b69f46 |
| artifacts/retrieval_dev_lexical_baseline/DEVELOPMENT_RESULTS.json | 353ecfa201a9edfd73e34c29d44053c9f6c3762a961f20313a43c8865f033977 |
| artifacts/retrieval_dev_lexical_baseline/RUN_MANIFEST.json | b51222774dd39ea0df24ae69a22844439841cecf0383851014f07ed1b733abe3 |

## Verified 25-section corpus identity

The active bundle is last-mile-exception-triage-demo, version 1.0-demo: 8 documents and exactly the 25 canonical identities below. Content hashes are the existing SectionStore hashes; the frozen policy artifact manifest checksum is recorded in the JSON metadata above. This is the same verified corpus used by Phase 2D and Phase 2E.

| Canonical identity (policy_id / version / section_id) | Content SHA-256 |
| --- | --- |
| SOP-01 / 1.0-demo / scope | 7ff50ba66d6de964fa0cef7384e411417bb9ddc01a4317b78a2d6ef2a47e4423 |
| SOP-01 / 1.0-demo / state-precedence | 1ecea461f89ccd2cd46f294b59c72cdc0a32d2afbb77cb6fd047c3f1f3938729 |
| SOP-01 / 1.0-demo / taxonomy | 569a93121de6264b1cdb23dea3c0c1da06bda56264bb2ac53510dfbb5d8f94fc |
| SOP-02 / 1.0-demo / late-boundaries | 2f6fa8647b7f737e40168c54ff1e9f2a6a0d4580a4b6240e5c5a8a9f22070172 |
| SOP-02 / 1.0-demo / late-escalate | 657f53921870e5267621149b236a02b4996a0b73e1753d9837959f312cbf5653 |
| SOP-02 / 1.0-demo / late-monitor | dff2dc2910aa5599706098ed16100658615999e82a96a18f9153c63b61c817ab |
| SOP-03 / 1.0-demo / scan-scope | 8c03da7dc4feb8e6d93753f36ed1f338b3e49349c939da6d038199513cb85c13 |
| SOP-03 / 1.0-demo / stale-escalate | 9fbb3508254ef320884bdfe6521d195e535ff1f9d4c017cd89c3e4817c1d40a8 |
| SOP-03 / 1.0-demo / stale-monitor | 9349f06368896747f43ca05122e6522188b715120a3e370633b48ea92dfe6f92 |
| SOP-04 / 1.0-demo / address-notices | 812950e28b26b73de16f3275b6f3e24ed910faa3ab26453d6cd5bf59514e1860 |
| SOP-04 / 1.0-demo / attempt-counting | 1c2b1e27e082ef5f54bf26e55a82d9752f42d6155a301e2d2ec27aa6a47b54dd |
| SOP-04 / 1.0-demo / repeated-attempts | 101811eb692e6d3f2c892a1d9d510674cf29204eb4f6a7613c9490d1a7d2905c |
| SOP-04 / 1.0-demo / single-attempt | 5ac5f5f297a0cab181843aea2ae48b1f1ee6a244cf065e1f8d630f325fa58fd9 |
| SOP-05 / 1.0-demo / attempt-address-evidence | 42445072a3d53692349e90f887d7b3cf1de86d4d201fffd14cd69c88e4a66e94 |
| SOP-05 / 1.0-demo / common-evidence | 1300d3a76dc0674b1ef29c08ab29bc210f9d494b1db48d11f3706b5dec3e5e68 |
| SOP-05 / 1.0-demo / late-evidence | 7046a97651a34415bd99b88f961b78c6a3de8665b314731cc22e335f6204d93d |
| SOP-05 / 1.0-demo / stale-evidence | 09d998430bae5729392b1dc7ef8448bad04161b3ff5822f151a8bfaecac4234b |
| SOP-06 / 1.0-demo / handoff-boundary | 6dec3f860f83b0d2e0eb2959c3501c8e299d7e0ad8731636ef7dfe62e52a21a5 |
| SOP-06 / 1.0-demo / handoff-fields | b72b0e6fd13bcec07a9a38c79ce448b7e9a4cc26f76f8d014e6714ae88ff353f |
| SOP-07 / 1.0-demo / data-conflicts | cc47a1a96b03b3c1a0d93723a9339c232888245f59eece16224bb0632bc592da |
| SOP-07 / 1.0-demo / missing-facts | 565fa200a2b48e8aa4956185fff15501bfaef2490790886eb709ee168eab2e38 |
| SOP-07 / 1.0-demo / missing-policy | d6ec6ec665358d9bf166a1f8284e0c9351d1dae5de138ff43aee93533f59e943 |
| SOP-08 / 1.0-demo / data-minimization | a787ced0f959e0cc8951dde567d5fa163381d03809322dbfba6d1696f7d02afe |
| SOP-08 / 1.0-demo / decision-record | 7578315d0a8faedd4fc2c5d63715ade662082adc13a9f6fdc1aa559de02cf5cf |
| SOP-08 / 1.0-demo / revision-history | cc8bd8e1437394b40084e3913595bdf8fc4172ee5b1d3241a955829ccdfd350a |

## Freeze boundary

> Any future change to the embedding model, model revision, query instruction, searchable fields, threshold, normalization, similarity, top-k evaluation depth, candidate filtering, tie-breaking, or retrieval method constitutes a new retriever revision and must not retroactively redefine this frozen configuration.

> The frozen retriever configuration was selected using only DEVELOPMENT results. Retrieval HELD_OUT remained unopened during method selection.

Exact required-section lookup remains authoritative for deterministic policy support. BGE is supplemental ranked context, and its score is not confidence, probability, policy authority, completeness or business readiness. BM25 and equal-weight RRF remain unchanged historical Development baselines.

All three baselines had negative correct abstention 0/1 and false support 1/1 on the single Development negative. Score threshold alone is not demonstrated to be a reliable scope/answerability detector; one negative is not a safety or production estimate. This known weakness remains deliberately unrepaired. No threshold adjustment, negative special-case, classifier, query rule, fallback or learned abstention is introduced.

No tuning followed the baseline evaluations. No HELD_OUT material was searched for, listed, copied, accessed, inferred or evaluated. This record ends before release of the held-out set. The owner may separately commit these records and create a pre-heldout tag after review; this task creates neither.
