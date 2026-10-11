"""Artificial structural fixtures and fake decoder only; no model/provider calls."""
import ast
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gateway.domain.evaluation.answerability import xgrammar_v2_decoder as d
from gateway.domain.evaluation.answerability import xgrammar_v2_smoke as s


def shape():
    return {'material_asks':[{'ask':'Opaque unit','support_status':'SUPPORTED','supporting_evidence_ranks':[1]}],
            'policy_context_status':'RESOLVED','decision':'ALLOW','reason_code':'SUPPORTED_BY_ACTIVE_POLICY'}


class DecoderTests(unittest.TestCase):
    def test_exact_wheel_receipt(self):
        self.assertEqual(d.read('WHEEL_CUSTODY.json')['sha256'],d.WHEEL_SHA)
        self.assertEqual(d.sha(Path(d.read('WHEEL_CUSTODY.json')['install_wheel_path']).read_bytes()),d.WHEEL_SHA)

    def test_exact_installed_version(self):
        self.assertEqual(d.inventory()['packages']['xgrammar']['version'],'0.2.8')

    def test_existing_runtime_unchanged(self):
        d.drift_check(d.read('PRE_INSTALL_PACKAGE_INVENTORY.json'),d.inventory())

    def test_version_drift_rejected(self):
        post=deepcopy(d.read('POST_INSTALL_PACKAGE_INVENTORY.json'));post['packages']['torch']['version']='wrong'
        with self.assertRaises(ValueError):d.drift_check(d.read('PRE_INSTALL_PACKAGE_INVENTORY.json'),post)

    def test_metadata_drift_rejected(self):
        post=deepcopy(d.read('POST_INSTALL_PACKAGE_INVENTORY.json'));post['packages']['torch']['metadata_sha256']='0'*64
        with self.assertRaises(ValueError):d.drift_check(d.read('PRE_INSTALL_PACKAGE_INVENTORY.json'),post)

    def test_additional_package_rejected(self):
        post=deepcopy(d.read('POST_INSTALL_PACKAGE_INVENTORY.json'));post['packages']['alternate']={}
        with self.assertRaises(ValueError):d.drift_check(d.read('PRE_INSTALL_PACKAGE_INVENTORY.json'),post)

    def test_wrong_decoder_rejected(self):
        post=deepcopy(d.read('POST_INSTALL_PACKAGE_INVENTORY.json'));post['packages']['xgrammar']['version']='0.2.9'
        with self.assertRaises(ValueError):d.drift_check(d.read('PRE_INSTALL_PACKAGE_INVENTORY.json'),post)

    def test_exact_schema_passed_without_rewrite(self):
        data=(d.PREREG/'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes();seen=[]
        class Compiler:
            def __init__(self,info):seen.append(info)
            def compile_json_schema(self,text):seen.append(text);return 'grammar'
        self.assertEqual(d.compile_exact(SimpleNamespace(GrammarCompiler=Compiler),'info',data),'grammar')
        self.assertEqual(seen,['info',data.decode()])

    def test_schema_drift_rejected_before_compile(self):
        with self.assertRaises(ValueError):d.compile_exact(None,None,b'{}')

    def test_compile_error_propagates_without_retry(self):
        calls=[]
        class Compiler:
            def __init__(self,info):pass
            def compile_json_schema(self,text):calls.append(text);raise RuntimeError('fake compiler error')
        with self.assertRaises(RuntimeError):d.compile_exact(SimpleNamespace(GrammarCompiler=Compiler),None,(d.PREREG/'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes())
        self.assertEqual(len(calls),1)

    def test_saved_api_availability(self):
        result=d.read('DECODER_API_RESULTS.json')
        self.assertTrue(result['passed']);self.assertTrue(all(result['required_apis'].values()))

    def test_missing_api_detected(self):
        fake=SimpleNamespace(TokenizerInfo=SimpleNamespace(),GrammarCompiler=type('Compiler',(),{}))
        self.assertFalse(all(d.api_present(fake,lambda:None).values()))

    def test_frozen_files_and_receipt(self):
        d.verify_v2()

    def test_suite_and_config_frozen(self):
        config,suite=s.frozen_plan();self.assertEqual(config['maximum_generate_calls'],3)
        self.assertEqual(len(suite['cases']),3)

    def test_config_tamper_rejected(self):
        original=d.read
        def fake(name):
            value=original(name)
            if name=='STRUCTURAL_SMOKE_CONFIG.json':value['max_new_tokens']=513
            return value
        with patch.object(d,'read',side_effect=fake),self.assertRaises(ValueError):s.frozen_plan()

    def test_suite_hash_tamper_rejected(self):
        original=Path.read_bytes
        def fake(path):
            data=original(path)
            return data+b' ' if path.name=='STRUCTURAL_SMOKE_SUITE.json' else data
        with patch.object(Path,'read_bytes',fake),self.assertRaises(ValueError):s.frozen_plan()

    def test_fourth_case_rejected(self):
        cases=d.read('STRUCTURAL_SMOKE_SUITE.json')['cases']
        with self.assertRaises(ValueError):s.validate_cases(cases+[dict(cases[0],case_id='S4')])

    def test_duplicate_case_rejected(self):
        cases=d.read('STRUCTURAL_SMOKE_SUITE.json')['cases'];cases[2]=cases[1]
        with self.assertRaises(ValueError):s.validate_cases(cases)

    def test_semantic_gold_forbidden(self):
        cases=d.read('STRUCTURAL_SMOKE_SUITE.json')['cases'];cases[0]['semantic_gold']='ALLOW'
        with self.assertRaises(ValueError):s.validate_cases(cases)

    def test_no_retry(self):
        with patch.object(Path,'read_text',return_value=json.dumps({'event':'STARTED'})),self.assertRaises(ValueError):d.no_repeat('STARTED')
        self.assertEqual(s.CONFIG['quality_retry'],0);self.assertEqual(s.CONFIG['infrastructure_retry'],0)

    def test_timeout_frozen(self):
        self.assertEqual(s.CONFIG['per_call_timeout_seconds'],600)
        tree=ast.parse(Path(s.__file__).read_text())
        joins=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='join']
        self.assertEqual(len(joins),1)

    def test_no_alternate_decoder_or_retrieval_import(self):
        for module in (d,s):
            tree=ast.parse(Path(module.__file__).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import): names=[x.name for x in node.names]
                elif isinstance(node,ast.ImportFrom):names=[node.module or '']
                else:continue
                self.assertFalse(any(any(t in name for t in ('retriever','evaluate_','outlines','guidance','lmformatenforcer','sentence_transformers')) for name in names))

    def test_one_model_load_and_generate_site(self):
        text=Path(s.__file__).read_text()
        self.assertEqual(text.count('AutoModelForCausalLM.from_pretrained('),1)
        self.assertEqual(text.count('model.generate('),1)
        self.assertIn('for case in suite[\'cases\']:',text)
        self.assertIn('logits_processor=[LogitsProcessor(grammar)]',text)

    def test_no_question_payloads_in_suite(self):
        raw=(d.OUT/'STRUCTURAL_SMOKE_SUITE.json').read_text()
        for token in ('AQ001','RQ001','Gold support','delivery policy','expected_gate'):
            self.assertNotIn(token,raw)

    def test_raw_serialization_roundtrip(self):
        raw=' {"a": "\u03b1"}\n'
        serialized=d.canonical({'raw_output_text':raw})
        self.assertEqual(json.loads(serialized)['raw_output_text'].encode(),raw.encode())


class ValidationTests(unittest.TestCase):
    def accepts(self,value):
        schema=json.loads((d.PREREG/'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes())
        s.schema_keyword_guard(schema)
        return s.validate_schema(schema,value)

    def test_structural_object_valid(self):self.assertTrue(self.accepts(shape()))

    def test_unknown_keyword_rejected(self):
        with self.assertRaises(ValueError):s.schema_keyword_guard({'unevaluatedProperties':False})

    def test_missing_required(self):
        value=shape();del value['decision'];self.assertFalse(self.accepts(value))

    def test_additional_key(self):
        value=shape();value['confidence']=1;self.assertFalse(self.accepts(value))

    def test_boolean_rank(self):
        value=shape();value['material_asks'][0]['supporting_evidence_ranks']=[True];self.assertFalse(self.accepts(value))

    def test_rank_bound(self):
        for rank in (0,11):
            value=shape();value['material_asks'][0]['supporting_evidence_ranks']=[rank];self.assertFalse(self.accepts(value))

    def test_unique_ranks_numeric_equality(self):
        value=shape();value['material_asks'][0]['supporting_evidence_ranks']=[1,1.0];self.assertFalse(self.accepts(value))

    def test_conditional_empty_rank(self):
        value=shape();value['material_asks'][0]['supporting_evidence_ranks']=[];self.assertFalse(self.accepts(value))

    def test_conditional_nonempty_rank(self):
        value=shape();value['material_asks'][0]['support_status']='UNSUPPORTED';self.assertFalse(self.accepts(value))

    def test_empty_branch_valid(self):
        value=shape();value['material_asks'][0].update(support_status='UNSUPPORTED',supporting_evidence_ranks=[])
        value.update(decision='ABSTAIN',reason_code='INSUFFICIENT_POLICY_SUPPORT');self.assertTrue(self.accepts(value))

    def test_contains_required(self):
        value=shape();value.update(decision='ABSTAIN',reason_code='INSUFFICIENT_POLICY_SUPPORT');self.assertFalse(self.accepts(value))

    def test_unresolved_anyof(self):
        value=shape();value.update(decision='ABSTAIN',reason_code='UNRESOLVED_POLICY_CONTEXT')
        self.assertFalse(self.accepts(value));value['policy_context_status']='UNRESOLVED';self.assertTrue(self.accepts(value))

    def test_ask_pattern(self):
        value=shape();value['material_asks'][0]['ask']='   ';self.assertFalse(self.accepts(value))

    def test_maximum_asks(self):
        value=shape();value['material_asks']*=9;self.assertFalse(self.accepts(value))

    def test_oneof_exactly_one(self):
        self.assertFalse(s.validate_schema({'oneOf':[{},{}]},{}))

    def test_no_fence_prefix_suffix_repair(self):
        valid=json.dumps(shape())
        for raw in ('```json\n'+valid+'\n```','prefix '+valid,valid+' suffix',valid+valid):
            result=s.assess(raw,'EOS');self.assertFalse(result['A_json_valid']);self.assertFalse(result['structural_acceptance'])

    def test_duplicate_key_and_nonfinite_rejected(self):
        for raw in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):s.strict_json(raw)

    def test_adapter_separate_from_schema(self):
        value=shape();value['material_asks'][0]['supporting_evidence_ranks']=[2,1]
        result=s.assess(json.dumps(value),'EOS')
        self.assertTrue(result['B_exact_schema_valid']);self.assertFalse(result['C_adapter_valid'])
        self.assertTrue(result['structural_acceptance'])

    def test_timeout_not_structural_success(self):
        result=s.assess(json.dumps(shape()),'TIMEOUT')
        self.assertTrue(result['A_json_valid']);self.assertTrue(result['B_exact_schema_valid'])
        self.assertFalse(result['structural_acceptance'])


if __name__=='__main__':unittest.main()
