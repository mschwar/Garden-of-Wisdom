# Work Queue

Living document — update it as items are picked up or closed, don't just append.

## Open — data curation

- [ ] Resolve the 14 unresolved `source_id` links (`docs/data/DATA_QUALITY_REPORT.md`). Mostly
      needs new `sources.csv` rows for small oral traditions (Shawnee, Cherokee, Nez Perce,
      Lakota, Tewa, Zuni, Ethiopian, Nguni) plus Nahua works and the Mahabharata.
- [ ] Human review of the 45 near-duplicate candidate pairs to decide: distinct variant
      translations (keep both) vs. accidental duplication (merge/remove). Note the
      generic-`"Oral Tradition"`-label false-positive caveat before trusting the list at face
      value.
- [ ] Resolve the 4 rows with literal `_` placeholder glyphs (IDs 1, 16, 314, 320) — needs a
      human who knows the correct diacritic/modifier character, not a guess.
- [ ] Review and reclassify the remaining `item_type = unknown` rows (20 after G4 reclassified
      donor ids 3 and 15 to `excerpt`). Frontier review noted ~10 Roman-numeral Gleanings
      citations that the digit-or-colon heuristic missed, plus paraphrase-shaped rows 31 and
      267 that were never typed `paraphrase`.
- [ ] Decide whether the 27-value tradition list should be formally documented as the new
      controlled list (this retrofit's README treats it as such) or trimmed/normalized further.

## Open — infra

- [ ] Consider adding a duplicate/near-duplicate review view to the browser if the curation
      pass above finds the CLI report insufficient (see `docs/architecture/QUOTE_BROWSER.md`).
- [ ] Guard the Pages deploy contract: `.github/workflows/pages.yml` must keep
      `path: '.'` (repo root) and Pages "Source" must stay **GitHub Actions**. Rooting the
      artifact at `browser/` breaks the `../quotes.csv` / `../sources.csv` fetches and the
      live page silently renders 0 quotes. Live checks are listed in `docs/RUNBOOK.md`.
      (`scripts/smoke_quote_browser.py` now fails loudly on the same mistake locally — but only
      when someone runs it against a mis-rooted tree; it cannot see the live Pages setting.)
- [ ] **Move CI off the deprecated Node 20 action majors.** GitHub annotated the `main` smoke run
      (`actions/checkout@v4`, `actions/setup-python@v5` still target Node 20 and were forced onto
      Node 24); the Pages actions in `pages.yml` are older majors too. CI is green today, so this
      is future-proofing — but bumping the Pages actions is a deploy-path change and must be
      re-verified live the way the 2026-09-11 acceptance was. Filed as
      [#19](https://github.com/mschwar/Garden-of-Wisdom/issues/19).
- [ ] **Card view has no empty state** (found while adding filter coverage, out of scope there).
      With a search/filter combination that matches nothing, card view renders an empty
      `#results` — 0 children, no message — so the page is just a blank area under a header
      reading "0 shown", while table view explains itself with `td.empty-state`
      ("No matching quotes. Adjust the filters or search."). Measured 2026-09-12:
      `resultChildren=0, resultsText=''`. Needs a browser behaviour change (and a matching
      smoke-test assertion), so it is its own unit, not a test-only edit. Filed as
      [#17](https://github.com/mschwar/Garden-of-Wisdom/issues/17).

## Open — corpus program (W0 landed 2026-09-12; Gate A accepted 2026-09-12; W1 NOT authorized)

- [ ] **W1 is decomposed but not authorized.** Six bounded units (storage decision → envelope
      contract → CLI submission → normalization/duplicate hints → curation review + audit →
      Gate B evidence pack) are specified in `docs/program/W1_DECOMPOSITION.md`. Gate A is now
      accepted (`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`); do not start any W1 unit
      without a separate, explicit operator authorization of **W1.1 only**. See
      `docs/program/W0_GATE_REPORT.md`.

## Open — debt and open questions discovered during W0 (specs only, not scheduled)

Filed from `docs/program/W0_GATE_REPORT.md` §Unresolved and
`docs/program/CLASSIFICATION_AND_FACETS.md`. None of these is authorized work.

- [ ] **D2 — `unverifiable` is not representable in `quotes.csv`.** The 3-valued
      `verification_status` maps every unfinished research state to `unverified`, so a record
      proven unverifiable is indistinguishable from a never-checked row. Issue #5 (Garden id
      30) is the live instance. Needs a migration unit; do not widen the enum as a side effect
      of other work.
- [ ] **D3 — no row-level verification evidence store.** The four `verified` rows carry their
      evidence only in `exports/bahai-homepage-preview/v1/` and `docs/DECISIONS.md`. Adding
      evidence fields is W2/W3 work; until then, `verified` in the CSV is a pointer to the
      export.
- [ ] **D4 — capture provenance policy for the 324 legacy rows.** They have no capture record
      and none is reconstructable (`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md`). Open
      question: does `legacy-import` ever get a synthetic capture record, or does the frozen
      archive stay the only provenance? Human decision.
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

## Explicitly NOT started (do not start without human sign-off)

- **The entire corpus program past W0.** W0 (docs/program) is doctrine only. No W1 unit, no
  datastore, no intake surface, no discovery adapter, and no canonical promotion path may be
  started without frontier acceptance of Gate A and explicit authorization of W1.1.
- Wiring the homepage preview export into `bahai-homepage` (H2B-B). Garden STOP is after the
  verified export; the consume path is `exports/bahai-homepage-preview/v1/collection.json`.
- Any other `bahai-homepage` implementation work.
- Bulk quote verification beyond the approved donor set.
- Deferred donor sets B (citation-shape diversity) and C (Hidden Words collision test) from
  the 2026-09-11 donor-set decision.

## Closed — 2026-09-12 W0 (corpus program doctrine)

- [x] W0 doctrine + contracts landed under `docs/program/` — all 12 required outputs (10 docs
      plus decision-log and queue entries), a planning fixture
      (`docs/program/fixtures/w0_scenarios.json`, 12 walkthroughs) and a deterministic doctrine
      checker (`scripts/check_program_contracts.py`, 20 negative controls recorded).
      Gate A evidence: `docs/program/W0_GATE_REPORT.md`. **W1 NOT STARTED.**
- [x] Gate A frontier review: **accepted**, 2026-09-12
      (`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`). Fixed three evidence-hygiene defects
      in the Gate A package (stale scenario/transition counts, undercounted decision-log
      entries) found during review; no doctrine content changed. **W1.1 is still not
      authorized** — that remains a separate, explicit operator decision.

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
