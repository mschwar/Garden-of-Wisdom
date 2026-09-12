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
`.git` and `.github`, plus top-level dotfiles by default) via `actions/deploy-pages` under the
`github-pages` environment. It runs on push to `main` and on manual `workflow_dispatch` from
`main` (the job is guarded so a dispatch from another branch is a no-op). Pages "Source" must
be **GitHub Actions**, not "Deploy from a branch" — that setting is created out of band
(`GITHUB_TOKEN` cannot enable it) and the workflow assumes it; see `docs/RUNBOOK.md`.

**Why the site root cannot change:** `browser/index.html` fetches `../quotes.csv` and
`../sources.csv` relative to itself, and both files live at the repo root. Publishing only
`browser/` as the site root would make those fetches 404 and the page would load with zero
quotes. The artifact path must stay `'.'` (repo root) and the equivalent live check is that
`https://mschwar.github.io/Garden-of-Wisdom/quotes.csv` returns 200. This mirrors the local
`python3 -m http.server` layout exactly — same relative paths, no separate build.

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
exits non-zero. Six negative controls are recorded in the unit's handoff — reverting either CSS
responsiveness fix, breaking the search filter, repointing the data fetch, breaking a copy
button, or logging a console error each turns the run red. CI runs it on every PR and push to
`main` (`.github/workflows/browser-smoke.yml`).

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
