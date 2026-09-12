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

## GitHub Pages (static site)

Published from the repo root by `.github/workflows/pages.yml` on every push to `main` (and by
manual `workflow_dispatch`, main only — the job is guarded with
`if: github.ref == 'refs/heads/main'` so a manual run from a branch cannot overwrite the live
site). Actions-based Pages: `configure-pages` → `upload-pages-artifact` → `deploy-pages`.

URLs once deployed:

- site root (a redirect shim in the repo-root `index.html`) —
  `https://mschwar.github.io/Garden-of-Wisdom/`
- the app — `https://mschwar.github.io/Garden-of-Wisdom/browser/index.html`
- the data the app fetches at runtime — `…/quotes.csv`, `…/sources.csv`

**Precondition that CI assumes but cannot create.** The repo's Pages site must exist with
`build_type: workflow` (Settings → Pages → Source = **GitHub Actions**, not "Deploy from a
branch"). `actions/configure-pages`'s `enablement: true` requires an admin PAT — the default
`GITHUB_TOKEN` cannot do it — so it was enabled once, out of band:

```
gh api repos/mschwar/Garden-of-Wisdom/pages | jq .build_type     # expect "workflow"
gh api -X POST repos/mschwar/Garden-of-Wisdom/pages -f build_type=workflow   # only if 404
```

If that setting is missing or gets flipped, `pages.yml` **fails** rather than mispublishing —
it does not silently publish a wrong thing.

**Hard contract — Pages must stay rooted at the repo root.** `browser/index.html` fetches
`../quotes.csv` and `../sources.csv`, both of which live at the repo root, so the published
site has to be the whole repo (`path: '.'` in the workflow). If anyone repoints the artifact
at `browser/` (or flips Pages back to "Deploy from a branch" with `/docs` or `/browser` as
the folder), the page still loads but renders 0 quotes because both fetches 404. The root
`index.html` is only a redirect shim; it is not the app.

**What actually gets published.** The whole repo root — including `docs/`, `bootstrap/`,
`exports/`, and the frozen `data/archive/` originals — because the app's
`../quotes.csv` / `../sources.csv` fetches require the root layout. All of it is already
public on GitHub, so this adds no exposure. `actions/upload-pages-artifact` always drops
`.git` and `.github` and, by default (`include-hidden-files: false`), all top-level dotfiles,
so a committed `.nojekyll` would never reach the artifact. That is fine here: an
Actions-deployed artifact is served as-is and is never run through Jekyll, so `.nojekyll` is
not needed.

Verify a deploy (all four must be 200):

```
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/browser/index.html
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/quotes.csv
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/sources.csv
```

To watch a deploy instead: `gh run list --workflow pages.yml --limit 3` then
`gh run watch <id>`.


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
