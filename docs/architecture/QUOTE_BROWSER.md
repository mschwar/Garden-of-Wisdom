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

This also works unmodified from GitHub Pages later: point Pages at the repo root and the same
relative fetches resolve correctly.

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
  - Every column header (`ID`, `Tradition`, `Author`, `Source`, `Tags`, `Type`,
    `Verification`, `Length`, `Quote text`) is click-to-sort; clicking the active column
    flips direction. The active column shows a ▲/▼ indicator and the choice is mirrored back
    to the "Sort by" dropdown.
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

## Manual smoke test performed

Loaded via a local `python3 -m http.server` and driven with Claude in Chrome:
- Confirmed initial load shows 324/324 with no console errors.
- Confirmed search for "Dhammapada" filters to 29 matching cards with correct content.
- Confirmed "Issues only" checkbox toggles the filtered count.
- Confirmed a copy button click produces no console errors.

No automated browser test was added in this phase (see `docs/queue.md` — "browser smoke test"
is listed as a deviation, not a completed item).
