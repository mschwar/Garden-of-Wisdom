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

## GitHub Pages (live site)

Live at **https://mschwar.github.io/Garden-of-Wisdom/** → forwards to
**https://mschwar.github.io/Garden-of-Wisdom/browser/index.html**.

Deployment is `.github/workflows/pages.yml` (Actions-based Pages: `configure-pages` →
`upload-pages-artifact` → `deploy-pages`), triggered on every push to `main` and by manual
`workflow_dispatch`. One-time setup was `gh api -X POST repos/mschwar/Garden-of-Wisdom/pages
-f build_type=workflow` — i.e. Pages "Source" is **GitHub Actions**, not "Deploy from a
branch".

**Hard contract — Pages must stay rooted at the repo root.** `browser/index.html` fetches
`../quotes.csv` and `../sources.csv`, both of which live at the repo root, so the published
site has to be the whole repo (`path: '.'` in the workflow). If anyone repoints the artifact
at `browser/` (or flips Pages back to "Deploy from a branch" with `/docs` or `/browser` as
the folder), the page still loads but renders 0 quotes because both fetches 404. The root
`index.html` is only a redirect shim; it is not the app.

Verify a deploy (must all be 200):

```
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/browser/index.html
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/quotes.csv
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/sources.csv
```


## Re-derive the canonical CSVs from the frozen originals

Only needed if you suspect the canonical `quotes.csv`/`sources.csv` at the repo root have
drifted from what the archived originals + documented transform would produce. This is
idempotent and always reads from `data/archive/2026-09-11/*.original.csv`, never from its own
output:

```
python3 scripts/rehabilitate_2026_09_11.py
```

Re-run `scripts/validate_quotes.py` afterward.

## Homepage-preview export (G4)

Regenerate and validate the versioned collection consumed by `bahai-homepage`
(do not live-read `quotes.csv` from that repo):

```
python3 scripts/export_homepage_preview.py
python3 scripts/validate_homepage_preview_export.py
```

Artifacts live under `exports/bahai-homepage-preview/v1/`. The exporter hard-fails
if an accepted donor’s `quote_text` has drifted from the verified snapshot in
`mapping.json`. See `GARDEN_HOMEPAGE_PREVIEW_EXPORT_HANDOFF.md`.

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
