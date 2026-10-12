"""A2.1-F exact local-wheel enablement. No structural or semantic qualification."""
import argparse
import base64
import csv
import datetime
from email.parser import BytesParser
import hashlib
import importlib.metadata as metadata
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'artifacts/answerability_semantic_v2_lmfe_enablement'
BASE = 'cfe69ac260fabac26b1b91fb9fec5f2bba5b8ded'
TAG = 'answerability-semantic-v2-decoder-replacement-v0.1-pre-install'
PYTHON = Path.home() / '.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe'
PINS = {
    'interegular': ('0.3.3', 'interegular-0.3.3-py37-none-any.whl', 'b0c07007d48c89d6d19f7204972d369b2a77222722e126b6aa63aa721dc3b19c'),
    'lm-format-enforcer': ('0.11.3', 'lm_format_enforcer-0.11.3-py3-none-any.whl', 'cf586350875def1ae7a8fba84fcbbfc8371424b6c9d05c1fcba70aa233fbf06f'),
}
SCHEMA = ROOT / 'artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json'
SCHEMA_SHA = '6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(name, value):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def read(name):
    return json.loads((OUT / name).read_bytes())


def journal(event, details):
    with (OUT / 'LMFE_ENABLEMENT_JOURNAL.jsonl').open('ab') as f:
        f.write((json.dumps({'event': event, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'details': details}, sort_keys=True) + '\n').encode())


def events():
    return [json.loads(line) for line in (OUT / 'LMFE_ENABLEMENT_JOURNAL.jsonl').read_text().splitlines()]


def inventory():
    packages = {}
    for d in metadata.distributions():
        key = canonicalize_name(d.metadata['Name'])
        require(key not in packages, 'Duplicate distribution: ' + key)
        packages[key] = {'name': d.metadata['Name'], 'version': d.version,
                         'metadata_sha256': sha((d.read_text('METADATA') or '').encode()),
                         'record_sha256': sha((d.read_text('RECORD') or '').encode())}
    return {'python': '.'.join(map(str, sys.version_info[:3])), 'platform': 'Windows' if os.name == 'nt' else os.name,
            'architecture': os.environ.get('PROCESSOR_ARCHITECTURE'), 'packages': packages}


def frozen_integrity():
    require(sha(SCHEMA.read_bytes()) == SCHEMA_SHA, 'Schema changed')
    old = ROOT / 'artifacts/answerability_semantic_v2_decoder_replacement_prereg'
    require(sha((old / 'PREREGISTRATION_RECORD.md').read_bytes()) == '6287e085b5414f00c7f584d5cf34622bb134875a29b302e4879d6ba9356e6400', 'Owner record changed')
    hist = json.loads((old / 'HISTORICAL_INTEGRITY_RECEIPT.json').read_bytes())
    for path, expected in hist['sha256'].items():
        require(sha((ROOT / path).read_bytes()) == expected, 'Historical file changed: ' + path)
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE, 'HEAD drift')
    require(subprocess.check_output(['git', 'rev-list', '-n', '1', TAG], cwd=ROOT, text=True).strip() == BASE, 'Tag drift')
    require(subprocess.check_output(['git', 'rev-list', '-n', '1', 'answerability-semantic-v2-xgrammar-v0.2-required-field-failure'], cwd=ROOT, text=True).strip() == '6e05245a6f7971ab05101bc2b24de42180a614cd', 'Historical tag drift')
    changes = subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=ROOT, text=True).splitlines()
    require(set(changes) <= {'.gitattributes'}, 'Existing tracked files changed: ' + str(changes))
    return {'historical_receipt_files_verified': len(hist['sha256']), 'existing_tracked_changes': changes,
            'method': 'Historical non-benchmark hashes plus Git tracked-change verification; no benchmark/private content parsed.',
            'all_historical_scopes_unchanged': True}


def run(command, timeout=120):
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PIP_DISABLE_PIP_VERSION_CHECK='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env)
    return {'command': list(map(str, command)), 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def pip_check():
    return run([str(PYTHON), '-B', '-m', 'pip', 'check'])


def wheel_check(name, filename, data):
    require(name in PINS, 'Unauthorized distribution')
    require(filename == PINS[name][1], 'Unauthorized wheel filename')
    require(sha(data) == PINS[name][2], 'Wheel SHA mismatch')


def dependency_graph(receipts, packages):
    versions = {n: row['version'] for n, row in packages.items()}
    versions.update({n: v[0] for n, v in PINS.items()})
    expected = ['pydantic>=1.10.8', 'interegular>=0.3.2', 'packaging', 'pyyaml']
    def identity(raw):
        req = Requirement(raw)
        return (canonicalize_name(req.name), str(req.specifier), tuple(sorted(req.extras)), str(req.marker) if req.marker else None)
    actual = receipts['lm-format-enforcer']['requires_dist']
    require(len(actual) == len(expected) and {identity(r) for r in actual} == {identity(r) for r in expected}, 'Unexpected LMFE dependency declaration')
    result = {}
    for name, row in receipts.items():
        result[name] = []
        for raw in row['requires_dist']:
            r = Requirement(raw)
            active = r.marker is None or r.marker.evaluate({'extra': ''})
            v = versions.get(canonicalize_name(r.name))
            require(not active or v is not None and v in r.specifier, 'Unresolved dependency: ' + raw)
            if name == 'interegular':
                require(not active, 'Unexpected mandatory interegular dependency: ' + raw)
            result[name].append({'requirement': raw, 'applicable': active, 'resolved_version': v, 'satisfied': True})
    return result


def package_diff(before, after):
    require(all(after.get(n) == v for n, v in before.items()), 'Pre-existing package METADATA/RECORD/version drift')
    require(set(after) - set(before) == set(PINS), 'Unexpected package addition')
    for n, pin in PINS.items():
        require(after[n]['version'] == pin[0], 'Wrong installed version')
    return {'additions': {n: after[n]['version'] for n in PINS}, 'removals': [], 'version_changes': [], 'unexpected_metadata_record_drift': 0}


def install_command(path):
    return [str(PYTHON), '-B', '-m', 'pip', 'install', '--no-deps', '--no-index', '--no-cache-dir', '--disable-pip-version-check', str(path)]


def validate_lock(lock, rows, digest):
    require(lock['packages'] == [{'name': n, 'version': v[0], 'filename': v[1], 'sha256': v[2]} for n, v in PINS.items()], 'Wrong lock package set/order')
    require([r['event'] for r in rows].count('DEPENDENCY_PLAN_FROZEN') == 1, 'Plan not frozen exactly once')
    freeze = next(r for r in rows if r['event'] == 'DEPENDENCY_PLAN_FROZEN')
    require(freeze['details']['sha256'] == digest, 'Lock changed after freeze')
    require(not any(r['event'] == 'INSTALL_BEGIN' for r in rows), 'Installation already attempted; no retry')


def preflight():
    require(Path(sys.executable).resolve() == PYTHON.resolve(), 'Wrong Python environment')
    require(not OUT.exists(), 'Refuse overwrite')
    integrity = frozen_integrity()
    before = inventory()
    expected = json.loads((ROOT / 'artifacts/answerability_semantic_v2_decoder_replacement_prereg/ENVIRONMENT_METADATA_SNAPSHOT.json').read_bytes())
    require(before == expected, 'Pre-install environment drift')
    require(not set(PINS).intersection(before['packages']), 'Target package already installed')
    OUT.mkdir()
    journal('PRECONDITION_VERIFIED', {'base': BASE, 'tag': TAG, 'initial_clean_status': True})
    write('PRE_HISTORICAL_INTEGRITY.json', integrity)
    write('PRE_ENABLE_PACKAGE_INVENTORY.json', before)
    health = pip_check()
    write('PRE_ENABLE_PIP_CHECK.json', health)
    require(health['returncode'] == 0, 'Pre-install pip check failed')
    journal('PRE_ENVIRONMENT_VERIFIED', {'package_count': len(before['packages']), 'inventory_sha256': sha((OUT / 'PRE_ENABLE_PACKAGE_INVENTORY.json').read_bytes())})


def plan(wheelhouse):
    house = Path(wheelhouse).resolve()
    require(not house.is_relative_to(ROOT), 'Wheelhouse inside repository')
    require(inventory() == read('PRE_ENABLE_PACKAGE_INVENTORY.json'), 'Environment changed before plan')
    receipts = {}
    for name, pin in PINS.items():
        path = house / pin[1]
        data = path.read_bytes()
        wheel_check(name, path.name, data)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            entries = [n for n in z.namelist() if n.endswith('.dist-info/METADATA')]
            require(len(entries) == 1, 'Ambiguous wheel metadata')
            raw = z.read(entries[0]); m = BytesParser().parsebytes(raw)
            require(canonicalize_name(m['Name']) == name and m['Version'] == pin[0], 'Metadata identity mismatch')
            require(bool(m['Requires-Python']) and '.'.join(map(str, sys.version_info[:3])) in SpecifierSet(m['Requires-Python']), 'Python compatibility ambiguity')
            receipts[name] = {'name': m['Name'], 'version': m['Version'], 'requires_python': m['Requires-Python'], 'requires_dist': m.get_all('Requires-Dist') or [], 'metadata_text': raw.decode(), 'metadata_sha256': sha(raw), 'wheel_filename': path.name, 'wheel_sha256': sha(data)}
    graph = dependency_graph(receipts, read('PRE_ENABLE_PACKAGE_INVENTORY.json')['packages'])
    write('LMFE_WHEEL_METADATA_RECEIPT.json', {'wheels': receipts, 'resolved_dependency_graph': graph})
    lock = {'wheelhouse': str(house), 'packages': [{'name': n, 'version': v[0], 'filename': v[1], 'sha256': v[2]} for n, v in PINS.items()], 'install_order': list(PINS), 'mode': ['--no-deps', '--no-index'], 'resolver_selection': False}
    write('LMFE_DEPENDENCY_LOCK.json', lock)
    journal('DEPENDENCY_PLAN_FROZEN', {'sha256': sha((OUT / 'LMFE_DEPENDENCY_LOCK.json').read_bytes())})


def install():
    lock = read('LMFE_DEPENDENCY_LOCK.json')
    validate_lock(lock, events(), sha((OUT / 'LMFE_DEPENDENCY_LOCK.json').read_bytes()))
    require(inventory() == read('PRE_ENABLE_PACKAGE_INVENTORY.json'), 'Environment drift before installation')
    for name, pin in PINS.items():
        path = Path(lock['wheelhouse']) / pin[1]
        wheel_check(name, path.name, path.read_bytes())
    journal('INSTALL_BEGIN', {'lock_sha256': sha((OUT / 'LMFE_DEPENDENCY_LOCK.json').read_bytes())})
    for name, pin in PINS.items():
        command = install_command(Path(lock['wheelhouse']) / pin[1])
        journal('PACKAGE_INSTALL_BEGIN', {'name': name, 'command': command})
        result = run(command)
        write('INSTALL_' + name + '.json', result)
        require(result['returncode'] == 0, 'Installation failed; no retries: ' + name)
        journal('PACKAGE_INSTALL_COMPLETE', {'name': name, 'version': pin[0]})
    after = inventory()
    write('POST_ENABLE_PACKAGE_INVENTORY.json', after)
    diff = package_diff(read('PRE_ENABLE_PACKAGE_INVENTORY.json')['packages'], after['packages'])
    write('PACKAGE_DIFF.json', diff)
    health = pip_check()
    write('POST_ENABLE_PIP_CHECK.json', health)
    require(health['returncode'] == 0, 'New dependency conflict')
    journal('INSTALLATION_VERIFIED', diff)


def payload_verify():
    lock = read('LMFE_DEPENDENCY_LOCK.json'); rows = []
    for name, pin in PINS.items():
        dist = metadata.distribution(name)
        require(dist.version == pin[0], 'Installed version mismatch')
        wheel = Path(lock['wheelhouse']) / pin[1]
        wheel_check(name, wheel.name, wheel.read_bytes())
        checked = []
        with zipfile.ZipFile(wheel) as z:
            for entry in z.infolist():
                if entry.is_dir() or entry.filename.endswith('.dist-info/RECORD'):
                    continue
                require('.data/' not in entry.filename, 'Unmapped wheel data scheme')
                installed = Path(dist.locate_file(entry.filename)).resolve()
                require(installed.is_relative_to(PYTHON.parent.parent.resolve()), 'Installed path outside venv')
                require(installed.read_bytes() == z.read(entry), 'Installed wheel payload mismatch: ' + entry.filename)
                checked.append({'path': entry.filename, 'sha256': sha(installed.read_bytes())})
        records = []
        for path, digest, size in csv.reader(io.StringIO(dist.read_text('RECORD'))):
            if not digest:
                records.append({'path': path, 'status': 'RECORD_UNHASHED_ENTRY'}); continue
            algorithm, value = digest.split('=', 1)
            require(algorithm == 'sha256', 'Unexpected RECORD hash algorithm')
            data = Path(dist.locate_file(path)).read_bytes()
            require(base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode() == value, 'RECORD payload mismatch')
            require(len(data) == int(size), 'RECORD size mismatch')
            records.append({'path': path, 'sha256': sha(data), 'status': 'VERIFIED'})
        module = 'lmformatenforcer' if name == 'lm-format-enforcer' else name
        rows.append({'name': name, 'version': dist.version, 'module_path': str(dist.locate_file(module)), 'metadata_text': dist.read_text('METADATA'), 'record_text': dist.read_text('RECORD'), 'metadata_sha256': sha(dist.read_text('METADATA').encode()), 'record_sha256': sha(dist.read_text('RECORD').encode()), 'wheel_payload_files': checked, 'installed_record_files': records, 'status': 'VERIFIED'})
    write('LMFE_INSTALLED_PAYLOAD_VERIFICATION.json', {'distributions': rows, 'status': 'VERIFIED'})


IMPORT_CHILD = r'''
import importlib, ipaddress, json, os, sys
observations={'socket_events':[], 'blocked_events':[], 'subprocess_events':[], 'prohibited_content_opens':[]}
def audit(event,args):
 if event.startswith('socket.'):
  observations['socket_events'].append({'operation':event,'arguments':[str(a) for a in args]})
  allowed=event in ('socket.__new__','socket.gethostname')
  if event=='socket.bind':
   try: allowed=ipaddress.ip_address(args[1][0]).is_loopback
   except (ValueError,IndexError,TypeError): allowed=False
  if not allowed:
   observations['blocked_events'].append(event);raise RuntimeError('Unexpected network operation: '+event)
 if event=='subprocess.Popen':
  observations['subprocess_events'].append(str(args))
  command=args[1]
  allowed=(isinstance(command,(list,tuple)) and len(command)==3 and os.path.basename(str(command[0])).lower() in ('cmd','cmd.exe') and list(command[1:])==['/c','ver']) or (isinstance(command,str) and command.lower().strip().endswith(' /c ver'))
  if not allowed: raise RuntimeError('Unexpected import subprocess')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.fsdecode(args[0]).lower().replace(chr(92),'/')
  if 'heldout' in p or 'held_out' in p or '/hf-cache/' in p or p.endswith('.safetensors') or ('/evaluation/' in p and '/development/' in p):
   observations['prohibited_content_opens'].append(p);raise RuntimeError('Prohibited content access')
def profile(frame,event,arg):
 if event!='call':return
 name=frame.f_code.co_name; path=frame.f_code.co_filename.lower().replace(chr(92),'/')
 if name in ('generate','forward','from_pretrained','build_transformers_prefix_allowed_tokens_fn') or (name=='__init__' and path.endswith('/lmformatenforcer/jsonschemaparser.py')):
  observations['blocked_events'].append(path+':'+name);raise RuntimeError('Scientific execution forbidden')
sys.addaudithook(audit);sys.setprofile(profile)
result={}
try:
 for target in ('interegular','lmformatenforcer'):
  module=importlib.import_module(target);result[target]={'import':'PASS','module_path':module.__file__}
 result['lmformatenforcer.JsonSchemaParser']=callable(getattr(sys.modules['lmformatenforcer'],'JsonSchemaParser',None))
 module=importlib.import_module('lmformatenforcer.integrations.transformers')
 result['lmformatenforcer.integrations.transformers.build_transformers_prefix_allowed_tokens_fn']=callable(getattr(module,'build_transformers_prefix_allowed_tokens_fn',None))
 result['status']='PASS'
finally:
 sys.setprofile(None)
 print('LMFE_API_RESULT='+json.dumps({'results':result,'observations':observations},sort_keys=True),flush=True)
'''


def api_valid(payload):
    r = payload['results']; o = payload['observations']
    require(not o['blocked_events'] and not o['prohibited_content_opens'], 'Import boundary violated')
    require(r.get('status') == 'PASS', 'Imports failed')
    require(all(r.get(n, {}).get('import') == 'PASS' for n in ('interegular', 'lmformatenforcer')), 'Required import absent')
    for key in ('lmformatenforcer.JsonSchemaParser', 'lmformatenforcer.integrations.transformers.build_transformers_prefix_allowed_tokens_fn'):
        require(r.get(key) is True, 'Missing API: ' + key)


def validate():
    require(not any(r['event'] == 'IMPORT_BEGIN' for r in events()), 'No import retry allowed')
    require(any(r['event'] == 'INSTALLATION_VERIFIED' for r in events()), 'Installation not verified')
    payload_verify()
    journal('IMPORT_BEGIN', {'mode': 'fresh process; import/API presence only'})
    result = run([str(PYTHON), '-B', '-c', IMPORT_CHILD], timeout=180)
    write('LMFE_IMPORT_PROCESS.json', result)
    require(result['returncode'] == 0, 'Import failure; no retry')
    line = next(x for x in result['stdout'].splitlines() if x.startswith('LMFE_API_RESULT='))
    payload = json.loads(line.split('=', 1)[1])
    write('LMFE_IMPORT_API_RESULTS.json', payload)
    api_valid(payload)
    final = inventory()
    require(final == read('POST_ENABLE_PACKAGE_INVENTORY.json'), 'Import-time environment drift')
    write('POST_IMPORT_PACKAGE_INVENTORY.json', final)
    write('POST_HISTORICAL_INTEGRITY.json', frozen_integrity())
    require(sha((OUT / 'LMFE_DEPENDENCY_LOCK.json').read_bytes()) == next(r for r in events() if r['event'] == 'DEPENDENCY_PLAN_FROZEN')['details']['sha256'], 'Lock changed')
    journal('ENABLEMENT_COMPLETE', {'outcome': 'LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE'})
    write('LMFE_ENABLEMENT_OUTCOME.json', {'outcome': 'LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE', 'review_status': 'CANDIDATE_AWAITING_OWNER_REVIEW', 'capability': 'NOT_ASSESSED', 'V2': 'PRE_REGISTERED_NOT_EVALUATED', 'fresh_semantic_suite': 'NOT YET AUTHORED', 'counters': {n: 0 for n in ['Qwen_initialization','generate','forward','semantic_outputs','V2_parser_constructions','V2_parser_conformance_executions','M1','M2','M3','M4','M5','M6','M7','M8','DEVELOPMENT','retrieval']}, 'Phase_2H_HELD_OUT_access': False, 'Phase_2G_private_HELDOUT_access': False})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['preflight','plan','install','validate'])
    parser.add_argument('--wheelhouse')
    args = parser.parse_args()
    try:
        require(Path(sys.executable).resolve() == PYTHON.resolve(), 'Wrong environment')
        require(not (OUT / 'LMFE_ENABLEMENT_OUTCOME.json').exists(), 'Prior terminal outcome; no retry authorized')
        if args.stage == 'plan':
            plan(args.wheelhouse)
        else:
            globals()[args.stage]()
        print(args.stage + ': PASS')
    except Exception as exc:
        if OUT.exists() and not (OUT / 'LMFE_ENABLEMENT_OUTCOME.json').exists():
            mutated = any(r['event'] == 'INSTALL_BEGIN' for r in events())
            outcome = 'LMFE_ENABLEMENT_FAILED' if mutated else 'LMFE_ENABLEMENT_BLOCKED'
            journal(outcome, {'error': repr(exc), 'stage': args.stage})
            write('LMFE_ENABLEMENT_OUTCOME.json', {'outcome': outcome, 'error': repr(exc), 'stage': args.stage})
        raise


if __name__ == '__main__':
    main()
