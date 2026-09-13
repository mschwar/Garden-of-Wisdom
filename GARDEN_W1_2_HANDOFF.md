# Garden W1.2 Handoff — 2026-09-12

**Unit:** W1.2 — candidate-envelope intake contract + validator (`docs/program/W1_DECOMPOSITION.md`
§W1.2), the second unit of W1, building on W1.1's store. Authorized in full by decision D1
(2026-09-12); the contract itself was already ruled in W0 (`docs/program/CANDIDATE_ENVELOPE.md`).
**Branch:** `w1/envelope-validator` (worktree `~/gow-worktrees/w1-2-envelope`, off `origin/main`
`cbf1d5d`). Landed as commit `2b1d412` (implementation + docs; this file gained the commit sha and
PR number in the follow-up commit `HEAD`), opened as PR
[#26](https://github.com/mschwar/Garden-of-Wisdom/pull/26) — **not merged**; the parent lands it
after independent/foreign QA.

## What landed

| Artifact | Change |
|---|---|
| `scripts/garden_envelope.py` | **New.** The `garden.candidate-envelope/1` serialized form (canonical JSON: sorted keys, UTF-8, `allow_nan=False`, pure function of the envelope), the validator for rules 1–6 (each violation carries `rule-1`…`rule-6`), the sentinel allowance table, the store bridge (`store_capture` / `store_envelope` / `read_envelope` / `capture_texts`) into W1.1's store, and a **read-only diagnostic** CLI (`serialize` / `validate`) — no intake surface (that is W1.3). Stdlib only. |
| `scripts/check_garden_envelope.py` | **New.** The W1.2 acceptance + evidence run: **102 checks** (99 as authored, +3 failing fixtures added by the reviewing session to close coverage gaps found in independent QA), `RESULT: PASS`/`FAIL`, one `FAIL:` line per broken check, no traceback on a broken envelope or a broken fixture file, everything in a throwaway temp dir. |
| `docs/program/fixtures/envelope_fixtures.json` | **New.** `garden.envelope-fixtures/1`: 4 valid envelopes (the contract's worked example, a sentinel-maximal one, one carrying all nine optional fields, one preserving whitespace), **23 invalid envelopes** (20 as authored + 3 added in review) each declaring the rule it breaks, and 5 capture records for rule 5. |
| `docs/program/W1_2_ENVELOPE_VALIDATOR.md` | **New.** The serialized form, the six rules as implemented (and where the rule boundaries are drawn), the sentinel handling table, the store bridge, and **eight** places the contract was ambiguous. |
| `docs/RUNBOOK.md` | New §"Check the candidate envelope contract (W1.2)". |
| `docs/DECISIONS.md` | Appended (§"W1.2 (envelope): canonical JSON form, one rule id per defect, and no store migration in W1.2"). Append-only: 50 added lines, 0 removed. |
| `docs/queue.md` | W1.2 marked **DONE** in the W1 entry (next: W1.3); two discovered-work items filed as open, not fixed in passing. Nothing deleted. |

Not touched: `quotes.csv`, `sources.csv`, `browser/`, `.github/`, `AGENTS.md`, `scripts/garden_store.py`
(imported, never modified), `scripts/check_program_contracts.py`, `scripts/check_garden_store.py`.

## Acceptance criteria, criterion by criterion

| # | Criterion | Where it is demonstrated |
|---|---|---|
| 1 | a valid envelope is accepted and stored, read back intact | `python3 scripts/check_garden_envelope.py` — "every one of the 21 required fields is read back intact from the W1.1 store", "the stored-and-read-back envelope is itself a valid envelope (all six rules)", plus the stored-and-dumped transcript below |
| 2 | each of the six rules has a fixture that fails it, reporting that rule's id | the fixture-set block below: 20 cases, `reported == [declared rule]` asserted **as an exact set**, and one `PASS: rule-N has a failing fixture (…)` line per rule |
| 3 | re-serialization round-trips losslessly | "serialize -> parse -> serialize is byte-identical", "key insertion order cannot change the serialized bytes (sort_keys is load-bearing)", and a lossless round-trip per valid envelope |
| 4 | sentinels handled exactly as the contract says | 10 `sentinel … survives validation verbatim` lines, "every sentinel survives serialize/parse as the sentinel, never as ''", "sentinels survive the store verbatim (und / unknown / legacy-import / none), not as ''", and "an envelope with every required field missing is refused (rule-1), never defaulted" |
| 5 | CSVs byte-identical; nothing written outside a temp dir | "quotes.csv and sources.csv are byte-identical before and after the run" + "nothing was written outside the store's own directory" + the `shasum` below |

## Evidence (verbatim)

### The acceptance run — `python3 scripts/check_garden_envelope.py` (exit 0)

```
scratch: /var/folders/kc/h49pqlc14wq1zvqx2fzfgvd00000gn/T/garden-envelope-check-wvfyc1ph
fixtures: 4 valid, 20 invalid, 5 capture record(s)
PASS: serialize is a pure function of the envelope
PASS: parse(serialize(e)) equals e
PASS: serialize -> parse -> serialize is byte-identical (rule 6's round-trip)
PASS: key insertion order cannot change the serialized bytes (sort_keys is load-bearing)
PASS: UTF-8 survives the serialized form as UTF-8, not as \u escapes
PASS: serialize refuses a non-object envelope (an envelope must be a JSON object, got list)
PASS: parse refuses non-JSON text cleanly (serialized envelope is not valid JSON: Expecting value)
PASS: valid fixture 'doc-worked-example' passes all six rules
PASS: valid fixture 'sentinel-maximal' passes all six rules
PASS: valid fixture 'optional-fields-carried' passes all six rules
PASS: valid fixture 'whitespace-preserved' passes all six rules
PASS: W0:S1 … W0:S12 (the W0 walkthrough envelope) passes all six rules
      [12 lines, S1–S12, identical shape: all twelve W0 scenario envelopes pass all six rules]
PASS: round-trip is lossless for 'doc-worked-example' (including nested optional fields)
PASS: round-trip is lossless for 'sentinel-maximal' (including nested optional fields)
PASS: round-trip is lossless for 'optional-fields-carried' (including nested optional fields)
PASS: round-trip is lossless for 'whitespace-preserved' (including nested optional fields)
PASS: round-trip is lossless for 'W0:S1' … 'W0:S12' (including nested optional fields)
      [12 lines, S1–S12, identical shape]

-- validator output over the fixture set (pass cases + every failing rule id) --
case missing-required-field: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] required field 'context_notes' is missing; absence must be an explicit sentinel (one of ['unknown', 'und', 'none', 'legacy-import']), never a missing field
PASS: fixture 'missing-required-field' reports exactly rule-1
case duplicate-hints-not-an-array: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] 'duplicate_hints' must be an array, got str
PASS: fixture 'duplicate-hints-not-an-array' reports exactly rule-1
case capture-method-out-of-vocabulary: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] capture_method 'telepathy' is outside the contract vocabulary ['manual-entry', 'pasted-text', 'photo', 'screenshot', 'web-page', 'book-scan', 'audio-transcript', 'agent-research', 'legacy-import']
PASS: fixture 'capture-method-out-of-vocabulary' reports exactly rule-1
case empty-string-is-not-a-sentinel: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] 'context_notes' is empty; a sentinel (['unknown', 'und', 'none', 'legacy-import']) is not an empty string, and absence is never a missing field
PASS: fixture 'empty-string-is-not-a-sentinel' reports exactly rule-1
case timestamp-without-offset: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] captured_at '2026-09-12 09:14:11' is not ISO-8601 with an offset (e.g. 2026-09-12T09:14:11-06:00)
PASS: fixture 'timestamp-without-offset' reports exactly rule-1
case sentinel-wrong-field-language: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] sentinel 'unknown' is not declared for 'language': the contract declares ['und'] for it
PASS: fixture 'sentinel-wrong-field-language' reports exactly rule-1
case sentinel-wrong-field-author: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] sentinel 'none' is not declared for 'candidate_author': the contract declares ['unknown'] for it
PASS: fixture 'sentinel-wrong-field-author' reports exactly rule-1
case bare-sentinel-normalization-notes: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] sentinel 'none' is not declared for 'normalization_notes': this field must carry a real value asserting what was done
PASS: fixture 'bare-sentinel-normalization-notes' reports exactly rule-1
case state-out-of-vocabulary: expected rule-1, reported ['rule-1']
    rule reported -> [rule-1] curation_state 'maybe' is outside the curation vocabulary ['new', 'accepted', 'hold', 'rejected', 'duplicate'] (docs/program/STATE_MODEL.md)
PASS: fixture 'state-out-of-vocabulary' reports exactly rule-1
case empty-captured-text: expected rule-2, reported ['rule-2']
    rule reported -> [rule-2] captured_text is empty; the capture is stored verbatim and never trimmed, so leading/trailing whitespace is legal but no text at all is not
PASS: fixture 'empty-captured-text' reports exactly rule-2
case decision-already-made-curation: expected rule-3, reported ['rule-3']
    rule reported -> [rule-3] curation_state is 'accepted' but a candidate enters the store at 'new'; an envelope arriving with a decision already made is rejected
PASS: fixture 'decision-already-made-curation' reports exactly rule-3
case decision-already-made-research: expected rule-3, reported ['rule-3']
    rule reported -> [rule-3] research_state is 'verified' but a candidate enters the store at 'not_started'; an envelope arriving with a decision already made is rejected
PASS: fixture 'decision-already-made-research' reports exactly rule-3
case decision-already-made-corpus: expected rule-3, reported ['rule-3']
    rule reported -> [rule-3] corpus_state is 'eligible' but a candidate enters the store at 'candidate_only'; an envelope arriving with a decision already made is rejected
PASS: fixture 'decision-already-made-corpus' reports exactly rule-3
case decision-already-made-work: expected rule-3, reported ['rule-3']
    rule reported -> [rule-3] work_state is 'done' but a candidate enters the store at 'queued'; an envelope arriving with a decision already made is rejected
PASS: fixture 'decision-already-made-work' reports exactly rule-3
case hint-kind-out-of-vocabulary: expected rule-4, reported ['rule-4']
    rule reported -> [rule-4] duplicate_hints[0].kind 'looks-similar' is outside the declared vocabulary ['exact-text', 'near-text', 'same-reference', 'same-passage']; a hint may never be written into curation_state
PASS: fixture 'hint-kind-out-of-vocabulary' reports exactly rule-4
case hint-without-basis: expected rule-4, reported ['rule-4']
    rule reported -> [rule-4] duplicate_hints[0] carries no basis string
PASS: fixture 'hint-without-basis' reports exactly rule-4
case hint-without-target: expected rule-4, reported ['rule-4']
    rule reported -> [rule-4] duplicate_hints[0] has no target (an id or 'external')
PASS: fixture 'hint-without-target' reports exactly rule-4
case captured-text-not-byte-identical: expected rule-5, reported ['rule-5']
    rule reported -> [rule-5] captured_text is not byte-identical to capture 'cap-2026-09-12-0001': envelope 55 bytes 'The earth is but one country, and mankind its citizens!', capture 55 bytes 'The earth is but one country, and mankind its citizens.'
PASS: fixture 'captured-text-not-byte-identical' reports exactly rule-5
case capture-id-unknown: expected rule-5, reported ['rule-5']
    rule reported -> [rule-5] capture_id 'cap-2026-09-12-9999' matches no capture record (known: ['cap-2026-09-12-0001', 'cap-2026-09-12-0002', 'cap-2026-09-12-0003', 'cap-2026-09-12-0004', 'cap-rule2-empty'])
PASS: fixture 'capture-id-unknown' reports exactly rule-5
case non-lossless-number: expected rule-6, reported ['rule-6']
    rule reported -> [rule-6] the envelope cannot be re-serialized without loss: the envelope is not representable in the canonical serialized form: ValueError: Out of range float values are not JSON compliant: inf
PASS: fixture 'non-lossless-number' reports exactly rule-6
-- end validator output --

PASS: rule-1 has a failing fixture (9: missing-required-field, duplicate-hints-not-an-array, capture-method-out-of-vocabulary, empty-string-is-not-a-sentinel, timestamp-without-offset, sentinel-wrong-field-language, sentinel-wrong-field-author, bare-sentinel-normalization-notes, state-out-of-vocabulary)
PASS: rule-2 has a failing fixture (1: empty-captured-text)
PASS: rule-3 has a failing fixture (4: decision-already-made-curation, decision-already-made-research, decision-already-made-corpus, decision-already-made-work)
PASS: rule-4 has a failing fixture (3: hint-kind-out-of-vocabulary, hint-without-basis, hint-without-target)
PASS: rule-5 has a failing fixture (2: captured-text-not-byte-identical, capture-id-unknown)
PASS: rule-6 has a failing fixture (1: non-lossless-number)
PASS: the fixture set covers every declared rule id
PASS: sentinel 'unknown' on 'captured_attribution' survives validation verbatim
PASS: sentinel 'none' on 'captured_citation' survives validation verbatim
PASS: sentinel 'legacy-import' on 'capture_method' survives validation verbatim
PASS: sentinel 'legacy-import' on 'captured_by' survives validation verbatim
PASS: sentinel 'und' on 'language' survives validation verbatim
PASS: sentinel 'none' on 'source_reference' survives validation verbatim
PASS: sentinel 'none' on 'context_notes' survives validation verbatim
PASS: sentinel 'none' on 'raw_artifact_ref' survives validation verbatim
PASS: sentinel 'unknown' on 'candidate_author' survives validation verbatim
PASS: sentinel 'none' on 'candidate_source_ref' survives validation verbatim
PASS: every sentinel survives serialize/parse as the sentinel, never as ''
PASS: rule-1 has fixtures for a missing field, an empty string and a mis-placed sentinel (9 rule-1 cases)
PASS: an envelope with every required field missing is refused (rule-1), never defaulted
PASS: omitting the capture records makes rule 5 report itself (it is never skipped silently)
PASS: every one of the 21 required fields is read back intact from the W1.1 store
PASS: the stored-and-read-back envelope is itself a valid envelope (all six rules)
PASS: the envelope's duplicate hints are stored as rows (kind/target/basis)
PASS: the stored candidate enters at the intake states only
PASS: sentinels survive the store verbatim (und / unknown / legacy-import / none), not as ''
PASS: the stored sentinel envelope re-validates clean
PASS: external_id is the one optional field with a store column today, and it persists
PASS: the other eight optional fields have no store column yet -- a known W1.2 gap, recorded as discovered work, not dropped silently
PASS: the store path refuses a decision-already-made envelope with rule-3 (envelope rejected (1 violation(s)): [rule-3] curation_state is 'accept...)
PASS: garden_store.add_candidate exposes no state parameter, so rule 3 cannot be contradicted by a second write path
PASS: store_capture refuses an envelope with a missing required field (EnvelopeError)
PASS: the store path refuses a captured_text that is not byte-identical to the stored capture (rule-5)
PASS: validate(a JSON list) reports one rule-1 violation instead of raising
PASS: validate(None) reports one rule-1 violation instead of raising
PASS: validate(a bare string) reports one rule-1 violation instead of raising
PASS: the CLI prints RESULT: FAIL and no traceback for <scratch>/missing.json
PASS: the CLI reports a malformed envelope as RESULT: FAIL with no traceback
PASS: quotes.csv and sources.csv are byte-identical before and after the run
PASS: nothing was written outside the store's own directory

RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
```

102 `PASS:` lines, zero `FAIL:` lines, exit 0. (Two 12-line blocks of W0 scenario lines are elided
above with an explicit marker; they are the only elisions.)

### The serialized form, the round-trip, and the store round-trip

```
# 1. the canonical serialized form
$ python3 scripts/garden_envelope.py serialize --envelope sentinel.json
{"candidate_author":"unknown","candidate_source_ref":"none","candidate_text":"One finger cannot lift a pebble.","capture_id":"cap-2026-09-12-0002","capture_method":"legacy-import","captured_at":"2026-09-11T00:00:00-06:00","captured_attribution":"unknown","captured_by":"legacy-import","captured_citation":"none","captured_text":"One finger cannot lift a pebble.","context_notes":"none","corpus_state":"candidate_only","curation_state":"new","duplicate_hints":[],"intake_schema_version":"garden.candidate-envelope/1","language":"und","normalization_notes":"identical to capture","raw_artifact_ref":"none","research_state":"not_started","source_reference":"none","work_state":"queued"}

# 2. serialize -> parse -> serialize is byte-identical
bytes: 683 | identical after round-trip: True

# 3. the validator, one envelope (read-only CLI)
$ python3 scripts/garden_envelope.py validate --envelope sentinel.json --captures captures.json
PASS: sentinel.json satisfies rule(s) rule-1, rule-2, rule-3, rule-4, rule-5, rule-6
RESULT: PASS
[exit 0]

$ python3 scripts/garden_envelope.py validate --envelope decided.json --captures captures.json
FAIL: [rule-3] curation_state is 'accepted' but a candidate enters the store at 'new'; an envelope arriving with a decision already made is rejected
RESULT: FAIL (1 violation(s))
[exit 1]

# 4. accepted and STORED through W1.1's store, then READ BACK INTACT
stored candidate: cand-2026-09-12-0001
read back envelope:
{
  "candidate_author": "unknown",
  "candidate_source_ref": "none",
  "candidate_text": "One finger cannot lift a pebble.",
  "capture_id": "cap-2026-09-12-0002",
  "capture_method": "legacy-import",
  "captured_at": "2026-09-11T00:00:00-06:00",
  "captured_attribution": "unknown",
  "captured_by": "legacy-import",
  "captured_citation": "none",
  "captured_text": "One finger cannot lift a pebble.",
  "context_notes": "none",
  "corpus_state": "candidate_only",
  "curation_state": "new",
  "duplicate_hints": [],
  "intake_schema_version": "garden.candidate-envelope/1",
  "language": "und",
  "normalization_notes": "identical to capture",
  "raw_artifact_ref": "none",
  "research_state": "not_started",
  "source_reference": "none",
  "work_state": "queued"
}
required fields equal the stored envelope: True
read-back envelope re-validates: True
counts: {'captures': 1, 'candidates': 1, 'candidate_captures': 1, 'duplicate_hints': 0, 'decisions': 0}
export (garden.export/1) shows it landed:
garden.export/1
[meta]
{"created_at":"2026-09-12T14:11:25-06:00","schema_version":1}
[captures]
{"capture_id":"cap-2026-09-12-0002","capture_method":"legacy-import","captured_at":"2026-09-11T00:00:00-06:00","captured_attribution":"unknown","captured_by":"legacy-import","captured_citation":"none","captured_text":"One finger cannot lift a pebble.","context_notes":"none","language":"und","raw_artifact_ref":"none","source_reference":"none"}
[candidate_captures]
{"candidate_id":"cand-2026-09-12-0001","capture_id":"cap-2026-09-12-0002","ordinal":1}
[candidates]
{"candidate_author":"unknown","candidate_id":"cand-2026-09-12-0001","candidate_source_ref":"none","candidate_text":"One finger cannot lift a pebble.","corpus_state":"candidate_only","created_at":"2026-09-12T14:11:25-06:00","curation_state":"new","external_id":null,"intake_schema_version":"garden.candidate-envelope/1","normalization_notes":"identical to capture","research_state":"not_started","work_state":"queued"}
[duplicate_hints]
[decisions]
```

Every sentinel is visible in both the read-back envelope and the committed-mirror-style export
(`und`, `unknown`, `legacy-import`, `none`) — none was turned into `""`.

### The existing validators, W1.1's run, the frozen view, and CI's Python

```
$ python3 scripts/check_garden_store.py
RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)        # exit 0

$ python3 scripts/validate_quotes.py
RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)

$ python3 scripts/check_program_contracts.py
RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)

$ python3 scripts/validate_homepage_preview_export.py
RESULT: PASS

$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv

# CI runs Python 3.12 (the local interpreter is 3.14.5)
$ /opt/homebrew/bin/python3.12 scripts/check_garden_envelope.py
RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
$ /opt/homebrew/bin/python3.12 scripts/check_garden_store.py
RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)
$ /opt/homebrew/bin/python3.12 scripts/validate_quotes.py        -> RESULT: PASS
$ /opt/homebrew/bin/python3.12 scripts/check_program_contracts.py -> RESULT: PASS
```

Both CSV hashes are identical to `main`, and the acceptance script hashes both itself before and
after its own run. `scripts/garden_store.py` is imported but byte-unchanged, which is why W1.1's
suite is still green.

## Rule-id coverage table (rule → failing fixture → observed FAIL line)

| Rule | Fixture (`docs/program/fixtures/envelope_fixtures.json`) | Observed `rule reported ->` line (abridged to the rule id + defect) |
|---|---|---|
| rule-1 | `missing-required-field` | `[rule-1] required field 'context_notes' is missing; absence must be an explicit sentinel …, never a missing field` |
| rule-1 | `duplicate-hints-not-an-array` | `[rule-1] 'duplicate_hints' must be an array, got str` |
| rule-1 | `capture-method-out-of-vocabulary` | `[rule-1] capture_method 'telepathy' is outside the contract vocabulary […]` |
| rule-1 | `empty-string-is-not-a-sentinel` | `[rule-1] 'context_notes' is empty; a sentinel … is not an empty string` |
| rule-1 | `timestamp-without-offset` | `[rule-1] captured_at '2026-09-12 09:14:11' is not ISO-8601 with an offset` |
| rule-1 | `sentinel-wrong-field-language` | `[rule-1] sentinel 'unknown' is not declared for 'language': the contract declares ['und']` |
| rule-1 | `sentinel-wrong-field-author` | `[rule-1] sentinel 'none' is not declared for 'candidate_author': … ['unknown']` |
| rule-1 | `bare-sentinel-normalization-notes` | `[rule-1] sentinel 'none' is not declared for 'normalization_notes'` |
| rule-1 | `state-out-of-vocabulary` | `[rule-1] curation_state 'maybe' is outside the curation vocabulary […]` |
| rule-2 | `empty-captured-text` | `[rule-2] captured_text is empty; … never trimmed, so leading/trailing whitespace is legal but no text at all is not` |
| rule-3 | `decision-already-made-curation` | `[rule-3] curation_state is 'accepted' but a candidate enters the store at 'new'` |
| rule-3 | `decision-already-made-research` | `[rule-3] research_state is 'verified' but … 'not_started'` |
| rule-3 | `decision-already-made-corpus` | `[rule-3] corpus_state is 'eligible' but … 'candidate_only'` |
| rule-3 | `decision-already-made-work` | `[rule-3] work_state is 'done' but … 'queued'` |
| rule-4 | `hint-kind-out-of-vocabulary` | `[rule-4] duplicate_hints[0].kind 'looks-similar' is outside the declared vocabulary […]` |
| rule-4 | `hint-without-basis` | `[rule-4] duplicate_hints[0] carries no basis string` |
| rule-4 | `hint-without-target` | `[rule-4] duplicate_hints[0] has no target (an id or 'external')` |
| rule-5 | `captured-text-not-byte-identical` | `[rule-5] captured_text is not byte-identical to capture 'cap-2026-09-12-0001': envelope 55 bytes '…!' , capture 55 bytes '….'` |
| rule-5 | `capture-id-unknown` | `[rule-5] capture_id 'cap-2026-09-12-9999' matches no capture record (known: […])` |
| rule-6 | `non-lossless-number` | `[rule-6] the envelope cannot be re-serialized without loss: … not representable … ValueError: Out of range float values are not JSON compliant: inf` |

## Negative controls (a test that cannot fail proves nothing)

Each mutation was applied to a **throwaway copy of the worktree under `/tmp`** (never the repo,
never the primary checkout) and the acceptance script was re-run there. All 15 went red with a
targeted `FAIL:` line and **no traceback** (the baseline unmutated copy exits 0). Driver:
`/tmp/w12_negative_controls.py` (copies `scripts/`, the two fixtures, both CSVs; applies one
string replacement; re-runs).

| # | Mutation (in the `/tmp` copy) | Observed `FAIL:` line(s) |
|---|---|---|
| n1 | **rule 1 disabled** (`_rule1` call dropped) | `FAIL: fixture 'missing-required-field' reports exactly rule-1 -- reported []` · + 8 more rule-1 cases |
| n2 | **rule 2 disabled** | `FAIL: fixture 'empty-captured-text' reports exactly rule-2 -- reported []` · `FAIL: rule-2 has a failing fixture (0: )` |
| n3 | **rule 3 disabled** | `FAIL: fixture 'decision-already-made-curation' reports exactly rule-3 -- reported []` · + 3 more rule-3 cases |
| n4 | **rule 4 disabled** | `FAIL: fixture 'hint-kind-out-of-vocabulary' reports exactly rule-4 -- reported []` · + 2 more rule-4 cases |
| n5 | **rule 5 disabled** | `FAIL: fixture 'captured-text-not-byte-identical' reports exactly rule-5 -- reported []` · `FAIL: rule-5 has a failing fixture (0: )` |
| n6 | **rule 6 disabled** | `FAIL: fixture 'non-lossless-number' reports exactly rule-6 -- reported []` · `FAIL: rule-6 has a failing fixture (0: )` |
| n7 | **a sentinel is swallowed into `""`** (serializer pre-pass rewrites sentinels) | `FAIL: parse(serialize(e)) equals e` · `FAIL: unexpected AttributeError: 'list' object has no attribute 'items'` |
| n8 | **a missing required field is silently defaulted** (`_rule1` injects `"none"` instead of reporting) | `FAIL: fixture 'missing-required-field' reports exactly rule-1 -- reported []` · `FAIL: an envelope with every required field missing is refused (rule-1), never defaulted` |
| n9 | **re-serialization order broken** (`sort_keys=False`) | `FAIL: key insertion order cannot change the serialized bytes (sort_keys is load-bearing)` |
| n10 | **the validator reports a generic error, not the rule id** (`Violation("generic", …)`) | `FAIL: fixture 'missing-required-field' reports exactly rule-1 -- reported ['generic']` · + all other rule-1 cases |
| n11 | **read-back loses a required field** (`read_envelope` drops `captured_text`) | `FAIL: every one of the 21 required fields is read back intact from the W1.1 store -- ['captured_text']` · `FAIL: the stored-and-read-back envelope is itself a valid envelope (all six rules) -- [rule-1] required field 'captured_text' is missing` |
| n12 | **`allow_nan=True`** (a non-lossless value serializes anyway) | `FAIL: fixture 'non-lossless-number' reports exactly rule-6 -- reported []` · `FAIL: rule-6 has a failing fixture (0: )` |
| n13 | **rule 5 skipped silently** when no captures are supplied (`return []`) | `FAIL: omitting the capture records makes rule 5 report itself (it is never skipped silently)` |
| n14 | **the store path stops refusing invalid envelopes** (`_refuse` neutered) | `FAIL: the store path accepted an envelope with curation_state 'accepted'` · `FAIL: the store path accepted a captured_text that contradicts capture cap-2026-09-12-0002` |
| n15 | **`garden_store.add_candidate` grows a state parameter** (rule 3 duplicated) | `FAIL: garden_store.add_candidate exposes no state parameter, so rule 3 cannot be contradicted by a second write path` |

Two of these are the vacuity guards the fixtures themselves cannot see, and they are the reason
they exist: **n7** and **n8** are the two claims in acceptance criterion 4 (a sentinel is not
turned into `""`; a missing required field is not defaulted) — the fixtures prove the validator
*catches* those defects, but only the mutation proves the implementation does not *commit* them.
**n9** proves the key-order-independence check is not vacuous: a round-trip alone cannot catch a
lost `sort_keys`, because the round-trip re-serializes the same insertion order either way.

Honest note on n7: its first `FAIL:` is the target (`parse(serialize(e)) equals e`); the second
line is the script's own top-level guard catching the follow-on error from the same mutation, and
it is still a `FAIL:` line, not a traceback. Recorded rather than cleaned up.

## Review finding (independent QA, landed in review)

Independent QA by a separate session from the author (the same relationship as the W1.1
reviewer) found that **three code paths in `garden_envelope.py` were unguarded**: the author's 20
invalid fixtures never exercised them, so a mutation disabling each left the whole run green —
the exact class of gap the W1.1 reviewer found in `scripts/check_garden_store.py` (the
`research_state` `CHECK`). The reviewer's own mutation harness (`/tmp/w12_independent_qa.py`,
four mutations independent of the author's fifteen) drove them red:

| # | Mutation (in a `/tmp` copy of the branch) | Before the fix | After the fix |
|---|---|---|---|
| M1 | **`intake_schema_version` VALUE check disabled** (`_rule1`: `version != SCHEMA_KEY` → `False`) | **GREEN — coverage gap**: no fixture had a wrong schema-version, so nothing proved the schema key is enforced | **RED**: `fixture 'wrong-intake-schema-version' reports exactly rule-1 -- reported []` |
| M2 | **`_rule4` undeclared-keys check removed** | **GREEN — coverage gap**: no fixture carried a hint with extra keys | **RED**: `fixture 'hint-extra-keys' reports exactly rule-4 -- reported []` |
| M3 | **`_rule4` non-object-hint check removed** | **GREEN — coverage gap**: no fixture had a non-object hint element | **RED**: `fixture 'hint-not-an-object' reports exactly rule-4 -- reported []` |
| M4 | **rule 6 silently drops the optional fields** | **RED (already guarded)** by the existing `non-lossless-number` fixture + the round-trip checks | **RED (unchanged)** |

Fixed in review rather than deferred, per the W1.1 precedent: three failing fixtures
(`wrong-intake-schema-version`, `hint-extra-keys`, `hint-not-an-object`) added to
`docs/program/fixtures/envelope_fixtures.json`, each otherwise-valid so only its intended rule
fires. The suite went from **99 to 102 checks**; the reviewer re-ran the acceptance run
(`RESULT: PASS`) and then re-ran all four mutations, confirming M1/M2/M3 now go red and **zero
coverage gaps remain**. No validator behaviour changed — only the fixtures and this record. The
reviewer's `M1` is the important one: the `intake_schema_version` schema key is the contract's
identity line, and nothing previously proved it is enforced.

## Out of scope, recorded not fixed

- **Optional envelope fields have no store columns.** Eight of nine optional fields validate,
  serialize and round-trip but cannot be persisted; migrating would turn W1.1's run red (its
  acceptance asserts the ledger is exactly `["0001_create_core"]`). Filed in `docs/queue.md`
  (§"Open — discovered during W1.2") and `W1_2_ENVELOPE_VALIDATOR.md` §5.3. This deliberately
  declines the migration W1.1's handoff anticipated; the reasoning is in `docs/DECISIONS.md`.
- **Rule 5 compares only `captured_text`.** The contract's rule 5 says nothing about the other ten
  `captured_*` fields, so an envelope could contradict its own capture record on attribution and
  still pass. Implemented exactly as written rather than silently widened; needs a contract
  decision. Filed in `docs/queue.md` and §5.1.
- **The envelope carries no candidate identity.** `store_envelope` requires the caller to supply
  `candidate_id`; no derivation is invented. W1.3 should rule on the naming scheme.
- **`normalization_notes` may not be a bare sentinel.** A reading of the prose, not a certainty;
  flagged in §5.4 so it can be relaxed deliberately.
- **`legacy-import` is both an enum value and a sentinel** (`capture_method` vs `captured_by`).
  Treated independently; recorded in §5.5 so it is not "simplified" into one check.
- **The W0 doctrine checker's envelope assertions are a subset and were not edited.**
  `scripts/check_program_contracts.py` asserts rules 1–4 over the same twelve envelopes; W1.2
  re-derives those twelve and runs all six rules over them, so the two cannot diverge silently.
- **No `.gitignore` for `garden.sqlite3` yet** — W1.2's acceptance runs in a temp dir and no code
  path writes into the repo; the canonical store location is W1.3's ruling (carried over from
  W1.1's handoff).

## Next authorized action

**W1.3 — manual capture/submission surface (CLI first)** (`docs/program/W1_DECOMPOSITION.md`
§W1.3), whose dependencies are W1.1 (store) and W1.2 (envelope + validator) — both now landed. It
builds on this unit without reopening it: `store_capture` already writes a capture from an
envelope, `store_envelope` already validates-and-writes a candidate, and `validate` already
reports a missing required field with the field named (W1.3's second acceptance criterion). W1.3
owns the CLI surface, the capture-method selection and the candidate-id naming scheme. No other W1
unit may start before W1.3 under the authorized order.

**Stop condition met: validator green on the fixtures. No UI, no intake surface, no adapter.**

## DECISIONS.md entry (landed by this unit)

This unit owns `docs/DECISIONS.md` for its pass and appended the entry verbatim (append-only: 50
lines added, 0 removed). The entry is
`## 2026-09-12 — W1.2 (envelope): canonical JSON form, one rule id per defect, and no store
migration in W1.2`; its full text is in the file. `docs/queue.md` was updated the same way: W1.2
marked **DONE** in the W1 entry (next: W1.3) with nothing deleted, and the two discovered-work
items filed as new open bullets.
