"""One frozen force-eager recovery; no new inputs, tuning, or retries."""
from copy import deepcopy
from dataclasses import asdict
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback

import run_qwen_structural_smoke as historical
from run_qwen_structural_smoke import (ROOT, RUNTIME, SCHEMA, REGEX, PROMPT, CHAT_SHA, INV_SHA,
    encoded, digest, sha, read, now, git, gate, snapshot_spec, verify_snapshot,
    load_cpu_fp32, require_context_capacity, inventory, pip_check, build_messages, adapt_response, ContractError)

ART = ROOT / 'artifacts/answerability_semantic_v2_1_qwen_structural_smoke_recovery'
HISTORY = historical.ART
BASE = 'b696dc6c521c05ad79b32256975d0a10a21644de'
TAG = 'answerability-semantic-v2_1-qwen-smoke-v0.1-runtime-failed'
MODE = 'PYTORCH_FORCE_EAGER_FOR_OUTLINES_MASK_RUNTIME'
FIXTURE_SHA = '3abf857514394cbbab8ea2b2f3f14095ffe917b8dd16906f5d97b6120ac598a6'
PROBES = [('PRE-1', 16, [0, 3, 7, 15]), ('PRE-2', 32, [31]),
          ('PRE-3', 70, [0, 1, 31, 32, 47, 63, 64, 69])]


def save(name, value, exclusive=False):
    with (ART / name).open('xb' if exclusive else 'wb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())


def prepare():
    assert not ART.exists(), 'Refuse overwrite of recovery'
    assert git('rev-parse', 'HEAD') == git('rev-list', '-n', '1', TAG) == BASE
    helper = Path(__file__).relative_to(ROOT).as_posix()
    assert git('status', '--porcelain', '--untracked-files=all') == '?? ' + helper
    old = read(HISTORY / 'RUNTIME_IDENTITY.json')
    owner = (HISTORY / 'FINAL_RECORD.md').read_text(encoding='utf-8')
    assert 'OWNER_REVIEWED / QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED' in owner
    assert 'OUTLINES_CORE_TORCH_MASK_INDUCTOR_TOOLCHAIN_UNAVAILABLE' in owner
    assert old['status'] == 'QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED'
    assert old['counters']['generate'] == old['counters']['forward'] == 1
    assert not read(HISTORY / 'RAW_GENERATIONS.json')['rows']
    assert 'InvalidCxxCompiler: Compiler: cl is not found.' in old['failure']
    assert sha(HISTORY / 'FINAL_SHA256.json') == '8234d07b3600d022e7a51bff6d6847b43ab2d5258e4f6712ebd06db57c996590'
    frozen = dict(old['immutable_inputs_sha256'])
    frozen.update(read(HISTORY / 'FINAL_SHA256.json')['files'])
    frozen[(HISTORY / 'FINAL_SHA256.json').relative_to(ROOT).as_posix()] = sha(HISTORY / 'FINAL_SHA256.json')
    for p, h in frozen.items():
        assert sha(ROOT / p) == h, p
    assert sha(HISTORY / 'SMOKE_FIXTURES.json') == FIXTURE_SHA
    assert len(old['requested_generation_config']) == 67
    assert old['actual_runtime_generation_configs'][0]['actual'] == old['requested_generation_config']
    spec = snapshot_spec()
    inv = verify_snapshot(spec, RUNTIME / 'MODEL_FILE_INVENTORY.json', INV_SHA)
    assert len(inv['files']) == 10
    assert digest(read(Path(spec.snapshot_path) / 'tokenizer_config.json')['chat_template'].encode()) == CHAT_SHA
    packages, check = inventory(), pip_check()
    assert packages == old['post_environment']['packages'] and check['returncode'] == 0
    assert packages['outlines']['version'] == '1.3.3' and packages['outlines-core']['version'] == '0.2.14'
    site = Path(sys.prefix) / 'Lib/site-packages'
    kernel_sources = {str(site / p): sha(site / p) for p in (
        'outlines_core/kernels/torch.py', 'outlines/backends/outlines_core.py',
        'outlines/processors/base_logits_processor.py', 'torch/compiler/__init__.py')}
    assert '@torch.compile(dynamic=True)' in (site / 'outlines_core/kernels/torch.py').read_text(encoding='utf-8')
    frozen[helper] = sha(__file__)
    ART.mkdir()
    protocol = '''# Qwen Structural Smoke Eager Runtime Recovery

Frozen before preflight. RECOVERY_RUN_AFTER_NON_RESULT_BEARING_RUNTIME_FAILURE.
The prior attempt remains immutable: one generate and one measured forward, no completed raw generation. This is not the first smoke attempt. SMOKE-02/03 were not run historically.

Only runtime change: official torch.compiler.set_stance("force_eager") around the installed masking function for preflight and around the frozen model.generate call in its worker thread. No package/source patch, kernel replacement, compiler installation, PATH modification, tensor-library change, decoder switch, or scientific change. No force_backend or unsafe flag. Compiler stance is separate from all 67 frozen generation parameters.

Three predetermined synthetic masks, executed exactly once before model loading: PRE-1 size 16 allowed [0,3,7,15]; PRE-2 size 32 allowed [31]; PRE-3 size 70 allowed [0,1,31,32,47,63,64,69]. Logits are exact FP32 values i/4 - 8. Python sets determine expected allowed IDs independently of the kernel; unsigned Python words are converted to signed int32 only for the installed kernel input. Expected output is independently assigned per index. Require allowed bytes unchanged, every disallowed logit negative infinity, full byte equality, and no exception/compiler invocation. Any preflight failure blocks model initialization.

Reuse historical SMOKE_FIXTURES.json bytes and messages, frozen canonical prompt, ten-file Qwen snapshot, tokenizer and chat template. Exactly the historical requested_generation_config, CPU FP32, seed=0, deterministic algorithms=true, threads=4/interop=1, timeout=600 seconds. Compare all 67 effective config fields inside _prepare_generation_config before forward. No model-default inheritance. No edits to helper, stance, inputs, parameters or structural components after preflight starts.

After all three preflight checks pass, SMOKE-01/02/03 each receive at most one sequential recovery generate. STOP on any runtime error or first completed structural failure. No retry, repair, manual completion, fallback or adaptive tuning. Preserve completed raw token IDs and UTF-8 payload before parsing, excluding only a final EOS control token exactly as the historical helper. No strip or normalization. Frozen decoder token traversal/final-state/EOS and qualified whitespace-closure interpretation, then original strict JSON parse, exact schema validator and deterministic adapter. Later stages NOT_RUN after failure. Semantic correctness NOT_EVALUATED, including every decision, material ask and support assignment.

Top-level causal-LM forwards are measured with the same pre-hook. Mask-only tensor operations are separate from model forward calls. Report historical and recovery calls separately, cumulative attempts=1+recovery actual. No new semantic suite, benchmark access, retrieval, download, external network or package mutation. Read-only hash/inventory checks and offline pip checks before/after. Seven artifacts and one helper only; no commit/tag.
'''
    (ART / 'RECOVERY_PROTOCOL.md').write_bytes(protocol.encode())
    state = {'status': 'FROZEN_BEFORE_PREFLIGHT', 'frozen_utc': now(), 'base_commit': BASE, 'base_tag': TAG,
        'entry_git_status': 'clean before sole recovery helper creation', 'recovery_mode': MODE,
        'run_type': 'RECOVERY_RUN_AFTER_NON_RESULT_BEARING_RUNTIME_FAILURE',
        'compiler_stance': 'force_eager', 'torch_version': packages['torch']['version'],
        'outlines_version': '1.3.3', 'outlines_core_version': '0.2.14', 'tensor_library': 'torch',
        'model': old['model'], 'snapshot_verification': {'matched':10,'files':inv['files'],'inventory_sha256':INV_SHA},
        'chat_template_sha256':CHAT_SHA, 'fixture_sha256':FIXTURE_SHA,
        'fixture_path':(HISTORY / 'SMOKE_FIXTURES.json').relative_to(ROOT).as_posix(),
        'requested_generation_config':old['requested_generation_config'],
        'requested_generation_config_sha256':old['requested_generation_config_sha256'],
        'actual_runtime_generation_configs':[], 'runtime_controls':old['runtime_controls'],
        'prompt_sha256':sha(PROMPT), 'schema_sha256':sha(SCHEMA), 'regex_sha256':sha(REGEX),
        'decoder':old['decoder'], 'validator':old['validator'],
        'helper_sha256':sha(__file__), 'protocol_sha256':sha(ART/'RECOVERY_PROTOCOL.md'),
        'immutable_inputs_sha256':frozen,'installed_execution_sources_sha256':kernel_sources,
        'pre_environment':{'packages':packages,'pip_check':check},
        'historical_counts':{'generate':1,'forward':1,'completed_generations':0},
        'counters':{'model_initialization':0,'tokenizer_loads':0,'generate':0,'forward':0,'retries':0,
                    'repairs':0,'timeouts':0,'mask_preflight_calls':0,'package_mutations':0,'downloads':0,
                    'DEVELOPMENT_access':0,'retrieval':0},
        'socket_events':[], 'subprocess_events':[], 'compiler_invocation_attempts':0,
        'phase_2h_held_out_access':False,'phase_2g_private_heldout_access':False,
        'fresh_semantic_qualification_suite':'NOT YET AUTHORED'}
    save('RUNTIME_IDENTITY.json',state,True)
    print(json.dumps({'status':state['status'],'helper_sha256':state['helper_sha256'],
                      'torch':state['torch_version'],'snapshot_matched':10}),flush=True)


def execute():
    assert not (ART/'EAGER_MASK_PREFLIGHT.json').exists(), 'Refuse second preflight or recovery'
    s=read(ART/'RUNTIME_IDENTITY.json')
    assert s['status']=='FROZEN_BEFORE_PREFLIGHT'
    assert git('rev-parse','HEAD')==git('rev-list','-n','1',TAG)==BASE
    assert sha(__file__)==s['helper_sha256'] and sha(ART/'RECOVERY_PROTOCOL.md')==s['protocol_sha256']
    assert all(sha(ROOT/p)==h for p,h in s['immutable_inputs_sha256'].items())
    assert all(sha(Path(p))==h for p,h in s['installed_execution_sources_sha256'].items())
    assert inventory()==s['pre_environment']['packages']
    fixtures=read(HISTORY/'SMOKE_FIXTURES.json')['fixtures']
    assert len(fixtures)==3
    pre={'status':'STARTED','rows':[],'compiler_stance':'force_eager','model_initialization_during_preflight':0}
    raw_rows, rows, attempts=[],[],[]
    s['pre_execution_runtime_identity_sha256']=sha(ART/'RUNTIME_IDENTITY.json')
    s['started_utc']=now()
    s['status']='PREFLIGHT_STARTED'
    def checkpoint():
        save('RUNTIME_IDENTITY.json',s)
    def results():
        save('STRUCTURAL_RESULTS.json',{'rows':rows,'attempts':attempts,'semantic_correctness':'NOT_EVALUATED'})
    save('EAGER_MASK_PREFLIGHT.json',pre,True)
    save('RAW_GENERATIONS.json',{'rows':raw_rows,'semantic_correctness':'NOT_EVALUATED'},True)
    checkpoint()
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',
                      PYTHONDONTWRITEBYTECODE='1',TOKENIZERS_PARALLELISM='false',
                      OUTLINES_CACHE_DIR=str(ROOT/'.cache/phase2h-direct-regex-runtime'))
    def guard(event,args):
        if event.startswith('socket.'):
            s['socket_events'].append({'operation':event,'arguments':str(args)})
            if event not in {'socket.__new__','socket.gethostname'}:
                if event!='socket.bind' or str(args[1][0]) not in {'::1','127.0.0.1'}:
                    raise RuntimeError('Offline boundary: '+event)
        if event=='subprocess.Popen':
            s['subprocess_events'].append({'executable':str(args[0]),'arguments':str(args[1])})
            executable=Path(str(args[0])).name.lower()
            if executable in {'cl','cl.exe','clang','clang.exe','clang-cl','clang-cl.exe','g++','g++.exe','gcc','gcc.exe','c++','c++.exe','ninja','ninja.exe'}:
                s['compiler_invocation_attempts']+=1
                raise RuntimeError('Native compiler invocation is outside recovery authorization')
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=os.fsdecode(args[0]).lower().replace('\\','/')
            if any(x in p for x in ('/private_heldout/','/held_out/','/heldout/','/answerability/development/',
                                   '/retrieval/development/','/answerability_dev_bge_evidence_v0/')):
                raise RuntimeError('Benchmark quarantine: '+p)
    sys.addaudithook(guard)
    failure=None
    timed_out=False
    active=None
    try:
        import torch
        from outlines_core.kernels.torch import apply_token_bitmask_inplace
        assert str(torch.__version__)==s['torch_version']
        for fid,size,allowed in PROBES:
            before_values=[i/4-8 for i in range(size)]
            expected_values=[v if i in set(allowed) else float('-inf') for i,v in enumerate(before_values)]
            unsigned=[sum(1<<(i%32) for i in allowed if i//32==word) for word in range((size+31)//32)]
            signed=[w if w<(1<<31) else w-(1<<32) for w in unsigned]
            logits=torch.tensor([before_values],dtype=torch.float32,device='cpu')
            before=logits.clone()
            mask=torch.tensor([signed],dtype=torch.int32,device='cpu')
            expected=torch.tensor([expected_values],dtype=torch.float32,device='cpu')
            probe={'id':fid,'vocab_size':size,'allowed_ids':allowed,'mask_words_int32':signed,'status':'STARTED'}
            pre['rows'].append(probe)
            s['counters']['mask_preflight_calls']+=1
            checkpoint()
            save('EAGER_MASK_PREFLIGHT.json',pre)
            with torch.compiler.set_stance('force_eager'):
                apply_token_bitmask_inplace(logits,mask)
            allowed_same=logits[0,allowed].numpy().tobytes()==before[0,allowed].numpy().tobytes()
            disallowed=[i for i in range(size) if i not in set(allowed)]
            disallowed_inf=bool(torch.isneginf(logits[0,disallowed]).all())
            exact_bytes=logits.numpy().tobytes()==expected.numpy().tobytes()
            probe.update(allowed_logits_byte_identical=allowed_same,disallowed_negative_infinity=disallowed_inf,
                         independent_expected_bytes_match=exact_bytes,actual_fp32_hex=logits.numpy().tobytes().hex(),
                         expected_fp32_hex=expected.numpy().tobytes().hex(),exception=None,
                         status='PASS' if allowed_same and disallowed_inf and exact_bytes else 'FAIL')
            save('EAGER_MASK_PREFLIGHT.json',pre)
            assert probe['status']=='PASS' and s['compiler_invocation_attempts']==0, 'Preflight mismatch'
        pre.update(status='PASS',passed=3,compiler_invocation_attempts=s['compiler_invocation_attempts'],finished_utc=now())
        save('EAGER_MASK_PREFLIGHT.json',pre)
        s['preflight_sha256']=sha(ART/'EAGER_MASK_PREFLIGHT.json')
        checkpoint()
        print('Mask semantic preflight: 3/3 PASS; no model loaded yet.',flush=True)
        from transformers import GenerationConfig,LogitsProcessorList
        from outlines_core import Guide
        from outlines.backends.outlines_core import OutlinesCoreBackend,OutlinesCoreLogitsProcessor
        from outlines.models.transformers import TransformerTokenizer
        from qualify_exact_validator import resolve,strict_parse
        requested=s['requested_generation_config']
        config=GenerationConfig.from_dict(deepcopy(requested))
        assert config.to_dict()==requested and len(requested)==67
        _,validator=resolve(read(SCHEMA))
        spec=snapshot_spec()
        assert digest(read(Path(spec.snapshot_path)/'tokenizer_config.json')['chat_template'].encode())==CHAT_SHA
        s['counters']['model_initialization']=1
        s['counters']['tokenizer_loads']=1
        s['status']='MODEL_INITIALIZING'
        checkpoint()
        model,tok,model_config,load_receipt=load_cpu_fp32(spec,RUNTIME/'MODEL_FILE_INVENTORY.json',INV_SHA)
        s['model_load_receipt']=load_receipt
        assert digest(tok.chat_template.encode())==CHAT_SHA
        assert torch.get_num_threads()==4 and torch.get_num_interop_threads()==1 and torch.are_deterministic_algorithms_enabled()
        model.generation_config=deepcopy(config)
        wrapped=TransformerTokenizer(tok)
        backend=object.__new__(OutlinesCoreBackend)
        backend.eos_token_id=wrapped.eos_token_id
        backend.vocabulary=OutlinesCoreBackend.create_outlines_core_vocabulary(wrapped.get_vocab(),wrapped.eos_token_id,wrapped.eos_token,wrapped.convert_token_to_string)
        backend.tensor_library_name='torch'
        index=backend.get_regex_logits_processor(REGEX.read_text(encoding='utf-8')).index
        s['index_constructions']=1
        s['decoder_eos_token_id']=wrapped.eos_token_id
        def observe_forward(module,args):
            s['counters']['forward']+=1
        hook=model.register_forward_pre_hook(observe_forward)
        original_prepare=model._prepare_generation_config
        def guarded_prepare(*args,**kwargs):
            effective,other=original_prepare(*args,**kwargs)
            actual=effective.to_dict()
            s['actual_runtime_generation_configs'].append({'id':active,'requested':deepcopy(requested),'actual':actual,
                                                           'equal':actual==requested,'matched_fields':sum(actual.get(k)==v for k,v in requested.items())})
            checkpoint()
            assert actual==requested, 'Frozen effective configuration mismatch'
            return effective,other
        model._prepare_generation_config=guarded_prepare
        for fixture in fixtures:
            assert sha(__file__)==s['helper_sha256'] and sha(HISTORY/'SMOKE_FIXTURES.json')==FIXTURE_SHA
            value=gate(fixture['gate_input'])
            assert digest(encoded(asdict(value)))==fixture['gate_input_sha256']
            messages=list(build_messages(value))
            assert messages==fixture['messages'] and digest(encoded(messages))==fixture['messages_sha256']
            rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            inputs=tok(rendered,return_tensors='pt',add_special_tokens=False)
            length=inputs['input_ids'].shape[1]
            margin=require_context_capacity(length,requested['max_new_tokens'],model_config.max_position_embeddings)
            assert config.to_dict()==requested
            active=fixture['id']
            attempt={'id':active,'status':'GENERATING','started_utc':now()}
            attempts.append(attempt)
            s['counters']['generate']+=1
            assert s['counters']['generate']<=3
            s['status']='GENERATING'
            checkpoint()
            results()
            processor=OutlinesCoreLogitsProcessor(index,'torch')
            start=time.monotonic()
            forward_before=s['counters']['forward']
            box={}
            def generate_once():
                try:
                    with torch.compiler.set_stance('force_eager'):
                        with torch.inference_mode():
                            box['tokens']=model.generate(**inputs,generation_config=deepcopy(config),use_model_defaults=False,
                                                         logits_processor=LogitsProcessorList([processor]))
                except BaseException:
                    box['error']=traceback.format_exc()
            worker=threading.Thread(target=generate_once,daemon=True)
            worker.start()
            worker.join(s['runtime_controls']['per_call_timeout_seconds'])
            if worker.is_alive():
                s['counters']['timeouts']+=1
                timed_out=True
                raise TimeoutError('Frozen 600-second generation deadline; stop without retry')
            if 'error' in box:
                raise RuntimeError(box['error'])
            tokens=box['tokens'][0,length:].tolist()
            terminal=tokens[-1] if tokens and tokens[-1] in requested['eos_token_id'] else None
            content=tokens[:-1] if terminal is not None else tokens
            raw=tok.decode(content,skip_special_tokens=False,clean_up_tokenization_spaces=False).encode('utf-8')
            raw_rows.append({'id':active,'generation_completed':True,'generated_token_ids':tokens,
                'decoded_with_control_tokens':tok.decode(tokens,skip_special_tokens=False,clean_up_tokenization_spaces=False),
                'terminal_control_token_id':terminal,'raw_text':raw.decode('utf-8'),'raw_utf8_hex':raw.hex(),
                'raw_byte_length':len(raw),'raw_sha256':digest(raw),'input_tokens':length,'context_margin':margin,
                'rendered_prompt_sha256':digest(rendered.encode()),'generated_tokens':len(tokens),
                'forward_calls':s['counters']['forward']-forward_before,'elapsed_seconds':time.monotonic()-start,
                'saved_before_parse_utc':now(),'semantic_accuracy':'NOT_EVALUATED'})
            save('RAW_GENERATIONS.json',{'rows':raw_rows,'semantic_correctness':'NOT_EVALUATED'})
            attempt['status']='GENERATION_COMPLETE'
            row={'id':active,'generation_completed':True,'raw_byte_length':len(raw),'raw_sha256':digest(raw),
                 'decoder':'NOT_RUN','JSON_parse':'NOT_RUN','exact_schema':'NOT_RUN','adapter':'NOT_RUN','semantic_accuracy':'NOT_EVALUATED'}
            guide=Guide(index)
            decoder_ok=True
            for token in content:
                if token not in guide.get_tokens():
                    decoder_ok=False
                    break
                guide.advance(token_id=token,return_tokens=False)
            decoder_ok=decoder_ok and guide.is_finished() and wrapped.eos_token_id in guide.get_tokens()
            row['decoder']='PASS' if decoder_ok else 'FAIL'
            row['decoder_acceptance_basis']='Frozen traversal/final-state/EOS and qualified JSON-whitespace closure; not sole-EOS'
            if not decoder_ok:
                row['disposition']='DECODER_STRUCTURAL_REJECT'
            else:
                try:
                    parsed=strict_parse(raw)
                    row['JSON_parse']='PASS'
                except (UnicodeError,ValueError) as exc:
                    row.update(JSON_parse='FAIL',disposition='JSON_PARSE_REJECT',error=str(exc))
                if row['JSON_parse']=='PASS':
                    errors=list(validator.iter_errors(parsed))
                    row['exact_schema']='FAIL' if errors else 'PASS'
                    if errors:
                        row.update(disposition='EXACT_SCHEMA_REJECT',schema_errors=[{'path':list(e.absolute_path),'schema_path':list(e.absolute_schema_path),'message':e.message} for e in errors])
                    else:
                        try:
                            output=adapt_response(raw,value)
                            row.update(adapter='PASS',gate_output=asdict(output),disposition='COMBINED_STRUCTURAL_ACCEPT')
                        except ContractError as exc:
                            row.update(adapter='FAIL',disposition='ADAPTER_STRUCTURAL_REJECT',error=str(exc))
            rows.append(row)
            attempt['status']=row['disposition']
            results()
            checkpoint()
            print(json.dumps({k:row[k] for k in ('id','JSON_parse','exact_schema','adapter','disposition')}),flush=True)
            if row['disposition']!='COMBINED_STRUCTURAL_ACCEPT':
                s['status']='QWEN_STRUCTURAL_SMOKE_RECOVERY_STRUCTURAL_FAILED'
                break
        hook.remove()
        if len(rows)==3 and all(r['disposition']=='COMBINED_STRUCTURAL_ACCEPT' for r in rows):
            s['status']='QWEN_STRUCTURAL_SMOKE_RECOVERY_PASS'
    except BaseException:
        failure=traceback.format_exc()
        s['failure']=failure
        s['status']='QWEN_SMOKE_EAGER_RECOVERY_BLOCKED' if s['counters']['model_initialization']==0 else 'QWEN_STRUCTURAL_SMOKE_RECOVERY_RUNTIME_FAILED'
        if pre['status']!='PASS':
            pre.update(status='FAIL',error=failure)
            if pre['rows'] and pre['rows'][-1]['status']=='STARTED':
                pre['rows'][-1].update(status='FAIL',exception=failure)
            save('EAGER_MASK_PREFLIGHT.json',pre)
        if attempts and attempts[-1]['status']=='GENERATING':
            attempts[-1].update(status='RUNTIME_FAILED',error=failure)
    finally:
        attempted={a['id'] for a in attempts}
        for fixture in fixtures:
            if fixture['id'] not in attempted:
                attempts.append({'id':fixture['id'],'status':'NOT_RUN_AFTER_STOP'})
        after,check=inventory(),pip_check()
        s['post_environment']={'packages':after,'pip_check':check,'matches_pre':after==s['pre_environment']['packages']}
        s['environment_integrity_pass']=s['post_environment']['matches_pre'] and check['returncode']==0
        s['immutable_inputs_unchanged']=all(sha(ROOT/p)==h for p,h in s['immutable_inputs_sha256'].items())
        s['installed_execution_sources_unchanged']=all(sha(Path(p))==h for p,h in s['installed_execution_sources_sha256'].items())
        s['protocol_unchanged']=sha(ART/'RECOVERY_PROTOCOL.md')==s['protocol_sha256']
        s['cumulative_attempted_generate_calls']=1+s['counters']['generate']
        s['finished_utc']=now()
        s['counts']={'preflight_PASS':sum(r['status']=='PASS' for r in pre['rows']),
                    'completed_generations':len(raw_rows),'JSON_parse_PASS':sum(r['JSON_parse']=='PASS' for r in rows),
                    'exact_schema_PASS':sum(r['exact_schema']=='PASS' for r in rows),
                    'adapter_PASS':sum(r['adapter']=='PASS' for r in rows),
                    'combined_structural_accept':sum(r['disposition']=='COMBINED_STRUCTURAL_ACCEPT' for r in rows)}
        checkpoint()
        results()
        record=('# Qwen Structural Smoke Eager Runtime Recovery\n\nStatus: CANDIDATE_AWAITING_OWNER_REVIEW\nOutcome: '+s['status']
                +'\nBase: '+BASE+'\nTag: '+TAG+'\nRun type: RECOVERY_RUN_AFTER_NON_RESULT_BEARING_RUNTIME_FAILURE\n'
                +'Historical outcome remains QWEN_STRUCTURAL_SMOKE_RUNTIME_FAILED: attempted generate=1, observed forward=1, completed=0.\n'
                +'Recovery mode: '+MODE+'; torch.compiler.set_stance("force_eager") only.\n\nCounts:\n```json\n'+json.dumps(s['counts'],indent=2)
                +'\n```\nRecovery counters:\n```json\n'+json.dumps(s['counters'],indent=2)+'\n```\nCumulative attempted generate calls: '+str(s['cumulative_attempted_generate_calls'])
                +'\n\nSemantic correctness: NOT_EVALUATED. All reused fixtures remain EXCLUDED_FROM_SEMANTIC_QUALIFICATION. Fresh formal suite: NOT YET AUTHORED.\n'
                +'DEVELOPMENT access=0; retrieval=0; Phase 2H HELD_OUT=false; Phase 2G private HELDOUT=false.\n'
                +'Environment integrity: '+str(s['environment_integrity_pass'])+'; frozen historical/helper inputs unchanged: '+str(s['immutable_inputs_unchanged'])
                +'; installed execution source bytes unchanged: '+str(s['installed_execution_sources_unchanged'])+'.\n'
                +'Per-call raw bytes are recorded before structural processing; no repair, retry, configuration change or semantic scoring. Full model/snapshot/config/source identities and failure traceback (if any) are in RUNTIME_IDENTITY.json. No commit, tag, compiler installation or package mutation. Stop for owner review.\n')
        (ART/'FINAL_RECORD.md').write_bytes(record.encode())
        files=[p for p in ART.iterdir() if p.name!='FINAL_SHA256.json']+[Path(__file__)]
        save('FINAL_SHA256.json',{'algorithm':'SHA-256','files':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
                                'self_hash':'Excluded to avoid circularity; reported externally.'})
        print(json.dumps({'outcome':s['status'],'counts':s['counts'],'counters':s['counters'],
                          'cumulative_attempts':s['cumulative_attempted_generate_calls'],'failure':failure}),flush=True)
        if timed_out:
            os._exit(2)


if __name__=='__main__':
    os.environ.update(PYTHONDONTWRITEBYTECODE='1',PIP_NO_INDEX='1')
    if sys.argv[1:]==['prepare']:
        prepare()
    elif sys.argv[1:]==['execute']:
        execute()
    else:
        raise SystemExit('prepare once, execute once; no retries')
