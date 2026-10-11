"""Deterministic R2 harness tests; no real import-validation subprocesses."""
import ast
from copy import deepcopy
from pathlib import Path
import unittest

from gateway.domain.evaluation.answerability import validate_dependency_imports_r2 as h


def targets():
    return [{'package': n} for n in h.ORDER]


def plan():
    return {'python': str(h.PYTHON), 'runner_sha256': h.sha(b'runner'), 'child_script': h.CHILD,
            'child_script_sha256': h.sha(h.CHILD.encode()), 'maximum_processes': 6,
            'independent_count': 5, 'retries': 0, 'combined_only_if_all_independent_pass': True}


class RecoveryTests(unittest.TestCase):
    def test_six_process_maximum(self):
        calls = []
        def fake(ts, stage, seq):
            calls.append((ts, stage, seq))
            return {'passed': True}
        independent, combined = h.stage_schedule(targets(), fake)
        self.assertEqual(len(calls), 6)
        self.assertEqual([x[2] for x in calls], list(range(1, 7)))
        self.assertEqual([x[0][0]['package'] for x in calls[:5]], list(h.ORDER))
        self.assertEqual(calls[5][0], targets())
        self.assertTrue(combined['passed'])

    def test_each_failure_skips_combined_without_retry(self):
        for failure in range(1, 6):
            calls = []
            def fake(ts, stage, seq):
                calls.append(seq)
                return {'passed': seq != failure}
            _, combined = h.stage_schedule(targets(), fake)
            self.assertIsNone(combined)
            self.assertEqual(calls, [1, 2, 3, 4, 5])

    def test_infrastructure_exception_not_retried(self):
        calls = []
        def fake(ts, stage, seq):
            calls.append(seq)
            raise RuntimeError('synthetic launch failure')
        with self.assertRaises(RuntimeError): h.stage_schedule(targets(), fake)
        self.assertEqual(calls, [1])

    def test_order_immutable(self):
        with self.assertRaises(ValueError): h.stage_schedule(targets()[::-1], lambda *a: None)

    def test_frozen_plan_accepted(self):
        raw = h.canonical(plan())
        self.assertEqual(h.validate_plan(raw, h.sha(raw), b'runner', []), plan())

    def test_modified_plan_rejected(self):
        with self.assertRaises(ValueError): h.validate_plan(h.canonical(plan()), 'wrong', b'runner', [])

    def test_modified_runner_rejected(self):
        raw = h.canonical(plan())
        with self.assertRaises(ValueError): h.validate_plan(raw, h.sha(raw), b'changed', [])

    def test_wrong_python_rejected(self):
        p = plan(); p['python'] = str(Path.cwd() / 'wrong-python.exe'); raw = h.canonical(p)
        with self.assertRaises(ValueError): h.validate_plan(raw, h.sha(raw), b'runner', [])

    def test_no_scientific_run_retry(self):
        raw = h.canonical(plan())
        with self.assertRaises(ValueError):
            h.validate_plan(raw, h.sha(raw), b'runner', [{'event': 'INDEPENDENT_IMPORT_VALIDATION_STARTED'}])

    def test_wrong_budget_rejected(self):
        for key, value in [('maximum_processes', 7), ('independent_count', 6), ('retries', 1), ('combined_only_if_all_independent_pass', False)]:
            p = plan(); p[key] = value; raw = h.canonical(p)
            with self.assertRaises(ValueError): h.validate_plan(raw, h.sha(raw), b'runner', [])

    def test_child_is_observer_not_guard(self):
        tree = ast.parse(h.CHILD)
        self.assertFalse(any(isinstance(n, ast.Raise) for n in ast.walk(tree)))
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                lhs = n.targets if isinstance(n, ast.Assign) else [n.target]
                self.assertFalse(any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id in ('subprocess', 'socket') for t in lhs))
        self.assertNotIn('enable_decoder_dependencies', Path(h.__file__).read_text())

    def test_no_child_benchmark_model_network_or_pip_operations(self):
        tree = ast.parse(h.CHILD)
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                self.assertTrue(all(a.name in {'sys', 'os', 'json', 'hashlib', 'importlib', 'importlib.metadata'} for a in n.names))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                self.assertNotIn(n.func.attr, {'from_pretrained', 'generate', 'forward', 'connect', 'urlopen', 'run', 'Popen', 'check_output'})

    def payload_fixture(self):
        identity = {'name': 'synthetic', 'version': '1', 'metadata_sha256': 'm', 'record_sha256': 'r'}
        target = {'package': 'synthetic', 'module': 'synthetic', 'identity': identity}
        row = {'package': 'synthetic', 'module': 'synthetic', 'module_path': str(h.PYTHON.parent.parent / 'Lib/site-packages/synthetic/__init__.py'),
               'distribution_name': 'synthetic', 'distribution_version': '1', 'metadata_sha256': 'm', 'record_sha256': 'r', 'import_success': True}
        return {'results': [row], 'observations': {'prohibited_content_opens': []}, 'forbidden_modules_present': []}, [target]

    def test_module_path_validated(self):
        p, ts = self.payload_fixture()
        self.assertTrue(h.payload_valid(p, ts, h.PYTHON.parent.parent))
        p['results'][0]['module_path'] = str(Path.cwd() / 'untrusted/__init__.py')
        self.assertFalse(h.payload_valid(p, ts, h.PYTHON.parent.parent))

    def test_distribution_identity_validated(self):
        for field in ('distribution_name', 'distribution_version', 'metadata_sha256', 'record_sha256'):
            p, ts = self.payload_fixture(); p['results'][0][field] = 'wrong'
            self.assertFalse(h.payload_valid(p, ts, h.PYTHON.parent.parent))

    def test_decoder_and_benchmark_excluded(self):
        p, ts = self.payload_fixture(); p['forbidden_modules_present'] = ['xgrammar']
        self.assertFalse(h.payload_valid(p, ts, h.PYTHON.parent.parent))
        p, ts = self.payload_fixture(); p['observations']['prohibited_content_opens'] = ['synthetic-forbidden-path']
        self.assertFalse(h.payload_valid(p, ts, h.PYTHON.parent.parent))

    def test_inventory_drift_and_decoder_presence(self):
        before = {'packages': {'existing': {'version': '1', 'record': 'a'}}}
        h.intact(before, deepcopy(before))
        after = deepcopy(before); after['packages']['existing']['record'] = 'b'
        with self.assertRaises(ValueError): h.intact(before, after)
        present = {'packages': {'xgrammar': {}}}
        with self.assertRaises(ValueError): h.intact(present, present)

    def test_serialization_deterministic(self):
        self.assertEqual(h.canonical({'a': 1, 'b': 2}), h.canonical({'b': 2, 'a': 1}))


if __name__ == '__main__': unittest.main()
