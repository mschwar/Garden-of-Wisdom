#!/usr/bin/env python3
"""Deterministic acceptance test for the W1.1 Garden corpus store.

Usage:
    python3 scripts/check_garden_store.py

Runs entirely in a throwaway temporary directory (never the repo) and asserts the W1.1
acceptance criteria from `docs/program/W1_DECOMPOSITION.md` section "W1.1 - Storage decision
+ minimal schema":

  1. create-from-empty in a fresh directory produces the schema;
  2. the migration is idempotent -- re-running `create` is a no-op and says so, and the store
     is byte-for-byte unchanged;
  3. write one candidate with its capture, then read it back with `captured_text` byte-identical
     (verbatim, including a newline, a tab, curly quotes, a literal `_` and edge whitespace);
  4. the export is a pure function of the store: deterministic bytes, records in a fixed sorted
     order even when they were written in a different order, one record per line, diffable;
  5. round-trip: write -> export to text -> wipe -> re-import -> byte-identical text;
  6. re-importing the same text is a no-op;
  7. `decisions` rejects UPDATE and DELETE (append-only enforced, not documented);
  8. `captures` rejects UPDATE and DELETE (immutable enforced);
  9. the four state dimensions carry exactly the vocabularies in
     `docs/program/STATE_MODEL.md` (curation 5, research 6, corpus 4, work 5); an
     out-of-vocabulary value is rejected by the SQL layer for **every** state column (each
     column is its own CHECK constraint) and, on the shared API path, by `record_decision` for
     a decision's target state;
 10. duplicate hints are rows (kind/target/basis) and rebuild deterministically;
 11. requirement 6's two queries answer correctly and stay on the index at ~2,000 rows;
 12. the legacy frozen view is untouched: `quotes.csv` / `sources.csv` are byte-identical
     before and after, and nothing is written outside the temp directory.

Exits 0 with `RESULT: PASS` when every check holds, non-zero with `RESULT: FAIL` and one
`FAIL:` line per broken check -- never a traceback, even on a broken store.

Every negative control for this unit (mutation -> observed FAIL line) is recorded in
`GARDEN_W1_1_HANDOFF.md`. Note the ordering checks in 4 exist *because* the round-trip alone
cannot catch a lost `ORDER BY` when records are written in export order: this test therefore
writes its records deliberately out of export order and asserts the export order directly.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import garden_store  # noqa: E402
from garden_store import (  # noqa: E402
    DIMENSIONS,
    EXPORT_HEADER,
    HINT_KINDS,
    SCHEMA_VERSION,
    STORE_FILENAME,
    STATE_COLUMNS,
    Store,
    StoreError,
    create_store,
    parse_export,
)

STATE_MODEL = ROOT / "docs" / "program" / "STATE_MODEL.md"
STATE_MODEL_SECTIONS = {
    "curation": "## 1. Curation state",
    "research": "## 2. Research state",
    "corpus": "## 3. Corpus state",
    "work": "## 4. Work state",
}
QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"

#: The nasty capture: leading/trailing spaces, a tab, a newline, curly quotes, an em dash and
#: the literal `_` placeholder the repo refuses to guess
#: (`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md`). Stored and returned verbatim.
NASTY_TEXT = (
    "  The earth is but one country,\n"
    "\tand mankind its citizens \u2014 \u201cattributed\u201d \u2014 Bah\u00e1_u\u2019ll\u00e1h  "
)
#: Written SECOND, so `cap-0001` must still export first. Likewise for candidates.
CAPTURE_A = "cap-0001"
CAPTURE_B = "cap-0002"
CANDIDATE_A = "cand-0001"
CANDIDATE_B = "cand-0002"

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


def section_ids(records: dict, section: str, key: str) -> list:
    return [record[key] for record in records[section]]


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-store-check-"))
    quotes_before = sha256(QUOTES) if QUOTES.exists() else None
    sources_before = sha256(SOURCES) if SOURCES.exists() else None
    print(f"scratch: {scratch}")

    try:
        run_checks(scratch)
    except Exception as exc:  # no traceback on a broken store: RESULT must still print
        fail(f"unexpected {type(exc).__name__}: {exc}")
    finally:
        if quotes_before is not None and sha256(QUOTES) != quotes_before:
            fail("quotes.csv changed during the run")
        if sources_before is not None and sha256(SOURCES) != sources_before:
            fail("sources.csv changed during the run")
        if quotes_before is not None and sources_before is not None:
            ok("quotes.csv and sources.csv are byte-identical before and after the run")
        stray = [
            p
            for p in scratch.rglob("*")
            if p.is_file() and p.name not in (STORE_FILENAME, "garden.export.txt")
        ]
        check(not stray, "the store wrote nothing outside its own directory", str(stray))
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    print("RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)")
    return 0


def run_checks(scratch: Path) -> None:
    store_dir = scratch / "store"

    # -- 1. create from empty ----------------------------------------------------------
    db_path, applied = create_store(store_dir)
    check(
        db_path.exists() and applied == ["0001_create_core"],
        f"create-from-empty applied migration {applied} into an empty directory",
    )
    with Store(store_dir) as store:
        tables = {
            row[0]
            for row in store.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        }
        expected_tables = {
            "captures",
            "candidates",
            "candidate_captures",
            "duplicate_hints",
            "decisions",
            "meta",
            "schema_migrations",
        }
        check(
            expected_tables <= tables,
            "schema has the capture / candidate / hint / decision / migration tables",
            f"missing={sorted(expected_tables - tables)}",
        )
        ledger = [row[0] for row in store.conn.execute("SELECT migration_id FROM schema_migrations")]
        check(ledger == ["0001_create_core"], "the migration ledger holds exactly 0001_create_core")
        version = store.conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
        check(int(version) == SCHEMA_VERSION, f"meta.schema_version is {SCHEMA_VERSION}")

    # -- 2. migration idempotency ------------------------------------------------------
    before = Store(store_dir).export_bytes()
    try:
        _, applied_again = create_store(store_dir)
        second_ok = applied_again == []
    except Exception as exc:
        second_ok = False
        fail(
            f"re-running create raised {type(exc).__name__}: {exc} "
            "(the migration is not idempotent)"
        )
    if second_ok:
        ok("re-running create applied no migration (reported no-op)")
    with Store(store_dir) as store:
        after = store.export_bytes()
    check(
        before == after,
        "re-running create left the store byte-identical (export unchanged)",
        "export bytes changed",
    )
    re_run_output = _create_output(store_dir)
    check(
        "no-op" in re_run_output and "applied migration(s): none" in re_run_output,
        "the re-run says so on stdout ('no-op: migration ... already applied')",
        re_run_output.strip().replace("\n", " | "),
    )

    # -- 3. write one candidate with its capture ---------------------------------------
    with Store(store_dir) as store:
        # Written out of export order on purpose: cap-0002 first, then cap-0001.
        store.add_capture(
            CAPTURE_B,
            "The earth is one home and mankind its family.",
            captured_attribution="\u2018Abdu\u2019l-Bah\u00e1",
            capture_method="pasted-text",
            captured_at="2026-09-12T09:20:00-06:00",
            captured_by="agent",
            language="en",
        )
        store.add_capture(
            CAPTURE_A,
            NASTY_TEXT,
            captured_attribution="Bah\u00e1_u\u2019ll\u00e1h",
            captured_citation="attributed - seen on a quote card",
            capture_method="screenshot",
            captured_at="2026-09-12T09:14:11-06:00",
            captured_by="operator",
            language="en",
            source_reference="https://example-quotes.example/one-country",
            context_notes="shared in a group chat with no citation beyond the author",
            raw_artifact_ref="captures/2026-09-12/one-country.png",
        )
        store.add_candidate(
            CANDIDATE_B,
            "The earth is one home and mankind its family.",
            [CAPTURE_B],
            candidate_author="\u2018Abdu\u2019l-Bah\u00e1",
            normalization_notes="identical to capture",
            created_at="2026-09-12T09:25:00-06:00",
        )
        store.add_candidate(
            CANDIDATE_A,
            NASTY_TEXT.strip(),
            [CAPTURE_A],
            candidate_author="Bah\u00e1_u\u2019ll\u00e1h",
            candidate_source_ref="none",
            normalization_notes=(
                "trimmed the capture's leading/trailing whitespace; retained the literal "
                "'_' placeholder verbatim (never guessed)"
            ),
            created_at="2026-09-12T09:15:00-06:00",
        )
        # Hints written out of hint_seq export order for candidate A.
        store.add_duplicate_hints(CANDIDATE_A, [{"kind": "same-reference", "target": "external", "basis": "same citation as an unlinked row"}])
        store.add_duplicate_hints(CANDIDATE_A, [{"kind": "near-text", "target": CANDIDATE_B, "basis": "0.74 text similarity, different author"}])
        row = store.conn.execute(
            "SELECT captured_text FROM captures WHERE capture_id = ?", (CAPTURE_A,)
        ).fetchone()
        check(
            bytes(row[0], "utf-8") == bytes(NASTY_TEXT, "utf-8"),
            "captured_text round-trips byte-identically through the store (verbatim)",
            repr(row[0]),
        )
        states = store.conn.execute(
            "SELECT curation_state, research_state, corpus_state, work_state FROM candidates "
            "WHERE candidate_id = ?",
            (CANDIDATE_A,),
        ).fetchone()
        check(
            tuple(states) == ("new", "not_started", "candidate_only", "queued"),
            "a new candidate enters at the intake states only",
            str(tuple(states)),
        )
        links = [
            row[0]
            for row in store.conn.execute(
                "SELECT capture_id FROM candidate_captures WHERE candidate_id = ? ORDER BY ordinal",
                (CANDIDATE_A,),
            )
        ]
        check(links == [CAPTURE_A], "the candidate references its capture", str(links))
        store.add_candidate(
            "cand-0003",
            "multi-capture candidate",
            [CAPTURE_A, CAPTURE_B],
            normalization_notes="identical to capture",
            created_at="2026-09-12T09:30:00-06:00",
        )
        many = [
            row[0]
            for row in store.conn.execute(
                "SELECT capture_id FROM candidate_captures WHERE candidate_id = 'cand-0003' "
                "ORDER BY ordinal"
            )
        ]
        check(
            many == [CAPTURE_A, CAPTURE_B],
            "a candidate may reference more than one capture (ordered)",
            str(many),
        )
        seq1 = store.record_decision(
            subject_kind="candidate",
            subject_id=CANDIDATE_A,
            dimension="curation",
            action="curation-decision",
            from_state="new",
            to_state="hold",
            actor="operator",
            actor_kind="operator",
            reason="want to check the attribution first",
            transition_id="T-C2",
            occurred_at="2026-09-12T09:40:00-06:00",
        )
        store.record_decision(
            subject_kind="candidate",
            subject_id=CANDIDATE_A,
            dimension="curation",
            action="curation-decision",
            from_state="hold",
            to_state="accepted",
            actor="operator",
            actor_kind="operator",
            reason="attribution confirmed by the operator",
            transition_id="T-C5",
            occurred_at="2026-09-12T09:45:00-06:00",
        )
        check(seq1 == 1, "the append-only log assigns ascending seq (1 = first row)")
        store.record_decision(
            subject_kind="work_unit",
            subject_id="W1.1",
            dimension="work",
            action="transition",
            from_state="queued",
            to_state="active",
            actor="agent",
            actor_kind="agent",
            reason="unit picked up on its isolated branch",
            transition_id="T-W1",
        )
        decisions = store.conn.execute(
            "SELECT dimension, from_state, to_state, actor, actor_kind, reason, transition_id "
            "FROM decisions ORDER BY seq"
        ).fetchall()
        check(
            len(decisions) == 3
            and decisions[0]["dimension"] == "curation"
            and decisions[2]["dimension"] == "work",
            "the log holds curation and work transitions with who/what/when/from/to/reason",
            str(len(decisions)),
        )

    # -- 4. export is deterministic and ordered ----------------------------------------
    with Store(store_dir) as store:
        export_a = store.export_bytes()
        export_a2 = store.export_bytes()
    check(export_a == export_a2, "exporting twice produces byte-identical text")
    check(export_a.startswith((EXPORT_HEADER + "\n").encode()), f"export starts with {EXPORT_HEADER!r}")
    check(
        b"\r" not in export_a and export_a.endswith(b"\n"),
        "export uses LF only and ends with a newline",
    )
    records = parse_export(export_a)
    check(
        section_ids(records, "captures", "capture_id") == [CAPTURE_A, CAPTURE_B],
        "captures export in sorted order even though cap-0002 was written first",
        str(section_ids(records, "captures", "capture_id")),
    )
    check(
        section_ids(records, "candidates", "candidate_id") == [CANDIDATE_A, CANDIDATE_B, "cand-0003"],
        "candidates export in sorted order (not insertion order)",
        str(section_ids(records, "candidates", "candidate_id")),
    )
    hint_keys = [
        (record["candidate_id"], record["hint_seq"]) for record in records["duplicate_hints"]
    ]
    check(
        hint_keys == sorted(hint_keys),
        "duplicate hints export ordered by (candidate_id, hint_seq)",
        str(hint_keys),
    )
    expected_lines = 3 + sum(1 + len(records[s]) for s in ("captures", "candidate_captures", "candidates", "duplicate_hints", "decisions"))
    actual_lines = export_a.decode("utf-8").count("\n")
    check(
        actual_lines == expected_lines,
        f"one record per line: {actual_lines} lines for {expected_lines} expected",
        f"actual={actual_lines} expected={expected_lines}",
    )
    check(
        records["meta"]["schema_version"] == SCHEMA_VERSION
        and set(records["meta"]) == {"schema_version", "created_at"},
        "the export carries exactly the store's schema_version and created_at (no export-time state)",
        str(records["meta"]),
    )

    # -- 5. round-trip: wipe -> re-import -> byte-identical ----------------------------
    with Store(store_dir) as store:
        store.write_export(store.dir / "garden.export.txt")
    text_path = store_dir / "garden.export.txt"
    check(text_path.read_bytes() == export_a, "the exported text file is the export bytes")
    (store_dir / STORE_FILENAME).unlink()
    create_store(store_dir)
    with Store(store_dir) as store:
        status = store.import_bytes(text_path.read_bytes())
        export_b = store.export_bytes()
    check(
        export_a == export_b,
        "round-trip is byte-identical (write -> export -> wipe -> re-import)",
        f"{len(export_a)} vs {len(export_b)} bytes",
    )
    check("imported" in status, f"the import reports what it loaded ({status})")
    check(
        Store(store_dir).counts()
        == {
            "captures": 2,
            "candidates": 3,
            "candidate_captures": 4,
            "duplicate_hints": 2,
            "decisions": 3,
        },
        "every record survived the round-trip",
        str(Store(store_dir).counts()),
    )
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT captured_text FROM captures WHERE capture_id = ?", (CAPTURE_A,)
        ).fetchone()
    check(row[0] == NASTY_TEXT, "the verbatim capture survived the round-trip unchanged")

    # -- 6. re-import idempotency ------------------------------------------------------
    with Store(store_dir) as store:
        before_noop = store.export_bytes()
        status = store.import_bytes(text_path.read_bytes())
        after_noop = store.export_bytes()
    check(
        "no-op" in status and before_noop == after_noop,
        f"re-importing the same text is a no-op and says so ({status})",
        status,
    )

    # -- 7. append-only decisions ------------------------------------------------------
    with Store(store_dir) as store:
        before_rows = [tuple(r) for r in store.conn.execute("SELECT * FROM decisions ORDER BY seq")]
        for statement, params in (
            ("UPDATE decisions SET reason = 'rewritten' WHERE seq = 1", ()),
            ("DELETE FROM decisions WHERE seq = 1", ()),
        ):
            try:
                store.conn.execute(statement, params)
                store.conn.commit()
                fail(f"decisions accepted {statement.split()[0]}: the log is not append-only")
            except sqlite3.IntegrityError as exc:
                ok(f"decisions rejects {statement.split()[0]} ({str(exc).splitlines()[0]})")
        after_rows = [tuple(r) for r in store.conn.execute("SELECT * FROM decisions ORDER BY seq")]
        check(before_rows == after_rows, "no decision row changed after the rejected writes")

    # -- 8. capture immutability -------------------------------------------------------
    with Store(store_dir) as store:
        before_rows = [tuple(r) for r in store.conn.execute("SELECT * FROM captures ORDER BY capture_id")]
        for statement in (
            "UPDATE captures SET captured_text = 'cleaned' WHERE capture_id = '%s'" % CAPTURE_A,
            "DELETE FROM captures WHERE capture_id = '%s'" % CAPTURE_A,
        ):
            try:
                store.conn.execute(statement)
                store.conn.commit()
                fail(f"captures accepted {statement.split()[0]}: captures are not immutable")
            except sqlite3.IntegrityError as exc:
                ok(f"captures rejects {statement.split()[0]} ({str(exc).splitlines()[0]})")
        after_rows = [tuple(r) for r in store.conn.execute("SELECT * FROM captures ORDER BY capture_id")]
        check(before_rows == after_rows, "no capture row changed after the rejected writes")

    # -- 9. vocabularies come from STATE_MODEL.md, and bad values are refused ----------
    if STATE_MODEL.exists():
        documented = parse_state_model_vocabularies(STATE_MODEL)
        for dimension, values in DIMENSIONS.items():
            check(
                list(values) == documented.get(dimension),
                f"{dimension} vocabulary equals STATE_MODEL.md ({len(values)} values)",
                f"code={list(values)} doc={documented.get(dimension)}",
            )
        check(
            {d: len(v) for d, v in DIMENSIONS.items()}
            == {"curation": 5, "research": 6, "corpus": 4, "work": 5},
            "vocabulary sizes are curation=5, research=6, corpus=4, work=5",
        )
    else:
        ok("STATE_MODEL.md not present in this copy: vocabulary/prose cross-check skipped")
    with Store(store_dir) as store:
        # Each state column is a separate schema object, so each needs its own assertion: a
        # loop over one sampled column (this check's first version tested only curation_state)
        # left the other three CHECK constraints unguarded — removing the research_state CHECK
        # left the whole run green. Found by the reviewing session's independent QA, which is
        # why the loop exists.
        for dimension, column in STATE_COLUMNS.items():
            try:
                store.conn.execute(
                    f"UPDATE candidates SET {column} = 'maybe' WHERE candidate_id = ?",
                    (CANDIDATE_A,),
                )
                store.conn.commit()
                fail(f"the SQL layer accepted {column} = 'maybe' (outside STATE_MODEL.md)")
            except sqlite3.IntegrityError as exc:
                ok(f"the SQL layer rejects {column} = 'maybe' ({str(exc).splitlines()[0]})")
        try:
            store.record_decision(
                subject_kind="candidate",
                subject_id=CANDIDATE_A,
                dimension="curation",
                action="curation-decision",
                from_state="new",
                to_state="maybe",
                actor="operator",
                actor_kind="operator",
                reason="invalid on purpose",
            )
            fail("record_decision accepted to_state = 'maybe' (outside STATE_MODEL.md)")
        except StoreError as exc:
            ok(f"the API rejects to_state = 'maybe' ({exc})")
        try:
            store.record_decision(
                subject_kind="candidate",
                subject_id=CANDIDATE_A,
                dimension="mood",
                action="x",
                from_state="new",
                to_state="new",
                actor="operator",
                actor_kind="operator",
                reason="invalid on purpose",
            )
            fail("record_decision accepted an unknown dimension")
        except StoreError:
            ok("the API rejects an unknown dimension")
        count = store.conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        check(count == 3, "no invalid decision was appended", str(count))

    # -- 10. duplicate hints are rows and rebuild deterministically --------------------
    with Store(store_dir) as store:
        before = store.export_bytes()
        store.replace_duplicate_hints(
            CANDIDATE_A,
            [
                {"kind": "same-reference", "target": "external", "basis": "same citation as an unlinked row"},
                {"kind": "near-text", "target": CANDIDATE_B, "basis": "0.74 text similarity, different author"},
            ],
        )
        check(
            store.export_bytes() == before,
            "rebuilding duplicate hints from the same basis reproduces the same rows (deterministic)",
        )
        try:
            store.replace_duplicate_hints(CANDIDATE_A, [{"kind": "looks-similar", "target": "x", "basis": "vibes"}])
            fail("and the hint vocabulary is enforced")
        except StoreError:
            ok("a hint kind outside the contract vocabulary is refused")
        try:
            store.replace_duplicate_hints(CANDIDATE_A, [{"kind": "near-text", "target": "x", "basis": ""}])
            fail("a hint without a basis was accepted")
        except StoreError:
            ok("a hint with no basis string is refused")
        ok(f"hint vocabulary = {list(HINT_KINDS)} (kind/target/basis only, never a state)")

    # -- 11. requirement 6's queries, at ~2,000 rows -----------------------------------
    scale_dir = scratch / "scale"
    create_store(scale_dir)
    with Store(scale_dir) as store:
        rows = [
            ("cand-%04d" % i, f"quote {i}", "author", "none", "identical to capture", "garden.candidate-envelope/1", None,
             "new", "not_started", "candidate_only", "queued", "2026-09-12T00:00:00-06:00")
            for i in range(2000)
        ]
        store.conn.executemany(
            "INSERT INTO candidates (candidate_id, candidate_text, candidate_author, "
            "candidate_source_ref, normalization_notes, intake_schema_version, external_id, "
            "curation_state, research_state, corpus_state, work_state, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        # Distinct timestamps so "newest first" is an exact assertion, not a tie-break.
        store.conn.executemany(
            "UPDATE candidates SET created_at = ? WHERE candidate_id = ?",
            [("2026-09-12T%02d:%02d:00-06:00" % (i // 60, i % 60), "cand-%04d" % i) for i in range(2000)],
        )
        store.conn.execute(
            "INSERT INTO decisions (occurred_at, actor, actor_kind, subject_kind, subject_id, "
            "dimension, action, transition_id, from_state, to_state, reason) "
            "VALUES ('2026-09-12T09:00:00-06:00','operator','operator','candidate','cand-0007',"
            "'curation','curation-decision','T-C3','new','rejected','not my tradition')"
        )
        store.conn.execute("UPDATE candidates SET curation_state = 'rejected' WHERE candidate_id = 'cand-0007'")
        store.conn.commit()
        queue = store.unreviewed_queue(limit=5)
        check(
            [row["candidate_id"] for row in queue] == ["cand-1999", "cand-1998", "cand-1997", "cand-1996", "cand-1995"],
            "the unreviewed queue is newest-first and excludes decided rows",
            str([row["candidate_id"] for row in queue]),
        )
        check(
            len(store.unreviewed_queue()) == 1999,
            "the queue returns exactly the 1999 undecided rows at ~2,000 rows",
            str(len(store.unreviewed_queue())),
        )
        rejected = store.rejected_with_reasons()
        check(
            [(row["candidate_id"], row["reason"]) for row in rejected] == [("cand-0007", "not my tradition")],
            "every rejected item returns with its reason",
            str([tuple(r) for r in rejected]),
        )
        plan = " | ".join(
            row[3]
            for row in store.conn.execute(
                "EXPLAIN QUERY PLAN SELECT candidate_id FROM candidates WHERE curation_state = 'new' "
                "ORDER BY created_at DESC, candidate_id LIMIT 20"
            )
        )
        check(
            "idx_candidates_queue" in plan,
            "the queue query stays on idx_candidates_queue at 2,000 rows",
            plan,
        )

    # -- 12. broken input is refused cleanly, not with a traceback ---------------------
    broken_dir = scratch / "broken"
    create_store(broken_dir)
    with Store(broken_dir) as store:
        try:
            store.import_bytes(b"not an export\n")
            fail("importing a file that is not a garden.export/1 text was accepted")
        except StoreError as exc:
            ok(f"a malformed import is refused cleanly ({exc})")
        try:
            store.add_candidate("cand-x", "text", [CAPTURE_A], normalization_notes="n")
            fail("a candidate referencing a missing capture was accepted")
        except StoreError as exc:
            ok(f"a candidate with a dangling capture reference is refused ({exc})")
        try:
            store.add_capture("cap-x", "")
            fail("an empty capture was accepted")
        except StoreError as exc:
            ok(f"an empty captured_text is refused ({exc})")
        try:
            store.add_candidate("cand-y", "text", [CAPTURE_A], normalization_notes="")
            fail("a candidate with empty normalization_notes was accepted")
        except StoreError as exc:
            ok(f"empty normalization_notes is refused ({exc})")


def parse_state_model_vocabularies(path: Path) -> dict[str, list[str]]:
    """Read each dimension's vocabulary out of STATE_MODEL.md.

    The vocabulary line is prose, not a code block: it starts with `Vocabulary:` and may wrap
    onto a second line (research state does). Take the paragraph up to the next blank line and
    read the backticked values; the surrounding paragraphs in these sections carry no other
    backticked words, so the result is exactly the declared list.
    """
    text = path.read_text(encoding="utf-8")
    vocabularies: dict[str, list[str]] = {}
    for dimension, heading in STATE_MODEL_SECTIONS.items():
        start = text.index(heading)
        block_start = text.index("Vocabulary:", start)
        block_end = text.find("\n\n", block_start)
        block = text[block_start : block_end if block_end != -1 else len(text)]
        vocabularies[dimension] = re.findall(r"`([^`]+)`", block)
    return vocabularies


_CREATE_OUTPUT = ""


def _create_output(store_dir: Path) -> str:
    """Capture what `create` prints on a re-run, without spawning a process."""
    global _CREATE_OUTPUT
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        garden_store.main(["create", "--dir", str(store_dir)])
    _CREATE_OUTPUT = buffer.getvalue()
    return _CREATE_OUTPUT


if __name__ == "__main__":
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    sys.exit(main())
