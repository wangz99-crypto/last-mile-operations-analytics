"""Pure installation-plan checks. No package install, decoder or model invocation."""
import ast
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'evaluation/answerability/enable_lmfe.py'
spec = importlib.util.spec_from_file_location('lmfe_enablement_under_test', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EnablementTests(unittest.TestCase):
    def lock(self):
        return {'packages': [{'name': n, 'version': v[0], 'filename': v[1], 'sha256': v[2]} for n, v in m.PINS.items()]}

    def test_only_authorized_versions_and_order(self):
        self.assertEqual([(n, v[0]) for n, v in m.PINS.items()], [('interegular','0.3.3'),('lm-format-enforcer','0.11.3')])

    def test_wrong_wheel_bytes_rejected(self):
        for name, pin in m.PINS.items():
            with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
                m.wheel_check(name, pin[1], b'corrupted')

    def test_wrong_filename_and_alternate_distribution_rejected(self):
        with self.assertRaises(ValueError): m.wheel_check('other', 'other.whl', b'')
        with self.assertRaises(ValueError): m.wheel_check('interegular', 'interegular-0.3.2.whl', b'')

    def test_exact_hash_allows_verification(self):
        for name,pin in m.PINS.items():
            with patch.object(m, 'sha', return_value=pin[2]):
                m.wheel_check(name,pin[1],b'synthetic hash oracle; no real wheel')

    def test_lock_must_freeze_once_before_install(self):
        row={'event':'DEPENDENCY_PLAN_FROZEN','details':{'sha256':'expected'}}
        m.validate_lock(self.lock(),[row],'expected')
        for rows in ([],[row,row],[row,{'event':'INSTALL_BEGIN'}]):
            with self.assertRaises(ValueError): m.validate_lock(self.lock(),rows,'expected')

    def test_lock_mutation_or_alternate_version_rejected(self):
        row={'event':'DEPENDENCY_PLAN_FROZEN','details':{'sha256':'expected'}}
        with self.assertRaises(ValueError):m.validate_lock(self.lock(),[row],'changed')
        lock=self.lock();lock['packages'][0]['version']='0.3.2'
        with self.assertRaises(ValueError):m.validate_lock(lock,[row],'expected')

    def test_install_is_local_no_deps_no_index(self):
        command=m.install_command(Path('C:/wheelhouse/exact.whl'))
        for flag in ('--no-deps','--no-index','--no-cache-dir','--disable-pip-version-check'):
            self.assertIn(flag,command)
        self.assertEqual(command[-1],str(Path('C:/wheelhouse/exact.whl')))
        self.assertNotIn('--upgrade',command)

    def test_exact_dependency_graph_and_unexpected_dependency_rejection(self):
        receipts={'lm-format-enforcer':{'requires_dist':['pydantic>=1.10.8','interegular>=0.3.2','packaging','pyyaml']},'interegular':{'requires_dist':[]}}
        packages={n:{'version':v} for n,v in [('pydantic','2.13.5'),('packaging','26.3'),('pyyaml','6.0.3')]}
        graph=m.dependency_graph(receipts,packages)
        self.assertEqual(graph['lm-format-enforcer'][1]['resolved_version'],'0.3.3')
        for name in receipts:
            bad=copy.deepcopy(receipts);bad[name]['requires_dist'].append('unexpected-package>=1')
            with self.assertRaises(ValueError):m.dependency_graph(bad,packages)

    def test_missing_existing_dependency_blocks(self):
        receipts={'lm-format-enforcer':{'requires_dist':['pydantic>=1.10.8','interegular>=0.3.2','packaging','pyyaml']},'interegular':{'requires_dist':[]}}
        with self.assertRaises(ValueError):m.dependency_graph(receipts,{})

    def test_wheel_metadata_order_and_parentheses_are_semantically_equivalent(self):
        receipts={'lm-format-enforcer':{'requires_dist':['interegular (>=0.3.2)','packaging','pydantic (>=1.10.8)','pyyaml']},'interegular':{'requires_dist':[]}}
        packages={n:{'version':v} for n,v in [('pydantic','2.13.5'),('packaging','26.3'),('pyyaml','6.0.3')]}
        graph=m.dependency_graph(receipts,packages)
        self.assertEqual(graph['lm-format-enforcer'][0]['resolved_version'],'0.3.3')
        bad=copy.deepcopy(receipts);bad['lm-format-enforcer']['requires_dist'][0]='interegular>=0.4'
        with self.assertRaises(ValueError):m.dependency_graph(bad,packages)

    def test_only_two_additions_and_no_existing_drift(self):
        before={'xgrammar':{'version':'0.2.8','metadata_sha256':'M','record_sha256':'R'}}
        after=copy.deepcopy(before);after.update({n:{'version':v[0]} for n,v in m.PINS.items()})
        self.assertEqual(len(m.package_diff(before,after)['additions']),2)
        for key,value in [('version','0.2.9'),('metadata_sha256','changed'),('record_sha256','changed')]:
            bad=copy.deepcopy(after);bad['xgrammar'][key]=value
            with self.assertRaises(ValueError):m.package_diff(before,bad)
        bad=copy.deepcopy(after);bad['extra']={'version':'1'}
        with self.assertRaises(ValueError):m.package_diff(before,bad)
        bad=copy.deepcopy(after);del bad['xgrammar']
        with self.assertRaises(ValueError):m.package_diff(before,bad)

    def api(self):
        return {'results':{'status':'PASS','interegular':{'import':'PASS'},'lmformatenforcer':{'import':'PASS'},'lmformatenforcer.JsonSchemaParser':True,'lmformatenforcer.integrations.transformers.build_transformers_prefix_allowed_tokens_fn':True},'observations':{'blocked_events':[],'prohibited_content_opens':[]}}

    def test_all_imports_and_apis_required(self):
        m.api_valid(self.api())
        for name in self.api()['results']:
            bad=self.api();del bad['results'][name]
            with self.assertRaises(ValueError):m.api_valid(bad)

    def test_prohibited_execution_or_content_blocks_acceptance(self):
        for field in ('blocked_events','prohibited_content_opens'):
            bad=self.api();bad['observations'][field]=['synthetic violation']
            with self.assertRaises(ValueError):m.api_valid(bad)

    def test_import_child_has_no_scientific_call_expression(self):
        tree=ast.parse(m.IMPORT_CHILD)
        forbidden={'JsonSchemaParser','build_transformers_prefix_allowed_tokens_fn','from_pretrained','generate','forward'}
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                self.assertNotIn(name,forbidden)
        for boundary in ('heldout','held_out','/hf-cache/','/development/'):
            self.assertIn(boundary,m.IMPORT_CHILD)
        self.assertIn('Scientific execution forbidden',m.IMPORT_CHILD)

    def test_source_import_has_not_imported_decoder_or_model(self):
        import sys
        self.assertFalse({'lmformatenforcer','interegular','transformers','torch'}.intersection(sys.modules))


if __name__ == '__main__':
    unittest.main()
