# Handoff — the five #45 checker-coverage gaps become registered controls

**Branch:** `harness/register-45-controls` · **Decision:** 2026-09-16 (see `docs/DECISIONS.md`)

## What this is

Issue #45's five checker-coverage gaps were closed inside the acceptance suites that own them
(PR #47), but the *mutations* that measure them were recorded only in
`GARDEN_CHECKER_COVERAGE_GAPS_HANDOFF.md` prose. That is the exact arrangement
`scripts/run_negative_controls.py` (issue #43) exists to replace: a guard whose only evidence is a
sentence in a handoff cannot be independently verified, and a later edit that silently deletes the
assertion leaves no trace anywhere. This unit registers all five as committed controls, so a
regression in any of them turns CI red by itself.

## What changed

| File | Change |
|---|---|
| `scripts/run_negative_controls.py` | five controls added (`g4`, `n4`, `r4`, `x3`, `l4`); `EXPECTED_CONTROLS` **39 → 44** (13 checkers, unchanged) |
| `scripts/check_garden_e2e.py` | the T-P7 audit-row assertion's `FAIL:` detail now names the recorded state instead of dumping the whole row (see below) |
| `docs/architecture/NEGATIVE_CONTROLS.md` | count paragraph, five table rows, the gaps section annotated, and a new limits rule (a `FAIL:` detail may not embed a wall-clock value) |
| `docs/RUNBOOK.md` | negative-controls section notes the table is 44 and names the five gap controls |
| `.github/workflows/browser-smoke.yml` | comment only: "all 36 negative controls" → "the whole negative-control table" (the count was already stale at 36 after D4) |
| `docs/queue.md` / `docs/DECISIONS.md` | #45 entry annotated; new closed section + decision entry |
| `GARDEN_45_CONTROLS_HANDOFF.md` | this file |

## The five controls

Each was measured in a throwaway copy first (mutation → observed first `FAIL:` line), then
re-run through the harness with `--checker <script>`; all five `FIRED` with the aimed line.

| id | checker | mutation (models a real regression of the guarded artefact) | asserted first `FAIL:` |
|---|---|---|---|
| `g4` | `check_garden_store.py` | the captures-UPDATE trigger still aborts, but its `RAISE` message stops naming the invariant | `the UPDATE trigger's own RAISE message names the invariant it enforces -- 'captures is immutable (trigger)' does not contain 'captures is immutable: UPDATE rejected'` |
| `n4` | `check_garden_normalize.py` | `_comparison_view()` stops case-folding | `two candidates whose text differs only in letter case still get an exact-text hint -- the comparison view is case-folded, as W1_4_NORMALIZATION_HINTS.md documents -- []` |
| `r4` | `check_garden_review.py` | the corpus follow-on is filed under the curation action vocabulary | `every curation-dimension row is recorded as 'curation-decision' and every corpus-dimension follow-on row as 'corpus-follow-on'` |
| `x3` | `check_garden_e2e.py` | the T-P7 audit row records a wrong `to_state` while the live column stays right | `the T-P7 audit row itself records to_state=candidate_only (not just the live corpus_state) -- to_state='eligible'` |
| `l4` | `check_garden_ledger.py` | `quotes.csv`'s `verification_status` is widened by hand (D3's ruling) | `issue #45 gap 4: quotes.csv's verification_status stays exactly ['disputed', 'unverified', 'verified'] -- D3 chose the side-car ledger 'instead of widening the 3-valued quotes.csv enum', and this suite (not just validate_quotes.py) falsifies that ruling directly -- ['1']` |

`l4` mutates `quotes.csv` — applied only inside the harness's throwaway copy, never the working
tree (the same posture as the existing `c1`–`c3` controls).

## The one assertion whose `FAIL:` detail had to change

`x3` could not be registered as written: the e2e check on the T-P7 audit row passed
`str(tp7_rows[0] if tp7_rows else None)` as its detail, and that row carries a wall-clock
`occurred_at`, so the failure line differed on every run and could never have been a committed
exact-match expectation. The detail now names the recorded state
(`to_state='eligible'`, or `no T-P7 audit row`). The assertion's **condition is unchanged** and
`check_garden_e2e.py` still reports **96** checks — this is a detail string, not a check. The rule
is recorded in `docs/architecture/NEGATIVE_CONTROLS.md` (a `FAIL:` detail may not embed a wall-clock
value; the same applies to rendered geometry, which is why the `overflow-wrap` control is excluded).

## Evidence

### Full negative-control harness (all 13 checkers, python3)

```
  checkers: 13 of 13 selected, 0 skipped
  controls: 44 fired, 0 not fired of 44 selected (44 registered in the table)
  harness self-tests: 9 of 9 passed
RESULT: PASS (44 controls fired, 9 harness self-tests) [negative controls]
harness_exit=0
```

### All 12 stdlib checkers, both interpreters (python3.14.5 / CI's python3.12)

```
validate_quotes.py                  exit=0 RESULT: PASS   (both)
check_program_contracts.py          exit=0 RESULT: PASS   (both)
validate_homepage_preview_export.py exit=0 RESULT: PASS   (both)
check_pages_contract.py            exit=0 RESULT: PASS (16 checks)   (both)
check_garden_store.py              exit=0 RESULT: PASS   (both)
check_garden_envelope.py           exit=0 RESULT: PASS   (both)
check_garden_submit.py             exit=0 RESULT: PASS   (both)
check_garden_normalize.py          exit=0 RESULT: PASS   (both)
check_garden_review.py             exit=0 RESULT: PASS   (both)
check_garden_ledger.py             exit=0 RESULT: PASS   (both)
check_garden_legacy_batch.py       exit=0 RESULT: PASS   (both)
check_garden_e2e.py                exit=0 RESULT: PASS   (both)
```

### Browser smoke

```
.venv/bin/python scripts/smoke_quote_browser.py
→ RESULT: PASS (0 warning(s))
```

### CSV byte-identity

`quotes.csv` `9766db8c…` / `sources.csv` `7aafcb67…` — identical before and after the whole
evidence pass (the D8-updated pair; this unit changes neither).

## Isolation of the controls

Each control's `FIRED` verdict is the harness's own isolation proof: `judge()` requires the aimed
`FAIL:` line to be the **first** one the checker prints, so a mutation that trips a different guard
first is reported `MASKED`, not credited. All five fired as aimed, so none is masked by an earlier
check.

## What this unit deliberately did not do

- Did not change any checker's check count, any suite's `EXPECTED_CHECKS`, or the harness's
  mutation vocabulary.
- Did not touch `quotes.csv`/`sources.csv` (the `l4` mutation runs only in the throwaway copy).
- Did not start D6 (near-duplicate curation — human-gated per `AGENTS.md`), D9 (bahai-homepage
  lane), or W2 (unauthorized).

## Exact next authorized action

Re-confirm with `gh issue list --state open`. The remaining Garden-side open items that are not
operator-gated are **D6** (near-duplicate curation — human look) and the authorized-queued **D9**
(H2B-B) lane, whose work lives in `bahai-homepage`, not this repo. W2 remains unauthorized.

## Review status

Same-session authoring and verification (no independent reviewer). The operator may still want a
foreign pass on the five control mutations and the e2e detail change.
