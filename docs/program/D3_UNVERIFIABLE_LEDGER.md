# D3 — the `unverifiable` side-car ledger

**Decision:** `docs/DECISIONS.md`, "2026-09-12 — D3 (unverifiable): a side-car ledger keyed by
legacy row id, not a widened enum".
**Unit branch:** `d3/unverifiable-ledger` · **Design doc for** `scripts/garden_store.py`
(migration `0002_unverifiable_ledger`), `scripts/garden_ledger.py`, `scripts/check_garden_ledger.py`.
**Live instance:** Garden id 30 (issue #5).

## Problem

`quotes.csv` `verification_status` is a 3-valued enum (`verified` / `unverified` /
`disputed`? — see `docs/program/STATE_MODEL.md` §5). Every unfinished research state projects
to `unverified`, so a record **proven unverifiable** is indistinguishable from a
**never-checked** row. Garden id 30 (`Prayer is the key of the doors of mercy.`) is the live
instance: G4 rejected it from the homepage-preview export because the sentence is not on the
Bahá'í Reference Library and no Dec 2 1911 Paris talk exists, yet in the CSV it is just another
`unverified` row.

Widening the enum is rejected (decision D3): it is a permanent widening of a frozen, lossy
projection. The chosen mechanism is a **side-car ledger keyed by legacy row id** — a table in
the W1.1 SQLite store — that records which legacy rows have been adjudicated `unverifiable`.

## One store, not two

Decision D3 defers implementation until W1.1 exists "so there is one store rather than two".
The ledger is therefore a **table in the existing store** (`legacy_verification`), part of the
same `garden.export/1` diffable mirror. It is never a second file or a second database.

## Schema (migration `0002_unverifiable_ledger`)

```sql
CREATE TABLE IF NOT EXISTS legacy_verification(
    legacy_row_id  TEXT PRIMARY KEY,
    research_state TEXT NOT NULL CHECK(research_state = 'unverifiable'),
    transition_id  TEXT NOT NULL CHECK(transition_id IN ('T-R6','T-R7','T-R10','T-R11')),
    reason         TEXT NOT NULL CHECK(length(reason) > 0),
    evidence_ref   TEXT NOT NULL CHECK(length(evidence_ref) > 0),
    decided_by     TEXT NOT NULL CHECK(length(decided_by) > 0),
    decided_at     TEXT NOT NULL
);
```

- **Keyed by the legacy row id** (the `quotes.csv` `id` column). It is **not** a `candidates`
  foreign key: legacy rows are not store candidates and may never be. The existing `external_id`
  on `candidates` is the future bridge between a store candidate and its legacy row, out of scope
  here.
- `research_state` is pinned to `unverifiable` (terminal, `STATE_MODEL.md` §2).
- `transition_id` is restricted to the four research transitions that **terminate** in
  `unverifiable` (T-R6, T-R7, T-R10, T-R11) — an `unverifiable` adjudication must name its route.
- `reason` and `evidence_ref` are required; `evidence_ref` defaults to `none` only through the
  API (`'none'` is the explicit *no-reference* assertion, not an omission).

## Write paths (`Store` methods, guarded)

**`mark_legacy_unverifiable(id, *, transition_id, reason, evidence_ref, decided_by, decided_at)`**
inserts the ledger row **and** a `research` `decisions` audit row in ONE transaction, so there is
never a ledger row without its audit row (same atomicity rule as W1.5's `curate`). Guards, all
checked before anything is written:

- `id`, `reason`, `evidence_ref`, `decided_by` must be non-empty;
- `transition_id` ∈ {T-R6, T-R7, T-R10, T-R11};
- the id must **not** already be in the ledger — a legacy row is either `unverifiable` or it is
  not; re-adjudicating means `reopen` (T-R12) then `mark` again, never a silent overwrite.

The audit row's `from_state` is **derived from `transition_id`** per `STATE_MODEL.md` §2 (T-R6 →
`in_research`, T-R7 → `needs_more_evidence`, T-R10 → `disputed`, T-R11 → `verified`) so the audit
always agrees with the model. Provenance caveat (D4): the legacy row's *true* prior research
state is unknown; the declared route is the operator's stated path, never an invented encounter.

**`reopen_legacy_unverifiable(id, *, reason, decided_by, decided_at)`** reverses an adjudication
when a new witness appears (`T-R12 unverifiable → in_research`): it appends the `T-R12` audit row
and **deletes** the ledger row in ONE transaction. Guards: the row must be in the ledger, and
`reason` / `decided_by` must be non-empty.

**`unverifiable_ledger()`** returns every ledger row ordered by legacy row id.

## Export / import

`legacy_verification` is an export section (`[legacy_verification]`, `ORDER BY legacy_row_id`),
in `ROW_TABLES`, `counts()`, and the import loop, so it round-trips byte-identically with the
store and diffs in git. **Ruling:** the export header stays `garden.export/1` and meta
`schema_version` stays `1`. The ledger is an *additive* section to the same version-1 format; a
version bump is reserved for a change to the *meaning* of existing bytes. There are no persisted
/1 exports in the wild (the store is git-ignored and was empty), and the store's byte-identity
guard still refuses an old text that lacks the new section, so no format can silently pass.

## CLI — `scripts/garden_ledger.py`

`mark --dir DIR --row ID --transition T-Rx --reason REASON [--evidence-ref REF] [--actor NAME]`,
`reopen --dir DIR --row ID --reason REASON [--actor NAME]`, `list --dir DIR [--json]`. Follows
the store/review CLI contract: `RESULT: PASS`/`FAIL`, no traceback on a refusal, `--json` emits
canonical single-line JSON.

## Acceptance — `scripts/check_garden_ledger.py` (43 checks)

Runs in a throwaway temp dir; asserts schema + CHECK constraints, the atomic
ledger-row-plus-audit-row write, no silent overwrite, the reopen reversal, byte-identical export
round-trip, per-guard refusal messages, and `quotes.csv` / `sources.csv` byte-identity. The seven
negative controls (mutate a guard's distinctive message in a `/tmp` repo copy → `RESULT: FAIL`
with that guard's `FAIL:` line, no traceback) are recorded in `GARDEN_D3_HANDOFF.md`.

**Necessary extension of the W1.1 suite:** `check_garden_store.py`'s exact-shape assertions
(migration list, table set, export line count, `counts()` dict) were updated to the two-migration
schema. That is a legitimate extension by a later unit, recorded in `docs/DECISIONS.md`.

## Live instance

The store mirror `data/store/garden.export.txt` seeds Garden id 30 as `unverifiable` (T-R6,
`evidence_ref` = issue #5). This is the first committed store mirror (consistent with the W1.3
ruling that the first real operator submission populates it): marking id 30 is a real operator
adjudication, and the ledger now makes the previously-indistinguishable row distinguishable.
`quotes.csv` / `sources.csv` are untouched.

## Out of scope (recorded, not done)

- A full research-case surface for `candidates` (`T-R*` transitions on store candidates) — W2 work.
- Any browser display of the ledger — no browser change in this unit.
- Re-opening a legacy row into the candidate flow — the ledger only records the terminal fact.
- Widening `quotes.csv` `verification_status` — explicitly rejected by decision D3.
