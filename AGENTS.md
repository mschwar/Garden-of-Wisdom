# AGENTS.md

Read this before touching anything in this repo.

## What this project is

A personal, curated Garden of **passages worth keeping** across religious, philosophical,
literary, scientific, artistic, historical, oral/cultural and other personally meaningful
sources, for rediscovery, understanding, comparison, memorization and reflection.

The durable domain object is **Passage**; “quote” is a legacy data/surface term. Read
`docs/product/PRODUCT_DOCTRINE.md` for stable product boundaries and
`docs/PRODUCT_REALITY.md` for standing system/usability reality.

**Product reality is not in this file.** It lives in `docs/PRODUCT_REALITY.md`.

**Live programme status is not in this file.** It lives in
`docs/program/usability-closure/CURRENT.md` — the current gate, the single READY unit, the
last completed unit, the frontier. If this file and CURRENT disagree about status, CURRENT
wins and this file is the bug (`scripts/check_front_door.py` enforces that routing).

## What data is authoritative vs provisional

- `quotes.csv` and `sources.csv` at repo root are the **current working data** — canonical
  UTF-8. As of the 2026-09-11 retrofit every row was `unverified`. A later G4 pass verified
  four homepage-preview donors (ids 3, 12, 15, 26); the other 320 rows remain `unverified`.
  Treat unverified wording as *probably close, not confirmed*.
- `data/store/garden.export.txt` is the **committed mirror of the corpus store**; the SQLite
  database (`garden.sqlite3`) is machine-local and git-ignored. The store is authoritative for
  captured candidates and curation state, and the mirror is what a fresh clone reads. Rebuild
  a local store with `garden_store.py bootstrap` — never by hand-editing the mirror.
- `data/archive/2026-09-11/*.original.csv` are the **frozen legacy bytes** exactly as they
  existed before the retrofit (Mac OS Roman encoded, mojibake and all). Never edit these.
  They exist so any transformation can be audited or redone from the true original.
- `docs/audit/2026-09-11/` is a point-in-time findings snapshot. Don't treat it as living
  documentation — re-run `scripts/validate_quotes.py` for current state.

### Read-only in practice: the canonical CSVs

`quotes.csv` and `sources.csv` were read-only for the whole of the corpus-program W1 wave
(now complete). They change only inside a **named data unit** (D3 / D4 / D6 / D7 / D8 …),
never as a side effect of another unit, and always with `python3 scripts/validate_quotes.py`
PASSing before and after. Do not edit them to make a check pass.

## What commands to run

Everything below is stdlib-only except the browser smoke test. `docs/RUNBOOK.md` carries the
arguments and the expected output for each — this list is the command surface, not the
reference.

- `python3 scripts/validate_quotes.py` — deterministic data validator. Run before and after
  any change to `quotes.csv` or `sources.csv`.
- `python3 scripts/check_program_contracts.py` — doctrine and fixture consistency for the
  corpus program.
- `python3 scripts/garden_store.py {bootstrap,status,sync} [--dir DIR]` — the store lifecycle,
  and the **resume/bootstrap path**. On a fresh clone, `bootstrap` hydrates the local SQLite
  store from the committed mirror; `status` reports `CURRENT` / `STALE` / `MISSING_DB` /
  `MISSING_MIRROR`; `sync` refreshes the mirror from the store.
- `python3 scripts/garden_submit.py submit …` (W1.3 capture) → `python3
  scripts/garden_normalize.py {normalize,hints,classify,describe}` (W1.4) → `python3
  scripts/garden_review.py {queue,show,audit,accept,hold,reject,duplicate,reopen}` (W1.5) —
  the candidate workbench loop (capture → normalize → hints → curation decision).
- `python3 scripts/garden_ledger.py {mark,reopen,list}` (D3 unverifiable side-car ledger) and
  `python3 scripts/garden_legacy_batch.py {seed,show,verify}` (D4 legacy batch capture feed).
- `python3 scripts/garden_envelope.py {serialize,validate}` — the candidate-envelope contract
  and its validator.
- `python3 scripts/check_garden_*.py` — the corpus-program acceptance suites, one per surface:
  store, envelope, submit, normalize, review, e2e, ledger, legacy-batch, lifecycle.
- `python3 scripts/run_negative_controls.py` — re-applies the committed negative-control table
  so every checker's falsifiability is machine-checked rather than asserted in a handoff.
- `python3 scripts/check_front_door.py` — asserts the front-door docs still describe the
  current command surface and route live status to CURRENT.
- `python3 scripts/check_pages_contract.py` and `python3 scripts/check_live_pages.py` — the
  GitHub Pages deploy contract, and live acceptance (four 200s, three 404s, live CSV
  byte-identity against the repo).
- `python3 scripts/smoke_quote_browser.py` — drives the browser in headless Chromium (needs
  `requirements-dev.txt` and a one-time `python3 -m playwright install chromium`).
- `python3 scripts/export_homepage_preview.py` then `validate_homepage_preview_export.py` —
  regenerate and check the v1 homepage-preview collection under
  `exports/bahai-homepage-preview/v1/`.
- `python3 -m http.server 8000` from repo root, then open `http://localhost:8000/browser/` —
  runs the quote browser locally. No build step.

## What may be changed autonomously

- Documentation under `docs/`.
- The browser (`browser/`) — pure static HTML/CSS/JS, no backend, no framework.
- `scripts/validate_quotes.py` — improving checks is always welcome.
- Small documentation/test improvements that preserve product/state authority. **Do not add new
  Garden passages by directly appending `quotes.csv` rows.** New material enters through the
  candidate workbench; canonical Garden admission is operator-controlled.

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
- Any gate decision in the usability-closure programme (Gate U0 / Gate U1 acceptance), and
  starting anything past the unit CURRENT marks READY.

## How to resume work

1. `git status` and `git log --oneline -10`.
2. Read `docs/program/usability-closure/CURRENT.md` — the live status: current gate, the
   single READY unit, the last completed unit, the frontier.
3. Read `docs/queue.md` (living work queue) and `docs/DECISIONS.md` (append-only rationale).
4. Read the READY unit's document under `docs/program/usability-closure/workunits/` and the
   most recent unit handoff (`GARDEN_<UNIT>_HANDOFF.md` at repo root). Root handoffs and the
   W0/W1 gate packets are **historical evidence**, not current status.
5. If the local store is absent, `python3 scripts/garden_store.py bootstrap --dir data/store`,
   then `python3 scripts/garden_store.py status --dir data/store` and confirm `CURRENT`.
6. Re-run the acceptance suites for the surface you are touching — never trust a stale
   report. `python3 scripts/validate_quotes.py` for data; `python3 scripts/check_garden_*.py`
   for the corpus surfaces; `python3 scripts/check_front_door.py` if you touched a front door.
7. Work discovered outside your unit's scope goes to `docs/queue.md` (observed problem, why it
   matters, evidence/path, proposed owner, whether it blocks the current gate). Do not fix it
   in passing.
