# Handoff — D4 legacy batch capture for the 324-row rehabilitation import

**Branch:** `d4/legacy-batch-capture` · **Decision:** D4 (2026-09-12), executed 2026-09-16

## What this is

The 324 legacy `quotes.csv` rows have no reconstructable per-row encounter. Decision D4
gives them **ONE batch capture** for the 2026-09-11 rehabilitation import — a true,
verifiable statement about the frozen archive + documented transform — plus a membership
side-car so every legacy row id has uniform provenance. Not 324 synthetic captures. Not
store candidates.

## What changed

| File | Change |
|---|---|
| `scripts/garden_store.py` | migration `0003_legacy_batch_capture`; `LEGACY_BATCH_*` constants; `seed_legacy_batch_capture` / `legacy_batch_capture` / `legacy_batch_membership`; export/import/counts updated |
| `scripts/garden_legacy_batch.py` | **new** — CLI `seed` / `show` / `verify` |
| `scripts/check_garden_legacy_batch.py` | **new** — acceptance + evidence run |
| `scripts/check_garden_store.py` | three-migration schema assertions |
| `scripts/check_garden_ledger.py` | three-migration + new export section in order assertion |
| `scripts/run_negative_controls.py` | +3 controls (`b1`–`b3`); `EXPECTED_CONTROLS` 36 → 39 |
| `.github/workflows/browser-smoke.yml` | runs `check_garden_legacy_batch.py` in the W1 suites step |
| `data/store/garden.export.txt` | seeded: 1 batch capture + 324 membership rows (D3 id-30 ledger row preserved) |
| `docs/program/D4_LEGACY_BATCH_CAPTURE.md` | design doc |
| `docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md` | legacy-corpus section updated for D4 |
| `docs/program/CORPUS_PROGRAM_DOCTRINE.md` | R3 updated for D4 |
| `docs/architecture/NEGATIVE_CONTROLS.md` | 39 / 13 |
| `docs/RUNBOOK.md` | D4 command surface |
| `docs/queue.md` / `docs/DECISIONS.md` | closed + executed entries |
| `GARDEN_D4_HANDOFF.md` | this file |

## Rulings this unit owns

1. **One capture, fixed body.** `cap-2026-09-11-legacy-batch`; body is constants, not
   caller-supplied, so two seeds cannot drift on wording.
2. **Membership side-car, not candidates.** Same posture as D3: legacy rows are not store
   candidates and may never be.
3. **Idempotent seed; conflicting state refused.** Exact same set → no-op; anything else →
   refuse before writing.
4. **Export header stays `/1`.** Additive section, same ruling as D3.
5. **`quotes.csv` / `sources.csv` untouched.**

## Evidence

### Acceptance

```
python3 scripts/check_garden_legacy_batch.py
→ RESULT: PASS
```

### Live seed + verify

```
python3 scripts/garden_legacy_batch.py verify --dir data/store
→ verified cap-2026-09-11-legacy-batch against 324 quotes.csv ids and archive digests
→ RESULT: PASS
```

Store counts after seed: `captures=1`, `legacy_batch_membership=324`, `legacy_verification=1`
(D3 id 30), `decisions=1`, candidates/hints empty.

### CSV byte-identity

`quotes.csv` `b3bb7848…` · `sources.csv` `7aafcb67…` (unchanged throughout).

### Negative controls (3)

| id | mutation | first FAIL |
|---|---|---|
| b1 | conflicting-membership guard disabled | `a conflicting membership set was accepted` |
| b2 | seed also inserts a candidate | `seed creates no candidates … candidates': 1 …` |
| b3 | export-order assertion drops membership section | `the export sections appear in the documented fixed order -- […, '[legacy_batch_membership]']` |

```
python3 scripts/run_negative_controls.py --checker scripts/check_garden_legacy_batch.py
→ RESULT: PASS (3 controls fired, 9 harness self-tests)
```

### Standing suites re-run clean (author session)

- `check_garden_store.py` → PASS
- `check_garden_ledger.py` → PASS
- `check_program_contracts.py` → PASS
- `validate_quotes.py` → PASS
- store `g1`–`g3` negative controls → PASS (g3 updated for 0003)

## What this unit deliberately did not do

- Create store candidates for the 324 rows.
- Invent per-row capture text.
- Touch `quotes.csv` / `sources.csv`.
- Start D9 (bahai-homepage consume lane) or W2.
- Edit `AGENTS.md` (still policy-blocked; #27).

## Exact next authorized action

`docs/queue.md` authorized-queued now leads with **D9 (H2B-B)** — work lives in
`bahai-homepage`, not this repo. Remaining Garden-side open items that are not
operator-gated: D6 (near-duplicate curation — human look), D8 (cheap `item_type` retypes +
document the 27-tradition list), and the optional follow-on of wiring the five #45 gap
mutations into the negative-control table as registered controls. Re-confirm with
`gh issue list --state open`. W2 remains unauthorized.
