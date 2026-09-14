# Handoff — CI runs the D3 ledger acceptance suite

**Branch:** `ci/wire-ledger-suite` · **Issue closed:** [#39](https://github.com/mschwar/Garden-of-Wisdom/issues/39)
("Spec: wire the D3 unverifiable-ledger acceptance suite into the browser-smoke CI step"),
filed at the D3 close-out (`GARDEN_D3_HANDOFF.md` → "Out of scope").

## What this unit is

Not a corpus-program unit (no W2 work, no store surface, no schema, no state vocabulary, no
CSV edit). It closes the CI-coverage gap the D3 unit deliberately left open: PR #38 shipped
`scripts/check_garden_ledger.py` (45 checks, 7 negative controls proving the guards are
load-bearing) but `.github/workflows/browser-smoke.yml`'s "Run the W1 corpus-program
acceptance suites" step only ran the six W1 suites. A regression in the `legacy_verification`
table, the `mark`/`reopen` guards, or the export section would have passed CI.

## What changed

One line appended to the existing step in `.github/workflows/browser-smoke.yml`, after
`check_garden_e2e.py` (same pattern as PR #37, which added the six W1 suites to this step):

```yaml
      - name: Run the W1 corpus-program acceptance suites
        run: |
          python scripts/check_garden_store.py
          python scripts/check_garden_envelope.py
          python scripts/check_garden_submit.py
          python scripts/check_garden_normalize.py
          python scripts/check_garden_review.py
          python scripts/check_garden_e2e.py
          python scripts/check_garden_ledger.py
```

`check_garden_ledger.py` is stdlib-only (no new dependency, no change to
`requirements-dev.txt`), deterministic, exits 0/1, and fits the existing job's Python 3.12
setup with no new install step. It creates and tears down its own SQLite store under a
throwaway temp directory and asserts nothing is written outside it — same isolation guarantee
as the other six suites in this step.

No other file changed besides this handoff and `docs/queue.md`. `git diff --stat` on the
workflow file shows exactly one line added.

## Evidence

All seven suites re-run locally immediately before this edit (Homebrew Python 3.12, matching
the workflow's `python-version: '3.12'`):

| Suite | Result |
|---|---|
| `check_garden_store.py` | `RESULT: PASS` (59 checks) |
| `check_garden_envelope.py` | `RESULT: PASS` (102 checks) |
| `check_garden_submit.py` | `RESULT: PASS` (134 checks) |
| `check_garden_normalize.py` | `RESULT: PASS` (232 checks) |
| `check_garden_review.py` | `RESULT: PASS` (246 checks) |
| `check_garden_ledger.py` | `RESULT: PASS` (45 checks, new) |
| `check_garden_e2e.py` | `RESULT: PASS` (96 checks) |

`quotes.csv` / `sources.csv` unchanged: `5675d7e6…` / `10b4c156…` (identical to every prior
unit's recorded hash).

## Negative control

One control, same session, proving the new line actually fails the step on a real regression
rather than passing vacuously — same method as PR #37's c1:

- **c1 — injected failure in `check_garden_ledger.py`.** Added
  `raise SystemExit("INJECTED NEGATIVE CONTROL FAILURE")` immediately before the
  `if __name__ == "__main__":` guard (fires only when run as a script, not on import). Ran the
  step's tail under `bash -e` (matching how GitHub Actions executes a multi-line `run:` block —
  first failing command aborts the step):

  ```
  $ bash -e -c 'python3 scripts/check_garden_e2e.py >/dev/null && echo "e2e OK, ledger next:"; python3 scripts/check_garden_ledger.py'
  e2e OK, ledger next:
  INJECTED NEGATIVE CONTROL FAILURE
  step exit: 1
  ```

  The step aborted at the injected failure — fail-fast, as intended. Reverted immediately from
  a pre-mutation backup; `git diff` on `check_garden_ledger.py` shows nothing, and a clean
  re-run of all seven suites (table above) confirms `RESULT: PASS` again.

## What this unit deliberately did not do

- Did not touch `.github/workflows/pages.yml` (separate workflow, separate concern, issue #23
  already open there).
- Did not add a new job or a matrix — `check_garden_ledger.py` runs sequentially in the
  existing `smoke` job, same as the six W1 suites already there. It's fast (a stdlib-only
  SQLite round-trip in a temp dir); a separate job would add a second Python/Playwright setup
  for no benefit.
- Did not touch `requirements-dev.txt` — no new dependency.
- Did not re-run or re-verify the D3 unit's own negative controls (the 7 from `GARDEN_D3_HANDOFF.md`) —
  those already proved `check_garden_ledger.py` is not vacuously green; this unit's own control
  (c1 above) proves the new CI line actually executes and fails fast, which is the distinct
  claim this unit needed to prove.
