"""Attempt-2 decoder identity and exact-schema qualification; no generation at this stage."""
import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from gateway.domain.evaluation.answerability.validate_dependency_imports_r2 import inventory

OUT = ROOT / 'artifacts/answerability_semantic_v2_decoder_qualification_attempt2'
PREREG = ROOT / 'artifacts/answerability_semantic_gate_v2_prereg'
R2 = ROOT / 'artifacts/answerability_semantic_v2_decoder_dependency_import_recovery'
PYTHON = Path.home() / '.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe'
BASE = '4fea18a9c70b1b9536dd92d7f1a118ac3e02a32f'
TAG = 'answerability-semantic-v2-deps-v0.2-imports-validated'
WHEEL_NAME = 'xgrammar-0.2.8-cp312-cp312-win_amd64.whl'
WHEEL_SHA = 'dbcf6718e049cbe429742cdb05f85c48135c2e389d45daeafb884af6994bb4a7'
SCHEMA_SHA = '6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e'
CHAT_SHA = 'cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f'
REGISTRY_SHA = 'c51d7f92e714421797f51bf1571cb8ee6f50b47352aad7867c1786d818a37ec2'
OFFLINE = {'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'PIP_NO_INDEX': '1',
           'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'PYTHONDONTWRITEBYTECODE': '1'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def write(name, value):
    with (OUT / name).open('xb') as handle:
        handle.write(canonical(value))


def read(name):
    return json.loads((OUT / name).read_bytes())


def event(name, details):
    with (OUT / 'DECODER_QUALIFICATION_JOURNAL.jsonl').open('ab') as handle:
        handle.write((json.dumps({'event': name, 'details': details,
                    'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}, sort_keys=True) + '\n').encode())


def no_repeat(name):
    events = (OUT / 'DECODER_QUALIFICATION_JOURNAL.jsonl').read_text()
    require(not any(json.loads(line)['event'] == name for line in events.splitlines()), 'No retry authorized')


def checked_schema(data):
    require(sha(data) == SCHEMA_SHA, 'Exact frozen schema required')
    return data.decode('utf-8')


def verify_v2():
    data = (PREREG / 'SEMANTIC_GATE_V2_REGISTRY.json').read_bytes()
    require(sha(data) == REGISTRY_SHA, 'Registry changed')
    registry = json.loads(data)
    pairs = [(PREREG / name, digest) for name, digest in registry['artifact_sha256'].items()]
    pairs += [(ROOT / registry['candidate_source_path'], registry['candidate_source_sha256']),
              (ROOT / 'gateway/domain/evaluation/answerability/gates/semantic_gate.py', registry['v1_parser_source_sha256'])]
    for path, digest in pairs:
        require(sha(path.read_bytes()) == digest, 'Frozen file changed: ' + str(path))
    receipt = ''.join(key + '\t' + registry[key] + '\n' for key in registry['parser_adapter_receipt_fields'])
    require(sha(receipt.encode()) == registry['parser_adapter_receipt_sha256'], 'Parser receipt changed')
    require(registry['candidate_status'] == 'PRE_REGISTERED_NOT_EVALUATED', 'Candidate state changed')
    return {'files': {str(p.relative_to(ROOT)): s for p, s in pairs}, 'registry_sha256': sha(data),
            'parser_adapter_receipt_sha256': sha(receipt.encode())}


def drift_check(before, after):
    require({k:v for k,v in before.items() if k != 'packages'} ==
            {k:v for k,v in after.items() if k != 'packages'}, 'Runtime drift')
    require(set(after['packages']) == set(before['packages']) | {'xgrammar'}, 'Unexpected package addition/removal')
    for name, identity in before['packages'].items():
        require(after['packages'][name] == identity, 'Pre-existing package drift: ' + name)
    require(after['packages']['xgrammar']['version'] == '0.2.8', 'Wrong XGrammar version')


def pip_check(name):
    result = subprocess.run([str(PYTHON), '-B', '-m', 'pip', 'check'], capture_output=True, text=True,
                            env=dict(os.environ, **OFFLINE))
    write(name, {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'pip check failed')


def prepare():
    require(not OUT.exists(), 'Refuse overwrite')
    require(Path(sys.executable).resolve() == PYTHON.resolve(), 'Wrong Python')
    for ref in ('HEAD', TAG):
        require(subprocess.check_output(['git','rev-parse', ref + '^{commit}'], cwd=ROOT, text=True).strip() == BASE, 'Wrong base')
    require(not subprocess.check_output(['git','diff','HEAD','--name-only'], cwd=ROOT, text=True).strip(), 'Tracked file changed')
    actual = inventory()
    require(actual == json.loads((R2 / 'POST_VALIDATION_PACKAGE_INVENTORY.json').read_bytes()), 'R2 environment drift')
    require('OWNER_REVIEWED / DEPENDENCIES_ENABLED_AWAITING_DECODER_REQUALIFICATION' in
            (R2 / 'IMPORT_RECOVERY_FREEZE_RECORD.md').read_text(), 'R2 not approved')
    verified = verify_v2()
    wheel = ROOT / '.cache/phase2h-a21' / WHEEL_NAME
    require(sha(wheel.read_bytes()) == WHEEL_SHA, 'Wheel SHA mismatch')
    OUT.mkdir()
    event('PRECONDITION_VERIFIED', {'base_commit': BASE, 'base_tag': TAG,
          'initial_clean_worktree': True, 'clean_check': 'git status --short before creating this runner'})
    event('R2_DEPENDENCY_RECOVERY_VERIFIED', {'inventory_match': True, 'packages': len(actual['packages'])})
    write('FROZEN_V2_VERIFICATION.json', verified)
    event('V2_PREREGISTRATION_VERIFIED', verified)
    write('DECODER_IDENTITY.json', {'package': 'xgrammar', 'version': '0.2.8', 'wheel_filename': WHEEL_NAME,
          'wheel_sha256': WHEEL_SHA, 'wheel_size': wheel.stat().st_size, 'original_verified_copy': str(wheel),
          'acquisition': 'REUSE_EXISTING_EXACT_WHEEL_COPY_OUTSIDE_REPOSITORY_BEFORE_INSTALL', 'downloads': 0})
    event('XGRAMMAR_WHEEL_VERIFIED', {'sha256': WHEEL_SHA, 'reused_existing_bytes': True})
    write('PRE_INSTALL_PACKAGE_INVENTORY.json', actual)
    event('PRE_INSTALL_INVENTORY_WRITTEN', {'package_drift_since_r2': 0})
    pip_check('PRE_INSTALL_PIP_CHECK.json')
    print('Prepared; R2 inventory, V2 receipts, wheel and pip check PASS.')


def install():
    no_repeat('XGRAMMAR_INSTALL_STARTED')
    require(inventory() == read('PRE_INSTALL_PACKAGE_INVENTORY.json'), 'Pre-install drift')
    source = ROOT / '.cache/phase2h-a21' / WHEEL_NAME
    require(sha(source.read_bytes()) == WHEEL_SHA, 'Wheel drift')
    outside = Path(tempfile.mkdtemp(prefix='phase2h-a21-attempt2-wheel-')) / WHEEL_NAME
    require(not outside.resolve().is_relative_to(ROOT.resolve()), 'Wheel must be outside repository')
    shutil.copyfile(source, outside)
    require(sha(outside.read_bytes()) == WHEEL_SHA, 'Copied wheel mismatch')
    write('WHEEL_CUSTODY.json', {'source': str(source), 'install_wheel_path': str(outside), 'sha256': WHEEL_SHA,
          'reused': True, 'copied_byte_identically': True, 'download_count': 0})
    event('XGRAMMAR_INSTALL_STARTED', {'wheel': str(outside), 'retry': 0})
    cmd = [str(PYTHON), '-B', '-m', 'pip', 'install', '--no-deps', '--no-index', '--no-compile', str(outside)]
    result = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, **OFFLINE))
    write('INSTALL_RESULT.json', {'command': cmd, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'Installation failed; stop')
    event('XGRAMMAR_INSTALLED', {'version': '0.2.8'})
    post = inventory()
    write('POST_INSTALL_PACKAGE_INVENTORY.json', post)
    drift_check(read('PRE_INSTALL_PACKAGE_INVENTORY.json'), post)
    dist = metadata.distribution('xgrammar')
    with zipfile.ZipFile(outside) as wheel:
        names = [n for n in wheel.namelist() if not n.endswith('/') and not n.endswith('.dist-info/RECORD')]
        for name in names:
            require(Path(dist.locate_file(name)).read_bytes() == wheel.read(name), 'Installed wheel payload mismatch')
    write('INSTALLED_PACKAGE_INTEGRITY.json', {'identity': post['packages']['xgrammar'],
          'wheel_payload_files_verified': len(names), 'existing_package_drift': 0,
          'additions': ['xgrammar==0.2.8'], 'direct_url': json.loads(dist.read_text('direct_url.json'))})
    event('POST_INSTALL_INVENTORY_VERIFIED', {'existing_package_drift': 0, 'payload_files_verified': len(names)})
    pip_check('POST_INSTALL_PIP_CHECK.json')
    print('Installed exact XGrammar wheel; prior packages unchanged; pip check PASS.')


def compile_exact(xgrammar, tokenizer_info, schema_bytes):
    schema_text = checked_schema(schema_bytes)
    return xgrammar.GrammarCompiler(tokenizer_info).compile_json_schema(schema_text)


def api_present(xgrammar, processor):
    return {'TokenizerInfo.from_huggingface': callable(getattr(xgrammar.TokenizerInfo, 'from_huggingface', None)),
            'GrammarCompiler': callable(xgrammar.GrammarCompiler),
            'GrammarCompiler.compile_json_schema': callable(getattr(xgrammar.GrammarCompiler, 'compile_json_schema', None)),
            'xgrammar.contrib.hf.LogitsProcessor': callable(processor)}


def probe_child():
    os.environ.update(OFFLINE)
    observations = {'socket_events': [], 'subprocess_events': [], 'prohibited_opens': []}
    def audit(name, args):
        if name.startswith('socket.'):
            observations['socket_events'].append({'operation': name, 'arguments': [str(a) for a in args]})
            if name in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname'):
                raise RuntimeError('No outbound networking authorized: ' + name)
        elif name == 'subprocess.Popen':
            observations['subprocess_events'].append({'executable': str(args[0]), 'arguments': str(args[1])})
        elif name == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = os.fsdecode(args[0]).replace(chr(92), '/').lower()
            if any(s in path for s in ('/development/', '/private_heldout/', '/held_out/')) or path.endswith('.safetensors'):
                observations['prohibited_opens'].append(path)
                raise RuntimeError('Prohibited data/model weight access during pre-model probe')
    sys.addaudithook(audit)
    stage = 'XGRAMMAR_IMPORT'
    try:
        import xgrammar
        require(metadata.version('xgrammar') == '0.2.8', 'Decoder version mismatch')
        event('XGRAMMAR_IMPORT_VERIFIED', {'module_path': xgrammar.__file__, 'version': metadata.version('xgrammar')})
        stage = 'XGRAMMAR_API'
        from xgrammar.contrib.hf import LogitsProcessor
        checks = api_present(xgrammar, LogitsProcessor)
        write('DECODER_API_RESULTS.json', {'import_success': True, 'distribution_version': metadata.version('xgrammar'),
              'module_reported_version': getattr(xgrammar, '__version__', None), 'module_path': xgrammar.__file__,
              'required_apis': checks, 'passed': all(checks.values())})
        require(all(checks.values()), 'Required API absent')
        event('XGRAMMAR_API_VERIFIED', checks)
        stage = 'TOKENIZER_INTEGRATION'
        model_inventory = json.loads((ROOT / 'artifacts/answerability_semantic_runtime_v1_enablement/MODEL_FILE_INVENTORY.json').read_bytes())
        snapshot = Path(model_inventory['snapshot_path'])
        files = [row for row in model_inventory['files'] if row['relative_path'] in
                 ('tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt', 'config.json')]
        for row in files:
            require(sha((snapshot / row['relative_path']).read_bytes()) == row['sha256'], 'Tokenizer/config drift')
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False)
        require(sha(tokenizer.chat_template.encode()) == CHAT_SHA, 'Chat template drift')
        config = json.loads((snapshot / 'config.json').read_bytes())
        info = xgrammar.TokenizerInfo.from_huggingface(tokenizer, vocab_size=config['vocab_size'])
        write('TOKENIZER_INTEGRATION_RESULT.json', {'passed': True, 'snapshot': str(snapshot),
              'revision': model_inventory['revision'], 'verified_files': files, 'chat_template_sha256': CHAT_SHA,
              'tokenizer_class': type(tokenizer).__name__, 'tokenizer_length': len(tokenizer),
              'model_vocab_size': config['vocab_size'], 'xgrammar_vocab_size': info.vocab_size,
              'vocabulary_sha256': sha(canonical(tokenizer.get_vocab())), 'model_initializations': 0})
        event('TOKENIZER_INTEGRATION_VERIFIED', {'model_initialized': False})
        stage = 'SCHEMA_COMPILATION'
        grammar = compile_exact(xgrammar, info, (PREREG / 'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes())
        write('SCHEMA_COMPILATION_RESULT.json', {'passed': True, 'schema_sha256': SCHEMA_SHA})
        event('V2_SCHEMA_COMPILED', {'sha256': SCHEMA_SHA})
        stage = 'HF_INTEGRATION'
        processor = LogitsProcessor(grammar)
        from transformers import LogitsProcessorList
        integration = LogitsProcessorList([processor])
        require(callable(integration) and callable(processor), 'Invalid processor')
        write('HF_INTEGRATION_RESULT.json', {'passed': True, 'processor_type': type(processor).__name__,
              'container_type': type(integration).__name__, 'generate_calls': 0})
        event('HF_LOGITS_PROCESSOR_VERIFIED', {'generation_not_yet_authorized_by_prerequisites': True})
    except Exception as exc:
        filename = {'SCHEMA_COMPILATION': 'SCHEMA_COMPILATION_RESULT.json', 'HF_INTEGRATION': 'HF_INTEGRATION_RESULT.json',
                    'TOKENIZER_INTEGRATION': 'TOKENIZER_INTEGRATION_RESULT.json'}.get(stage, 'API_FAILURE.json')
        write(filename, {'passed': False, 'stage': stage, 'error_type': type(exc).__name__, 'error': str(exc),
              'traceback': traceback.format_exc(), 'schema_sha256': SCHEMA_SHA})
        event('QUALIFICATION_FAILED', {'stage': stage, 'error_type': type(exc).__name__, 'error': str(exc)})
        raise
    finally:
        write('PROBE_OBSERVATIONS.json', observations)


def probe():
    no_repeat('FUNCTIONAL_PROBE_STARTED')
    require(inventory() == read('POST_INSTALL_PACKAGE_INVENTORY.json'), 'Post-install drift')
    verify_v2()
    event('FUNCTIONAL_PROBE_STARTED', {'retry': 0, 'model_initializations': 0})
    start = time.monotonic()
    result = subprocess.run([str(PYTHON), '-I', '-B', str(Path(__file__).resolve()), 'probe_child'],
                            cwd=PYTHON.parent.parent, env=dict(os.environ, **OFFLINE), capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    write('FUNCTIONAL_PROBE_PROCESS.json', {'returncode': result.returncode, 'stdout': result.stdout,
          'stderr': result.stderr, 'elapsed_seconds': time.monotonic() - start, 'retry_count': 0})
    print('Functional probe exit:', result.returncode)
    print(result.stderr)


if __name__ == '__main__':
    {'prepare': prepare, 'install': install, 'probe': probe, 'probe_child': probe_child}[sys.argv[1]]()
