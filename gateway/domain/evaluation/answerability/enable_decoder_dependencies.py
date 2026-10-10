"""A2.1-R exact dependency enablement; never installs/imports a decoder or model."""
import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from email.parser import BytesParser
import zipfile

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import sys_tags
from packaging.utils import canonicalize_name, parse_wheel_filename

BASE = '36ccd603bd0bfba6ba5359bc39d3e6f4225db184'
TAG = 'answerability-semantic-v2-decoder-v0.1-qualification-blocked'
PINS = {
    'apache-tvm-ffi': ('0.1.14.post1', 'apache_tvm_ffi-0.1.14.post1-cp312-cp312-win_amd64.whl', 'fd3edd7ccb4fb90092845f4db10ddec92696a5119842062222a9abd3e719565e'),
    'pydantic': ('2.13.5', 'pydantic-2.13.5-py3-none-any.whl', '346a034f080da3755d8e9cb5e00e8b07de1d39e4f6e2c87d8ab7cafa0b269a73'),
    'pydantic-core': ('2.46.5', 'pydantic_core-2.46.5-cp312-cp312-win_amd64.whl', '5e81740c09e310f5aa5cbd3e434a01c154d4bef93241c7877b39f211d2b78ba8'),
    'annotated-types': ('0.8.0', 'annotated_types-0.8.0-py3-none-any.whl', 'f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0'),
    'typing-inspection': ('0.4.4', 'typing_inspection-0.4.4-py3-none-any.whl', '65b8397ba37ccbce054456aaccddfc91e6e3083c92824df348d96ca832f3f147'),
}
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'artifacts/answerability_semantic_v2_decoder_dependency_enablement'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def serialized(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def write(name, value):
    path = OUT / name
    with path.open('xb') as stream:
        stream.write(serialized(value))


def read(name):
    return json.loads((OUT / name).read_bytes())


def journal(event, details):
    with (OUT / 'DEPENDENCY_ENABLEMENT_JOURNAL.jsonl').open('ab') as stream:
        stream.write((json.dumps({'event': event, 'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'details': details}, sort_keys=True) + '\n').encode())


def inventory():
    packages = {}
    for dist in metadata.distributions():
        name = canonicalize_name(dist.metadata['Name'])
        require(name not in packages, 'Duplicate installed distribution')
        packages[name] = {'name': dist.metadata['Name'], 'version': dist.version,
                          'metadata_sha256': digest((dist.read_text('METADATA') or '').encode()),
                          'record_sha256': digest((dist.read_text('RECORD') or '').encode())}
    return {'python': platform.python_version(), 'platform': platform.system(),
            'architecture': platform.machine(), 'packages': packages}


def typing_check(packages):
    require('typing-extensions' in packages, 'typing-extensions absent')
    require(packages['typing-extensions']['version'] in SpecifierSet('>=4.14.1'), 'typing-extensions too old')


def wheel_check(name, filename, data):
    require(name in PINS, 'Unauthorized dependency')
    version, expected_file, expected_hash = PINS[name]
    require(filename == expected_file, 'Wrong wheel filename')
    require(digest(data) == expected_hash, 'Wheel SHA mismatch')
    parsed_name, parsed_version, _, tags = parse_wheel_filename(filename)
    require(canonicalize_name(parsed_name) == name and str(parsed_version) == version, 'Wrong version')
    require(bool(set(sys_tags()) & tags), 'Incompatible wheel platform')


def requirement_check(raw, versions):
    req = Requirement(raw)
    active = req.marker is None or req.marker.evaluate({'extra': ''})
    version = versions.get(canonicalize_name(req.name))
    return {'requirement': raw, 'name': canonicalize_name(req.name), 'applicable': active,
            'resolved_version': version,
            'satisfied': not active or version is not None and (not req.specifier or version in req.specifier)}


def resolve_graph(receipts, preserved):
    versions = {k: v['version'] for k, v in preserved.items()}
    versions.update({k: PINS[k][0] for k in receipts})
    edges = {k: [requirement_check(raw, versions) for raw in v['requires_dist']] for k, v in receipts.items()}
    require(all(e['satisfied'] for rows in edges.values() for e in rows), 'Unresolved mandatory dependency')
    pending = set(receipts)
    order = []
    while pending:
        ready = sorted(k for k in pending if not any(e['applicable'] and e['name'] in pending for e in edges[k]))
        require(bool(ready), 'Cyclic/ambiguous dependency graph')
        order.extend(ready)
        pending.difference_update(ready)
    return edges, order


def drift_check(before, after, new):
    require(all(after.get(k) == v for k, v in before.items()), 'Pre-existing package drift')
    require(set(after) - set(before) == set(new), 'Unexpected added packages')
    for name in new:
        require(after[name]['version'] == PINS[name][0], 'Installed version mismatch')
    require('xgrammar' not in after, 'XGrammar must remain absent')


def install_command(paths):
    return [sys.executable, '-B', '-m', 'pip', 'install', '--no-deps', '--no-index', '--no-cache-dir', '--disable-pip-version-check', *map(str, paths)]


def pip_check():
    result = subprocess.run([sys.executable, '-B', '-m', 'pip', 'check'], capture_output=True, text=True)
    return {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def preflight():
    require(not OUT.exists(), 'Refuse overwrite')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE, 'Wrong HEAD')
    require(subprocess.check_output(['git', 'rev-list', '-n', '1', TAG], cwd=ROOT, text=True).strip() == BASE, 'Wrong tag')
    # Initial clean status was checked before this helper was authored. Allow only this helper now.
    changes = subprocess.check_output(['git', 'status', '--short', '--untracked-files=all'], cwd=ROOT, text=True).splitlines()
    allowed = {'?? gateway/domain/evaluation/answerability/enable_decoder_dependencies.py', '?? gateway/domain/tests/test_decoder_dependency_enablement.py'}
    require(set(changes) <= allowed, 'Unexpected worktree changes')
    require(subprocess.check_output(['git', 'rev-list', '-n', '1', 'answerability-semantic-gate-v0.2-pre-decoder'], cwd=ROOT, text=True).strip() == '4c3d715ccf4f2026387ebf5599f36f7e234081f1', 'Wrong V2 tag')
    blocked = ROOT / 'artifacts/answerability_semantic_v2_decoder_qualification'
    require(digest((blocked / 'DECODER_FREEZE_RECORD.md').read_bytes()) == 'f0884be52d33f27288c3cf176216130ae067add36ae595fa035b2743702c8afc', 'Wrong blocked freeze')
    require(not subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=ROOT, text=True).strip(), 'Frozen tracked changes')
    inv = inventory()
    require((inv['python'], inv['platform'], inv['architecture']) == ('3.12.10', 'Windows', 'AMD64'), 'Wrong runtime')
    old = json.loads((blocked / 'FINAL_PACKAGE_INVENTORY.json').read_bytes())['packages']
    require({canonicalize_name(k): v for k, v in old.items()} == {k: v['version'] for k, v in inv['packages'].items()}, 'Package version drift')
    typing_check(inv['packages'])
    require('xgrammar' not in inv['packages'], 'XGrammar already installed')
    OUT.mkdir()
    journal('PRECONDITION_VERIFIED', {'base_commit': BASE, 'base_tag': TAG, 'initial_clean_worktree': True})
    journal('BLOCKED_ATTEMPT_VERIFIED', {'record_sha256': digest((blocked / 'DECODER_FREEZE_RECORD.md').read_bytes())})
    journal('FROZEN_RUNTIME_VERIFIED', {'python': inv['python'], 'unchanged_package_count': len(inv['packages'])})
    write('PRE_ENABLE_PACKAGE_INVENTORY.json', inv)
    journal('PRE_ENABLE_INVENTORY_WRITTEN', {'sha256': digest((OUT / 'PRE_ENABLE_PACKAGE_INVENTORY.json').read_bytes())})
    write('PRE_ENABLE_PIP_CHECK.json', pip_check())
    journal('ROOT_DEPENDENCIES_AUTHORIZED', {'pins': PINS})
    journal('TYPING_EXTENSIONS_COMPATIBILITY_VERIFIED', inv['packages']['typing-extensions'])
    wheelhouse = Path(tempfile.mkdtemp(prefix='phase2h-a21r-wheels-')).resolve()
    require(not wheelhouse.is_relative_to(ROOT), 'Wheelhouse must be outside repository')
    write('WHEELHOUSE_LOCATION.json', {'path': str(wheelhouse)})
    print('Preflight PASS; external wheelhouse:', wheelhouse)


def acquire():
    import urllib.request
    pre = read('PRE_ENABLE_PACKAGE_INVENTORY.json')['packages']
    house = Path(read('WHEELHOUSE_LOCATION.json')['path'])
    require(not (OUT / 'WHEEL_INVENTORY.json').exists(), 'No acquisition rerun')
    rows = []
    for name, (version, filename, expected) in PINS.items():
        if name in pre:
            continue
        path = house / filename
        require(not path.exists(), 'No wheel overwrite/redownload')
        source = f'https://pypi.org/pypi/{name}/{version}/json'
        journal('WHEEL_ACQUISITION_STARTED', {'package': name, 'version': version, 'metadata_url': source})
        with urllib.request.urlopen(source, timeout=60) as response:
            release = json.load(response)
        matches = [x for x in release['urls'] if x['filename'] == filename]
        require(len(matches) == 1, 'Exact wheel unavailable')
        info = matches[0]
        require(not info['yanked'], 'Yanked wheel forbidden')
        require(info['digests']['sha256'] == expected, 'Published hash mismatch')
        require(info['url'].startswith('https://files.pythonhosted.org/'), 'Unexpected package host')
        with urllib.request.urlopen(info['url'], timeout=60) as response:
            data = response.read()
        with path.open('xb') as stream:
            stream.write(data)
        wheel_check(name, filename, data)
        events = [json.loads(line) for line in (OUT / 'DEPENDENCY_ENABLEMENT_JOURNAL.jsonl').read_text().splitlines()]
        prior_lost_downloads = sum(e['event'] == 'WHEEL_PERSISTENCE_FAILED' and e['details']['package'] == name for e in events)
        row = {'package': name, 'version': version, 'filename': filename, 'source': info['url'], 'metadata_source': source,
               'size': len(data), 'sha256': digest(data), 'download_count': 1 + prior_lost_downloads,
               'verified_saved_copies': 1, 'prior_unsaved_transfers': prior_lost_downloads, 'yanked': info['yanked']}
        rows.append(row)
        journal('WHEEL_ACQUIRED_AND_VERIFIED', row)
        print(name, version, 'SHA verified', flush=True)
    write('WHEEL_INVENTORY.json', rows)
    journal('WHEELS_ACQUIRED', {'count': len(rows)})
    journal('WHEEL_HASHES_VERIFIED', {'count': len(rows)})


def plan():
    pre = read('PRE_ENABLE_PACKAGE_INVENTORY.json')['packages']
    require(pre == inventory()['packages'], 'Runtime changed before plan')
    house = Path(read('WHEELHOUSE_LOCATION.json')['path'])
    receipts = {}
    for item in read('WHEEL_INVENTORY.json'):
        name = item['package']
        path = house / item['filename']
        wheel_check(name, path.name, path.read_bytes())
        with zipfile.ZipFile(path) as wheel:
            meta_names = [n for n in wheel.namelist() if n.endswith('.dist-info/METADATA')]
            require(len(meta_names) == 1, 'Ambiguous METADATA')
            raw = wheel.read(meta_names[0])
            meta = BytesParser().parsebytes(raw)
            require(canonicalize_name(meta['Name']) == name and meta['Version'] == PINS[name][0], 'Wrong wheel metadata identity')
            require(platform.python_version() in SpecifierSet(meta.get('Requires-Python', '')), 'Incompatible Requires-Python')
            top = [n[:-12] for n in wheel.namelist() if n.count('/') == 1 and n.endswith('/__init__.py') and n.split('/')[0].isidentifier()]
            require(len(top) == 1, 'Ambiguous dependency import module')
            receipts[name] = {'name': meta['Name'], 'version': meta['Version'], 'requires_python': meta.get('Requires-Python'),
                              'requires_dist': meta.get_all('Requires-Dist', []), 'metadata_sha256': digest(raw),
                              'import_module': top[0], 'import_evidence': top[0] + '/__init__.py'}
    write('WHEEL_METADATA_RECEIPT.json', receipts)
    journal('WHEEL_METADATA_RESOLVED', {'sha256': digest((OUT / 'WHEEL_METADATA_RECEIPT.json').read_bytes())})
    edges, order = resolve_graph(receipts, pre)
    journal('TRANSITIVE_CLOSURE_RESOLVED', {'dependency_edges': edges, 'installation_order': order})
    lock = {'preserved_packages': pre, 'new_packages': read('WHEEL_INVENTORY.json'), 'dependency_edges': edges,
            'installation_order': order, 'forbidden_from_changing': sorted(pre), 'xgrammar_install': False,
            'install_flags': ['--no-deps', '--no-index', '--no-cache-dir', '--disable-pip-version-check'],
            'wheelhouse': str(house), 'import_modules': {k: v['import_module'] for k, v in receipts.items()}}
    write('DEPENDENCY_LOCK.json', lock)
    journal('DEPENDENCY_PLAN_FROZEN', {'sha256': digest((OUT / 'DEPENDENCY_LOCK.json').read_bytes())})
    print('Plan frozen:', order, 'modules:', lock['import_modules'])


def verified_lock():
    events = [json.loads(line) for line in (OUT / 'DEPENDENCY_ENABLEMENT_JOURNAL.jsonl').read_text().splitlines()]
    frozen = [e for e in events if e['event'] == 'DEPENDENCY_PLAN_FROZEN']
    require(len(frozen) == 1 and frozen[0]['details']['sha256'] == digest((OUT / 'DEPENDENCY_LOCK.json').read_bytes()), 'Lock hash changed')
    return read('DEPENDENCY_LOCK.json'), events


def install():
    lock, events = verified_lock()
    require(not any(e['event'] == 'DEPENDENCY_INSTALLATION_STARTED' for e in events), 'No installation retry')
    require(lock['preserved_packages'] == inventory()['packages'], 'Pre-install drift')
    paths = []
    for name in lock['installation_order']:
        path = Path(lock['wheelhouse']) / PINS[name][1]
        wheel_check(name, path.name, path.read_bytes())
        paths.append(path)
    journal('DEPENDENCY_INSTALLATION_STARTED', {'lock_sha256': digest((OUT / 'DEPENDENCY_LOCK.json').read_bytes()), 'order': lock['installation_order']})
    env = dict(os.environ, PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1', PYTHONDONTWRITEBYTECODE='1')
    for path in paths:
        cmd = install_command([path])
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        journal('PACKAGE_INSTALL_RESULT', {'command': cmd, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        require(result.returncode == 0, 'Installation failed; STOP, no repair')
    journal('DEPENDENCY_INSTALLATION_COMPLETED', {'packages': lock['installation_order']})
    print('Installation complete; no dependency resolution/index access.')


def verify():
    lock, events = verified_lock()
    require(any(e['event'] == 'DEPENDENCY_INSTALLATION_COMPLETED' for e in events), 'Installation incomplete')
    require(not (OUT / 'POST_ENABLE_PACKAGE_INVENTORY.json').exists(), 'No verification overwrite')
    post = inventory()
    write('POST_ENABLE_PACKAGE_INVENTORY.json', post)
    journal('POST_ENABLE_INVENTORY_WRITTEN', {'sha256': digest((OUT / 'POST_ENABLE_PACKAGE_INVENTORY.json').read_bytes())})
    drift_check(lock['preserved_packages'], post['packages'], lock['installation_order'])
    journal('PACKAGE_DRIFT_CHECKED', {'preexisting_changed': 0, 'new_packages': lock['installation_order'], 'xgrammar_installed': False})
    # Installed payload identity checked against wheel members, without executing them.
    payloads = {}
    for name in lock['installation_order']:
        dist = metadata.distribution(name)
        with zipfile.ZipFile(Path(lock['wheelhouse']) / PINS[name][1]) as wheel:
            members = [n for n in wheel.namelist() if not n.endswith('/') and not n.endswith('.dist-info/RECORD')]
            require(not any('.data/' in n for n in members), 'Unsupported wheel relocation; STOP')
            for member in members:
                require(Path(dist.locate_file(member)).read_bytes() == wheel.read(member), 'Installed wheel payload mismatch: ' + member)
            payloads[name] = {'wheel_payload_files_verified': len(members), 'metadata_version': dist.version}
    write('INSTALLED_PAYLOAD_VERIFICATION.json', payloads)
    check = pip_check()
    write('POST_ENABLE_PIP_CHECK.json', check)
    pre_check = read('PRE_ENABLE_PIP_CHECK.json')
    require(check['returncode'] == 0 or check == pre_check, 'New dependency conflict')
    journal('PIP_CHECK_VERIFIED', {'pre': pre_check, 'post': check})
    code = '''
import os,sys,json,importlib
blocked={'xgrammar','transformers','sentence_transformers'}
class Guard:
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in blocked:raise RuntimeError('Decoder/model import forbidden')
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event.startswith('socket.') and event not in ('socket.__new__','socket.gethostname'):
  if event=='socket.bind' and args[1][0] in ('::1','127.0.0.1'):return
  raise RuntimeError('Network prohibited during dependency import')
 if event=='subprocess.Popen':raise RuntimeError('Dependency import must not launch a build/helper process')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.fsdecode(args[0]).lower().replace(chr(92),'/')
  if any(x in p for x in ('heldout','held_out','/development/','answerability_dev_','qualification_attempt2')):raise RuntimeError('Benchmark content prohibited')
sys.addaudithook(audit)
modules=json.loads(sys.argv[1]);result={}
for package,name in modules.items():
 m=importlib.import_module(name)
 result[package]={'module':name,'path':m.__file__,'reported_version':str(m.__version__) if hasattr(m,'__version__') else None,'import_success':True}
assert not blocked.intersection(sys.modules)
print(json.dumps(result,sort_keys=True))
'''
    env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-B', '-c', code, json.dumps(lock['import_modules'])], env=env, capture_output=True, text=True, timeout=60)
    write('DEPENDENCY_IMPORT_RESULTS.json', {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
                                           'results': json.loads(result.stdout) if result.returncode == 0 else None})
    require(result.returncode == 0, 'Dependency import failure; STOP, no repair')
    journal('DEPENDENCY_IMPORTS_VERIFIED', {'packages': list(lock['import_modules']), 'decoder_imports': 0, 'model_initializations': 0})
    xwheel = ROOT / '.cache/phase2h-a21/xgrammar-0.2.8-cp312-cp312-win_amd64.whl'
    require(digest(xwheel.read_bytes()) == 'dbcf6718e049cbe429742cdb05f85c48135c2e389d45daeafb884af6994bb4a7', 'XGrammar saved wheel hash mismatch')
    with zipfile.ZipFile(xwheel) as wheel:
        meta = BytesParser().parsebytes(wheel.read('xgrammar-0.2.8.dist-info/METADATA'))
    require(meta['Name'] == 'xgrammar' and meta['Version'] == '0.2.8', 'XGrammar metadata identity mismatch')
    versions = {k: v['version'] for k, v in post['packages'].items()}
    rows = [requirement_check(raw, versions) for raw in meta.get_all('Requires-Dist', [])]
    write('XGRAMMAR_REQUIREMENT_EVALUATION.json', {'wheel_sha256': digest(xwheel.read_bytes()), 'requirements': rows,
                                               'all_satisfied': all(e['satisfied'] for e in rows), 'installed': False, 'imported': False})
    require(all(e['satisfied'] for e in rows), 'XGrammar dependency closure unsatisfied')
    journal('XGRAMMAR_REQUIREMENTS_REEVALUATED', {'all_applicable_satisfied': True, 'installed': False, 'imported': False})
    require(inventory() == post, 'Package drift during import checks')
    print('DEPENDENCIES_ENABLED_AWAITING_DECODER_REQUALIFICATION')


if __name__ == '__main__':
    {'preflight': preflight, 'acquire': acquire, 'plan': plan, 'install': install, 'verify': verify}[sys.argv[1]]()
