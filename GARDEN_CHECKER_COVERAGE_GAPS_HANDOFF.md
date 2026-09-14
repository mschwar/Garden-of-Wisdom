# Handoff — the five checker coverage gaps from issue #45 are closed

**Branch:** `fix/checker-coverage-gaps` · **Closes:** issue
[#45](https://github.com/mschwar/Garden-of-Wisdom/issues/45)

## What this is

Issue #45 was filed while authoring the committed negative-control table for issue #43
(`scripts/run_negative_controls.py`): five mutations that stayed green because a documented
contract or ruling had no falsifier in the acceptance suite that owns it. Each was re-verified
independently in this unit, against the exact anchor/replacement text #45 recorded, before and
after the fix.

## The five gaps and their fixes

| # | gap | fix | file |
|---|---|---|---|
| 1 | `garden_normalize._comparison_view()`'s documented case-folding was unexercised | added a fixture pair whose text differs only in letter case (submitted via the real CLI, generic `none` citations to avoid a reference-hint confound); asserts `exact-text` fires and `near-text` does not | `scripts/check_garden_normalize.py` |
| 2 | `check_garden_review.py` never inspected a decision row's `action` vocabulary | added a check over every recorded decision row: `curation` dimension rows must carry `action="curation-decision"`, every other row `action="corpus-follow-on"` | `scripts/check_garden_review.py` |
| 3 | `check_garden_e2e.py` asserted the live `corpus_state` but not the T-P7 audit row's own `to_state` | added an assertion reading the T-P7 decision row directly and checking its `to_state == "candidate_only"`, independent of the live column | `scripts/check_garden_e2e.py` |
| 4 | D3's "do not widen the `quotes.csv` enum" ruling had no falsifier anywhere (`check_garden_ledger.py` only hashed the CSVs) | added a new first section to `check_garden_ledger.py` that reads `quotes.csv` directly and asserts `verification_status` stays in the 3-valued enum, plus that the live instance (id 30, issue #5) stays `unverified` there (its adjudication lives only in the ledger) | `scripts/check_garden_ledger.py` |
| 5 | the captures-UPDATE/DELETE trigger's `RAISE` *message* was unguarded (only the abort itself was) | added a message-content assertion alongside the existing `IntegrityError` check, for both UPDATE and DELETE | `scripts/check_garden_store.py` |

Gap 4 also fixes a scope note in #45's own filing: it says the check could live "here or in
`validate_quotes.py`, which owns the CSV's vocabulary" — `validate_quotes.py` already enforces
`VALID_VERIFICATION_STATUSES = {"unverified", "verified", "disputed"}` (from the original G2
rehab, unrelated to D3) and already fails on the exact mutation. But `check_garden_ledger.py` is
the suite that owns D3's ruling, and it had no assertion of its own — it would report `RESULT:
PASS` in isolation even though the mutation it exists to guard against had happened. The fix adds
the guard directly to `check_garden_ledger.py` so D3's own suite proves D3's own ruling, rather
than depending on a different suite that happens to also run in the same CI step.

## Verification

Each of the five fixes was verified against the **exact** mutation #45 recorded, using a
throwaway copy of the mutated file, run, then restored — the working tree in this repo was never
left in a mutated state during authoring.

```
gap 1: casefold() dropped from _comparison_view          -> FAIL (was PASS before the fix)
gap 2: action="decided"/"followon" renamed                -> FAIL (was PASS before the fix)
gap 3: T-P7 follow tuple's to_state -> "eligible"          -> FAIL (was PASS before the fix)
gap 4: quotes.csv row 30 verification_status -> unverifiable -> FAIL (was PASS before the fix)
gap 5: RAISE(ABORT, 'rewritten')                           -> FAIL (was PASS before the fix)
```

All five now report their own aimed `FAIL:` line and no traceback; restoring the pristine file
returns each suite to `RESULT: PASS`.

## Regression check

All eleven stdlib validators/acceptance suites re-run clean after the fixes:
`validate_quotes.py`, `check_program_contracts.py`, `validate_homepage_preview_export.py`,
`check_garden_store.py` (now with the two new message-content checks),
`check_garden_envelope.py`, `check_garden_submit.py`, `check_garden_normalize.py` (now with the
case-fold fixture), `check_garden_review.py` (now with the `action`-vocabulary check),
`check_garden_e2e.py` (now with the T-P7 `to_state` check), `check_garden_ledger.py` (now with
the enum guard), `check_pages_contract.py` — all `RESULT: PASS`.

The full committed negative-control table also re-runs clean:
`python3 scripts/run_negative_controls.py` → `RESULT: PASS (36 controls fired, 9 harness
self-tests)`, `checkers: 12 of 12 selected, 0 skipped` on a machine with `playwright` installed
(the two `smoke_quote_browser.py` controls need it). **Independent QA reproduced this on a
machine without `playwright`: `RESULT: PASS (34 controls fired, 9 harness self-tests)`,
`checkers: 12 of 12 selected, 1 skipped`, and confirmed the same 34-vs-36 split already happens
on unmodified `main` — a pre-existing, environment-dependent condition, not something this unit
introduced.** Either way, none of the five new checks collide with an existing control's anchor
or expected output, and the table's own coverage floor
(`EXPECTED_CONTROLS`/`EXPECTED_SELF_TESTS`) is unchanged because this unit added fixtures/checks
to the acceptance suites, not new entries to the negative-control table itself. (A future unit
could add five more controls to the table — one per gap closed here — but that is a harness
change, not required to close #45, and is left as a natural follow-on rather than folded in
silently.)

`quotes.csv` / `sources.csv` byte-identical before and after this unit (`b3bb7848…` /
`7aafcb67…`, the D7-updated pair) — no working-tree diff on either file at any point; every
mutation used for verification was applied to a copy or reverted immediately after its
observation was recorded.

## Review status (foreign QA)

**Independent reviewer, own harness, own throwaway copies (never read this file or the author's
transcript): PASS, no high/medium defects.** For each of the five gaps, the reviewer made an
independent throwaway `git archive` copy of both `main` and this branch, applied issue #45's
exact anchor/replacement mutation to both, and confirmed: the fix branch's owning suite reports
its own aimed `FAIL:` line with no traceback, while `main`'s same suite stays `RESULT: PASS` (the
gap was real). Vacuousness checks the reviewer ran beyond the minimum: confirmed
`check_garden_review.py`'s new `action` check only iterates `subject_kind='candidate'` rows (so
research-dimension rows, which use a third `action` value, never enter the binary
curation/corpus mapping — not accidentally always-true); confirmed `check_garden_e2e.py`'s new
check reads the T-P7 decision row's own `to_state` field via `decision_rows()`, not the live
`corpus_state` column; confirmed `check_garden_store.py`'s new message check is mapped
per-verb by separately mutating only the DELETE trigger's message and observing the
DELETE-specific mismatch reported (not a shared/wrong string). All eleven other suites plus the
negative-control table re-ran clean on the fix branch in the reviewer's own environment, and both
CSVs' sha256 matched between `main` and the branch.

**One low-severity finding, addressed above:** the reviewer's environment had no `playwright`
installed, so `run_negative_controls.py` reported 34/9 with one skip rather than 36/9 — traced to
a pre-existing, environment-dependent condition reproducible on unmodified `main`, not introduced
by this unit. The handoff's regression-check section above now states both outcomes.

## What this unit did not do

- Did not add new entries to `run_negative_controls.py`'s own 36-control table. Each gap here is
  now guarded by an assertion inside the suite that owns it, which is what #45 asked for; wiring
  those same five mutations into the harness's own table is a separate, optional follow-on.
- Did not touch `docs/architecture/NEGATIVE_CONTROLS.md` or
  `GARDEN_NEGATIVE_CONTROLS_HANDOFF.md`'s "Out-of-scope findings" table — both describe the state
  *before* this unit and are left as the historical record; this handoff and the queue entry are
  where the closure is recorded.
