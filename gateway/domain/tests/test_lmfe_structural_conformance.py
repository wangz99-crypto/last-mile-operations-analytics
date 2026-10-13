"""Offline qualification-harness tests: no native LMFE import or execution."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

SOURCE=Path(__file__).resolve().parents[1]/'evaluation/answerability/qualify_lmfe_structure.py'
spec=importlib.util.spec_from_file_location('lmfe_structure_offline',SOURCE)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


class FakeParser:
    def __init__(self,text,index=0,complete=True):
        self.text=text;self.index=index;self.complete=complete
    def get_allowed_characters(self):
        return self.text[self.index:self.index+1]
    def add_character(self,ch):
        if ch not in self.get_allowed_characters():raise AssertionError('invalid transition')
        return FakeParser(self.text,self.index+1,self.complete)
    def can_end(self):return self.index==len(self.text) and self.complete


class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema,cls.validator=g.schema_oracle()
        cls.core=g.read('CORE_CONFORMANCE_FIXTURES.json')['fixtures']
        cls.extended=g.read('EXTENDED_CONFORMANCE_PLAN.json')['fixtures']

    def test_exact_schema_and_oracle_identity(self):
        self.assertEqual(g.sha(g.SCHEMA.read_bytes()),g.SCHEMA_SHA)
        with patch.object(g,'SCHEMA_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'Schema SHA'):g.schema_oracle()
        with patch.object(g,'ORACLE_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'validator changed'):g.schema_oracle()

    def test_exact_version_and_inventory_drift(self):
        inventory=g.read('PRE_VALIDATION_PACKAGE_INVENTORY.json')
        g.intact(inventory,copy.deepcopy(inventory))
        for key in ('version','metadata_sha256','record_sha256'):
            altered=copy.deepcopy(inventory);altered['packages']['lm-format-enforcer'][key]='different'
            with self.assertRaises(ValueError):g.intact(inventory,altered)
        wrong=copy.deepcopy(inventory);wrong['packages']['lm-format-enforcer']['version']='0.11.4'
        with self.assertRaisesRegex(ValueError,'Wrong LMFE'):g.intact(wrong,wrong)
        removed=copy.deepcopy(inventory);removed['packages'].pop('interegular')
        with self.assertRaises(ValueError):g.intact(inventory,removed)

    def test_core_exact_outcomes_historical_bytes(self):
        self.assertEqual(self.core,g.core_fixtures())
        self.assertEqual([x['expected'] for x in self.core],['ACCEPT']+['REJECT']*7)
        self.assertEqual([x['fixture_id'] for x in self.core],['M'+str(i) for i in range(1,9)])
        g.check_fixtures(self.core,self.schema,type(self).validator)

    def test_fixture_immutability_and_expectation_guard(self):
        changed=copy.deepcopy(self.core);changed[0]['text']+=' '
        with self.assertRaisesRegex(ValueError,'Fixture text changed'):g.check_fixtures(changed,self.schema,type(self).validator)
        changed=copy.deepcopy(self.core);changed[0]['expected']='REJECT'
        with self.assertRaisesRegex(ValueError,'expectation mismatch'):g.check_fixtures(changed,self.schema,type(self).validator)

    def test_freeze_events_precede_any_execution(self):
        events=g.journal();names=[e['event'] for e in events]
        self.assertLess(names.index('SCHEMA_KEYWORD_INVENTORY_COMPLETE'),names.index('CORE_CONFORMANCE_FIXTURES_FROZEN'))
        for name,file in [('PARSER_CONFIGURATION_FROZEN','PARSER_CONFIGURATION.json'),('CORE_CONFORMANCE_FIXTURES_FROZEN','CORE_CONFORMANCE_FIXTURES.json'),('EXTENDED_CONFORMANCE_PLAN_FROZEN','EXTENDED_CONFORMANCE_PLAN.json')]:
            event=next(e for e in events if e['event']==name)
            self.assertEqual(event['details']['sha256'],g.sha((g.OUT/file).read_bytes()))
        if 'CORE_EXECUTION_BEGIN' in names:
            self.assertLess(names.index('EXTENDED_CONFORMANCE_PLAN_FROZEN'),names.index('CORE_EXECUTION_BEGIN'))

    def test_default_config_no_env_override(self):
        self.assertEqual(g.config_from_source(),g.read('PARSER_CONFIGURATION.json'))
        for name in g.ENV_NAMES:
            with patch.dict(g.os.environ,{name:'override'}):
                with self.assertRaisesRegex(ValueError,'Non-default'):g.config_from_source()

    def test_fresh_parser_per_fixture_no_retry(self):
        factory=Mock(side_effect=lambda:FakeParser('x'))
        rows=[g.fixture('M'+str(i),'x','ACCEPT',[]) for i in range(1,9)]
        results=[g.traverse(factory,row) for row in rows]
        self.assertEqual(factory.call_count,8)
        self.assertTrue(g.core_pass(results))

    def test_exact_consumption_and_completion(self):
        row=g.fixture('fake','xy','ACCEPT',[])
        result=g.traverse(lambda:FakeParser('xy'),row)
        self.assertEqual(result['actual'],'ACCEPT');self.assertTrue(result['all_characters_consumed'])
        result=g.traverse(lambda:FakeParser('xy',complete=False),row)
        self.assertEqual(result['actual'],'REJECT');self.assertFalse(result['completion_can_end'])
        result=g.traverse(lambda:FakeParser('x'),row)
        self.assertEqual(result['actual'],'REJECT');self.assertEqual(result['first_rejected_character_position'],1)
        self.assertFalse(result['all_characters_consumed'])

    def test_exceptions_not_scientific_rejections_or_retried(self):
        factory=Mock(side_effect=RuntimeError('synthetic constructor failure'))
        result=g.traverse(factory,g.fixture('fake','x','REJECT',[]))
        self.assertEqual(result['actual'],'ERROR');self.assertFalse(result['matches_expected'])
        self.assertEqual(result['exception']['phase'],'constructor');self.assertEqual(factory.call_count,1)
        parser=Mock();parser.get_allowed_characters.side_effect=RuntimeError('synthetic traversal failure')
        result=g.traverse(lambda:parser,g.fixture('fake','x','REJECT',[]))
        self.assertEqual(result['exception']['phase'],'traversal');self.assertEqual(result['actual'],'ERROR')

    def test_hard_core_gate_blocks_all_extended_calls(self):
        passing=[{'fixture_id':'M'+str(i),'matches_expected':True} for i in range(1,9)]
        for core in ([],passing[:-1],[{**r,'matches_expected':False} if i==3 else r for i,r in enumerate(passing)]):
            factory=Mock(side_effect=AssertionError('Must not construct'));record=Mock()
            self.assertEqual(g.run_extended(core,self.extended,factory,record),[])
            factory.assert_not_called();record.assert_not_called()

    def test_extended_stops_at_first_critical_mismatch(self):
        passing=[{'fixture_id':'M'+str(i),'matches_expected':True} for i in range(1,9)]
        rows=[g.fixture('E1','x','REJECT',[]),g.fixture('E2','x','ACCEPT',[])]
        factory=Mock(side_effect=lambda:FakeParser('x'));record=Mock()
        results=g.run_extended(passing,rows,factory,record)
        self.assertEqual(len(results),1);self.assertEqual(factory.call_count,1)
        self.assertFalse(results[0]['matches_expected']);self.assertEqual(record.call_count,1)

    def test_independent_json_schema_parser_triangulation(self):
        row=self.core[1]
        tri=g.triangulate(self.schema,type(self).validator,row)
        result=g.traverse(lambda:FakeParser(row['text']),row)
        self.assertTrue(tri['JSON_valid']);self.assertFalse(tri['frozen_schema_valid'])
        self.assertEqual(result['actual'],'ACCEPT');self.assertFalse(result['matches_expected'])
        self.assertFalse(g.triangulate(self.schema,type(self).validator,{'text':'{'})['JSON_valid'])

    def test_keyword_inventory_and_criticality(self):
        inventory=g.keyword_inventory(self.schema)
        self.assertEqual(inventory,g.read('V2_SCHEMA_KEYWORD_INVENTORY.json')['keywords'])
        self.assertEqual(inventory['required']['criticality'],'CRITICAL')
        for key in ('exclusiveMinimum','exclusiveMaximum','maxLength'):self.assertFalse(inventory[key]['present'])
        self.assertEqual(inventory['$schema']['criticality'],'ANNOTATION')
        self.assertTrue(g.read('CRITICALITY_ASSESSMENT.json')['no_responsibility_transfer'])

    def test_extended_frozen_coverage_and_authoritative_validity(self):
        self.assertEqual(self.extended,g.extended_fixtures(json.loads(self.core[0]['text'])))
        g.check_fixtures(self.extended,self.schema,type(self).validator)
        for key,entry in g.keyword_inventory(self.schema).items():
            if entry['criticality']!='CRITICAL':continue
            relevant=[r for r in self.extended if key in r['features']]
            self.assertIn('ACCEPT',[r['expected'] for r in relevant],key)
            self.assertIn('REJECT',[r['expected'] for r in relevant],key)

    def test_no_native_parser_tokenizer_model_or_benchmark_in_offline_tests(self):
        self.assertNotIn('lmformatenforcer',g.sys.modules)
        tree=ast.parse(SOURCE.read_bytes())
        calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id if isinstance(n.func,ast.Name) else '' for n in ast.walk(tree) if isinstance(n,ast.Call)]
        for name in ('from_pretrained','generate','forward','build_transformers_prefix_allowed_tokens_fn','TokenizerPrefixTree','retrieve'):
            self.assertNotIn(name,calls)
        imported=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertNotIn('transformers',imported)
        strings=[n.value.replace(chr(92),'/') for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
        self.assertFalse(any(s.startswith(('artifacts/retrieval_heldout','gateway/domain/evaluation/answerability/development')) for s in strings))


if __name__=='__main__':unittest.main(verbosity=2)
