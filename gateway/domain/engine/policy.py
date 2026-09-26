"""Load structured policy and verify only runtime contract artifacts."""
import hashlib
import json
import operator
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TYPES = ("LATE_DELIVERY", "STALE_TRACKING", "FAILED_ATTEMPT_ADDRESS")
COMMON = ("E-IDENTITY", "E-STATUS", "E-POLICY-CONTEXT")


def timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z") or "T" not in value:
        raise ValueError("Canonical UTC timestamp ending in Z required")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def section_key(section):
    return section["policy_id"], section["version"], section["section_id"]


def sections_unique(sections):
    return [dict(zip(("policy_id", "version", "section_id"), key))
            for key in sorted({section_key(s) for s in sections})]


@dataclass
class Policy:
    registry: dict
    schema: dict
    available_sections: set
    context_valid: bool

    @classmethod
    def load(cls, root=ROOT):
        root = Path(root)
        def read(name):
            return json.loads((root / name).read_text(encoding="utf-8"))
        hashes = read("policy/artifact_manifest.json")["sha256"]
        def intact(name):
            path = root / name
            return (path.resolve().is_relative_to(root.resolve()) and path.is_file()
                    and hashlib.sha256(path.read_bytes()).hexdigest() == hashes.get(name))
        registry = read("policy/policy_registry.json")
        schema = read("schemas/contracts.schema.json")
        available = {(sop["policy_id"], registry["bundle_version"], section)
                     for sop in registry["sops"] if intact(sop["path"])
                     for section in sop["section_ids"]}
        return cls(registry, schema, available,
                   intact("policy/policy_registry.json") and intact("schemas/contracts.schema.json"))

    @property
    def rules(self):
        return {r["rule_id"]: r for r in self.registry["rules"]}

    @property
    def requirements(self):
        return {r["requirement_id"]: r for r in self.registry["evidence_requirements"]}

    def threshold(self, name):
        entry = self.registry["thresholds"][name]
        value = entry["value"]
        return timedelta(hours=value) if entry["unit"] == "elapsed_hours" else value

    def meets(self, name, value):
        entry = self.registry["thresholds"][name]
        ops = {">": operator.gt, ">=": operator.ge, "<": operator.lt,
               "<=": operator.le, "==": operator.eq, "enabled": operator.eq}
        return ops[entry["operator"]](value, self.threshold(name))

    def dependencies(self, rules):
        return sorted({e for r in rules for e in self.rules[r]["decision_dependency_ids"]})

    def sections(self, rules, requirements=(), failure=False):
        role = "failure_guidance_sections" if failure else "support_sections"
        entries = [self.rules[r] for r in rules] + [self.requirements[e] for e in requirements]
        return sections_unique([s for e in entries for s in e[role]])

    def active(self, reference, as_of):
        return (self.context_valid and isinstance(reference, dict)
                and reference == {k: self.registry[k] for k in ("bundle_id", "bundle_version")}
                and as_of is not None and timestamp(self.registry["effective_from"]) <= as_of
                and (self.registry["effective_to"] is None or as_of < timestamp(self.registry["effective_to"])))
