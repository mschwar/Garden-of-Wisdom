# W1.4 — Normalization + duplicate hints

**Status: implemented 2026-09-13** on branch `w1/normalization-hints` (W1.4 of
`docs/program/W1_DECOMPOSITION.md`). This document is the written half of the unit: the declared
normalization algorithm, the two (three) rulings the unit owns, and the hints it generates. The
executable half is `scripts/garden_normalize.py` (the module + CLI) and
`scripts/check_garden_normalize.py` (acceptance + evidence, **229** checks).

W1.4 is the unit the W1.3 surface deliberately left a hole for: W1.3 stored the captured text
verbatim and asserted `normalization_notes: identical to capture`; it implemented **no**
normalization and generated **no** hints. W1.4 fills both, without touching the capture.

## 1. The surface

```
python3 scripts/garden_normalize.py normalize  --dir DIR (--candidate-id ID | --all) [--json]
python3 scripts/garden_normalize.py hints      --dir DIR (--candidate-id ID | --all) [--json]
python3 scripts/garden_normalize.py classify   --reference 'TEXT'      # read-only
python3 scripts/garden_normalize.py describe   --text 'TEXT'           # read-only
```

`normalize` writes the Garden-facing **proposal** for a stored candidate:
`candidate_text`, `candidate_author`, `candidate_source_ref` and `normalization_notes`. It never
touches `captures` (the acceptance run asserts the whole `[captures]` export section is
byte-identical), never writes a state column, and never writes a `decisions` row.

`hints` recomputes the candidate's `{kind, target, basis}` rows from the store. Hints are *derived*
data: a rebuild deletes and regenerates (`garden_store.replace_duplicate_hints`), never edits, and
the acceptance run asserts that three rebuilds in a row leave identical bytes.

`classify` / `describe` are read-only helpers for inspecting one citation or one text; neither
opens a store.

## 2. The declared normalization algorithm (`garden.normalize/1`)

Deterministic, in this order, and every change is named in the note:

1. **Unicode NFC recomposition.** The capture may arrive decomposed (`Baha\u0301'i`); the proposal
   is composed. The capture keeps the decomposed bytes.
2. **Canonical characters**, one declared class at a time, each counted separately in the note:
   * `quote-marks` — curly single/double quotes and primes → `'` / `"`;
   * `dashes` — hyphen/en-dash/em-dash/figure-dash/minus → `-`;
   * `ellipsis` — `…` → `...`;
   * `no-break-spaces` — NBSP / figure space / narrow NBSP → a plain space.
   Each class is translated with **its own** table. (Applying the union of the tables in one
   `str.translate` converts a later class's characters while attributing the count to the first
   class that fired — the note then under-reports. The acceptance run counts each class
   independently and caught exactly this; control `n6` is the regression test for it.)
3. **Whitespace**: every run of whitespace (including newlines and tabs) collapses to one space,
   then leading/trailing whitespace is trimmed. The note records how many characters were
   collapsed and how many boundary characters were trimmed.
4. **Placeholder glyphs are preserved and reported, never repaired.** A literal `_` (the four
   legacy `has_unresolved_glyph` rows) stays in the proposal and the note says so. Guessing the
   character it stands for is fabrication (`docs/DECISIONS.md`, 2026-09-11).

Anything not in that list — guillemets, ideographic spaces, a trailing `— Rumi` attribution line —
is left exactly as encountered. An undeclared transform is a silent edit, so there are none.

A field whose value is unchanged by all of the above gets the note part `identical to capture`
(the same string W1.3 writes, asserted equal by the acceptance run so there is one vocabulary for
"nothing changed", not two). When no field changed at all, `normalization_notes` **is** that string.
Otherwise the note is field-attributed:

```
captured_text: quote-marks: 2 character(s) canonicalized; whitespace: 4 character(s) collapsed,
2 boundary character(s) trimmed; 1 literal '_' preserved (not repaired: guessing the character is
fabrication); captured_attribution: quote-marks: 2 character(s) canonicalized; captured_citation:
identical to capture
```

(one line in the store; wrapped here for readability).

## 3. Ruling 1 — the similarity threshold

`NEAR_TEXT_THRESHOLD = 0.60`, computed with `difflib.SequenceMatcher` over the **normalized,
case-folded** text and compared with `>=`. That is the heuristic the legacy validator already used
(`scripts/validate_quotes.py`: `ratio > 0.6`), so the repo's own 45 near-duplicate pairs stay the
reference data a reviewer can sanity-check the hints against.

**The similarity is the mean of the two directional ratios, and that is a deliberate correction.**
`SequenceMatcher.ratio()` is not symmetric: the same pair scores 0.69 one way and 0.67 the other
(measured on rows 113/114, `"Dhammapada, v. 277"` vs `v. 278`). A hint whose basis number depends on
which candidate is being compared is an artefact, and the two candidates would disagree about their
own pair; the acceptance run asserts symmetry and that both candidates' bases carry the identical
number (control `n5`). Consequence: a basis number can differ from the legacy report's by a
hundredth (0.68 vs 0.69 for that pair), which is recorded here so a reviewer does not read it as a
bug. The legacy report's own direction-dependence is filed as a separate issue, because the D6
curation pass will want to re-derive those pairs.

## 4. Ruling 2 — a shared citation is only evidence when the citation pinpoints something

This is the fix for the false-positive class `docs/data/DATA_QUALITY_REPORT.md` describes: *"many
oral-tradition rows share the literal `source_ref` value `"Oral Tradition"` with no further pinpoint
citation, so they get flagged against each other even when the quotes are unrelated … roughly half
the 45 flagged pairs are this false-positive pattern."*

`citation_specificity(reference)` classifies a citation three ways:

| class | test | examples from the corpus |
|---|---|---|
| `none` | a sentinel / empty (`none`, `unknown`, `und`, `""`) | the sentinel default |
| `generic` | no locator | `Oral Tradition` (19 rows), `Tablets of Bahá’u’lláh, Words of Paradise`, `Blessingway Chant`, `Metta Sutta` |
| `specific` | carries a **locator**: an Arabic digit, a Roman-numeral token (`CV`, `CXVII`, and a standalone `I`/`V`/`X`), or `§` | `Gita 2.47`, `Yasna 43:1`, `Gleanings, CV`, `Epistle…, p. 26`, `Dhammapada, v. 277` |

`same-reference` and `same-passage` require a **specific** shared citation. A generic label produces
no reference hint at all, even when both rows carry it verbatim and the legacy heuristic's own
predicate (`a.source_ref == b.source_ref`) would flag the pair — the acceptance run asserts the
legacy predicate *and* the absence of the hint on the same fixtures, so the guard is proven to be
doing work rather than describing itself (control `n1`).

The rule is deliberately stricter than the legacy report's split in one direction: it also
suppresses a shared *bare work title* (`Tablets of Bahá’u’lláh, Words of Paradise`, 3 rows, all
different passages). "Same work" is not "same passage", and the review surface is only pleasant if
the noise is gone; a hint is cheap to miss and expensive to act on wrongly.

## 5. The hint kinds

| kind | when | basis |
|---|---|---|
| `exact-text` | normalized, case-folded texts are identical | `normalized text identical (case-folded, N characters)` |
| `near-text` | similarity >= 0.60 and not exact | `normalized text similarity 0.74 >= 0.60 (case-folded, difflib.SequenceMatcher)` |
| `same-reference` | same **specific** citation | `same specific citation 'Gleanings, CV'` |
| `same-passage` | same specific citation **and** similarity >= 0.60 | `same specific citation 'Dhammapada, v. 277' with normalized text similarity 0.68 >= 0.60` |

Kinds co-occur (an identical passage in the same specific place gets all three of `exact-text`,
`same-reference`, `same-passage`), and they are ordered `(target, kind)` inside each candidate, so a
rebuild writes the same rows in the same `hint_seq` order. `target` is the other candidate's
`candidate_id`; the contract's `'external'` target is unused, because W1.4 compares stored
candidates against each other and does not read the frozen legacy corpus as a comparison set.

Documented divergence from the legacy heuristic, beyond ruling 2: the legacy report compared pairs
**within one `tradition`**; the W1 store has no `tradition` column, so W1.4 compares every candidate
against every other. That is the right direction for a duplicate hint (a duplicate can be filed
under a different label) and it is recorded here so it is a decision rather than an accident.

## 6. Ruling 3 — what a batch run does with a candidate it cannot normalize

A submission of nothing but whitespace is legal at intake (`captured_text` is non-empty, rule 2),
but its proposal normalizes to `""`, which is not a proposal and which the store's
`CHECK(length(candidate_text) > 0)` would refuse. There is no path anywhere in W1 to withdraw or
delete a candidate (filed as an issue by this unit), so one junk row must not make the batch
unusable:

* an **explicit** `--candidate-id` that cannot be normalized is a **refusal** — non-zero exit, the
  reason named, nothing written;
* an **`--all`** run normalizes everything it can, prints a `SKIPPED: <id>: <reason>` line for each
  candidate it cannot, and still exits 0 — but a batch where **nothing** could be normalized is a
  **failure**: a run that writes nothing must not report success.

Every candidate in a batch is checked (and its proposal computed) before any of them is written, so
a batch never half-applies. The acceptance run covers both halves: the fixture store's one
whitespace candidate is skipped while the rest normalize, and a store containing only that candidate
fails the batch with `nothing could be normalized`.

## 7. The two guard layers, and why both are asserted

`garden_store.apply_normalization` is the only write path for a proposal, and it refuses: a missing
candidate, a candidate whose `curation_state` is not `new`, an empty `candidate_text`, an empty
`normalization_notes`. `garden_normalize.proposal_for` refuses the same four things *before* the
store is asked — that pre-check is what makes the batch all-or-nothing (the store guard alone would
fire per candidate during the write loop, so a batch could half-apply).

Both layers are load-bearing, so both have their own falsifier in the acceptance run: the CLI layer
via the skip/refusal behaviour, the store layer via direct `apply_normalization` calls made by the
test. This is the lesson W1.3 recorded (`W1_3_SUBMISSION_CLI.md` §7.4): a duplicated check with no
unique falsifier is unproven. Here it was found the same way — control `n11` (removing the store's
state guard) left the suite green until the direct store-layer checks were added (controls `n15`,
`n16`, `n17` cover the reverse directions).

## 8. What this unit does not do

Per the card's stop condition — **hints generate deterministically; no decisions**:

* no auto-merge, no auto-reject, no `duplicate` decision: `curation_state` is untouched
  (`T-C4`/`T-C7`/`T-C9` stay the operator's), and `decisions` stays empty (asserted);
* no semantic or embedding similarity — the comparison is `difflib` over normalized text and a
  citation classifier, both stdlib;
* no review/queue surface (W1.5): there is no `list`/`show`/`accept` command here;
* **no schema migration.** The optional envelope fields still have no columns (W1.2's filed gap).
  W1.4 needed `placeholder_markers` *observable*, not structured, and `normalization_notes` — a
  field that exists and whose contract is "what changed and why" — carries the observation. Adding
  columns with no consumer would be a speculative schema change in a unit whose lane is ingestion,
  and it would have forced W1.1's ledger assertion to be relaxed. The decision is recorded in
  `docs/DECISIONS.md`; the persistence gap stays filed against the first unit that actually consumes
  those fields structurally;
* no write to `quotes.csv` / `sources.csv` (read-only for the whole of W1; the acceptance run hashes
  both before and after), no network, no third-party dependency, stdlib only.

## 9. Commands

| Command | Effect |
|---|---|
| `python3 scripts/check_garden_normalize.py` | the full W1.4 acceptance + evidence run (229 checks) |
| `python3 scripts/garden_normalize.py normalize --dir DIR --all` | write every candidate's proposal |
| `python3 scripts/garden_normalize.py normalize --dir DIR --candidate-id ID` | write one candidate's proposal |
| `python3 scripts/garden_normalize.py hints --dir DIR --all` | rebuild every candidate's hints |
| `python3 scripts/garden_normalize.py classify --reference 'Oral Tradition'` | read-only: specific / generic / none |
| `python3 scripts/garden_normalize.py describe --text '…'` | read-only: one text's proposal part |

## 10. Evidence

`scripts/check_garden_normalize.py` runs **229** checks in a throwaway temp directory and exits 0
with `RESULT: PASS`. It drives `garden_submit.py` and `garden_normalize.py` as **subprocesses**, so a
passing run is evidence about the real command lines, and every fixture's text and citation is read
out of the real `quotes.csv` (id 3 ~ 283 for near-text, 4/14 for a shared specific citation,
319/331/332 and 5/19 for the generic false-positive shapes, 113/114 for different verses of one
work, the `has_unresolved_glyph` rows for the placeholder rule, and a searched-for already-clean row
for the `identical to capture` case) — each fixture class is asserted to exist, with a
`would be vacuous` failure otherwise.

**17 negative controls** (mutation → first `FAIL:` line, no traceback) are recorded in
`GARDEN_W1_4_HANDOFF.md`; all 17 turn the run red with the check they were aimed at.
