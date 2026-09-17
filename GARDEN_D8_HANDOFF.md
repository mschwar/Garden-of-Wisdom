# Handoff — D8 legacy item_type hygiene + the 27-tradition controlled list

**Branch:** `d8/item-type-hygiene` · **Decision:** D8 (2026-09-12), executed 2026-09-16

## What this is

The cheap deterministic subset of legacy `item_type` hygiene: retype the five Roman-numeral
**Gleanings** rows still in `item_type = unknown` → `excerpt` (the "digit or `:` → excerpt"
heuristic missed Roman numerals), retype the two paraphrase-shaped rows → `paraphrase`, and
document the 27-value `tradition` list as the controlled list. `item_type` is **not** widened;
the four `_`-glyph rows stay operator-gated.

## What changed

| File | Change |
|---|---|
| `quotes.csv` | 7 `item_type` cells retyped (byte-surgical, nothing else touched) |
| `README.md` | §"Traditions in use" now enumerates all 27 values as the controlled list |
| `docs/program/fixtures/w0_scenarios.json` | `item_type_counts` re-derived in the same unit |
| `docs/data/DATA_QUALITY_REPORT.md` | new dated "Re-derivation 2026-09-16 (D8)" section; prior transcripts byte-identical |
| `docs/queue.md` / `docs/DECISIONS.md` | D8 items marked done + executed entry |
| `GARDEN_D8_HANDOFF.md` | this file |

## The retypes

| id | source_ref | old | new |
|---|---|---|---|
| 4 | Gleanings, CV | unknown | excerpt |
| 7 | Gleanings, CLIII | unknown | excerpt |
| 14 | Gleanings, CV | unknown | excerpt |
| 22 | Gleanings, CXXI | unknown | excerpt |
| 285 | Gleanings, CXXXV | unknown | excerpt |
| 31 | The Chosen Highway, p. 167 | excerpt | paraphrase |
| 267 | Various Sutras (paraphrased) | unknown | paraphrase |

`item_type` counts: `{unknown: 20, excerpt: 270, oral-attribution: 34}` →
`{unknown: 14, excerpt: 274, paraphrase: 2, oral-attribution: 34}`.

## Rulings held

- `item_type` enum **not** widened.
- `_`-glyph rows (ids 1, 16, 314, 320) left for the operator — guessing stays forbidden.
- The other `unknown` rows (Tablets-of-Bahá'u'lláh 5/19/23/25, Sutta rows 261/262/268/270,
  164/188/213/304) are **not** part of D8's cheap deterministic subset — they need real
  classification judgment and were left untouched.
- `quotes.csv` changed (7 cells only); `sources.csv` byte-identical (`7aafcb67…`).

## Evidence

### Validators (all 12, both interpreters where applicable)

```
validate_quotes.py                  PASS
check_program_contracts.py          PASS
validate_homepage_preview_export.py PASS
check_pages_contract.py            PASS
check_garden_store.py              PASS
check_garden_envelope.py           PASS
check_garden_submit.py             PASS
check_garden_normalize.py          PASS
check_garden_review.py             PASS
check_garden_ledger.py            PASS
check_garden_legacy_batch.py      PASS
check_garden_e2e.py               PASS
```

`validate_quotes.py` PASS under both Homebrew 3.14.5 and CI's 3.12.

### Browser smoke

```
.venv/bin/python scripts/smoke_quote_browser.py
→ RESULT: PASS (0 warning(s))
```

### Negative controls (full harness)

```
checkers: 13 of 13 selected, 0 skipped
controls: 39 fired, 0 not fired of 39 selected (39 registered in the table)
harness self-tests: 9 of 9 passed
RESULT: PASS (39 controls fired, 9 harness self-tests) [negative controls]
```

### CSV byte-identity

`quotes.csv` changed (the 7 retypes, verified by `git diff` to be only `item_type` cells).
`sources.csv` `7aafcb67…` (unchanged).

## What this unit deliberately did not do

- Widen the `item_type` enum.
- Touch the `_`-glyph rows (operator-gated).
- Reclassify the non-deterministic `unknown` rows (need human judgment).
- Start D6 (near-duplicate curation — human-gated per AGENTS.md), D9 (bahai-homepage lane), or W2.

## Exact next authorized action

`docs/queue.md` authorized-queued still leads with **D9 (H2B-B)** — work lives in
`bahai-homepage`, not this repo. Remaining Garden-side open items that are not operator-gated:
**D6** (near-duplicate curation — human look) and the optional follow-on of wiring the five #45
gap mutations into the negative-control table as registered controls. Re-confirm with
`gh issue list --state open`. W2 remains unauthorized.

## Review status

Same-session authoring and verification (no independent reviewer). The operator may still want
a foreign pass on the retype set and the README enumeration.
