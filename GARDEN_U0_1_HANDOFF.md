# Handoff — U0.1 Store Lifecycle + Mirror Freshness Invariant

**Branch:** `u0.1/store-lifecycle` · **Gate:** U0 — resumable workbench · **Unit:** U0.1

## What this is

Implements the deterministic SQLite ↔ committed mirror (`garden.export.txt`) lifecycle primitives and enforces the mutation invariant across all operator-facing mutating surfaces. Persistence no longer depends on manual operator export/import rituals, fresh-clone hydration is automated, and divergence between local SQLite and committed mirror is safely prevented.

## What changed

| File | Change |
|---|---|
| `scripts/garden_store.py` | `bootstrap_store()`, `store_status()`, `Store.mirror_path()`, `Store.status()`, `Store.sync_mirror()`, CLI subcommands `bootstrap`, `status`, `sync` |
| `scripts/garden_submit.py` | `store.sync_mirror()` on successful candidate submission |
| `scripts/garden_normalize.py` | `store.sync_mirror()` on successful proposal normalization and hint rebuild |
| `scripts/garden_review.py` | `store.sync_mirror()` on successful curation decisions (`accept`, `hold`, `reject`, `duplicate`, `reopen`) |
| `scripts/garden_ledger.py` | `store.sync_mirror()` on successful `mark` and `reopen` of unverifiable legacy rows |
| `scripts/garden_legacy_batch.py` | `store.sync_mirror()` on successful legacy batch `seed` |
| `scripts/check_garden_lifecycle.py` | Deterministic acceptance suite (**42 checks**, count-guarded) testing all lifecycle paths and invariants |
| `scripts/run_negative_controls.py` | Registered 3 negative controls (`u1`, `u2`, `u3`), table bumped 44 → 47 over 14 checkers |
| `.github/workflows/browser-smoke.yml` | Appended `scripts/check_garden_lifecycle.py` to acceptance suites step |
| `docs/RUNBOOK.md` | Documented store lifecycle commands, invariants, and recovery path |
| `docs/queue.md` | Marked U0.1 DONE, U0.2 READY |
| `docs/program/usability-closure/CURRENT.md` | Updated READY unit to U0.2, last completed to U0.1, updated frontier |
| `docs/DECISIONS.md` | Appended U0.1 execution decision entry |
| `GARDEN_U0_1_HANDOFF.md` | This file |

## Lifecycle States and Semantics

| State | Condition | Meaning |
|---|---|---|
| `CURRENT` | `garden.sqlite3` and `garden.export.txt` both exist, and `store.export_bytes() == mirror.read_bytes()` | Store and committed mirror are in exact sync. |
| `STALE` | `garden.sqlite3` and `garden.export.txt` both exist, but their export bytes differ | Store was mutated without mirror refresh (e.g. uncommitted/raw DB change). |
| `MISSING_DB` | `garden.sqlite3` is absent | Fresh clone or deleted DB; ready for `bootstrap`. |
| `MISSING_MIRROR` | `garden.export.txt` is absent | Mirror was deleted or withheld; requires `sync`. |

## Invariants and Safety

1. **Bootstrap Invariant:**
   - DB absent, mirror present → creates DB and imports mirror; returns `CURRENT`.
   - DB absent, mirror absent → strictly refuses (`StoreError`).
   - DB present, mirror matching → no-op; returns `CURRENT`.
   - DB present, mirror diverging → strictly refuses (`StoreError`). Bootstrap never silently overwrites or clobbers a divergent store or mirror.
2. **Mutation Invariant:**
   - Every operator-facing mutation (`submit`, `normalize`, `hints`, `accept`, `hold`, `reject`, `duplicate`, `reopen`, `mark`, `seed`) automatically invokes `store.sync_mirror()`.
   - A command cannot succeed (exit 0) while leaving a stale committed mirror.
3. **Failure / Crash Recovery:**
   - If an un-synced mutation occurs or an exception interrupts execution after DB commit, `store_status` immediately detects and reports `STALE`.
   - The operator can recover by either:
     - Running `garden_store.py sync --dir DIR` to refresh the committed mirror from the local store; or
     - Deleting `garden.sqlite3` and running `garden_store.py bootstrap --dir DIR` to revert local state from the committed mirror.

## Acceptance Suite (`scripts/check_garden_lifecycle.py`)

Deterministic stdlib runner executing 42 checks across all lifecycle criteria:
- **1a–1d:** Mirror exists, SQLite absent → bootstrap recreates store, exports byte-identical to mirror.
- **2a–2b:** Both absent → explicit refusal with clear error message, writes nothing.
- **3a–3b:** SQLite and mirror equal → `store_status` and CLI `status` report `CURRENT`.
- **4a–4g:** All mutation surfaces (`submit`, `normalize`, `hints`, `accept`, `mark`, `reopen`, `seed`) leave status `CURRENT`.
- **5a–5d:** Stale store and missing mirror detection (`STALE`, `MISSING_MIRROR`).
- **6a–6c:** Divergent DB + mirror → bootstrap refuses, leaves both store and mirror untouched.
- **7a–7c:** Delete local SQLite → re-bootstrap → export byte-identical.
- **8a–8d:** D3 unverifiable ledger row and D4 legacy batch capture + 324 membership rows survive round-trip.
- **9a–9d:** `sync_mirror` refreshes stale mirror to `CURRENT`, byte-identical.
- **Byte-identity:** `quotes.csv` and `sources.csv` verified unchanged before and after.
- **Stray file check:** Asserts nothing written outside the store directory.
- **Count guard:** Asserts exactly `EXPECTED_CHECKS = 42`.

## Negative Controls (`scripts/run_negative_controls.py`)

Registered under `scripts/check_garden_lifecycle.py` in the negative control harness:
- `u1`: Mutation invariant dropped from `submit` (mirror stays stale) → `FAIL: 4a. after a successful submit the mirror is current (mutation invariant) -- STALE`
- `u2`: Divergence check in `bootstrap_store` disabled (`if True: return "CURRENT"`) → `FAIL: 6a. bootstrap did not refuse a divergent store + mirror`
- `u3`: `store_status` fails to detect stale mirror (`return "CURRENT"`) → `FAIL: 5a. a store mutated behind the mirror reports STALE`

All 3 controls fired with exact target lines; table verified at 47 controls across 14 checkers.

## CSV Byte-Identity

```
quotes.csv:  9766db8c30372efc57752c0b12b373536e4ddb666f52591610ec238e1c3e01a3 (byte-identical)
sources.csv: 7aafcb67119564201baf700f29143668ed469f59d83aae60f8f99648a11a27da (byte-identical)
```

## Evidence & Verification

- `check_garden_lifecycle.py`: `RESULT: PASS (42 checks)`
- `run_negative_controls.py --checker scripts/check_garden_lifecycle.py`: `RESULT: PASS (3 controls fired, 9 harness self-tests)`
- `run_negative_controls.py --check`: `RESULT: PASS (47 anchors checked)`
- All 13 existing acceptance test suites: `RESULT: PASS`
- `check_pages_contract.py`: `RESULT: PASS (16 checks)`
- `validate_quotes.py`: `RESULT: PASS`
- `check_live_pages.py --self-test`: `RESULT: PASS (10 checks)`

## Next Authorized Action

Unit **U0.2 — truthful front door + current-state routing** (`docs/program/usability-closure/workunits/U0.2_FRONT_DOOR.md`).
