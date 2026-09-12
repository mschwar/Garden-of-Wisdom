# Decisions

Append-only. Add new entries at the bottom with a date. Don't edit or delete past entries even
if later superseded — add a new entry that supersedes the old one and say so.

## 2026-09-11 — Rehabilitate encoding by re-decoding, not by string-replacing mojibake

The original files were Mac OS Roman, not UTF-8. Decided to re-decode the archived original
bytes with the correct codec rather than pattern-matching and replacing mojibake sequences in
the (already-decoded-wrong) text, because the former is a provable, lossless transform and the
latter risks silently "fixing" text that only looks like mojibake by coincidence.

## 2026-09-11 — Do not guess the glyph behind literal `_` placeholders

4 rows use a literal ASCII `_` where a diacritic/modifier letter belongs. Decided not to
replace it with a guessed correct character, even though the likely intent is often obvious
(e.g. Bahá_u'lláh → Baháʼu'lláh), because that crosses from encoding restoration into
editorial judgment about source text. Flagged instead via `has_unresolved_glyph` for a human
to fix with the right reference.

## 2026-09-11 — Link `source_id` by matching `source_ref` keywords, not by `tradition`

Considered mapping each `tradition` value to a single `sources.csv` row. Rejected: several
traditions (Judaism, Christianity) legitimately span multiple manifest entries (Talmud vs.
Bible vs. Pirkei Avot), so a tradition-level mapping would silently misattribute many rows.
Matched on substrings of `source_ref` against known titles/keywords instead, leaving `source_id`
blank where no confident match exists rather than falling back to a coarser, wrong guess.

## 2026-09-11 — Keep the 27-value tradition list as-is rather than collapsing to the old 7

The pre-retrofit README declared 7 traditions; the actual data has always had 27 (including
Sikhism and 19 Indigenous/African oral-tradition labels). Decided the data reflects real
project scope and the README was simply out of date, not the reverse — updated the canonical
README's list to match the data instead of trimming the data to match the README.

## 2026-09-11 — Ship the quote browser as a single-page vanilla JS app, no CSV library

Considered pulling in a CSV parsing library (e.g. PapaParse) for robustness. Decided a small
hand-rolled RFC4180-ish parser in `browser/app.js` is sufficient for this dataset's shape and
keeps the "no framework unless demonstrably necessary" constraint from
`docs/product/PRODUCT_DOCTRINE.md` / the originating work-unit prompt. Revisit if quote data
grows pathological embedded-quote/newline cases the hand-rolled parser mishandles.

## 2026-09-11 — Approved donor set for the homepage preview export: Garden ids [3, 12, 15, 26, 30]

Three candidate donor-set options were proposed for
`bootstrap/seed/2026-09-11-garden-2026-retrofit/prompts/02_GARDEN_VERIFY_AND_EXPORT_HOMEPAGE_PREVIEW.txt`'s
`APPROVED_GARDEN_IDS`: (A) the safest/most-famous, least-ambiguous Bahá'í passages; (B) a set
deliberately diverse across citation shapes and source works, to stress-test the export
mechanics; (C) a set including one deliberate Hidden Words item, to test collision handling
against the homepage's existing Hidden Words corpus. Chose **option A** — ids 3, 12, 15, 26, 30
— because this is a first "tiny preview" export whose job is proving the verify→export pipeline
works at all, not stress-testing edge cases yet. All five resolve cleanly to `source_id 12`
("Official Baha'i Writings"), none carries `has_unresolved_glyph`, none appears in any
near-duplicate candidate pair (`docs/data/DATA_QUALITY_REPORT.md`), and none is drawn from The
Hidden Words. Options B and C are deferred to a later, deliberate follow-up export, not rejected.

## 2026-09-11 — Phase 0 frontier review: accept with documented debt

Independent re-check of G0–G3 (encoding bytes, rehab/validate scripts, CSVs vs archived
originals, live browser). Full write-up: `docs/audit/2026-09-11/PHASE0_FRONTIER_REVIEW.md`.

Accepted. No data-integrity reason to revert PR #1. Encoding diagnosis (Mac OS Roman → UTF-8)
is evidenced, not asserted; 324/324 core fields match the mac_roman-decoded originals; literal
`_` placeholders were not "fixed." `item_type` is a heuristic queue signal, not an export
classification — Roman-numeral Gleanings citations (including donor ids 3 and 15) landed in
`unknown`, and paraphrase-shaped rows 31 and 267 were not typed `paraphrase`. A future H2B
export must reclassify `item_type` at verification time, map `verification_status` →
`verification_state`, and record `source_url` then. Do not live-read `quotes.csv` from
`bahai-homepage`.

## 2026-09-11 — Donor-set near-dupe claim was false for id 3 (supersedes the "none appears" sentence above)

The donor-set entry above said ids 3/12/15/26/30 appear in no near-duplicate candidate pair.
Validator output flags `3 ~ 283` (text similarity 0.74): “The earth is but one country, and
mankind its citizens.” (Bahá’u’lláh, Gleanings CXVII) vs “The earth is one home and mankind
its family.” (‘Abdu’l-Bahá, Selections 255). Different author, different work, similar
teaching — not a reason to drop id 3 from the donor set, but the “none appears” claim is
false and must not be used as a verification/export gate. Ids 12, 15, 26, 30 are still
unflagged.

## 2026-09-11 — G4: verify approved donors; export four; reject id 30; correct two locators

Executed Prompt 02 against the accepted H2B-A contract (bahai-homepage D27). Approved set
stayed `[3, 12, 15, 26, 30]`.

Accepted, wording exact on bahai.org: 3 (Gleanings CXVII), 12 (Tablet of ‘Abdu’l-Bahá),
15 (Gleanings CXXII), 26 (Promulgation of Universal Peace, 12 April 1912). All four classified
`excerpt` and `verified` in `quotes.csv`. Export:
`exports/bahai-homepage-preview/v1/collection.json`.

Rejected: id 30 — sentence not found; Paris Talks has no 2 December 1911 meeting. Left
`unverified`; omitted from the collection (no paraphrase as scripture).

Explicit CSV corrections, quote text untouched: id 12 author `Bahá’u’lláh` → `‘Abdu’l-Bahá`
and `source_ref` retargeted from ADJ p. 22 to the tablet (ADJ is the secondary print
witness); id 26 `source_ref` retargeted from Paris Talks 22 Oct 1911 (the “Sun of Truth”
talk, which does not contain the sentence) to PUP 12 April 1912. Ids 3 and 15 only changed
`item_type` `unknown` → `excerpt` (Roman-numeral heuristic miss).

Did not add a `source_url` column to Garden; URLs live on the export. Did not rename
`verification_status` to `verification_state`; mapped at export time.

## 2026-09-12 — W0: program doctrine is additive, and lives under `docs/program/`

The corpus-program seed (`bootstrap/seed/2026-09-12-garden-corpus-program/`) asked W0 to
produce "corpus/program doctrine" as a canonical doc. Considered rewriting
`docs/product/PRODUCT_DOCTRINE.md` into a merged product+program doctrine. Rejected: that
would restate (and eventually drift from) the product non-negotiables, and the retrofit's
frontier review already established `PRODUCT_DOCTRINE.md` + `DATA_CONTRACT.md` as the
authorities for the existing corpus. Decided instead that program doctrine is **additive**:
it lives under `docs/program/`, governs only the corpus lifecycle, and *inherits* the product
non-negotiables by reference. `PRODUCT_DOCTRINE.md` gains a pointer, not a rewrite. Eight
reconciliation rulings (seed vs existing doctrine) are recorded in
`docs/program/CORPUS_PROGRAM_DOCTRINE.md` §"Reconciliation".

## 2026-09-12 — W0: four orthogonal state dimensions; the 3-valued CSV stays a projection

The seed warned against `intake → approval → final truth` and demanded separate curation,
research, corpus, and work state. Considered widening `quotes.csv.verification_status` (or
adding curation/corpus columns) to match the model immediately. Rejected: the 324 rows carry
no capture records, no per-claim evidence, and no decision history, so a schema change now
would write empty columns and imply data that does not exist — exactly the false-certainty
failure the program exists to avoid. Decided the four dimensions are the model of record
(`docs/program/STATE_MODEL.md`) and the CSVs remain a **documented lossy projection**:
`verified → verified`, `disputed → disputed`, and all of `not_started`/`in_research`/
`needs_more_evidence`/`unverifiable` → `unverified`. The known loss is that `unverifiable` is
not representable in the CSV (issue #5, Garden id 30, is the live instance). No migration in
W0; a migration is its own unit.

## 2026-09-12 — W0: `canonical` does not imply `verified`; the existing 324 rows prove it

Resolved the seed's rule "canonical must not imply verified" against the actual repo by
naming the current state honestly: every row in `quotes.csv` is a canonical record
(`corpus_state = canonical`, `curation_state = accepted`) whose truth is mostly unfinished
(320 of 324 are `unverified`). The gate that admitted them is the Phase 0 retrofit acceptance
plus the 2026-09-11 frontier review — not verification. Decided this is the intended
behaviour, not a contradiction: canonical means "passed defined gates while faithfully
representing remaining uncertainty". Consequence: any surface showing a canonical record must
keep its research state visible, and the exporter must keep refusing `unverified` rows.

## 2026-09-12 — W0: terminal research outcomes are human-adjudicated; agents stop at `in_research`/`needs_more_evidence`

The seed said `verified` must be tied to a written verification contract, not agent
confidence. Considered allowing an agent to record `verified` when its evidence package met
the contract mechanically. Rejected for W0: an agent that both gathers and certifies evidence
has no independent check, and the repo's own history (G4, and id 30's rejected claim) shows the
value of a human adjudication step. Decided the agent-authority research transitions are only
`T-R1`/`T-R2`/`T-R3` (open, block, resume); `verified`, `disputed`, and `unverifiable` are
operator-authority and must carry an adjudication record (who, when, rationale, evidence ids,
contract version). W5 may automate case *execution* with independent QA, but adjudication stays
a recorded gate. Enforced by `scripts/check_program_contracts.py`.

## 2026-09-12 — W0: no datastore is chosen; SQLite is a W1 hypothesis with written requirements

The seed's storage posture said not to select a database in W0. Honored literally: W0 selects
nothing. `docs/program/W1_DECOMPOSITION.md` lists the eight storage/access requirements W1
actually has (immutable captures, envelope + normalization notes, rebuildable duplicate hints,
append-only decision log, four state dimensions, a fast unreviewed queue, no network
dependency, text export), and W1.1 must rule on them with a decision-log entry. SQLite is
recorded as the working hypothesis only — not a decision — precisely so a later agent cannot
cite it as settled.

## 2026-09-12 — W0: 324 legacy rows get no invented capture record

The seed requires preserving the raw encounter. The existing rows have none: what the original
author saw, where, and when was never recorded. Considered synthesizing `legacy-import`
capture records so every row has one. Rejected: a fabricated capture record would be a
provenance claim with no evidence behind it — the exact failure mode this program exists to
prevent. Decided their recorded provenance is the frozen archive
(`data/archive/2026-09-11/*.original.csv`), git history, and the documented rehabilitation
transform, and that future imports must use the `legacy-import` sentinel rather than imply a
real encounter. The open policy question (does `legacy-import` ever get a capture record at
all?) is queued, not decided.

## 2026-09-12 — W0: faceted classification, and the 27-value tradition list stays un-collapsed

Restates and extends the 2026-09-11 decision to keep 27 tradition values. The seed asked for
faceted classification rather than a single exclusive category. Decided: facets are the model
(10 facets, multi-valued where warranted), `tradition` stays single-valued and unrenamed for
now (it is a facet with one value), `item_type` is acknowledged as overloaded (shape mixed with
provenance shape) and its split is deferred to W3 rather than widened now, and six ontology
questions (multi-valued tradition? domain redundancy? non-text sources? period? shape vs
item_type? culture?) are recorded as open in
`docs/program/CLASSIFICATION_AND_FACETS.md`. No vocabulary is hardened in W0.

## 2026-09-12 — W0 ships a documentation-consistency checker, not runtime

`scripts/check_program_contracts.py` parses the transition table out of `STATE_MODEL.md` and
the required-field list out of `CANDIDATE_ENVELOPE.md`, then simulates the ten canonical
adversarial scenarios in `docs/program/fixtures/w0_scenarios.json`: transition chains must be
connected and end where declared, operator-authority transitions must be declared as such,
transition guards must hold (`T-P1`/`T-P2` require curation acceptance; `T-R4` requires a
research case to have run), each record's research state must equal the aggregate of its
per-claim statuses, a claim may only be `verified` with a witness *and* a locator, uncertainty
must stay visible whenever the record is not fully verified or makes no wording claim, and all
ten canonical cases plus the five Gate A requirement kinds must be covered. Decided this is
warranted in W0 because a doctrine set with no executable check is a doctrine set that drifts;
and decided it is *not* implementation because it reads only `docs/program/**`, writes nothing,
and exercises no intake/curation/research behaviour. Its teeth are demonstrated with the
negative controls recorded in `docs/program/W0_GATE_REPORT.md`.

## 2026-09-12 — Quote-browser smoke test: Playwright as a test-only dependency, expectations derived from the CSVs

Considered (a) driving the system Chrome over raw CDP from a dependency-free Node script, (b) a
DOM shim such as jsdom, (c) Playwright. Rejected (a): hand-rolled CDP + WebSocket plumbing in a
repo whose whole value is trustworthiness adds protocol code nobody will maintain. Rejected (b):
jsdom cannot answer the questions that actually matter here — real layout (the phone-width
overflow), real clipboard, real console/network errors. Chose (c), pinned in
`requirements-dev.txt`: the test must exercise the real rendered page. The app itself stays
dependency-free — `requirements-dev.txt` is dev-only and every script under `scripts/` except
this test remains stdlib-only. Consequences: CI needs a browser, so the smoke test runs in its
own workflow (`.github/workflows/browser-smoke.yml`, on PRs and pushes to `main`) instead of the
Pages deploy job; and no count is hard-coded — expected rows, search hits and table rows are
recomputed from `quotes.csv` with the same parsing rule `browser/app.js` uses, so a data change
cannot silently pass. Teeth demonstrated with seven negative controls (breaking the search
filter, the data fetch path, a copy button, the console, or any of the three layout fixes each
turns the run into `RESULT: FAIL` with no traceback).

## 2026-09-12 — The queue's stated cause of the phone-width overflow was wrong; the measured cause is recorded

The queue item filed from PR #9 said the ~375px overflow came from `#controls select{min-width:140px}`.
Measured in headless Chromium at 375px, `min-width` was not the driver: a `<select>`'s intrinsic
width follows its longest `<option>`, and the Source dropdown's longest `source_ref` is 61
characters, so that control laid out at **390px** (Author: 276px) inside a 341px content box,
producing a 421px document. Fixed by letting the label shrink (`min-width: 0; max-width: 100%`)
and capping the select (`max-width: 100%`). The defect was real; the explanation was not, and it
is corrected in `docs/queue.md` and `docs/architecture/QUOTE_BROWSER.md`. The new test then
exposed two further defects nobody had reported: the comma-joined `.tags` string is one
unbreakable ~280px token that escaped the card at 320px, and card view left `#table-wrap` (the
border/scroll container) visible while hiding the table inside it, i.e. an empty 2px bordered box
at the end of the page. Both fixed in this unit. All three are covered by the smoke test. No data,
CSV, or export file was touched.

## 2026-09-12 — W0: curation reversal must move the corpus dimension (T-P7/T-P8 added)

Foreign QA on the W0 branch found a stranded-state bug in the state model: eligibility is a
deterministic consequence of curation acceptance (`T-P1`), but curation is reversible
(`T-C8 accepted → rejected`, `T-C9 accepted → duplicate`), and the corpus dimension had no
transition out of `eligible`. A record the operator withdrew acceptance from would have been
stuck `eligible` (or `canonical`) forever with no legal transition to correct it — a real
inconsistency, not a documentation nit. Fixed by adding `T-P7 eligible → candidate_only` and
`T-P8 canonical → eligible` (both operator-authority), stating the reversal rule in
`docs/program/STATE_MODEL.md`, asserting the end-state consistency in
`scripts/check_program_contracts.py` (a record may never end with curation
`hold`/`rejected`/`duplicate` while the corpus state is `eligible`/`canonical`), and adding
walkthrough S11 to exercise the path. Also hardened in the same pass, from the same review: the
checker now asserts the authority of all 40 transitions (not just the ones a scenario uses),
compares the fixture template and doc required-field list in both directions, re-parses the
aggregate rule out of `VERIFICATION_CONTRACT.md` so a doc-only edit fails, validates the
envelope template itself, and reports malformed fixtures as `RESULT: FAIL` instead of a
traceback.

## 2026-09-12 — Gate A frontier review: accept, with three evidence-hygiene defects fixed

Independent review (`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`) re-ran the doctrine
checker and both existing validators, recomputed `quotes.csv`/`sources.csv` hashes, and
cross-checked every count claim in `docs/program/W0_GATE_REPORT.md` and `docs/queue.md`
against the actual fixture, doc, and decision-log contents. All eight Gate A criteria
(`bootstrap/seed/2026-09-12-garden-corpus-program/ACCEPTANCE_GATES.md`) are satisfied.

Found and fixed three stale-number defects, all caused by the `T-P7`/`T-P8` stranded-state fix
(decision above) landing after the numbers were first written and never being refreshed: the
Gate A report's appended acceptance-run block still showed the pre-fix 38 transitions/10
scenarios instead of 40/12; the report undercounted its own decision-log entries as 8 instead
of 9 and never listed decision 9; and `docs/queue.md`'s closed-W0 summary said "11 walkthroughs"
and "15 negative controls" instead of 12 and 20. None reached doctrine substance, the
transition table, the envelope contract, or the checker's behavior — decided the correction
belongs as a dated addendum to the existing report (not a silent rewrite of its evidence
blocks), consistent with how this log already treats a falsified prior claim (the donor-set
near-dupe entry above).

Verdict: **Gate A accepted**, 2026-09-12. Decided this acceptance does **not** authorize W1.1 —
that stays a separate, explicit operator decision per `docs/program/CORPUS_PROGRAM_DOCTRINE.md`
and the W0 report's own stop point.

## 2026-09-12 — Filter coverage is asserted by searching the data for narrowing cases, not by naming a value

Implementing issue #13 (smoke-test coverage for the six filter dropdowns, the "Issues only"
toggle, a combined interaction and the empty-result state) required choosing which value to
select in each dropdown. Considered hard-coding a representative value per filter (e.g. a known
tradition, a known tag) — it reads well in the output and is one line each. Rejected: a
hard-coded value is exactly the failure mode the existing test was already fixed for once (the
unguarded `SEARCH_TERM`, foreign-QA finding 3 in `GARDEN_BROWSER_SMOKE_HANDOFF.md`): if a data
edit removes or renames that value the check either crashes or, worse, passes on an empty set.
Decided the test **searches `quotes.csv` for a value that actually narrows** (0 < count < total)
per dropdown, and searches for filter+search combinations that narrow and that match nothing,
failing with an explicit "would be vacuous" line if the data stops offering one. The six
dropdowns' *option sets* are also compared against the CSV's distinct values, because a
count-only check cannot see a dropdown that lost an option it never selected. Cost: the chosen
value is data-dependent and so varies as the corpus changes — accepted deliberately, since the
run prints the value it used and every expectation is recomputed from `quotes.csv`.

Also decided here: the card view's missing empty state (zero matches renders a blank `#results`
while table view explains itself) is a **browser behaviour** change, so it is out of scope for a
test-only unit and is filed as issue #17 + a queue entry rather than fixed in passing. Teeth for
the new checks: seven negative controls (one per broken filter/toggle/empty-state/population/sort
path) plus three controls that show the vacuity guards themselves firing when
`quotes.csv` stops distinguishing the behaviour — recorded in
`GARDEN_FILTER_SMOKE_COVERAGE_HANDOFF.md`.

## 2026-09-12 — D1 (authorization): W1 is authorized IN FULL; the per-unit gates are not merged

Gate A was accepted 2026-09-12 (`docs/audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`). Considered
authorizing W1 one unit at a time — W1.1, then re-decide — which is literally what the W0 report's
stop point and the queue item said. Rejected: the operator chose to authorize the **whole wave**,
on the explicit condition that authorizing the wave does **not** merge the per-unit gates. Each
unit still keeps its own isolated branch/worktree, its own PR, independent/foreign QA, and its own
merge; the unit boundaries are unchanged.

Authorized in full: **W1.1** storage decision + minimal schema, **W1.2** candidate-envelope
validator, **W1.3** manual capture/submission CLI, **W1.4** normalization + duplicate hints,
**W1.5** curation review + decisions + audit history, **W1.6** end-to-end test pack + Gate B
packet. Ordering and dependencies in `docs/program/W1_DECOMPOSITION.md` still hold: W1.1 → W1.2 →
W1.3 → W1.4 (W1.4 may overlap W1.3) → W1.5 → W1.6. The stop point is unchanged — W1 ends at the
Gate B packet, and W2 is not started. This entry supersedes the "W1 NOT authorized" posture
everywhere it is stated (`docs/program/W1_DECOMPOSITION.md` header, `docs/queue.md`,
`docs/program/W0_GATE_REPORT.md`).

## 2026-09-12 — D2 (storage): W1.1's store of record is SQLite with a committed full-text export

W1.1 decides the store. Chosen: **SQLite** as the store of record, with a full text export
committed to git as the human-readable, diffable mirror. Rationale: it meets all eight
storage/access requirements in `docs/program/W1_DECOMPOSITION.md` §Storage and access
(immutable captures, append-only decision log, the four state dimensions, a fast unreviewed-queue
query, no network, no server) with one file and one code path, and the committed export preserves
diffability. Rejected: (a) plain JSONL/CSV files + git as the store — immutability and the
append-only audit log become conventions rather than enforced structure; (b) a hybrid of JSONL
plus a rebuildable SQLite index — two write paths for no W1 gain. The hybrid is recorded as the
**upgrade path** if the operator later wants decisions diffable in git from day one. This
supersedes the W0 "no datastore is chosen" entry: W0 chose nothing on purpose; W1.1 now decides.

## 2026-09-12 — D3 (unverifiable): a side-car ledger keyed by legacy row id, not a widened enum

`unverifiable` will be represented in a **side-car ledger keyed by legacy row id**, NOT by
widening the 3-valued `quotes.csv` `verification_status` enum. Implementation is deferred until
after W1.1 exists, so there is one store rather than two. Rationale: the CSV is a documented lossy
projection of a 6-value research dimension (`docs/program/STATE_MODEL.md`), and
`docs/program/W1_DECOMPOSITION.md` already names a side-car ledger as the way legacy rows are
re-opened. Rejected: (a) adding a 4th enum value — a permanent widening of a frozen view that is
still lossy; (b) leaving it to the export only — issue #5's live instance (Garden id 30) stays
indistinguishable from a never-checked row.

## 2026-09-12 — D4 (legacy capture provenance): one batch capture record for the 2026-09-11 import

The 324 legacy rows get **ONE batch capture record** for the 2026-09-11 rehabilitation import,
explicitly marked as such and explicitly noting that the encounter context is unknown. Rationale:
that is a true, verifiable statement (git history + `data/archive/2026-09-11/` + the documented
transform) rather than an invented encounter, and it gives downstream code a uniform shape.
Rejected: (a) no capture at all — the archive stays the only provenance, kept as the fallback if
the operator prefers zero synthetic entities; (b) one synthetic capture per row — fabricated
per-row provenance, the exact failure the program exists to prevent. This closes the W0 open
policy question ("does `legacy-import` ever get a capture record at all?") without inventing a
per-row encounter.

## 2026-09-12 — D5 (naming): `verification_status` and `verification_state` are different things, and the mapping is machine-checked

`verification_status` and `verification_state` are declared **DIFFERENT things** rather than one
renamed to the other: `verification_status` = the 3-valued `quotes.csv` projection;
`verification_state` = the store's 6-valued research dimension. The mapping must be written down
and machine-checked — `scripts/check_program_contracts.py` already recomputes the projection from
the data and must assert the mapping. This closes issue #7 as a **decision, not a rename**.
Rejected: (a) renaming the CSV column — touches the frozen view, validator, browser and export to
save one mapping; (b) leaving it as an undocumented status quo — the two spellings keep hardening.
(The checker assertion itself is implemented by a separate unit; this entry only records the
decision.)

## 2026-09-12 — D6 (near-duplicate curation): curate the citation-sharing pairs; skip the generic-`source_ref` false positives

Of the 45 near-duplicate candidate pairs in `docs/data/DATA_QUALITY_REPORT.md`, curate the ~22
pairs that share a **specific citation**, and explicitly skip the ~23 pairs that are the
validator's generic-`source_ref` false positive (e.g. unrelated rows both labelled 'Oral
Tradition'). Keep both rows for legitimate variant translations; only merge/remove accidental
duplication. Sequencing constraint: this writes `quotes.csv`, and W1 makes `quotes.csv`/`sources.csv`
**READ-ONLY for the whole of W1**, so it runs **AFTER W1 completes**. Rejected: (a) tightening the
heuristic first — that is W1.4's job, for new candidates; (b) deferring entirely — the legacy
browser view is what people use today.

## 2026-09-12 — D7 (manifest gap): close the 14 unresolved `source_id` links by adding rows, after W1

Close the 14 unresolved `source_id` links by adding `sources.csv` rows — the identifiable works
(Mahabharata 5.1517, Huehuetlahtolli, Florentine Codex) plus per-tradition oral rows for Shawnee,
Cherokee, Nez Perce, Lakota, Tewa, Zuni, Ethiopian and Nguni — then re-link `source_id`. Quote text
is untouched; the validator runs before and after. Sequenced **AFTER W1** (it writes `sources.csv`,
read-only during W1). Rejected: (a) only the three works — leaves 9 rows permanently badged;
(b) leaving all 14 — permanent badge noise, manifest stays incomplete.

## 2026-09-12 — D8 (legacy hygiene): the cheap deterministic subset now, the `_` rows left to the operator

Do the cheap deterministic subset of legacy hygiene: retype the ~10 Roman-numeral Gleanings rows
and the paraphrase-shaped rows 31/267 out of `item_type = unknown`, and document the 27-value
tradition list as the controlled list. Leave the 4 rows with a literal `_` placeholder (ids 1, 16,
314, 320) for the operator, who must supply the real character — guessing stays forbidden by the
2026-09-11 decision. Do **not** widen `item_type`. Sequenced **AFTER W1** (writes `quotes.csv`).
Rejected: (a) leaving all hygiene to post-W1 tools; (b) doing the `_` rows now by guessing.

## 2026-09-12 — D9 (H2B-B lane): open the bahai-homepage consume lane against the v1 export

The `bahai-homepage` consume lane (H2B-B) is **OPENED** against the v1 export at
`exports/bahai-homepage-preview/v1/collection.json` (4 verified rows), rather than widening the
donor set first. Rationale: it closes the loop the v1 export was built to prove and surfaces the
real contract questions (issue #4 `source_url`, the D5 spelling above) with four rows instead of
forty; it lives in a different repo, so Garden's frozen data is undisturbed. This is a **lane
authorization, not work performed in Garden**. It supersedes the "do not start H2B-B" posture in
`docs/queue.md`.

## 2026-09-12 — D10 (two small gates): fix the card-view empty state (#17) and move CI off the deprecated Node 20 action majors (#19), before W1.1

Two small gates are authorized for **immediate fix**, both landing BEFORE W1.1 starts so they are
part of W1's pre-W1 baseline (W1's rule is that the CSVs stay byte-identical and the browser keeps
working; the browser change must keep the smoke test and validators green):

- **(a) issue #17** — card view has no empty state at zero matches (measured 2026-09-12:
  `resultChildren=0, resultsText=''` while table view explains itself). Authorized for immediate
  fix.
- **(b) issue #19** — move CI off the deprecated Node 20 action majors. Authorized for immediate
  fix, with live re-verification of the Pages deploy.

Rejected: deferring both into W1 or later — #17 is a browser behaviour change plus a smoke
assertion, and #19 touches the deploy path, so neither belongs inside a corpus-program unit whose
job is intake and curation.

## 2026-09-12 — The empty-result message is one constant, and the empty-state check compares the two views to each other

Fixing issue #17 required choosing where the message lives now that two views render it.
Considered leaving the table's literal in `renderTableRows()` and adding a second literal for the
card branch — smallest diff, and the new check could have asserted each against its own copy.
Rejected: two literals is exactly the drift the issue is about, and a per-view assertion would keep
passing after a one-sided edit. Decided on a single `EMPTY_STATE_MESSAGE` constant referenced by
both branches, with the smoke check asserting the card-view text EQUALS the table view's (with a
substring anchor on "No matching quotes." so the run output stays pinned). Presentation follows the
table's existing `.empty-state` conventions plus `grid-column: 1 / -1`; an empty result must not
introduce horizontal overflow at 320px, measured rather than assumed. Teeth: two negative controls,
each turning the run red with a targeted FAIL line and no traceback.

## 2026-09-12 — CI moves to the current action majors; the repo-root artifact path is left alone

Issue #19 authorized moving CI off the deprecated Node 20 action majors. Decided to bump **all
five** actions in both workflows — `actions/checkout` v4→v7, `actions/setup-python` v5→v7,
`actions/configure-pages` v5→v6, `actions/upload-pages-artifact` v3→v5, `actions/deploy-pages`
v4→v5 — rather than only the two GitHub had annotated (`checkout`, `setup-python`): the
re-verification cost is identical once the deploy path is exercised live, and the three Pages
actions were several majors behind as well, so leaving them would have queued the same work again
without changing the risk.

The release notes were read before choosing the target majors, and they matter: `upload-pages-artifact`
v4 dropped dotfiles from the published artifact and v5 only **adds** an opt-in `include-hidden-files`
input (default false), so the repo-root dotfile-exclusion claim still reads true in intent; and
`deploy-pages` v5.0.0 moved to Node 24.

Acceptance signal, deliberately the same shape as the 2026-09-11 live acceptance: the Node 20
deprecation annotation **disappeared** from PR [#22](https://github.com/mschwar/Garden-of-Wisdom/pull/22)
check run [34715295423](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715295423)
(success), then a green `main` smoke run
[34715362562](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715362562) and a green Pages
deploy run [34715362601](https://github.com/mschwar/Garden-of-Wisdom/actions/runs/34715362601), with
full live acceptance passed (`/`, `/browser/index.html`, `/quotes.csv`, `/sources.csv` all 200; live
CSV `sha256`s identical to the repo).

Deliberately **not** touched: `path: '.'`, the `pages` concurrency group, the `github-pages`
environment and the `refs/heads/main` deploy guard. Those are the repo-root contract the page's
relative `../quotes.csv` / `../sources.csv` fetches depend on, and #19 is a version bump, not a
deploy-path redesign.

Honest note on evidence: the authoring child **timed out before producing its handoff**, so the
parent verified the work and authored the handoff. Self-reports are not evidence here — the runs
above were re-checked directly against the GitHub API, not taken from the child's summary. That
verification also surfaced a separate, pre-existing defect: the Pages artifact publishes the
repo-root `.gitignore` (live, 200) despite the workflow comment claiming top-level dotfiles are
excluded. It is **not** a regression from this bump (the pre-bump artifact from run 34713537851
already contained `./.gitignore`). Filed as issue #23 rather than fixed here, because a fix is a
deploy-path change that needs its own live re-verification.

## 2026-09-12 — D2 executed (W1.1): SQLite + text export, and the requirement each rejected option failed

W1.1 implemented D2 and recorded the comparison it requires. Chosen: **SQLite** (stdlib
`sqlite3`, no dependency) as the store of record with a committed deterministic text mirror
(`garden.export/1`). It satisfies all eight storage/access requirements of
`docs/program/W1_DECOMPOSITION.md` §"Storage and access requirements W1 actually has" with one
file and one code path, and the export keeps the store diffable in git. Naming the requirement
each rejected option failed:

- **Plain JSONL/CSV files + git as the store of record** fails **requirement 1** (immutable
  captures) and **requirement 4** (append-only decision log): with the files as the store, both
  guarantees become conventions — git records that a capture or an audit row was rewritten but
  nothing refuses the write.
- **JSONL files as the store + a rebuildable SQLite index** fails the same two requirements for
  the same reason (the enforced store is still the files) and adds a second write path plus a
  rebuild-determinism burden for no W1 gain. It remains the **upgrade path** if the operator
  later wants the decision log diffable in git from day one.
- **A server database (PostgreSQL/MySQL/document store)** fails **requirement 7**: the operator
  must be able to work with no daemon and no network, and a server is a deployment, not a store.
- **Widening `quotes.csv` with capture/state/decision columns** fails **requirement 1** (no
  capture row is representable), **requirement 4** (a CSV rewrite is not append-only) and
  requirement 8's "untouched" clause, and it would mutate the frozen, documented-lossy view —
  the same reason D5 refuses the rename.
- **SQLite with no text mirror** fails **requirement 7** (human-readable, diffable) and
  **requirement 8** (export to text): the export is part of the decision, not an add-on.

Implemented as `scripts/garden_store.py` (DDL + idempotent create-from-empty migration +
export/import CLI) with `scripts/check_garden_store.py` as the deterministic acceptance run
(59 checks: create → write → read back → export → wipe → re-import byte-identical, migration
idempotency, capture immutability and decision-log append-only enforced by triggers, the four
`STATE_MODEL.md` vocabularies re-parsed from the document, and requirement 6's two queries at
~2,000 rows). Eight negative controls are recorded in `GARDEN_W1_1_HANDOFF.md` — seven from the unit and one added by the reviewing session, which found the first version guarded only one of the four state columns' `CHECK` constraints (removing the `research_state` `CHECK` left the run green); the loop over all four columns is the fix. Details:
`docs/program/W1_1_STORAGE_AND_SCHEMA.md`. This executes the D2 decision; it does not
supersede or amend it.
