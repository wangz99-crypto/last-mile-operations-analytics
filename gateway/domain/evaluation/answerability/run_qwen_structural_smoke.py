"""Three authorized, offline structural-only generations; no evaluation loader."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from recover_direct_regex_acceptance import inventory, pip_check
from gateway.domain.evaluation.answerability.answerability_contracts import ActiveBundle, GateInput, RankedEvidence, ContractError
from gateway.domain.evaluation.answerability.gates.semantic_gate_v2 import build_messages, canonical_prompt, adapt_response
from gateway.domain.evaluation.answerability.semantic_transformers_runtime import RuntimeSpec, verify_snapshot, load_cpu_fp32, require_context_capacity

ART = ROOT / 'artifacts/answerability_semantic_v2_1_qwen_structural_smoke'
EXACT = ROOT / 'artifacts/answerability_semantic_v2_1_exact_validator'
RUNTIME = ROOT / 'artifacts/answerability_semantic_runtime_v1_enablement'
OLD = ROOT / 'artifacts/answerability_semantic_v2_decoder_qualification_attempt2'
SCHEMA = ROOT / 'artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json'
REGEX = ROOT / 'artifacts/answerability_semantic_v2_1_direct_regex_decoder/DECODER_ENFORCEMENT_REGEX.txt'
PROMPT = ROOT / 'artifacts/answerability_semantic_gate_v2_prereg/SEMANTIC_PROMPT_V2.txt'
BASE = 'c044cc3d9f4e15c147b7b5dade7647f24c05d707'
TAG = 'answerability-semantic-v2_1-structure-v0.1-qualified'
CHAT_SHA = 'cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f'
INV_SHA = 'bd997774f25c307eb4421488607110f011592250e0bd82b2a096b3a7cf17b4fb'


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def save(name, value, exclusive=False):
    with (ART / name).open('xb' if exclusive else 'wb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def gate(value):
    return GateInput(value['question'], tuple(RankedEvidence(**e) for e in value['evidence']),
                     ActiveBundle(**value['active_bundle']))


def snapshot_spec():
    inv = read(RUNTIME / 'MODEL_FILE_INVENTORY.json')
    return RuntimeSpec(inv['repository'], inv['revision'], inv['snapshot_path'], 'cpu', 'float32', None)


def prepare():
    assert not ART.exists(), 'Refuse overwrite of smoke artifacts'
    assert git('rev-parse', 'HEAD') == git('rev-list', '-n', '1', TAG) == BASE
    # This helper is the sole permitted change after the independently checked clean entry.
    helper_name = Path(__file__).relative_to(ROOT).as_posix()
    assert git('status', '--porcelain', '--untracked-files=all') == '?? ' + helper_name
    assert 'OWNER_REVIEWED / EXACT_VALIDATOR_AND_COMBINED_STRUCTURE_QUALIFIED' in (EXACT / 'FINAL_RECORD.md').read_text(encoding='utf-8')
    previous = read(EXACT / 'VALIDATOR_IDENTITY.json')
    frozen = dict(previous['immutable_inputs_sha256'])
    frozen.update(read(EXACT / 'FINAL_SHA256.json')['files'])
    for path in (EXACT / 'FINAL_SHA256.json', EXACT / 'VALIDATOR_IDENTITY.json',
                 RUNTIME / 'LOCAL_RUNTIME_IDENTITY.json', RUNTIME / 'MODEL_FILE_INVENTORY.json',
                 OLD / 'STRUCTURAL_SMOKE_CONFIG.json', OLD / 'EXECUTION_CONFIG_CONFORMANCE.json',
                 OLD / 'DECODER_FREEZE_RECORD.md', PROMPT,
                 ROOT / 'gateway/domain/evaluation/answerability/semantic_transformers_runtime.py'):
        frozen[path.relative_to(ROOT).as_posix()] = sha(path)
    for name, expected in frozen.items():
        assert sha(ROOT / name) == expected, name
    assert sha(SCHEMA) == '6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e'
    assert sha(REGEX) == '3ec42de4a205e599789575954494ad2004beedcc49e2ed550ef865b591dc1482'
    assert sha(PROMPT) == digest(canonical_prompt().encode()) == '1b36fbf92f120f77bfb9d2af55409ed48e43341956f7e06fae83777f4937f35e'
    smoke = read(OLD / 'STRUCTURAL_SMOKE_CONFIG.json')
    deviation = read(OLD / 'EXECUTION_CONFIG_CONFORMANCE.json')
    requested = deepcopy(read(RUNTIME / 'LOCAL_RUNTIME_IDENTITY.json')['full_proposed_generation_config'])
    assert deviation['authorized_differences'] == ['max_new_tokens']
    assert deviation['unauthorized_differences'] == ['repetition_penalty']
    requested['max_new_tokens'] = smoke['max_new_tokens']
    assert requested['max_new_tokens'] == 512 and requested['repetition_penalty'] == 1.0
    for key in ('do_sample', 'num_beams'):
        assert requested[key] == smoke[key]
    assert smoke['seed'] == 0 and smoke['deterministic_algorithms'] is True
    assert smoke['torch_num_threads'] == 4 and smoke['torch_num_interop_threads'] == 1
    spec = snapshot_spec()
    inv = verify_snapshot(spec, RUNTIME / 'MODEL_FILE_INVENTORY.json', INV_SHA)
    assert len(inv['files']) == 10
    chat = read(Path(spec.snapshot_path) / 'tokenizer_config.json')['chat_template']
    assert digest(chat.encode()) == CHAT_SHA == smoke['chat_template_sha256']
    before = inventory()
    assert before == previous['pre_environment']['packages'], 'Package drift before smoke'
    check = pip_check()
    assert check['returncode'] == 0, check

    # Only three explicitly named public policy documents, never benchmark files.
    domain = ROOT / 'gateway/domain'
    manifest = domain / 'policy/artifact_manifest.json'
    registry = domain / 'policy/policy_registry.json'
    authority = read(manifest)['sha256']
    bundle_data = read(registry)
    bundle = ActiveBundle(**{k: bundle_data[k] for k in ('bundle_id', 'bundle_version', 'effective_from', 'effective_to')},
                          manifest_sha256=sha(manifest), registry_sha256=sha(registry))
    assert sha(registry) == authority['policy/policy_registry.json']
    public = {manifest.relative_to(ROOT).as_posix(): sha(manifest), registry.relative_to(ROOT).as_posix(): sha(registry)}
    docs = {}
    for name in ('operations_audit', 'carrier_handoff', 'insufficient_evidence'):
        path = domain / ('sops/last_mile/' + name + '.md')
        assert sha(path) == authority[path.relative_to(domain).as_posix()], path
        public[path.relative_to(ROOT).as_posix()] = sha(path)
        text = path.read_text(encoding='utf-8')
        meta = json.loads(re.search(r'```json\s*\n(.*?)\n```', text, re.S)[1])
        sections = {s['section_id']: s for s in meta['sections']}
        bodies = dict(re.findall(r'^## ([a-z0-9-]+)\n(.*?)(?=^## |\Z)', text, re.S | re.M))
        docs[name] = (meta, sections, bodies)

    definitions = [
        ('SMOKE-01', 'single ask, one supplied section',
         'For the fictional MARBLE-17 rehearsal, what information belongs in the audit record of a deterministic assessment?',
         [('operations_audit', 'decision-record')]),
        ('SMOKE-02', 'multiple asks, two supplied sections',
         'For a fictional QUARTZ-28 carrier handoff draft, what information must the draft contain, and what review or action boundary applies to the draft?',
         [('carrier_handoff', 'handoff-fields'), ('carrier_handoff', 'handoff-boundary')]),
        ('SMOKE-03', 'conditional context, three supplied sections',
         'In the fictional LANTERN-39 rehearsal, if observations are missing and other observations conflict, how should those issues be represented in an assessment record?',
         [('insufficient_evidence', 'missing-facts'), ('insufficient_evidence', 'data-conflicts'), ('operations_audit', 'decision-record')]),
    ]
    fixtures = []
    for fid, shape, question, refs in definitions:
        evidence = []
        for rank, (doc, sid) in enumerate(refs, 1):
            meta, sections, bodies = docs[doc]
            evidence.append(RankedEvidence(rank, meta['policy_id'], meta['version'], sid, meta['title'],
                                            sections[sid]['section'], bodies[sid].strip(), 0.95 - rank * 0.01))
        value = GateInput(question, tuple(evidence), bundle)
        messages = list(build_messages(value))
        fixtures.append({'id': fid, 'structural_shape': shape, 'scope': 'EXCLUDED_FROM_SEMANTIC_QUALIFICATION',
                         'gate_input': asdict(value), 'gate_input_sha256': digest(encoded(asdict(value))),
                         'messages': messages, 'messages_sha256': digest(encoded(messages)),
                         'semantic_accuracy': 'NOT_EVALUATED'})
    protocol = '''# Three-call Qwen structural smoke\n\nStatus: FROZEN_BEFORE_MODEL_INITIALIZATION\n\nExactly three fresh, independently authored public-policy smoke inputs; no semantic Gold or expected gate decisions. Evidence is copied deterministically from named active SOP sections. Scores are synthetic interface placeholders (0.95 - rank * 0.01), never measured retrieval results. No benchmark contents were consulted. All fixtures are EXCLUDED_FROM_SEMANTIC_QUALIFICATION.\n\nFrozen V2 canonical prompt and unmodified GateInput boundary. SMOKE IDs and shape/scope annotations are not passed to the model. No prompt edits, truncation, or evidence reordering. Complete fixed direct-regex V0.1 decoder, exact Draft202012Validator on original schema bytes, and frozen deterministic adapter. No per-input substitute schema.\n\nGeneration configuration comes from full_proposed_generation_config in the frozen runtime identity, with ONLY the previously authorized structural-smoke max_new_tokens=512 change. The historical owner-reviewed repetition_penalty=1.1 deviation is rejected; frozen repetition_penalty=1.0 applies. Greedy sampling flags and all other serialized fields are preserved, including inactive temperature=1.0, top_p=1.0, top_k=50. Seed=0, threads=4, interop=1, deterministic algorithms=true, CPU FP32. Timeout=600 seconds per call; zero quality/infrastructure retries. No inference during preparation.\n\nRequested GenerationConfig is constructed explicitly, never inherited from snapshot generation_config.json. Model defaults are disabled and the effective configuration is compared field-for-field inside _prepare_generation_config before any forward pass for each call. Transformers' derived max_length from input length + max_new_tokens is runtime bookkeeping, not a change in the frozen new-token budget. The guard records the resolved configuration, no scientific decision is repaired.\n\nEach exact generated token sequence and decoded text (with special tokens) is checkpointed before parsing. Raw JSON payload excludes only one final generation EOS control token if emitted; no strip, special-token filtering, manual completion, or whitespace normalization. UTF-8 hex and SHA preserve payload bytes. Outputs capped without EOS are retained unchanged and subjected to structural checks. Decoder acceptance is checked on observed content tokens without advancing EOS; previously qualified JSON whitespace closure permits legal trailing whitespace, not a sole-EOS oracle.\n\nOrdered pipeline: frozen token constraint -> strict standard JSON parse -> exact authoritative schema -> deterministic adapter -> structural disposition. Failure skips later stages. Semantic accuracy, decision correctness and support correctness are NOT_EVALUATED. Completed structural failures do not trigger retries; proceed with remaining preregistered calls. Genuine runtime failure stops remaining calls and preserves partial evidence. Forward counter measures top-level causal-LM forward invocations via a pre-hook. No package changes, downloads, external network, retrieval, DEVELOPMENT or HELDOUT access. No formal semantic qualification suite authored.\n'''
    ART.mkdir()
    (ART / 'SMOKE_PROTOCOL.md').write_bytes(protocol.encode())
    save('SMOKE_FIXTURES.json', {'fixtures': fixtures, 'public_source_sha256': public,
                               'evidence_origin': 'DIRECT_PUBLIC_SOP_COPY_NO_RETRIEVAL',
                               'score_origin': 'SYNTHETIC_INTERFACE_PLACEHOLDER_NOT_RETRIEVAL',
                               'semantic_suite': 'NOT YET AUTHORED'}, True)
    frozen.update(public)
    frozen[helper_name] = sha(__file__)
    state = {'status': 'FROZEN_BEFORE_MODEL_INITIALIZATION', 'frozen_utc': now(), 'base_commit': BASE, 'base_tag': TAG,
             'entry_git_status': 'clean before sole helper creation', 'model': asdict(spec),
             'snapshot_verification': {'matched': 10, 'inventory_sha256': INV_SHA, 'files': inv['files']},
             'chat_template_sha256': CHAT_SHA, 'prompt_sha256': sha(PROMPT),
             'schema_sha256': sha(SCHEMA), 'regex_sha256': sha(REGEX),
             'decoder': 'DECODER_ENFORCEMENT_REGEX_V2_1_V0_1',
             'validator': {'package': 'jsonschema', 'version': '4.26.0', 'class': 'Draft202012Validator', 'referencing': '0.37.0'},
             'requested_generation_config': requested, 'requested_generation_config_sha256': digest(encoded(requested)),
             'actual_runtime_generation_configs': [], 'config_authority': {
                 'full_base': (RUNTIME / 'LOCAL_RUNTIME_IDENTITY.json').relative_to(ROOT).as_posix(),
                 'authorized_override': {'max_new_tokens': 512},
                 'override_source': (OLD / 'STRUCTURAL_SMOKE_CONFIG.json').relative_to(ROOT).as_posix(),
                 'owner_accepted_deviation_record': (OLD / 'DECODER_FREEZE_RECORD.md').relative_to(ROOT).as_posix(),
                 'conformance_record': (OLD / 'EXECUTION_CONFIG_CONFORMANCE.json').relative_to(ROOT).as_posix(),
                 'repetition_penalty': '1.0 frozen; historical actual 1.1 is explicitly unauthorized'},
             'runtime_controls': {k: smoke[k] for k in ('seed', 'deterministic_algorithms', 'torch_num_threads', 'torch_num_interop_threads', 'per_call_timeout_seconds', 'quality_retry', 'infrastructure_retry')},
             'freeze_sha256': {n: sha(ART / n) for n in ('SMOKE_PROTOCOL.md', 'SMOKE_FIXTURES.json')},
             'immutable_inputs_sha256': frozen, 'pre_environment': {'packages': before, 'pip_check': check},
             'counters': {'model_initialization': 0, 'tokenizer_loads': 0, 'generate': 0, 'forward': 0,
                          'retries': 0, 'repairs': 0, 'timeouts': 0, 'package_mutations': 0, 'downloads': 0,
                          'DEVELOPMENT_access': 0, 'retrieval': 0},
             'socket_events': [], 'phase_2h_held_out_access': False, 'phase_2g_private_heldout_access': False,
             'fresh_semantic_suite': 'NOT YET AUTHORED'}
    save('RUNTIME_IDENTITY.json', state, True)
    print(json.dumps({'status': state['status'], 'fixture_sha256': state['freeze_sha256']['SMOKE_FIXTURES.json'],
                      'snapshot_files_verified': 10, 'packages': len(before), 'model_calls': 0}), flush=True)


def execute():
    assert not (ART / 'RAW_GENERATIONS.json').exists(), 'Refuse retry or overwrite'
    state = read(ART / 'RUNTIME_IDENTITY.json')
    assert state['status'] == 'FROZEN_BEFORE_MODEL_INITIALIZATION'
    assert git('rev-parse', 'HEAD') == git('rev-list', '-n', '1', TAG) == BASE
    for name, expected in state['immutable_inputs_sha256'].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in state['freeze_sha256'].items():
        assert sha(ART / name) == expected, name
    fixtures = read(ART / 'SMOKE_FIXTURES.json')['fixtures']
    assert len(fixtures) == 3 and inventory() == state['pre_environment']['packages']
    rows, raw_rows = [], []
    state['status'] = 'STARTED'
    state['started_utc'] = now()
    state['pre_execution_runtime_identity_sha256'] = sha(ART / 'RUNTIME_IDENTITY.json')
    def checkpoint():
        save('RUNTIME_IDENTITY.json', state)
    def raw_checkpoint():
        save('RAW_GENERATIONS.json', {'scope': 'STRUCTURAL_SMOKE_ONLY', 'semantic_accuracy': 'NOT_EVALUATED', 'rows': raw_rows})
    def results_checkpoint():
        save('STRUCTURAL_RESULTS.json', {'rows': rows, 'semantic_accuracy': 'NOT_EVALUATED'})
    raw_checkpoint()
    checkpoint()
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                      PYTHONDONTWRITEBYTECODE='1', TOKENIZERS_PARALLELISM='false',
                      OUTLINES_CACHE_DIR=str(ROOT / '.cache/phase2h-direct-regex-runtime'))
    def guard(event, args):
        if event.startswith('socket.'):
            state['socket_events'].append({'operation': event, 'arguments': str(args)})
            if event not in {'socket.__new__', 'socket.gethostname'}:
                if event != 'socket.bind' or str(args[1][0]) not in {'::1', '127.0.0.1'}:
                    raise RuntimeError('Offline network boundary: ' + event)
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = os.fsdecode(args[0]).lower().replace('\\', '/')
            if any(s in path for s in ('/private_heldout/', '/held_out/', '/heldout/', '/answerability/development/',
                                      '/retrieval/development/', '/answerability_dev_bge_evidence_v0/')):
                raise RuntimeError('Benchmark quarantine: ' + path)
    sys.addaudithook(guard)
    failure = None
    try:
        import torch
        from transformers import GenerationConfig, LogitsProcessorList
        from outlines_core import Guide
        from outlines.backends.outlines_core import OutlinesCoreBackend, OutlinesCoreLogitsProcessor
        from outlines.models.transformers import TransformerTokenizer
        from qualify_exact_validator import resolve, strict_parse
        requested = state['requested_generation_config']
        config = GenerationConfig.from_dict(deepcopy(requested))
        assert config.to_dict() == requested, 'QWEN_STRUCTURAL_SMOKE_BLOCKED_CONFIG_UNRESOLVED'
        assert metadata.version('outlines') == '1.3.3' and metadata.version('outlines_core') == '0.2.14'
        assert metadata.version('jsonschema') == '4.26.0' and metadata.version('referencing') == '0.37.0'
        _, validator = resolve(read(SCHEMA))
        spec = snapshot_spec()
        assert digest(read(Path(spec.snapshot_path) / 'tokenizer_config.json')['chat_template'].encode()) == CHAT_SHA
        state['counters']['model_initialization'] = 1
        state['counters']['tokenizer_loads'] = 1
        checkpoint()
        model, tok, model_config, load_receipt = load_cpu_fp32(spec, RUNTIME / 'MODEL_FILE_INVENTORY.json', INV_SHA)
        state['model_load_receipt'] = load_receipt
        assert digest(tok.chat_template.encode()) == CHAT_SHA
        assert torch.get_num_threads() == 4 and torch.get_num_interop_threads() == 1
        assert torch.are_deterministic_algorithms_enabled()
        model.generation_config = deepcopy(config)
        wrapped = TransformerTokenizer(tok)
        backend = object.__new__(OutlinesCoreBackend)
        backend.eos_token_id = wrapped.eos_token_id
        backend.vocabulary = OutlinesCoreBackend.create_outlines_core_vocabulary(
            wrapped.get_vocab(), wrapped.eos_token_id, wrapped.eos_token, wrapped.convert_token_to_string)
        backend.tensor_library_name = 'torch'
        index = backend.get_regex_logits_processor(REGEX.read_text(encoding='utf-8')).index
        state['index_constructions'] = 1
        state['decoder_eos_token_id'] = wrapped.eos_token_id
        def forward_count(module, args):
            state['counters']['forward'] += 1
        handle = model.register_forward_pre_hook(forward_count)
        original_prepare = model._prepare_generation_config
        active = {'id': None}
        def guarded_prepare(*args, **kwargs):
            effective, other = original_prepare(*args, **kwargs)
            actual = effective.to_dict()
            comparison = {'id': active['id'], 'requested': deepcopy(requested), 'actual': actual,
                          'equal': actual == requested, 'observed_utc': now()}
            state['actual_runtime_generation_configs'].append(comparison)
            checkpoint()
            assert comparison['equal'], 'Effective frozen generation configuration mismatch'
            return effective, other
        model._prepare_generation_config = guarded_prepare
        for fixture in fixtures:
            value = gate(fixture['gate_input'])
            assert digest(encoded(asdict(value))) == fixture['gate_input_sha256']
            messages = list(build_messages(value))
            assert messages == fixture['messages'] and digest(encoded(messages)) == fixture['messages_sha256']
            assert all(sha(ART / n) == h for n, h in state['freeze_sha256'].items())
            rendered = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tok(rendered, return_tensors='pt', add_special_tokens=False)
            input_length = inputs['input_ids'].shape[1]
            margin = require_context_capacity(input_length, requested['max_new_tokens'], model_config.max_position_embeddings)
            assert config.to_dict() == requested
            active['id'] = fixture['id']
            state['counters']['generate'] += 1
            assert state['counters']['generate'] <= 3
            checkpoint()
            started = time.monotonic()
            observed_before = state['counters']['forward']
            result = {}
            processor = OutlinesCoreLogitsProcessor(index, 'torch')
            def run_once():
                try:
                    with torch.inference_mode():
                        result['tokens'] = model.generate(**inputs, generation_config=deepcopy(config),
                                                         use_model_defaults=False,
                                                         logits_processor=LogitsProcessorList([processor]))
                except BaseException:
                    result['error'] = traceback.format_exc()
            worker = threading.Thread(target=run_once, daemon=True)
            worker.start()
            worker.join(state['runtime_controls']['per_call_timeout_seconds'])
            if worker.is_alive():
                state['counters']['timeouts'] += 1
                state['status'] = 'QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED'
                state['failure'] = 'Generation wall-clock deadline exceeded; no retry'
                checkpoint()
                results_checkpoint()
                os._exit(2)
            if 'error' in result:
                raise RuntimeError(result['error'])
            tokens = result['tokens'][0, input_length:].tolist()
            terminal = tokens[-1] if tokens and tokens[-1] in requested['eos_token_id'] else None
            content = tokens[:-1] if terminal is not None else tokens
            raw = tok.decode(content, skip_special_tokens=False, clean_up_tokenization_spaces=False).encode('utf-8')
            raw_row = {'id': fixture['id'], 'generation_completed': True, 'generated_token_ids': tokens,
                       'decoded_with_control_tokens': tok.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
                       'terminal_control_token_id': terminal, 'raw_text': raw.decode('utf-8'),
                       'raw_utf8_hex': raw.hex(), 'raw_byte_length': len(raw), 'raw_sha256': digest(raw),
                       'input_tokens': input_length, 'context_margin': margin, 'rendered_prompt_sha256': digest(rendered.encode()),
                       'generated_tokens': len(tokens), 'forward_calls': state['counters']['forward'] - observed_before,
                       'elapsed_seconds': time.monotonic() - started, 'saved_before_parse_utc': now(),
                       'semantic_accuracy': 'NOT_EVALUATED'}
            raw_rows.append(raw_row)
            raw_checkpoint()  # exact generation receipt persisted BEFORE parser/validator/adapter
            row = {'id': fixture['id'], 'generation_completed': True, 'raw_byte_length': len(raw),
                   'raw_sha256': digest(raw), 'decoder': 'NOT_RUN', 'JSON_parse': 'NOT_RUN',
                   'exact_schema': 'NOT_RUN', 'adapter': 'NOT_RUN', 'semantic_accuracy': 'NOT_EVALUATED'}
            guide = Guide(index)
            decoder_ok = True
            for token in content:
                if token not in guide.get_tokens():
                    decoder_ok = False
                    break
                guide.advance(token_id=token, return_tokens=False)
            decoder_ok = decoder_ok and guide.is_finished() and wrapped.eos_token_id in guide.get_tokens()
            row['decoder'] = 'PASS' if decoder_ok else 'FAIL'
            row['decoder_acceptance_basis'] = 'Observed content traversal + final state + EOS; frozen qualified whitespace closure retained, no sole-EOS condition'
            if not decoder_ok:
                row['disposition'] = 'DECODER_STRUCTURAL_REJECT'
            else:
                try:
                    parsed = strict_parse(raw)
                    row['JSON_parse'] = 'PASS'
                except (UnicodeError, ValueError) as exc:
                    row.update(JSON_parse='FAIL', disposition='JSON_PARSE_REJECT', error=str(exc))
                if row['JSON_parse'] == 'PASS':
                    errors = list(validator.iter_errors(parsed))
                    row['exact_schema'] = 'FAIL' if errors else 'PASS'
                    if errors:
                        row.update(disposition='EXACT_SCHEMA_REJECT', schema_errors=[{'path': list(e.absolute_path), 'schema_path': list(e.absolute_schema_path), 'message': e.message} for e in errors])
                    else:
                        try:
                            output = adapt_response(raw, value)
                            row.update(adapter='PASS', gate_output=asdict(output), disposition='COMBINED_STRUCTURAL_ACCEPT')
                        except ContractError as exc:
                            row.update(adapter='FAIL', disposition='ADAPTER_STRUCTURAL_REJECT', error=str(exc))
            rows.append(row)
            results_checkpoint()
            checkpoint()
            print(json.dumps({k: row[k] for k in ('id', 'JSON_parse', 'exact_schema', 'adapter', 'disposition')}), flush=True)
        handle.remove()
    except BaseException:
        failure = traceback.format_exc()
        state['failure'] = failure
    finally:
        after, check = inventory(), pip_check()
        state['post_environment'] = {'packages': after, 'pip_check': check,
                                     'matches_pre': after == state['pre_environment']['packages']}
        state['immutable_inputs_unchanged'] = all(sha(ROOT / p) == h for p, h in state['immutable_inputs_sha256'].items())
        state['frozen_fixtures_protocol_unchanged'] = all(sha(ART / p) == h for p, h in state['freeze_sha256'].items())
        accepted = sum(r['disposition'] == 'COMBINED_STRUCTURAL_ACCEPT' for r in rows)
        if any(r['disposition'] != 'COMBINED_STRUCTURAL_ACCEPT' for r in rows):
            state['status'] = 'QWEN_STRUCTURAL_SMOKE_FAILED'
        elif failure or len(rows) != 3:
            state['status'] = ('QWEN_STRUCTURAL_SMOKE_BLOCKED_CONFIG_UNRESOLVED'
                               if failure and 'BLOCKED_CONFIG_UNRESOLVED' in failure and state['counters']['generate'] == 0
                               else 'QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED')
        else:
            state['status'] = 'QWEN_STRUCTURAL_SMOKE_PASS'
        state['finished_utc'] = now()
        state['environment_integrity_pass'] = state['post_environment']['matches_pre'] and check['returncode'] == 0
        checkpoint()
        results_checkpoint()
        counts = {'generation_completed': len(raw_rows), 'JSON_parse_PASS': sum(r['JSON_parse'] == 'PASS' for r in rows),
                  'exact_schema_PASS': sum(r['exact_schema'] == 'PASS' for r in rows),
                  'adapter_PASS': sum(r['adapter'] == 'PASS' for r in rows), 'combined_structural_accept': accepted}
        record = ('# Qwen Three-Call Structural Smoke\n\nStatus: CANDIDATE_AWAITING_OWNER_REVIEW\nOutcome: ' + state['status']
                  + '\n\nBase: ' + BASE + '\nTag: ' + TAG + '\n\nCounts:\n```json\n' + json.dumps(counts, indent=2)
                  + '\n```\nCounters:\n```json\n' + json.dumps(state['counters'], indent=2)
                  + '\n```\nSemantic correctness: NOT_EVALUATED. No semantic labels, scoring, repair, retry or tuning.\n'
                  + 'Fresh formal V2.1 semantic qualification suite: NOT YET AUTHORED.\n'
                  + 'Both HELDOUT sets accessed: false. DEVELOPMENT access: 0. Retrieval: 0.\n'
                  + 'Environment integrity: ' + str(state['environment_integrity_pass']) + '. Frozen sources unchanged: '
                  + str(state['immutable_inputs_unchanged']) + '. Fixtures/protocol unchanged: ' + str(state['frozen_fixtures_protocol_unchanged'])
                  + '.\n\nRequested and observed effective configuration, all source/model hashes, per-call raw outputs and structural dispositions are recorded in the adjacent JSON artifacts. No commit or tag.\n')
        (ART / 'FINAL_RECORD.md').write_bytes(record.encode())
        files = [p for p in ART.iterdir() if p.name != 'FINAL_SHA256.json'] + [Path(__file__)]
        save('FINAL_SHA256.json', {'algorithm': 'SHA-256', 'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)},
                                 'self_hash': 'Excluded to avoid circularity; report separately.'})
        print(json.dumps({'outcome': state['status'], 'counts': counts, 'counters': state['counters'],
                          'environment_integrity': state['environment_integrity_pass'], 'failure': failure}), flush=True)


if __name__ == '__main__':
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', PIP_NO_INDEX='1')
    if sys.argv[1:] == ['prepare']:
        prepare()
    elif sys.argv[1:] == ['execute']:
        execute()
    else:
        raise SystemExit('Use prepare once, then execute once; no retries.')
