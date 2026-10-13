"""FR fake-result and plan checks; never launches imports or model execution."""
import ast
import copy
import importlib.util
from pathlib import Path
import unittest

SOURCE=Path(__file__).resolve().parents[1]/'evaluation/answerability/recover_lmfe_imports.py'
spec=importlib.util.spec_from_file_location('recovery_under_test',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class RecoveryTests(unittest.TestCase):
    def payload(self):
        return {'results':{'interegular':{'module_path':str(m.PYTHON.parent.parent/'Lib/site-packages/interegular/__init__.py'),'distribution':'interegular','version':'0.3.3'}},'observations':{'scientific_calls':[],'prohibited_content_opens':[],'subprocess_events':[],'socket_events':[]}}

    def test_exact_python_sequence_budget(self):
        p=m.plan()
        self.assertEqual(Path(p['python']),m.PYTHON)
        self.assertEqual([r['id'] for r in p['validations']],['I1','I2','A1','A2','C1'])
        self.assertEqual(p['max_validation_processes'],5)
        self.assertEqual(p['retry_policy'],'FORBIDDEN')

    def test_budget_stage_order_and_no_retry(self):
        p=m.plan();completed=[];started=[]
        for ident in ['I1','I2','A1','A2','C1']:
            self.assertEqual(m.permitted_next(p,completed,started),ident)
            started.append(ident)
            with self.assertRaises(ValueError):m.permitted_next(p,completed,started)
            completed.append({'id':ident,'pass':True})
        with self.assertRaises(ValueError):m.permitted_next(p,completed,started)
        with self.assertRaises(ValueError):m.permitted_next(p,[{'id':'I1','pass':False}],['I1'])

    def test_inventory_drift_rejected(self):
        packages={str(i):{'version':'1','metadata_sha256':'a','record_sha256':'b'} for i in range(34)}
        packages.update({'interegular':{'version':'0.3.3'},'lm-format-enforcer':{'version':'0.11.3'}})
        before={'packages':packages};m.intact(before,copy.deepcopy(before))
        for field in ['version','metadata_sha256','record_sha256']:
            after=copy.deepcopy(before);after['packages']['0'][field]='changed'
            with self.assertRaises(ValueError):m.intact(before,after)
        after=copy.deepcopy(before);del after['packages']['0']
        with self.assertRaises(ValueError):m.intact(before,after)

    def test_identity_exit_and_environment_paths(self):
        m.assess('I1',self.payload(),0)
        with self.assertRaises(ValueError):m.assess('I1',self.payload(),1)
        for key,value in [('version','0.3.2'),('distribution','other'),('module_path',str(m.ROOT/'fake.py'))]:
            p=self.payload();p['results']['interegular'][key]=value
            with self.assertRaises(ValueError):m.assess('I1',p,0)

    def test_required_api_without_invocation(self):
        for ident,name in [('A1','JsonSchemaParser'),('A2','build_transformers_prefix_allowed_tokens_fn')]:
            p=self.payload();p['results']={name:{'available':True,'callable':True,'module':'lmformatenforcer.test','source_path':str(m.PYTHON.parent.parent/'Lib/site-packages/lmformatenforcer/test.py')}}
            m.assess(ident,p,0)
            p['results'][name]['available']=False
            with self.assertRaises(ValueError):m.assess(ident,p,0)

    def test_quoted_platform_command_is_observed_not_denied(self):
        p=self.payload();p['observations']['subprocess_events']=[{'command':'C:/Windows/System32/cmd.exe /c "ver"','platform_stack':['_syscmd_ver','_win32_ver','win32_ver','uname','machine']}]
        m.assess('I1',p,0)
        p['observations']['subprocess_events'][0]['platform_stack']=[]
        with self.assertRaises(ValueError):m.assess('I1',p,0)

    def test_no_broad_guard_and_no_forbidden_calls(self):
        forbidden={'JsonSchemaParser','build_transformers_prefix_allowed_tokens_fn','from_pretrained','generate','forward','Popen','run','check_output'}
        for row in m.plan()['validations']:
            tree=ast.parse(row['code'])
            self.assertFalse(any(isinstance(n,ast.Raise) for n in ast.walk(tree)))
            for n in ast.walk(tree):
                if isinstance(n,ast.Call):
                    name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else ''
                    self.assertNotIn(name,forbidden)
        imports=[n for n in ast.walk(ast.parse(SOURCE.read_text())) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertFalse(any('enable_lmfe' in ast.unparse(n) for n in imports))
        self.assertNotIn('enable_lmfe',m.PREFIX)

    def test_quarantine_and_scientific_observations_block_acceptance(self):
        for field in ['scientific_calls','prohibited_content_opens']:
            p=self.payload();p['observations'][field]=['synthetic']
            with self.assertRaises(ValueError):m.assess('I1',p,0)
        p=self.payload();p['observations']['socket_events']=[{'operation':'socket.connect','arguments':[]}]
        with self.assertRaises(ValueError):m.assess('I1',p,0)

    def test_loopback_probe_allowed(self):
        p=self.payload();p['observations']['socket_events']=[{'operation':'socket.gethostname','arguments':[]},{'operation':'socket.__new__','arguments':[]},{'operation':'socket.bind','arguments':['socket',"('::1', 0)"]}]
        m.assess('I1',p,0)
        p['observations']['socket_events'][-1]['arguments'][1]="('0.0.0.0', 0)"
        with self.assertRaises(ValueError):m.assess('I1',p,0)

    def test_plan_freeze_before_validation_in_source(self):
        source=SOURCE.read_text()
        self.assertIn("event('IMPORT_API_PLAN_FROZEN'",source)
        self.assertIn("'Plan hash changed'",source)
        self.assertIn("'Execution already attempted; no retry'",source)
        self.assertNotIn('pip\', \'install',source)


if __name__=='__main__':unittest.main()
