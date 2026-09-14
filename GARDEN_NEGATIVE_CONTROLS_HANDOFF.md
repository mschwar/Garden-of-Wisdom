# Handoff — the checkers' negative controls become a committed, CI-wired table

**Branch:** `ci/negative-control-harness` · **PR:** [#46](https://github.com/mschwar/Garden-of-Wisdom/pull/46)
**Records:** issue [#43](https://github.com/mschwar/Garden-of-Wisdom/issues/43) (closed deliberately
after the merge, never by a closing keyword) · **Filed out of scope:**
[#45](https://github.com/mschwar/Garden-of-Wisdom/issues/45)

> Closing-keyword hazard note: this file is reused verbatim as the PR body, so no sentence here
> writes a `close`/`fix`/`resolve` keyword followed by an issue number for an issue that must
> stay open. #43 is closed with `gh issue close 43 --comment …` after the merge.

## Landed

**Merge:** `<filled in the follow-up docs commit on main>` · **PR:** #46 · **CI:** `<run ids>` ·
**Live acceptance:** `<recorded in the follow-up docs commit>`.

## What this unit is

Not a corpus-program unit: no W2 work, no store surface, no schema, no state vocabulary, no
`quotes.csv`/`sources.csv` edit. It closes issue #43, which had two measured halves:

1. **The evidence was not independently verifiable.** Every checker's negative controls were a
   table in a `GARDEN_*_HANDOFF.md`, produced by a throwaway `/tmp` harness deleted with the
   unit. The foreign QA pass on the Pages guard unit reported: *"I could not verify '16 negative
   controls, all fired as aimed' — that requires reading the author's harness, which was out of
   bounds for this pass."*
2. **A vacuous check was undetectable.** `check_pages_contract.py`'s `EXPECTED_CHECKS` fails when
   a check is *deleted* — but foreign QA mutation `p36` gutted a check body to `return None`
   while keeping its registration, and the run stayed **green**.

Both are now machine-checked on every PR and every push to `main`.

## What changed

| File | Change |
|---|---|
| `scripts/run_negative_controls.py` | **new** — the harness and its 36-control table (stdlib only) |
| `.github/workflows/browser-smoke.yml` | +8 lines — one new step, "Machine-check the checkers' negative controls", and `timeout-minutes` 15 → 30 for it |
| `docs/architecture/NEGATIVE_CONTROLS.md` | **new** — the design doc and the control-by-control record |
| `docs/RUNBOOK.md` | new section "Machine-check the checkers' negative controls"; the Pages-guard section no longer says the harness is "deliberately not part of this unit" |
| `docs/DECISIONS.md` | new dated entry recording the seven rulings and their rejected alternatives |
| `docs/queue.md` | the infra item closed; the five coverage gaps filed as #45 |
| `GARDEN_NEGATIVE_CONTROLS_HANDOFF.md` | this file |

`quotes.csv` / `sources.csv` are **unchanged by this unit**, byte-identical to `main`:
`b3bb7848…` (quotes.csv) / `7aafcb67…` (sources.csv). Note for a future reader: those are the
**D7-updated** bytes — the `5675d7e6…` / `10b4c156…` pair quoted by every pre-D7 handoff and doc
is the state *before* the D7 unit rewrote the two CSVs, and no unit had recorded the current pair
before this one (the D7 close-out did not). No new dependency, no change to `requirements-dev.txt`,
`pages.yml` untouched, `check_pages_contract.py` untouched.

## How the harness works

`python3 scripts/run_negative_controls.py` — stdlib only, exits 0 with `RESULT: PASS` / non-zero
with `RESULT: FAIL` and one `FAIL:` line per broken control, like every other checker here.

1. **Copy, never mutate.** The working tree is copied to a throwaway directory (excluding
   `.git`/`.venv`/`node_modules`/`__pycache__`); checkers run with `cwd` inside the copy, and the
   one file a control mutated is restored from its pristine bytes in a `finally`.
2. **Anchor first** — the anchor must occur **exactly once** in its target, else `ROTTEN_ANCHOR`
   ("re-derive this control") rather than a silent skip or a mutation of the wrong occurrence.
3. **Baseline first** — each checker is run unmutated before its controls; an already-red
   baseline is reported as itself and its controls are **not** credited with firing.
4. **One mutation, one run, one asserted line** — the **first** `FAIL:` line must equal the
   control's expectation **exactly** (never `in`; substring matching is how this repo twice
   shipped a silent pass). `normalize_paths()` masks the copy root as `<copy>` and the temp root
   as `<tmp>` on both sides, so a committed expectation is portable to CI's Linux without
   weakening the comparison.

Verdicts: `FIRED` and `GREEN_OK` pass; `COVERAGE_GAP`, `MASKED`, `ROTTEN_ANCHOR`,
`FALSE_POSITIVE`, `CRASH`, `INCONSISTENT`, `TIMEOUT` fail the run. **`COVERAGE_GAP` is what
closes `p36`:** with a check body gutted, the control aimed at that check cannot produce its
`FAIL:` line, so the harness reports the gap and exits non-zero even though the count guard is
satisfied.

Modes: `--check` (anchors only, no checker run), `--list` (print the table), `--checker` (narrow
a local run), `--require-all` (a capability skip is an error; implied when `CI` is set).

## Harness self-tests (9, run on every invocation)

Five verdicts proven end to end through the real copy/mutate/run path against a synthetic
mini-repo, plus four table-hygiene guards:

| id | control | |
|---|---|---|
| `s1` | a mutation that breaks a check is reported `FIRED` | verdict |
| `s2` | a mutation that changes nothing observable is a `COVERAGE_GAP` | verdict |
| `s3` | a different check refusing first is reported `MASKED` | verdict |
| `s4` | an anchor that no longer exists is reported `ROTTEN_ANCHOR` | verdict |
| `s5` | a contract-preserving edit that goes red is a `FALSE_POSITIVE` | verdict |
| `s6` | an empty table is refused, not passed vacuously | table |
| `s7` | a checker with no controls is refused | table |
| `s8` | a deleted control registration is caught by the count guard | table |
| `s9` | a narrowed `--checker` selection is never validated against the whole-table count guard | table |

`run_self_tests()` builds the synthetic repo in a temp dir and drives `run_specs()` — the same
code path the real table uses — so these are end-to-end controls of the harness, not unit tests
of a helper.

## The controls (36 over 12 checkers)

`python3 scripts/run_negative_controls.py --list` prints each control with its exact anchor and
replacement; `docs/architecture/NEGATIVE_CONTROLS.md` tabulates them with the asserted `FAIL:`
line. The full transcript of the committed run is pasted below.

Three things about how the table was authored, because they are the difference between evidence
and decoration:

- **Every entry was re-derived from the code and re-run through this harness**, not copied from a
  handoff's prose. Ten discovery passes proposed 36 mutations; every one of them reproduced
  exactly on the first full run of the committed table.
- **`validate_quotes.py`'s two policy guards are now genuinely controlled.** `c4` reverts the
  score to one directional ratio and expects the ORDER guard's line; `c6` narrows the sweep back
  to per-`tradition` groups and expects the SCOPE guard's line, which names exactly the five
  cross-tradition overlaps #34's decision recorded (`39 ~ 53` at 0.82, `50 ~ 318`, `78 ~ 173`,
  `87 ~ 187`, `175 ~ 332`). That is the "policy has no automated falsifier" defect #31 filed,
  now machine-checked rather than asserted.
- **One locally-measured control is deliberately excluded**: dropping `overflow-wrap: anywhere`
  from `browser/style.css` fails the smoke test with a `FAIL:` line embedding rendered geometry
  (`document scrollWidth=355 > clientWidth=320 … {'right': 448, 'tag': 'DD'}`), which depends on
  the runner's font stack. An exact expectation would be a CI-only false alarm. Recorded in
  `DECISIONS.md` and the design doc instead of committed with a loose match.

## Negative controls for the harness itself (measured, in a `/tmp` copy)

Harness: `/tmp/harness_controls.py` (throwaway). Each case mutates a **copy** of the repo and
then runs the copy's own harness with `--checker scripts/check_pages_contract.py` (fast), asserting
the verdict the harness must reach. A case that does not reach it is a defect in the harness.

```text
ok   h1 p36 replayed for real: the uploaded-path check's body is gutted to `return None`
       exit=1 wanted='p2 (COVERAGE_GAP)'
       | FAIL: scripts/check_pages_contract.py p2 (COVERAGE_GAP) -- expected a FAIL line but the run stayed GREEN -- this check has no falsifier (or the mutation no longer models a real break)
       | RESULT: FAIL (1 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
ok   h2 p36 replayed on a second guard: the app.js fetch check's body is gutted
       exit=1 wanted='p4 (COVERAGE_GAP)'
       | FAIL: scripts/check_pages_contract.py p4 (COVERAGE_GAP) -- expected a FAIL line but the run stayed GREEN -- this check has no falsifier (or the mutation no longer models a real break)
       | RESULT: FAIL (1 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
ok   h3 a control's replacement is rewritten to equal its anchor (a no-op mutation)
       exit=1 wanted='p2 (ROTTEN_ANCHOR)'
       | FAIL: scripts/check_pages_contract.py p2 (ROTTEN_ANCHOR) -- the replacement is identical to the anchor: the mutation is a no-op (.github/workflows/pages.yml)
       | RESULT: FAIL (1 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
ok   h4 a control's expected FAIL line is rewritten to a strict substring of the real one
       exit=1 wanted='p2 (MASKED)'
       | FAIL: scripts/check_pages_contract.py p2 (MASKED) -- a different check refused first; expected "FAIL: the uploaded path is the repo root ('.')"
       | RESULT: FAIL (1 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
ok   h5 one control registration is deleted (EXPECTED_CONTROLS no longer matches)
       exit=1 wanted='EXPECTED_CONTROLS is 35 but 36 are registered'
       | FAIL: control table -- EXPECTED_CONTROLS is 35 but 36 are registered; re-derive this harness rather than deleting a control
       | RESULT: FAIL (1 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
ok   h6 an anchor no longer occurs exactly once (its line is duplicated in the target)
       exit=1 wanted='p4 (ROTTEN_ANCHOR)'
       | FAIL: scripts/check_pages_contract.py p4 (ROTTEN_ANCHOR) -- anchor occurs 2 time(s) in the target, expected exactly 1 -- the file changed under the control table; re-derive this control (bro
       | RESULT: FAIL (1 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
ok   h7 the checker is already red before any mutation (a wrong EXPECTED_CHECKS)
       exit=1 wanted='FAIL: baseline'
       | FAIL: baseline -- scripts/check_pages_contract.py is already red on the unmutated copy: exit=1 RESULT: FAIL (1 of 16 checks failed)
       | RESULT: FAIL (1 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
ok   h8 the whole table declares itself empty
       exit=1 wanted='EXPECTED_CONTROLS must be positive'
       | FAIL: control table -- EXPECTED_CONTROLS is 0 but 36 are registered; re-derive this harness rather than deleting a control
       | FAIL: control table -- EXPECTED_CONTROLS must be positive, else the count guard is a no-op
       | RESULT: FAIL (2 of 4 selected controls failed, 0 self-test(s) failed) [negative controls]
```

**`h5` found a real defect in the harness and it is fixed in this branch.** The count guard was
evaluated against the *selected* checkers, so any `--checker` run failed with
`EXPECTED_CONTROLS is 36 but 4 are registered` — i.e. the one mode that exists for local
iteration was unusable. `report()` now always receives the whole table (`table=CHECKERS`), the
run prints its scope, and self-test `s9` pins the invariant. `h4` initially failed for a reason
of its own: my edit built an 8-argument `Mutation(...)` and the harness refused to even import —
which is the correct behaviour (a syntax error is loud, not silent), and is recorded here rather
than quietly repaired.

`h1` and `h2` are the `p36` replay in the form the issue asked for: a real check body gutted to
`return None` **with its registration intact** now produces `COVERAGE_GAP` for the control aimed
at it, and the run exits 1 — where before, the only guard was a count of registrations that the
gutting does not change.

## Out-of-scope findings (measured, filed, NOT fixed)

Issue [#45](https://github.com/mschwar/Garden-of-Wisdom/issues/45) — five checker coverage gaps.
A green mutation is the signature of a documented contract with no falsifier; the authoring pass
found five, and **each was re-verified independently of the agent that reported it** (fresh copy,
one substitution, checker run from the copy root):

| # | gap | mutation | observed |
|---|---|---|---|
| 1 | `garden_normalize._comparison_view()`'s documented case-folding is unexercised | drop `.casefold()` from the comparison view | `exit=0, 0 FAIL lines, RESULT: PASS` |
| 2 | `check_garden_review.py` never inspects a decision row's `action` vocabulary | rename both `action=` values | `exit=0, 0 FAIL lines, RESULT: PASS` |
| 3 | `check_garden_e2e.py` asserts the live `corpus_state`, not the T-P7 audit row's `to_state` | `("corpus","eligible","candidate_only","T-P7",…)` → `…"eligible"…` | `exit=0, 0 FAIL lines, RESULT: PASS` |
| 4 | D3's "do not widen the `quotes.csv` enum" ruling has no falsifier anywhere | row 30's `verification_status` → `unverifiable` | `exit=0, 0 FAIL lines, RESULT: PASS` |
| 5 | the captures-UPDATE trigger's `RAISE` *message* is unguarded (lowest value) | message text → `'rewritten'` | `exit=0, 0 FAIL lines, RESULT: PASS` |

Not fixed here because each is a *fixture/check* change to the acceptance suite that owns it, not
to the harness — and this unit's mandate was the harness. #45 carries the exact mutation, the
observed output and the fix each one needs.

## Review status (foreign QA)

**Two review passes were run, both as separate subagents with their own mutation code and their
own `/tmp` copies; neither read the author's throwaway harness. Both ran in the same session as
the author — this is a *same-session* review, and the operator may still want a foreign pass.**

**Pass 1 — 14 attacks, then it TIMED OUT before writing a final verdict.** Its per-attack results
are its transcript, outside the repo
(`~/.hermes/cache/delegation/live/deleg_426867d3/task-0.log`) — which is itself the gap #43
recorded. Everything it completed, verbatim:

| attack | what it changed | observed |
|---|---|---|
| 1 | gutted `check_upload_path` to `return None` (registration kept) in its copy | `FAIL: scripts/check_pages_contract.py p2 (COVERAGE_GAP)`, exit 1 |
| 2 | gutted the ledger check that `l1` aims at, to always pass | `COVERAGE_GAP`, exit 1 |
| 3 | rewrote `p1`'s replacement to equal its anchor (no-op) | `p1 (ROTTEN_ANCHOR)`, exit 1 |
| 4 | duplicated a line so `p4`'s anchor occurs twice | `p4 (ROTTEN_ANCHOR)`, exit 1 |
| 5 | replaced `p1`'s expected line with a wrong-but-plausible one | `MASKED`, exit 1 |
| 6 | truncated `p1`'s expected line to a strict substring | `MASKED`, exit 1 — proves exact comparison, not `in` |
| 7a | deleted one control registration | `EXPECTED_CONTROLS is 36 but 35 are registered`, exit 1 |
| 7b | emptied the table (`CHECKERS = ()`) | vacuity guard fired, exit 1 |
| 8 | broke `judge()` to always return the fired verdict | self-tests went red, exit 1 |
| 9 | made the checker red before any mutation | `FAIL: baseline -- … is already red on the unmutated copy`, 0 controls credited fired |
| 10 | ran the author's full harness from the real repo path | `36/36 fired`, exit 0; pre-run `git status` and both CSV hashes snapshotted |
| 11 | rotted an anchor, then `--check` | count/rot guard fired, exit 1 (no checker run) |
| 12 | `--list` vs the table object | control ids and expectations matched |
| 13 | `--checker scripts/smoke_quote_browser.py` where playwright is absent, then with `CI=1` | `SKIP … these controls were NOT run on this machine`, 0 fired; with `CI=1` the required-capability failure appears and the run exits 1 |
| 14 | made a checker print its `FAIL:` line but exit 0 | `INCONSISTENT`, not `FIRED` |

**No attack bypassed the harness.** One observation of its own is worth recording: it noticed
early that a `--checker`-confined run tripped the count guard
(`EXPECTED_CONTROLS is 36 but 4 are registered`) and flagged it as a confound while reading
verdicts. That is the same defect the author's own control `h5` found and fixed in this branch
(`report(..., table=CHECKERS)` + self-test `s9`) — the first seven of its attacks ran against the
pre-fix revision, and its flag and the fix agree. Its attacks 1–14 all target the verdict logic
(`judge`, `run_specs`, `table_problems`, the CLI), which the fix did not touch.

**Pass 2 — time-boxed re-run against the frozen, fixed revision.** `<filled in when it returns>`


## Evidence

**The committed table, both interpreters, verbatim** (`python3` = Homebrew 3.14.5, `/opt/homebrew/bin/python3.12` = CI's interpreter):

```
=== python3 (Homebrew 3.14.5) ===
harness self-tests
PASS: self-test s1 -- a mutation that breaks a check is reported FIRED
PASS: self-test s2 -- a mutation that changes nothing observable is a COVERAGE GAP
PASS: self-test s3 -- a different check refusing first is reported MASKED
PASS: self-test s4 -- an anchor that no longer exists is reported ROTTEN_ANCHOR
PASS: self-test s5 -- a contract-preserving edit that goes red is a FALSE POSITIVE
PASS: self-test s6 -- an empty table is refused, not passed vacuously
PASS: self-test s7 -- a checker with no controls is refused
PASS: self-test s8 -- a deleted control registration is caught by the count guard
PASS: self-test s9 -- a narrowed selection is never validated against the whole-table count guard

throwaway copy: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/negative-controls-jomg4q27/copy

checker scripts/validate_quotes.py  (6 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
ok   c1 a duplicated primary key (row 344 rekeyed onto an existing id)
       first FAIL: FAIL: duplicate ids: ['1']
ok   c2 a dangling source link: sources.csv renames the id row 344 cites
       first FAIL: FAIL: quotes reference source_id not present in sources.csv: ['344']
ok   c3 a controlled-vocabulary regression: row 1's item_type leaves the enum
       first FAIL: FAIL: rows with invalid item_type: ['1']
ok   c4 the near-duplicate score reverts to one directional difflib ratio (issue #31)
       first FAIL: FAIL: near-duplicate detection is row-order dependent: pairs/numbers only in file order [(66, 67, 'same specific citation'), (87, 187, 'text similarity 0.64'), (113, 114, 'text similarity 0.69')], only in reversed order [(66, 67, 'same specific citation; text similarity 0.61'), (113, 114, 'text similarity 0.67'), (189, 216, 'text similarity 0.60')]
ok   c5 the imported locator rule drifts: citation_specificity() always 'generic'
       first FAIL: FAIL: citation rule drift: citation_specificity('Gita 2.47') is 'generic', but this report's ruling assumes 'specific'
ok   c6 the sweep is narrowed back to per-tradition groups (issue #34's reversion)
       first FAIL: FAIL: the near-duplicate sweep is not corpus-wide: pairs/numbers only in the corpus-wide scan [(39, 53, 'text similarity 0.82'), (50, 318, 'text similarity 0.71'), (78, 173, 'text similarity 0.62'), (87, 187, 'text similarity 0.61'), (175, 332, 'text similarity 0.61')], only in the reported sweep []

checker scripts/check_program_contracts.py  (3 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
ok   pc1 S2's wording claim demoted to unverifiable: the record aggregate disagrees
       first FAIL: FAIL: S2: record research_state 'verified' disagrees with the aggregate of its claims ('unverifiable')
ok   pc2 S3's walkthrough names a transition the STATE_MODEL table does not define
       first FAIL: FAIL: S3: transition T-R99 (step 4) is not in the STATE_MODEL table
ok   pc3 the fixture template loses a required envelope field (capture_id)
       first FAIL: FAIL: CANDIDATE_ENVELOPE.md required fields and the fixture template disagree: doc-only=['capture_id'] template-only=[]

checker scripts/validate_homepage_preview_export.py  (2 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS
ok   h1 an exported item's text drifts from the frozen quotes.csv wording
       first FAIL: FAIL: items[0]: text does not match quotes.csv id 3
ok   h2 exact scripture is re-typed as a paraphrase (item_type excerpt -> paraphrase)
       first FAIL: FAIL: items[0]: paraphrase may not be emitted as exact scripture

checker scripts/check_pages_contract.py  (4 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (16 checks)
ok   p1 the upload action major regresses to v3, the one that published ./.gitignore
       first FAIL: FAIL: the upload action major excludes top-level hidden files -- actions/upload-pages-artifact@3 is below the minimum verified major 4 -- its tar invocation does NOT exclude top-level dotfiles, which published ./.gitignore (issue #23)
ok   p2 the artifact is rooted at browser/, so ../quotes.csv 404s and the page is empty
       first FAIL: FAIL: the uploaded path is the repo root ('.') -- the upload path is "'browser/'", not '.': browser/index.html fetches ../quotes.csv, so a differently-rooted artifact renders 0 quotes
ok   p3 include-hidden-files is switched on, republishing top-level dotfiles
       first FAIL: FAIL: the upload step does not include hidden files -- include-hidden-files is 'true': top-level dotfiles would be published (issue #23)
ok   p4 app.js fetch repointed to the wrong root, old path kept in a // comment
       first FAIL: FAIL: browser/app.js still fetches ../quotes.csv and ../sources.csv -- browser/app.js no longer fetches '../quotes.csv'; if the fetch changed, the artifact layout requirement changed with it

checker scripts/smoke_quote_browser.py  (2 control(s), /Users/mschwar/Developer/Garden-of-Wisdom/.venv/bin/python)
baseline: exit=0 RESULT: PASS (0 warning(s))
ok   sm1 matchesSearch() stops narrowing: every search returns all 324 rows
       first FAIL: FAIL: search 'Dhammapada': page never showed 29 quotes within 15000ms (filtered-count='324')
ok   sm2 the card/table empty state loses its message
       first FAIL: FAIL: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada'): empty-state text was 'Nothing to see here.', expected it to contain 'No matching quotes.'

checker scripts/check_garden_store.py  (3 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)
ok   g1 capture immutability: the UPDATE trigger no longer aborts
       first FAIL: FAIL: captures accepted UPDATE: captures are not immutable
ok   g2 the research_state CHECK constraint is dropped (W1.1 review's finding)
       first FAIL: FAIL: the SQL layer accepted research_state = 'maybe' (outside STATE_MODEL.md)
ok   g3 a migration id is renamed: the ledger no longer matches the schema
       first FAIL: FAIL: create-from-empty applied migration ['0001_create_core_v2', '0002_unverifiable_ledger'] into an empty directory

checker scripts/check_garden_envelope.py  (3 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
ok   e1 the serializer loses canonical determinism (sort_keys is load-bearing)
       first FAIL: FAIL: key insertion order cannot change the serialized bytes (sort_keys is load-bearing)
ok   e2 rule 1 stops checking the intake schema version
       first FAIL: FAIL: fixture 'wrong-intake-schema-version' reports exactly rule-1 -- reported []
ok   e3 rule 2 stops refusing an empty captured_text
       first FAIL: FAIL: fixture 'empty-captured-text' reports exactly rule-2 -- reported []

checker scripts/check_garden_submit.py  (2 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)
ok   t1 the capture is trimmed instead of stored byte-for-byte
       first FAIL: FAIL: captured_text is byte-identical to the submitted file (verified against the file bytes) -- 75 vs 78 bytes
ok   t2 the no-normalization-without-a-note refusal is dropped
       first FAIL: FAIL: --candidate-text differing with no note is refused (exit 0, RESULT: FAIL)

checker scripts/check_garden_normalize.py  (3 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (normalization records every change and preserves the capture verbatim; hints are deterministic, cited, and never a state)
ok   n1 the similarity collapses to one directional ratio (asymmetric basis)
       first FAIL: FAIL: the similarity of a pair is symmetric (the same number reaches both candidates' hints)
ok   n2 a shared generic label counts as a specific citation again (ruling 2)
       first FAIL: FAIL: the legacy heuristic flags rows 319 ~ 331 on the shared label 'Oral Tradition', and W1.4 emits no same-reference/same-passage hint for them -- ['same-reference']
ok   n3 the hint rebuild accumulates instead of replacing (the DELETE is lost)
       first FAIL: FAIL: rebuilding every hint exports byte-identical text (derived, deterministic, not appended)

checker scripts/check_garden_review.py  (3 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (all twelve curation transitions audit correctly, the reversal path strands no dimension, and no curation action writes research state)
ok   r1 acceptance no longer fires the required T-P1 corpus follow-on
       first FAIL: FAIL: accept: cand-t01 recorded exactly ['T-C1', 'T-P1'] -- ['T-C1']
ok   r2 curate's OWN required-reason guard is disabled (the backstop remains)
       first FAIL: FAIL: the refusal for an empty reason came from curate's OWN guard ('every curation decision must carry a reason') not a shared/backstop guard -- a decision must carry a reason
ok   r3 a curation action writes research state (invariant 5)
       first FAIL: FAIL: accept: cand-t01 research_state stayed not_started -- in_research

checker scripts/check_garden_e2e.py  (2 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (a messy batch is ingested, normalized, hinted and reviewed while originals, provenance, decision history and duplicate hints all survive, and no curation action implies verification)
ok   x1 the withdrawal path bypasses its state write, stranding a dimension
       first FAIL: FAIL: the reversal strands no dimension: curation=rejected, corpus=candidate_only -- curation=rejected corpus=eligible
ok   x2 the decision log stops being append-only (trigger narrowed to seq)
       first FAIL: FAIL: decisions accepted UPDATE: the log is not append-only

checker scripts/check_garden_ledger.py  (3 control(s), /opt/homebrew/opt/python@3.14/bin/python3.14)
baseline: exit=0 RESULT: PASS (the unverifiable side-car ledger works end to end)
ok   l1 the re-adjudication guard is disabled: a marked row can be re-marked
       first FAIL: FAIL: a duplicate mark is refused by the explicit re-adjudication guard -- unverifiable adjudication for legacy row '30' rejected: UNIQUE constraint failed: legacy_verification.legacy_row_id
ok   l2 the ledger row is written without its research audit row (D3 §2)
       first FAIL: FAIL: mark appends one research audit row (T-R6 from_state derived from the model) -- []
ok   l3 reopen no longer requires the row to be in the ledger
       first FAIL: FAIL: reopen on a missing row was accepted

summary
  checkers: 12 of 12 selected, 0 skipped
  controls: 36 fired, 0 not fired of 36 selected (36 registered in the table)
  harness self-tests: 9 of 9 passed

RESULT: PASS (36 controls fired, 9 harness self-tests) [negative controls]
rc=0

=== python3.12 (CI interpreter) ===
harness self-tests
PASS: self-test s1 -- a mutation that breaks a check is reported FIRED
PASS: self-test s2 -- a mutation that changes nothing observable is a COVERAGE GAP
PASS: self-test s3 -- a different check refusing first is reported MASKED
PASS: self-test s4 -- an anchor that no longer exists is reported ROTTEN_ANCHOR
PASS: self-test s5 -- a contract-preserving edit that goes red is a FALSE POSITIVE
PASS: self-test s6 -- an empty table is refused, not passed vacuously
PASS: self-test s7 -- a checker with no controls is refused
PASS: self-test s8 -- a deleted control registration is caught by the count guard
PASS: self-test s9 -- a narrowed selection is never validated against the whole-table count guard

throwaway copy: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/negative-controls-mk5m7sqr/copy

checker scripts/validate_quotes.py  (6 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
ok   c1 a duplicated primary key (row 344 rekeyed onto an existing id)
       first FAIL: FAIL: duplicate ids: ['1']
ok   c2 a dangling source link: sources.csv renames the id row 344 cites
       first FAIL: FAIL: quotes reference source_id not present in sources.csv: ['344']
ok   c3 a controlled-vocabulary regression: row 1's item_type leaves the enum
       first FAIL: FAIL: rows with invalid item_type: ['1']
ok   c4 the near-duplicate score reverts to one directional difflib ratio (issue #31)
       first FAIL: FAIL: near-duplicate detection is row-order dependent: pairs/numbers only in file order [(66, 67, 'same specific citation'), (87, 187, 'text similarity 0.64'), (113, 114, 'text similarity 0.69')], only in reversed order [(66, 67, 'same specific citation; text similarity 0.61'), (113, 114, 'text similarity 0.67'), (189, 216, 'text similarity 0.60')]
ok   c5 the imported locator rule drifts: citation_specificity() always 'generic'
       first FAIL: FAIL: citation rule drift: citation_specificity('Gita 2.47') is 'generic', but this report's ruling assumes 'specific'
ok   c6 the sweep is narrowed back to per-tradition groups (issue #34's reversion)
       first FAIL: FAIL: the near-duplicate sweep is not corpus-wide: pairs/numbers only in the corpus-wide scan [(39, 53, 'text similarity 0.82'), (50, 318, 'text similarity 0.71'), (78, 173, 'text similarity 0.62'), (87, 187, 'text similarity 0.61'), (175, 332, 'text similarity 0.61')], only in the reported sweep []

checker scripts/check_program_contracts.py  (3 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
ok   pc1 S2's wording claim demoted to unverifiable: the record aggregate disagrees
       first FAIL: FAIL: S2: record research_state 'verified' disagrees with the aggregate of its claims ('unverifiable')
ok   pc2 S3's walkthrough names a transition the STATE_MODEL table does not define
       first FAIL: FAIL: S3: transition T-R99 (step 4) is not in the STATE_MODEL table
ok   pc3 the fixture template loses a required envelope field (capture_id)
       first FAIL: FAIL: CANDIDATE_ENVELOPE.md required fields and the fixture template disagree: doc-only=['capture_id'] template-only=[]

checker scripts/validate_homepage_preview_export.py  (2 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS
ok   h1 an exported item's text drifts from the frozen quotes.csv wording
       first FAIL: FAIL: items[0]: text does not match quotes.csv id 3
ok   h2 exact scripture is re-typed as a paraphrase (item_type excerpt -> paraphrase)
       first FAIL: FAIL: items[0]: paraphrase may not be emitted as exact scripture

checker scripts/check_pages_contract.py  (4 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (16 checks)
ok   p1 the upload action major regresses to v3, the one that published ./.gitignore
       first FAIL: FAIL: the upload action major excludes top-level hidden files -- actions/upload-pages-artifact@3 is below the minimum verified major 4 -- its tar invocation does NOT exclude top-level dotfiles, which published ./.gitignore (issue #23)
ok   p2 the artifact is rooted at browser/, so ../quotes.csv 404s and the page is empty
       first FAIL: FAIL: the uploaded path is the repo root ('.') -- the upload path is "'browser/'", not '.': browser/index.html fetches ../quotes.csv, so a differently-rooted artifact renders 0 quotes
ok   p3 include-hidden-files is switched on, republishing top-level dotfiles
       first FAIL: FAIL: the upload step does not include hidden files -- include-hidden-files is 'true': top-level dotfiles would be published (issue #23)
ok   p4 app.js fetch repointed to the wrong root, old path kept in a // comment
       first FAIL: FAIL: browser/app.js still fetches ../quotes.csv and ../sources.csv -- browser/app.js no longer fetches '../quotes.csv'; if the fetch changed, the artifact layout requirement changed with it

checker scripts/smoke_quote_browser.py  (2 control(s), /Users/mschwar/Developer/Garden-of-Wisdom/.venv/bin/python)
baseline: exit=0 RESULT: PASS (0 warning(s))
ok   sm1 matchesSearch() stops narrowing: every search returns all 324 rows
       first FAIL: FAIL: search 'Dhammapada': page never showed 29 quotes within 15000ms (filtered-count='324')
ok   sm2 the card/table empty state loses its message
       first FAIL: FAIL: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada'): empty-state text was 'Nothing to see here.', expected it to contain 'No matching quotes.'

checker scripts/check_garden_store.py  (3 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)
ok   g1 capture immutability: the UPDATE trigger no longer aborts
       first FAIL: FAIL: captures accepted UPDATE: captures are not immutable
ok   g2 the research_state CHECK constraint is dropped (W1.1 review's finding)
       first FAIL: FAIL: the SQL layer accepted research_state = 'maybe' (outside STATE_MODEL.md)
ok   g3 a migration id is renamed: the ledger no longer matches the schema
       first FAIL: FAIL: create-from-empty applied migration ['0001_create_core_v2', '0002_unverifiable_ledger'] into an empty directory

checker scripts/check_garden_envelope.py  (3 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
ok   e1 the serializer loses canonical determinism (sort_keys is load-bearing)
       first FAIL: FAIL: key insertion order cannot change the serialized bytes (sort_keys is load-bearing)
ok   e2 rule 1 stops checking the intake schema version
       first FAIL: FAIL: fixture 'wrong-intake-schema-version' reports exactly rule-1 -- reported []
ok   e3 rule 2 stops refusing an empty captured_text
       first FAIL: FAIL: fixture 'empty-captured-text' reports exactly rule-2 -- reported []

checker scripts/check_garden_submit.py  (2 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)
ok   t1 the capture is trimmed instead of stored byte-for-byte
       first FAIL: FAIL: captured_text is byte-identical to the submitted file (verified against the file bytes) -- 75 vs 78 bytes
ok   t2 the no-normalization-without-a-note refusal is dropped
       first FAIL: FAIL: --candidate-text differing with no note is refused (exit 0, RESULT: FAIL)

checker scripts/check_garden_normalize.py  (3 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (normalization records every change and preserves the capture verbatim; hints are deterministic, cited, and never a state)
ok   n1 the similarity collapses to one directional ratio (asymmetric basis)
       first FAIL: FAIL: the similarity of a pair is symmetric (the same number reaches both candidates' hints)
ok   n2 a shared generic label counts as a specific citation again (ruling 2)
       first FAIL: FAIL: the legacy heuristic flags rows 319 ~ 331 on the shared label 'Oral Tradition', and W1.4 emits no same-reference/same-passage hint for them -- ['same-reference']
ok   n3 the hint rebuild accumulates instead of replacing (the DELETE is lost)
       first FAIL: FAIL: rebuilding every hint exports byte-identical text (derived, deterministic, not appended)

checker scripts/check_garden_review.py  (3 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (all twelve curation transitions audit correctly, the reversal path strands no dimension, and no curation action writes research state)
ok   r1 acceptance no longer fires the required T-P1 corpus follow-on
       first FAIL: FAIL: accept: cand-t01 recorded exactly ['T-C1', 'T-P1'] -- ['T-C1']
ok   r2 curate's OWN required-reason guard is disabled (the backstop remains)
       first FAIL: FAIL: the refusal for an empty reason came from curate's OWN guard ('every curation decision must carry a reason') not a shared/backstop guard -- a decision must carry a reason
ok   r3 a curation action writes research state (invariant 5)
       first FAIL: FAIL: accept: cand-t01 research_state stayed not_started -- in_research

checker scripts/check_garden_e2e.py  (2 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (a messy batch is ingested, normalized, hinted and reviewed while originals, provenance, decision history and duplicate hints all survive, and no curation action implies verification)
ok   x1 the withdrawal path bypasses its state write, stranding a dimension
       first FAIL: FAIL: the reversal strands no dimension: curation=rejected, corpus=candidate_only -- curation=rejected corpus=eligible
ok   x2 the decision log stops being append-only (trigger narrowed to seq)
       first FAIL: FAIL: decisions accepted UPDATE: the log is not append-only

checker scripts/check_garden_ledger.py  (3 control(s), /opt/homebrew/opt/python@3.12/bin/python3.12)
baseline: exit=0 RESULT: PASS (the unverifiable side-car ledger works end to end)
ok   l1 the re-adjudication guard is disabled: a marked row can be re-marked
       first FAIL: FAIL: a duplicate mark is refused by the explicit re-adjudication guard -- unverifiable adjudication for legacy row '30' rejected: UNIQUE constraint failed: legacy_verification.legacy_row_id
ok   l2 the ledger row is written without its research audit row (D3 §2)
       first FAIL: FAIL: mark appends one research audit row (T-R6 from_state derived from the model) -- []
ok   l3 reopen no longer requires the row to be in the ledger
       first FAIL: FAIL: reopen on a missing row was accepted

summary
  checkers: 12 of 12 selected, 0 skipped
  controls: 36 fired, 0 not fired of 36 selected (36 registered in the table)
  harness self-tests: 9 of 9 passed

RESULT: PASS (36 controls fired, 9 harness self-tests) [negative controls]
rc=0
```

**Isolation, re-checked after both full runs** (measured, not asserted): `git status --short` in
the repo lists exactly this unit's seven paths and nothing else, `shasum -a 256 quotes.csv
sources.csv` still reads `b3bb7848…` / `7aafcb67…`, and no temporary directory was created inside
the repo — the only writes are the copies under the system temp dir, which the harness removes on
exit. Every checker also prints its own `baseline: exit=0 RESULT: PASS …` line before its controls,
which is the standing suite's evidence for the unmutated tree (all eleven checkers plus the Pages
guard), for both interpreters.

## What this unit deliberately did not do

- **No corpus, store, schema or state change.** `quotes.csv`/`sources.csv` byte-identical;
  no migration; no new store surface; `data/store/garden.export.txt` untouched.
- **No control for `scripts/smoke_quote_browser.py`'s overflow regression** — the one exclusion,
  with the reason above.
- **No auto-authoring of mutations.** The table is hand-written; a checker that gains a guard
  gains no control until a human writes one. A mutation generator would produce green mutations
  the harness would then have to be trusted to judge.
- **No `AGENTS.md` edit** — still policy-blocked (#27). The new command is documented in
  `RUNBOOK.md` and the design doc instead.
- **Did not change `check_pages_contract.py`, `pages.yml` or `requirements-dev.txt`.**

## Exact next authorized action

`gh issue list --state open` at the time of writing: **#45** (the five coverage gaps, filed by
this unit), **#41** (automate the live Pages acceptance checklist — one stdlib script, no CI
wiring possible), **#30** (needs an operator contract decision), **#27** (needs an `AGENTS.md`
edit or a policy exception), **#6** (audit the remaining Bahá'í rows for misattribution), **#4**
(optional `source_url` column). The queue's first open item is **D6** (the near-duplicate
curation pass, which needs a human curation decision and is explicitly not agent work).

Two items remain **blocked on the operator**, not on work: #27 and #30. W2 remains unauthorized.
The next non-gated, non-operator unit is therefore
[#41](https://github.com/mschwar/Garden-of-Wisdom/issues/41) — automate the six live Pages
probes into one stdlib command with the CSV `sha256` comparison — unless the operator prefers
[#45](https://github.com/mschwar/Garden-of-Wisdom/issues/45), which is five small fixture
additions to existing suites and now has exact reproductions for each.
