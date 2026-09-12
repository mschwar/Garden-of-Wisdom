# Garden W1.1 Handoff — 2026-09-12

**Unit:** W1.1 — storage decision + minimal schema (`docs/program/W1_DECOMPOSITION.md` §W1.1),
the first unit of W1. Authorized by decision D1 (2026-09-12), decided by D2 (storage).
**Branch:** `w1/storage-schema` (worktree `~/gow-worktrees/w1-1-storage`, off `origin/main`
`6df549b`). Landed as commit `355648f`, opened as PR
[#25](https://github.com/mschwar/Garden-of-Wisdom/pull/25) — **not merged**; the parent lands it
after independent/foreign QA.

## What landed

| Artifact | Change |
|---|---|
| `scripts/garden_store.py` | **New.** The store of record: SQLite (stdlib `sqlite3`, no dependency, no server, no network), the DDL for captures / candidates / candidate↔capture links / duplicate hints / the append-only decision log / the migration ledger, the create-from-empty migration with the idempotency rule, the deterministic `garden.export/1` text export + import, and the `create`/`export`/`dump`/`import`/`verify` CLI. |
| `scripts/check_garden_store.py` | **New.** The W1.1 acceptance + evidence run: 59 checks, `RESULT: PASS`/`FAIL`, one `FAIL:` line per broken check, no traceback on a broken store, everything in a throwaway temp dir. |
| `docs/program/W1_1_STORAGE_AND_SCHEMA.md` | **New.** The eight-requirement comparison, the rejected options with the requirement each failed, the DDL summary, the four vocabularies as implemented, the idempotency rule, the export format, and six doctrine ambiguities found while implementing. |
| `docs/RUNBOOK.md` | New §"Create and check the corpus store (W1.1)". |

Not touched: `quotes.csv`, `sources.csv`, `browser/`, `.github/`, `docs/DECISIONS.md`,
`docs/queue.md` (the last two are another agent's files in this pass).

## Evidence (verbatim, on the branch, `python3` = 3.14.5)

### The acceptance run

```
$ python3 scripts/check_garden_store.py
PASS: create-from-empty applied migration ['0001_create_core'] into an empty directory
PASS: re-running create applied no migration (reported no-op)
PASS: re-running create left the store byte-identical (export unchanged)
PASS: the re-run says so on stdout ('no-op: migration ... already applied')
PASS: captured_text round-trips byte-identically through the store (verbatim)
PASS: a new candidate enters at the intake states only
PASS: a candidate may reference more than one capture (ordered)
PASS: exporting twice produces byte-identical text
PASS: captures export in sorted order even though cap-0002 was written first
PASS: candidates export in sorted order (not insertion order)
PASS: one record per line: 22 lines for 22 expected
PASS: round-trip is byte-identical (write -> export -> wipe -> re-import)
PASS: every record survived the round-trip
PASS: re-importing the same text is a no-op and says so (no-op: store already holds exactly this text)
PASS: decisions rejects UPDATE (decisions is append-only: UPDATE rejected)
PASS: decisions rejects DELETE (decisions is append-only: DELETE rejected)
PASS: captures rejects UPDATE (captures is immutable: UPDATE rejected)
PASS: captures rejects DELETE (captures is immutable: DELETE rejected)
PASS: curation vocabulary equals STATE_MODEL.md (5 values)
PASS: research vocabulary equals STATE_MODEL.md (6 values)
PASS: corpus vocabulary equals STATE_MODEL.md (4 values)
PASS: work vocabulary equals STATE_MODEL.md (5 values)
PASS: the SQL layer rejects curation_state = 'maybe' (CHECK constraint failed: curation_state IN ('new', 'accepted', 'hold', 'rejected', 'duplicate'))
PASS: the API rejects to_state = 'maybe' (to_state='maybe' is outside the curation vocabulary [...] in docs/program/STATE_MODEL.md)
PASS: rebuilding duplicate hints from the same basis reproduces the same rows (deterministic)
PASS: the unreviewed queue is newest-first and excludes decided rows
PASS: the queue returns exactly the 1999 undecided rows at ~2,000 rows
PASS: every rejected item returns with its reason
PASS: the queue query stays on idx_candidates_queue at 2,000 rows
PASS: quotes.csv and sources.csv are byte-identical before and after the run
PASS: the store wrote nothing outside its own directory
... (59 PASS lines in total)

RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)   # exit 0
```

The nasty capture used by the round-trip check is edge-case-shaped on purpose:
leading/trailing spaces, a tab, an embedded newline, curly quotes, an em dash and the literal
`_` placeholder (`"  The earth is but one country,\n\tand mankind its citizens — “attributed” —
Bahá_u’lláh  "`). It is stored and returned byte-identically, and survives the export/import
cycle unchanged. The store's write-once triggers refuse to "clean" it.

### The migration, from an empty directory, through the CLI

```
$ python3 scripts/garden_store.py create --dir /tmp/cli-demo/store
store: /tmp/cli-demo/store/garden.sqlite3
applied migration(s): 0001_create_core
RESULT: PASS

$ python3 scripts/garden_store.py create --dir /tmp/cli-demo/store      # the re-run
store: /tmp/cli-demo/store/garden.sqlite3
applied migration(s): none
no-op: migration 0001_create_core already applied; store unchanged
RESULT: PASS
```

### Export / re-import / verify (one capture + one candidate + one decision)

```
$ python3 scripts/garden_store.py export --dir /tmp/cli-demo/store
export: /tmp/cli-demo/store/garden.export.txt (1485 bytes)
RESULT: PASS

$ python3 scripts/garden_store.py dump --dir /tmp/cli-demo/store
garden.export/1
[meta]
{"created_at":"2026-09-12T13:58:30-06:00","schema_version":1}
[captures]
{"capture_id":"cap-2026-09-12-0001","capture_method":"screenshot","captured_at":"2026-09-12T09:14:11-06:00","captured_attribution":"Bahá’u’lláh","captured_by":"operator","captured_citation":"attributed - seen on a quote card","captured_text":"The earth is but one country,\nand mankind its citizens.","context_notes":"none","language":"en","raw_artifact_ref":"none","source_reference":"https://example-quotes.example/one-country"}
[candidate_captures]
{"candidate_id":"cand-2026-09-12-0001","capture_id":"cap-2026-09-12-0001","ordinal":1}
[candidates]
{"candidate_author":"Bahá’u’lláh","candidate_id":"cand-2026-09-12-0001","candidate_source_ref":"none","candidate_text":"The earth is but one country, and mankind its citizens.","corpus_state":"candidate_only","created_at":"2026-09-12T13:58:30-06:00","curation_state":"new","external_id":null,"intake_schema_version":"garden.candidate-envelope/1","normalization_notes":"identical to capture apart from the line break","research_state":"not_started","work_state":"queued"}
[duplicate_hints]
[decisions]
{"action":"curation-decision","actor":"operator","actor_kind":"operator","dimension":"curation","from_state":"new","occurred_at":"2026-09-12T09:40:00-06:00","reason":"attribution shape to be checked by a human","seq":1,"subject_id":"cand-2026-09-12-0001","subject_kind":"candidate","to_state":"hold","transition_id":"T-C2"}

$ python3 scripts/garden_store.py import --dir /tmp/cli-demo/store --from /tmp/cli-demo/store/garden.export.txt
import: /tmp/cli-demo/store/garden.export.txt -> /tmp/cli-demo/store/garden.sqlite3
no-op: store already holds exactly this text
RESULT: PASS

$ python3 scripts/garden_store.py verify --dir /tmp/cli-demo/store
round-trip: 1485 bytes identical (imported 4 record(s))
RESULT: PASS
```

### Existing validators, byte-identical frozen view, and CI's Python

```
$ python3 scripts/validate_quotes.py                    -> RESULT: PASS (no hard-integrity failures; ...)
$ python3 scripts/check_program_contracts.py            -> RESULT: PASS (transition chains simulate, ...)
$ python3 scripts/validate_homepage_preview_export.py   -> RESULT: PASS

$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv

$ git status --short
 M docs/RUNBOOK.md
?? docs/program/W1_1_STORAGE_AND_SCHEMA.md
?? scripts/check_garden_store.py
?? scripts/garden_store.py

$ /opt/homebrew/bin/python3.12 scripts/check_garden_store.py  -> RESULT: PASS   # CI runs 3.12
$ /opt/homebrew/bin/python3.12 scripts/validate_quotes.py     -> RESULT: PASS
$ /opt/homebrew/bin/python3.12 scripts/check_program_contracts.py -> RESULT: PASS
$ /opt/homebrew/bin/python3.12 scripts/validate_homepage_preview_export.py -> RESULT: PASS
```

Both CSV hashes are identical to `main`: no data, CSV, browser or export file was touched, and
the acceptance script hashes both CSVs itself before and after the run.

## Negative controls (a test that cannot fail proves nothing)

Each mutation was applied to a **throwaway copy of the worktree under `/tmp`** (never the repo,
never the primary checkout), and the acceptance script was re-run there. The authoring session
recorded seven mutations (seven red runs, each with a targeted `FAIL:` line and **no traceback**,
`stderr` empty in all seven); the reviewing session added control **f**, which initially did *not*
go red — see below — and does now.

| # | Mutation (in the `/tmp` copy) | Observed FAIL line(s) |
|---|---|---|
| a1 | export is no longer a pure function: `datetime.now(...).isoformat()` folded into the `[meta]` record | `FAIL: exporting twice produces byte-identical text` · `FAIL: unexpected StoreError: re-export after import is not byte-identical to the imported text (the export encoding lost or reordered data)` — 5 checks red |
| a2 | every `ORDER BY` dropped from the export queries (unordered row iteration) | `FAIL: captures export in sorted order even though cap-0002 was written first -- ['cap-0002', 'cap-0001']` · `FAIL: candidates export in sorted order (not insertion order) -- ['cand-0002', 'cand-0001', 'cand-0003']` |
| b | migration made non-idempotent: the `schema_migrations` ledger skip removed | `FAIL: re-running create raised IntegrityError: UNIQUE constraint failed: schema_migrations.migration_id (the migration is not idempotent)` |
| c | capture immutability dropped: both capture triggers neutralised (`RAISE(ABORT,…)` → `SELECT 1`) | `FAIL: captures accepted UPDATE: captures are not immutable` · `FAIL: no capture row changed after the rejected writes` |
| d1 | vocabulary guard dropped at the SQL layer: the `curation_state` `CHECK` removed | `FAIL: the SQL layer accepted curation_state = 'maybe' (outside STATE_MODEL.md)` |
| d2 | vocabulary guard dropped in the API: the `from_state`/`to_state` guard removed | `FAIL: record_decision accepted to_state = 'maybe' (outside STATE_MODEL.md)` · `FAIL: no invalid decision was appended -- 4` |
| e | append-only dropped: both decision triggers neutralised | `FAIL: decisions accepted UPDATE: the log is not append-only` · `FAIL: decisions accepted DELETE: the log is not append-only` · `FAIL: no decision row changed after the rejected writes` |
| **f** | **parent QA, added on review:** the `research_state` `CHECK` removed (a *different* column than d1) | **Initially `RESULT: PASS` — a coverage gap, not a control.** Fixed (see below); now: `FAIL: the SQL layer accepted research_state = 'maybe' (outside STATE_MODEL.md)` · `RESULT: FAIL`, exit 1, no traceback |

Control **a2 exists because of a real vacuity trap**: a round-trip alone cannot detect a lost
`ORDER BY`, since `import` re-inserts records in file order. The acceptance test therefore
writes `cap-0002`/`cand-0002` *before* `cap-0001`/`cand-0001` and asserts the export order
directly, which is what turns a2 red. (An earlier version of the suite wrote records in export
order and would have passed a2 vacuously.)

### Review finding f: only one of the four state columns was guarded (fixed in review)

The authoring session's seven controls did not cover this, and the reviewing session's
independent QA found it by mutation: **removing the `research_state` `CHECK` constraint left the
whole acceptance run green**, because section 9 asserted SQL-layer rejection for a single
sampled column (`curation_state`) while the schema has four independent `CHECK` constraints — one
per state column. The suite's own docstring also overclaimed ("the four state dimensions …
rejected by both the API and the SQL layer") when only one column was exercised.

Fixed in review rather than deferred: section 9 now loops over all four columns via
`STATE_COLUMNS`, so dropping **any** column's `CHECK` turns the run red
(`the SQL layer rejects curation_state / research_state / corpus_state / work_state = 'maybe'`),
and the docstring states exactly what is asserted and why one API assertion is sufficient
(`record_decision` validates `from_state`/`to_state` against `DIMENSIONS[dimension]` on a single
shared code path, whereas the four `CHECK`s are four separate schema objects). The suite went
from **56 to 59 checks**; both parent controls (the decision-trigger neutralisation and the
`research_state` `CHECK` removal) then reproduced red. The unit's author was a different session
from the reviewer, and the reviewer's mutation was not part of the original evidence — the
provenance of this fix is stated here rather than folded silently into the author's table.

## Out of scope, recorded not fixed

- **The committed mirror has no content to commit yet.** D2 asks for "a full text export
  committed to git as the diffable mirror"; W1.1's acceptance is create-from-empty, so the
  mirror would be empty (or one synthetic row) and W1.3 would supersede it immediately. The
  mechanism, format and round-trip are shipped; the first commit of a populated mirror belongs
  to W1.3. Recorded in `W1_1_STORAGE_AND_SCHEMA.md` §8.3.
- **No `.gitignore` for `garden.sqlite3`.** The store is created wherever `--dir` points, and no
  path in this unit writes into the repo, so nothing needed ignoring yet. W1.3, which picks the
  canonical store location, should add the ignore rule with the location.
- **`work_state` has two subjects.** `STATE_MODEL.md` §4 gives work state to work units and
  research cases; requirement 5 says "work state per candidate". Implemented per the
  requirement (a column on `candidates`) and the decision log accepts `work_unit` /
  `research_case` subjects, so one column carries two meanings until a work-unit table exists.
  Recorded, not resolved — it is a model question, not a W1.1 one.
- **Capture deletion is now impossible, not just discouraged.**
  `PROVENANCE_AND_CAPTURE_CONTRACT.md` forbids updating a capture and forbids deleting it
  *because its candidate was rejected*. W1.1 blocks both UPDATE and DELETE; a future retention
  policy will need a sanctioned path. Recorded in `W1_1_STORAGE_AND_SCHEMA.md` §8.2.
- **Transition legality is not enforced.** `decisions` guarantees the log's shape and its
  append-only nature; it does not check that a move is a legal `T-*` transition, or that its
  authority is the one `STATE_MODEL.md` declares. That guard is W1.5's.
- **`rejected_with_reasons()` depends on a pairing W1.1 cannot guarantee**: a candidate with
  `curation_state = 'rejected'` but no `decisions.to_state = 'rejected'` row would vanish from
  that view. W1.5 must make the pairing an invariant.
- **The existing D2 entry does not name a requirement for each rejected option** — it says the
  file-based options make "immutability and the append-only audit log … conventions rather than
  enforced structure" (requirements 1 and 4, by implication) and rejects the hybrid as "two
  write paths for no W1 gain", naming no requirement. W1.1's acceptance criterion asks exactly
  for that naming, so the append-ready entry below supplies it. The parent decides whether to
  land it as a new entry or fold it into D2 — see the note under the entry.

## Next authorized action

**W1.2 — candidate envelope intake contract + validator** (`docs/program/W1_DECOMPOSITION.md`
§W1.2), whose dependency on W1.1 is "store + schema". It builds on this unit without reopening
it: `candidates.intake_schema_version` is already recorded, the four state columns already
refuse anything outside `STATE_MODEL.md`, and `add_candidate` already enforces the intake
values (rule 3) and a non-empty `normalization_notes` — W1.2 owns the remaining five validation
rules, the sentinel handling and the fixtures, and adds the fields the envelope carries beyond
the minimum (`source_link_state`, `placeholder_markers`, …) as its own migration (a new id in
`MIGRATIONS`, never an edit of `0001`). No other W1 unit may start before W1.2 under the
authorized order.

**Stop condition met: schema exists and round-trips; no intake surface, no review surface.**

## DECISIONS.md entry (for the parent to land)

Append-ready text, repo style. `docs/DECISIONS.md` is **not** edited by this unit (another
agent owns that file in this pass); the parent lands this verbatim, or folds it into the
existing D2 entry (see the last bullet of "Out of scope" above).

```markdown
## 2026-09-12 — D2 executed (W1.1): SQLite + text export, and the requirement each rejected option failed

W1.1 implemented D2 and recorded the comparison it requires. Chosen: **SQLite** (stdlib
`sqlite3`, no dependency) as the store of record with a committed deterministic text mirror
(`garden.export/1`). It satisfies all eight storage/access requirements of
`docs/program/W1_DECOMPOSITION.md` §"Storage and access requirements W1 actually has" with one
file and one code path, and the export keeps the store diffable in git. Naming the requirement
each rejected option failed:

- **Plain JSONL/CSV files + git as the store of record** fails **requirement 1** (immutable
  captures) and **requirement 4** (append-only decision log): with the files as the store, both
  guarantees become conventions — git records that a capture or an audit row was rewritten but
  nothing refuses the write.
- **JSONL files as the store + a rebuildable SQLite index** fails the same two requirements for
  the same reason (the enforced store is still the files) and adds a second write path plus a
  rebuild-determinism burden for no W1 gain. It remains the **upgrade path** if the operator
  later wants the decision log diffable in git from day one.
- **A server database (PostgreSQL/MySQL/document store)** fails **requirement 7**: the operator
  must be able to work with no daemon and no network, and a server is a deployment, not a store.
- **Widening `quotes.csv` with capture/state/decision columns** fails **requirement 1** (no
  capture row is representable), **requirement 4** (a CSV rewrite is not append-only) and
  requirement 8's "untouched" clause, and it would mutate the frozen, documented-lossy view —
  the same reason D5 refuses the rename.
- **SQLite with no text mirror** fails **requirement 7** (human-readable, diffable) and
  **requirement 8** (export to text): the export is part of the decision, not an add-on.

Implemented as `scripts/garden_store.py` (DDL + idempotent create-from-empty migration +
export/import CLI) with `scripts/check_garden_store.py` as the deterministic acceptance run
(59 checks: create → write → read back → export → wipe → re-import byte-identical, migration
idempotency, capture immutability and decision-log append-only enforced by triggers, the four
`STATE_MODEL.md` vocabularies re-parsed from the document, and requirement 6's two queries at
~2,000 rows). Seven negative controls are recorded in `GARDEN_W1_1_HANDOFF.md`. Details:
`docs/program/W1_1_STORAGE_AND_SCHEMA.md`. This executes the D2 decision; it does not
supersede or amend it.
```
