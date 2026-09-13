# Handoff — issue #31: the validator's near-duplicate score is now a property of the pair

**Unit:** `fix/validator-symmetric-similarity` · **Branch → PR:** `fix/validator-symmetric-similarity` → PR #35
**Date:** 2026-09-13 · **Scope:** `scripts/validate_quotes.py` + the frozen evidence it generates +
the queue item that cites that evidence. **No corpus edit.**

## Why this unit

`docs/queue.md` and issue [#31](https://github.com/mschwar/Garden-of-Wisdom/issues/31) recorded a
real defect: `scripts/validate_quotes.py` scored each near-duplicate candidate pair with **one
directional** `difflib.SequenceMatcher.ratio()` call, and that ratio is asymmetric. So the number a
pair was reported with was a function of the order the two rows happened to be visited in:

- `113 ~ 114` → `0.6888…` one way, `0.6666…` the other (the frozen report says `0.69`);
- `189 ~ 216` → `0.6023` one way, `0.5909` the other — it **crosses the `0.60` threshold in one order
  and not the other**, so a re-run could add or drop a pair, not merely shift a number.

`AGENTS.md` names `scripts/validate_quotes.py` as a file where "improving checks is always welcome",
it changes no CSV, and the issue explicitly asks for the fix to land with a re-generated report and a
re-counted D6 item — so it is in scope as its own unit, which is what it got.

## What landed

1. **The score is the mean of both directional ratios** (`pair_similarity()`, threshold
   `NEAR_DUPLICATE_THRESHOLD = 0.6` compared with `>`). Same rule W1.4's store-side hint generator
   already used (`docs/program/W1_4_NORMALIZATION_HINTS.md` §3 ruling 1), so the validator and the
   store now agree about what a pair's similarity is.
2. **A hard failure, not a note, when the result is order-dependent.** The whole detection pass is
   re-run over the same rows with every tradition's rows reversed; the pair set *and* the reason
   strings must match, else `FAIL:` and exit 1. This line is in CI (`browser-smoke.yml` runs the
   validator), so the class cannot return silently.
3. **A second hard check on the reporting contract:** every printed reason is re-derived from the rows
   themselves, so a pair sharing a pinpoint citation that *also* clears the text threshold must carry
   its number.
4. **Decision 1 — a shared citation that also clears the threshold now reports the number** (3 pairs
   today: `66 ~ 67` 0.60, `201 ~ 306` 0.86, `209 ~ 301` 0.82). The old loop `continue`d on a shared
   `source_ref` and silently discarded the second, independent piece of evidence. The pair count does
   not move — the number is appended to the existing line.
5. **Decision 2 — the sweep stays scoped within one `tradition`**, decided *with* the measurement, not
   before it. Corpus-wide the same rules flag **196** pairs instead of **45**; **146 of the 151**
   additions are the same bare `Oral Tradition` label matching unrelated rows across traditions, which
   would bury the signal in the queue this feeds. Filed as
   [#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34), with the part that is *not* noise: 5
   additions are cross-tradition text overlaps the scoped sweep cannot see at all, the strongest being
   `39` (Christianity, "Thou shalt love thy neighbour as thyself.") ~ `53` (Judaism, "Love thy
   neighbour as thyself.") at 0.82.
6. **`docs/data/DATA_QUALITY_REPORT.md` was extended, never rewritten.** The 2026-09-11 transcript is
   still there byte-identical — `git diff` on that file shows **0 deleted lines** — and a dated
   "Re-derivation 2026-09-13 (issue #31)" section carries the verbatim fresh transcript (captured from
   a real run, not transcribed), the exact pair-class table, the two decisions and the evidence for
   them.
7. **The queue's D6 item was re-counted** from its approximate `~22` / `~23` split to the re-derived
   **15 to inspect / 30 to skip**, with the classification rule and its source named.
8. `docs/DECISIONS.md` carries the full decision entry (including the rejected alternatives);
   `docs/RUNBOOK.md` documents the two new hard-failure lines and how to re-freeze the report;
   `docs/program/W1_4_NORMALIZATION_HINTS.md` §3 gets a dated annotation (the reviewed text above it is
   untouched).

## Evidence

`quotes.csv` / `sources.csv` byte-identical to the tree before the unit — the re-count is a derivation
over the corpus, not an edit to it:

```
$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
$ git diff --stat quotes.csv sources.csv
(no output)
```

The whole output delta against the pre-unit validator, exactly four lines plus the new check lines:

```
16c16
<   66 ~ 67 (same source_ref)
---
>   66 ~ 67 (same source_ref; text similarity 0.60)
19c19
<   113 ~ 114 (text similarity 0.69)
---
>   113 ~ 114 (text similarity 0.68)
23c23
<   201 ~ 306 (same source_ref)
---
>   201 ~ 306 (same source_ref; text similarity 0.86)
25c25
<   209 ~ 301 (same source_ref)
---
>   209 ~ 301 (same source_ref; text similarity 0.82)
52a53
> pair detection re-run with every tradition's rows reversed: 45 candidates
> near-duplicate reasons re-derived from the rows and matched: 45
```

The pair set is unchanged at **45**, and the pair-class decomposition (deterministic rule, no
editorial judgement) is:

| class | rule | pairs |
|---|---|---|
| text similarity, no shared citation | similarity > 0.60 | 2 |
| shared citation with a pinpoint locator | `source_ref` equal, contains a digit / Roman numeral / `§` | 13 |
| shared citation without a locator — bare label | not a citation at all (the literal `Oral Tradition`) | 25 |
| shared citation without a locator — real work/section | names a work, no pinpoint | 5 |

Both interpreters, and the rest of the repo's checks, on the unit's tree:

```
$ python3 scripts/validate_quotes.py                     -> RESULT: PASS, exit 0   (2.3s, was 0.6s)
$ /opt/homebrew/bin/python3.12 scripts/validate_quotes.py -> RESULT: PASS, exit 0
$ python3 scripts/check_program_contracts.py             -> exit 0
$ python3 scripts/validate_homepage_preview_export.py    -> exit 0
$ python3 scripts/check_garden_store.py                  -> exit 0, RESULT: PASS
$ python3 scripts/check_garden_envelope.py               -> exit 0, RESULT: PASS
$ python3 scripts/check_garden_submit.py                 -> exit 0, RESULT: PASS
$ python3 scripts/check_garden_normalize.py              -> exit 0, RESULT: PASS
$ python3 scripts/check_garden_review.py                 -> exit 0, RESULT: PASS
$ python3 scripts/check_garden_e2e.py                    -> exit 0, RESULT: PASS
```

Runtime note, recorded because it is a real cost: the reversal pass doubles the sweep, so the validator
went from **0.6s to 2.3s** on this corpus. That is the price of a guard that fires (see `c1`), and the
script is CI-only.

## Negative controls (independent harness, same session)

`/tmp/gow31/controls.py` (throwaway, not committed): each control copies the repo to `/tmp`, applies
**exactly one** source mutation to `scripts/validate_quotes.py`, asserts the anchor is unique, and runs
the copy's validator with the real `python3`. This session both authored and reviewed the change; the
harness was written after the code, and **the operator may still want a foreign pass** — that is
labelled plainly rather than implied otherwise.

| # | mutation | observed `FAIL:` line (first) | proves |
|---|---|---|---|
| c1 | `pair_similarity` reverted to one directional `ratio()` | `near-duplicate detection is row-order dependent: pairs/numbers only in file order [(66, 67, 'same source_ref'), (113, 114, 'text similarity 0.69')], only in reversed order [(66, 67, 'same source_ref; text similarity 0.61'), (113, 114, 'text similarity 0.67'), (189, 216, 'text similarity 0.60')]` | the order-independence guard catches the real defect class — **both** the number (`0.69`/`0.67`) and membership (`189 ~ 216` appears only in one order) |
| c2 | c1 **plus** the guard made inert (`if False:`) | `<none>` — `RESULT: PASS` | the guard, and not some other check, is what catches c1 (layering evidence) |
| c3 | the dual-reason suffix dropped (`if False:`) | `near-duplicate reasons do not match the evidence (reported, expected): [('66','67','same source_ref','same source_ref; text similarity 0.60'), ('201','306',…), ('209','301',…)]` | decision 1's annotation has its own unique falsifier |
| c4 | the text sweep widened to the whole corpus | `<none>` — `RESULT: PASS` | **finding, not a catch** — see below |
| c5 | every citation pair mislabelled as text-evidence-only | `near-duplicate reasons do not match the evidence (reported, expected): [('66','67','text similarity 0.60','same source_ref; text similarity 0.60'), …]` | the reason string is contract-checked in both directions, not just "not empty" |
| sanity | the same copy with no mutation | `<none>` — `RESULT: PASS` | the harness is not trivially red |

**Finding (c4) — the scope has no automated falsifier, and that is recorded rather than papered over.**
Widening the sweep to the whole corpus leaves the validator green: a 196-pair report is still internally
consistent, so nothing *can* be asserted about which scope is correct without asserting policy. The only
detector is the `45`-pair count in the transcript and the D6 re-count that cites it, which is why both
the report and the queue call that count the **tripwire**. Checked for inertness before calling it a
finding: c4 is not inert — it changes the printed count from 45 to 196 — it is simply unguarded.

## Out-of-scope findings (recorded, not fixed in passing)

- **[#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34) — the sweep is per-`tradition` and
  treats any shared `source_ref` as evidence.** The measured numbers are in the report's re-derivation
  section and in the issue (45 vs 196 pairs; 146 label-noise additions vs 5 real cross-tradition
  overlaps; 13 of 43 shared-citation pairs carry a locator). Not fixed here: this was a **correctness**
  unit, and the scope is a **policy** choice that moves the D6 counts — its own unit, its own decision.
- **Not a new finding, re-filed for completeness:** CI still runs none of the six W1 acceptance suites,
  nor `check_garden_review.py`. The validator changed here **is** in CI, so this unit's own guard is
  covered; the gap is unchanged and still needs its own unit (it is a change to the guarded workflow).

## Deliberately NOT done

- **No corpus edit** — `quotes.csv` / `sources.csv` byte-identical; no row merged, deleted or re-typed.
- **No D6 curation** — the queue item is re-counted, not executed: deciding whether two near-duplicate
  rows are accidental duplication or legitimate variant translations is a human curation pass
  (`AGENTS.md`, "What requires human/provenance review").
- **No scope change** — filed as #34 instead.
- **No corpus-program work** — no store surface, no schema, no migration, no state vocabulary, no W2.

## Resume / next action

The next in-scope open `Spec:` issue on the board is
[#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34) (this unit's own follow-up: the sweep's
scope and the locator rule), and it is the one that unblocks the queue's next data-curation item by
settling what the near-duplicate list should contain.

### Exact next Prompt

**Execute issue #34 — decide the near-duplicate sweep's scope and citation rule, then re-derive the
counts it moves.** Specifically: (1) decide whether the validator keeps the sweep scoped per
`tradition` or widens it to the whole corpus, and whether it adopts W1.4 ruling 2's locator test
(`citation_specificity()` in `scripts/garden_normalize.py`) for the `source_ref` branch — the measured
options are in the issue (current 45 pairs; corpus-wide 196; 146 label-noise additions vs 5 real
cross-tradition text overlaps, strongest `39 ~ 53` at 0.82; 13 of 43 shared-citation pairs carry a
locator); (2) implement the decision in `scripts/validate_quotes.py` with a guard that can fail for the
rule you change, and prove it with a negative control in a throwaway `/tmp` copy; (3) re-derive
`docs/data/DATA_QUALITY_REPORT.md` in a **new dated section** (never overwrite the 2026-09-11 or
2026-09-13 transcripts) and re-count the queue's D6 item to match; (4) `quotes.csv` / `sources.csv` stay
byte-identical (`5675d7e6…` / `10b4c156…`) — if a decision cannot be implemented without editing the
corpus, stop and record why instead. One branch → one PR → merge → push, then state the next task. If
the operator prefers the validator's scope be frozen as-is, close #34 as "no change" with that
measurement as the reason and take the **CI-coverage unit** instead (wire the six W1 acceptance suites
into `browser-smoke.yml`) — that is the other long-open, non-gated item.

**Still gated — do not start:** W2 and everything after it (Gate B is accepted; W2 authorization is a
separate operator decision), any discovery adapter, any canonical promotion path, the D6/D7 corpus
curation edits themselves (human pass), and any verification-status change.

## Merged — post-merge record (2026-09-13)

- Commit `d27cb64` on `fix/validator-symmetric-similarity`, PR
  [#35](https://github.com/mschwar/Garden-of-Wisdom/pull/35), **merged as `f24fae7`**.
- CI: PR smoke run
  [34790379227](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34790379227) **success**;
  on `main` after merge, smoke run
  [34790423853](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34790423853) **success** and
  Pages deploy run
  [34790423865](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34790423865) **success**.
  GitGuardian on the PR: pass.
- Live acceptance on the merged `main` (`curl`):

  ```
  /                    200
  /browser/index.html  200
  /quotes.csv          200
  /sources.csv         200

  quotes.csv     live=5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793 repo=5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793 MATCH
  sources.csv    live=10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13 repo=10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13 MATCH
  ```
- Re-ran on merged `main`: `validate_quotes.py` → `RESULT: PASS` (exit 0);
  `check_program_contracts.py` and `validate_homepage_preview_export.py` → exit 0; all six W1
  acceptance suites (`check_garden_store` / `_envelope` / `_submit` / `_normalize` / `_review` / `_e2e`)
  → `RESULT: PASS`.
- Branch deleted locally and remotely (`gh pr merge --delete-branch`; `git remote prune origin`), the
  throwaway `/tmp` harness and control copies removed. Issue #31 closed; the follow-up is
  [#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34).
