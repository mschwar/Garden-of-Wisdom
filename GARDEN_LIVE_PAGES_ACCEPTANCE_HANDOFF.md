# Handoff — the live Pages acceptance checklist is automated into one command

**Branch:** `infra/check-live-pages` · **Records:** issue
[#41](https://github.com/mschwar/Garden-of-Wisdom/issues/41)

> **Process note on issue closure:** this repo's convention (see #34's, #43's, and #45's
> handoffs) is to close a finished issue **deliberately by comment after the merge, never by a
> closing keyword** in a PR/commit body, because this repo has lost issues to that keyword before.
> Issue #41 will be closed deliberately with full evidence after the merge.

## What this is

Every post-merge deploy previously required running six manual `curl` probes and two `shasum`
comparisons by hand from `docs/RUNBOOK.md` ("GitHub Pages") and transcribing the numbers into the
handoff. This had two major failure modes (issue #41):
1. **Easy to omit a probe:** missing a probe was precisely why issue #23 was misread (the manual
   checklist only probed `/.git/config`, so a published `/.gitignore` went unnoticed);
2. **Transcription risk:** copying numbers into a handoff is a manual step rather than machine-verified
   evidence; nothing re-checks the pasted numbers.

This unit ships `scripts/check_live_pages.py`, a single stdlib-only, deterministic command that:
* executes all four required 200 probes (`/`, `/browser/index.html`, `/quotes.csv`, `/sources.csv`);
* executes all three required 404 probes (`/.gitignore` [dotfile exclusion], `/.git/config` [.git exclusion], and `/.github/workflows/pages.yml` [.github exclusion]);
* downloads both live CSVs, computes their `sha256` digests, and asserts byte-identity against the local repository;
* provides built-in offline negative controls (`--self-test`) running against an ephemeral mock HTTP server on loopback to verify every failure mode with zero network dependency.

It complements `scripts/check_pages_contract.py` (which guards the workflow configuration offline in CI): the config guard asserts what the workflow asks for; this script asserts what the deployment actually published.

## What changed

| File | Change |
|---|---|
| `scripts/check_live_pages.py` | **new** — the automated checker (9 contract checks, 10 self-tests/negative controls) |
| `docs/RUNBOOK.md` | updated "GitHub Pages" section to document `check_live_pages.py` usage and options |
| `GARDEN_LIVE_PAGES_ACCEPTANCE_HANDOFF.md` | this file |

## The 9 contract checks and their negative controls

The script enforces `EXPECTED_CHECKS = 9`:
1. `GET / returns 200`
2. `GET /browser/index.html returns 200`
3. `GET /quotes.csv returns 200`
4. `GET /sources.csv returns 200`
5. `GET /.gitignore returns 404 (published dotfile guard)`
6. `GET /.git/config returns 404 (.git exclusion guard)`
7. `GET /.github/workflows/pages.yml returns 404 (.github exclusion guard)`
8. `live quotes.csv is byte-identical to repo quotes.csv`
9. `live sources.csv is byte-identical to repo sources.csv`

The 10 built-in negative controls (`--self-test`) run against an in-process ephemeral `http.server`:

| # | Self-Test ID | Condition Tested | Expected Verdict | Observed First FAIL |
|---|---|---|---|---|
| 1 | `s1_baseline` | Valid deploy (all 4x 200, 3x 404, matching CSVs) | PASS | `RESULT: PASS (9 checks)` |
| 2 | `s2_misroot_app` | Mis-rooted artifact (`/browser/index.html` returns 404) | FAIL | `got HTTP 404 (expected 200) from .../browser/index.html` |
| 3 | `s3_missing_csv` | Missing CSV (`/quotes.csv` returns 404) | FAIL | `got HTTP 404 (expected 200) from .../quotes.csv` |
| 4 | `s4_dotfile_leak` | Published dotfile (`/.gitignore` returns 200; issue #23) | FAIL | `got HTTP 200 (expected 404; /.gitignore was published!)` |
| 5 | `s5_git_leak` | Published git config (`/.git/config` returns 200) | FAIL | `got HTTP 200 (expected 404; /.git/config was published!)` |
| 6 | `s6_workflow_leak` | Published workflow (`/.github/workflows/pages.yml` returns 200) | FAIL | `got HTTP 200 (expected 404; /.github/workflows/pages.yml was published!)` |
| 7 | `s7_stale_quotes` | Stale `quotes.csv` (content/sha256 mismatch) | FAIL | `hash mismatch: live sha256=... vs repo sha256=...` |
| 8 | `s8_stale_sources` | Stale `sources.csv` (content/sha256 mismatch) | FAIL | `hash mismatch: live sha256=... vs repo sha256=...` |
| 9 | `s9_unreachable` | Host unreachable / connection refused | FAIL | `network error fetching ...: <urlopen error [Errno 61] Connection refused>` |
| 10 | `s10_local_missing` | Local repo CSV missing from disk | FAIL | `local file missing from repo: .../sources.csv` |

All 10 self-tests pass in < 0.2s without making external network calls.

## Evidence

### 1. Offline self-tests / negative controls (`python3 scripts/check_live_pages.py --self-test`)

```
=== check_live_pages self-tests (negative controls) ===
PASS: s1_baseline -- mock server provides all valid probes -> PASS
PASS: s2_misroot_app -- mis-rooted artifact (/browser/index.html returns 404) -> FAIL (fired as aimed: got HTTP 404 (expected 200) from http://127.0.0.1:59536/browser/index.html)
PASS: s3_missing_csv -- missing CSV (/quotes.csv returns 404) -> FAIL (fired as aimed: got HTTP 404 (expected 200) from http://127.0.0.1:59544/quotes.csv)
PASS: s4_dotfile_leak -- published dotfile (/.gitignore returns 200) -> FAIL (fired as aimed: got HTTP 200 (expected 404; /.gitignore was published!))
PASS: s5_git_leak -- published git config (/.git/config returns 200) -> FAIL (fired as aimed: got HTTP 200 (expected 404; /.git/config was published!))
PASS: s6_workflow_leak -- published workflow (/.github/workflows/pages.yml returns 200) -> FAIL (fired as aimed: got HTTP 200 (expected 404; /.github/workflows/pages.yml was published!))
PASS: s7_stale_quotes -- stale quotes.csv (sha256 mismatch) -> FAIL (fired as aimed: hash mismatch: live sha256=1dd74b86a150bfc3397d86f88b1bbf7234166051d660318f9a11984537f11d68 (24 bytes) vs repo sha256=b3bb78489672228020e40975e47f34f5651cdf6e3b5c3d5b3075b95227b257e6 (65672 bytes))
PASS: s8_stale_sources -- stale sources.csv (sha256 mismatch) -> FAIL (fired as aimed: hash mismatch: live sha256=fa58179ee58144fa4c8353dba0a6ded66ba4c337e6822769292e4f696193145d (19 bytes) vs repo sha256=7aafcb67119564201baf700f29143668ed469f59d83aae60f8f99648a11a27da (7222 bytes))
PASS: s9_unreachable -- unreachable server (connection refused) -> FAIL (fired as aimed: network error fetching http://127.0.0.1:59999/: <urlopen error [Errno 61] Connection refused>)
PASS: s10_local_missing -- local repository CSV missing -> FAIL (fired as aimed: local file missing from repo: .../sources.csv)

RESULT: PASS (10 self-tests / negative controls)
```

### 2. Live acceptance run (`python3 scripts/check_live_pages.py`)

```
Target URL: https://mschwar.github.io/Garden-of-Wisdom
Local repo: /Users/mschwar/Developer/Garden-of-Wisdom

PASS: GET / returns 200 (878 bytes)
PASS: GET /browser/index.html returns 200 (3713 bytes)
PASS: GET /quotes.csv returns 200 (65672 bytes)
PASS: GET /sources.csv returns 200 (7222 bytes)
PASS: GET /.gitignore returns 404 (published dotfile guard)
PASS: GET /.git/config returns 404 (.git exclusion guard)
PASS: GET /.github/workflows/pages.yml returns 404 (.github exclusion guard)
PASS: live quotes.csv is byte-identical to repo quotes.csv (sha256: b3bb78489672228020e40975e47f34f5651cdf6e3b5c3d5b3075b95227b257e6)
PASS: live sources.csv is byte-identical to repo sources.csv (sha256: 7aafcb67119564201baf700f29143668ed469f59d83aae60f8f99648a11a27da)

RESULT: PASS (9 checks)
```

Verified identically under Python 3.14 (Homebrew) and Python 3.12 (CI interpreter).

### 3. Standing suites re-run clean

* `check_pages_contract.py` → `RESULT: PASS (16 checks)`
* `check_program_contracts.py` → `RESULT: PASS`
* `validate_homepage_preview_export.py` → `RESULT: PASS`
* `check_garden_store.py` → `RESULT: PASS`
* `check_garden_envelope.py` → `RESULT: PASS`
* `check_garden_submit.py` → `RESULT: PASS`
* `check_garden_normalize.py` → `RESULT: PASS`
* `check_garden_review.py` → `RESULT: PASS`
* `check_garden_e2e.py` → `RESULT: PASS`
* `check_garden_ledger.py` → `RESULT: PASS`
* `run_negative_controls.py --check` → `RESULT: PASS (36 anchors checked, 9 harness self-tests)`

`quotes.csv` and `sources.csv` are byte-identical throughout (`b3bb7848…` / `7aafcb67…`).

## Review status (independent QA)

**Independent reviewer, fresh subagent: PASS, no high/medium defects.**
The reviewer verified:
1. Git diff against `main`: only `scripts/check_live_pages.py`, `docs/RUNBOOK.md`, and `GARDEN_LIVE_PAGES_ACCEPTANCE_HANDOFF.md` are touched.
2. `quotes.csv` and `sources.csv` are byte-identical to `main` (`b3bb7848…` / `7aafcb67…`).
3. Self-tests (`--self-test`) pass with all 10 controls firing as aimed in <0.2s without network calls.
4. Live acceptance probes against `https://mschwar.github.io/Garden-of-Wisdom` pass with 9/9 checks green.
5. Zero closing keywords (`Closes #41`, `Fixes #41`, etc.) exist anywhere in the commit or PR template.
6. One low/informational suggestion (L-1: use a dynamic closed socket rather than a hard-coded port 59999 for `s9_unreachable`) was implemented and re-verified clean immediately.

## What this unit deliberately did not do

* Did not touch `quotes.csv` or `sources.csv`.
* Did not change `.github/workflows/pages.yml` or the deployment pipeline.
* Did not wire a live probe into CI (per issue #41 design: CI cannot run live checks without an external network and an existing deployment to point at).
* Did not touch `AGENTS.md` (policy-blocked).

