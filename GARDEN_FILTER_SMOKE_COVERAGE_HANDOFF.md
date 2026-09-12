# Garden Filter-Coverage Handoff — 2026-09-12

Unit: the open infra item filed as
[#13](https://github.com/mschwar/Garden-of-Wisdom/issues/13) — extend
`scripts/smoke_quote_browser.py` to the six filter dropdowns, the "Issues only" toggle, a
combined interaction, and the empty-result state. **Test coverage only: no browser behaviour
changed, no data changed.**

Landed as PR [#18](https://github.com/mschwar/Garden-of-Wisdom/pull/18), merged into `main` as
`745c1dc` with the branch deleted (CI + live acceptance in the block below).
Gate state unchanged: Gate A accepted 2026-09-12 (`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`);
**W1.1 remains unauthorized** and nothing in this unit touches the corpus program.

## What landed

| Artifact | Change |
|---|---|
| `scripts/smoke_quote_browser.py` | 22 → **32** checks: filter option sets, one narrowing value per dropdown, "Issues only", one filter+search+sort combination, the empty-result state — plus vacuity guards on all of them. |
| `docs/architecture/QUOTE_BROWSER.md` | §Automated smoke test rewritten: new coverage, 32-check count, the "refuses to pass vacuously" rule, 14 negative controls. |
| `docs/RUNBOOK.md` | §Smoke-test the browser: assertion list extended, 32-check count, vacuity rule. |
| `docs/queue.md` | #13 closed (new "Closed — 2026-09-12 browser smoke test: filter coverage" section); the older 22-check close-out annotated as "22 at the time"; new open infra item for the card-view empty state. |
| `docs/DECISIONS.md` | New entry: filter coverage searches the data for narrowing cases instead of hard-coding a value; card-view empty state is out of scope for a test-only unit. |
| [#17](https://github.com/mschwar/Garden-of-Wisdom/issues/17) | Filed: card view has no empty state (see "Out of scope" below). |

## The ten new checks

All expectations are recomputed from `quotes.csv` with the same predicates `browser/app.js`
uses (`matchesSearch`, `detectIssues`, exact column equality, tag membership). Nothing is
hard-coded; the values below are simply the ones the data offered on 2026-09-12.

| Check | What it asserts | Run on this data |
|---|---|---|
| dropdown option sets | each of the six dropdowns offers exactly the CSV's distinct values, with `All` first | 27 traditions, 60 authors, 291 sources, 401 tags, 3 item types, 2 verification values |
| `#filter-tradition` | rendered card count == Python count | `Akan (Ghana)` → 1 |
| `#filter-author` | same | `Akan Proverb` → 1 |
| `#filter-source` | same | `1 Corinthians 13:13` → 1 |
| `#filter-tag` | tag **membership** (not substring) | `acceptance` → 2 |
| `#filter-item-type` | same | `excerpt` → 270 |
| `#filter-verification` | same | `unverified` → 320 |
| `#filter-issues-only` | narrows to exactly the rows with non-empty `detectIssues()`, every rendered card carries an issue badge, and the toggle is asserted to **drop** rows | 320 cards shown, 4 dropped |
| combined | one dropdown value + one search term + sort direction, in table view: row count **and** `td-len` descending order | `Baha'i` + `god` + Length desc → 8 rows |
| empty result | a no-match combination renders `td.empty-state` containing "No matching quotes." and zero cards | `Akan (Ghana)` + `Dhammapada` |

### Vacuity guards

The unit that added the test was fixed once for an unguarded `SEARCH_TERM` (foreign-QA finding 3
in `GARDEN_BROWSER_SMOKE_HANDOFF.md`), so the same class of hole is closed here up front: every
filter value, the toggle, and every combination the test uses is **searched for in the data**
(0 < count < total, or count == 0 for the empty case), and a check that can no longer
distinguish working behaviour from broken behaviour fails with an explicit
`… would be vacuous …` line instead of passing.

## Evidence

Local, on the branch (`python3` = the repo's `.venv/bin/python`, Playwright 1.55 + Chromium):

```
$ .venv/bin/python scripts/smoke_quote_browser.py
... 32 PASS lines ...
RESULT: PASS (0 warning(s))                      # exit 0

$ python3 scripts/validate_quotes.py             -> RESULT: PASS
$ python3 scripts/check_program_contracts.py     -> RESULT: PASS
$ python3 scripts/validate_homepage_preview_export.py -> RESULT: PASS

$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
```

Both CSV hashes are **identical to `main` before this unit** — no data, CSV, or export file was
touched, which is the whole point of a test-only unit.

A sample of the new output:

```
PASS: all 6 filter dropdowns offer exactly the quotes.csv values plus an 'All' first option
PASS: #filter-tag = 'acceptance' narrows to 2 cards, matching quotes.csv
PASS: 'Issues only' narrows to 320 cards (dropping 4), every one badged
PASS: combined #filter-tradition = "Baha'i" + search 'god' + Length desc renders 8 rows in order, matching quotes.csv
PASS: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada') renders the empty-state row 'No matching quotes. Adjust the filters or search.'
```

## Negative controls (a test that cannot fail proves nothing)

Each mutation was applied to a throwaway copy of the repo under `/tmp` (never to the repo), then
the smoke test was re-run against that copy. All seven produced `RESULT: FAIL` with a `FAIL:` line
and no traceback.

| # | Mutation in `browser/app.js` | Observed (target line) |
|---|---|---|
| 1 | tradition predicate no longer applied (`if (f.tradition)` → `if (false)`) | `FAIL: #filter-tradition = 'Akan (Ghana)': page never showed 1 quotes within 15000ms (filtered-count='324')` (3 checks failed; the combined check also caught it, `filtered-count='77'`) |
| 2 | tag filter changed from membership to whole-string equality | `FAIL: #filter-tag = 'acceptance': page never showed 2 quotes within 15000ms (filtered-count='0')` |
| 3 | "Issues only" toggle stops subtracting | `FAIL: 'Issues only' checked: page never showed 320 quotes within 15000ms (filtered-count='324')` |
| 4 | `renderTableRows()` no longer emits the empty-state row | `FAIL: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada'): table view rendered 0 empty-state cells, expected 1` |
| 5 | `populateSelect("filter-verification", …)` removed | `FAIL: filter dropdowns do not offer the values in quotes.csv: #filter-verification missing=['unverified', 'verified'] unexpected=[]` |
| 6 | verification predicate no longer applied | `FAIL: #filter-verification = 'unverified': page never showed 320 quotes within 15000ms (filtered-count='324')` |
| 7 | sort direction ignored (`const dir = state.sortDir === "asc" ? 1 : -1;` → `const dir = 1;`) | `FAIL: combined filter+search+sort left Length descending order broken (#filter-tradition = "Baha'i", search 'god'): [38, 51, 51, 54, 80]..` |

Three further controls target the **guards** rather than the checks. `quotes.csv` was rewritten in
a `/tmp` copy so that every row is `verified` / `excerpt` / `source_id 12` /
`has_unresolved_glyph=false` — i.e. **no** row carries an issue and two columns collapse to a
single value:

```
FAIL: #filter-item-type: no quotes.csv value narrows the set (each matches all 324 rows or zero) — the filter check would be vacuous
FAIL: #filter-verification: no quotes.csv value narrows the set (each matches all 324 rows or zero) — the filter check would be vacuous
FAIL: 'Issues only' would be vacuous: 0 of 324 rows carry an issue in quotes.csv — the check cannot distinguish a working toggle from a broken one
RESULT: FAIL (3 check(s) failed)
```

An intermediate version of that control — rewriting only `verification_status` — fired the two
filter guards and **not** the "Issues only" one, because 38 rows still carried other issues
(missing `source_id`, `item_type = unknown`, unresolved glyph). That is the guard behaving
precisely rather than trigger-happily, and it is why the control above zeroes all four issue
sources.

## CI and live acceptance

- PR [#18](https://github.com/mschwar/Garden-of-Wisdom/pull/18) — `smoke` (pull_request)
  **success**, run
  [34714335171](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34714335171).
- Merged into `main` as `745c1dc` ("Merge pull request #18"), branch deleted.
- On `main` after the merge: `smoke` run
  [34714388506](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34714388506) **success**;
  Pages deploy run 34714388432 **success**.
- **Live acceptance** — the same 32 checks pointed at production, not at a local server:

```
$ .venv/bin/python scripts/smoke_quote_browser.py --base-url https://mschwar.github.io/Garden-of-Wisdom
...
PASS: all 6 filter dropdowns offer exactly the quotes.csv values plus an 'All' first option
PASS: #filter-tag = 'acceptance' narrows to 2 cards, matching quotes.csv
PASS: 'Issues only' narrows to 320 cards (dropping 4), every one badged
PASS: combined #filter-tradition = "Baha'i" + search 'god' + Length desc renders 8 rows in order, matching quotes.csv
PASS: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada') renders the empty-state row 'No matching quotes. Adjust the filters or search.'
RESULT: PASS (0 warning(s))
```

i.e. the deployed page offers the CSV's own filter values, filters, toggles, combines with search
and sort, and reports an empty result exactly as the data says — not just the local server.

## Out of scope, recorded not fixed

- **Card view has no empty state.** Found while writing the empty-result check and confirmed by
  direct measurement (headless Chromium, 1280px, a search matching nothing):
  `#results` children = 0, `#results` text = `''`, `.empty-state` elements = 0 — a blank area under
  a header reading "0 shown", where table view renders
  "No matching quotes. Adjust the filters or search." Fixing it is a browser **behaviour** change,
  which #13 explicitly puts out of scope ("any change to the browser's filter behaviour itself"),
  so it is filed as [#17](https://github.com/mschwar/Garden-of-Wisdom/issues/17) with a queue entry
  and a `docs/DECISIONS.md` note, and the new empty-result check asserts only what exists today
  (zero cards + the table's empty-state row). The follow-up unit should add the card-view assertion.
- **CI runs on deprecated Node 20 action majors.** GitHub annotated the `main` smoke run:
  `actions/checkout@v4` and `actions/setup-python@v5` still target Node 20 and were forced onto
  Node 24 (the three Pages actions in `pages.yml` are older majors as well — current: `checkout`
  v7.0.1, `setup-python` v7.0.0, `configure-pages` v6.0.0, `upload-pages-artifact` v5.0.0,
  `deploy-pages` v5.0.1). CI is green today, so this is future-proofing, not a break — but the
  Pages actions are the deploy path the queue explicitly guards, so it is its own unit rather than
  a drive-by version bump here. Filed as [#19](https://github.com/mschwar/Garden-of-Wisdom/issues/19)
  with a queue entry.
- **`AGENTS.md` was still not updated** (its "What commands to run" section would be the natural
  home for `scripts/smoke_quote_browser.py`); the write is refused by tool policy, the same
  deviation the W0 unit and the previous browser unit recorded. The command is documented in
  `README.md`, `docs/RUNBOOK.md`, and `docs/architecture/QUOTE_BROWSER.md`. A human who approves
  the write can add one line.

## Next authorized action

**Nothing in this lane.** Issue #13 is closed; the only remaining browser-lane item is #17 (card
view empty state), which needs an explicit go-ahead because it changes the page's behaviour. The
corpus-program next action is unchanged and still gated on the operator: **W1.1 storage decision +
minimal schema** — see `docs/program/W1_DECOMPOSITION.md` §W1.1 and `docs/queue.md` §"Open —
corpus program"; it is decomposed but **not authorized**.
