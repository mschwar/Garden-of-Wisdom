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

## 2026-09-12 — W1.2 (envelope): canonical JSON form, one rule id per defect, and no store migration in W1.2

W1.2 implemented the `garden.candidate-envelope/1` contract
(`docs/program/CANDIDATE_ENVELOPE.md`) as a serialized form plus a validator for rules 1-6, and
ruled on the three questions implementing it actually raised.

**1. The serialized form is canonical JSON with `sort_keys=True` and `allow_nan=False`.** One
envelope is one JSON object: keys sorted (so key insertion order cannot change the bytes),
compact separators, `ensure_ascii=False` so UTF-8 stays UTF-8 rather than `\u` escapes, and no
export-time state, so it is a pure function of the envelope. `allow_nan=False` is the deliberate
part: a value the canonical form cannot represent (the `Infinity` a JSON reader makes of
`1e999`) is a **refusal**, not an `Infinity` literal nobody can re-parse. Rejected: a
newline-terminated pretty-printed form (diff-friendly but not canonical — two equal envelopes
could serialize differently), and `allow_nan=True` (which would let rule 6's own round-trip
succeed on a value that is not valid JSON).

**2. Each broken check reports exactly one rule id, and the rule boundaries are drawn so one
defect has one id.** Rule 1 owns out-of-vocabulary values and missing/empty/ill-typed required
fields; rule 3 owns in-vocabulary-but-non-intake state values, so `curation_state: "maybe"` is
rule-1 while `curation_state: "accepted"` is rule-3, never both. `captured_text` non-emptiness
belongs to rule 2 alone, so rule 1 does not also flag it. Rule 5 compares UTF-8 **bytes**, and a
`captures=None` call reports rule 5 rather than silently skipping it — a check that does not run
is worse than no check. Rejected: letting a defect report several rules (it would make the
"fixture X reports exactly rule Y" assertion — the only thing that proves the rule ids are
carried — impossible to state).

**3. W1.2 adds NO store migration.** W1.1's handoff anticipated that W1.2 would add the optional
envelope fields (`source_link_state`, `placeholder_markers`, `provenance_chain`, ...) as a new
migration id. W1.2 declines. Of the nine optional fields only `external_id` has a column today;
adding the rest means a `0002` migration, and W1.1's acceptance suite asserts the migration
ledger is exactly `["0001_create_core"]`, so a W1.2 migration would turn W1.1's run red unless
W1.1's own acceptance assertions were edited — i.e. a storage-schema decision (W1.1's lane) plus
an edit to another unit's evidence, taken inside the envelope unit. Instead: the serialized form
carries all nine losslessly, the store persists the 21 **required** fields, a stored envelope
reads back intact and re-validates, and the optional-field persistence gap is filed as open work
in `docs/queue.md` (to be closed by whichever unit first needs the columns, likely W1.4 for
`placeholder_markers`/`provenance_chain`). Rejected: (a) the `0002` migration plus relaxing W1.1's
ledger assertion; (b) inventing a generic `extra_json` column to avoid naming the fields (it
would make the store schema a bucket and hide which fields the contract actually has).

Also decided in W1.2: the envelope carries no candidate identity, so `store_envelope` requires the
caller to supply `candidate_id` rather than inventing a derivation the contract does not declare;
`normalization_notes` may not be a bare sentinel (a sentinel is absence, and the contract requires
an assertion even for a no-op); and the module's CLI is a read-only diagnostic (`serialize` /
`validate` over a file) — it creates no capture and records no decision, because the intake
surface is W1.3. Implemented as `scripts/garden_envelope.py` with
`scripts/check_garden_envelope.py` as the deterministic acceptance + evidence run (99 checks, 15
negative controls recorded in `GARDEN_W1_2_HANDOFF.md`). Details:
`docs/program/W1_2_ENVELOPE_VALIDATOR.md`.

## 2026-09-12 — W1.2 review (QA): three validator paths were unguarded; three failing fixtures added (99 → 102 checks)

Independent QA by a separate session from the author — the same relationship as the W1.1
reviewer — found that three code paths in `scripts/garden_envelope.py` had no failing fixture,
so a mutation disabling each left the whole `check_garden_envelope.py` run green: the
`intake_schema_version` value check in rule 1 (no fixture had a wrong schema key), and rule 4's
undeclared-keys and non-object-hint checks (no fixture had a hint with extra keys or a bare
non-object element). This is the same class of coverage gap the W1.1 reviewer found (the
`research_state` `CHECK`), and it is fixed the same way: three otherwise-valid failing fixtures
(`wrong-intake-schema-version`, `hint-extra-keys`, `hint-not-an-object`) added to
`docs/program/fixtures/envelope_fixtures.json`, taking the suite from 99 to **102 checks** and the
invalid-fixture set from 20 to 23. No validator behaviour changed. Re-run of the reviewer's four
independent mutations confirmed all three paths now go red and zero coverage gaps remain.
This supersedes the "99 checks" sentence in the W1.2 entry above; the validation contract itself
is unchanged. Recorded in `GARDEN_W1_2_HANDOFF.md` §"Review finding (independent QA, landed in review)".

## 2026-09-13 — W1.3 (submission CLI): the record-id scheme, the normalization boundary, the store location, and no populated mirror yet

W1.3 is the first surface in the corpus program that writes. It owns the candidate-id naming
scheme (W1.2 §5.2 left it open) and the canonical store location (W1.1's handoff left it open), and
it had to draw the line between "submit" and "normalize" without implementing W1.4's algorithm.
The implementation is `scripts/garden_submit.py` with `scripts/check_garden_submit.py` as the
acceptance + evidence run (**134** checks, 15 negative controls + a separate 5-mutation review
pass). Details: `docs/program/W1_3_SUBMISSION_CLI.md`.

**1. Record ids are `cap-YYYY-MM-DD-NNNN` and `cand-YYYY-MM-DD-NNNN`, derived by scanning the
store.** The day is the **capture** day (`captured_at`'s date), not the wall-clock day the command
ran, so a submission recorded with an explicit historical timestamp is numbered on its own day and
a different capture day gets its own `0001` sequence. `NNNN` is one greater than the highest number
already used for that kind on that day, read out of the store itself. An explicit
`--capture-id` / `--candidate-id` is honoured; an id the store already holds is **refused before
anything is written**. Rejected: (a) a counter table (a second source of truth for an id the store
can already derive); (b) a random or UUID suffix (no day grouping, not diffable, and not
reproducible — the acceptance run asserts determinism by computing the next id twice and then
checking the CLI allocates exactly it); (c) re-using an existing `capture_id` to attach a second
candidate to a stored capture, which the contract permits (invariant 3) but which rule 5 cannot
police — rule 5 compares only `captured_text` (W1.2 §5.1), so a restatement could disagree with the
stored record on attribution and still validate. W1.3 therefore creates exactly one capture per
submission and refuses to restate one; the multi-capture path belongs to the unit that needs it.

**2. The normalization boundary: W1.3 performs no normalization, and enforces "no normalization
without a note".** `candidate_text` / `candidate_author` / `candidate_source_ref` default to the
captured values, so a plain submission records `normalization_notes: identical to capture` — an
assertion that every normalization is accounted for, made by saying there is none. A value that
differs from the capture without `--normalization-notes` is refused, naming both
`normalization_notes` and the field it would have changed; with a note it is accepted and the
capture stays byte-identical (the proposal is stored *alongside* the encounter). Rejected: (a)
implementing whitespace/quote/diacritic normalization here — it is W1.4's algorithm and W1.4 is the
unit that can iterate on it, thresholds and all; (b) "normalizing only the obvious cases" as a
convenience, because an unrecorded transform is exactly what `PROVENANCE_AND_CAPTURE_CONTRACT.md`
forbids. W1.4 replaces the default with a real transform and must keep the invariant.

**3. An omitted flag becomes the field's declared sentinel; a flag supplied *empty* is passed
through untouched so the validator names the field.** `--attribution` omitted →
`captured_attribution: "unknown"`; `--attribution ""` → `""` → `[rule-1] 'captured_attribution' is
empty; a sentinel … is not an empty string`. Rejected: treating an empty flag as "not supplied",
which would turn "the operator gave us nothing here" into a silent claim that the attribution is
unknown — a different and better-sounding fact. This is the mechanism behind the card's second
acceptance criterion and it is asserted by 5 refusal cases, each with its own "wrote nothing" check.

**4. The canonical store lives at `data/store/`: the SQLite file is git-ignored, the text export
beside it is the committed mirror.** `data/store/garden.sqlite3` is machine-local and not diffable;
`data/store/garden.export.txt` (`garden.export/1`) is the mirror W1.1's decision describes, and a
diff of it is a per-record diff. Rejected: committing the database (an opaque binary in the history
of a repository whose entire audit story is textual), and keeping the store outside the repo (the
diffable mirror is the whole point of the split).

**5. W1.3 commits NO populated mirror — a deliberate deviation from W1.1's handoff.** W1.1
anticipated that "the first commit of a populated mirror belongs to the first unit that writes real
submissions (W1.3)". W1.3 declines the *timing* while making the location ruling above. At this
unit's stop point the only submissions that exist are its own test fixtures, and they live in a
throwaway temp directory by design: the acceptance run must pass from a clean clone with no
committed data, which is exactly what W1.6's Gate B packet requires. Committing fixture submissions
into the store of record's history would put review scaffolding into the corpus, and W1.6 would have
to unwind it. The first **real** operator submission populates the mirror, and Gate B is where an
evidence store demonstrating it belongs. Nothing about the mechanism is deferred — only the first
populated commit, and to the unit that will have real content.

Also decided in W1.3: `captured_by` defaults to `operator` (a reading of the contract, matching
`garden_store.add_capture`'s own default, recorded so a reviewer can require it to be explicit
instead); a submission with `--candidate-author ""` and no note is refused naming
`normalization_notes` rather than silently accepted, because a value that differs is a
normalization whether or not it looks like one; the manual surface exposes **no** flag for any of
the nine optional envelope fields — eight have no store column (W1.2's filed gap) and `external_id`,
which does, is left to the adapters that will need it, because a flag that accepts a value the
store cannot hold is a silent drop; and the `captured_at` offset check is deliberately duplicated
between the submission surface (which derives the ids from the stamp's date) and rule 1, with the
acceptance run asserting the layering so the earlier check has a unique falsifier (it did not, until
control n14 found it).

## 2026-09-13 — W1.4 (normalization + hints): the algorithm, the threshold, specificity, and no migration

W1.4 owns the deterministic intake transform and the duplicate-hint generator. Four decisions, each
with the rejected alternative recorded.

**1. The normalization algorithm is a closed, declared list — and every change is counted.**
`garden.normalize/1` = Unicode NFC recomposition, then four canonical-character classes (quote marks,
dashes, ellipsis, no-break spaces) applied **one class at a time**, then whitespace runs collapsed to
one space and boundary whitespace trimmed. Rejected: a general "smart punctuation" pass, or
`str.translate` with the union of the class tables. The union is not just untidy — it converts a
later class's characters while attributing the count to the first class that fired, so the note
silently **under-reports**; the acceptance run counts each class independently and caught it
(control `n6`). Also rejected: touching anything not on the list (guillemets, a trailing
`— Rumi` attribution line, the literal `_` placeholder). Guessing the placeholder's character stays
forbidden (2026-09-11), so the proposal keeps the `_` and the note says it was preserved.

**2. The similarity threshold is 0.60, and the score is the *mean* of the two directional
`difflib` ratios.** 0.60 matches the legacy validator so the repo's 45 near-duplicate pairs remain
usable as reference data. The mean is a correction, not a preference: `SequenceMatcher.ratio()` is
asymmetric (rows 113/114 score 0.69 one way and 0.67 the other), so a raw ratio makes a pair's
reported number depend on which candidate is being compared and lets the two candidates disagree
about their own pair. Rejected: keeping the raw ratio and documenting the asymmetry. The cost is
that a basis number can differ from the legacy report's by a hundredth; that is recorded rather than
hidden, and the legacy report's own direction-dependence is filed separately because the D6 curation
pass will re-derive those pairs.

**3. A shared citation is evidence only when the citation pinpoints something.** This is the fix for
the false-positive class `docs/data/DATA_QUALITY_REPORT.md` names: 19 rows share the literal
`source_ref` `"Oral Tradition"` and get flagged against each other although the quotes are
unrelated. `same-reference`/`same-passage` now require a citation carrying a **locator** (an Arabic
digit, a Roman-numeral token, or `§`); `none`/`unknown`/`und`/`""` is not a citation at all; a bare
work title is `generic`. Rejected: reproducing the legacy predicate (equal `source_ref`) — it is the
noise the hint exists to remove — and rejected a curated allow/deny list of known-generic labels,
which is arbitrary and would rot. The rule is strictly narrower than the legacy report's split
(it also suppresses a shared bare work title, e.g. three rows of
`Tablets of Bahá’u’lláh, Words of Paradise`), because "same work" is not "same passage"; a missed
hint is cheap, a wrong duplicate decision is expensive. Also recorded: the legacy report compared
pairs within one `tradition`, the store has no `tradition` column, so hints compare every candidate
against every other — deliberate, because a duplicate can be filed under a different label.

**4. W1.4 adds NO migration, so `placeholder_markers` stays unstructured.** W1.2 filed that eight
optional envelope fields (including `placeholder_markers`) have no store column, and W1.3's handoff
guessed W1.4 would be the unit to need one. W1.4 needs the placeholder *observation*, not a
structure: `normalization_notes` exists, its contract is "what changed and why", and it carries
"`1 literal '_' preserved (not repaired…)`". Adding columns with no consumer would be a speculative
schema change in an ingestion-lane unit, and it would have forced W1.1's acceptance run to relax its
exact ledger assertion (`["0001_create_core"]`). Rejected: adding migration `0002` now. The
persistence gap stays filed; the unit that first *consumes* those fields structurally owns the
migration and the ledger-assertion change together.

Also decided in W1.4: an explicit `--candidate-id` that cannot be normalized is a refusal, while an
`--all` run skips such a candidate with a named `SKIPPED:` line — because a whitespace-only
submission is legal at intake and there is no withdrawal path anywhere in W1, so one junk row must
not make the batch unusable; but a batch that can normalize **nothing** fails, since a run that
writes nothing must not report success. And both guard layers (`proposal_for` before the write, and
`garden_store.apply_normalization` at the write) are kept and asserted separately: the surface's
pre-check is what makes a batch all-or-nothing, and the store's is what makes the write path safe for
any future caller. Control `n11` showed the store layer unproven until the suite called it directly —
the same class of gap W1.3 recorded for `captured_at`, found the same way.

## 2026-09-13 — W1.5 (curation review): a single atomic write gate, the reversal path, research read-only, and no migration

W1.5 is the loop's payoff: the operator-facing `accept / hold / reject / duplicate / reopen`
surface, where a curation decision is a recorded, audited transition — never a silent state flip. The
implementation is `scripts/garden_review.py` (the CLI) on top of a new store write gate
`garden_store.Store.curate`, with `scripts/check_garden_review.py` as the acceptance + evidence run
(**246** checks, both interpreters; an 8-mutation same-session review pass, all recorded in
`GARDEN_W1_5_HANDOFF.md`). Details: `docs/program/W1_5_CURATION_SURFACE.md`. It falsifies the
carried-forward risk from `W0_GATE_REPORT.md` — *"the reversal rule (T-C8 → T-P7) is legal on paper
but untested against a real store"* — by exercising both reversal paths against the real store and
asserting no dimension is stranded.

**1. Every curation decision goes through ONE atomic write: `Store.curate`.** It looks the legal
T-C1…T-C12 transition up, computes the required corpus follow-on, updates `curation_state` (and
`corpus_state` when a follow-on fires), and appends every audit row — the curation row and each
corpus row — **in one SQLite transaction**, so there is never a window in which a state changed
without its audit row. Rejected: a state UPDATE and a separate `record_decision` call, because two
commits would create exactly that window. `record_decision` was refactored into a non-committing
`_insert_decision` helper so `curate` can drive the whole thing transactionally; the public
`record_decision` still commits and still passes W1.1's suite byte-for-byte.

**2. Acceptance fires T-P1 `candidate_only → eligible` (authority `system`); a withdrawn acceptance
fires T-P7 `eligible → candidate_only` (authority `operator`) — the reversal strands no dimension.**
Becoming `accepted` is the deterministic, audited eligibility-for-a-wanted-record, never "true"
(`STATE_MODEL.md` §3). Leaving `accepted` (`T-C8` → `rejected` / `T-C9` → `duplicate`) while the
record is `eligible` fires T-P7 back to `candidate_only`, so no record ever has
`curation ∈ {hold, rejected, duplicate}` with `corpus = eligible`. The acceptance run asserts that
invariant over every candidate after every transition. Note: rejecting from `new`/`hold` does **not**
retire the record (`T-P3 candidate_only → retired`) — T-P3 is an operator promotion decision and out
of W1.5 (the walkthrough's branch B adds it as a *separate* later decision), and rejection keeps the
capture and the candidate readable, exactly as the acceptance criterion requires.

**3. No curation action writes research state — it is rendered read-only and always `not_started`.**
`curate` updates only `curation_state` and `corpus_state`; there is no research write path and no
research surface. Asserted after every curation action, on every fixture and transition candidate,
and a mutation that makes `curate` set `research_state = 'in_research'` turns the run red.

**4. The machine-inferred-vs-asserted marker is rendered, not hidden.** The queue view labels the
capture `asserted (the verbatim encounter)`, the proposal `derived (deterministic normalization of
the capture)`, the notes `asserted (what changed and why)`, and the duplicate hints
`machine-inferred (a hint is evidence, never a decision)` — invariant 6 of `STATE_MODEL.md`, made
visible where the operator reads it.

**5. W1.5 adds NO migration.** The `decisions` ledger, the four state columns, and the append-only /
immutability triggers all exist from W1.1; W1.5 only adds code. W1.1's exact-ledger assertion
(`["0001_create_core"]`) is untouched, and `quotes.csv` / `sources.csv` are byte-identical
before/after every W1.5 run.

**6. The "one guard per layer" lesson W1.5 had to relearn — and gave the guard its own falsifier.**
The store-layer empty-reason guard is backed up by `_insert_decision`'s own empty-reason check, so
removing `curate`'s guard in isolation left the suite green (the backstop masked it) — the same class
of masking the skill warns about. The acceptance run now asserts the **layering**: it looks for
`curate`'s distinctive wording (`every curation decision must carry a reason`) rather than the shared
substring, giving the surface's guard a unique falsifier.

**Also decided in W1.5:** an omitted `--actor` records the decision as `operator` (fallback identity,
never anonymous); `--reason` is required and refused-empty before anything is written; a refused
decision (illegal transition, missing candidate, empty reason) writes nothing at all (asserted,
store byte-identical); the read-only commands (`queue`, `show`, `audit`) never write; and a
candidate deposited before normalization is shown as-is — the operator runs `normalize --all` /
`hints --all` before reviewing (W1.6's end-to-end does exactly this), which is why the design relies
on the pipeline in `docs/RUNBOOK.md` rather than forcing it at review time.

## 2026-09-13 — W1.5 lesson for the CI gap: the review surface is a sixth command, and its suite is a fifth acceptance suite

W1.2 filed that CI does not run the W1 acceptance suites; W1.3 and W1.4 re-filed it as the count
grew. W1.5 leaves it open again, now over **five** deterministic, stdlib-only, exit-0/1 suites —
`check_garden_store.py` (59), `check_garden_envelope.py` (102), `check_garden_submit.py` (134),
`check_garden_normalize.py` (232), `check_garden_review.py` (246) — and a sixth surface
(`garden_review.py`) that none of them protect from a future regression. It is still a change to the
guarded `browser-smoke.yml` workflow and was not fixed as a side effect of an ingestion/review unit.

## 2026-09-13 — W1.6 (Gate B pack): the loop is one reproducible command; W1 is complete

W1.6 is the wave gate, not a new surface. It ships `scripts/check_garden_e2e.py` — a
deterministic, clean-clone, one-command acceptance run (**96** checks, both interpreters) that
drives the whole loop through the real W1.3/W1.4/W1.5 CLIs inside a throwaway temp dir and asserts
the Gate B pass condition. Details: `docs/program/W1_6_E2E_TEST_PACK.md`; the evidence package is
`docs/program/W1_6_GATE_B_PACKET.md` (mirroring `W0_GATE_REPORT.md`'s shape).

**1. The messy batch is real corpus + controlled mess.** The e2e reads row 320 (a literal `_`
placeholder glyph) and row 21 (a curly apostrophe) **verbatim from `quotes.csv`**, so the loop is
proved against the corpus's own awkward bytes, not a toy; plus a wrong author, leading/trailing
whitespace, a missing citation (omitted flag → `none` sentinel), a near-duplicate pair (must
produce a hint) and two unrelated rows sharing the generic `Oral Tradition` label (must produce **no**
reference hint — the W1.4 false-positive fix). Nothing is hard-coded; a fixture that stops narrowing
fails loudly rather than passing vacuously.

**2. "No curation action implies verification" is asserted, not just documented.** After every
decision the e2e asserts every candidate's `research_state` is still `not_started`, that no decision
row writes or implies a research state, and that corpus stays in the W1 vocabulary
(`candidate_only`/`eligible`) — nothing claiming truth. Control **c2** (a `curate` that writes
`research_state='in_research'`) turns the run red on exactly that check.

**3. W1.6 adds no migration and no populated store mirror.** The loop's reproducibility is proved
by the e2e's temp-dir round-trip from a clean clone (`garden.export/1` write → import → re-export
byte-identical); a committed `data/store/garden.export.txt` is left to the first real operator
population (W1.3 decision), not synthesized here. W1.1's exact-ledger assertion
(`["0001_create_core"]`) is untouched.

**4. W1.6 keeps the "give each guard its own falsifier" lesson.** The e2e's round-trip check turned
out to be **backstopped** by `garden_store.import_bytes`' own internal re-export comparison: a
mutation that makes the import lossy goes red on the store's `StoreError`, not on the e2e's
round-trip `FAIL:` line (control **c5**, recorded as a finding). The e2e does not duplicate a guard
the store already proves; it is recorded in the handoff rather than papered over.

**5. W1 is complete; the Gate B packet is submitted.** Per `W1_DECOMPOSITION.md` and the wave
authorization (decision D1), W1 ends at the Gate B packet. **W2 is not started** — no research
surface, no promotion path, no migration. The carried-forward risks from `W0_GATE_REPORT.md` are
all falsified or green (see the packet's status table). The next authorized action is an
operator/frontier decision on **Gate B**, followed (if accepted) by authorization of **W2**.

## 2026-09-13 — Gate B frontier review: accept, no defects found

Independent review (`docs/audit/2026-09-13/GATE_B_FRONTIER_REVIEW.md`) re-ran
`scripts/check_garden_e2e.py` (96 checks), `validate_quotes.py`, and `check_program_contracts.py`
fresh from the working tree, recomputed `quotes.csv`/`sources.csv` hashes, cross-checked the
quoted Gate B and W1.6-acceptance-criteria text against `ACCEPTANCE_GATES.md` and
`W1_DECOMPOSITION.md` verbatim, and verified the PR #33 merge/CI/live-deploy chain independently
via `gh pr view`, `gh run view`, and `curl` rather than trusting the packet's own pasted output.
Also live-tested negative control c1: temporarily patched `garden_submit.py`'s `read_text` to
strip the submitted text, confirmed the e2e goes red on exactly the two checks the packet names,
then restored the file and verified `diff` showed no residual change.

Every claim in `docs/program/W1_6_GATE_B_PACKET.md` reproduced exactly. Unlike the Gate A review,
**no defects were found** — no stale numbers, no misquoted gate text, nothing resting on unbacked
assertion.

Verdict: **Gate B accepted**, 2026-09-13. Decided this acceptance does **not** authorize W2 — that
stays a separate, explicit operator decision per `W1_DECOMPOSITION.md`.

## 2026-09-13 — The near-duplicate score is a property of the pair, and the sweep stays per-tradition

Fix for issue [#31](https://github.com/mschwar/Garden-of-Wisdom/issues/31), executed as its own unit
(branch `fix/validator-symmetric-similarity`, PR #35). `scripts/validate_quotes.py`'s near-duplicate
heuristic scored each candidate pair with **one directional** `difflib.SequenceMatcher.ratio()` call.
That ratio is asymmetric, so the number a pair was reported with was a function of which row was
visited first, and a pair straddling the `0.60` threshold could appear or disappear outright rather
than merely shift. Measured on the frozen corpus: `113 ~ 114` scores `0.6888…` one way and `0.6666…`
the other; `189 ~ 216` crosses the threshold in one order (`0.6023`) and not the other (`0.5909`).

**1. The score is the mean of both directional ratios.** This is the rule W1.4's store-side hint
generator already adopted (`docs/program/W1_4_NORMALIZATION_HINTS.md` §3 ruling 1), so the validator
and the store now agree about what a pair's similarity is. The rejected alternative — "canonically
order the pair, then score it once" — was rejected because it makes the score depend on the
canonicalisation (id order? text order?) rather than on the pair, which is the same defect wearing a
different hat. The consequence is recorded rather than hidden: the frozen report's number for
`113 ~ 114` moves `0.69` → `0.68`, which W1.4's design doc had already predicted to the hundredth.

**2. The validator hard-fails on an order-dependent result.** A second detection pass over the same
rows with every tradition's rows reversed must produce an identical pair set *and* identical reason
strings, otherwise the run exits 1. An order-dependent number is a **correctness** bug, so it is not
parked as curation signal — and it is a defect this repo actually shipped, so it gets a guard rather
than a note. The guard is a hard failure in the validator, which is in CI (`browser-smoke.yml` runs
it), so the class cannot return silently. Control `c1` (revert the scorer to one directional call)
turns the run red with exactly the difference the issue described, including the membership flip on
`189 ~ 216`; control `c2` (the same mutation plus the guard disabled) is green, which is what proves
the guard — and not something else — is the catcher.

**3. A shared citation that also clears the text threshold now reports its number.** The old loop
`continue`d on a shared `source_ref`, so a pair sharing a pinpoint citation *and* reading nearly
identically threw away the second, independent piece of evidence. The pair count does not move (the
number is appended to the existing line), and a second hard check re-derives each printed reason from
the rows so the annotation cannot be dropped silently (control `c3`).

**4. The sweep stays scoped within one `tradition` — decided *with* the measurement, not before it.**
Corpus-wide, the same rules flag **196** pairs instead of **45**. Of the 151 additions, **146** are
the same bare `Oral Tradition` label matching unrelated rows across traditions (the documented
false-positive class), so widening now would bury the signal in the curation queue this feeds.
The rejected alternative was to widen *and* apply W1.4 ruling 2's locator test in the same pass — a
coherent design, but it silently redefines what the queue's D6 item is looking at, and #31's own
re-count (15 pairs to inspect / 30 to skip) is defined against the current scope. Filed as
[#34](https://github.com/mschwar/Garden-of-Wisdom/issues/34) with the numbers, including the 5
cross-tradition text pairs the scoped sweep cannot see at all — the strongest being
`39` (Christianity) ~ `53` (Judaism) at 0.82, the same commandment in two traditions.

**5. The frozen evidence was extended, never rewritten.** `docs/data/DATA_QUALITY_REPORT.md` keeps its
2026-09-11 transcript byte-identical (`git diff` shows **0 deleted lines** in that file) and gains a
dated re-derivation section carrying the verbatim fresh transcript, the exact pair-class table
(2 text-only + 13 pinpointed-citation + 25 bare-label + 5 work-level = **45**), and the two decisions
above. The validator writes nothing; `quotes.csv` / `sources.csv` stay byte-identical
(`5675d7e6…` / `10b4c156…`). The queue's D6 item was re-counted from its approximate `~22` / `~23`
split to the re-derived **15 to inspect / 30 to skip** — a stale count in a queue item is a defect of
the same class as a stale number in the report.

**Known limitation, recorded not papered over:** the *scope* has no automated falsifier. Control `c4`
(widen the sweep to the whole corpus) leaves the suite green, because a wider sweep is still
internally consistent; the only detector is the `45`-pair count in the transcript and the D6 re-count
that cites it. That is why the count is called out as the tripwire in both the report and the queue.

## 2026-09-13 — Never write a closing keyword with an issue number into a PR or commit body

Process convention, learned the expensive way during #31's close-out. The unit's handoff
(`GARDEN_VALIDATOR_SYMMETRY_HANDOFF.md`) is used **verbatim as the PR body**, and its "Exact next
Prompt" section contained the phrase `close #34` — a sentence telling a future session how to *decline*
that issue. GitHub parses `<closing keyword> #N` anywhere in a PR body as a closing reference, so
merging PR #35 marked issue #34 **COMPLETED** with nothing done, at the same moment the merge landed.
#34 was reopened with that explanation rather than silently re-filed (a re-filed issue loses the
comment trail and hides the cause).

**The rule:** never write a closing keyword (`close`, `closes`, `closed`, `fix`, `fixes`, `fixed`,
`resolve`, `resolves`, `resolved`) followed by `#N` for an issue you want to stay open — not in the
handoff, not in the commit message, not in any prose that will be reused as a PR or commit body. Write
"record #34 as \"no change\"", not "close #34". The failure mode is subtle because the text is *about*
the issue rather than an action on it, and it fires later, at merge time, on a different issue than the
one the PR is about. A repo-wide grep for
`\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b[:\ ]*#[0-9]+` is the cheap check before opening a PR.
