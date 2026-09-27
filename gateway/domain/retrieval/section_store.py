"""Immutable exact section index over checksum-verified domain artifacts only."""
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from types import MappingProxyType

DOMAIN = Path(__file__).resolve().parents[1]
IDENTITY_FIELDS = ("policy_id", "version", "section_id")
NOTICE = "Fictional demo operating policy. Not real carrier or industry standards."


class RetrievalError(Exception):
    """Base class for explicit retrieval failures; no substitute policy is returned."""


class SectionIntegrityError(RetrievalError):
    """The complete active corpus could not be verified and indexed."""


class InvalidSectionReferenceError(RetrievalError, ValueError):
    """A request is not an exact identity or contains mixed versions."""


class SectionNotFoundError(RetrievalError, LookupError):
    def __init__(self, identities):
        self.identities = tuple(identities)
        super().__init__(f"Required policy sections unavailable: {self.identities!r}")


def section_identity(reference):
    """Accept an exact three-key mapping or (policy_id, version, section_id) tuple."""
    if isinstance(reference, Mapping) and set(reference) == set(IDENTITY_FIELDS):
        identity = tuple(reference[key] for key in IDENTITY_FIELDS)
    elif isinstance(reference, tuple) and len(reference) == 3:
        identity = reference
    else:
        raise InvalidSectionReferenceError("An exact policy_id/version/section_id identity is required")
    if not all(isinstance(value, str) and value and value == value.strip() for value in identity):
        raise InvalidSectionReferenceError("Identity components must be nonempty, unpadded strings")
    return identity


def _requested_identities(references):
    if isinstance(references, (str, bytes, Mapping)):
        raise InvalidSectionReferenceError("Provide an iterable of exact section identities")
    try:
        identities = tuple(section_identity(ref) for ref in references)
    except TypeError as exc:
        raise InvalidSectionReferenceError("Provide an iterable of exact section identities") from exc
    if len({identity[1] for identity in identities}) > 1:
        raise InvalidSectionReferenceError("Mixed policy versions are not allowed in one retrieval result")
    return identities


def section_content_hash(policy_id, version, section_id, section_title, body):
    """SHA-256 of the specified UTF-8 payload; only line endings are normalized."""
    payload = "\n".join((policy_id, version, section_id, section_title, body))
    return hashlib.sha256(payload.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SectionRecord:
    policy_id: str
    version: str
    section_id: str
    title: str
    section_title: str
    exception_types: tuple[str, ...]
    rule_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    effective_from: str
    effective_to: str | None
    demo_policy: bool
    source_path: str
    content_hash: str
    text: str

    @property
    def identity(self):
        return self.policy_id, self.version, self.section_id


@dataclass(frozen=True, slots=True)
class ResolvedSection:
    section: SectionRecord
    request_indices: tuple[int, ...]

    @property
    def identity(self):
        return self.section.identity


def _require(condition, message):
    if not condition:
        raise SectionIntegrityError(message)


def _json(raw, label):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result
    def invalid_constant(value):
        raise SectionIntegrityError(f"{label}: invalid JSON constant {value}")
    try:
        result = json.loads(raw, object_pairs_hook=unique_keys, parse_constant=invalid_constant)
        _require(isinstance(result, dict), f"{label}: JSON object required")
        return result
    except (ValueError, UnicodeError) as exc:
        raise SectionIntegrityError(f"{label}: malformed JSON metadata: {exc}") from exc


def _strings(values, label, *, nonempty=False):
    _require(isinstance(values, list) and all(isinstance(v, str) and v.strip() for v in values),
             f"{label}: string array required")
    _require(len(values) == len(set(values)), f"{label}: duplicate values")
    _require(not nonempty or bool(values), f"{label}: empty inventory")
    return tuple(values)


def _parse_sop(raw, label):
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    blocks = list(re.finditer(r"^```json\n(.*?)^```[ \t]*(?:\n|$)", text, re.M | re.S))
    _require(len(blocks) == 1, f"{label}: exactly one JSON metadata block required")
    metadata = _json(blocks[0].group(1), label)
    _require(re.match(r"\A# [^\n]+\n", text) is not None, f"{label}: document heading missing")
    _require(NOTICE in text[:blocks[0].start()], f"{label}: fictional policy notice missing")
    # Locate stable H2 headings outside fenced code; keep nested Markdown intact.
    headings, offset, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        content = line.removesuffix("\n")
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", content)
        if fence is not None:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
        elif marker:
            fence = (marker[1][0], len(marker[1]))
        elif re.match(r"^ {0,3}##(?:[ \t]|$)", content):
            match = re.fullmatch(r"## ([a-z][a-z0-9-]*)", content)
            _require(match is not None, f"{label}: invalid stable section heading {content!r}")
            headings.append((match[1], offset, offset + len(line)))
        offset += len(line)
    _require(fence is None, f"{label}: unclosed Markdown fence")
    _require(headings and blocks[0].end() <= headings[0][1], f"{label}: metadata must precede sections")
    declared = metadata["sections"]
    _require(isinstance(declared, list) and all(isinstance(s, dict) for s in declared), f"{label}: invalid section metadata")
    _require([h[0] for h in headings] == [s["section_id"] for s in declared], f"{label}: section headings/metadata differ")
    bodies = []
    for index, (_, _, start) in enumerate(headings):
        end = headings[index + 1][1] if index + 1 < len(headings) else len(text)
        body = text[start:end]
        _require(bool(body.strip()), f"{label}: empty section body")
        bodies.append(body)
    return metadata, bodies


def _load_sections(root):
    manifest = _json((root / "policy/artifact_manifest.json").read_bytes(), "artifact manifest")
    _require(manifest["algorithm"] == "sha256" and isinstance(manifest["sha256"], dict), "Invalid artifact manifest")
    hashes = manifest["sha256"]

    def verified(name):
        _require(isinstance(name, str) and not PurePosixPath(name).is_absolute(), "Invalid artifact path")
        path = root / name
        _require(path.resolve().is_relative_to(root), f"Artifact path escapes root: {name}")
        _require(path.is_file(), f"Missing artifact: {name}")
        raw = path.read_bytes()
        _require(hashlib.sha256(raw).hexdigest() == hashes.get(name), f"Artifact checksum mismatch: {name}")
        return raw

    registry = _json(verified("policy/policy_registry.json"), "policy registry")
    schema = _json(verified("schemas/contracts.schema.json"), "contract schema")
    version = registry["bundle_version"]
    _require(isinstance(version, str) and bool(version.strip()), "Invalid bundle version")
    _require(registry["demo_policy"] is True, "Registry demo policy label missing")
    start = datetime.fromisoformat(registry["effective_from"].replace("Z", "+00:00"))
    end = registry["effective_to"]
    _require(start.tzinfo is not None, "Registry effective interval requires timezone")
    if end is not None:
        finish = datetime.fromisoformat(end.replace("Z", "+00:00"))
        _require(finish.tzinfo is not None and finish > start, "Invalid registry effective interval")
    allowed_types = set(schema["$defs"]["exception_type"]["enum"])
    sops = registry["sops"]
    _require(isinstance(sops, list) and bool(sops), "Registry SOP inventory missing")
    _strings([s["policy_id"] for s in sops], "SOP identities", nonempty=True)
    paths = _strings([s["path"] for s in sops], "SOP paths", nonempty=True)
    _require(all(PurePosixPath(p).parent == PurePosixPath("sops/last_mile") and p.endswith(".md") for p in paths),
             "Registry SOP paths must belong to sops/last_mile")
    actual_paths = {p.relative_to(root).as_posix() for p in (root / "sops/last_mile").rglob("*.md")}
    _require(actual_paths == set(paths), "SOP document inventory differs from registry")
    manifest_paths = {p for p in hashes if p.startswith("sops/last_mile/")}
    _require(manifest_paths == set(paths), "Manifest SOP inventory differs from registry")
    sections = {}
    for sop in sops:
        label = sop["path"]
        # Verify raw bytes BEFORE parsing/indexing. All records derive from these bytes.
        meta, bodies = _parse_sop(verified(label), label)
        _require(meta["policy_id"] == sop["policy_id"], f"{label}: policy ID mismatch")
        _require(meta["version"] == version, f"{label}: SOP version mismatch")
        _require(meta["demo_policy"] is True, f"{label}: demo policy label missing")
        _require(meta["effective_from"] == registry["effective_from"] and meta["effective_to"] == end,
                 f"{label}: effective interval mismatch")
        _require(isinstance(meta["title"], str) and meta["title"].strip(), f"{label}: document title missing")
        coverage = _strings(meta["exception_types"], f"{label} exception types", nonempty=True)
        _require(set(coverage) <= allowed_types, f"{label}: unknown exception coverage")
        declared_ids = _strings(sop["section_ids"], f"{label} registry sections", nonempty=True)
        _require(tuple(s["section_id"] for s in meta["sections"]) == declared_ids, f"{label}: SOP section inventory mismatch")
        for section, body in zip(meta["sections"], bodies):
            identity = (meta["policy_id"], version, section["section_id"])
            _require(identity not in sections, f"Duplicate section identity: {identity}")
            title = section["section"]
            _require(isinstance(title, str) and title.strip(), f"{label}: section title missing")
            rule_ids = _strings(section["rule_ids"], f"{identity} rule IDs")
            requirement_ids = _strings(section["requirement_ids"], f"{identity} requirement IDs")
            sections[identity] = SectionRecord(*identity, meta["title"], title, coverage, rule_ids, requirement_ids,
                meta["effective_from"], end, True, label, section_content_hash(*identity, title, body), body)
    # Validate both directions of section backlinks; do not select rules or evaluate facts.
    for inventory, id_field, backlink, enum in (
        (registry["rules"], "rule_id", "rule_ids", "rule_id"),
        (registry["evidence_requirements"], "requirement_id", "requirement_ids", "requirement_id"),
    ):
        ids = _strings([entry[id_field] for entry in inventory], f"Registry {id_field}", nonempty=True)
        _require(set(ids) == set(schema["$defs"][enum]["enum"]), f"Registry {id_field} inventory mismatch")
        declared_backlinks = {identity: set() for identity in sections}
        for entry in inventory:
            refs = entry["support_sections"] + entry["failure_guidance_sections"]
            targets = _requested_identities(refs)
            _require(bool(targets) and len(targets) == len(set(targets)), f"Invalid section mappings for {entry[id_field]}")
            for identity in targets:
                _require(identity in sections, f"Registry section unavailable: {identity}")
                declared_backlinks[identity].add(entry[id_field])
        for identity, section in sections.items():
            _require(set(getattr(section, backlink)) == declared_backlinks[identity], f"Inconsistent {backlink} backlinks: {identity}")
    _require(len(sections) == sum(len(s["section_ids"]) for s in sops), "Section inventory differs from registry")
    return sections


@dataclass(frozen=True, slots=True)
class SectionStore:
    _sections: Mapping

    def __post_init__(self):
        object.__setattr__(self, "_sections", MappingProxyType(dict(self._sections)))

    @classmethod
    def load(cls, root=DOMAIN):
        """Load one verified bundle atomically; any defect prevents returning a store."""
        try:
            return cls(_load_sections(Path(root).resolve()))
        except SectionIntegrityError:
            raise
        except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise SectionIntegrityError(f"Unable to load SOP section corpus: {exc}") from exc

    @property
    def sections(self):
        return tuple(self._sections.values())

    @property
    def document_count(self):
        return len({(s.policy_id, s.version) for s in self.sections})

    @property
    def section_count(self):
        return len(self._sections)

    @property
    def versions(self):
        return tuple(sorted({identity[1] for identity in self._sections}))

    def get(self, *, policy_id, version, section_id):
        identity = section_identity((policy_id, version, section_id))
        if identity not in self._sections:
            raise SectionNotFoundError((identity,))
        return self._sections[identity]

    def resolve_many(self, section_refs):
        """First-request order, deduplicated, with all zero-based request positions."""
        identities = _requested_identities(section_refs)
        positions = {}
        for index, identity in enumerate(identities):
            positions.setdefault(identity, []).append(index)
        missing = tuple(identity for identity in positions if identity not in self._sections)
        if missing:
            raise SectionNotFoundError(missing)
        return tuple(ResolvedSection(self._sections[identity], tuple(indices)) for identity, indices in positions.items())
