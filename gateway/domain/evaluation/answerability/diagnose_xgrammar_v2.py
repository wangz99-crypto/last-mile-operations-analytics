"""Frozen-schema matcher diagnostic only. No model construction, inference, or fixes."""
import ast
import datetime
import hashlib
import importlib.metadata as metadata
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from gateway.domain.evaluation.answerability.validate_dependency_imports_r2 import inventory
from gateway.domain.evaluation.answerability.xgrammar_v2_smoke import strict_json, schema_keyword_guard, validate_schema

BASE = 'e085c96e5c80ce61bb833be78f36c62ee8ee5790'
TAG = 'answerability-semantic-v2-decoder-v0.2-qualification-failed-nonconforming'
OUT = ROOT / 'artifacts/answerability_semantic_v2_xgrammar_diagnostic'
A2 = ROOT / 'artifacts/answerability_semantic_v2_decoder_qualification_attempt2'
SCHEMA = ROOT / 'artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json'
SCHEMA_SHA = '6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e'
PYTHON = Path.home() / '.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe'
SITE = PYTHON.parent.parent / 'Lib/site-packages'
SOURCES = {
    'gateway/domain/evaluation/answerability/xgrammar_v2_decoder.py': '2d7aef05951544a4ac99c7a49b6c614a711691077f323d6b7e1d2de350f4f07b',
    'gateway/domain/evaluation/answerability/xgrammar_v2_smoke.py': 'ffe40fc052f6c25484d0abdf60411c1317873c1965e38c94860d6c88781181f9',
    'gateway/domain/tests/test_xgrammar_v2_decoder.py': '4e846070e2c0e0955720b0d7373165b316984954121893687bdc251b536e8c61',
}
IDS = ('M1_VALID_COMPLETE','M2_MISSING_DECISION','M3_MISSING_POLICY_CONTEXT','M4_MISSING_REASON',
       'M5_MISSING_ALL_THREE','M6_ATTEMPT2_S1_RAW','M7_ATTEMPT2_S2_RAW','M8_ATTEMPT2_S3_RAW')
OFFLINE = {'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1',
           'PIP_NO_INDEX':'1','PIP_DISABLE_PIP_VERSION_CHECK':'1'}


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def write(name, value):
    with (OUT/name).open('xb') as f: f.write(canonical(value))


def read(name):
    return json.loads((OUT/name).read_bytes())


def event(name, details):
    with (OUT/'XGRAMMAR_DIAGNOSTIC_JOURNAL.jsonl').open('ab') as f:
        f.write((json.dumps({'event':name,'details':details,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},sort_keys=True)+'\n').encode())


def checked_schema(data):
    require(sha(data)==SCHEMA_SHA,'Frozen schema hash mismatch')
    value=json.loads(data)
    schema_keyword_guard(value)
    return value


def integrity():
    for path,digest in SOURCES.items(): require(sha((ROOT/path).read_bytes())==digest,'Attempt-2 source drift: '+path)
    checked_schema(SCHEMA.read_bytes())
    require(metadata.version('xgrammar')=='0.2.8','Wrong XGrammar')
    require(inventory()==json.loads((A2/'FINAL_PACKAGE_INVENTORY.json').read_bytes()),'Frozen package drift')
    receipt=json.loads((A2/'FINAL_SHA256.json').read_bytes())
    for path,digest in receipt['files'].items():
        if path.endswith('/DECODER_FREEZE_RECORD.md') or path=='.gitattributes': continue
        require(sha((ROOT/path).read_bytes())==digest,'Frozen receipt drift: '+path)
    require(sha((A2/'DECODER_FREEZE_RECORD.md').read_bytes())=='5c0a330c1581222891688add768730cb6889f776b465ed5c6342c4901816fa61','Owner record drift')
    return {p.name:sha(p.read_bytes()) for p in sorted(A2.iterdir()) if p.is_file()}


def signature_defaults(path, class_name, method):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==class_name)
    fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==method)
    defaults={arg.arg:ast.literal_eval(default) for arg,default in zip(fn.args.kwonlyargs,fn.args.kw_defaults)}
    return defaults,{'path':str(path),'sha256':sha(path.read_bytes()),'start_line':fn.lineno,'end_line':fn.end_lineno,
                    'source':ast.get_source_segment(path.read_text(encoding='utf-8'),fn)}


def fixtures(schema, raw_rows):
    obj={'decision':'ALLOW','material_asks':[{'ask':'Opaque diagnostic requirement','support_status':'SUPPORTED',
         'supporting_evidence_ranks':[1]}],'policy_context_status':'RESOLVED','reason_code':'SUPPORTED_BY_ACTIVE_POLICY'}
    require(validate_schema(schema,obj),'M1 must satisfy frozen schema')
    removed=[(),('decision',),('policy_context_status',),('reason_code',),('decision','policy_context_status','reason_code')]
    result=[]
    for name,keys in zip(IDS[:5],removed):
        text=json.dumps({k:v for k,v in obj.items() if k not in keys},ensure_ascii=False,separators=(',',':'))
        result.append({'fixture_id':name,'text':text,'text_sha256':sha(text.encode()),'expected':'ACCEPT' if not keys else 'REJECT',
                       'source':'DETERMINISTIC_STRUCTURE_ONLY','removed_keys':list(keys)})
    require([r['case_id'] for r in raw_rows]==['S1','S2','S3'],'Raw case inventory')
    for name,row in zip(IDS[5:],raw_rows):
        require(sha(row['raw_output_text'].encode())==row['raw_output_sha256'],'Raw custody mismatch')
        require(row['termination_status']=='EOS','Unexpected prior termination')
        result.append({'fixture_id':name,'text':row['raw_output_text'],'text_sha256':row['raw_output_sha256'],
                       'expected':'REJECT','source':'EXACT_SAVED_ATTEMPT2_'+row['case_id'],
                       'saved_generated_token_ids':row['generated_token_ids'],'saved_token_count':row['generated_token_count']})
    require(tuple(r['fixture_id'] for r in result)==IDS,'Fixture inventory/order changed')
    for row in result: require(validate_schema(schema,strict_json(row['text']))==(row['expected']=='ACCEPT'),'Fixture expectation mismatch')
    return result


def prepare():
    require(not OUT.exists(),'Refuse diagnostic overwrite')
    require(Path(sys.executable).resolve()==PYTHON.resolve(),'Wrong interpreter')
    for ref in ('HEAD',TAG):
        require(subprocess.check_output(['git','rev-parse',ref+'^{commit}'],cwd=ROOT,text=True).strip()==BASE,'Wrong base/tag')
    require(subprocess.check_output(['git','rev-list','-n','1','answerability-semantic-v2-deps-v0.2-imports-validated'],cwd=ROOT,text=True).strip()=='4fea18a9c70b1b9536dd92d7f1a118ac3e02a32f','R2 tag drift')
    require(not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).strip(),'Historical worktree changed')
    history=integrity()
    schema=checked_schema(SCHEMA.read_bytes())
    raw=[json.loads(x) for x in (A2/'RAW_STRUCTURAL_OUTPUTS.jsonl').read_text().splitlines()]
    frozen=fixtures(schema,raw)
    opts,source=signature_defaults(SITE/'xgrammar/compiler.py','GrammarCompiler','compile_json_schema')
    init_opts,init_source=signature_defaults(SITE/'xgrammar/compiler.py','GrammarCompiler','__init__')
    # Verify actual call AST: exactly one schema positional argument, no keyword overrides.
    tree=ast.parse((ROOT/next(iter(SOURCES))).read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compile_exact')
    call=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='compile_json_schema')
    require(len(call.args)==1 and not call.keywords,'Unexpected compile argument overrides')
    require(opts=={'any_whitespace':True,'indent':None,'separators':None,'strict_mode':True,'max_whitespace_cnt':None,'any_order':False},'Compile source identity/parameters changed')
    OUT.mkdir()
    event('PRECONDITION_VERIFIED',{'base_commit':BASE,'base_tag':TAG,'initial_clean_worktree':True,
          'clean_check':'git status --short before authoring diagnostic helper'})
    write('ATTEMPT2_INTEGRITY_RECEIPT.json',{'files':history,'execution_sources':SOURCES,'owner_status':'OWNER_REVIEWED / DECODER_QUALIFICATION_FAILED',
          'execution_integrity':'NONCONFORMING_CONFIG','clean_decoder_capability_judgment':'NOT_CONCLUSIVE'})
    write('PRE_DIAGNOSTIC_PACKAGE_INVENTORY.json',inventory())
    write('SCHEMA_REQUIRED_FIELD_RECEIPT.json',{'schema_sha256':SCHEMA_SHA,'type':schema['type'],
          'properties':schema['properties'],'required':schema['required'],'additionalProperties':schema['additionalProperties']})
    write('ATTEMPT2_COMPILATION_PARAMETERS.json',{'schema_argument':'exact frozen UTF-8 schema text, one positional argument',
          'schema_sha256':SCHEMA_SHA,'explicit_keyword_overrides':{},'effective_options':opts,'compiler_constructor_options':init_opts,
          'evidence_basis':'Hash-verified Attempt-2 call AST plus installed exact-version Python function definitions; not generic documentation defaults.',
          'compile_method_source':source,'compiler_constructor_source':init_source,
          'tokenizer_identity':json.loads((A2/'TOKENIZER_INTEGRATION_RESULT.json').read_bytes())})
    write('MATCHER_DIAGNOSTIC_FIXTURES.json',{'schema_sha256':SCHEMA_SHA,'fixtures':frozen,'model_calls':0,'retries':0,
          'matcher_path':'tokenize M1-M5 without special tokens; replay exact saved token IDs for M6-M8; accept_token one pass then one EOS check if all body tokens accepted; fresh matcher per fixture'})
    event('MATCHER_FIXTURES_FROZEN',{'sha256':sha((OUT/'MATCHER_DIAGNOSTIC_FIXTURES.json').read_bytes()),'count':8})
    print('Frozen M1-M8; no matcher/model execution.')


def validate_plan(data, expected_hash, events):
    require(sha(data)==expected_hash,'Frozen fixtures changed')
    require(not any(e['event']=='MATCHER_DIAGNOSTIC_STARTED' for e in events),'No diagnostic retry')
    plan=json.loads(data)
    require(tuple(r['fixture_id'] for r in plan['fixtures'])==IDS,'Fixture inventory changed')
    for row in plan['fixtures']: require(sha(row['text'].encode())==row['text_sha256'],'Fixture text changed')
    return plan


def match_once(matcher, tokens, stop_id):
    first=None
    for index,token in enumerate(tokens):
        if not matcher.accept_token(token): first=index;break
    completed=matcher.is_completed()
    terminated_before=matcher.is_terminated()
    eos_accepted=None if first is not None else matcher.accept_token(stop_id)
    terminated_after=matcher.is_terminated()
    accepted=first is None and completed and bool(eos_accepted) and terminated_after
    return {'actual':'ACCEPT' if accepted else 'REJECT','all_body_tokens_accepted':first is None,
            'first_rejection_token_index_zero_based':first,'body_token_count':len(tokens),'body_completed':completed,
            'terminated_before_eos':terminated_before,'stop_token_id':stop_id,'stop_token_accepted':eos_accepted,
            'terminated_after_eos':terminated_after,'completion_after_eos':matcher.is_completed()}


def child():
    os.environ.update(OFFLINE)
    events=[json.loads(x) for x in (OUT/'XGRAMMAR_DIAGNOSTIC_JOURNAL.jsonl').read_text().splitlines()]
    frozen=next(e for e in events if e['event']=='MATCHER_FIXTURES_FROZEN')['details']['sha256']
    require(sha((OUT/'MATCHER_DIAGNOSTIC_FIXTURES.json').read_bytes())==frozen,'Fixture drift')
    observations={'socket_events':[],'subprocess_events':[],'prohibited_opens':[],
                  'model_initializations':0,'generate_calls':0,'forward_calls':0}
    def audit(name,args):
        if name.startswith('socket.'):
            observations['socket_events'].append({'operation':name,'arguments':[str(a) for a in args]})
            if name in ('socket.connect','socket.getaddrinfo','socket.gethostbyname'): raise RuntimeError('Network prohibited')
        elif name=='subprocess.Popen': observations['subprocess_events'].append({'executable':str(args[0]),'arguments':str(args[1])})
        elif name=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            path=os.fsdecode(args[0]).replace(chr(92),'/').lower()
            if any(x in path for x in ('/development/','/private_heldout/','/held_out/')) or path.endswith(('.safetensors','pytorch_model.bin')):
                observations['prohibited_opens'].append(path);raise RuntimeError('Model weights/benchmark access forbidden')
    def profile(frame,event,arg):
        if event!='call': return
        path=frame.f_code.co_filename.replace(chr(92),'/').lower();name=frame.f_code.co_name
        if '/transformers/' in path and name in ('generate','forward'):
            observations[name+'_calls']+=1;raise RuntimeError('Model execution forbidden')
        if path.endswith('/transformers/modeling_utils.py') and name in ('from_pretrained','__init__'):
            observations['model_initializations']+=1;raise RuntimeError('Model construction forbidden')
    sys.addaudithook(audit);sys.setprofile(profile)
    try:
        import xgrammar as xg
        from transformers import AutoTokenizer
        require(metadata.version('xgrammar')=='0.2.8','Wrong decoder')
        expected=read('ATTEMPT2_COMPILATION_PARAMETERS.json')
        schema_text=SCHEMA.read_bytes().decode('utf-8');checked_schema(schema_text.encode())
        signature=inspect.signature(xg.GrammarCompiler.compile_json_schema)
        bound=signature.bind(None,schema_text);bound.apply_defaults()
        actual={k:v for k,v in bound.arguments.items() if k not in ('self','schema')}
        require(actual==expected['effective_options'],'Effective parameter drift')
        token_receipt=expected['tokenizer_identity'];snapshot=Path(token_receipt['snapshot'])
        for row in token_receipt['verified_files']:
            require(sha((snapshot/row['relative_path']).read_bytes())==row['sha256'],'Tokenizer drift')
        tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False)
        require(sha(canonical(tokenizer.get_vocab()))==token_receipt['vocabulary_sha256'],'Tokenizer vocabulary drift')
        info=xg.TokenizerInfo.from_huggingface(tokenizer,vocab_size=token_receipt['model_vocab_size'])
        compiler=xg.GrammarCompiler(info)
        grammar=compiler.compile_json_schema(schema_text)
        grammar_text=str(grammar.grammar)
        with (OUT/'COMPILED_GRAMMAR.ebnf').open('xb') as f:f.write(grammar_text.encode())
        write('GRAMMAR_COMPILATION_RECEIPT.json',{'schema_sha256':SCHEMA_SHA,'explicit_keyword_overrides':{},
              'effective_options':actual,'any_order':actual['any_order'],'compiler_constructor_options':expected['compiler_constructor_options'],
              'compiled_grammar_sha256':sha(grammar_text.encode()),'xgrammar_version':metadata.version('xgrammar'),
              'tokenizer_type':type(tokenizer).__name__,'tokenizer_info_vocab_size':info.vocab_size,
              'vocabulary_sha256':token_receipt['vocabulary_sha256'],'model_initializations':0,
              'matcher_constructor_defaults':{k:v.default for k,v in inspect.signature(xg.GrammarMatcher.__init__).parameters.items() if k not in ('self','compiled_grammar')},
              'compilation_count':1,'compiled':True})
        event('EXACT_SCHEMA_COMPILED',{'schema_sha256':SCHEMA_SHA,'any_order':actual['any_order']})
        plan=read('MATCHER_DIAGNOSTIC_FIXTURES.json');rows=[];matrix=[]
        schema=checked_schema(SCHEMA.read_bytes())
        for fixture in plan['fixtures']:
            if 'saved_generated_token_ids' in fixture:
                tokens=fixture['saved_generated_token_ids'][:-1];stop=fixture['saved_generated_token_ids'][-1]
            else:
                tokens=tokenizer.encode(fixture['text'],add_special_tokens=False);stop=tokenizer.eos_token_id
            decoded=tokenizer.decode(tokens,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            require(decoded==fixture['text'],'Tokenized fixture bytes changed')
            event('MATCHER_CASE_STARTED',{'fixture_id':fixture['fixture_id']})
            matcher=xg.GrammarMatcher(grammar)
            result=match_once(matcher,tokens,stop)
            index=result['first_rejection_token_index_zero_based']
            result.update(fixture_id=fixture['fixture_id'],expected=fixture['expected'],text_sha256=fixture['text_sha256'],
                          input_token_ids=tokens,matcher_stop_token_ids=matcher.stop_token_ids,
                          first_rejection_token_id=None if index is None else tokens[index],
                          accepted_prefix_utf8_length=None if index is None else len(tokenizer.decode(tokens[:index],clean_up_tokenization_spaces=False).encode()))
            result['matches_schema_expectation']=result['actual']==fixture['expected']
            rows.append(result)
            if fixture['fixture_id'] in IDS[5:]:
                matrix.append({'case_id':fixture['source'].removeprefix('EXACT_SAVED_ATTEMPT2_'),
                    'json_parser':'PASS','exact_schema_validator':'PASS' if validate_schema(schema,strict_json(fixture['text'])) else 'FAIL',
                    'xgrammar_matcher':result['actual'],'text_sha256':fixture['text_sha256']})
            event('MATCHER_CASE_COMPLETED',{'fixture_id':fixture['fixture_id'],'actual':result['actual'],'expected':fixture['expected']})
            print(fixture['fixture_id'],result['actual'],'expected',fixture['expected'],flush=True)
        write('MATCHER_DIAGNOSTIC_RESULTS.json',{'results':rows,'fixture_sha256':frozen,'compilation_count':1,'matcher_instances':8,'retries':0})
        write('RAW_OUTPUT_TRIANGULATION.json',{'results':matrix,'schema_sha256':SCHEMA_SHA,
              'validator':'Independent exact-keyword interpreter from frozen Attempt-2 runner; schema hash and supported keywords enforced; not a claim of general JSON Schema support.'})
        event('MATCHER_DIAGNOSTIC_COMPLETED',{'cases':8,'retries':0})
    finally:
        sys.setprofile(None)
        write('DIAGNOSTIC_EXECUTION_OBSERVATIONS.json',observations)


def run():
    require(integrity()==read('ATTEMPT2_INTEGRITY_RECEIPT.json')['files'],'Attempt-2 artifact mutation')
    events=[json.loads(x) for x in (OUT/'XGRAMMAR_DIAGNOSTIC_JOURNAL.jsonl').read_text().splitlines()]
    freeze=next(e for e in events if e['event']=='MATCHER_FIXTURES_FROZEN')
    validate_plan((OUT/'MATCHER_DIAGNOSTIC_FIXTURES.json').read_bytes(),freeze['details']['sha256'],events)
    require(read('PRE_DIAGNOSTIC_TEST_RESULTS.json')['passed'],'Pre-diagnostic tests required')
    for p,h in read('DIAGNOSTIC_SOURCE_RECEIPT.json').items(): require(sha((ROOT/p).read_bytes())==h,'Diagnostic source drift')
    event('MATCHER_DIAGNOSTIC_STARTED',{'model_calls':0,'maximum_matcher_cases':8,'retry':0})
    start=time.monotonic()
    result=subprocess.run([str(PYTHON),'-I','-B',str(Path(__file__).resolve()),'child'],cwd=PYTHON.parent.parent,
                          env=dict(os.environ,**OFFLINE),capture_output=True,text=True,encoding='utf-8',errors='replace')
    write('DIAGNOSTIC_PROCESS.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
          'elapsed_seconds':time.monotonic()-start,'retries':0})
    print(result.stdout);print(result.stderr)
    require(result.returncode==0,'Diagnostic process failed; do not retry')


if __name__=='__main__':
    {'prepare':prepare,'run':run,'child':child}[sys.argv[1]]()
