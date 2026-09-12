# bahai-homepage preview collection — v1

Versioned Garden export that conforms to the accepted `bahai-homepage` H2B-A
collection contract (`docs/architecture/COLLECTION_CONTRACT.md` in that repo,
accepted as D27).

**Consume this file:** `exports/bahai-homepage-preview/v1/collection.json`

Do not live-read `quotes.csv` from `bahai-homepage`. This directory is the seam.

## What it is

A four-item Bahá’í-only preview. Garden ids `[3, 12, 15, 26]` accepted; id `30`
rejected (see `REVIEW.md`). None are Hidden Words.

| Field | Value |
|---|---|
| `collection_id` | `garden-homepage-preview` |
| `schema_version` | `1` |
| `version` | `1` |
| `producer` | `garden-of-wisdom` |
| `default_eligibility` | `{"max_words": 75}` |
| SHA-256 of `collection.json` | `85fa2f6b2882633a683b7449f9e4daf650f78b5ee28faf9e59dbff52222d6bd5` |

Recompute the hash after any rewrite:

```
shasum -a 256 exports/bahai-homepage-preview/v1/collection.json
```

## Regenerate / validate

From repo root:

```
python3 scripts/export_homepage_preview.py
python3 scripts/validate_homepage_preview_export.py
python3 scripts/validate_quotes.py
```

The exporter reads `quotes.csv` plus `mapping.json`. It will refuse to emit if an
accepted donor’s `quote_text` has drifted from the verified snapshot.

## Contract mapping (Garden → H2B item)

| Garden | Collection item |
|---|---|
| `id` | `upstream_id` (string) and `item_id` `garden-<id>` |
| `quote_text` | `text` (only after word-for-word verification) |
| `author` | `author` |
| `source_ref` | `source_ref` (export may use a fuller locator than the CSV) |
| `item_type` | `item_type` (reclassified at verify time; not the Phase 0 heuristic) |
| `verification_status` | `verification_state` (name differs; mapped here, not renamed in Garden) |
| `tags` (CSV string) | `tags` (JSON array) |
| (none) | `source_url` |

## Out of scope

Homepage wiring, the Hidden Words migration path, and any change to
`bahai-homepage` itself. Those belong to that repo’s H2B-B work unit.
