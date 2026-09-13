#!/usr/bin/env python3
"""Deterministic acceptance + evidence run for W1.4: normalization + duplicate hints.

Usage:
    python3 scripts/check_garden_normalize.py

Runs entirely in a throwaway temporary directory (never the repo) and asserts the W1.4 acceptance
criteria from `docs/program/W1_DECOMPOSITION.md` section "W1.4":

  1. deterministic normalization records a note for every change it makes, and the capture itself
     stays byte-for-byte the encounter (curly quotes, runs of whitespace, a literal `_`, an NFC/
     NFD difference and a wrong author all survive in `captured_text`);
  2. the generic-`source_ref` false-positive pattern from `docs/data/DATA_QUALITY_REPORT.md`
     ("Oral Tradition" and the bare work titles) produces **no** `same-passage`/`same-reference`
     hint, while a genuinely specific shared citation does -- with the legacy heuristic's own
     predicate asserted on the same fixtures, so the guard is proven to be doing work rather than
     describing itself;
  3. the documented similarity threshold makes the repo's real near-text pair (`id 3 ~ 283`, the
     pair `DATA_QUALITY_REPORT.md` names) a `near-text` hint in both directions, with a symmetric
     number in the basis;
  4. every hint carries a basis string and a resolvable target, hint rows are recomputed (a rebuild
     is idempotent and replaces rather than accumulates), and **no hint appears in any state**: the
     four dimensions are untouched, no candidate is `duplicate`, and `decisions` stays empty;
  5. a refused run writes nothing at all, `quotes.csv` / `sources.csv` are byte-identical before and
     after, and nothing is written outside the temp directory.

Every fixture candidate is submitted through the real W1.3 CLI as a subprocess and its text/citation
are read out of the real `quotes.csv`, so the expectations are derived from the corpus rather than
hard-coded; each fixture class is asserted to exist (`would be vacuous` otherwise).

Exits 0 with `RESULT: PASS`, non-zero with `RESULT: FAIL` and one `FAIL:` line per broken check --
never a traceback. Negative controls (mutation -> observed `FAIL:` line) are recorded in
`GARDEN_W1_4_HANDOFF.md`.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import garden_normalize as gn  # noqa: E402
import garden_store  # noqa: E402
from garden_envelope import (  # noqa: E402
    REQUIRED_FIELDS,
    capture_texts,
    read_envelope,
    validate,
)
from garden_store import HINT_KINDS, INTAKE_STATES, Store  # noqa: E402
from garden_submit import IDENTICAL_NOTE as SUBMIT_IDENTICAL_NOTE  # noqa: E402

NORMALIZE = SCRIPTS / "garden_normalize.py"
SUBMIT = SCRIPTS / "garden_submit.py"
STORE_CLI = SCRIPTS / "garden_store.py"
QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
STORE_FILENAME = garden_store.STORE_FILENAME

#: The test's OWN canonical-character table, written independently of the module's. It is a
#: superset used to re-derive every fixture's expected proposal: if the module stops canonicalizing
#: one of these classes, the re-derivation disagrees and the check fails.
TEST_CHARACTERS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u201b": "'",
    "\u2032": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u2033": '"',
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2015": "-",
    "\u2212": "-",
    "\u2026": "...",
    "\u00a0": " ",
    "\u2007": " ",
    "\u202f": " ",
}
QUOTE_MARKS = "".join(g for g in TEST_CHARACTERS if g in "\u2018\u2019\u201a\u201b\u2032\u201c\u201d\u201e\u2033")
TEST_TRANSLATION = {ord(g): r for g, r in TEST_CHARACTERS.items()}

#: The test's OWN placeholder glyph. Deliberately not `garden_normalize.PLACEHOLDER_GLYPH`: if the
#: test discovered its fixtures with the module's constant, changing the constant would change what
#: the test thinks the corpus contains instead of failing. The two are asserted equal below.
PLACEHOLDER = "_"

#: An NFC/NFD pair: the decomposed form is what a capturer pasting from some tools would get.
NFD_TEXT = "Baha\u0301'i, the light of unity."
WHITESPACE_ONLY = "   \n\t  "

failures: list[str] = []
refusal_outputs: list[tuple[str, str]] = []


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    failures.append(msg)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def check(condition: bool, msg: str, detail: str = "") -> bool:
    if condition:
        ok(msg)
        return True
    fail(msg + (f" -- {detail}" if detail else ""))
    return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def would_be_vacuous(msg: str) -> None:
    fail(f"{msg} -- would be vacuous")


def quote_marks_in(text: str) -> list[str]:
    """The distinct curly quote marks in a text, from the test's own table (never the module's)."""
    return sorted({char for char in text if char in QUOTE_MARKS})


# -- running the real CLIs -------------------------------------------------------------------


def run(script: Path, *args: object, stdin_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        input=stdin_bytes if stdin_bytes is not None else b"",
        capture_output=True,
    )


def out_text(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout + proc.stderr).decode("utf-8", "replace")


def first_json(proc: subprocess.CompletedProcess) -> dict:
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    return {}


# -- reading what the CLIs wrote -------------------------------------------------------------


def counts(store_dir: Path) -> dict[str, int]:
    with Store(store_dir) as store:
        return store.counts()


def export_bytes(store_dir: Path) -> bytes:
    with Store(store_dir) as store:
        return store.export_bytes()


def export_section(store_dir: Path, section: str) -> list[str]:
    """The lines of one export section -- used to prove a section was not rewritten."""
    lines = export_bytes(store_dir).decode("utf-8").splitlines()
    header = f"[{section}]"
    if header not in lines:
        return []
    out: list[str] = []
    for line in lines[lines.index(header) + 1 :]:
        if line.startswith("[") and line.endswith("]"):
            break
        if line:
            out.append(line)
    return out


def candidate_row(store_dir: Path, candidate_id: str) -> dict:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
    return dict(row) if row else {}


def capture_row(store_dir: Path, capture_id: str) -> dict:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT * FROM captures WHERE capture_id = ?", (capture_id,)
        ).fetchone()
    return dict(row) if row else {}


def hint_rows(store_dir: Path, candidate_id: str) -> list[dict]:
    with Store(store_dir) as store:
        return [
            dict(row)
            for row in store.conn.execute(
                "SELECT hint_seq, kind, target, basis FROM duplicate_hints "
                "WHERE candidate_id = ? ORDER BY hint_seq",
                (candidate_id,),
            )
        ]


def all_candidate_ids(store_dir: Path) -> list[str]:
    with Store(store_dir) as store:
        return [
            row["candidate_id"]
            for row in store.conn.execute("SELECT candidate_id FROM candidates ORDER BY candidate_id")
        ]


def set_curation_state(store_dir: Path, candidate_id: str, state: str) -> None:
    """Test scaffolding, not a surface: W1.5 owns transitions. Used only to prove W1.4's guard."""
    with Store(store_dir) as store:
        store.conn.execute(
            "UPDATE candidates SET curation_state = ? WHERE candidate_id = ?", (state, candidate_id)
        )
        store.conn.commit()


# -- the corpus the fixtures come from -------------------------------------------------------


def load_rows() -> dict[int, dict]:
    rows: dict[int, dict] = {}
    with QUOTES.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[int(row["id"])] = row
    return rows


def find_row(rows: dict[int, dict], label: str, predicate) -> int | None:
    for row_id in sorted(rows):
        if predicate(rows[row_id]):
            return row_id
    would_be_vacuous(f"no row in quotes.csv matches the {label} fixture")
    return None


def expected_proposal(text: str, attribution: str, citation: str) -> tuple[str, str, str]:
    """The test's own re-derivation of the proposal, from its own character table."""

    def one(value: str) -> str:
        composed = unicodedata.normalize("NFC", value)
        return " ".join(composed.translate(TEST_TRANSLATION).split())

    return one(text), one(attribution), one(citation)


def refusal(
    label: str,
    proc: subprocess.CompletedProcess,
    needle: str,
    store_dir: Path,
    before_export: bytes,
) -> None:
    """A refused W1.4 run: non-zero exit, the field/flag named, and not one byte written."""
    text = out_text(proc)
    refusal_outputs.append((label, text))
    check(
        proc.returncode != 0 and "RESULT: FAIL" in text,
        f"{label} is refused (exit {proc.returncode}, RESULT: FAIL)",
    )
    check(needle in text, f"{label} names {needle!r} in the refusal", text.strip()[:170])
    check(
        export_bytes(store_dir) == before_export,
        f"{label} wrote nothing at all (the store exports the same bytes)",
    )


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-normalize-check-"))
    quotes_before = sha256(QUOTES) if QUOTES.exists() else None
    sources_before = sha256(SOURCES) if SOURCES.exists() else None
    print(f"scratch: {scratch}")

    try:
        run_checks(scratch)
    except Exception as exc:  # never a traceback: RESULT must still print
        fail(f"unexpected {type(exc).__name__}: {exc}")
    finally:
        for label, text in refusal_outputs:
            if "Traceback" in text:
                fail(f"{label} refused with a traceback instead of a FAIL line")
        if refusal_outputs:
            ok(f"none of the {len(refusal_outputs)} refusals printed a traceback")
        if quotes_before is not None and sha256(QUOTES) != quotes_before:
            fail("quotes.csv changed during the run")
        if sources_before is not None and sha256(SOURCES) != sources_before:
            fail("sources.csv changed during the run")
        if quotes_before is not None and sources_before is not None:
            ok("quotes.csv and sources.csv are byte-identical before and after the run")
        check(
            not (ROOT / STORE_FILENAME).exists(),
            "no store was created in the repo root (the CLIs only ever write to --dir)",
        )
        allowed = ("store", "store_only_whitespace", "inputs", "out")
        stray = [
            p
            for p in scratch.rglob("*")
            if p.is_file() and p.relative_to(scratch).parts[0] not in allowed
        ]
        check(not stray, "nothing was written outside the store and the scratch inputs", str(stray))
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    print(
        "RESULT: PASS (normalization records every change and preserves the capture verbatim; "
        "hints are deterministic, cited, and never a state)"
    )
    return 0


def run_checks(scratch: Path) -> None:  # noqa: C901 -- one linear evidence script, by design
    store = scratch / "store"
    inputs = scratch / "inputs"
    out = scratch / "out"
    inputs.mkdir()
    out.mkdir()

    created = run(STORE_CLI, "create", "--dir", store)
    check(
        created.returncode == 0 and "RESULT: PASS" in out_text(created),
        "the store is created from empty by garden_store.py create",
        out_text(created).strip()[:170],
    )

    rows = load_rows()
    check(bool(rows), "quotes.csv is readable as CSV (the fixture source)", str(len(rows)))

    # -- 0. W1.4's rulings, stated as executable facts --------------------------------------
    print("\n-- the two rulings (threshold + citation specificity) --")
    check(
        gn.NEAR_TEXT_THRESHOLD == 0.60,
        "the documented similarity threshold is 0.60",
        str(gn.NEAR_TEXT_THRESHOLD),
    )
    check(
        gn.IDENTICAL_NOTE == SUBMIT_IDENTICAL_NOTE,
        "the 'nothing changed' note is W1.3's exact string (one vocabulary, not two)",
        f"{gn.IDENTICAL_NOTE!r} vs {SUBMIT_IDENTICAL_NOTE!r}",
    )
    check(
        gn.PLACEHOLDER_GLYPH == PLACEHOLDER,
        "the module's placeholder glyph is the corpus's literal `_` (the test's own constant, so a "
        "change to the module's constant fails here instead of silently redefining the fixture)",
        f"{gn.PLACEHOLDER_GLYPH!r} vs {PLACEHOLDER!r}",
    )
    check(
        gn.citation_specificity("Oral Tradition") == "generic",
        "'Oral Tradition' is classified generic (a label that pinpoints nothing)",
    )
    check(
        gn.citation_specificity("Tablets of Bahá’u’lláh, Words of Paradise") == "generic",
        "a bare work title with no locator is classified generic",
    )
    check(
        gn.citation_specificity("Gita 2.47") == "specific",
        "a citation with an Arabic locator is classified specific",
    )
    check(
        gn.citation_specificity("Gleanings, CV") == "specific",
        "a citation with a Roman-numeral locator is classified specific",
    )
    check(
        gn.citation_specificity("Epistle to the Son of the Wolf, p. 26") == "specific",
        "a citation with a page locator is classified specific",
    )
    check(gn.citation_specificity("none") == "none", "the sentinel 'none' is not a citation at all")
    check(gn.citation_specificity("unknown") == "none", "the sentinel 'unknown' is not a citation")
    check(
        gn.citation_specificity("") == "none",
        "an empty citation is not a citation (never 'generic')",
    )

    # -- 1. the fixture batch, derived from the real corpus --------------------------------
    print("\n-- the fixture batch (derived from quotes.csv) --")
    near_pair = (3, 283)
    for row_id in near_pair:
        check(row_id in rows, f"the id 3 ~ 283 fixture row {row_id} still exists in quotes.csv")
    near_similarity = gn.similarity(
        gn.normalize_text(rows[near_pair[0]]["quote_text"]).casefold(),
        gn.normalize_text(rows[near_pair[1]]["quote_text"]).casefold(),
    )
    check(
        near_similarity >= gn.NEAR_TEXT_THRESHOLD,
        f"the id {near_pair[0]} ~ {near_pair[1]} pair of DATA_QUALITY_REPORT.md is still a "
        f"near-text pair ({near_similarity:.2f} >= {gn.NEAR_TEXT_THRESHOLD:.2f})",
    )
    check(
        rows[near_pair[0]]["source_ref"] != rows[near_pair[1]]["source_ref"],
        "the near-text fixture pair carries two different citations (so it cannot be a "
        "same-reference hit)",
    )

    specific_pair = (4, 14)
    check(
        rows[specific_pair[0]]["source_ref"] == rows[specific_pair[1]]["source_ref"]
        and gn.citation_specificity(rows[specific_pair[0]]["source_ref"]) == "specific",
        "the same-reference fixture pair shares a specific citation",
    )
    specific_similarity = gn.similarity(
        gn.normalize_text(rows[specific_pair[0]]["quote_text"]).casefold(),
        gn.normalize_text(rows[specific_pair[1]]["quote_text"]).casefold(),
    )
    check(
        specific_similarity < gn.NEAR_TEXT_THRESHOLD,
        f"the same-reference fixture pair is below the threshold "
        f"({specific_similarity:.2f} < {gn.NEAR_TEXT_THRESHOLD:.2f}), so it must not be a "
        f"same-passage fixture",
    )

    generic_group = [319, 331, 332]
    generic_labels = {rows[row_id]["source_ref"] for row_id in generic_group}
    check(
        len(generic_labels) == 1 and gn.citation_specificity(next(iter(generic_labels))) == "generic",
        "the false-positive fixture group all carry one generic label",
        str(sorted(generic_labels)),
    )
    legacy_flagged = [
        (a, b)
        for a in generic_group
        for b in generic_group
        if a < b and rows[a]["source_ref"] == rows[b]["source_ref"]
    ]
    check(
        len(legacy_flagged) == 3,
        "the legacy heuristic's own predicate (equal source_ref) flags all three of those pairs -- "
        "this fixture is exactly the pattern DATA_QUALITY_REPORT.md calls a false positive",
        str(legacy_flagged),
    )

    title_pair = (5, 19)
    check(
        rows[title_pair[0]]["source_ref"] == rows[title_pair[1]]["source_ref"]
        and gn.citation_specificity(rows[title_pair[0]]["source_ref"]) == "generic",
        "the bare-work-title fixture pair shares a generic citation and no other pinpoint",
    )
    verse_pair = (113, 114)
    check(
        rows[verse_pair[0]]["source_ref"] != rows[verse_pair[1]]["source_ref"]
        and gn.citation_specificity(rows[verse_pair[0]]["source_ref"]) == "specific"
        and gn.citation_specificity(rows[verse_pair[1]]["source_ref"]) == "specific",
        "the same-work/different-verse fixture pair carries two *different* specific citations",
        f"{rows[verse_pair[0]]['source_ref']!r} / {rows[verse_pair[1]]['source_ref']!r}",
    )
    check(
        all(
            row_id in rows
            for row_id in (
                near_pair[0],
                near_pair[1],
                *specific_pair,
                *generic_group,
                *title_pair,
                *verse_pair,
            )
        ),
        "every named fixture row resolves in quotes.csv",
    )

    placeholder_ids = [
        row_id
        for row_id in sorted(rows)
        if row_id < 200
        and any(PLACEHOLDER in rows[row_id][field] for field in ("quote_text", "author", "source_ref"))
    ][:2]
    check(
        bool(placeholder_ids),
        "quotes.csv still contains rows with a literal `_` placeholder glyph (the fixture class)",
    )
    curly_ids = [
        row_id
        for row_id in sorted(rows)
        if any(char in rows[row_id]["quote_text"] for char in QUOTE_MARKS)
    ][:1]
    check(bool(curly_ids), "quotes.csv still contains rows whose text carries curly quote marks")
    clean_ids = [
        row_id
        for row_id in sorted(rows)
        if rows[row_id]["quote_text"] == " ".join(rows[row_id]["quote_text"].split())
        and rows[row_id]["quote_text"].translate(TEST_TRANSLATION) == rows[row_id]["quote_text"]
        and rows[row_id]["source_ref"] == rows[row_id]["source_ref"].translate(TEST_TRANSLATION)
        and rows[row_id]["author"] == rows[row_id]["author"].translate(TEST_TRANSLATION)
        and " ".join(rows[row_id]["source_ref"].split()) == rows[row_id]["source_ref"]
        and " ".join(rows[row_id]["author"].split()) == rows[row_id]["author"]
        and all(
            PLACEHOLDER not in rows[row_id][field]
            for field in ("quote_text", "source_ref", "author")
        )
    ][:1]
    check(
        bool(clean_ids),
        "quotes.csv still contains a row that is already fully normalized (the no-op fixture)",
    )

    fixture_order = [
        *near_pair,
        *specific_pair,
        *generic_group,
        *title_pair,
        *verse_pair,
        *placeholder_ids,
        *curly_ids,
        *clean_ids,
    ]
    deduped: list[int] = []
    for row_id in fixture_order:
        if row_id not in deduped:
            deduped.append(row_id)
    fixture_order = deduped
    check(
        len(set(fixture_order)) == len(fixture_order),
        f"the {len(fixture_order)} fixture rows are distinct (so the per-row checks are unambiguous)",
    )
    submitted: dict[int, tuple[str, str]] = {}
    for row_id in fixture_order:
        row = rows[row_id]
        proc = run(
            SUBMIT,
            "submit",
            "--dir",
            store,
            "--text",
            row["quote_text"],
            "--attribution",
            row["author"],
            "--citation",
            row["source_ref"],
            "--capture-method",
            "pasted-text",
            "--json",
        )
        check(
            proc.returncode == 0,
            f"fixture {row_id} is submitted through the real W1.3 CLI",
            out_text(proc).strip()[:170],
        )
        payload = first_json(proc)
        submitted[row_id] = (payload.get("capture_id", ""), payload.get("candidate_id", ""))

    check(
        len(submitted) == len(fixture_order) and all(cid and cid for cid, cid in submitted.values()),
        f"all {len(fixture_order)} fixtures have a capture and a candidate in the store",
        str(submitted),
    )
    candidate_of = {row_id: pair[1] for row_id, pair in submitted.items()}
    capture_of = {row_id: pair[0] for row_id, pair in submitted.items()}

    # A hand-made pair for the exact-text fixture and a hand-made messy capture. Neither is
    # hard-coded *data*: the text comes from a real row, repeated.
    repeated_text = rows[near_pair[0]]["quote_text"]
    repeated_citation = rows[specific_pair[0]]["source_ref"]

    def submit_raw(text: str, citation: str, attribution: str = "operator") -> tuple[str, str]:
        proc = run(
            SUBMIT,
            "submit",
            "--dir",
            store,
            "--text",
            text,
            "--attribution",
            attribution,
            "--citation",
            citation,
            "--capture-method",
            "pasted-text",
            "--json",
        )
        check(proc.returncode == 0, f"an extra fixture is submitted ({text[:24]!r}…)", out_text(proc).strip()[:170])
        payload = first_json(proc)
        return payload.get("capture_id", ""), payload.get("candidate_id", "")

    messy_text = f"  \u201c{repeated_text}\u201d\u2026\tand   a _ gap\n\n"
    messy_capture, messy_candidate = submit_raw(
        messy_text, f"\u201c{repeated_citation}\u201d", "\u201cRumi\u201d"
    )
    _, exact_a = submit_raw(repeated_text, repeated_citation)
    _, exact_b = submit_raw(repeated_text, repeated_citation)
    _, generic_exact_a = submit_raw(repeated_text, next(iter(generic_labels)))
    _, generic_exact_b = submit_raw(repeated_text, next(iter(generic_labels)))
    NFD_CAPTURE, NFD_CANDIDATE = submit_raw(NFD_TEXT, "none")
    _, whitespace_candidate = submit_raw(WHITESPACE_ONLY, "none")

    check(
        NFD_TEXT != unicodedata.normalize("NFC", NFD_TEXT),
        "the NFC fixture really is decomposed (so the NFC check cannot pass vacuously)",
    )

    # -- 2. normalization ------------------------------------------------------------------
    print("\n-- normalization: a note for every change, the capture untouched --")
    captures_before = export_section(store, "captures")
    candidates_before = export_section(store, "candidates")
    proc = run(NORMALIZE, "normalize", "--dir", store, "--all")
    transcript = out_text(proc)
    check(
        proc.returncode == 0 and "RESULT: PASS" in transcript,
        "normalize --all is accepted (exit 0, RESULT: PASS)",
        transcript.strip()[:200],
    )
    check("Traceback" not in transcript, "normalize prints no traceback")
    check(
        transcript.count("RESULT: PASS") == 1 and transcript.count("RESULT: FAIL") == 0,
        "the normalize transcript carries exactly one RESULT line",
    )
    check(gn.ALGORITHM in transcript, f"the transcript names the algorithm {gn.ALGORITHM!r}")
    check(
        "SKIPPED:" in transcript and whitespace_candidate in transcript,
        "the batch run names the one candidate it cannot normalize (the whitespace-only capture) "
        "instead of failing the whole batch",
        transcript.strip().splitlines()[2] if len(transcript.strip().splitlines()) > 2 else "",
    )
    check(
        "(1 skipped)" in transcript,
        "the batch reports exactly one skipped candidate",
    )
    check(
        export_section(store, "captures") == captures_before,
        "the whole [captures] export section is byte-identical after normalizing everything "
        "(a proposal is stored alongside the encounter, never instead of it)",
    )
    check(
        export_section(store, "candidates") != candidates_before,
        "the [candidates] section did change -- normalization wrote something",
    )

    for row_id, candidate_id in sorted(candidate_of.items()):
        row = rows[row_id]
        candidate = candidate_row(store, candidate_id)
        captured = candidate_row(store, candidate_id)
        expected_text, expected_author, expected_ref = expected_proposal(
            row["quote_text"], row["author"], row["source_ref"]
        )
        check(
            candidate.get("candidate_text") == expected_text,
            f"candidate {candidate_id} (row {row_id}) candidate_text equals an independently "
            f"re-derived normalization of the row",
            f"{candidate.get('candidate_text')!r} vs {expected_text!r}",
        )
        check(
            candidate.get("candidate_author") == expected_author,
            f"candidate {candidate_id} (row {row_id}) candidate_author is normalized the same way",
        )
        check(
            candidate.get("candidate_source_ref") == expected_ref,
            f"candidate {candidate_id} (row {row_id}) candidate_source_ref is normalized the same way",
        )
        stored_capture = capture_row(store, capture_of[row_id])
        check(
            stored_capture.get("captured_text", "").encode("utf-8")
            == row["quote_text"].encode("utf-8"),
            f"capture {capture_of[row_id]} (row {row_id}) is still byte-identical to the row's "
            f"verbatim text",
        )
        del captured

    # The hand-made messy fixture: every class of change it contains must be named in the note,
    # with counts that agree with counts computed here, from the captured text.
    messy_row = candidate_row(store, messy_candidate)
    messy_captured = capture_row(store, messy_capture).get("captured_text", "")
    messy_attribution = "\u201cRumi\u201d"
    check(
        messy_captured == messy_text,
        "the messy fixture's capture is byte-identical to the submitted bytes (verbatim)",
        f"{len(messy_captured)} vs {len(messy_text)} characters",
    )
    note = messy_row.get("normalization_notes", "")
    check(
        messy_row.get("candidate_text") == " ".join(messy_text.translate(TEST_TRANSLATION).split()),
        "the messy fixture's candidate_text equals the independently re-derived value",
        f"{messy_row.get('candidate_text')!r}",
    )
    check("\u201c" not in messy_row.get("candidate_text", "")
          and "\u2026" not in messy_row.get("candidate_text", ""),
          "no curly quote and no ellipsis survives in the messy fixture's candidate_text")
    check(
        messy_captured == messy_text and bool(quote_marks_in(messy_text)) and "\u2026" in messy_captured,
        "the messy fixture's capture keeps the curly quotes and the ellipsis verbatim",
    )
    quote_mark_count = sum(messy_text.count(char) for char in QUOTE_MARKS)
    check(quote_mark_count > 0, "the messy fixture really carries curly quote marks (non-vacuous)")
    check(
        f"quote-marks: {quote_mark_count} character(s) canonicalized" in note,
        f"the note names the quote-mark change with its exact count ({quote_mark_count})",
        note,
    )
    ellipsis_count = messy_text.count("\u2026")
    check(
        ellipsis_count > 0 and f"ellipsis: {ellipsis_count} character(s) canonicalized" in note,
        "the note names the ellipsis change with its exact count",
        note,
    )
    collapsed = len(messy_text) - len(re.sub(r"\s+", " ", messy_text))
    trimmed = len(re.sub(r"\s+", " ", messy_text)) - len(re.sub(r"\s+", " ", messy_text).strip())
    check(
        f"whitespace: {collapsed} character(s) collapsed, {trimmed} boundary character(s) trimmed"
        in note,
        f"the note names the whitespace change with its exact counts ({collapsed}, {trimmed})",
        note,
    )
    check(
        "literal '_' preserved" in note,
        "the note reports the literal `_` as preserved (not repaired)",
        note,
    )
    check(
        messy_row.get("candidate_text", "").count(PLACEHOLDER)
        == messy_text.count(PLACEHOLDER),
        "the placeholder glyph count is identical in the capture and the proposal",
    )
    check(
        "captured_text:" in note and "captured_attribution:" in note and "captured_citation:" in note,
        "the note attributes every change to the captured field it came from (text/attribution/citation)",
        note,
    )
    check(
        messy_row.get("candidate_author")
        == " ".join(messy_attribution.translate(TEST_TRANSLATION).split()),
        "the messy fixture's curly-quoted attribution normalizes to a straight-quoted value",
        repr(messy_row.get("candidate_author")),
    )
    check(
        messy_row.get("candidate_source_ref")
        == " ".join(f"\u201c{repeated_citation}\u201d".translate(TEST_TRANSLATION).split()),
        "the messy fixture's curly-quoted citation normalizes to a straight-quoted value",
        repr(messy_row.get("candidate_source_ref")),
    )

    # The two real placeholder rows: never repaired.
    for row_id in placeholder_ids:
        candidate = candidate_row(store, candidate_of[row_id])
        captured = capture_row(store, capture_of[row_id])
        for row_field, candidate_field, capture_field in (
            ("quote_text", "candidate_text", "captured_text"),
            ("source_ref", "candidate_source_ref", "captured_citation"),
            ("author", "candidate_author", "captured_attribution"),
        ):
            source_count = rows[row_id][row_field].count(PLACEHOLDER)
            if not source_count:
                continue
            check(
                captured.get(capture_field, "").count(PLACEHOLDER) == source_count,
                f"row {row_id}'s capture carries `{row_field}`'s {source_count} literal `_` verbatim",
            )
            check(
                candidate.get(candidate_field, "").count(PLACEHOLDER) == source_count,
                f"row {row_id}'s proposal preserves `{row_field}`'s {source_count} `_` -- no glyph "
                f"was guessed",
                repr(candidate.get(candidate_field)),
            )
        check(
            "literal '_' preserved" in candidate.get("normalization_notes", ""),
            f"row {row_id}'s note says the placeholder was preserved",
            candidate.get("normalization_notes", ""),
        )

    # The clean row: nothing changed, and the note says so in W1.3's words.
    clean_candidate = candidate_of[clean_ids[0]]
    clean_row = candidate_row(store, clean_candidate)
    check(
        clean_row.get("normalization_notes") == gn.IDENTICAL_NOTE,
        f"the already-normalized row {clean_ids[0]} gets the note {gn.IDENTICAL_NOTE!r}",
        clean_row.get("normalization_notes", ""),
    )
    check(
        clean_row.get("candidate_text") == rows[clean_ids[0]]["quote_text"],
        "the already-normalized row's proposal is verbatim its capture",
    )

    # NFC.
    nfd_row = candidate_row(store, NFD_CANDIDATE)
    check(
        capture_row(store, NFD_CAPTURE).get("captured_text") == NFD_TEXT,
        "the decomposed capture is stored exactly as submitted (NFC is a proposal, not a capture edit)",
    )
    check(
        nfd_row.get("candidate_text") == unicodedata.normalize("NFC", NFD_TEXT),
        "the proposal recomposes the decomposed text to NFC",
        repr(nfd_row.get("candidate_text")),
    )
    check(
        "unicode: NFC recomposed" in nfd_row.get("normalization_notes", ""),
        "the note names the NFC recomposition",
        nfd_row.get("normalization_notes", ""),
    )

    # Determinism + idempotency of the whole normalize pass.
    after_first = export_bytes(store)
    proc = run(NORMALIZE, "normalize", "--dir", store, "--all")
    check(
        proc.returncode == 0 and "no-op" in out_text(proc),
        "a second normalize --all is a no-op (every candidate already carries its proposal)",
        out_text(proc).strip()[:170],
    )
    check(
        export_bytes(store) == after_first,
        "normalizing twice in a row exports byte-identical text (the pass is idempotent)",
    )

    # A batch that can normalize nothing is a failure, not a pass (ruling 3's other half).
    print("\n-- a batch that normalizes nothing is a refusal, not a silent pass --")
    lonely = scratch / "store_only_whitespace"
    run(STORE_CLI, "create", "--dir", lonely)
    lonely_proc = run(
        SUBMIT, "submit", "--dir", lonely, "--text", WHITESPACE_ONLY,
        "--capture-method", "pasted-text", "--json",
    )
    check(lonely_proc.returncode == 0, "the whitespace-only store accepts its one submission")
    lonely_before = export_bytes(lonely)
    lonely_norm = run(NORMALIZE, "normalize", "--dir", lonely, "--all")
    refusal(
        "a batch normalize where every candidate is unnormalizable",
        lonely_norm,
        "nothing could be normalized",
        lonely,
        lonely_before,
    )

    # -- 3. duplicate hints ----------------------------------------------------------------
    print("\n-- duplicate hints: deterministic, cited, and never a state --")
    decisions_before = counts(store)["decisions"]
    proc = run(NORMALIZE, "hints", "--dir", store, "--all")
    transcript = out_text(proc)
    check(
        proc.returncode == 0 and "RESULT: PASS" in transcript,
        "hints --all is accepted (exit 0, RESULT: PASS)",
        transcript.strip()[:200],
    )
    check("Traceback" not in transcript, "hints prints no traceback")
    check(
        f">= {gn.NEAR_TEXT_THRESHOLD:.2f}" in transcript,
        "the transcript states the documented threshold",
    )
    check(
        "hints are not decisions" in transcript,
        "the transcript says out loud that a hint is not a state",
    )

    def kinds_between(left_id: str, right_id: str) -> set[str]:
        return {
            row["kind"]
            for row in hint_rows(store, left_id)
            if row["target"] == right_id
        }

    a, b = candidate_of[near_pair[0]], candidate_of[near_pair[1]]
    check(
        "near-text" in kinds_between(a, b) and "near-text" in kinds_between(b, a),
        f"the id {near_pair[0]} ~ {near_pair[1]} pair gets a near-text hint in both directions",
        str(kinds_between(a, b)),
    )
    check(
        "same-reference" not in kinds_between(a, b) and "same-passage" not in kinds_between(a, b),
        "the near-text pair carries two different citations, so it is neither same-reference nor "
        "same-passage",
    )
    near_basis = next(
        row["basis"] for row in hint_rows(store, a) if row["target"] == b and row["kind"] == "near-text"
    )
    check(
        f"{near_similarity:.2f}" in near_basis,
        f"the near-text basis carries the measured similarity ({near_similarity:.2f})",
        near_basis,
    )
    check(
        f">= {gn.NEAR_TEXT_THRESHOLD:.2f}" in near_basis and "difflib" in near_basis,
        "the near-text basis names the threshold and the algorithm",
        near_basis,
    )

    c, d = candidate_of[specific_pair[0]], candidate_of[specific_pair[1]]
    check(
        kinds_between(c, d) == {"same-reference"} and kinds_between(d, c) == {"same-reference"},
        "the shared-specific-citation pair gets exactly a same-reference hint in both directions "
        "(not same-passage: it is below the threshold)",
        f"{sorted(kinds_between(c, d))} / {sorted(kinds_between(d, c))}",
    )
    shared_reference_basis = next(
        row["basis"] for row in hint_rows(store, c) if row["target"] == d
    )
    check(
        rows[specific_pair[0]]["source_ref"] in shared_reference_basis,
        "the same-reference basis quotes the shared citation verbatim",
        shared_reference_basis,
    )

    print("-- the generic-label false positive (DATA_QUALITY_REPORT.md) --")
    for left_id, right_id in legacy_flagged:
        left, right = candidate_of[left_id], candidate_of[right_id]
        kinds = kinds_between(left, right) | kinds_between(right, left)
        check(
            not ({"same-reference", "same-passage"} & kinds),
            f"the legacy heuristic flags rows {left_id} ~ {right_id} on the shared label "
            f"{rows[left_id]['source_ref']!r}, and W1.4 emits no same-reference/same-passage hint "
            f"for them",
            str(sorted(kinds)),
        )
    title_left, title_right = candidate_of[title_pair[0]], candidate_of[title_pair[1]]
    check(
        not (
            {"same-reference", "same-passage"}
            & (kinds_between(title_left, title_right) | kinds_between(title_right, title_left))
        ),
        f"the bare work title {rows[title_pair[0]]['source_ref']!r} produces no reference hint either",
    )

    x, y = candidate_of[verse_pair[0]], candidate_of[verse_pair[1]]
    check(
        "near-text" in kinds_between(x, y) and "same-reference" not in kinds_between(x, y),
        "two verses of the same work (different pinpoint citations) are near-text but not "
        "same-reference",
        str(sorted(kinds_between(x, y))),
    )
    left_text = gn.normalize_text(rows[verse_pair[0]]["quote_text"]).casefold()
    right_text = gn.normalize_text(rows[verse_pair[1]]["quote_text"]).casefold()
    check(
        abs(gn.similarity(left_text, right_text) - gn.similarity(right_text, left_text)) < 1e-12,
        "the similarity of a pair is symmetric (the same number reaches both candidates' hints)",
    )
    basis_x = next(row["basis"] for row in hint_rows(store, x) if row["target"] == y)
    basis_y = next(row["basis"] for row in hint_rows(store, y) if row["target"] == x)
    check(
        re.search(r"similarity ([\d.]+)", basis_x).group(1)
        == re.search(r"similarity ([\d.]+)", basis_y).group(1),
        "the two candidates' near-text bases report the identical similarity number",
        f"{basis_x!r} vs {basis_y!r}",
    )

    print("-- exact-text and same-passage (the positive controls) --")
    for other, label in ((exact_b, "a repeated submission with the same specific citation"),):
        kinds = kinds_between(exact_a, other)
        check(
            {"exact-text", "same-reference", "same-passage"} <= kinds,
            f"{label} gets exact-text, same-reference and same-passage hints",
            str(sorted(kinds)),
        )
    check(
        kinds_between(generic_exact_a, generic_exact_b) == {"exact-text"},
        "the same text under a *generic* label gets exact-text only -- the reference guard still "
        "suppresses the citation hints",
        str(sorted(kinds_between(generic_exact_a, generic_exact_b))),
    )
    exact_basis = next(
        row["basis"] for row in hint_rows(store, exact_a) if row["kind"] == "exact-text"
    )
    check(
        "normalized text identical" in exact_basis and "case-folded" in exact_basis,
        "the exact-text basis says what was identical and how it was compared",
        exact_basis,
    )

    print("-- hints are derived data, not states --")
    every_hint_ok = True
    target_ok = True
    known_candidates = set(all_candidate_ids(store))
    for candidate_id in sorted(all_candidate_ids(store)):
        rows_here = hint_rows(store, candidate_id)
        if [row["hint_seq"] for row in rows_here] != list(range(1, len(rows_here) + 1)):
            every_hint_ok = False
        for row in rows_here:
            if row["kind"] not in HINT_KINDS or not row["basis"] or not row["target"]:
                every_hint_ok = False
            if row["target"] not in known_candidates:
                target_ok = False
    check(every_hint_ok, "every hint has a declared kind, a non-empty basis, and is gapless from 1")
    check(target_ok, "every hint target resolves to a candidate in the store")
    ordering_ok = True
    for candidate_id in sorted(all_candidate_ids(store)):
        keys = [(row["target"], row["kind"]) for row in hint_rows(store, candidate_id)]
        documented = sorted(keys, key=lambda pair: (pair[0], gn.KIND_ORDER.index(pair[1])))
        if keys != documented:
            ordering_ok = False
    check(
        ordering_ok,
        "every candidate's hints are stored in the documented (target, kind) order, so hint_seq is "
        "stable across rebuilds and diffable",
    )
    check(
        set(gn.KIND_ORDER) == set(HINT_KINDS) and len(gn.KIND_ORDER) == 4,
        "the documented kind order covers exactly the contract's four hint kinds",
    )
    check(
        {row["kind"] for candidate_id in known_candidates for row in hint_rows(store, candidate_id)}
        <= set(HINT_KINDS),
        "no hint kind outside the contract vocabulary reached the store",
    )
    states = {candidate_row(store, cid).get("curation_state") for cid in known_candidates}
    check(
        states == {"new"},
        "no curation_state was written by normalizing or hinting: every candidate is still 'new'",
        str(sorted(states)),
    )
    check(
        "duplicate" not in states,
        "no candidate was marked 'duplicate' by a hint (T-C4/T-C7/T-C9 remain the operator's)",
    )
    check(
        {candidate_row(store, cid).get("research_state") for cid in known_candidates}
        == {"not_started"},
        "research_state is untouched by W1.4 (an intake transform implies no research)",
    )
    check(
        all(
            candidate_row(store, cid).get(key) == value
            for cid in known_candidates
            for key, value in INTAKE_STATES.items()
        ),
        "all four dimensions are still at their intake values after normalize + hints",
    )
    check(
        counts(store)["decisions"] == decisions_before == 0,
        "normalize and hints wrote no decision row at all (the append-only log is still empty)",
    )

    print("-- rebuilds are idempotent and replace rather than accumulate --")
    hint_total = counts(store)["duplicate_hints"]
    check(hint_total > 0, "the fixture batch produced at least one hint", str(hint_total))
    stable = export_bytes(store)
    proc = run(NORMALIZE, "hints", "--dir", store, "--all")
    check(proc.returncode == 0, "a hint rebuild is accepted", out_text(proc).strip()[:170])
    check(
        export_bytes(store) == stable,
        "rebuilding every hint exports byte-identical text (derived, deterministic, not appended)",
    )
    check(
        counts(store)["duplicate_hints"] == hint_total,
        "the rebuild replaced the rows instead of accumulating a second set",
        f"{counts(store)['duplicate_hints']} vs {hint_total}",
    )
    for _ in range(2):
        run(NORMALIZE, "hints", "--dir", store, "--all")
    check(
        counts(store)["duplicate_hints"] == hint_total and export_bytes(store) == stable,
        "three rebuilds in a row leave the same rows in the same order",
    )
    single = run(
        NORMALIZE, "hints", "--dir", store, "--candidate-id", candidate_of[near_pair[0]], "--json"
    )
    payload = first_json(single)
    check(single.returncode == 0, "a single-candidate rebuild is accepted")
    check(
        export_bytes(store) == stable,
        "rebuilding one candidate's hints is deterministic too (no change in the export)",
    )
    check(
        payload.get("counts", {}).get("duplicate_hints") == hint_total,
        "the single-candidate rebuild reported the store's real hint count",
    )

    # -- 4. the store's own contract still holds after W1.4's writes ------------------------
    print("\n-- W1.4's writes do not break W1.2's envelope contract --")
    with Store(store) as live:
        captures = capture_texts(live)
        violations = []
        for candidate_id in sorted(all_candidate_ids(store)):
            violations += validate(read_envelope(live, candidate_id), captures)
        fields_ok = all(
            sorted(read_envelope(live, candidate_id)) == sorted(REQUIRED_FIELDS)
            for candidate_id in sorted(all_candidate_ids(store))
        )
    check(not violations, "every stored envelope still re-validates with zero violations", str(violations[:2]))
    check(fields_ok, "every stored envelope still carries exactly the 21 required fields")
    check(
        read_envelope(Store(store), candidate_of[near_pair[0]])["duplicate_hints"]
        == [
            {"kind": row["kind"], "target": row["target"], "basis": row["basis"]}
            for row in hint_rows(store, candidate_of[near_pair[0]])
        ],
        "the stored hints are what read_envelope reports (rule 4 sees the real rows)",
    )

    # -- 5. refusals write nothing ---------------------------------------------------------
    print("\n-- the surface's own guards, not only the store's (layering is asserted) --")
    guard_target = candidate_of[clean_ids[0]]
    set_curation_state(store, guard_target, "accepted")
    decided_export = export_bytes(store)
    batch = run(NORMALIZE, "normalize", "--dir", store, "--all")
    batch_text = out_text(batch)
    check(
        batch.returncode == 0 and f"SKIPPED: {guard_target}" in batch_text,
        "a batch run skips a decided candidate instead of aborting the whole batch",
        batch_text.strip()[:200],
    )
    check(
        "intake-time operation" in batch_text,
        "the skip is refused by the submission surface's own guard, not delegated to the store "
        "(both layers are load-bearing and both are asserted)",
        batch_text.strip()[:200],
    )
    check(
        export_bytes(store) == decided_export,
        "the skipped decided candidate's row is byte-identical (its proposal is not re-derived "
        "after a decision)",
    )
    set_curation_state(store, guard_target, "new")
    check(
        candidate_row(store, guard_target).get("curation_state") == "new"
        and candidate_row(store, guard_target).get("candidate_text")
        == gn.normalize_text(rows[clean_ids[0]]["quote_text"]),
        "the scaffolding state is restored, with the candidate's proposal intact, for the CLI "
        "refusals below",
    )

    print("\n-- the store's own write path refuses too (each layer has its own falsifier) --")
    from garden_store import StoreError  # local: only this block needs it

    # The empty-value guards are probed on a candidate that is still 'new', so the intake-state
    # guard cannot mask what is being tested (the reverse of the layering asserted above).
    empty_value_refusals = (
        ("an empty proposal", {"candidate_text": "", "candidate_author": "y",
                               "candidate_source_ref": "z", "normalization_notes": "n"},
         "candidate_text"),
        ("an empty note", {"candidate_text": "x", "candidate_author": "y",
                           "candidate_source_ref": "z", "normalization_notes": ""},
         "normalization_notes"),
    )
    for label, kwargs, needle in empty_value_refusals:
        try:
            with Store(store) as live:
                live.apply_normalization(guard_target, **kwargs)
            fail(f"the store's apply_normalization accepted {label} -- it must refuse")
        except StoreError as exc:
            check(
                needle in str(exc) and "curation_state" not in str(exc),
                f"the store's own apply_normalization refuses {label} and names {needle!r}",
                str(exc)[:170],
            )
        except Exception as exc:  # noqa: BLE001 -- the point is to name the layer that refused
            fail(
                f"the store's apply_normalization refused {label} with {type(exc).__name__} "
                f"instead of its own StoreError guard: {exc}"
            )
    set_curation_state(store, guard_target, "accepted")
    guarded_export = export_bytes(store)
    store_layer_refusals = (
        ("a decided candidate", {"candidate_text": "x", "candidate_author": "y",
                                 "candidate_source_ref": "z", "normalization_notes": "n"},
         "curation_state"),
    )
    for label, kwargs, needle in store_layer_refusals:
        try:
            with Store(store) as live:
                live.apply_normalization(guard_target, **kwargs)
            fail(f"the store's apply_normalization accepted {label} -- it must refuse")
        except StoreError as exc:
            check(
                needle in str(exc),
                f"the store's own apply_normalization refuses {label} and names {needle!r}",
                str(exc)[:170],
            )
    check(
        export_bytes(store) == guarded_export,
        "the refused store-layer calls wrote nothing at all",
    )
    set_curation_state(store, guard_target, "new")
    check(
        candidate_row(store, guard_target).get("curation_state") == "new"
        and candidate_row(store, guard_target).get("candidate_text")
        == gn.normalize_text(rows[clean_ids[0]]["quote_text"]),
        "the scaffolding state is restored, with the candidate's proposal intact, for the CLI "
        "refusals below",
    )

    print("\n-- refusals (every one names its field/flag and writes nothing) --")
    before_export = export_bytes(store)
    refusal(
        "a normalize with neither --candidate-id nor --all",
        run(NORMALIZE, "normalize", "--dir", store),
        "--candidate-id",
        store,
        before_export,
    )
    refusal(
        "a normalize with both --candidate-id and --all",
        run(
            NORMALIZE, "normalize", "--dir", store, "--all",
            "--candidate-id", candidate_of[near_pair[0]],
        ),
        "exactly one of",
        store,
        before_export,
    )
    refusal(
        "a hints run with neither selection",
        run(NORMALIZE, "hints", "--dir", store),
        "--all",
        store,
        before_export,
    )
    refusal(
        "a normalize for a candidate that does not exist",
        run(NORMALIZE, "normalize", "--dir", store, "--candidate-id", "cand-1999-01-01-0001"),
        "no candidate",
        store,
        before_export,
    )
    refusal(
        "a hints run for a candidate that does not exist",
        run(NORMALIZE, "hints", "--dir", store, "--candidate-id", "cand-1999-01-01-0001"),
        "no candidate",
        store,
        before_export,
    )
    refusal(
        "a normalize of a whitespace-only capture",
        run(NORMALIZE, "normalize", "--dir", store, "--candidate-id", whitespace_candidate),
        "candidate_text",
        store,
        before_export,
    )
    check(
        candidate_row(store, whitespace_candidate).get("candidate_text") == WHITESPACE_ONLY,
        "the whitespace-only candidate is untouched by the refused run (its proposal is unchanged)",
    )
    set_curation_state(store, candidate_of[clean_ids[0]], "accepted")
    after_state_change = export_bytes(store)
    refusal(
        "a normalize of an already-decided candidate",
        run(NORMALIZE, "normalize", "--dir", store, "--candidate-id", candidate_of[clean_ids[0]]),
        "curation_state",
        store,
        after_state_change,
    )
    set_curation_state(store, candidate_of[clean_ids[0]], "new")
    check(
        export_bytes(store) == before_export,
        "restoring the scaffolding state returns the store to its pre-refusal bytes",
    )

    # -- 6. the read-only, no-store commands ------------------------------------------------
    print("\n-- the read-only helpers --")
    classified = run(NORMALIZE, "classify", "--reference", rows[generic_group[0]]["source_ref"])
    check(
        classified.returncode == 0 and "specificity: generic" in out_text(classified),
        "classify reports the corpus's generic label as generic on the real CLI",
        out_text(classified).strip()[:170],
    )
    described = run(NORMALIZE, "describe", "--text", messy_text)
    check(
        described.returncode == 0
        and "RESULT: PASS" in out_text(described)
        and "whitespace:" in out_text(described),
        "describe prints the note part for a text and exits cleanly, without touching any store",
    )
    check(
        export_bytes(store) == before_export,
        "the read-only helpers left the store byte-identical",
    )


if __name__ == "__main__":
    sys.exit(main())
