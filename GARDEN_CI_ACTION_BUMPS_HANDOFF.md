# Garden CI Action-Bump Handoff — 2026-09-12

Unit: the open infra item filed as
[#19](https://github.com/mschwar/Garden-of-Wisdom/issues/19) — move CI off the deprecated Node 20
action majors. **Deploy-path change: the three Pages actions in `pages.yml` were bumped and the
live deploy was re-verified the way the 2026-09-11 acceptance was. No data changed.**

Landed as PR [#22](https://github.com/mschwar/Garden-of-Wisdom/pull/22), merged into `main` as
`6df549b` (CI + live acceptance in the block below).
Gate state unchanged: Gate A accepted 2026-09-12
(`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`); **W1 is authorized in full** (2026-09-12,
decision D1) and nothing in this unit touches the corpus program.

## Deviation: this handoff is parent-authored

The authoring child **timed out before producing its handoff**. The work itself was complete on
the branch (both workflows edited, committed, PR opened, PR CI green), but the closing artifact
this repo requires was never written. The parent therefore verified the unit directly and
completed it, and is authoring this handoff rather than reconstructing the child's account of it.
Everything below is from the parent's own checks: the run ids were read back from the GitHub API,
not taken from a subagent summary. Self-reports are not evidence.

## What landed

| Artifact | Change |
|---|---|
| `.github/workflows/browser-smoke.yml` | `actions/checkout` v4→v7, `actions/setup-python` v5→v7. |
| `.github/workflows/pages.yml` | `actions/checkout` v4→v7, `actions/configure-pages` v5→v6, `actions/upload-pages-artifact` v3→v5, `actions/deploy-pages` v4→v5. `path: '.'`, the `pages` concurrency group, the `github-pages` environment and the `refs/heads/main` guard are **unchanged**. |
| `GARDEN_CI_ACTION_BUMPS_HANDOFF.md` | This file (parent-authored — see the deviation above). |
| [#23](https://github.com/mschwar/Garden-of-Wisdom/issues/23) | Filed: Pages artifact publishes the repo-root `.gitignore` (see below). Found during this unit's verification; **not** a regression from it. |

No other file was touched. `quotes.csv` / `sources.csv` are byte-identical to `main`.

### The diff (two workflow files, `path: '.'` and the deploy guards preserved verbatim)

```diff
--- a/.github/workflows/browser-smoke.yml
+++ b/.github/workflows/browser-smoke.yml
@@
-        uses: actions/checkout@v4
+        uses: actions/checkout@v7
@@
-        uses: actions/setup-python@v5
+        uses: actions/setup-python@v7

--- a/.github/workflows/pages.yml
+++ b/.github/workflows/pages.yml
@@
-        uses: actions/checkout@v4
+        uses: actions/checkout@v7
@@
-        uses: actions/configure-pages@v5
+        uses: actions/configure-pages@v6
@@
-        uses: actions/upload-pages-artifact@v3
+        uses: actions/upload-pages-artifact@v5
         with:
          path: '.'
@@
-        uses: actions/deploy-pages@v4
+        uses: actions/deploy-pages@v5
```

Unchanged and deliberately so: `path: '.'`, the `pages` concurrency group, the `github-pages`
environment, and the `if: github.ref == 'refs/heads/main'` deploy guard.

## The five bumps, with the release-note finding

All five actions in both workflows were bumped, not just the two GitHub annotated
(`checkout`, `setup-python`). Rationale: the re-verification cost is identical once the deploy path
is exercised live, and the three Pages actions were several majors behind as well.

| Action | Before | After | Release-note finding relevant here |
|---|---|---|---|
| `actions/checkout` | `@v4` | `@v7` | Node runtime major bump in the v5/v6/v7 line; the Node 20 annotation on the `main` run named this action. |
| `actions/setup-python` | `@v5` | `@v7` | Same Node-runtime annotation; `python-version` input is unchanged and still honored. |
| `actions/configure-pages` | `@v5` | `@v6` | Node runtime major bump; no change to the inputs this repo uses. |
| `actions/upload-pages-artifact` | `@v3` | `@v5` | **v4 dropped dotfiles from the artifact; v5 only *adds* an opt-in `include-hidden-files` input (default `false`).** So the repo-root dotfile-exclusion claim in `pages.yml` still reads true in intent. |
| `actions/deploy-pages` | `@v4` | `@v5` | **v5.0.0 moved to Node 24.** |

## Evidence

- PR [#22](https://github.com/mschwar/Garden-of-Wisdom/pull/22) — `smoke` check run
  [34715295423](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715295423):
  **success**, and the **Node 20 deprecation annotation is gone** (it was present on the
  pre-bump `main` smoke run). That disappearance is the acceptance signal for the deprecation,
  not merely the green check.
- Merged into `main` as `6df549b`.
- On `main` after the merge: `smoke` run
  [34715362562](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715362562)
  **success**; Pages deploy run
  [34715362601](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715362601)
  **success**.
- **Live acceptance** — pointed at production, not a local server:

```
$ curl -s -o /dev/null -w '%{http_code}\n' \
    https://mschwar.github.io/Garden-of-Wisdom/ \
    https://mschwar.github.io/Garden-of-Wisdom/browser/index.html \
    https://mschwar.github.io/Garden-of-Wisdom/quotes.csv \
    https://mschwar.github.io/Garden-of-Wisdom/sources.csv
200
200
200
200

$ # live CSVs byte-identical to the repo:
$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
# live https://mschwar.github.io/Garden-of-Wisdom/quotes.csv  -> 5675d7e6…
# live https://mschwar.github.io/Garden-of-Wisdom/sources.csv -> 10b4c156…
```

- Local validators after the bump: `python3 scripts/validate_quotes.py` → `RESULT: PASS`;
  `python3 scripts/check_program_contracts.py` → `RESULT: PASS`;
  `python3 scripts/validate_homepage_preview_export.py` → `RESULT: PASS`. Both CSV hashes match
  `main` before this unit, i.e. no data or export file was touched.

## Dotfile finding — issue [#23](https://github.com/mschwar/Garden-of-Wisdom/issues/23), NOT a regression

While confirming the artifact shape the bump affected, the verification found that the published
Pages artifact contains the repo-root `.gitignore`:

```
$ curl -s -o /dev/null -w '%{http_code}\n' \
    https://mschwar.github.io/Garden-of-Wisdom/.gitignore \
    https://mschwar.github.io/Garden-of-Wisdom/.git/config \
    https://mschwar.github.io/Garden-of-Wisdom/.github/workflows/pages.yml
200
404
404
```

`.gitignore` is live and returns **200**, even though `pages.yml`'s comment says top-level
dotfiles are excluded. Facts established:

- **Not caused by this bump.** The pre-bump artifact from run
  [34713537851](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34713537851) already
  contained `./.gitignore`. Comparing the pre-bump and post-bump artifacts
  (34713537851 vs 34715362601), the **only** diff is the two new handoff files — the dotfile was
  already there before the version change.
- Only **three** dotfiles are tracked repo-wide:
  `.github/workflows/browser-smoke.yml` and `.github/workflows/pages.yml` (both correctly **404** —
  they are not at the artifact root) and `.gitignore` (**published**).
- The acceptance checklist in `docs/RUNBOOK.md` only probes `/.git/config`, which is why this was
  missed — `/.git/config` is correctly 404 and that probe passing hid the `.gitignore` case.
- **Hypothesis** (to confirm on the runner, **not** a proven cause): the action's
  `--exclude=.[^/]*` pattern cannot match the `./`-prefixed names this tar invocation emits, so
  the exclusion silently does nothing at the top level.

Filed as #23 rather than fixed here: a fix is a deploy-path change that needs its own live
re-verification, exactly the rule this unit itself followed.

## Next authorized action

Issue #19 is closed. The remaining infra item is **#23** (Pages artifact dotfile exposure), which
is filed but not authorized — it needs an explicit go-ahead because it changes the deploy path.
The corpus-program next action is **W1.1 storage decision + minimal schema**, authorized in full
2026-09-12 (decision D1) — see `docs/program/W1_DECOMPOSITION.md` §W1.1 and `docs/queue.md`
§"Open — corpus program"; each W1 unit keeps its own branch, PR, and independent QA.
