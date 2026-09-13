#!/usr/bin/env python3
"""Garden curation review surface: the operator-facing queue, decision commands, and audit history.

Usage:
    python3 scripts/garden_review.py queue      --dir DIR [--json]
    python3 scripts/garden_review.py show       --dir DIR --candidate-id ID [--json]
    python3 scripts/garden_review.py accept     --dir DIR --candidate-id ID --reason REASON [--actor NAME] [--json]
    python3 scripts/garden_review.py hold       --dir DIR --candidate-id ID --reason REASON [--actor NAME] [--json]
    python3 scripts/garden_review.py reject     --dir DIR --candidate-id ID --reason REASON [--actor NAME] [--json]
    python3 scripts/garden_review.py duplicate  --dir DIR --candidate-id ID --reason REASON [--actor NAME] [--json]
    python3 scripts/garden_review.py reopen     --dir DIR --candidate-id ID --reason REASON [--actor NAME] [--json]
    python3 scripts/garden_review.py audit      --dir DIR [--candidate-id ID] [--json]

W1.5 of the Garden corpus program (`docs/program/W1_DECOMPOSITION.md` section "W1.5 - Curation
review + decision recording + audit history"). This is the loop's payoff: a text-first, newest-first
review surface where the operator's `accept / hold / reject / duplicate` decision is a recorded,
audited transition -- never a silent state flip.

What this module guarantees (and what `scripts/check_garden_review.py` asserts):

  1. **One write gate, atomic.** Every decision goes through `garden_store.Store.curate`, which
     moves `curation_state` along a legal T-C1..T-C12 transition and, when the model requires it,
     the corpus state too (T-P1 `candidate_only -> eligible` on acceptance, authority `system`;
     T-P7 `eligible -> candidate_only` when an acceptance is withdrawn, `T-C8`/`T-C9`, authority
     `operator`) -- all in one transaction with every audit row, so no dimension is ever stranded
     (`docs/program/STATE_MODEL.md` section 3).  The command that decides writes nothing else.
  2. **A curation decision implies no research.** No command here touches `research_state`; it is
     rendered read-only and always `not_started`. (`curate` has no research write path.)
  3. **`--reason` is required.** An empty or missing reason is refused before anything is written.
  4. **A refused decision writes nothing at all** (an illegal transition, a missing candidate, or a
     missing reason leaves the store byte-identical).
  5. **The queue is read-only and explicit.** `queue` prints the unreviewed queue
     (`curation_state = 'new'`) newest first, rendering the capture verbatim, the normalized
     proposal, the normalization notes, and the duplicate hints each with an explicit
     machine-inferred-vs-asserted marker (`STATE_MODEL.md` invariant 6). `show` prints any one
     candidate with its audit history; `audit` prints the append-only decision log.
  6. **Everything is audited.** Each decision records actor, actor_kind, timestamp, from_state,
     to_state, transition_id, and reason in the append-only `decisions` ledger.

Deliberately absent (out of W1.5 scope): any research action (there is no research surface);
canonical admission and retirement (T-P2..T-P6, including retirement T-P3, are W3/wave work); any
write to `quotes.csv` / `sources.csv` (read-only for the whole of W1); and any schema migration
(the `decisions` ledger and the four state columns already exist from W1.1).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden_store import CURATION_ACTIONS, Store, StoreError, json_line  # noqa: E402

#: The actor recorded for a decision when `--actor` is omitted. Every curation decision in W1.5
#: is the operator's; this is the fallback identity, not a way to make a decision "anonymous".
DEFAULT_ACTOR = "operator"

#: The explicit machine-inferred-vs-asserted markers (`STATE_MODEL.md` invariant 6).
M_ASSERTED = "asserted (the verbatim encounter)"
M_DERIVED = "derived (deterministic normalization of the capture)"
M_NOTES = "asserted (what changed and why)"
M_HINT = "machine-inferred (a hint is evidence, never a decision)"
M_RESEARCH = "not_started (read-only in W1.5: a curation action never changes it)"
M_NOTE = "hints are not decisions: only the operator sets 'duplicate'"


class ReviewError(Exception):
    """A refusal this module is designed to make (bad input, not a bug)."""


def _candidate_detail(store: Store, candidate_id: str) -> dict:
    row = store.conn.execute(
        "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
    ).fetchone()
    if row is None:
        raise ReviewError(f"no candidate {candidate_id!r} in the store")
    captures = [
        dict(r)
        for r in store.conn.execute(
            "SELECT c.* FROM candidate_captures cc JOIN captures c ON c.capture_id = cc.capture_id "
            "WHERE cc.candidate_id = ? ORDER BY cc.ordinal",
            (candidate_id,),
        )
    ]
    hints = [
        dict(r)
        for r in store.conn.execute(
            "SELECT hint_seq, kind, target, basis FROM duplicate_hints "
            "WHERE candidate_id = ? ORDER BY hint_seq",
            (candidate_id,),
        )
    ]
    history = [
        dict(r)
        for r in store.conn.execute(
            "SELECT transition_id, dimension, from_state, to_state, actor, actor_kind, "
            "occurred_at, reason FROM decisions "
            "WHERE subject_kind = 'candidate' AND subject_id = ? ORDER BY seq",
            (candidate_id,),
        )
    ]
    return {"candidate": dict(row), "captures": captures, "hints": hints, "history": history}


def _render(detail: dict) -> list[str]:
    """The text view of one candidate: capture, proposal, notes, hints (marked), states (read-only)."""
    cand = detail["candidate"]
    lines: list[str] = [f"candidate: {cand['candidate_id']}"]
    lines.append(f"  curation_state: {cand['curation_state']}  (the operator decides)")
    lines.append(f"  research_state: {M_RESEARCH}")
    lines.append(f"  corpus_state: {cand['corpus_state']}")
    lines.append(f"  work_state: {cand['work_state']}")
    for capture in detail["captures"]:
        lines.append(f"  capture ({M_ASSERTED}):")
        lines.append(f"    {capture['captured_text']}")
        lines.append(
            f"    attribution: {capture['captured_attribution']!r}  "
            f"citation: {capture['captured_citation']!r}  "
            f"method: {capture['capture_method']!r}  captured_by: {capture['captured_by']!r}"
        )
    lines.append(f"  proposal ({M_DERIVED}):")
    lines.append(f"    candidate_text: {cand['candidate_text']!r}")
    lines.append(f"    candidate_author: {cand['candidate_author']!r}")
    lines.append(f"    candidate_source_ref: {cand['candidate_source_ref']!r}")
    lines.append(f"  normalization_notes ({M_NOTES}):")
    lines.append(f"    {cand['normalization_notes']}")
    if detail["hints"]:
        lines.append(f"  duplicate hints ({M_HINT}):")
        for hint in detail["hints"]:
            lines.append(
                f"    [{hint['kind']}] -> {hint['target']}  basis={hint['basis']}"
            )
        lines.append(f"    ({M_NOTE})")
    else:
        lines.append(f"  duplicate hints ({M_HINT}): (none)")
    if detail["history"]:
        lines.append("  audit history (append-only, newest first):")
        for entry in reversed(detail["history"]):
            lines.append(
                f"    {entry['transition_id']} {entry['from_state']} -> {entry['to_state']}  "
                f"{entry['actor']} ({entry['actor_kind']})  {entry['occurred_at']}  "
                f"{entry['reason']}"
            )
    return lines


def _queue_rows(store: Store) -> list[dict]:
    """The unreviewed queue (`curation_state = 'new'`), newest first (requirement 6 of W1)."""
    return [
        dict(r)
        for r in store.conn.execute(
            "SELECT candidate_id FROM candidates WHERE curation_state = 'new' "
            "ORDER BY created_at DESC, candidate_id"
        )
    ]


def _decision_rows(store: Store, candidate_id: str | None) -> list[dict]:
    if candidate_id is not None:
        if not store.conn.execute(
            "SELECT 1 FROM candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone():
            raise ReviewError(f"no candidate {candidate_id!r} in the store")
        rows = store.conn.execute(
            "SELECT seq, transition_id, dimension, from_state, to_state, actor, actor_kind, "
            "occurred_at, reason FROM decisions "
            "WHERE subject_kind = 'candidate' AND subject_id = ? ORDER BY seq DESC",
            (candidate_id,),
        )
    else:
        rows = store.conn.execute(
            "SELECT seq, transition_id, dimension, from_state, to_state, actor, actor_kind, "
            "occurred_at, reason FROM decisions ORDER BY seq DESC"
        )
    return [dict(r) for r in rows]


def cmd_queue(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        ids = _queue_rows(store)
        details = [_candidate_detail(store, row["candidate_id"]) for row in ids]
        counts = store.counts()
    if args.json:
        print(json_line({"queue": [d["candidate"]["candidate_id"] for d in details], "counts": counts}))
        return 0
    print(f"store: {args.dir}")
    print(f"unreviewed queue (curation_state='new'), newest first: {len(details)} candidate(s)")
    for detail in details:
        for line in _render(detail):
            print(line)
    print(f"counts: {json_line(counts)}")
    print("RESULT: PASS")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        detail = _candidate_detail(store, args.candidate_id)
        counts = store.counts()
    if args.json:
        print(json_line({"candidate": detail, "counts": counts}))
        return 0
    print(f"store: {args.dir}")
    for line in _render(detail):
        print(line)
    print(f"counts: {json_line(counts)}")
    print("RESULT: PASS")
    return 0


def _run_action(args: argparse.Namespace) -> int:
    actor = args.actor or DEFAULT_ACTOR
    with Store(args.dir) as store:
        result = store.curate(
            args.candidate_id, action=args.action, actor=actor, reason=args.reason
        )
        counts = store.counts()
    if args.json:
        print(json_line({"decision": result, "counts": counts}))
        return 0
    print(f"store: {args.dir}")
    print(
        f"{args.action}: {result['candidate_id']}  {result['curation']['from']} -> "
        f"{result['curation']['to']}  ({result['curation']['transition_id']})"
    )
    if result["corpus"] is not None:
        c = result["corpus"]
        print(
            f"  corpus follow-on: {c['from']} -> {c['to']}  ({c['transition_id']}, "
            f"authority {c['authority']})"
        )
    print(
        f"audit: {len(result['seq'])} decision row(s) appended (append-only), actor={actor}, "
        f"reason={args.reason!r}"
    )
    print(
        "research_state was not touched: a curation decision implies no research "
        "(it stays 'not_started')"
    )
    print(f"counts: {json_line(counts)}")
    print("RESULT: PASS")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        rows = _decision_rows(store, args.candidate_id)
    if args.json:
        print(json_line({"decisions": rows}))
        return 0
    print(f"store: {args.dir}")
    if args.candidate_id:
        print(f"decision log for {args.candidate_id}, newest first ({len(rows)} row(s)):")
    else:
        print(f"decision log (all subjects), newest first ({len(rows)} row(s)):")
    for row in rows:
        print(
            f"  {row['transition_id']} [{row['dimension']}] {row['from_state']} -> "
            f"{row['to_state']}  {row['actor']} ({row['actor_kind']})  {row['occurred_at']}  "
            f"{row['reason']}"
        )
    print("the decision log is append-only: a corrected decision is a new row, never an edit")
    print("RESULT: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    queue = sub.add_parser(
        "queue",
        help="print the unreviewed queue (curation_state='new'), newest first",
        description=(
            "Read-only. Print every candidate that is still 'new', newest first, with the "
            "capture verbatim, the proposed values, the normalization notes, and the duplicate "
            "hints each marked as with the machine-inferred-vs-asserted marker."
        ),
    )
    queue.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    queue.add_argument("--json", action="store_true", help="one canonical JSON object")
    queue.set_defaults(func=cmd_queue)

    show = sub.add_parser(
        "show",
        help="print one candidate with its audit history (read-only)",
        description="Read-only. Render any one candidate's full review view, in any curation state.",
    )
    show.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    show.add_argument("--candidate-id", required=True, help="the candidate to render")
    show.add_argument("--json", action="store_true", help="one canonical JSON object")
    show.set_defaults(func=cmd_show)

    audit = sub.add_parser(
        "audit",
        help="print the append-only decision log (read-only)",
        description="Read-only. Print the decision log, newest first, for the whole store or one candidate.",
    )
    audit.add_argument("--dir", required=True, help="store directory (run 'create' first)")
    audit.add_argument("--candidate-id", default=None, help="limit to one candidate")
    audit.add_argument("--json", action="store_true", help="one canonical JSON object")
    audit.set_defaults(func=cmd_audit)

    for action in CURATION_ACTIONS:
        cmd_parser = sub.add_parser(
            action,
            help=f"take a curation decision: move a candidate to {CURATION_ACTIONS[action]!r}",
            description=(
                f"Record one operator curation decision moving the candidate along a legal "
                f"T-C transition (towards curations_state={CURATION_ACTIONS[action]!r}), append "
                f"the corresponding audit row(s) in the same transaction, and fire the corpus "
                f"follow-on the state model requires. --reason is required; nothing is written "
                f"on a refusal. A curation decision implies no research."
            ),
        )
        cmd_parser.add_argument("--dir", required=True, help="store directory (run 'create' first)")
        cmd_parser.add_argument("--candidate-id", required=True, help="the candidate to decide on")
        cmd_parser.add_argument(
            "--reason", required=True, help="why this decision (required; never omitted)"
        )
        cmd_parser.add_argument(
            "--actor", default=None, help=f"who decided (default: {DEFAULT_ACTOR})"
        )
        cmd_parser.add_argument("--json", action="store_true", help="one canonical JSON object")
        cmd_parser.set_defaults(func=_run_action, action=action)

    args = parser.parse_args(argv)
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    try:
        return args.func(args)
    except (ReviewError, StoreError) as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())