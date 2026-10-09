# Attempt 2 synthetic semantic qualification

Outcome: **QUALIFICATION_FAILED**
Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**
Model: `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. CPU / FP32 / no quantization.
Base HEAD and runtime tag: `a36fda5958492ca326f944642fe252b5d41442b7` / answerability-semantic-runtime-v0.1-pre-qualification.
Clean pre-implementation status, historical tags, prompt/parser/registry, runtime,
28 dependencies and all 10 snapshot hashes were verified before execution.
All 146 previously frozen file hashes remain unchanged; benchmark hashing only.

One executable config and all synthetic cases were frozen and hashed before model
initialization. See INFERENCE_CONFIG.json for full effective settings and explicit
provider-schema mapping. Greedy / one beam / 4096 max new tokens / 600 seconds /
seed 0 / PROMPT_ONLY_STRICT_JSON / strict frozen parser / zero retries.
Every request was token-budget checked with the unchanged tokenizer/chat template.

Model initializations this attempt: 1 (historical BR: 1).
Primary records: 12; duplicate records: 3.
Real generate calls: 15; timeouts: 0.
Call infrastructure failures: 0.
Run-level infrastructure error: None.
Quality retries=0; infrastructure retries=0; model alternatives=0.

| Primary metric | Score |
| --- | --- |
| structured_output_validity | 7/12 |
| section_reference_validity | 0/12 |
| internal_consistency | 7/12 |
| binary_correctness | 0/12 |
| reason_code_correctness | 0/12 |
| critical_case_binary_correctness | 0/6 |

| Case | Frozen GateOutput | Binary correct | Reason correct | Parser error |
| --- | --- | --- | --- | --- |
| Q1 | None | False | False | invalid canonical section identity |
| Q2 | None | False | False | invalid canonical section identity |
| Q3 | None | False | False | invalid strict JSON output |
| Q4 | None | False | False | invalid strict JSON output |
| Q5 | None | False | False | invalid strict JSON output |
| Q6 | None | False | False | invalid canonical section identity |
| Q7 | None | False | False | invalid canonical section identity |
| Q8 | None | False | False | invalid canonical section identity |
| Q9 | None | False | False | invalid canonical section identity |
| Q10 | None | False | False | invalid strict JSON output |
| Q11 | None | False | False | invalid canonical section identity |
| Q12 | None | False | False | invalid strict JSON output |

Failed primary IDs: ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10', 'Q11', 'Q12'].
Determinism comparisons (diagnostic only):
```json
{
  "diagnostic_only": true,
  "qualification_requirement": false,
  "comparisons": [
    {
      "case_id": "Q2",
      "comparison_available": true,
      "raw_text_identical": true,
      "raw_utf8_bytes_identical": true,
      "both_parser_valid": false,
      "semantic_fields": null,
      "semantic_fields_identical": null
    },
    {
      "case_id": "Q7",
      "comparison_available": true,
      "raw_text_identical": true,
      "raw_utf8_bytes_identical": true,
      "both_parser_valid": false,
      "semantic_fields": null,
      "semantic_fields_identical": null
    },
    {
      "case_id": "Q11",
      "comparison_available": true,
      "raw_text_identical": true,
      "raw_utf8_bytes_identical": true,
      "both_parser_valid": false,
      "semantic_fields": null,
      "semantic_fields_identical": null
    }
  ]
}
```

Network/boundary observations:
```json
[
  {
    "allowed": true,
    "arguments": "()",
    "event": "socket.gethostname"
  },
  {
    "allowed": true,
    "arguments": "(<socket.socket fd=-1, family=0, type=0, proto=0>, 23, 1, 0)",
    "event": "socket.__new__"
  },
  {
    "allowed": true,
    "arguments": "(<socket.socket fd=1136, family=23, type=1, proto=0>, ('::1', 0))",
    "event": "socket.bind"
  }
]
```
No outbound model requests or downloads. Local socket capability probes, if any,
are recorded above; no external fallback. DEVELOPMENT semantic calls=0; retrieval=0.
Phase 2H HELD_OUT and Phase 2G private HELDOUT accessed=false. No real benchmark
question was parsed or transmitted. No DEVELOPMENT eligibility metrics computed.

Pre-generation tests: {'termination_test': 'spawned synthetic worker killed at short deadline; no model', 'tests': {'model_calls': 0, 'passed': 141, 'total': 141}, 'timeout_seconds': 600}. Post-result tests: {'total': 141, 'passed': 141, 'model_calls': 0}.
Saved raw-output parser results, primary scores, deterministic serialization and
duplicate comparisons reproduced identically without model calls. Only scheduled
calls appear in custody records; no repair, prompt edit, tuning or second pass.
The fake-worker test exercised forced timeout termination; absence of a real timeout
does not establish runtime bounds for arbitrary future input. These synthetic
results do not establish DEVELOPMENT or production performance.

| Artifact | SHA-256 |
| --- | --- |
| QUALIFICATION_PROTOCOL.md | `e69cd231d63346c49bebef7077a8645b90af1cbec80f6ba040267988168f5075` |
| INFERENCE_CONFIG.json | `4eeb39c086b9f0e60f10fc0ea0d03eeb67b401b0e3876854b8cc138b0b910db9` |
| SYNTHETIC_QUALIFICATION_SUITE.json | `b320a1af101f07d11a9fd42254c6b0c680a9b95ebcdff80de735c89f79e2c508` |
| SYNTHETIC_QUALIFICATION_RESULTS.json | `c6c6db9f3b5c9287acbbba8951520cfb12b2e912222b7192f2b62b14772f1a21` |
| RAW_MODEL_OUTPUTS.jsonl | `e86228c5f6bb80e3dd9e1083a8242558970fbacb96b70435acdc2747fa1a4b0a` |
| DETERMINISM_REPORT.json | `540992230c2636ed1ddfc958dcbc90cf72c19332eacfe7a1075502ef79e3dc9d` |
| QUALIFICATION_JOURNAL.jsonl | `c8754c489aac3709345a3e88669e5926e3ad692cfe0c5bcb3d647954fb81dd19` |

Journal is append-only and finalized; this report does not hash itself. The review
record hashes this report. Stop for owner review; no commit/tag/B3.2-C.
