"""A2.1-G exact-schema character-parser qualification; no token/model integration."""
import ast
import copy
import datetime
import hashlib
import importlib.metadata as md
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import types

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'artifacts/answerability_semantic_v2_lmfe_structural_conformance'
PYTHON=Path.home()/'.virtualenvs/llm-rag-semantic-qwen25-1p5b/Scripts/python.exe'
SITE=PYTHON.parent.parent/'Lib/site-packages'
BASE='8ccdacedd1b47de0471b534ac0b0e786e2c36299'
TAG='answerability-semantic-v2-lmfe-v0.2-imports-validated'
SCHEMA=ROOT/'artifacts/answerability_semantic_gate_v2_prereg/RAW_ASSESSMENT_SCHEMA_V2.json'
SCHEMA_SHA='6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e'
INVENTORY_SHA='00b635d6dd1a3458e78db08d3a0a1c12de90c7b95684f231efdfda5af1a24d0d'
ORACLE=ROOT/'gateway/domain/evaluation/answerability/xgrammar_v2_smoke.py'
ORACLE_SHA='ffe40fc052f6c25484d0abdf60411c1317873c1965e38c94860d6c88781181f9'
ENV_NAMES=['LMFE_STRICT_JSON_FIELD_ORDER','LMFE_MAX_CONSECUTIVE_WHITESPACES','LMFE_MAX_JSON_ARRAY_LENGTH','LMFE_DEFAULT_ALPHABET']
MINIMUM_KEYWORDS=['type','properties','required','additionalProperties','enum','const','items','minItems','maxItems','uniqueItems','minimum','maximum','exclusiveMinimum','exclusiveMaximum','minLength','maxLength','pattern','oneOf','anyOf','allOf','if','then','else','contains']


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


def encoded(obj):return (json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()


def write(name,obj):
    with (OUT/name).open('xb') as f:f.write(encoded(obj))


def read(name):return json.loads((OUT/name).read_bytes())


def event(name,details):
    with (OUT/'LMFE_STRUCTURAL_CONFORMANCE_JOURNAL.jsonl').open('ab') as f:
        f.write((json.dumps({'event':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'details':details},sort_keys=True)+'\n').encode())


def journal():return [json.loads(x) for x in (OUT/'LMFE_STRUCTURAL_CONFORMANCE_JOURNAL.jsonl').read_text().splitlines()]


def inventory():
    packages={}
    for d in md.distributions():
        n=re.sub(r'[-_.]+','-',d.metadata['Name']).lower();require(n not in packages,'Duplicate distribution')
        packages[n]={'name':d.metadata['Name'],'version':d.version,'metadata_sha256':sha((d.read_text('METADATA') or '').encode()),'record_sha256':sha((d.read_text('RECORD') or '').encode())}
    return {'python':'.'.join(map(str,sys.version_info[:3])),'platform':'Windows' if os.name=='nt' else os.name,'architecture':os.environ.get('PROCESSOR_ARCHITECTURE'),'packages':packages}


def intact(before,after):
    require(before==after,'Frozen complete package identity drift')
    require(len(after['packages'])==36 and after['packages']['lm-format-enforcer']['version']=='0.11.3','Wrong LMFE environment')


def schema_oracle():
    require(sha(SCHEMA.read_bytes())==SCHEMA_SHA,'Schema SHA mismatch')
    raw=ORACLE.read_bytes();require(sha(raw)==ORACLE_SHA,'Authoritative frozen validator changed')
    # Load only the two existing pure functions, never the historical model runner.
    nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in ('validate_schema','schema_keyword_guard')]
    require(len(nodes)==2,'Missing frozen validator functions')
    namespace={'re':re,'d':types.SimpleNamespace(require=require)}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(ORACLE),'exec'),namespace)
    schema=json.loads(SCHEMA.read_bytes());namespace['schema_keyword_guard'](schema)
    return schema,namespace['validate_schema']


def keyword_inventory(schema):
    paths={k:[] for k in MINIMUM_KEYWORDS}
    def visit(node,path):
        for key,value in node.items():
            paths.setdefault(key,[]).append({'path':path+'/'+key,'value':value})
        for key in ('items','contains','if','then','else'):
            if key in node:visit(node[key],path+'/'+key)
        for key in ('oneOf','anyOf','allOf'):
            for i,child in enumerate(node.get(key,[])):visit(child,path+'/'+key+'/'+str(i))
        for name,child in node.get('properties',{}).items():visit(child,path+'/properties/'+name)
    visit(schema,'')
    return {k:{'present':bool(v),'occurrences':v,'criticality':'ANNOTATION' if k=='$schema' else 'CRITICAL' if v else 'NOT_APPLICABLE','justification':'Any violation of this raw-schema constraint can reject an output before adapter processing.' if v and k!='$schema' else 'Dialect declaration or absent keyword; no irrelevant probe.'} for k,v in sorted(paths.items())}


def config_from_source():
    path=SITE/'lmformatenforcer/consts.py'
    constants={}
    for node in ast.parse(path.read_bytes()).body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
            try:constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    env={k:os.environ.get(k) for k in ENV_NAMES}
    require(all(v is None for v in env.values()),'Non-default LMFE environment settings; stop before qualification')
    settings={'alphabet':constants['COMPLETE_ALPHABET'],'max_consecutive_whitespaces':constants['DEFAULT_MAX_CONSECUTIVE_WHITESPACES'],'force_json_field_order':constants['DEFAULT_FORCE_JSON_FIELD_ORDER'],'max_json_array_length':constants['DEFAULT_MAX_JSON_ARRAY_LENGTH']}
    return {'parser_class':'lmformatenforcer.JsonSchemaParser','distribution':'lm-format-enforcer','version':'0.11.3','environment':env,'effective_CharacterLevelParserConfig':settings,'config_argument':None,'non_default_overrides':{},'constructor':'JsonSchemaParser(json.loads(exact_original_schema_bytes), config=None); existing_stack=None; num_consecutive_whitespaces=0','traversal':'For each Unicode character in exact decoded UTF-8 bytes: require membership in state.get_allowed_characters(); state = state.add_character(character).','completion':'ACCEPT iff every character was consumed without exception AND final state.can_end() is True. REJECT on disallowed character or nonterminal final state. Exceptions are ERROR, not credited as expected rejection. No artificial EOS character appended.','position_convention':'zero-based Unicode character position; corresponding UTF-8 byte offset also recorded','source_sha256':{n:sha((SITE/n).read_bytes()) for n in ['lmformatenforcer/consts.py','lmformatenforcer/characterlevelparser.py','lmformatenforcer/jsonschemaparser.py','lmformatenforcer/external/jsonschemaobject.py']}}


def fixture(ident,text,expect,features):
    return {'fixture_id':ident,'text':text,'input_sha256':sha(text.encode()),'input_byte_length':len(text.encode()),'input_character_length':len(text),'expected':expect,'features':features}


def core_fixtures():
    path=ROOT/'artifacts/answerability_semantic_v2_xgrammar_diagnostic/MATCHER_DIAGNOSTIC_FIXTURES.json'
    require(sha(path.read_bytes())=='3519ecfb0cd1e215af9d550ed219eff48d02a6fb2ebc3918c7f74425a6390e29','Historical fixture drift')
    rows=json.loads(path.read_bytes())['fixtures'];require(len(rows)==8,'Wrong core count')
    result=[]
    for i,row in enumerate(rows,1):
        require(sha(row['text'].encode())==row['text_sha256'],'Historical text hash mismatch')
        result.append(fixture('M'+str(i),row['text'],row['expected'],['required']))
    require([x['expected'] for x in result]==['ACCEPT']+['REJECT']*7,'Core expectations changed')
    return result


def extended_fixtures(base):
    rows=[]
    def add(label,obj,valid,features):
        rows.append(fixture('E%02d_'%(len(rows)+1)+label,json.dumps(obj,separators=(',',':'),ensure_ascii=False),'ACCEPT' if valid else 'REJECT',features))
    def mod(label,change,valid,features):
        obj=copy.deepcopy(base);change(obj);add(label,obj,valid,features)
    add('VALID_BASE',base,True,['type','properties','required','additionalProperties','enum','const','items','minItems','maxItems','uniqueItems','minimum','maximum','minLength','pattern','oneOf','allOf','if','then'])
    mod('UNKNOWN_ROOT',lambda x:x.update(extra=1),False,['additionalProperties','properties'])
    mod('UNKNOWN_ITEM',lambda x:x['material_asks'][0].update(extra=1),False,['additionalProperties','properties'])
    for key in ('ask','support_status','supporting_evidence_ranks'):
        mod('MISSING_'+key,lambda x,k=key:x['material_asks'][0].pop(k),False,['required'])
    for key in ('decision','policy_context_status','reason_code'):
        mod('BAD_ENUM_'+key,lambda x,k=key:x.update({k:'UNKNOWN'}),False,['enum','const','oneOf'])
    mod('BAD_STATUS',lambda x:x['material_asks'][0].update(support_status='UNKNOWN'),False,['enum','items'])
    add('ROOT_ARRAY',[],False,['type'])
    mod('ASKS_STRING',lambda x:x.update(material_asks='wrong'),False,['type','items'])
    mod('ITEM_STRING',lambda x:x.update(material_asks=['wrong']),False,['type','items'])
    for label,value in [('STRING','1'),('FRACTION',1.5),('BOOLEAN',True),('NULL',None)]:
        mod('RANK_'+label,lambda x,v=value:x['material_asks'][0].update(supporting_evidence_ranks=[v]),False,['type','items'])
    mod('RANKS_SCALAR',lambda x:x['material_asks'][0].update(supporting_evidence_ranks=1),False,['type'])
    mod('ASK_NUMBER',lambda x:x['material_asks'][0].update(ask=1),False,['type'])
    mod('EMPTY_ASKS',lambda x:x.update(material_asks=[]),False,['minItems'])
    mod('EIGHT_ASKS',lambda x:x.update(material_asks=x['material_asks']*8),True,['maxItems','items'])
    mod('NINE_ASKS',lambda x:x.update(material_asks=x['material_asks']*9),False,['maxItems'])
    mod('TEN_RANKS',lambda x:x['material_asks'][0].update(supporting_evidence_ranks=list(range(1,11))),True,['maxItems','minimum','maximum','uniqueItems','items'])
    mod('ELEVEN_RANKS',lambda x:x['material_asks'][0].update(supporting_evidence_ranks=list(range(1,11))+[1]),False,['maxItems','uniqueItems'])
    for label,value,valid,feature in [('LOW',0,False,'minimum'),('HIGH',11,False,'maximum'),('UPPER',10,True,'maximum')]:
        mod('RANK_'+label,lambda x,v=value:x['material_asks'][0].update(supporting_evidence_ranks=[v]),valid,[feature])
    mod('DUPLICATE',lambda x:x['material_asks'][0].update(supporting_evidence_ranks=[1,1]),False,['uniqueItems'])
    mod('ASK_EMPTY',lambda x:x['material_asks'][0].update(ask=''),False,['minLength','pattern'])
    mod('ASK_WHITESPACE',lambda x:x['material_asks'][0].update(ask='   '),False,['pattern'])
    mod('SUPPORTED_EMPTY',lambda x:x['material_asks'][0].update(supporting_evidence_ranks=[]),False,['allOf','if','then','minItems'])
    insufficient=copy.deepcopy(base);insufficient.update(decision='ABSTAIN',reason_code='INSUFFICIENT_POLICY_SUPPORT');insufficient['material_asks'][0].update(support_status='UNSUPPORTED',supporting_evidence_ranks=[])
    add('INSUFFICIENT_VALID',insufficient,True,['oneOf','contains','if','else','maxItems','allOf'])
    bad=copy.deepcopy(insufficient);bad['material_asks'][0]['supporting_evidence_ranks']=[1]
    add('UNSUPPORTED_WITH_RANK',bad,False,['if','else','maxItems','allOf'])
    bad=copy.deepcopy(base);bad.update(decision='ABSTAIN',reason_code='INSUFFICIENT_POLICY_SUPPORT')
    add('CONTAINS_MISSING',bad,False,['contains','oneOf'])
    unresolved=copy.deepcopy(insufficient);unresolved.update(reason_code='UNRESOLVED_POLICY_CONTEXT',policy_context_status='UNRESOLVED')
    add('CONTEXT_BRANCH_VALID',unresolved,True,['oneOf','anyOf','const'])
    unresolved_ask=copy.deepcopy(insufficient);unresolved_ask.update(reason_code='UNRESOLVED_POLICY_CONTEXT');unresolved_ask['material_asks'][0]['support_status']='CONTEXT_UNRESOLVED'
    add('ASK_BRANCH_VALID',unresolved_ask,True,['anyOf','contains','oneOf'])
    bad=copy.deepcopy(insufficient);bad.update(reason_code='UNRESOLVED_POLICY_CONTEXT')
    add('NO_UNRESOLVED_ROUTE',bad,False,['anyOf','contains','oneOf'])
    mod('CONST_PAIRING',lambda x:x.update(reason_code='INSUFFICIENT_POLICY_SUPPORT'),False,['const','oneOf'])
    return rows


def triangulate(schema,validator,row):
    try:
        value=json.loads(row['text'],parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
        return {'JSON_valid':True,'frozen_schema_valid':validator(schema,value)}
    except (ValueError,TypeError) as exc:return {'JSON_valid':False,'frozen_schema_valid':False,'error':str(exc)}


def check_fixtures(rows,schema,validator):
    for row in rows:
        require(sha(row['text'].encode())==row['input_sha256'],'Fixture text changed')
        tri=triangulate(schema,validator,row)
        require(tri['JSON_valid'] and tri['frozen_schema_valid']==(row['expected']=='ACCEPT'),'Authoritative fixture expectation mismatch: '+row['fixture_id'])


def traverse(factory,row):
    start=time.perf_counter();state=None;phase='constructor';position=None
    result={k:row[k] for k in ('fixture_id','input_sha256','input_byte_length','input_character_length','expected','features')}
    result.update(actual='ERROR',all_characters_consumed=False,first_rejected_character_position=None,first_rejected_byte_offset=None,completion_can_end=None,exception=None)
    try:
        state=factory();phase='traversal'
        for position,ch in enumerate(row['text']):
            if ch not in state.get_allowed_characters():
                result.update(actual='REJECT',first_rejected_character_position=position,first_rejected_byte_offset=len(row['text'][:position].encode()),completion_can_end=bool(state.can_end()))
                break
            state=state.add_character(ch)
        else:
            phase='completion';can_end=bool(state.can_end())
            result.update(actual='ACCEPT' if can_end else 'REJECT',all_characters_consumed=True,completion_can_end=can_end)
    except Exception as exc:
        result['exception']={'type':type(exc).__name__,'message':str(exc),'phase':phase,'character_position':position}
    result['elapsed_seconds']=time.perf_counter()-start
    result['matches_expected']=result['actual']==row['expected']
    return result


def core_pass(rows):return len(rows)==8 and [r['fixture_id'] for r in rows]==['M'+str(i) for i in range(1,9)] and all(r['matches_expected'] for r in rows)


def run_extended(core_results,fixtures,factory,record):
    """A failed core gate cannot construct even one extended parser."""
    results=[]
    if not core_pass(core_results):return results
    for row in fixtures:
        result=traverse(factory,row);results.append(result);record(row,result)
        if not result['matches_expected']:break
    return results


def prepare():
    require(not OUT.exists(),'Refuse overwrite')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE,'Wrong HEAD')
    require(subprocess.check_output(['git','rev-list','-n','1',TAG],cwd=ROOT,text=True).strip()==BASE,'Wrong tag')
    require(subprocess.check_output(['git','rev-list','-n','1','answerability-semantic-v2-lmfe-v0.1-enablement-failed'],cwd=ROOT,text=True).strip()=='eaad53841caf73ad6933d7a7bf9612cea09376af','Historical failed checkpoint changed')
    require(not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).strip(),'Historical tracked changes')
    fr=ROOT/'artifacts/answerability_semantic_v2_lmfe_import_recovery'
    require(sha((fr/'LMFE_IMPORT_RECOVERY_FREEZE_RECORD.md').read_bytes())=='b21c1038a1d10707505c13982e8e67b413cbb7a1f887765aa2531e18fecf4a1a','FR owner record changed')
    frozen=(fr/'POST_VALIDATION_PACKAGE_INVENTORY.json').read_bytes();require(sha(frozen)==INVENTORY_SHA,'Frozen inventory hash mismatch')
    inv=inventory();intact(json.loads(frozen),inv)
    schema,validator=schema_oracle();config=config_from_source()
    OUT.mkdir();event('PRECONDITIONS_VERIFIED',{'base':BASE,'tag':TAG,'initial_clean_status':True})
    write('PRE_VALIDATION_PACKAGE_INVENTORY.json',inv)
    write('PARSER_CONFIGURATION.json',config);event('PARSER_CONFIGURATION_FROZEN',{'sha256':sha((OUT/'PARSER_CONFIGURATION.json').read_bytes())})
    keywords=keyword_inventory(schema);write('V2_SCHEMA_KEYWORD_INVENTORY.json',{'schema_sha256':SCHEMA_SHA,'keywords':keywords})
    event('SCHEMA_KEYWORD_INVENTORY_COMPLETE',{'sha256':sha((OUT/'V2_SCHEMA_KEYWORD_INVENTORY.json').read_bytes())})
    core=core_fixtures();check_fixtures(core,schema,validator)
    write('CORE_CONFORMANCE_FIXTURES.json',{'schema_sha256':SCHEMA_SHA,'fixtures':core,'source':'Exact preregistered diagnostic text strings; historical raw outputs untouched.'})
    event('CORE_CONFORMANCE_FIXTURES_FROZEN',{'sha256':sha((OUT/'CORE_CONFORMANCE_FIXTURES.json').read_bytes()),'count':8})
    extended=extended_fixtures(json.loads(core[0]['text']));check_fixtures(extended,schema,validator)
    write('EXTENDED_CONFORMANCE_PLAN.json',{'fixtures':extended,'count':len(extended),'gate':'CORE_8_OF_8_REQUIRED','stop':'First critical mismatch; no retries or adaptive fixtures.','overlap_note':'Eleven ranks cannot isolate maxItems from uniqueItems/domain constraints. All these material rules are critical; do not claim isolated causal attribution. oneOf branches have disjoint decision/reason constants, so a multiply-matching valid object is impossible.'})
    event('EXTENDED_CONFORMANCE_PLAN_FROZEN',{'sha256':sha((OUT/'EXTENDED_CONFORMANCE_PLAN.json').read_bytes()),'count':len(extended)})
    write('CRITICALITY_ASSESSMENT.json',{'material_rules':'All materially present raw-schema constraints are CRITICAL: violation is rejected by the frozen raw schema before adapter processing. $schema is a dialect annotation. Absent keywords are not tested.','adapter_only':['actual evidence-count bound','rank-to-policy identity mapping','semantic support judgment','final GateOutput transformation'],'no_responsibility_transfer':True,'oracle_source':str(ORACLE.relative_to(ROOT)),'oracle_source_sha256':ORACLE_SHA,'oracle_scope':'Existing frozen exact-keyword interpreter, independent of LMFE and adapter; not a general JSON Schema implementation. Two pure function ASTs loaded without executing historical model-runner imports.'})
    paths=subprocess.check_output(['git','ls-files','--','artifacts/answerability_semantic_v2_lmfe_import_recovery','artifacts/answerability_semantic_v2_lmfe_enablement','gateway/domain/evaluation/answerability/recover_lmfe_imports.py','gateway/domain/evaluation/answerability/enable_lmfe.py','gateway/domain/tests/test_lmfe_import_recovery.py','gateway/domain/tests/test_lmfe_enablement.py'],cwd=ROOT,text=True).splitlines()
    write('HISTORICAL_INTEGRITY_RECEIPT.json',{'sha256':{x:sha((ROOT/x).read_bytes()) for x in paths},'all_historical_tracked_files_unchanged':True})


def execute():
    require(not (OUT/'LMFE_STRUCTURAL_CONFORMANCE_OUTCOME.json').exists(),'Prior terminal outcome; no retry')
    require(not any(r['event']=='CORE_EXECUTION_BEGIN' for r in journal()),'Execution already attempted; no retry')
    require(read('OFFLINE_TEST_RESULTS.json')['exit_code']==0,'Tests must pass before M1')
    for eventname,filename in [('PARSER_CONFIGURATION_FROZEN','PARSER_CONFIGURATION.json'),('CORE_CONFORMANCE_FIXTURES_FROZEN','CORE_CONFORMANCE_FIXTURES.json'),('EXTENDED_CONFORMANCE_PLAN_FROZEN','EXTENDED_CONFORMANCE_PLAN.json')]:
        events=[r for r in journal() if r['event']==eventname]
        require(len(events)==1 and sha((OUT/filename).read_bytes())==events[0]['details']['sha256'],'Frozen plan drift')
    config=read('PARSER_CONFIGURATION.json');require(config==config_from_source(),'Parser settings/source changed')
    intact(read('PRE_VALIDATION_PACKAGE_INVENTORY.json'),inventory())
    for path,value in read('EXECUTION_SOURCE_RECEIPT.json')['sha256'].items():require(sha((ROOT/path).read_bytes())==value,'Execution source changed')
    schema,validator=schema_oracle();core=read('CORE_CONFORMANCE_FIXTURES.json')['fixtures'];check_fixtures(core,schema,validator)
    observations={'socket_events':[],'subprocess_events':[],'prohibited_opens':[],'forbidden_scientific_calls':[]}
    def audit(name,args):
        if name.startswith('socket.'):observations['socket_events'].append({'operation':name,'arguments':[str(x) for x in args]})
        elif name=='subprocess.Popen':observations['subprocess_events'].append({'executable':str(args[0]),'command':str(args[1])})
        elif name=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            path=os.fsdecode(args[0]).lower().replace(chr(92),'/')
            if '/hf-cache/' in path or path.endswith('.safetensors') or '/private_heldout/' in path or '/held_out/' in path or ('/evaluation/' in path and '/development/' in path):observations['prohibited_opens'].append(path)
    def profile(frame,ev,arg):
        if ev!='call':return
        path=frame.f_code.co_filename.replace(chr(92),'/');name=frame.f_code.co_name
        if ('/transformers/' in path and name in ('from_pretrained','generate','forward')) or ('/lmformatenforcer/' in path and (name=='build_transformers_prefix_allowed_tokens_fn' or (name=='__init__' and path.endswith('/tokenizerprefixtree.py')))):
            observations['forbidden_scientific_calls'].append({'path':path,'name':name})
    sys.addaudithook(audit);sys.setprofile(profile)
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    from lmformatenforcer import JsonSchemaParser
    initial_parsers=[]
    def factory():
        parser=JsonSchemaParser(json.loads(SCHEMA.read_bytes()),config=None)
        require(vars(parser.config)==config['effective_CharacterLevelParserConfig'],'Effective parser config mismatch')
        initial_parsers.append(parser)
        return parser
    event('CORE_EXECUTION_BEGIN',{'fixtures':8,'fresh_top_level_parser_per_fixture':True})
    core_results=[];triangulation=[];blocked=False
    for row in core:
        result=traverse(factory,row);core_results.append(result)
        tri=triangulate(schema,validator,row);tri.update(fixture_id=row['fixture_id'],LMFE_acceptance=result['actual'],expected_LMFE_acceptance=row['expected'])
        triangulation.append(tri);event('CORE_FIXTURE_COMPLETE',result)
        if result['exception'] and result['exception']['phase']=='constructor':blocked=True;break
    passed=core_pass(core_results)
    write('CORE_CONFORMANCE_RESULTS.json',{'results':core_results,'score':sum(r['matches_expected'] for r in core_results),'required':8,'executions':len(core_results),'fresh_top_level_parsers_constructed':len(initial_parsers),'passed':passed,'retries':0,'note':'Internal immutable state clones made by add_character are not additional fixture executions.'})
    def record_extended(row,result):
        tri=triangulate(schema,validator,row);tri.update(fixture_id=row['fixture_id'],LMFE_acceptance=result['actual'],expected_LMFE_acceptance=row['expected']);triangulation.append(tri)
        event('EXTENDED_FIXTURE_COMPLETE',result)
    extended_results=run_extended(core_results,read('EXTENDED_CONFORMANCE_PLAN.json')['fixtures'],factory,record_extended)
    write('EXTENDED_CONFORMANCE_RESULTS.json',{'status':'EXECUTED' if passed else 'NOT_RUN_DUE_TO_CORE_GATE_FAILURE','results':extended_results,'executions':len(extended_results),'planned_count':read('EXTENDED_CONFORMANCE_PLAN.json')['count'],'remaining_status':'NOT_RUN_AFTER_CRITICAL_FAILURE' if passed and len(extended_results)<read('EXTENDED_CONFORMANCE_PLAN.json')['count'] else 'NOT_APPLICABLE'})
    write('SCHEMA_PARSER_TRIANGULATION.json',{'schema_sha256':SCHEMA_SHA,'oracle_source_sha256':ORACLE_SHA,'results':triangulation,'semantic_scoring':'NOT_PERFORMED'})
    matrix={}
    all_results=core_results+extended_results
    for key,entry in read('V2_SCHEMA_KEYWORD_INVENTORY.json')['keywords'].items():
        relevant=[r for r in all_results if key in r['features']]
        violations=[r['fixture_id'] for r in relevant if r['actual']=='ACCEPT' and r['expected']=='REJECT']
        status='MATERIAL_SCHEMA_FEATURE_UNENFORCED' if violations else 'NOT_RUN_DUE_TO_CORE_GATE_FAILURE' if not passed and key!='required' else 'PROBED_NO_MISMATCH' if relevant and all(r['matches_expected'] for r in relevant) else 'INCOMPLETE_OR_MISMATCH' if relevant else 'NOT_TESTED'
        if not entry['present']:status='NOT_APPLICABLE'
        if key=='$schema':status='DIALECT_ANNOTATION'
        matrix[key]={'present':entry['present'],'criticality':entry['criticality'],'status':status,'probe_ids':[r['fixture_id'] for r in relevant],'invalid_acceptance_ids':violations,'causal_limit':'Feature labels may overlap; acceptance violates critical raw schema but keyword-level root cause is not isolated.'}
    write('MATERIAL_SCHEMA_FEATURE_MATRIX.json',matrix)
    sys.setprofile(None)
    write('RUNTIME_OBSERVATIONS.json',observations)
    after=inventory();write('POST_VALIDATION_PACKAGE_INVENTORY.json',after);intact(read('PRE_VALIDATION_PACKAGE_INVENTORY.json'),after)
    check=subprocess.run([str(PYTHON),'-B','-m','pip','check'],capture_output=True,text=True,env={**os.environ,'PIP_DISABLE_PIP_VERSION_CHECK':'1'})
    write('POST_VALIDATION_PIP_CHECK.json',{'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr});require(check.returncode==0,'pip check failed')
    require(not observations['prohibited_opens'] and not observations['forbidden_scientific_calls'],'Scientific boundary violation')
    require(not any(r['operation'] in ('socket.connect','socket.getaddrinfo','socket.gethostbyname') for r in observations['socket_events']),'Unexpected network')
    for path,val in read('HISTORICAL_INTEGRITY_RECEIPT.json')['sha256'].items():require(sha((ROOT/path).read_bytes())==val,'Historical drift')
    require(not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).strip(),'Historical tracked change')
    outcome='LMFE_STRUCTURAL_CONFORMANCE_BLOCKED' if blocked else 'LMFE_STRUCTURAL_CONFORMANCE_QUALIFIED' if passed and len(extended_results)==read('EXTENDED_CONFORMANCE_PLAN.json')['count'] and all(r['matches_expected'] for r in extended_results) else 'LMFE_STRUCTURAL_CONFORMANCE_FAILED'
    write('LMFE_STRUCTURAL_CONFORMANCE_OUTCOME.json',{'outcome':outcome,'review_status':'CANDIDATE_AWAITING_OWNER_REVIEW','core_score':sum(r['matches_expected'] for r in core_results),'core_executions':len(core_results),'extended_executions':len(extended_results),'retries':0,'package_drift':0,'pip_check':'PASS','tokenizer_loads':0,'Qwen_initialization':0,'generate':0,'forward':0,'semantic_outputs':0,'DEVELOPMENT':0,'retrieval':0,'Phase_2H_HELD_OUT_access':False,'Phase_2G_private_HELDOUT_access':False,'fresh_semantic_suite':'NOT YET AUTHORED'})
    event('QUALIFICATION_COMPLETE',{'outcome':outcome,'core_executions':len(core_results),'extended_executions':len(extended_results)})


if __name__=='__main__':
    require(Path(sys.executable).resolve()==PYTHON.resolve(),'Wrong frozen Python executable')
    require(len(sys.argv)==2 and sys.argv[1] in ('prepare','execute'),'Expected prepare/execute')
    globals()[sys.argv[1]]()
    print(sys.argv[1]+': complete')
