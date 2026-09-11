# Archaeology Findings — 2026-09-11

Re-testing the "important observations to verify" from the Phase 0 prompt against the repo
itself, before any change.

## Git history

```
1e90d5f Initial commit
94aff1a Update README.md
51e838f Update README.md
da068c6 Feat: Add 325 quotes and refine data conventions
689463b Update README.md
13262fb feat: Add source manifest and project roadmap
b2c30b6 Merge branch 'main' of https://github.com/mschwar/Garden-of-Wisdom
ef38aca Update README.md
```

8 commits total prior to this retrofit, all 2025-era. The repo has always contained only
`README.md`, `quotes.csv`, `sources.csv`, and a tracked `.DS_Store` — confirmed, nothing else
existed.

## Encoding

**Confirmed false**: the previous README's claim that data was UTF-8. Both `quotes.csv` and
`sources.csv` are Mac OS Roman (`decode('utf-8')` fails at the first non-ASCII byte in each;
`decode('mac_roman')` succeeds cleanly and produces correct diacritics, e.g. byte `0x87` →
`á`). This is why GitHub's web renderer showed mojibake for names like "Bahá'u'lláh" — GitHub
assumes UTF-8.

Separately, and NOT an encoding issue: 4 rows contain a literal ASCII underscore (`0x5F`)
character where a diacritic or modifier letter belongs (e.g. `Bahá_u'lláh` — the underscore
stands in for U+02BC MODIFIER LETTER APOSTROPHE or similar, which the original author
apparently couldn't type or paste). Re-decoding does not fix this; it was typed as `_`
literally. Rows: 1, 16, 314, 320.

## Row counts and ID integrity

- 324 quote rows (not 325 as one commit message claims — that commit message counted something
  slightly differently, e.g. before a later edit; not investigated further, doesn't matter for
  data integrity).
- IDs run 1–344, are all unique, all parse as integers. Two non-contiguous gaps confirmed:
  250→261 (11 IDs missing) and 290→301 (10 IDs missing). No evidence in git history of deleted
  rows in those ranges — most likely IDs were reserved/skipped during original authoring and
  never backfilled. Left as-is per instruction to preserve legacy IDs even when non-contiguous.

## Tradition / distribution

27 distinct `tradition` values against a README-documented controlled list of 7. The 20 extra
values are Sikhism (26 quotes — a full extra major tradition, not a typo) plus 19 distinct
Indigenous American and African oral-tradition labels (11 Diné, 3 Hopi, 2 Haudenosaunee, 2
Yoruba, 2 Nahua, and 15 traditions with exactly 1 quote each). See
`docs/data/DATA_QUALITY_REPORT.md` for the full distribution.

## Malformed rows

`quotes.csv`: none — every row has exactly 6 fields after correct CSV parsing.

`sources.csv`: real bug found. The `notes` column contains **unescaped commas** in the
original file (never wrapped in quotes), so naive CSV parsing fragments long notes across
extra trailing columns and a naive fixed-width truncation (an early version of the
rehabilitation script did exactly this) **silently drops the end of the notes text**. Fixed by
rejoining any fields beyond the header count back into `notes`. This is also why the header
row itself has trailing empty column names (`,,,,`) in the original file — ragged from the
same underlying issue.

## Duplicate / near-duplicate candidates

Confirmed the examples named in the prompt: `Gita 2.47` (2 rows), `Dhammapada v.1` and several
other Dhammapada verses (multiple rows per verse), `Yasna 43:1` (3 rows). 0 exact-text
duplicates found; all near-duplicates are same-citation, different-wording — i.e. plausible
variant translations, not copy-paste errors. Full list and a false-positive caveat (generic
`"Oral Tradition"` source_ref causing spurious matches) are in
`docs/data/DATA_QUALITY_REPORT.md`.

## Source manifest quality

`sources.csv` had 18 rows before this retrofit, one non-integer `source_id` (`7.1`, Hadith
collections — left as-is, renumbering would only churn IDs for no benefit). Quote rows were
**not** linked to `sources.csv` by ID before this retrofit — only a shared free-text
`tradition` column existed, which is not enough to disambiguate (e.g. Judaism spans three
different `sources.csv` rows: Talmud, Bible, Pirkei Avot). This retrofit adds a `source_id`
foreign key to `quotes.csv`, resolved by matching `source_ref` text against `sources.csv`
title/keyword patterns (see `scripts/rehabilitate_2026_09_11.py`). 14 rows remain unresolved —
genuine manifest gaps, documented in `docs/data/DATA_QUALITY_REPORT.md`, not silently guessed.

## Rights / provenance risk

Not deeply assessed in this phase (out of scope for Phase 0 per the prompt's boundaries).
Surface observation: `sources.csv`'s own notes already flag several sources as copyrighted
(Black Elk Speaks, Official Baha'i Writings, Official Sikh Writings) and route to non-Gutenberg
resources. No new risk introduced by this retrofit — no source text was added, only the
existing quote/citation/attribution data was re-encoded and relinked.

## Quote-type / attribution ambiguity

Exact passages, excerpts, and oral-tradition attributions were mixed with no field to
distinguish them before this retrofit. Added `item_type` as a heuristic, provisional
classification (`full-passage` / `excerpt` / `paraphrase` / `oral-attribution` / `unknown`) —
see `docs/data/DATA_CONTRACT.md` for exactly how it's derived and its limits. No row was
individually hand-verified; this phase explicitly excludes that (see `docs/queue.md`).
