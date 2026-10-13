"""GD offline diagnostic safeguards; native parser is never imported here."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

SOURCE=Path(__file__).resolve().parents[1]/'evaluation/answerability/localize_lmfe_schema.py'
spec=importlib.util.spec_from_file_location('gd_offline',SOURCE)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


class LocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads(d.g.SCHEMA.read_bytes())
        cls.plan=d.read('LOCALIZATION_PROBE_PLAN.json')
        cls.digest=d.g.sha(d.g.encoded(cls.plan))

    def test_exact_frozen_schema(self):
        self.assertEqual(d.g.sha(d.g.SCHEMA.read_bytes()),'6fd9429c6238525dadf259d8a3b2b877b0da2b9bc1c2e8f44c42bbe1d07dfc1e')

    def test_inventory_deterministic_and_complete(self):
        original=copy.deepcopy(self.schema)
        first=d.inventory_nodes(self.schema)
        self.assertEqual(first,d.inventory_nodes(self.schema))
        self.assertEqual(first,d.read('SCHEMA_NODE_INVENTORY.json'))
        self.assertEqual(self.schema,original)
        pointers=[r['pointer'] for r in first['nodes']]
        self.assertEqual(len(pointers),len(set(pointers)))
        for row in first['nodes']:
            self.assertEqual(d.g.sha(d.g.encoded(d.pointer_get(self.schema,row['pointer']))),row['node_sha256'])

    def test_json_pointer_stability_and_escaping(self):
        self.assertIs(d.pointer_get(self.schema,''),self.schema)
        self.assertEqual(d.pointer_get({'a/b':{'~k':[17]}},'/a~1b/~0k/0'),17)
        with self.assertRaises(ValueError):d.pointer_get(self.schema,'not-a-pointer')

    def test_absent_categories_not_invented(self):
        counts=d.inventory_nodes(self.schema)['category_counts']
        for category in ('$ref-only','$ref plus siblings','empty schema {}','type as array / union','additionalProperties schema object','oneOf-only','anyOf-only','allOf-only'):
            self.assertEqual(counts[category],0,category)

    def test_plan_immutability(self):
        d.verify_plan(self.plan,self.digest,self.schema)
        changed=copy.deepcopy(self.plan);changed['probes'][0]['prefix']='different'
        with self.assertRaisesRegex(ValueError,'plan drift'):d.verify_plan(changed,self.digest,self.schema)

    def test_no_adaptive_additions_or_reordering(self):
        for changed in (copy.deepcopy(self.plan),copy.deepcopy(self.plan)):
            changed['probes'].reverse()
            with self.assertRaises(ValueError):d.verify_plan(changed,d.g.sha(d.g.encoded(changed)),self.schema)
        changed=copy.deepcopy(self.plan);changed['probes'].append(changed['probes'][0]);changed['probe_count']+=1
        with self.assertRaises(ValueError):d.verify_plan(changed,d.g.sha(d.g.encoded(changed)),self.schema)

    def test_exact_subtrees_unchanged(self):
        before=d.g.encoded(self.schema)
        for row in self.plan['probes']:
            if row['kind']=='EXACT_SCHEMA_SUBTREE':self.assertEqual(row['schema'],d.pointer_get(self.schema,row['source_pointer']))
        self.assertEqual(before,d.g.encoded(self.schema))

    def test_no_qualification_rerun_or_root_schema(self):
        self.assertEqual(self.plan['root_V2_parser_calls'],0)
        self.assertEqual(self.plan['probe_count'],26)
        for row in self.plan['probes']:
            self.assertTrue(row['probe_id'].startswith(('D','T')))
            self.assertNotEqual(row['schema'],self.schema)
            self.assertLess(len(row['prefix']),10)

    def test_constructor_error_is_diagnostic_and_not_retried(self):
        factory=Mock(side_effect=Exception('Unsupported type None'))
        row=self.plan['probes'][0]
        result=d.probe(row,factory,d.read('PARSER_CONFIGURATION.json'),[])
        self.assertEqual(factory.call_count,1)
        self.assertEqual(result['constructor'],'ERROR')
        self.assertTrue(result['same_target_exception'])
        self.assertEqual(result['qualification_verdict'],'NOT_A_QUALIFICATION_CASE')
        self.assertEqual(result['traversal'],'NOT_STARTED')

    def test_frozen_package_and_source_integrity(self):
        self.assertEqual(d.installed_sources(),d.read('INSTALLED_SOURCE_RECEIPT.json'))
        inventory=d.read('PRE_LOCALIZATION_PACKAGE_INVENTORY.json')
        self.assertEqual(len(inventory['packages']),36)
        self.assertEqual(inventory['packages']['lm-format-enforcer']['version'],'0.11.3')
        self.assertEqual(d.g.sha(d.g.encoded(inventory)),d.g.INVENTORY_SHA)

    def test_no_model_tokenizer_or_benchmark_execution(self):
        self.assertNotIn('lmformatenforcer',d.sys.modules)
        tree=d.ast.parse(SOURCE.read_bytes())
        calls=[d.ast.unparse(n.func) for n in d.ast.walk(tree) if isinstance(n,d.ast.Call)]
        forbidden=['from_pretrained','generate','forward','build_transformers_prefix_allowed_tokens_fn','TokenizerPrefixTree','g.execute','g.prepare','g.core_fixtures','g.run_extended','g.extended_fixtures','retrieve']
        for name in forbidden:self.assertFalse(any(c==name or c.endswith('.'+name) for c in calls),name)
        imports=[n.module for n in d.ast.walk(tree) if isinstance(n,d.ast.ImportFrom)]
        self.assertNotIn('transformers',imports)

    def test_helper_path_verified_without_execution(self):
        receipt=d.read('HELPER_PATH_RECEIPT.json')
        self.assertIn('JsonSchemaParser(json.loads(SCHEMA.read_bytes()), config=None)',receipt['factory_source'])
        self.assertEqual(receipt['helper_sha256'],'45cc57a9534a56fef5834fffd422e618e2bb0574adaed90ac019ab4072d66bc0')
        self.assertTrue(all(r['character_at_error']==':' and r['prefix_before_error'].endswith('"material_asks"') for r in receipt['historical_exception_context']))


if __name__=='__main__':unittest.main(verbosity=2)
