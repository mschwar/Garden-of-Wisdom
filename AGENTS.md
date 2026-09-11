# AGENTS.md

Read this before touching anything in this repo.

## What this project is

A personal, curated collection of memorable passages from multiple religious/philosophical
traditions, for memorization and reflection. See `docs/product/PRODUCT_DOCTRINE.md` for
intent and non-goals.

## What data is authoritative vs provisional

- `quotes.csv` and `sources.csv` at repo root are the **current working data** — canonical
  UTF-8, but every row's `verification_status` is `unverified` as of the 2026-09-11 retrofit.
  Nothing here has been checked word-for-word against a primary source yet. Treat quote
  wording as *probably close, not confirmed*.
- `data/archive/2026-09-11/*.original.csv` are the **frozen legacy bytes** exactly as they
  existed before the retrofit (Mac OS Roman encoded, mojibake and all). Never edit these.
  They exist so any transformation can be audited or redone from the true original.
- `docs/audit/2026-09-11/` is a point-in-time findings snapshot. Don't treat it as living
  documentation — re-run `scripts/validate_quotes.py` for current state.

## What commands to run

- `python3 scripts/validate_quotes.py` — deterministic data validator. Run before and after
  any change to `quotes.csv` or `sources.csv`. See `docs/RUNBOOK.md`.
- `python3 -m http.server 8000` from repo root, then open `http://localhost:8000/browser/` —
  runs the quote browser locally. No build step.

## What may be changed autonomously

- Documentation under `docs/`.
- The browser (`browser/`) — pure static HTML/CSS/JS, no backend, no framework.
- `scripts/validate_quotes.py` — improving checks is always welcome.
- Adding new `unverified` quotes with correct schema, as long as `scripts/validate_quotes.py`
  still passes.

## What requires human/provenance review before proceeding

- Anything that would change `verification_status` to `verified` — that means a human (or a
  frontier-review pass explicitly authorized to do so) checked the quote against a real
  primary source.
- Any donor-set export intended for `bahai-homepage` or any other consuming project. See
  `shared/CROSS_REPO_COLLECTION_PRINCIPLES.md` under the seed packet and
  `bootstrap/seed/2026-09-11-garden-2026-retrofit/workunits/G4_VERIFIED_HOMEPAGE_PREVIEW_EXPORT.md`.
  Do not run that work unit without an operator-approved donor ID list.
- Rewriting quote text to "fix" the literal `_` placeholders left by the original author for
  diacritics/modifier letters they couldn't type (see `docs/data/DATA_QUALITY_REPORT.md`).
  Replacing `_` with a guessed glyph is fabrication unless it's a provable restoration.
- Deleting or merging rows flagged as near-duplicates. Some are legitimate variant
  translations of the same verse; only a human curation pass should decide.

## How to resume work

1. `git status` and `git log --oneline -10`.
2. Read `docs/queue.md` for the current work queue.
3. Read `docs/DECISIONS.md` (append-only) for what's already been decided and why.
4. Read the most recent handoff document at repo root (e.g. `GARDEN_PHASE0_HANDOFF.md`).
5. Re-run `python3 scripts/validate_quotes.py` before claiming anything is done — do not
   trust a stale report.
