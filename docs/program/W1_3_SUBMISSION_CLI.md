# W1.3 — Manual capture/submission surface (CLI first)

**Status: implemented 2026-09-13** on branch `w1/submission-cli` (W1.3 of
`docs/program/W1_DECOMPOSITION.md`). This document is the written half of the unit: what the
surface accepts, the order in which it writes, the rulings W1.3 owns (the candidate-id naming
scheme and the canonical store location), the normalization boundary against W1.4, and the places
the doctrine was ambiguous. The executable half is `scripts/garden_submit.py` (the CLI) and
`scripts/check_garden_submit.py` (acceptance + evidence, 134 checks).

W1.3 is the first surface in the program that **writes**. Everything before it either read
(W1.2's diagnostic CLI) or created an empty store (W1.1).

## 1. The surface

```
python3 scripts/garden_submit.py submit --dir DIR --text 'TEXT'    --capture-method METHOD [flags]
python3 scripts/garden_submit.py submit --dir DIR --text-file FILE --capture-method METHOD [flags]
python3 scripts/garden_submit.py submit --dir DIR --stdin          --capture-method METHOD [flags]
```

Exactly one of `--text` / `--text-file` / `--stdin` supplies the raw text; it is decoded as UTF-8
and otherwise **untouched**. `--capture-method` (required, no default) is one of the nine contract
methods. The rest are optional and map onto the envelope's fields:

| Flag | Envelope field | Default when omitted |
|---|---|---|
| `--capture-id` | `capture_id` | allocated: `cap-YYYY-MM-DD-NNNN` |
| `--candidate-id` | (candidate key) | allocated: `cand-YYYY-MM-DD-NNNN` |
| `--attribution` | `captured_attribution` | `unknown` |
| `--citation` | `captured_citation` | `none` |
| `--source-reference` / `--source-url` | `source_reference` | `none` |
| `--context-notes` | `context_notes` | `none` |
| `--raw-artifact-ref` | `raw_artifact_ref` | `none` |
| `--language` | `language` | `und` |
| `--captured-by` | `captured_by` | `operator` |
| `--captured-at` | `captured_at` | now, ISO-8601 with offset |
| `--candidate-text` | `candidate_text` | the captured text, verbatim |
| `--candidate-author` | `candidate_author` | the captured attribution, verbatim |
| `--candidate-source-ref` | `candidate_source_ref` | the captured citation, verbatim |
| `--normalization-notes` | `normalization_notes` | `identical to capture` |
| `--emit-envelope PATH` | *(also writes the canonical envelope JSON)* | off |
| `--json` | *(one canonical JSON object instead of the transcript)* | off |

None of the nine **optional** envelope fields has a flag — including `external_id`, the one that
does have a store column. See §7.2.

The four state dimensions have **no flags**: a submission cannot state a decision, because
`garden_store.add_candidate` has no state parameter and this surface never passes one.

`--json` is an addition the card does not name. It exists because the card requires
"non-interactive flags for scripted/testing use": the acceptance run needs the allocated ids and the
stored record in a machine-readable form, and adding it is cheaper and more honest than parsing the
human transcript. It prints exactly one line in W1.2's canonical form.

## 2. Order of operations (why a refused submission writes nothing)

```
1. the capture method is named and in the vocabulary        → refuse, nothing opened
2. the text is read and UTF-8-decoded                       → refuse, nothing opened
3. --captured-at is resolved as ISO-8601 with an offset     → refuse, nothing opened
4. the store is opened (it must already exist)              → refuse, nothing opened
5. the record ids are allocated and checked free            → refuse, nothing opened
6. the envelope is built                                    → (pure)
7. rules 1,2,3,4,6 + rule 5 against the prospective capture → refuse, nothing written
8. the normalization-difference requirement                 → refuse, nothing written
9. store_capture   (the immutable capture row)              → unwritable from here on
10. store_envelope (the candidate + its duplicate-hint rows)
11. the stored capture is compared byte-for-byte with the submission
12. the candidate is read back and re-validated
13. only then: the transcript and RESULT: PASS
```

Steps 7 and 8 are the reason a refused submission leaves the store byte-identical: everything that
can be known before the first write is checked before the first write. The acceptance run asserts
the store's counts are unchanged after each of the **18** refusals it exercises.

Step 1 runs before the store is even opened, so `--capture-method` cannot be "helped" into a
default by anything downstream.

Once step 9 has happened the capture is history: if step 10 failed (a genuine SQLite error, not a
refusal) the capture stays, and the CLI reports that. Captures are never deleted, and
`PROVENANCE_AND_CAPTURE_CONTRACT.md` invariant 2 is explicit that a rejected candidate does not
remove the encounter it came from.

## 3. Ruling: the record-id naming scheme

W1.2 deliberately left this open — the envelope contract carries no candidate identity, so
`store_envelope` takes `candidate_id` from the caller rather than inventing a derivation (§5.2 of
`W1_2_ENVELOPE_VALIDATOR.md`). W1.3 rules:

- `cap-YYYY-MM-DD-NNNN` for captures, `cand-YYYY-MM-DD-NNNN` for candidates, matching the ids
  already used in W1.2's fixtures (`cap-2026-09-12-0001`).
- The day is the **capture day** (`captured_at`'s date), not the wall-clock day of the command, so
  a submission recorded with an explicit historical timestamp is numbered on its own day.
- `NNNN` is four digits, one greater than the highest number already used for that kind on that
  day, derived by **scanning the store's own ids**. Not a counter table, not a random suffix, not a
  clock reading: the same store state always yields the same next id, and the acceptance run
  asserts that by computing the next id twice in-process and then checking that the CLI allocates
  exactly it.
- `--capture-id` / `--candidate-id` override the allocation. An id the store already holds is
  **refused**, before anything is written. For a candidate that would be a second write under an
  existing key; for a capture it is stronger — captures are immutable, so a submission never
  re-uses or restates one (see §7.3).

## 4. Ruling: the normalization boundary (W1.3 vs W1.4)

The card asks that a messy submission produce "a stored envelope where `captured_text` is
byte-identical to the input and `normalization_notes` explains every normalization". The
normalization *algorithm* is W1.4's lane, so W1.3 must not implement one. What W1.3 does instead:

- `candidate_text` / `candidate_author` / `candidate_source_ref` default to the captured values,
  so a plain submission is a pure capture and its note is `identical to capture` — an assertion
  that every normalization is accounted for, made by saying there was none.
- Supplying a value that differs from the capture **without** `--normalization-notes` is refused,
  naming `normalization_notes`. The refusal also names the field it would have changed, so the
  operator can see what they were about to do.
- A difference **with** a note is accepted and the note is stored verbatim. The acceptance run
  proves the capture is still byte-identical afterwards: the normalized proposal is stored
  *alongside* the encounter, never instead of it.

So the invariant W1.3 enforces is *"no normalization without a note"*, not *"no normalization"*.
W1.4 replaces the default with a deterministic transform that produces the notes itself; the
invariant is what it has to keep.

## 5. Sentinels and defaults

The sentinel vocabulary is W1.2's (`unknown` / `und` / `none` / `legacy-import`,
`garden_envelope.SENTINEL_ALLOWED`). W1.3 adds one rule of its own:

> **an omitted flag becomes the field's declared sentinel; a flag supplied empty is passed through
> untouched.**

`--attribution` omitted → `captured_attribution: "unknown"`. `--attribution ""` → `""`, which the
validator reports as `[rule-1] 'captured_attribution' is empty; a sentinel … is not an empty
string`. The distinction matters: a default that swallows an empty flag would turn "the operator
gave us nothing here" into a silent claim that the attribution is unknown, which is a different
(and better-sounding) fact. This is the mechanism behind acceptance criterion 2, and it is asserted
by 5 refusal cases and 5 "wrote nothing" checks.

`captured_by` defaults to `operator` rather than to a sentinel. That is a reading, not a contract
statement: the store's own `add_capture` has the same default (`garden_store.add_capture(…,
captured_by="operator")`), and the CLI is run by the operator. It is recorded in §7.1 so a reviewer
can disagree.

## 6. Ruling: the canonical store location

W1.1's handoff left two things to W1.3: "the canonical store location is W1.3's ruling" and "the
first commit of a populated mirror belongs to the first unit that writes real submissions (W1.3)".
W1.3 rules the first and **declines the second**, deliberately:

- **Location:** `data/store/`, created with
  `python3 scripts/garden_store.py create --dir data/store`. The SQLite file
  (`data/store/garden.sqlite3`) is **git-ignored** — it is machine-local, not diffable, and would
  put an opaque binary in the history of a repository whose whole audit story is textual. The
  deterministic text export beside it (`data/store/garden.export.txt`, `garden.export/1`) is the
  **committed mirror** W1.1's decision describes; a diff of it is a per-record diff.
- **No populated mirror is committed in W1.3.** At this unit's stop point the only submissions that
  exist are the acceptance run's own fixtures, and they live in a throwaway temp directory *by
  design* — the run has to pass from a clean clone with no committed data, which is exactly what
  W1.6's Gate B packet will require. Committing fixture submissions into the store of record's
  history would put review scaffolding into the corpus and W1.6 would have to unwind it.
  The first real operator submission is what populates the mirror, and Gate B (W1.6) is where the
  evidence store that demonstrates it belongs.

This is a deviation from W1.1's expectation and is recorded as such in `docs/DECISIONS.md`. The
ruling is the location and the split (git-ignored database, committed text mirror); only the timing
of the first populated commit moves, and it moves to the unit that will have real content.

## 7. Doctrine ambiguities found while implementing (reported, not papered over)

1. **`captured_by` has a CLI default that the contract does not give it.** The contract says
   `captured_by` is "the human or agent that performed the capture, or `legacy-import`". Defaulting
   it to `operator` is an assumption about who runs the CLI; it is not in the contract. It matches
   W1.1's store default, so the two surfaces agree, but a reviewer could reasonably require it to
   be an explicit flag. Recorded so the default is a decision rather than an accident.
2. **None of the nine optional envelope fields has a flag.** Eight have no store column at all
   (W1.1's schema; filed by W1.2), so a flag for them could only accept a value the store cannot
   hold — a silent drop, the one failure mode this program least wants. `external_id` *does* have a
   column and `store_envelope` already carries it, but no W1 flow needs it yet and an untested flag
   is worse than an absent one, so the manual surface leaves it to the adapters that will need it.
   The persistence gap stays filed in `docs/queue.md`; the migration belongs to the unit that first
   needs the columns, most likely W1.4 for `placeholder_markers`.
3. **The contract allows several captures per candidate; W1.3 creates exactly one and refuses to
   re-use an existing capture.** `PROVENANCE_AND_CAPTURE_CONTRACT.md` invariant 3 says the same
   passage may be captured twice and "the candidate records all of them". W1.3 has no path to
   attach a second capture to an existing candidate, and it refuses a `--capture-id` that already
   exists rather than restating a stored capture's fields (rule 5 compares only `captured_text` —
   W1.2 §5.1 — so a restatement could silently disagree on attribution). Both are deliberate
   narrowings; the multi-capture path belongs to the unit that needs it.
4. **The `captured_at` offset check is duplicated between the surface and rule 1.** The CLI checks
   the stamp before deriving the record ids from its date; the envelope validator checks it again
   as rule 1. The duplication is intentional (see §2 step 3) but it meant the CLI's check had **no
   unique falsifier** — a mutation removing it left the suite green, because rule 1 caught the same
   defect one step later. Resolved in review by asserting the *layering* ("refused by the
   submission surface itself, not `envelope rejected`") rather than by deleting the check. Found by
   the unit's own negative-control pass (control n14), not by reading the code.
5. **A candidate value that merely repeats the capture still needs no note, but a *sentinel*
   substitution does.** If the operator writes `--candidate-author unknown` for an encounter whose
   attribution was `Rumi`, the two differ, so a note is required — correct, but worth stating: the
   check compares values, and it does not try to judge whether a difference is "meaningful".
6. **Empty input is not the same as absent input.** `--text ""` is a submission with no text
   (rule 2, `captured_text` named); omitting all three input flags is a usage error. The first
   implementation conflated them — `--text ""` was reported as "exactly one of … is required"
   because an empty string is falsy. Fixed in the unit (the check is presence by `is not None`,
   never truthiness) and asserted, because the same trap is available to every later flag.
7. **`work_state` still has two subjects** (`W1_1_STORAGE_AND_SCHEMA.md` §8.1). W1.3 writes
   `work_state = 'queued'` per candidate because the envelope requires it; nothing here resolves
   the ambiguity, and nothing here should.
8. **Which fields may carry a sentinel is still prose** (W1.2 §5.6). W1.3 consumes W1.2's derived
   table; a new flag added later must be checked against the contract's `Notes` column rather than
   copied from a neighbour.

## 8. What this unit does not do

Per the card's stop condition — **submissions persist; no review commands**:

- no web UI, no browser capture extension, no automated discovery, no clipboard polling;
- **no normalization or duplicate-hint algorithm** (W1.4). `duplicate_hints` is always `[]` at
  intake, and there is no `--duplicate-hints` flag: hints are generated, not typed, and a hint is
  never a decision;
- **no review, queue or decision command** (W1.5). There is no `list`, `show` or `accept`
  subcommand; the stored record is dumped back out with `garden_store.py export` / `dump`, which
  already existed;
- no transition machinery, no promotion path to `canonical`, no research action — and no way for a
  submission to move any of the four state dimensions;
- no write to `quotes.csv` / `sources.csv` (read-only for the whole of W1; the acceptance run
  hashes both before and after), no network, no third-party dependency, stdlib only.

## 9. Commands

| Command | Effect |
|---|---|
| `python3 scripts/check_garden_submit.py` | the full W1.3 acceptance + evidence run (134 checks) |
| `python3 scripts/garden_submit.py submit --dir DIR --text 'TEXT' --capture-method METHOD` | one submission: capture + candidate |
| `python3 scripts/garden_submit.py submit … --emit-envelope FILE` | also write the canonical envelope JSON |
| `python3 scripts/garden_submit.py submit … --json` | one canonical JSON object instead of the transcript |
| `python3 scripts/garden_store.py export --dir DIR` | write the committed mirror; `dump` prints it |
| `python3 scripts/garden_store.py verify --dir DIR` | export → re-import → byte-identical |

## 10. Evidence

`scripts/check_garden_submit.py` runs 134 checks in a throwaway temp directory and exits 0 with
`RESULT: PASS`. It drives the CLI as a **subprocess** for every submission, so a passing run is
evidence about the real command line, not about an in-process call. Its checks cover: the messy
submission of acceptance criterion 1 (byte-identity against the submitted file's bytes, the literal
`_`, the curly quotes, the untrimmed whitespace, the uncorrected wrong author, the absent citation
as `none`); the 18 refusals (each with the field named and the store's counts unchanged); the
normalization boundary; verbatim storage through all three input modes; the id scheme; the emitted
envelope; the immutability of captures after submission; and the empty `decisions` log.

**15 negative controls** and a **separate 5-mutation review pass** are recorded in
`GARDEN_W1_3_HANDOFF.md`, each showing the run going red with a targeted `FAIL:` line and no
traceback.
