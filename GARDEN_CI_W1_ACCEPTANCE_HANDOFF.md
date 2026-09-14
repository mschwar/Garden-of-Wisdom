# Handoff — CI runs the six W1 acceptance suites

**Branch:** `ci/w1-acceptance-suites` · **Issue closed:** the CI gap first filed at W1.2's
close-out and reaffirmed at every unit through W1.6 (see `docs/queue.md` → "Open — discovered
during W1.2" → "CI does not run the W1 acceptance suites").

## What this unit is

Not a corpus-program unit (no W2 work, no store surface, no schema, no state vocabulary, no
CSV edit). It closes a standing CI-coverage gap: `.github/workflows/browser-smoke.yml` ran
`validate_quotes.py`, `check_program_contracts.py` and `validate_homepage_preview_export.py`
on every PR and push to `main`, but none of the six `check_garden_*.py` acceptance suites that
W1.1–W1.6 built and evidenced locally. A regression in `scripts/garden_store.py`,
`garden_envelope.py`, `garden_submit.py`, `garden_normalize.py`, or `garden_review.py` could
land on `main` with a green check.

## What changed

One new step appended to the existing `smoke` job in `.github/workflows/browser-smoke.yml`,
after the "Check the data validators still pass" step:

```yaml
      - name: Run the W1 corpus-program acceptance suites
        run: |
          python scripts/check_garden_store.py
          python scripts/check_garden_envelope.py
          python scripts/check_garden_submit.py
          python scripts/check_garden_normalize.py
          python scripts/check_garden_review.py
          python scripts/check_garden_e2e.py
```

All six suites are stdlib-only (no new dependency, no change to `requirements-dev.txt`),
deterministic, and exit 0/1 — they fit the existing job's Python 3.12 setup with no new step
needed to install anything. Each suite creates and tears down its own SQLite store under a
throwaway temp directory (asserted by each suite's own "nothing written outside its own
directory" check); none of them touch `quotes.csv`/`sources.csv` or `data/`.

No other file changed. `git diff --stat` shows exactly the one workflow file.

## Evidence

All six suites re-run locally immediately before this edit (Homebrew Python, same interpreter
CI will use is 3.12 per the workflow's `python-version: '3.12'`):

| Suite | Result |
|---|---|
| `check_garden_store.py` | `RESULT: PASS` (59 checks, W1.1) |
| `check_garden_envelope.py` | `RESULT: PASS` (102 checks, W1.2) |
| `check_garden_submit.py` | `RESULT: PASS` (134 checks, W1.3) |
| `check_garden_normalize.py` | `RESULT: PASS` (232 checks, W1.4) |
| `check_garden_review.py` | `RESULT: PASS` (246 checks, W1.5) |
| `check_garden_e2e.py` | `RESULT: PASS` (96 checks, W1.6 / Gate B) |

`quotes.csv` / `sources.csv` unchanged: `5675d7e6…` / `10b4c156…` (identical to every prior
unit's recorded hash).

## Negative control

One control, same session, proving the new step actually fails on a real regression rather
than passing vacuously:

- **c1 — injected failure in `check_garden_store.py`.** Added
  `raise SystemExit("INJECTED NEGATIVE CONTROL FAILURE")` immediately before the
  `if __name__ == "__main__":` guard (so it fires only when the script runs as a script, not
  on import). Ran the new step's exact command sequence under `bash -e -c '...'` (matching how
  GitHub Actions executes a multi-line `run:` block — first failing command aborts the step):

  ```
  $ bash -e -c 'python3 scripts/check_garden_store.py; python3 scripts/check_garden_envelope.py; python3 scripts/check_garden_submit.py'
  INJECTED NEGATIVE CONTROL FAILURE
  step exit: 1
  ```

  The step aborted at the first suite and never reached `check_garden_envelope.py` or
  `check_garden_submit.py` — fail-fast, as intended. Reverted immediately
  (`cp` from a pre-mutation backup); `git diff` on `check_garden_store.py` shows nothing, and a
  clean re-run confirms `RESULT: PASS` again.

## What this unit deliberately did not do

- Did not touch `.github/workflows/pages.yml` (separate workflow, separate concern, issue #23
  already open there).
- Did not add a new job or a matrix — the six suites run sequentially in the existing `smoke`
  job, same as the three validators already there. They're fast (each is a stdlib-only SQLite
  round-trip in a temp dir); a separate job would add a second Python/Playwright setup for no
  benefit.
- Did not touch `requirements-dev.txt` — no new dependency.
- Did not re-open or change the "seventh surface" gap noted at W1.6 close-out
  (`garden_review.py` itself has no acceptance suite of its own beyond what
  `check_garden_review.py` and `check_garden_e2e.py` already exercise) — that's a different,
  unfiled question, not this unit's scope.
