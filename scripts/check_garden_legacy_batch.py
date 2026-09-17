#!/usr/bin/env python3
"""Deterministic acceptance test for the D4 legacy batch capture.

Usage:
    python3 scripts/check_garden_legacy_batch.py

Runs mostly in a throwaway temporary directory (never mutating the repo store) and asserts
the D4 acceptance criteria from `docs/program/D4_LEGACY_BATCH_CAPTURE.md` (decision D4,
2026-09-12, `docs/DECISIONS.md`): the 324 legacy rows get **ONE batch capture** for the
2026-09-11 rehabilitation import, with a membership side-car keyed by legacy row id.

  1. `create` applies migration `0003_legacy_batch_capture` and the membership table exists;
  2. `seed` writes exactly one `legacy-import` capture with the fixed true statement and
     links every `quotes.csv` id to it — never invents per-row quote text, never creates
     candidates;
  3. re-seeding the same set is a no-op; a conflicting capture/membership is refused and
     writes nothing;
  4. the membership section exports, ordered by legacy row id, and round-trips;
  5. the CLI `seed` / `show` / `verify` surfaces work through subprocesses;
  6. `quotes.csv` / `sources.csv` are byte-identical before and after.

Exits 0 with `RESULT: PASS` when every check holds, non-zero with `RESULT: FAIL` and one
`FAIL:` line per broken check — never a traceback, even on a broken store.
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
    LEGACY_BATCH_ARCHIVE_QUOTES_SHA256,
    LEGACY_BATCH_ARCHIVE_SOURCES_SHA256,
    LEGACY_BATCH_CAPTURE_ID,
    LEGACY_BATCH_CAPTURED_AT,
    LEGACY_BATCH_CAPTURED_TEXT,
    LEGACY_BATCH_CONTEXT_NOTES,
    LEGACY_BATCH_EXPECTED_ROW_COUNT,
    LEGACY_BATCH_RAW_ARTIFACT_REF,
    SCHEMA_VERSION,
    STORE_FILENAME,
    Store,
    StoreError,
    create_store,
    parse_export,
)

QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
CLI = ROOT / "scripts" / "garden_legacy_batch.py"

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
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def quote_ids() -> list[str]:
    with QUOTES.open(newline="", encoding="utf-8") as handle:
        return [row["id"] for row in csv.DictReader(handle)]


def run_checks(scratch: Path) -> None:
    store_dir = scratch / "store"
    ids = quote_ids()
    check(
        len(ids) == LEGACY_BATCH_EXPECTED_ROW_COUNT,
        f"quotes.csv still has exactly {LEGACY_BATCH_EXPECTED_ROW_COUNT} rows",
        str(len(ids)),
    )
    check(
        len(ids) == len(set(ids)),
        "quotes.csv ids are unique",
    )

    # -- 1. schema: migration 0003 + membership table ---------------------------------
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
            for row in store.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        check(
            "legacy_batch_membership" in tables,
            "the schema has the legacy_batch_membership table",
            f"missing from {sorted(tables)}",
        )
        check(
            set(store.counts())
            == {
                "captures",
                "candidates",
                "candidate_captures",
                "duplicate_hints",
                "decisions",
                "legacy_verification",
                "legacy_batch_membership",
            },
            "counts() exposes the legacy_batch_membership table",
        )
        check(
            store.legacy_batch_capture() is None
            and store.legacy_batch_membership() == [],
            "a fresh store has no legacy batch capture or membership",
        )

    # -- 2. seed: one capture + 324 membership rows, no candidates --------------------
    with Store(store_dir) as store:
        before = store.export_bytes()
        result = store.seed_legacy_batch_capture(ids)
        check(
            result["status"] == "created"
            and result["capture_id"] == LEGACY_BATCH_CAPTURE_ID
            and result["row_count"] == LEGACY_BATCH_EXPECTED_ROW_COUNT,
            "seed creates the batch capture for all quotes.csv ids",
            str(result),
        )
        capture = store.legacy_batch_capture()
        check(
            capture is not None
            and capture["capture_id"] == LEGACY_BATCH_CAPTURE_ID
            and capture["capture_method"] == "legacy-import"
            and capture["captured_by"] == "legacy-import"
            and capture["captured_at"] == LEGACY_BATCH_CAPTURED_AT
            and capture["captured_text"] == LEGACY_BATCH_CAPTURED_TEXT
            and capture["context_notes"] == LEGACY_BATCH_CONTEXT_NOTES
            and capture["raw_artifact_ref"] == LEGACY_BATCH_RAW_ARTIFACT_REF
            and capture["captured_attribution"] == "unknown"
            and "Encounter context unknown" in capture["captured_text"]
            and LEGACY_BATCH_ARCHIVE_QUOTES_SHA256 in capture["captured_text"]
            and LEGACY_BATCH_ARCHIVE_SOURCES_SHA256 in capture["captured_text"],
            "the batch capture is legacy-import, fixed-text, and notes unknown encounter context",
            str(dict(capture) if capture else None),
        )
        members = store.legacy_batch_membership()
        check(
            [m["legacy_row_id"] for m in members] == sorted(ids)
            and all(m["capture_id"] == LEGACY_BATCH_CAPTURE_ID for m in members)
            and len(members) == LEGACY_BATCH_EXPECTED_ROW_COUNT,
            "membership links every quotes.csv id to the single batch capture",
            f"count={len(members)}",
        )
        check(
            store.counts()["candidates"] == 0
            and store.counts()["candidate_captures"] == 0,
            "seed creates no candidates and no candidate_captures links",
            str(store.counts()),
        )
        # The capture body must not be any individual quote text.
        sample_quote = next(
            row["quote_text"]
            for row in csv.DictReader(QUOTES.open(newline="", encoding="utf-8"))
        )
        check(
            capture is not None and sample_quote not in capture["captured_text"],
            "captured_text is the batch statement, not a fabricated per-row quote",
        )
        after = store.export_bytes()
    check(before != after, "seed changed the store (capture + membership landed)")

    # -- 3. idempotent re-seed; conflicting seed refused ------------------------------
    with Store(store_dir) as store:
        before = store.export_bytes()
        again = store.seed_legacy_batch_capture(ids)
        check(
            again["status"] == "no-op" and store.export_bytes() == before,
            "re-seeding the same set is a no-op and writes nothing",
            str(again),
        )
        try:
            # Same cardinality, different membership: swap one id for a non-corpus id so
            # the cardinality guard is not the one that fires.
            alt = list(ids)
            alt[0] = "999999"
            store.seed_legacy_batch_capture(alt)
            fail("a conflicting membership set was accepted")
        except StoreError as exc:
            check(
                "different id set" in str(exc),
                "a conflicting membership set is refused by the explicit guard",
                str(exc),
            )
        check(store.export_bytes() == before, "the refused conflicting seed wrote nothing")

        # Empty / wrong-sized / duplicate id list refused before any write.
        try:
            store.seed_legacy_batch_capture([])
            fail("an empty legacy_row_ids list was accepted")
        except StoreError as exc:
            check(
                "must be non-empty" in str(exc),
                "an empty legacy_row_ids list is refused",
                str(exc),
            )
        try:
            store.seed_legacy_batch_capture(ids[:-1])
            fail("a wrong-sized legacy_row_ids list was accepted by the Store API")
        except StoreError as exc:
            check(
                f"expects exactly {LEGACY_BATCH_EXPECTED_ROW_COUNT}" in str(exc),
                "the Store API refuses a legacy_row_ids list whose length is not 324",
                str(exc),
            )
        try:
            # Pad a duplicate into a 324-length list so the cardinality guard is not
            # the one that fires — the duplicate guard must have its own falsifier.
            dup_list = list(ids)
            dup_list[-1] = ids[0]
            store.seed_legacy_batch_capture(dup_list)
            fail("a duplicate legacy_row_id inside the seed set was accepted")
        except StoreError as exc:
            check(
                "duplicate legacy_row_id" in str(exc),
                "a duplicate legacy_row_id inside the seed set is refused",
                str(exc),
            )
        check(
            store.export_bytes() == before,
            "refused empty/wrong-sized/duplicate seeds wrote nothing",
        )

    # -- 4. export section + round-trip -----------------------------------------------
    with Store(store_dir) as store:
        store.write_export(store.dir / "garden.export.txt")
    text = (store_dir / "garden.export.txt").read_bytes()
    check(text.startswith((EXPORT_HEADER + "\n").encode()), f"export starts with {EXPORT_HEADER!r}")
    records = parse_export(text)
    check(
        len(records["legacy_batch_membership"]) == LEGACY_BATCH_EXPECTED_ROW_COUNT
        and [r["legacy_row_id"] for r in records["legacy_batch_membership"]] == sorted(ids),
        "the export carries the membership section ordered by legacy row id",
        str(len(records["legacy_batch_membership"])),
    )
    check(
        len(records["captures"]) == 1
        and records["captures"][0]["capture_id"] == LEGACY_BATCH_CAPTURE_ID,
        "the export carries exactly the one batch capture",
        str([c["capture_id"] for c in records["captures"]]),
    )
    section_headers = [
        ln
        for ln in text.decode("utf-8").splitlines()
        if ln.startswith("[") and ln.endswith("]")
    ]
    check(
        section_headers
        == [
            "[meta]",
            "[captures]",
            "[candidate_captures]",
            "[candidates]",
            "[duplicate_hints]",
            "[decisions]",
            "[legacy_verification]",
            "[legacy_batch_membership]",
        ],
        "the export sections appear in the documented fixed order",
        str(section_headers),
    )
    check(
        records["meta"]["schema_version"] == SCHEMA_VERSION,
        "the export meta schema_version is unchanged by the membership section",
        str(records["meta"]["schema_version"]),
    )
    (store_dir / STORE_FILENAME).unlink()
    create_store(store_dir)
    with Store(store_dir) as store:
        status = store.import_bytes(text)
        reexport = store.export_bytes()
    check(reexport == text, "the batch capture round-trips (write -> wipe -> re-import)")
    expected_count = 1 + LEGACY_BATCH_EXPECTED_ROW_COUNT  # capture + membership rows
    check(
        f"imported {expected_count} record(s)" in status,
        "the import reports exactly the loaded record count (capture + membership)",
        status,
    )

    # -- 5. CLI seed / show / verify ---------------------------------------------------
    cli_dir = scratch / "cli-store"
    create_store(cli_dir)
    code, out = run_cli(["seed", "--dir", str(cli_dir), "--quotes", str(QUOTES)])
    check(
        code == 0 and "RESULT: PASS" in out and LEGACY_BATCH_CAPTURE_ID in out,
        "CLI seed exits 0 and names the batch capture",
        out.strip()[-300:],
    )
    code, out = run_cli(["show", "--dir", str(cli_dir)])
    check(
        code == 0
        and "RESULT: PASS" in out
        and "legacy-import" in out
        and str(LEGACY_BATCH_EXPECTED_ROW_COUNT) in out,
        "CLI show reports legacy-import and the membership count",
        out.strip()[-300:],
    )
    code, out = run_cli(["verify", "--dir", str(cli_dir), "--quotes", str(QUOTES)])
    check(
        code == 0 and "RESULT: PASS" in out and "verified" in out,
        "CLI verify exits 0 against the live quotes.csv and archive digests",
        out.strip()[-300:],
    )
    # A verify against a quotes file with the wrong count must fail.
    bad_quotes = scratch / "bad-quotes.csv"
    bad_quotes.write_text("id,quote_text\n1,only one\n", encoding="utf-8")
    code, out = run_cli(["verify", "--dir", str(cli_dir), "--quotes", str(bad_quotes)])
    check(
        code != 0
        and "RESULT: FAIL" in out
        and f"expects exactly {LEGACY_BATCH_EXPECTED_ROW_COUNT}" in out,
        "CLI verify refuses a quotes.csv whose row count is not 324",
        out.strip()[-300:],
    )


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-legacy-batch-check-"))
    quotes_before = sha256(QUOTES) if QUOTES.exists() else None
    sources_before = sha256(SOURCES) if SOURCES.exists() else None
    print(f"scratch: {scratch}")
    try:
        run_checks(scratch)
    except Exception as exc:  # no traceback on a broken store: RESULT must still print
        fail(f"unexpected {type(exc).__name__}: {exc}")
    finally:
        if quotes_before is not None:
            if sha256(QUOTES) != quotes_before:
                fail("quotes.csv changed during the run")
            else:
                ok("quotes.csv is byte-identical before and after the run")
        if sources_before is not None:
            if sha256(SOURCES) != sources_before:
                fail("sources.csv changed during the run")
            else:
                ok("sources.csv is byte-identical before and after the run")
        shutil.rmtree(scratch, ignore_errors=True)

    if failures:
        print(f"RESULT: FAIL ({len(failures)} checks)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
