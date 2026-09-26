"""Offline deterministic V1 domain engine; no application or evaluation imports."""
from .triage import triage_snapshot
from .validation import CanonicalInputError

__all__ = ["triage_snapshot", "CanonicalInputError"]
