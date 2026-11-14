# Garden of Wisdom

Curated multi-tradition quote collection (`quotes.csv` and `sources.csv`), static client-side quote browser (`browser/`), and verified homepage preview export (`exports/bahai-homepage-preview/v1/`).

## Repository Layout

- `quotes.csv` — 324 curated quotes with tradition, author, source reference, item type, and verification status.
- `sources.csv` — 32 source manifest records linked from `quotes.csv`.
- `index.html` & `browser/` — zero-backend static quote browser deployed to GitHub Pages (staged via `_site/`).
- `exports/bahai-homepage-preview/v1/` — deterministic verified Bahá'í preview export consumed downstream (`collection.json`, `mapping.json`, `SHA256SUMS`).
- `scripts/validate_quotes.py` — deterministic corpus validator for `quotes.csv` and `sources.csv`.
- `scripts/export_homepage_preview.py` — regenerates `exports/bahai-homepage-preview/v1/` from `quotes.csv` and `sources.csv`.
- `scripts/validate_homepage_preview_export.py` — verifies schema, counts, provenance, and SHA-256 digests of the homepage preview export.
- `scripts/smoke_quote_browser.py` — headless Chromium Playwright smoke suite for `browser/index.html`.
- `tests/` — fast `pytest` suite covering `validate_quotes.py` and GitHub Pages `_site/` staging isolation.

## Verification

```bash
python3 scripts/validate_quotes.py
python3 scripts/validate_homepage_preview_export.py
pytest
```

To run the full headless Chromium browser smoke check:

```bash
python3 scripts/smoke_quote_browser.py
```
