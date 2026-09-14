# GARDEN_D3_HANDOFF.md

**Unit:** D3 — the `unverifiable` side-car ledger.
**Branch:** `d3/unverifiable-ledger` · **PR:** [#38](https://github.com/mschwar/Garden-of-Wisdom/pull/38) · **Merge:** (filled after merge).
**Date:** 2026-09-13.

## Summary

Decision D3 (2026-09-12) is executed: `unverifiable` is now represented in a **side-car ledger
keyed by legacy row id** — a `legacy_verification` table in the W1.1 store (one store, not two) —
so a record proven unverifiable is no longer indistinguishable from a never-checked row in the
3-valued `quotes.csv` enum. Issue #5 / Garden id 30 is the live instance, seeded into the
committed store mirror `data/store/garden.export.txt`.

The CSV is untouched. **No enum widening** (decision D3's rejection), **no second store** (the
ledger is a table in the existing store), **no export-header bump** (additive section to
`garden.export/1`; recorded ruling).

## What landed

- `scripts/garden_store.py` — migration `0002_unverifiable_ledger` adds `legacy_verification`
  (keyed by `legacy_row_id`; `research_state` pinned to `unverifiable`; `transition_id`
  ∈ T-R6/T-R7/T-R10/T-R11); `Store.mark_legacy_unverifiable` and
  `Store.reopen_legacy_unverifiable` (each writes its `research` audit row in the **same
  transaction** — never a ledger row without its audit row); `Store.unverifiable_ledger()`;
  the ledger is a `[legacy_verification]` export section in `EXPORT_SECTIONS`, `ROW_TABLES`,
  `counts()`, and the import loop.
- `scripts/garden_ledger.py` — the CLI (`mark` / `reopen` / `list`), `RESULT: PASS`/`FAIL`, no
  traceback on a refusal.
- `scripts/check_garden_ledger.py` — the acceptance + evidence run, **43 checks** (see verbatim
  output below).
- `scripts/check_garden_store.py` — exact-shape assertions updated to the two-migration schema
  (see rulings in `docs/DECISIONS.md`).
- `docs/program/D3_UNVERIFIABLE_LEDGER.md` — design doc.
- `docs/DECISIONS.md` / `docs/queue.md` / `docs/RUNBOOK.md` — close-out.
- `data/store/garden.export.txt` — the committed diffable store mirror seeding the live instance.
- This handoff.

**Rulings recorded** (`docs/DECISIONS.md`, "D3 executed (the `unverifiable` side-car ledger)"):
export header stays `/1` (additive section); `check_garden_store.py`'s exact-shape assertions were
necessarily updated; the store mirror is now populated (first real operator submission, per the
W1.3 ruling); `research_state` `from_state` is derived from `transition_id`.

## Evidence

### 1. The D3 acceptance suite — `scripts/check_garden_ledger.py` (43 checks)

Verbatim output (run 2026-09-13, `python3` Homebrew 3.14.5 and `/opt/homebrew/bin/python3.12` —
byte-identical `RESULT: PASS` under both):

```
PASS: create applies 0001 and 0002 in order (['0001_create_core', '0002_unverifiable_ledger'])
PASS: the schema has the legacy_verification table
PASS: the SQL layer rejects transition_id = 'T-R1'
PASS: the SQL layer rejects transition_id = 'T-R5'
PASS: the SQL layer rejects transition_id = 'T-R8'
PASS: the SQL layer rejects transition_id = 'T-C1'
PASS: the SQL layer rejects transition_id = 'garbage'
PASS: the SQL layer pins research_state to 'unverifiable'
PASS: UNVERIFIABLE_FROM_STATE names exactly the four terminating transitions
PASS: counts() exposes the legacy_verification table
PASS: a fresh store has an empty unverifiable ledger
PASS: mark records the live instance as unverifiable
PASS: the ledger holds exactly the live instance with its evidence
PASS: mark appends one research audit row (T-R6 from_state derived from the model)
PASS: mark changed the store (the ledger + audit row landed)
PASS: a duplicate mark is refused by the explicit re-adjudication guard
PASS: the refused re-mark wrote nothing at all
PASS: export starts with 'garden.export/1'
PASS: the export carries the ledger section with the live instance
PASS: the export meta schema_version is unchanged by the ledger section
PASS: the ledger round-trips (write -> wipe -> re-import byte-identical)
PASS: the import reports what it loaded (imported 2 record(s))
PASS: empty reason is refused with its own message (…must carry a reason…)
PASS: empty evidence_ref is refused with its own message (…evidence_ref is required…)
PASS: empty decided_by is refused with its own message (…decided_by must be non-empty…)
PASS: invalid transition is refused with its own message (…does not terminate in unverifiable…)
PASS: empty legacy row id is refused with its own message (…legacy_row_id must be non-empty…)
PASS: reopen on a missing row is refused with its own message (…not in the unverifiable ledger…)
PASS: reopen with empty reason is refused with its own message (…must carry a reason…)
PASS: all seven invalid writes were refused by their explicit guard (7/7)
PASS: every refused write left the store byte-identical
PASS: reopen records the T-R12 reversal
PASS: the live instance left the ledger after reopen
PASS: reopen appends the T-R12 audit row (unverifiable -> in_research)
PASS: reopen changed the store (audit row landed)
PASS: after reopen a legacy row may be marked again (T-R11 route recorded)
PASS: CLI mark returns RESULT: PASS
PASS: CLI list shows the live instance
PASS: CLI refuses a duplicate mark cleanly
PASS: CLI reopen returns RESULT: PASS
PASS: CLI list reports an empty ledger after reopen
PASS: quotes.csv and sources.csv are byte-identical before and after the run
PASS: the ledger wrote nothing outside the store directory

RESULT: PASS (the unverifiable side-car ledger works end to end)
```

### 2. No regression — all suites, both interpreters

```
                   3.14        3.12
check_garden_store:     59 PASS   59 PASS
check_garden_envelope: 102 PASS  102 PASS
check_garden_submit:   134 PASS  134 PASS
check_garden_normalize:232 PASS  232 PASS
check_garden_review:   246 PASS  246 PASS
check_garden_ledger:    43 PASS   43 PASS   (new)
check_garden_e2e:       96 PASS   96 PASS
```
plus the three CI validators (`validate_quotes.py`, `check_program_contracts.py`,
`validate_homepage_preview_export.py`) all `RESULT: PASS`. `quotes.csv` / `sources.csv`
byte-identical (`5675d7e6…` / `10b4c156…`).

### 3. Negative controls (7, all RED)

Each control mutates a guard's **distinctive message** in a throwaway `/tmp` copy of the repo
(never the real tree), runs the copy's `check_garden_ledger.py`, and requires `RESULT: FAIL` with
that guard's `FAIL:` line and **no traceback**. The mutations break the asserted needle *inside*
the message (so a second layer — the SQL `CHECK`/PK — cannot mask the guard). Observed first-`FAIL`
lines are copied verbatim from the harness run.

| id | mutation (in `/tmp` repo copy of `garden_store.py`) | observed first `FAIL:` line |
|----|------------------------------------------------------|-----------------------------|
| c1 | `does not terminate in unverifiable` → `does not Xterminate in unverifiable` | `FAIL: invalid transition was refused, but NOT by its explicit guard: transition_id 'T-R1' does not Xterminate in unverifiable (STATE_MODEL.md lists [...])` |
| c2 | `already in the unverifiable ledger; ` → `already in the Xunverifiable ledger; ` | `FAIL: a duplicate mark is refused by the explicit re-adjudication guard -- legacy row '30' is already in the Xunverifiable ledger; …` |
| c3 | `…must carry a reason` → `…must Xcarry a reason` | `FAIL: empty reason was refused, but NOT by its explicit guard: every unverifiable adjudication must Xcarry a reason` |
| c4 | `evidence_ref is required` → `evidence_ref Xis required` | `FAIL: empty evidence_ref was refused, but NOT by its explicit guard: evidence_ref Xis required (…)` |
| c5 | `not in the unverifiable ledger; nothing to reopen` → `not in the Xunverifiable ledger; …` | `FAIL: reopen on a missing row was refused, but NOT by its explicit guard: legacy row '404' is not in the Xunverifiable ledger; …` |
| c6 | `decided_by must be non-empty` → `decided_by Xmust be non-empty` | `FAIL: empty decided_by was refused, but NOT by its explicit guard: decided_by Xmust be non-empty` |
| c7 | import loop drops `legacy_verification` from its section list | `FAIL: unexpected StoreError: re-export after import is not byte-identical to the imported text (the export encoding lost or reordered data)` |

Every control: `returncode=1`, `traceback=False`, the aimed guard's `FAIL:` line first — except c7,
whose first `FAIL` is the store's byte-identity guard refusing the broken import (it proves the
ledger is load-bearing in the round-trip and surfaces as the round-trip guarantee firing, which is
the intended evidence).

Authoring note (no foreign reviewer in this session): the negative controls were written as a
**second, independent harness** (`/tmp/d3_negctrl.py`) after the suite, aimed at guard paths the
author's in-suite checks exercise. A foreign QA pass is still recommended before merge.

## Out of scope (recorded, not fixed)

- A full `candidates` research-case surface (`T-R*` transitions on store candidates) — W2 work.
- Browser display of the ledger — no browser change in this unit.
- Re-opening a legacy row into the candidate flow — the ledger records the terminal fact only.
- Widening `quotes.csv` `verification_status` — explicitly rejected by decision D3.
- `docs/architecture/QUOTE_BROWSER.md` was not changed (the browser does not consume the ledger).
- Wiring `scripts/check_garden_ledger.py` into the `browser-smoke.yml` CI step — a guarded workflow
  change; **filed as issue #39** (the step runs the six W1 suites but not the new ledger suite). The
  D3 suite already proves its negative controls, so the wiring cannot create a vacuously-green step.

## Exact next authorized action

`docs/queue.md` now leads with **D9 (H2B-B: open the `bahai-homepage` consume lane against the v1
export)** and **D4 (ONE batch capture record for the 324 legacy rows)**, both still authorized and
unstarted. The next non-gated unit per the standing skill note is the CI-coverage gap (wiring the
six/seven W1 suites into the `browser-smoke.yml` validator step, with one negative control per
suite) — re-confirm the open-issue set with `gh issue list --state open` before trusting any
breadcrumb. W2 remains unauthorized.
