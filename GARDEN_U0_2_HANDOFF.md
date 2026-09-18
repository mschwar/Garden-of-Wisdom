# Handoff — U0.2 Truthful front door + current-state routing

**Branch:** `u0.2/front-door` · **Gate:** U0 — resumable workbench · **Unit:** U0.2
**Spec:** `docs/program/usability-closure/workunits/U0.2_FRONT_DOOR.md`

## What this is

An information-architecture repair, not a prose expansion. The front door now says what is
true, and one authority — `docs/program/usability-closure/CURRENT.md` — owns live programme
status while every other front door *routes* to it. The failure class is now falsifiable:
`scripts/check_front_door.py` (23 checks, CI-wired, 5 registered negative controls) fails the
build if a front-door document re-asserts a stale live-status claim, if the queue and CURRENT
disagree about which unit is READY, or if a front door stops naming its own command surface.

## Before/after contradiction table

Every row was read off `main` at `a5284c2` before this unit; the "before" strings are quoted
verbatim, and the "after" column is what the file says now. `scripts/check_front_door.py` run
against the **unfixed** tree reports **11 FAIL of 23** (transcript below); against the branch it
reports `RESULT: PASS (23 checks)`.

| # | Document | Before (false/stale) | After | Caught by |
|---|---|---|---|---|
| 1 | `docs/program/README.md` | "No datastore, intake surface, discovery adapter, or W1 runtime code exists in this repo yet." | "Doctrine, contracts and the W1 runtime all landed: the store, the candidate envelope, the submission CLI, normalization + duplicate hints, the curation surface and the end-to-end pack are implemented in `scripts/garden_store.py`, `garden_envelope.py`, `garden_submit.py`, `garden_normalize.py` and `garden_review.py` …" | check 22 |
| 2 | `docs/program/README.md` | "The wave is in progress" | "**W1 complete, Gate B accepted** 2026-09-13" | check 23 |
| 3 | `docs/program/README.md` | read order item 9: "`W1_DECOMPOSITION.md` — bounded W1 work units (authorized in full 2026-09-12; in progress)" | "the bounded W1 work units; **historical plan, all six landed**" | check 23 |
| 4 | `docs/program/README.md` | "Current data and validators are untouched: `quotes.csv` and `sources.csv` are byte-identical to `main`" (present tense in a 2026-09-12 section; D7/D8 changed both CSVs since) | "were byte-identical to `main` *at that time* … That is history, not live status" | **review only** (see limits) |
| 5 | `docs/program/README.md` | no route to live status | "**This directory is doctrine and history; live programme status is not here.** It lives in `docs/program/usability-closure/CURRENT.md`" + a canonical-doc table row | check 14 |
| 6 | `docs/product/PRODUCT_DOCTRINE.md` | "**W1 is authorized in full** (2026-09-12 …) and is in progress." | "W1 … is **complete** (Gate B accepted 2026-09-13). W2 is not started … **Live status and the single READY unit live in `docs/program/usability-closure/CURRENT.md`**" | checks 15, 23 |
| 7 | `README.md` | "**W1 is authorized in full (2026-09-12)** … the wave's stop point is the Gate B packet" — no current state, no store, no pointer | new "Where are we now?" section routing to CURRENT; roadmap bullets say W1 **complete** with Gate B accepted 2026-09-13 and name the usability-closure programme | checks 13, 23 |
| 8 | `README.md` | "Phase 1 (not started)": human curation pass | "Phase 1 (curation, partly executed as named data units)": D3/D4/D6/D7/D8 listed as landed, with the operator-gated residue named | review (a stale *plan* claim, not a live-status claim) |
| 9 | `README.md` | Quickstart stopped at the retrofit commands | Quickstart adds `garden_store.py bootstrap` / `status` and `check_front_door.py`, and points at RUNBOOK for the workbench | review |
| 10 | `AGENTS.md` | three commands (`validate_quotes`, homepage-preview export, `http.server`); zero occurrences of `garden_` | the full command surface: store lifecycle incl. **bootstrap/resume**, the W1.3/W1.4/W1.5 loop, the ledger and batch feeds, the envelope, the acceptance suites, the negative-control harness, the front-door guard, Pages contract/live acceptance, the smoke test | checks 17, 19, 20 |
| 11 | `AGENTS.md` | no pointer to live status; resume path went to the queue and "the most recent handoff" | "**Live programme status is not in this file.** It lives in `…/CURRENT.md` … if this file and CURRENT disagree about status, CURRENT wins and this file is the bug"; resume steps 2–7 route through CURRENT → queue → DECISIONS → READY unit doc + handoff → bootstrap → acceptance suites → queue discovery | checks 12, 21 |
| 12 | `AGENTS.md` | no CSV change discipline (issue #27's second complaint) | "`quotes.csv` and `sources.csv` were read-only for the whole of the corpus-program W1 wave (now complete). They change only inside a **named data unit** … Do not edit them to make a check pass." | check 18 |
| 13 | `docs/queue.md` | `- [ ] **W1 — IN PROGRESS. Authorized in full 2026-09-12 (decision D1).**` (unchecked, complete) | `- [x] **W1 — COMPLETE (W1.1–W1.6 merged; Gate B accepted 2026-09-13). …**` | check 23 |
| 14 | `docs/queue.md` | "Explicitly NOT started": "**W1 is now authorized in full** (2026-09-12, decision D1) **and in progress**." | "**W1 is COMPLETE** (authorized in full 2026-09-12, decision D1; Gate B accepted 2026-09-13)", plus a new bullet: every usability-closure unit past the READY one is not started | check 23 |
| 15 | `docs/RUNBOOK.md` | no resume entry point; the tail's "session died" path went straight to the queue | new top section "Where are we? (resume here)" routing through CURRENT → queue → DECISIONS → unit doc + handoff → `bootstrap`; the tail section now matches | review (RUNBOOK installed) |
| 16 | `docs/program/usability-closure/CURRENT.md` | frontier sentence: "The front-door docs (README.md, AGENTS.md) still present outdated paths and need truthful current-state routing." | "The front-door docs (…) route live status here and are guarded by `scripts/check_front_door.py`. The next frontier is the real persistent operator canary (U0.3) …" | review (found by the cold-start dry run, see below) |

Rows 4, 8, 9, 15 and 16 are **review-caught, not check-caught** — see "Limits of the guard".

## Evidence

### 1. The guard fires on the real pre-fix tree (not just on a synthetic mutation)

`scripts/check_front_door.py` was written and run **before** any document was edited. Its
"before" transcript (11 real contradictions, exit 1) is pasted verbatim:

```
PASS: 1. CURRENT.md exists (docs/program/usability-closure/CURRENT.md)
PASS: 2. CURRENT.md keeps its required structure (all present)
PASS: 3. CURRENT.md has exactly one '## Current READY unit' heading (found 1)
PASS: 4. CURRENT.md names a READY unit id (value '`U0.2 — truthful front door + current-state routing`')
PASS: 5. the READY unit's work-unit document exists (U0.2 -> U0.2_FRONT_DOOR.md)
PASS: 6. CURRENT.md's READY unit and last-completed unit differ (a unit cannot be both)
PASS: 7. CURRENT.md names a last-completed unit id (value '`U0.1 — store lifecycle + mirror freshness invariant`')
PASS: 8. the last-completed unit's handoff exists (GARDEN_U0_1_HANDOFF.md)
PASS: 9. the READY unit belongs to the gate CURRENT.md names (ready 'U0.2', gate '`U0 — resumable workbench`')
PASS: 10. docs/queue.md marks exactly one unit READY in the usability-closure section (found 1)
PASS: 11. docs/queue.md's READY unit is CURRENT.md's READY unit (queue U0.2, CURRENT U0.2)
FAIL: 12. AGENTS.md routes live programme status to docs/program/usability-closure/CURRENT.md
FAIL: 13. README.md routes live programme status to docs/program/usability-closure/CURRENT.md
FAIL: 14. docs/program/README.md routes live programme status to docs/program/usability-closure/CURRENT.md
FAIL: 15. docs/product/PRODUCT_DOCTRINE.md routes live programme status to docs/program/usability-closure/CURRENT.md
PASS: 16. docs/queue.md routes live programme status to docs/program/usability-closure/CURRENT.md
FAIL: 17. AGENTS.md names the store bootstrap/resume path (garden_store.py bootstrap)
FAIL: 18. AGENTS.md states the canonical CSVs' change discipline (read-only outside a named data unit)
FAIL: 19. AGENTS.md names every corpus-program module in scripts/ (unnamed: garden_envelope.py, garden_ledger.py, garden_legacy_batch.py, garden_normalize.py, garden_review.py, garden_store.py, garden_submit.py)
FAIL: 20. AGENTS.md names the negative-control harness (run_negative_controls.py)
FAIL: 21. AGENTS.md's resume path resolves the READY work-unit document (docs/program/usability-closure/workunits/)
FAIL: 22. no front door document makes the stale claim [w1-runtime-or-store-absent] (docs/program/README.md -> claims the W1 runtime/store does not exist)
FAIL: 23. no front door document makes the stale claim [w1-in-progress] (docs/program/README.md, docs/queue.md -> claims W1 is still in progress)

RESULT: FAIL (11 failed of 23 checks)
```

After the edits (branch head):

```
RESULT: PASS (23 checks)
```

### 2. grep/search proof

The stale-claim scan asserts two patterns over the five status-bearing documents
(`AGENTS.md`, `README.md`, `docs/program/README.md`, `docs/product/PRODUCT_DOCTRINE.md`,
`docs/queue.md`): `\bno\b … \b(w1 runtime|w1 store|corpus-program (runtime|store|datastore))\b …
\bexists?\b` and `\bw1\b[^.]{0,90}\bin progress\b`.

An independent repo-wide grep (all tracked markdown, excluding the deliberately-unscanned
historical packets) returns **only the U0.2 spec itself**, which quotes the phrases as
requirements:

```
$ grep -rniE "w1 runtime code exists|w1[^.]{0,90}in progress" --include=*.md . \
    | grep -v '^./docs/program/W1_' | grep -v '^./GARDEN_' | grep -v '^./docs/audit/'
./docs/program/usability-closure/workunits/U0.2_FRONT_DOOR.md:45:No canonical front-door doc claims that W1 runtime/store does not exist or that W1 is still in progress.
./docs/program/usability-closure/workunits/U0.2_FRONT_DOOR.md:73:Search for contradictory live-status claims, especially "no W1 runtime/store", "W1 in progress", stale command lists, and ambiguous source-of-truth statements.
```

### 3. Negative controls

Five controls registered in `scripts/run_negative_controls.py` under
`scripts/check_front_door.py` (table 47 → **52** controls, **15** checkers). Each was measured
in the harness's throwaway copy and fires with the **exact** aimed first `FAIL:` line:

| control | mutation | first `FAIL:` line |
|---|---|---|
| `fd1` | `docs/program/README.md` reverts to naming the W1 runtime as non-existent | `FAIL: 22. no front door document makes the stale claim [w1-runtime-or-store-absent] (docs/program/README.md -> claims the W1 runtime/store does not exist)` |
| `fd2` | `AGENTS.md` stops naming `garden_review.py` | `FAIL: 19. AGENTS.md names every corpus-program module in scripts/ (unnamed: garden_review.py)` |
| `fd3` | `docs/queue.md` flips U1.1's status to `READY` (two READY units) | `FAIL: 10. docs/queue.md marks exactly one unit READY in the usability-closure section (found 2)` |
| `fd4` | `README.md` stops routing live status to CURRENT.md | `FAIL: 13. README.md routes live programme status to docs/program/usability-closure/CURRENT.md` |
| `fd5` | `CURRENT.md` loses its `## Last completed unit` heading | `FAIL: 2. CURRENT.md keeps its required structure (missing '## Last completed unit')` |

```
$ python3 scripts/run_negative_controls.py --checker scripts/check_front_door.py
checkers: 1 of 15 selected, 0 skipped
controls: 5 fired, 0 not fired of 5 selected (52 registered in the table)
RESULT: PASS (5 controls fired, 9 harness self-tests) [negative controls]
```

`fd3` deliberately anchors on the **U1.1** line rather than on the unit that is currently READY:
a control anchored on today's READY line would rot the moment the unit closes out.

### 4. The must-stay-green half: withdrawn, and why (a real defect, filed not fixed)

A sixth control `fd6` was authored as `expect_fail=None` — the harness's documented
"contract-preserving edit must stay GREEN" case. It was **withdrawn** because the harness cannot
pass it:

```
ok   fd1 … ok   fd5 
FAIL: scripts/check_front_door.py fd6 (GREEN_OK) -- stayed green as required
summary
  controls: 5 fired, 1 not fired of 6 selected (53 registered in the table)
RESULT: FAIL (1 of 6 selected controls failed, 0 self-test(s) failed) [negative controls]
```

`judge()` returns `GREEN_OK` for that case and `docs/architecture/NEGATIVE_CONTROLS.md` documents
`GREEN_OK` as passing ("a contract-preserving edit stayed green, as the control requires"), but
`report()` counts every non-`FIRED` verdict as "not fired" and exits 1. **Filed as issue #56**
and recorded in `docs/queue.md` ("Open — infra") rather than fixed inside a front-door unit: a
harness change is a change to the mechanism every checker depends on.

So the false-positive direction is covered here by a **local throwaway battery**
(`/tmp/u02_staygreen.py`, in a `copytree` of the repo — nothing in the repo tree is touched),
which applies six legitimate edits and requires the checker to stay green:

```
PASS: reflow a README paragraph (whitespace only) -- stayed green (RESULT: PASS (23 checks))
PASS: reword W0's historical scope sentence -- stayed green (RESULT: PASS (23 checks))
PASS: reflow AGENTS.md's CSV-discipline paragraph -- stayed green (RESULT: PASS (23 checks))
PASS: extend CURRENT.md's frontier sentence -- stayed green (RESULT: PASS (23 checks))
PASS: retitle README's current-state heading -- stayed green (RESULT: PASS (23 checks))
PASS: swap two command bullets in AGENTS.md -- stayed green (RESULT: PASS (23 checks))
PASS: all 6 legitimate edits together -- stayed green (RESULT: PASS (23 checks))

RESULT: PASS (7 legitimate edits accepted)
```

This is evidence, but it is *not* evidence CI re-applies — that is exactly what issue #56 costs.

### 5. Fresh-agent dry run (cold start, files only)

A fresh subagent was given **only** the entry point and told to follow the path `AGENTS.md`
itself prescribes, with no access to this session's context, and to answer the eight acceptance
questions from files alone.

Verdict returned:

> `DRY RUN: PASS — a cold-start agent reading only AGENTS.md and the path it names can answer
> all eight questions without archaeology. Caveat (not disqualifying): the prescribed path does
> contain two stale/false status sentences … so the agent must reconcile CURRENT against
> README/AGENTS rather than trusting CURRENT's prose verbatim.`

All eight questions were answered with a file path: project identity (AGENTS.md /
PRODUCT_DOCTRINE.md); what is usable now (CURRENT.md §"What is usable now"); W1 and Gate B state
(README.md, CURRENT.md, program/README.md); current gate (CURRENT.md §Gate); the one READY unit
(CURRENT.md + queue.md); the bootstrap command (AGENTS.md §"How to resume work" → step 5);
where discovered work goes (AGENTS.md step 7); what must not be started (AGENTS.md
§"What requires human/provenance review" + queue's "Explicitly NOT started").

Both false claims it flagged are fixed in this branch:

1. `docs/program/README.md`: "Current data and validators are untouched: `quotes.csv` and
   `sources.csv` are byte-identical to `main`" (contradiction table row 4);
2. `CURRENT.md`'s frontier sentence naming the front-door docs as still needing repair
   (row 16).

The dry run was executed against the PR head, i.e. *before* the closeout commit advances
`CURRENT.md`'s READY/last-completed fields — the frontier sentence was reworded in this branch so
that it is true both before and after the merge.

## Issue #27 disposition

Issue #27 asked for the corpus-program command surface and the CSV read-only rule in
`AGENTS.md`. It was closed as COMPLETED once already with the file byte-unchanged, which is why
the repo's rule is to check the artefact and not the tracker.

- Artefact check on the branch: `grep -c 'garden_' AGENTS.md` → **7** (was 0);
  `grep -c 'run_negative_controls.py' AGENTS.md` → 1; `grep -ci 'read-only' AGENTS.md` → 1.
- Its second premise no longer holds: it says the change "needs an operator edit (or an explicit
  policy exception)" because writes are refused by tool policy. On 2026-09-17 an `AGENTS.md` edit
  succeeded directly in this environment (a `patch` probe, reverted, then the real edit), so the
  file is editable and the issue is satisfied by this unit.
- The read-only rule is recorded as **history**: W1 is complete, so the rule is no longer live
  law; what is live is that the CSVs change only inside a named data unit.
- Disposition: **close deliberately by comment with this evidence after the merge** — never with
  a closing keyword in this handoff, which becomes the PR body.

## Limits of the guard (stated, not hidden)

- Rows 4, 8, 9, 15 and 16 of the contradiction table are review-caught, not check-caught. A
  general "present-tense claim inside a historical section" detector was not built: pattern
  matching on `are byte-identical` fires on dozens of legitimate *historical* queue entries, and
  a guard that fires on history is worse than no guard. The check is deliberately scoped to (a)
  routing, (b) READY-unit agreement, (c) `AGENTS.md` naming modules derived from the tree, and
  (d) two named stale-claim shapes.
- The READY/queue agreement check compares two independently-parsed fields, so it catches a
  disagreement but cannot know which side is *right*.
- `check 19` derives its module list from `scripts/garden_*.py`. Adding a corpus-program module
  before naming it in `AGENTS.md` will fail CI — that is the intended behaviour (a new surface
  must reach the front door), and the failure message names the unnamed module.
- The checker reads only the repository. It cannot tell whether a *true* statement is the right
  thing to say; it falsifies the specific drift classes issue #27 belongs to.

## Files deliberately untouched

- **All historical evidence:** `docs/program/W0_GATE_REPORT.md`, `docs/program/W1_*.md`,
  `docs/audit/**` (both dated snapshots and both gate reviews), and every root
  `GARDEN_*_HANDOFF.md` — verified by `git status`/`git diff --stat` showing no changes.
- **`quotes.csv` / `sources.csv`:** byte-identical to `main`
  (`9766db8c30372efc57752c0b12b373536e4ddb666f52591610ec238e1c3e01a3` /
  `7aafcb67119564201baf700f29143668ed469f59d83aae60f8f99648a11a27da`); this unit changes no data.
- **`data/store/garden.export.txt`:** untouched (no store mutation in this unit).
- **`browser/`:** untouched — no browser change is in U0.2's scope.
- **`.github/workflows/pages.yml`:** untouched (the guarded Pages contract); the new step went
  into `browser-smoke.yml`, which is the workflow that already owns the acceptance checks.

## Discovered follow-ons (queued, not fixed here)

1. **issue #56** — `run_negative_controls.py` counts `GREEN_OK` as a failure, so no
   "must stay green" control can be registered. Queue entry added under "Open — infra".
2. **`check_front_door.py` ships without a must-stay-green control** — a direct consequence of
   #56; the false-positive direction is covered locally only.
3. Not filed, recorded here: the cold-start dry run noted that `CURRENT.md`'s prose is the single
   point of failure for live status. That is by design (one authority is the point), and the
   structural fields are now guarded; the narrative `frontier` sentence is not.

## Verification run on the branch

```
python3 scripts/check_front_door.py                              RESULT: PASS (23 checks)
python3 scripts/check_pages_contract.py                          RESULT: PASS (16 checks)
python3 scripts/validate_quotes.py                               RESULT: PASS
python3 scripts/check_program_contracts.py                       RESULT: PASS
python3 scripts/validate_homepage_preview_export.py              RESULT: PASS
python3 scripts/check_garden_{store,envelope,submit,normalize,review,e2e,ledger,legacy_batch,lifecycle}.py
                                                                 RESULT: PASS (all ten, both interpreters)
python3 scripts/run_negative_controls.py --check                 RESULT: PASS (52 anchors checked)
python3 scripts/run_negative_controls.py --checker scripts/check_front_door.py
                                                                 RESULT: PASS (5 controls fired)
```

## Out-of-scope / stop

No persistence mechanics, admission mechanics, browser changes, ontology cleanup or W2 were
touched. The unit stops here for foreign QA; U0.3 (the real persistent operator canary) is not
started.

## Foreign QA prompt

Review U0.2 as a cold-start agent. Ignore this handoff's explanation at first: starting from
`AGENTS.md`, follow the documented resume path and see whether you can reconstruct current state
without archaeology. Search for contradictory live-status claims, especially "no W1 runtime/store",
"W1 in progress", stale command lists, and ambiguous source-of-truth statements; confirm the
historical packets were not rewritten misleadingly (`git diff --stat` against the base); check the
`AGENTS.md` module-coverage claim against `scripts/garden_*.py` yourself; and try to break
`scripts/check_front_door.py` with your own mutations (a green mutation is a coverage gap). PASS
only if a new agent is routed to CURRENT/queue/decisions and exactly one READY unit without tacit
context.
