# Garden W1.3 Handoff — 2026-09-13

**Unit:** W1.3 — manual capture/submission surface (CLI first) (`docs/program/W1_DECOMPOSITION.md`
§W1.3), the third unit of W1, building on W1.1's store and W1.2's envelope validator. Authorized in
full by decision D1 (2026-09-12). **Branch:** `w1/submission-cli` (worktree
`~/gow-worktrees/w1-3-submit`, off `origin/main` `e5d5734`), opened as PR
[#28](https://github.com/mschwar/Garden-of-Wisdom/pull/28).

**What this unit is:** the first surface in the corpus program that *writes*. It turns one messy
manual submission into one immutable capture plus one candidate at its intake states, and nothing
else — no decision, no research state, no hints, no normalization algorithm, no review command.

## What landed

| Artifact | Change |
|---|---|
| `scripts/garden_submit.py` | **New.** The submission CLI: `submit` with a raw text (`--text` / `--text-file` / `--stdin`), an explicitly required `--capture-method`, every other envelope field as an optional flag, `--emit-envelope PATH`, and `--json`. Allocates `cap-`/`cand-YYYY-MM-DD-NNNN` ids deterministically by scanning the store. Validates everything before the first write and refuses an id the store already holds, so a refused submission leaves the store byte-identical. Stdlib only. |
| `scripts/check_garden_submit.py` | **New.** The W1.3 acceptance + evidence run: **134 checks**, `RESULT: PASS`/`FAIL`, one `FAIL:` line per broken check, no traceback. Drives the CLI as a **subprocess** for all 18 refusals and every accepted submission, then asserts against the store the CLI wrote (through W1.1's `Store` and W1.2's `read_envelope`/`validate`). Everything in a throwaway temp dir. |
| `docs/program/W1_3_SUBMISSION_CLI.md` | **New.** The surface, the order of operations, the two rulings W1.3 owns (id scheme, store location), the normalization boundary, the sentinel/default table, and **eight** doctrine ambiguities. |
| `.gitignore` | `data/store/garden.sqlite3` — the store location ruling: database machine-local and ignored, text mirror committed. |
| `docs/RUNBOOK.md` | New §"Submit a candidate by hand (W1.3)". |
| `docs/DECISIONS.md` | Appended (§"2026-09-13 — W1.3 (submission CLI): …"). Append-only: 74 lines added, 0 removed. |
| `docs/queue.md` | W1.3 marked **DONE** (next: W1.4), a new §"Open — discovered during W1.3" with four filed items, and the existing CI-coverage item annotated as now covering three W1 suites. Nothing deleted; the older W1 status lines are left byte-identical and a new status line is appended. |

Not touched: `quotes.csv`, `sources.csv`, `browser/`, `.github/`, `AGENTS.md`, and — deliberately —
`scripts/garden_store.py` and `scripts/garden_envelope.py` (imported, never modified, so W1.1's and
W1.2's suites stay green and their evidence stays valid).

## The two rulings this unit owns

**1. Record ids.** `cap-YYYY-MM-DD-NNNN` / `cand-YYYY-MM-DD-NNNN`. The day is the **capture** day
(`captured_at`'s date), not the wall-clock day of the command, so a submission with an explicit
historical timestamp is numbered on its own day. `NNNN` is one greater than the highest number
already used for that kind on that day, derived by scanning the store's own ids — no counter table,
no random suffix, no clock. `--capture-id` / `--candidate-id` override it; an id the store already
holds is refused before anything is written. W1.2 §5.2 explicitly left this open for W1.3.

**2. The canonical store location.** `data/store/`. `data/store/garden.sqlite3` is git-ignored
(machine-local, non-diffable); `data/store/garden.export.txt` (`garden.export/1`) is the committed
mirror. W1.3 **declines** the *timing* of W1.1's expected first populated-mirror commit and says why
(`DECISIONS.md` §5 of the entry, §6 of the design doc): the only submissions that exist at this
unit's stop point are its own temp-dir fixtures, and the acceptance run has to pass from a clean
clone — the same property Gate B will require. The first real operator submission populates the
mirror.

## Acceptance criteria, criterion by criterion

| # | Criterion (`W1_DECOMPOSITION.md` §W1.3) | Where it is demonstrated |
|---|---|---|
| 1 | submitting text containing a literal `_`, curly quotes, a wrong author and no citation produces a stored envelope whose `captured_text` is **byte-identical to the input** and whose `normalization_notes` explains every normalization | `check_garden_submit.py` §1: "captured_text is byte-identical to the submitted file (verified against the file bytes)", "the literal `_` placeholder survives verbatim", "the curly quotes survive verbatim", "leading indent and trailing newline survive verbatim", "the wrong author is stored verbatim as encountered ('Rumi')", "an absent citation is the sentinel 'none', never an empty string", "normalization_notes accounts for every normalization by asserting there is none". Transcript below. |
| 2 | a submission with a missing required field is rejected with the field named | `check_garden_submit.py` §4: five empty-flag refusals, each asserting the field name appears **and** that the store's counts are unchanged (`captured_attribution`, `captured_text`, `normalization_notes`, `language`, `candidate_text`), plus the `captured_at` case. |
| — | explicit capture-method selection | §5: an omitted `--capture-method` is refused naming the flag and listing the full nine-method vocabulary; `telepathy` is refused naming `capture_method`. 9–10 checks. |
| — | the raw input stored verbatim, non-interactive flags | §3: `--text`, `--text-file` and `--stdin` all store identical bytes for a payload with a tab, a newline, a `_` and curly quotes; §9: `--json` prints one canonical line and the whole surface is flag-driven. |
| — | the CLI never sets a decision | §10: `decisions` count is 0 after 15 submissions; every candidate is still `curation_state = new`; no candidate is off `research_state = not_started`. |
| — | submissions persist | §10: captures are UPDATE- and DELETE-rejected after submission; `garden_store.py verify` round-trips (export → re-import → byte-identical); every submitted capture appears in the `garden.export/1` mirror. |
| — | `quotes.csv` / `sources.csv` read-only for W1 | the run hashes both before and after: "quotes.csv and sources.csv are byte-identical before and after the run", and the `shasum` below. |

## Evidence (verbatim)

### The acceptance run — `python3 scripts/check_garden_submit.py` (exit 0)

```
scratch: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/garden-submit-check-j9a3susu
PASS: the store is created from empty by garden_store.py create

-- the messy submission (criterion 1) --
PASS: the messy submission is accepted (exit 0, RESULT: PASS)
PASS: the accepted submission prints no traceback
PASS: the transcript carries exactly one RESULT line
PASS: the transcript asserts byte-identity with the submission
PASS: captured_text is byte-identical to the submitted file (verified against the file bytes)
PASS: the literal `_` placeholder survives verbatim (neither repaired nor removed)
PASS: the curly quotes survive verbatim (no straight-quote rewriting)
PASS: leading indent and trailing newline survive verbatim (the text is never trimmed)
PASS: the wrong author is stored verbatim as encountered ('Rumi')
PASS: an absent citation is the sentinel 'none', never an empty string
PASS: the explicitly selected capture method is the one stored
PASS: the language default is the sentinel 'und'
PASS: the captured_by default is 'operator'
PASS: candidate_author is not corrected: a submission implies no research
PASS: candidate_source_ref defaults to the captured citation sentinel
PASS: normalization_notes accounts for every normalization by asserting there is none
PASS: candidate_text defaults to the captured text, byte for byte
PASS: the candidate enters at curation_state=new
PASS: the candidate enters at research_state=not_started
PASS: the candidate enters at corpus_state=candidate_only
PASS: the candidate enters at work_state=queued
PASS: the stored candidate carries the garden.candidate-envelope/1 schema key
PASS: exactly one capture was written for the submission
PASS: exactly one candidate was written for the submission
PASS: the stored record reads back and re-validates with zero violations
PASS: the stored record carries exactly the 21 required envelope fields
PASS: the read-back envelope's captured_text is still byte-identical to the input
PASS: intake writes no duplicate hints (hint generation is W1.4, and a hint is not a decision)

-- the emitted envelope file --
PASS: a submission with --emit-envelope is accepted
PASS: the emitted envelope equals the stored record read back out of the store
PASS: the emitted envelope carries exactly the 21 required fields
PASS: the emitted file is W1.2's canonical serialized form, byte-identical

-- verbatim through --text, --text-file and --stdin --
PASS: the --text submission is accepted
PASS: the --text-file submission is accepted
PASS: the --stdin submission is accepted
PASS: all three input modes store the identical bytes, verbatim
PASS: the three input modes cannot disagree
PASS: --text prints one RESULT line

-- missing required fields are named, and write nothing (criterion 2) --
PASS: --attribution '' is refused (exit 1, RESULT: FAIL)
PASS: --attribution '' names 'captured_attribution' in the refusal
PASS: --attribution '' wrote nothing to the store
PASS: --text '' is refused (exit 1, RESULT: FAIL)
PASS: --text '' names 'captured_text' in the refusal
PASS: --text '' wrote nothing to the store
PASS: --normalization-notes '' is refused (exit 1, RESULT: FAIL)
PASS: --normalization-notes '' names 'normalization_notes' in the refusal
PASS: --normalization-notes '' wrote nothing to the store
PASS: --language '' is refused (exit 1, RESULT: FAIL)
PASS: --language '' names 'language' in the refusal
PASS: --language '' wrote nothing to the store
PASS: --candidate-text '' with a note is refused (exit 1, RESULT: FAIL)
PASS: --candidate-text '' with a note names 'candidate_text' in the refusal
PASS: --candidate-text '' with a note wrote nothing to the store
PASS: --captured-at without an offset is refused (exit 1, RESULT: FAIL)
PASS: --captured-at without an offset names 'captured_at' in the refusal
PASS: --captured-at without an offset wrote nothing to the store
PASS: a malformed captured_at is refused by the submission surface itself, before any id is derived from its date (not delegated to the envelope validator)

-- the capture method is an explicit choice --
PASS: an omitted --capture-method is refused (exit 1, RESULT: FAIL)
PASS: an omitted --capture-method names '--capture-method' in the refusal
PASS: an omitted --capture-method wrote nothing to the store
PASS: an out-of-vocabulary capture method is refused (exit 1, RESULT: FAIL)
PASS: an out-of-vocabulary capture method names 'capture_method' in the refusal
PASS: an out-of-vocabulary capture method wrote nothing to the store
PASS: the out-of-vocabulary refusal quotes the offending value
PASS: the omitted-method refusal lists the whole contract vocabulary

-- broken input is refused cleanly --
PASS: no input flag at all is refused (exit 1, RESULT: FAIL)
PASS: no input flag at all names '--text' in the refusal
PASS: no input flag at all wrote nothing to the store
PASS: --text together with --stdin is refused (exit 2)
PASS: --text together with --stdin names '--text' in the refusal
PASS: --text together with --stdin wrote nothing to the store
PASS: a non-UTF-8 text file is refused (exit 1, RESULT: FAIL)
PASS: a non-UTF-8 text file names 'UTF-8' in the refusal
PASS: a non-UTF-8 text file wrote nothing to the store
PASS: a --text-file that does not exist is refused (exit 1, RESULT: FAIL)
PASS: a --text-file that does not exist names 'cannot read' in the refusal
PASS: a --text-file that does not exist wrote nothing to the store
PASS: --dir with no store in it is refused (exit 1, RESULT: FAIL)
PASS: --dir with no store in it names 'no store at' in the refusal
PASS: --dir with no store in it wrote nothing to the store

-- no normalization is recorded without a note --
PASS: --candidate-text differing with no note is refused (exit 1, RESULT: FAIL)
PASS: --candidate-text differing with no note names 'normalization_notes' in the refusal
PASS: --candidate-text differing with no note wrote nothing to the store
PASS: the refusal from --candidate-text also names the field it would have changed (candidate_text)
PASS: --candidate-author differing with no note is refused (exit 1, RESULT: FAIL)
PASS: --candidate-author differing with no note names 'normalization_notes' in the refusal
PASS: --candidate-author differing with no note wrote nothing to the store
PASS: the refusal from --candidate-author also names the field it would have changed (candidate_author)
PASS: --candidate-source-ref differing with no note is refused (exit 1, RESULT: FAIL)
PASS: --candidate-source-ref differing with no note names 'normalization_notes' in the refusal
PASS: --candidate-source-ref differing with no note wrote nothing to the store
PASS: the refusal from --candidate-source-ref also names the field it would have changed (candidate_source_ref)
PASS: the same change WITH an explicit note is accepted
PASS: a normalized submission still stores the encounter byte-identically
PASS: the normalized proposal is stored alongside, never instead of, the capture
PASS: the operator's normalization note is stored verbatim
PASS: a candidate value equal to the capture needs no note and records 'identical to capture'

-- the candidate-id naming scheme --
PASS: every allocated capture id matches cap-YYYY-MM-DD-NNNN
PASS: every allocated candidate id matches cand-YYYY-MM-DD-NNNN
PASS: no id was ever allocated twice
PASS: the day's candidates are numbered 1..N with no gaps
PASS: the id allocator is deterministic on an unchanged store
PASS: the next submission is accepted
PASS: the CLI allocates exactly the deterministic next id
PASS: a submission with an explicit capture day is accepted
PASS: a different capture day gets its own 0001 sequence
PASS: an explicit --capture-id / --candidate-id is honoured
PASS: an already-used --capture-id is refused (exit 1, RESULT: FAIL)
PASS: an already-used --capture-id names 'capture_id' in the refusal
PASS: an already-used --capture-id wrote nothing to the store
PASS: an already-used --candidate-id is refused (exit 1, RESULT: FAIL)
PASS: an already-used --candidate-id names 'candidate_id' in the refusal
PASS: an already-used --candidate-id wrote nothing to the store
PASS: the capture behind a taken candidate id is untouched by the refusal

-- the CLI is non-interactive and machine-readable --
PASS: --json is accepted
PASS: --json prints exactly one line
PASS: --json prints one canonical object with the stored ids, states, counts and envelope
PASS: --json reports the intake states
PASS: --json reports the store's own counts
PASS: --json output is canonical (sorted keys)

-- submissions persist and imply nothing --
PASS: no submission moved research_state off not_started (no implied verification)
PASS: intake recorded no decision: the decisions log is still empty
PASS: every candidate is still curation_state=new (intake decides nothing)
PASS: a stored capture is immutable after submission (IntegrityError)
PASS: a stored capture cannot be deleted after submission (IntegrityError)
PASS: the store still round-trips: export -> re-import -> byte-identical
PASS: the store exports to its deterministic text mirror
PASS: every submitted capture appears in the committed-mirror export
PASS: the export is a garden.export/1 mirror with the capture and candidate sections
PASS: none of the 18 refusals printed a traceback
PASS: quotes.csv and sources.csv are byte-identical before and after the run
PASS: no store was created in the repo root (the CLI only ever writes to --dir)
PASS: nothing was written outside the store and the scratch inputs

RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)
```

134 `PASS:` lines, zero `FAIL:` lines, exit 0.

### CLI transcripts: a valid submission, an invalid one, and the stored record dumped back out

```text
$ python3 scripts/garden_store.py create --dir /tmp/w13ev/store
store: /tmp/w13ev/store/garden.sqlite3
applied migration(s): 0001_create_core
RESULT: PASS

$ cd /tmp/w13ev && xxd messy.txt                 # the submitted file, as bytes
00000000: 2020 e280 9c54 6865 2065 6172 7468 2069    ...The earth i
00000010: 7320 6275 7420 6f6e 6520 636f 756e 7472  s but one countr
00000020: 792c 0a20 616e 6420 6d61 6e6b 696e 6420  y,. and mankind 
00000030: 6974 7320 6369 7469 7a65 6e73 2e5f e280  its citizens._..
00000040: 9d0a 0a20 20e2 8094 2052 756d 690a       ...  ... Rumi.

$ python3 scripts/garden_submit.py submit --dir /tmp/w13ev/store \
      --text-file /tmp/w13ev/messy.txt --capture-method pasted-text --attribution Rumi
store: /tmp/w13ev/store
capture: cap-2026-09-13-0001 (new; capture_method=pasted-text, captured_at=2026-09-13T13:39:05-06:00, captured_by=operator)
candidate: cand-2026-09-13-0001 (new; curation_state=new, research_state=not_started, corpus_state=candidate_only, work_state=queued)
captured_text: 78 bytes, byte-identical to the submission (no trimming, no glyph repair, no quote or diacritic rewriting)
normalization_notes: identical to capture
duplicate_hints: 0 at intake (hint generation is W1.4; a hint is never a decision)
counts: {"candidate_captures":1,"candidates":1,"captures":1,"decisions":0,"duplicate_hints":0}
stored record, read back out of the store (all 21 required fields, re-validated):
{"candidate_author":"Rumi","candidate_source_ref":"none","candidate_text":"  “The earth is but one country,\n and mankind its citizens._”\n\n  — Rumi\n","capture_id":"cap-2026-09-13-0001","capture_method":"pasted-text","captured_at":"2026-09-13T13:39:05-06:00","captured_attribution":"Rumi","captured_by":"operator","captured_citation":"none","captured_text":"  “The earth is but one country,\n and mankind its citizens._”\n\n  — Rumi\n","context_notes":"none","corpus_state":"candidate_only","curation_state":"new","duplicate_hints":[],"intake_schema_version":"garden.candidate-envelope/1","language":"und","normalization_notes":"identical to capture","raw_artifact_ref":"none","research_state":"not_started","source_reference":"none","work_state":"queued"}
RESULT: PASS
[exit 0]

$ python3 scripts/garden_submit.py submit --dir /tmp/w13ev/store \
      --text 'x' --capture-method pasted-text --attribution ''
FAIL: envelope rejected (2 violation(s)): [rule-1] 'captured_attribution' is empty; a sentinel (['unknown', 'und', 'none', 'legacy-import']) is not an empty string, and absence is never a missing field; [rule-1] 'candidate_author' is empty; a sentinel (['unknown', 'und', 'none', 'legacy-import']) is not an empty string, and absence is never a missing field
RESULT: FAIL
[exit 1]

$ python3 scripts/garden_store.py dump --dir /tmp/w13ev/store
garden.export/1
[meta]
{"created_at":"2026-09-13T13:39:05-06:00","schema_version":1}
[captures]
{"capture_id":"cap-2026-09-13-0001","capture_method":"pasted-text","captured_at":"2026-09-13T13:39:05-06:00","captured_attribution":"Rumi","captured_by":"operator","captured_citation":"none","captured_text":"  “The earth is but one country,\n and mankind its citizens._”\n\n  — Rumi\n","context_notes":"none","language":"und","raw_artifact_ref":"none","source_reference":"none"}
[candidate_captures]
{"candidate_id":"cand-2026-09-13-0001","capture_id":"cap-2026-09-13-0001","ordinal":1}
[candidates]
{"candidate_author":"Rumi","candidate_id":"cand-2026-09-13-0001","candidate_source_ref":"none","candidate_text":"  “The earth is but one country,\n and mankind its citizens._”\n\n  — Rumi\n","corpus_state":"candidate_only","created_at":"2026-09-13T13:39:05-06:00","curation_state":"new","external_id":null,"intake_schema_version":"garden.candidate-envelope/1","normalization_notes":"identical to capture","research_state":"not_started","work_state":"queued"}
[duplicate_hints]
[decisions]

# byte-identity, computed independently of the CLI
stored == file bytes: True | 78 bytes
literal '_' present: True | curly quotes: True
[duplicate_hints] and [decisions] are both empty: the submission recorded no hint and no decision.
```

The invalid submission left the store at `captures: 1, candidates: 1, decisions: 0` — the same as
before it ran.

### The existing suites, the frozen view, and CI's Python

```
$ python3 scripts/validate_quotes.py
RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
$ python3 scripts/check_program_contracts.py
RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
$ python3 scripts/check_garden_store.py
RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)
$ python3 scripts/check_garden_envelope.py
RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
$ python3 scripts/check_garden_submit.py
RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)

# all five again under CI's interpreter (Python 3.12; local is 3.14.5) -- identical results
$ /opt/homebrew/bin/python3.12 scripts/check_garden_submit.py
RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)

$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
```

Both CSV hashes are identical to `main` and to W1.1's and W1.2's handoffs; the read-only rule held.

## Negative controls (a test that cannot fail proves nothing)

Each mutation was applied to a **throwaway copy of the worktree under `/tmp`** (never the repo,
never the primary checkout) and the acceptance suite was re-run there. All 15 went red with a
targeted `FAIL:` line and **no traceback**; the baseline unmutated copy exits 0. Driver:
`/tmp/w13_negative_controls.py` (copies `scripts/`, both CSVs; applies one or more exact string
replacements; re-runs).

| # | Mutation (in the `/tmp` copy) | Observed `FAIL:` line(s) |
|---|---|---|
| n1 | the submitted text is `.strip()`ed instead of stored verbatim | `FAIL: captured_text is byte-identical to the submitted file (verified against the file bytes)` (+5 more) |
| n2 | the literal `_` is "repaired" to a guessed glyph in `captured_text` and `candidate_text` | `FAIL: the messy submission is accepted … -- FAIL: envelope rejected … [rule-5] captured_text is not byte-identical to capture 'cap-2026-09-13-0001'` (+3 more) |
| n3 | an empty flag is silently replaced by the field's sentinel (`_coalesce` treats `""` as absent) | `FAIL: --attribution '' is refused (exit 0, RESULT: FAIL)` (+19 more) |
| n4 | the normalization-note requirement is skipped | `FAIL: --candidate-text differing with no note is refused …` (+5 more) |
| n5 | the id allocator ignores the capture day | `FAIL: a different capture day gets its own 0001 sequence` |
| n6 | the allocator never looks at the ids already in the store | `FAIL: a submission with --emit-envelope is accepted` (+1 more) |
| n7 | the id-collision pre-check is dropped | `FAIL: an already-used --candidate-id wrote nothing to the store` |
| n8 | intake writes a `research_state` of its own | `FAIL: the messy submission is accepted … -- FAIL: envelope rejected … [rule-3] research_state is 'verified'` (+6 more) |
| n9 | intake records a decision of its own | `FAIL: intake recorded no decision: the decisions log is still empty` |
| n10 | the `--json` output is no longer canonical | `FAIL: --json output is canonical (sorted keys)` |
| n11 | an omitted `--capture-method` silently defaults to `pasted-text` | `FAIL: an omitted --capture-method is refused (exit 0, RESULT: FAIL)` (+12 more) |
| n12 | the emitted envelope silently loses a field | `FAIL: the emitted envelope equals the stored record read back out of the store` (+2 more) |
| n13 | non-UTF-8 input is decoded with `"replace"` instead of refused | `FAIL: a non-UTF-8 text file is refused (exit 0, RESULT: FAIL)` (+7 more) |
| n14 | `captured_at` is accepted without an offset | `FAIL: a malformed captured_at is refused by the submission surface itself, before any id is derived from its date` |
| n15 | the transcript's byte-identity claim is a lie | `FAIL: the transcript asserts byte-identity with the submission` |

Three of these are worth naming because they are the checks that could most easily have been
vacuous:

- **n3** is acceptance criterion 2's whole mechanism. Without it, the five empty-flag refusals all
  silently pass — a default that swallows `""` turns "the operator gave us nothing here" into a
  claim that the attribution is unknown, and no acceptance check would notice.
- **n7** proves the *ordering* is load-bearing rather than decorative: with the pre-check gone, a
  submission refused for a taken candidate id still writes its capture, and the "wrote nothing"
  assertions catch it. (Captures are history, so that orphan would have been permanent.)
- **n14 is the one control that initially did NOT go red** — see the review section below.

## Review pass (independent mutation harness, same session)

The W1.2 precedent is an independent/foreign review by a separate session. Here the author and the
reviewer are the same session, and this is stated plainly rather than implied: the five mutations
below were written **after** the fifteen above, against paths those fifteen did not touch, and the
operator may still want a foreign pass before treating the unit as reviewed.

| # | Mutation (in a `/tmp` copy of the branch) | Result |
|---|---|---|
| M1 | the transcript prints a second `RESULT: PASS` line | **RED**: `FAIL: the transcript carries exactly one RESULT line` |
| M2 | the id allocator leaves a gap (`highest + 10`) | **RED**: `FAIL: the day's candidates are numbered 1..N with no gaps` |
| M3 | the `--json` payload drops `counts` | **RED**: `FAIL: --json prints one canonical object with the stored ids, states, counts and envelope` |
| M4 | an explicit `--captured-at` is ignored (the clock always wins) | **RED**: `FAIL: --captured-at without an offset is refused` |
| M5 | `--dir` silently creates a store when there is none | **RED**: `FAIL: --dir with no store in it is refused` |

Zero coverage gaps. Driver: `/tmp/w13_review_pass.py`.

### The one real gap this found (control n14)

The CLI checks `captured_at` itself, before deriving the record ids from its date, and the envelope
validator checks it again as rule 1. Mutating the CLI's check to always pass left the whole suite
**green**, because rule 1 caught the same defect one step later — the CLI's check had no unique
falsifier. It is not a bug (the two refuse identically and nothing is written either way), but it
was unproven code, which is the thing this program's review process exists to find.

Fixed by asserting the **layering** rather than deleting the check: the acceptance run now requires
that a malformed `captured_at` is refused by the submission surface itself — `captured_at` named,
and *not* the envelope validator's `envelope rejected … [rule-1]` wording. Re-running n14 turns it
red. Recorded in `docs/program/W1_3_SUBMISSION_CLI.md` §7.4, and the suite grew from 133 to **134
checks**.

## Defect found and fixed inside the unit

`--text ""` was reported as `exactly one of --text, --text-file or --stdin is required`, because the
input-source check tested each flag for **truthiness** and an empty string is falsy. An empty
submission is a submission with no text — rule 2's finding, with `captured_text` named — not a usage
error. Fixed to presence-by-`is not None` and asserted (§7.6 of the design doc). Found by the
acceptance run's own criterion-2 case, not by review.

## Out of scope, recorded not fixed

- **`AGENTS.md` does not describe the corpus-program command surface**, and omits the W1 rule that
  `quotes.csv` / `sources.csv` are read-only for the whole wave — on the file that is the documented
  resume path for every agent. Filed as
  [#27](https://github.com/mschwar/Garden-of-Wisdom/issues/27) and in `docs/queue.md`. Not fixed
  here: `AGENTS.md` writes are refused by tool policy and it is a protected file with a size budget.
- **A candidate can only ever have one capture.** `PROVENANCE_AND_CAPTURE_CONTRACT.md` invariant 3
  allows several, and `candidate_captures.ordinal` exists for it, but no surface can attach a second
  capture to an existing candidate — and W1.3 refuses to restate a stored capture because rule 5
  compares only `captured_text` (W1.2 §5.1), so a restatement could disagree on attribution and
  still validate. Needs a decision on the link-existing path *and* on whether rule 5 widens. Filed
  in `docs/queue.md`; `W1_3_SUBMISSION_CLI.md` §7.3.
- **No populated store mirror is committed** (deviation from W1.1's expectation). Recorded in
  `DECISIONS.md` and §6 of the design doc; the first real operator submission populates it and Gate B
  is where the evidence store belongs.
- **`captured_by` defaults to `operator`** — a reading, not a contract statement. Filed in
  `docs/queue.md`; `W1_3_SUBMISSION_CLI.md` §7.1.
- **No flag for any of the nine optional envelope fields**, including `external_id` which *has* a
  column: an untested flag is worse than an absent one, and a flag for the other eight could only
  accept a value the store cannot hold. W1.2's persistence gap stands unchanged, and its migration
  decision is still owed to W1.4.
- **CI still does not run any W1 acceptance suite.** There are now three (W1.1, W1.2, W1.3) and
  `browser-smoke.yml` runs none of them. Annotated in `docs/queue.md`. A CI change touches the
  guarded workflow, so it is filed, not fixed in a W1 unit.
- **`work_state` still has two subjects** (W1.1 §8.1). W1.3 writes `work_state = 'queued'` because
  the envelope requires it; nothing here resolves the ambiguity.

## Next authorized action

**W1.4 — normalization + duplicate hints** (`docs/program/W1_DECOMPOSITION.md` §W1.4), whose
dependencies are W1.2 (envelope) and W1.3 (submissions to normalize) — both now landed. W1.4 owns
the deterministic normalization the W1.3 surface deliberately did not implement: it replaces the
`identical to capture` default with a real transform that produces its own notes, and it must keep
the invariant W1.3 put in place — **no normalization without a note**, and `captured_text`
byte-identical to the encounter no matter what. It also owns duplicate-hint kinds
(`exact-text`/`near-text`/`same-reference`/`same-passage`) with explicit basis strings, the
similarity threshold, and not reproducing the generic-`source_ref` false positive from
`docs/data/DATA_QUALITY_REPORT.md`. The optional-field store migration
(`placeholder_markers`/`provenance_chain`) is the decision W1.2 filed and W1.3 confirmed still owed;
if W1.4 needs those columns it owns that migration and W1.1's ledger assertion.

**Stop condition met: submissions persist. No review commands, no decision path, no normalization
algorithm, no hints.**

## DECISIONS.md and queue.md entries (landed by this unit)

`docs/DECISIONS.md` gained one append-only entry (74 lines added, 0 removed):
*"2026-09-13 — W1.3 (submission CLI): the record-id scheme, the normalization boundary, the store
location, and no populated mirror yet"*. `docs/queue.md` gained the W1.3 close-out bullet, an
appended W1 status line, a new *"Open — discovered during W1.3"* section with four filed items, and
one annotation on the existing CI-coverage item. Nothing was deleted.
