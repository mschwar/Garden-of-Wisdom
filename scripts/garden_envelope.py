#!/usr/bin/env python3
"""The `garden.candidate-envelope/1` serialized form, its deterministic validator, and the
bridge that stores a valid envelope through W1.1's store of record.

Usage (diagnostic, read-only -- this is NOT an intake surface; W1.3 owns that):
    python3 scripts/garden_envelope.py serialize --envelope FILE
    python3 scripts/garden_envelope.py validate  --envelope FILE [--captures FILE] [--rule N]

W1.2 of the Garden corpus program (`docs/program/W1_DECOMPOSITION.md` section "W1.2 - Candidate
envelope intake contract + validator"). The contract is `docs/program/CANDIDATE_ENVELOPE.md`:
21 required fields, 6 validation rules, the sentinel vocabulary `unknown`/`und`/`none`/
`legacy-import` (`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md`).

What this module provides:

  * **The serialized form.** One envelope is one canonical JSON object: keys sorted, UTF-8,
    compact separators `(",", ":")`, `ensure_ascii=False`, and `allow_nan=False` so a value
    the canonical form cannot represent is a hard failure rather than a silent `Infinity`/
    `NaN` in the text. It is a pure function of the envelope, so `serialize -> parse ->
    serialize` is byte-identical and two envelopes that are equal as objects serialize
    identically whatever their key insertion order.

  * **A validator for rules 1-6, each violation carrying its rule id** (`rule-1`..`rule-6`,
    the numbering of `CANDIDATE_ENVELOPE.md`). No traceback on broken input: a non-object
    envelope is a `rule-1` violation, not an exception.

  * **Sentinel handling.** A sentinel is a *value*, never absence and never an empty string.
    Each field that the contract gives a sentinel has its own declared set; a sentinel used on
    a field the contract does not give it (`language: "unknown"`) is a rule-1 violation, and
    an empty string is never treated as a sentinel. Nothing here ever rewrites a sentinel to
    `""` or omits a field because its value is a sentinel.

  * **Store integration.** `store_capture` writes the immutable capture row from an
    envelope's `captured_*` fields; `store_envelope` validates all six rules against the
    store's own captures (rule 5 reads the real capture record) and then writes the candidate
    and its duplicate hints through `scripts/garden_store.py`. `read_envelope` reconstructs
    the envelope's required fields from the store. States are never passed to the store by
    this module: `garden_store.add_candidate` fixes them at their intake values, which is the
    same rule 3 the validator enforces, so the two cannot be pulled apart (`W1_DECOMPOSITION.md`
    cross-unit rule; `W1_1_STORAGE_AND_SCHEMA.md` section 3).

Deliberately absent (out of W1.2 scope): any source adapter, any discovery, any intake CLI
surface (W1.3), any decision-making field or transition, any normalization or duplicate-hint
algorithm (W1.4), any review/UI surface (W1.5), any write to `quotes.csv` / `sources.csv`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# One vocabulary, taken from the store module (which took it from STATE_MODEL.md), so the
# envelope vocabulary and the schema vocabulary cannot drift apart.
from garden_store import (  # noqa: E402
    CAPTURE_METHODS,
    CORPUS_STATES,
    CURATION_STATES,
    DIMENSIONS,
    HINT_KINDS,
    INTAKE_STATES,
    RESEARCH_STATES,
    SENTINELS,
    STATE_COLUMNS,
    WORK_STATES,
)

SCHEMA_KEY = "garden.candidate-envelope/1"

#: The 21 required fields, in the order `CANDIDATE_ENVELOPE.md`'s table lists them.
REQUIRED_FIELDS = (
    "intake_schema_version",
    "capture_id",
    "captured_text",
    "captured_attribution",
    "captured_citation",
    "capture_method",
    "captured_at",
    "captured_by",
    "language",
    "source_reference",
    "context_notes",
    "raw_artifact_ref",
    "candidate_text",
    "candidate_author",
    "candidate_source_ref",
    "normalization_notes",
    "duplicate_hints",
    "curation_state",
    "research_state",
    "corpus_state",
    "work_state",
)
REQUIRED_STRING_FIELDS = tuple(f for f in REQUIRED_FIELDS if f != "duplicate_hints")
REQUIRED_ARRAY_FIELDS = ("duplicate_hints",)

#: Optional fields (`CANDIDATE_ENVELOPE.md` section "Optional fields"). They are carried,
#: serialized and round-tripped like any other field; the store has no columns for them yet
#: (recorded as discovered work, see docs/program/W1_2_ENVELOPE_VALIDATOR.md section 6).
OPTIONAL_FIELDS = (
    "external_id",
    "provenance_chain",
    "attribution_chain",
    "placeholder_markers",
    "source_link_state",
    "locator",
    "container",
    "period_hint",
    "rights_note",
)

#: The states that are ALSO optional-field-shaped and therefore must not be rejected.
STATE_FIELDS = ("curation_state", "research_state", "corpus_state", "work_state")

#: Which sentinel each field is allowed to carry, straight from the contract prose.
#: A field NOT listed here carries no sentinel restriction (its value is free text).
#: `normalization_notes` is listed with an EMPTY set on purpose: "we did not touch it" must be
#: an assertion (`identical to capture`), so a bare sentinel is not a valid normalization note.
#: (`capture_method` takes `legacy-import` as an enum VALUE, not as this sentinel; that overlap
#: is intentional in the contract and is why it is not listed here.)
SENTINEL_ALLOWED = {
    "captured_attribution": ("unknown",),
    "captured_citation": ("none",),
    "captured_by": ("legacy-import",),
    "language": ("und",),
    "source_reference": ("none",),
    "context_notes": ("none",),
    "raw_artifact_ref": ("none",),
    "candidate_author": ("unknown",),
    "candidate_source_ref": ("none",),
    "normalization_notes": (),
}

#: Rule ids, exactly the numbering of `CANDIDATE_ENVELOPE.md` section "Validation rules".
RULE_IDS = ("rule-1", "rule-2", "rule-3", "rule-4", "rule-5", "rule-6")

#: The capture fields an envelope carries; used by `store_capture`.
CAPTURE_FIELDS = (
    "capture_id",
    "captured_text",
    "captured_attribution",
    "captured_citation",
    "capture_method",
    "captured_at",
    "captured_by",
    "language",
    "source_reference",
    "context_notes",
    "raw_artifact_ref",
)


class EnvelopeError(Exception):
    """A refusal this module is designed to make (broken envelope or broken input, not a bug)."""


class Violation:
    """One broken check, always reporting the rule id that broke."""

    __slots__ = ("rule", "message")

    def __init__(self, rule: str, message: str):
        self.rule = rule
        self.message = message

    def __str__(self) -> str:
        return f"[{self.rule}] {self.message}"


# -- the serialized form -------------------------------------------------------------------


def serialize(envelope: dict) -> str:
    """The canonical serialized form of one envelope, as a `str`.

    Canonical means: `sort_keys=True` (so key insertion order cannot change the bytes),
    `ensure_ascii=False` (UTF-8 must survive as UTF-8, not as escapes), compact separators, and
    `allow_nan=False` (a value the canonical form cannot represent -- e.g. an `Infinity` a JSON
    reader produced from `1e999` -- is a refusal, not text nobody can re-parse).
    """
    if not isinstance(envelope, dict):
        raise EnvelopeError(f"an envelope must be a JSON object, got {type(envelope).__name__}")
    try:
        return json.dumps(
            envelope,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (ValueError, TypeError) as exc:
        raise EnvelopeError(
            f"the envelope is not representable in the canonical serialized form: "
            f"{type(exc).__name__}: {exc}"
        ) from None


def serialize_bytes(envelope: dict) -> bytes:
    """The canonical serialized form encoded UTF-8 -- what would be written to a file."""
    return serialize(envelope).encode("utf-8")


def parse(text: str | bytes | bytearray) -> dict:
    """Parse the serialized form back into an envelope object. Refuses cleanly, never raises JSON's."""
    if isinstance(text, (bytes, bytearray)):
        try:
            text = bytes(text).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EnvelopeError(f"serialized envelope is not valid UTF-8: {exc}") from None
    if not isinstance(text, str):
        raise EnvelopeError(f"serialized envelope must be text, got {type(text).__name__}")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnvelopeError(f"serialized envelope is not valid JSON: {exc.msg}") from None
    if not isinstance(obj, dict):
        raise EnvelopeError("serialized envelope is not a JSON object")
    return obj


# -- sentinels -----------------------------------------------------------------------------


def is_sentinel(value: object) -> bool:
    return isinstance(value, str) and value in SENTINELS


def sentinel_allowed(field: str, value: str) -> bool:
    """True if `value` is a sentinel the contract declares for `field`."""
    return value in SENTINEL_ALLOWED.get(field, ())


# -- validation ----------------------------------------------------------------------------


def _iso8601_with_offset(value: str) -> bool:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(candidate).tzinfo is not None
    except ValueError:
        return False


def validate(
    envelope: object,
    captures: dict | None = None,
    rules: tuple[str, ...] = RULE_IDS,
) -> list[Violation]:
    """Run the requested rules over one envelope. Returns every violation, each with its rule id.

    `captures` maps `capture_id` -> the capture record's `captured_text`, for rule 5. Passing
    `None` is NOT "skip rule 5": rule 5 reports that no capture record was supplied, because a
    check that silently does not run is worse than no check. Pass `rules=(...)` to run a subset.
    """
    if not isinstance(envelope, dict):
        return [
            Violation(
                "rule-1",
                f"an envelope must be a JSON object, got {type(envelope).__name__}"
                f"{' (' + repr(envelope)[:60] + ')' if not isinstance(envelope, (list, int, float, bool)) else ''}",
            )
        ]
    violations: list[Violation] = []
    if "rule-1" in rules:
        violations += _rule1(envelope)
    if "rule-2" in rules:
        violations += _rule2(envelope)
    if "rule-3" in rules:
        violations += _rule3(envelope)
    if "rule-4" in rules:
        violations += _rule4(envelope)
    if "rule-5" in rules:
        violations += _rule5(envelope, captures)
    if "rule-6" in rules:
        violations += _rule6(envelope)
    return violations


def _rule1(env: dict) -> list[Violation]:
    """All required fields present; values well-typed and non-empty; enums match vocabulary.

    An empty string is NOT a sentinel: absence must be the explicit sentinel the contract
    declares for that field, never `""` and never a missing key.
    """
    out: list[Violation] = []

    def bad(message: str) -> None:
        out.append(Violation("rule-1", message))

    for field in REQUIRED_FIELDS:
        if field not in env:
            bad(
                f"required field {field!r} is missing; absence must be an explicit sentinel "
                f"(one of {list(SENTINELS)}), never a missing field"
            )
    for field in REQUIRED_STRING_FIELDS:
        if field in env and not isinstance(env[field], str):
            bad(f"{field!r} must be a string, got {type(env[field]).__name__}")
    for field in REQUIRED_ARRAY_FIELDS:
        if field in env and not isinstance(env[field], list):
            bad(f"{field!r} must be an array, got {type(env[field]).__name__}")

    version = env.get("intake_schema_version")
    if isinstance(version, str) and version != SCHEMA_KEY:
        bad(f"intake_schema_version must be {SCHEMA_KEY!r}, got {version!r}")

    method = env.get("capture_method")
    if isinstance(method, str) and method not in CAPTURE_METHODS:
        bad(f"capture_method {method!r} is outside the contract vocabulary {list(CAPTURE_METHODS)}")

    for field in STATE_FIELDS:
        value = env.get(field)
        dimension = field[: -len("_state")]
        if isinstance(value, str) and value not in DIMENSIONS[dimension]:
            bad(
                f"{field} {value!r} is outside the {dimension} vocabulary "
                f"{list(DIMENSIONS[dimension])} (docs/program/STATE_MODEL.md)"
            )

    # Non-empty. `captured_text` is deliberately excluded here: its non-emptiness is rule 2's
    # own check, and giving one defect one rule keeps a failing fixture unambiguous.
    for field in REQUIRED_STRING_FIELDS:
        if field == "captured_text" or field not in env:
            continue
        value = env[field]
        if isinstance(value, str) and value == "":
            bad(
                f"{field!r} is empty; a sentinel ({list(SENTINELS)}) is not an empty string, "
                f"and absence is never a missing field"
            )

    captured_at = env.get("captured_at")
    if isinstance(captured_at, str) and not _iso8601_with_offset(captured_at):
        bad(f"captured_at {captured_at!r} is not ISO-8601 with an offset (e.g. 2026-09-12T09:14:11-06:00)")

    for field, allowed in SENTINEL_ALLOWED.items():
        value = env.get(field)
        if isinstance(value, str) and is_sentinel(value) and value not in allowed:
            allowed_note = (
                "this field must carry a real value asserting what was done"
                if not allowed
                else f"the contract declares {list(allowed)} for it"
            )
            bad(
                f"sentinel {value!r} is not declared for {field!r}: {allowed_note}"
            )
    return out


def _rule2(env: dict) -> list[Violation]:
    """`captured_text` non-empty after no transformation whatsoever."""
    text = env.get("captured_text")
    if isinstance(text, str) and text == "":
        return [
            Violation(
                "rule-2",
                "captured_text is empty; the capture is stored verbatim and never trimmed, "
                "so leading/trailing whitespace is legal but no text at all is not",
            )
        ]
    return []


def _rule3(env: dict) -> list[Violation]:
    """The four dimensions are at their intake values. A decision already made is rejected."""
    out: list[Violation] = []
    for field, intake in INTAKE_STATES.items():
        value = env.get(field)
        dimension = field[: -len("_state")]
        # Only complain about a value that IS in the vocabulary but is not the intake value;
        # an out-of-vocabulary value is rule 1's finding, so one defect keeps one rule id.
        if isinstance(value, str) and value in DIMENSIONS[dimension] and value != intake:
            out.append(
                Violation(
                    "rule-3",
                    f"{field} is {value!r} but a candidate enters the store at {intake!r}; an "
                    f"envelope arriving with a decision already made is rejected",
                )
            )
    return out


def _rule4(env: dict) -> list[Violation]:
    """Every `duplicate_hints[]` entry is a `{kind, target, basis}` with a declared `kind`."""
    hints = env.get("duplicate_hints")
    if not isinstance(hints, list):
        return []  # a non-list is rule 1's finding
    out: list[Violation] = []
    for index, hint in enumerate(hints):
        if not isinstance(hint, dict):
            out.append(Violation("rule-4", f"duplicate_hints[{index}] is not an object"))
            continue
        extra = sorted(set(hint) - {"kind", "target", "basis"})
        if extra:
            out.append(
                Violation("rule-4", f"duplicate_hints[{index}] carries undeclared keys {extra}")
            )
        kind = hint.get("kind")
        if kind not in HINT_KINDS:
            out.append(
                Violation(
                    "rule-4",
                    f"duplicate_hints[{index}].kind {kind!r} is outside the declared vocabulary "
                    f"{list(HINT_KINDS)}; a hint may never be written into curation_state",
                )
            )
        target = hint.get("target")
        if not isinstance(target, str) or target == "":
            out.append(
                Violation("rule-4", f"duplicate_hints[{index}] has no target (an id or 'external')")
            )
        basis = hint.get("basis")
        if not isinstance(basis, str) or basis == "":
            out.append(Violation("rule-4", f"duplicate_hints[{index}] carries no basis string"))
    return out


def _rule5(env: dict, captures: dict | None) -> list[Violation]:
    """`captured_text` byte-identical to the capture record referenced by `capture_id`."""
    if captures is None:
        return [
            Violation(
                "rule-5",
                "no capture records were supplied, so captured_text cannot be checked against "
                "the capture it claims to derive from (the check is not skipped silently)",
            )
        ]
    capture_id = env.get("capture_id")
    if not isinstance(capture_id, str) or capture_id == "":
        return []  # rule 1 already names the defect
    if capture_id not in captures:
        return [
            Violation(
                "rule-5",
                f"capture_id {capture_id!r} matches no capture record "
                f"(known: {sorted(captures)[:6]}{'...' if len(captures) > 6 else ''})",
            )
        ]
    text = env.get("captured_text")
    if not isinstance(text, str):
        return []
    recorded = captures[capture_id]
    if isinstance(recorded, (bytes, bytearray)):
        recorded = bytes(recorded).decode("utf-8", "replace")
    if not isinstance(recorded, str):
        return [Violation("rule-5", f"capture {capture_id!r} has no readable captured_text")]
    if text.encode("utf-8") != recorded.encode("utf-8"):
        return [
            Violation(
                "rule-5",
                f"captured_text is not byte-identical to capture {capture_id!r}: envelope "
                f"{len(text.encode('utf-8'))} bytes {text!r}, capture "
                f"{len(recorded.encode('utf-8'))} bytes {recorded!r}",
            )
        ]
    return []


def _rule6(env: dict) -> list[Violation]:
    """Re-serializing the envelope round-trips without loss -- no field silently dropped."""
    def bad(message: str) -> list[Violation]:
        return [Violation("rule-6", message)]

    try:
        first = serialize(env)
        reparsed = parse(first)
        second = serialize(reparsed)
    except EnvelopeError as exc:
        return bad(f"the envelope cannot be re-serialized without loss: {exc}")
    if first != second:
        return bad("serialize(parse(serialize(e))) is not byte-identical to serialize(e)")
    if set(reparsed) != set(env):
        dropped = sorted(set(env) - set(reparsed))
        added = sorted(set(reparsed) - set(env))
        return bad(f"the round-trip changed the field set (dropped={dropped}, added={added})")
    if reparsed != env:
        differing = sorted(k for k in set(env) | set(reparsed) if env.get(k) != reparsed.get(k))
        return bad(f"the round-trip changed the value of {differing}")
    return []


# -- store integration ---------------------------------------------------------------------


def capture_texts(store) -> dict[str, str]:
    """Every capture record in a W1.1 store, as `capture_id` -> `captured_text` (for rule 5)."""
    return {
        row["capture_id"]: row["captured_text"]
        for row in store.conn.execute("SELECT capture_id, captured_text FROM captures")
    }


def store_capture(store, envelope: dict) -> str:
    """Write the envelope's immutable capture row through the W1.1 store. Returns `capture_id`.

    The envelope carries the capture (`captured_*`), so this is where a raw encounter enters the
    store of record. Rules 1, 2 and 6 are enforced first; rule 5 is meaningless before the
    record exists. The store's own triggers make the row immutable from then on.
    """
    _refuse(envelope, validate(envelope, captures=None, rules=("rule-1", "rule-2", "rule-6")))
    return store.add_capture(
        envelope["capture_id"],
        envelope["captured_text"],
        captured_attribution=envelope.get("captured_attribution", "unknown"),
        captured_citation=envelope.get("captured_citation", "none"),
        capture_method=envelope.get("capture_method"),
        captured_at=envelope.get("captured_at"),
        captured_by=envelope.get("captured_by", "unknown"),
        language=envelope.get("language", "und"),
        source_reference=envelope.get("source_reference", "none"),
        context_notes=envelope.get("context_notes", "none"),
        raw_artifact_ref=envelope.get("raw_artifact_ref", "none"),
    )


def store_envelope(store, envelope: dict, *, candidate_id: str) -> str:
    """Validate all six rules against the store's captures, then write candidate + hints.

    The capture must already exist (use `store_capture` for a new encounter): rule 5 is checked
    against the store's real capture record, not against a copy of the envelope. The four state
    dimensions are not passed to the store at all -- `garden_store.add_candidate` fixes them at
    their intake values, the same rule 3 this function just enforced.
    """
    _refuse(envelope, validate(envelope, capture_texts(store)))
    candidate = store.add_candidate(
        candidate_id,
        envelope["candidate_text"],
        [envelope["capture_id"]],
        candidate_author=envelope.get("candidate_author", "unknown"),
        candidate_source_ref=envelope.get("candidate_source_ref", "none"),
        normalization_notes=envelope["normalization_notes"],
        intake_schema_version=envelope.get("intake_schema_version", SCHEMA_KEY),
        external_id=envelope.get("external_id"),
    )
    hints = envelope.get("duplicate_hints") or []
    if hints:
        store.add_duplicate_hints(candidate, list(hints))
    return candidate


def read_envelope(store, candidate_id: str) -> dict:
    """Reconstruct an envelope's required fields from the store (capture + candidate + hints).

    Used to prove a stored envelope is readable back intact: the result validates with zero
    violations, and its required fields equal the envelope that was stored.
    """
    candidate = store.conn.execute(
        "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
    ).fetchone()
    if candidate is None:
        raise EnvelopeError(f"no candidate {candidate_id!r} in the store")
    link = store.conn.execute(
        "SELECT capture_id FROM candidate_captures WHERE candidate_id = ? ORDER BY ordinal",
        (candidate_id,),
    ).fetchall()
    if not link:
        raise EnvelopeError(f"candidate {candidate_id!r} references no capture")
    capture = store.conn.execute(
        "SELECT * FROM captures WHERE capture_id = ?", (link[0]["capture_id"],)
    ).fetchone()
    hints = [
        {"kind": row["kind"], "target": row["target"], "basis": row["basis"]}
        for row in store.conn.execute(
            "SELECT kind, target, basis FROM duplicate_hints WHERE candidate_id = ? "
            "ORDER BY hint_seq",
            (candidate_id,),
        )
    ]
    envelope = {field: capture[field] for field in CAPTURE_FIELDS}
    envelope.update(
        {
            "intake_schema_version": candidate["intake_schema_version"],
            "candidate_text": candidate["candidate_text"],
            "candidate_author": candidate["candidate_author"],
            "candidate_source_ref": candidate["candidate_source_ref"],
            "normalization_notes": candidate["normalization_notes"],
            "duplicate_hints": hints,
            "curation_state": candidate["curation_state"],
            "research_state": candidate["research_state"],
            "corpus_state": candidate["corpus_state"],
            "work_state": candidate["work_state"],
        }
    )
    if candidate["external_id"] is not None:
        envelope["external_id"] = candidate["external_id"]
    return envelope


def _refuse(envelope: object, violations: list[Violation]) -> None:
    if violations:
        raise EnvelopeError(
            f"envelope rejected ({len(violations)} violation(s)): "
            + "; ".join(str(v) for v in violations)
        )


# -- CLI (diagnostic, read-only) ------------------------------------------------------------


def _load_json(path: Path, label: str) -> object:
    try:
        return json.loads(path.read_bytes().decode("utf-8"))
    except OSError as exc:
        raise EnvelopeError(f"cannot read {label} {path}: {exc}") from None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnvelopeError(f"{label} {path} is not valid JSON: {exc}") from None


def cmd_serialize(args: argparse.Namespace) -> int:
    try:
        envelope = _load_json(Path(args.envelope), "envelope")
        if not isinstance(envelope, dict):
            raise EnvelopeError("envelope file must contain a JSON object")
        text = serialize(envelope)
    except EnvelopeError as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    sys.stdout.write(text + "\n")
    print("RESULT: PASS")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Read-only: validate one envelope file and print one line per violation, with its rule id."""
    try:
        envelope = _load_json(Path(args.envelope), "envelope")
        captures = None
        if args.captures:
            captures = _load_json(Path(args.captures), "captures")
            if not isinstance(captures, dict):
                raise EnvelopeError("captures file must be a JSON object mapping capture_id -> text")
        rules = RULE_IDS if args.rule is None else (f"rule-{args.rule}",)
        violations = validate(envelope, captures, rules)
    except EnvelopeError as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    for violation in violations:
        print(f"FAIL: {violation}")
    if violations:
        print(f"RESULT: FAIL ({len(violations)} violation(s))")
        return 1
    print(f"PASS: {args.envelope} satisfies rule(s) {', '.join(rules)}")
    print("RESULT: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    ser = sub.add_parser("serialize", help="print one envelope's canonical serialized form")
    ser.add_argument("--envelope", required=True, help="envelope JSON file")
    ser.set_defaults(func=cmd_serialize)

    val = sub.add_parser("validate", help="validate one envelope file (read-only)")
    val.add_argument("--envelope", required=True, help="envelope JSON file")
    val.add_argument(
        "--captures",
        default=None,
        help="JSON object mapping capture_id -> captured_text, for rule 5 "
        "(omit and rule 5 reports that no capture record was supplied)",
    )
    val.add_argument("--rule", type=int, default=None, help="run only this rule number (1-6)")
    val.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except EnvelopeError as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
