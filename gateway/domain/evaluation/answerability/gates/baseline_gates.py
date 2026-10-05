"""Owner-specified Round-1 baselines. No benchmark, file, model or retrieval access."""
from dataclasses import dataclass
from fractions import Fraction
import re

from ..answerability_contracts import ALLOW, ABSTAIN, SUPPORTED, INSUFFICIENT, GateInput, GateOutput, require

IDS = (
    "CONTROL_ALWAYS_ALLOW",
    "CONTROL_ALWAYS_ABSTAIN",
    "BASELINE_RETRIEVAL_RESPONSE",
    "BASELINE_TOP1_LEXICAL_60",
    "BASELINE_TOP3_UNION_LEXICAL_60",
)
TOKEN_PATTERN = r"[a-z0-9]+"
STOPWORDS = frozenset("""a an the and or but if then is are was were be been being
to of in on for with at by from as it this that these those i me my we our you your
he she they them their do does did can could would should may might will what
which who whom whose how when where why""".split())


def tokens(text):
    return frozenset(re.findall(TOKEN_PATTERN, text.lower())) - STOPWORDS


@dataclass(frozen=True, slots=True)
class CoverageCounts:
    informative_question_token_count: int
    matched_token_count: int
    evidence_depth_used: int

    @property
    def coverage(self):
        n = self.informative_question_token_count
        return Fraction(self.matched_token_count, n) if n else Fraction(0)

    @property
    def passes(self):
        n = self.informative_question_token_count
        return n > 0 and self.evidence_depth_used > 0 and self.matched_token_count * 5 >= n * 3


def lexical_counts(value, depth):
    require(type(value) is GateInput, "GateInput only")
    require(depth in (1, 3), "only registered evidence depths")
    question = tokens(value.question)
    selected = value.evidence[:depth]
    evidence = frozenset().union(*(tokens(item.section_title + "\n" + item.body) for item in selected))
    return CoverageCounts(len(question), len(question & evidence), len(selected))


@dataclass(frozen=True, slots=True)
class BaselineGate:
    """The only retained attribute is a public algorithm identifier, never a case ID."""
    candidate_id: str

    def __post_init__(self):
        require(self.candidate_id in IDS, "unregistered candidate")

    def decide(self, value):
        require(type(value) is GateInput, "GateInput only")
        if self.candidate_id == IDS[0]:
            allow = True
        elif self.candidate_id == IDS[1]:
            allow = False
        elif self.candidate_id == IDS[2]:
            allow = bool(value.evidence)
        else:
            allow = lexical_counts(value, 1 if self.candidate_id == IDS[3] else 3).passes
        return GateOutput(ALLOW, SUPPORTED) if allow else GateOutput(ABSTAIN, INSUFFICIENT)
