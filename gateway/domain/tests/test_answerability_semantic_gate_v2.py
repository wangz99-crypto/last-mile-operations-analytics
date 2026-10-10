"""Interface-only fake-output tests; not a V2 semantic qualification suite."""
import ast
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

from gateway.domain.evaluation.answerability.answerability_contracts import ActiveBundle, GateInput, GateOutput, RankedEvidence
from gateway.domain.evaluation.answerability.gates import semantic_gate as v1
from gateway.domain.evaluation.answerability.gates import semantic_gate_v2 as v2

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / 'artifacts/answerability_semantic_gate_v2_prereg'
ARTIFACT_NAMES = {
    'SEMANTIC_GATE_V2_PROTOCOL.md', 'SEMANTIC_GATE_V2_REGISTRY.json', 'SEMANTIC_PROMPT_V2.txt',
    'RAW_ASSESSMENT_SCHEMA_V2.json', 'RANK_MAPPING_CONTRACT.md', 'CONSTRAINED_DECODER_REQUIREMENTS.md',
    'FRESH_QUALIFICATION_BLUEPRINT.md', 'PREREGISTRATION_RECORD.md',
}


def gate(count=5):
    """Opaque payloads test interfaces only; no substantive policy scenario or Gold."""
    bundle = ActiveBundle('last-mile-exception-triage-demo', '1.0-demo', '2026-01-01T00:00:00Z', None, '0'*64, '1'*64)
    evidence = tuple(RankedEvidence(i, 'SOP-90', '1.0-demo', 'unit-'+str(i), 'Interface unit fixture',
                                   'Opaque item '+str(i), 'Opaque unit-test payload '+str(i), 0.95-i*0.01)
                     for i in range(1, count+1))
    return GateInput('Synthetic interface-only input.', evidence, bundle)


def assessment(status='SUPPORTED', ranks=None):
    if ranks is None:
        ranks = [1] if status == 'SUPPORTED' else []
    return {'material_asks': [{'ask': 'Unit-test material requirement', 'support_status': status,
                              'supporting_evidence_ranks': ranks}],
            'policy_context_status': 'UNRESOLVED' if status == 'CONTEXT_UNRESOLVED' else 'RESOLVED',
            'decision': 'ALLOW' if status == 'SUPPORTED' else 'ABSTAIN',
            'reason_code': {'SUPPORTED': 'SUPPORTED_BY_ACTIVE_POLICY', 'UNSUPPORTED': 'INSUFFICIENT_POLICY_SUPPORT',
                            'CONTEXT_UNRESOLVED': 'UNRESOLVED_POLICY_CONTEXT'}[status]}


def schema_accepts(schema, value):
    """Test-only interpreter for the keywords in this schema, not a decoder/library claim.

    It follows JSON Schema integer semantics (integral floats are numbers representing
    integers). The actual parser separately requires lexical JSON integer tokens.
    """
    types = {'object': lambda v: type(v) is dict, 'array': lambda v: type(v) is list,
             'string': lambda v: type(v) is str,
             'integer': lambda v: type(v) is int or (type(v) is float and v.is_integer())}
    if 'type' in schema and not types[schema['type']](value): return False
    if 'enum' in schema and value not in schema['enum']: return False
    if 'const' in schema and value != schema['const']: return False
    if type(value) in (int, float):
        if 'minimum' in schema and value < schema['minimum']: return False
        if 'maximum' in schema and value > schema['maximum']: return False
    if type(value) is str:
        if len(value) < schema.get('minLength', 0): return False
        if 'pattern' in schema and re.search(schema['pattern'], value) is None: return False
    if type(value) is list:
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')): return False
        if schema.get('uniqueItems') and len({json.dumps(x, sort_keys=True) for x in value}) != len(value): return False
        if 'items' in schema and not all(schema_accepts(schema['items'], x) for x in value): return False
        if 'contains' in schema and not any(schema_accepts(schema['contains'], x) for x in value): return False
    if type(value) is dict:
        if not set(schema.get('required', [])) <= set(value): return False
        properties = schema.get('properties', {})
        if schema.get('additionalProperties') is False and not set(value) <= set(properties): return False
        if not all(schema_accepts(properties[k], v) for k,v in value.items() if k in properties): return False
    if 'allOf' in schema and not all(schema_accepts(s, value) for s in schema['allOf']): return False
    if 'anyOf' in schema and not any(schema_accepts(s, value) for s in schema['anyOf']): return False
    if 'oneOf' in schema and sum(schema_accepts(s, value) for s in schema['oneOf']) != 1: return False
    if 'if' in schema:
        branch = 'then' if schema_accepts(schema['if'], value) else 'else'
        if not schema_accepts(schema.get(branch, {}), value): return False
    return True


class InterfaceTests(unittest.TestCase):
    def rejected(self, value, input_value=None):
        with self.assertRaises(v1.SemanticOutputError):
            v2.adapt_response(v2.canonical_json(value), input_value or gate())

    def test_single_rank_exact_identity(self):
        result = v2.canonicalize(v2.canonical_json(assessment()), gate())
        self.assertEqual(result.assessment.material_asks[0].supporting_section_ids, ('SOP-90@1.0-demo#unit-1',))
        self.assertEqual(result.rank_bindings[0].canonical_identity, gate().evidence[0].identity)
        self.assertEqual(result.rank_bindings[0].evidence_rank, 1)

    def test_joint_rank_mapping_two_and_five(self):
        result = v2.canonicalize(v2.canonical_json(assessment(ranks=[2,5])), gate())
        self.assertEqual(result.assessment.material_asks[0].supporting_section_ids,
                         ('SOP-90@1.0-demo#unit-2', 'SOP-90@1.0-demo#unit-5'))
        self.assertEqual([b.material_ask_index for b in result.rank_bindings], [0,0])

    def test_rank_above_actual_count(self): self.rejected(assessment(ranks=[5]), gate(4))
    def test_rank_zero(self): self.rejected(assessment(ranks=[0]))
    def test_rank_eleven(self): self.rejected(assessment(ranks=[11]), gate(10))
    def test_negative_rank(self): self.rejected(assessment(ranks=[-1]))
    def test_duplicate_rank(self): self.rejected(assessment(ranks=[2,2]))
    def test_unsorted_ranks(self): self.rejected(assessment(ranks=[5,2]))
    def test_supported_needs_rank(self): self.rejected(assessment(ranks=[]))
    def test_unsupported_forbids_rank(self): self.rejected(assessment('UNSUPPORTED', [1]))
    def test_unresolved_forbids_rank(self): self.rejected(assessment('CONTEXT_UNRESOLVED', [1]))

    def test_wrong_rank_types(self):
        for rank in (True, False, 1.0, '1', None, {}, []):
            with self.subTest(rank=rank): self.rejected(assessment(ranks=[rank]))

    def test_rank_list_required(self):
        for ranks in ('1', 1, None, {}):
            value = assessment()
            value['material_asks'][0]['supporting_evidence_ranks'] = ranks
            self.rejected(value)

    def test_empty_evidence_cannot_be_cited(self): self.rejected(assessment(), gate(0))

    def test_empty_evidence_insufficient_valid(self):
        self.assertEqual(v2.adapt_response(v2.canonical_json(assessment('UNSUPPORTED')), gate(0)),
                         GateOutput('ABSTAIN', 'INSUFFICIENT_POLICY_SUPPORT'))

    def test_valid_unresolved(self):
        self.assertEqual(v2.adapt_response(v2.canonical_json(assessment('CONTEXT_UNRESOLVED')), gate()),
                         GateOutput('ABSTAIN', 'UNRESOLVED_POLICY_CONTEXT'))

    def test_context_unresolved_even_if_individual_asks_supported(self):
        value = assessment()
        value.update(decision='ABSTAIN', reason_code='UNRESOLVED_POLICY_CONTEXT', policy_context_status='UNRESOLVED')
        self.assertEqual(v2.adapt_response(v2.canonical_json(value), gate()).decision, 'ABSTAIN')

    def test_ask_context_unresolved_with_resolved_global_context(self):
        value = assessment('CONTEXT_UNRESOLVED')
        value['policy_context_status'] = 'RESOLVED'
        self.assertEqual(v2.adapt_response(v2.canonical_json(value), gate()).reason_code, 'UNRESOLVED_POLICY_CONTEXT')

    def test_partial_support_abstains(self):
        value = assessment('UNSUPPORTED')
        value['material_asks'].insert(0, assessment()['material_asks'][0])
        self.assertEqual(v2.adapt_response(v2.canonical_json(value), gate()).reason_code, 'INSUFFICIENT_POLICY_SUPPORT')

    def test_allow_with_unsupported_rejected(self):
        value = assessment('UNSUPPORTED'); value.update(decision='ALLOW', reason_code='SUPPORTED_BY_ACTIVE_POLICY')
        self.rejected(value)

    def test_insufficient_with_unresolved_ask_rejected(self):
        value = assessment('UNSUPPORTED'); value['material_asks'].append(assessment('CONTEXT_UNRESOLVED')['material_asks'][0])
        self.rejected(value)

    def test_false_unresolved_reason_rejected(self):
        value = assessment('UNSUPPORTED'); value['reason_code'] = 'UNRESOLVED_POLICY_CONTEXT'
        self.rejected(value)

    def test_wrong_reason_pair_rejected(self):
        value = assessment(); value['reason_code'] = 'INSUFFICIENT_POLICY_SUPPORT'; self.rejected(value)

    def test_allow_with_unresolved_context_rejected(self):
        value = assessment(); value['policy_context_status'] = 'UNRESOLVED'; self.rejected(value)

    def test_unknown_keys_rejected(self):
        for key in ('confidence', 'score', 'probability', 'question_id', 'expected_gate'):
            value = assessment(); value[key] = 1; self.rejected(value)
        value = assessment(); value['material_asks'][0]['supporting_section_ids'] = ['unit-1']; self.rejected(value)

    def test_missing_keys_rejected(self):
        for key in assessment():
            value = assessment(); del value[key]; self.rejected(value)

    def test_wrong_enum_rejected(self):
        for key in ('decision', 'reason_code', 'policy_context_status'):
            value = assessment(); value[key] = 'UNKNOWN'; self.rejected(value)
        value = assessment(); value['material_asks'][0]['support_status'] = 'LIKELY'; self.rejected(value)

    def test_empty_and_excess_asks(self):
        for size in (0,9):
            value = assessment(); value['material_asks'] *= size; self.rejected(value)

    def test_eight_asks_is_structurally_valid(self):
        value = assessment(); value['material_asks'] *= 8
        self.assertEqual(len(v2.parse_assessment(v2.canonical_json(value), gate()).material_asks), 8)

    def test_blank_ask_rejected(self):
        value = assessment(); value['material_asks'][0]['ask'] = '  \n '; self.rejected(value)

    def test_no_fence_or_prose_cleanup(self):
        text = v2.canonical_json(assessment()).decode()
        for raw in ('```json\n'+text+'```', 'Here is JSON: '+text, text+' trailing text', text+text):
            with self.assertRaises(v1.SemanticOutputError): v2.adapt_response(raw, gate())

    def test_strict_duplicate_nonfinite_utf8_and_top_level(self):
        for raw in ('{"decision":"ALLOW","decision":"ABSTAIN"}', 'NaN', 'null', '[]', b'\xff'):
            with self.assertRaises(v1.SemanticOutputError): v2.adapt_response(raw, gate())

    def test_no_fuzzy_or_partial_id_repair(self):
        for ref in ('unit-1', 'SOP-90@1.0-demo#unit-1', 'Opaque item 1', 'ONE'):
            self.rejected(assessment(ranks=[ref]))

    def test_mapping_stability_no_mutation(self):
        value, input_value = assessment(ranks=[2,5]), gate()
        before = v2.canonical_json(asdict(input_value))
        a = v2.canonicalize(v2.canonical_json(value), input_value)
        b = v2.canonicalize(json.dumps(value), input_value)
        self.assertEqual(a, b); self.assertEqual(a.audit_bytes(), b.audit_bytes())
        self.assertEqual(a.canonical_bytes(), b.canonical_bytes())
        self.assertEqual(before, v2.canonical_json(asdict(input_value)))

    def test_frozen_parser_is_final_authority(self):
        with patch.object(v1, 'parse_assessment', wraps=v1.parse_assessment) as parser:
            result = v2.adapt_response(v2.canonical_json(assessment()), gate())
        parser.assert_called_once()
        self.assertIs(type(result), GateOutput)
        self.assertEqual(set(asdict(result)), {'decision','reason_code'})

    def test_exact_gate_input_boundary(self):
        class RichGateInput(GateInput): pass
        value = gate()
        for bad in (asdict(value), {'gate_input': value, 'question_id':'CANARY'}, RichGateInput(value.question, value.evidence, value.active_bundle)):
            with self.assertRaises(v1.SemanticOutputError): v2.build_request(bad)

    def test_prompt_payload_is_identical_to_frozen_allowlist(self):
        value = gate(10)
        self.assertEqual(v2.build_messages(value)[1], v1.build_messages(value)[1])
        payload = json.loads(v2.build_messages(value)[1]['content'])
        self.assertEqual([e['rank'] for e in payload['evidence']], list(range(1,11)))
        self.assertEqual(set(payload), {'question', 'active_bundle', 'evidence'})
        forbidden = {'question_id','split','expected_gate','gold_support_sections','required_support_sections','difficulty','hard_negative','support_shape','rationale','review_status','v1_result'}
        self.assertFalse(forbidden & set(payload))
        self.assertFalse(any(forbidden & set(e) for e in payload['evidence']))

    def test_request_serialization_deterministic(self):
        self.assertEqual(v2.canonical_json(v2.build_request(gate())), v2.canonical_json(v2.build_request(gate())))
        self.assertEqual(v2.build_request(gate())['structured_output_mode'], 'JSON_SCHEMA_CONSTRAINED_DECODING')

    def test_semantic_instructions_and_decision_schema_unchanged(self):
        self.assertEqual(v2.SEMANTIC_INSTRUCTIONS, v1.SYSTEM_INSTRUCTIONS.split('Return one JSON object only,',1)[0])
        self.assertEqual(v2.RAW_ASSESSMENT_SCHEMA_V2['oneOf'], v1.RAW_ASSESSMENT_SCHEMA['oneOf'])

    def test_non_executable_candidate_has_no_retained_input(self):
        candidate = v2.SemanticGateV2()
        with self.assertRaisesRegex(v2.ConstrainedDecoderImplementationRequired, 'IMPLEMENTATION_REQUIRED'):
            candidate.decide(gate())
        self.assertFalse(hasattr(candidate, '__dict__'))


class SchemaTests(unittest.TestCase):
    def valid(self, value, schema=None): return schema_accepts(schema or v2.RAW_ASSESSMENT_SCHEMA_V2, value)

    def test_positive_samples(self):
        for status in ('SUPPORTED','UNSUPPORTED','CONTEXT_UNRESOLVED'):
            self.assertTrue(self.valid(assessment(status)))

    def test_unknown_top_and_ask_keys(self):
        value=assessment(); value['extra']=True; self.assertFalse(self.valid(value))
        value=assessment(); value['material_asks'][0]['extra']=True; self.assertFalse(self.valid(value))

    def test_wrong_enums(self):
        for key in ('decision','reason_code','policy_context_status'):
            value=assessment(); value[key]='BAD'; self.assertFalse(self.valid(value))
        value=assessment(); value['material_asks'][0]['support_status']='BAD'; self.assertFalse(self.valid(value))

    def test_string_boolean_zero_eleven_duplicate_ranks(self):
        for ranks in (['1'],[True],[0],[11],[2,2]): self.assertFalse(self.valid(assessment(ranks=ranks)))

    def test_empty_excess_asks(self):
        for size in (0,9):
            value=assessment(); value['material_asks']*=size; self.assertFalse(self.valid(value))

    def test_status_reference_consistency(self):
        self.assertFalse(self.valid(assessment(ranks=[])))
        self.assertFalse(self.valid(assessment('UNSUPPORTED',[1])))
        self.assertFalse(self.valid(assessment('CONTEXT_UNRESOLVED',[1])))

    def test_dynamic_upper_bound_and_empty_evidence(self):
        self.assertFalse(self.valid(assessment(ranks=[5]), v2.schema_for_input(gate(4))))
        self.assertTrue(self.valid(assessment(ranks=[4]), v2.schema_for_input(gate(4))))
        self.assertFalse(self.valid(assessment(), v2.schema_for_input(gate(0))))
        self.assertTrue(self.valid(assessment('UNSUPPORTED'), v2.schema_for_input(gate(0))))

    def test_schema_limitations_are_not_misrepresented(self):
        # Standard JSON Schema integer semantics accept 1.0; ordering needs the adapter.
        self.assertTrue(self.valid(assessment(ranks=[1.0])))
        self.assertTrue(self.valid(assessment(ranks=[5,2])))
        self.assertTrue(self.valid(assessment(ranks=[5])))  # static maximum=10
        for value,input_value in ((assessment(ranks=[1.0]),gate()),(assessment(ranks=[5,2]),gate()),(assessment(ranks=[5]),gate(4))):
            with self.assertRaises(v1.SemanticOutputError):v2.adapt_response(v2.canonical_json(value),input_value)

    def test_dynamic_schema_does_not_mutate_static_or_v1(self):
        before=v2.canonical_json(v2.RAW_ASSESSMENT_SCHEMA_V2)
        inherited=v2.canonical_json(v1.RAW_ASSESSMENT_SCHEMA)
        dynamic=v2.schema_for_input(gate(4)); dynamic['properties'].clear()
        self.assertEqual(before,v2.canonical_json(v2.RAW_ASSESSMENT_SCHEMA_V2))
        self.assertEqual(inherited,v2.canonical_json(v1.RAW_ASSESSMENT_SCHEMA))


class PreregistrationGuardTests(unittest.TestCase):
    def test_exact_artifact_inventory_no_qualification_suite(self):
        self.assertEqual({p.name for p in ARTIFACTS.iterdir() if p.is_file()},ARTIFACT_NAMES)
        registry=json.loads((ARTIFACTS/'SEMANTIC_GATE_V2_REGISTRY.json').read_bytes())
        self.assertEqual(registry['qualification_suite_status'],'FRESH_SUITE_REQUIRED_NOT_YET_AUTHORED')
        self.assertEqual(registry['constrained_decoder_status'],'IMPLEMENTATION_REQUIRED')
        def check(value):
            if type(value) is dict:
                self.assertFalse(set(value)&{'case_id','question_id','expected_gate','gate_input','raw_text','expected_answers','gold_support_sections','required_support_sections'})
                for item in value.values():check(item)
            elif type(value) is list:
                for item in value:check(item)
        check(registry)

    def test_candidate_source_has_no_payload_reader_or_old_suite_import(self):
        source=Path(v2.__file__).read_text()
        tree=ast.parse(source)
        imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):imports.append('.'*node.level+(node.module or ''))
            elif isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                self.assertNotIn(name,{'open','read_text','read_bytes','load','generate','search','retrieve','exec','eval','__import__'})
        self.assertEqual(set(imports),{'copy','dataclasses','json','..answerability_contracts','.'})
        self.assertNotIn('qualify_semantic_attempt2',source)
        self.assertNotIn('SYNTHETIC_QUALIFICATION_SUITE',source)

    def test_prompt_schema_artifacts_and_hash_receipts(self):
        self.assertEqual((ARTIFACTS/'SEMANTIC_PROMPT_V2.txt').read_bytes(),v2.canonical_prompt().encode())
        self.assertEqual((ARTIFACTS/'RAW_ASSESSMENT_SCHEMA_V2.json').read_bytes(),v2.canonical_json(v2.RAW_ASSESSMENT_SCHEMA_V2))
        registry=json.loads((ARTIFACTS/'SEMANTIC_GATE_V2_REGISTRY.json').read_bytes())
        for name,digest in registry['artifact_sha256'].items():
            self.assertIn(name,ARTIFACT_NAMES)
            self.assertEqual(hashlib.sha256((ARTIFACTS/name).read_bytes()).hexdigest(),digest)
        self.assertEqual(hashlib.sha256(Path(v2.__file__).read_bytes()).hexdigest(),registry['candidate_source_sha256'])
        self.assertEqual(hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),registry['synthetic_test_source_sha256'])
        receipt=''.join(key+'\t'+registry[key]+'\n' for key in registry['parser_adapter_receipt_fields'])
        self.assertEqual(hashlib.sha256(receipt.encode()).hexdigest(),registry['parser_adapter_receipt_sha256'])

    def test_isolated_no_model_network_retrieval_or_legacy_payload_access(self):
        script='''
import os,sys
blocked=('torch','transformers','sentence_transformers','huggingface_hub','openai','anthropic','outlines','lmformatenforcer','xgrammar','guidance')
class Guard:
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in blocked or name.startswith('gateway.domain.retrieval') or 'qualify_semantic_attempt2' in name:
   raise RuntimeError('Forbidden model/retrieval/old-suite import')
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event.startswith('socket.'):raise RuntimeError('No network')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.fsdecode(args[0]).lower().replace(chr(92),'/')
  if any(s in p for s in ('heldout','held_out','/development/','/answerability_dev_gate_baselines_v0/','/answerability_dev_bge_evidence_v0/','/answerability_semantic_model_v1_qualification_attempt2/')):
   raise RuntimeError('Quarantined content access forbidden')
sys.addaudithook(audit)
from gateway.domain.evaluation.answerability.gates import semantic_gate_v2 as v2
from gateway.domain.tests.test_answerability_semantic_gate_v2 import gate,assessment
v2.build_request(gate())
v2.adapt_response(v2.canonical_json(assessment()),gate())
assert not set(blocked).intersection(sys.modules)
print('isolated V2 boundary PASS')
'''
        result=subprocess.run([sys.executable,'-B','-c',script],cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('isolated V2 boundary PASS',result.stdout)


if __name__=='__main__':unittest.main()
