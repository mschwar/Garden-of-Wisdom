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
