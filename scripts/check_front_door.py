#!/usr/bin/env python3
"""U0.2 acceptance: the repo front door tells the truth about current state.

Usage:
    python3 scripts/check_front_door.py

Why this exists
---------------
The repo's implementation outran its front door: `AGENTS.md`, `README.md`,
`docs/program/README.md` and `docs/product/PRODUCT_DOCTRINE.md` kept asserting W1-era state
("no datastore, intake surface, discovery adapter, or W1 runtime code exists in this repo
yet", "W1 ... is in progress", and a command surface that stopped at the 2026-09-11 retrofit)
long after W1 shipped. Issue #27 was even *closed as COMPLETED* with the file unchanged, so
"the tracker says it landed" was not evidence either. A documentation claim that no check can
falsify drifts exactly like this, and a cold-start agent reading only the front door then
cannot answer "where are we?" without archaeology.

This is the smallest check that prevents that recurrence. It asserts three things about the
front door, and it deliberately does NOT try to be a documentation framework:

  1. **One live status authority.** `docs/program/usability-closure/CURRENT.md` is the single
     place live programme status lives; every front door routes to it, it names exactly one
     READY unit, and that unit's work-unit document and the last-completed unit's handoff
     both exist on disk (so status cannot point at a document that was never written).
  2. **Agreement.** `docs/queue.md`'s usability-closure section marks the *same* single unit
     READY. The two are derived by different code paths here (a heading value vs. a checkbox
     line), so the check compares them rather than trusting either.
  3. **No stale live-status claim.** The front door must not (a) name the W1 runtime/store as
     non-existent or (b) call W1 "in progress", and `AGENTS.md` must actually name its command
     surface: the store lifecycle entry point, every `scripts/garden_*.py` module in the tree
     (derived from the tree, never hard-coded, so a new module forces a front-door decision),
     the CSV change discipline, and the negative-control harness.

Historical documents are NOT scanned: `docs/program/W1_*.md`, the W0/Gate packets, the dated
`docs/audit/*` snapshots and the root `GARDEN_*_HANDOFF.md` files stay exactly as written.
A check that rewrote or forbade "W1 in progress" inside a *historical* packet would destroy
evidence, so the scan is scoped to the documents a cold-start agent can mistake for status.

Exits 0 with `RESULT: PASS`, non-zero with `RESULT: FAIL` and one `FAIL:` line per broken
check -- never a traceback.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
PROGRAM_README = ROOT / "docs" / "program" / "README.md"
PRODUCT_DOCTRINE = ROOT / "docs" / "product" / "PRODUCT_DOCTRINE.md"
QUEUE = ROOT / "docs" / "queue.md"
CURRENT = ROOT / "docs" / "program" / "usability-closure" / "CURRENT.md"
WORKUNITS = ROOT / "docs" / "program" / "usability-closure" / "workunits"
SCRIPTS = ROOT / "scripts"

CURRENT_POINTER = "docs/program/usability-closure/CURRENT.md"

# Every one of these must route live status to CURRENT.md.
ROUTED = (AGENTS, README, PROGRAM_README, PRODUCT_DOCTRINE, QUEUE)

# The documents a cold-start agent may read and mistake for live status. Historical packets
# are deliberately absent: they are evidence and must stay as written.
SCANNED = (AGENTS, README, PROGRAM_README, PRODUCT_DOCTRINE, QUEUE)

# (id, compiled pattern over whitespace-normalized text, why it is a stale live-status claim)
STALE_CLAIMS = (
    (
        "w1-runtime-or-store-absent",
        re.compile(r"\bno\b[^.]{0,90}\b(w1 runtime|w1 store|corpus[- ]program (runtime|store|datastore))\b[^.]{0,60}\bexists?\b", re.I),
        "claims the W1 runtime/store does not exist",
    ),
    (
        "w1-in-progress",
        re.compile(r"\bw1\b[^.]{0,90}\bin progress\b", re.I),
        "claims W1 is still in progress",
    ),
)

REQUIRED_CURRENT_HEADINGS = ("## Gate", "## Current READY unit", "## Last completed unit", "## Update rule")

UNIT_ID_RE = re.compile(r"(U\d+\.\d+)\b")
QUEUE_READY_RE = re.compile(r"^\s*-\s*\[[ x]\]\s*(U\d+\.\d+)\b[^\n]*—\s*READY\s*$", re.M)

EXPECTED_CHECKS = 23

failures: list[str] = []
passed: list[str] = []


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    failures.append(msg)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")
    passed.append(msg)


def check(condition: bool, msg: str) -> bool:
    if condition:
        ok(msg)
    else:
        fail(msg)
    return condition


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def normalize(text: str) -> str:
    """Collapse all whitespace runs to single spaces, so a pattern matches across line wraps."""
    return re.sub(r"\s+", " ", text)


def section_value(text: str, heading: str) -> str | None:
    """The first non-empty, non-quote body line of a `## heading` section."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == heading:
            for body in lines[index + 1:]:
                if not body.strip():
                    continue
                if body.lstrip().startswith("#"):
                    return None
                return body.strip()
            return None
    return None


def unit_id(value: str | None) -> str | None:
    if not value:
        return None
    match = UNIT_ID_RE.search(value)
    return match.group(1) if match else None


def handoff_path(unit: str) -> Path:
    return ROOT / f"GARDEN_{unit.replace('.', '_')}_HANDOFF.md"


def main() -> int:
    # ---------------------------------------------------------------- 1. the status authority
    current_text = read(CURRENT)
    check(CURRENT.exists(), f"1. CURRENT.md exists ({CURRENT_POINTER})")

    missing = [h for h in REQUIRED_CURRENT_HEADINGS if h not in current_text]
    check(
        not missing,
        f"2. CURRENT.md keeps its required structure "
        f"({'all present' if not missing else 'missing ' + ', '.join(repr(h) for h in missing)})",
    )

    heading_count = current_text.count("## Current READY unit")
    check(
        heading_count == 1,
        f"3. CURRENT.md has exactly one '## Current READY unit' heading (found {heading_count})",
    )

    ready_value = section_value(current_text, "## Current READY unit")
    ready_id = unit_id(ready_value)
    check(ready_id is not None, f"4. CURRENT.md names a READY unit id (value {ready_value!r})")

    if ready_id:
        ready_doc = sorted(WORKUNITS.glob(f"{ready_id}_*.md"))
        check(
            bool(ready_doc),
            f"5. the READY unit's work-unit document exists ({ready_id} -> "
            f"{ready_doc[0].name if ready_doc else 'none found in workunits/'})",
        )
    else:
        check(False, "5. the READY unit's work-unit document exists (no READY unit id to look up)")

    completed_value = section_value(current_text, "## Last completed unit")
    completed_id = unit_id(completed_value)
    check(
        completed_id is not None and ready_id is not None and completed_id != ready_id,
        "6. CURRENT.md's READY unit and last-completed unit differ (a unit cannot be both)",
    )

    check(completed_id is not None, f"7. CURRENT.md names a last-completed unit id (value {completed_value!r})")

    if completed_id:
        handoff = handoff_path(completed_id)
        check(handoff.exists(), f"8. the last-completed unit's handoff exists ({handoff.name})")
    else:
        check(False, "8. the last-completed unit's handoff exists (no last-completed unit id)")

    gate_value = section_value(current_text, "## Gate") or ""
    check(
        ready_id is not None and ready_id.split(".")[0] in gate_value,
        f"9. the READY unit belongs to the gate CURRENT.md names "
        f"(ready {ready_id!r}, gate {gate_value!r})",
    )

    # ------------------------------------------------------- 2. queue.md agrees with CURRENT.md
    queue_text = read(QUEUE)
    queue_ready = QUEUE_READY_RE.findall(queue_text)
    check(
        len(queue_ready) == 1,
        f"10. docs/queue.md marks exactly one unit READY in the usability-closure section "
        f"(found {len(queue_ready)})",
    )
    check(
        len(queue_ready) == 1 and ready_id is not None and queue_ready[0] == ready_id,
        f"11. docs/queue.md's READY unit is CURRENT.md's READY unit "
        f"(queue {queue_ready[0] if queue_ready else 'none'}, CURRENT {ready_id or 'none'})",
    )

    # ------------------------------------------------------------------------- 3. routing
    for index, path in enumerate(ROUTED, start=12):
        rel = path.relative_to(ROOT).as_posix()
        check(
            CURRENT_POINTER in read(path),
            f"{index}. {rel} routes live programme status to {CURRENT_POINTER}",
        )

    # --------------------------------------------------- 4. AGENTS.md names the real surface
    agents = read(AGENTS)
    agents_norm = normalize(agents)

    check(
        "garden_store.py" in agents and re.search(r"garden_store\.py[^`]*\bbootstrap\b|\bbootstrap\b[^`]{0,40}garden_store\.py", agents_norm) is not None,
        "17. AGENTS.md names the store bootstrap/resume path (garden_store.py bootstrap)",
    )

    check(
        "read-only" in agents.lower() and "quotes.csv" in agents and "sources.csv" in agents,
        "18. AGENTS.md states the canonical CSVs' change discipline (read-only outside a named data unit)",
    )

    modules = sorted(p.name for p in SCRIPTS.glob("garden_*.py"))
    unnamed = [name for name in modules if name not in agents]
    check(
        not unnamed,
        "19. AGENTS.md names every corpus-program module in scripts/ "
        f"({'all ' + str(len(modules)) + ' named' if not unnamed else 'unnamed: ' + ', '.join(unnamed)})",
    )

    check(
        "run_negative_controls.py" in agents,
        "20. AGENTS.md names the negative-control harness (run_negative_controls.py)",
    )

    check(
        "usability-closure/workunits/" in agents,
        "21. AGENTS.md's resume path resolves the READY work-unit document "
        "(docs/program/usability-closure/workunits/)",
    )

    # --------------------------------------------------------- 5. no stale live-status claim
    for index, (claim_id, pattern, why) in enumerate(STALE_CLAIMS, start=22):
        offenders = []
        for path in SCANNED:
            if pattern.search(normalize(read(path))):
                offenders.append(path.relative_to(ROOT).as_posix())
        check(
            not offenders,
            f"{index}. no front door document makes the stale claim [{claim_id}] "
            f"({'clean' if not offenders else ', '.join(sorted(offenders)) + ' -> ' + why})",
        )

    # --------------------------------------------------------------------------- report
    registered = len(passed) + len(failures)
    if registered != EXPECTED_CHECKS:
        fail(
            f"count guard -- EXPECTED_CHECKS is {EXPECTED_CHECKS} but {registered} checks ran; "
            "re-derive EXPECTED_CHECKS (deleting a check must not read as PASS)"
        )

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failed of {registered} checks)")
        return 1
    print(f"RESULT: PASS ({registered} checks)")
    return 0


if __name__ == "__main__":
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    sys.exit(main())
