#!/usr/bin/env python3
"""Garden manual capture/submission surface: one pasted text in, one immutable capture plus one
candidate envelope out.

Usage:
    python3 scripts/garden_submit.py submit --dir DIR --text 'TEXT'      --capture-method METHOD [options]
    python3 scripts/garden_submit.py submit --dir DIR --text-file FILE   --capture-method METHOD [options]
    python3 scripts/garden_submit.py submit --dir DIR --stdin            --capture-method METHOD [options]

W1.3 of the Garden corpus program (`docs/program/W1_DECOMPOSITION.md` section "W1.3 - Manual
capture/submission surface (CLI first)"). It is the first surface that WRITES: it turns a messy
manual submission into the two records the rest of the loop works on, using W1.1's store of
record (`scripts/garden_store.py`) and W1.2's envelope contract and validator
(`scripts/garden_envelope.py`, `docs/program/CANDIDATE_ENVELOPE.md`).

What this module guarantees (and what `scripts/check_garden_submit.py` asserts):

  1. **The raw input is stored verbatim.** `captured_text` is the submitted text, byte for byte:
     no strip, no trim, no quote/diacritic/glyph "fixing", no newline normalization. A literal
     `_` placeholder, curly quotes, a wrong author and a missing citation all survive exactly as
     encountered (`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md`). The documented normalization
     *algorithm* is W1.4; this surface performs none, and says so in `normalization_notes`.
  2. **No normalization without a note.** `candidate_text` / `candidate_author` /
     `candidate_source_ref` default to the captured values verbatim, so a plain submission records
     `normalization_notes: identical to capture`. Supplying a value that differs from the capture
     without `--normalization-notes` is refused, naming `normalization_notes` -- "every difference
     from the capture and why" is an assertion the operator must make, never an omission.
  3. **Absence is a sentinel, never an empty string.** An omitted optional flag becomes the
     sentinel the contract declares for that field (`unknown` / `none` / `und`); a flag supplied
     *empty* is passed through untouched so the validator names the field instead of a default
     quietly replacing it.
  4. **The capture method is selected explicitly.** `--capture-method` has no default: it must be
     one of the nine contract methods, named in the refusal otherwise.
  5. **Submission touches no state and records no decision.** The four dimensions enter at their
     intake values (`new` / `not_started` / `candidate_only` / `queued`) because
     `garden_store.add_candidate` has no state parameter; this surface never writes a
     `decisions` row, never sets research state, and never implies verification.
  6. **A refused submission writes nothing.** The whole envelope is validated (rules 1-4 and 6,
     plus rule 5 against the prospective capture record) *before* the first write, and a
     `capture_id` / `candidate_id` that already exists is refused before it too, so a rejected
     submission leaves the store byte-identical.

The candidate-id naming scheme, ruled here: `cap-YYYY-MM-DD-NNNN` and `cand-YYYY-MM-DD-NNNN`,
where the day is the capture day and `NNNN` is one greater than the highest number already used
for that kind on that day. It is derived by scanning the store's own ids -- not from a counter
table, a random suffix or the clock -- so the same store state always yields the same next id.

Deliberately absent (out of W1.3 scope): a web UI, browser capture extensions, automated
discovery, clipboard polling, any normalization or duplicate-hint algorithm (W1.4), any
review/queue/decision command (W1.5), any promotion path, and any write to `quotes.csv` /
`sources.csv` (read-only for the whole of W1).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden_envelope import (  # noqa: E402
    EnvelopeError,
    capture_texts,
    read_envelope,
    serialize,
    store_capture,
    store_envelope,
    validate,
)
from garden_store import (  # noqa: E402
    CAPTURE_METHODS,
    INTAKE_STATES,
    Store,
    StoreError,
    json_line,
    now_iso,
)

#: `normalization_notes` for a submission that recorded no difference at all. The contract's own
#: wording: "we did not touch it" must be an assertion, not an omission.
IDENTICAL_NOTE = "identical to capture"

#: The W1.3 id scheme: `cap-YYYY-MM-DD-NNNN` / `cand-YYYY-MM-DD-NNNN`.
DAILY_ID = re.compile(r"^(cap|cand)-(\d{4}-\d{2}-\d{2})-(\d{4,})$")

#: The flags that propose a Garden-facing value, and the captured value each one must agree with
#: unless `--normalization-notes` says what changed and why.
NORMALIZED_PAIRS = (
    ("candidate_text", "captured_text"),
    ("candidate_author", "captured_attribution"),
    ("candidate_source_ref", "captured_citation"),
)


class SubmitError(Exception):
    """A refusal this module is designed to make (bad submission, not a bug)."""


def _coalesce(value: str | None, default: str) -> str:
    """`default` when the flag was omitted; the value itself, verbatim, when it was supplied.

    An empty string is *supplied*, not absent: it is passed through so the envelope validator can
    name the field instead of a sentinel quietly standing in for input nobody gave.
    """
    return default if value is None else value


def _iso8601_with_offset(value: str) -> bool:
    """ISO-8601 with an explicit offset (the `captured_at` requirement, rule 1)."""
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(candidate).tzinfo is not None
    except ValueError:
        return False


def resolve_captured_at(value: str | None) -> str:
    """The encounter timestamp: the supplied one, or now. Refused, not repaired, if malformed."""
    stamp = value if value is not None else now_iso()
    if not _iso8601_with_offset(stamp):
        raise SubmitError(
            f"captured_at {stamp!r} is not ISO-8601 with an offset "
            f"(e.g. 2026-09-12T09:14:11-06:00)"
        )
    return stamp


def next_daily_id(store: Store, kind: str, day: str) -> str:
    """The next free `cap-<day>-NNNN` (captures) or `cand-<day>-NNNN` (candidates).

    Deterministic by construction: a scan of the store's own ids for that day, never a counter,
    a random suffix or a clock reading.
    """
    table, column = (
        ("captures", "capture_id") if kind == "cap" else ("candidates", "candidate_id")
    )
    highest = 0
    for row in store.conn.execute(
        f"SELECT {column} FROM {table} WHERE {column} LIKE ?", (f"{kind}-%",)
    ):
        match = DAILY_ID.match(row[0])
        if match and match.group(2) == day:
            highest = max(highest, int(match.group(3)))
    return f"{kind}-{day}-{highest + 1:04d}"


def read_text(args: argparse.Namespace) -> str:
    """The submitted text, decoded as UTF-8 and otherwise untouched."""
    sources = []
    if args.text is not None:
        sources.append("--text")
    if args.text_file is not None:
        sources.append("--text-file")
    if args.stdin:
        sources.append("--stdin")
    if len(sources) != 1:
        raise SubmitError(
            "exactly one of --text, --text-file or --stdin is required "
            f"(got {len(sources)}: {', '.join(sources) if sources else 'none'})"
        )
    if args.text is not None:
        return args.text
    if args.text_file is not None:
        path = Path(args.text_file)
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise SubmitError(f"cannot read --text-file {path}: {exc}") from None
        label = f"--text-file {path}"
    else:
        raw = sys.stdin.buffer.read()
        label = "--stdin"
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SubmitError(
            f"{label} is not valid UTF-8 ({exc}); the capture is stored verbatim, so an "
            f"encoding is never guessed -- re-encode the artifact and resubmit"
        ) from None


def build_envelope(
    args: argparse.Namespace, *, text: str, captured_at: str, capture_id: str, candidate_id: str
) -> dict:
    """Build the `garden.candidate-envelope/1` object for this submission, states at intake."""
    captured_attribution = _coalesce(args.attribution, "unknown")
    captured_citation = _coalesce(args.citation, "none")
    envelope = {
        "intake_schema_version": "garden.candidate-envelope/1",
        "capture_id": capture_id,
        "captured_text": text,
        "captured_attribution": captured_attribution,
        "captured_citation": captured_citation,
        "capture_method": args.capture_method,
        "captured_at": captured_at,
        "captured_by": _coalesce(args.captured_by, "operator"),
        "language": _coalesce(args.language, "und"),
        "source_reference": _coalesce(args.source_reference, "none"),
        "context_notes": _coalesce(args.context_notes, "none"),
        "raw_artifact_ref": _coalesce(args.raw_artifact_ref, "none"),
        "candidate_text": _coalesce(args.candidate_text, text),
        "candidate_author": _coalesce(args.candidate_author, captured_attribution),
        "candidate_source_ref": _coalesce(args.candidate_source_ref, captured_citation),
        "normalization_notes": _coalesce(args.normalization_notes, IDENTICAL_NOTE),
        # Intake writes no hints: generating duplicate hints is W1.4's job, and a hint is never a
        # decision (`CANDIDATE_ENVELOPE.md` section Duplicate hints).
        "duplicate_hints": [],
        **INTAKE_STATES,
    }
    return envelope


def _unsupported_normalization(envelope: dict, explicit_note: str | None) -> str | None:
    """The names of the normalized fields that differ from the capture without a note, if any."""
    if explicit_note is not None:
        return None
    differing = [
        candidate_field
        for candidate_field, captured_field in NORMALIZED_PAIRS
        if envelope[candidate_field] != envelope[captured_field]
    ]
    if not differing:
        return None
    return ", ".join(differing)


def require_capture_method(args: argparse.Namespace) -> None:
    if args.capture_method is None:
        raise SubmitError(
            "--capture-method is required: how the text was encountered is evidence, not a "
            f"default (choose from {list(CAPTURE_METHODS)})"
        )
    if args.capture_method not in CAPTURE_METHODS:
        raise SubmitError(
            f"capture_method {args.capture_method!r} is outside the contract vocabulary "
            f"{list(CAPTURE_METHODS)}"
        )


def _id_is_free(store: Store, capture_id: str, candidate_id: str) -> None:
    """Refuse an id the store already holds, before anything is written.

    Captures are immutable (`PROVENANCE_AND_CAPTURE_CONTRACT.md`), so this surface creates one
    capture per submission and never re-uses an existing one; a repeated candidate id would be a
    second write under an existing key.
    """
    if store.conn.execute(
        "SELECT 1 FROM captures WHERE capture_id = ?", (capture_id,)
    ).fetchone():
        raise SubmitError(
            f"capture_id {capture_id!r} already exists in the store; a capture is immutable, so "
            f"a new encounter needs a new capture_id (omit --capture-id to have one allocated)"
        )
    if store.conn.execute(
        "SELECT 1 FROM candidates WHERE candidate_id = ?", (candidate_id,)
    ).fetchone():
        raise SubmitError(
            f"candidate_id {candidate_id!r} already exists in the store; omit --candidate-id to "
            f"have one allocated ({candidate_id!r} is already taken)"
        )


def _refuse(envelope: dict, violations: list) -> None:
    if violations:
        raise EnvelopeError(
            f"envelope rejected ({len(violations)} violation(s)): "
            + "; ".join(str(v) for v in violations)
        )


def submit(args: argparse.Namespace) -> int:
    """The whole submission: validate, then write the capture and its candidate."""
    require_capture_method(args)
    text = read_text(args)
    captured_at = resolve_captured_at(args.captured_at)
    day = captured_at[:10]

    store_dir = Path(args.dir)
    with Store(store_dir) as store:
        capture_id = args.capture_id or next_daily_id(store, "cap", day)
        candidate_id = args.candidate_id or next_daily_id(store, "cand", day)
        _id_is_free(store, capture_id, candidate_id)

        envelope = build_envelope(
            args,
            text=text,
            captured_at=captured_at,
            capture_id=capture_id,
            candidate_id=candidate_id,
        )

        # The whole envelope is checked BEFORE the first write, so a refused submission leaves the
        # store byte-identical. Rule 5 is run against the prospective capture record, which is
        # the only record this submission could derive from.
        _refuse(envelope, validate(envelope, {capture_id: text}))

        differing = _unsupported_normalization(envelope, args.normalization_notes)
        if differing:
            raise SubmitError(
                f"normalization_notes: this submission changes {differing} away from the "
                f"capture, so an explicit --normalization-notes is required (every difference "
                f"from the capture must be explained and must say why; nothing was written)"
            )

        store_capture(store, envelope)
        store_envelope(store, envelope, candidate_id=candidate_id)

        # Read it back out of the store: the transcript below is the stored record, not the
        # object that was written, and the two are compared before RESULT: PASS is printed.
        stored = store.conn.execute(
            "SELECT captured_text FROM captures WHERE capture_id = ?", (capture_id,)
        ).fetchone()
        stored_text = stored["captured_text"]
        if stored_text.encode("utf-8") != text.encode("utf-8"):
            raise SubmitError(
                f"the stored capture {capture_id!r} is not byte-identical to the submitted text "
                f"({len(stored_text.encode('utf-8'))} vs {len(text.encode('utf-8'))} bytes)"
            )
        read_back = read_envelope(store, candidate_id)
        _refuse(read_back, validate(read_back, capture_texts(store)))
        counts = store.counts()

    if args.emit_envelope:
        target = Path(args.emit_envelope)
        target.write_bytes(serialize(envelope).encode("utf-8"))

    if args.json:
        print(
            json_line(
                {
                    "capture_id": capture_id,
                    "candidate_id": candidate_id,
                    "captured_text_bytes": len(text.encode("utf-8")),
                    "normalization_notes": envelope["normalization_notes"],
                    "duplicate_hints": envelope["duplicate_hints"],
                    "states": {key: envelope[key] for key in INTAKE_STATES},
                    "counts": counts,
                    "envelope": read_back,
                }
            )
        )
        return 0

    print(f"store: {store_dir}")
    print(
        f"capture: {capture_id} (new; capture_method={envelope['capture_method']}, "
        f"captured_at={envelope['captured_at']}, captured_by={envelope['captured_by']})"
    )
    print(
        f"candidate: {candidate_id} (new; "
        + ", ".join(f"{key}={value}" for key, value in INTAKE_STATES.items())
        + ")"
    )
    print(
        f"captured_text: {len(text.encode('utf-8'))} bytes, byte-identical to the submission "
        f"(no trimming, no glyph repair, no quote or diacritic rewriting)"
    )
    print(f"normalization_notes: {envelope['normalization_notes']}")
    print(
        "duplicate_hints: 0 at intake (hint generation is W1.4; a hint is never a decision)"
    )
    print(f"counts: {json_line(counts)}")
    print("stored record, read back out of the store (all 21 required fields, re-validated):")
    print(serialize(read_back))
    if args.emit_envelope:
        print(f"envelope: {args.emit_envelope}")
    print("RESULT: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    submit_parser = sub.add_parser(
        "submit",
        help="create one capture and its candidate envelope from a raw submission",
        description=(
            "Store the submitted text verbatim as an immutable capture, validate the envelope "
            "for it, and write the candidate plus its (empty) duplicate-hint rows. Nothing is "
            "written when the submission is refused."
        ),
    )
    submit_parser.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    source = submit_parser.add_mutually_exclusive_group()
    source.add_argument("--text", default=None, help="the submitted text, on the command line")
    source.add_argument("--text-file", default=None, help="the submitted text, read as UTF-8")
    source.add_argument(
        "--stdin", action="store_true", help="the submitted text, read as UTF-8 from stdin"
    )
    submit_parser.add_argument(
        "--capture-method",
        default=None,
        help=f"how the text was encountered, required, one of {list(CAPTURE_METHODS)}",
    )
    submit_parser.add_argument("--capture-id", default=None, help="override the allocated id")
    submit_parser.add_argument("--candidate-id", default=None, help="override the allocated id")
    submit_parser.add_argument(
        "--attribution", default=None, help="attribution as encountered (default: unknown)"
    )
    submit_parser.add_argument(
        "--citation", default=None, help="citation as encountered (default: none)"
    )
    submit_parser.add_argument(
        "--source-reference",
        "--source-url",
        dest="source_reference",
        default=None,
        help="where the encounter happened: URL / book+page / transcript line (default: none)",
    )
    submit_parser.add_argument(
        "--context-notes", default=None, help="surrounding context (default: none)"
    )
    submit_parser.add_argument(
        "--raw-artifact-ref", default=None, help="path to the unmodified artifact (default: none)"
    )
    submit_parser.add_argument("--language", default=None, help="BCP-47 tag (default: und)")
    submit_parser.add_argument(
        "--captured-by", default=None, help="who performed the capture (default: operator)"
    )
    submit_parser.add_argument(
        "--captured-at", default=None, help="ISO-8601 with offset (default: now)"
    )
    submit_parser.add_argument(
        "--candidate-text",
        default=None,
        help="normalized proposal (default: the captured text, verbatim)",
    )
    submit_parser.add_argument(
        "--candidate-author", default=None, help="normalized attribution (default: as captured)"
    )
    submit_parser.add_argument(
        "--candidate-source-ref",
        default=None,
        help="normalized citation (default: as captured)",
    )
    submit_parser.add_argument(
        "--normalization-notes",
        default=None,
        help=f"what changed and why; required when a candidate value differs from the capture "
        f"(default: {IDENTICAL_NOTE!r})",
    )
    submit_parser.add_argument(
        "--emit-envelope", default=None, help="also write the canonical envelope JSON to PATH"
    )
    submit_parser.add_argument(
        "--json", action="store_true", help="print one canonical JSON object instead of a transcript"
    )
    submit_parser.set_defaults(func=submit)

    args = parser.parse_args(argv)
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    try:
        return args.func(args)
    except (SubmitError, EnvelopeError, StoreError) as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
