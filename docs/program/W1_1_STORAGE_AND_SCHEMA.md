# W1.1 — Storage decision and minimal schema

**Status: implemented 2026-09-12** on branch `w1/storage-schema` (W1.1 of
`W1_DECOMPOSITION.md`). This document is the written half of the unit: the decision, the
comparison against the eight requirements, the schema, the vocabularies, the idempotency rule,
and the export format. The executable half is `scripts/garden_store.py` (store + DDL +
migration/export/import CLI) and `scripts/check_garden_store.py` (acceptance + evidence).

The decision itself is authoritative in `docs/DECISIONS.md` (entry "2026-09-12 — D2 (storage):
W1.1's store of record is SQLite with a committed full-text export", landed by the parent from
`GARDEN_W1_1_HANDOFF.md`). This file does not restate the decision as fresh authority; it
records how it is implemented and why the rejected options lost.

## 1. The storage and access requirements, and what each option does about them

The eight requirements are `W1_DECOMPOSITION.md` §"Storage and access requirements W1 actually
has", verbatim. "Enforced" below means a write that breaks the requirement is **rejected by
the store**, not merely detectable afterwards.

| # | Requirement | Chosen: SQLite + committed text export | A: plain JSONL/CSV files + git | B: JSONL files + rebuildable SQLite index | C: server database | D: widen `quotes.csv` |
|---|---|---|---|---|---|---|
| 1 | Immutable capture records, keyed, never updated after write | **Enforced** — `captures` is PK-keyed and two `BEFORE UPDATE`/`BEFORE DELETE` triggers `RAISE(ABORT)` | Convention only: a file can be rewritten in place; git shows the diff after the fact | Same as A — the enforced store is still files | Enforced (same schema) | Not representable: the encounter has no row of its own |
| 2 | Candidate records referencing one or more captures, with normalized fields + `normalization_notes` | **Yes** — `candidates` + `candidate_captures(candidate_id, capture_id, ordinal)`, FK-enforced | Possible, by hand-rolled referential integrity | Same as A | Yes | Yes, but a candidate is only ever one CSV row |
| 3 | Duplicate hints as rows (kind/target/basis), rebuildable deterministically | **Yes** — `duplicate_hints`, PK `(candidate_id, hint_seq)`, rebuild = delete + regenerate | Yes, as nested JSON | Yes | Yes | No place to put them |
| 4 | Append-only decision/audit log: who/what, when, from-state, to-state, reason | **Enforced** — `decisions` triggers reject `UPDATE` and `DELETE`; `seq` is the only ordering | Convention only; an edit is a normal file write | Same as A; the index is derived, so the file is what is enforced | Enforced | No: a CSV row edit is indistinguishable from an edit of the quote |
| 5 | The four state dimensions with their exact vocabularies | **Yes** — four columns on `candidates`, each with a `CHECK` over `STATE_MODEL.md`'s vocabulary | Yes, as a convention in a text field | Same as A | Yes | Only by widening a frozen, lossy view (refused by D5) |
| 6 | Query path for the unreviewed queue (newest first) and rejected-with-reason, fast at low thousands | **Yes** — `idx_candidates_queue` on `(curation_state, created_at DESC, candidate_id)`; both queries indexed; measured on 2,000 rows | Full parse per query; acceptable at low thousands, a scan by construction | Index exists, but it is rebuilt from files | Yes | Possible with a full CSV parse |
| 7 | No network dependency, no server process, human-readable and diffable representation of everything that matters | **Yes** — stdlib `sqlite3`, one local file; the mirror is `garden.export/1` text committed to git | Yes (files *are* the text) | Yes | **No** — needs a running server | Yes |
| 8 | Export of the whole store to text, with the browser still reading `quotes.csv` untouched | **Yes** — `export` writes the whole store as deterministic text; nothing in this unit opens `quotes.csv` | Yes | Yes | Yes, with a dump step | **No** — writing the store into the CSV is exactly the write W1 forbids |

### Rejected options, and the requirement each one failed

| Rejected option | Requirement it fails | Why |
|---|---|---|
| **A. Plain JSONL/CSV files + git as the store of record** | **#1** (immutable captures) and **#4** (append-only log) | Both become *conventions*: git records that a capture or an audit row was rewritten, but nothing refuses the write. The two requirements the program cares most about — "the raw encounter is never rewritten" and "every transition is auditable" — would rest on everyone remembering. |
| **B. JSONL files as the store + a rebuildable SQLite index** | **#1** and **#4** (as A), plus cost | Two write paths where W1 needs one, and the index is derived, so the enforced guarantees still live on the editable files. The rebuild-determinism burden buys nothing W1 uses. Recorded in D2 as the **upgrade path** if the operator later wants the decision log diffable in git from day one. |
| **C. A server database (PostgreSQL/MySQL/document store)** | **#7** (no network, no server process) | The operator must be able to work with no daemon and no network. This is a personal, local-first corpus; a server is a deployment, not a store. |
| **D. Widen `quotes.csv` (new columns for captures/states/decisions)** | **#1** (no immutable capture rows) and **#4** (a CSV rewrite is not append-only); also #8's "untouched" clause | The legacy CSV has no capture records to preserve (W0 decision), is a documented **lossy** projection, and is read-only for the whole of W1. Widening it would mutate the frozen view and still not represent a capture. D5 refuses the rename/widening for the same reason. |
| **E. SQLite alone, no text mirror** | **#7** (human-readable, diffable) and **#8** (export to text) | A binary store nobody can review or diff in a PR is not "inspectable". The export is part of the decision, not an add-on, which is why it is specified as a format with its own header and round-trip test. |

## 2. Schema (DDL) summary

One file, `garden.sqlite3`, created from empty by one command. `sqlite3` from the standard
library; `PRAGMA foreign_keys = ON` on every connection.

| Object | Role | Key constraints / guards |
|---|---|---|
| `schema_migrations` | migration ledger | PK `migration_id`; a migration id is applied at most once |
| `meta` | `schema_version`, `created_at` | PK `key`; written with `INSERT OR IGNORE` so a re-run cannot restamp it |
| `captures` | the raw encounter, verbatim | PK `capture_id`; `captured_text` non-empty; `capture_method` ∈ the nine-method contract list; **triggers `captures_immutable_update` / `captures_immutable_delete` reject UPDATE and DELETE** |
| `candidates` | the normalized proposal | PK `candidate_id`; `candidate_text` and `normalization_notes` non-empty; four state columns each `CHECK`ed against its vocabulary; `intake_schema_version` recorded |
| `candidate_captures` | many-to-many candidate ↔ capture | PK `(candidate_id, ordinal)`, `UNIQUE (candidate_id, capture_id)`, FKs to both sides |
| `duplicate_hints` | hints as rows | PK `(candidate_id, hint_seq)`; `kind` ∈ 4-value vocabulary; `basis` non-empty; FK to `candidates` |
| `decisions` | the append-only audit log | PK `seq` (AUTOINCREMENT); `actor`/`actor_kind`, `occurred_at`, `subject_kind`/`subject_id`, `dimension`, `action`, `transition_id`, `from_state`, `to_state`, `reason` (non-empty); **triggers `decisions_append_only_update` / `decisions_append_only_delete` reject UPDATE and DELETE** |
| `idx_candidates_queue` | requirement 6 | `(curation_state, created_at DESC, candidate_id)` |
| `idx_candidates_research`, `idx_candidates_corpus`, `idx_candidate_captures_capture`, `idx_decisions_subject`, `idx_decisions_dimension` | supporting lookups | — |

Deliberate design points:

- **`from_state`/`to_state` are not SQL-`CHECK`ed**, because the legal set depends on
  `dimension` (a cross-column rule SQL cannot express declaratively). The API validates both
  against `DIMENSIONS[dimension]` and refuses anything else; the acceptance script asserts
  both the API refusal and the column `CHECK` on `candidates`.
- **Whether a move is a legal transition** (`T-C*`, `T-P*`, `T-R*`, `T-W*` and their
  authorities) is **not** enforced here. That guard belongs to W1.5, which owns the review
  surface. W1.1 guarantees the log's *shape* and *immutability*, not its transition legality.
- **Candidates are deliberately mutable.** Only captures and decisions are immutable; the four
  state columns have to move. Every move is meant to be paired with a recorded decision —
  W1.5's job — and `record_decision` is the only writer W1.1 exposes.
- **Hints are derived data.** There is no guard on `duplicate_hints` because the sanctioned
  write is `replace_duplicate_hints` (delete + regenerate), never a hand edit. The hint
  *algorithm* is W1.4.
- **Requirement 8's `quotes.csv` clause** is honored by touching neither CSV: no code path in
  this unit opens either file, and the acceptance run hashes both before and after.

## 3. The four vocabularies, as implemented

Copied from `STATE_MODEL.md` §§1–4 into `scripts/garden_store.py` as the single source for
both the SQL `CHECK` constraints and the API. `scripts/check_garden_store.py` **parses the
document** and fails if the two ever disagree, so the schema cannot drift from the model.

| Dimension | Column | Values (count) |
|---|---|---|
| curation | `candidates.curation_state` | `new`, `accepted`, `hold`, `rejected`, `duplicate` (5) |
| research | `candidates.research_state` | `not_started`, `in_research`, `verified`, `disputed`, `unverifiable`, `needs_more_evidence` (6) |
| corpus | `candidates.corpus_state` | `candidate_only`, `eligible`, `canonical`, `retired` (4) |
| work | `candidates.work_state` | `queued`, `active`, `qa`, `blocked`, `done` (5) |

Intake rule (`CANDIDATE_ENVELOPE.md` validation rule 3): a candidate enters the store at
`new` / `not_started` / `candidate_only` / `queued` and nowhere else. `add_candidate` has no
parameter for the states, so an envelope arriving with a decision already made cannot be
stored. Nothing in this unit writes `research_state` at all; no promotion path exists.

## 4. Migration and the idempotency rule

```
python3 scripts/garden_store.py create --dir DIR
```

- **Rule:** a migration id is applied **at most once**. `schema_migrations` is the ledger;
  `apply_migrations` skips an id already present. Re-running `create` on an existing store
  applies nothing, writes nothing, and prints
  `no-op: migration 0001_create_core already applied; store unchanged`.
- `meta.created_at` is written with `INSERT OR IGNORE`, so a re-run cannot restamp it.
- The acceptance script asserts the re-run's *export bytes* are unchanged, not merely that the
  message printed. Verified: `create` twice in the same directory leaves the export identical.
- Schema change from here is a **new migration id appended to `MIGRATIONS`**; an applied
  migration's statements are never edited in place.

## 5. Export format (`garden.export/1`) and the round-trip

The mirror is one text file, `garden.export.txt` in the store directory (`export --dir D`
writes it; `dump --dir D` writes the same bytes to stdout). It is a **pure function of the
store**: fixed section order, records sorted by key, one canonical single-line JSON object per
line (UTF-8, `sort_keys=True`, no export timestamp), LF line endings, trailing newline.

```
garden.export/1
[meta]
{"created_at":"2026-09-12T13:58:30-06:00","schema_version":1}
[captures]
{"capture_id":"cap-2026-09-12-0001","capture_method":"screenshot","captured_attribution":"Bahá’u’lláh", ...}
[candidate_captures]
{"candidate_id":"cand-2026-09-12-0001","capture_id":"cap-2026-09-12-0001","ordinal":1}
[candidates]
{"candidate_author":"Bahá’u’lláh","candidate_id":"cand-2026-09-12-0001","corpus_state":"candidate_only", ...}
[duplicate_hints]
[decisions]
{"action":"curation-decision","actor":"operator","actor_kind":"operator","dimension":"curation","from_state":"new","occurred_at":"2026-09-12T09:40:00-06:00","reason":"...","seq":1,"subject_id":"cand-2026-09-12-0001","subject_kind":"candidate","to_state":"hold","transition_id":"T-C2"}
```

Every section header is emitted even when empty, so the file's shape does not change with the
data. One record per line means a `git diff` of the mirror is a per-record diff.

**Round-trip:** `write → export → wipe → re-import → byte-identical`. `import` re-exports what
it just wrote and compares against the input **before** returning, so a lossy or
order-dependent encoding fails the import instead of silently passing. `verify --dir D` runs
the same comparison as a one-command check.

Idempotency of the export mirror: `import`ing the text a store already holds is a no-op
(`no-op: store already holds exactly this text`); importing different text into a non-empty
store is refused rather than merged.

**One consequence of "sorted by key", stated because it is a real test-design trap:** the
round-trip alone cannot catch a lost `ORDER BY`, because an import re-inserts records in
file order. The acceptance test therefore writes its records *deliberately out of export
order* and asserts the export order directly (see negative control a2 in the handoff).

## 6. What this unit does not do

Per the card's stop condition — **schema exists and round-trips; no intake surface, no review
surface**:

- no migration of `quotes.csv`/`sources.csv` (read-only for all of W1; no code path opens them);
- no canonical promotion path (`T-P2`…`T-P6` are W3);
- no intake/submission CLI (W1.3), no envelope validator (W1.2), no normalization or
  duplicate-hint algorithm (W1.4), no queue/review command and no transition guard machinery
  (W1.5);
- no performance tuning (the 2,000-row check is a functional check of requirement 6, not a
  benchmark), no embeddings, no network, no concurrency, no auth.

## 7. Commands

| Command | Effect |
|---|---|
| `python3 scripts/garden_store.py create --dir DIR` | create the store from empty; idempotent no-op afterwards |
| `python3 scripts/garden_store.py export --dir DIR [--out PATH]` | write `garden.export.txt` (the committed mirror) |
| `python3 scripts/garden_store.py dump --dir DIR` | the same bytes on stdout |
| `python3 scripts/garden_store.py import --dir DIR --from FILE` | load an export; no-op if it is already the store's content |
| `python3 scripts/garden_store.py verify --dir DIR` | export → re-import into a throwaway copy → compare bytes |
| `python3 scripts/check_garden_store.py` | the full W1.1 acceptance + evidence run |

## 8. Doctrine ambiguities found while implementing (reported, not papered over)

1. **`work_state` has two subjects.** `STATE_MODEL.md` §4 says work state "belongs to work units
   and research cases"; `W1_DECOMPOSITION.md` requirement 5 says "work state per candidate", and
   `CANDIDATE_ENVELOPE.md` makes `work_state` a required envelope field. W1.1 implements the
   requirement literally — a `work_state` column on `candidates`, and the decision log accepts
   `subject_kind` `work_unit`/`research_case` — so one column currently carries two meanings.
   A separate work-unit table is deferred to the unit that first needs one.
2. **"Never deleted" is narrower in the contract than in the store.**
   `PROVENANCE_AND_CAPTURE_CONTRACT.md` invariant 1 forbids *updating* a capture and invariant 2
   forbids deleting it *because its candidate was rejected*. W1.1 implements the stronger
   reading (no UPDATE, no DELETE at all), which leaves no sanctioned way to remove a capture if
   a retention policy ever wants one. Noted as a future decision, not a gap to fix now.
3. **D2 asks for a committed mirror; W1.1's acceptance is create-from-empty.** There is no
   content at this unit's stop point, so committing an empty (or one-writer-created) mirror
   would add a file that W1.3 immediately supersedes. The unit ships the mechanism and the
   format; the first commit of a populated mirror belongs to the first unit that writes real
   submissions (W1.3). Flagged rather than silently skipped.
4. **Requirement 8's two clauses pull in different directions if read strictly** ("export of the
   whole store to text" vs. "the browser can keep reading `quotes.csv` untouched"). Resolved
   as: the store exports to its *own* text format, and nothing writes the CSV — the browser's
   input stays byte-identical. A store→CSV projection would contradict the W1 cross-unit rule.
5. **Requirement 6's rejected-with-reason query assumes the log always records the rejection.**
   `rejected_with_reasons()` joins `candidates.curation_state = 'rejected'` to a
   `decisions.to_state = 'rejected'` row. W1.1 cannot guarantee that pairing (it does not
   implement transitions); W1.5 must, and a candidate with `curation_state = 'rejected'` and no
   decision row would silently disappear from that view. Recorded as a contract W1.1's schema
   relies on.
6. **D5's naming split is honored but its assertion is not this unit's.** The store's dimension
   is spelled `research_state` everywhere; there is no `verification_status` column, so the CSV
   projection cannot leak into the store. D5 places the machine-checked mapping in
   `scripts/check_program_contracts.py`, which is a separate unit's work.
