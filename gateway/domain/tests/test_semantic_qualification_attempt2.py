"""Synthetic-only custody, timeout, scoring and boundary tests; no ML imports."""
import copy
import json
import multiprocessing
import tempfile
import time
from pathlib import Path
import unittest
from unittest.mock import Mock

from gateway.domain.evaluation.answerability import qualify_semantic_attempt2 as q
from gateway.domain.evaluation.answerability.gates.semantic_gate import canonical_json, build_messages


def fake_worker(connection, mode):
    connection.send({'type': 'ready'})
    if mode == 'hang':
        time.sleep(10)
    else:
        connection.send({'type': 'result', 'raw_text': 'fake only'})
    connection.close()


def fake_assessment(case):
    reason = case['expected']['reason_code']
    status = {'SUPPORTED_BY_ACTIVE_POLICY': 'SUPPORTED', 'INSUFFICIENT_POLICY_SUPPORT': 'UNSUPPORTED',
              'UNRESOLVED_POLICY_CONTEXT': 'CONTEXT_UNRESOLVED'}[reason]
    gate = q.gate_from_wire(case['gate_input'])
    return {'material_asks': [{'ask': 'Synthetic substantive requirement', 'support_status': status,
                              'supporting_section_ids': [q.section_reference(gate.evidence[0])] if status == 'SUPPORTED' else []}],
            'policy_context_status': 'UNRESOLVED' if status == 'CONTEXT_UNRESOLVED' else 'RESOLVED',
            **case['expected']}


def records(suite):
    cases = {c['case_id']: c for c in suite['cases']}
    return [{'case_id': cid, 'attempt_type': kind, 'raw_text': canonical_json(fake_assessment(cases[cid])).decode(),
             'termination_status': 'EOS'} for cid, kind in q.PLAN]


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.suite = q.synthetic_suite()
        self.config = q.execution_config()

    def test_exact_revision(self):
        for value in ('main', 'latest', '0' * 40):
            self.config['revision'] = value
            with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_local_only_required(self):
        self.config['local_files_only'] = False
        with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_cpu_required(self):
        self.config['device'] = 'cuda'
        with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_fp32_required(self):
        self.config['dtype'] = 'bfloat16'
        with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_quantization_forbidden(self):
        self.config['quantization'] = 'int8'
        with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_configuration_complete(self):
        q.validate_execution_config(self.config)
        for key in ('timeout_seconds', 'seed', 'temperature', 'max_new_tokens', 'structured_output_mode'):
            bad = copy.deepcopy(self.config)
            del bad[key]
            with self.assertRaises(ValueError): q.validate_execution_config(bad)

    def test_no_quality_retry(self):
        self.config['quality_retry'] = 'ON_FAILURE'
        with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_no_infrastructure_retry(self):
        self.config['infrastructure_retry_count'] = 1
        with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_full_generation_settings_unchanged(self):
        self.config['generation_config']['repetition_penalty'] = 1.1
        with self.assertRaises(ValueError): q.validate_execution_config(self.config)

    def test_suite_inventory(self):
        self.assertEqual(tuple(c['case_id'] for c in self.suite['cases']), q.PRIMARY)
        self.assertEqual(len({c['gate_input']['question'] for c in self.suite['cases']}), 12)
        self.assertEqual(q.REPEATS, ('Q2', 'Q7', 'Q11'))
        for c in self.suite['cases']:
            q.gate_from_wire(c['gate_input'])

    def test_no_labels_or_richer_object_cross_boundary(self):
        for c in self.suite['cases']:
            with self.assertRaises(ValueError): q.gate_from_wire(c)
            value = copy.deepcopy(c['gate_input'])
            for key in ('case_id', 'expected', 'question_id', 'gold_support_sections', 'difficulty', 'review_status'):
                bad = dict(value, **{key: 'FORBIDDEN_CANARY'})
                with self.assertRaises(ValueError): q.gate_from_wire(bad)
            payload = json.loads(build_messages(q.gate_from_wire(value))[1]['content'])
            self.assertEqual(set(payload), {'question', 'active_bundle', 'evidence'})
            self.assertNotIn('FORBIDDEN_CANARY', str(payload))
            self.assertNotIn('AQ001', str(payload))

    def test_no_development_or_private_access(self):
        for path in ('/answerability/development/example.json', '/a/held_out/file.json', '/a/private_heldout/file.json',
                     '/retrieval/development/example.json', '/answerability_dev_bge_evidence_v0/file.json'):
            self.assertTrue(q.blocked_path(path))
        self.assertFalse(q.blocked_path('/synthetic/qualification.json'))

    def test_network_policy(self):
        self.assertTrue(q.network_allowed('socket.__new__', ()))
        self.assertTrue(q.network_allowed('socket.gethostname', ()))
        self.assertTrue(q.network_allowed('socket.bind', (None, ('::1', 0, 0, 0))))
        self.assertFalse(q.network_allowed('socket.bind', (None, ('0.0.0.0', 0))))
        for event in ('socket.connect', 'socket.getaddrinfo', 'socket.sendto'):
            self.assertFalse(q.network_allowed(event, ()))

    def test_suite_and_config_frozen_before_execution(self):
        raw = canonical_json(self.suite)
        config = canonical_json(self.config)
        events = [{'event': 'QUALIFICATION_SUITE_FROZEN', 'details': {'sha256': q.sha(raw)}},
                  {'event': 'INFERENCE_CONFIG_FROZEN', 'details': {'sha256': q.sha(config)}},
                  {'event': 'TIMEOUT_WORKER_VERIFIED', 'details': {}}]
        q.require_frozen_ready(events, raw, config)
        with self.assertRaises(ValueError): q.require_frozen_ready(events[1:], raw, config)
        with self.assertRaises(ValueError): q.require_frozen_ready(events, raw + b' ', config)
        with self.assertRaises(ValueError): q.require_frozen_ready(events, raw, config + b' ')
        with self.assertRaises(ValueError): q.require_frozen_ready(events + [{'event': 'EXECUTION_STARTED'}], raw, config)

    def test_call_budget_exact_order_no_sixteenth(self):
        budget = q.CallBudget()
        for case, kind in q.PLAN: budget.claim(case, kind)
        with self.assertRaises(ValueError): budget.claim('Q2', 'DETERMINISM')

    def test_call_budget_no_quality_retry(self):
        budget = q.CallBudget()
        budget.claim('Q1', 'PRIMARY')
        with self.assertRaises(ValueError): budget.claim('Q1', 'PRIMARY')
        with self.assertRaises(ValueError): budget.claim('Q3', 'PRIMARY')

    def test_worker_timeout_terminates_real_fake_process(self):
        ctx = multiprocessing.get_context('spawn')
        parent, child = ctx.Pipe()
        process = ctx.Process(target=fake_worker, args=(child, 'hang'))
        process.start()
        child.close()
        try:
            self.assertEqual(q.receive_with_timeout(parent, process, 10)['type'], 'ready')
            with self.assertRaises(TimeoutError): q.receive_with_timeout(parent, process, 0.05)
            self.assertFalse(process.is_alive())
        finally:
            if process.is_alive(): process.terminate()
            process.join(5)
            parent.close()

    def test_worker_success_no_restart(self):
        ctx = multiprocessing.get_context('spawn')
        parent, child = ctx.Pipe()
        process = ctx.Process(target=fake_worker, args=(child, 'return'))
        process.start()
        child.close()
        try:
            self.assertEqual(q.receive_with_timeout(parent, process, 10)['type'], 'ready')
            self.assertEqual(q.receive_with_timeout(parent, process, 10)['raw_text'], 'fake only')
        finally:
            process.join(5)
            if process.is_alive(): process.terminate()
            parent.close()

    def test_timeout_deadline_not_reset_by_events(self):
        connection = Mock()
        connection.poll.return_value = False
        process = Mock()
        process.is_alive.return_value = False
        with self.assertRaises(TimeoutError): q.receive_with_timeout(connection, process, 0.01)
        process.terminate.assert_called_once()

    def test_strict_parser_no_fence_repair(self):
        c = self.suite['cases'][0]
        raw = canonical_json(fake_assessment(c)).decode()
        result = q.assess('```json\n' + raw + '```', q.gate_from_wire(c['gate_input']))
        self.assertFalse(result['parser_valid'])
        self.assertIsNone(result['gate_output'])

    def test_invalid_reference_is_error_not_abstain(self):
        c = self.suite['cases'][0]
        value = fake_assessment(c)
        value['material_asks'][0]['supporting_section_ids'] = ['SOP-99@1.0-demo#imaginary']
        a = q.assess(canonical_json(value).decode(), q.gate_from_wire(c['gate_input']))
        self.assertTrue(a['structured_output_validity'])
        self.assertFalse(a['section_reference_validity'])
        self.assertFalse(a['parser_valid'])

    def test_inconsistent_decision_is_error(self):
        c = self.suite['cases'][0]
        value = fake_assessment(c)
        value['material_asks'][0]['support_status'] = 'UNSUPPORTED'
        a = q.assess(canonical_json(value).decode(), q.gate_from_wire(c['gate_input']))
        self.assertFalse(a['internal_consistency'])
        self.assertFalse(a['parser_valid'])

    def test_empty_asks_duplicate_key_unknown_enum(self):
        c = self.suite['cases'][0]
        gate = q.gate_from_wire(c['gate_input'])
        for raw in ('{"decision":"ALLOW","decision":"ABSTAIN"}', '{}', 'NaN', 'null'):
            self.assertFalse(q.assess(raw, gate)['parser_valid'])
        value = fake_assessment(c)
        value['material_asks'] = []
        self.assertFalse(q.assess(canonical_json(value).decode(), gate)['parser_valid'])
        value = fake_assessment(c)
        value['decision'] = 'MAYBE'
        self.assertFalse(q.assess(canonical_json(value).decode(), gate)['parser_valid'])

    def test_all_valid_fake_responses_qualify(self):
        result = q.score(self.suite, records(self.suite))
        self.assertEqual(result['outcome'], 'QUALIFIED')
        self.assertEqual(result['metrics']['binary_correctness'], {'numerator': 12, 'denominator': 12})

    def test_one_noncritical_error_allowed_two_fail(self):
        data = records(self.suite)
        for index in (0, 1):
            case = copy.deepcopy(self.suite['cases'][index])
            case['expected'] = {'decision': 'ABSTAIN', 'reason_code': 'INSUFFICIENT_POLICY_SUPPORT'}
            data[index]['raw_text'] = canonical_json(fake_assessment(case)).decode()
            self.assertEqual(q.score(self.suite, data)['outcome'], 'QUALIFIED' if index == 0 else 'QUALIFICATION_FAILED')

    def test_critical_error_fails_even_eleven_correct(self):
        data = records(self.suite)
        data[2]['raw_text'] = data[0]['raw_text']
        # Give the wrong ALLOW a supplied citation to make it structurally valid.
        value = json.loads(data[2]['raw_text'])
        value['material_asks'][0]['supporting_section_ids'] = [q.section_reference(q.gate_from_wire(self.suite['cases'][2]['gate_input']).evidence[0])]
        data[2]['raw_text'] = canonical_json(value).decode()
        result = q.score(self.suite, data)
        self.assertEqual(result['metrics']['binary_correctness']['numerator'], 11)
        self.assertEqual(result['outcome'], 'QUALIFICATION_FAILED')

    def test_one_structural_error_fails(self):
        data = records(self.suite)
        data[0]['raw_text'] = 'not JSON'
        self.assertEqual(q.score(self.suite, data)['outcome'], 'QUALIFICATION_FAILED')

    def test_incomplete_timeout_no_capability_judgment(self):
        data = records(self.suite)[:3]
        data[-1].update(raw_text=None, termination_status='TIMEOUT')
        result = q.score(self.suite, data)
        self.assertEqual(result['outcome'], 'QUALIFICATION_INCOMPLETE')
        self.assertEqual(result['timeout_count'], 1)

    def test_duplicate_not_an_accuracy_case(self):
        data = records(self.suite)
        data[-1]['raw_text'] = 'broken duplicate'
        result = q.score(self.suite, data)
        self.assertEqual(result['outcome'], 'QUALIFIED')
        self.assertEqual(result['metrics']['binary_correctness']['denominator'], 12)
        self.assertFalse(q.determinism(result, data)['comparisons'][-1]['both_parser_valid'])

    def test_unauthorized_duplicate_rejected(self):
        data = records(self.suite)
        data[-1]['case_id'] = 'Q1'
        with self.assertRaises(ValueError): q.score(self.suite, data)

    def test_determinism_fields_and_wording(self):
        data = records(self.suite)
        value = json.loads(data[12]['raw_text'])
        value['material_asks'][0]['ask'] = 'Different wording of the same synthetic ask'
        data[12]['raw_text'] = canonical_json(value).decode()
        comparison = q.determinism(q.score(self.suite, data), data)['comparisons'][0]
        self.assertTrue(comparison['semantic_fields_identical'])
        self.assertFalse(comparison['raw_utf8_bytes_identical'])

    def test_context_budget_rejects_no_truncation(self):
        self.assertEqual(q.require_context_capacity(100, 4096, 32768), 28572)
        with self.assertRaises(ValueError): q.require_context_capacity(30000, 4096, 32768)

    def test_determinism_detects_semantic_disagreement_without_new_threshold(self):
        data = records(self.suite)
        case = copy.deepcopy(self.suite['cases'][1])
        case['expected'] = {'decision': 'ABSTAIN', 'reason_code': 'INSUFFICIENT_POLICY_SUPPORT'}
        data[12]['raw_text'] = canonical_json(fake_assessment(case)).decode()
        result = q.score(self.suite, data)
        self.assertEqual(result['outcome'], 'QUALIFIED')
        comparison = q.determinism(result, data)['comparisons'][0]
        self.assertFalse(comparison['semantic_fields_identical'])
        self.assertFalse(comparison['semantic_fields']['decision'])

    def test_artifact_serialization_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.json'
            digest = q.write_new(path, self.suite)
            self.assertEqual(path.read_bytes(), canonical_json(json.loads(path.read_bytes())))
            self.assertEqual(digest, q.sha(path.read_bytes()))
            with self.assertRaises(FileExistsError): q.write_new(path, self.suite)


if __name__ == '__main__':
    unittest.main()
