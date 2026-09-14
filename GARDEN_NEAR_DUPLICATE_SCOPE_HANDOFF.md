# Handoff — issue #34: the near-duplicate sweep is corpus-wide, and a shared citation needs a locator

Repo: `mschwar/Garden-of-Wisdom`. Branch `fix/near-duplicate-scope-and-citation`, one unit, one PR.
Decided and implemented 2026-09-13. `quotes.csv` / `sources.csv` untouched (`5675d7e6…` /
`10b4c156…`).

## What was asked

Decide the two policy questions #31 deliberately left open — the sweep's **scope** and whether a shared
`source_ref` is evidence on its own (W1.4 ruling 2's locator test) — implement the decision with a guard
that can fail for the rule changed, prove it with a negative control in a throwaway `/tmp` copy,
re-derive the frozen report in a new dated section, and re-count the queue's D6 item. If a decision
could not be implemented without editing the corpus, stop and record why.

## The decision, and the measurement that made it

Four combinations were measured on the frozen 324-row corpus before choosing:

| # | scope | what a shared `source_ref` needs | pairs flagged |
|---|---|---|---|
| A | per-`tradition` | anything | **45** — the count the 2026-09-11 transcript prints |
| B | corpus-wide | anything | **196** |
| C | per-`tradition` | a **specific** citation (carries a locator) | **15** |
| D | **corpus-wide** | **a specific citation** | **20** ← adopted |

**Adopted: D.** The two questions turn out to be one decision. #31 kept the sweep scoped because
widening it under the rules as they then were (A → B) adds 151 pairs, **146** of them the bare
`Oral Tradition` label. Under the locator rule (A → D) the same widening adds **5** pairs and **zero**
label noise — the 151 additions of B and the 30 suppressions of the locator rule are *the same pairs*.
The citation rule removes the noise; once it does, keeping the scope costs real signal for nothing.

The 5 recovered pairs are cross-tradition text overlaps the old sweep could not see at all:

| pair | traditions | similarity |
|---|---|---|
| `39 ~ 53` | Christianity ~ Judaism | **0.82** |
| `50 ~ 318` | Christianity ~ Diné (Navajo) | 0.71 |
| `78 ~ 173` | Islam ~ Sikhism | 0.62 |
| `87 ~ 187` | Islam ~ Zoroastrianism | 0.61 |
| `175 ~ 332` | Sikhism ~ Hopi (Pueblo) | 0.61 |

`39 ~ 53` is "Thou shalt love thy neighbour as thyself." against "Love thy neighbour as thyself." — a
pair a duplicate sweep exists to surface, and the strongest argument that the scope mattered.

**Rejected:** variant C (adopt the rule, keep the scope) — internally consistent and 5 pairs cheaper,
but it leaves the validator blind to a duplicate filed under a second `tradition` label, and it leaves
the validator disagreeing with the store, whose W1.4 hint generator already compares every candidate
against every other and documents that as a decision (`docs/program/W1_4_NORMALIZATION_HINTS.md` §5).
**Also rejected:** variant B (widen without tightening the rule) — the state #31 explicitly refused.

**Rejected implementation choice:** a local copy of the locator test plus a conformance assertion. The
validator **imports** `citation_specificity()` from `scripts/garden_normalize.py` instead, so there is
one implementation of the rule; the hidden coupling that creates is made loud by a hard check pinning
the rule's two canonical outcomes. Full reasoning in `docs/DECISIONS.md` ("The near-duplicate sweep is
corpus-wide …").

## What changed in `scripts/validate_quotes.py`

- Scope: `groups = [rows]` — the sweep is every row, not one `tradition`'s.
- Citation rule: a shared `source_ref` is evidence only when
  `citation_specificity(source_ref) == "specific"`.
- Reason string: `same source_ref` → `same specific citation` (the old wording no longer describes the
  rule). `same specific citation; text similarity 0.60` for the 3 pairs that clear both.
- New evidence line: `pairs sharing an exact source_ref (corpus-wide): 189 -- 13 specific (citation
  evidence), 176 generic (suppressed by the locator rule)`.
- Four hard checks (see the control table below), one of which implements #31's own finding that the
  scope had no automated falsifier.
- `pair_similarity` gained an exact pre-filter (see "Cost").

Output: **45 → 20** pairs, `RESULT: PASS`.

## Negative controls (throwaway `/tmp` copy — the real tree only ever read)

Harness: `/tmp/issue34_controls.py`; each control copies the repo, asserts its anchor string is unique,
mutates the copy, and runs the copy's `scripts/validate_quotes.py`. Verbatim transcript:

```
--- sanity (no mutation)
    exit=0
    first FAIL: <none>
    RESULT line: ['RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)']
--- c1 scope reverted to per-tradition
    exit=1
    first FAIL: FAIL: the near-duplicate sweep is not corpus-wide: pairs/numbers only in the corpus-wide scan [(39, 53, 'text similarity 0.82'), (50, 318, 'text similarity 0.71'), (78, 173, 'text similarity 0.62'), (87, 187, 'text similarity 0.61'), (175, 332, 'text similarity 0.61')], only in the reported sweep []
    RESULT line: ['RESULT: FAIL (1 hard failure categories)']
--- c2 locator condition dropped in detected_reason
    exit=1
    first FAIL: FAIL: near-duplicate reasons do not match the evidence (reported, expected): [('5', '19', 'same specific citation', None), ('5', '23', 'same specific citation', None), ('19', '23', 'same specific citation', None), ('262', '270', 'same specific citation', None), ('312', '315', 'same specific citation', None), ('312', '316', 'same specific citation', None), ('312', '319', 'same specific citation', None), ('312', '322', 'same specific citation', None), ('312', '323', 'same specific citation', None), ('312', '325', 'same specific citation', None), ('312', '327', 'same specific citation', None), ('312', '328', 'same specific citation', None), ('312', '329', 'same specific citation', None), ('312', '330', 'same specific citation', None), ('312', '331', 'same specific citation', None), ('312', '332', 'same specific citation', None), ('312', '334', 'same specific citation', None), ('312', '335', 'same specific citation', None), ('312', '336', 'same specific citation', None), ('312', '338', 'same specific citation', None), ('312', '339', 'same specific citation', None), ('312', '340', 'same specific citation', None), ('315', '316', 'same specific citation', None), ('315', '319', 'same specific citation', None), ('315', '322', 'same specific citation', None), ('315', '323', 'same specific citation', None), ('315', '325', 'same specific citation', None), ('315', '327', 'same specific citation', None), ('315', '328', 'same specific citation', None), ('315', '329', 'same specific citation', None), ('315', '330', 'same specific citation', None), ('315', '331', 'same specific citation', None), ('315', '332', 'same specific citation', None), ('315', '334', 'same specific citation', None), ('315', '335', 'same specific citation', None), ('315', '336', 'same specific citation', None), ('315', '338', 'same specific citation', None), ('315', '339', 'same specific citation', None), ('315', '340', 'same specific citation', None), ('316', '319', 'same specific citation', N... [truncated by the harness's own print, not by this file]
    RESULT line: ['RESULT: FAIL (1 hard failure categories)']
--- c3 dual-reason suffix dropped
    exit=1
    first FAIL: FAIL: near-duplicate reasons do not match the evidence (reported, expected): [('66', '67', 'same specific citation', 'same specific citation; text similarity 0.60'), ('201', '306', 'same specific citation', 'same specific citation; text similarity 0.86'), ('209', '301', 'same specific citation', 'same specific citation; text similarity 0.82')]
    RESULT line: ['RESULT: FAIL (1 hard failure categories)']
--- c4 citation_specificity drift (store rule changed)
    exit=1
    first FAIL: FAIL: citation rule drift: citation_specificity('Gita 2.47') is 'generic', but this report's ruling assumes 'specific'
    RESULT line: ['RESULT: FAIL (1 hard failure categories)']
--- c6 pair_similarity reverted to one directional ratio
    exit=1
    first FAIL: FAIL: near-duplicate detection is row-order dependent: pairs/numbers only in file order [(66, 67, 'same specific citation'), (87, 187, 'text similarity 0.64'), (113, 114, 'text similarity 0.69')], only in reversed order [(66, 67, 'same specific citation; text similarity 0.61'), (113, 114, 'text similarity 0.67'), (189, 216, 'text similarity 0.60')]
    RESULT line: ['RESULT: FAIL (1 hard failure categories)']
--- c5 corpus mutation: rewrote source_ref on 48 generic rows
--- c5 vacuity guard (no generic shared source_ref left)
    exit=1
    first FAIL: FAIL: vacuity guard: no pair on this corpus shares a generic source_ref, so the locator rule's suppression cannot be shown to do work -- re-derive this guard against the current corpus rather than letting it pass on nothing
    RESULT line: ['RESULT: FAIL (1 hard failure categories)']
```

| # | mutation | first `FAIL:` line | proves |
|---|---|---|---|
| sanity | none | `<none>` — `RESULT: PASS` | the harness is not trivially red |
| c1 | `groups` regrouped per `tradition` | `the near-duplicate sweep is not corpus-wide: … only in the corpus-wide scan [(39, 53, …), (50, 318, …), (78, 173, …), (87, 187, …), (175, 332, …)], only in the reported sweep []` | the SCOPE guard catches the reversion and **names the exact 5 pairs** the scoped sweep would have missed — this is #31's control c4, now closed |
| c2 | locator condition removed from the rule | `near-duplicate reasons do not match the evidence (reported, expected): [('5','19','same specific citation', None), …]` | the CITATION guard catches reporting a generic shared citation as evidence (30 pairs) |
| c3 | dual-reason suffix dropped | same line, naming exactly `66 ~ 67`, `201 ~ 306`, `209 ~ 301` | #31's decision 1 annotation still has its own falsifier |
| c4 | `LOCATOR_PATTERN` neutered in `garden_normalize` | `citation rule drift: citation_specificity('Gita 2.47') is 'generic', but this report's ruling assumes 'specific'` | the imported rule cannot be silently redefined under the validator |
| c5 | every generic `source_ref` made unique in a copy of `quotes.csv` | `vacuity guard: no pair on this corpus shares a generic source_ref …` | the suppression is not passing on nothing |
| c6 | scorer reverted to one directional `ratio()` | `near-duplicate detection is row-order dependent: …` | #31's order-independence guard is intact |

Every control exits 1 with a targeted `FAIL:` line and **no traceback**; the unmutated copy exits 0.
Each fires on the check it was aimed at, and each of the four checks has a control that only it catches
(c1 → SCOPE alone; c2/c3 → CITATION; c4 → DRIFT; c5 → VACUITY; c6 → ORDER).

**This session both authored and reviewed the change.** The control harness was written after the code
by the same session; the operator may still want a foreign pass. Said plainly rather than implied
otherwise.

## Cost, and the pre-filter's proof

The sweep is now every unordered pair — **52,326** of them — and the run went from ~2.3s to **~21s**
(measured 20.8s / 20.3s, byte-identical output under Homebrew `python3` 3.14.5 and CI's
`/opt/homebrew/bin/python3.12`). `pair_similarity` carries an exact pre-filter (a pair's score cannot
exceed `2 × |multiset intersection| / (len(a)+len(b))`, so a pair that cannot clear `0.60` is not scored
at all). Its output-neutrality was verified by brute force over every pair, not argued:

```
pairs: 52326  scored: 27152  pre-filtered: 25174
highest TRUE symmetric score among pre-filtered pairs: 0.5062  (pair ('16', '87'))
threshold: 0.60 -> OK: no pre-filtered pair could have been flagged
```

Probe: `/tmp/issue34_prefilter_proof.py`. Accepted rather than optimized further: the guard passes are
the unit's evidence, and 21s in a CI job with a 15-minute timeout is not worth a weaker guard.

## Docs closeout

- `docs/data/DATA_QUALITY_REPORT.md` — new section **"Re-derivation 2026-09-13 (issue #34)"** with the
  four-variant table, the class tables, the guard/control table and the verbatim fresh transcript. The
  2026-09-11 and "#31" transcripts are **byte-identical**; the change is verified as additions only:
  `git diff -U0 docs/data/DATA_QUALITY_REPORT.md | grep '^-[^-]' | wc -l` → `0`. Two pointer annotations
  were added at the top and under the caveat so a reader is not left with the superseded `45`.
- `docs/queue.md` — the D6 item re-counted to **20 to inspect / 0 to skip** (it read 15 / 30), with the
  note that the item's own "explicitly SKIP the generic-`source_ref` false positive" instruction is now
  vacuous; the #34 filing bullet marked resolved with its superseded numbers annotated; the #31 closed
  entry annotated where its `45` and `15/30` are now stale; a new
  `## Closed — 2026-09-13 near-duplicate sweep scope + citation rule (issue #34)` section.
- `docs/DECISIONS.md` — new dated entry with both decisions, both rejected alternatives, the scope
  measurement, the import-vs-copy reasoning, the guards, and the cost.
- `docs/RUNBOOK.md` — the validator section now names the four checks (it named two), the corpus-wide
  scope, the locator rule, the ~21s cost and the pre-filter, so the operator's copy of the rule is not
  stale.
- Stale counts annotated where a *live* doc still claimed `45`: `docs/program/SYSTEM_MODEL.md` and
  `docs/program/W1_DECOMPOSITION.md` carry a parenthetical, and
  `docs/program/W1_4_NORMALIZATION_HINTS.md` gained two annotations (the §3 `45` reference and the §5
  "the legacy report compared pairs within one `tradition`" divergence, which this unit closed).
- This handoff.

## Deliberately NOT done

- **No corpus edit.** `quotes.csv` / `sources.csv` byte-identical (`5675d7e6…` / `10b4c156…`), checked
  after every step. Every number in the report, the queue and `DECISIONS.md` is a derivation over the
  corpus. Nothing needed the corpus changed, so nothing was stopped for that reason.
- **No D6 curation.** The item is re-counted, not executed: whether the 5 new cross-tradition pairs are
  accidental duplication or legitimate parallel attestations is a human curation decision (`AGENTS.md`).
- **No verification-status change**, no `_`-glyph rewrite, no row merge or deletion.
- **No corpus-program work.** No store surface, no schema, no migration, no state vocabulary, no W2.

## Out-of-scope findings (recorded, not fixed in passing)

- **CI still runs none of the six W1 acceptance suites.** `browser-smoke.yml` runs
  `validate_quotes.py`, `check_program_contracts.py` and `validate_homepage_preview_export.py`; the six
  W1 suites (`check_garden_store.py` 59, `check_garden_envelope.py` 102, `check_garden_submit.py` 134,
  `check_garden_normalize.py` 232, `check_garden_review.py` 246, `check_garden_e2e.py` 96) are
  local-evidence only. Unchanged by this unit and still needing its own unit (it is a guarded workflow
  change) — see the queue. **This unit's own validator is in CI**, so its guards are covered.
- **The vacuity guard is a tripwire for future corpus work.** If a D6/D7 edit ever leaves the corpus
  with no pair sharing a generic `source_ref`, `validate_quotes.py` fails on purpose with the
  `vacuity guard:` line and the fix is to re-derive that guard, not to delete it. Recorded here because
  the failure will look like a data error and is not one.

## Exact next Prompt

**Wire the six W1 acceptance suites into CI.** That is the other long-open, non-gated item: extend the
`Check the data validators still pass` step in `.github/workflows/browser-smoke.yml` to run
`scripts/check_garden_store.py`, `scripts/check_garden_envelope.py`, `scripts/check_garden_submit.py`,
`scripts/check_garden_normalize.py`, `scripts/check_garden_review.py` and `scripts/check_garden_e2e.py`
(all stdlib-only, deterministic, exit-0/1), which is the decision the queue has carried open since W1.2
and re-recorded at every W1 close-out. Measure the step's wall-clock (the validator now takes ~21s on
its own) and confirm a failure in any one suite turns the job red — a suite that is wired in but cannot
fail is the same defect class this repo keeps finding, so give each one a negative control in a
throwaway `/tmp` copy before claiming the work done. `pages.yml`'s artifact `path: '.'` is a guarded
contract and must not be touched.

Remaining open `Spec:` issues, with their status read honestly rather than assumed: **#30** (no
candidate-withdrawal path; store/contract surface — non-gated but it changes W1's store contract, so
read the W1 decomposition before starting), **#23** (Pages artifact publishes `/.gitignore`; deploy-path
change needing its own live re-verification), **#27** (`AGENTS.md` doc gap — needs an operator edit,
agent writes to that file are refused), **#6 / #5 / #4** (corpus and export curation; #5 and #4 touch
verification status or the CSV schema and are gated behind the human curation pass).

**Still gated — do not start:** W2 and everything after it (Gate B is accepted; W2 authorization is a
separate operator decision), any discovery adapter, any canonical promotion path, the D6/D7 corpus
curation edits themselves (human pass), and any verification-status change.

## Merged — post-merge record

- Commit `f5986c8` on `fix/near-duplicate-scope-and-citation`, PR
  [#36](https://github.com/mschwar/Garden-of-Wisdom/pull/36), **merged as `4ce8e8e`** (2026-09-13).
- CI on the PR: smoke run
  [34794438967](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34794438967) **success**
  (1m22s), GitGuardian **pass**. The job log shows the new rule itself running in CI, not just
  compiling:
  `near-duplicate candidates: 20 (corpus-wide)`,
  `pairs sharing an exact source_ref (corpus-wide): 189 -- 13 specific (citation evidence), 176 generic
  (suppressed by the locator rule)`, `RESULT: PASS`.
- On `main` after the merge: smoke run
  [34794547436](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34794547436) **success**,
  Pages deploy run
  [34794547412](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34794547412) **success**.
- Live acceptance on the merged `main` (`curl`): `/`, `/browser/index.html`, `/quotes.csv`,
  `/sources.csv` all **200**, and both live CSVs `sha256`-identical to the repo
  (`5675d7e6…` / `10b4c156…`).
- Re-ran on the merged `main`: all nine stdlib validators (`validate_quotes.py`,
  `check_program_contracts.py`, `validate_homepage_preview_export.py`, and the six W1 suites) →
  `RESULT: PASS` / exit 0 under **both** interpreters; `smoke_quote_browser.py` → `RESULT: PASS`
  (33 checks).
- **The issue stayed open through the merge** — checked after merging, because this repo has already
  lost #34 twice to a closing keyword in a PR/commit body. It is still `OPEN` and now carries this
  unit's decision.
- Local environment note (not a repo defect): `smoke_quote_browser.py` could not launch Chromium on
  this machine — the Playwright browser had never been downloaded — so
  `.venv/bin/python -m playwright install chromium` was run (81.9 MiB, test-only dependency) before
  the smoke test could pass locally.
