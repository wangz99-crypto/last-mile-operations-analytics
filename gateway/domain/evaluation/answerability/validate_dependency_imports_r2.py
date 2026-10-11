"""R2 dependency-only import recovery. No historical guard reuse or environment mutation."""
import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'artifacts/answerability_semantic_v2_decoder_dependency_import_recovery'
R1 = ROOT / 'artifacts/answerability_semantic_v2_decoder_dependency_enablement'
TAG = 'answerability-semantic-v2-deps-v0.1-enablement-failed'
PYTHON = Path.home() / '.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe'
ORDER = ('annotated-types', 'typing-inspection', 'pydantic-core', 'pydantic', 'apache-tvm-ffi')
VERSIONS = {'annotated-types': '0.8.0', 'typing-inspection': '0.4.4', 'pydantic-core': '2.46.5', 'pydantic': '2.13.5', 'apache-tvm-ffi': '0.1.14.post1'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def write(name, value):
    with (OUT / name).open('xb') as f:
        f.write(canonical(value))


def read(name):
    return json.loads((OUT / name).read_bytes())


def event(name, details):
    with (OUT / 'IMPORT_RECOVERY_JOURNAL.jsonl').open('ab') as f:
        f.write((json.dumps({'event': name, 'details': details, 'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}, sort_keys=True) + '\n').encode())


def inventory():
    packages = {}
    for dist in metadata.distributions():
        name = dist.metadata['Name'].lower().replace('_', '-').replace('.', '-')
        require(name not in packages, 'Duplicate package identity')
        packages[name] = {'name': dist.metadata['Name'], 'version': dist.version,
                          'metadata_sha256': sha((dist.read_text('METADATA') or '').encode()),
                          'record_sha256': sha((dist.read_text('RECORD') or '').encode())}
    return {'python': platform.python_version(), 'platform': platform.system(), 'architecture': platform.machine(), 'packages': packages}


def intact(expected, actual):
    require(expected == actual, 'Environment drift: no repair authorized')
    require('xgrammar' not in actual['packages'], 'XGrammar must remain absent')


# Observation only: no socket/subprocess monkeypatch, no denial hook. Normal OS probes are allowed.
CHILD = r'''
import sys,os,json,hashlib,importlib,importlib.metadata as metadata
targets=json.loads(sys.argv[1]); observations={'platform_calls':[],'subprocess_events':[],'socket_events':[],'prohibited_content_opens':[]}
def profile(frame,event,arg):
 if event=='call' and frame.f_code.co_filename.replace(chr(92),'/').endswith('/platform.py'):
  name=frame.f_code.co_name
  if name in ('machine','uname','win32_ver','_win32_ver','_syscmd_ver') and name not in observations['platform_calls']:observations['platform_calls'].append(name)
def audit(event,args):
 if event=='subprocess.Popen':observations['subprocess_events'].append({'executable':str(args[0]),'arguments':str(args[1])})
 elif event.startswith('socket.'):
  observations['socket_events'].append({'operation':event,'arguments':[str(x) for x in args]})
 elif event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  path=os.fsdecode(args[0]);p=path.lower().replace(chr(92),'/')
  if any(s in p for s in ('heldout','held_out','/development/','/hf-cache/')) or p.endswith('.safetensors'):observations['prohibited_content_opens'].append(path)
sys.setprofile(profile)
sys.addaudithook(audit)
results=[]
try:
 for target in targets:
  module=importlib.import_module(target['module'])
  dist=metadata.distribution(target['package'])
  results.append({'package':target['package'],'module':target['module'],'module_path':module.__file__,
   'module_version':str(module.__version__) if hasattr(module,'__version__') else None,
   'distribution_name':dist.metadata['Name'],'distribution_version':dist.version,
   'metadata_sha256':hashlib.sha256((dist.read_text('METADATA') or '').encode()).hexdigest(),
   'record_sha256':hashlib.sha256((dist.read_text('RECORD') or '').encode()).hexdigest(),'import_success':True})
finally:
 sys.setprofile(None)
 print('R2_RESULT_JSON='+json.dumps({'results':results,'observations':observations,'torch_imported':'torch' in sys.modules,
  'forbidden_modules_present':[n for n in ('xgrammar','transformers','sentence_transformers','gateway') if n in sys.modules]},sort_keys=True),flush=True)
'''


def payload_valid(payload, targets, venv):
    if payload.get('forbidden_modules_present') or payload['observations']['prohibited_content_opens']:
        return False
    rows = payload.get('results', [])
    if len(rows) != len(targets):
        return False
    for row, target in zip(rows, targets):
        if not row['import_success'] or row['package'] != target['package'] or row['module'] != target['module']:
            return False
        if not Path(row['module_path']).resolve().is_relative_to(Path(venv).resolve()):
            return False
        identity = target['identity']
        if row['distribution_name'] != identity['name'] or row['distribution_version'] != identity['version']:
            return False
        if row['metadata_sha256'] != identity['metadata_sha256'] or row['record_sha256'] != identity['record_sha256']:
            return False
    return True


def stage_schedule(targets, launch):
    """Fixed five independent attempts, and one combined only after five PASS results."""
    require(len(targets) == 5 and tuple(t['package'] for t in targets) == ORDER, 'Wrong fixed import order')
    independent = [launch([target], 'independent', i + 1) for i, target in enumerate(targets)]
    combined = launch(targets, 'combined', 6) if all(r['passed'] for r in independent) else None
    return independent, combined


def validate_plan(plan_bytes, recorded_hash, runner_bytes, events):
    require(sha(plan_bytes) == recorded_hash, 'Plan drift')
    plan = json.loads(plan_bytes)
    require(plan['runner_sha256'] == sha(runner_bytes), 'Runner changed after freeze')
    require(Path(plan['python']).resolve() == PYTHON.resolve(), 'Wrong frozen Python')
    require(plan['child_script_sha256'] == sha(CHILD.encode()) and plan['child_script'] == CHILD, 'Child script drift')
    require(plan['maximum_processes'] == 6 and plan['independent_count'] == 5 and plan['retries'] == 0, 'Wrong import budget')
    require(plan['combined_only_if_all_independent_pass'] is True, 'Invalid combined-stage prerequisite')
    require(not any(e['event'] == 'INDEPENDENT_IMPORT_VALIDATION_STARTED' for e in events), 'No R2 retry')
    return plan


def freeze():
    require(not OUT.exists(), 'Refuse recovery overwrite')
    base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    require(subprocess.check_output(['git', 'rev-list', '-n', '1', TAG], cwd=ROOT, text=True).strip() == base, 'Base/tag mismatch')
    require(subprocess.check_output(['git', 'rev-list', '-n', '1', 'answerability-semantic-v2-decoder-v0.1-qualification-blocked'], cwd=ROOT, text=True).strip() == '36ccd603bd0bfba6ba5359bc39d3e6f4225db184', 'Historical tag mismatch')
    require(not subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=ROOT, text=True).strip(), 'Historical file modified')
    require(sha((R1 / 'DEPENDENCY_FREEZE_RECORD.md').read_bytes()) == '7a426b0ab5902d1b0751744c5a7a6890b986af7b7ddbff42f49075411146fbe6', 'R1 checkpoint mismatch')
    expected = json.loads((R1 / 'POST_ENABLE_PACKAGE_INVENTORY.json').read_bytes())
    actual = inventory()
    intact(expected, actual)
    require(Path(sys.executable).resolve() == PYTHON.resolve(), 'Wrong Python executable')
    targets = []
    for name in ORDER:
        dist = metadata.distribution(name)
        require(dist.version == VERSIONS[name], 'Wrong dependency version')
        roots = [str(p)[:-12] for p in dist.files if str(p).count('/') == 1 and str(p).endswith('/__init__.py') and str(p).split('/')[0].isidentifier()]
        require(len(roots) == 1, 'Ambiguous import module')
        targets.append({'package': name, 'module': roots[0], 'identity': actual['packages'][name], 'module_evidence': roots[0] + '/__init__.py'})
    lock = json.loads((R1 / 'DEPENDENCY_LOCK.json').read_bytes())
    payload_counts = {}
    for row in lock['new_packages']:
        path = Path(lock['wheelhouse']) / row['filename']
        require(sha(path.read_bytes()) == row['sha256'], 'Frozen wheel mismatch')
        dist = metadata.distribution(row['package'])
        with zipfile.ZipFile(path) as wheel:
            names = [p for p in wheel.namelist() if not p.endswith('/') and not p.endswith('.dist-info/RECORD')]
            for name in names:
                require(Path(dist.locate_file(name)).read_bytes() == wheel.read(name), 'Installed payload mismatch')
            payload_counts[row['package']] = len(names)
    OUT.mkdir()
    event('PRECONDITION_VERIFIED', {'base_commit': base, 'base_tag': TAG, 'initial_clean_worktree': True})
    event('R1_FAILURE_VERIFIED', {'outcome': 'OWNER_REVIEWED / DEPENDENCY_ENABLEMENT_FAILED', 'classification': 'IMPORT_VALIDATION_HARNESS_INTERFERENCE', 'record_sha256': sha((R1 / 'DEPENDENCY_FREEZE_RECORD.md').read_bytes())})
    write('STARTING_ENVIRONMENT_RECEIPT.json', {'r1_post_inventory_sha256': sha((R1 / 'POST_ENABLE_PACKAGE_INVENTORY.json').read_bytes()), 'inventory_exact_match': True, 'payload_counts': payload_counts, 'package_additions': 0, 'package_removals': 0, 'version_changes': 0, 'record_drift': 0})
    event('FROZEN_POST_INSTALL_STATE_VERIFIED', read('STARTING_ENVIRONMENT_RECEIPT.json'))
    write('PRE_VALIDATION_PACKAGE_INVENTORY.json', actual)
    event('PRE_VALIDATION_INVENTORY_WRITTEN', {'sha256': sha((OUT / 'PRE_VALIDATION_PACKAGE_INVENTORY.json').read_bytes())})
    plan = {'python': str(PYTHON), 'cwd': str(PYTHON.parent.parent), 'venv': str(PYTHON.parent.parent),
            'environment_overrides': {'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'PIP_NO_INDEX': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1'},
            'python_flags': ['-I', '-B'], 'targets': targets, 'child_script': CHILD, 'child_script_sha256': sha(CHILD.encode()),
            'runner_sha256': sha(Path(__file__).read_bytes()), 'timeout_seconds': 120,
            'independent_count': 5, 'combined_only_if_all_independent_pass': True, 'maximum_processes': 6, 'retries': 0,
            'subprocess_guard': 'NONE_OBSERVATION_ONLY', 'socket_monkeypatch': False}
    write('IMPORT_VALIDATION_PLAN.json', plan)
    event('R2_IMPORT_PLAN_FROZEN', {'sha256': sha((OUT / 'IMPORT_VALIDATION_PLAN.json').read_bytes())})
    print('R2 plan frozen; no dependency imports executed.')


def run():
    events = [json.loads(line) for line in (OUT / 'IMPORT_RECOVERY_JOURNAL.jsonl').read_text().splitlines()]
    frozen = [e for e in events if e['event'] == 'R2_IMPORT_PLAN_FROZEN']
    require(len(frozen) == 1, 'Exactly one frozen plan required')
    plan = validate_plan((OUT / 'IMPORT_VALIDATION_PLAN.json').read_bytes(), frozen[0]['details']['sha256'], Path(__file__).read_bytes(), events)
    intact(read('PRE_VALIDATION_PACKAGE_INVENTORY.json'), inventory())
    env = dict(os.environ, **plan['environment_overrides'])
    def launch(targets, stage, sequence):
        require(1 <= sequence <= 6, 'Import process budget exceeded')
        prefix = 'INDEPENDENT' if stage == 'independent' else 'COMBINED'
        event(prefix + '_IMPORT_VALIDATION_STARTED', {'sequence': sequence, 'modules': [t['module'] for t in targets]})
        start = time.monotonic()
        cmd = [plan['python'], *plan['python_flags'], '-c', plan['child_script'], json.dumps(targets)]
        try:
            result = subprocess.run(cmd, cwd=plan['cwd'], env=env, capture_output=True, text=True, encoding='utf-8', timeout=plan['timeout_seconds'])
            code, stdout, stderr, timed_out = result.returncode, result.stdout, result.stderr, False
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr, timed_out = None, exc.stdout or b'', exc.stderr or b'', True
            stdout = stdout.decode('utf-8', errors='replace') if isinstance(stdout, bytes) else stdout
            stderr = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else stderr
        marker = [s[len('R2_RESULT_JSON='):] for s in stdout.splitlines() if s.startswith('R2_RESULT_JSON=')]
        try:
            payload = json.loads(marker[0]) if len(marker) == 1 else None
            valid = payload is not None and payload_valid(payload, targets, plan['venv'])
        except (ValueError, KeyError, TypeError):
            payload, valid = None, False
        row = {'sequence': sequence, 'stage': stage, 'targets': [t['module'] for t in targets], 'python': plan['python'],
               'cwd': plan['cwd'], 'environment_overrides': plan['environment_overrides'], 'exit_code': code,
               'stdout': stdout, 'stderr': stderr, 'elapsed_seconds': time.monotonic() - start, 'timeout': timed_out,
               'payload': payload, 'passed': code == 0 and valid}
        write(f'IMPORT_PROCESS_{sequence:02d}.json', row)
        event(prefix + '_IMPORT_VALIDATION_COMPLETED', {'sequence': sequence, 'passed': row['passed'], 'exit_code': code})
        print(stage, sequence, row['targets'], 'PASS' if row['passed'] else 'FAIL', flush=True)
        return row
    independent, combined = stage_schedule(plan['targets'], launch)
    write('INDEPENDENT_IMPORT_RESULTS.json', independent)
    write('COMBINED_IMPORT_RESULT.json', combined if combined is not None else {'status': 'NOT_RUN', 'reason': 'Stage A not 5/5 PASS'})
    post = inventory()
    write('POST_VALIDATION_PACKAGE_INVENTORY.json', post)
    event('POST_VALIDATION_INVENTORY_WRITTEN', {'sha256': sha((OUT / 'POST_VALIDATION_PACKAGE_INVENTORY.json').read_bytes())})
    drift = read('PRE_VALIDATION_PACKAGE_INVENTORY.json') == post
    event('PACKAGE_DRIFT_CHECKED', {'unchanged': drift, 'xgrammar_absent': 'xgrammar' not in post['packages']})
    check = subprocess.run([plan['python'], '-B', '-m', 'pip', 'check'], cwd=plan['cwd'], env=env, capture_output=True, text=True)
    write('POST_VALIDATION_PIP_CHECK.json', {'returncode': check.returncode, 'stdout': check.stdout, 'stderr': check.stderr})
    event('POST_VALIDATION_PIP_CHECKED', {'returncode': check.returncode})
    intact_env = drift and check.returncode == 0 and 'xgrammar' not in post['packages']
    outcome = ('DEPENDENCIES_ENABLED_AWAITING_DECODER_REQUALIFICATION' if intact_env and combined and combined['passed']
               else 'IMPORT_RECOVERY_FAILED' if intact_env else 'IMPORT_RECOVERY_BLOCKED')
    write('RECOVERY_OUTCOME.json', {'outcome': outcome, 'review_status': 'CANDIDATE_AWAITING_OWNER_REVIEW',
                                  'independent_pass_count': sum(r['passed'] for r in independent), 'combined_pass': bool(combined and combined['passed']),
                                  'import_processes': 5 + int(combined is not None), 'retries': 0, 'environment_unchanged': drift})
    event('RECOVERY_OUTCOME_DETERMINED', read('RECOVERY_OUTCOME.json'))
    print(outcome)


if __name__ == '__main__':
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
