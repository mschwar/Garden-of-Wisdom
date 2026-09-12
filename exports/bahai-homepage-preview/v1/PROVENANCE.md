# Provenance — garden-homepage-preview v1

Verified 2026-09-11 against the Bahá’í Reference Library at bahai.org. Garden
legacy ids are the upstream identity. Quote wording in `quotes.csv` was not
silently rewritten; two locators/attributions were corrected in the CSV with
this note as the record.

Primary texts are copyright © Bahá’í International Community
(<https://www.bahai.org/legal>).

## How verification was done

For each approved Garden id `[3, 12, 15, 26, 30]`:

1. Read the Garden row (`quote_text`, `author`, `source_ref`).
2. Locate the work on the current Bahá’í Reference Library (`bahai.org/library`),
   not a third-party quote site.
3. Compare Garden wording to the official English text.
4. Check author and locator.
5. Classify `item_type` from the primary text (excerpt vs full passage vs
   paraphrase).
6. Accept only if the Garden sentence appears verbatim in the official source
   and can be attributed cleanly. Record mapping when Garden’s citation was
   wrong but the wording was exact.

Machine-readable verdicts: `mapping.json`. Human table: `REVIEW.md`.

## Authoritative links used

| Garden id | Official page |
|---|---|
| 3 | https://www.bahai.org/library/authoritative-texts/bahaullah/gleanings-writings-bahaullah/6 (Gleanings CXVII) |
| 12 | https://www.bahai.org/library/authoritative-texts/abdul-baha/additional-tablets-extracts-talks/826608209/826608209.xhtml |
| 15 | https://www.bahai.org/library/authoritative-texts/bahaullah/gleanings-writings-bahaullah/6 (Gleanings CXXII) |
| 26 | https://www.bahai.org/library/authoritative-texts/abdul-baha/promulgation-universal-peace/promulgation-universal-peace.xhtml (12 April 1912, Studio of Miss Phillips) |
| 30 | no matching official text; not exported |

Also consulted (supporting, not the export URL): the official Gleanings PDF;
`reference.bahai.org` Gleanings CXVII / CXXII; the Trustworthiness compilation
citation of *The Advent of Divine Justice* p. 26 (1984); Paris Talks TOC (last
1911 Paris meeting is 1 December).

## Corrections applied to Garden rows (explicit, not silent)

Quote `quote_text` was left unchanged for every donor.

- **id 12** — author `Bahá’u’lláh` → `‘Abdu’l-Bahá`. The sentence is from a
  Tablet of ‘Abdu’l-Bahá. Shoghi Effendi’s English of that clause is printed in
  *The Advent of Divine Justice*; Garden had cited ADJ p. 22 as if Bahá’u’lláh
  were the author, with an edition-dependent page (1984 ADJ is p. 26).
- **id 12** — `source_ref` updated to `Tablet of ‘Abdu’l-Bahá; cited in The Advent of Divine Justice`.
- **id 26** — `source_ref` `Paris Talks, Oct 22 1911` → `The Promulgation of Universal Peace, 12 April 1912`.
  Paris Talks 22 October 1911 is “The Sun of Truth” and does not contain the
  sentence. The sentence is in PUP, New York, 12 April 1912.
- **ids 3 and 15** — `item_type` `unknown` → `excerpt` (Roman-numeral Gleanings
  citations; Phase 0 heuristic miss). Wording and author unchanged.

## Rejection

**id 30** — `Prayer is the key of the doors of mercy.` / `Paris Talks, Dec 2 1911`.
No such sentence on the Reference Library. No 2 December 1911 Paris Talks
entry. Closest official wording is about meditation, not prayer, on a different
date. Left `unverified` in `quotes.csv`; omitted from `collection.json`.

## What this export is not

Not a rights clearance for commercial republication. Not a claim that the rest
of Garden is verified. Not a Hidden Words overlap test (deferred donor set C).
