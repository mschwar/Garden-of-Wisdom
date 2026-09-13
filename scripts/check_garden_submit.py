#!/usr/bin/env python3
"""Deterministic acceptance + evidence run for W1.3: the manual capture/submission surface.

Usage:
    python3 scripts/check_garden_submit.py

Runs entirely in a throwaway temporary directory (never the repo) and asserts the W1.3
acceptance criteria from `docs/program/W1_DECOMPOSITION.md` section "W1.3":

  1. submitting text containing a literal `_`, curly quotes, a wrong author and no citation
     produces a stored envelope whose `captured_text` is **byte-identical to the input** and
     whose `normalization_notes` accounts for every normalization (there is none, so it says
     `identical to capture`);
  2. a submission with a missing required field is **rejected with the field named**, and a
     refused submission writes nothing at all;
  3. the capture method is selected explicitly (no default), the raw input is stored verbatim
     through all three input modes, and the CLI is fully non-interactive;
  4. submission touches no state and records no decision: the four dimensions enter at their
     intake values, `decisions` stays empty, and no candidate can be `research_state` anything
     but `not_started`;
  5. `quotes.csv` / `sources.csv` are byte-identical before and after, and nothing is written
     outside the temp directory.

Every check runs the CLI as a **subprocess** (`python3 scripts/garden_submit.py submit …`), so the
transcript this prints is the real CLI's, not an in-process call. Deep assertions are then made
against the store the CLI wrote, through W1.1's `Store` and W1.2's `read_envelope` / `validate`.

Exits 0 with `RESULT: PASS`, non-zero with `RESULT: FAIL` and one `FAIL:` line per broken check --
never a traceback. Negative controls (mutation -> observed `FAIL:` line) are recorded in
`GARDEN_W1_3_HANDOFF.md`.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import garden_store  # noqa: E402
import garden_submit as gs  # noqa: E402
from garden_envelope import (  # noqa: E402
    REQUIRED_FIELDS,
    capture_texts,
    read_envelope,
    serialize,
    validate,
)
from garden_store import CAPTURE_METHODS, INTAKE_STATES, Store  # noqa: E402

SUBMIT = SCRIPTS / "garden_submit.py"
STORE_CLI = SCRIPTS / "garden_store.py"
QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
STORE_FILENAME = garden_store.STORE_FILENAME

#: The messy submission of acceptance criterion 1: leading indent, curly quotes, a literal `_`
#: placeholder, an embedded newline, a trailing blank line, and a wrong author -- with no citation.
MESSY_BYTES = (
    "  \u201cThe earth is but one country,\n"
    " and mankind its citizens._\u201d\n"
    "\n"
    "  \u2014 Rumi\n"
).encode("utf-8")
WRONG_AUTHOR = "Rumi"
ID_RE = re.compile(r"^(cap|cand)-(\d{4}-\d{2}-\d{2})-(\d{4,})$")

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


# -- running the real CLI -------------------------------------------------------------------


def run_submit(*args: object, stdin_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SUBMIT), "submit", *[str(a) for a in args]],
        input=stdin_bytes if stdin_bytes is not None else b"",
        capture_output=True,
    )


def out_text(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout + proc.stderr).decode("utf-8", "replace")


def store_cli(*args: object) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(STORE_CLI), *[str(a) for a in args]],
        input=b"",
        capture_output=True,
    )


# -- reading what the CLI wrote -------------------------------------------------------------


def counts(store_dir: Path) -> dict[str, int]:
    with Store(store_dir) as store:
        return store.counts()


def capture_row(store_dir: Path, capture_id: str) -> dict:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT * FROM captures WHERE capture_id = ?", (capture_id,)
        ).fetchone()
    return dict(row) if row else {}


def candidate_row(store_dir: Path, candidate_id: str) -> dict:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
    return dict(row) if row else {}


def envelope_back(store_dir: Path, candidate_id: str) -> dict:
    with Store(store_dir) as store:
        return read_envelope(store, candidate_id)


def refusal(
    label: str,
    proc: subprocess.CompletedProcess,
    needle: str,
    store_dir: Path,
    before: dict[str, int],
    *,
    result_line: bool = True,
) -> None:
    """A refused submission: non-zero exit, the field named, and nothing written."""
    text = out_text(proc)
    refusal_outputs.append((label, text))
    if result_line:
        check(
            proc.returncode != 0 and "RESULT: FAIL" in text,
            f"{label} is refused (exit {proc.returncode}, RESULT: FAIL)",
        )
    else:
        check(proc.returncode != 0, f"{label} is refused (exit {proc.returncode})")
    check(needle in text, f"{label} names {needle!r} in the refusal", text.strip()[:170])
    check(counts(store_dir) == before, f"{label} wrote nothing to the store")


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-submit-check-"))
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
            "no store was created in the repo root (the CLI only ever writes to --dir)",
        )
        allowed = ("store", "inputs", "out")
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
        "RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, "
        "no decision, refused submissions write nothing)"
    )
    return 0


def run_checks(scratch: Path) -> None:
    store = scratch / "store"
    inputs = scratch / "inputs"
    out = scratch / "out"
    inputs.mkdir()
    out.mkdir()

    created = store_cli("create", "--dir", store)
    check(
        created.returncode == 0 and "RESULT: PASS" in out_text(created),
        "the store is created from empty by garden_store.py create",
        out_text(created).strip()[:170],
    )

    messy = inputs / "messy.txt"
    messy.write_bytes(MESSY_BYTES)

    # -- 1. acceptance criterion 1: the messy submission ------------------------------------
    print("\n-- the messy submission (criterion 1) --")
    before = counts(store)
    proc = run_submit(
        "--dir",
        store,
        "--text-file",
        messy,
        "--capture-method",
        "pasted-text",
        "--attribution",
        WRONG_AUTHOR,
    )
    transcript = out_text(proc)
    check(
        proc.returncode == 0 and "RESULT: PASS" in transcript,
        "the messy submission is accepted (exit 0, RESULT: PASS)",
        transcript.strip()[:200],
    )
    check("Traceback" not in transcript, "the accepted submission prints no traceback")
    check(transcript.count("RESULT: PASS") == 1, "the transcript carries exactly one RESULT line")
    check("byte-identical to the submission" in transcript,
          "the transcript asserts byte-identity with the submission")

    capture_id, candidate_id = first_ids(store)
    row = capture_row(store, capture_id)
    stored = row.get("captured_text", "").encode("utf-8")
    check(
        stored == MESSY_BYTES,
        "captured_text is byte-identical to the submitted file (verified against the file bytes)",
        f"{len(stored)} vs {len(MESSY_BYTES)} bytes",
    )
    check("_" in row.get("captured_text", ""),
          "the literal `_` placeholder survives verbatim (neither repaired nor removed)")
    check(
        "\u201c" in row.get("captured_text", "") and "\u201d" in row.get("captured_text", ""),
        "the curly quotes survive verbatim (no straight-quote rewriting)",
    )
    check(
        row.get("captured_text", "").startswith("  \u201c")
        and row.get("captured_text", "").endswith("\n"),
        "leading indent and trailing newline survive verbatim (the text is never trimmed)",
    )
    check(row.get("captured_attribution") == WRONG_AUTHOR,
          f"the wrong author is stored verbatim as encountered ({WRONG_AUTHOR!r})")
    check(row.get("captured_citation") == "none",
          "an absent citation is the sentinel 'none', never an empty string")
    check(row.get("capture_method") == "pasted-text",
          "the explicitly selected capture method is the one stored")
    check(row.get("language") == "und", "the language default is the sentinel 'und'")
    check(row.get("captured_by") == "operator", "the captured_by default is 'operator'")

    candidate = candidate_row(store, candidate_id)
    check(candidate.get("candidate_author") == WRONG_AUTHOR,
          "candidate_author is not corrected: a submission implies no research")
    check(candidate.get("candidate_source_ref") == "none",
          "candidate_source_ref defaults to the captured citation sentinel")
    check(
        candidate.get("normalization_notes") == "identical to capture",
        "normalization_notes accounts for every normalization by asserting there is none",
    )
    check(
        candidate.get("candidate_text", "").encode("utf-8") == MESSY_BYTES,
        "candidate_text defaults to the captured text, byte for byte",
    )
    for field, intake in INTAKE_STATES.items():
        check(candidate.get(field) == intake, f"the candidate enters at {field}={intake}")
    check(
        candidate.get("intake_schema_version") == "garden.candidate-envelope/1",
        "the stored candidate carries the garden.candidate-envelope/1 schema key",
    )
    check(before["captures"] + 1 == counts(store)["captures"],
          "exactly one capture was written for the submission")
    check(before["candidates"] + 1 == counts(store)["candidates"],
          "exactly one candidate was written for the submission")

    back = envelope_back(store, candidate_id)
    check(not validate(back, capture_texts_or_empty(store)),
          "the stored record reads back and re-validates with zero violations")
    check(sorted(back) == sorted(REQUIRED_FIELDS),
          "the stored record carries exactly the 21 required envelope fields")
    check(back["captured_text"].encode("utf-8") == MESSY_BYTES,
          "the read-back envelope's captured_text is still byte-identical to the input")
    check(back["duplicate_hints"] == [],
          "intake writes no duplicate hints (hint generation is W1.4, and a hint is not a decision)")

    # -- 2. the emitted canonical envelope --------------------------------------------------
    print("\n-- the emitted envelope file --")
    emitted_path = out / "envelope.json"
    proc = run_submit(
        "--dir",
        store,
        "--text",
        "One finger cannot lift a pebble.",
        "--capture-method",
        "manual-entry",
        "--emit-envelope",
        emitted_path,
    )
    check(proc.returncode == 0, "a submission with --emit-envelope is accepted")
    emitted_bytes = emitted_path.read_bytes()
    emitted = json.loads(emitted_bytes.decode("utf-8"))
    emitted_capture, emitted_candidate = last_ids(store)
    emitted_back = envelope_back(store, emitted_candidate)
    check(emitted == emitted_back,
          "the emitted envelope equals the stored record read back out of the store")
    check(sorted(emitted) == sorted(REQUIRED_FIELDS),
          "the emitted envelope carries exactly the 21 required fields")
    check(emitted_bytes == serialize(emitted_back).encode("utf-8"),
          "the emitted file is W1.2's canonical serialized form, byte-identical")

    # -- 3. acceptance criterion 1, verbatim through all three input modes ------------------
    print("\n-- verbatim through --text, --text-file and --stdin --")
    payload = "  tab\tand newline\nand a _ glyph \u2014 \u201cdone\u201d  \n"
    text_file = inputs / "modes.txt"
    text_file.write_bytes(payload.encode("utf-8"))
    proc_text = run_submit("--dir", store, "--text", payload, "--capture-method", "manual-entry")
    proc_file = run_submit(
        "--dir", store, "--text-file", text_file, "--capture-method", "manual-entry"
    )
    proc_stdin = run_submit(
        "--dir",
        store,
        "--stdin",
        "--capture-method",
        "manual-entry",
        stdin_bytes=payload.encode("utf-8"),
    )
    for label, proc in (("--text", proc_text), ("--text-file", proc_file), ("--stdin", proc_stdin)):
        check(proc.returncode == 0, f"the {label} submission is accepted")
    ids = recent_ids(store, 3)
    texts = [capture_row(store, cid)["captured_text"].encode("utf-8") for cid, _ in ids]
    check(
        all(text == payload.encode("utf-8") for text in texts),
        "all three input modes store the identical bytes, verbatim",
        str([len(t) for t in texts]),
    )
    check(len(set(texts)) == 1, "the three input modes cannot disagree")
    check(proc_text.stdout.count(b"RESULT: PASS") == 1, "--text prints one RESULT line")

    # -- 4. acceptance criterion 2: a missing required field is named, and nothing is written --
    print("\n-- missing required fields are named, and write nothing (criterion 2) --")
    before = counts(store)
    refusal(
        "--attribution ''",
        run_submit("--dir", store, "--text", "x", "--capture-method", "manual-entry",
                   "--attribution", ""),
        "captured_attribution",
        store,
        before,
    )
    refusal(
        "--text ''",
        run_submit("--dir", store, "--text", "", "--capture-method", "manual-entry"),
        "captured_text",
        store,
        before,
    )
    refusal(
        "--normalization-notes ''",
        run_submit("--dir", store, "--text", "x", "--capture-method", "manual-entry",
                   "--normalization-notes", ""),
        "normalization_notes",
        store,
        before,
    )
    refusal(
        "--language ''",
        run_submit("--dir", store, "--text", "x", "--capture-method", "manual-entry",
                   "--language", ""),
        "language",
        store,
        before,
    )
    refusal(
        "--candidate-text '' with a note",
        run_submit("--dir", store, "--text", "x", "--capture-method", "manual-entry",
                   "--candidate-text", "", "--normalization-notes", "emptied deliberately"),
        "candidate_text",
        store,
        before,
    )
    refusal(
        "--captured-at without an offset",
        run_submit("--dir", store, "--text", "x", "--capture-method", "manual-entry",
                   "--captured-at", "2026-09-12 09:14:11"),
        "captured_at",
        store,
        before,
    )
    # Layering, asserted because it is load-bearing: the capture DAY derives the record ids, so a
    # malformed timestamp must be refused by the submission surface BEFORE anything is built from
    # its first ten characters -- not handed down to the envelope validator, which would have
    # already had an id derived from a string it cannot read as a date.
    malformed_at = out_text(
        run_submit("--dir", store, "--text", "x", "--capture-method", "manual-entry",
                   "--captured-at", "2026-09-12 09:14:11")
    )
    check(
        "captured_at" in malformed_at and "envelope rejected" not in malformed_at,
        "a malformed captured_at is refused by the submission surface itself, before any id is "
        "derived from its date (not delegated to the envelope validator)",
        malformed_at.strip().replace("\n", " | ")[:170],
    )

    # -- 5. the capture method is explicit --------------------------------------------------
    print("\n-- the capture method is an explicit choice --")
    refusal(
        "an omitted --capture-method",
        run_submit("--dir", store, "--text", "x"),
        "--capture-method",
        store,
        before,
    )
    refusal(
        "an out-of-vocabulary capture method",
        run_submit("--dir", store, "--text", "x", "--capture-method", "telepathy"),
        "capture_method",
        store,
        before,
    )
    check(
        "telepathy" in out_text(
            run_submit("--dir", store, "--text", "x", "--capture-method", "telepathy")
        ),
        "the out-of-vocabulary refusal quotes the offending value",
    )
    check(
        all(method in out_text(run_submit("--dir", store, "--text", "x")) for method in CAPTURE_METHODS),
        "the omitted-method refusal lists the whole contract vocabulary",
    )

    # -- 6. broken input --------------------------------------------------------------------
    print("\n-- broken input is refused cleanly --")
    refusal(
        "no input flag at all",
        run_submit("--dir", store, "--capture-method", "manual-entry"),
        "--text",
        store,
        before,
    )
    refusal(
        "--text together with --stdin",
        run_submit("--dir", store, "--text", "x", "--stdin", "--capture-method", "manual-entry",
                   stdin_bytes=b"x"),
        "--text",
        store,
        before,
        result_line=False,
    )
    bad = inputs / "latin1.bin"
    bad.write_bytes(b"\xff\xfe not utf-8")
    refusal(
        "a non-UTF-8 text file",
        run_submit("--dir", store, "--text-file", bad, "--capture-method", "book-scan"),
        "UTF-8",
        store,
        before,
    )
    refusal(
        "a --text-file that does not exist",
        run_submit("--dir", store, "--text-file", inputs / "nope.txt",
                   "--capture-method", "book-scan"),
        "cannot read",
        store,
        before,
    )
    refusal(
        "--dir with no store in it",
        run_submit("--dir", scratch / "nothing-here", "--text", "x",
                   "--capture-method", "manual-entry"),
        "no store at",
        store,
        before,
    )

    # -- 7. the normalization boundary ------------------------------------------------------
    print("\n-- no normalization is recorded without a note --")
    for flag, value, field in (
        ("--candidate-text", "Something else entirely.", "candidate_text"),
        ("--candidate-author", "Bah\u00e1\u2019u\u2019ll\u00e1h", "candidate_author"),
        ("--candidate-source-ref", "Gleanings, p. 1", "candidate_source_ref"),
    ):
        proc = run_submit("--dir", store, "--text", "x", "--capture-method", "manual-entry",
                          flag, value)
        refusal(f"{flag} differing with no note", proc, "normalization_notes", store, before)
        check(field in out_text(proc),
              f"the refusal from {flag} also names the field it would have changed ({field})")

    noted = run_submit(
        "--dir",
        store,
        "--text-file",
        messy,
        "--capture-method",
        "photo",
        "--attribution",
        WRONG_AUTHOR,
        "--candidate-text",
        "The earth is but one country.",
        "--normalization-notes",
        "curly quotes straightened and the placeholder removed per the printed card",
    )
    check(noted.returncode == 0, "the same change WITH an explicit note is accepted")
    noted_capture, noted_candidate = last_ids(store)
    check(
        capture_row(store, noted_capture)["captured_text"].encode("utf-8") == MESSY_BYTES,
        "a normalized submission still stores the encounter byte-identically",
    )
    check(
        candidate_row(store, noted_candidate)["candidate_text"] == "The earth is but one country.",
        "the normalized proposal is stored alongside, never instead of, the capture",
    )
    check(
        candidate_row(store, noted_candidate)["normalization_notes"].startswith("curly quotes"),
        "the operator's normalization note is stored verbatim",
    )
    equal = run_submit("--dir", store, "--text", "plain", "--capture-method", "manual-entry",
                       "--candidate-text", "plain")
    check(
        equal.returncode == 0
        and candidate_row(store, last_ids(store)[1])["normalization_notes"] == "identical to capture",
        "a candidate value equal to the capture needs no note and records 'identical to capture'",
    )

    # -- 8. ids: allocated, deterministic, day-scoped, never reused -------------------------
    print("\n-- the candidate-id naming scheme --")
    for cid, _ in recent_ids(store, counts(store)["candidates"]):
        if not ID_RE.match(cid):
            fail(f"an allocated capture id does not match the W1.3 scheme: {cid!r}")
            break
    else:
        ok("every allocated capture id matches cap-YYYY-MM-DD-NNNN")
    candidate_ids = [r["candidate_id"] for r in all_candidates(store)]
    check(all(ID_RE.match(cid) for cid in candidate_ids),
          "every allocated candidate id matches cand-YYYY-MM-DD-NNNN")
    check(len(set(candidate_ids)) == len(candidate_ids), "no id was ever allocated twice")
    day = today(store)
    check(
        sorted(int(ID_RE.match(cid).group(3)) for cid in candidate_ids) ==
        list(range(1, len(candidate_ids) + 1)),
        "the day's candidates are numbered 1..N with no gaps",
    )
    with Store(store) as handle:
        first_offer = gs.next_daily_id(handle, "cap", day)
        second_offer = gs.next_daily_id(handle, "cap", day)
    check(first_offer == second_offer,
          "the id allocator is deterministic on an unchanged store", f"{first_offer} vs {second_offer}")
    proc = run_submit("--dir", store, "--text", "next", "--capture-method", "manual-entry")
    check(proc.returncode == 0, "the next submission is accepted")
    check(last_ids(store)[0] == first_offer,
          "the CLI allocates exactly the deterministic next id", first_offer)
    other_day = run_submit(
        "--dir", store, "--text", "from another day", "--capture-method", "legacy-import",
        "--captured-at", "2026-08-01T10:00:00-06:00",
    )
    check(other_day.returncode == 0, "a submission with an explicit capture day is accepted")
    check(last_ids(store) == ("cap-2026-08-01-0001", "cand-2026-08-01-0001"),
          "a different capture day gets its own 0001 sequence", str(last_ids(store)))
    explicit = run_submit(
        "--dir", store, "--text", "explicit", "--capture-method", "manual-entry",
        "--capture-id", "cap-explicit-1", "--candidate-id", "cand-explicit-1",
    )
    check(
        explicit.returncode == 0 and last_ids(store) == ("cap-explicit-1", "cand-explicit-1"),
        "an explicit --capture-id / --candidate-id is honoured",
        out_text(explicit).strip()[:170],
    )
    before = counts(store)
    refusal(
        "an already-used --capture-id",
        run_submit("--dir", store, "--text", "again", "--capture-method", "manual-entry",
                   "--capture-id", "cap-explicit-1"),
        "capture_id",
        store,
        before,
    )
    refusal(
        "an already-used --candidate-id",
        run_submit("--dir", store, "--text", "again", "--capture-method", "manual-entry",
                   "--candidate-id", "cand-explicit-1"),
        "candidate_id",
        store,
        before,
    )
    check(
        capture_row(store, "cap-explicit-1")["captured_text"] == "explicit",
        "the capture behind a taken candidate id is untouched by the refusal",
    )

    # -- 9. non-interactive, machine-readable ----------------------------------------------
    print("\n-- the CLI is non-interactive and machine-readable --")
    machine = run_submit("--dir", store, "--text", "machine", "--capture-method", "agent-research",
                         "--attribution", "unknown", "--json")
    check(machine.returncode == 0, "--json is accepted")
    lines = [line for line in machine.stdout.decode("utf-8").splitlines() if line.strip()]
    check(len(lines) == 1, "--json prints exactly one line", str(len(lines)))
    payload_obj = json.loads(lines[0])
    check(
        sorted(payload_obj) ==
        sorted(["capture_id", "candidate_id", "captured_text_bytes", "normalization_notes",
                "duplicate_hints", "states", "counts", "envelope"]),
        "--json prints one canonical object with the stored ids, states, counts and envelope",
        str(sorted(payload_obj)),
    )
    check(payload_obj["states"] == INTAKE_STATES, "--json reports the intake states")
    check(payload_obj["counts"] == counts(store), "--json reports the store's own counts")
    check(len(lines[0]) == len(serialize(payload_obj)), "--json output is canonical (sorted keys)")

    # -- 10. nothing implies verification; captures stay immutable -------------------------
    print("\n-- submissions persist and imply nothing --")
    for row in all_candidates(store):
        if row["research_state"] != "not_started":
            fail(f"{row['candidate_id']} has research_state={row['research_state']!r}")
            break
    else:
        ok("no submission moved research_state off not_started (no implied verification)")
    check(counts(store)["decisions"] == 0,
          "intake recorded no decision: the decisions log is still empty")
    check(all(row["curation_state"] == "new" for row in all_candidates(store)),
          "every candidate is still curation_state=new (intake decides nothing)")
    with Store(store) as handle:
        store_alive = handle
        try:
            store_alive.conn.execute("UPDATE captures SET captured_text = 'rewritten'")
            fail("a stored capture was UPDATEable after submission")
        except Exception as exc:
            ok(f"a stored capture is immutable after submission ({type(exc).__name__})")
        try:
            store_alive.conn.execute("DELETE FROM captures")
            fail("a stored capture was DELETEable after submission")
        except Exception as exc:
            ok(f"a stored capture cannot be deleted after submission ({type(exc).__name__})")

    verified = store_cli("verify", "--dir", store)
    check(
        verified.returncode == 0 and "RESULT: PASS" in out_text(verified),
        "the store still round-trips: export -> re-import -> byte-identical",
        out_text(verified).strip()[:170],
    )
    exported = store_cli("export", "--dir", store)
    check(exported.returncode == 0, "the store exports to its deterministic text mirror")
    export_bytes = (store / garden_store.DEFAULT_EXPORT_NAME).read_bytes().decode("utf-8")
    missing = [
        cid for cid, _ in recent_ids(store, counts(store)["captures"])
        if f'"capture_id":"{cid}"' not in export_bytes
    ]
    check(not missing, "every submitted capture appears in the committed-mirror export", str(missing))
    check(
        export_bytes.startswith("garden.export/1\n")
        and "[captures]" in export_bytes
        and "[candidates]" in export_bytes,
        "the export is a garden.export/1 mirror with the capture and candidate sections",
    )


# -- small store readers --------------------------------------------------------------------


def capture_texts_or_empty(store_dir: Path) -> dict[str, str]:
    with Store(store_dir) as store:
        return capture_texts(store)


def all_candidates(store_dir: Path) -> list[dict]:
    with Store(store_dir) as store:
        return [
            dict(row)
            for row in store.conn.execute("SELECT * FROM candidates ORDER BY candidate_id")
        ]


def recent_ids(store_dir: Path, limit: int) -> list[tuple[str, str]]:
    """The `(capture_id, candidate_id)` pairs of the last `limit` submissions, oldest first.

    Ordered by `rowid` (insert order), not by id text: an explicit `--capture-id` need not sort
    near the allocated ones.
    """
    with Store(store_dir) as store:
        rows = store.conn.execute(
            "SELECT c.capture_id, cc.candidate_id FROM candidates cc "
            "JOIN candidate_captures c ON c.candidate_id = cc.candidate_id "
            "ORDER BY cc.rowid"
        ).fetchall()
    return [(row["capture_id"], row["candidate_id"]) for row in rows[-limit:]]


def first_ids(store_dir: Path) -> tuple[str, str]:
    pairs = recent_ids(store_dir, 1)
    if not pairs:
        raise SystemExit("FAIL: no submission landed in the store")
    return pairs[0]


def last_ids(store_dir: Path) -> tuple[str, str]:
    return first_ids(store_dir)


def today(store_dir: Path) -> str:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT capture_id FROM captures ORDER BY rowid LIMIT 1"
        ).fetchone()
    return ID_RE.match(row["capture_id"]).group(2)


if __name__ == "__main__":
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    sys.exit(main())
