"""V2 preregistration: strict rank interface, no decoder implementation or inference."""
from copy import deepcopy
from dataclasses import asdict, dataclass
import json

from ..answerability_contracts import ContractError, GateInput, GateOutput
from . import semantic_gate as v1

CANDIDATE_ID = 'SEMANTIC_MATERIAL_SUPPORT_V2'
CANDIDATE_STATUS = 'PRE_REGISTERED_NOT_EVALUATED'
DECODER_STATUS = 'CONSTRAINED_DECODER_IMPLEMENTATION_REQUIRED'
STRUCTURED_OUTPUT_MODE = 'JSON_SCHEMA_CONSTRAINED_DECODING'
MAX_MATERIAL_ASKS = 8
MAX_EVIDENCE_RANK = 10


def _make_schema():
    # Retain the exact V1 semantic oneOf rules. Only the raw interface changes.
    schema = deepcopy(v1.RAW_ASSESSMENT_SCHEMA)
    asks = schema['properties']['material_asks']
    asks['maxItems'] = MAX_MATERIAL_ASKS
    item = asks['items']
    del item['properties']['supporting_section_ids']
    item['required'] = ['ask', 'support_status', 'supporting_evidence_ranks']
    item['properties']['supporting_evidence_ranks'] = {
        'type': 'array', 'uniqueItems': True, 'maxItems': MAX_EVIDENCE_RANK,
        'items': {'type': 'integer', 'minimum': 1, 'maximum': MAX_EVIDENCE_RANK},
    }
    item['allOf'] = [{
        'if': {'properties': {'support_status': {'const': 'SUPPORTED'}}},
        'then': {'properties': {'supporting_evidence_ranks': {'minItems': 1}}},
        'else': {'properties': {'supporting_evidence_ranks': {'maxItems': 0}}},
    }]
    return schema


RAW_ASSESSMENT_SCHEMA_V2 = _make_schema()
SEMANTIC_INSTRUCTIONS = v1.SYSTEM_INSTRUCTIONS.split('Return one JSON object only,', 1)[0]
INTERFACE_INSTRUCTIONS = '''Return only the required structured JSON object, without commentary, confidence, or an answer.
The generation interface requires token-level JSON-schema constraints; prompt-only JSON instructions are not the structural enforcement mechanism.
Include between one and eight material_asks. This maximum bounds malformed output size; never omit a material ask to fit the interface bound. Each ask is a concise audit statement, not an extended reasoning narrative.
Each ask must contain ask, support_status, and supporting_evidence_ranks. Use evidence ranks exactly as supplied. Do not generate policy/version/section identifier strings as references.
For SUPPORTED asks, cite one or more supplied evidence ranks. Multiple supplied sections may jointly support one ask. For UNSUPPORTED or CONTEXT_UNRESOLVED asks, supporting_evidence_ranks must be an empty array.
Ranks must be JSON integers, between 1 and 10 inclusive and no larger than the actual supplied evidence count. Within each ask they must be unique and strictly ascending. Do not invent ranks.
The deterministic adapter maps each selected rank only to that exact supplied section's canonical identity. It does not retrieve, guess, replace, or repair evidence or semantic decisions.
Use the complete supplied evidence set in its original rank order, up to ten sections; do not truncate it to a smaller rank depth.
All keys, enums, rank membership, status/reference pairing and semantic decision consistency are validated strictly after generation. Invalid output is a candidate error, never an automatic ABSTAIN or a reason to retry for quality.
'''


def canonical_json(value):
    return v1.canonical_json(value)


def canonical_prompt():
    return (SEMANTIC_INSTRUCTIONS + INTERFACE_INSTRUCTIONS
            + '\nRequired V2 JSON schema (actual rank membership and ascending order are also checked by the adapter):\n'
            + canonical_json(RAW_ASSESSMENT_SCHEMA_V2).decode('utf-8'))


class SemanticOutputErrorV2(v1.SemanticOutputError):
    """Invalid scientific output; never repaired or converted into ABSTAIN."""


class ConstrainedDecoderImplementationRequired(ContractError):
    """No constrained decoder is selected, qualified or callable in A2."""


def _require(condition, message):
    if not condition:
        raise SemanticOutputErrorV2(message)


def _keys(value, expected, label):
    _require(type(value) is dict and set(value) == set(expected), 'Invalid ' + label + ' keys')


def _input(value):
    # Reuse the frozen exact-type and deep contract validation, not a benchmark loader.
    v1._input(value)


def schema_for_input(value):
    """A fresh per-request schema; no truncation or modification of input evidence."""
    _input(value)
    schema = deepcopy(RAW_ASSESSMENT_SCHEMA_V2)
    ranks = schema['properties']['material_asks']['items']['properties']['supporting_evidence_ranks']
    count = len(value.evidence)
    ranks['maxItems'] = count
    # With no evidence, maxItems=0 makes every nonempty rank list impossible.
    ranks['items']['maximum'] = max(1, count)
    return schema


def build_messages(value):
    """Copy only the unchanged B1.1 allowlist; preserve all supplied fields and ranks."""
    _input(value)
    frozen_messages = v1.build_messages(value)
    return ({'role': 'system', 'content': canonical_prompt()}, frozen_messages[1])


def build_request(value):
    """Deterministic request specification only; this does not authorize execution."""
    return {'messages': build_messages(value), 'response_schema': schema_for_input(value),
            'structured_output_mode': STRUCTURED_OUTPUT_MODE, 'decoder_status': DECODER_STATUS}


@dataclass(frozen=True, slots=True)
class RankBinding:
    material_ask_index: int
    evidence_rank: int
    canonical_identity: tuple[str, str, str]
    canonical_reference: str


@dataclass(frozen=True, slots=True)
class CanonicalizedAssessment:
    assessment: v1.SemanticAssessment
    rank_bindings: tuple[RankBinding, ...]

    def gate_output(self):
        return self.assessment.gate_output()

    def canonical_bytes(self):
        return canonical_json(asdict(self.assessment))

    def audit_bytes(self):
        return canonical_json(asdict(self))


def canonicalize(raw, value):
    """Validate raw V2 JSON, map exact ranks, then apply the frozen V1 consistency parser."""
    _input(value)
    _require(type(raw) in (str, bytes), 'Raw JSON text or UTF-8 bytes required')

    def unique(pairs):
        result = {}
        for key, item in pairs:
            _require(key not in result, 'Duplicate JSON key')
            result[key] = item
        return result

    def invalid_constant(constant):
        raise SemanticOutputErrorV2('Nonfinite JSON constant')

    try:
        text = raw.decode('utf-8') if type(raw) is bytes else raw
        parsed = json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant)
    except (UnicodeError, ValueError) as exc:
        raise SemanticOutputErrorV2('Invalid strict V2 JSON output') from exc
    _keys(parsed, ('material_asks', 'policy_context_status', 'decision', 'reason_code'), 'assessment')
    asks = parsed['material_asks']
    _require(type(asks) is list and 1 <= len(asks) <= MAX_MATERIAL_ASKS, 'One to eight material asks required')
    for key, choices in (
        ('policy_context_status', ('RESOLVED', 'UNRESOLVED')),
        ('decision', ('ALLOW', 'ABSTAIN')),
        ('reason_code', ('SUPPORTED_BY_ACTIVE_POLICY', 'INSUFFICIENT_POLICY_SUPPORT', 'UNRESOLVED_POLICY_CONTEXT')),
    ):
        _require(type(parsed[key]) is str and parsed[key] in choices, 'Invalid ' + key)
    supplied = {item.rank: item for item in value.evidence}
    canonical_asks, bindings = [], []
    for index, ask in enumerate(asks):
        _keys(ask, ('ask', 'support_status', 'supporting_evidence_ranks'), 'material ask')
        _require(type(ask['ask']) is str and bool(ask['ask'].strip()), 'Nonempty ask text required')
        status, ranks = ask['support_status'], ask['supporting_evidence_ranks']
        _require(type(status) is str and status in ('SUPPORTED', 'UNSUPPORTED', 'CONTEXT_UNRESOLVED'), 'Invalid support status')
        _require(type(ranks) is list, 'Rank array required')
        _require(all(type(rank) is int and 1 <= rank <= MAX_EVIDENCE_RANK for rank in ranks), 'Ranks must be exact integers 1 through 10')
        _require(all(left < right for left, right in zip(ranks, ranks[1:])), 'Ranks must be unique and strictly ascending')
        _require(all(rank in supplied for rank in ranks), 'Rank absent from exact supplied GateInput')
        _require(bool(ranks) if status == 'SUPPORTED' else not ranks, 'Status/rank references inconsistent')
        references = []
        for rank in ranks:
            section = supplied[rank]
            reference = v1.section_reference(section)
            references.append(reference)
            bindings.append(RankBinding(index, rank, section.identity, reference))
        canonical_asks.append({'ask': ask['ask'], 'support_status': status, 'supporting_section_ids': references})
    canonical = {'material_asks': canonical_asks, 'policy_context_status': parsed['policy_context_status'],
                 'decision': parsed['decision'], 'reason_code': parsed['reason_code']}
    # No semantic decision or text is altered. The same frozen rules remain authoritative.
    assessment = v1.parse_assessment(canonical_json(canonical), value)
    return CanonicalizedAssessment(assessment, tuple(bindings))


def parse_assessment(raw, value):
    return canonicalize(raw, value).assessment


def adapt_response(raw, value) -> GateOutput:
    return canonicalize(raw, value).gate_output()


class SemanticGateV2:
    """Non-executable candidate; no model/provider object or richer benchmark retained."""
    __slots__ = ()

    def decide(self, value: GateInput):
        _input(value)
        raise ConstrainedDecoderImplementationRequired(DECODER_STATUS)
