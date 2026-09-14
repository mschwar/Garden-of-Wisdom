# Quote Browser / Audit Console

## What it is

A static, dependency-free HTML/CSS/JS page at `browser/index.html` that fetches
`../quotes.csv` and `../sources.csv` at load time, parses them client-side, and renders a
searchable/filterable/sortable card view. No backend, no build step, no framework, no
analytics, no runtime AI.

## Run it

From the repo root:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/browser/index.html`. (Any static file server works — the
only requirement is that `browser/index.html` can `fetch()` `../quotes.csv` and
`../sources.csv` relative to itself, which needs an actual HTTP server, not a `file://` URL,
because `fetch()` on `file://` is blocked by the browser.)

This also works unmodified from GitHub Pages: the live site is rooted at the repo root, so
the same relative fetches resolve correctly. See the deployment section below.

## Deployment (GitHub Pages)

Site URLs (deployed from `main` by `.github/workflows/pages.yml`):

- app — `https://mschwar.github.io/Garden-of-Wisdom/browser/index.html`
- site root — `https://mschwar.github.io/Garden-of-Wisdom/`, a redirect shim in the repo-root
  `index.html` that forwards to the app

The workflow publishes the **repo root** (`path: '.'`; `actions/upload-pages-artifact` drops
`.git` and `.github`, plus — **from v4 on** — top-level dotfiles by default) via
`actions/deploy-pages` under the `github-pages` environment. It runs on push to `main` and on
manual `workflow_dispatch` from `main` (the job is guarded so a dispatch from another branch
is a no-op). Pages "Source" must be **GitHub Actions**, not "Deploy from a branch" — that
setting is created out of band (`GITHUB_TOKEN` cannot enable it) and the workflow assumes it;
see `docs/RUNBOOK.md`.

The action's major version is part of that path, not a cosmetic pin: v3 had no hidden-file
exclusion and published `./.gitignore` (issue #23), so
`scripts/check_pages_contract.py` fails if the upload action drops below v4, if
`include-hidden-files` is switched on, or if `path:`/the artifact name/the deploy job's main
guard change. It also fails if the app's `../` fetches, the root CSVs, or the root shim move
out from under the layout this deploy serves.

**Why the site root cannot change:** `browser/index.html` fetches `../quotes.csv` and
`../sources.csv` relative to itself, and both files live at the repo root. Publishing only
`browser/` as the site root would make those fetches 404 and the page would load with zero
quotes. The artifact path must stay `'.'` (repo root) and the equivalent live checks are that
`https://mschwar.github.io/Garden-of-Wisdom/quotes.csv` returns 200 **and** that
`/.gitignore` returns 404 (a mis-rooted artifact is not the only silent failure — a
published dotfile is the other; the full probe list is in `docs/RUNBOOK.md`). This mirrors the
local `python3 -m http.server` layout exactly — same relative paths, no separate build.

## Features implemented

- Global text search across quote text, author, source, and tags.
- Sort by ID, tradition, author, source, or quote length, ascending or descending.
- Filters: tradition, author, source, tag, item type, verification status.
- "Issues only" toggle — hides rows whose only issue would have been `unverified` once they
  are `verified` and have no other flags. After G4, four donor rows (ids 3, 12, 15, 26) are
  `verified`; the toggle therefore drops those four unless they carry another issue badge.
- Visible total count and filtered count in the header.
- Per-card issue badges (unresolved glyph, unresolved source link, unknown item type,
  unverified) so uncertainty is visible on the card itself, not just in a hidden field.
- One-click "Copy quote", "Copy quote + attribution", and "Copy JSON" (full record) per card,
  via `navigator.clipboard`.
- Expandable "Provenance & details" panel per card showing `item_type`,
  `verification_status`, linked `source_id`, and the linked `sources.csv` title/notes when
  resolved.
- **Cards / Table view toggle** (`#view-mode`). Table mode renders the same filtered/sorted
  rows as a dense, sortable table:
  - Every sortable column header (`ID`, `Tradition`, `Author`, `Source`, `Tags`, `Type`,
    `Verification`, `Length`) is click- or keyboard-activatable to sort (Enter/Space); clicking
    the active column flips direction. The active column shows a ▲/▼ indicator and
    `aria-sort`, and the choice is mirrored back to the "Sort by" dropdown.
  - Verification status is shown as a color-coded pill (`verified` green, else neutral).
  - Issue badges render inline above each quote so problematic rows stand out while scanning.
  - Per-row `Copy`, `+Attr`, and `JSON` action buttons match the card actions.
  - The table sits in a `max-height` scroll container with a sticky header row and horizontal
    scrolling, so headers stay visible while scanning all rows on narrow screens.
- **Empty state in both views.** When the search/filter combination matches nothing, both views
  say so with the same message — `No matching quotes. Adjust the filters or search.` — rendered
  as the table's `td.empty-state` row and as a full-width `#results .empty-state` message in
  card view. The string lives in one constant in `browser/app.js`
  (`EMPTY_STATE_MESSAGE`), so the two views cannot drift into disagreeing about an empty
  result; before this, card view rendered a blank area under a header reading "0 shown".

## Not implemented (deliberately, per Phase 0 scope)

- No dedicated duplicate/near-duplicate review UI beyond what the issue badges surface —
  `scripts/validate_quotes.py`'s near-duplicate output is the source of truth for that queue
  item; wiring it into the browser is future work if the curation flow needs it (see
  `docs/queue.md`).
- No auth, no backend, no write-back from the browser into the CSVs — this is a read-only
  audit tool by design (`docs/product/PRODUCT_DOCTRINE.md` non-negotiables).

## Automated smoke test

`scripts/smoke_quote_browser.py` drives the real page in headless Chromium (Playwright) against
a throwaway static server rooted at the repo root. It asserts, with every expected count
recomputed from `quotes.csv`/`sources.csv` rather than hard-coded:

- `/browser/index.html`, `/quotes.csv`, `/sources.csv` all serve 200, and both CSVs are
  byte-identical to the working tree (the repo-root layout contract above);
- header counts and the rendered card count equal the number of rows `browser/app.js`'s parser
  would keep;
- search narrows the set to exactly the rows containing the term, and sorting by length orders
  the rendered rows (both directions), while clicking a table header sets `aria-sort`;
- **all six filter dropdowns** — each offers exactly the distinct values present in
  `quotes.csv` (with `All` as its first option), and selecting a narrowing value renders exactly
  the rows Python counts with the same predicate `browser/app.js` uses (exact column match, tag
  membership for `#filter-tag`);
- **the "Issues only" toggle** — narrows the set to exactly the rows whose `detectIssues()` is
  non-empty and every rendered card carries an issue badge;
- **a combined interaction** — a dropdown value plus a search term plus a sort direction,
  asserted in table view on both the row count and the ordering;
- **the empty-result state** — a filter/search combination with no matches renders
  `No matching quotes. Adjust the filters or search.` in **both** views: the table view's
  `td.empty-state` row and a `#results .empty-state` element in card view, the two messages
  compared with each other, and zero cards;
- the table view renders one row per filtered quote;
- the per-card copy button puts that card's quote text on the clipboard;
- the document does not overflow horizontally at 320/375/768px, in card **and** table view;
- zero console errors, page errors, and failed requests.

Run it with (from the repo root):

```
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
python3 scripts/smoke_quote_browser.py
```

It exits 0 with `RESULT: PASS`; any broken check prints a `FAIL:` line naming what broke and
exits non-zero. A green run prints 33 `PASS:` lines and `RESULT: PASS (0 warning(s))`.

The test refuses to pass vacuously: the search term, every filter value it selects, and the
"Issues only" toggle are each asserted to still *narrow* the data, the combined-interaction and
empty-result combinations are *searched for* in the data rather than assumed, and if any of them
stops distinguishing behaviour the run fails with an explicit "would be vacuous" line. Sixteen
negative controls are recorded — seven in `GARDEN_BROWSER_SMOKE_HANDOFF.md` (reverting either CSS
responsiveness fix, removing the `#table-wrap` hide, breaking the search filter, repointing the
data fetch, breaking a copy button, logging a console error), seven in
`GARDEN_FILTER_SMOKE_COVERAGE_HANDOFF.md` (breaking each filter predicate, the tag membership
rule, the Issues-only toggle, the empty state, a dropdown's population, and the sort direction),
and two in `GARDEN_CARD_EMPTY_STATE_HANDOFF.md` (card view dropping its empty state, and the
card/table messages being edited apart), each of which turns the run red. Three further controls
in the filter-coverage handoff show the vacuity guards themselves firing when the data stops
distinguishing them. CI runs it on every PR and push to `main`
(`.github/workflows/browser-smoke.yml`).

### Responsiveness (fixed 2026-09-12)

At phone widths the page used to scroll horizontally. Two independent causes, both measured in
Chromium at 375px:

1. A `<select>` sizes itself to its longest `<option>`, and the Source dropdown's longest
   `source_ref` is 61 characters — the control rendered **390px** wide (Author: 276px) inside a
   341px container, overflowing the document to 421px. Fixed by letting the control row's
   labels shrink (`min-width: 0; max-width: 100%`) and capping the selects (`max-width: 100%`).
   The old queue note blamed `min-width: 140px`; that was not the cause.
2. `.tags` renders a comma-joined tag list with no spaces (`love,neighbor,goldenrule`), i.e. one
   unbreakable token ~280px wide that escaped the card and added its own overflow at 320px.
   Fixed with `overflow-wrap: anywhere` plus allowing `.meta-row` to wrap.

`docs/queue.md` carried the first as a known defect; the second was found by the new test.
