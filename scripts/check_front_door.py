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

What it asserts (29 checks)

  1. **One live status authority.** `docs/program/usability-closure/CURRENT.md` is the single
     place live programme status lives: its structural fields are present, it names exactly one
     READY unit, that unit's work-unit document and the last-completed unit's handoff both
     exist on disk, the READY unit belongs to the gate CURRENT names, and its own
     "What is usable now" section is not empty.
  2. **Agreement.** `docs/queue.md`'s usability-closure section marks the *same* single unit
     READY. The two are parsed by different code paths and compared, so neither is trusted.
  3. **Routing.** Every core front door names CURRENT.md, so a cold-start agent is sent to one
     place instead of restating status.
  4. **A fail-closed guarded set.** `GUARDED` is an explicit list, and a **derived coverage
     check** fails if any non-excluded markdown file in the tree names CURRENT.md but is not in
     it -- so a new front-door document cannot silently acquire status-bearing prose outside the
     scan. The exclusion list is itself checked for rotten (matching-nothing) entries.
  5. **No stale live-status claim** in any guarded document, over three named shapes: the
     W1 runtime/store described as absent, W1 described as in progress / underway / not yet
     landed, and the W1 runtime/store described as not existing.
  6. **`AGENTS.md` names its command surface** -- derived from the tree, never hard-coded: the
     store-lifecycle line must name the bootstrap *and* status *and* sync subcommands, every
     `scripts/garden_*.py` module present must be named (so a new module forces a front-door
     decision), the negative-control harness must be named, the CSV change discipline stated,
     and the resume path must resolve to the work-unit directory.

Historical documents are NOT scanned, and every exclusion carries its reason: the dated
`docs/audit/*` snapshots and gate reviews, the W0/W1 packets, `docs/DECISIONS.md` (an
append-only log that must be free to quote a superseded claim), the frozen
`docs/data/DATA_QUALITY_REPORT.md` transcript, the root `GARDEN_*_HANDOFF.md` evidence files,
the work-unit specs (which quote the false claims as acceptance criteria), and the
seed/export trees. A check that forbade "W1 in progress" inside a historical packet would
destroy evidence.

Exits 0 with `RESULT: PASS`, non-zero with `RESULT: FAIL` and one `FAIL:` line per broken
check -- never a traceback.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CURRENT = ROOT / "docs" / "program" / "usability-closure" / "CURRENT.md"
WORKUNITS = ROOT / "docs" / "program" / "usability-closure" / "workunits"
SCRIPTS = ROOT / "scripts"

CURRENT_POINTER = "docs/program/usability-closure/CURRENT.md"

# The documents a cold-start agent must be routed *by*: every one names CURRENT.md.
CORE_FRONT_DOORS = (
    ROOT / "AGENTS.md",
    ROOT / "README.md",
    ROOT / "docs" / "RUNBOOK.md",
    ROOT / "docs" / "product" / "PRODUCT_DOCTRINE.md",
    ROOT / "docs" / "program" / "README.md",
    ROOT / "docs" / "queue.md",
)

# The documents whose status prose is guarded (the stale-claim scan). CURRENT.md is in here on
# purpose: the authority's own body must not be able to assert the opposite of its own fields.
GUARDED = CORE_FRONT_DOORS + (
    CURRENT,
    ROOT / "docs" / "program" / "usability-closure" / "PROGRAM_CHARTER.md",
    ROOT / "docs" / "program" / "usability-closure" / "EXECUTION_MAP.md",
    ROOT / "docs" / "program" / "usability-closure" / "OPERATOR_RUNBOOK.md",
    ROOT / "docs" / "program" / "usability-closure" / "RESUME.md",
    ROOT / "docs" / "program" / "usability-closure" / "SYNTHESIS_GATES.md",
    ROOT / "docs" / "program" / "usability-closure" / "QUEUE_PATCH.md",
)

# Markdown that is deliberately outside the guard, with the reason. Each entry must match at
# least one file in the tree, or the coverage check reports it as a rotten exclusion (an
# exclusion that matches nothing hides nothing and defeats the coverage check's purpose).
EXCLUSIONS: tuple[tuple[str, str], ...] = (
    ("docs/audit/", "dated evidence snapshots and gate reviews -- point-in-time, never a claim"),
    ("docs/DECISIONS.md", "append-only log; must be free to quote a superseded claim"),
    ("docs/data/DATA_QUALITY_REPORT.md", "frozen data-quality transcript, verbatim by contract"),
    ("docs/program/W1_", "W1 wave doctrine and the Gate B packet -- historical evidence"),
    ("docs/program/W0_GATE_REPORT.md", "the Gate A packet -- historical evidence"),
    ("docs/program/usability-closure/workunits/",
     "work-unit specs quote the false claims as acceptance criteria"),
    ("bootstrap/", "seed packets -- planning input, not authority"),
    ("exports/", "generated export artifacts"),
    ("GARDEN_", "root unit handoffs -- evidence, and they quote the claims they fixed"),
)

# (id, compiled pattern over whitespace-normalized text, why it is a stale live-status claim)
STALE_CLAIMS = (
    (
        "w1-runtime-or-store-absent",
        re.compile(
            # `no longer claim X does not exist` is a *meta*-claim (the charter's own Gate U0
            # acceptance criterion), not the claim, so a "no longer" negation is allowed through.
            r"\bno(?! longer)\b[^.]{0,90}\b(w1 runtime|w1 store|corpus[- ]program (runtime|store|datastore))\b"
            r"[^.]{0,60}\bexists?\b",
            re.I,
        ),
        "describes the W1 runtime/store as absent",
    ),
    (
        "w1-in-progress",
        re.compile(
            r"\bw1\b[^.]{0,90}\b(in progress|underway|not yet landed|has not landed|"
            r"hasn't landed|not landed)\b",
            re.I,
        ),
        "describes W1 as in progress / underway / not yet landed",
    ),
    (
        "w1-runtime-or-store-not-landed",
        re.compile(
            r"\b(w1 runtime|w1 store|corpus[- ]program (runtime|store|datastore))\b[^.]{0,40}"
            r"\b(does not|doesn't|has not|hasn't|did not|never)\b[^.]{0,25}\b(exist|land|ship)",
            re.I,
        ),
        "describes the W1 runtime/store as never having existed",
    ),
)

# A statement *about* a claim is not the claim: "no longer claims the W1 runtime does not
# exist" is the programme charter's own Gate U0 acceptance criterion, and "the README says no
# W1 store exists" is a report about the README. Any match whose immediately preceding text
# ends in a claim/assert/report verb (optionally with an article) is treated as a meta-claim
# and not counted. Fixed-width lookbehinds cannot express this ("claims the " is 11 characters,
# "claim " is 6), so the guard is applied over the match's preceding window instead.
META_CLAIM_RE = re.compile(
    r"\b(claim|claims|claimed|claiming|assert|asserts|asserted|asserting|"
    r"say|says|said|saying|state|states|stated|stating|"
    r"describe|describes|described|describing|report|reports|reported|reporting)\b"
    r"(\s+the|\s+that|\s+any|\s+a)?[^.]{0,12}$",
    re.I,
)
META_CLAIM_WINDOW = 46

REQUIRED_CURRENT_HEADINGS = ("## Gate", "## Current READY unit", "## Last completed unit", "## Update rule")

UNIT_ID_RE = re.compile(r"(U\d+\.\d+)\b")
QUEUE_READY_RE = re.compile(r"^\s*-\s*\[[ x]\]\s*(U\d+\.\d+)\b[^\n]*—\s*READY\s*$", re.M)

WALK_SKIP = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache"}
EXPECTED_CHECKS = 29

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


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalize(text: str) -> str:
    """Collapse all whitespace runs to single spaces, so a pattern matches across line wraps."""
    return re.sub(r"\s+", " ", text)


def excluded(relative: str) -> bool:
    """True when a path is deliberately outside the guard (single source: EXCLUSIONS)."""
    return any(
        pattern in relative or relative.startswith(pattern.rstrip("/"))
        for pattern, _reason in EXCLUSIONS
    )


def section_lines(text: str, heading: str) -> list[str]:
    """The body lines of a `## heading` section, up to the next heading."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == heading:
            body: list[str] = []
            for candidate in lines[index + 1:]:
                if candidate.lstrip().startswith("#"):
                    break
                body.append(candidate)
            return body
    return []


def section_value(text: str, heading: str) -> str | None:
    """The first non-empty body line of a `## heading` section."""
    for body in section_lines(text, heading):
        if body.strip():
            return body.strip()
    return None


def unit_id(value: str | None) -> str | None:
    if not value:
        return None
    match = UNIT_ID_RE.search(value)
    return match.group(1) if match else None


def handoff_path(unit: str) -> Path:
    return ROOT / f"GARDEN_{unit.replace('.', '_')}_HANDOFF.md"


def is_meta_claim(normalized_text: str, start: int) -> bool:
    """True when a stale-claim match is preceded by a claim/assert/report verb (a meta-claim)."""
    window = normalized_text[max(0, start - META_CLAIM_WINDOW):start]
    return bool(META_CLAIM_RE.search(window))


def markdown_files() -> list[Path]:
    found: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in WALK_SKIP for part in path.parts):
            continue
        found.append(path)
    return sorted(found, key=rel)


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
    queue_text = read(ROOT / "docs" / "queue.md")
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
    for index, path in enumerate(CORE_FRONT_DOORS, start=12):
        check(
            CURRENT_POINTER in read(path),
            f"{index}. {rel(path)} routes live programme status to {CURRENT_POINTER}",
        )

    # ------------------------------------- 4. the authority's own body is not vacuously empty
    usable = [
        line for line in section_lines(current_text, "## What is usable now")
        if line.strip().startswith("-")
    ]
    check(
        bool(usable),
        f"18. CURRENT.md's 'What is usable now' section lists at least one item "
        f"(found {len(usable)})",
    )

    # ------------------------------------------------ 5. the guarded set is closed and honest
    guarded_rels = [rel(path) for path in GUARDED]
    absent = [name for path, name in zip(GUARDED, guarded_rels) if not path.exists()]
    check(
        not absent,
        f"19. every guarded document exists "
        f"({'all ' + str(len(GUARDED)) + ' present' if not absent else 'missing: ' + ', '.join(absent)})",
    )

    tree = markdown_files()
    unguarded = [
        rel(path) for path in tree
        if not excluded(rel(path))
        and rel(path) not in guarded_rels
        and CURRENT_POINTER in read(path)
    ]
    check(
        not unguarded,
        "20. fail-closed coverage: no document outside the guarded set names "
        f"{CURRENT_POINTER} "
        f"({'closed' if not unguarded else 'add to GUARDED or to EXCLUSIONS: ' + ', '.join(unguarded)})",
    )

    rotten = [
        pattern for pattern, _reason in EXCLUSIONS
        if not any(pattern in rel(path) for path in tree)
    ]
    check(
        not rotten,
        f"21. every exclusion still matches at least one document "
        f"({'all ' + str(len(EXCLUSIONS)) + ' live' if not rotten else 'matches nothing: ' + ', '.join(rotten)})",
    )

    # --------------------------------------------------- 6. AGENTS.md names the real surface
    agents = read(ROOT / "AGENTS.md")

    lifecycle = [
        line for line in agents.splitlines()
        if "garden_store.py" in line
        and all(token in line for token in ("bootstrap", "status", "sync"))
    ]
    check(
        bool(lifecycle),
        "22. AGENTS.md's command surface carries the whole store lifecycle on one line "
        f"(garden_store.py + bootstrap + status + sync; found {len(lifecycle)})",
    )

    check(
        "read-only" in agents.lower() and "quotes.csv" in agents and "sources.csv" in agents,
        "23. AGENTS.md states the canonical CSVs' change discipline (read-only outside a named data unit)",
    )

    modules = sorted(p.name for p in SCRIPTS.glob("garden_*.py"))
    unnamed = [name for name in modules if name not in agents]
    check(
        not unnamed,
        "24. AGENTS.md names every corpus-program module in scripts/ "
        f"({'all ' + str(len(modules)) + ' named' if not unnamed else 'unnamed: ' + ', '.join(unnamed)})",
    )

    check(
        "run_negative_controls.py" in agents,
        "25. AGENTS.md names the negative-control harness (run_negative_controls.py)",
    )

    check(
        "usability-closure/workunits/" in agents,
        "26. AGENTS.md's resume path resolves the READY work-unit document "
        "(docs/program/usability-closure/workunits/)",
    )

    # --------------------------------------------------------- 7. no stale live-status claim
    for index, (claim_id, pattern, why) in enumerate(STALE_CLAIMS, start=27):
        offenders = []
        for path in GUARDED:
            text = normalize(read(path))
            if any(not is_meta_claim(text, match.start()) for match in pattern.finditer(text)):
                offenders.append(rel(path))
        check(
            not offenders,
            f"{index}. no guarded document makes the stale claim [{claim_id}] "
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
