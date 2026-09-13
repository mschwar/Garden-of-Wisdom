# GARDEN_W1_5_HANDOFF.md

**Unit:** W1.5 — Curation review + decision recording + audit history.
**Branch:** `w1/curation-review` · **PR:** #30 (this unit's own PR) · **Merge:** see the post-merge
docs commit for the merge sha / CI run ids.
**Date:** 2026-09-13.

## Summary

W1.5 is the loop's payoff: the operator-facing `accept / hold / reject / duplicate / reopen`
surface where a curation decision is a **recorded, audited transition** — never a silent state flip.
New surface `scripts/garden_review.py` sits on one new store write gate,
`garden_store.Store.curate`, which applies a legal T-C1…T-C12 transition and its required
corpus follow-on and writes the candidate's states **and every audit row in one SQLite
transaction**. The acceptance run `scripts/check_garden_review.py` exercises all twelve T-C
transitions through the real CLI, asserts each audit row's actor/timestamp/from/to/transition_id/
reason, and proves — for the first time against a real store — that the W0 carried-forward risk is
false: the reversal (`T-C8` → `T-P7`, `T-C9` → `T-P7`) strands **no** dimension.

## What landed

- `scripts/garden_store.py` — refactored `record_decision` into a non-committing
  `_insert_decision` + a committing public `record_decision`, and added:
  - `CURATION_ACTIONS` / `CURATION_TRANSITIONS` (the twelve T-C, all `operator`) /
    `CORPUS_TRANSITIONS` (T-P1 `system`, T-P7 `operator`);
  - `Store.curate(...)` — the single atomic write gate;
  - `_corpus_followon_reason(...)` — the audit reason for T-P1 / T-P7.
- `scripts/garden_review.py` — `queue`, `show`, `audit` (read-only) and `accept`, `hold`, `reject`,
  `duplicate`, `reopen` (each requires `--reason`, records actor, prints what transition fired).
- `scripts/check_garden_review.py` — the acceptance + evidence run (**246 checks**, both
  interpreters), driving every transition and every refusal through the real CLI as a subprocess,
  with fixtures derived from the real `quotes.csv`.
- `docs/program/W1_5_CURATION_SURFACE.md` — the design doc.
- `docs/DECISIONS.md` / `docs/queue.md` / `docs/RUNBOOK.md` — close-out updates.
- This handoff.

**No migration.** The `decisions` ledger and the four state columns already exist from W1.1; W1.5
only adds code. W1.1's exact-ledger assertion (`["0001_create_core"]`) is untouched.
**No populated store mirror is committed** — the only submissions are W1.5's throwaway test
fixtures; the first real operator-submitted population belongs to Gate B (W1.3 decision).

## The gateway

`Store.curate(candidate_id, *, action, actor, reason)`:
1. loads the candidate's `curation_state` / `corpus_state`;
2. looks `(from, to)` up in `CURATION_TRANSITIONS` (refuses an illegal move);
3. computes the corpus follow-on — acceptance with `candidate_only` → **T-P1**
   `candidate_only → eligible` (authority `system`); leaving `accepted` while `eligible` → **T-P7**
   `eligible → candidate_only` (authority `operator`);
4. updates the states and appends every decision row **in one transaction**, then commits.

`curate` writes only `curation_state` and `corpus_state`. It has **no research write path**;
`research_state` stays `not_started`. `reason` is required before anything is written.

## Acceptance evidence

Both interpreters (Homebrew `python3` 3.14.5 and `/opt/homebrew/bin/python3.12` = CI's 3.12), and
`quotes.csv`/`sources.csv` byte-identical (`5675d7e6…` / `10b4c156…`):

```
$ python3 scripts/check_garden_review.py
... 246 PASS lines ...
RESULT: PASS (all twelve curation transitions audit correctly, the reversal path strands
no dimension, and no curation action writes research state)
exit=0
```

```
$ /opt/homebrew/bin/python3.12 scripts/check_garden_review.py
... 246 PASS lines ...
RESULT: PASS (all twelve curation transitions audit correctly, the reversal path strands
no dimension, and no curation action writes research state)
exit=0
```

The suite covers: all twelve T-C transitions driven through the CLI, each with the exact audit rows
asserted; T-P1/T-P7 recorded with the right dimension/authority/actor; the three refused-write
guards (illegal transition, missing candidate, empty reason) each leaving the store byte-identical;
research state read-only after every action; the machine-inferred-vs-asserted markers rendered in
the queue; the `decisions` triggers re-proven append-only; and the two CSVs hashed before/after.

## Negative controls (same-session review pass)

The scope is large, so this session both authored and reviewed. The review pass is an **independent
mutation harness** (`/tmp/w15_controls.py`, throwaway) written after the code, aimed at paths the
author's own hand-testing did not touch. The operator may still want a foreign pass (see the skill's
note). Every control copies the repo, applies exactly one source mutation, and runs the suite in the
copy; each **goes red on the intended guard**:

| # | Mutation | Observed `FAIL:` line (first) |
|---|---|---|
| g1 | Remove T-P1 firing (acceptance no longer promotes to `eligible`) | `FAIL: accept: cand-t01 recorded exactly ['T-C1', 'T-P1'] -- ['T-C1']` |
| g2 | Remove T-P7 firing (reversal no longer demotes to `candidate_only`) | `FAIL: reject: cand-t08 recorded exactly [..., 'T-P7'] -- ['T-C1', 'T-P1', 'T-C8']` |
| g3 | Add `accepted -> accepted` to the transition table (an illegal move becomes legal) | `FAIL: there are exactly twelve curation transitions -- 13` |
| g4 | Remove `curate`'s required-reason guard | `FAIL: the refusal for an empty reason came from curate's OWN guard ('every curation decision must carry a reason') not a shared/backstop guard` |
| g5 | Make `curate` also write `research_state='in_research'` | `FAIL: accept: cand-t01 research_state stayed not_started -- in_research` |
| g6 | Change the queue's machine-inferred marker wording | `FAIL: the queue marks the duplicate hints as machine-inferred` |
| g7 | Record T-P1 as `operator` instead of `system` | `FAIL: T-P1 is recorded as a system-authority corpus transition -- {...}` |
| g8 | CLI layer defaults an empty `--reason` instead of refusing | `FAIL: a decision with an empty reason is refused (exit 0, RESULT: FAIL)` |

**Finding during the review pass (fixed):** `curate`'s empty-reason guard was masked by
`_insert_decision`'s own empty-reason check — removing the one in isolation left the suite green
(the backstop refused first). Per the skill's "two guards, one rule" lesson, the acceptance run now
asserts the **layering**: it looks for `curate`'s distinctive wording
(`every curation decision must carry a reason`) rather than the shared substring, giving `curate`'s
guard a unique falsifier. g4 currently proves it fires.

## Falsified carried-forward risk (W0_GATE_REPORT)

"The reversal rule (`T-C8` → `T-P7`) is legal on paper but untested against a real store." W1.5
exercises `accept → eligible` then `reject → candidate_only` (and `accept → eligible` then
`duplicate → candidate_only`) against the real store and asserts no record ends with
`curation ∈ {hold, rejected, duplicate}` while `corpus = eligible`. Control g2 proves the guard does
the work (removing T-P7 leaves the stranded-dimension path red).

## Out-of-scope findings (recorded, not fixed in passing)

- **CI still does not run any of the five W1 acceptance suites** (now `check_garden_store.py` 59,
  `check_garden_envelope.py` 102, `check_garden_submit.py` 134, `check_garden_normalize.py` 232,
  `check_garden_review.py` 246) nor the sixth surface `garden_review.py`. This is the long-open W1.2
  queue item, re-filed to FIVE; it is a change to the guarded `browser-smoke.yml` workflow and was
  not fixed as a side effect of an ingestion/review unit. Decision recorded in `DECISIONS.md`
  ("W1.5 lesson for the CI gap…").
- **A candidate deposited before normalization is shown (and can be decided) as-is.** The queue
  renders whatever the store holds; the operator runs `normalize --all` / `hints --all` before
  reviewing, and W1.6's end-to-end does exactly this. A decision on an un-normalized candidate is
  safe (states/hints are separate from the proposal) but the reviewer should see the raw values.
  Recorded as a design note, not filed as an issue: W1.6 is the unit that must enforce the
  "normalize-then-review" pipeline order.

## Deliberately NOT done

- **No promotion / no retirement surface.** `T-P2`…`T-P6` (including `T-P3 candidate_only →
  retired`) are operator promotion decisions and out of W1.5; rejecting from `new`/`hold` keeps the
  record readable rather than retiring it.
- **No research surface.** There is no code path in W1.5 that writes `research_state`.
- **No web/browser review UI.**
- **No populated `data/store` mirror.**

## Resume / next action

The next unit is **W1.6 — End-to-end test pack + Gate B evidence packet** (`docs/queue.md`, W1 the
"corpus program" section says *next: W1.6*). It must run from a clean clone with one command and
exit 0 (submit a messy batch → normalize → hints → review → assert originals/provenance/decision
history survived and no curation action implied verification), keep `quotes.csv`/`sources.csv`
byte-identical, and produce the Gate B packet mirroring `W0_GATE_REPORT.md`'s shape. W1 ends at the
Gate B packet; **W2 is not started.**

### Exact next Prompt

**Execute W1.6 — the end-to-end test pack + Gate B evidence packet** on an isolated branch
(`w1/gate-b-packet`), following `docs/program/W1_DECOMPOSITION.md` §"W1.6" and this skill
(`garden-of-wisdom-unit-ops`): implement the deterministic end-to-end acceptance run and the
Gate B evidence document, one PR → independent/foreign QA → resolve findings → record discovered
work in `docs/queue.md` and `docs/DECISIONS.md` → re-run acceptance under both `python3` (3.14) and
`/opt/homebrew/bin/python3.12` → merge → stop at the Gate B packet without starting W2.