#!/usr/bin/env python3
"""Garden normalization + duplicate hints: the deterministic intake transform and the hint generator.

Usage:
    python3 scripts/garden_normalize.py normalize  --dir DIR (--candidate-id ID | --all) [--json]
    python3 scripts/garden_normalize.py hints      --dir DIR (--candidate-id ID | --all) [--json]
    python3 scripts/garden_normalize.py classify   --reference 'TEXT'
    python3 scripts/garden_normalize.py describe   --text 'TEXT'

W1.4 of the Garden corpus program (`docs/program/W1_DECOMPOSITION.md` section "W1.4 -
Normalization + duplicate hints"). Two jobs, one lane, one algorithm each:

  1. **Normalization** (`garden.normalize/1`) turns a verbatim capture into the Garden-facing
     *proposal* deterministically, and records a note for **every** change it makes. The capture
     itself is never touched: `captured_text` stays byte-for-byte the encounter
     (`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md`). The declared transforms are, in order:
     Unicode NFC recomposition; canonical characters (curly quotes/primes -> straight quotes,
     dashes/minus -> `-`, ellipsis -> `...`, no-break/narrow spaces -> a plain space); then
     whitespace runs (including newlines and tabs) collapsed to one space and boundary whitespace
     trimmed. Characters the algorithm does not declare (guillemets, ideographic spaces, …) are
     left alone -- an undeclared transform is a silent edit. A literal `_` placeholder glyph is
     **preserved and reported**, never repaired: guessing the character it stands for is
     fabrication (`docs/data/DATA_QUALITY_REPORT.md`, the four `has_unresolved_glyph` rows).

  2. **Duplicate hints** (`docs/program/CANDIDATE_ENVELOPE.md` section Duplicate hints) compare a
     candidate against every other candidate in the store and emit `{kind, target, basis}` rows.
     Hints are *derived* data: they are recomputed from the store, never hand-edited, and are
     **never** a state -- nothing here writes `curation_state` (the operator owns `T-C4`/`T-C7`/
     `T-C9`), and nothing here writes a `decisions` row.

The hint kinds, and the two rulings this unit owns:

| kind | when | basis |
|---|---|---|
| `exact-text` | normalized, case-folded texts are identical | `normalized text identical (case-folded, N characters)` |
| `near-text` | similarity >= `NEAR_TEXT_THRESHOLD` (0.60) and not exact | `normalized text similarity 0.74 >= 0.60 …` |
| `same-reference` | the two candidates carry the *same specific* citation | `same specific citation 'Gleanings, CV'` |
| `same-passage` | same specific citation **and** similarity >= the threshold | `same specific citation 'X' with normalized text similarity 0.83 >= 0.60` |

**Ruling 1 -- the similarity threshold is 0.60**, computed with `difflib.SequenceMatcher` over
the normalized, case-folded text, and compared with `>=`. That matches the heuristic the legacy
validator already used (`scripts/validate_quotes.py` near-duplicate report), so the repo's own
"45 near-duplicate pairs" remain the reference data a reviewer can sanity-check the hints against.

**Ruling 2 -- a shared citation is only evidence when the citation actually pinpoints something.**
This is the fix for the legacy report's false-positive class (`docs/data/DATA_QUALITY_REPORT.md`
"~half the 45 flagged pairs are this false-positive pattern"): 19 legacy rows share the literal
`source_ref` `"Oral Tradition"` and get flagged against each other although the quotes are
unrelated. So `same-reference`/`same-passage` require a citation that carries a **locator**
(`citation_specificity`: an Arabic digit, a Roman-numeral token, or `§`). A generic label
(`Oral Tradition`, a bare work title, a sentinel) produces no reference hint at all, and the
sentinels `none`/`unknown`/`und` are never a shared citation. `near-text`/`exact-text` are
text-only comparisons and deliberately need no citation.

Hints are ordered `(target, kind)` for every candidate, so a rebuild of the same store always
writes the same rows in the same `hint_seq` order.

Deliberately absent (out of W1.4 scope): any auto-merge, any auto-reject, semantic/embedding
similarity, a review/queue surface (W1.5), any promotion path, any transition write (no
`decisions` row, no state change), any schema migration -- and any write to `quotes.csv` /
`sources.csv` (read-only for the whole of W1). The legacy corpus is not read as a comparison set;
hints compare stored candidates against each other.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden_store import HINT_KINDS, Store, StoreError, json_line  # noqa: E402

#: The algorithm id, carried in every note so a later change to the transform is visible in the
#: history of what was normalized rather than silently re-interpreting the same text.
ALGORITHM = "garden.normalize/1"

#: `normalization_notes` for a proposal that differs from the capture in no way at all. The same
#: string W1.3 writes for a plain submission: "we did not touch it" is an assertion, not an
#: omission (`docs/program/W1_3_SUBMISSION_CLI.md` section 4).
IDENTICAL_NOTE = "identical to capture"

#: Ruling 1: the documented similarity threshold. `>=`, over normalized case-folded text.
NEAR_TEXT_THRESHOLD = 0.60

#: The glyph the original author of the legacy corpus used for a character they could not type.
#: It is preserved and reported -- never replaced with a guess.
PLACEHOLDER_GLYPH = "_"

#: The declared canonical-character classes, in the order they are applied. Only these are
#: transformed; anything not listed is left exactly as it was encountered. Each class is applied
#: with its own table (`_canonical_characters`), so the note can attribute every change to it.
CHARACTER_CLASSES: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "quote-marks",
        {
            "\u2018": "'",
            "\u2019": "'",
            "\u201a": "'",
            "\u201b": "'",
            "\u2032": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u201e": '"',
            "\u2033": '"',
        },
    ),
    (
        "dashes",
        {
            "\u2010": "-",
            "\u2011": "-",
            "\u2012": "-",
            "\u2013": "-",
            "\u2014": "-",
            "\u2015": "-",
            "\u2212": "-",
        },
    ),
    ("ellipsis", {"\u2026": "..."}),
    ("no-break-spaces", {"\u00a0": " ", "\u2007": " ", "\u202f": " "}),
)

#: Ruling 2's locator test. A citation is *specific* when it pinpoints a place: an Arabic digit
#: (`2.47`, `43:1`, `p. 26`, `v. 277`, `255`), a Roman-numeral token (`CV`, `CXVII`, `XXIII`, and
#: a standalone chapter/verse numeral `V`/`X`), or a section mark. Uppercase-only, so ordinary
#: words (`civil`) cannot match.
LOCATOR_PATTERN = re.compile(
    r"\d"
    r"|(?:^|[^\w])([IVXLCDM]{2,})(?![\w])"
    r"|(?:^|[^\w])([IVX])(?![\w])"
    r"|\u00a7"
)

#: Sentinel values that are never a value: `none`/`unknown`/`und` cannot be a shared citation.
NOT_A_VALUE = ("none", "unknown", "und", "")

#: Hint order inside one candidate, so `hint_seq` is deterministic and stable across rebuilds.
KIND_ORDER = ("exact-text", "near-text", "same-reference", "same-passage")

#: The three capture fields a proposal is derived from, and the candidate field each one feeds.
NORMALIZED_PAIRS = (
    ("candidate_text", "captured_text"),
    ("candidate_author", "captured_attribution"),
    ("candidate_source_ref", "captured_citation"),
)


class NormalizeError(Exception):
    """A refusal this module is designed to make (broken input, not a bug)."""


# -- normalization ---------------------------------------------------------------------------


def _canonical_characters(value: str) -> tuple[str, list[str]]:
    """Apply the declared canonical-character classes. Returns the value and one note per class.

    Each class is translated with **its own** table: applying the union of the tables in one
    `str.translate` would convert a later class's characters while attributing them to the first
    class that happened to fire -- the note would then under-report (found by the acceptance run,
    which counts each class independently).
    """
    parts: list[str] = []
    for label, table in CHARACTER_CLASSES:
        changed = sum(value.count(glyph) for glyph in table)
        if changed:
            value = value.translate({ord(glyph): replacement for glyph, replacement in table.items()})
            parts.append(f"{label}: {changed} character(s) canonicalized")
    return value, parts


def normalize_field(value: str) -> tuple[str, str]:
    """Normalize one field. Returns `(normalized_value, note_part)`.

    `note_part` is `IDENTICAL_NOTE` only when nothing at all was observed about the value; every
    other case names each change (and each preserved placeholder) explicitly.
    """
    if not isinstance(value, str):
        raise NormalizeError(f"canonical normalization needs text, got {type(value).__name__}")
    parts: list[str] = []

    composed = unicodedata.normalize("NFC", value)
    if composed != value:
        parts.append("unicode: NFC recomposed")

    value, character_parts = _canonical_characters(composed)
    parts += character_parts

    collapsed = re.sub(r"\s+", " ", value)
    collapsed_characters = len(value) - len(collapsed)
    trimmed_characters = len(collapsed) - len(collapsed.strip())
    if collapsed_characters or trimmed_characters:
        parts.append(
            f"whitespace: {collapsed_characters} character(s) collapsed, "
            f"{trimmed_characters} boundary character(s) trimmed"
        )
    value = collapsed.strip()

    placeholders = value.count(PLACEHOLDER_GLYPH)
    if placeholders:
        parts.append(
            f"{placeholders} literal {PLACEHOLDER_GLYPH!r} preserved "
            f"(not repaired: guessing the character is fabrication)"
        )

    return value, ("; ".join(parts) if parts else IDENTICAL_NOTE)


def normalize_text(value: str) -> str:
    """The normalized value alone -- the comparison key the hints use."""
    return normalize_field(value)[0]


@dataclass
class Proposal:
    """The Garden-facing proposal for one capture, plus the note accounting for every change."""

    candidate_text: str
    candidate_author: str
    candidate_source_ref: str
    normalization_notes: str
    parts: dict[str, str] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return any(part != IDENTICAL_NOTE for part in self.parts.values())


def propose(captured_text: str, captured_attribution: str, captured_citation: str) -> Proposal:
    """The whole normalization: three normalized values and one note, deterministically.

    Deterministic by construction: a pure function of the three captured values -- no clock, no
    counter, no store state -- so the same captured encounter always yields the same proposal and
    the same note.
    """
    text, text_part = normalize_field(captured_text)
    author, author_part = normalize_field(captured_attribution)
    source_ref, source_part = normalize_field(captured_citation)
    parts = {
        "captured_text": text_part,
        "captured_attribution": author_part,
        "captured_citation": source_part,
    }
    if all(part == IDENTICAL_NOTE for part in parts.values()):
        # The one case where "nothing changed" is the whole note -- W1.3's exact wording, so a
        # plain proposal reads the same whichever surface produced it.
        notes = IDENTICAL_NOTE
    else:
        notes = "; ".join(f"{name}: {part}" for name, part in parts.items())
    return Proposal(
        candidate_text=text,
        candidate_author=author,
        candidate_source_ref=source_ref,
        normalization_notes=notes,
        parts=parts,
    )


# -- duplicate hints -------------------------------------------------------------------------


def citation_specificity(reference: str) -> str:
    """Classify a citation: `none` (a sentinel / nothing), `generic` (a bare label), `specific`.

    Ruling 2 in one function. `"Oral Tradition"` and `"Tablets of Bahá'u'lláh, Words of Paradise"`
    are `generic`: they name a body of material but pinpoint nothing, so two rows carrying them are
    not evidence of the same passage. `"Gita 2.47"`, `"Gleanings, CV"` and
    `"Epistle to the Son of the Wolf, p. 26"` are `specific`.
    """
    value = normalize_text(reference)
    if value in NOT_A_VALUE:
        return "none"
    return "specific" if LOCATOR_PATTERN.search(value) else "generic"


def _comparison_view(row: dict) -> dict:
    """The fields hints compare: the candidate's own view, normalized. Never writes anything."""
    return {
        "candidate_id": row["candidate_id"],
        "text": normalize_text(row["candidate_text"]).casefold(),
        "reference": normalize_text(row["candidate_source_ref"]),
    }


def similarity(left: str, right: str) -> float:
    """Ruling 1's similarity: `difflib.SequenceMatcher` over normalized case-folded text.

    `SequenceMatcher.ratio()` is **not** symmetric -- `ratio(a, b) != ratio(b, a)` in general,
    because the matching-block search recurses differently depending on which argument it sees
    second (measured on this corpus: `"Dhammapada, v. 277"`'s text scores 0.69 against `v. 278`'s
    in one direction and 0.67 in the other). A hint whose basis number depends on which candidate
    is being compared would be an artefact, so the similarity is defined as the **mean of the two
    directional ratios**: deterministic, symmetric, and the same number appears in both
    candidates' hints for the pair. The result is reported to two decimals in every basis string.
    """
    forward = difflib.SequenceMatcher(None, left, right).ratio()
    backward = difflib.SequenceMatcher(None, right, left).ratio()
    return (forward + backward) / 2


def compare(subject: dict, other: dict) -> list[dict]:
    """Every hint `subject` gets from `other`. Pure: two candidates in, hints out, nothing written."""
    hints: list[dict] = []
    left, right = _comparison_view(subject), _comparison_view(other)
    target = right["candidate_id"]

    if left["text"] == right["text"]:
        hints.append(
            {
                "kind": "exact-text",
                "target": target,
                "basis": f"normalized text identical (case-folded, {len(left['text'])} characters)",
            }
        )
    ratio = similarity(left["text"], right["text"])
    near = ratio >= NEAR_TEXT_THRESHOLD

    shared = left["reference"] == right["reference"]
    specific = citation_specificity(right["reference"]) == "specific"
    # Both are required: two sentinels are equal but are not a citation, so a candidate pair that
    # both say `source_ref: none` -- the shape the legacy report calls a false positive -- gets no
    # reference hint at all.
    same_specific_citation = shared and specific

    if near and left["text"] != right["text"]:
        hints.append(
            {
                "kind": "near-text",
                "target": target,
                "basis": (
                    f"normalized text similarity {ratio:.2f} >= {NEAR_TEXT_THRESHOLD:.2f} "
                    f"(case-folded, difflib.SequenceMatcher)"
                ),
            }
        )
    if same_specific_citation:
        hints.append(
            {
                "kind": "same-reference",
                "target": target,
                "basis": f"same specific citation {right['reference']!r}",
            }
        )
    if same_specific_citation and near:
        hints.append(
            {
                "kind": "same-passage",
                "target": target,
                "basis": (
                    f"same specific citation {right['reference']!r} with normalized text "
                    f"similarity {ratio:.2f} >= {NEAR_TEXT_THRESHOLD:.2f}"
                ),
            }
        )
    hints.sort(key=lambda hint: KIND_ORDER.index(hint["kind"]))
    return hints


def candidate_rows(store: Store) -> list[dict]:
    """Every candidate, ordered by `candidate_id` -- the order hints are compared and written in."""
    return [
        dict(row)
        for row in store.conn.execute(
            "SELECT candidate_id, candidate_text, candidate_source_ref FROM candidates "
            "ORDER BY candidate_id"
        )
    ]


def hints_for(rows: list[dict], candidate_id: str) -> list[dict]:
    """All hints for one candidate, against every other candidate, ordered `(target, kind)`."""
    subject = next((row for row in rows if row["candidate_id"] == candidate_id), None)
    if subject is None:
        return []
    hints: list[dict] = []
    for other in rows:  # already ordered by candidate_id
        if other["candidate_id"] == candidate_id:
            continue
        hints += compare(subject, other)
    return hints


def rebuild_hints(store: Store, candidate_ids: list[str], rows: list[dict]) -> dict[str, int]:
    """Recompute hints for each candidate, in `candidate_id` order, replacing what was there.

    The only sanctioned write mode for hints: they are derived data, so a rebuild is a delete and
    a regenerate, never an edit (`scripts/garden_store.py`, `duplicate_hints`).
    """
    written = 0
    for candidate_id in sorted(candidate_ids):
        hints = hints_for(rows, candidate_id)
        written += len(hints)
        store.replace_duplicate_hints(candidate_id, hints)
    return {"candidates": len(candidate_ids), "hints": written}


# -- store writes ----------------------------------------------------------------------------


def normalize_candidate(store: Store, candidate_id: str) -> tuple[Proposal, bool]:
    """Normalize one stored candidate and write the proposal + note. Returns (proposal, wrote).

    Refusals (all of them before any write) are computed by `proposal_for`; the write itself goes
    through the store's guarded `apply_normalization`.
    """
    proposal, row = proposal_for(store, candidate_id)
    changed = (
        proposal.candidate_text != row["candidate_text"]
        or proposal.candidate_author != row["candidate_author"]
        or proposal.candidate_source_ref != row["candidate_source_ref"]
        or proposal.normalization_notes != row["normalization_notes"]
    )
    if changed:
        store.apply_normalization(
            candidate_id,
            candidate_text=proposal.candidate_text,
            candidate_author=proposal.candidate_author,
            candidate_source_ref=proposal.candidate_source_ref,
            normalization_notes=proposal.normalization_notes,
        )
    return proposal, changed


def proposal_for(store: Store, candidate_id: str) -> tuple[Proposal, dict]:
    """The proposal for one stored candidate, with every refusal checked. Writes nothing.

    Refusals:
      * the candidate must exist;
      * its `curation_state` must still be `new` -- normalization is an intake-time operation, and
        a candidate the operator has already decided on is history, not a work in progress;
      * the proposal's `candidate_text` must be non-empty -- a capture of nothing but whitespace
        normalizes to the empty string, which the store's own `CHECK(length(...) > 0)` refuses.

    Splitting this out is what lets a batch run be all-or-nothing: every candidate in the
    selection is checked before any of them is written, so `--all` never half-applies.
    """
    row = store.conn.execute(
        "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
    ).fetchone()
    if row is None:
        raise NormalizeError(f"no candidate {candidate_id!r} in the store")
    if row["curation_state"] != "new":
        raise NormalizeError(
            f"candidate {candidate_id!r} is curation_state={row['curation_state']!r}: "
            f"normalization is an intake-time operation and only applies while a candidate is "
            f"'new' (a decided candidate is history, not a proposal)"
        )
    capture = store.conn.execute(
        "SELECT c.* FROM candidate_captures cc JOIN captures c ON c.capture_id = cc.capture_id "
        "WHERE cc.candidate_id = ? ORDER BY cc.ordinal",
        (candidate_id,),
    ).fetchone()
    if capture is None:
        raise NormalizeError(f"candidate {candidate_id!r} references no capture")
    proposal = propose(
        capture["captured_text"], capture["captured_attribution"], capture["captured_citation"]
    )
    if proposal.candidate_text == "":
        raise NormalizeError(
            f"candidate {candidate_id!r} normalizes to an empty candidate_text: the capture is "
            f"only whitespace, and an empty proposal is not a proposal (the capture itself is "
            f"kept verbatim)"
        )
    return proposal, dict(row)


# -- CLI -------------------------------------------------------------------------------------


def _selection(args: argparse.Namespace, store: Store) -> list[str]:
    """`--candidate-id ID` or `--all`, exactly one, explicitly -- never an implicit whole store."""
    if (args.candidate_id is None) == (not args.all):
        raise NormalizeError(
            "exactly one of --candidate-id ID or --all is required: a write to the store is never "
            "implicit (--all normalizes/hints every candidate, in candidate_id order)"
        )
    if args.candidate_id is not None:
        if not store.conn.execute(
            "SELECT 1 FROM candidates WHERE candidate_id = ?", (args.candidate_id,)
        ).fetchone():
            raise NormalizeError(f"no candidate {args.candidate_id!r} in the store")
        return [args.candidate_id]
    return [row["candidate_id"] for row in candidate_rows(store)]


def cmd_normalize(args: argparse.Namespace) -> int:
    """Write the proposal for the selected candidates.

    Ruling 3 (this unit's): an **explicit** `--candidate-id` that cannot be normalized is a
    refusal -- non-zero exit, nothing written. A **batch** `--all` normalizes every candidate it
    can and names each one it skipped with its reason on a `SKIPPED:` line, because the store has
    no path to remove a junk candidate (a submission of nothing but whitespace is legal at intake)
    and one such row must not make the whole batch unusable. A batch where *nothing* could be
    normalized is a failure, not a pass: a run that writes nothing must not report success. Every
    candidate in the run is checked before any of them is written, so `--all` never half-applies.
    """
    results: list[dict] = []
    skipped: list[dict] = []
    with Store(args.dir) as store:
        ids = _selection(args, store)
        prepared: list[tuple[str, Proposal, dict]] = []
        for candidate_id in ids:
            try:
                proposal, row = proposal_for(store, candidate_id)
            except NormalizeError as exc:
                if args.candidate_id is not None:
                    raise  # an explicit request that cannot be met is a refusal
                skipped.append({"candidate_id": candidate_id, "reason": str(exc)})
                continue
            prepared.append((candidate_id, proposal, row))
        if not prepared:
            first = skipped[0] if skipped else {"candidate_id": "(none)", "reason": "no candidates"}
            raise NormalizeError(
                f"nothing could be normalized: {len(skipped)} candidate(s) skipped, starting with "
                f"{first['candidate_id']}: {first['reason']}"
            )
        for candidate_id, _proposal, _row in prepared:
            proposal, changed = normalize_candidate(store, candidate_id)
            results.append({"candidate_id": candidate_id, "changed": changed, **proposal.__dict__})
        counts = store.counts()

    if args.json:
        print(
            json_line(
                {
                    "algorithm": ALGORITHM,
                    "normalized": results,
                    "skipped": skipped,
                    "counts": counts,
                }
            )
        )
        return 0

    print(f"store: {args.dir}")
    print(f"algorithm: {ALGORITHM}")
    for skip in skipped:
        print(f"SKIPPED: {skip['candidate_id']}: {skip['reason']}")
    for result in results:
        print(
            f"candidate: {result['candidate_id']} "
            f"({'normalized' if result['changed'] else 'no-op: already normalized'})"
        )
        print(f"  candidate_text: {result['candidate_text']!r}")
        print(f"  candidate_author: {result['candidate_author']!r}")
        print(f"  candidate_source_ref: {result['candidate_source_ref']!r}")
        print(f"  normalization_notes: {result['normalization_notes']}")
    print(
        f"normalized {sum(1 for r in results if r['changed'])} of {len(results)} candidate(s) "
        f"({len(skipped)} skipped)"
    )
    print("the captures were not touched: a proposal is stored alongside the encounter")
    print(f"counts: {json_line(counts)}")
    print("RESULT: PASS")
    return 0


def cmd_hints(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        ids = _selection(args, store)
        rows = candidate_rows(store)
        before = store.counts()["duplicate_hints"]
        summary = rebuild_hints(store, ids, rows)
        after = store.counts()["duplicate_hints"]
        logged: list[dict] = []
        for candidate_id in sorted(ids):
            logged.append(
                {
                    "candidate_id": candidate_id,
                    "hints": [
                        {"kind": row["kind"], "target": row["target"], "basis": row["basis"]}
                        for row in store.conn.execute(
                            "SELECT kind, target, basis FROM duplicate_hints WHERE candidate_id = ? "
                            "ORDER BY hint_seq",
                            (candidate_id,),
                        )
                    ],
                }
            )
        counts = store.counts()

    if args.json:
        print(json_line({"hints": logged, "counts": counts}))
        return 0

    print(f"store: {args.dir}")
    print(
        f"hints: {summary['hints']} written for {summary['candidates']} candidate(s) "
        f"({before} row(s) before, {after} after; a rebuild replaces, never edits)"
    )
    print(f"threshold: normalized case-folded similarity >= {NEAR_TEXT_THRESHOLD:.2f}")
    for entry in logged:
        if not entry["hints"]:
            print(f"candidate: {entry['candidate_id']} (no hints)")
            continue
        print(f"candidate: {entry['candidate_id']} ({len(entry['hints'])} hint(s))")
        for hint in entry["hints"]:
            print(f"  [{hint['kind']}] -> {hint['target']} basis={hint['basis']}")
    print(
        "note: hints are not decisions -- no curation_state was written and no decisions row was "
        "recorded (T-C4/T-C7/T-C9 are the operator's)"
    )
    print(f"counts: {json_line(counts)}")
    print("RESULT: PASS")
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    print(f"reference: {args.reference!r}")
    print(f"normalized: {normalize_text(args.reference)!r}")
    print(f"specificity: {citation_specificity(args.reference)}")
    print("RESULT: PASS")
    return 0


def cmd_describe(args: argparse.Namespace) -> int:
    value, part = normalize_field(args.text)
    print(f"captured: {args.text!r}")
    print(f"normalized: {value!r}")
    print(f"note_part: {part}")
    print("RESULT: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    norm = sub.add_parser(
        "normalize",
        help="write the normalized proposal + notes for a stored candidate",
        description=(
            "Compute the deterministic proposal for a stored candidate's capture and write "
            "candidate_text / candidate_author / candidate_source_ref / normalization_notes. "
            "The capture is never modified, and nothing is written when the run is refused."
        ),
    )
    norm.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    norm.add_argument("--candidate-id", default=None, help="normalize this candidate")
    norm.add_argument("--all", action="store_true", help="normalize every candidate, id order")
    norm.add_argument("--json", action="store_true", help="one canonical JSON object")
    norm.set_defaults(func=cmd_normalize)

    hints = sub.add_parser(
        "hints",
        help="recompute a candidate's duplicate hints from the store",
        description=(
            "Rebuild {kind, target, basis} hint rows for a candidate (or every candidate) by "
            "comparing normalized texts and specific citations. Hints are derived data and are "
            "never a state: no curation_state and no decisions row is written."
        ),
    )
    hints.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    hints.add_argument("--candidate-id", default=None, help="recompute this candidate's hints")
    hints.add_argument("--all", action="store_true", help="recompute every candidate, id order")
    hints.add_argument("--json", action="store_true", help="one canonical JSON object")
    hints.set_defaults(func=cmd_hints)

    classify = sub.add_parser(
        "classify",
        help="read-only: is a citation specific, generic, or nothing?",
        description="Print citation_specificity() for one reference. Reads nothing, writes nothing.",
    )
    classify.add_argument("--reference", required=True, help="the citation text to classify")
    classify.set_defaults(func=cmd_classify)

    describe = sub.add_parser(
        "describe",
        help="read-only: print one text's normalized value and its note part",
        description="Print normalize_field() for one string. Reads nothing, writes nothing.",
    )
    describe.add_argument("--text", required=True, help="the text to normalize")
    describe.set_defaults(func=cmd_describe)

    args = parser.parse_args(argv)
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    try:
        return args.func(args)
    except (NormalizeError, StoreError) as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
