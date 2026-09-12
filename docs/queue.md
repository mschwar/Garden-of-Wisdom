# Work Queue

Living document — update it as items are picked up or closed, don't just append.

## Open — data curation

- [ ] **ADOPTED SCOPE (D7) — close the 14 unresolved `source_id` links by adding `sources.csv` rows**
      for the identifiable works (Mahabharata 5.1517, Huehuetlahtolli, Florentine Codex) plus
      per-tradition oral rows for the small oral traditions (Shawnee, Cherokee, Nez Perce, Lakota,
      Tewa, Zuni, Ethiopian, Nguni), then re-link `source_id`. Quote text untouched; validator
      before and after. **Sequence: runs AFTER W1** — this writes `sources.csv`, which is
      READ-ONLY for the whole of W1 (`docs/program/W1_DECOMPOSITION.md` §Cross-unit rules). Not
      done.
- [ ] **ADOPTED SCOPE (D6) — curate the ~22 near-duplicate pairs that share a *specific citation*;
      explicitly SKIP the ~23 pairs that are the validator's generic-`source_ref` false positive**
      (e.g. unrelated rows both labelled `"Oral Tradition"`). Keep both rows for legitimate variant
      translations; only merge/remove accidental duplication. **Sequence: runs AFTER W1** — this
      writes `quotes.csv`, which is READ-ONLY for the whole of W1. The 45-pair list and its caveat
      are in `docs/data/DATA_QUALITY_REPORT.md`. Not done.
- [ ] Resolve the 4 rows with literal `_` placeholder glyphs (IDs 1, 16, 314, 320) — needs a
      human who knows the correct diacritic/modifier character, not a guess. **D8 (2026-09-12)
      leaves these 4 rows for the operator** — guessing stays forbidden.
- [ ] Review and reclassify the remaining `item_type = unknown` rows (20 after G4 reclassified
      donor ids 3 and 15 to `excerpt`). Frontier review noted ~10 Roman-numeral Gleanings
      citations that the digit-or-colon heuristic missed, plus paraphrase-shaped rows 31 and
      267 that were never typed `paraphrase`. **D8 (2026-09-12) adopts the cheap deterministic
      subset (~10 Roman-numeral Gleanings rows + rows 31/267), sequenced AFTER W1 (writes
      `quotes.csv`); `item_type` is not widened.**
- [ ] Decide whether the 27-value tradition list should be formally documented as the new
      controlled list (this retrofit's README treats it as such) or trimmed/normalized further.
      **D8 (2026-09-12) decides: document the 27-value list as the controlled list.**

## Open — infra

- [ ] Consider adding a duplicate/near-duplicate review view to the browser if the curation
      pass above finds the CLI report insufficient (see `docs/architecture/QUOTE_BROWSER.md`).
- [ ] Guard the Pages deploy contract: `.github/workflows/pages.yml` must keep
      `path: '.'` (repo root) and Pages "Source" must stay **GitHub Actions**. Rooting the
      artifact at `browser/` breaks the `../quotes.csv` / `../sources.csv` fetches and the
      live page silently renders 0 quotes. Live checks are listed in `docs/RUNBOOK.md`.
      (`scripts/smoke_quote_browser.py` now fails loudly on the same mistake locally — but only
      when someone runs it against a mis-rooted tree; it cannot see the live Pages setting.)
- [ ] **OPEN — Pages artifact publishes top-level dotfiles.** Issue
      [#23](https://github.com/mschwar/Garden-of-Wisdom/issues/23): `/.gitignore` is live and
      returns **200**, even though the comment in `.github/workflows/pages.yml` claims top-level
      dotfiles are excluded. **Not a regression from #19** — the pre-bump artifact from run
      34713537851 already contained `./.gitignore` (the only diff between the two artifacts is the
      two new handoff files). Only three dotfiles are tracked repo-wide:
      `.github/workflows/browser-smoke.yml` and `.github/workflows/pages.yml` (both correctly
      **404** — they are not at the artifact root) and `.gitignore` (**published**). The acceptance
      checklist in `docs/RUNBOOK.md` only probes `/.git/config`, which is why this was missed.
      Candidate mechanism — the action's `--exclude=.[^/]*` pattern cannot match the `./`-prefixed
      names this tar invocation emits — is a **hypothesis to confirm on the runner, not a proven
      cause.** Filed rather than fixed (the fix is a deploy-path change needing its own live
      re-verification).

## Open — corpus program (W0 landed 2026-09-12; Gate A accepted 2026-09-12; W1 AUTHORIZED IN FULL 2026-09-12 — IN PROGRESS)

- [ ] **W1 — IN PROGRESS. Authorized in full 2026-09-12 (decision D1).** Six bounded units are
      specified in `docs/program/W1_DECOMPOSITION.md`:
      **W1.1** storage decision + minimal schema ✅ **DONE** · **W1.2** candidate-envelope contract
      + validator · **W1.3** manual capture/submission CLI · **W1.4** normalization + duplicate
      hints · **W1.5** curation review + decisions + audit history · **W1.6** end-to-end test pack +
      Gate B evidence packet.
      **Strict order:** W1.1 → W1.2 → W1.3 → W1.4 → W1.5 → W1.6. W1.4 may overlap W1.3; every other
      dependency is strict.
      **Per-unit contract (authorization of the wave does NOT merge the per-unit gates):** each unit
      gets its own isolated branch/worktree → complete bounded implementation → **one PR** →
      **independent/foreign QA** → resolve findings → merge → report, then **STOP before the next
      unit**.
      **Stop point:** W1 ends at the Gate B packet. **W2 is not started.** See
      `docs/program/W0_GATE_REPORT.md`. (This entry supersedes the earlier "W1 is decomposed but not
      authorized" item.)
- [x] **W1.1 — storage decision + minimal schema. DONE 2026-09-12** (PR
      [#25](https://github.com/mschwar/Garden-of-Wisdom/pull/25), merge `c90def3`). SQLite store of
      record (stdlib `sqlite3`) + deterministic text mirror: `scripts/garden_store.py`, with
      `scripts/check_garden_store.py` as the acceptance run (**59** checks) and
      `docs/program/W1_1_STORAGE_AND_SCHEMA.md` for the comparison/DDL. Round-trips byte-identically,
      the migration is idempotent, capture immutability and decision-log append-only are enforced by
      triggers rather than documented, and the four state vocabularies are re-parsed from
      `docs/program/STATE_MODEL.md`. Decision recorded in `docs/DECISIONS.md` ("D2 executed (W1.1)").
      Independent review found and fixed one real coverage gap — the suite guarded only one of the
      four state columns' `CHECK` constraints, so removing the `research_state` `CHECK` left the run
      green; it now loops over all four, with the review control recorded (control `f`) in
      `GARDEN_W1_1_HANDOFF.md`. `quotes.csv`/`sources.csv` byte-identical (read-only rule held). Also
      recorded there: six doctrine ambiguities W1.5/W3 must resolve (notably `work_state` having two
      subjects, and no sanctioned capture-deletion path). **Next: W1.2.**

## Open — debt and open questions discovered during W0 (specs only, not scheduled)

Filed from `docs/program/W0_GATE_REPORT.md` §Unresolved and
`docs/program/CLASSIFICATION_AND_FACETS.md`. None of these is authorized work.

> **Namespace note (2026-09-12):** the `D1`–`D8` labels below are the **W0 debt IDs** from
> `docs/program/W0_GATE_REPORT.md` and are **not** the same namespace as the 2026-09-12 decision
> IDs `D1`–`D10`. When referring to a *decision*, cite its dated entry in `docs/DECISIONS.md` by
> title, never by a bare `D<n>`.

- [ ] **D2 — `unverifiable` is not representable in `quotes.csv`.** The 3-valued
      `verification_status` maps every unfinished research state to `unverified`, so a record
      proven unverifiable is indistinguishable from a never-checked row. Issue #5 (Garden id
      30) is the live instance. **Decided 2026-09-12 (decision D3):** represented in a side-car
      ledger keyed by legacy row id, after W1.1 — see the authorized section above. Do not widen
      the enum as a side effect of other work.
- [ ] **D3 — no row-level verification evidence store.** The four `verified` rows carry their
      evidence only in `exports/bahai-homepage-preview/v1/` and `docs/DECISIONS.md`. Adding
      evidence fields is W2/W3 work; until then, `verified` in the CSV is a pointer to the
      export.
- [ ] **D4 — capture provenance policy for the 324 legacy rows.** They have no capture record
      and none is reconstructable (`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md`). **Decided
      2026-09-12 (decision D4):** ONE batch capture record for the 2026-09-11 rehabilitation
      import, explicitly marked as such and noting the encounter context is unknown — see the
      authorized section above. Not one synthetic capture per row.
- [ ] **D5 — `item_type` mixes text shape with provenance shape.** `full-passage`/`excerpt`/
      `paraphrase` are shape; `oral-attribution` is not a text relation. The split is W3 work
      (`docs/program/CLASSIFICATION_AND_FACETS.md`); do not widen the enum meanwhile.
- [ ] **D7 — `verification_status` (Garden) vs `verification_state` (H2B) naming** (issue #7).
      Now also entangled with the W0 projection rule; resolve before more export/validator code
      hardens either spelling.
- [ ] **Q1 — should `tradition` become multi-valued?** Some labels overlap in practice.
- [ ] **Q2 — is `domain` genuinely multi-valued, or effectively single per record?**
- [ ] **Q3 — how is a non-text "source" represented?** (e.g. id 344 `Modern Mayan Greeting`,
      which is a greeting rather than a work.)
- [ ] **Q4 — does `culture` add anything beyond `tradition` + `source_type` on this corpus?**
- [ ] **Q5 — does `shape` replace `item_type`, or does `item_type` stay its projection?**
- [ ] **Q6 — should period/era be recorded at all**, given how many oral records have no
      datable origin?

## Open — candidate units found during G4 (not scheduled; specs only)

Filed as GitHub issues. Do not start without a named contract and owner sign-off.

- [ ] Audit remaining Bahá’í rows for the id-12 / id-26 class of error: wrong author, or
      right sentence attributed to the wrong work/date. G4 only touched the approved donor
      set. [#6](https://github.com/mschwar/Garden-of-Wisdom/issues/6)
- [ ] Resolve unverifiable Garden id 30 (`Prayer is the key of the doors of mercy.` /
      `Paris Talks, Dec 2 1911`). Rejected from the v1 export; still sitting `unverified` in
      `quotes.csv`. [#5](https://github.com/mschwar/Garden-of-Wisdom/issues/5)
- [ ] Add an optional `source_url` column to `quotes.csv` once more rows are verified. v1
      records URLs only on the export. [#4](https://github.com/mschwar/Garden-of-Wisdom/issues/4)
- [ ] Reconcile `verification_status` (Garden) vs `verification_state` (H2B) before more
      export/validator code hardens either spelling. H2B D27 already flagged this.
      [#7](https://github.com/mschwar/Garden-of-Wisdom/issues/7)

## Closed — 2026-09-12 card-view empty state

- [x] Issue [#17](https://github.com/mschwar/Garden-of-Wisdom/issues/17) — card view now renders an
      empty state when the filtered set is empty. The "No matching quotes. Adjust the filters or
      search." string moved into one constant in `browser/app.js` (`EMPTY_STATE_MESSAGE`) used by
      both views, so card (`#results .empty-state`) and table (`td.empty-state`) cannot drift; the
      card-view message spans the grid and adds no overflow at 320px. The
      smoke test's `check_empty_state` now asserts the card-view element exists *and* carries the
      table view's exact text (views compared with each other), taking
      `scripts/smoke_quote_browser.py` from 32 to **33** checks; two negative controls in
      `GARDEN_CARD_EMPTY_STATE_HANDOFF.md`. PR
      [#21](https://github.com/mschwar/Garden-of-Wisdom/pull/21). No data changed.

## Closed — 2026-09-12 CI action majors bumped off deprecated Node 20

- [x] Issue [#19](https://github.com/mschwar/Garden-of-Wisdom/issues/19) — all five action majors
      bumped in both workflows (`actions/checkout` v4→v7, `actions/setup-python` v5→v7,
      `actions/configure-pages` v5→v6, `actions/upload-pages-artifact` v3→v5,
      `actions/deploy-pages` v4→v5). PR
      [#22](https://github.com/mschwar/Garden-of-Wisdom/pull/22) check run
      [34715295423](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715295423)
      **success** with the Node 20 deprecation annotation **gone**; on `main` after merge, smoke run
      [34715362562](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715362562)
      **success** and Pages deploy run
      [34715362601](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715362601)
      **success**; live acceptance passed (`/`, `/browser/index.html`, `/quotes.csv`,
      `/sources.csv` all **200**; live CSV `sha256`s identical to the repo). `path: '.'`, the pages
      concurrency group, the `github-pages` environment and the `refs/heads/main` guard are all
      unchanged. **The authoring child timed out before writing its handoff, so the parent verified
      the unit and completed it** — which is why `GARDEN_CI_ACTION_BUMPS_HANDOFF.md` is
      parent-authored. The verification surfaced a separate pre-existing defect, filed as
      [#23](https://github.com/mschwar/Garden-of-Wisdom/issues/23) (see the open infra section
      above).

## Closed — 2026-09-12 browser smoke test: filter coverage

- [x] **Issue [#13](https://github.com/mschwar/Garden-of-Wisdom/issues/13) — extend the smoke test
      to the six filters, the "Issues only" toggle, a combined interaction and the empty-result
      state.** Test coverage only; no browser behaviour changed. `scripts/smoke_quote_browser.py`
      grew from 22 to **32** checks: the six dropdowns' option sets are compared with the distinct
      values in `quotes.csv`, one narrowing value per dropdown is selected and its rendered card
      count asserted against Python's count for the same predicate, "Issues only" is asserted to
      narrow to exactly the rows with a non-empty `detectIssues()` (every card badged) *and* to
      drop rows, one filter+search+sort combination is asserted on both count and length ordering
      in table view, and a no-match combination is asserted to render the table's `td.empty-state`
      row with zero cards. Every value and combination the test uses is searched for in the data,
      and a check that would otherwise pass vacuously (a filter value that narrows nothing, a
      toggle that drops nothing) now fails loudly. Seven new negative controls, one per broken
      path, plus three showing the vacuity guards firing — `GARDEN_FILTER_SMOKE_COVERAGE_HANDOFF.md`.
      Out of scope, filed as [#17](https://github.com/mschwar/Garden-of-Wisdom/issues/17): card
      view renders no empty state at zero matches (see the infra queue above).

## Closed — 2026-09-12 quote-browser smoke test + responsiveness

- [x] **Automated browser smoke test** (`scripts/smoke_quote_browser.py` +
      `.github/workflows/browser-smoke.yml`, which runs it on every PR and push to `main`).
      Headless Chromium via Playwright (test-only dependency, `requirements-dev.txt`); every
      expected count is recomputed from `quotes.csv` rather than hard-coded. 22 checks at the
      time (the test has since grown to 32 — see the filter-coverage close-out above): static
      layout (both CSVs byte-identical at the paths the page fetches), 324/324 header + card
      counts, search narrowing to the rows that contain the term, length sort ordering both
      directions, `aria-sort` on header click, table row count, copy button round-trip through
      the clipboard, no horizontal overflow at 320/375/768px in both views, and zero console /
      page errors / failed requests. Seven negative controls recorded in
      `GARDEN_BROWSER_SMOKE_HANDOFF.md` (each
      re-breaks one behaviour and turns the run red with `RESULT: FAIL`, no traceback). Closes
      the D8 debt from `docs/program/W0_GATE_REPORT.md`. Local run instructions:
      `docs/RUNBOOK.md` §"Smoke-test the browser".
- [x] **Horizontal overflow at phone widths** (flagged by foreign QA on PR #9). Root cause was
      mis-stated in this queue: it was *not* `min-width: 140px` on the selects. Measured in
      Chromium at 375px, the `<select>` intrinsic width follows its longest `<option>`, so
      `#filter-source` (longest `source_ref` = 61 chars) rendered **390px** wide — and `Author`
      276px — inside a 341px container, pushing the document to 421px. Fixed by allowing the
      control row's labels to shrink (`min-width: 0; max-width: 100%`) and capping the selects
      at `max-width: 100%`. The new test then found a **second, independent** cause the PR #9
      note never mentioned: `.tags` is a comma-joined list with no spaces
      (`love,neighbor,goldenrule`), i.e. one ~280px unbreakable token that escaped the card and
      overflowed at 320px; fixed with `overflow-wrap: anywhere` and a wrapping `.meta-row`.
      Reasoning: `docs/architecture/QUOTE_BROWSER.md` §Responsiveness.
- [x] **Stray 2px bordered box under the cards** — a third defect the new test surfaced: in card
      view `#quote-table` was hidden but its wrapper `#table-wrap` (which owns the border and
      scroll container) was not, so an empty 2px-tall bordered box sat at the end of the page on
      every load. Fixed in `browser/app.js` `render()`; the smoke test asserts the switch hides
      and shows both containers.

## Closed — 2026-09-11 Pages deploy

- [x] Deploy the quote browser to GitHub Pages, rooted at the repo root so the relative
      `../quotes.csv` / `../sources.csv` fetches keep resolving. Workflow:
      `.github/workflows/pages.yml` (`configure-pages` → `upload-pages-artifact` with
      `path: '.'` → `deploy-pages`; `pages` concurrency, `github-pages` environment,
      deploy job guarded to `refs/heads/main`). Pages enabled out of band with
      `gh api -X POST repos/mschwar/Garden-of-Wisdom/pages -f build_type=workflow`.
      Root `index.html` added as a redirect shim. PR #10.
- [x] Acceptance verified 2026-09-11 on the merged commit `6da1e9f` (workflow run
      [34676486409](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34676486409),
      conclusion `success`): `/`, `/browser/index.html`, `/quotes.csv`, `/sources.csv` all
      **200**; live `quotes.csv`/`sources.csv` byte-identical to the repo (`sha256` match);
      live headless Chrome renders `324 quotes, 324 shown`, table view 324 rows, 0 console
      errors; `/` redirects to `browser/index.html`; `/.git/config` and
      `/.github/workflows/pages.yml` return 404 (not published).
      Live: https://mschwar.github.io/Garden-of-Wisdom/browser/index.html

## Authorized — queued (2026-09-12 decisions; not yet started)

- [ ] **D9 — H2B-B: open the `bahai-homepage` consume lane against the v1 export.** Authorized
      2026-09-12. The Garden side is a **lane authorization only**; the work happens in
      `bahai-homepage` against `exports/bahai-homepage-preview/v1/collection.json` (4 verified
      rows), not by widening the donor set first. Expected to surface issue #4 (`source_url`) and
      the D5 `verification_status` / `verification_state` contract question. Garden's frozen data is
      untouched by this lane. This supersedes the earlier "do not start H2B-B" bullet.
- [ ] **D3 — `unverifiable` side-car ledger (after W1.1).** Authorized 2026-09-12: represent
      `unverifiable` in a side-car ledger keyed by legacy row id, NOT by widening the 3-valued
      `quotes.csv` enum. **Sequence: after W1.1 exists**, so there is one store rather than two.
      Issue #5 / Garden id 30 is the live instance. (Resolves the open question in the debt section
      below.)
- [ ] **D4 — ONE batch capture record for the 324 legacy rows.** Authorized 2026-09-12: a single
      batch capture record for the 2026-09-11 rehabilitation import, explicitly marked as such and
      noting the encounter context is unknown — not one synthetic capture per row. (Resolves the
      "human decision" open question in the debt section below.)

## Explicitly NOT started (do not start without human sign-off)

- **The entire corpus program past W1.** W0 (`docs/program`) is doctrine only; **W1 is now
  authorized in full** (2026-09-12, decision D1) and in progress. Still **NOT started**: W2 and
  everything after it, any discovery adapter, and any canonical promotion path (W3). The
  authorization of W1 does not authorize anything past the Gate B packet.
- Any `bahai-homepage` implementation work **other than** the D9 consume lane against the v1 export
  (see the authorized section below).
- Bulk quote verification beyond the approved donor set.
- Deferred donor sets B (citation-shape diversity) and C (Hidden Words collision test) from
  the 2026-09-11 donor-set decision.

## Closed — 2026-09-12 W0 (corpus program doctrine)

- [x] W0 doctrine + contracts landed under `docs/program/` — all 12 required outputs (10 docs
      plus decision-log and queue entries), a planning fixture
      (`docs/program/fixtures/w0_scenarios.json`, 12 walkthroughs) and a deterministic doctrine
      checker (`scripts/check_program_contracts.py`, 20 negative controls recorded).
      Gate A evidence: `docs/program/W0_GATE_REPORT.md`. **W1 was NOT started at W0's close**
      (since superseded — W1 authorized in full 2026-09-12; see the corpus-program section above).
- [x] Gate A frontier review: **accepted**, 2026-09-12
      (`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`). Fixed three evidence-hygiene defects
      in the Gate A package (stale scenario/transition counts, undercounted decision-log
      entries) found during review; no doctrine content changed. **W1.1 was still not
      authorized at that point** — since authorized in full 2026-09-12 (decision D1), which
      remains a separate, explicit operator decision from Gate A acceptance.

## Closed — 2026-09-11 G4

- [x] Prompt 02 / G4 verified homepage-preview export — ids 3, 12, 15, 26 accepted; 30
      rejected. Artifacts under `exports/bahai-homepage-preview/v1/`. Handoff:
      `GARDEN_HOMEPAGE_PREVIEW_EXPORT_HANDOFF.md`.

## Closed — 2026-09-11 Phase 0

- [x] G0 archaeology — `docs/audit/2026-09-11/FINDINGS.md`
- [x] G1 agent-first retrofit docs (this file and its siblings)
- [x] G2 data rehabilitation — UTF-8 canonical CSVs, `item_type`/`verification_status`/
      `source_id`/`has_unresolved_glyph` columns, archived originals, `.DS_Store` untracked
- [x] G3 static quote browser
- [x] Phase 0 frontier review — accept with documented debt
      (`docs/audit/2026-09-11/PHASE0_FRONTIER_REVIEW.md`)
