# Runbook

## Validate the data

```
python3 scripts/validate_quotes.py
```

Exits 0 with `RESULT: PASS` if there are no hard-integrity failures (parse errors, malformed
UTF-8, duplicate IDs, missing required fields, invalid controlled values, dangling
`source_id` references). Everything else it prints (near-duplicates, unresolved source links,
unresolved-glyph rows, counts by `item_type`/`verification_status`) is curation-queue signal,
not a failure — read `docs/data/DATA_QUALITY_REPORT.md` for how to interpret it.

## Run the browser locally

```
python3 -m http.server 8000
```

Open `http://localhost:8000/browser/index.html`. See `docs/architecture/QUOTE_BROWSER.md`.

## Re-derive the canonical CSVs from the frozen originals

Only needed if you suspect the canonical `quotes.csv`/`sources.csv` at the repo root have
drifted from what the archived originals + documented transform would produce. This is
idempotent and always reads from `data/archive/2026-09-11/*.original.csv`, never from its own
output:

```
python3 scripts/rehabilitate_2026_09_11.py
```

Re-run `scripts/validate_quotes.py` afterward.

## Adding a new quote

1. Append a row to `quotes.csv` with all 10 columns filled in. Set `verification_status` to
   `unverified` unless you've actually checked it against a primary source.
2. If it cites a source already in `sources.csv`, set `source_id` accordingly; if not, either
   add a `sources.csv` row first or leave `source_id` blank (don't guess).
3. Run `python3 scripts/validate_quotes.py` and confirm `RESULT: PASS`.

## Recovery if an agent session dies mid-task

1. `git status`
2. Read `AGENTS.md`.
3. Read `docs/queue.md` for the active work unit.
4. Read the most recent handoff/checkpoint file at repo root.
5. Resume only the named active work unit — don't restart from memory or improvise scope.
6. Re-run `scripts/validate_quotes.py` before claiming anything is done.
