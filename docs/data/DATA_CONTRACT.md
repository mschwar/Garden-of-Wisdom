# Data Contract

## Files

- `quotes.csv` — canonical, UTF-8, one row per quote. Current working data.
- `sources.csv` — source manifest: what texts quotes are drawn from, and where to find them.
- `data/archive/2026-09-11/quotes.original.csv`, `sources.original.csv` — frozen legacy bytes
  (Mac OS Roman encoded), preserved exactly as found before the 2026-09-11 retrofit. Never
  edit. `scripts/rehabilitate_2026_09_11.py` documents exactly how the canonical files were
  derived from these, and can be re-run (it always reads from the archive, never from its own
  output).

## `quotes.csv` schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | integer | yes | Legacy identifier from the 2025 CSV. Stable, non-contiguous (gaps at 250→261, 290→301 are original, not corruption). Never renumber. |
| `quote_text` | string | yes | The quote as transcribed. May contain a literal `_` where the original author placed a diacritic/modifier letter they couldn't type — see "Known data issues" below. |
| `tradition` | string | yes | Free-text tradition/culture label. See "Controlled list" below — as of this retrofit it is **not** actually controlled; 27 distinct values exist against a README that claimed 7. |
| `source_ref` | string | yes | Human-readable citation (verse, chapter, book, speech, etc). Format varies by tradition; see original README conventions, which remain a reasonable style guide even though they're descriptive, not enforced. |
| `author` | string | yes | Attributed speaker/author/collective (e.g. "Diné Oral Tradition"). |
| `tags` | string | yes | Comma-separated, lowercase, singular-preferred theme tags. |
| `item_type` | enum | yes (added 2026-09-11) | One of `full-passage`, `excerpt`, `paraphrase`, `oral-attribution`, `unknown`. Heuristically assigned during retrofit — see below. Not hand-verified per row. |
| `verification_status` | enum | yes (added 2026-09-11) | One of `unverified`, `verified`, `disputed`. Every row is `unverified` as of this retrofit. Only set to `verified` after checking against a real primary source. |
| `source_id` | string | no (added 2026-09-11) | Foreign key into `sources.csv`. Blank means "no confident manifest match" — see `docs/data/DATA_QUALITY_REPORT.md` for the current unresolved list; this is a real manifest gap, not a bug to silently patch with a guess. |
| `has_unresolved_glyph` | boolean string | yes (added 2026-09-11) | `"true"` if `quote_text`, `author`, or `source_ref` contains a literal `_` standing in for a character the original author couldn't type. Flags rows that need a human with the right keyboard/reference to fix properly. |

### `item_type` heuristic (not authoritative)

Assigned by `scripts/rehabilitate_2026_09_11.py` at retrofit time:
- `oral-attribution` if `tradition` is one of the oral-tradition cultures listed in
  `sources.csv` notes (Diné, Haudenosaunee, Hopi, Oglala Lakota, and similar).
- `excerpt` if `source_ref` contains a digit or a colon (implies a pinpoint verse/chapter
  reference rather than a whole-work citation).
- `unknown` otherwise.

This is a first-pass signal for the curation queue, not a verified classification. 22 rows are
currently `unknown`.

### Controlled list status

The original README declared a 7-value controlled tradition list (`Baha'i`, `Buddhism`,
`Christianity`, `Hinduism`, `Islam`, `Judaism`, `Zoroastrianism`). The actual data has 27
distinct tradition values, including Sikhism and 19 distinct Indigenous American and African
oral-tradition labels. The README's list was stale, not the data wrong — see
`docs/audit/2026-09-11/FINDINGS.md`. This retrofit does **not** collapse those 27 values back
to 7; it documents them as the real controlled list going forward (see canonical `README.md`).

## `sources.csv` schema

| Field | Notes |
|---|---|
| `source_id` | Mostly integer strings; one value (`7.1`, Hadith collections) is not an integer. Left as-is — renumbering would break existing `quotes.csv` links for no data-quality benefit. |
| `source_title`, `tradition`, `gutenberg_search_term`, `notes` | Free text. `notes` previously contained unescaped commas that fragmented across extra CSV columns in the legacy file (a real malformed-CSV bug, not stylistic) — this retrofit rejoins them into one properly quoted field. |

## Known data issues (see `docs/data/DATA_QUALITY_REPORT.md` for exact current counts)

1. **Legacy encoding**: original `quotes.csv`/`sources.csv` were Mac OS Roman, not UTF-8 as the
   old README claimed. Fixed by re-decoding from the archived original bytes.
2. **Underscore-as-placeholder**: a small number of rows use a literal `_` where a diacritic or
   modifier letter (e.g. the modifier apostrophe in Baháʼu'lláh, a macron/dot-under letter in a
   Lakota word) should be. This is original authoring behavior, not a decode artifact — the
   underlying byte is a real ASCII `_` (0x5F). Not silently replaced with a guessed glyph.
3. **Near-duplicate / variant records**: multiple rows cite the same verse (e.g. `Gita 2.47`,
   several `Yasna 43:1` renderings, several `Dhammapada v.1`/`v.277`-style entries). These look
   like different translations of the same source rather than errors, but that needs a human
   curation pass, not automatic deduplication.
4. **Unresolved source links**: 14 quote rows cite a source_ref that doesn't match any
   `sources.csv` entry closely enough to link confidently (mostly small oral traditions with no
   manifest row yet, plus `Mahabharata` and one `Various Sutras (paraphrased)` row). Real gap,
   not a linking bug.
