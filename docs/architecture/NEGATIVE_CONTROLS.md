# Negative controls: how a checker's own falsifiability is machine-checked

**Script:** `scripts/run_negative_controls.py` (stdlib only) · **CI:** `browser-smoke.yml`,
step "Machine-check the checkers' negative controls" · **Filed from:** issue
[#43](https://github.com/mschwar/Garden-of-Wisdom/issues/43)

## The problem this closes

Every checker in this repo was supposed to come with *negative controls* — for each guard, a
mutation that turns the run red with that guard's own `FAIL:` line. The tables lived in prose
(`GARDEN_*_HANDOFF.md`), produced by a throwaway harness in `/tmp` that was deleted with the
unit. Two consequences, both measured rather than assumed:

1. **The evidence was not independently verifiable.** The foreign QA pass on the Pages
   deploy-contract guard unit reported it could not verify "16 negative controls, all fired as
   aimed" without reading the author's harness, which was out of bounds for that pass. The
   only support for a guard's falsifiability was the author's own claim about a file nobody
   else could run.
2. **A vacuous check was undetectable.** `scripts/check_pages_contract.py` has an
   `EXPECTED_CHECKS` count guard that fails when a check is *deleted* — but foreign QA
   mutation `p36` gutted a check body to `return None` while keeping its registration, and the
   run stayed **green**. Counting registrations is not proving falsifiability.

## What the harness does

```
python3 scripts/run_negative_controls.py            # self-tests + root check + every control
python3 scripts/run_negative_controls.py --check     # anchors only: no checker is run
python3 scripts/run_negative_controls.py --list      # print the control table
python3 scripts/run_negative_controls.py --checker scripts/check_pages_contract.py
```

1. **Copy, never mutate.** The working tree is copied to a throwaway directory
   (`shutil.copytree`, excluding `.git` / `.venv` / `node_modules` / `__pycache__`). Checkers
   are run with `cwd` inside that copy, so a checker that writes a store, a temp file or a
   `__pycache__` writes it there. The repo's own files are never touched — the file a control
   mutated is restored from its pristine bytes in a `finally`, and the isolation is proven by
   re-running a full pass and comparing the repo's bytes (recorded in the handoff).
2. **Anchor first.** For every control, the anchor must occur **exactly once** in its target
   file. This is the anti-rot guard: when the file changes under the table, the run says
   `anchor occurs 0 time(s) … re-derive this control` (`ROTTEN_ANCHOR`) instead of silently
   skipping the control or mutating the wrong occurrence. `--check` runs just this pass.
3. **Baseline first.** Each checker is run unmutated before its controls. An already-red
   baseline is reported as itself and its controls are **not** credited with firing, so a
   control can never be evidence of a failure the tree already had.
4. **One mutation, one run, one asserted line.** The mutation is applied, the checker is run
   from inside the copy, and the **first** `FAIL:` line in its output must equal the control's
   expected line **exactly**. `FAIL:` is the whole evidence: it names which guard refused.

## Verdicts

| Verdict | Meaning | Passes? |
|---|---|---|
| `FIRED` | the aimed `FAIL:` line was the first one, and the checker exited non-zero | ✅ |
| `GREEN_OK` | a contract-preserving edit stayed green, as the control requires | ✅ |
| `COVERAGE_GAP` | the mutation stayed green — **this check has no falsifier** | ❌ |
| `MASKED` | a different check refused first (the aimed check was never exercised) | ❌ |
| `ROTTEN_ANCHOR` | the anchor no longer occurs exactly once; the table has drifted | ❌ |
| `FALSE_POSITIVE` | an edit that must stay green went red | ❌ |
| `CRASH` | non-zero exit with no `FAIL:` line — a crash is not the aimed guard | ❌ |
| `INCONSISTENT` | the aimed line printed but the checker exited 0 | ❌ |
| `TIMEOUT` | the checker exceeded 300s | ❌ |

`COVERAGE_GAP` is the verdict that closes `p36`: with a check body gutted to `return None`,
the control aimed at that check can no longer produce its `FAIL:` line, so the harness reports
the gap and fails the run even though the count guard is satisfied.

Comparison is **exact**, not `in` — substring matching is how this repo twice shipped a silent
pass (the `page_url_unused` and root-shim substring checks). To keep exact expectations
portable, `normalize_paths()` masks the throwaway copy root as `<copy>` and the system temp
root as `<tmp>` on **both** sides of the comparison; a checker's `FAIL:` detail may name the
file it read, and that path differs per run and between macOS and CI's Linux.

## The harness's own controls

Run on every invocation, in process, against a synthetic mini-repo whose fake checker can be
broken in exactly the ways the harness must recognize:

| id | control |
|---|---|
| `s1` | a mutation that breaks a check is reported `FIRED` |
| `s2` | a mutation that changes nothing observable is a `COVERAGE_GAP` |
| `s3` | a different check refusing first is reported `MASKED` |
| `s4` | an anchor that no longer exists is reported `ROTTEN_ANCHOR` |
| `s5` | a contract-preserving edit that goes red is a `FALSE_POSITIVE` |
| `s6` | an empty table is refused, not passed vacuously |
| `s7` | a checker with no controls is refused |
| `s8` | a deleted control registration is caught by the count guard |
| `s9` | a narrowed `--checker` selection is never validated against the whole-table count guard |

`EXPECTED_SELF_TESTS` and `EXPECTED_CONTROLS` are count guards (deleting either fails the run).
`table_problems()` additionally refuses an empty table, a checker with no controls, and a
non-positive `EXPECTED_CONTROLS` — a run that checks nothing must not print `PASS`.

**Both count guards are floors, not proofs**, and the design says so out loud because that
distinction is the whole point of issue #43. What actually proves a guard is the control that
must turn it red.

## The control table

39 controls over 13 checkers (36 from the original table + 3 D4 `b1`–`b3` controls added with
the legacy-batch-capture unit). `scripts/run_negative_controls.py --list` prints the same table
with the exact anchor and replacement strings.

| checker | id | mutation | asserted first `FAIL:` |
|---|---|---|---|
| `validate_quotes.py` | c1 | row 344's primary key rekeyed onto an existing id | `duplicate ids: ['1']` |
| | c2 | `sources.csv` renames the id row 344 cites | `quotes reference source_id not present in sources.csv: ['344']` |
| | c3 | row 1's `item_type` leaves the controlled vocabulary | `rows with invalid item_type: ['1']` |
| | c4 | the near-duplicate score reverts to **one** directional ratio (#31) | `near-duplicate detection is row-order dependent: …` |
| | c5 | the imported locator rule drifts (`citation_specificity` → always generic) | `citation rule drift: citation_specificity('Gita 2.47') is 'generic', …` |
| | c6 | the sweep narrows back to per-`tradition` groups (#34's reversion) | `the near-duplicate sweep is not corpus-wide: pairs/numbers only in the corpus-wide scan [(39, 53, …)]` |
| `check_program_contracts.py` | pc1 | S2's wording claim demoted to `unverifiable` | `S2: record research_state 'verified' disagrees with the aggregate of its claims ('unverifiable')` |
| | pc2 | S3's walkthrough names an undefined transition (`T-R99`) | `S3: transition T-R99 (step 4) is not in the STATE_MODEL table` |
| | pc3 | the fixture template loses the required `capture_id` | `CANDIDATE_ENVELOPE.md required fields and the fixture template disagree: doc-only=['capture_id'] …` |
| `validate_homepage_preview_export.py` | h1 | an exported item's text drifts from `quotes.csv` | `items[0]: text does not match quotes.csv id 3` |
| | h2 | exact scripture re-typed as a paraphrase | `items[0]: paraphrase may not be emitted as exact scripture` |
| `check_pages_contract.py` | p1 | upload action major regresses to v3 (#23's mechanism) | `the upload action major excludes top-level hidden files -- …@3 is below the minimum verified major 4 …` |
| | p2 | the artifact is rooted at `browser/` | `the uploaded path is the repo root ('.') -- the upload path is "'browser/'", not '.' …` |
| | p3 | `include-hidden-files: true` | `the upload step does not include hidden files -- include-hidden-files is 'true' …` |
| | p4 | `app.js` fetch repointed, old path kept in a `//` comment | `browser/app.js still fetches ../quotes.csv and ../sources.csv -- …` |
| `smoke_quote_browser.py` | sm1 | `matchesSearch()` stops narrowing | `search 'Dhammapada': page never showed 29 quotes within 15000ms (filtered-count='324')` |
| | sm2 | the empty state loses its message | `empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada'): empty-state text was …` |
| `check_garden_store.py` | g1 | the capture-immutability UPDATE trigger stops aborting | `captures accepted UPDATE: captures are not immutable` |
| | g2 | the `research_state` CHECK constraint is dropped (W1.1's review finding) | `the SQL layer accepted research_state = 'maybe' (outside STATE_MODEL.md)` |
| | g3 | a migration id is renamed | `create-from-empty applied migration ['0001_create_core_v2', …] into an empty directory` |
| `check_garden_envelope.py` | e1 | the serializer loses `sort_keys` determinism | `key insertion order cannot change the serialized bytes (sort_keys is load-bearing)` |
| | e2 | rule 1 stops checking the intake schema version (W1.2's review finding) | `fixture 'wrong-intake-schema-version' reports exactly rule-1 -- reported []` |
| | e3 | rule 2 stops refusing an empty `captured_text` | `fixture 'empty-captured-text' reports exactly rule-2 -- reported []` |
| `check_garden_submit.py` | t1 | the capture is trimmed instead of stored byte-for-byte | `captured_text is byte-identical to the submitted file … -- 75 vs 78 bytes` |
| | t2 | the no-normalization-without-a-note refusal is dropped | `--candidate-text differing with no note is refused (exit 0, RESULT: FAIL)` |
| `check_garden_normalize.py` | n1 | similarity collapses to one directional ratio | `the similarity of a pair is symmetric (the same number reaches both candidates' hints)` |
| | n2 | a shared generic label counts as a specific citation (ruling 2) | `the legacy heuristic flags rows 319 ~ 331 on the shared label 'Oral Tradition' …` |
| | n3 | the hint rebuild accumulates (the `DELETE` is lost) | `rebuilding every hint exports byte-identical text (derived, deterministic, not appended)` |
| `check_garden_review.py` | r1 | acceptance skips the required T-P1 corpus follow-on | `accept: cand-t01 recorded exactly ['T-C1', 'T-P1'] -- ['T-C1']` |
| | r2 | `curate`'s **own** required-reason guard is disabled | `the refusal for an empty reason came from curate's OWN guard …` |
| | r3 | a curation action writes research state (invariant 5) | `accept: cand-t01 research_state stayed not_started -- in_research` |
| `check_garden_e2e.py` | x1 | the withdrawal path bypasses its state write | `the reversal strands no dimension: curation=rejected, corpus=candidate_only -- … corpus=eligible` |
| | x2 | the decision log stops being append-only | `decisions accepted UPDATE: the log is not append-only` |
| `check_garden_ledger.py` | l1 | the re-adjudication guard is disabled | `a duplicate mark is refused by the explicit re-adjudication guard -- … UNIQUE constraint failed …` |
| | l2 | the ledger row is written without its research audit row (D3 §2) | `mark appends one research audit row (T-R6 from_state derived from the model) -- []` |
| | l3 | `reopen` no longer requires the row to be in the ledger | `reopen on a missing row was accepted` |

The table is deliberately **not** a copy of each handoff's prose table: the mutation had to be
re-derived from the code and re-run, and several of the historical controls are not expressible
in this harness's vocabulary (see limits). What was ported is the control, not the wording.

## Adding a control

1. Pick a mutation of the **artifact the checker guards** — not the checker itself. A control
   whose mutation is inside the checker proves only that the checker can be made to fail.
2. Find a substring that occurs **exactly once** in the target file
   (`python3 -c "print(open('f').read().count(anchor))"`), and a replacement that models a real
   regression.
3. In a throwaway copy (`rsync -a --exclude .git --exclude .venv`), apply it, run the checker,
   and copy the **first** `FAIL:` line verbatim — do not tidy it.
4. Add the `Mutation(...)`, bump `EXPECTED_CONTROLS`, and run
   `python3 scripts/run_negative_controls.py --checker <script>` — a control that does not
   reproduce shows up immediately as `MASKED`/`COVERAGE_GAP`, naming the line it saw instead.
5. If the control needs a new mutation *kind* (a delete, a multi-file edit), add that kind to
   the harness **and** a self-test that proves the harness can judge it.

## CI

`browser-smoke.yml` runs the full table as its own step, after the acceptance suites. The
browsers' controls run there because that job installs Chromium; when the capability is
missing the checker is reported **SKIPPED** (never PASS) and, with `CI` set or `--require-all`,
a skip is an error rather than a quiet reduction in coverage.

Measured cost: **~4 minutes warm on the developer Mac** — dominated by `validate_quotes.py`
(~21s/run × 6) and `check_garden_e2e.py` (~22s/run × 3) — and **~6.5–7 minutes in CI** on a
2-core runner (the step was 6m58s on PR #46 and 6m24s on the post-merge `main` run). The `smoke`
job's budget was raised from 15 to 30 minutes for this step, deliberately: the alternative —
checking the table only for anchor rot — is not the claim issue #43 filed. `--checker` narrows a
local run; CI does not narrow.

## Limits, stated rather than papered over

- **A control is one exact-string substitution.** A regression needing a deleted file, a
  renamed path, or a multi-file edit is outside the vocabulary. The self-tests are where a new
  mutation kind must first be proven judgeable.
- **The table proves modelled breaks are detected, never that a guard is complete.** Its worth
  is exactly the quality of the mutations a human wrote; an unmodelled bypass still passes.
- **`EXPECTED_CONTROLS` is a floor.** It catches a deleted registration, exactly as
  `EXPECTED_CHECKS` catches a deleted check — and, exactly as there, it cannot see a gutted
  body. Here that case is caught by the `COVERAGE_GAP` verdict instead, which is the fix.
- **One locally-measured control is deliberately excluded.** Dropping `overflow-wrap: anywhere`
  from `browser/style.css` makes the smoke test fail at 320px, but the `FAIL:` line embeds
  rendered geometry (`document scrollWidth=355 > clientWidth=320 … {'right': 448, 'tag': 'DD'}`)
  which depends on the runner's font stack. Committing it with an exact expectation would be a
  CI-only false alarm, and committing it with a loose match would weaken every other control.
- **Coverage gaps the table itself does not close** (measured while authoring it, filed rather
  than fixed here — each is a fixture/check change to an existing suite): the captures-UPDATE
  trigger's `RAISE` *message* text is unguarded; `garden_normalize._comparison_view()`'s
  documented case-folding has no case-differing fixture;
  `check_garden_review.py` never inspects a decision row's `action` vocabulary;
  `check_garden_e2e.py` asserts the live `corpus_state` but not the T-P7 audit row's recorded
  `to_state`; and D3's "do not widen the `quotes.csv` enum" ruling has no falsifier anywhere.
  **Filed as issue #45; all five closed 2026-09-14** — see
  `GARDEN_CHECKER_COVERAGE_GAPS_HANDOFF.md`. This description of the gaps (and this file's list
  of them) is left as the historical record of what the authoring pass found; none of the five
  mutations above still passes silently.
