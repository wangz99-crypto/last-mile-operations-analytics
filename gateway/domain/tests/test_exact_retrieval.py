"""Exact retrieval and synthetic deterministic-output round trips; no Gold reads."""
import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import subprocess
import sys
import unittest

DOMAIN = Path(__file__).resolve().parents[1]
if str(DOMAIN) not in sys.path:
    sys.path.insert(0, str(DOMAIN))
from retrieval import (
    InvalidSectionReferenceError, SectionNotFoundError, SectionStore,
    collect_required_sections, retrieve_case_sections, retrieve_required_sections,
)


def ref(policy="SOP-02", section="late-escalate", version="1.0-demo"):
    return dict(policy_id=policy, version=version, section_id=section)


class ExactRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = SectionStore.load()

    def test_exact_identity_body_source_and_presentation_rank(self):
        refs = [ref("SOP-03", "stale-escalate"), ref(), ref("SOP-03", "stale-escalate")]
        before = copy.deepcopy(refs)
        records = retrieve_required_sections(refs, store=self.store)
        self.assertEqual(refs, before)
        self.assertEqual([r.identity for r in records], [("SOP-03", "1.0-demo", "stale-escalate"), ("SOP-02", "1.0-demo", "late-escalate")])
        self.assertEqual([r.rank for r in records], [1, 2])
        self.assertEqual([r.request_indices for r in records], [(0, 2), (1,)])
        for record in records:
            section = self.store.get(**dict(zip(("policy_id", "version", "section_id"), record.identity)))
            self.assertEqual((record.text, record.content_hash, record.source_path), (section.text, section.content_hash, section.source_path))
            self.assertEqual(record.retrieval_method, "EXACT_POLICY_SECTION")
            self.assertFalse(hasattr(record, "similarity_score"))
            self.assertFalse(hasattr(record, "confidence"))
        with self.assertRaises(FrozenInstanceError):
            records[0].rank = 99

    def test_default_store_api(self):
        records = retrieve_required_sections([ref()])
        self.assertEqual(records[0].identity, ("SOP-02", "1.0-demo", "late-escalate"))
        self.assertEqual(records[0].source_path, "sops/last_mile/late_delivery.md")

    def test_unavailable_identity_is_never_replaced_with_nearby_section(self):
        for missing in (ref(section="late-escalation"), ref(version="2.0-demo"), ref(policy="SOP-03")):
            with self.subTest(ref=missing), self.assertRaises(SectionNotFoundError):
                retrieve_required_sections([missing], store=self.store)
        with self.assertRaises(SectionNotFoundError):
            retrieve_required_sections([ref(), ref(section="late-escalation")], store=self.store)

    def test_mixed_versions_fail_across_assessments(self):
        result = {"assessments": [
            {"exception_type": "LATE_DELIVERY", "rule_ids": ["L-2"], "expected_sections": [ref()]},
            {"exception_type": "STALE_TRACKING", "rule_ids": ["S-2"], "expected_sections": [ref("SOP-03", "stale-escalate", "2.0-demo")]},
        ]}
        for operation in (collect_required_sections, lambda value: retrieve_case_sections(value, store=self.store)):
            with self.assertRaisesRegex(InvalidSectionReferenceError, "Mixed policy versions"):
                operation(result)

    def test_dedup_retains_each_requesting_assessment_and_rule_list(self):
        shared = ref("SOP-05", "common-evidence")
        result = {"assessments": [
            {"exception_type": "LATE_DELIVERY", "rule_ids": ["L-2"], "expected_sections": [ref(), shared, shared]},
            {"exception_type": "STALE_TRACKING", "rule_ids": ["S-2"], "expected_sections": [shared]},
            {"exception_type": "LATE_DELIVERY", "rule_ids": ["L-2"], "expected_sections": [shared]},
        ]}
        before = copy.deepcopy(result)
        required = collect_required_sections(result)
        records = retrieve_case_sections(result, store=self.store)
        self.assertEqual(len(required), 2)
        self.assertEqual([r.identity for r in records], [r.identity for r in required])
        self.assertEqual([r.requested_by for r in records], [r.requested_by for r in required])
        provenance = records[1].requested_by
        self.assertEqual([(p.assessment_index, p.exception_type, p.rule_ids) for p in provenance],
                         [(0, "LATE_DELIVERY", ("L-2",)), (1, "STALE_TRACKING", ("S-2",)), (2, "LATE_DELIVERY", ("L-2",))])
        self.assertEqual(result, before)

    def test_case_helper_uses_only_declared_references_not_business_fields(self):
        result = {"assessments": [{"exception_type": "LATE_DELIVERY", "rule_ids": ["L-2"],
                                   "expected_sections": [ref()]}]}
        baseline = retrieve_case_sections(result, store=self.store)
        changed = copy.deepcopy(result)
        changed.update(priority="HIGH", aggregate_action_state="READY_TO_ESCALATE", derived_facts={"hours_overdue": 99999},
                       input={"tracking_events": ["not consulted"]})
        changed["assessments"][0].update(result="UNKNOWN", escalation_eligible=False, action_state="NEEDS_REVIEW")
        self.assertEqual(retrieve_case_sections(changed, store=self.store), baseline)
        self.assertEqual(len(baseline), 1)
        self.assertFalse(any(r.identity[0] == "SOP-08" for r in baseline))
        changed["assessments"][0]["expected_sections"] = []
        self.assertEqual(retrieve_case_sections(changed, store=self.store), ())

    def test_explicitly_requested_audit_section_resolves_without_special_treatment(self):
        result = {"assessments": [{"exception_type": "LATE_DELIVERY", "rule_ids": [],
                                   "expected_sections": [ref("SOP-08", "decision-record")]}]}
        records = retrieve_case_sections(result, store=self.store)
        self.assertEqual([r.identity for r in records], [("SOP-08", "1.0-demo", "decision-record")])

    def test_synthetic_engine_result_round_trip_is_exact_and_nonmutating(self):
        from engine import triage_snapshot
        from test_engine import event, packet, seal
        for mode in ("normal", "multiple_ready", "unknown_history"):
            inputs = packet()
            if mode != "normal":
                inputs["input"]["shipments"][0]["promised_delivery_at"] = "2026-09-30T12:00:00Z"
            if mode == "multiple_ready":
                inputs["input"]["tracking_events"] = [
                    event("F1", "2026-09-28T08:00:00Z", "ATTEMPT_FAILED", "A"),
                    event("F2", "2026-09-28T09:00:00Z", "ATTEMPT_FAILED", "B")]
            elif mode == "unknown_history":
                inputs["input"]["history_declarations"][0]["history_complete"] = False
            actual = triage_snapshot(**seal(inputs))
            before = copy.deepcopy(actual)
            for result in actual["results"]:
                expected = list(dict.fromkeys(tuple(a[key] for key in ("policy_id", "version", "section_id"))
                                             for assessment in result["assessments"] for a in assessment["expected_sections"]))
                with self.subTest(mode=mode):
                    records = retrieve_case_sections(result, store=self.store)
                    self.assertEqual([r.identity for r in records], expected)
                    self.assertFalse(any(r.identity[0] == "SOP-08" for r in records))
                    for record in records:
                        self.assertTrue(record.requested_by)
                        for requester in record.requested_by:
                            assessment = result["assessments"][requester.assessment_index]
                            self.assertEqual(requester.exception_type, assessment["exception_type"])
                            self.assertEqual(requester.rule_ids, tuple(assessment["rule_ids"]))
            self.assertEqual(actual, before)

    def test_malformed_case_contract_fails_explicitly(self):
        for value in ({}, {"results": []}, {"assessments": [{}]},
                      {"assessments": [{"exception_type": "LATE_DELIVERY", "rule_ids": "L-2", "expected_sections": []}]},
                      {"assessments": [{"exception_type": "LATE_DELIVERY", "rule_ids": ["L-2"], "expected_sections": None}]}):
            with self.subTest(value=value), self.assertRaises(InvalidSectionReferenceError):
                retrieve_case_sections(value, store=self.store)
        self.assertEqual(collect_required_sections({"assessments": []}), ())
        self.assertEqual(retrieve_required_sections([], store=self.store), ())

    def test_clean_subprocess_needs_only_stdlib_and_public_runtime_artifacts(self):
        code = r'''
import builtins, json, pathlib, sys
sys.path.insert(0, sys.argv[1])
real_import = builtins.__import__
def offline_import(name, globals=None, locals=None, fromlist=(), level=0):
    if not level and name.split('.')[0] not in sys.stdlib_module_names | {'retrieval'}:
        raise AssertionError('Unexpected external/engine dependency: ' + name)
    return real_import(name, globals, locals, fromlist, level)
builtins.__import__ = offline_import
root = pathlib.Path(sys.argv[1]).resolve()
def audit(event, args):
    if event.startswith('socket.') or event == 'subprocess.Popen':
        raise AssertionError('Network/process access is not retrieval')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        value = str(args[0]).replace('\\', '/')
        if any(part in value for part in ('/evaluation/', '/examples/', '/artifacts/', '/kb/')):
            raise AssertionError('Non-runtime artifact read: ' + value)
sys.addaudithook(audit)
from retrieval import SectionStore, retrieve_required_sections
store = SectionStore.load()
records = retrieve_required_sections([('SOP-02','1.0-demo','late-escalate')], store=store)
assert (store.document_count, store.section_count) == (8, 25)
assert len(records) == 1
assert 'engine' not in sys.modules
print(json.dumps({'documents': store.document_count, 'sections': store.section_count}))
'''
        completed = subprocess.run([sys.executable, "-I", "-B", "-S", "-c", code, str(DOMAIN)],
                                   capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(completed.stdout), {"documents": 8, "sections": 25})


if __name__ == "__main__":
    unittest.main()
