# Handoff — D6 near-duplicate curation (keep all 20)

**Branch:** `d6/near-duplicate-curation` · **Decision:** D6 (2026-09-12), executed 2026-09-16

## What this is

The human curation pass over the **20** corpus-wide near-duplicate pairs the validator reports
after issue #34 (13 same-specific-citation + 7 text-similarity, including 5 cross-tradition).
Rule: keep both rows for legitimate variant translations; only merge/remove accidental
duplication.

## What changed

| File | Change |
|---|---|
| `docs/data/DATA_QUALITY_REPORT.md` | new dated "Curation 2026-09-16 (D6)" section + top-note; prior transcripts byte-identical |
| `docs/queue.md` / `docs/DECISIONS.md` | D6 marked done + executed entry |
| `GARDEN_D6_HANDOFF.md` | this file |
| `quotes.csv` / `sources.csv` | **untouched** (`9766db8c…` / `7aafcb67…`) |

## Disposition

**20 / 20 KEEP BOTH. 0 merges. 0 deletes.**

Operator explicitly kept the three borderline same-passage pairs:

| pair | texts (abbrev.) | ruling |
|---|---|---|
| `201 ~ 306` | Yasna 30:9 renovation line, two English renderings (sim 0.86) | KEEP BOTH — variant translations |
| `209 ~ 301` | Yasna 43:1 happiness-for-others, two English renderings (sim 0.82) | KEEP BOTH — variant translations |
| `73 ~ 240` | Deuteronomy 30:19 "Choose life." vs the full verse | KEEP BOTH — mnemonic + full |

All other pairs are different excerpts from one citation, cross-tradition parallels, adjacent
verses, or threshold noise — see the disposition table in
`docs/data/DATA_QUALITY_REPORT.md` → "Curation 2026-09-16 (D6)".

## Evidence

### Validator (fresh)

```
near-duplicate candidates: 20 (corpus-wide)
… (same 20 pairs as the #34 transcript) …
RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
```

CSV sha256 unchanged: quotes `9766db8c…` / sources `7aafcb67…`.

### What "done" means here

D6 is a *curation* unit, not a detector change. Closing it means every flagged pair has an
operator disposition. The WARN list remaining at 20 is expected and correct.

## What this unit deliberately did not do

- Delete or merge any `quotes.csv` row.
- Silence or suppress reviewed pairs in `validate_quotes.py`.
- Add a browser duplicate-review view (optional infra item; CLI + table were sufficient).
- Touch the `_`-glyph rows, remaining `unknown` item_types, D9, or W2.

## Exact next authorized action

`docs/queue.md` authorized-queued still leads with **D9 (H2B-B)** — work lives in
`bahai-homepage`, not this repo. Remaining Garden-side open items are mostly operator-gated
(`_`-glyph rows; remaining `unknown` item_types) or need a named contract (#27 AGENTS.md,
#30 withdrawal, #6 Bahá'í audit, #4 `source_url`). Re-confirm with `gh issue list --state open`.
W2 remains unauthorized.

## Review status

Same-session authoring and verification (no independent reviewer). The disposition table is the
review surface; a foreign pass can re-read the 20 pairs against it without re-deriving the list.
