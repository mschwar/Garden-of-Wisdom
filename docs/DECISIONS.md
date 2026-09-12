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

## 2026-09-11 — Phase 0 frontier review: accept with documented debt

Independent re-check of G0–G3 (encoding bytes, rehab/validate scripts, CSVs vs archived
originals, live browser). Full write-up: `docs/audit/2026-09-11/PHASE0_FRONTIER_REVIEW.md`.

Accepted. No data-integrity reason to revert PR #1. Encoding diagnosis (Mac OS Roman → UTF-8)
is evidenced, not asserted; 324/324 core fields match the mac_roman-decoded originals; literal
`_` placeholders were not "fixed." `item_type` is a heuristic queue signal, not an export
classification — Roman-numeral Gleanings citations (including donor ids 3 and 15) landed in
`unknown`, and paraphrase-shaped rows 31 and 267 were not typed `paraphrase`. A future H2B
export must reclassify `item_type` at verification time, map `verification_status` →
`verification_state`, and record `source_url` then. Do not live-read `quotes.csv` from
`bahai-homepage`.

## 2026-09-11 — Donor-set near-dupe claim was false for id 3 (supersedes the "none appears" sentence above)

The donor-set entry above said ids 3/12/15/26/30 appear in no near-duplicate candidate pair.
Validator output flags `3 ~ 283` (text similarity 0.74): “The earth is but one country, and
mankind its citizens.” (Bahá’u’lláh, Gleanings CXVII) vs “The earth is one home and mankind
its family.” (‘Abdu’l-Bahá, Selections 255). Different author, different work, similar
teaching — not a reason to drop id 3 from the donor set, but the “none appears” claim is
false and must not be used as a verification/export gate. Ids 12, 15, 26, 30 are still
unflagged.

## 2026-09-11 — G4: verify approved donors; export four; reject id 30; correct two locators

Executed Prompt 02 against the accepted H2B-A contract (bahai-homepage D27). Approved set
stayed `[3, 12, 15, 26, 30]`.

Accepted, wording exact on bahai.org: 3 (Gleanings CXVII), 12 (Tablet of ‘Abdu’l-Bahá),
15 (Gleanings CXXII), 26 (Promulgation of Universal Peace, 12 April 1912). All four classified
`excerpt` and `verified` in `quotes.csv`. Export:
`exports/bahai-homepage-preview/v1/collection.json`.

Rejected: id 30 — sentence not found; Paris Talks has no 2 December 1911 meeting. Left
`unverified`; omitted from the collection (no paraphrase as scripture).

Explicit CSV corrections, quote text untouched: id 12 author `Bahá’u’lláh` → `‘Abdu’l-Bahá`
and `source_ref` retargeted from ADJ p. 22 to the tablet (ADJ is the secondary print
witness); id 26 `source_ref` retargeted from Paris Talks 22 Oct 1911 (the “Sun of Truth”
talk, which does not contain the sentence) to PUP 12 April 1912. Ids 3 and 15 only changed
`item_type` `unknown` → `excerpt` (Roman-numeral heuristic miss).

Did not add a `source_url` column to Garden; URLs live on the export. Did not rename
`verification_status` to `verification_state`; mapped at export time.
