# Agents Operating Guide

## Scope & Product Surfaces

`Garden-of-Wisdom` ships three live surfaces:

1. **Canonical CSV corpus:** `quotes.csv` (324 quotes) and `sources.csv` (32 sources) at the repository root.
2. **Static quote browser:** `index.html` and `browser/{index.html,app.js,style.css}`, deployed to GitHub Pages from a minimal staged `_site/` directory (`{index.html, browser/, quotes.csv, sources.csv}`).
3. **Downstream preview export:** `exports/bahai-homepage-preview/v1/*` (`collection.json` schema consumed by `bahai-homepage` and `song-book`).

## Guardrails

- Do **not** break `exports/bahai-homepage-preview/v1/collection.json` schema or checksums; run `python3 scripts/validate_homepage_preview_export.py` after any corpus or export change.
- Do **not** alter `ops/merge-policy.json` without explicit operator authorization.
- Keep GitHub Pages staging in `.github/workflows/pages.yml` restricted to `_site/` containing only `index.html`, `browser/`, `quotes.csv`, and `sources.csv` — never upload the repository root.
- Run proportional local verification before opening or updating a PR:
  - `uvx ruff check scripts tests`
  - `python3 scripts/validate_quotes.py`
  - `python3 scripts/validate_homepage_preview_export.py`
  - `pytest`
