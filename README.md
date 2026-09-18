# A Garden of Wisdom

A personal, curated Garden of **passages worth keeping** — religious, philosophical, literary,
scientific, artistic, historical, oral/cultural, or otherwise personally meaningful — for
rediscovery, understanding, comparison, memorization, and reflection.

The idea is inspired by the Bahá'í passage "A kindly tongue is the lodestone of the heart of
men," but the current religious/philosophical corpus is the **seed inventory**, not the permanent
product boundary.

The durable product object is **Passage**; “quote” remains a legacy CSV/browser term. Uncertainty
and provenance stay visible rather than being polished away.

See `docs/product/PRODUCT_DOCTRINE.md` for stable product boundaries,
`docs/PRODUCT_REALITY.md` for the standing answer to what actually works and where use breaks,
and `AGENTS.md` if you're an agent picking up work here.

## Where are we now?

Standing product/system reality lives in `docs/PRODUCT_REALITY.md`. Live programme execution
status is **not** duplicated here — it lives in
`docs/program/usability-closure/CURRENT.md` (current gate, the single READY unit, the last
completed unit, the frontier). If this file and CURRENT disagree about status, CURRENT wins.
In one paragraph, as of 2026-09-17:

- The **legacy corpus** is the 324-row `quotes.csv` / `sources.csv` pair; the static browser
  and the homepage-preview export read it.
- The **candidate workbench is real and landed**. The corpus-program W1 wave — capture →
  normalization → duplicate hints → operator curation — shipped in `scripts/garden_*.py` over
  a persisted SQLite store plus the committed mirror `data/store/garden.export.txt`, with a
  deterministic acceptance suite per surface and a committed table of negative controls. W1 is
  **complete** and its Gate B packet was accepted 2026-09-13.
- W2 and everything after it are **not** started. Current work is the bounded
  **usability-closure programme** (`docs/program/usability-closure/`), which closes the loop
  from an eligible candidate to the Garden-facing browser. Its READY unit is whichever unit
  CURRENT.md names — read that file, not this paragraph.

## Status — data (as of the 2026-09-11 retrofit)

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
python3 scripts/garden_store.py bootstrap --dir data/store   # hydrate the local store from the committed mirror
python3 scripts/garden_store.py status    --dir data/store   # CURRENT / STALE / MISSING_DB / MISSING_MIRROR
python3 scripts/check_front_door.py                    # front-door docs still describe current state
python3 scripts/smoke_quote_browser.py                 # drive the browser in headless Chromium
python3 -m http.server 8000                            # then open http://localhost:8000/browser/
```

The smoke test needs a one-time `python3 -m pip install -r requirements-dev.txt` and
`python3 -m playwright install chromium`; it is the only command above that is not stdlib-only.

The corpus workbench (`garden_submit.py` → `garden_normalize.py` → `garden_review.py`, the
`check_garden_*.py` acceptance suites, the D3/D4 ledger and batch feeds, and the
negative-control harness) is documented command by command in `docs/RUNBOOK.md`, and `AGENTS.md`
lists the full command surface for an agent picking this up cold.

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
- **Phase 1 (curation, partly executed as named data units)**: the human-curation work has
  been landing as named units rather than as one phase — D3 (the `unverifiable` side-car
  ledger, live instance Garden id 30), D4 (one batch capture for the 324 legacy rows), D6 (all
  20 near-duplicate pairs reviewed, kept), D7 (14 dangling `source_id` links closed in
  `sources.csv`), D8 (`item_type` hygiene plus the 27-tradition controlled list). Still open
  and operator-gated: the 4 literal `_` placeholder glyph rows (ids 1, 16, 314, 320), the
  remaining `unknown` `item_type` rows, and any bulk verification. See `docs/queue.md`.
- **Corpus program (2026-09-12 →)**: doctrine and contracts for a provenance-aware,
  human-governed corpus — how a messy uncited candidate moves through capture → curation →
  research → possible canonical outcomes, which transitions need the operator, and what counts
  as evidence. **W0 done** (Gate A accepted; start at `docs/program/W0_GATE_REPORT.md`) and
  **W1 complete** — the six W1 units are merged, their acceptance suites and the
  negative-control table are CI-wired, and the Gate B packet was accepted 2026-09-13. The
  runtime is `scripts/garden_*.py` over the store plus the committed mirror. **W2 is not
  started.** The corpus lifecycle changes no CSV or browser behaviour. See
  `docs/program/README.md` for the doctrine map.
- **Usability-closure programme (2026-09-17 →)**: the bounded bridge from the landed W1
  workbench to real use — `encounter → capture → normalize → curate → admit → Garden read
  model → browser → rediscover later`. U0.1/U0.2 landed; R0 then reconciled the product around
  the Passage domain object and the Garden/Initiate boundary before a real canary was persisted.
  Gate U0 remains the active gate; U1 is unauthorized until Gate U0 is accepted. See
  `docs/PRODUCT_REALITY.md` and `docs/program/usability-closure/PROGRAM_CHARTER.md`.
- **Later, not authorized yet**: verify a small donor set and export it for use by a separate
  project (`bahai-homepage`), without merging the two repos or coupling their schemas. See
  `docs/product/PRODUCT_DOCTRINE.md`.
