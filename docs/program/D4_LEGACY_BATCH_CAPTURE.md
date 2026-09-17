# D4 — ONE batch capture for the 324 legacy rows

**Decision:** `docs/DECISIONS.md`, "2026-09-12 — D4 (legacy capture provenance): one batch
capture record for the 2026-09-11 import".
**Unit branch:** `d4/legacy-batch-capture` · **Design doc for** `scripts/garden_store.py`
(migration `0003_legacy_batch_capture`), `scripts/garden_legacy_batch.py`,
`scripts/check_garden_legacy_batch.py`.
**Live seed:** every `quotes.csv` id linked to `cap-2026-09-11-legacy-batch`.

## Problem

The 324 legacy rows in `quotes.csv` have no reconstructable raw encounter: what the original
author saw, where, when, and typed-in-as-is was never recorded
(`PROVENANCE_AND_CAPTURE_CONTRACT.md`). W0 rejected synthesizing a capture per row. Decision D4
supersedes the open policy question: give the corpus **ONE batch capture** for the
2026-09-11 rehabilitation import — a true, verifiable statement about the frozen archive +
documented transform — rather than inventing 324 encounters or leaving provenance empty.

## What is recorded

| Piece | Where | Content |
|---|---|---|
| The batch capture | `captures` row `cap-2026-09-11-legacy-batch` | `capture_method`/`captured_by` = `legacy-import`; `captured_at` = `2026-09-11T00:00:00-06:00`; `captured_text` = the fixed true statement naming the archive paths and their sha256 digests; `context_notes` explicitly says encounter context is unknown |
| Membership | `legacy_batch_membership` | one row per legacy `quotes.csv` `id` → that capture_id |
| Candidates | **none** | legacy rows are not store candidates (same posture as D3) |

Rejected alternatives (decision D4): (a) no capture at all — archive stays the only provenance;
(b) one synthetic capture per row — fabricated per-row provenance.

## Schema (migration `0003_legacy_batch_capture`)

```sql
CREATE TABLE IF NOT EXISTS legacy_batch_membership(
    legacy_row_id TEXT PRIMARY KEY,
    capture_id    TEXT NOT NULL REFERENCES captures(capture_id)
);
```

- Keyed by the legacy row id (the `quotes.csv` `id` column). **Not** a `candidates` FK.
- The capture body lives in the existing immutable `captures` table; this table only records
  coverage.
- Export section `[legacy_batch_membership]`, ordered by `legacy_row_id`. Export header stays
  `garden.export/1` / `schema_version` 1 (additive section, same ruling as D3).

## Write path (`Store.seed_legacy_batch_capture`)

Inserts the fixed capture **and** every membership row in ONE transaction. Guards:

- the id list is non-empty, every id non-empty, no duplicates inside the call;
- if the store already holds exactly this capture body and exactly this membership set →
  **no-op** (idempotent);
- if a capture or membership exists that disagrees → refuse (never a silent overwrite or
  in-place repair).

The capture fields are constants in `garden_store.py` (`LEGACY_BATCH_*`), not caller-supplied,
so two seeds cannot drift on wording.

## CLI — `scripts/garden_legacy_batch.py`

`seed --dir DIR [--quotes PATH] [--json]` — reads every `id` from `quotes.csv` (default: repo
root), asserts the count is exactly 324, and calls `seed_legacy_batch_capture`.
`show --dir DIR [--json]` — prints the capture + membership count.
`verify --dir DIR [--quotes PATH]` — asserts the seeded membership set equals the current
`quotes.csv` id set and that the capture body matches the constants (including archive
sha256s against the live archive files when present).

## Acceptance — `scripts/check_garden_legacy_batch.py`

Runs in a throwaway temp dir. Asserts migration `0003`, the capture constants, the 324-row
membership against a real `quotes.csv` read, idempotent re-seed, refusal of a conflicting
seed, export round-trip of the new section, and byte-identity of `quotes.csv` /
`sources.csv`.

## Out of scope (recorded, not done)

- Creating store candidates for the 324 rows.
- Per-row capture records.
- Guessing the `_` placeholder glyphs (still forbidden).
- Widening `quotes.csv`.
- W2 research / promotion work.
