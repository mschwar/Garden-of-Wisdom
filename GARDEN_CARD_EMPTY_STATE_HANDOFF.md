# Garden Card-View Empty-State Handoff — 2026-09-12

Unit: the open infra item filed as
[#17](https://github.com/mschwar/Garden-of-Wisdom/issues/17) — card view must render an empty
state when the filtered result set is empty. Filed as out-of-scope by the filter-coverage unit
([#13](https://github.com/mschwar/Garden-of-Wisdom/issues/13), PR
[#18](https://github.com/mschwar/Garden-of-Wisdom/pull/18), merged as `745c1dc`) because it is a
browser **behaviour** change rather than a test-only edit.

**No data changed.** `quotes.csv` and `sources.csv` are byte-identical to `main` (hashes below).

Branch `fix/card-view-empty-state`, authored in the worktree `~/gow-worktrees/card-empty-state`
(the primary checkout was never switched off `main`).

## The defect

Measured 2026-09-12 in headless Chromium at 1280px, with a search matching nothing: card view
rendered an empty `#results` (`children=0`, `text=''`, zero `.empty-state` elements) — a blank
area under a header reading "0 shown" — while table view rendered a `td.empty-state` row saying
"No matching quotes. Adjust the filters or search." Two views disagreed about whether an empty
result is worth explaining.

## What landed

| Artifact | Change |
|---|---|
| `browser/app.js` | New module-level `EMPTY_STATE_MESSAGE` constant — **one** source of truth for the message. `renderTableRows()` now uses it, and `render()`'s card branch renders `<p class="empty-state">` with it when the filtered set is empty. |
| `browser/style.css` | The existing table rule became a shared `#quote-table .empty-state, #results .empty-state` rule (same declarations: centred, muted, italic, 24px padding), plus `#results .empty-state { grid-column: 1 / -1 }` so the message spans the card grid instead of sitting in one 280px column. |
| `scripts/smoke_quote_browser.py` | `check_empty_state` now also switches to card view and asserts a `#results .empty-state` element exists **and** that its text equals the table view's text exactly (the two views are compared with each other, not each against a copy of the string). 32 → **33** checks. |
| `docs/architecture/QUOTE_BROWSER.md` | §Features implemented: new "Empty state in both views" bullet. §Automated smoke test: empty-result bullet rewritten, 33-check count, negative-control narrative 14 → 16. |
| `docs/RUNBOOK.md` | §Smoke-test the browser: assertion list and 33-check count updated (14 → 16 negative controls). |
| `docs/queue.md`, `docs/DECISIONS.md` | **Deliberately not touched by this unit** — the parent owns both ledgers. The exact proposed text (queue close-out + decision entry) is reported to the operator instead. |
| `AGENTS.md` | Still not updated; the write is refused by tool policy, the same recorded deviation as the W0, browser-smoke, and filter-coverage units. |

Markup note: the card-view element is a `<p class="empty-state">`, matching the table's
`td.empty-state` conventions (same class name, same shared CSS declarations) without inventing a
second visual language.

## Verification (verbatim)

```
$ /Users/mschwar/Developer/Garden-of-Wisdom/.venv/bin/python scripts/smoke_quote_browser.py
quotes.csv parses to 324 rows (app.js rule)
serving /Users/mschwar/gow-worktrees/card-empty-state on http://127.0.0.1:51676
PASS: GET /browser/index.html -> 200
...
PASS: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada') renders the table's empty-state row 'No matching quotes. Adjust the filters or search.'
PASS: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada') renders the same empty state in card view 'No matching quotes. Adjust the filters or search.'
...
PASS: no horizontal overflow at 768px (table view)

RESULT: PASS (0 warning(s))          # 33 PASS lines, exit 0

$ python3 scripts/validate_quotes.py                     -> RESULT: PASS (exit 0)
$ python3 scripts/check_program_contracts.py             -> RESULT: PASS (exit 0)
$ python3 scripts/validate_homepage_preview_export.py    -> RESULT: PASS (exit 0)

$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
```

Both hashes equal the values `main` carried before this unit (and the values recorded in
`GARDEN_FILTER_SMOKE_COVERAGE_HANDOFF.md`), i.e. no data, CSV, or export byte moved.

### The two changed PASS lines

```
PASS: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada') renders the table's empty-state row 'No matching quotes. Adjust the filters or search.'
PASS: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada') renders the same empty state in card view 'No matching quotes. Adjust the filters or search.'
```

(The second line is the new check; the first line's wording changed from "renders the empty-state
row" to "renders the table's empty-state row" so the two views are named unambiguously.)

### 320px presentation check (ad-hoc, not part of the committed test)

The committed overflow check sweeps the *populated* page, so it does not by itself exercise the
new element. Measured separately in the same headless Chromium, forcing the no-match combination
in card view:

```
320px:  P.empty-state @x=16 w=288  text='No matching quotes. Adjust the filters or search.' cards=0 docScroll=320  docClient=320  overflow=no
375px:  P.empty-state @x=16 w=343  text='No matching quotes. Adjust the filters or search.' cards=0 docScroll=375  docClient=375  overflow=no
1280px: P.empty-state @x=16 w=1248 text='No matching quotes. Adjust the filters or search.' cards=0 docScroll=1280 docClient=1280 overflow=no
```

The message spans the full content width at every width and adds no horizontal overflow at 320px.

## Negative controls (a check that cannot fail proves nothing)

Each mutation was applied to a throwaway copy of this worktree under `/tmp`
(`/tmp/nc-card-a`, `/tmp/nc-card-b` — never the real tree), after which the smoke test was re-run
against that copy. Both produced `RESULT: FAIL`, exit 1, with one targeted `FAIL:` line, 32 PASS
lines, and **no traceback**.

| # | Mutation in `browser/app.js` | Observed |
|---|---|---|
| 1 | card view stops rendering the empty state (the new `if (rows.length === 0)` guard → `if (false)`, control A) | `FAIL: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada'): card view rendered 0 empty-state elements, expected 1 (issue #17: card view must not leave the result area blank)` then `RESULT: FAIL (1 check(s) failed)` |
| 2 | card and table messages edited apart (card branch's `EMPTY_STATE_MESSAGE` reference → a divergent literal `"No matching quotes. Adjust the filters."`, control B) | `FAIL: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada'): card view says 'No matching quotes. Adjust the filters.', table view says 'No matching quotes. Adjust the filters or search.' — the two views share one message and must not drift` then `RESULT: FAIL (1 check(s) failed)` |

Control 2 is the one that justifies comparing the two views against each other: with each view
checked against its own copy of the string, this drift would pass.

## Out of scope, recorded not fixed

- **The committed overflow check does not cover an empty result.** `check_viewport_overflow` runs
  against the unfiltered page, so the width sweep never sees the empty state in either view. The
  fact was recorded here (and measured ad hoc) rather than folded into this unit, because
  widening the width sweep is a separate coverage decision and would change the check count the
  docs pin.
- **`EMPTY_STATE_TEXT` in the smoke test is still a substring anchor.** The test asserts the table
  text *contains* `"No matching quotes."` and then that the card text equals the table text. The
  full message therefore appears in the docs and in the run output (and in the `!r` FAIL lines),
  not as an exact-equality constant in the test — deliberate, so a cosmetic rewording of the
  message does not silently break the suite, while a *one-sided* change still fails.
- **`AGENTS.md`** (see the table above): refused by tool policy; a human who approves the write
  can add the smoke-test command to its "What commands to run" section.
- **#19 (deprecated Node 20 action majors)** is untouched and unrelated — still its own unit.

## Next authorized action

Issue #17 is closed by this branch pending review. Nothing else in the browser lane is open. The
corpus-program next action is unchanged and still gated on the operator: **W1.1 storage decision +
minimal schema** — see `docs/program/W1_DECOMPOSITION.md` §W1.1 and `docs/queue.md` §"Open —
corpus program"; it is decomposed but **not authorized**.
