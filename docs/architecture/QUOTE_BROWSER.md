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
- "Issues only" toggle — currently shows all 324 rows, because every row is
  `verification_status = unverified` right now (see `docs/data/DATA_QUALITY_REPORT.md`). This
  is correct, not a bug: nothing has been verified yet. It becomes a meaningful filter once
  some rows are marked `verified` in a later phase.
- Visible total count and filtered count in the header.
- Per-card issue badges (unresolved glyph, unresolved source link, unknown item type,
  unverified) so uncertainty is visible on the card itself, not just in a hidden field.
- One-click "Copy quote", "Copy quote + attribution", and "Copy JSON" (full record) per card,
  via `navigator.clipboard`.
- Expandable "Provenance & details" panel per card showing `item_type`,
  `verification_status`, linked `source_id`, and the linked `sources.csv` title/notes when
  resolved.

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
