"""Offline dependency enablement guards; no decoder or model imports."""
import json
import unittest
from unittest.mock import patch
from gateway.domain.evaluation.answerability import enable_decoder_dependencies as h


class EnablementTests(unittest.TestCase):
    def test_exact_roots(self):
        self.assertEqual(h.PINS['apache-tvm-ffi'][0], '0.1.14.post1')
        self.assertEqual(h.PINS['pydantic'][0], '2.13.5')

    def test_yanked_version_rejected(self):
        with self.assertRaises(ValueError):
            h.wheel_check('apache-tvm-ffi', 'apache_tvm_ffi-0.1.14-cp312-cp312-win_amd64.whl', b'')

    def test_wrong_wheel_rejected(self):
        with self.assertRaises(ValueError): h.wheel_check('pydantic', 'pydantic-2.14.0-py3-none-any.whl', b'')

    def test_wrong_sha_rejected(self):
        with self.assertRaises(ValueError): h.wheel_check('pydantic', h.PINS['pydantic'][1], b'incorrect')

    def test_unexpected_dependency_blocks(self):
        with self.assertRaises(ValueError): h.resolve_graph({'pydantic': {'requires_dist': ['unapproved-missing>=1']}}, {})

    def test_existing_satisfying_dependency_allowed(self):
        edges, order = h.resolve_graph({'pydantic': {'requires_dist': ['already-there>=1']}}, {'already-there': {'version': '1.0'}})
        self.assertTrue(edges['pydantic'][0]['satisfied'])
        self.assertEqual(order, ['pydantic'])

    def test_typing_extensions_preserved(self):
        packages = {'typing-extensions': {'version': '4.16.0'}}
        before = h.serialized(packages)
        h.typing_check(packages)
        self.assertEqual(h.serialized(packages), before)

    def test_typing_extensions_missing_old_blocked(self):
        for packages in ({}, {'typing-extensions': {'version': '4.13.0'}}):
            with self.assertRaises(ValueError): h.typing_check(packages)

    def test_no_deps_no_index_install(self):
        cmd = h.install_command(['exact.whl'])
        self.assertIn('--no-deps', cmd)
        self.assertIn('--no-index', cmd)
        self.assertNotIn('-U', cmd)
        self.assertEqual(cmd[-1], 'exact.whl')

    def test_drift_rejected(self):
        with self.assertRaises(ValueError): h.drift_check({'torch': {'version': '1'}}, {'torch': {'version': '2'}}, [])

    def test_decoder_must_remain_absent(self):
        with self.assertRaises(ValueError): h.drift_check({}, {'xgrammar': {'version': '0.2.8'}}, [])

    def test_optional_extras_inactive(self):
        self.assertFalse(h.requirement_check('email-validator; extra == "email"', {})['applicable'])
        self.assertFalse(h.requirement_check('tzdata; extra == "timezone"', {})['applicable'])

    def test_plan_immutable(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp, patch.object(h, 'OUT', Path(temp)):
            h.write('DEPENDENCY_LOCK.json', {'fixture': True})
            h.journal('DEPENDENCY_PLAN_FROZEN', {'sha256': h.digest((h.OUT / 'DEPENDENCY_LOCK.json').read_bytes())})
            self.assertEqual(h.verified_lock()[0], {'fixture': True})
            (h.OUT / 'DEPENDENCY_LOCK.json').write_bytes(b'{}')
            with self.assertRaises(ValueError): h.verified_lock()

    def test_serialization_deterministic(self):
        self.assertEqual(h.serialized({'a': 1, 'b': 2}), h.serialized({'b': 2, 'a': 1}))

    def test_only_authorized_pins(self):
        self.assertEqual(set(h.PINS), {'apache-tvm-ffi', 'pydantic', 'pydantic-core', 'annotated-types', 'typing-inspection'})
        with self.assertRaises(ValueError): h.wheel_check('xgrammar', 'any.whl', b'')


if __name__ == '__main__':
    unittest.main()
