#!/usr/bin/env python3
"""Deterministic acceptance test for the D3 `unverifiable` side-car ledger.

Usage:
    python3 scripts/check_garden_ledger.py

Runs entirely in a throwaway temporary directory (never the repo) and asserts the D3
acceptance criteria from `docs/program/D3_UNVERIFIABLE_LEDGER.md` (decision D3, 2026-09-12,
`docs/DECISIONS.md`): `unverifiable` is represented in a **side-car ledger keyed by legacy
row id**, NOT by widening the 3-valued `quotes.csv` enum. Issue #5 / Garden id 30 is the
live instance.

  1. `create` applies migration `0002_unverifiable_ledger` and the `legacy_verification`
     table exists with its CHECK constraints;
  2. `mark` records one legacy row as `unverifiable` with a `research` audit row in the same
     transaction -- never a ledger row without its audit row;
  3. a legacy row already in the ledger cannot be re-marked (no silent overwrite);
  4. `reopen` reverses an adjudication (`T-R12 unverifiable -> in_research`), removing the
     ledger row and appending its audit row in the same transaction;
  5. a refused `mark`/`reopen` writes nothing at all -- the store is byte-identical;
  6. the ledger is an export section ordered by legacy row id, and round-trips with the store;
  7. `quotes.csv` / `sources.csv` are byte-identical before and after.

Exits 0 with `RESULT: PASS` when every check holds, non-zero with `RESULT: FAIL` and one
`FAIL:` line per broken check -- never a traceback, even on a broken store.

Every negative control (mutation -> observed FAIL line) is recorded in
`GARDEN_D3_HANDOFF.md`. The negative controls themselves run in a throwaway /tmp copy of the
repo, never the real tree.
"""
from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import garden_store  # noqa: E402
from garden_store import (  # noqa: E402
    EXPORT_HEADER,
    SCHEMA_VERSION,
    STORE_FILENAME,
    UNVERIFIABLE_FROM_STATE,
    Store,
    StoreError,
    create_store,
    parse_export,
)

QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
LEDGER_SCRIPT = ROOT / "scripts" / "garden_ledger.py"

#: The live instance (issue #5): the Garden id that G4 rejected from the homepage-preview
#: export. This is the exact reason recorded for the seeded row.
LIVE_ID = "30"
LIVE_TRANSITION = "T-R6"
LIVE_EVIDENCE = "issue #5"
LIVE_REASON = (
    "G4 rejected; sentence not found on the Bahá'í Reference Library; Paris Talks has no "
    "Dec 2 1911 meeting (last 1911 Paris talk is 1 December); closest official wording "
    "differs (Meditation is the key for opening the doors of mysteries, London 12 Jan 1913)"
)

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


def run_cli(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(LEDGER_SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def run_cli_store(args: list[str], store_dir: Path) -> tuple[int, str]:
    return run_cli([*args, "--dir", str(store_dir)])


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-ledger-check-"))
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
        check(not stray, "the ledger wrote nothing outside the store directory", str(stray))
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    print("RESULT: PASS (the unverifiable side-car ledger works end to end)")
    return 0


#: D3's own ruling, restated here so this suite falsifies it directly rather than trusting
#: `validate_quotes.py` to catch a drift it does not own: `unverifiable` lives in the ledger,
#: never in `quotes.csv`'s `verification_status` column.
QUOTES_VERIFICATION_ENUM = {"unverified", "verified", "disputed"}


def run_checks(scratch: Path) -> None:
    store_dir = scratch / "store"

    # -- 0. D3's own ruling: the ledger is a side-car, and quotes.csv's enum stays 3-valued --
    with open(QUOTES, newline="", encoding="utf-8") as fh:
        quote_rows = list(csv.DictReader(fh))
    check(bool(quote_rows), "quotes.csv is readable as CSV (the fixture source)", str(len(quote_rows)))
    bad_enum = [
        r["id"] for r in quote_rows if r.get("verification_status", "") not in QUOTES_VERIFICATION_ENUM
    ]
    check(
        not bad_enum,
        "issue #45 gap 4: quotes.csv's verification_status stays exactly "
        f"{sorted(QUOTES_VERIFICATION_ENUM)} -- D3 chose the side-car ledger 'instead of widening "
        "the 3-valued quotes.csv enum', and this suite (not just validate_quotes.py) falsifies that "
        "ruling directly",
        str(bad_enum),
    )
    live_row = next((r for r in quote_rows if r["id"] == LIVE_ID), None)
    check(
        live_row is not None and live_row["verification_status"] == "unverified",
        f"the live instance (id {LIVE_ID}, issue #5) stays 'unverified' in quotes.csv -- its "
        "unverifiable adjudication lives only in the ledger, seeded separately below",
        str(live_row),
    )

    # -- 1. schema: migration 0002 + the ledger table with its CHECK constraints ---------
    db_path, applied = create_store(store_dir)
    check(
        db_path.exists()
        and applied
        == [
            "0001_create_core",
            "0002_unverifiable_ledger",
            "0003_legacy_batch_capture",
        ],
        f"create applies 0001, 0002 and 0003 in order ({applied})",
    )
    with Store(store_dir) as store:
        tables = {
            row[0]
            for row in store.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        check(
            "legacy_verification" in tables,
            "the schema has the legacy_verification table",
            f"missing from {sorted(tables)}",
        )
        # CHECK constraints: research_state fixed to unverifiable; transition_id restricted.
        for bad_transition in ("T-R1", "T-R5", "T-R8", "T-C1", "garbage"):
            try:
                store.conn.execute(
                    "INSERT INTO legacy_verification(legacy_row_id, research_state, "
                    "transition_id, reason, evidence_ref, decided_by, decided_at) "
                    "VALUES ('x', 'unverifiable', ?, 'r', 'none', 'op', 't')",
                    (bad_transition,),
                )
                store.conn.commit()
                fail(f"the SQL layer accepted transition_id = {bad_transition!r}")
            except Exception:
                store.conn.rollback()
                ok(f"the SQL layer rejects transition_id = {bad_transition!r}")
        try:
            store.conn.execute(
                "INSERT INTO legacy_verification(legacy_row_id, research_state, "
                "transition_id, reason, evidence_ref, decided_by, decided_at) "
                "VALUES ('y', 'in_research', 'T-R6', 'r', 'none', 'op', 't')"
            )
            store.conn.commit()
            fail("the SQL layer accepted research_state = 'in_research' in the ledger")
        except Exception:
            store.conn.rollback()
            ok("the SQL layer pins research_state to 'unverifiable'")
        # The transition map covers exactly the four terminating transitions.
        check(
            sorted(UNVERIFIABLE_FROM_STATE) == ["T-R10", "T-R11", "T-R6", "T-R7"],
            "UNVERIFIABLE_FROM_STATE names exactly the four terminating transitions",
            str(sorted(UNVERIFIABLE_FROM_STATE)),
        )
        check(
            set(store.counts()) == {
                "captures",
                "candidates",
                "candidate_captures",
                "duplicate_hints",
                "decisions",
                "legacy_verification",
                "legacy_batch_membership",
            },
            "counts() exposes the legacy_verification table",
        )
        empty = store.unverifiable_ledger()
        check(empty == [], "a fresh store has an empty unverifiable ledger", str(empty))

    # -- 2. mark: ledger row + research audit row in one transaction ---------------------
    with Store(store_dir) as store:
        before_mark = store.export_bytes()
        result = store.mark_legacy_unverifiable(
            LIVE_ID,
            transition_id=LIVE_TRANSITION,
            reason=LIVE_REASON,
            evidence_ref=LIVE_EVIDENCE,
            decided_by="operator",
            decided_at="2026-09-13T12:00:00-06:00",
        )
        check(
            result["research_state"] == "unverifiable"
            and result["transition_id"] == LIVE_TRANSITION
            and result["legacy_row_id"] == LIVE_ID,
            "mark records the live instance as unverifiable",
            str(result),
        )
        rows = store.unverifiable_ledger()
        check(
            len(rows) == 1 and rows[0]["legacy_row_id"] == LIVE_ID
            and rows[0]["research_state"] == "unverifiable"
            and rows[0]["transition_id"] == LIVE_TRANSITION
            and rows[0]["evidence_ref"] == LIVE_EVIDENCE,
            "the ledger holds exactly the live instance with its evidence",
            str([dict(r) for r in rows]),
        )
        dec = store.conn.execute(
            "SELECT subject_kind, subject_id, dimension, action, transition_id, "
            "from_state, to_state, reason FROM decisions ORDER BY seq"
        ).fetchall()
        check(
            len(dec) == 1
            and dec[0]["subject_kind"] == "research_case"
            and dec[0]["subject_id"] == LIVE_ID
            and dec[0]["dimension"] == "research"
            and dec[0]["transition_id"] == LIVE_TRANSITION
            and dec[0]["from_state"] == "in_research"  # T-R6's documented From
            and dec[0]["to_state"] == "unverifiable"
            and LIVE_REASON in dec[0]["reason"],
            "mark appends one research audit row (T-R6 from_state derived from the model)",
            str([dict(r) for r in dec]),
        )
        after_mark = store.export_bytes()
    check(before_mark != after_mark, "mark changed the store (the ledger + audit row landed)")

    # -- 2b. D-1 falsifier (foreign-QA): one clock read per adjudication ----------------
    # When decided_at is omitted (every CLI mark), the ledger row's decided_at and the audit
    # row's occurred_at must be the SAME instant -- never two separate now_iso() reads. Use a
    # dedicated store so this probe's extra audit row cannot perturb the main store's counts.
    d1_dir = scratch / "d1"
    create_store(d1_dir)
    with Store(d1_dir) as store:
        store.mark_legacy_unverifiable("d1-probe", transition_id="T-R6", reason="probe")
        lrow = store.conn.execute(
            "SELECT decided_at FROM legacy_verification WHERE legacy_row_id = 'd1-probe'"
        ).fetchone()
        arow = store.conn.execute(
            "SELECT occurred_at FROM decisions WHERE subject_id = 'd1-probe'"
        ).fetchone()
        check(
            lrow is not None
            and arow is not None
            and lrow["decided_at"] == arow["occurred_at"],
            "the ledger decided_at and audit occurred_at are one clock read (D-1)",
            f"ledger={lrow['decided_at'] if lrow else None} audit={arow['occurred_at'] if arow else None}",
        )

    # -- 3. no silent overwrite ----------------------------------------------------------
    with Store(store_dir) as store:
        before = store.export_bytes()
        try:
            store.mark_legacy_unverifiable(LIVE_ID, transition_id="T-R11", reason="again")
            fail("re-marking an already-ledgered row was accepted")
        except StoreError as exc:
            # Assert the explicit guard's wording, not merely "refused": the ledger PK would
            # also stop the duplicate, so a bare refusal check would not prove the guard.
            check(
                "already in the unverifiable ledger" in str(exc),
                "a duplicate mark is refused by the explicit re-adjudication guard",
                str(exc),
            )
        check(store.export_bytes() == before, "the refused re-mark wrote nothing at all")

    # -- 4. the ledger is an export section and round-trips ------------------------------
    with Store(store_dir) as store:
        store.write_export(store.dir / "garden.export.txt")
    text = (store_dir / "garden.export.txt").read_bytes()
    check(text.startswith((EXPORT_HEADER + "\n").encode()), f"export starts with {EXPORT_HEADER!r}")
    records = parse_export(text)
    check(
        [r["legacy_row_id"] for r in records["legacy_verification"]] == [LIVE_ID],
        "the export carries the ledger section with the live instance",
        str([r["legacy_row_id"] for r in records["legacy_verification"]]),
    )
    # The section order is a documented contract (EXPORT_SECTIONS): decisions, then the
    # ledger last. Pin it so a reordering cannot silently pass (foreign-QA O-2).
    section_headers = [ln for ln in text.decode("utf-8").splitlines() if ln.startswith("[") and ln.endswith("]")]
    check(
        section_headers == [
            "[meta]",
            "[captures]",
            "[candidate_captures]",
            "[candidates]",
            "[duplicate_hints]",
            "[decisions]",
            "[legacy_verification]",
            "[legacy_batch_membership]",
        ],
        "the export sections appear in the documented fixed order (O-2)",
        str(section_headers),
    )
    check(
        records["meta"]["schema_version"] == SCHEMA_VERSION,
        "the export meta schema_version is unchanged by the ledger section",
        str(records["meta"]["schema_version"]),
    )
    (store_dir / STORE_FILENAME).unlink()
    create_store(store_dir)
    with Store(store_dir) as store:
        status = store.import_bytes(text)
        reexport = store.export_bytes()
    check(reexport == text, "the ledger round-trips (write -> wipe -> re-import byte-identical)")
    check(
        "imported 2 record(s)" in status,
        "the import reports exactly the loaded record count (ledger + audit; O-1)",
        status,
    )

    # -- 5. guards refuse cleanly and write nothing --------------------------------------
    # Each guard's refusal is asserted by its OWN distinctive message, not by "refused": a
    # second layer (the SQL CHECK / PK on `legacy_verification`) also stops some of these, so
    # a bare refusal check would not prove the explicit guard. Matching the specific wording
    # gives each guard a unique falsifier (same lesson as W1.5's layered empty-reason guard).
    with Store(store_dir) as store:
        before = store.export_bytes()
        expected = [
            ("empty reason", "must carry a reason"),
            ("empty evidence_ref", "evidence_ref is required"),
            ("empty decided_by", "decided_by must be non-empty"),
            ("invalid transition", "does not terminate in unverifiable"),
            ("empty legacy row id", "legacy_row_id must be non-empty"),
            ("reopen on a missing row", "not in the unverifiable ledger"),
            ("reopen with empty reason", "must carry a reason"),
        ]
        refused = 0
        for label, needle in expected:
            try:
                if label == "empty reason":
                    store.mark_legacy_unverifiable("99", transition_id="T-R6", reason="")
                elif label == "empty evidence_ref":
                    store.mark_legacy_unverifiable("99", transition_id="T-R6", reason="r", evidence_ref="")
                elif label == "empty decided_by":
                    store.mark_legacy_unverifiable("99", transition_id="T-R6", reason="r", decided_by="")
                elif label == "invalid transition":
                    store.mark_legacy_unverifiable("99", transition_id="T-R1", reason="r")
                elif label == "empty legacy row id":
                    store.mark_legacy_unverifiable("", transition_id="T-R6", reason="r")
                elif label == "reopen on a missing row":
                    store.reopen_legacy_unverifiable("404", reason="r")
                else:  # reopen with empty reason
                    store.reopen_legacy_unverifiable(LIVE_ID, reason="")
                fail(f"{label} was accepted")
            except StoreError as exc:
                if needle in str(exc):
                    ok(f"{label} is refused with its own message (…{needle}…)")
                    refused += 1
                else:
                    fail(f"{label} was refused, but NOT by its explicit guard: {str(exc)[:120]}")
        check(refused == 7, f"all seven invalid writes were refused by their explicit guard ({refused}/7)")
        check(store.export_bytes() == before, "every refused write left the store byte-identical")

    # -- 6. reopen reverses (T-R12) in one transaction -----------------------------------
    with Store(store_dir) as store:
        before_reopen = store.export_bytes()
        reopened = store.reopen_legacy_unverifiable(
            LIVE_ID, reason="a new witness appeared", decided_at="2026-09-13T13:00:00-06:00"
        )
        check(
            reopened["from_state"] == "unverifiable"
            and reopened["to_state"] == "in_research"
            and reopened["transition_id"] == "T-R12",
            "reopen records the T-R12 reversal",
            str(reopened),
        )
        check(store.unverifiable_ledger() == [], "the live instance left the ledger after reopen")
        dec = store.conn.execute(
            "SELECT transition_id, from_state, to_state FROM decisions ORDER BY seq"
        ).fetchall()
        check(
            len(dec) == 2 and dec[1]["transition_id"] == "T-R12"
            and dec[1]["from_state"] == "unverifiable" and dec[1]["to_state"] == "in_research",
            "reopen appends the T-R12 audit row (unverifiable -> in_research)",
            str([dict(r) for r in dec]),
        )
        check(before_reopen != store.export_bytes(), "reopen changed the store (audit row landed)")

    # -- 7. re-adjudication: reopen-then-mark is the sanctioned cycle --------------------
    with Store(store_dir) as store:
        store.mark_legacy_unverifiable(
            LIVE_ID, transition_id="T-R11", reason="witness invalidated (misquotation)", evidence_ref=LIVE_EVIDENCE
        )
        rows = store.unverifiable_ledger()
        check(
            len(rows) == 1 and rows[0]["transition_id"] == "T-R11",
            "after reopen a legacy row may be marked again (T-R11 route recorded)",
            str([dict(r) for r in rows]),
        )

    # -- 8. the CLI drives the same guarded writes --------------------------------------
    cli_store = scratch / "cli"
    create_store(cli_store)
    rc, out = run_cli_store(["mark", "--row", LIVE_ID, "--transition", LIVE_TRANSITION,
                             "--reason", LIVE_REASON, "--evidence-ref", LIVE_EVIDENCE], cli_store)
    check(rc == 0 and "RESULT: PASS" in out, "CLI mark returns RESULT: PASS", out.strip())
    rc, out = run_cli_store(["list"], cli_store)
    check(rc == 0 and LIVE_ID in out and "unverifiable" in out, "CLI list shows the live instance", out.strip())
    # A refused CLI mark exits 1 with a FAIL: line, no traceback.
    rc, out = run_cli_store(["mark", "--row", LIVE_ID, "--transition", "T-R11",
                             "--reason", "again"], cli_store)
    check(rc != 0 and "FAIL:" in out and "Traceback" not in out, "CLI refuses a duplicate mark cleanly", out.strip())
    rc, out = run_cli_store(["reopen", "--row", LIVE_ID, "--reason", "new witness"], cli_store)
    check(rc == 0 and "RESULT: PASS" in out, "CLI reopen returns RESULT: PASS", out.strip())
    rc, out = run_cli_store(["list"], cli_store)
    check(rc == 0 and "empty" in out, "CLI list reports an empty ledger after reopen", out.strip())


if __name__ == "__main__":
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    sys.exit(main())
