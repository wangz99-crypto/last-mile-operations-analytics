"""Frozen 12-case qualification execution only; no semantic judge or retrieval."""
from copy import deepcopy
from dataclasses import asdict
import os
from pathlib import Path
import sys
import threading
import time
import traceback
import json

from run_qwen_smoke_eager_recovery import (ROOT, RUNTIME, SCHEMA, REGEX, CHAT_SHA, INV_SHA,
    sha, read, encoded, digest, now, git, gate, snapshot_spec, verify_snapshot, load_cpu_fp32,
    require_context_capacity, inventory, pip_check, build_messages, adapt_response, ContractError)

ART = ROOT / 'artifacts/answerability_semantic_v2_1_semantic_qualification'
PREVIOUS = ROOT / 'artifacts/answerability_semantic_v2_1_qwen_structural_smoke_recovery'


def save(name, value):
    with (ART/name).open('wb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def execute():
    assert not (ART/'RAW_GENERATIONS.json').exists(), 'Refuse qualification retry/overwrite'
    freeze=read(ART/'SUITE_FREEZE_RECEIPT.json')
    audit=read(ART/'FRESHNESS_AUDIT.json')
    assert audit['status']=='PASS' and audit['exact_duplicates']==audit['one_to_one_paraphrases']==0
    assert sha(__file__)==audit['execution_helper_sha256']
    assert sha(ART/'SUITE_FREEZE_RECEIPT.json')==audit['suite_freeze_receipt_sha256']
    assert git('rev-parse','HEAD')==git('rev-list','-n','1',freeze['base_tag'])==freeze['base_commit']
    for p,h in freeze['files_sha256'].items(): assert sha(ART/p)==h,p
    for p,h in freeze['immutable_source_sha256'].items(): assert sha(ROOT/p)==h,p
    previous=read(PREVIOUS/'RUNTIME_IDENTITY.json')
    historical_receipt=read(PREVIOUS/'FINAL_SHA256.json')
    for p,h in historical_receipt['files'].items(): assert sha(ROOT/p)==h,p
    for p,h in previous['immutable_inputs_sha256'].items(): assert sha(ROOT/p)==h,p
    for p,h in previous['installed_execution_sources_sha256'].items(): assert sha(Path(p))==h,p
    packages,check=inventory(),pip_check()
    assert packages==previous['post_environment']['packages'] and check['returncode']==0
    # Execution loads only frozen GateInputs/messages. Gold is never loaded here.
    fixtures=read(ART/'QUALIFICATION_SUITE.json')['cases']
    assert [x['case_id'] for x in fixtures]==['Q%02d'%i for i in range(1,13)]
    execution={'status':'STARTED','started_utc':now(),'helper_sha256':sha(__file__),
        'suite_freeze_receipt_sha256':sha(ART/'SUITE_FREEZE_RECEIPT.json'),
        'freshness_audit_sha256':sha(ART/'FRESHNESS_AUDIT.json'),
        'historical_recovery_manifest_sha256':sha(PREVIOUS/'FINAL_SHA256.json'),
        'requested_generation_config':freeze['generation_config'],'actual_configs':[],
        'compiler_stance':'force_eager','pre_environment':{'packages':packages,'pip_check':check},
        'counters':{'model_initialization':0,'tokenizer_loads':0,'generate':0,'forward':0,'retries':0,'repairs':0,
                    'timeouts':0,'DEVELOPMENT':0,'retrieval':0,'package_mutations':0,'downloads':0},
        'socket_events':[],'phase_2h_held_out_access':False,'phase_2g_private_heldout_access':False}
    raw_rows,rows,attempts=[],[],[]
    def checkpoint(): save('STRUCTURAL_RESULTS.json',{'execution':execution,'rows':rows,'attempts':attempts})
    save('RAW_GENERATIONS.json',{'rows':raw_rows})
    checkpoint()
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',
                      PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false',
                      OUTLINES_CACHE_DIR=str(ROOT/'.cache/phase2h-direct-regex-runtime'))
    def guard(event,args):
        if event.startswith('socket.'):
            execution['socket_events'].append({'operation':event,'arguments':str(args)})
            if event not in {'socket.__new__','socket.gethostname'}:
                if event!='socket.bind' or str(args[1][0]) not in {'::1','127.0.0.1'}:
                    raise RuntimeError('Offline boundary: '+event)
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=os.fsdecode(args[0]).lower().replace('\\','/')
            if any(x in p for x in ('/private_heldout/','/held_out/','/heldout/','/answerability/development/',
                                   '/retrieval/development/','/answerability_dev_bge_evidence_v0/')):
                raise RuntimeError('Benchmark quarantine: '+p)
    sys.addaudithook(guard)
    active=None; timed_out=False
    try:
        spec=snapshot_spec()
        verified=verify_snapshot(spec,RUNTIME/'MODEL_FILE_INVENTORY.json',INV_SHA)
        assert len(verified['files'])==10
        execution['snapshot_verification']={'matched':10,'files':verified['files']}
        assert digest(read(Path(spec.snapshot_path)/'tokenizer_config.json')['chat_template'].encode())==CHAT_SHA
        import torch
        from transformers import GenerationConfig,LogitsProcessorList
        from outlines_core import Guide
        from outlines.backends.outlines_core import OutlinesCoreBackend,OutlinesCoreLogitsProcessor
        from outlines.models.transformers import TransformerTokenizer
        from qualify_exact_validator import resolve,strict_parse
        assert str(torch.__version__)==previous['torch_version']=='2.14.0+cpu'
        requested=freeze['generation_config']; config=GenerationConfig.from_dict(deepcopy(requested))
        assert config.to_dict()==requested and len(requested)==67
        _,validator=resolve(read(SCHEMA))
        execution['counters']['model_initialization']=1; execution['counters']['tokenizer_loads']=1
        checkpoint()
        model,tok,model_config,receipt=load_cpu_fp32(spec,RUNTIME/'MODEL_FILE_INVENTORY.json',INV_SHA)
        execution['model_load_receipt']=receipt
        assert digest(tok.chat_template.encode())==CHAT_SHA
        assert torch.get_num_threads()==4 and torch.get_num_interop_threads()==1 and torch.are_deterministic_algorithms_enabled()
        model.generation_config=deepcopy(config)
        wrapped=TransformerTokenizer(tok); backend=object.__new__(OutlinesCoreBackend)
        backend.eos_token_id=wrapped.eos_token_id
        backend.vocabulary=OutlinesCoreBackend.create_outlines_core_vocabulary(wrapped.get_vocab(),wrapped.eos_token_id,wrapped.eos_token,wrapped.convert_token_to_string)
        backend.tensor_library_name='torch'
        index=backend.get_regex_logits_processor(REGEX.read_text(encoding='utf-8')).index
        execution['index_constructions']=1
        def forward_count(module,args): execution['counters']['forward']+=1
        hook=model.register_forward_pre_hook(forward_count)
        original_prepare=model._prepare_generation_config
        def guarded_prepare(*args,**kwargs):
            effective,other=original_prepare(*args,**kwargs); actual=effective.to_dict()
            execution['actual_configs'].append({'case_id':active,'requested':deepcopy(requested),'actual':actual,
                'equal':actual==requested,'matched_fields':sum(actual.get(k)==v for k,v in requested.items())})
            checkpoint(); assert actual==requested, 'Effective configuration mismatch'
            return effective,other
        model._prepare_generation_config=guarded_prepare
        for fixture in fixtures:
            for p,h in freeze['files_sha256'].items(): assert sha(ART/p)==h,p
            assert sha(__file__)==audit['execution_helper_sha256']
            value=gate(fixture['gate_input']); messages=list(build_messages(value))
            assert digest(encoded(asdict(value)))==fixture['gate_input_sha256']
            assert messages==fixture['messages'] and digest(encoded(messages))==fixture['messages_sha256']
            assert len(value.evidence)==10
            rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            inputs=tok(rendered,return_tensors='pt',add_special_tokens=False); length=inputs['input_ids'].shape[1]
            margin=require_context_capacity(length,requested['max_new_tokens'],model_config.max_position_embeddings)
            active=fixture['case_id']; attempt={'case_id':active,'status':'GENERATING','started_utc':now()}; attempts.append(attempt)
            execution['counters']['generate']+=1; assert execution['counters']['generate']<=12
            checkpoint(); start=time.monotonic(); before=execution['counters']['forward']; box={}
            processor=OutlinesCoreLogitsProcessor(index,'torch')
            def once():
                try:
                    with torch.compiler.set_stance('force_eager'):
                        with torch.inference_mode():
                            box['tokens']=model.generate(**inputs,generation_config=deepcopy(config),use_model_defaults=False,
                                                         logits_processor=LogitsProcessorList([processor]))
                except BaseException: box['error']=traceback.format_exc()
            worker=threading.Thread(target=once,daemon=True); worker.start(); worker.join(freeze['runtime_controls']['per_call_timeout_seconds'])
            if worker.is_alive():
                execution['counters']['timeouts']+=1; timed_out=True
                raise TimeoutError('Frozen 600-second deadline; no recovery')
            if 'error' in box: raise RuntimeError(box['error'])
            tokens=box['tokens'][0,length:].tolist(); eos=tokens[-1] if tokens and tokens[-1] in requested['eos_token_id'] else None
            content=tokens[:-1] if eos is not None else tokens
            raw=tok.decode(content,skip_special_tokens=False,clean_up_tokenization_spaces=False).encode('utf-8')
            raw_rows.append({'case_id':active,'generation_completed':True,'generated_token_ids':tokens,
                'decoded_with_control_tokens':tok.decode(tokens,skip_special_tokens=False,clean_up_tokenization_spaces=False),
                'terminal_control_token_id':eos,'raw_text':raw.decode('utf-8'),'raw_utf8_hex':raw.hex(),
                'raw_sha256':digest(raw),'raw_byte_length':len(raw),'generated_tokens':len(tokens),'input_tokens':length,
                'context_margin':margin,'rendered_prompt_sha256':digest(rendered.encode()),
                'forward_calls':execution['counters']['forward']-before,'elapsed_seconds':time.monotonic()-start,
                'saved_before_parse_utc':now()})
            save('RAW_GENERATIONS.json',{'rows':raw_rows})
            attempt['status']='GENERATION_COMPLETE'
            row={'case_id':active,'generation_completed':True,'raw_sha256':digest(raw),'raw_byte_length':len(raw),
                 'decoder':'NOT_RUN','JSON_parse':'NOT_RUN','exact_schema':'NOT_RUN','adapter':'NOT_RUN'}
            guide=Guide(index); ok=True
            for token in content:
                if token not in guide.get_tokens(): ok=False; break
                guide.advance(token_id=token,return_tokens=False)
            ok=ok and guide.is_finished() and wrapped.eos_token_id in guide.get_tokens()
            row['decoder']='PASS' if ok else 'FAIL'
            if not ok: row['disposition']='DECODER_STRUCTURAL_REJECT'
            else:
                try: parsed=strict_parse(raw); row['JSON_parse']='PASS'
                except (UnicodeError,ValueError) as exc: row.update(JSON_parse='FAIL',disposition='JSON_PARSE_REJECT',error=str(exc))
                if row['JSON_parse']=='PASS':
                    errors=list(validator.iter_errors(parsed)); row['exact_schema']='FAIL' if errors else 'PASS'
                    if errors:
                        row.update(disposition='EXACT_SCHEMA_REJECT',schema_errors=[{'path':list(e.absolute_path),'schema_path':list(e.absolute_schema_path),'message':e.message} for e in errors])
                    else:
                        try: row.update(adapter='PASS',gate_output=asdict(adapt_response(raw,value)),disposition='COMBINED_STRUCTURAL_ACCEPT')
                        except ContractError as exc: row.update(adapter='FAIL',disposition='ADAPTER_STRUCTURAL_REJECT',error=str(exc))
            rows.append(row); attempt['status']=row['disposition']; checkpoint()
            print(json.dumps({k:row[k] for k in ('case_id','JSON_parse','exact_schema','adapter','disposition')}),flush=True)
        hook.remove(); execution['status']='EXECUTION_COMPLETE_AWAITING_MANUAL_SCORING'
    except BaseException:
        execution['status']='SEMANTIC_V2_1_QUALIFICATION_RUNTIME_FAILED'; execution['failure']=traceback.format_exc()
        if attempts and attempts[-1]['status']=='GENERATING': attempts[-1]['status']='RUNTIME_FAILED'
    finally:
        seen={a['case_id'] for a in attempts}
        for fixture in fixtures:
            if fixture['case_id'] not in seen: attempts.append({'case_id':fixture['case_id'],'status':'NOT_RUN'})
        after,check=inventory(),pip_check()
        execution['post_environment']={'packages':after,'pip_check':check,'matches_pre':after==packages}
        execution['historical_sources_unchanged']=all(sha(ROOT/p)==h for p,h in previous['immutable_inputs_sha256'].items()) and all(sha(ROOT/p)==h for p,h in historical_receipt['files'].items())
        execution['installed_execution_sources_unchanged']=all(sha(Path(p))==h for p,h in previous['installed_execution_sources_sha256'].items())
        execution['freeze_unchanged']=all(sha(ART/p)==h for p,h in freeze['files_sha256'].items())
        execution['finished_utc']=now()
        execution['counts']={'completed_generations':len(raw_rows),'JSON_PASS':sum(r['JSON_parse']=='PASS' for r in rows),
            'exact_schema_PASS':sum(r['exact_schema']=='PASS' for r in rows),'adapter_PASS':sum(r['adapter']=='PASS' for r in rows),
            'combined_accept':sum(r['disposition']=='COMBINED_STRUCTURAL_ACCEPT' for r in rows)}
        checkpoint()
        print(json.dumps({'status':execution['status'],'counts':execution['counts'],'counters':execution['counters'],
                          'failure':execution.get('failure')}),flush=True)
        if timed_out: os._exit(2)


if __name__=='__main__':
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',PIP_NO_INDEX='1')
    execute()
