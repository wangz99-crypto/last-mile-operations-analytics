"""GD diagnostic fragments/subtrees only; never reruns G qualification."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[4]
SPEC=importlib.util.spec_from_file_location('frozen_g_util',ROOT/'gateway/domain/evaluation/answerability/qualify_lmfe_structure.py')
g=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(g)
OUT=ROOT/'artifacts/answerability_semantic_v2_lmfe_schema_localization'
BASE='bc8b6371e84b0a98662ab3eaf12183b232f04213'
TAG='answerability-semantic-v2-lmfe-v0.3-structural-conformance-failed'
HISTORY=g.OUT
DISPATCH=g.SITE/'lmformatenforcer/jsonschemaparser.py'
CATEGORIES=['explicit scalar/object/array type','missing type','enum-only','const-only','oneOf-only','anyOf-only','allOf-only','if/then/else node','$ref-only','$ref plus siblings','empty schema {}','type as array / union','nested items schema','additionalProperties schema object']


def write(name,value):
    with (OUT/name).open('xb') as f:f.write(g.encoded(value))


def read(name):return json.loads((OUT/name).read_bytes())


def event(name,data):
    with (OUT/'LMFE_SCHEMA_LOCALIZATION_JOURNAL.jsonl').open('ab') as f:
        f.write(g.encoded({'event':name,'utc':g.datetime.datetime.now(g.datetime.timezone.utc).isoformat(),'details':data}).replace(b'\n',b'')+b'\n')


def pointer_get(schema,pointer):
    current=schema
    if pointer=='':return current
    g.require(pointer.startswith('/'),'Invalid JSON Pointer')
    for token in pointer[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~')
        current=current[int(token)] if isinstance(current,list) else current[token]
    return current


def inventory_nodes(schema):
    result=[]
    def visit(node,pointer,parent):
        g.require(isinstance(node,dict),'Frozen schema node must be object')
        keys=sorted(node);categories=[]
        if isinstance(node.get('type'),str):categories.append(CATEGORIES[0])
        if 'type' not in node:categories.append('missing type')
        for key in ['enum','const','oneOf','anyOf','allOf']:
            if keys==[key]:categories.append(key+'-only')
        if any(k in node for k in ['if','then','else']):categories.append('if/then/else node')
        if '$ref' in node:categories.append('$ref-only' if keys==['$ref'] else '$ref plus siblings')
        if not node:categories.append('empty schema {}')
        if isinstance(node.get('type'),list):categories.append('type as array / union')
        if pointer.endswith('/items'):categories.append('nested items schema')
        if pointer.endswith('/additionalProperties'):categories.append('additionalProperties schema object')
        result.append({'pointer':pointer,'parent_schema_pointer':parent,'parent_pointer':pointer.rsplit('/',1)[0] if pointer else None,'keys':keys,'type_present':'type' in node,'type_value':node.get('type'),'no_explicit_type':'type' not in node,'presence':{k:k in node for k in ['enum','const','properties','items','oneOf','anyOf','allOf','if','then','else','$ref','additionalProperties']},'additionalProperties_value':node.get('additionalProperties'),'categories':categories,'node_sha256':g.sha(g.encoded(node))})
        for key in sorted(node):
            value=node[key]
            if key=='properties':
                for name in sorted(value):visit(value[name],pointer+'/properties/'+name.replace('~','~0').replace('/','~1'),pointer)
            elif key in ('oneOf','anyOf','allOf'):
                for i,child in enumerate(value):visit(child,pointer+'/'+key+'/'+str(i),pointer)
            elif key in ('items','contains','if','then','else','additionalProperties') and isinstance(value,dict):visit(value,pointer+'/'+key,pointer)
    visit(schema,'',None)
    return {'schema_sha256':g.SCHEMA_SHA,'nodes':result,'node_count':len(result),'no_explicit_type_count':sum(r['no_explicit_type'] for r in result),'category_counts':{c:sum(c in r['categories'] for r in result) for c in CATEGORIES},'category_note':'Categories overlap; absence is descriptive, never assumed causal.'}


def build_plan(schema):
    conditional={'if':{'properties':{'s':{'const':'A'}}},'then':{'properties':{'r':{'minItems':1}}},'else':{'properties':{'r':{'maxItems':0}}}}
    item={'properties':{'s':{'const':'A'}}}
    collision={'type':'object','properties':{'x':{'type':'array','items':{'type':'object','properties':{'s':{'enum':['A']}}}}},'required':['x'],'oneOf':[{'properties':{'x':{'items':item}}}]}
    definitions=[
        ('/properties/material_asks/items/properties/ask','explicit string',{'type':'string'},'"A"'),
        ('/properties/material_asks/items/properties/supporting_evidence_ranks/items','explicit integer',{'type':'integer'},'1'),
        ('/properties/material_asks/items/properties/supporting_evidence_ranks','typed array / nested items',{'type':'array','items':{'type':'integer'}},'[1'),
        ('/properties/decision','enum-only',{'enum':['A','B']},'"A"'),
        ('/oneOf/0/properties/decision','const-only',{'const':'A'},'"A"'),
        ('/oneOf/0','missing type / properties-only',{'properties':{'s':{'const':'A'}}},'{'),
        ('/oneOf/0/properties/material_asks','missing type / items-only',{'items':item},'['),
        ('/oneOf/2/anyOf/1/properties/material_asks','missing type / contains-only',{'contains':item},'['),
        ('/properties/material_asks/items/allOf/0/then/properties/supporting_evidence_ranks','missing type / minItems-only',{'minItems':1},'['),
        ('/properties/material_asks/items/allOf/0/else/properties/supporting_evidence_ranks','missing type / maxItems-only',{'maxItems':0},'['),
        ('/properties/material_asks/items/allOf/0','conditional node',conditional,'{'),
        ('/properties/material_asks/items','typed object with allOf conditional',{'type':'object','allOf':[conditional]},'{'),
        ('/oneOf/2','anyOf with properties sibling',{'anyOf':[{'properties':{'s':{'const':'A'}}}],'properties':{'d':{'const':'A'}}},'{'),
        ('','typed object oneOf overlapping property',collision,'{"x":'),
    ]
    rows=[]
    for pointer,category,fragment,prefix in definitions:
        rows.append({'probe_id':'D%02d'%(len(rows)+1),'kind':'MINIMAL_DIAGNOSTIC_FRAGMENT','source_pointer':pointer,'category':category,'schema':fragment,'schema_sha256':g.sha(g.encoded(fragment)),'prefix':prefix,'purpose':'Localize dispatch behavior of this present structural shape, not conformance; no expected acceptance score.','derivation':'Retain named structural form; shorten property names/values and remove unrelated siblings. No candidate substitution; no type added to a source node missing type.'})
    pointers=[('/properties/decision','"ALLOW"'),('/oneOf/0/properties/decision','"ALLOW"'),('/oneOf/0/properties/material_asks','['),('/oneOf/1/properties/material_asks','['),('/oneOf/2/anyOf/1/properties/material_asks','['),('/properties/material_asks/items','{'),('/properties/material_asks/items/allOf/0','{'),('/properties/material_asks/items/allOf/0/if','{'),('/properties/material_asks/items/allOf/0/then/properties/supporting_evidence_ranks','['),('/properties/material_asks/items/allOf/0/else/properties/supporting_evidence_ranks','['),('/properties/material_asks','['),('/oneOf/2','{')]
    for i,(pointer,prefix) in enumerate(pointers,1):
        fragment=copy.deepcopy(pointer_get(schema,pointer))
        rows.append({'probe_id':'T%02d'%i,'kind':'EXACT_SCHEMA_SUBTREE','source_pointer':pointer,'category':'exact subtree; categories in node inventory','schema':fragment,'schema_sha256':g.sha(g.encoded(fragment)),'prefix':prefix,'purpose':'Dispatch unchanged extracted subtree in an independent diagnostic instance; not a full V2 conformance run.','derivation':'Exact JSON Pointer extraction, no structure/value edits.'})
    return {'schema_sha256':g.SCHEMA_SHA,'probe_count':len(rows),'minimal_count':len(definitions),'subtree_count':len(pointers),'probes':rows,'retries':0,'adaptive_probes':False,'root_V2_parser_calls':0,'rule':'One instance per frozen probe; stop each prefix on exception or disallowed character. No acceptance qualification. No M1-M8 or extended probes.'}


def verify_plan(plan,digest,schema):
    g.require(g.sha(g.encoded(plan))==digest,'Frozen probe plan drift')
    g.require(len(plan['probes'])==plan['probe_count'],'Probe count drift')
    g.require(plan==build_plan(schema),'Adaptive probe/schema/prefix change')
    for row in plan['probes']:
        g.require(g.sha(g.encoded(row['schema']))==row['schema_sha256'],'Probe schema drift')
        if row['kind']=='EXACT_SCHEMA_SUBTREE':
            g.require(row['source_pointer']!='' and row['schema']==pointer_get(schema,row['source_pointer']),'Exact subtree mutation')


def installed_sources():
    return {str(p.relative_to(g.SITE)).replace('\\','/'):g.sha(p.read_bytes()) for p in sorted((g.SITE/'lmformatenforcer').rglob('*.py'))}


def prepare():
    g.require(not OUT.exists(),'Refuse overwrite')
    g.require(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==BASE,'Wrong base')
    g.require(subprocess.check_output(['git','rev-list','-n','1',TAG],text=True).strip()==BASE,'Wrong tag')
    g.require(subprocess.check_output(['git','rev-list','-n','1',g.TAG],text=True).strip()==g.BASE,'Predecessor moved')
    g.require(not subprocess.check_output(['git','diff','HEAD','--name-only'],text=True).strip(),'Historical changes')
    g.require(g.sha((HISTORY/'LMFE_STRUCTURAL_CONFORMANCE_FREEZE_RECORD.md').read_bytes())=='29e0fffca5e5c965dd31d7b4cc479441d1f8d94506a911ae124ecdd28074c883','G owner record drift')
    g.require(g.sha(g.SCHEMA.read_bytes())==g.SCHEMA_SHA,'Schema drift')
    g.require(g.sha(Path(g.__file__).read_bytes())=='45cc57a9534a56fef5834fffd422e618e2bb0574adaed90ac019ab4072d66bc0','G helper drift')
    inv=g.inventory();g.intact(json.loads((HISTORY/'POST_VALIDATION_PACKAGE_INVENTORY.json').read_bytes()),inv)
    schema=json.loads(g.SCHEMA.read_bytes());config=g.config_from_source()
    g.require(config==json.loads((HISTORY/'PARSER_CONFIGURATION.json').read_bytes()),'Config changed')
    OUT.mkdir();event('PRECONDITIONS_VERIFIED',{'base':BASE,'tag':TAG,'initial_clean_status':True})
    write('PRE_LOCALIZATION_PACKAGE_INVENTORY.json',inv)
    write('PARSER_CONFIGURATION.json',config);write('INSTALLED_SOURCE_RECEIPT.json',installed_sources())
    write('SCHEMA_NODE_INVENTORY.json',inventory_nodes(schema));event('SCHEMA_NODE_INVENTORY_FROZEN',{'sha256':g.sha((OUT/'SCHEMA_NODE_INVENTORY.json').read_bytes())})
    plan=build_plan(schema);write('LOCALIZATION_PROBE_PLAN.json',plan)
    event('LOCALIZATION_PROBE_PLAN_FROZEN',{'sha256':g.sha((OUT/'LOCALIZATION_PROBE_PLAN.json').read_bytes()),'count':plan['probe_count']})
    factory=next(n for n in ast.walk(ast.parse(Path(g.__file__).read_bytes())) if isinstance(n,ast.FunctionDef) and n.name=='factory')
    constructor=next(n for n in ast.walk(factory) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='JsonSchemaParser')
    g.require(ast.unparse(constructor.args[0])=='json.loads(SCHEMA.read_bytes())','Unexpected helper transformation')
    old=json.loads((HISTORY/'CORE_CONFORMANCE_FIXTURES.json').read_bytes())['fixtures']
    old_results=json.loads((HISTORY/'CORE_CONFORMANCE_RESULTS.json').read_bytes())['results']
    write('HELPER_PATH_RECEIPT.json',{'helper_sha256':g.sha(Path(g.__file__).read_bytes()),'factory_line':factory.lineno,'factory_source':ast.unparse(factory),'schema_sha256':g.SCHEMA_SHA,'parsed_object_order_preserved':list(schema),'path':['SCHEMA.read_bytes()','json.loads(original bytes), no sorting or structure transformation','JsonSchemaParser(parsed object, config=None)','LMFE JsonSchemaObject(**json_schema)','get_parser(context.model_class)'],'project_transformation':'NONE: direct parsed original argument, established by frozen AST/source inspection; historical helper NOT executed','native_input_receipt':'Per diagnostic probe trace records constructor-entry dict hash and internal dispatch object; full V2/M1-M8 are not rerun.','historical_exception_context':[{'fixture_id':r['fixture_id'],'position':r['exception']['character_position'],'prefix_before_error':f['text'][:r['exception']['character_position']],'character_at_error':f['text'][r['exception']['character_position']]} for f,r in zip(old,old_results)]})
    historical={str(p.relative_to(ROOT)).replace('\\','/'):g.sha(p.read_bytes()) for p in sorted(HISTORY.iterdir()) if p.is_file()}
    historical.update(json.loads((HISTORY/'HISTORICAL_INTEGRITY_RECEIPT.json').read_bytes())['sha256'])
    for path,digest in historical.items():g.require(g.sha((ROOT/path).read_bytes())==digest,'Historical drift')
    write('HISTORICAL_INTEGRITY_RECEIPT.json',{'sha256':historical,'historical_tracked_git_state_unchanged':True})


def probe(row,parser_class,config,trace_rows):
    result={'probe_id':row['probe_id'],'kind':row['kind'],'source_pointer':row['source_pointer'],'category':row['category'],'constructor':'NOT_COMPLETED','traversal':'NOT_STARTED','same_target_exception':False,'exception':None,'characters_consumed':0}
    argument=copy.deepcopy(row['schema']);before=g.sha(g.encoded(argument));phase='constructor';start=time.perf_counter()
    def trace(frame,ev,arg):
        if frame.f_code.co_filename.replace('\\','/')!=str(DISPATCH).replace('\\','/'):return None
        name=frame.f_code.co_name
        if ev=='call' and name=='__init__' and isinstance(frame.f_locals.get('json_schema'),dict):
            trace_rows.append({'probe_id':row['probe_id'],'event':'constructor_argument','line':frame.f_lineno,'sha256':g.sha(g.encoded(frame.f_locals['json_schema']))})
        elif name=='get_parser' and ev in ('call','exception'):
            value=frame.f_locals.get('value_schema')
            entry={'probe_id':row['probe_id'],'event':ev,'function':name,'line':frame.f_lineno,'type_resolved':getattr(value,'type',None),'incoming_schema_object':value.model_dump(mode='json',by_alias=True,exclude_unset=True) if value is not None else None}
            if ev=='exception':entry['exception']={'type':arg[0].__name__,'message':str(arg[1])}
            trace_rows.append(entry)
        elif name=='_merge_object_schemas' and ev in ('call','return'):
            trace_rows.append({'probe_id':row['probe_id'],'event':'merge_'+ev,'line':frame.f_lineno,'base':frame.f_locals['base_schema'].model_dump(mode='json',exclude_unset=True),'option':frame.f_locals['option_schema'].model_dump(mode='json',exclude_unset=True)})
        return trace
    sys.settrace(trace)
    try:
        state=parser_class(argument,config=None);result['constructor']='PASS'
        g.require(vars(state.config)==config['effective_CharacterLevelParserConfig'],'Parser configuration drift')
        phase='traversal';result['traversal']='PREFIX_EXERCISED_WITHOUT_TARGET_EXCEPTION'
        for position,ch in enumerate(row['prefix']):
            if ch not in state.get_allowed_characters():
                result.update(traversal='PREFIX_CHARACTER_DISALLOWED',position=position);break
            state=state.add_character(ch);result['characters_consumed']+=1
    except Exception as exc:
        result['constructor']='ERROR' if phase=='constructor' else result['constructor']
        result['traversal']='NOT_STARTED' if phase=='constructor' else 'ERROR'
        result['exception']={'type':type(exc).__name__,'message':str(exc),'phase':phase,'traceback':traceback.format_exc()}
        result['same_target_exception']=str(exc)=='Unsupported type None'
    finally:sys.settrace(None)
    result.update(elapsed_seconds=time.perf_counter()-start,constructor_input_sha256=before,constructor_input_after_sha256=g.sha(g.encoded(argument)),qualification_verdict='NOT_A_QUALIFICATION_CASE')
    return result


def execute():
    events=[json.loads(x) for x in (OUT/'LMFE_SCHEMA_LOCALIZATION_JOURNAL.jsonl').read_text().splitlines()]
    g.require(not any(r['event']=='DIAGNOSTIC_EXECUTION_BEGIN' for r in events),'No retry')
    g.require(read('OFFLINE_TEST_RESULTS.json')['exit_code']==0,'Offline tests required')
    schema=json.loads(g.SCHEMA.read_bytes());g.require(g.sha(g.SCHEMA.read_bytes())==g.SCHEMA_SHA,'Schema drift')
    digest=next(r['details']['sha256'] for r in events if r['event']=='LOCALIZATION_PROBE_PLAN_FROZEN')
    plan=read('LOCALIZATION_PROBE_PLAN.json');verify_plan(plan,digest,schema)
    g.intact(read('PRE_LOCALIZATION_PACKAGE_INVENTORY.json'),g.inventory())
    g.require(installed_sources()==read('INSTALLED_SOURCE_RECEIPT.json'),'LMFE source changed')
    config=read('PARSER_CONFIGURATION.json');g.require(config==g.config_from_source(),'Config changed')
    for path,digest in read('EXECUTION_SOURCE_RECEIPT.json').items():g.require(g.sha((ROOT/path).read_bytes())==digest,'Diagnostic source drift')
    observations={'socket_events':[],'subprocess_events':[],'protected_opens':[],'forbidden_calls':[]}
    def audit(name,args):
        if name.startswith('socket.'):observations['socket_events'].append({'event':name,'args':[str(x) for x in args]})
        elif name=='subprocess.Popen':observations['subprocess_events'].append(str(args[1]))
        elif name=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            path=os.fsdecode(args[0]).lower().replace('\\','/')
            if '/private_heldout/' in path or '/held_out/' in path or ('/evaluation/' in path and '/development/' in path) or path.endswith('.safetensors'):observations['protected_opens'].append(path)
    def profile(frame,ev,arg):
        path=frame.f_code.co_filename.replace('\\','/');name=frame.f_code.co_name
        if ev=='call' and (('/transformers/' in path and name in ('from_pretrained','generate','forward')) or ('/lmformatenforcer/' in path and (name=='build_transformers_prefix_allowed_tokens_fn' or (name=='__init__' and path.endswith('/tokenizerprefixtree.py'))))):observations['forbidden_calls'].append({'path':path,'name':name})
    sys.addaudithook(audit);sys.setprofile(profile)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
    event('DIAGNOSTIC_EXECUTION_BEGIN',{'count':plan['probe_count'],'retries':0})
    from lmformatenforcer import JsonSchemaParser
    results=[];trace_rows=[]
    for row in plan['probes']:
        result=probe(row,JsonSchemaParser,config,trace_rows);results.append(result);event('DIAGNOSTIC_PROBE_COMPLETE',result)
    sys.setprofile(None)
    write('LOCALIZATION_PROBE_RESULTS.json',{'results':[r for r in results if r['kind']=='MINIMAL_DIAGNOSTIC_FRAGMENT'],'retries':0})
    write('EXACT_SCHEMA_SUBTREE_RESULTS.json',{'results':[r for r in results if r['kind']=='EXACT_SCHEMA_SUBTREE'],'retries':0})
    write('LMFE_DISPATCH_TRACE.json',{'source':str(DISPATCH),'source_sha256':g.sha(DISPATCH.read_bytes()),'trace_method':'sys.settrace observes calls/exceptions/merge state; no monkeypatch/library changes','events':trace_rows})
    write('RUNTIME_OBSERVATIONS.json',observations)
    after=g.inventory();write('POST_LOCALIZATION_PACKAGE_INVENTORY.json',after);g.intact(read('PRE_LOCALIZATION_PACKAGE_INVENTORY.json'),after)
    check=subprocess.run([str(g.PYTHON),'-B','-m','pip','check'],capture_output=True,text=True,env={**os.environ,'PIP_DISABLE_PIP_VERSION_CHECK':'1'})
    write('POST_LOCALIZATION_PIP_CHECK.json',{'exit_code':check.returncode,'stdout':check.stdout,'stderr':check.stderr})
    g.require(check.returncode==0,'pip check failed')
    g.require(installed_sources()==read('INSTALLED_SOURCE_RECEIPT.json'),'LMFE source drift')
    g.require(g.sha(g.SCHEMA.read_bytes())==g.SCHEMA_SHA,'Frozen schema mutation')
    for path,digest in read('HISTORICAL_INTEGRITY_RECEIPT.json')['sha256'].items():g.require(g.sha((ROOT/path).read_bytes())==digest,'Historical mutation')
    g.require(not observations['protected_opens'] and not observations['forbidden_calls'],'Boundary violation')
    g.require(not subprocess.check_output(['git','diff','HEAD','--name-only'],text=True).strip(),'Historical Git drift')
    event('DIAGNOSTIC_EXECUTION_COMPLETE',{'probes':len(results),'retries':0,'package_drift':0,'pip_check':'PASS'})


if __name__=='__main__':
    g.require(Path(sys.executable).resolve()==g.PYTHON.resolve(),'Frozen Python required')
    g.require(len(sys.argv)==2 and sys.argv[1] in ('prepare','execute'),'prepare/execute required')
    globals()[sys.argv[1]]()
