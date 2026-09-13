# Garden W1.4 Handoff — 2026-09-13

**Unit:** W1.4 — normalization + duplicate hints (`docs/program/W1_DECOMPOSITION.md` §W1.4).
**Branch:** `w1/normalization-hints` → PR [#29](https://github.com/mschwar/Garden-of-Wisdom/pull/29).
**Commits:** `78432c8` (the unit) and `604990c` (the review pass's two findings, below).
**Design doc:** `docs/program/W1_4_NORMALIZATION_HINTS.md`.
**Stop condition:** hints generate deterministically. No decisions. **Met** — no review surface, no
transition, no `research_state` write, no `T-C4`/`T-C7`/`T-C9` path, no migration, no CSV write.

## What landed

| Path | What it is |
|---|---|
| `scripts/garden_normalize.py` | `garden.normalize/1` (the deterministic intake transform) + the duplicate-hint generator, with the `normalize` / `hints` / `classify` / `describe` CLI |
| `scripts/garden_store.py` | **+58 lines**: one new guarded method, `apply_normalization` (the only write path for a proposal). No schema change; W1.1's `["0001_create_core"]` ledger assertion is untouched |
| `scripts/check_garden_normalize.py` | the acceptance + evidence run — **232** checks, driving the real CLIs as subprocesses |
| `docs/program/W1_4_NORMALIZATION_HINTS.md` | the design doc: the declared algorithm, the three rulings, the guard layering, what the unit does not do |
| `docs/RUNBOOK.md` | §"Normalize a candidate and generate duplicate hints (W1.4)" |
| `docs/DECISIONS.md` | one append-only entry (4 decisions, each with the rejected alternative) |
| `docs/queue.md` | the W1.4 close-out bullet, an appended W1 status line, a new *Open — discovered during W1.4* section |

`quotes.csv` / `sources.csv` are byte-identical to the start of the wave
(`5675d7e6…` / `10b4c156…`), asserted in the acceptance run and checked again here.

## The three rulings this unit owns

1. **The algorithm is a closed, declared list, and every change is counted.** NFC; four
   canonical-character classes (quote marks, dashes, ellipsis, no-break spaces) applied **one class
   at a time**; whitespace runs collapsed and boundary whitespace trimmed; a literal `_` preserved
   and reported. Rejected: a union-table `str.translate` (it converts a later class while crediting
   the count to the first class that fired — the note under-reports; control `n6` is the regression
   test), and touching anything undeclared.
2. **Similarity 0.60 over normalized case-folded text, scored as the *mean of the two directional
   `difflib` ratios*.** `SequenceMatcher.ratio()` is asymmetric (rows 113/114: 0.69 one way, 0.67
   the other), so a raw ratio lets the two candidates disagree about their own pair. Rejected:
   keeping the raw ratio and documenting the asymmetry.
3. **A shared citation is evidence only when it pinpoints something.** `same-reference` /
   `same-passage` require a locator (Arabic digit, Roman-numeral token, `§`); `none`/`unknown`/`und`
   is not a citation; a bare work title is `generic`. This is the fix for the
   `"Oral Tradition"` false-positive class in `docs/data/DATA_QUALITY_REPORT.md`, and it is
   deliberately narrower than that report's split (it also suppresses a shared bare work title).

Batch semantics belong to ruling 3's implementation rather than the card: an explicit
`--candidate-id` that cannot be normalized is a **refusal** that writes nothing; an `--all` run
**names** each `SKIPPED:` candidate and continues; a batch that can normalize **nothing** fails.

## Acceptance criteria, criterion by criterion

| Card criterion | Where it is proven |
|---|---|
| the generic-`source_ref` false positive produces no `same-passage` hint unless the citation is actually specific | rows 319/331/332 (`Oral Tradition`) and 5/19 (bare work title) produce **no** `same-reference`/`same-passage` hint, asserted **on the same fixtures** where the legacy heuristic's own predicate (`a.source_ref == b.source_ref`) flags the pair — so the guard is proven to be doing work, not describing itself. Control `n1`. |
| every hint carries a basis string | every stored row is asserted to have a declared kind, a non-empty basis and a resolvable target; the near-text and same-reference bases are additionally asserted to carry the measured similarity and the quoted citation |
| hints never appear in `curation_state` | every candidate is still `new`, no candidate is `duplicate`, all four dimensions are at their intake values, and `decisions` is still empty (count 0) after normalize + three hint rebuilds |
| evidence: hint output for the fixture batch including the `"Oral Tradition"` shape and the id 3 ~ 283 pair | both are fixtures **read out of the real `quotes.csv`**; `3 ~ 283` gets `near-text` in both directions with the symmetric basis number, and the `Oral Tradition` triples get nothing |

The card's own evidence line ("hint output for a fixture batch") is the `--all` transcript below;
the machine-checked form is the acceptance run.

## Evidence (verbatim)

### The acceptance run

```
$ python3 scripts/check_garden_normalize.py
...
PASS: none of the 8 refusals printed a traceback
PASS: quotes.csv and sources.csv are byte-identical before and after the run
PASS: no store was created in the repo root (the CLIs only ever write to --dir)
PASS: nothing was written outside the store and the scratch inputs

RESULT: PASS (normalization records every change and preserves the capture verbatim; hints are deterministic, cited, and never a state)
```

232 `PASS:` lines, exit 0.

### The whole suite set, under both interpreters

```
===== python3 (Python 3.14.5) =====
validate_quotes                       exit0 0 PASS | RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
check_program_contracts               exit0 0 PASS | RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
validate_homepage_preview_export      exit0 0 PASS | RESULT: PASS
check_garden_store                    exit0 59 PASS | RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)
check_garden_envelope                 exit0 102 PASS | RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
check_garden_submit                   exit0 134 PASS | RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)
check_garden_normalize                exit0 232 PASS | RESULT: PASS (normalization records every change and preserves the capture verbatim; hints are deterministic, cited, and never a state)
===== /opt/homebrew/bin/python3.12 (Python 3.12.13) =====
validate_quotes                       exit0 0 PASS | RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
check_program_contracts               exit0 0 PASS | RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
validate_homepage_preview_export      exit0 0 PASS | RESULT: PASS
check_garden_store                    exit0 59 PASS | RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)
check_garden_envelope                 exit0 102 PASS | RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
check_garden_submit                   exit0 134 PASS | RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)
check_garden_normalize                exit0 232 PASS | RESULT: PASS (normalization records every change and preserves the capture verbatim; hints are deterministic, cited, and never a state)
```

### The CLIs by hand (a two-candidate store, then hints)

```
$ T=$(mktemp -d)
$ python3 scripts/garden_store.py create --dir "$T/store"
$ python3 scripts/garden_submit.py submit --dir "$T/store" --text 'The earth is but one country, and mankind its citizens.' --citation 'Gleanings, CXVII' --attribution 'Bahá’u’lláh' --capture-method pasted-text --json      # exit 0
$ python3 scripts/garden_submit.py submit --dir "$T/store" --text 'The earth is one home and mankind its family.' --citation 'Selections from the Writings of ‘Abdu’l-Bahá, 255' --attribution '‘Abdu’l-Bahá' --capture-method pasted-text --json   # exit 0
### normalize --all
store: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/tmp.5h2Osb1ksf/store
algorithm: garden.normalize/1
candidate: cand-2026-09-13-0001 (normalized)
  candidate_text: 'The earth is but one country, and mankind its citizens.'
  candidate_author: "Bahá'u'lláh"
  candidate_source_ref: 'Gleanings, CXVII'
  normalization_notes: captured_text: identical to capture; captured_attribution: quote-marks: 2 character(s) canonicalized; captured_citation: identical to capture
candidate: cand-2026-09-13-0002 (normalized)
  candidate_text: 'The earth is one home and mankind its family.'
  candidate_author: "'Abdu'l-Bahá"
  candidate_source_ref: "Selections from the Writings of 'Abdu'l-Bahá, 255"
  normalization_notes: captured_text: identical to capture; captured_attribution: quote-marks: 2 character(s) canonicalized; captured_citation: quote-marks: 2 character(s) canonicalized
normalized 2 of 2 candidate(s) (0 skipped)
the captures were not touched: a proposal is stored alongside the encounter
counts: {"candidate_captures":2,"candidates":2,"captures":2,"decisions":0,"duplicate_hints":0}
RESULT: PASS
### hints --all
store: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/tmp.5h2Osb1ksf/store
hints: 2 written for 2 candidate(s) (0 row(s) before, 2 after; a rebuild replaces, never edits)
threshold: normalized case-folded similarity >= 0.60
candidate: cand-2026-09-13-0001 (1 hint(s))
  [near-text] -> cand-2026-09-13-0002 basis=normalized text similarity 0.74 >= 0.60 (case-folded, difflib.SequenceMatcher)
candidate: cand-2026-09-13-0002 (1 hint(s))
  [near-text] -> cand-2026-09-13-0001 basis=normalized text similarity 0.74 >= 0.60 (case-folded, difflib.SequenceMatcher)
note: hints are not decisions -- no curation_state was written and no decisions row was recorded (T-C4/T-C7/T-C9 are the operator's)
counts: {"candidate_captures":2,"candidates":2,"captures":2,"decisions":0,"duplicate_hints":2}
RESULT: PASS
### classify
reference: 'Oral Tradition'
normalized: 'Oral Tradition'
specificity: generic
RESULT: PASS
```

(A hand transcript for illustration — the machine-checked fixture batch is the acceptance run, which
derives every fixture, its text, its citation and its author out of the real `quotes.csv`.)

## Negative controls (a test that cannot fail proves nothing)

17 mutations, each in a throwaway `/tmp` copy of the repo, one exact string replacement per copy
(the harness asserts the pattern appears exactly once before mutating), then the real suite re-run.
Every one must exit non-zero with a targeted `FAIL:` line and no traceback, and the **first**
`FAIL:` line must be the check the mutation was aimed at.

```
n1 specificity guard dropped (shared citation alone is enough)
    OK exit=1 traceback=False fails=5 first=FAIL: the legacy heuristic flags rows 319 ~ 331 on the shared label 'Oral Tradition', and W1.4 emits no same-reference/same-passage hint for them -- ['same-reference']
n2 every non-sentinel citation classified specific
    OK exit=1 traceback=False fails=10 first=FAIL: 'Oral Tradition' is classified generic (a label that pinpoints nothing)
n3 similarity test lowered to 0.0 at the comparison site
    OK exit=1 traceback=False fails=2 first=FAIL: the shared-specific-citation pair gets exactly a same-reference hint in both directions (not same-passage: it is below the threshold) -- ['near-text', 'same-passage', 'same-reference'] / ['near-text', 'same-passage', 'same-reference']
n4 similarity test raised to 0.99 at the comparison site
    OK exit=1 traceback=False fails=2 first=FAIL: the id 3 ~ 283 pair gets a near-text hint in both directions -- set()
n5 similarity made asymmetric again (mean dropped)
    OK exit=1 traceback=False fails=2 first=FAIL: the similarity of a pair is symmetric (the same number reaches both candidates' hints)
n6 canonical classes translated with the union table (note under-reports)
    OK exit=1 traceback=False fails=1 first=FAIL: the note names the ellipsis change with its exact count -- captured_text: quote-marks: 2 character(s) canonicalized; whitespace: 4 character(s) collapsed, 2 boundary character(s) trimmed; 1 literal '_' preserved (not repaired: guessing the character is fabrication); captured_attribution: quote-marks: 2 character(s) canonicalized; captured_citation: quote-marks: 2 character(s) canonicalized
n7 whitespace collapse dropped
    OK exit=1 traceback=False fails=2 first=FAIL: the messy fixture's candidate_text equals the independently re-derived value -- '"The earth is but one country, and mankind its citizens."...\tand   a _ gap'
n8 placeholder observation dropped from the note
    OK exit=1 traceback=False fails=3 first=FAIL: the note reports the literal `_` as preserved (not repaired) -- captured_text: quote-marks: 2 character(s) canonicalized; ellipsis: 1 character(s) canonicalized; whitespace: 4 character(s) collapsed, 2 boundary character(s) trimmed; captured_attribution: quote-marks: 2 character(s) canonicalized; captured_citation: quote-marks: 2 character(s) canonicalized
n9 NFC recomposition dropped
    OK exit=1 traceback=False fails=2 first=FAIL: the proposal recomposes the decomposed text to NFC -- "Bahá'i, the light of unity."
n10 'nothing changed' note replaced by a bare sentinel
    OK exit=1 traceback=False fails=2 first=FAIL: the already-normalized row 32 gets the note 'identical to capture' -- none
n11 the intake-state guard on the store-side write path removed
    OK exit=1 traceback=False fails=3 first=FAIL: the store's apply_normalization accepted a decided candidate -- it must refuse
n12 the empty-proposal refusal removed
    OK exit=1 traceback=False fails=9 first=FAIL: normalize --all is accepted (exit 0, RESULT: PASS) -- FAIL: candidate_text must be non-empty (an empty proposal is not a proposal)
n13 the --candidate-id/--all exclusivity guard weakened
    OK exit=1 traceback=False fails=2 first=FAIL: a normalize with both --candidate-id and --all is refused (exit 0, RESULT: FAIL)
n14 hint rebuild accumulates instead of replacing
    OK exit=1 traceback=False fails=5 first=FAIL: rebuilding every hint exports byte-identical text (derived, deterministic, not appended)
n15 the surface's own intake-state guard removed (store guard left in place)
    OK exit=1 traceback=False fails=4 first=FAIL: a batch run skips a decided candidate instead of aborting the whole batch -- store: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/garden-normalize-check-yhg44ekz/store
n16 the store's empty-proposal guard removed
    OK exit=1 traceback=False fails=1 first=FAIL: the store's apply_normalization refused an empty proposal with IntegrityError instead of its own StoreError guard: CHECK constraint failed: length(candidate_text) > 0
n17 the store's empty-note guard removed
    OK exit=1 traceback=False fails=1 first=FAIL: the store's apply_normalization refused an empty note with IntegrityError instead of its own StoreError guard: CHECK constraint failed: length(normalization_notes) > 0

17/17 controls behaved as predicted
```

## Review pass (independent mutation harness, same session)

**This is not a foreign review.** The same session that authored the unit wrote a *second* harness
afterwards, aiming at paths the author's set did not touch: the note's field attribution, the hint
**ordering** contract, the no-op/write decision, the fixture-discovery vacuity guards, and the
placeholder constant. The operator may still want a foreign pass; nothing here should be read as
one.

```
r1 the note stops attributing changes to attribution/citation (text part only)
    OK exit=1 traceback=False fails=3 first=FAIL: the note attributes every change to the captured field it came from (text/attribution/citation) -- captured_text: quote-marks: 2 character(s) canonicalized; ellipsis: 1 character(s) ca
r2 hint targets iterated in reverse (stored order breaks the documented contract)
    OK exit=1 traceback=False fails=1 first=FAIL: every candidate's hints are stored in the documented (target, kind) order, so hint_seq is stable across rebuilds and diffable
r3 the no-op decision forced true (every run rewrites every candidate)
    OK exit=1 traceback=False fails=1 first=FAIL: a second normalize --all is a no-op (every candidate already carries its proposal) -- store: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/garden-normalize-check-6xo9r903/store
r4 the normalized write skipped entirely (proposals never land)
    OK exit=1 traceback=False fails=27 first=FAIL: the [candidates] section did change -- normalization wrote something
r5 candidate comparison order reversed (the hint ordering contract breaks)
    OK exit=1 traceback=False fails=1 first=FAIL: every candidate's hints are stored in the documented (target, kind) order, so hint_seq is stable across rebuilds and diffable
r6 quotes.csv fixture mutated: the generic false-positive group loses its shared label
    OK exit=1 traceback=False fails=2 first=FAIL: the false-positive fixture group all carry one generic label -- ['Hopi Oral Tradition', 'Oral Tradition']
r7 the placeholder glyph swapped for a guess (the fabrication the unit forbids)
    OK exit=1 traceback=False fails=4 first=FAIL: the module's placeholder glyph is the corpus's literal `_` (the test's own constant, so a change to the module's constant fails here instead of silently redefining the fixture) -- 'ʼ' 

7/7 review controls behaved as predicted
```

### The two real gaps it found (both fixed in `604990c`)

1. **The stored hint order had no assertion.** `docs/program/W1_4_NORMALIZATION_HINTS.md` claims
   hints are ordered `(target, kind)` inside a candidate and that this is what makes `hint_seq`
   stable; nothing tested it, and controls `r2`/`r5` (reversing the comparison order two different
   ways) both left the suite **green** before the fix. The suite now asserts the stored order per
   candidate against the documented kind order, and both controls go red on it.
2. **The acceptance run discovered its placeholder fixtures with `garden_normalize.PLACEHOLDER_GLYPH`.**
   A test that reads the fixture class from the constant it is testing redefines its own fixture
   when the constant changes — control `r7` (swapping the constant for a guessed `ʼ`) went red only
   on the *vacuity* guard, never on the checks that are supposed to prove the `_` is preserved. The
   suite now uses its own literal `"_"` for discovery and counts, and asserts the module's constant
   equals it, so the same mutation now fails on the drift check.

### One control that is inert, and why that is not a gap

The first version of `r5` reversed the **candidate id list in `rebuild_hints`** and left the suite
green. That is correct, not a hole: `hints_for` receives the comparison rows in store order
regardless, so reversing the iteration order of the outer loop only reorders writes to *independent*
candidates — the mutation has no observable effect at all. r5 was replaced with a mutation that does
have one (reversing the comparison-order query), which now fails on the ordering assertion. Recorded
because "a control that does not go red" is only a finding when the mutation is observable.

## Defects found and fixed inside the unit

1. **The note under-reported its own changes.** `_canonical_characters` counted each class separately
   but then applied the *union* of all tables, so a later class's characters were converted during an
   earlier class's step and never counted. Found by the acceptance run's independent per-class count
   (control `n6`). Fixed by translating with each class's own table.
2. **The similarity was asymmetric**, so the same pair reported 0.69 or 0.67 depending on which
   candidate was being compared and the two candidates disagreed about their own pair. Fixed by the
   mean of the two directional ratios (control `n5`), and recorded as a divergence from the legacy
   report's numbers — which is filed separately (issue #31) because the D6 curation pass will
   re-derive those pairs.
3. **`normalize --all` aborted on a candidate it could not normalize.** A whitespace-only submission
   is legal at intake, and W1 has no withdrawal path, so one junk row made the batch unusable. Fixed
   with the skip/refuse split (ruling 3), including the "a batch that normalizes nothing fails" half.

A fourth, found during the unit's own control pass and fixed in the suite rather than the code: the
store's `apply_normalization` state guard had **no unique falsifier** (control `n11` left the suite
green, because the CLI's own pre-check refused first). Controls `n15`, `n16`, `n17` now cover the
reverse directions by calling the store method directly from the test. This is the same class of gap
W1.3 recorded for `captured_at`, found the same way — by a control that did not go red.

## Out of scope, recorded not fixed

Filed on the board, each also in `docs/queue.md`:

- **[#30](https://github.com/mschwar/Garden-of-Wisdom/issues/30) — a candidate can never be
  withdrawn, and a whitespace-only submission is permanent.** The concrete instance of the
  "no sanctioned capture-deletion path" ambiguity W1.1 recorded. Both fixes are contract decisions
  (tighten envelope rule 2, or add an operator-visible withdrawal), so neither is W1.4's to make.
- **[#31](https://github.com/mschwar/Garden-of-Wisdom/issues/31) — `validate_quotes.py`'s
  near-duplicate similarity is direction-dependent.** `SequenceMatcher.ratio()` is asymmetric, so the
  frozen report's numbers are a function of row order and cannot be reproduced in the other order.
  Fixing it means re-generating `docs/data/DATA_QUALITY_REPORT.md` and re-counting the queue's D6
  item — its own unit, because that report is a frozen evidence artifact.
- **[#27](https://github.com/mschwar/Garden-of-Wisdom/issues/27) reopened — `AGENTS.md` still does
  not describe the corpus-program command surface** (and still omits the W1 read-only rule). The
  issue had been closed as COMPLETED, but `AGENTS.md` at `main` is unchanged (`grep -c 'garden_'
  AGENTS.md` → 0, 63 lines, last touched by `31f06e0`). Reopened with that evidence; the change needs
  an operator edit or a policy exception for the file (which is why this unit's own doc-surface
  changes stop at `RUNBOOK.md`).
- **CI still does not run the W1 acceptance suites.** There are now **four**
  (`check_garden_store` 59, `check_garden_envelope` 102, `check_garden_submit` 134,
  `check_garden_normalize` 232) and `browser-smoke.yml` runs none of them. Unchanged from W1.2/W1.3:
  it is a change to a guarded workflow, so it stays filed rather than fixed in passing.
- **The optional envelope fields still have no store columns** (W1.2's filed gap). W1.4 considered
  `placeholder_markers` and **declined** the migration — the placeholder needs to be observable, not
  structured, and `normalization_notes` carries it. The decision and the reason are in
  `docs/DECISIONS.md`; the persistence gap stays filed against the first unit that consumes those
  fields structurally.

## Post-merge verification

_(filled in by the follow-up docs commit after the merge: merge sha, PR number, both CI run ids, and
the live acceptance — four URLs 200 plus the live CSV hashes against the repo's.)_

## Next authorized action

**W1.5 — curation review + decision recording + audit history**
(`docs/program/W1_DECOMPOSITION.md` §W1.5), whose dependencies are W1.1 (decisions log + states),
W1.2 (envelopes to review) and **W1.4 (hints shown in the queue)** — all now landed. W1.5 owns the
queue view (newest first, showing the captured verbatim text, the normalized proposal, the
normalization notes, the duplicate hints **with their basis**, and an explicit
machine-inferred-vs-asserted marker), the accept / reject / hold / duplicate commands with a required
reason, and the append-only audit entries implementing `T-C1…T-C12`; it must render `research_state`
read-only and always `not_started`, and it owns the reversal path (`T-C8`→`T-P7`, `T-C9`→`T-P7`).
**Per-unit contract still applies:** its own branch → one PR → foreign QA → merge → stop. **W1.6 and
`W2` are not started.**

## DECISIONS.md and queue.md entries (landed by this unit)

`docs/DECISIONS.md` gained one append-only entry: *"2026-09-13 — W1.4 (normalization + hints): the
algorithm, the threshold, specificity, and no migration"* (four decisions, each with the rejected
alternative, plus the batch-semantics and guard-layering notes). `docs/queue.md` gained the W1.4
close-out bullet, an appended W1 status line naming W1.5 as next, a new *"Open — discovered during
W1.4"* section, and annotations on the existing CI-coverage and optional-field-persistence items.
Nothing was deleted; the pre-existing lines were left byte-identical.
