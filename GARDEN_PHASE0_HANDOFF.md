# Garden Phase 0 Handoff — 2026-09-11

Executed against
`bootstrap/seed/2026-09-11-garden-2026-retrofit/prompts/01_GARDEN_PHASE0_RETROFIT_AND_BROWSER.txt`
on branch `feat/phase0-garden-2026-retrofit` (based on `bootstrap/2026-agent-retrofit`, based
on `main`).

## 1. What the project actually is

A personal, curated collection of memorable passages from multiple religious/philosophical/
oral traditions, for memorization and reflection — a corpus plus a curation/review workbench.
Distinct from, and not to be merged with, `bahai-homepage`. Full doctrine:
`docs/product/PRODUCT_DOCTRINE.md`.

## 2. Archaeology findings

Full detail in `docs/audit/2026-09-11/FINDINGS.md`. Headlines:

- Repo previously had only `README.md`, `quotes.csv`, `sources.csv`, and a tracked
  `.DS_Store` across 8 commits, all 2025.
- README's claim of UTF-8 encoding was false; actual encoding was Mac OS Roman. Confirmed by
  direct decode attempts, not assumed.
- `sources.csv` had a real malformed-CSV bug (unescaped commas in `notes` fragmenting rows) —
  an early version of the migration script accidentally truncated notes text because of this;
  caught and fixed before this data reached the canonical files.
- ID gaps (250→261, 290→301) confirmed original, not corruption.
- Tradition list: 27 actual values vs. 7 documented. Confirmed the data, not the README, was
  right — canonical README now documents all 27.
- Multiple genuine near-duplicate/variant-translation clusters confirmed (Gita 2.47, Yasna
  43:1, several Dhammapada verses). 0 exact-text duplicates.

## 3. Exact data counts

- 324 quote rows, IDs 1–344, 0 duplicate IDs, 0 rows with missing required fields.
- 27 distinct traditions.
- `item_type` counts: `excerpt` 268, `oral-attribution` 34, `unknown` 22, `full-passage` 0,
  `paraphrase` 0 (no row was classified into these last two — see limits below).
- `verification_status`: all 324 rows `unverified`.
- 14 rows with unresolved `source_id`.
- 4 rows with `has_unresolved_glyph = true`.
- `sources.csv`: 18 rows, unchanged count, notes field repaired (no longer truncated).

Full raw validator output: `docs/data/DATA_QUALITY_REPORT.md`.

## 4. Encoding diagnosis and what was done

Diagnosis: both CSVs were Mac OS Roman, not UTF-8. Verified by direct `bytes.decode('utf-8')`
failure and successful `bytes.decode('mac_roman')` round-trip producing correct diacritics
(e.g. byte `0x87` → `á`).

Action: archived the original bytes byte-for-byte at
`data/archive/2026-09-11/{quotes,sources}.original.csv` (checksummed to confirm identical to
the pre-retrofit root files), then wrote `scripts/rehabilitate_2026_09_11.py`, which reads only
from that archive and writes new UTF-8 `quotes.csv`/`sources.csv` at the repo root. The script
is re-runnable and idempotent (always reads from the frozen archive).

Separately identified and explicitly NOT auto-fixed: 4 rows use a literal `_` character where
a diacritic/modifier letter belongs. This is not an encoding bug (the byte really is ASCII
`0x5F`) — flagged via `has_unresolved_glyph` for human correction instead of guessed.

## 5. Schema / data-contract decisions

Added four columns to `quotes.csv`: `item_type`, `verification_status`, `source_id`,
`has_unresolved_glyph`. Rationale and exact heuristics for each in
`docs/data/DATA_CONTRACT.md`. Key decisions and why, in `docs/DECISIONS.md`:

- Re-decode from archived bytes rather than string-replace mojibake patterns.
- Don't guess the glyph behind literal `_` placeholders.
- Link `source_id` by matching `source_ref` keywords, not by coarse `tradition`-level mapping.
- Keep the 27-value tradition list; update the README instead of the data.
- Ship the browser as vanilla JS, no CSV library.

## 6. What remains unverified

Everything. `verification_status` is `unverified` for all 324 rows — this phase explicitly
excluded verification work. See `docs/queue.md` for the itemized curation backlog (unresolved
source links, near-duplicate review, unresolved glyphs, `unknown` item-type reclassification).

## 7. Quote-browser features and exact run command/URL

Run: `python3 -m http.server 8000` from repo root, open
`http://localhost:8000/browser/index.html`.

Features: global search, sort (ID/tradition/author/source/length, both directions), filters
(tradition/author/source/tag/item type/verification status), issues-only toggle, visible
total/filtered counts, per-card issue badges, copy quote / copy quote+attribution / copy JSON,
expandable provenance panel. Full detail: `docs/architecture/QUOTE_BROWSER.md`.

## 8. Validator commands and raw results

Command: `python3 scripts/validate_quotes.py`. Exit code 0. Full raw output captured verbatim
in `docs/data/DATA_QUALITY_REPORT.md` (not reproduced twice here to avoid drift between
copies — that file is the source of truth, re-run the script yourself to get current numbers).

## 9. Screenshots / evidence paths

No screenshot files were saved to the repo. The browser was manually smoke-tested via Claude
in Chrome against a local `python3 -m http.server` instance:
- Initial load: 324/324 shown, 0 console errors.
- Search "Dhammapada": correctly filtered to 29 cards.
- "Issues only" checkbox: toggled correctly (shows 324/324 currently, expected — see
  `docs/architecture/QUOTE_BROWSER.md`).
- Copy-quote button click: no console errors.

No automated test/screenshot artifacts were generated or committed.

## 10. Repo changes by category

- **New files**: `AGENTS.md`, `.gitignore`, `docs/**` (product doctrine, data contract, data
  quality report, architecture doc, runbook, queue, decisions, audit findings), `browser/**`
  (index.html, style.css, app.js), `scripts/rehabilitate_2026_09_11.py`,
  `scripts/validate_quotes.py`, `data/archive/2026-09-11/*.original.csv`, this handoff.
- **Modified**: `quotes.csv` (re-encoded UTF-8, 4 new columns), `sources.csv` (re-encoded
  UTF-8, `notes` field repair), `README.md` (rewritten to be canonical/current).
- **Removed**: tracked `.DS_Store` (now git-ignored).
- **Not touched**: no row's `quote_text`, `tradition`, `source_ref`, `author`, or `tags` value
  was altered in meaning — only re-encoded to UTF-8. (One caveat: literal `_` placeholder
  characters were preserved verbatim, not "fixed," per the decision above.)

## 11. Queued next work

See `docs/queue.md`. Top items: fill 14 source-manifest gaps, human-review 45 near-duplicate
candidates (with the generic-label false-positive caveat), resolve 4 unresolved-glyph rows,
reclassify 22 `unknown` item-type rows.

## 12. Proposal for a later Garden export satisfying the homepage collection contract

Not built in this phase (out of scope). Proposal for later, once a homepage collection
contract exists (see the seed's `bahai-homepage` work unit) and a human has approved a donor
ID list:

- Export would be a **new, separate, generated file** (e.g. `exports/bahai-homepage/
  <date>-donor-set.json`), never a live read of `quotes.csv` by the homepage repo — this keeps
  Garden's schema free to evolve without coupling to homepage's runtime shape.
- Only rows with `verification_status = verified` AND `tradition = "Baha'i"` AND an explicit,
  human-approved donor `id` list would be eligible — never an automatic "all Baha'i rows"
  export, since verification status today is uniformly `unverified`.
- The export step itself should re-run `scripts/validate_quotes.py` as a precondition and
  hard-fail if the donor IDs aren't all `verified`.
- This proposal does not commit to a shape for the exported JSON; that should be negotiated
  against whatever the homepage's H2B collection contract actually specifies once it exists,
  per `shared/CROSS_REPO_COLLECTION_PRINCIPLES.md` in the seed packet.

## 13. Deviations from the prompt

- The prompt's `item_type` enum includes `full-passage` and `paraphrase`; the heuristic
  implemented in this phase never assigns either (it only distinguishes `excerpt` /
  `oral-attribution` / `unknown`). Distinguishing a full passage from an excerpt, or an excerpt
  from a paraphrase, requires comparing against actual primary-source text, which is
  explicitly out of scope for Phase 0 ("do not verify hundreds of quotes manually"). Flagged
  here rather than fabricating a classification without evidence.
- The prompt asked for preserving original bytes "in an archival location or git-appropriate
  immutable record." Chose a plain archival directory (`data/archive/2026-09-11/`) with
  checksum verification over a git-native mechanism (e.g. a tag on the pre-retrofit commit),
  since the pre-retrofit commit already exists in history (`ef38aca` and earlier) and is itself
  an adequate immutable record — the archive directory is redundant-but-convenient, not the
  only copy.
- Did not build a dedicated duplicate-review UI in the browser (listed as a "consider" item in
  `docs/queue.md`, not implemented) — the CLI validator's near-duplicate report was judged
  sufficient signal for this phase, and adding UI for it without knowing the actual curation
  workflow risked over-building.
- No automated browser test/CI was added; only a manual Claude-in-Chrome smoke test was
  performed and recorded in `docs/architecture/QUOTE_BROWSER.md`. If this repo gets CI later,
  wiring a headless check for `scripts/validate_quotes.py` would be the cheap first step.

## STOP

Per the prompt's stop condition: this phase is complete. No donor-set selection, authoritative
verification, or homepage work has been started. Next step is human/frontier review of this
handoff, the rehabilitated data, and the browser.
