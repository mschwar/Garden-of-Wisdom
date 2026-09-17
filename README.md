# A Garden of Wisdom

A personal collection of impactful quotes from world religions, philosophies, and oral
traditions, curated for memorization and reflection.

The idea is inspired by the Bahá'í quote: "A kindly tongue is the lodestone of the heart of
men."

The goal is not to be exhaustive, but to be a clean, simple, impactful source of personal
inspiration — with its uncertainty made visible rather than hidden. See
`docs/product/PRODUCT_DOCTRINE.md` for the full doctrine and non-negotiables, and `AGENTS.md`
if you're an agent picking up work here.

## Status (as of the 2026-09-11 retrofit)

324 quotes across 27 traditions/cultures. Data is canonical UTF-8. Four homepage-preview
donors (ids 3, 12, 15, 26) are `verified` as of G4; the other 320 rows remain `unverified`
(see `docs/data/DATA_QUALITY_REPORT.md` for the retrofit snapshot, and
`exports/bahai-homepage-preview/v1/` for the export). A static browser/audit console is
available (see below).

## Quickstart

```
python3 scripts/validate_quotes.py                     # check data integrity
python3 scripts/check_program_contracts.py             # check the corpus-program doctrine set
python3 scripts/validate_homepage_preview_export.py    # check the v1 homepage export
python3 scripts/smoke_quote_browser.py                 # drive the browser in headless Chromium
python3 -m http.server 8000                            # then open http://localhost:8000/browser/
```

The smoke test needs a one-time `python3 -m pip install -r requirements-dev.txt` and
`python3 -m playwright install chromium`; it is the only command above that is not stdlib-only.

## Data files

- `quotes.csv` — canonical, UTF-8, one row per quote.
- `sources.csv` — manifest of source texts quotes are drawn from.
- `data/archive/2026-09-11/` — frozen original bytes (pre-retrofit, Mac OS Roman encoded),
  kept for provenance. Never edited.

Full schema and known data issues: `docs/data/DATA_CONTRACT.md`.

### `quotes.csv` fields

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Legacy identifier, stable, non-contiguous by design. |
| `quote_text` | yes | May contain literal `_` where an untypeable diacritic belongs — see `has_unresolved_glyph`. |
| `tradition` | yes | See **Traditions in use** below — this is now a documented, not enforced, controlled list. |
| `source_ref` | yes | Citation. |
| `author` | yes | Attributed speaker/author/collective. |
| `tags` | yes | Comma-separated, lowercase, singular-preferred. |
| `item_type` | yes | `full-passage` / `excerpt` / `paraphrase` / `oral-attribution` / `unknown`. Heuristic, not hand-verified — see `docs/data/DATA_CONTRACT.md`. |
| `verification_status` | yes | `unverified` / `verified` / `disputed`. |
| `source_id` | no | Links to `sources.csv`. Blank = no confident manifest match yet (real gap, see quality report). |
| `has_unresolved_glyph` | yes | `"true"` if a literal `_` placeholder is present. |

### Traditions in use

The **controlled list** of `tradition` values is the 27 distinct values observed in the
corpus (decision D8, 2026-09-12 — documented, not enforced in code):

`Akan (Ghana)`, `Baha'i`, `Buddhism`, `Cherokee`, `Christianity`, `Diné (Navajo)`,
`Ethiopian`, `Haudenosaunee (Iroquois)`, `Hinduism`, `Hopi (Pueblo)`, `Igbo (Nigeria)`,
`Islam`, `Judaism`, `K'iche' (Maya)`, `Lakota`, `Modern Mayan`, `Multitribal Proverb`,
`Nahua (Aztec)`, `Nez Perce`, `Nguni (Bantu)`, `Oglala Lakota`, `Shawnee`, `Sikhism`,
`Tewa (Pueblo)`, `Yoruba (Nigeria)`, `Zoroastrianism`, `Zuni (Pueblo)`.

This list reflects the actual data as of 2026-09-11; it is documentation of current scope,
not a hard enum enforced anywhere in code. See `sources.csv` and
`docs/data/DATA_QUALITY_REPORT.md` for counts.

### Reference (`source_ref`) conventions

Followed loosely, not enforced by the validator:

- Bible: `Book Chapter:Verse[-range]` (e.g. `Proverbs 15:1`)
- Qur'an: `Qur'an Surah#:Ayah#`
- Bahá'í Writings: book/tablet title (e.g. `Gleanings from the Writings of Baháʼu'lláh`)
- Hindu: `Book Chapter.Verse` (e.g. `Gita 2.47`)
- Buddhist: `Text Name, verse` (e.g. `Dhammapada, v. 1`)
- Sikh: `GGS, Ang <page>`
- Oral traditions: the named chant/speech/tradition where known, or `Oral Tradition` where not
  more specific.

### Tagging conventions

Comma-separated, lowercase, no spaces between tags, singular preferred (`virtue` not
`virtues`).

## A note on attribution for the Qur'an

Quotes are attributed to their central human figures (Jesus, The Buddha, Zarathushtra, etc.)
for data consistency. Islamic tradition holds the Qur'an is the literal, unauthored word of
God revealed through the Angel Gabriel to Prophet Muhammad — he is the messenger, not the
author. Qur'an rows are attributed to `Prophet Muhammad` as final recipient/conveyor; this is
a database classification choice, not a theological claim about authorship.

## Curation console

A static, dependency-free quote browser lives in `browser/`. See
`docs/architecture/QUOTE_BROWSER.md` for features and how to run it. It makes uncertainty
visible: every card shows its `item_type`, `verification_status`, and any data-quality issues
rather than presenting every row as settled scripture. It is also published on GitHub Pages
from the repo root: <https://mschwar.github.io/Garden-of-Wisdom/browser/index.html> (the bare
site root redirects there).

## Roadmap

See `docs/queue.md` for the current, living work queue and `docs/DECISIONS.md` for
append-only rationale on past calls. High-level phases:

- **Phase 0 (2026-09-11, done)**: encoding rehabilitation, schema additions
  (`item_type`/`verification_status`/`source_id`/`has_unresolved_glyph`), source-manifest
  linking, static browser.
- **Phase 1 (not started)**: human curation pass — resolve near-duplicates, fill manifest
  gaps, reclassify `unknown` item types.
- **Corpus program (2026-09-12, W0 done)**: doctrine and contracts for a provenance-aware,
  human-governed corpus — how a messy uncited candidate moves through capture → curation →
  research → possible canonical outcomes, which transitions need the operator, what counts as
  evidence, and the bounded W1 decomposition. **W1 is authorized in full (2026-09-12)** — see
  `docs/DECISIONS.md` and `docs/queue.md`. Each W1 unit still lands its own branch, PR and
  independent QA, and the wave's stop point is the Gate B packet (W2 is not started). See
  `docs/program/README.md` (start with `docs/program/W0_GATE_REPORT.md` for the Gate A
  evidence). The corpus lifecycle does not change any current CSV or browser behaviour.
- **Later, not authorized yet**: verify a small donor set and export it for use by a separate
  project (`bahai-homepage`), without merging the two repos or coupling their schemas. See
  `docs/product/PRODUCT_DOCTRINE.md`.
