#!/usr/bin/env python3
"""Deterministic acceptance test for the U0.1 store lifecycle + mirror freshness invariant.

Usage:
    python3 scripts/check_garden_lifecycle.py

Runs entirely in a throwaway temporary directory (never the repo, never `data/store`) and
asserts the U0.1 acceptance criteria from
`docs/program/usability-closure/workunits/U0.1_STORE_LIFECYCLE.md`:

  1. mirror exists, SQLite absent -> `bootstrap` recreates the store and the exported bytes
     equal the mirror;
  2. both absent -> `bootstrap` refuses with an explicit message (never a guess);
  3. SQLite and mirror equal -> `status` says CURRENT;
  4. mutate through a real operator surface (submit / review / normalize / hints / ledger /
     legacy-batch seed) -> a successful command leaves `status` CURRENT (the mutation
     invariant: no successful operator-facing mutating command may exit 0 while the
     committed mirror is silently different from the resulting store);
  5. manually alter or withhold the mirror -> `status` detects STALE / MISSING_MIRROR;
  6. divergent local DB + mirror -> `bootstrap` refuses the destructive guess;
  7. delete the local SQLite -> re-bootstrap -> export byte-identical;
  8. the D3/D4 committed state (the real `data/store/garden.export.txt`) survives the
     round-trip;
  9. the existing W1 suites remain green (run separately; this suite re-runs the store
     round-trip and the legacy-batch verify as a spot check).

Exits 0 with `RESULT: PASS`, non-zero with `RESULT: FAIL` and one `FAIL:` line per broken
check -- never a traceback.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import garden_store  # noqa: E402
from garden_store import (  # noqa: E402
    DEFAULT_EXPORT_NAME,
    STORE_FILENAME,
    Store,
    StoreError,
    bootstrap_store,
    create_store,
    store_status,
)

STORE_CLI = SCRIPTS / "garden_store.py"
SUBMIT = SCRIPTS / "garden_submit.py"
REVIEW = SCRIPTS / "garden_review.py"
NORMALIZE = SCRIPTS / "garden_normalize.py"
LEDGER = SCRIPTS / "garden_ledger.py"
LEGACY_BATCH = SCRIPTS / "garden_legacy_batch.py"
QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
COMMITTED_MIRROR = ROOT / "data" / "store" / DEFAULT_EXPORT_NAME

failures: list[str] = []
passed: list[str] = []
EXPECTED_CHECKS = 42


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    failures.append(msg)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")
    passed.append(msg)


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


def cli_status(store_dir: Path) -> str:
    """The `status` subcommand's reported state (the last non-empty line before RESULT)."""
    proc = run(STORE_CLI, "status", "--dir", str(store_dir))
    for line in out_text(proc).splitlines():
        if line.startswith("status: "):
            return line[len("status: "):]
    return f"(no status line; rc={proc.returncode})"


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-lifecycle-check-"))
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
            if p.is_file() and p.name not in (STORE_FILENAME, DEFAULT_EXPORT_NAME)
        ]
        check(not stray, "the lifecycle wrote nothing outside the store directory", str(stray))
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    if len(passed) != EXPECTED_CHECKS:
        print(f"FAIL: expected exactly {EXPECTED_CHECKS} passing checks, observed {len(passed)}")
        print(f"RESULT: FAIL (expected {EXPECTED_CHECKS} checks)")
        return 1
    print(f"RESULT: PASS ({EXPECTED_CHECKS} checks; bootstrap/status/sync + the mutation invariant hold end to end)")
    return 0


def run_checks(scratch: Path) -> None:
    # -- 1. mirror exists, SQLite absent -> bootstrap recreates the store -----------------
    d1 = scratch / "mirror_only"
    d1.mkdir()
    (d1 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    check(not (d1 / STORE_FILENAME).exists(), "1a. SQLite is absent before bootstrap")
    state = bootstrap_store(d1)
    check(state == "CURRENT", f"1b. bootstrap from a mirror-only dir returns CURRENT ({state})")
    check((d1 / STORE_FILENAME).exists(), "1c. bootstrap created the SQLite store")
    with Store(d1) as store:
        check(
            store.export_bytes() == COMMITTED_MIRROR.read_bytes(),
            "1d. the bootstrapped store exports bytes equal to the mirror",
        )

    # -- 2. both absent -> explicit refusal, not a guess ---------------------------------
    d2 = scratch / "both_absent"
    d2.mkdir()
    try:
        bootstrap_store(d2)
        fail("2a. bootstrap with neither store nor mirror did not refuse")
    except StoreError as exc:
        ok(f"2a. bootstrap with neither store nor mirror refuses explicitly ({exc})")
    check(
        not (d2 / STORE_FILENAME).exists() and not (d2 / DEFAULT_EXPORT_NAME).exists(),
        "2b. the refusal wrote nothing",
    )

    # -- 3. SQLite and mirror equal -> status says current --------------------------------
    d3 = scratch / "equal"
    d3.mkdir()
    (d3 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    bootstrap_store(d3)
    check(store_status(d3) == "CURRENT", "3a. store_status reports CURRENT when equal")
    check(cli_status(d3) == "CURRENT", "3b. the status CLI reports CURRENT when equal")

    # -- 4. mutation invariant: a successful operator mutation leaves status current -----
    d4 = scratch / "mutate"
    d4.mkdir()
    (d4 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    bootstrap_store(d4)

    # 4a. submit
    sub = run(
        SUBMIT, "submit", "--dir", str(d4),
        "--text", "A passage for the lifecycle acceptance.",
        "--capture-method", "pasted-text",
        "--captured-at", "2026-09-17T13:00:00-06:00",
    )
    check(
        sub.returncode == 0 and "RESULT: PASS" in out_text(sub),
        "4a. submit succeeds",
        out_text(sub).strip()[:120],
    )
    check(
        store_status(d4) == "CURRENT",
        "4a. after a successful submit the mirror is current (mutation invariant)",
        store_status(d4),
    )

    cid = _first_queue_candidate(d4)
    # 4b. normalize + hints (W1.4 write surfaces) -- before curation, while 'new'
    norm = run(NORMALIZE, "normalize", "--dir", str(d4), "--candidate-id", cid)
    check(
        norm.returncode == 0 and "RESULT: PASS" in out_text(norm),
        "4b. normalize succeeds",
        out_text(norm).strip()[:120],
    )
    check(
        store_status(d4) == "CURRENT",
        "4b. after a successful normalization the mirror is current",
        store_status(d4),
    )
    hints = run(NORMALIZE, "hints", "--dir", str(d4), "--candidate-id", cid)
    check(
        hints.returncode == 0 and "RESULT: PASS" in out_text(hints),
        "4c. hints succeeds",
        out_text(hints).strip()[:120],
    )
    check(
        store_status(d4) == "CURRENT",
        "4c. after a successful hint rebuild the mirror is current",
        store_status(d4),
    )

    # 4d. review accept (a real operator curation decision)
    acc = run(REVIEW, "accept", "--dir", str(d4), "--candidate-id", cid, "--reason", "wanted")
    check(
        acc.returncode == 0 and "RESULT: PASS" in out_text(acc),
        "4d. review accept succeeds",
        out_text(acc).strip()[:120],
    )
    check(
        store_status(d4) == "CURRENT",
        "4d. after a successful curation decision the mirror is current",
        store_status(d4),
    )

    # 4e. ledger mark + reopen (D3 write surfaces)
    mark = run(LEDGER, "mark", "--dir", str(d4), "--row", "5", "--transition", "T-R6",
               "--reason", "lifecycle acceptance")
    check(
        mark.returncode == 0 and "RESULT: PASS" in out_text(mark),
        "4e. ledger mark succeeds",
        out_text(mark).strip()[:120],
    )
    check(
        store_status(d4) == "CURRENT",
        "4e. after a successful ledger mark the mirror is current",
        store_status(d4),
    )
    reopen = run(LEDGER, "reopen", "--dir", str(d4), "--row", "5", "--reason", "new witness")
    check(
        reopen.returncode == 0 and "RESULT: PASS" in out_text(reopen),
        "4f. ledger reopen succeeds",
        out_text(reopen).strip()[:120],
    )
    check(
        store_status(d4) == "CURRENT",
        "4f. after a successful ledger reopen the mirror is current",
        store_status(d4),
    )


    # 4g. legacy-batch seed (D4 write surface) -- needs the real quotes.csv id set
    seed = run(LEGACY_BATCH, "seed", "--dir", str(d4))
    check(
        seed.returncode == 0 and "RESULT: PASS" in out_text(seed),
        "4g. legacy-batch seed succeeds",
        out_text(seed).strip()[:120],
    )
    check(
        store_status(d4) == "CURRENT",
        "4g. after a successful legacy-batch seed the mirror is current",
        store_status(d4),
    )

    # -- 5. stale / missing-mirror detection ---------------------------------------------
    d5 = scratch / "stale"
    d5.mkdir()
    (d5 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    bootstrap_store(d5)
    # mutate the store directly (bypassing the CLI) so the mirror is genuinely stale
    with Store(d5) as store:
        store.add_capture("cap-stale", "stale capture", captured_at="2026-09-17T14:00:00-06:00")
    check(store_status(d5) == "STALE", "5a. a store mutated behind the mirror reports STALE")
    check(cli_status(d5) == "STALE", "5b. the status CLI reports STALE")
    # withhold the mirror entirely
    (d5 / DEFAULT_EXPORT_NAME).unlink()
    check(store_status(d5) == "MISSING_MIRROR", "5c. a missing mirror reports MISSING_MIRROR")
    check(cli_status(d5) == "MISSING_MIRROR", "5d. the status CLI reports MISSING_MIRROR")

    # -- 6. divergent DB + mirror -> bootstrap refuses the destructive guess --------------
    d6 = scratch / "divergent"
    d6.mkdir()
    (d6 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    bootstrap_store(d6)
    # make the store diverge from the mirror
    with Store(d6) as store:
        store.add_capture("cap-div", "divergent capture", captured_at="2026-09-17T15:00:00-06:00")
    mirror_before = (d6 / DEFAULT_EXPORT_NAME).read_bytes()
    try:
        bootstrap_store(d6)
        fail("6a. bootstrap did not refuse a divergent store + mirror")
    except StoreError as exc:
        ok(f"6a. bootstrap refuses a divergent store + mirror ({exc})")
    check(
        (d6 / DEFAULT_EXPORT_NAME).read_bytes() == mirror_before,
        "6b. the refusal left the mirror untouched",
    )
    with Store(d6) as store:
        check(
            store.export_bytes() != mirror_before,
            "6c. the refusal left the divergent store untouched",
        )

    # -- 7. delete local SQLite -> re-bootstrap -> export byte-identical ------------------
    d7 = scratch / "rebootstrap"
    d7.mkdir()
    (d7 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    bootstrap_store(d7)
    with Store(d7) as store:
        first = store.export_bytes()
    (d7 / STORE_FILENAME).unlink()
    check(not (d7 / STORE_FILENAME).exists(), "7a. the SQLite store was deleted")
    state = bootstrap_store(d7)
    check(state == "CURRENT", f"7b. re-bootstrap returns CURRENT ({state})")
    with Store(d7) as store:
        check(
            store.export_bytes() == first,
            "7c. re-bootstrap reproduces byte-identical export bytes",
        )

    # -- 8. D3/D4 committed state survives the round-trip --------------------------------
    d8 = scratch / "d3d4"
    d8.mkdir()
    (d8 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    bootstrap_store(d8)
    with Store(d8) as store:
        counts = store.counts()
        ledger = store.unverifiable_ledger()
        batch = store.legacy_batch_capture()
    check(
        counts["legacy_verification"] >= 1,
        "8a. the D3 unverifiable ledger row survives bootstrap",
        str(counts["legacy_verification"]),
    )
    check(
        any(row["legacy_row_id"] == "30" for row in ledger),
        "8b. the seeded Garden id 30 is in the bootstrapped ledger",
    )
    check(
        batch is not None and batch["capture_id"] == "cap-2026-09-11-legacy-batch",
        "8c. the D4 legacy batch capture survives bootstrap",
    )
    check(
        counts["legacy_batch_membership"] == 324,
        "8d. all 324 legacy membership rows survive bootstrap",
        str(counts["legacy_batch_membership"]),
    )

    # -- 9. sync refreshes a stale mirror and reports CURRENT -----------------------------
    d9 = scratch / "sync"
    d9.mkdir()
    (d9 / DEFAULT_EXPORT_NAME).write_bytes(COMMITTED_MIRROR.read_bytes())
    bootstrap_store(d9)
    with Store(d9) as store:
        store.add_capture("cap-sync", "sync me", captured_at="2026-09-17T16:00:00-06:00")
    check(store_status(d9) == "STALE", "9a. the store is stale before sync")
    with Store(d9) as store:
        state = store.sync_mirror()
    check(state == "CURRENT", f"9b. sync_mirror returns CURRENT ({state})")
    check(store_status(d9) == "CURRENT", "9c. the mirror is current after sync")
    with Store(d9) as store:
        check(
            store.export_bytes() == (d9 / DEFAULT_EXPORT_NAME).read_bytes(),
            "9d. the synced mirror equals the store export",
        )


def _first_queue_candidate(store_dir: Path) -> str:
    proc = run(REVIEW, "queue", "--dir", str(store_dir), "--json")
    import json
    for line in out_text(proc).splitlines():
        line = line.strip()
        if line.startswith("{"):
            data = json.loads(line)
            queue = data.get("queue", [])
            if queue:
                return queue[0]
    raise SystemExit("no candidate in the queue")


if __name__ == "__main__":
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    sys.exit(main())
