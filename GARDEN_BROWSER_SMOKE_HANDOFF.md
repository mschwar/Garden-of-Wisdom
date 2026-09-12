# Garden Quote-Browser Smoke Test Handoff — 2026-09-12

Unit: the open infra item "add an automated browser smoke test for the quote browser" (also the
`D8` debt recorded in `docs/program/W0_GATE_REPORT.md`), plus the phone-width overflow defect
filed by foreign QA on PR #9 — and the two further defects the new test then exposed.

Landed as PR [#14](https://github.com/mschwar/Garden-of-Wisdom/pull/14) (merge `d2eb203`, branch
`test/quote-browser-smoke`, merged by the operator while CI was green). Gate state at the time:
Gate A accepted 2026-09-12 (`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`); **W1.1 remains
unauthorized** and nothing in this unit touches the corpus program.

## What landed

| Artifact | Purpose |
|---|---|
| `scripts/smoke_quote_browser.py` | 22-check headless-Chromium smoke test of `browser/index.html`. Starts its own static server rooted at the repo root (or `--base-url` for a live server). |
| `.github/workflows/browser-smoke.yml` | Runs the smoke test on every PR and push to `main`, then the three existing validators. Independent of the Pages deploy; publishes nothing. |
| `requirements-dev.txt` | `playwright==1.55.0`, test-only. Every other script under `scripts/` stays stdlib-only and the app itself stays dependency-free. |
| `browser/style.css` | Phone-width overflow fixes (see below). |
| `browser/app.js` | Card view hides `#table-wrap` with the table. |
| Docs | `docs/RUNBOOK.md` §"Smoke-test the browser"; `docs/architecture/QUOTE_BROWSER.md` (§Automated smoke test, §Responsiveness); `docs/queue.md` close-outs; two `docs/DECISIONS.md` entries. |

## The three defects

Measured in Chromium; each was reproduced **before** it was fixed, and each is now covered by a
check that fails if the fix is reverted.

1. **Horizontal overflow at phone widths (known, PR #9).** The queue blamed
   `#controls select{min-width:140px}`. That was wrong: a `<select>` sizes itself to its longest
   `<option>`, and `#filter-source`'s longest `source_ref` is 61 characters, so the control laid
   out **390px** wide (Author: 276px) inside a 341px content box at a 375px viewport — a 421px
   document. Fixed by letting the row's labels shrink (`min-width: 0; max-width: 100%`) and
   capping the selects (`max-width: 100%`).
2. **Unbreakable tag list (new).** `.tags` renders a comma-joined list with no spaces
   (`love,neighbor,goldenrule`) — one ~280px token that escaped the card and overflowed the
   document at 320px even after fix 1. Fixed with `overflow-wrap: anywhere` and a wrapping
   `.meta-row`.
3. **Stray 2px bordered box (new).** Card view set `#quote-table` hidden but left `#table-wrap`
   (which owns the border and the scroll container) visible, so an empty 2px-tall bordered box
   sat at the end of the page on every load. Fixed in `render()`.

## Evidence

Local, on the merged commit:

```
$ python3 scripts/smoke_quote_browser.py                  -> RESULT: PASS (0 warnings), exit 0
$ python3 scripts/validate_quotes.py                      -> RESULT: PASS, exit 0
$ python3 scripts/check_program_contracts.py              -> RESULT: PASS, exit 0
$ python3 scripts/validate_homepage_preview_export.py     -> RESULT: PASS, exit 0
$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
```

Unchanged from `main` before the unit — no data, CSV, or export file was touched.

CI: [run 34713205864](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34713205864)
(`smoke`, pull_request) **success**; on `main` after the merge, run 34713239588 (`smoke`) and
34713239599 (Pages deploy) both **success**.

Live acceptance — the same test pointed at production, not just at a local server:

```
$ python3 scripts/smoke_quote_browser.py --base-url https://mschwar.github.io/Garden-of-Wisdom
...
PASS: GET /quotes.csv -> 200 (byte-identical)
PASS: header renders 324 total / 324 shown, matching quotes.csv
PASS: no horizontal overflow at 320px (cards view)
RESULT: PASS (0 warning(s))
```

i.e. the deployed page renders 324/324, serves both CSVs byte-identical to the repo, lays out at
phone widths, and produces no console/page/request errors.

## Negative controls (a test that cannot fail proves nothing)

Each mutation was applied to a throwaway copy of the repo under `/tmp` (never to the repo), then
the smoke test was re-run. All seven produced `RESULT: FAIL` with a `FAIL:` line and no traceback:

| Mutation | Observed |
|---|---|
| Revert the select/label CSS fix | `FAIL: cards view overflows horizontally at 320px: document scrollWidth=421 > clientWidth=320 widest overflowing element: {'right': 421, 'tag': 'LABEL'}` (plus 375px, both views) |
| Revert only the `.tags` wrap fix | `FAIL: cards view overflows horizontally at 320px: document scrollWidth=355 > clientWidth=320 widest overflowing element: {'right': 355, 'tag': 'SPAN.tags'}` |
| Remove the `#table-wrap` hide in `render()` | `FAIL: card view leaves an empty table container on the page (2px tall)` |
| Break the search filter (`filter(() => true)`) | `FAIL: search 'Dhammapada': page never showed 29 quotes within 15000ms (filtered-count='324')` |
| Repoint the data fetch to `quotes.csv` (the mis-rooted-site mistake) | `FAIL: page never rendered 324 quotes (filtered-count='17')` |
| Make the copy button copy the wrong text | `FAIL: copy button clipboard mismatch: got 'WRONG', expected 'A kindly tongue is the lodestone…'` |
| Log a console error on load | `FAIL: 1 console error(s): ['boom']` |

The first attempt at the search mutation exited with a bare traceback instead of a verdict; that
was a real robustness gap in the test and is fixed — every interaction failure is now reported as
one `FAIL:` line, and an unexpected exception is converted to `FAIL: unexpected error: …` so the
run always prints `RESULT:`.

## Out of scope, recorded not fixed

- **Filter coverage gap** — the test covers search, sort, view switch, copy and layout but not the
  six filter dropdowns or the "Issues only" toggle (the manual pass it replaced did check
  "Issues only"). Filed as
  [#13](https://github.com/mschwar/Garden-of-Wisdom/issues/13); queue entry added.
- **`AGENTS.md` was not updated.** Its "What commands to run" section would be the natural home
  for `scripts/smoke_quote_browser.py`, but the write is refused by tool policy (same deviation W0
  recorded). The command is documented in `README.md` and `docs/RUNBOOK.md` instead; a human who
  approves the write can add one line to `AGENTS.md`.

## Next authorized action

**Nothing in this lane.** The queue's remaining open infra items are the duplicate-review view
(conditional on the curation pass) and the Pages-root guard (documented, now also covered
locally by the smoke test's static-layout checks). The corpus-program next action is unchanged and
still gated on the operator: **W1.1 storage decision + minimal schema** — see
`docs/program/W1_DECOMPOSITION.md` §W1.1 and `docs/queue.md` §"Open — corpus program"; it is
decomposed but **not authorized**.
