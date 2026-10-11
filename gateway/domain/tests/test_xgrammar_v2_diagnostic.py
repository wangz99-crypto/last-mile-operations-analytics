"""No native matcher/model calls: deterministic fixtures, custody and fake matcher tests."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest

from gateway.domain.evaluation.answerability import diagnose_xgrammar_v2 as d


class FakeMatcher:
    def __init__(self, reject=None):
        self.calls=[];self.reject=reject;self.ended=False
    def accept_token(self,token):
        self.calls.append(token)
        if token==self.reject:return False
        if token==99:self.ended=True
        return True
    def is_completed(self):return bool(self.calls) and self.reject not in self.calls
    def is_terminated(self):return self.ended


class DiagnosticTests(unittest.TestCase):
    def plan(self):return d.read('MATCHER_DIAGNOSTIC_FIXTURES.json')

    def test_schema_hash_enforced(self):
        with self.assertRaises(ValueError):d.checked_schema(b'{}')
        self.assertEqual(d.checked_schema(d.SCHEMA.read_bytes())['type'],'object')

    def test_exact_required_fields(self):
        self.assertEqual(set(d.checked_schema(d.SCHEMA.read_bytes())['required']),
                         {'decision','material_asks','policy_context_status','reason_code'})

    def test_eight_fixture_order(self):
        self.assertEqual(tuple(x['fixture_id'] for x in self.plan()['fixtures']),d.IDS)

    def test_required_field_removal_only(self):
        rows=self.plan()['fixtures'];base=json.loads(rows[0]['text'])
        for row in rows[1:5]:
            self.assertEqual(json.loads(row['text']),{k:v for k,v in base.items() if k not in row['removed_keys']})

    def test_expected_schema_conformance(self):
        schema=d.checked_schema(d.SCHEMA.read_bytes())
        for row in self.plan()['fixtures']:
            self.assertEqual(d.validate_schema(schema,d.strict_json(row['text'])),row['expected']=='ACCEPT')

    def test_raw_output_custody(self):
        raw=[json.loads(x) for x in (d.A2/'RAW_STRUCTURAL_OUTPUTS.jsonl').read_text().splitlines()]
        for fixture,row in zip(self.plan()['fixtures'][5:],raw):
            self.assertEqual(fixture['text'].encode(),row['raw_output_text'].encode())
            self.assertEqual(fixture['saved_generated_token_ids'],row['generated_token_ids'])
            self.assertEqual(d.sha(fixture['text'].encode()),row['raw_output_sha256'])

    def test_fixture_builder_deterministic_and_no_mutation(self):
        schema=d.checked_schema(d.SCHEMA.read_bytes())
        raw=[json.loads(x) for x in (d.A2/'RAW_STRUCTURAL_OUTPUTS.jsonl').read_text().splitlines()]
        before=deepcopy((schema,raw))
        self.assertEqual(d.fixtures(schema,raw),d.fixtures(schema,raw))
        self.assertEqual((schema,raw),before)

    def test_raw_custody_tamper_rejected(self):
        raw=[json.loads(x) for x in (d.A2/'RAW_STRUCTURAL_OUTPUTS.jsonl').read_text().splitlines()]
        raw[0]['raw_output_text']+=' '
        with self.assertRaises(ValueError):d.fixtures(d.checked_schema(d.SCHEMA.read_bytes()),raw)

    def test_matcher_accepts_once_in_order(self):
        matcher=FakeMatcher();result=d.match_once(matcher,[1,2],99)
        self.assertEqual(matcher.calls,[1,2,99]);self.assertEqual(result['actual'],'ACCEPT')
        self.assertFalse(result['terminated_before_eos']);self.assertTrue(result['terminated_after_eos'])

    def test_matcher_rejection_no_retry_no_eos(self):
        matcher=FakeMatcher(reject=2);result=d.match_once(matcher,[1,2,3],99)
        self.assertEqual(matcher.calls,[1,2]);self.assertEqual(result['actual'],'REJECT')
        self.assertEqual(result['first_rejection_token_index_zero_based'],1)
        self.assertIsNone(result['stop_token_accepted'])

    def test_matcher_deterministic_fake_execution(self):
        self.assertEqual(d.match_once(FakeMatcher(),[1,2],99),d.match_once(FakeMatcher(),[1,2],99))

    def test_reexecution_guard(self):
        data=(d.OUT/'MATCHER_DIAGNOSTIC_FIXTURES.json').read_bytes()
        with self.assertRaises(ValueError):d.validate_plan(data,d.sha(data),[{'event':'MATCHER_DIAGNOSTIC_STARTED'}])

    def test_fixture_hash_guard(self):
        data=(d.OUT/'MATCHER_DIAGNOSTIC_FIXTURES.json').read_bytes()
        with self.assertRaises(ValueError):d.validate_plan(data+b' ',d.sha(data),[])

    def test_any_order_actual_source_default(self):
        defaults,_=d.signature_defaults(d.SITE/'xgrammar/compiler.py','GrammarCompiler','compile_json_schema')
        self.assertIs(defaults['any_order'],False)
        self.assertEqual(defaults,d.read('ATTEMPT2_COMPILATION_PARAMETERS.json')['effective_options'])

    def test_no_model_initialization_generation_or_forward_calls(self):
        tree=ast.parse(Path(d.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                self.assertNotIn(node.func.attr,('generate','forward'))
                if node.func.attr=='from_pretrained':self.assertEqual(ast.unparse(node.func.value),'AutoTokenizer')
        self.assertNotIn('AutoModel',Path(d.__file__).read_text())

    def test_only_diagnostic_writes(self):
        tree=ast.parse(Path(d.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
                self.assertNotIn(node.func.attr,('write_bytes','write_text','unlink','rename','reset'))
                if node.func.attr=='replace':
                    # The audit/profile guards normalize string paths; this is not Path.replace.
                    self.assertIn(ast.unparse(node.func.value),('os.fsdecode(args[0])','frame.f_code.co_filename'))
                if node.func.attr=='open' and node.args and isinstance(node.args[0],ast.Constant) and any(c in str(node.args[0].value) for c in ('w','a','x')):
                    self.assertIn('OUT',ast.unparse(node.func.value))

    def test_historical_integrity_and_schema_unchanged(self):
        self.assertEqual(d.integrity(),d.read('ATTEMPT2_INTEGRITY_RECEIPT.json')['files'])


if __name__=='__main__':unittest.main()
