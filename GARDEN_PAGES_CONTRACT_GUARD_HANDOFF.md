# Handoff — the Pages deploy contract gets an automated guard

**Branch:** `ci/guard-pages-deploy-contract` ·
**Closed:** the `docs/queue.md` infra item "Guard the Pages deploy contract" and issue
[#23](https://github.com/mschwar/Garden-of-Wisdom/issues/23) ·
**Filed out of scope:** [#41](https://github.com/mschwar/Garden-of-Wisdom/issues/41)

## What this unit is

Not a corpus-program unit: no W2 work, no store surface, no schema, no state vocabulary, no
CSV edit. It closes two long-open items that turned out to be one contract:

1. the queue's "Guard the Pages deploy contract" item (`.github/workflows/pages.yml` must keep
   `path: '.'`, and Pages "Source" must stay GitHub Actions), and
2. issue [#23](https://github.com/mschwar/Garden-of-Wisdom/issues/23) — the Pages artifact
   publishes top-level dotfiles (`/.gitignore` live and 200 despite the claimed exclusion).

Both lived only as **prose** (the workflow's comment block, `docs/RUNBOOK.md` -> "GitHub
Pages", `docs/architecture/QUOTE_BROWSER.md` -> "Deployment") and **nothing in the repo could
falsify any of it**. The two ways this contract can break are both silent: a mis-rooted
artifact loads and renders **0 quotes**, and an upload-action regression publishes tracked
dotfiles. In either case the deploy job **succeeds**. `scripts/smoke_quote_browser.py` drives
the page over a local server rooted at the repo root, so it cannot see the artifact at all.

## What changed

Four files, one of them new:

| File | Change |
|---|---|
| `scripts/check_pages_contract.py` | **new** — the guard (15 checks: 14 contract + a count guard) |
| `.github/workflows/browser-smoke.yml` | one new step, "Guard the Pages deploy contract", running the guard |
| `.github/workflows/pages.yml` | **comment only** — records that the hidden-file exclusion is a v4+ behavior and that the major is load-bearing; `path: '.'`, the action majors and every other line are unchanged |
| `docs/RUNBOOK.md` | new section "Guard the Pages deploy contract"; the live checklist gains the two 404 probes it was missing; the "always drops dotfiles" claim is qualified with the v4 dependency |
| `docs/architecture/QUOTE_BROWSER.md` | same claim qualified; the live check now names `/.gitignore`, not just `/quotes.csv` |
| `docs/queue.md`, `docs/DECISIONS.md` | close-out and the decision record |

`git diff --stat` on the two workflow files: `pages.yml` is comment-only (no YAML change), and
`browser-smoke.yml` adds three lines.

## What the guard checks, and why each check is falsifiable

`python3 scripts/check_pages_contract.py` — stdlib only, no network, writes nothing, exits 0
with `RESULT: PASS` / non-zero with `RESULT: FAIL` and one `FAIL:` line per broken check.

```
$ python3 scripts/check_pages_contract.py
PASS: the workflow parses into the shape this guard reads
PASS: triggers: push to main and workflow_dispatch
PASS: concurrency: group `pages`, cancel-in-progress false
PASS: permissions include `pages: write` and `id-token: write`
PASS: the deploy job is guarded to refs/heads/main
PASS: an upload step uses actions/upload-pages-artifact
PASS: the upload action major excludes top-level hidden files
PASS: the uploaded path is the repo root ('.')
PASS: the upload step does not include hidden files
PASS: the upload step keeps the artifact name `github-pages`
PASS: the deploy step keeps id `deployment` and the environment reads its page_url
PASS: browser/app.js still fetches ../quotes.csv and ../sources.csv
PASS: the fetched CSVs exist at the repo root
PASS: the root index.html shim still forwards to browser/index.html

RESULT: PASS (15 checks)
```

Two guards are worth calling out because they are the difference between a guard and a
decoration:

- **The shape guard.** If the workflow cannot be parsed into the shape the guard understands,
  the run FAILs with "re-derive this guard rather than deleting it" — an unrecognized reformat
  can never pass silently, which is the failure mode a text-scanning check would otherwise have.
- **`VERIFIED_UPLOAD_MAJORS = {4, 5}`.** Below 4 FAILs naming the #23 mechanism; **above** the
  set FAILs with an instruction to read the action's `action.yml` and extend the set with the
  evidence. A future major can change the `tar` invocation — that is exactly how this class
  appeared — so an unknown version must not pass.

## The negative controls (16, all fired as aimed)

Throwaway `/tmp` copy of the repo, one mutation per control, each asserting the **first**
`FAIL:` line is the aimed check. Harness: `/tmp/pages_guard_controls.py`.

```
pristine copy: exit=0  RESULT: PASS (15 checks)
ok   c1 upload path -> browser/
       exit=1 first-FAIL="the uploaded path is the repo root ('.')"
ok   c2 upload action v5 -> v3 (published .gitignore, issue #23)
       exit=1 first-FAIL='the upload action major excludes top-level hidden files'
ok   c3 include-hidden-files: true
       exit=1 first-FAIL='the upload step does not include hidden files'
ok   c4 override the artifact name
       exit=1 first-FAIL='the upload step keeps the artifact name `github-pages`'
ok   c5 delete the refs/heads/main guard
       exit=1 first-FAIL='the deploy job is guarded to refs/heads/main'
ok   c6 cancel-in-progress -> true
       exit=1 first-FAIL='concurrency: group `pages`, cancel-in-progress false'
ok   c7 id-token: write -> read
       exit=1 first-FAIL='permissions include `pages: write` and `id-token: write`'
ok   c8 app.js fetch -> ../data/quotes.csv
       exit=1 first-FAIL='browser/app.js still fetches ../quotes.csv and ../sources.csv'
ok   c9 upload step uses an unknown action
       exit=1 first-FAIL='an upload step uses actions/upload-pages-artifact'
ok   c10 upload action -> unverified major v6
       exit=1 first-FAIL='the upload action major excludes top-level hidden files'
ok   c11 root quotes.csv removed
       exit=1 first-FAIL='the fetched CSVs exist at the repo root'
ok   c12 push trigger -> dev branch
       exit=1 first-FAIL='triggers: push to main and workflow_dispatch'
ok   c13 environment url loses the page_url output
       exit=1 first-FAIL='the deploy step keeps id `deployment` and the environment reads its page_url'
ok   c16 deploy step id -> deploy
       exit=1 first-FAIL='the deploy step keeps id `deployment` and the environment reads its page_url'
ok   c14 steps list destroyed (shape guard)
       exit=1 first-FAIL='the workflow parses into the shape this guard reads'
ok   c15 a registered check is deleted (count guard)
       exit=1 first-FAIL='check count'

restored copy: exit=0  RESULT: PASS (15 checks)
ALL CONTROLS FIRED AS AIMED
```

**A control found a real coverage gap, which is the point of running them.** `c13` — mutating
`steps.deployment.outputs.page_url` to `...page_url_unused` — left the run **green**: the check
matched a substring, so any value *containing* the output expression passed. The check now
compares the environment URL exactly, and `c16` (the deploy step's `id` -> `deploy`) gives the
other half of that check its own falsifier, so neither half can be the one that silently holds.

## Issue #23, re-measured rather than assumed

The filed premise: `/.gitignore` is live and returns 200. **On `main` today it does not
reproduce**, and the evidence is artifact-level:

```
$ gh api repos/mschwar/Garden-of-Wisdom/actions/artifacts?per_page=5
10332485746 github-pages 2026-09-14T03:46:34Z expired=false size=444279

$ cd /tmp/ghpages && gh api repos/mschwar/Garden-of-Wisdom/actions/artifacts/10332485746/zip > a.zip
$ unzip -q a.zip && tar -tf artifact.tar | grep -E '^\./\.[^/]*$'
$ tar -tf artifact.tar | grep -E '/\.'
$ tar -tf artifact.tar | wc -l
     139

$ for p in "" "browser/index.html" "quotes.csv" "sources.csv" ".gitignore" ".git/config"; do
    code=$(curl -s -o /dev/null -w '%{http_code}' "https://mschwar.github.io/Garden-of-Wisdom/$p")
    echo "$code  /$p"; done
200  /
200  /browser/index.html
200  /quotes.csv
200  /sources.csv
404  /.gitignore
404  /.git/config
```

No member of the current artifact is hidden at any depth: no `./.gitignore`, no `./.git`, no
`./.github`, no `./.venv`.

**The mechanism is the upload action's own `action.yml`**, read at three majors:

```
v3  tar ... --exclude=.git --exclude=.github .        # dotfiles NOT excluded
v4  ... --exclude=".[^/]*"                            # dotfiles excluded
v5  ... --exclude=.[^/]*                              # dotfiles excluded
```

v3 is what this repo ran when the issue was filed, and it published `./.gitignore`. So the
major bump of 2026-09-12 (`10d8c31`, PR #22) **removed** the leak — the queue's own note ("not a
regression from #19") was right about the cause and wrong about the cure, and the queue's
candidate mechanism ("the action's `--exclude=.[^/]*` pattern cannot match the `./`-prefixed
names") is a hypothesis the artifact refutes. The issue is closed deliberately by comment
**after** the merge, never by a closing keyword (this repo has twice lost an issue to one).

**The real gap was the checklist, not the code.** It probed `/.git/config` — correctly 404,
because `.git` was always excluded — and never `/.gitignore`. A correctly-rooted artifact can
still publish dotfiles, so the docs now probe both, and the artifact can be listed without a
deploy (`gh api …/artifacts` -> download -> `tar -tf artifact.tar`; no member may start with
`./.`).

## Evidence — the whole local suite, before and after

`check_pages_contract.py` added to the standing set; all eleven pass under `python3` (Homebrew
3.14.5) and the three validators + the new guard under `/opt/homebrew/bin/python3.12` (CI's
interpreter):

```
check_pages_contract                rc=0 RESULT: PASS (15 checks)
validate_quotes                     rc=0 RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
check_program_contracts             rc=0 RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
validate_homepage_preview_export    rc=0 RESULT: PASS
check_garden_store                  rc=0 RESULT: PASS (create -> write -> export -> wipe -> re-import is byte-identical)
check_garden_envelope               rc=0 RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)
check_garden_submit                 rc=0 RESULT: PASS (submissions persist: captures verbatim + immutable, candidates at intake, no decision, refused submissions write nothing)
check_garden_normalize              rc=0 RESULT: PASS (normalization records every change and preserves the capture verbatim; hints are deterministic, cited, and never a state)
check_garden_review                 rc=0 RESULT: PASS (all twelve curation transitions audit correctly, the reversal path strands no dimension, and no curation action writes research state)
check_garden_e2e                    rc=0 RESULT: PASS (a messy batch is ingested, normalized, hinted and reviewed while originals, provenance, decision history and duplicate hints all survive, and no curation action implies verification)
check_garden_ledger                 rc=0 RESULT: PASS (the unverifiable side-car ledger works end to end)
```

`quotes.csv` / `sources.csv` unchanged: `5675d7e6…` / `10b4c156…` (identical to every prior
unit's recorded hash). No new dependency, no change to `requirements-dev.txt`, `pages.yml`'s
`path:` untouched.

## Review status (read this before trusting the controls)

**Same-session authoring and review, declared.** The unit was authored and its control harness
written in this session; there was no independent reviewer. The controls are an *author's* set,
aimed one per check. A foreign pass — re-reading `scripts/check_pages_contract.py` against
`pages.yml` with its own mutations, especially around the indentation-based step parser and the
`VERIFIED_UPLOAD_MAJORS` boundary — is still worthwhile, and the operator may want it before
merging.

## What this unit deliberately did not do

- **No deploy-path change.** `path: '.'` is unchanged and `pages.yml` changed by comment only.
  Staging the artifact into a temp directory with `rsync` (rejected alternative (a) in
  `docs/DECISIONS.md`) would satisfy the `../` fetches but breaks the documented contract this
  guard exists to keep.
- **No live check in CI.** The guard is offline and deterministic by design; a live probe cannot
  run in CI without a successful deploy to point at. Automating the manual checklist is filed as
  issue [#41](https://github.com/mschwar/Garden-of-Wisdom/issues/41), with its own negative
  controls owed.
- **No `AGENTS.md` edit** — still policy-blocked (see the out-of-scope findings below).
- **No change to `scripts/smoke_quote_browser.py`** — it already fails loudly on a mis-rooted
  *local* tree, and that check is not weakened by this one.
- Did not touch `requirements-dev.txt`, `pages.yml`'s deploy step, or the `github-pages`
  environment settings.

## Out of scope (recorded, not fixed)

- **Issue [#41](https://github.com/mschwar/Garden-of-Wisdom/issues/41) (new)** — automate the
  live Pages acceptance checklist into one command. Filed, with a queue entry in the infra
  section.
- **Issue [#27](https://github.com/mschwar/Garden-of-Wisdom/issues/27) is still blocked and is
  the head of the issue board.** A guard-writing unit is the natural place to close the
  documented resume-path gap, and it could not: `AGENTS.md` writes are refused by tool policy
  in this environment — the attempt was made and blocked, with the policy stating that silence
  is not consent and that the edit must not be retried through another path. It still needs an
  operator edit or an explicit policy exception for the file. The corpus-program commands and
  the read-only rule are unchanged from the issue body, and `AGENTS.md` is still 63 lines with
  `grep -c 'garden_' AGENTS.md` -> `0`.
- **Issue [#30](https://github.com/mschwar/Garden-of-Wisdom/issues/30)** (a candidate can never
  be withdrawn; a whitespace-only submission is permanent) remains the next-most-recent open
  spec and still needs a **contract decision** (tighten envelope rule 2, or add an operator
  withdrawal that keeps the capture) before it can be implemented. It was not taken here
  precisely because it is not an implementation-only unit.
- The "Consider adding a duplicate/near-duplicate review view to the browser" infra item is
  conditional on the D6 curation pass and stays open.

## Exact next authorized action

`docs/queue.md`'s first open item is **D7 — close the 14 unresolved `source_id` links** (ADOPTED
SCOPE, sequenced "runs AFTER W1", and W1 is complete, so the sequencing gate is satisfied).
Re-confirm the open-issue set with `gh issue list --state open` before trusting any breadcrumb.
Two items are **blocked on the operator**, not on work: issue
[#27](https://github.com/mschwar/Garden-of-Wisdom/issues/27) (needs an edit to `AGENTS.md` or a
policy exception) and issue [#30](https://github.com/mschwar/Garden-of-Wisdom/issues/30) (needs
a contract decision). W2 remains unauthorized.
