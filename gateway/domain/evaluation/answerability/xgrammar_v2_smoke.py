"""One-shot, three-case structural qualification, never semantic accuracy evaluation."""
import ast
from dataclasses import asdict
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
from gateway.domain.evaluation.answerability import xgrammar_v2_decoder as d
from gateway.domain.evaluation.answerability.answerability_contracts import ActiveBundle, GateInput, RankedEvidence
from gateway.domain.evaluation.answerability.gates import semantic_gate_v2 as v2

CASE_IDS = ('S1', 'S2', 'S3')
CONFIG = {'device': 'cpu', 'dtype': 'float32', 'do_sample': False, 'num_beams': 1,
          'max_new_tokens': 512, 'seed': 0, 'quality_retry': 0, 'infrastructure_retry': 0,
          'per_call_timeout_seconds': 600, 'timeout_enforcement': 'worker join wall-clock deadline; process exits on timeout',
          'temperature': 'NOT_APPLICABLE_GREEDY', 'top_p': 'NOT_APPLICABLE_GREEDY',
          'top_k': 'NOT_APPLICABLE_GREEDY', 'structured_generation': 'XGRAMMAR_EXACT_FROZEN_V2_SCHEMA',
          'torch_num_threads': 4, 'torch_num_interop_threads': 1, 'deterministic_algorithms': True,
          'model': 'Qwen/Qwen2.5-1.5B-Instruct', 'revision': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306',
          'schema_sha256': d.SCHEMA_SHA, 'chat_template_sha256': d.CHAT_SHA, 'maximum_generate_calls': 3}


def strict_json(text):
    def pairs(items):
        value = {}
        for k,v in items:
            d.require(k not in value, 'Duplicate JSON key')
            value[k] = v
        return value
    def nonfinite(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    value = json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)
    d.require(type(value) is dict, 'Exactly one JSON object required')
    return value


def validate_schema(schema, value):
    """Draft-2020-12 semantics for every keyword used in the hash-locked V2 schema.

    Independent of decoder grammar and adapter; no schema rewriting. This is not
    advertised as a general-purpose implementation of the entire JSON Schema spec.
    """
    if 'type' in schema:
        types = {'object': lambda x:type(x) is dict, 'array': lambda x:type(x) is list,
                 'string': lambda x:type(x) is str,
                 'integer': lambda x:type(x) is int or (type(x) is float and x.is_integer())}
        if not types[schema['type']](value): return False
    if 'enum' in schema and value not in schema['enum']: return False
    if 'const' in schema and value != schema['const']: return False
    if type(value) in (int,float):
        if value < schema.get('minimum', float('-inf')) or value > schema.get('maximum', float('inf')): return False
    if type(value) is str:
        if len(value) < schema.get('minLength', 0): return False
        if 'pattern' in schema and re.search(schema['pattern'], value) is None: return False
    if type(value) is list:
        if len(value) < schema.get('minItems',0) or len(value) > schema.get('maxItems',float('inf')): return False
        # Frozen uniqueItems applies only to integer rank arrays, including numeric equality of 1 and 1.0.
        if schema.get('uniqueItems') and any(a == b for i,a in enumerate(value) for b in value[i+1:]): return False
        if 'items' in schema and not all(validate_schema(schema['items'], x) for x in value): return False
        if 'contains' in schema and not any(validate_schema(schema['contains'], x) for x in value): return False
    if type(value) is dict:
        if not set(schema.get('required', [])) <= set(value): return False
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and not set(value) <= set(props): return False
        if not all(validate_schema(props[k],v) for k,v in value.items() if k in props): return False
    if 'allOf' in schema and not all(validate_schema(s,value) for s in schema['allOf']): return False
    if 'anyOf' in schema and not any(validate_schema(s,value) for s in schema['anyOf']): return False
    if 'oneOf' in schema and sum(validate_schema(s,value) for s in schema['oneOf']) != 1: return False
    if 'if' in schema:
        branch = 'then' if validate_schema(schema['if'],value) else 'else'
        if not validate_schema(schema.get(branch,{}),value): return False
    return True


def schema_keyword_guard(schema):
    known = {'$schema','type','properties','required','additionalProperties','items','minItems','maxItems',
             'uniqueItems','contains','oneOf','anyOf','allOf','if','then','else','enum','const','minimum',
             'maximum','minLength','pattern'}
    d.require(set(schema) <= known, 'Unimplemented schema keyword')
    for key in ('items','contains','if','then','else'):
        if key in schema: schema_keyword_guard(schema[key])
    for key in ('allOf','anyOf','oneOf'):
        for child in schema.get(key,[]): schema_keyword_guard(child)
    for child in schema.get('properties',{}).values(): schema_keyword_guard(child)


def diagnostic_input():
    # Contract requires these fixed bundle strings; only artificial payloads, no corpus lookup.
    bundle = ActiveBundle('last-mile-exception-triage-demo','1.0-demo','2026-01-01T00:00:00Z',None,'0'*64,'1'*64)
    evidence = tuple(RankedEvidence(i,'SOP-99','1.0-demo','shape-'+str(i),'Opaque interface',
                    'Slot '+str(i),'Arbitrary symbol slot '+str(i),0.9-i*0.01) for i in range(1,11))
    return GateInput('Artificial schema-only rank mapping diagnostic.',evidence,bundle)


def assess(raw, termination):
    result = {'A_json_valid': False, 'B_exact_schema_valid': False, 'C_adapter_valid': False,
              'generation_complete': termination == 'EOS', 'semantic_scoring': 'NOT_PERFORMED',
              'fencing_or_prefix_suffix_violation': raw.lstrip().startswith('```') or
                  not (raw.lstrip().startswith('{') and raw.rstrip().endswith('}'))}
    try:
        value = strict_json(raw)
        result['A_json_valid'] = True
        schema = json.loads(d.checked_schema((d.PREREG/'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes()))
        schema_keyword_guard(schema)
        result['B_exact_schema_valid'] = validate_schema(schema,value)
    except (ValueError,TypeError) as exc:
        result['json_error'] = str(exc)
    try:
        output = v2.adapt_response(raw,diagnostic_input())
        result['C_adapter_valid'] = True
        result['C_gate_output'] = asdict(output)
    except (ValueError,TypeError) as exc:
        result['C_adapter_error'] = str(exc)
    result['structural_acceptance'] = result['generation_complete'] and result['A_json_valid'] and result['B_exact_schema_valid']
    return result


def freeze():
    d.verify_v2()
    for filename in ('DECODER_API_RESULTS.json','TOKENIZER_INTEGRATION_RESULT.json','SCHEMA_COMPILATION_RESULT.json','HF_INTEGRATION_RESULT.json'):
        d.require(d.read(filename)['passed'], 'Prerequisite failed: '+filename)
    d.require(d.read('FUNCTIONAL_PROBE_PROCESS.json')['returncode'] == 0, 'Probe failed')
    schema = d.checked_schema((d.PREREG/'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes())
    schema_keyword_guard(json.loads(schema))
    system = ('This is an artificial JSON interface test, not a policy question or semantic evaluation. '
              'Emit exactly one object satisfying the supplied JSON Schema. No Markdown, commentary or external facts. '
              'Rank slots 1 through 10 are arbitrary supplied symbols. Select compatible enum fields for the requested '
              'structural branch. Keep each ask string short.\nExact schema:\n'+schema)
    branches = [
        'Create one material_asks element with ask string "Opaque alpha", support_status SUPPORTED, and supporting_evidence_ranks [1]. Choose compatible remaining fields.',
        'Create two material_asks elements: "Opaque beta" with SUPPORTED and ranks [1,2], and "Opaque gamma" with SUPPORTED and ranks [3]. Choose compatible remaining fields.',
        'Create one material_asks element with ask string "Opaque delta", support_status UNSUPPORTED, and an empty supporting_evidence_ranks array. Choose compatible remaining fields.',
    ]
    cases = [{'case_id': case_id, 'messages':[{'role':'system','content':system},{'role':'user','content':branch}],
              'semantic_gold': None} for case_id,branch in zip(CASE_IDS,branches)]
    d.write('STRUCTURAL_SMOKE_CONFIG.json', CONFIG)
    d.event('SMOKE_CONFIG_FROZEN', {'sha256':d.sha((d.OUT/'STRUCTURAL_SMOKE_CONFIG.json').read_bytes())})
    d.write('STRUCTURAL_SMOKE_SUITE.json', {'purpose':'STRUCTURAL_ONLY_NO_SEMANTIC_LABELS','cases':cases})
    d.event('STRUCTURAL_SMOKE_SUITE_FROZEN', {'sha256':d.sha((d.OUT/'STRUCTURAL_SMOKE_SUITE.json').read_bytes())})
    print('S1-S3 and config frozen; no model initialized.')


def frozen_plan():
    events = [json.loads(s) for s in (d.OUT/'DECODER_QUALIFICATION_JOURNAL.jsonl').read_text().splitlines()]
    for event_name, filename in (('SMOKE_CONFIG_FROZEN','STRUCTURAL_SMOKE_CONFIG.json'),
                                 ('STRUCTURAL_SMOKE_SUITE_FROZEN','STRUCTURAL_SMOKE_SUITE.json')):
        rows = [e for e in events if e['event']==event_name]
        d.require(len(rows)==1 and d.sha((d.OUT/filename).read_bytes())==rows[0]['details']['sha256'], 'Frozen input drift')
    config,suite = d.read('STRUCTURAL_SMOKE_CONFIG.json'),d.read('STRUCTURAL_SMOKE_SUITE.json')
    d.require(config==CONFIG, 'Config mismatch')
    validate_cases(suite['cases'])
    return config,suite


def validate_cases(cases):
    d.require(tuple(c['case_id'] for c in cases)==CASE_IDS, 'Exactly S1-S3, fixed order, no fourth call')
    d.require(all(c['semantic_gold'] is None for c in cases), 'No semantic labels')


def mark_tests():
    d.require(not (d.OUT/'MODEL_INITIALIZATION_RESULT.json').exists(), 'Tests must precede initialization')
    d.require(d.read('PRE_GENERATION_TEST_RESULTS.json')['passed'], 'Tests did not pass')
    files = [Path(d.__file__),Path(__file__),ROOT/'gateway/domain/tests/test_xgrammar_v2_decoder.py']
    d.write('EXECUTION_SOURCE_RECEIPT.json', {str(p.relative_to(ROOT)):d.sha(p.read_bytes()) for p in files})
    d.event('PRE_GENERATION_TESTS_PASSED', {'source_receipt_sha256':d.sha((d.OUT/'EXECUTION_SOURCE_RECEIPT.json').read_bytes())})


def generate_child():
    os.environ.update(d.OFFLINE)
    config,suite = frozen_plan()
    observations = {'socket_events':[],'subprocess_events':[],'prohibited_opens':[]}
    def audit(name,args):
        if name.startswith('socket.'):
            observations['socket_events'].append({'operation':name,'arguments':[str(a) for a in args]})
            if name in ('socket.connect','socket.getaddrinfo','socket.gethostbyname'): raise RuntimeError('Network forbidden')
        elif name=='subprocess.Popen': observations['subprocess_events'].append({'executable':str(args[0]),'arguments':str(args[1])})
        elif name=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            path=os.fsdecode(args[0]).replace(chr(92),'/').lower()
            if any(s in path for s in ('/development/','/private_heldout/','/held_out/')):
                observations['prohibited_opens'].append(path)
                raise RuntimeError('Benchmark access forbidden')
    sys.addaudithook(audit)
    try:
        import torch
        import xgrammar
        from xgrammar.contrib.hf import LogitsProcessor
        from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
        torch.set_num_threads(config['torch_num_threads'])
        torch.set_num_interop_threads(config['torch_num_interop_threads'])
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        model_inventory=json.loads((ROOT/'artifacts/answerability_semantic_runtime_v1_enablement/MODEL_FILE_INVENTORY.json').read_bytes())
        snapshot=Path(model_inventory['snapshot_path'])
        for row in model_inventory['files']:
            path=snapshot/row['relative_path']
            # Streaming custody check, including all weight bytes, before initialization.
            h=__import__('hashlib').sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda:f.read(8*1024*1024), b''): h.update(chunk)
            d.require(h.hexdigest()==row['sha256'], 'Model file drift')
        d.write('MODEL_FILE_VERIFICATION.json', {'passed':True,'files':model_inventory['files'],'count':10})
        tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False)
        d.require(d.sha(tokenizer.chat_template.encode())==d.CHAT_SHA,'Chat template drift')
        model_config=json.loads((snapshot/'config.json').read_bytes())
        info=xgrammar.TokenizerInfo.from_huggingface(tokenizer,vocab_size=model_config['vocab_size'])
        grammar=d.compile_exact(xgrammar,info,(d.PREREG/'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes())
        d.event('MODEL_INITIALIZATION_STARTED',{'count':1})
        model=AutoModelForCausalLM.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False,
                    torch_dtype=torch.float32,device_map='cpu').eval()
        d.require(all(p.device.type=='cpu' and p.dtype==torch.float32 for p in model.parameters()),'Model runtime mismatch')
        d.write('MODEL_INITIALIZATION_RESULT.json',{'passed':True,'count':1,'device':'cpu','dtype':'float32','quantized':False})
        d.event('MODEL_INITIALIZED',{'count':1,'device':'cpu','dtype':'float32'})
        generation=GenerationConfig.from_pretrained(str(snapshot),local_files_only=True)
        generation.do_sample=False
        generation.num_beams=1
        generation.max_new_tokens=512
        generation.temperature=1.0
        generation.top_p=1.0
        generation.top_k=50
        d.write('EFFECTIVE_GENERATION_CONFIG.json',generation.to_dict())
        results=[]
        with (d.OUT/'RAW_STRUCTURAL_OUTPUTS.jsonl').open('xb') as raw_file:
            for case in suite['cases']:
                ids=tokenizer.apply_chat_template(case['messages'],tokenize=True,add_generation_prompt=True,return_tensors='pt')
                start=time.monotonic()
                d.event('STRUCTURAL_SMOKE_STARTED',{'case_id':case['case_id'],'call_number':len(results)+1})
                box={}
                def worker():
                    try:
                        with torch.inference_mode():
                            box['output']=model.generate(ids,attention_mask=torch.ones_like(ids),
                                generation_config=generation,logits_processor=[LogitsProcessor(grammar)])
                    except BaseException:
                        box['error']=traceback.format_exc()
                thread=threading.Thread(target=worker,daemon=True)
                thread.start()
                thread.join(config['per_call_timeout_seconds'])
                elapsed=time.monotonic()-start
                status='TIMEOUT' if thread.is_alive() else 'ERROR' if 'error' in box else None
                token_ids=[] if status else box['output'][0,ids.shape[1]:].tolist()
                eos=generation.eos_token_id if isinstance(generation.eos_token_id,list) else [generation.eos_token_id]
                status=status or ('EOS' if token_ids and token_ids[-1] in eos else 'TOKEN_LIMIT')
                raw=tokenizer.decode(token_ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                row={'case_id':case['case_id'],'request_config_sha256':d.sha(d.canonical({'case':case,'config':config})),
                     'input_token_count':ids.shape[1],'raw_output_text':raw,'raw_output_byte_length':len(raw.encode()),
                     'raw_output_sha256':d.sha(raw.encode()),'generated_token_count':len(token_ids),'generated_token_ids':token_ids,
                     'elapsed_seconds':elapsed,'termination_status':status,'error':box.get('error'),
                     'partial_tokens_available':status not in ('TIMEOUT','ERROR')}
                raw_file.write((json.dumps(row,sort_keys=True)+'\n').encode());raw_file.flush();os.fsync(raw_file.fileno())
                validation=assess(raw,status)
                results.append({'case_id':case['case_id'],**validation})
                d.event('STRUCTURAL_SMOKE_COMPLETED',{'case_id':case['case_id'],'termination':status,**validation})
                print(case['case_id'],status,validation,flush=True)
                if status in ('TIMEOUT','ERROR'):
                    d.write('STRUCTURAL_SMOKE_RESULTS.json',{'results':results,'outcome':'DECODER_QUALIFICATION_FAILED'})
                    if status=='TIMEOUT':
                        d.write('GENERATION_OBSERVATIONS.json',observations)
                        os._exit(2)
                    return
        outcome='DECODER_QUALIFIED' if all(r['structural_acceptance'] for r in results) else 'DECODER_QUALIFICATION_FAILED'
        d.write('STRUCTURAL_SMOKE_RESULTS.json',{'results':results,'outcome':outcome})
        d.event('QUALIFICATION_SCORED',{'outcome':outcome,'structural_passes':sum(r['structural_acceptance'] for r in results)})
    except BaseException:
        d.write('GENERATION_FAILURE.json',{'traceback':traceback.format_exc(),'retries':0})
        raise
    finally:
        d.write('GENERATION_OBSERVATIONS.json',observations)


def run():
    d.no_repeat('STRUCTURAL_EXECUTION_STARTED')
    frozen_plan()
    d.require(d.inventory()==d.read('POST_INSTALL_PACKAGE_INVENTORY.json'),'Runtime drift')
    d.verify_v2()
    for path,digest in d.read('EXECUTION_SOURCE_RECEIPT.json').items():
        d.require(d.sha((ROOT/path).read_bytes())==digest,'Execution source drift')
    d.event('STRUCTURAL_EXECUTION_STARTED',{'maximum_calls':3,'retries':0})
    result=subprocess.run([str(d.PYTHON),'-I','-B',str(Path(__file__).resolve()),'generate_child'],
                          cwd=d.PYTHON.parent.parent,env=dict(os.environ,**d.OFFLINE),capture_output=True,text=True,
                          encoding='utf-8',errors='replace')
    d.write('GENERATION_PROCESS.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    print(result.stdout);print(result.stderr)


def recompute():
    frozen_plan()
    rows=[json.loads(line) for line in (d.OUT/'RAW_STRUCTURAL_OUTPUTS.jsonl').read_text().splitlines()]
    d.require(tuple(r['case_id'] for r in rows)==CASE_IDS,'Expected three raw outputs')
    for row in rows:
        d.require(d.sha(row['raw_output_text'].encode())==row['raw_output_sha256'],'Raw output drift')
    results=[{'case_id':r['case_id'],**assess(r['raw_output_text'],r['termination_status'])} for r in rows]
    expected=d.read('STRUCTURAL_SMOKE_RESULTS.json')
    d.require(expected['results']==results,'Saved-result validation mismatch')
    d.require(expected['outcome']==('DECODER_QUALIFIED' if all(r['structural_acceptance'] for r in results) else 'DECODER_QUALIFICATION_FAILED'),'Outcome mismatch')
    events=[json.loads(s) for s in (d.OUT/'DECODER_QUALIFICATION_JOURNAL.jsonl').read_text().splitlines()]
    d.require(sum(e['event']=='STRUCTURAL_SMOKE_STARTED' for e in events)==3,'Call budget mismatch')
    d.require(d.inventory()==d.read('POST_INSTALL_PACKAGE_INVENTORY.json'),'Post-generation drift')
    d.verify_v2()
    d.write('SAVED_RESULT_RECOMPUTATION.json',{'passed':True,'exact_raw_records':3,'outcome':expected['outcome'],
           'schema_validation_method':'Independent interpreter of all keywords in hash-locked exact V2 schema',
           'package_drift':0,'source_and_config_unchanged':True})
    d.write('FINAL_PACKAGE_INVENTORY.json',d.inventory())
    d.pip_check('FINAL_PIP_CHECK.json')
    print('Saved-result recomputation PASS;',expected['outcome'])


if __name__=='__main__':
    {'freeze':freeze,'mark_tests':mark_tests,'run':run,'generate_child':generate_child,'recompute':recompute}[sys.argv[1]]()
