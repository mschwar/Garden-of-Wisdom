#!/usr/bin/env python3
"""Garden `unverifiable` side-car ledger: record that a legacy row is unverifiable.

Usage:
    python3 scripts/garden_ledger.py mark   --dir DIR --row ID --transition T-Rx --reason REASON \
        [--evidence-ref REF] [--actor NAME] [--json]
    python3 scripts/garden_ledger.py reopen --dir DIR --row ID --reason REASON \
        [--actor NAME] [--json]
    python3 scripts/garden_ledger.py list   --dir DIR [--json]

Decision D3 (2026-09-12, `docs/DECISIONS.md`): `unverifiable` is represented in a **side-car
ledger keyed by legacy row id**, NOT by widening the 3-valued `quotes.csv` enum, so a record
proven unverifiable is no longer indistinguishable from a never-checked row. The ledger is a
table in the W1.1 store (`legacy_verification`), which is what "one store rather than two"
means -- it is not a separate file. Issue #5 / Garden id 30 is the live instance.

What this module guarantees (and what `scripts/check_garden_ledger.py` asserts):

  1. **Keyed by legacy row id, leaving the CSV untouched.** The ledger holds one row per
     `quotes.csv` `id`; `quotes.csv` / `sources.csv` are never read or written here.
  2. **One atomic write, audited.** `mark` inserts the ledger row AND appends a `research`
     `decisions` audit row (the declared STATE_MODEL transition, `From` derived from the
     transition table) in one transaction -- there is never a ledger row without its audit
     row. `reopen` reverses it (`T-R12 unverifiable -> in_research`) in one transaction.
  3. **Terminal state asserted.** `research_state` is fixed to `unverifiable`; `transition_id`
     must be one of the four transitions that terminate in `unverifiable`
     (T-R6 / T-R7 / T-R10 / T-R11).
  4. **No silent overwrite.** A legacy row is either unverifiable or it is not; `mark` refuses
     an id already in the ledger and `reopen` refuses one that is not.
  5. **A refused write writes nothing at all.** Every guard is checked before anything is
     written, so a refused `mark`/`reopen` leaves the store byte-identical.
  6. **Deterministic, diffable.** The ledger is an export section (`[legacy_verification]`,
     ordered by legacy row id), so it round-trips with the store and diffs in git.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden_store import (  # noqa: E402
    UNVERIFIABLE_FROM_STATE,
    Store,
    StoreError,
    json_line,
)

#: The actor recorded when `--actor` is omitted. Terminal research outcomes are
#: operator-adjudicated (`STATE_MODEL.md` section 2); this is the fallback identity, not a
#: way to make an adjudication "anonymous".
DEFAULT_ACTOR = "operator"


class LedgerError(Exception):
    """A refusal this module is designed to make (bad input, not a bug)."""


def _row_json(store: Store, legacy_row_id: str) -> dict:
    row = store.conn.execute(
        "SELECT legacy_row_id, research_state, transition_id, reason, evidence_ref, "
        "decided_by, decided_at FROM legacy_verification WHERE legacy_row_id = ?",
        (legacy_row_id,),
    ).fetchone()
    if row is None:
        raise LedgerError(f"legacy row {legacy_row_id!r} is not in the unverifiable ledger")
    return {key: row[key] for key in row.keys()}


def cmd_mark(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        result = store.mark_legacy_unverifiable(
            args.row,
            transition_id=args.transition,
            reason=args.reason,
            evidence_ref=args.evidence_ref,
            decided_by=args.actor or DEFAULT_ACTOR,
        )
        if args.json:
            print(json_line(result))
        else:
            print(
                f"legacy row {result['legacy_row_id']} marked {result['research_state']} "
                f"({result['transition_id']}); audit seq {result['seq']}"
            )
    print("RESULT: PASS")
    return 0


def cmd_reopen(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        result = store.reopen_legacy_unverifiable(
            args.row,
            reason=args.reason,
            decided_by=args.actor or DEFAULT_ACTOR,
        )
        if args.json:
            print(json_line(result))
        else:
            print(
                f"legacy row {result['legacy_row_id']} reopened "
                f"{result['from_state']} -> {result['to_state']} "
                f"({result['transition_id']}); audit seq {result['seq']}"
            )
    print("RESULT: PASS")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        rows = [
            {key: row[key] for key in row.keys()}
            for row in store.unverifiable_ledger()
        ]
        if args.json:
            for row in rows:
                print(json_line(row))
        else:
            if not rows:
                print("the unverifiable ledger is empty")
            for row in rows:
                print(
                    f"legacy row {row['legacy_row_id']}: {row['research_state']} "
                    f"({row['transition_id']}) decided_by={row['decided_by']} "
                    f"decided_at={row['decided_at']} evidence_ref={row['evidence_ref']}"
                )
                print(f"  reason: {row['reason']}")
    print("RESULT: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    mark = sub.add_parser(
        "mark",
        help="record that a legacy row (a quotes.csv id) is unverifiable",
        description=(
            "Record one operator adjudication that a legacy row is `unverifiable`, keyed by "
            "the legacy row id, leaving quotes.csv untouched. Appends the ledger row and its "
            "research audit row in one transaction. --reason is required; --transition must "
            "be one of the four research transitions that terminate in unverifiable "
            "(T-R6 / T-R7 / T-R10 / T-R11). Nothing is written on a refusal."
        ),
    )
    mark.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    mark.add_argument("--row", dest="row", required=True, help="the legacy quotes.csv row id")
    mark.add_argument(
        "--transition",
        required=True,
        help="STATE_MODEL research transition to unverifiable (T-R6/T-R7/T-R10/T-R11)",
    )
    mark.add_argument("--reason", required=True, help="why this adjudication (required)")
    mark.add_argument(
        "--evidence-ref",
        default="none",
        help="where the adjudication is evidenced (an issue, an export review; default 'none')",
    )
    mark.add_argument(
        "--actor", default=None, help=f"who decided (default: {DEFAULT_ACTOR})"
    )
    mark.add_argument("--json", action="store_true", help="one canonical JSON object")
    mark.set_defaults(func=cmd_mark)

    reopen = sub.add_parser(
        "reopen",
        help="reverse an unverifiable adjudication (a new witness appears, T-R12)",
        description=(
            "Reverse a legacy row's unverifiable adjudication: the row leaves the side-car "
            "ledger and the reversal is recorded as `T-R12 unverifiable -> in_research` in "
            "one transaction. --reason is required; nothing is written on a refusal."
        ),
    )
    reopen.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    reopen.add_argument("--row", dest="row", required=True, help="the legacy quotes.csv row id")
    reopen.add_argument("--reason", required=True, help="why this reversal (required)")
    reopen.add_argument(
        "--actor", default=None, help=f"who decided (default: {DEFAULT_ACTOR})"
    )
    reopen.add_argument("--json", action="store_true", help="one canonical JSON object")
    reopen.set_defaults(func=cmd_reopen)

    listing = sub.add_parser(
        "list",
        help="print the unverifiable ledger (read-only)",
        description="Read-only. Print every legacy row adjudicated unverifiable.",
    )
    listing.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    listing.add_argument("--json", action="store_true", help="one canonical JSON object per row")
    listing.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    try:
        return args.func(args)
    except (LedgerError, StoreError) as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
