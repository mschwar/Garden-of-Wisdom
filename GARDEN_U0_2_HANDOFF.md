# Handoff — U0.2 Truthful front door + current-state routing

**Branch:** `u0.2/front-door` · **Gate:** U0 — resumable workbench · **Unit:** U0.2
**Spec:** `docs/program/usability-closure/workunits/U0.2_FRONT_DOOR.md`

## What this is

An information-architecture repair, not a prose expansion. The front door now says what is
true, and one authority — `docs/program/usability-closure/CURRENT.md` — owns live programme
status while every other front door *routes* to it. The failure class is now falsifiable:
`scripts/check_front_door.py` (29 checks, CI-wired, 9 registered negative controls) fails the
build if a front-door document re-asserts a stale live-status claim, if a document outside the
guarded set starts carrying status-bearing prose, if the queue and CURRENT disagree about which
unit is READY, or if a front door stops naming its own command surface.

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
| 17 | `docs/queue.md` — two live entries ("discovered during W1.4", "discovered during W1.3") | "the file is unchanged at `main` (`grep -c 'garden_' AGENTS.md` → 0, 63 lines, last touched by `31f06e0`)" and "`AGENTS.md` does not describe the corpus-program command surface" — true when filed, false the moment this unit lands | each entry carries a dated `**UPDATED 2026-09-17 (U0.2):**` annotation with the fresh measurement (`AGENTS.md` 119 lines, `grep -c 'garden_' AGENTS.md` → **12**), saying the superseded numbers are kept as the pre-fix record | **review** (found by the cold-start dry run) |
| 18 | `docs/program/usability-closure/CURRENT.md` §"What is usable now" | did not state the corpus-program W1/Gate B position at all, so "W1/Gate B state" was answerable only by way of `docs/queue.md` | adds: "Corpus-program **W1 is complete** (W1.1–W1.6 merged; Gate B accepted 2026-09-13): the candidate workbench runs as `scripts/garden_*.py` over the persisted SQLite store plus the committed mirror … **W2 is not started.**" | **review** (found by the cold-start dry run) |

Rows 4, 8, 9, 15, 16, 17 and 18 are **review-caught, not check-caught** — see "Limits of the guard".
Row 17 is the reason the unit's own dry run was worth running: it is the *mirror image* of the
failure class — a status-bearing entry that quoted a **measurement of the front door** and went
false the moment the front door was fixed.

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
| `fd6` | `docs/RUNBOOK.md` — the command reference AGENTS.md points at — gains a `W1 is in progress` line | `FAIL: 28. no guarded document makes the stale claim [w1-in-progress] (docs/RUNBOOK.md -> describes W1 as in progress / underway / not yet landed)` |
| `fd7` | `CURRENT.md`'s **own** "What is usable now" body asserts the opposite of its fields | `FAIL: 27. no guarded document makes the stale claim [w1-runtime-or-store-absent] (docs/program/usability-closure/CURRENT.md -> describes the W1 runtime/store as absent)` |
| `fd8` | a document *outside* the guarded set starts naming CURRENT.md | `FAIL: 20. fail-closed coverage: no document outside the guarded set names docs/program/usability-closure/CURRENT.md (add to GUARDED or to EXCLUSIONS: docs/program/usability-closure/DEFERRED_NOT_NOW.md)` |
| `fd9` | `AGENTS.md`'s store-lifecycle line loses its `status`/`sync` subcommands | `FAIL: 22. AGENTS.md's command surface carries the whole store lifecycle on one line (garden_store.py + bootstrap + status + sync; found 0)` |

`fd6`–`fd9` were added in the QA-remediation round, one per gap a cold-start reviewer found;
each was measured before registration. `fd3` deliberately anchors on the **U1.1** line rather
than on the unit that is currently READY: a control anchored on today's READY line would rot the
moment the unit closes out.

```
$ python3 scripts/run_negative_controls.py --checker scripts/check_front_door.py
checkers: 1 of 15 selected, 0 skipped
controls: 9 fired, 0 not fired of 9 selected (56 registered in the table)
RESULT: PASS (9 controls fired, 9 harness self-tests) [negative controls]
```

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
which applies legitimate edits and requires the checker to stay green. *(Id note: this withdrawn
stay-green control was first drafted as `fd6`. That id was reused in the remediation round for a
red-direction control, so the withdrawn one is referred to by description here; the committed
table contains `fd1`–`fd9`, all red-direction.)*

```
PASS: reflow a README paragraph (whitespace only) -- stayed green (RESULT: PASS (29 checks))
PASS: reword W0's historical scope sentence -- stayed green (RESULT: PASS (29 checks))
PASS: reflow AGENTS.md's CSV-discipline paragraph -- stayed green (RESULT: PASS (29 checks))
PASS: extend CURRENT.md's frontier sentence -- stayed green (RESULT: PASS (29 checks))
PASS: retitle README's current-state heading -- stayed green (RESULT: PASS (29 checks))
PASS: swap two command bullets in AGENTS.md -- stayed green (RESULT: PASS (29 checks))
PASS: a meta-claim about the old claim (PROGRAM_CHARTER's own Gate U0 wording) -- stayed green (RESULT: PASS (29 checks))
PASS: a new unrelated bullet in CURRENT.md's usable-now list -- stayed green (RESULT: PASS (29 checks))
PASS: all 8 legitimate edits together -- stayed green (RESULT: PASS (29 checks))

RESULT: PASS (9 legitimate edits accepted)
```

**This battery earned its keep twice, and the second time is a finding.** Its two added cases
(round 2) were the meta-claim wording — `PROGRAM_CHARTER.md`'s own Gate U0 criterion, "no longer
claim W1 runtime does not exist" — and an unrelated new bullet. The first **failed**: the guard's
then-fixed-width lookbehind `(?<!claims )` does not block `claims **the** W1 runtime …`, so the
charter's own acceptance criterion was a false positive, and so was the same sentence with an
article. The fix replaces the lookbehinds with an explicit meta-claim guard (`META_CLAIM_RE` over
the 46 characters preceding a match), which is the only mechanism that can express "a statement
about the claim is not the claim" at variable distance. Without a must-stay-green direction this
would have shipped as a check that fails on a *correct* document — exactly the defect class this
repo's Pages-contract review found three of.

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
(README.md, CURRENT.md, docs/program/README.md); current gate (CURRENT.md §Gate); the one READY
unit (CURRENT.md + queue.md); the bootstrap command (AGENTS.md §"How to resume work" → step 5);
where discovered work goes (AGENTS.md step 7); what must not be started (AGENTS.md
§"What requires human/provenance review" + queue's "Explicitly NOT started").

It reported **three** problems, all fixed in this branch:

1. `docs/program/README.md`: "Current data and validators are untouched: `quotes.csv` and
   `sources.csv` are byte-identical to `main`" — a live-sounding claim in a 2026-09-12 section,
   false since D7/D8 changed both CSVs (contradiction table row 4).
2. `CURRENT.md`'s frontier sentence naming the front-door docs as still needing repair — the
   pointer contradicting the tree it points at (row 16). It reconciled them by running the guard
   rather than trusting either document, which is the behaviour the unit wants.
3. `docs/queue.md`'s two live issue-#27 entries quoting `grep -c 'garden_' AGENTS.md` → 0 and
   63 lines (row 17), plus the observation that `AGENTS.md` never names Gate B, so question 3 was
   reachable only through `docs/queue.md` (row 18: CURRENT.md now states the W1/Gate B position).

Its own words on the closing point: *"The weakness is at that single source: CURRENT.md is
correctly structured and names the right gate/READY unit, but its own 'Current frontier' prose
contains a stale status claim … so the routing is unambiguous but CURRENT's narrative sentence
about the front door is not itself trustworthy."* That is now fixed, and it is recorded as a
standing limit rather than claimed away: the structural fields are guarded, the narrative
sentence is not.

The dry run was executed against the PR head, i.e. *before* the closeout commit advances
`CURRENT.md`'s READY/last-completed fields — the frontier sentence was reworded in this branch so
that it is true both before and after the merge.

**Self-correction worth recording:** the first draft of the row-17 annotation said `AGENTS.md`
"is 128 lines". `wc -l AGENTS.md` returns **119**. The wrong number was caught by re-running the
measurement before committing and corrected in place — the point of the unit is that quoted
measurements must be read off the tree, and an annotation asserting a stale count would have been
a fourth instance of the very defect.

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

- Rows 4, 8, 9, 15, 16, 17 and 18 of the contradiction table are review-caught, not check-caught. A
  general "present-tense claim inside a historical section" detector was not built: pattern
  matching on `are byte-identical` fires on dozens of legitimate *historical* queue entries, and
  a guard that fires on history is worse than no guard. The check is deliberately scoped to (a)
  routing, (b) READY-unit agreement, (c) `AGENTS.md` naming modules derived from the tree, and
  (d) two named stale-claim shapes.
- **The stale-measurement class (row 17) is not automatable with this unit's design, and this is a
  deliberate limit.** A guard could forbid `grep -c 'garden_' AGENTS.md` from appearing next to a
  zero count — but the repo's own doctrine requires a superseded number to be **annotated in
  place**, i.e. the annotation must be allowed to quote the old value. A pattern that forbids the
  quote forbids the required annotation. The mitigation is the doctrine itself: re-measure in the
  same unit that changes the artefact (which is how the 128 → 119 error was caught before commit).
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

## Foreign QA (round 1) and the remediation it produced

An independent cold-start reviewer (own harness, own mutations, no access to this session) was
given the commit under review and told to try to break the claims. Verdict: **CONDITIONAL PASS**,
with 22 mutations of its own (`M1`–`M11`, `T1`, `L1`–`L4`, `G1`–`G6`) and ten findings.

It confirmed every positive claim independently: `AGENTS.md`'s "324 rows / four verified donors /
320 unverified" matches `quotes.csv`; all 7 `scripts/garden_*.py` modules are named; the 9
`check_garden_*` surfaces match the 9 scripts on disk; `garden_store.py` really has
`bootstrap`/`status`/`sync`; both Gate packet paths exist; and its own 4 legitimate edits stayed
green. Its verdict on the routing: *"the routing is unambiguous."*

The findings that mattered, and what changed:

| # | severity | finding | disposition in this branch |
|---|---|---|---|
| 1 | **high** | `SCANNED` was a hard-coded five-file list, so `docs/RUNBOOK.md` — which `AGENTS.md` itself calls the command reference — could carry "W1 is in progress" and the guard exited 0 (its mutation `G1`) | **fixed.** The guarded set is still explicit, but a **derived coverage check** now fails if any non-excluded markdown file in the tree names CURRENT.md and is not guarded, and `RUNBOOK.md` is now routing-checked *and* scanned. Exclusion entries are themselves checked for rot. Regression control: `fd6`, `fd8` |
| 2 | **high** | the status authority's own body was unchecked: replacing `CURRENT.md`'s "What is usable now" with "Nothing is usable yet; no corpus-program datastore exists and W1 is in progress" still passed (its mutation `G2`) | **fixed.** `CURRENT.md` is now in the guarded set, and a check asserts the section still lists at least one item. Regression control: `fd7` |
| 3 | medium | `STALE_CLAIMS` were phrasing-bound: "the W1 runtime has not landed yet … remains underway" passed (its mutation `G3`) | **fixed.** The in-progress pattern now covers `underway` / `not yet landed` / `has not landed`, and a third shape covers "<subject> does not exist". |
| 4 | medium | `RESUME.md` and `START_GARDEN_CORPUS_PROGRAM.md` are front doors by name and use but were outside the guarded set (its `G5`, `G6`) | **partly fixed.** The coverage check now catches any such document the moment it names CURRENT (`RESUME.md`, `OPERATOR_RUNBOOK.md`, `EXECUTION_MAP.md`, `QUEUE_PATCH.md` and the charter are now guarded); `START_GARDEN_CORPUS_PROGRAM.md` remains a pointer to the seed packet and is judged historical, not a status surface — recorded, not silently dropped. |
| 5 | medium | `check_front_door.py` ships with no must-stay-green control (harness defect, issue #56) | **accepted as a limit, filed.** See "Limits" and issue #56; the local battery covers the direction, CI does not. |
| 6 | medium | two live queue entries quoted measurements of the front door itself (row 17) | **fixed** before the review landed — the reviewer confirmed it was self-disclosed, not hidden. |
| 7 | low | check 17 was satisfied by any `bootstrap` token near `garden_store.py`, so the command-surface line could be deleted wholesale (its mutation `M4`) | **fixed.** The check now requires the whole store lifecycle — `bootstrap` **and** `status` **and** `sync` — on one line. Regression control: `fd9` |
| 8 | low | `docs/program/README.md`'s W0 scope note reads as live state to a skimmer | **fixed earlier in this branch** (contradiction-table row 4). |
| 9 | low | the tree was being edited concurrently during the review | **expected**; the reviewer labelled which commit it attacked (`c6e7099`) and the round-2 head is this one, so a re-review is the remaining step. |
| 10 | low | the green-while-broken search stopped at five confirmed gaps rather than exhausting the space | **accepted**; the four it could reach are closed above with a control each. |

The review's own scope note is worth keeping: it did **not** re-run its battery against the
remediated head. Round 2 therefore also caught a false positive the review could not see — see
the must-stay-green battery below, which is why that direction matters.

## Verification run on the branch

```
python3 scripts/check_front_door.py                              RESULT: PASS (29 checks)   [both interpreters]
python3 scripts/check_pages_contract.py                          RESULT: PASS (16 checks)   [both interpreters]
python3 scripts/validate_quotes.py                               RESULT: PASS                [both interpreters]
python3 scripts/check_program_contracts.py                       RESULT: PASS                [both interpreters]
python3 scripts/validate_homepage_preview_export.py              RESULT: PASS                [both interpreters]
python3 scripts/check_garden_{store,envelope,submit,normalize,review,e2e,ledger,legacy_batch,lifecycle}.py
                                                                 RESULT: PASS (all ten, both interpreters)
python3 scripts/run_negative_controls.py                         RESULT: PASS (56 controls fired, 9 harness self-tests)
                                                                 checkers: 15 of 15 selected, 0 skipped
python3 scripts/run_negative_controls.py --check                 RESULT: PASS (56 anchors checked)
python3 scripts/run_negative_controls.py --checker scripts/check_front_door.py
                                                                 RESULT: PASS (9 controls fired)
python3 /tmp/u02_staygreen.py                                    RESULT: PASS (9 legitimate edits accepted)
shasum -a 256 quotes.csv sources.csv       9766db8c… / 7aafcb67…  (byte-identical)
```

## Limits of the guard (stated, not hidden)

- **The guarded set is closed, not total.** The coverage check makes the set *fail-closed* for
  any document that names CURRENT.md, so a new status-bearing front door cannot escape the scan.
  A document that carries a stale claim and never names CURRENT.md (e.g. an architecture note) is
  still invisible — that is the residual class, and it is why the check's failure message says
  "add to GUARDED or to EXCLUSIONS" rather than pretending to be exhaustive.
- **The stale-claim scan is pattern-based, over three named shapes.** A sufficiently novel
  rewording of the same falsehood passes. This is deliberate: the alternative — a semantic check —
  would be non-deterministic, and a guard that fires on legitimate historical prose (the queue's
  closed entries, the append-only log, the frozen transcripts) is worse than no guard. The three
  shapes are the ones this repo has actually produced.
- **A meta-claim is not the claim.** "no longer claims the W1 runtime does not exist" is the
  charter's own Gate U0 criterion, so a claim/assert/report verb in the 46 characters before a
  match suppresses it (`META_CLAIM_RE`). The cost is symmetric: a *real* claim phrased as "the
  README claims W1 is in progress" is also suppressed. That trade is recorded rather than hidden,
  and it is covered by the local must-stay-green battery.
- **Rows 4, 8, 9, 15, 16, 17 and 18 of the contradiction table are review-caught, not
  check-caught.** A general "present-tense claim inside a historical section" detector was not
  built: pattern matching on `are byte-identical` fires on dozens of legitimate *historical* queue
  entries.
- **The stale-measurement class (row 17) is deliberately not automated.** A guard could forbid
  `grep -c 'garden_' AGENTS.md` next to a zero count — but the repo's doctrine requires a
  superseded number to be **annotated in place**, i.e. the annotation must be allowed to quote the
  old value. A pattern forbidding the quote forbids the required annotation. The mitigation is the
  doctrine: re-measure in the unit that changes the artefact (which is how the 128 → 119 error was
  caught before commit).
- **No CI-reapplied must-stay-green control** (issue #56). The false-positive direction is
  evidenced by a throwaway battery only; a future check could gain a false positive that CI would
  not catch. Filed, not hidden.
- The READY/queue agreement check compares two independently-parsed fields, so it catches a
  disagreement but cannot know which side is *right*.
- Check 24 derives its module list from `scripts/garden_*.py`. Adding a corpus-program module
  before naming it in `AGENTS.md` will fail CI — intended (a new surface must reach the front
  door), and the failure names the unnamed module.
- The checker reads only the repository. It cannot tell whether a *true* statement is the right
  thing to say; it falsifies the specific drift classes issue #27 belongs to.

## Out-of-scope / stop

No persistence mechanics, admission mechanics, browser changes, ontology cleanup or W2 were
touched. The unit stops here; U0.3 (the real persistent operator canary) is not started.

## Foreign QA prompt

Review U0.2 as a cold-start agent. Ignore this handoff's explanation at first: starting from
`AGENTS.md`, follow the documented resume path and see whether you can reconstruct current state
without archaeology. Search for contradictory live-status claims, especially "no W1 runtime/store",
"W1 in progress", stale command lists, and ambiguous source-of-truth statements; confirm the
historical packets were not rewritten misleadingly (`git diff --stat` against the base); check the
`AGENTS.md` module-coverage claim against `scripts/garden_*.py` yourself; and try to break
`scripts/check_front_door.py` with your own mutations (a green mutation is a coverage gap).

Round 2 additionally asks the reviewer to attack the **remediation**: (a) find a document that
carries a stale claim and must be caught, but is neither guarded nor excluded — the coverage check
should name it; (b) find a *legitimate* front-door edit that the guard rejects (a false positive —
especially any meta-claim wording, since that is where the last false positive lived); (c) confirm
each of the round-1 findings above is actually closed by re-running the reviewer's own `G1`, `G2`,
`G3`, `M4`, `G5` and `G6` mutations against this head, and say plainly which are still open. PASS
only if a new agent is routed to CURRENT/queue/decisions and exactly one READY unit without tacit
context, and no round-1 finding reopens.
