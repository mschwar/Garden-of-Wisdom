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
"the tracker said it landed" was not evidence either. A documentation claim that no check can
falsify drifts exactly like this, and a cold-start agent reading only the front door then
cannot answer "where are we?" without archaeology.

What it asserts (27 checks)

  1. **One live status authority.** `docs/program/usability-closure/CURRENT.md` is the single
     place live programme status lives: its structural fields are present, it names exactly one
     READY unit, that unit's work-unit document and the last-completed unit's handoff both exist
     on disk, the READY unit belongs to the gate CURRENT names, and its own "What is usable now"
     section is not empty.
  2. **Agreement.** `docs/queue.md`'s usability-closure section marks the *same* single unit
     READY. The two are parsed by different code paths and compared, so neither is trusted.
  3. **Routing.** Every core front door names CURRENT.md -- compared on whitespace-free text, so
     a reflow that wraps the long path cannot fail the check.
  4. **A fail-closed stale-claim scan.** *Every* markdown file in the tree that is not on the
     exclusion list is scanned for three named shapes of stale live-status claim. The scan is
     not opt-in: a brand-new status document, a relative link to CURRENT.md, or a file that
     never names CURRENT.md at all is scanned by default, because the default is "scanned".
     The exclusion list is explicit, typed (prefix / exact / root-prefix), carries a reason per
     entry, and is itself checked for rotten (matching-nothing) entries.
  5. **`AGENTS.md` names its command surface** -- derived from the tree, never hard-coded: the
     store-lifecycle line must name the bootstrap *and* status *and* sync subcommands, every
     `scripts/garden_*.py` module present must be named (so a new module forces a front-door
     decision), the negative-control harness must be named, the CSV change discipline stated,
     and the resume path must resolve to the work-unit directory.

Two explicit allowances, because a statement *about* a claim is not the claim: a match is not
counted when it sits inside quotation marks (straight or curly double quotes, curly single
quotes -- see the note on apostrophes below), or when its own sentence carries a past-tense or
reporting cue from `PAST_OR_REPORT_CUES`. The cue list is deliberately **generous**: it is
cheaper to miss a stale claim than to fail an honest document, and every cue in it is a word a
*live assertion of current state* does not normally contain ("was", "previously", "earlier",
"before", "no longer", "said", "claimed", "asserted", "corrected", "removed", "retired", ...).
That is how the charter's Gate U0 criterion, a "## History" section, a provenance annotation, a
changelog bullet and a dated historical statement are all permitted, while a bare assertion of
the same words is not.

**What this check cannot do, stated plainly:** it is a pattern matcher, not a claim classifier.
A stale status claim phrased with a synonym the three shapes do not enumerate ("W1 has yet to
land", "the W1 store remains unimplemented", "W1-in-progress") is NOT caught; renaming or
hyphenating the subject is enough to evade a shape. The scan's value is regression protection
for the drift shapes this repo has actually produced (they are in U0.2's contradiction table and
pinned as controls `fd1`-`fd10`) plus the structural facts -- one READY unit, routing, the
queue agreement, `AGENTS.md`'s command surface -- which ARE decidable. Do not read "23 of 27
checks pass" as "no document can misstate status".

Apostrophes are deliberately NOT treated as quotation marks: `don't` and `W1's` would open a
span that could swallow a genuine claim, so supporting straight single quotes would cost more
than it buys.

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

# Markdown deliberately outside the scan, with a reason each. Typed so a substring cannot
# silently exempt a whole family of paths: "prefix" (a directory), "exact" (one file),
# "root-prefix" (a prefix at the repository root only -- e.g. the GARDEN_*_HANDOFF.md evidence
# files, which live at the root, not every path that merely contains "GARDEN_").
EXCLUSIONS: tuple[tuple[str, str, str], ...] = (
    ("prefix", "docs/audit/", "dated evidence snapshots and gate reviews -- point-in-time"),
    ("exact", "docs/DECISIONS.md", "append-only log; must be free to quote a superseded claim"),
    ("exact", "docs/data/DATA_QUALITY_REPORT.md", "frozen data-quality transcript, verbatim"),
    ("prefix", "docs/program/W1_", "W1 wave doctrine and the Gate B packet -- historical evidence"),
    ("exact", "docs/program/W0_GATE_REPORT.md", "the Gate A packet -- historical evidence"),
    ("prefix", "docs/program/usability-closure/workunits/",
     "work-unit specs quote the false claims as acceptance criteria"),
    ("prefix", "bootstrap/", "seed packets -- planning input, not authority"),
    ("prefix", "exports/", "generated export artifacts"),
    ("root-prefix", "GARDEN_", "root unit handoffs -- evidence, and they quote the claims they fixed"),
)

# (id, compiled pattern over whitespace-normalized text, why it is a stale live-status claim)
STALE_CLAIMS = (
    (
        "w1-runtime-or-store-absent",
        re.compile(
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

# Allowance 1: the match is a quotation -- span-checked over the WHOLE text, because a sentence
# boundary can fall inside a quotation and a sentence-scoped scan would then never see a closed
# quote pair (that bug made the allowance pass only by accident on the sample that had a cue).
# Allowance 2: its sentence marks it as past/reported. Both are documented, and deliberately
# generous in the direction that avoids rejecting legitimate documentation.
QUOTE_SPANS_RE = re.compile(
    r'"[^"\n]*"'                    # straight double
    r"|\u201c[^\u201d\n]*\u201d"    # curly double
    r"|\u2018[^\u2019\n]*\u2019"    # curly single (rare as an apostrophe, unlike ' )
)

# Past-tense / reporting cues: a live assertion of *current* status does not normally carry one.
# Single words are matched on word boundaries so "was" cannot match inside "waste".
PAST_OR_REPORT_CUES = (
    "was", "were", "had", "did", "didn't", "been", "would",
    "previously", "earlier", "before", "prior", "until", "formerly", "historically",
    "no longer", "used to", "at the time", "at that stage", "at that point", "at a time",
    "said", "says", "wrote", "written", "claimed", "claim", "asserted", "asserts", "assert",
    "reported", "recorded", "noted", "described", "corrected", "removed", "replaced",
    "retired", "superseded", "obsolete", "deprecated", "old", "previous",
)

_WORD_CUES = tuple(cue for cue in PAST_OR_REPORT_CUES if " " not in cue)
_PHRASE_CUES = tuple(cue for cue in PAST_OR_REPORT_CUES if " " in cue)
CUE_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(cue) for cue in _WORD_CUES) + r")\b"
    r"|" + "|".join(re.escape(cue) for cue in _PHRASE_CUES),
    re.I,
)

REQUIRED_CURRENT_HEADINGS = ("## Gate", "## Current READY unit", "## Last completed unit", "## Update rule")

UNIT_ID_RE = re.compile(r"(U\d+\.\d+)\b")
QUEUE_READY_RE = re.compile(r"^\s*-\s*\[[ x]\]\s*(U\d+\.\d+)\b[^\n]*—\s*READY\s*$", re.M)

WALK_SKIP = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache"}
EXPECTED_CHECKS = 27

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


def ws_free(text: str) -> str:
    """Drop all whitespace: a reflow may wrap a long path, which is not a content change."""
    return re.sub(r"\s+", "", text)


def excluded(relative: str) -> bool:
    """True when a path is deliberately outside the scan (single source: EXCLUSIONS)."""
    return any(exclusion_matches(kind, value, relative) for kind, value, _reason in EXCLUSIONS)


def exclusion_matches(kind: str, value: str, relative: str) -> bool:
    if kind == "prefix":
        return relative.startswith(value)
    if kind == "exact":
        return relative == value
    if kind == "root-prefix":
        return "/" not in relative and relative.startswith(value)
    raise AssertionError(f"unknown exclusion kind {kind!r}")


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


def allowance(text: str, start: int, end: int, spans: list[tuple[int, int]]) -> str | None:
    """'quoted' / 'cue <word>' when a stale-claim match is being discussed, not asserted."""
    for span_start, span_end in spans:
        if span_start < end and span_end > start:
            return "quoted"
    left = text.rfind(".", 0, start) + 1
    right = text.find(".", end)
    sentence = text[left:right if right != -1 else len(text)]
    cue = CUE_RE.search(sentence)
    return f"cue {cue.group(0)!r}" if cue else None


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
    pointer_ws_free = ws_free(CURRENT_POINTER)
    for index, path in enumerate(CORE_FRONT_DOORS, start=12):
        check(
            pointer_ws_free in ws_free(read(path)),
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

    tree = markdown_files()
    scanned = [path for path in tree if not excluded(rel(path))]

    # ------------------------------------------------- 5. the exclusion list is not rotten
    rotten = [
        value for kind, value, _reason in EXCLUSIONS
        if not any(exclusion_matches(kind, value, rel(path)) for path in tree)
    ]
    check(
        not rotten,
        f"19. every exclusion still matches at least one document "
        f"({'all ' + str(len(EXCLUSIONS)) + ' live; ' + str(len(scanned)) + ' of ' + str(len(tree)) + ' documents scanned' if not rotten else 'matches nothing: ' + ', '.join(rotten)})",
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
        "20. AGENTS.md's command surface carries the whole store lifecycle on one line "
        f"(garden_store.py + bootstrap + status + sync; found {len(lifecycle)})",
    )

    check(
        "read-only" in agents.lower() and "quotes.csv" in agents and "sources.csv" in agents,
        "21. AGENTS.md states the canonical CSVs' change discipline (read-only outside a named data unit)",
    )

    modules = sorted(p.name for p in SCRIPTS.glob("garden_*.py"))
    unnamed = [name for name in modules if name not in agents]
    check(
        not unnamed,
        "22. AGENTS.md names every corpus-program module in scripts/ "
        f"({'all ' + str(len(modules)) + ' named' if not unnamed else 'unnamed: ' + ', '.join(unnamed)})",
    )

    check(
        "run_negative_controls.py" in agents,
        "23. AGENTS.md names the negative-control harness (run_negative_controls.py)",
    )

    check(
        "usability-closure/workunits/" in agents,
        "24. AGENTS.md's resume path resolves the READY work-unit document "
        "(docs/program/usability-closure/workunits/)",
    )

    # --------------------------------------------------------- 7. no stale live-status claim
    for index, (claim_id, pattern, why) in enumerate(STALE_CLAIMS, start=25):
        offenders = []
        for path in scanned:
            text = normalize(read(path))
            spans = [(match.start(), match.end()) for match in QUOTE_SPANS_RE.finditer(text)]
            if any(
                allowance(text, match.start(), match.end(), spans) is None
                for match in pattern.finditer(text)
            ):
                offenders.append(rel(path))
        check(
            not offenders,
            f"{index}. no scanned document makes the stale claim [{claim_id}] "
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
