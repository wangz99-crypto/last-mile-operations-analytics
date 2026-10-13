"""A2.1-FR: fixed five-process import/API validation; no scientific execution."""
import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'artifacts/answerability_semantic_v2_lmfe_import_recovery'
HISTORY = ROOT / 'artifacts/answerability_semantic_v2_lmfe_enablement'
BASE = 'eaad53841caf73ad6933d7a7bf9612cea09376af'
TAG = 'answerability-semantic-v2-lmfe-v0.1-enablement-failed'
PYTHON = Path.home() / '.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe'
EXPECTED_INVENTORY = '00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d'
OVERRIDES = {'PYTHONDONTWRITEBYTECODE': '1', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1'}


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
    with (OUT / 'LMFE_IMPORT_RECOVERY_JOURNAL.jsonl').open('ab') as f:
        f.write((json.dumps({'event': name, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'details': details}, sort_keys=True) + '\n').encode())


def events():
    return [json.loads(line) for line in (OUT / 'LMFE_IMPORT_RECOVERY_JOURNAL.jsonl').read_text().splitlines()]


def inventory():
    packages = {}
    for d in metadata.distributions():
        name = re.sub(r'[-_.]+', '-', d.metadata['Name']).lower()
        require(name not in packages, 'Duplicate distribution')
        packages[name] = {'name': d.metadata['Name'], 'version': d.version,
                          'metadata_sha256': sha((d.read_text('METADATA') or '').encode()),
                          'record_sha256': sha((d.read_text('RECORD') or '').encode())}
    return {'python': '.'.join(map(str, sys.version_info[:3])), 'platform': 'Windows' if os.name == 'nt' else os.name,
            'architecture': os.environ.get('PROCESSOR_ARCHITECTURE'), 'packages': packages}


def intact(expected, actual):
    require(expected == actual, 'Complete package identity drift; no repair authorized')
    require(len(actual['packages']) == 36, 'Unexpected package count')
    for name, version in [('interegular', '0.3.3'), ('lm-format-enforcer', '0.11.3')]:
        require(actual['packages'][name]['version'] == version, 'Wrong target version')


# Observation only: no subprocess/socket monkeypatch or denial hook. Platform
# probes (including Windows quoting) execute normally. Observations are assessed
# after the child exits; the five fixed snippets contain no scientific calls.
PREFIX = r'''
import sys, os, json, inspect, importlib.metadata as md
observations={'platform_calls':[], 'subprocess_events':[], 'socket_events':[], 'scientific_calls':[], 'prohibited_content_opens':[]}
def audit(event,args):
 if event=='subprocess.Popen':
  stack=[]; frame=sys._getframe(1)
  while frame is not None:
   if frame.f_code.co_filename.replace(chr(92),'/').endswith('/platform.py'):stack.append(frame.f_code.co_name)
   frame=frame.f_back
  observations['subprocess_events'].append({'executable':str(args[0]),'command':str(args[1]),'cwd':str(args[2]),'platform_stack':stack})
 elif event.startswith('socket.'):
  observations['socket_events'].append({'operation':event,'arguments':[str(x) for x in args]})
 elif event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.fsdecode(args[0]).lower().replace(chr(92),'/')
  if 'heldout' in p or 'held_out' in p or '/hf-cache/' in p or p.endswith('.safetensors') or ('/evaluation/' in p and '/development/' in p):observations['prohibited_content_opens'].append(p)
def profile(frame,event,arg):
 if event!='call':return
 path=frame.f_code.co_filename.replace(chr(92),'/');name=frame.f_code.co_name
 if path.endswith('/platform.py') and name in ('machine','uname','win32_ver','_win32_ver','_syscmd_ver') and name not in observations['platform_calls']:observations['platform_calls'].append(name)
 if (path.endswith('/lmformatenforcer/jsonschemaparser.py') and name=='__init__') or (('/transformers/' in path or '/lmformatenforcer/' in path) and name in ('from_pretrained','generate','forward','build_transformers_prefix_allowed_tokens_fn')):observations['scientific_calls'].append({'path':path,'name':name})
sys.addaudithook(audit);sys.setprofile(profile)
results={}
def module_identity(module,distribution):
 d=md.distribution(distribution)
 return {'module_path':module.__file__,'distribution':d.metadata['Name'],'version':d.version}
def symbol_identity(symbol):
 return {'available':True,'callable':callable(symbol),'module':symbol.__module__,'source_path':inspect.getfile(symbol)}
try:
'''
SUFFIX = r'''
finally:
 sys.setprofile(None)
 print('FR_RESULT_JSON='+json.dumps({'results':results,'observations':observations,'torch_imported':'torch' in sys.modules},sort_keys=True),flush=True)
'''
SNIPPETS = [
    ('I1', 'A', "import interegular\nresults['interegular']=module_identity(interegular,'interegular')"),
    ('I2', 'A', "import lmformatenforcer\nresults['lmformatenforcer']=module_identity(lmformatenforcer,'lm-format-enforcer')"),
    ('A1', 'B', "from lmformatenforcer import JsonSchemaParser\nresults['JsonSchemaParser']=symbol_identity(JsonSchemaParser)"),
    ('A2', 'B', "from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn\nresults['build_transformers_prefix_allowed_tokens_fn']=symbol_identity(build_transformers_prefix_allowed_tokens_fn)"),
    ('C1', 'C', "import interegular\nimport lmformatenforcer\nfrom lmformatenforcer import JsonSchemaParser\nfrom lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn\nresults['interegular']=module_identity(interegular,'interegular')\nresults['lmformatenforcer']=module_identity(lmformatenforcer,'lm-format-enforcer')\nresults['JsonSchemaParser']=symbol_identity(JsonSchemaParser)\nresults['build_transformers_prefix_allowed_tokens_fn']=symbol_identity(build_transformers_prefix_allowed_tokens_fn)"),
]


def plan():
    return {'python': str(PYTHON), 'cwd': str(ROOT), 'environment_overrides': OVERRIDES,
            'max_validation_processes': 5, 'retry_policy': 'FORBIDDEN', 'timeout_seconds': 180,
            'boundary': 'Observation only. Normal Windows/platform subprocess and local capability probes allowed. No broad historical denial guard reused.',
            'forbidden': ['parser construction','M1-M8','API invocation','model/tokenizer loading','generate','forward','package mutation','network download','DEVELOPMENT','HELD_OUT','retrieval'],
            'validations': [{'id': ident, 'stage': stage, 'snippet': snippet, 'code': PREFIX + '\n'.join(' '+line for line in snippet.splitlines()) + '\n' + SUFFIX} for ident, stage, snippet in SNIPPETS]}


def permitted_next(plan_value, completed, started):
    sequence = [r['id'] for r in plan_value['validations']]
    require(sequence == ['I1','I2','A1','A2','C1'], 'Changed sequence')
    require(plan_value['max_validation_processes'] == 5, 'Wrong process budget')
    require(started == sequence[:len(completed)], 'Prior interrupted/failed attempt; no retry')
    require(all(r['pass'] for r in completed), 'Prior failure; no next stage')
    require(len(completed) < 5, 'Budget exhausted')
    require([r['id'] for r in completed] == sequence[:len(completed)], 'Invalid completed order')
    return sequence[len(completed)]


def assess(ident, payload, returncode):
    require(returncode == 0, 'Child import/API failure')
    obs = payload['observations']; result = payload['results']
    require(not obs['scientific_calls'] and not obs['prohibited_content_opens'], 'Scientific/quarantine violation')
    require(all('_syscmd_ver' in row['platform_stack'] for row in obs['subprocess_events']), 'Unexpected subprocess observation')
    # Do not equate construction, hostname or loopback bind with external traffic.
    for row in obs['socket_events']:
        op = row['operation']
        require(op in ('socket.__new__','socket.gethostname','socket.bind'), 'Unexpected network-relevant observation: ' + op)
        if op == 'socket.bind':
            import ast
            import ipaddress
            require(ipaddress.ip_address(ast.literal_eval(row['arguments'][1])[0]).is_loopback, 'Non-loopback bind')
    venv = PYTHON.parent.parent.resolve()
    modules = {'interegular': ('interegular','0.3.3'), 'lmformatenforcer': ('lm-format-enforcer','0.11.3')}
    required = {'I1':['interegular'], 'I2':['lmformatenforcer'], 'A1':['JsonSchemaParser'], 'A2':['build_transformers_prefix_allowed_tokens_fn'], 'C1':list(modules)+['JsonSchemaParser','build_transformers_prefix_allowed_tokens_fn']}[ident]
    require(set(result) == set(required), 'Wrong result fields')
    for name in required:
        row = result[name]
        if name in modules:
            require((row['distribution'], row['version']) == modules[name], 'Wrong distribution identity')
            require(Path(row['module_path']).resolve().is_relative_to(venv), 'Module outside frozen environment')
        else:
            require(row['available'] and row['callable'], 'Missing API symbol')
            require(row['module'].startswith('lmformatenforcer.'), 'Wrong API namespace')
            require(Path(row['source_path']).resolve().is_relative_to(venv), 'API outside frozen environment')


def historical():
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE, 'HEAD changed')
    require(subprocess.check_output(['git','rev-list','-n','1',TAG],cwd=ROOT,text=True).strip() == BASE, 'Tag changed')
    require(subprocess.check_output(['git','rev-list','-n','1','answerability-semantic-v2-decoder-replacement-v0.1-pre-install'],cwd=ROOT,text=True).strip() == 'cfe69ac260fabac26b1b91fb9fec5f2bba5b8ded', 'Predecessor changed')
    require(not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).strip(), 'Historical tracked changes')
    require(sha((HISTORY/'LMFE_ENABLEMENT_FREEZE_RECORD.md').read_bytes()) == '103df18b2dedc94186e2901490f44c714092453b93683596d833cc45ce2b7d5f', 'Wrong owner record')
    paths = subprocess.check_output(['git','ls-files','--','artifacts/answerability_semantic_v2_lmfe_enablement','gateway/domain/evaluation/answerability/enable_lmfe.py','gateway/domain/tests/test_lmfe_enablement.py'],cwd=ROOT,text=True).splitlines()
    return {'sha256': {n:sha((ROOT/n).read_bytes()) for n in paths}, 'all_historical_tracked_files_unchanged': True, 'method': 'Git tracked-change verification plus A2.1-F non-benchmark hashes; no benchmark body inspection.'}


def prepare():
    require(not OUT.exists(), 'Refuse overwrite')
    hist = historical()
    frozen_bytes = (HISTORY/'POST_ENABLE_PACKAGE_INVENTORY.json').read_bytes()
    require(sha(frozen_bytes) == EXPECTED_INVENTORY, 'Frozen inventory SHA mismatch')
    current = inventory(); intact(json.loads(frozen_bytes),current)
    OUT.mkdir()
    event('STARTING_STATE_VERIFIED',{'base':BASE,'tag':TAG,'initial_clean_worktree':True})
    write('PRE_VALIDATION_PACKAGE_INVENTORY.json',current)
    write('HISTORICAL_INTEGRITY_RECEIPT.json',hist)
    write('STARTING_ENVIRONMENT_RECEIPT.json',{'base':BASE,'tag':TAG,'frozen_inventory_sha256':EXPECTED_INVENTORY,'current_inventory_sha256':sha(canonical(current)),'package_count':36,'exact_match':True,'package_drift':0})
    write('IMPORT_API_VALIDATION_PLAN.json',plan())
    event('IMPORT_API_PLAN_FROZEN',{'sha256':sha((OUT/'IMPORT_API_VALIDATION_PLAN.json').read_bytes())})


def execute():
    require(not (OUT/'LMFE_IMPORT_RECOVERY_OUTCOME.json').exists(), 'Terminal outcome exists; no retry')
    p = read('IMPORT_API_VALIDATION_PLAN.json')
    require(p == plan(), 'Runner/plan changed')
    require(sha((OUT/'IMPORT_API_VALIDATION_PLAN.json').read_bytes()) == next(r for r in events() if r['event']=='IMPORT_API_PLAN_FROZEN')['details']['sha256'], 'Plan hash changed')
    intact(read('PRE_VALIDATION_PACKAGE_INVENTORY.json'),inventory())
    require(not any(r['event']=='VALIDATION_BEGIN' for r in events()), 'Execution already attempted; no retry')
    results=[];started=[]
    for index,row in enumerate(p['validations'],1):
        require(permitted_next(p,results,started) == row['id'], 'Wrong next validation')
        event('VALIDATION_BEGIN',{'id':row['id'],'process_number':index});started.append(row['id'])
        env=os.environ.copy();env.update(OVERRIDES);begin=time.perf_counter()
        try:
            r=subprocess.run([str(PYTHON),'-B','-c',row['code']],cwd=ROOT,env=env,capture_output=True,text=True,timeout=p['timeout_seconds'])
            process={'validation_id':row['id'],'python':str(PYTHON),'cwd':str(ROOT),'environment_overrides':OVERRIDES,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'elapsed_seconds':time.perf_counter()-begin}
        except subprocess.TimeoutExpired as exc:
            process={'validation_id':row['id'],'python':str(PYTHON),'cwd':str(ROOT),'environment_overrides':OVERRIDES,'exit_code':None,'stdout':str(exc.stdout or ''),'stderr':str(exc.stderr or ''),'elapsed_seconds':time.perf_counter()-begin,'timeout':True}
        write('IMPORT_PROCESS_%02d.json'%index,process)
        lines=[line for line in process['stdout'].splitlines() if line.startswith('FR_RESULT_JSON=')]
        payload=json.loads(lines[-1].split('=',1)[1]) if lines else {}
        try:
            assess(row['id'],payload,process['exit_code'])
        except Exception as exc:
            results.append({'id':row['id'],'pass':False,'error':repr(exc),'payload':payload})
            write('IMPORT_API_RESULTS.json',{'results':results,'validation_processes':len(started),'retries':0})
            event('VALIDATION_FAILED',{'id':row['id'],'error':repr(exc)})
            raise
        results.append({'id':row['id'],'pass':True,'payload':payload})
        event('VALIDATION_PASS',{'id':row['id']})
    write('IMPORT_API_RESULTS.json',{'results':results,'validation_processes':5,'retries':0})
    after=inventory();write('POST_VALIDATION_PACKAGE_INVENTORY.json',after)
    intact(read('PRE_VALIDATION_PACKAGE_INVENTORY.json'),after)
    env=os.environ.copy();env.update(OVERRIDES)
    check=subprocess.run([str(PYTHON),'-B','-m','pip','check'],cwd=ROOT,env=env,capture_output=True,text=True)
    write('POST_VALIDATION_PIP_CHECK.json',{'command':[str(PYTHON),'-B','-m','pip','check'],'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr,'role':'administrative health check, not an import/API validation process'})
    require(check.returncode==0,'pip check failure')
    require(historical()==read('HISTORICAL_INTEGRITY_RECEIPT.json'),'Historical integrity changed')
    require(sha((OUT/'IMPORT_API_VALIDATION_PLAN.json').read_bytes())==next(r for r in events() if r['event']=='IMPORT_API_PLAN_FROZEN')['details']['sha256'],'Plan changed')
    outcome={'outcome':'LMFE_INSTALLED_AWAITING_STRUCTURAL_CONFORMANCE','review_status':'CANDIDATE_AWAITING_OWNER_REVIEW','validation_processes':5,'retries':0,'package_drift':0,'pip_check':'PASS','capability':'NOT_ASSESSED','parser_conformance':'NOT_ASSESSED','V2':'PRE_REGISTERED_NOT_EVALUATED','fresh_semantic_suite':'NOT YET AUTHORED','counters':{n:0 for n in ['downloads','package_index_access','model_network_access','package_mutation','JsonSchemaParser_constructions','V2_parser_constructions','M1','M2','M3','M4','M5','M6','M7','M8','Qwen_initialization','tokenizer_loading','generate','forward','semantic_outputs','DEVELOPMENT','retrieval']},'Phase_2H_HELD_OUT_access':False,'Phase_2G_private_HELDOUT_access':False}
    event('RECOVERY_COMPLETE',outcome);write('LMFE_IMPORT_RECOVERY_OUTCOME.json',outcome)


if __name__=='__main__':
    try:
        require(Path(sys.executable).resolve()==PYTHON.resolve(),'Wrong frozen Python executable')
        require(len(sys.argv)==2 and sys.argv[1] in ('prepare','execute'),'Expected prepare/execute')
        globals()[sys.argv[1]]()
        print(sys.argv[1]+': PASS')
    except Exception as exc:
        if OUT.exists() and not (OUT/'LMFE_IMPORT_RECOVERY_OUTCOME.json').exists():
            begun=any(r['event']=='VALIDATION_BEGIN' for r in events())
            outcome={'outcome':'LMFE_IMPORT_RECOVERY_FAILED' if begun else 'LMFE_IMPORT_RECOVERY_BLOCKED','error':repr(exc)}
            event('RECOVERY_STOPPED',outcome);write('LMFE_IMPORT_RECOVERY_OUTCOME.json',outcome)
        raise
