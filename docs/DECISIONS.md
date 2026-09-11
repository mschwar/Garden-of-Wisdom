# Decisions

Append-only. Add new entries at the bottom with a date. Don't edit or delete past entries even
if later superseded — add a new entry that supersedes the old one and say so.

## 2026-09-11 — Rehabilitate encoding by re-decoding, not by string-replacing mojibake

The original files were Mac OS Roman, not UTF-8. Decided to re-decode the archived original
bytes with the correct codec rather than pattern-matching and replacing mojibake sequences in
the (already-decoded-wrong) text, because the former is a provable, lossless transform and the
latter risks silently "fixing" text that only looks like mojibake by coincidence.

## 2026-09-11 — Do not guess the glyph behind literal `_` placeholders

4 rows use a literal ASCII `_` where a diacritic/modifier letter belongs. Decided not to
replace it with a guessed correct character, even though the likely intent is often obvious
(e.g. Bahá_u'lláh → Baháʼu'lláh), because that crosses from encoding restoration into
editorial judgment about source text. Flagged instead via `has_unresolved_glyph` for a human
to fix with the right reference.

## 2026-09-11 — Link `source_id` by matching `source_ref` keywords, not by `tradition`

Considered mapping each `tradition` value to a single `sources.csv` row. Rejected: several
traditions (Judaism, Christianity) legitimately span multiple manifest entries (Talmud vs.
Bible vs. Pirkei Avot), so a tradition-level mapping would silently misattribute many rows.
Matched on substrings of `source_ref` against known titles/keywords instead, leaving `source_id`
blank where no confident match exists rather than falling back to a coarser, wrong guess.

## 2026-09-11 — Keep the 27-value tradition list as-is rather than collapsing to the old 7

The pre-retrofit README declared 7 traditions; the actual data has always had 27 (including
Sikhism and 19 Indigenous/African oral-tradition labels). Decided the data reflects real
project scope and the README was simply out of date, not the reverse — updated the canonical
README's list to match the data instead of trimming the data to match the README.

## 2026-09-11 — Ship the quote browser as a single-page vanilla JS app, no CSV library

Considered pulling in a CSV parsing library (e.g. PapaParse) for robustness. Decided a small
hand-rolled RFC4180-ish parser in `browser/app.js` is sufficient for this dataset's shape and
keeps the "no framework unless demonstrably necessary" constraint from
`docs/product/PRODUCT_DOCTRINE.md` / the originating work-unit prompt. Revisit if quote data
grows pathological embedded-quote/newline cases the hand-rolled parser mishandles.

## 2026-09-11 — Approved donor set for the homepage preview export: Garden ids [3, 12, 15, 26, 30]

Three candidate donor-set options were proposed for
`bootstrap/seed/2026-09-11-garden-2026-retrofit/prompts/02_GARDEN_VERIFY_AND_EXPORT_HOMEPAGE_PREVIEW.txt`'s
`APPROVED_GARDEN_IDS`: (A) the safest/most-famous, least-ambiguous Bahá'í passages; (B) a set
deliberately diverse across citation shapes and source works, to stress-test the export
mechanics; (C) a set including one deliberate Hidden Words item, to test collision handling
against the homepage's existing Hidden Words corpus. Chose **option A** — ids 3, 12, 15, 26, 30
— because this is a first "tiny preview" export whose job is proving the verify→export pipeline
works at all, not stress-testing edge cases yet. All five resolve cleanly to `source_id 12`
("Official Baha'i Writings"), none carries `has_unresolved_glyph`, none appears in any
near-duplicate candidate pair (`docs/data/DATA_QUALITY_REPORT.md`), and none is drawn from The
Hidden Words. Options B and C are deferred to a later, deliberate follow-up export, not rejected.
