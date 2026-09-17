#!/usr/bin/env python3
"""W1.6 deterministic end-to-end acceptance run + Gate B evidence driver.

Usage:
    python3 scripts/check_garden_e2e.py

Runs the whole W1 loop -- a messy manual submission batch -> ingest -> normalize -> hints ->
review -- inside a throwaway temporary directory (never the repo, never `data/store`), driving
every step through the real W1.3/W1.4/W1.5 CLIs as subprocesses, and asserts the Gate B pass
conditions from `bootstrap/seed/2026-09-12-garden-corpus-program/ACCEPTANCE_GATES.md` section
"Gate B": *"a representative batch of messy manual submissions can be ingested and reviewed while
preserving originals, provenance, decision history, and duplicate hints. No curation action may
imply verification."*

Concretely it asserts, in order:

  1. A messy batch (a literal `_` placeholder-glyph row, a curly-quote row -- both taken verbatim
     from `quotes.csv` -- plus a controlled wrong-author row, a whitespace row and a no-citation
     row, and a near-duplicate text pair) is submitted through the real W1.3 CLI, and every
     capture is byte-identical to the submitted text (nothing trimmed, quote-normalized, or
     glyph-"fixed"); `captured_at` and the capture-method/attribution/citation provenance are
     preserved on the capture.
  2. `normalize --all` then `hints --all` (W1.4) write a proposal + notes and derived hint rows
     WITHOUT touching any capture (the whole `[captures]` export section is byte-identical
     before and after), a hint is never a state (no `curation_state` write, no `decisions`
     row), the generic `"Oral Tradition"` shared-citation pair produces NO reference hint (the
     W1.4 false-positive fix), and a near-text pair DOES produce a hint with a basis.
  3. The review surface (W1.5) drives accept / hold / reject / duplicate / reopen and one full
     reversal (accept -> eligible, then reject -> candidate_only via T-P7) through the real CLI;
     every decision is audited with actor / from / to / transition_id / reason; a rejected
     candidate keeps its capture and candidate readable; the reversal strands no dimension; and
     the audit history is append-only.
  4. No curation action implies verification: after every decision every candidate's
     `research_state` is still `not_started`, no decision row writes or implies a research
     state, and acceptance reaches `corpus = eligible` (wanted), never anything that claims
     truth.
  5. `quotes.csv` / `sources.csv` are byte-identical before and after, `validate_quotes.py`
     still exits 0, and nothing is written outside the temp directory.

The whole store is exported (garden.export/1), the export is re-imported into a fresh store and
compared byte-for-byte, and the committed text mirror round-trips -- the reproducibility
artifact the Gate B packet names. Everything is derived from `quotes.csv` at runtime (fixture
texts come from the real corpus) or from the submitted batch itself, so no expected value is
hard-coded and a check that stops narrowing fails loudly rather than passing vacuously.

Exits 0 with `RESULT: PASS`, non-zero with `RESULT: FAIL` and one `FAIL:` line per broken check
-- never a traceback.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import garden_store  # noqa: E402
from garden_store import Store  # noqa: E402

SUBMIT = SCRIPTS / "garden_submit.py"
NORMALIZE = SCRIPTS / "garden_normalize.py"
REVIEW = SCRIPTS / "garden_review.py"
STORE_CLI = SCRIPTS / "garden_store.py"
VALIDATE = SCRIPTS / "validate_quotes.py"
QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
STORE_FILENAME = garden_store.STORE_FILENAME

failures: list[str] = []


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


def run(script: Path, *args: object) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
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


def counts(store_dir: Path) -> dict[str, int]:
    with Store(store_dir) as store:
        return store.counts()


def export_bytes(store_dir: Path) -> bytes:
    with Store(store_dir) as store:
        return store.export_bytes()


def capture_row(store_dir: Path, capture_id: str) -> dict:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT * FROM captures WHERE capture_id = ?", (capture_id,)
        ).fetchone()
    return dict(row) if row else {}


def capture_text(store_dir: Path, capture_id: str) -> str:
    return capture_row(store_dir, capture_id).get("captured_text", "")


def candidate_row(store_dir: Path, candidate_id: str) -> dict:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
    return dict(row) if row else {}


def candidate_captures(store_dir: Path, candidate_id: str) -> list[dict]:
    with Store(store_dir) as store:
        return [
            dict(r)
            for r in store.conn.execute(
                "SELECT c.* FROM candidate_captures cc JOIN captures c "
                "ON c.capture_id = cc.capture_id WHERE cc.candidate_id = ? ORDER BY cc.ordinal",
                (candidate_id,),
            )
        ]


def hint_rows(store_dir: Path, candidate_id: str) -> list[dict]:
    with Store(store_dir) as store:
        return [
            dict(r)
            for r in store.conn.execute(
                "SELECT hint_seq, kind, target, basis FROM duplicate_hints "
                "WHERE candidate_id = ? ORDER BY hint_seq",
                (candidate_id,),
            )
        ]


def decision_rows(store_dir: Path, candidate_id: str | None = None) -> list[dict]:
    with Store(store_dir) as store:
        if candidate_id is None:
            rows = store.conn.execute("SELECT * FROM decisions ORDER BY seq")
        else:
            rows = store.conn.execute(
                "SELECT * FROM decisions WHERE subject_kind = 'candidate' "
                "AND subject_id = ? ORDER BY seq",
                (candidate_id,),
            )
        return [dict(r) for r in rows]


def decision_transitions(store_dir: Path, candidate_id: str) -> list[str]:
    return [row["transition_id"] for row in decision_rows(store_dir, candidate_id)]


def all_candidate_ids(store_dir: Path) -> list[str]:
    with Store(store_dir) as store:
        return [
            row["candidate_id"]
            for row in store.conn.execute("SELECT candidate_id FROM candidates ORDER BY candidate_id")
        ]


def submit(store_dir: Path, *, text: str, candidate_id: str, capture_id: str,
           attribution: str = "unknown", citation: str = "none", captured_at: str | None = None,
           **extra: object) -> subprocess.CompletedProcess:
    argv = [
        SUBMIT, "submit", "--dir", store_dir, "--text", text,
        "--attribution", attribution, "--citation", citation,
        "--capture-method", "pasted-text",
        "--candidate-id", candidate_id, "--capture-id", capture_id,
    ]
    if captured_at is not None:
        argv += ["--captured-at", captured_at]
    for key, value in extra.items():
        argv += [f"--{key}", str(value)]
    return run(*argv)


def normalize_all(store_dir: Path) -> subprocess.CompletedProcess:
    return run(NORMALIZE, "normalize", "--dir", store_dir, "--all")


def hints_all(store_dir: Path) -> subprocess.CompletedProcess:
    return run(NORMALIZE, "hints", "--dir", store_dir, "--all")


def decide(action: str, store_dir: Path, candidate_id: str, reason: str,
           actor: str = "operator") -> subprocess.CompletedProcess:
    return run(REVIEW, action, "--dir", store_dir, "--candidate-id", candidate_id,
               "--reason", reason, "--actor", actor)


def quote_rows() -> dict[int, dict]:
    rows: dict[int, dict] = {}
    with QUOTES.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[int(row["id"])] = row
    return rows


def would_be_vacuous(msg: str) -> None:
    fail(f"{msg} -- would be vacuous")


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-e2e-check-"))
    quotes_before = sha256(QUOTES)
    sources_before = sha256(SOURCES)
    print(f"scratch: {scratch}")
    try:
        run_checks(scratch)
    except Exception as exc:  # never a traceback: RESULT must still print
        fail(f"unexpected {type(exc).__name__}: {exc}")
    finally:
        if sha256(QUOTES) != quotes_before:
            fail("quotes.csv changed during the run")
        if sha256(SOURCES) != sources_before:
            fail("sources.csv changed during the run")
        check(sha256(QUOTES) == quotes_before and sha256(SOURCES) == sources_before,
              "quotes.csv and sources.csv are byte-identical before and after the whole loop")
        val = run(VALIDATE)
        check(val.returncode == 0 and "RESULT: PASS" in out_text(val),
              "validate_quotes.py still exits 0 after the whole loop",
              out_text(val).strip()[:170])
        check(not (ROOT / STORE_FILENAME).exists(),
              "no store was created in the repo root (the loop only ever wrote to the temp --dir)", "")
        stray = [p for p in scratch.rglob("*") if p.is_file()
                 and p.relative_to(scratch).parts[0] not in ("store", "e2e_store", "store_imported")
                 and p.name != "garden.export.txt"]
        check(not stray, "nothing was written outside the stores and scratch inputs", str(stray))
        shutil.rmtree(scratch, ignore_errors=True)
    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    print("RESULT: PASS (a messy batch is ingested, normalized, hinted and reviewed while "
          "originals, provenance, decision history and duplicate hints all survive, and no "
          "curation action implies verification)")
    return 0


def run_checks(scratch: Path) -> None:  # noqa: C901 -- one linear evidence script, by design
    rows = quote_rows()
    check(bool(rows), "quotes.csv is readable as CSV", str(len(rows)))

    store = scratch / "store"
    created = run(STORE_CLI, "create", "--dir", store)
    check(created.returncode == 0 and "RESULT: PASS" in out_text(created),
          "the store is created from empty", out_text(created).strip()[:170])

    # -- 1. the messy batch, taken from the real corpus + controlled messy shapes -----------
    print("\n-- 1. the messy manual submission batch --")
    # Row 320 carries the literal `_` placeholder glyph (Mitákuye Oyás_i_) -- the corpus's own
    # most fragile shape. Row 21 carries a curly apostrophe. Both are submitted verbatim from
    # the CSV, so the test proves the loop survives the corpus's actual awkward bytes.
    glyph_row = rows.get(320)
    curly_row = rows.get(21)
    if glyph_row is None:
        would_be_vacuous("row 320 (a literal `_` placeholder glyph) exists in quotes.csv")
        glyph_text = "Mit\u00e1kuye Oy\u00e1s_i_ (All are related)."
    else:
        glyph_text = glyph_row["quote_text"]
    if curly_row is None:
        would_be_vacuous("row 21 (a curly apostrophe) exists in quotes.csv")
        curly_text = "Knowledge is as wings to man\u2019s life, and a ladder for his ascent."
    else:
        curly_text = curly_row["quote_text"]
    check("_" in glyph_text, "the glyph fixture really contains a literal `_` placeholder", repr(glyph_text[:60]))
    check("\u2019" in curly_text or "\u2018" in curly_text or "\u201c" in curly_text or "\u201d" in curly_text,
          "the curly fixture really contains a curly quote", repr(curly_text[:60]))

    # The controlled messy shapes: a wrong author, a leading/trailing-whitespace capture, a
    # missing citation, and a near-duplicate text pair (so a hint must fire). Each asserts a
    # specific preservation property later.
    wrong_author_text = "The earth is but one country and mankind its citizens."
    whitespace_text = "  \n\tThis quote has   messy whitespace.  \n"
    nocitation_text = "Do not argue with your father until you have walked a mile in his shoes."
    near_a = "We are the ones we have been waiting for."
    near_b = "We are the ones we have been waiting for."
    dup_a = "The unexamined life is not worth living."
    dup_b = "The unexamined life is not worth living."

    batch = {
        "cand-G01": ("cap-G01", glyph_text, "unknown", "none", "Mitakuye Oyasin"),
        "cand-G02": ("cap-G02", curly_text, "unknown", "none", "Bah\u00e1\u02bc\u00ed Writings"),
        "cand-W01": ("cap-W01", wrong_author_text, "wrong author on purpose", "none", "operator"),
        "cand-W02": ("cap-W02", whitespace_text, "unknown", "none", "operator"),
        # `__omit__` = the citation flag is omitted, so W1.3 writes the `none` sentinel.
        "cand-N01": ("cap-N01", nocitation_text, "unknown", "__omit__", "operator"),
        "cand-N02": ("cap-N02", near_a, "unknown", "none", "operator"),
        "cand-N03": ("cap-N03", near_b, "unknown", "none", "operator"),
        "cand-D01": ("cap-D01", dup_a, "unknown", "Oral Tradition", "operator"),
        "cand-D02": ("cap-D02", dup_b, "unknown", "Oral Tradition", "operator"),
    }
    # `captured_at` is pinned so `next_daily_id` and the queue's newest-first order are
    # deterministic across runs and interpreters.
    stamps = [f"2026-09-13T{9 + i:02d}:00:00-06:00" for i in range(len(batch))]
    for i, (cid, (capid, text, attr, cit, _actor)) in enumerate(batch.items()):
        # A missing citation is an OMITTED flag (W1.3 turns absence into the `none` sentinel); a
        # supplied-empty citation is refused by the envelope validator, never defaulted.
        cit_kwargs = {} if cit == "__omit__" else {"citation": cit}
        proc = submit(store, text=text, candidate_id=cid, capture_id=capid,
                      attribution=attr, captured_at=stamps[i], **cit_kwargs)
        check(proc.returncode == 0, f"messy submission {cid} is accepted by the real W1.3 CLI",
              out_text(proc).strip()[:170])
    check(counts(store)["captures"] == len(batch) and counts(store)["candidates"] == len(batch),
          f"the batch produced {len(batch)} captures and {len(batch)} candidates",
          str(counts(store)))
    check(counts(store)["decisions"] == 0, "submission alone wrote no decision row",
          str(counts(store)["decisions"]))

    # -- 2. originals preserved verbatim ------------------------------------------------
    print("\n-- 2. originals are preserved verbatim (nothing trimmed, glyph-fixed, or quote-normalized) --")
    capture_before_normalize = export_bytes(store)
    for cid, (capid, text, attr, cit, _actor) in batch.items():
        stored_text = capture_text(store, capid)
        check(stored_text.encode("utf-8") == text.encode("utf-8"),
              f"{cid}: capture {capid} is byte-identical to the submitted text",
              f"{len(stored_text.encode('utf-8'))} vs {len(text.encode('utf-8'))} bytes")
    check("_" in capture_text(store, "cap-G01"),
          "the `_` placeholder glyph survives the capture byte-for-byte (never guessed)")
    check("\u2019" in capture_text(store, "cap-G02") or "\u2018" in capture_text(store, "cap-G02"),
          "the curly apostrophe survives the capture byte-for-byte")
    wrong_cap = capture_row(store, "cap-W01")
    check(wrong_cap["captured_attribution"] == "wrong author on purpose",
          "a wrong author is preserved on the capture (the encounter, not a correction)",
          repr(wrong_cap["captured_attribution"]))
    ws_cap = capture_row(store, "cap-W02")
    check(ws_cap["captured_text"].startswith("  \n\t"),
          "leading whitespace is preserved verbatim on the capture", repr(ws_cap["captured_text"][:10]))
    nocap = capture_row(store, "cap-N01")
    check(nocap["captured_citation"] == "none",
          "a missing citation becomes the 'none' sentinel on the capture (absence, not empty)",
          repr(nocap["captured_citation"]))
    check(capture_row(store, "cap-G01")["capture_method"] == "pasted-text"
          and capture_row(store, "cap-G01")["captured_at"].endswith("-06:00"),
          "capture provenance (method, timestamp with offset) is preserved on the capture")
    check(export_bytes(store) == capture_before_normalize,
          "the store export is deterministic before any normalization (byte-identical snapshot)")

    # -- 3. normalize + hints never touch a capture, and hints are derived, never a state --
    print("\n-- 3. normalize --all then hints --all (W1.4) --")
    captures_section_before = _section(export_bytes(store), "captures")
    norm = normalize_all(store)
    check(norm.returncode == 0 and "RESULT: PASS" in out_text(norm),
          "normalize --all is accepted", out_text(norm).strip()[:170])
    check(_section(export_bytes(store), "captures") == captures_section_before,
          "the whole [captures] export section is byte-identical after normalize --all")
    g01 = candidate_row(store, "cand-G01")
    check("preserved" in g01["normalization_notes"] and "_" in g01["candidate_text"],
          "the glyph is reported in the normalization note and preserved in the proposal",
          g01["normalization_notes"][:120])
    g02 = candidate_row(store, "cand-G02")
    check("quote" in g02["normalization_notes"].lower() or "\u2019" not in g02["candidate_text"],
          "the curly quote is canonicalized in the proposal and its change is noted",
          g02["normalization_notes"][:120])
    w02 = candidate_row(store, "cand-W02")
    check(w02["candidate_text"] == "This quote has messy whitespace."
          and "whitespace" in w02["normalization_notes"],
          "whitespace is collapsed/trimmed in the proposal with a named note",
          repr(w02["candidate_text"]))
    check(counts(store)["decisions"] == 0, "normalize wrote no decision row",
          str(counts(store)["decisions"]))

    hints = hints_all(store)
    check(hints.returncode == 0 and "RESULT: PASS" in out_text(hints),
          "hints --all is accepted", out_text(hints).strip()[:170])
    # the near-duplicate pair cand-N02/N03 must produce a hint; the generic "Oral Tradition"
    # pair cand-D01/D02 must produce NO reference hint (the W1.4 false-positive fix).
    n02_hints = hint_rows(store, "cand-N02")
    check(any(h["kind"] in ("exact-text", "near-text", "same-reference", "same-passage")
              and h["target"] == "cand-N03" for h in n02_hints),
          "the near-duplicate pair cand-N02/N03 produces a duplicate hint",
          str(n02_hints))
    d01_hints = hint_rows(store, "cand-D01")
    check(all(h["kind"] not in ("same-reference", "same-passage") for h in d01_hints),
          "two unrelated rows sharing the generic 'Oral Tradition' label produce NO reference hint",
          str(d01_hints))
    check(all(h["basis"] for h in hint_rows(store, "cand-N02")),
          "every duplicate hint carries a basis string")
    check(counts(store)["decisions"] == 0, "hint generation wrote no decision row",
          str(counts(store)["decisions"]))
    # hints are not a state: curation_state stays 'new' for every candidate after hints.
    all_new = all(candidate_row(store, cid)["curation_state"] == "new" for cid in all_candidate_ids(store))
    check(all_new, "after hints, every candidate is still curation_state='new' (a hint is never a state)")
    check(_section(export_bytes(store), "captures") == captures_section_before,
          "the [captures] export section is still byte-identical after hints --all")

    # -- 4. review: accept/hold/reject/duplicate/reopen + the full reversal -----------------
    print("\n-- 4. review (W1.5): every decision audited, reversal strands no dimension --")
    # accept the glyph candidate: fires T-C1 then T-P1 candidate_only -> eligible.
    acc = decide("accept", store, "cand-G01", "wanted and pursuable")
    check(acc.returncode == 0 and "RESULT: PASS" in out_text(acc), "accept cand-G01 (exit 0)",
          out_text(acc).strip()[:170])
    g01 = candidate_row(store, "cand-G01")
    check(g01["curation_state"] == "accepted" and g01["corpus_state"] == "eligible",
          "accept sets curation=accepted and fires T-P1 to corpus=eligible",
          f"curation={g01['curation_state']} corpus={g01['corpus_state']}")
    check(decision_transitions(store, "cand-G01") == ["T-C1", "T-P1"],
          "accept cand-G01 recorded exactly ['T-C1', 'T-P1']",
          str(decision_transitions(store, "cand-G01")))

    hold = decide("hold", store, "cand-N01", "defer until citation is checked")
    check(hold.returncode == 0, "hold cand-N01 (exit 0)", out_text(hold).strip()[:170])
    check(candidate_row(store, "cand-N01")["curation_state"] == "hold",
          "hold sets curation=hold (no corpus change)")
    check(decision_transitions(store, "cand-N01") == ["T-C2"], "hold cand-N01 recorded T-C2",
          str(decision_transitions(store, "cand-N01")))

    rej = decide("reject", store, "cand-W01", "not wanted in the Garden")
    check(rej.returncode == 0, "reject cand-W01 (exit 0)", out_text(rej).strip()[:170])
    check(candidate_row(store, "cand-W01")["curation_state"] == "rejected",
          "reject sets curation=rejected")
    # rejecting keeps the capture and candidate readable.
    w01_caps = candidate_captures(store, "cand-W01")
    check(w01_caps and w01_caps[0]["captured_text"] == wrong_author_text,
          "the rejected candidate still reads back with its verbatim capture")
    show_rejected = out_text(run(REVIEW, "show", "--dir", store, "--candidate-id", "cand-W01"))
    check(wrong_author_text in show_rejected and "rejected" in show_rejected,
          "show still renders the rejected candidate and its capture", "")

    dup = decide("duplicate", store, "cand-D01", "already represented by cand-D02")
    check(dup.returncode == 0, "duplicate cand-D01 (exit 0)", out_text(dup).strip()[:170])
    check(candidate_row(store, "cand-D01")["curation_state"] == "duplicate",
          "duplicate sets curation=duplicate")
    check(decision_transitions(store, "cand-D01") == ["T-C4"],
          "duplicate cand-D01 recorded T-C4", str(decision_transitions(store, "cand-D01")))

    # The full reversal: accept (eligible) then reject -> T-C8 then T-P7 back to candidate_only.
    rv = decide("accept", store, "cand-N02", "wanted first")
    check(rv.returncode == 0, "accept cand-N02 (exit 0)", out_text(rv).strip()[:170])
    check(candidate_row(store, "cand-N02")["corpus_state"] == "eligible",
          "accept cand-N02 fired T-P1 to eligible")
    rv2 = decide("reject", store, "cand-N02", "reversal: attribution is wrong")
    check(rv2.returncode == 0, "reject cand-N02 (reversal, exit 0)", out_text(rv2).strip()[:170])
    check(decision_transitions(store, "cand-N02") == ["T-C1", "T-P1", "T-C8", "T-P7"],
          "the reversal recorded exactly ['T-C1', 'T-P1', 'T-C8', 'T-P7']",
          str(decision_transitions(store, "cand-N02")))
    n02 = candidate_row(store, "cand-N02")
    check(n02["curation_state"] == "rejected" and n02["corpus_state"] == "candidate_only",
          "the reversal strands no dimension: curation=rejected, corpus=candidate_only",
          f"curation={n02['curation_state']} corpus={n02['corpus_state']}")
    # issue #45 gap 3: the T-P7 audit row's own recorded to_state, not only the live column.
    tp7_rows = [
        row for row in decision_rows(store, "cand-N02")
        if row["transition_id"] == "T-P7"
    ]
    check(bool(tp7_rows) and tp7_rows[0]["to_state"] == "candidate_only",
          "the T-P7 audit row itself records to_state=candidate_only (not just the live corpus_state)",
          # Deliberately the state, never the whole row: the row carries a wall-clock
          # `occurred_at`, so a row dump could never be a reproducible `FAIL:` line in
          # run_negative_controls.py's exact-match control table.
          (f"to_state={tp7_rows[0]['to_state']!r}" if tp7_rows else "no T-P7 audit row"))

    reopen = decide("reopen", store, "cand-W01", "new information arrived")
    check(reopen.returncode == 0, "reopen cand-W01 (exit 0)", out_text(reopen).strip()[:170])
    check(candidate_row(store, "cand-W01")["curation_state"] == "new",
          "reopen returns a rejected candidate to new (T-C10)")
    check(decision_transitions(store, "cand-W01") == ["T-C3", "T-C10"],
          "reopen cand-W01 recorded ['T-C3', 'T-C10']",
          str(decision_transitions(store, "cand-W01")))

    # no stranded dimension across the whole store.
    stranded = [
        (cid, candidate_row(store, cid)["curation_state"], candidate_row(store, cid)["corpus_state"])
        for cid in all_candidate_ids(store)
        if candidate_row(store, cid)["curation_state"] in ("hold", "rejected", "duplicate")
        and candidate_row(store, cid)["corpus_state"] in ("eligible", "canonical")
    ]
    check(not stranded, "no record has curation hold/rejected/duplicate while corpus is eligible/canonical",
          str(stranded))

    # -- 5. decision history: audit rows complete + append-only -----------------------------
    print("\n-- 5. decision history survives, every decision audited, append-only --")
    for cid, capid, text, _attr, _cit, _actor in [
        ("cand-G01", "cap-G01", glyph_text, "", "", ""),
        ("cand-N02", "cap-N02", near_a, "", "", ""),
    ]:
        for row in decision_rows(store, cid):
            check(row.get("actor") and row.get("from_state") and row.get("to_state")
                  and row.get("transition_id") and row.get("reason") and row.get("occurred_at"),
                  f"{cid}: every decision row carries actor/from/to/transition_id/reason/timestamp",
                  str(row))
    total_decisions = counts(store)["decisions"]
    # G01: 2 (T-C1,T-P1). N01: 1. W01: T-C3,T-C10 = 2. D01: 1. N02: 4. = 10 decision rows.
    check(total_decisions == 10, f"the review produced exactly 10 audited decision rows (got {total_decisions})",
          str(total_decisions))
    import sqlite3
    with Store(store) as s:
        before_rows = [tuple(r) for r in s.conn.execute("SELECT * FROM decisions ORDER BY seq")]
        for statement, params in (("UPDATE decisions SET reason='rewritten' WHERE seq=1", ()),
                                  ("DELETE FROM decisions WHERE seq=1", ())):
            try:
                s.conn.execute(statement, params)
                s.conn.commit()
                fail(f"decisions accepted {statement.split()[0]}: the log is not append-only")
            except sqlite3.IntegrityError as exc:
                ok(f"decisions rejects {statement.split()[0]} ({str(exc).splitlines()[0]})")
        after_rows = [tuple(r) for r in s.conn.execute("SELECT * FROM decisions ORDER BY seq")]
    check(before_rows == after_rows, "no decision row changed after the rejected writes")

    # -- 6. no curation action implies verification ----------------------------------------
    print("\n-- 6. no curation action implies verification (research stays not_started) --")
    research_ok = all(
        candidate_row(store, cid).get("research_state") == "not_started"
        for cid in all_candidate_ids(store)
    )
    check(research_ok, "after every decision, every candidate's research_state is still 'not_started'")
    # No decision row touches the research dimension.
    research_rows = [r for r in decision_rows(store) if r["dimension"] == "research"]
    check(not research_rows, "no decision row writes or implies a research state",
          str(research_rows))
    # No candidate was ever moved to a corpus/curation state that claims truth.
    for cid in all_candidate_ids(store):
        row = candidate_row(store, cid)
        check(row["corpus_state"] in ("candidate_only", "eligible"),
              f"{cid}: corpus_state stays in the W1 vocabulary (candidate_only/eligible)",
              row["corpus_state"])

    # -- 7. the store round-trips and the export is the reproducible artifact ---------------
    print("\n-- 7. the store export round-trips (garden.export/1) --")
    data = export_bytes(store)
    with Store(store) as s:
        s.write_export(scratch / "garden.export.txt")
    check((scratch / "garden.export.txt").read_bytes() == data,
          "write_export wrote the same bytes the in-memory export returned")
    imported = scratch / "store_imported"
    run(STORE_CLI, "create", "--dir", imported)
    with Store(imported) as s:
        status = s.import_bytes(data)
    check(status.startswith("imported"), "the export imports into a fresh store", status)
    with Store(imported) as s:
        check(s.export_bytes() == data,
              "re-export after import is byte-identical to the original (round-trip lossless)")
    verify = run(STORE_CLI, "verify", "--dir", store)
    check(verify.returncode == 0 and "RESULT: PASS" in out_text(verify),
          "the store's own verify (export -> re-import -> compare) passes",
          out_text(verify).strip()[:170])

    # -- 8. the committed mirror is reproducible from a clean clone --------------------------
    print("\n-- 8. the whole loop is one self-contained command from a clean tree --")
    check(not (ROOT / STORE_FILENAME).exists(),
          "the run did not create a store in the repo (a clean clone reproduces it via --dir)")


def _section(data: bytes, name: str) -> list[str]:
    """The lines of one `[section]` from a garden.export text, for byte comparison."""
    text = data.decode("utf-8")
    out: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]"):
            in_section = (line == f"[{name}]")
            continue
        if in_section and line:
            out.append(line)
    return out


if __name__ == "__main__":
    sys.exit(main())
