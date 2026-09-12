# Garden Homepage Preview Export Handoff — 2026-09-11

Executed against
`bootstrap/seed/2026-09-11-garden-2026-retrofit/prompts/02_GARDEN_VERIFY_AND_EXPORT_HOMEPAGE_PREVIEW.txt`
on branch `feat/g4-homepage-preview-export`.

Gates were both true before this work started:

1. Garden Phase 0 accepted (`docs/audit/2026-09-11/PHASE0_FRONTIER_REVIEW.md`,
   `docs/DECISIONS.md`).
2. `bahai-homepage` H2B-A collection contract accepted as D27
   (`~/Developer/bahai-homepage/docs/architecture/COLLECTION_CONTRACT.md`,
   `docs/DECISIONS.md` D27, merged PR #25).

## Accepted / rejected donors

Approved set: `[3, 12, 15, 26, 30]`. No substitution.

| id | Verdict | Reason |
|---|---|---|
| 3 | **accept** | Exact Gleanings CXVII sentence. Author Bahá’u’lláh. Excerpt. |
| 12 | **accept** | Exact sentence; **author was Bahá’u’lláh in Garden, actually ‘Abdu’l-Bahá**. Locator was a secondary ADJ page cite. Mapped; CSV author/`source_ref` corrected explicitly. |
| 15 | **accept** | Exact Gleanings CXXII sentence. Author Bahá’u’lláh. Excerpt. |
| 26 | **accept** | Exact sentence; **work was Paris Talks 22 Oct 1911 in Garden, actually PUP 12 April 1912**. Mapped; CSV `source_ref` corrected explicitly. |
| 30 | **reject** | Wording not found on the Reference Library. No 2 Dec 1911 Paris Talks meeting. Would be a paraphrase (or a misremembered line) if emitted. |

Quote `quote_text` was not rewritten for any row.

## Exact authoritative links

- 3 / 15: https://www.bahai.org/library/authoritative-texts/bahaullah/gleanings-writings-bahaullah/6
- 12: https://www.bahai.org/library/authoritative-texts/abdul-baha/additional-tablets-extracts-talks/826608209/826608209.xhtml
- 26: https://www.bahai.org/library/authoritative-texts/abdul-baha/promulgation-universal-peace/promulgation-universal-peace.xhtml

Full notes: `exports/bahai-homepage-preview/v1/PROVENANCE.md` and `REVIEW.md`.

## Export version / hash

Path the homepage agent should consume:

```
exports/bahai-homepage-preview/v1/collection.json
```

- `collection_id`: `garden-homepage-preview`
- `schema_version`: `1`
- `version`: `1`
- items: 4 (`garden-3`, `garden-12`, `garden-15`, `garden-26`)
- SHA-256: `85fa2f6b2882633a683b7449f9e4daf650f78b5ee28faf9e59dbff52222d6bd5`

Also in this directory: `README.md`, `PROVENANCE.md`, `REVIEW.md`, `mapping.json`,
`SHA256SUMS`.

## Validation output

```
$ python3 scripts/export_homepage_preview.py
wrote exports/bahai-homepage-preview/v1/collection.json (4 items)

$ python3 scripts/validate_homepage_preview_export.py
collection: exports/bahai-homepage-preview/v1/collection.json
schema_version: 1
collection_id: garden-homepage-preview
items: 4
upstream_ids: ['3', '12', '15', '26']
rejected (not exported): ['30']
sha256: 85fa2f6b2882633a683b7449f9e4daf650f78b5ee28faf9e59dbff52222d6bd5

RESULT: PASS

$ python3 scripts/validate_quotes.py
parsed 324 quote rows, 10 columns: ['id', 'quote_text', 'tradition', 'source_ref', 'author', 'tags', 'item_type', 'verification_status', 'source_id', 'has_unresolved_glyph']
duplicate ids: none
id range: 1-344 (324 ids). non-contiguous gaps (expected, legacy IDs preserved): [(250, 261), (290, 301)]
missing required fields: none
exact duplicate quote_text groups: 0
near-duplicate candidates: 45
unresolved source links: 14 -> ids ['267', '275', '312', '315', '316', '317', '320', '333', '334', '335', '339', '342', '343', '344']
rows with unresolved glyph markers (literal '_' standing in for an untyped character): 4 -> ids ['1', '16', '314', '320']
counts by item_type: {'unknown': 20, 'excerpt': 270, 'oral-attribution': 34}
counts by verification_status: {'unverified': 320, 'verified': 4}
sources.csv: 18 rows, ids: ['1', '10', '11', '12', '13', '14', '15', '16', '17', '18', '2', '3', '4', '5', '6', '7.1', '8', '9']

RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
```

`item_type` unknown 22 → 20 because ids 3 and 15 were reclassified `excerpt`.
`verification_status` verified: 4.

## Contract friction

Recorded, not papered over:

1. **`verification_status` (Garden) vs `verification_state` (H2B).** Mapped at
   export time. Not renamed in Garden. H2B D27 already asked to reconcile before
   more code hardens either spelling.
2. **`tags` shape.** Garden CSV string → JSON array. Trivial; D27 already noted it.
3. **No `source_url` column in Garden.** Recorded only on the export (and in
   `mapping.json`). Adding a CSV column is a schema change for 324 rows — queued,
   not done here.
4. **Eligibility rule is still only `{max_words: 75}`.** All four accepted items
   are 7–11 words. A future “verified-only” rule would need `schema_version` 2 on
   the homepage side.
5. **Four items, not 6–12.** The owner-approved set was five; one failed
   verification. The prompt forbids substituting a different set.

## STOP

Verified export is done. Homepage wiring is a separate work unit in
`bahai-homepage` (H2B-B), still gated on that repo’s D26 owner decisions
(especially in-place vs new path for Hidden Words JSON). Do not modify
`bahai-homepage` from this repo.
