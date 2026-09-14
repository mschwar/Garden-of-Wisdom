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
- [ ] **ADOPTED SCOPE (D6) — curate the near-duplicate pairs that share a *specific citation*;
      explicitly SKIP the pairs that are the validator's generic-`source_ref` false positive**
      (e.g. unrelated rows both labelled `"Oral Tradition"`). Keep both rows for legitimate variant
      translations; only merge/remove accidental duplication. **Sequence: runs AFTER W1** — this
      writes `quotes.csv`, which is READ-ONLY for the whole of W1.
      **Numbers re-derived 2026-09-13 (issue #31; the earlier `~22` / `~23` split was approximate and
      no re-run reproduced it): of the 45 flagged pairs, 15 warrant a human look (13 sharing a citation
      that carries a pinpoint locator + 2 text-similarity-only) and 30 are not evidence that two records
      are the same passage (25 sharing only the bare label `Oral Tradition`, 5 sharing a real work with
      no pinpoint).** The exact class table, the classification rule and the transcript are in
      `docs/data/DATA_QUALITY_REPORT.md` → "Re-derivation 2026-09-13 (issue #31)".
      **Numbers re-derived AGAIN 2026-09-13 (issue #34 — the sweep's scope and citation rule were the
      two policy questions #31 left open, and settling them moves this count): the list is now
      **20 pairs, all 20 worth a look, 0 to skip** — 13 sharing a citation that carries a pinpoint
      locator + 7 text-similarity-only, of which **5 are cross-tradition** and were invisible to the
      old per-`tradition` sweep (`39 ~ 53` Christianity ~ Judaism at 0.82, `50 ~ 318` Christianity ~
      Diné, `78 ~ 173` Islam ~ Sikhism, `87 ~ 187` Islam ~ Zoroastrianism, `175 ~ 332` Sikhism ~ Hopi).
      The "skip" class did not shrink, it stopped existing: the validator no longer reports a pair whose
      only evidence is a shared generic label, so the "explicitly SKIP the pairs that are the
      validator's generic-`source_ref` false positive" instruction in this item's own title is now
      vacuous — there is nothing in the list to skip.** The class table and the verbatim transcript are
      in `docs/data/DATA_QUALITY_REPORT.md` → "Re-derivation 2026-09-13 (issue #34)". Not done.
      **Related spec [#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34) — settled
      2026-09-13**: the sweep is now corpus-wide and applies W1.4's locator rule, so the per-`tradition`
      scope and the 196-pair / 45-pair measurements quoted in the filing are historical — the working
      count is **20**. See the "Closed — 2026-09-13 near-duplicate sweep scope + citation rule
      (issue #34)" section below.
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

- [x] Wire the D3 unverifiable-ledger acceptance suite into CI. `browser-smoke.yml`'s "Run the W1
      corpus-program acceptance suites" step runs the six W1 suites but not the new
      `scripts/check_garden_ledger.py` (45 checks) shipped by the D3 unit. A regression in the
      `legacy_verification` table, the `mark`/`reopen` guards, or the export section would pass CI.
      Issue [#39](https://github.com/mschwar/Garden-of-Wisdom/issues/39). CI-step change (guarded
      workflow), so filed rather than fixed inside the D3 unit; the D3 suite already proves its
      negative controls, so wiring it in cannot create a vacuously-green step.
      **CLOSED 2026-09-13/14 (branch `ci/wire-ledger-suite`, PR
      [#40](https://github.com/mschwar/Garden-of-Wisdom/pull/40), merged as `5b02b4e`):**
      `python scripts/check_garden_ledger.py` appended as a seventh line to the existing step,
      after `check_garden_e2e.py`. All seven suites (six W1 + ledger) re-verified `RESULT: PASS`
      locally immediately before the edit; one negative control (an injected `SystemExit` in
      `check_garden_ledger.py`, reverted after) confirmed the step fails fast under `bash -e`.
      `quotes.csv`/`sources.csv` untouched (`5675d7e6…` / `10b4c156…`). No new dependency, no
      change to `requirements-dev.txt`, `pages.yml` untouched. CI: PR smoke run
      [34803423991](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34803423991)
      **success** — the job log's own `RESULT: PASS` lines confirm `check_garden_ledger.py`
      genuinely executed and printed its 45-check pass, not merely that the step exited 0; on
      `main` after the merge, smoke run
      [34803565944](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34803565944)
      **success** and Pages deploy run `34803565954` **success**. Live acceptance on the merged
      `main`: `/`, `/browser/index.html`, `/quotes.csv`, `/sources.csv` all **200**, both live
      CSVs `sha256`-identical to the repo (`5675d7e6…` / `10b4c156…`). Design trail:
      `GARDEN_CI_LEDGER_HANDOFF.md`. Issue #39 closed by the merge.
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

## Open — corpus program (W0 landed 2026-09-12; Gate A accepted 2026-09-12; W1 AUTHORIZED IN FULL 2026-09-12 — COMPLETE; Gate B accepted 2026-09-13)

- [ ] **W1 — IN PROGRESS. Authorized in full 2026-09-12 (decision D1).** Six bounded units are
      specified in `docs/program/W1_DECOMPOSITION.md`:
      **W1.1** storage decision + minimal schema ✅ **DONE** · **W1.2** candidate-envelope contract
      + validator · **W1.3** manual capture/submission CLI · **W1.4** normalization + duplicate
      hints · **W1.5** curation review + decisions + audit history · **W1.6** end-to-end test pack +
      Gate B evidence packet.
      **Unit status (updated, appended — the lines above are left byte-identical): W1.1 ✅ DONE ·
      W1.2 ✅ DONE (see the close-out bullet below) · next: W1.3.**
      **Unit status (updated again, appended 2026-09-13): W1.1 ✅ DONE · W1.2 ✅ DONE · W1.3 ✅ DONE
      (see its close-out bullet below) · next: W1.4.**
      **Unit status (updated again, appended 2026-09-13, W1.4 close-out): W1.1 ✅ DONE · W1.2 ✅ DONE ·
      W1.3 ✅ DONE · W1.4 ✅ DONE (see its close-out bullet below) · next: W1.5.**
      **Unit status (updated again, appended 2026-09-13, W1.5 close-out): W1.1 ✅ DONE · W1.2 ✅ DONE ·
      W1.3 ✅ DONE · W1.4 ✅ DONE · W1.5 ✅ DONE (see its close-out bullet below) · next: W1.6.**
      **Unit status (updated again, appended 2026-09-13, W1.6 close-out): W1.1–W1.6 ✅ ALL DONE (see
      the W1.6 close-out bullet below). W1 COMPLETE — the Gate B packet is submitted. W2 is not started.**
      **Unit status (updated again, appended 2026-09-13, Gate B frontier review): Gate B accepted,
      2026-09-13 — see `docs/audit/2026-09-13/GATE_B_FRONTIER_REVIEW.md`. Independent review re-ran
      `check_garden_e2e.py` (96 checks), `validate_quotes.py` and `check_program_contracts.py`
      fresh, recomputed both CSV hashes, verified the PR #33 merge/CI/live-deploy chain via
      `gh`/`curl`, and confirmed one negative control (c1) actually fires by live-mutating and
      reverting `garden_submit.py`. No defects found — every claim in `W1_6_GATE_B_PACKET.md`
      reproduced exactly. W2 remains unauthorized; this review grants only Gate B acceptance, a
      separate operator decision from W2 authorization.**
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
- [x] **W1.2 — candidate-envelope contract + validator. DONE 2026-09-12** (branch
      `w1/envelope-validator`, PR
      [#26](https://github.com/mschwar/Garden-of-Wisdom/pull/26), **merged as `98631f5`**;
      independent/foreign QA found three unguarded validator paths and fixed them before merge —
      see the review section in `GARDEN_W1_2_HANDOFF.md`). `scripts/garden_envelope.py` implements
      `garden.candidate-envelope/1` (`docs/program/CANDIDATE_ENVELOPE.md`) as a canonical
      serialized JSON form (sorted keys, UTF-8, `allow_nan=False`) plus a deterministic validator
      for rules 1–6, each violation reporting `rule-1` … `rule-6`. Sentinel handling for
      `unknown`/`und`/`none`/`legacy-import` is a per-field allowance table: a sentinel is carried
      verbatim through validation, serialization and SQLite, never turned into `""`, and a missing
      required field is never defaulted. `scripts/check_garden_envelope.py` is the acceptance +
      evidence run (**102** checks; 99 as authored, +3 failing fixtures added by the reviewing
      session to close coverage gaps found in independent QA): round-trip is byte-identical and
      key-order independent, **23 invalid fixtures** (≥1 per rule, asserted as an *exact* rule-id
      set) plus 4 valid ones and all twelve W0 scenario envelopes pass/ fail exactly as declared,
      and a valid envelope is stored through W1.1's store and read back with all **21 required
      fields intact**. The `.invalid_envelopes` fixture set lives in
      `docs/program/fixtures/envelope_fixtures.json`; the design doc is
      `docs/program/W1_2_ENVELOPE_VALIDATOR.md`. **15 negative controls** recorded in
      `GARDEN_W1_2_HANDOFF.md` (each turns the run red with a targeted `FAIL:` line, no
      traceback), plus a separate **review finding** (independent QA found three unguarded paths —
      the `intake_schema_version` value check and rule 4's undeclared-keys / non-object-hint
      checks — and fixed them with three fixtures; see the handoff's review section and
      `docs/DECISIONS.md` "W1.2 review (QA)"). `quotes.csv`/`sources.csv` byte-identical
      (read-only rule held). Decision recorded in `docs/DECISIONS.md` ("W1.2 (envelope): no
      migration in W1.2 …"). **Next: W1.3.**
- [x] **W1.3 — manual capture/submission surface (CLI first). DONE 2026-09-13** (branch
      `w1/submission-cli`, PR
      [#28](https://github.com/mschwar/Garden-of-Wisdom/pull/28)). `scripts/garden_submit.py` turns
      one raw submission into one **immutable capture** (the text byte for byte, as encountered —
      literal `_`, curly quotes, leading/trailing whitespace, a wrong author and an absent citation
      all survive) plus one **candidate** at its intake states (`new`/`not_started`/`candidate_only`/
      `queued`), through W1.1's store and W1.2's validator. `scripts/check_garden_submit.py` is the
      acceptance + evidence run (**134** checks; it drives the CLI as a subprocess for all 18
      refusals and for every accepted submission, then asserts against the store the CLI wrote).
      Rulings W1.3 owns: the record-id scheme (`cap-`/`cand-YYYY-MM-DD-NNNN`, day = the **capture**
      day, next number derived by scanning the store, existing ids refused before anything is
      written), the canonical store location (`data/store/`, SQLite git-ignored, `garden.export.txt`
      the committed mirror), and the normalization boundary (W1.3 implements **no** normalization;
      the invariant it enforces is *no normalization without a note*, so a differing
      `--candidate-text`/`--candidate-author`/`--candidate-source-ref` is refused unless
      `--normalization-notes` says what changed and why). An omitted flag becomes the field's
      declared sentinel, while a flag supplied *empty* is passed through so the validator names the
      field; a refused submission writes nothing at all (asserted for all 18). Design doc:
      `docs/program/W1_3_SUBMISSION_CLI.md`. Decision recorded in `docs/DECISIONS.md` ("W1.3
      (submission CLI): the record-id scheme, the normalization boundary, the store location, and no
      populated mirror yet"). `quotes.csv`/`sources.csv` byte-identical (read-only rule held).
      **Deliberately not done, with the reason recorded:** no populated store mirror is committed —
      W1.3's only submissions are its own temp-dir fixtures and the acceptance run must pass from a
      clean clone; the first real operator submission populates it and the Gate B evidence store is
      where the demonstration belongs (this deviates from W1.1's handoff expectation and is recorded
      as such in `DECISIONS.md`). **Next: W1.4.**
- [x] **W1.4 — normalization + duplicate hints. DONE 2026-09-13** (branch `w1/normalization-hints`,
      PR [#29](https://github.com/mschwar/Garden-of-Wisdom/pull/29); commits `78432c8` + `604990c`).
      `scripts/garden_normalize.py` implements `garden.normalize/1` — NFC recomposition; four
      canonical-character classes (quote marks, dashes, ellipsis, no-break spaces) applied **one class
      at a time**; whitespace runs collapsed and boundary whitespace trimmed; a literal `_` placeholder
      **preserved and reported, never repaired** — and records a note for **every** change, with counts,
      attributed to the captured field it came from (`identical to capture`, W1.3's exact string, when
      nothing changed). The capture is never touched: the acceptance run asserts the whole `[captures]`
      export section is byte-identical after normalizing everything. `normalize` writes the proposal
      through one new guarded store method (`garden_store.apply_normalization`, which refuses a decided
      candidate, an empty proposal and an empty note); `hints` rebuilds `{kind, target, basis}` rows
      (`exact-text` / `near-text` / `same-reference` / `same-passage`), so hints are derived data that a
      rebuild **replaces rather than accumulates**, and **never a state** — no `curation_state` write, no
      candidate `duplicate`, and `decisions` stays empty (all asserted).
      **The three rulings W1.4 owns:** (1) the similarity threshold is **0.60** over normalized
      case-folded text, scored as the **mean of the two directional `difflib` ratios** — the raw ratio is
      asymmetric (rows 113/114 score 0.69 one way and 0.67 the other), so the two candidates would
      otherwise disagree about their own pair; (2) a shared citation is evidence only when it carries a
      **locator** (digit, Roman numeral, `§`) — the fix for the generic-`source_ref` false positive in
      `docs/data/DATA_QUALITY_REPORT.md`, asserted on the same fixtures where the legacy heuristic's own
      predicate flags the pair, so the guard is proven to do work; (3) a batch run **skips and names**
      a candidate it cannot normalize (a whitespace-only submission is legal at intake and W1 has no
      withdrawal path) while an explicit `--candidate-id` refusal writes nothing, and a batch that
      normalizes **nothing** fails. `scripts/check_garden_normalize.py` is the acceptance + evidence run
      (**232** checks, both interpreters), every fixture derived from the real `quotes.csv` (3 ~ 283,
      4/14, 319/331/332, 5/19, 113/114, the `has_unresolved_glyph` rows, a searched-for already-clean
      row) with a vacuity guard per fixture class. Design doc: `docs/program/W1_4_NORMALIZATION_HINTS.md`.
      Decision recorded in `docs/DECISIONS.md` ("W1.4 (normalization + hints) …"). `quotes.csv` /
      `sources.csv` byte-identical (`5675d7e6…` / `10b4c156…`). Three defects were found and fixed inside
      the unit (the note under-reported changes from a union-table `str.translate`; the similarity was
      asymmetric; `--all` aborted on an unnormalizable candidate), plus one coverage gap found by the
      unit's own control pass (the store's state guard had no unique falsifier — controls `n15`–`n17` now
      cover it). **17 author controls + 7 review controls**, all recorded in `GARDEN_W1_4_HANDOFF.md`.
      **No migration** — W1.4 declined the `placeholder_markers` column (see the W1.4 findings section).
      **Next: W1.5.**
- [x] **W1.5 — curation review + decision recording + audit history. DONE 2026-09-13** (branch
      `w1/curation-review`, PR
      [#32](https://github.com/mschwar/Garden-of-Wisdom/pull/32), merged as `627d604`).
      `scripts/garden_review.py` (`queue` / `show` / `audit` / `accept` /
      `hold` / `reject` / `duplicate` / `reopen`) is the operator-facing review surface on a single
      new store write gate, `garden_store.Store.curate`: it looks the legal T-C1…T-C12 transition up,
      applies the required corpus follow-on, and writes the candidate's states **and every audit row
      in one SQLite transaction** — no window in which a state changes without its audit row.
      `scripts/check_garden_review.py` is the acceptance + evidence run (**246** checks, both
      interpreters): all twelve T-C transitions are exercised through the real CLI and each produces
      an audit row with actor/timestamp/from/to/transition_id/reason; acceptance fires the
      deterministic **T-P1** `candidate_only → eligible` (authority `system`, audited); both
      reversal paths (`T-C8` then **T-P7**, `T-C9` then **T-P7**) leave **no dimension stranded**
      (falsifying the W0 carried-forward risk — `T-P7` returns an accepted-then-withdrawn record to
      `candidate_only`); rejecting keeps the capture and the candidate readable; **no curation action
      writes research state** (rendered read-only, always `not_started`, asserted after every
      transition); the queue renders the capture as `asserted`, the proposal as `derived
      (normalization)`, the notes as `asserted`, and the hints as `machine-inferred (a hint is
      evidence, never a decision)` (invariant 6); refused decisions (illegal transition, missing
      candidate, empty `--reason`) write nothing at all; the `decisions` log is re-asserted
      append-only; and `quotes.csv`/`sources.csv` are byte-identical (`5675d7e6…` / `10b4c156…`).
      Design doc: `docs/program/W1_5_CURATION_SURFACE.md`. Decision recorded in `docs/DECISIONS.md`
      ("W1.5 (curation review) …"). **No migration** — the `decisions` ledger and the four state
      columns already exist from W1.1, so W1.1's exact-ledger assertion is untouched. **8 negative
      controls** (same-session review pass; each fires W1.5's *own* guard — T-P1 firing, T-P7 firing,
      illegal-transition admission, the required-reason guard, a research-state write, the
      machine-inferred marker, the T-P1 system authority, and a CLI layer that would default an empty
      reason) are all recorded in `GARDEN_W1_5_HANDOFF.md`. **Next: W1.6.** **→ W1.6 DONE; see the
      W1.6 close-out bullet below.**
- [x] **W1.6 — end-to-end test pack + Gate B evidence packet. DONE 2026-09-13** (branch
      `w1/gate-b-packet`, PR [#33](https://github.com/mschwar/Garden-of-Wisdom/pull/33), merged as
      `0d8f5e5`). `scripts/check_garden_e2e.py` is the deterministic,
      clean-clone, one-command end-to-end acceptance run (**96 checks**, both interpreters,
      stdlib-only): it drives the whole loop — a messy submission batch (a literal `_` glyph row
      and a curly apostrophe row read **verbatim from `quotes.csv`**, plus a wrong author,
      leading/trailing whitespace, a missing citation, a near-duplicate pair, and two unrelated
      rows sharing the generic `Oral Tradition` label) → `submit` (W1.3) → `normalize --all` +
      `hints --all` (W1.4) → `accept/hold/reject/duplicate/reopen` with the full `accept → reject`
      reversal (W1.5) — through the real CLIs in a throwaway temp dir, and asserts: every capture
      **byte-identical** to the submitted text after every stage; provenance (method, timestamp,
      wrong author, whitespace, a missing citation's `none` sentinel) preserved; normalize + hints
      never touch the `[captures]` section and write no decision row; a hint is never a state; the
      generic `Oral Tradition` pair produces **no** reference hint (the W1.4 false-positive fix);
      every decision audited and the `decisions` log append-only; the reversal
      (`['T-C1','T-P1','T-C8','T-P7']`) strands no dimension; and **no curation action implies
      verification** (`research_state` stays `not_started` throughout). It re-runs
      `validate_quotes.py` and hashes both CSVs before/after (byte-identical: `5675d7e6…` /
      `10b4c156…`), proves the store export (`garden.export/1`) round-trips, and writes nothing
      outside the temp dir. The Gate B packet `docs/program/W1_6_GATE_B_PACKET.md` (mirroring
      `W0_GATE_REPORT.md`'s shape) is the wave gate's evidence package; the design doc is
      `docs/program/W1_6_E2E_TEST_PACK.md`. **6 same-session negative controls** (c1–c6, each to a
      stored write path; one finding — c5 — where the store's own `import_bytes` guard masks the
      e2e's round-trip check) recorded in `GARDEN_W1_6_HANDOFF.md`. **No migration**, no new store
      surface, `quotes.csv`/`sources.csv` untouched. **W1 is COMPLETE: the Gate B packet is
      submitted; W2 is not started.**

### Open — discovered during W1.4 (filed, NOT fixed in passing)

- [ ] **A candidate can never be withdrawn, and a whitespace-only submission is permanent.**
      `garden_submit.py` accepts a text that is only whitespace (envelope rule 2 requires non-empty, and
      whitespace is non-empty — correctly, since a capture is never trimmed), whose proposal normalizes to
      `""` and can therefore never be written; captures are immutable and undeletable by trigger
      (`PROVENANCE_AND_CAPTURE_CONTRACT.md` invariant 2) and no candidate/capture deletion or withdrawal
      command exists anywhere in W1. This is the concrete instance of the "no sanctioned capture-deletion
      path" ambiguity W1.1 recorded, and it is why `normalize --all` must skip such a row forever. Both
      available fixes are contract decisions (tighten envelope rule 2, or add an operator-visible
      withdrawal that keeps the capture), so neither is W1.4's to make. Filed as
      [#30](https://github.com/mschwar/Garden-of-Wisdom/issues/30); recorded in
      `docs/program/W1_4_NORMALIZATION_HINTS.md` §6.
- [x] **`validate_quotes.py`'s near-duplicate similarity is direction-dependent. CLOSED 2026-09-13**
      (branch `fix/validator-symmetric-similarity`, PR
      [#35](https://github.com/mschwar/Garden-of-Wisdom/pull/35)) — see the close-out bullet in the
      "Closed — 2026-09-13 validator near-duplicate score" section below.
      The original filing text follows, unchanged:
      `difflib.SequenceMatcher.ratio()` is asymmetric (`ratio(113, 114) = 0.6888…`, `ratio(114, 113) =
      0.6666…` on the real corpus), so the pair's reported number is a function of row order and the
      frozen `docs/data/DATA_QUALITY_REPORT.md` numbers cannot be reproduced in the other order — with a
      `> 0.6` threshold, a pair straddling 0.60 could even appear or disappear. Filed as
      [#31](https://github.com/mschwar/Garden-of-Wisdom/issues/31).
- [x] **RESOLVED 2026-09-13 — the near-duplicate sweep is now corpus-wide and applies W1.4's locator
      rule** (issue [#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34)). The original filing
      text follows with its **superseded** numbers annotated, kept as the record of what was measured
      before the decision: "a corpus-wide sweep flags **196** pairs instead of **45**" (the working
      count after the decision is **20** — the locator rule drops the 30 generic-`source_ref` pairs the
      196 was mostly made of, and widening then adds the 5 real cross-tradition overlaps), "of which 146
      of the 151 additions are the same bare `Oral Tradition` label matching across traditions — but 5
      are real cross-tradition text overlaps the scoped sweep cannot see at all" (still true, and the
      reason the decision widened the sweep rather than only tightening the rule; strongest `39`
      Christianity ~ `53` Judaism at 0.82), and "of the validator's 43 shared-`source_ref` pairs only 13
      carry one" (that 43 was the per-`tradition` count; corpus-wide it is 189, of which the same **13**
      carry a locator). Deciding this moved the D6 curation counts, as predicted — see the D6 item and
      "Closed — 2026-09-13 near-duplicate sweep scope + citation rule (issue #34)" below.
- [ ] **`AGENTS.md` still does not describe the corpus-program command surface** — and still omits the
      W1 read-only rule. Issue [#27](https://github.com/mschwar/Garden-of-Wisdom/issues/27) had been
      *closed as COMPLETED*, but the file is unchanged at `main` (`grep -c 'garden_' AGENTS.md` → 0, 63
      lines, last touched by `31f06e0`), so the documented resume path — "read `AGENTS.md` first" — is
      still wrong and an agent reading only that file can still believe editing the CSVs is fine. W1.4
      **reopened** it with that evidence; it still needs an operator edit or a policy exception (which is
      why W1.4's own doc-surface work stops at `RUNBOOK.md`).
- [ ] **A generic-citation duplicate can never attract a reference hint, so the queue must show the
      basis** — not a defect, a consequence worth writing down for W1.5: with ruling 2 in force, a
      duplicate whose citation is a bare label (or a sentinel) can only ever attract `exact-text` /
      `near-text` hints, never `same-reference` / `same-passage`. The queue surface must therefore show
      the hint's `basis` (which it is specified to do), because the kind alone no longer tells the
      operator how strong the evidence is.

### Open — discovered during W1.3 (filed, NOT fixed in passing)

- [ ] **`AGENTS.md` does not describe the corpus-program command surface.** The first file every
      agent reads lists `validate_quotes.py`, the homepage-preview export and `python3 -m http.server`
      — and nothing about `check_program_contracts.py`, `smoke_quote_browser.py`, the W1 store/
      envelope/submit commands, or the **W1 cross-unit rule that `quotes.csv` and `sources.csv` are
      read-only for the whole wave**. The gap predates W1.3 (it was already stale after W1.1/W1.2) and
      is now larger. Not fixed here: `AGENTS.md` writes are refused by tool policy and it is a
      protected file with a stated size budget, so the change needs an operator edit. Filed as
      [#27](https://github.com/mschwar/Garden-of-Wisdom/issues/27).
- [ ] **A candidate can only ever have one capture.** `PROVENANCE_AND_CAPTURE_CONTRACT.md` invariant
      3 explicitly allows the same passage to be captured twice and says "the candidate records all
      of them", and `candidate_captures` has an `ordinal` column for exactly that — but no surface
      can attach a second capture to an existing candidate, and W1.3 refuses a `--capture-id` the
      store already holds rather than restating it (rule 5 compares only `captured_text`, so a
      restatement could disagree with the stored record on attribution and still validate). Needs a
      decision on the link-existing-capture path and on whether rule 5 should widen; recorded in
      `docs/program/W1_3_SUBMISSION_CLI.md` §7.3 and `DECISIONS.md`. Not fixed in W1.3.
- [ ] **`captured_by` has a surface default the contract does not give it.** W1.3 defaults it to
      `operator` (matching `garden_store.add_capture`) rather than requiring an explicit flag. A
      reading, not a contract statement; recorded in `W1_3_SUBMISSION_CLI.md` §7.1 so a reviewer can
      require the flag instead.
- [ ] **The manual surface exposes no flag for any optional envelope field** (W1.2's
      persistence gap, unchanged). Eight of the nine optional fields still have no store column;
      `external_id` has one but no W1 flow needs it yet, so no flag was added. A flag that accepted a
      value the store cannot hold would be a silent drop. See the W1.2 entry above for the migration
      decision that is still owed to W1.4.
      **Answered 2026-09-13 (W1.4 close-out):** the migration decision was made — no migration, and
      still no flag for any optional field. See the W1.2 entry's W1.4 annotation above.

### Open — discovered during W1.2 (filed, NOT fixed in passing)

- [ ] **Optional envelope fields have no store columns.** Of the nine optional fields
      (`docs/program/CANDIDATE_ENVELOPE.md` §"Optional fields"), only `external_id` has a column in
      W1.1's schema; `provenance_chain`, `attribution_chain`, `placeholder_markers`,
      `source_link_state`, `locator`, `container`, `period_hint` and `rights_note` are validated,
      serialized and round-tripped but cannot be persisted. Persisting them needs a new migration,
      and W1.1's acceptance run asserts the ledger is exactly `["0001_create_core"]`, so a W1.2
      migration would turn W1.1's suite red. **Not fixed in W1.2** (a storage-schema change is
      W1.1's lane, and its acceptance would have to be edited to accept it). Needs a decision:
      either add migration `0002` (and relax W1.1's ledger assertion to "0001 present, applied
      once") or keep the optional fields out of the store until the unit that first needs them
      (likely W1.4, for `placeholder_markers`/`provenance_chain`). Recorded in
      `docs/program/W1_2_ENVELOPE_VALIDATOR.md` §5.3.
      **Answered 2026-09-13 (W1.4 close-out): W1.4 needed the placeholder *observation*, not a
      structure, and it added NO migration.** `placeholder_markers` still has no column; the
      `_`-glyph observation lives in `normalization_notes` (a field that already exists, whose
      contract is "what changed and why"), and W1.1's exact-ledger assertion is untouched. The
      reason — adding columns with no consumer is a speculative schema change in an ingestion lane,
      and it would force W1.1's acceptance run to be relaxed — is recorded in `docs/DECISIONS.md`
      ("W1.4 (normalization + hints) …", decision 4). The gap stays open, and now belongs to the
      first unit that *consumes* one of those fields structurally (a discovery adapter, or a W2/W3
      export).
- [ ] **Rule 5 only compares `captured_text`.** The contract's rule 5 says nothing about the other
      ten `captured_*` fields an envelope also carries, so an envelope whose
      `captured_attribution`/`captured_citation`/etc. contradict its own capture record would pass.
      W1.2 implements the rule exactly as written rather than silently widening it; the gap needs a
      contract decision (extend rule 5, or state that the other capture fields are the capture's
      and an envelope must not restate them). Recorded in `W1_2_ENVELOPE_VALIDATOR.md` §5.1.
- [ ] **CI does not run the W1 acceptance suites.** `.github/workflows/browser-smoke.yml`'s
      "Check the data validators still pass" step runs `validate_quotes.py`,
      `check_program_contracts.py` and `validate_homepage_preview_export.py`, but not
      `scripts/check_garden_store.py` (W1.1) or `scripts/check_garden_envelope.py` (W1.2).
      **Updated 2026-09-13 (W1.3): there are now three W1 acceptance suites**
      (`check_garden_store.py`, `check_garden_envelope.py`, `check_garden_submit.py`) — all
      stdlib-only, deterministic, exit-0/1 — and all three are still absent from CI. The decision
      below applies to three, not two. The two
      **Updated 2026-09-13 (W1.4 close-out): there are now FOUR W1 acceptance suites**
      (`check_garden_store.py` 59 checks, `check_garden_envelope.py` 102, `check_garden_submit.py`
      134, `check_garden_normalize.py` 232) and CI still runs none of them — `browser-smoke.yml`'s
      validator step is unchanged. All four are stdlib-only, deterministic and exit-0/1, and all four
      were re-run locally under both interpreters (Homebrew 3.14.5 and CI's 3.12) as W1.4's evidence.
      W1.4 again did not fix it: it is a change to a guarded workflow, so it needs its own unit
      (and its own branch/PR), not a side effect of an ingestion unit. The decision asked for at
      W1.2 is therefore still open, now over four suites.
      **Updated 2026-09-13 (W1.5 close-out): there are now FIVE W1 acceptance suites**
      (`check_garden_store.py` 59, `check_garden_envelope.py` 102, `check_garden_submit.py` 134,
      `check_garden_normalize.py` 232, `check_garden_review.py` 246) and a **sixth surface**
      (`garden_review.py`) that none of them protect from a future regression — CI still runs none of
      the five. The decision asked for at W1.2 is therefore still open, now over five suites; the
      decision in `DECISIONS.md` ("W1.5 lesson for the CI gap…") records that it was not fixed as a
      side effect of an ingestion/review unit.
      **Updated 2026-09-13 (W1.6 close-out): there are now SIX W1 acceptance suites**
      (`check_garden_store.py` 59, `check_garden_envelope.py` 102, `check_garden_submit.py` 134,
      `check_garden_normalize.py` 232, `check_garden_review.py` 246, `check_garden_e2e.py` 96) — the
      last of them the wave's own gate — and a **seventh surface** (`garden_review.py`) that none of
      them protect from a future regression — CI still runs none of the six. This is now the final
      recorded count for W1; the decision asked for at W1.2 remains open over six suites.
      W1 evidence runs therefore pass locally (and in the reviewer's run) but are not protected
      from a future regression by CI. Adding them is a low-risk, deterministic, stdlib-only,
      exit-0/1 addition to that step, but it is a CI change touching the guarded workflow and both
      W1 units shipped without it, so it is filed here rather than fixed in W1.2. Decide: extend
      the smoke workflow's validator step to run both W1 acceptance suites, or leave them as
      local-evidence-only.
      **CLOSED 2026-09-13/14 (branch `ci/w1-acceptance-suites`, PR
      [#37](https://github.com/mschwar/Garden-of-Wisdom/pull/37), merged as `396547b`):** decided —
      a new step, "Run the W1 corpus-program acceptance suites", appended to the existing `smoke`
      job, running all six suites (`check_garden_store.py`, `check_garden_envelope.py`,
      `check_garden_submit.py`, `check_garden_normalize.py`, `check_garden_review.py`,
      `check_garden_e2e.py`) after the existing validator step. All six re-verified `RESULT: PASS`
      locally immediately before the edit; one negative control (an injected `SystemExit` in
      `check_garden_store.py`, reverted after) confirmed the step fails fast under `bash -e` and
      stops before later suites when a real regression fires. `quotes.csv`/`sources.csv` untouched
      (`5675d7e6…` / `10b4c156…`). No new dependency, no change to `requirements-dev.txt`,
      `pages.yml` untouched. Independent/foreign QA (see `docs/DECISIONS.md` if recorded, or the
      PR's review thread) re-verified all six suites locally, confirmed the diff's scope, confirmed
      every import across the six suites and their `garden_*.py` modules is stdlib, and pulled the
      PR's own CI job log line-by-line to confirm the six suites genuinely executed under
      `bash -e` in the CI environment (not merely parsed) and each printed its own `RESULT: PASS`
      there — PASS verdict, no defects, flagged only informational notes (job now ~2m23s against
      a 15-minute timeout, most of it `check_garden_e2e.py`'s ~45s; single shared step means one
      early failure aborts the rest, which is the intended fail-fast behavior). CI: PR smoke run
      [34797609209](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34797609209)
      **success** (the job log shows all six suites' own `RESULT: PASS` lines, not just the step
      exiting 0); on `main` after the merge, smoke run
      [34797901059](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34797901059)
      **success** and Pages deploy run
      [34797901160](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34797901160)
      **success**. Live acceptance on the merged `main`: `/`, `/browser/index.html`,
      `/quotes.csv`, `/sources.csv` all **200**, and both live CSVs `sha256`-identical to the repo
      (`5675d7e6…` / `10b4c156…`). Design trail: `GARDEN_CI_W1_ACCEPTANCE_HANDOFF.md`. This is the
      final close-out for this long-open debt item — all six W1 acceptance suites are now
      CI-protected against regression; the "seventh surface" note from the W1.6 close-out
      (`garden_review.py` has no dedicated suite of its own beyond what `check_garden_review.py`/
      `check_garden_e2e.py` exercise) stays open as a separate, unfiled question, not part of this
      unit's scope.

## Open — debt and open questions discovered during W0 (specs only, not scheduled)

Filed from `docs/program/W0_GATE_REPORT.md` §Unresolved and
`docs/program/CLASSIFICATION_AND_FACETS.md`. None of these is authorized work.

> **Namespace note (2026-09-12):** the `D1`–`D8` labels below are the **W0 debt IDs** from
> `docs/program/W0_GATE_REPORT.md` and are **not** the same namespace as the 2026-09-12 decision
> IDs `D1`–`D10`. When referring to a *decision*, cite its dated entry in `docs/DECISIONS.md` by
> title, never by a bare `D<n>`.

- [x] **D2 — `unverifiable` is not representable in `quotes.csv`.** The 3-valued
      `verification_status` maps every unfinished research state to `unverified`, so a record
      proven unverifiable is indistinguishable from a never-checked row. Issue #5 (Garden id
      30) is the live instance. **Decided 2026-09-12 (decision D3):** represented in a side-car
      ledger keyed by legacy row id, after W1.1. **RESOLVED 2026-09-13 (decision D3 executed):**
      the `legacy_verification` side-car ledger is implemented and Garden id 30 is seeded — see
      the "Closed — 2026-09-13 D3" section. Do not widen the enum as a side effect of other work.
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

## Closed — 2026-09-13 near-duplicate sweep scope + citation rule (issue #34)

- [x] **Issue [#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34) — the near-duplicate sweep is
      now corpus-wide, and a shared `source_ref` is evidence only when the citation pinpoints a place.**
      Both rulings were decided *with* their measurement, over the four combinations, on the frozen
      324-row corpus:

      | scope | shared `source_ref` needs | pairs |
      |---|---|---|
      | per-`tradition` | any shared value | **45** (the pre-#34 count) |
      | corpus-wide | any shared value | **196** |
      | per-`tradition` | a **specific** citation (locator) | **15** |
      | **corpus-wide** | **a specific citation (locator)** | **20** ← adopted |

      They are one decision, not two: the 146 label-noise pairs that made #31 keep the sweep scoped are
      the *same* pairs the locator rule drops, so under that rule widening adds **5** pairs
      (`39 ~ 53` Christianity ~ Judaism at 0.82, `50 ~ 318` Christianity ~ Diné, `78 ~ 173` Islam ~
      Sikhism, `87 ~ 187` Islam ~ Zoroastrianism, `175 ~ 332` Sikhism ~ Hopi) and **zero** label noise.
      Those 5 were invisible to the scoped sweep — a duplicate filed under a second `tradition` label is
      exactly what the sweep exists to catch, and W1.4's store-side hint generator already compared
      corpus-wide for that reason. The rejected alternative (adopt the rule, keep the scope: variant C)
      is recorded in `docs/DECISIONS.md` with why. The locator test is **not re-implemented**: the
      validator imports `citation_specificity()` from `scripts/garden_normalize.py` so the store and the
      legacy corpus share one definition of the rule.

      **The count moved 45 → 20** (30 generic-`source_ref` pairs no longer reported at all — 25 the bare
      `Oral Tradition` label, 5 a real work with no pinpoint — and the 5 cross-tradition overlaps added),
      so the queue's **D6 item was re-counted in the same unit to 20 pairs to inspect / 0 to skip**. The
      "skip" class did not shrink, it stopped existing: the validator no longer reports a pair whose only
      evidence is a shared generic label. `docs/data/DATA_QUALITY_REPORT.md` gained a dated re-derivation
      section ("Re-derivation 2026-09-13 (issue #34)") carrying the class tables, the guards and the
      verbatim fresh transcript; the 2026-09-11 and "#31" transcripts are kept **byte-identical** (`git
      diff` shows **0 deletions** in that file). `quotes.csv` / `sources.csv` are byte-identical
      (`5675d7e6…` / `10b4c156…`) — every number here is a derivation over the corpus, not an edit to it.

      **Guards (this unit's answer to #31's control c4, "the scope has no automated falsifier"):** four
      hard checks now cover both rules — the pair set re-derived over every unordered row pair with no
      grouping (SCOPE), the reversal pass kept from #31 (ORDER), every printed reason re-derived from the
      rows with the rule inline (CITATION), and the imported rule's two canonical outcomes plus a vacuity
      check that the corpus still offers pairs the rule suppresses (DRIFT/VACUITY). **6 negative controls**
      in a throwaway `/tmp` copy (c1 scope regrouped, c2 locator condition dropped, c3 suffix dropped,
      c4 `LOCATOR_PATTERN` neutered, c5 corpus with no generic shared `source_ref`, c6 scorer reverted to
      one directional ratio) each exit 1 with the expected `FAIL:` line and no traceback; the unmutated
      copy exits 0. Recorded in `GARDEN_NEAR_DUPLICATE_SCOPE_HANDOFF.md`. The run went from ~2.3s to
      ~21s (52,326 unordered pairs); `pair_similarity` carries an exact multiset-overlap pre-filter whose
      output-neutrality was verified by brute force over all pairs (highest true score among pre-filtered
      pairs: 0.5062, `16 ~ 87`). **Nothing here is corpus-program W1/W2 work** — no store surface, no
      schema, no migration, no state vocabulary, and no corpus edit. Decision recorded in
      `docs/DECISIONS.md` ("The near-duplicate sweep is corpus-wide …").
      **Landed:** commit `f5986c8`, PR
      [#36](https://github.com/mschwar/Garden-of-Wisdom/pull/36), **merged as `4ce8e8e`** (2026-09-13).
      CI: PR smoke run
      [34794438967](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34794438967) **success**
      (the job log shows the new rule running in CI, not just compiling:
      `near-duplicate candidates: 20 (corpus-wide)`) and GitGuardian **pass**; on `main` after the
      merge, smoke run
      [34794547436](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34794547436) **success** and
      Pages deploy run
      [34794547412](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34794547412) **success**.
      Live acceptance on the merged `main`: `/`, `/browser/index.html`, `/quotes.csv`, `/sources.csv`
      all **200**, and both live CSVs `sha256`-identical to the repo (`5675d7e6…` / `10b4c156…`).
      Re-ran on merged `main`: all nine stdlib validators under both interpreters → `RESULT: PASS`, and
      `smoke_quote_browser.py` → `RESULT: PASS` (33 checks). Issue #34 stayed `OPEN` through the merge
      (verified after it, because this repo has lost that issue twice to a closing keyword in a PR or
      commit body). Design trail: `GARDEN_NEAR_DUPLICATE_SCOPE_HANDOFF.md` (**6 negative controls** plus
      a sanity run).

## Closed — 2026-09-13 validator near-duplicate score (issue #31)

- [x] **Issue [#31](https://github.com/mschwar/Garden-of-Wisdom/issues/31) — the near-duplicate score
      is now a property of the pair.** `scripts/validate_quotes.py` scored each candidate pair with ONE
      directional `difflib.SequenceMatcher.ratio()` call, and that ratio is asymmetric, so a pair's
      reported number depended on which row was visited first (`113 ~ 114`: 0.69 one way, 0.67 the
      other) and a pair straddling the `0.60` threshold could **appear or disappear** rather than merely
      shift (`189 ~ 216`: 0.6023 vs 0.5909). The score is now the **mean of both directional ratios**
      (the rule W1.4's store-side hint generator already used, `docs/program/W1_4_NORMALIZATION_HINTS.md`
      §3 ruling 1) and the validator **hard-fails** if a second detection pass with every tradition's rows
      reversed disagrees with the first — an order-dependent number is now a `RESULT: FAIL`, not a
      curation item. A second hard check re-derives every printed reason from the rows themselves, so a
      citation pair that also clears the text threshold must carry its number. The pair set is unchanged
      (**45**); four output lines moved. The two related questions #31 asked to decide: (1) a shared
      citation that also clears the threshold now **reports** its number (3 pairs today) rather than
      discarding it, and (2) the sweep **stays scoped per `tradition`** — with the measurement recorded
      (corpus-wide flags 196 pairs; 146 of the 151 additions are the bare-`Oral Tradition` label, but 5
      are real cross-tradition overlaps the scoped sweep misses) and the widening filed as its own spec,
      [#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34). `docs/data/DATA_QUALITY_REPORT.md`
      gained a dated re-derivation (the 2026-09-11 transcript is kept byte-identical; `git diff` shows
      **0 deletions** in that file) with the verbatim fresh transcript, the exact pair-class table
      (2 text-only + 13 pinpointed-citation + 25 bare-label + 5 work-level = 45) and the two decisions;
      the queue's **D6 item was re-counted** from the approximate `~22` / `~23` split to **15 to inspect /
      30 to skip**. `quotes.csv` and `sources.csv` are byte-identical (`5675d7e6…` / `10b4c156…`): the
      re-count is a derivation over the corpus, not an edit to it. Design trail:
      `GARDEN_VALIDATOR_SYMMETRY_HANDOFF.md` (**5 negative controls**, one per changed path, plus the two
      that stay green and why). Decision recorded in `docs/DECISIONS.md` ("The near-duplicate score is a
      property of the pair …"). **Nothing here is corpus-program W1/W2 work** — no store surface, no
      schema, no migration, no state vocabulary touched.
      **Annotated 2026-09-13 (issue #34):** two numbers in this entry are superseded. "The pair set is
      unchanged (**45**)" and the D6 re-count "**15 to inspect / 30 to skip**" were correct *under
      #31's rules*; #34 then widened the sweep to the whole corpus and adopted W1.4's locator rule, so
      the working counts are **20 pairs — 20 to inspect, 0 to skip**. The "sweep **stays scoped per
      `tradition`**" sentence records #31's decision, which #34 deliberately reversed, with the
      measurement, in the closed section below. Everything else in this entry still reproduces.
      **Landed:** commit `d27cb64`, PR [#35](https://github.com/mschwar/Garden-of-Wisdom/pull/35),
      **merged as `f24fae7`** (2026-09-13). CI: PR smoke run
      [34790379227](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34790379227) **success**;
      on `main` after merge, smoke run
      [34790423853](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34790423853) **success**
      and Pages deploy run
      [34790423865](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34790423865) **success**.
      Live acceptance on the merged `main`: `/`, `/browser/index.html`, `/quotes.csv`, `/sources.csv`
      all **200**, and both live CSVs `sha256`-identical to the repo
      (`5675d7e6…` / `10b4c156…`). Re-ran on merged `main`: `validate_quotes.py` → `RESULT: PASS`,
      `check_program_contracts.py` / `validate_homepage_preview_export.py` → exit 0, and all six W1
      acceptance suites → `RESULT: PASS`.

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
- [ ] **D4 — ONE batch capture record for the 324 legacy rows.** Authorized 2026-09-12: a single
      batch capture record for the 2026-09-11 rehabilitation import, explicitly marked as such and
      noting the encounter context is unknown — not one synthetic capture per row. (Resolves the
      "human decision" open question in the debt section below.)

## Closed — 2026-09-13 D3 (unverifiable side-car ledger)

- [x] **D3 — `unverifiable` side-car ledger. DONE 2026-09-13** (branch `d3/unverifiable-ledger`,
      PR [#38](https://github.com/mschwar/Garden-of-Wisdom/pull/38) — see the handoff for the merge). Represent `unverifiable` in a side-car ledger keyed
      by legacy row id, NOT by widening the 3-valued `quotes.csv` enum, in the W1.1 store (one store,
      not two). `legacy_verification` table via migration `0002_unverifiable_ledger`;
      `Store.mark_legacy_unverifiable` / `Store.reopen_legacy_unverifiable` (each writes its audit
      row in the same transaction); `scripts/garden_ledger.py` CLI (mark/reopen/list);
      `scripts/check_garden_ledger.py` (**45** checks) + **10** negative controls (each goes
      `RESULT: FAIL` with its guard's `FAIL:` line, no traceback). Design doc:
      `docs/program/D3_UNVERIFIABLE_LEDGER.md`. Decision recorded in `docs/DECISIONS.md`
      ("D3 executed (the unverifiable side-car ledger)"), including the rulings that the export
      header stays `/1` and that `check_garden_store.py`'s exact-shape assertions were necessarily
      updated to the two-migration schema. **Live instance seeded:** Garden id 30 (issue #5) is
      `unverifiable` in the committed store mirror `data/store/garden.export.txt` — the CSV row is
      now distinguishable from a never-checked row. `quotes.csv`/`sources.csv` byte-identical
      (`5675d7e6…` / `10b4c156…`). (Resolves the open question in the debt section below.)

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
