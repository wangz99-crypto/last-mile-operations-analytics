"""One-shot synthetic qualification; frozen prompt/parser and offline CPU worker."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import ipaddress
import json
import multiprocessing
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest

from .answerability_contracts import ActiveBundle, GateInput, RankedEvidence
from .gates.semantic_gate import (
    RAW_ASSESSMENT_SCHEMA, SemanticOutputError, build_messages, canonical_json,
    parse_assessment, section_reference, validate_configuration,
)
from .semantic_transformers_runtime import (
    MODEL_REPOSITORY, MODEL_REVISION, RuntimeSpec, file_sha256, load_cpu_fp32,
    render_gate_input, require_context_capacity, verify_preregistration, verify_snapshot,
)

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'artifacts/answerability_semantic_model_v1_qualification_attempt2'
BR = ROOT / 'artifacts/answerability_semantic_runtime_v1_enablement'
HEAD = 'a36fda5958492ca326f944642fe252b5d41442b7'
INVENTORY_SHA = 'bd997774f25c307eb4421488607110f011592250e0bd82b2a096b3a7cf17b4fb'
CHAT_SHA = 'cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f'
PRIMARY = tuple(f'Q{i}' for i in range(1, 13))
REPEATS = ('Q2', 'Q7', 'Q11')
CRITICAL = ('Q3', 'Q4', 'Q7', 'Q8', 'Q11', 'Q12')
PLAN = tuple((q, 'PRIMARY') for q in PRIMARY) + tuple((q, 'DETERMINISM') for q in REPEATS)
SOURCE = Path(__file__).resolve()
TEST_SOURCE = ROOT / 'gateway/domain/tests/test_semantic_qualification_attempt2.py'
TEST_MODULES = (
    'gateway.domain.tests.test_semantic_transformers_runtime',
    'gateway.domain.tests.test_answerability_semantic_gate',
    'gateway.domain.tests.test_answerability_scoring',
    'gateway.domain.tests.test_answerability_evaluator_boundary',
    'gateway.domain.tests.test_semantic_qualification_attempt2',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, value):
    raw = canonical_json(value)
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return sha(raw)


def append_line(path, value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode() + b'\n'
    with Path(path).open('ab') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def journal(event, **details):
    path = OUT / 'QUALIFICATION_JOURNAL.jsonl'
    sequence = len(path.read_bytes().splitlines()) + 1
    append_line(path, {'sequence': sequence, 'utc': datetime.now(timezone.utc).isoformat(),
                       'event': event, 'details': details})
    print(event, details.get('case_id', ''), flush=True)


def journal_events():
    return [json.loads(line) for line in (OUT / 'QUALIFICATION_JOURNAL.jsonl').read_bytes().splitlines()]


def synthetic_suite():
    """Synthetic workshop policies; these labels are never transmitted to the worker."""
    bundle = ActiveBundle('last-mile-exception-triage-demo', '1.0-demo',
                          '2026-01-01T00:00:00Z', None, '0' * 64, '1' * 64)
    specifications = [
        ('single-section supported', 'Before using the sample dispenser, which lever must I lock?',
         [('dispenser', 'The sample dispenser may be used only after its blue lever is locked.')], 'ALLOW'),
        ('multi-section supported', 'What must I check before using a gauge, and where must I return it afterward?',
         [('gauge-check', 'Before using a gauge, check that its calibration sticker is current.'),
          ('gauge-return', 'After using a gauge, return it to cabinet M.')], 'ALLOW'),
        ('partial multi-part support', 'What check is required before gauge use, and what fee is charged for a failed check?',
         [('gauge-check', 'Before using a gauge, check that its calibration sticker is current. If the sticker has expired, set the gauge aside for inspection.')], 'INSUFFICIENT'),
        ('relevant-but-not-supportive', 'How many hours must a survey-device battery be charged before use?',
         [('battery-storage', 'Store survey-device batteries upright in the grey battery cupboard and record the shelf position.')], 'INSUFFICIENT'),
        ('external/common-knowledge temptation', 'How long should I boil water to sanitize a workshop measuring cup?',
         [('cup-storage', 'Place measuring cups on the clean-equipment shelf after washing. Cups awaiting washing go in the marked tray.')], 'INSUFFICIENT'),
        ('resolved-context insufficiency', 'What is the maximum time an instrument may remain in the inspection holding area?',
         [('inspection-hold', 'The active workshop procedure requires instruments awaiting inspection to remain in the holding area until an inspector releases them.')], 'INSUFFICIENT'),
        ('unresolved authority/version', 'How many seals does the governing workshop edition require on a dispatch container?',
         [('seal-editions', 'The workshop register lists both the Cedar edition and the Birch edition as effective for dispatch containers on the same date. It records no supersession or precedence between them.'),
          ('seal-counts', 'The Cedar edition requires four seals per dispatch container. The Birch edition requires six seals per dispatch container.')], 'UNRESOLVED'),
        ('unresolved applicability', 'May mobile bench Vega use the two-person lift procedure for the prism frame?',
         [('lift-scope', 'The two-person lift procedure for prism frames is authorized only for benches certified as Green-zone benches. Bench names do not indicate their zone. The supplied certification register contains no zone entry for mobile bench Vega.')], 'UNRESOLVED'),
        ('evidence synthesis', 'Does an amber-marked crate need two inspection signatures before release?',
         [('crate-groups', 'Every amber-marked crate belongs to handling group K.'),
          ('group-k-release', 'Before release, every handling group K crate must carry signatures from two different inspectors.')], 'ALLOW'),
        ('lexically weak paraphrase', 'Before wheeling the enclosure away, do I need to fasten its hinged cover?',
         [('cabinet-movement', 'Engage the lid latch before moving the cabinet on its casters.')], 'ALLOW'),
        ('high lexical-overlap false friend', 'May a visitor keep using a workshop visitor badge for twenty-one days?',
         [('visitor-badge-records', 'Retain workshop visitor badge scan records for twenty-one days after each visit, then delete those records.')], 'INSUFFICIENT'),
        ('unsupported extra material ask', 'Which card must accompany a loaned probe, and how many probes may one person borrow at once?',
         [('probe-loans', 'Each loaned probe must be accompanied by its blue calibration card. Return the card with the probe.')], 'INSUFFICIENT'),
    ]
    cases = []
    reasons = {'ALLOW': 'SUPPORTED_BY_ACTIVE_POLICY', 'INSUFFICIENT': 'INSUFFICIENT_POLICY_SUPPORT',
               'UNRESOLVED': 'UNRESOLVED_POLICY_CONTEXT'}
    for number, (category, question, sections, outcome) in enumerate(specifications, 1):
        evidence = tuple(RankedEvidence(rank, 'SOP-91', '1.0-demo', section,
                                       'Synthetic Workshop Manual', section.replace('-', ' ').title(),
                                       body, 0.9 - 0.1 * (rank - 1))
                         for rank, (section, body) in enumerate(sections, 1))
        gate = GateInput(question, evidence, bundle)
        cases.append({'case_id': f'Q{number}', 'category': category, 'gate_input': asdict(gate),
                      'expected': {'decision': 'ALLOW' if outcome == 'ALLOW' else 'ABSTAIN',
                                   'reason_code': reasons[outcome]}})
    return {'schema': 'synthetic-semantic-qualification-v1', 'origin': 'Original synthetic workshop cases; no benchmark questions',
            'bundle_note': 'Contract-compatible synthetic metadata and placeholder digests; no real policy lookup or retrieval',
            'cases': cases}


def gate_from_wire(value):
    require(type(value) is dict and set(value) == {'question', 'evidence', 'active_bundle'}, 'GateInput-only boundary')
    return GateInput(value['question'], tuple(RankedEvidence(**e) for e in value['evidence']),
                     ActiveBundle(**value['active_bundle']))


def execution_config():
    proposal = json.loads((BR / 'PROPOSED_INFERENCE_CONFIG.json').read_bytes())
    provider_contract = {
        'provider': 'LOCAL_TRANSFORMERS_DIRECT', 'model_identifier': MODEL_REPOSITORY,
        'model_revision': {'supported': True, 'value': MODEL_REVISION, 'unsupported_reason': None},
        'immutable_model_reference': {'kind': 'REVISION_SNAPSHOT', 'value': MODEL_REVISION,
                                     'provenance': 'Owner-frozen BR snapshot inventory'},
        'api_client': {'name': 'transformers', 'version': '4.57.6'}, 'temperature': 1.0,
        'top_p': {'supported': True, 'value': 1.0, 'unsupported_reason': None},
        'seed': {'supported': True, 'value': 0, 'unsupported_reason': None},
        'max_output_tokens': 4096, 'timeout_seconds': 600,
        'response_format': {'type': 'json_schema', 'schema_sha256': sha(canonical_json(RAW_ASSESSMENT_SCHEMA))},
        'retry_policy': {'quality_retries': 0, 'infrastructure_retries': 0,
                         'infrastructure_retry_authorization': 'NOT_AUTHORIZED'},
    }
    config = {
        'schema': 'local-synthetic-qualification-execution-v1', 'candidate': 'SEMANTIC_MATERIAL_SUPPORT_V1',
        'repository': MODEL_REPOSITORY, 'revision': MODEL_REVISION, 'device': 'cpu', 'dtype': 'float32',
        'quantization': 'NONE', 'local_files_only': True, 'offline': True, 'do_sample': False,
        'num_beams': 1, 'max_new_tokens': 4096, 'timeout_seconds': 600, 'context_limit': 32768,
        'temperature': 'NOT_APPLICABLE_UNDER_GREEDY_DECODING', 'top_p': 'NOT_APPLICABLE_UNDER_GREEDY_DECODING',
        'seed': 0, 'seed_note': 'torch.manual_seed(0); not claimed to control greedy decoding',
        'structured_output_mode': 'PROMPT_ONLY_STRICT_JSON', 'quality_retry': 'FORBIDDEN',
        'infrastructure_retry_count': 0, 'generation_config': proposal['full_effective_generation_config'],
        'frozen_provider_contract_mapping': provider_contract,
        'mapping_note': 'response_format specifies strict post-generation validation, not native schema enforcement; numeric temperature/top_p are inert library values under greedy decoding',
        'chat_template_sha256': CHAT_SHA, 'inventory_sha256': INVENTORY_SHA,
        'proposal_sha256': file_sha256(BR / 'PROPOSED_INFERENCE_CONFIG.json'),
        'threads': 4, 'interop_threads': 1, 'deterministic_algorithms': True,
        'budget': {'primary': list(PRIMARY), 'determinism': list(REPEATS), 'critical': list(CRITICAL)},
        'runner_sha256': file_sha256(SOURCE), 'test_source_sha256': file_sha256(TEST_SOURCE),
    }
    validate_execution_config(config)
    return config


def validate_execution_config(config):
    expected = {'repository': MODEL_REPOSITORY, 'revision': MODEL_REVISION, 'device': 'cpu',
                'dtype': 'float32', 'quantization': 'NONE', 'local_files_only': True, 'offline': True,
                'do_sample': False, 'num_beams': 1, 'max_new_tokens': 4096, 'timeout_seconds': 600,
                'context_limit': 32768, 'seed': 0, 'structured_output_mode': 'PROMPT_ONLY_STRICT_JSON',
                'quality_retry': 'FORBIDDEN', 'infrastructure_retry_count': 0, 'threads': 4,
                'interop_threads': 1, 'deterministic_algorithms': True, 'chat_template_sha256': CHAT_SHA,
                'temperature': 'NOT_APPLICABLE_UNDER_GREEDY_DECODING',
                'top_p': 'NOT_APPLICABLE_UNDER_GREEDY_DECODING'}
    for key, value in expected.items():
        require(key in config and type(config[key]) is type(value) and config[key] == value, 'Execution configuration mismatch: ' + key)
    validate_configuration(config['frozen_provider_contract_mapping'])
    gen = config['generation_config']
    for key in ('do_sample', 'num_beams', 'max_new_tokens'):
        require(gen[key] == config[key], 'Generation config mismatch: ' + key)
    require(sha(canonical_json(gen)) == 'b4180c37cc8c648477b1adced732e8bd8039170a95c053231226c2ba20b4d775', 'Frozen full generation config mismatch')
    require(config['budget'] == {'primary': list(PRIMARY), 'determinism': list(REPEATS), 'critical': list(CRITICAL)}, 'Call budget mismatch')


def check_frozen_inputs():
    events = journal_events()
    require(events[0]['event'] == 'PRECONDITION_VERIFIED' and events[0]['details']['git_status'] == '', 'Missing clean precondition')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == HEAD, 'HEAD changed')
    for name, digest in events[0]['details']['protected_sha256'].items():
        require(not any(s in name.lower() for s in ('heldout', 'held_out')), 'Private path forbidden')
        require(file_sha256(ROOT / name) == digest, 'Frozen historical file changed: ' + name)
    verify_preregistration(ROOT)


def require_frozen_ready(events, suite_raw, config_raw):
    for name, raw in [('QUALIFICATION_SUITE_FROZEN', suite_raw), ('INFERENCE_CONFIG_FROZEN', config_raw)]:
        matches = [e for e in events if e['event'] == name]
        require(len(matches) == 1 and matches[0]['details']['sha256'] == sha(raw), 'Missing/mismatched freeze: ' + name)
    require(any(e['event'] == 'TIMEOUT_WORKER_VERIFIED' for e in events), 'Tests must pass before initialization')
    require(not any(e['event'] in ('EXECUTION_STARTED', 'MODEL_INITIALIZED', 'MODEL_INITIALIZATION_ATTEMPTED') for e in events), 'Refuse execution restart')


class CallBudget:
    def __init__(self):
        self.position = 0

    def claim(self, case_id, kind):
        require(self.position < len(PLAN) and PLAN[self.position] == (case_id, kind), 'Unregistered call or retry')
        self.position += 1


def blocked_path(path):
    name = os.fsdecode(path).lower().replace('\\', '/')
    return any(s in name for s in ('heldout', 'held_out', '/answerability/development/',
        '/answerability_dev_bge_evidence_v0/', '/answerability_dev_gate_baselines_v0/',
        '/retrieval/development/', '/phase2d-model/'))


def network_allowed(event, args):
    if event in ('socket.__new__', 'socket.gethostname'):
        return True
    if event == 'socket.bind':
        address = args[1]
        try:
            return isinstance(address, tuple) and ipaddress.ip_address(address[0]).is_loopback
        except ValueError:
            return False
    return False


def install_guards(notify=lambda value: None, no_model=False):
    class ImportGuard:
        def find_spec(self, fullname, path=None, target=None):
            forbidden = fullname.startswith('gateway.domain.retrieval')
            forbidden |= no_model and fullname.split('.')[0] in {'torch', 'transformers', 'huggingface_hub', 'sentence_transformers', 'openai', 'anthropic'}
            if forbidden:
                raise RuntimeError('Forbidden model/retrieval import: ' + fullname)
    sys.meta_path.insert(0, ImportGuard())

    def audit(event, args):
        if event.startswith('socket.'):
            allowed = not no_model and network_allowed(event, args)
            notify({'event': event, 'arguments': repr(args), 'allowed': allowed})
            if not allowed:
                raise RuntimeError('Outbound network forbidden: ' + event)
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)) and blocked_path(args[0]):
            notify({'event': 'FORBIDDEN_FILE_ACCESS', 'path': os.fsdecode(args[0]), 'allowed': False})
            raise RuntimeError('Real benchmark/private data access forbidden')
    sys.addaudithook(audit)


def receive_with_timeout(connection, process, seconds, event_handler=lambda event: None):
    """A parent-owned deadline; timeout kills the worker, never starts a replacement."""
    deadline = time.monotonic() + seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not connection.poll(max(0, remaining)):
            process.terminate()
            process.join(5)
            if process.is_alive():
                process.kill()
                process.join(5)
            raise TimeoutError('Worker exceeded fixed deadline; no retry')
        message = connection.recv()
        if message['type'] in ('network', 'initialization_attempted', 'generation_started'):
            event_handler(message)
            continue
        return message


def worker(connection, config, snapshot_path):
    """Receives only GateInput payloads, never case IDs or expected outputs."""
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                      TOKENIZERS_PARALLELISM='false')
    install_guards(lambda event: connection.send({'type': 'network', 'details': event}))
    try:
        validate_execution_config(config)
        require(sys.platform == 'win32' and sys.version_info[:3] == (3, 12, 10), 'Frozen Windows/Python runtime required')
        for line in (BR / 'DEPENDENCY_RECEIPT.txt').read_text().splitlines():
            package, version = line.split('==')
            require(importlib.metadata.version(package) == version, 'Dependency mismatch: ' + package)
        import torch
        from transformers import AutoModelForCausalLM, GenerationConfig
        from unittest.mock import patch
        original = AutoModelForCausalLM.from_pretrained

        def tracked_load(*args, **kwargs):
            connection.send({'type': 'initialization_attempted'})
            return original(*args, **kwargs)

        spec = RuntimeSpec(MODEL_REPOSITORY, MODEL_REVISION, snapshot_path, 'cpu', 'float32', None)
        with patch.object(AutoModelForCausalLM, 'from_pretrained', tracked_load):
            model, tokenizer, model_config, receipt = load_cpu_fp32(spec, BR / 'MODEL_FILE_INVENTORY.json', INVENTORY_SHA)
        require(sha(tokenizer.chat_template.encode()) == CHAT_SHA, 'Chat template mismatch')
        require(model_config.max_position_embeddings == 32768, 'Context limit changed')
        gen_config = GenerationConfig.from_dict(config['generation_config'])
        require(canonical_json(gen_config.to_dict()) == canonical_json(config['generation_config']), 'Effective generation settings changed')
        forwards = [0]

        def count_forward(module, args):
            forwards[0] += 1

        model.register_forward_pre_hook(count_forward)
        connection.send({'type': 'ready', 'receipt': receipt})
        for ordinal in range(15):
            request = connection.recv()
            if request is None:
                break
            gate = gate_from_wire(request)
            ids = render_gate_input(tokenizer, gate)
            margin = require_context_capacity(len(ids), config['max_new_tokens'], config['context_limit'])
            connection.send({'type': 'prepared', 'input_tokens': len(ids), 'token_ids_sha256': sha(canonical_json(ids)), 'context_margin': margin})
            require(connection.recv() == 'GENERATE_ONCE', 'Explicit one-call command required')
            tensors = torch.tensor([ids], dtype=torch.long, device='cpu')
            before_forwards = forwards[0]
            start = time.monotonic()
            connection.send({'type': 'generation_started', 'ordinal': ordinal + 1})
            with torch.inference_mode():
                output = model.generate(input_ids=tensors, attention_mask=torch.ones_like(tensors), generation_config=gen_config)
            tokens = output[0, len(ids):].tolist()
            raw = tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            eos = gen_config.eos_token_id if isinstance(gen_config.eos_token_id, list) else [gen_config.eos_token_id]
            connection.send({'type': 'result', 'raw_text': raw, 'raw_output_byte_length': len(raw.encode('utf-8')),
                             'generated_token_ids': tokens, 'generated_token_count': len(tokens),
                             'elapsed_seconds': time.monotonic() - start, 'forward_calls': forwards[0] - before_forwards,
                             'termination_status': 'EOS' if tokens and tokens[-1] in eos else 'MAX_NEW_TOKENS' if len(tokens) == config['max_new_tokens'] else 'OTHER_STOP'})
        connection.close()
    except BaseException as exc:
        try:
            connection.send({'type': 'infrastructure_error', 'error_type': type(exc).__name__, 'message': str(exc)})
        finally:
            connection.close()


def assess(raw, gate):
    """Diagnostic facets never emit GateOutput; only the frozen parser can do so."""
    result = {'structured_output_validity': False, 'section_reference_validity': False,
              'internal_consistency': False, 'parser_valid': False, 'parser_error': None,
              'assessment': None, 'gate_output': None}
    try:
        parsed = parse_assessment(raw, gate)
        result.update(parser_valid=True, assessment=asdict(parsed), gate_output=asdict(parsed.gate_output()))
    except (SemanticOutputError, ValueError, TypeError) as exc:
        result['parser_error'] = str(exc)
    try:
        def pairs(items):
            value = {}
            for key, item in items:
                require(key not in value, 'duplicate key')
                value[key] = item
            return value
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        require(type(value) is dict and set(value) == {'material_asks', 'policy_context_status', 'decision', 'reason_code'}, 'shape')
        asks = value['material_asks']
        require(type(asks) is list and bool(asks), 'asks')
        require(value['decision'] in ('ALLOW', 'ABSTAIN') and value['reason_code'] in ('SUPPORTED_BY_ACTIVE_POLICY', 'INSUFFICIENT_POLICY_SUPPORT', 'UNRESOLVED_POLICY_CONTEXT') and value['policy_context_status'] in ('RESOLVED', 'UNRESOLVED'), 'enums')
        for ask in asks:
            require(type(ask) is dict and set(ask) == {'ask', 'support_status', 'supporting_section_ids'}, 'ask shape')
            require(type(ask['ask']) is str and bool(ask['ask'].strip()) and ask['support_status'] in ('SUPPORTED', 'UNSUPPORTED', 'CONTEXT_UNRESOLVED'), 'ask value')
            refs = ask['supporting_section_ids']
            require(type(refs) is list and all(type(ref) is str for ref in refs) and len(refs) == len(set(refs)), 'refs shape')
        result['structured_output_validity'] = True
        supplied = {section_reference(e) for e in gate.evidence}
        result['section_reference_validity'] = all(
            (ask['support_status'] != 'SUPPORTED' or bool(ask['supporting_section_ids']))
            and all(ref in supplied for ref in ask['supporting_section_ids']) for ask in asks)
        statuses = {ask['support_status'] for ask in asks}
        decision, reason, context = value['decision'], value['reason_code'], value['policy_context_status']
        result['internal_consistency'] = bool(
            (decision == 'ALLOW' and reason == 'SUPPORTED_BY_ACTIVE_POLICY' and context == 'RESOLVED' and statuses == {'SUPPORTED'})
            or (decision == 'ABSTAIN' and reason == 'INSUFFICIENT_POLICY_SUPPORT' and context == 'RESOLVED' and 'UNSUPPORTED' in statuses and 'CONTEXT_UNRESOLVED' not in statuses)
            or (decision == 'ABSTAIN' and reason == 'UNRESOLVED_POLICY_CONTEXT' and (context == 'UNRESOLVED' or 'CONTEXT_UNRESOLVED' in statuses)))
    except (ValueError, TypeError, KeyError):
        pass
    require(result['parser_valid'] == all(result[k] for k in ('structured_output_validity', 'section_reference_validity', 'internal_consistency')), 'Diagnostic/frozen-parser disagreement')
    return result


def score(suite, records):
    expected = {c['case_id']: c for c in suite['cases']}
    require(tuple(expected) == PRIMARY, 'Suite inventory mismatch')
    seen = [(r['case_id'], r['attempt_type']) for r in records]
    require(seen == list(PLAN[:len(seen)]), 'Unauthorized, duplicate, or missing call order')
    items = []
    for record in records:
        c = expected[record['case_id']]
        a = assess(record['raw_text'], gate_from_wire(c['gate_input'])) if record['raw_text'] is not None else {
            'structured_output_validity': False, 'section_reference_validity': False, 'internal_consistency': False,
            'parser_valid': False, 'parser_error': record['termination_status'], 'assessment': None, 'gate_output': None}
        a.update(case_id=record['case_id'], attempt_type=record['attempt_type'])
        a['binary_correctness'] = a['parser_valid'] and a['gate_output']['decision'] == c['expected']['decision']
        a['reason_code_correctness'] = a['parser_valid'] and a['gate_output']['reason_code'] == c['expected']['reason_code']
        items.append(a)
    primary = [a for a in items if a['attempt_type'] == 'PRIMARY']
    metrics = {k: {'numerator': sum(a[k] for a in primary), 'denominator': 12} for k in
               ('structured_output_validity', 'section_reference_validity', 'internal_consistency', 'binary_correctness', 'reason_code_correctness')}
    metrics['critical_case_binary_correctness'] = {'numerator': sum(a['binary_correctness'] for a in primary if a['case_id'] in CRITICAL), 'denominator': 6}
    infrastructure = [r for r in records if r['termination_status'] in ('TIMEOUT', 'INFRASTRUCTURE_ERROR', 'TOKEN_BUDGET_REJECTED')]
    complete = len(records) == 15 and not infrastructure
    accepted = complete and all(metrics[k]['numerator'] >= n for k, n in (
        ('structured_output_validity', 12), ('section_reference_validity', 12), ('internal_consistency', 12),
        ('binary_correctness', 11), ('reason_code_correctness', 11), ('critical_case_binary_correctness', 6)))
    outcome = 'QUALIFICATION_INCOMPLETE' if not complete else 'QUALIFIED' if accepted else 'QUALIFICATION_FAILED'
    return {'outcome': outcome, 'metrics': metrics, 'cases': items,
            'primary_count': len(primary), 'determinism_count': len(items) - len(primary),
            'failed_primary_case_ids': [a['case_id'] for a in primary if not (a['parser_valid'] and a['binary_correctness'] and a['reason_code_correctness'])],
            'infrastructure_failure_count': len(infrastructure), 'timeout_count': sum(r['termination_status'] == 'TIMEOUT' for r in records)}


def determinism(results, records):
    comparisons = []
    for q in REPEATS:
        items = [a for a in results['cases'] if a['case_id'] == q]
        raw = [a for a in records if a['case_id'] == q]
        comparison = {'case_id': q, 'comparison_available': len(items) == 2}
        if len(items) == 2:
            comparison['raw_text_identical'] = raw[0]['raw_text'] == raw[1]['raw_text']
            comparison['raw_utf8_bytes_identical'] = raw[0]['raw_text'] is not None and raw[1]['raw_text'] is not None and raw[0]['raw_text'].encode() == raw[1]['raw_text'].encode()
            comparison['both_parser_valid'] = all(a['parser_valid'] for a in items)
            if comparison['both_parser_valid']:
                x, y = (a['assessment'] for a in items)
                agreement = {key: x[key] == y[key] for key in ('decision', 'reason_code', 'policy_context_status')}
                agreement['support_status_pattern'] = [a['support_status'] for a in x['material_asks']] == [a['support_status'] for a in y['material_asks']]
                agreement['supporting_section_identities'] = [sorted(a['supporting_section_ids']) for a in x['material_asks']] == [sorted(a['supporting_section_ids']) for a in y['material_asks']]
                comparison.update(semantic_fields=agreement, semantic_fields_identical=all(agreement.values()))
            else:
                comparison.update(semantic_fields=None, semantic_fields_identical=None)
        comparisons.append(comparison)
    return {'diagnostic_only': True, 'qualification_requirement': False, 'comparisons': comparisons}


def run_tests():
    suite = unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    require(result.wasSuccessful(), 'Pre/post unit tests failed')
    require(not {'torch', 'transformers', 'huggingface_hub', 'sentence_transformers'}.intersection(sys.modules), 'Tests loaded model libraries')
    return {'total': result.testsRun, 'passed': result.testsRun, 'model_calls': 0}


def prepare():
    check_frozen_inputs()
    require(len(journal_events()) == 4, 'Preparation already started; refuse overwrite')
    config = execution_config()
    suite = synthetic_suite()
    for case in suite['cases']:
        build_messages(gate_from_wire(case['gate_input']))
    config_sha = write_new(OUT / 'INFERENCE_CONFIG.json', config)
    journal('INFERENCE_CONFIG_FROZEN', sha256=config_sha)
    suite_sha = write_new(OUT / 'SYNTHETIC_QUALIFICATION_SUITE.json', suite)
    journal('QUALIFICATION_SUITE_FROZEN', sha256=suite_sha, primary_count=12, determinism_count=3)
    protocol = '''# Attempt 2 synthetic semantic qualification protocol

Status: CANDIDATE_AWAITING_OWNER_REVIEW. One offline CPU/FP32 Qwen snapshot,
one frozen canonical prompt/parser, no DEVELOPMENT, no retrieval, no private data.
Twelve synthetic workshop cases Q1-Q12, followed by Q2/Q7/Q11 once each.
Expectations and synthetic categories remain evaluator-only. The worker receives
only contract-compatible GateInput. No case IDs, categories or labels enter messages.

The exact suite/config and runner/test source hashes are bound before model load.
Structured validity, supplied-reference validity and internal consistency each
require 12/12; binary and reason correctness each require >=11/12; critical binary
Q3/Q4/Q7/Q8/Q11/Q12 requires 6/6. Invalid parser output never becomes ABSTAIN.
Diagnostic shape/reference/consistency checks cannot emit a GateOutput; the frozen
parser alone does so. Binary/reason correctness requires a valid frozen parse.
All primary cases retain denominator 12; incomplete runs have no capability verdict.
Duplicates are diagnostic only, never extra accuracy cases or a new eligibility rule.

A persistent isolated spawned worker loads the model once. The parent imposes a
600-second deadline per preparation/generation operation, terminates a timed-out
worker, preserves completed raw outputs, and stops with QUALIFICATION_INCOMPLETE.
No worker replacement, infrastructure retry, quality retry or second pass is allowed.
Per-request exact chat-template tokenization checks input + 4096 against 32768;
the frozen helper conservatively requires positive remaining margin. No truncation.
Startup also has a 600-second infrastructure deadline, separately identified.

Generation is greedy, one beam, max_new_tokens=4096, seed 0 in the frozen runtime.
The full proposed GenerationConfig is used without scientific changes. Inert library
temperature/top_p values are 1.0; their scientific treatment is not applicable to
greedy decoding. PROMPT_ONLY_STRICT_JSON is strict parser post-validation, not native
constrained decoding. The original provider-oriented configuration is explicitly
mapped without changing its frozen schema. No generation/output repair is allowed.

Raw text is tokenizer.decode(new tokens, skip_special_tokens=True,
clean_up_tokenization_spaces=False), with all generated token IDs separately retained.
Raw UTF-8 byte length/hash, token counts, request/config hashes, duration, stop status,
strict parser result and GateOutput are recorded once per call and fsynced immediately.
EOS and output-limit stops are distinguished. A transport/timeout failure has null
raw text and unknown unavailable token counts; no fabricated output is substituted.

Outbound socket operations and benchmark/private file reads are blocked and recorded.
Socket construction, hostname reading and loopback-only bind probes are allowed.
No network fallback/download/package installation is authorized. Historic files are
hash-checked only, outside model execution; no benchmark question is parsed.
Artifacts refuse overwrite; the journal/raw custody files append only. Post-run
reproduction uses saved raw bytes and the frozen parser, never another model call.
Stop after artifacts, hash validation and non-model tests; do not commit or tag.
'''
    with (OUT / 'QUALIFICATION_PROTOCOL.md').open('x', encoding='utf-8', newline='\n') as f:
        f.write(protocol)


def execute():
    check_frozen_inputs()
    suite_raw = (OUT / 'SYNTHETIC_QUALIFICATION_SUITE.json').read_bytes()
    config_raw = (OUT / 'INFERENCE_CONFIG.json').read_bytes()
    require_frozen_ready(journal_events(), suite_raw, config_raw)
    config, suite = json.loads(config_raw), json.loads(suite_raw)
    validate_execution_config(config)
    require(config['runner_sha256'] == file_sha256(SOURCE) and config['test_source_sha256'] == file_sha256(TEST_SOURCE), 'Runner/test changed after freeze')
    require(tuple(c['case_id'] for c in suite['cases']) == PRIMARY, 'Suite IDs changed')
    require(not (OUT / 'RAW_MODEL_OUTPUTS.jsonl').exists(), 'Raw outputs already exist')
    (OUT / 'RAW_MODEL_OUTPUTS.jsonl').touch(exist_ok=False)
    inv = json.loads((BR / 'MODEL_FILE_INVENTORY.json').read_bytes())
    spec = RuntimeSpec(MODEL_REPOSITORY, MODEL_REVISION, inv['snapshot_path'], 'cpu', 'float32', None)
    verify_snapshot(spec, BR / 'MODEL_FILE_INVENTORY.json', INVENTORY_SHA)
    journal('EXECUTION_STARTED', suite_sha256=sha(suite_raw), config_sha256=sha(config_raw), retries=0)
    ctx = multiprocessing.get_context('spawn')
    parent, child = ctx.Pipe()
    process = ctx.Process(target=worker, args=(child, config, spec.snapshot_path), daemon=True)
    counts = {'model_initializations': 0, 'generate_calls': 0, 'network_events': [], 'fatal_error': None}

    def event(message):
        if message['type'] == 'network':
            counts['network_events'].append(message['details'])
            journal('SOCKET_OR_BOUNDARY_EVENT', observation=message['details'])
        elif message['type'] == 'initialization_attempted':
            counts['model_initializations'] += 1
            journal('MODEL_INITIALIZATION_ATTEMPTED', count=counts['model_initializations'])
        elif message['type'] == 'generation_started':
            counts['generate_calls'] += 1
            journal('GENERATE_INVOKED', ordinal=message['ordinal'])

    budget = CallBudget()
    active_record = None
    try:
        process.start()
        child.close()
        loaded = receive_with_timeout(parent, process, 600, event)
        require(loaded['type'] == 'ready', repr(loaded))
        journal('MODEL_INITIALIZED', initialization_count=counts['model_initializations'], receipt=loaded['receipt'])
        cases = {c['case_id']: c for c in suite['cases']}
        journal('PRIMARY_QUALIFICATION_STARTED', suite_sha256=sha(suite_raw), config_sha256=sha(config_raw))
        for index, (case_id, kind) in enumerate(PLAN):
            if index == 12:
                journal('PRIMARY_QUALIFICATION_COMPLETED', calls=12)
                journal('DETERMINISM_CHECK_STARTED', case_ids=list(REPEATS))
            budget.claim(case_id, kind)
            gate = gate_from_wire(cases[case_id]['gate_input'])
            messages = build_messages(gate)
            active_record = {'case_id': case_id, 'attempt_type': kind, 'config_sha256': sha(config_raw),
                             'request_sha256': sha(canonical_json({'messages': messages, 'config_sha256': sha(config_raw), 'chat_template_sha256': CHAT_SHA})),
                             'input_token_count': None, 'raw_text': None, 'raw_output_byte_length': None,
                             'generated_token_count': None, 'elapsed_seconds': None, 'termination_status': 'INFRASTRUCTURE_ERROR',
                             'generation_invoked': False}
            journal('CALL_PREPARATION_STARTED', case_id=case_id, attempt_type=kind, request_sha256=active_record['request_sha256'])
            parent.send(asdict(gate))
            prepared = receive_with_timeout(parent, process, 600, event)
            require(prepared['type'] == 'prepared', repr(prepared))
            active_record.update(input_token_count=prepared['input_tokens'], input_token_ids_sha256=prepared['token_ids_sha256'], context_margin=prepared['context_margin'])
            start = time.monotonic()
            before_calls = counts['generate_calls']
            parent.send('GENERATE_ONCE')
            try:
                response = receive_with_timeout(parent, process, 600, event)
            finally:
                active_record['generation_invoked'] = counts['generate_calls'] > before_calls
                active_record['elapsed_seconds'] = time.monotonic() - start
            require(response['type'] == 'result', repr(response))
            active_record.update({k: v for k, v in response.items() if k != 'type'})
            active_record['raw_output_sha256'] = sha(active_record['raw_text'].encode())
            active_record['parser_result'] = assess(active_record['raw_text'], gate)
            append_line(OUT / 'RAW_MODEL_OUTPUTS.jsonl', active_record)
            journal('CALL_COMPLETED', case_id=case_id, attempt_type=kind, termination_status=active_record['termination_status'],
                    generated_tokens=active_record['generated_token_count'], parser_valid=active_record['parser_result']['parser_valid'],
                    raw_output_sha256=active_record['raw_output_sha256'])
            active_record = None
        journal('DETERMINISM_CHECK_COMPLETED', calls=3)
        process.join(10)
    except BaseException as exc:
        counts['fatal_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        if active_record is not None:
            active_record['termination_status'] = 'TIMEOUT' if isinstance(exc, TimeoutError) else 'INFRASTRUCTURE_ERROR'
            active_record['infrastructure_error'] = counts['fatal_error']
            append_line(OUT / 'RAW_MODEL_OUTPUTS.jsonl', active_record)
        journal('EXECUTION_INCOMPLETE', **counts['fatal_error'])
    finally:
        if process.is_alive():
            process.terminate()
            process.join(5)
        parent.close()
    journal('EXECUTION_ENDED', **counts)


def reproduce():
    suite = json.loads((OUT / 'SYNTHETIC_QUALIFICATION_SUITE.json').read_bytes())
    config_sha = file_sha256(OUT / 'INFERENCE_CONFIG.json')
    records = [json.loads(line) for line in (OUT / 'RAW_MODEL_OUTPUTS.jsonl').read_bytes().splitlines()]
    for record in records:
        case = next(c for c in suite['cases'] if c['case_id'] == record['case_id'])
        gate = gate_from_wire(case['gate_input'])
        require(record['config_sha256'] == config_sha, 'Per-call config hash mismatch')
        request = {'messages': build_messages(gate), 'config_sha256': config_sha, 'chat_template_sha256': CHAT_SHA}
        require(record['request_sha256'] == sha(canonical_json(request)), 'Per-call request hash mismatch')
        if record['raw_text'] is not None:
            require(record['raw_output_sha256'] == sha(record['raw_text'].encode()), 'Raw output hash mismatch')
            require(record['raw_output_byte_length'] == len(record['raw_text'].encode()), 'Raw byte length mismatch')
            require(record['generated_token_count'] == len(record['generated_token_ids']), 'Generated token count mismatch')
            require(canonical_json(record['parser_result']) == canonical_json(assess(record['raw_text'], gate)), 'Saved parser result mismatch')
            require(record['generation_invoked'] is True, 'Missing generation receipt')
            require_context_capacity(record['input_token_count'], 4096, 32768)
    results = score(suite, records)
    return results, determinism(results, records), records


def finalize():
    check_frozen_inputs()
    require(any(e['event'] == 'EXECUTION_ENDED' for e in journal_events()), 'Execution has not ended')
    require(not any(e['event'] == 'ARTIFACTS_WRITTEN' for e in journal_events()), 'Finalization already completed')
    results, duplicate_report, records = reproduce()
    execution = next(e['details'] for e in journal_events() if e['event'] == 'EXECUTION_ENDED')
    if results['outcome'] != 'QUALIFICATION_INCOMPLETE':
        require(execution['model_initializations'] == 1 and execution['generate_calls'] == 15, 'Initialization/generation count integrity violation')
        require(execution['fatal_error'] is None and all(e['allowed'] for e in execution['network_events']), 'Run integrity violation')
    for event, filename in [('INFERENCE_CONFIG_FROZEN', 'INFERENCE_CONFIG.json'), ('QUALIFICATION_SUITE_FROZEN', 'SYNTHETIC_QUALIFICATION_SUITE.json')]:
        frozen = next(e for e in journal_events() if e['event'] == event)
        require(file_sha256(OUT / filename) == frozen['details']['sha256'], 'Frozen input changed')
    write_new(OUT / 'SYNTHETIC_QUALIFICATION_RESULTS.json', results)
    write_new(OUT / 'DETERMINISM_REPORT.json', duplicate_report)
    journal('QUALIFICATION_SCORED', outcome=results['outcome'], metrics=results['metrics'])
    a, b, _ = reproduce()
    require(canonical_json(a) == (OUT / 'SYNTHETIC_QUALIFICATION_RESULTS.json').read_bytes(), 'Score reproduction mismatch')
    require(canonical_json(b) == (OUT / 'DETERMINISM_REPORT.json').read_bytes(), 'Determinism reproduction mismatch')
    install_guards(no_model=True)
    tested = run_tests()
    journal('POST_RESULT_VERIFICATION', tests=tested, score_reproduction=True, primary_count=results['primary_count'], determinism_count=results['determinism_count'])
    names = ['QUALIFICATION_PROTOCOL.md', 'INFERENCE_CONFIG.json', 'SYNTHETIC_QUALIFICATION_SUITE.json',
             'SYNTHETIC_QUALIFICATION_RESULTS.json', 'RAW_MODEL_OUTPUTS.jsonl', 'DETERMINISM_REPORT.json']
    journal('ARTIFACTS_WRITTEN', sha256={n: file_sha256(OUT / n) for n in names}, runner_sha256=file_sha256(SOURCE), test_source_sha256=file_sha256(TEST_SOURCE))
    counts = next(e['details'] for e in journal_events() if e['event'] == 'EXECUTION_ENDED')
    tests_before = next(e['details'] for e in journal_events() if e['event'] == 'TIMEOUT_WORKER_VERIFIED')
    names.append('QUALIFICATION_JOURNAL.jsonl')
    metrics = '\n'.join(f"| {key} | {value['numerator']}/{value['denominator']} |" for key, value in results['metrics'].items())
    case_table = '\n'.join(f"| {a['case_id']} | {a['gate_output']} | {a['binary_correctness']} | {a['reason_code_correctness']} | {a['parser_error']} |" for a in results['cases'] if a['attempt_type'] == 'PRIMARY')
    hashes = '\n'.join(f'| {n} | `{file_sha256(OUT / n)}` |' for n in names)
    report = f'''# Attempt 2 synthetic semantic qualification

Outcome: **{results['outcome']}**
Review status: **CANDIDATE_AWAITING_OWNER_REVIEW**
Model: `{MODEL_REPOSITORY}@{MODEL_REVISION}`. CPU / FP32 / no quantization.
Base HEAD and runtime tag: `{HEAD}` / answerability-semantic-runtime-v0.1-pre-qualification.
Clean pre-implementation status, historical tags, prompt/parser/registry, runtime,
28 dependencies and all 10 snapshot hashes were verified before execution.
All 146 previously frozen file hashes remain unchanged; benchmark hashing only.

One executable config and all synthetic cases were frozen and hashed before model
initialization. See INFERENCE_CONFIG.json for full effective settings and explicit
provider-schema mapping. Greedy / one beam / 4096 max new tokens / 600 seconds /
seed 0 / PROMPT_ONLY_STRICT_JSON / strict frozen parser / zero retries.
Every request was token-budget checked with the unchanged tokenizer/chat template.

Model initializations this attempt: {counts['model_initializations']} (historical BR: 1).
Primary records: {results['primary_count']}; duplicate records: {results['determinism_count']}.
Real generate calls: {counts['generate_calls']}; timeouts: {results['timeout_count']}.
Call infrastructure failures: {results['infrastructure_failure_count']}.
Run-level infrastructure error: {counts['fatal_error']}.
Quality retries=0; infrastructure retries=0; model alternatives=0.

| Primary metric | Score |
| --- | --- |
{metrics}

| Case | Frozen GateOutput | Binary correct | Reason correct | Parser error |
| --- | --- | --- | --- | --- |
{case_table}

Failed primary IDs: {results['failed_primary_case_ids']}.
Determinism comparisons (diagnostic only):
```json
{json.dumps(duplicate_report, indent=2)}
```

Network/boundary observations:
```json
{json.dumps(counts['network_events'], indent=2)}
```
No outbound model requests or downloads. Local socket capability probes, if any,
are recorded above; no external fallback. DEVELOPMENT semantic calls=0; retrieval=0.
Phase 2H HELD_OUT and Phase 2G private HELDOUT accessed=false. No real benchmark
question was parsed or transmitted. No DEVELOPMENT eligibility metrics computed.

Pre-generation tests: {tests_before}. Post-result tests: {tested}.
Saved raw-output parser results, primary scores, deterministic serialization and
duplicate comparisons reproduced identically without model calls. Only scheduled
calls appear in custody records; no repair, prompt edit, tuning or second pass.
The fake-worker test exercised forced timeout termination; absence of a real timeout
does not establish runtime bounds for arbitrary future input. These synthetic
results do not establish DEVELOPMENT or production performance.

| Artifact | SHA-256 |
| --- | --- |
{hashes}

Journal is append-only and finalized; this report does not hash itself. The review
record hashes this report. Stop for owner review; no commit/tag/B3.2-C.
'''
    with (OUT / 'MODEL_QUALIFICATION_REPORT.md').open('x', encoding='utf-8', newline='\n') as f:
        f.write(report)
    names.append('MODEL_QUALIFICATION_REPORT.md')
    record = f'''# Attempt 2 qualification review record

Status: **CANDIDATE_AWAITING_OWNER_REVIEW**
Outcome: **{results['outcome']}**
Model: `{MODEL_REPOSITORY}@{MODEL_REVISION}`
Runtime: owner-frozen CPU / FP32 / Transformers; no quantization.
Base: `{HEAD}`. Historical preregistration, blocked Attempt 1 and BR unchanged.
This outcome concerns only the frozen synthetic suite; no DEVELOPMENT gate has run.
Model initializations={counts['model_initializations']}; generate calls={counts['generate_calls']}.
Primary={results['primary_count']}; determinism={results['determinism_count']}; retries=0.
DEVELOPMENT semantic=0; retrieval=0; outbound model requests/downloads=0; HELD_OUT=false.
Source SHA: `{file_sha256(SOURCE)}`. Test source SHA: `{file_sha256(TEST_SOURCE)}`.

| Artifact | SHA-256 |
| --- | --- |
''' + '\n'.join(f'| {n} | `{file_sha256(OUT / n)}` |' for n in names) + '\n\nNo self hash. Stop for owner review; do not commit, tag or begin B3.2-C.\n'
    with (OUT / 'MODEL_FREEZE_RECORD.md').open('x', encoding='utf-8', newline='\n') as f:
        f.write(record)
    print(json.dumps({'outcome': results['outcome'], 'metrics': results['metrics'], 'artifact_sha256': {p.name: file_sha256(p) for p in sorted(OUT.iterdir())}}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'test', 'execute', 'finalize', 'verify'))
    action = parser.parse_args().action
    if action == 'prepare':
        prepare()
    elif action == 'test':
        install_guards(no_model=True)
        tests = run_tests()
        require(not any(e['event'] in ('TIMEOUT_WORKER_VERIFIED', 'EXECUTION_STARTED') for e in journal_events()), 'Pre-generation test receipt already exists')
        journal('TIMEOUT_WORKER_VERIFIED', tests=tests, termination_test='spawned synthetic worker killed at short deadline; no model', timeout_seconds=600)
    elif action == 'execute':
        execute()
    elif action == 'finalize':
        finalize()
    else:
        check_frozen_inputs()
        install_guards(no_model=True)
        a, b, records = reproduce()
        require(canonical_json(a) == (OUT / 'SYNTHETIC_QUALIFICATION_RESULTS.json').read_bytes(), 'Results differ')
        require(canonical_json(b) == (OUT / 'DETERMINISM_REPORT.json').read_bytes(), 'Determinism differs')
        print('Saved-artifact reproduction PASS; no model calls.', len(records), 'records')


if __name__ == '__main__':
    main()
