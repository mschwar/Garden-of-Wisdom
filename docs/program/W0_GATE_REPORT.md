# W0 Gate Report — doctrine and contracts (Gate A)

Date: 2026-09-12. Branch: `docs/garden-corpus-w0-doctrine`. **W1 NOT STARTED.**

This is the evidence package for Gate A (`ACCEPTANCE_GATES.md`). Claims below are backed by
the commands and outputs in §Evidence, not by assertion.

## What landed

Canonical doctrine under `docs/program/` (this directory):

| Doc | W0 required output |
|---|---|
| `CORPUS_PROGRAM_DOCTRINE.md` | 1. program doctrine reconciled with existing product doctrine (8-recorded rulings) |
| `SYSTEM_MODEL.md` | 2. entity/system model |
| `STATE_MODEL.md` | 3. orthogonal state model + transition authority + invariants + projection into today's CSV |
| `PROVENANCE_AND_CAPTURE_CONTRACT.md` | 4. provenance/capture contract |
| `CANDIDATE_ENVELOPE.md` | 5. candidate-envelope contract |
| `VERIFICATION_CONTRACT.md` | 6. verification/evidence contract |
| `WORK_LANES.md` | 7. permanent work-lane definitions |
| `CLASSIFICATION_AND_FACETS.md` | 8. faceted classification posture + 6 explicit open ontology questions |
| `W1_DECOMPOSITION.md` | 9. bounded W1 work units |
| this file | 12. W0 evidence-gate report |

Plus: 8 decision-log entries (`../DECISIONS.md`), queue entries for deferred ideas/debt
(`../queue.md`), a planning fixture (`fixtures/w0_scenarios.json`), a deterministic
doctrine-consistency checker (`../../scripts/check_program_contracts.py`), and pointers from
`../../README.md`, `../RUNBOOK.md`, `../product/PRODUCT_DOCTRINE.md`, `../../AGENTS.md`.

## Gate A criteria, item by item

| Gate A requirement | Where satisfied |
|---|---|
| Curation state and research/evidence state are explicitly separate | `STATE_MODEL.md` §1/§2 — separate dimensions, separate authorities, separate vocabularies; enforced by the checker (a curation transition cannot touch research state; there is no code path that can) |
| A source-agnostic candidate envelope is defined | `CANDIDATE_ENVELOPE.md` — `garden.candidate-envelope/1`, 21 required fields, 6 validation rules |
| Original capture provenance is preserved by contract | `PROVENANCE_AND_CAPTURE_CONTRACT.md` — captures immutable, raw fields never machine-written, normalization notes mandatory and enumerable |
| The verification contract says what evidence is sufficient | `VERIFICATION_CONTRACT.md` — witness classes, required locator, adjudication record, per-claim-kind standards, explicit insufficiency list |
| Disputed and unverifiable outcomes are first-class | `STATE_MODEL.md` §2 + per-claim aggregate rule; scenarios S1, S3, S4, S5, S7 terminate in `unverifiable`/`disputed` and are all *wanted, eligible* records |
| Faceted classification is the working model; no premature single enum hardened | `CLASSIFICATION_AND_FACETS.md` — 10 facets, multi-valued where they need to be; the 27-value tradition list is documented, not enforced or collapsed; 6 open questions recorded |
| W1 is decomposed into bounded work units with acceptance criteria | `W1_DECOMPOSITION.md` — W1.1–W1.6, each with lane, scope, out-of-scope, human gates, acceptance criteria, evidence, stop condition |
| No W1 runtime implementation has started | §"Non-implementation proof" below |

## Required scenario test — an uncited, possibly misattributed passage, end to end

The trace below is the machine-checked walkthrough in `fixtures/w0_scenarios.json`, simulating
against the transition table in `STATE_MODEL.md`. It uses S1's exact starting point (a
screenshot of a quote card with no author and no work) and shows **every plausible outcome**.

**Encounter.** A screenshot of a quote card reading *"We are the ones we have been waiting
for."* — no author, no work, no date. Capture: method `screenshot`, timestamp, by operator,
raw artifact retained.

**Step 0 — capture (`PROVENANCE_AND_CAPTURE_CONTRACT.md`).** `captured_text` stored verbatim;
`captured_attribution = unknown` (sentinel, not blank); the card's own non-source recorded in
`captured_citation`. Authority: whoever captured it. No truth claim exists yet.

**Step 1 — intake (`T-…` none; envelope only).** The envelope is built with
`curation_state = new`, `research_state = not_started`, `corpus_state = candidate_only`,
`work_state = queued`, `normalization_notes = "identical to capture; no attribution
invented"`, and one deliberately weak duplicate hint (`same-reference` against id 319, basis:
"same generic source_ref 'Oral Tradition'"). A hint is not a decision.

**Step 2 — curation, branch A: the operator wants it** → `T-C1 new → accepted`,
**authority: operator**. `T-P1 candidate_only → eligible` fires deterministically
(authority: `system`). Note what did *not* happen: the research state is still
`not_started`. Eligibility means "wanted", not "true".

**Step 2′ — curation, branch B: not wanted** → `T-C3 new → rejected` (operator), then
`T-P3 candidate_only → retired` (operator). The capture is retained; the passage is not in the
Garden; the decision and its reason are in the audit log. Nothing about truth was decided.
*(Branch C: `T-C2 new → hold` (operator) — deferred, no other state changes. Branch D:
`T-C4 new → duplicate` (operator) — only after the operator confirms the duplicate link; a
machine hint can never do this.)*

**Step 3 — research opens** → `T-R1 not_started → in_research`, **authority: agent**. The
agent may search freely. It may not conclude anything: the research state it can reach on its
own are only `in_research` and `needs_more_evidence` (`T-R2`/`T-R3`).

**Step 4 — research outcomes, all four terminal branches:**

- **S1 — verifiable?** No: no author, no work, no early witness; every occurrence traces to
  the same circulating text. → `T-R6 in_research → unverifiable`, **authority: operator**.
  Record state: curation `accepted`, research `unverifiable`, corpus `eligible`, uncertainty
  displayed. This is a *successful* outcome, not a failure — the system asserted nothing it
  could not support.
- **S2 — actually verifiable.** Had a witness been located (witness + locator + adjudication),
  → `T-R4 in_research → verified` (**authority: operator**, and the checker refuses this
  transition unless a research case actually ran). The same card could equally have been the
  G4 id-3 case, which is exactly how the four existing `verified` rows were produced.
- **S3 — the wording is real but the attribution is wrong.** → `T-R5 in_research → disputed`
  (operator). If the operator still wants it, `T-P2 eligible → canonical` (operator) admits it
  **while the attribution stays disputed**. This is the concrete counterexample to
  `canonical ⇒ verified`.
- **S4/S5 — wrong work, or a quote of a quote.** Same `T-R5` path; the *corrected* citation is
  a new recorded claim, the original wrong citation stays visible in the capture, and quote
  text is never edited.
- **S6 — a translation variant.** → `T-R4`: what is verified is that *this named translation*
  reads thus; sibling renderings coexist as one Passage (`translation-of`), not duplicates.
- **S7 — fabricated attribution.** No early witness exists anywhere → `T-R6` → `unverifiable`;
  retainable as a documented example of misattribution, never emittable as verified.
- **S8 — oral attribution.** → `T-R4` for the *documented rendering* + its context. The record
  makes no originality claim; if it did, that claim would be `unverifiable` and would drag the
  record down with it.
- **S9 — ambiguous source.** → `T-R2 in_research → needs_more_evidence` (agent) and it stops
  there honestly; `verified` is not available, so no pinpoint locator is invented.
- **S10 — paraphrase.** Verified as *a paraphrase* (`locus` + `shape`), with no `wording` claim
  at all — which is precisely why every surface showing it must mark it as a paraphrase.

**Step 5 — work state (execution, never truth).** `T-W1 queued → active` (agent),
`T-W2 active → qa` (agent), `T-W6 qa → done` (agent; a wave-gate unit additionally needs
operator acceptance). Work state stays `done` regardless of which truth outcome the record
reached — proving the dimensions are actually independent.

### Transition authority, every step

| Step | Transition(s) | Authority | Why |
|---|---|---|---|
| capture | — | capturer | recording an encounter asserts nothing |
| intake | — (envelope construction) | agent/operator | machine-inferred fields stay marked as such |
| curation decision | T-C1…T-C12 | **operator** | taste and admission are the operator's |
| eligibility | T-P1 | system (deterministic) | a consequence of curation, not a new judgement |
| research open / re-block | T-R1, T-R2, T-R3 | agent | searching is delegable |
| **terminal research outcome** | T-R4, T-R5, T-R6, T-R7, T-R8, T-R9, T-R10, T-R11 | **operator** | no agent may self-certify `verified`/`disputed`/`unverifiable` |
| canonical admission | T-P2 | **operator** | admission into the Garden, and it may admit disputed material |
| retire / re-admit | T-P3…T-P6 | **operator** | removal from and re-admission to the Garden |
| execution | T-W1…T-W7 | agent (T-W7: operator) | work state never answers a truth question |

## Non-implementation proof

- `quotes.csv` and `sources.csv` are **byte-identical** to `main` (§Evidence hashes), and were
  never opened for writing by any W0 artifact.
- `scripts/check_program_contracts.py` reads only `docs/program/STATE_MODEL.md`,
  `docs/program/CANDIDATE_ENVELOPE.md`, `docs/program/VERIFICATION_CONTRACT.md`, and
  `docs/program/fixtures/w0_scenarios.json`. It imports nothing from a store and exercises no
  intake, curation, or research behaviour.
- No datastore, no migration, no intake surface, no discovery adapter, no browser change, no
  schema change, no rename of `verification_status`.
- `git show --stat` on this branch touches `README.md`, `docs/**` (`program/`, `DECISIONS.md`,
  `queue.md`, `RUNBOOK.md`, `product/PRODUCT_DOCTRINE.md`), plus the one checker script and one
  JSON fixture. Nothing else — in particular no data, browser, export, or workflow file.
  (`AGENTS.md` was intentionally left untouched — see §Deviations.)

## Evidence

Baseline (main @ `2e3ef8a`, before any W0 change), recorded in the worktree:

```
$ python3 scripts/validate_quotes.py      -> exit 0, RESULT: PASS
$ python3 scripts/validate_homepage_preview_export.py -> exit 0
$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
```

After (same worktree, W0 docs present): the two validators and the two hashes are unchanged —
see the post-change block appended at the bottom of this file by the acceptance run.

Doctrine checker:

```
$ python3 scripts/check_program_contracts.py
parsed 38 transitions, 21 required envelope fields, 10 scenarios
vocabularies: corpus=4; curation=5; research=6; work=5

RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
```

Negative controls (run on a throwaway copy — a checker that cannot fail proves nothing):

| Mutation | Observed |
|---|---|
| S3 attribution claim forced to `verified` while the record stays `disputed` | `FAIL: S3: record research_state 'disputed' disagrees with the aggregate of its claims ('verified')` |
| `T-R5` authority flipped `operator → agent` in `STATE_MODEL.md` | `FAIL: S3/S4/S5: operator_transitions […] do not match the operator-authority transitions actually used` |
| S6 `normalization_notes` blanked | `FAIL: S6: envelope field 'normalization_notes' is empty` |
| S2 verified wording claim with its evidence list emptied | `FAIL: S2: claim 'wording' is verified with no evidence item` |
| Canonical case `paraphrase` deleted | `FAIL: canonical test cases not covered by any scenario: ['paraphrase']` |

Coverage: all ten canonical test cases of `STATE_MODEL.md` and all five Gate A requirement
kinds (`uncited`, `verified`, `disputed`, `unverifiable`, `translation-variant`) are exercised,
each case exactly once — asserted by the checker, not by hand.

## Decisions made (all appended to `../DECISIONS.md`)

1. Program doctrine lives under `docs/program/` and inherits `PRODUCT_DOCTRINE.md` by
   reference instead of restating or rewriting it.
2. Four orthogonal state dimensions are adopted; the current 3-valued
   `verification_status` stays as a compatibility projection, with its loss
   (`unverifiable → unverified`) documented rather than papered over.
3. Capture is a first-class, immutable entity going forward; the 324 legacy rows get no
   invented capture — their provenance is the frozen archive + git history.
4. Terminal research outcomes (`verified`/`disputed`/`unverifiable`) are human-adjudicated;
   agents may reach `in_research`/`needs_more_evidence` only.
5. `canonical` does not imply `verified`, and the 324 existing rows are the concrete proof:
   they are the canonical working set and mostly unverified.
6. Faceted classification; `tradition` stays single-valued and un-collapsed for now.
7. No datastore is chosen in W0; SQLite is a W1 hypothesis with explicit requirements.
8. W0 ships a documentation-consistency checker, not runtime.

## Unresolved questions / debt (queued, not implemented)

| # | Item | Why it is not settled |
|---|---|---|
| D1 | Storage technology for W1 | deliberately deferred to W1.1 with requirements written down |
| D2 | `unverifiable` is not representable in the current CSV enum | needs a migration unit; today it silently projects to `unverified` (issue #5 is the live instance) |
| D3 | Row-level verification evidence does not exist in the CSV | the four `verified` rows carry evidence only in the export + decision log |
| D4 | No capture provenance for the 324 legacy rows | policy question: does `legacy-import` ever get a synthetic capture record, or does the archive stay the only provenance? |
| D5 | `item_type` mixes shape and provenance shape | split is W3 work; do not widen the enum meanwhile |
| D6 | 6 ontology questions (Q1–Q6 in `CLASSIFICATION_AND_FACETS.md`) | vocabularies must be learned from real records, not legislated now |
| D7 | `verification_status` vs `verification_state` naming (issue #7) | interacts with the projection; resolve before more export/validator code hardens either spelling |
| D8 | No automated browser smoke test | pre-existing queue item, untouched by W0 |

## Proposed W1 work-unit order

`W1.1 storage decision + minimal schema` → `W1.2 envelope contract + validator` →
`W1.3 manual submission surface (CLI)` → `W1.4 normalization + duplicate hints` →
`W1.5 curation review + decisions + audit history` → `W1.6 end-to-end test pack + Gate B
packet`. Full cards in `W1_DECOMPOSITION.md`. Cross-unit rule: `quotes.csv`/`sources.csv` stay
read-only throughout W1, and no canonical promotion path exists until W3.

## Deviations

1. **`AGENTS.md` pointer is not landed.** W0 intended a short pointer in `AGENTS.md`
   ("What requires human/provenance review before proceeding" → the corpus program boundary
   and the Gate A stop). The write was refused by tool policy: `AGENTS.md` is a protected
   agent-instruction file, and the approval prompt timed out with no user response. Rather than
   route around the gate (terminal/`execute_code`/`sed`), W0 records the intended text here and
   leaves `AGENTS.md` untouched. The pointer is a convenience, not a required W0 output — every
   required deliverable lives under `docs/program/`, and `README.md`, `docs/RUNBOOK.md`,
   `docs/product/PRODUCT_DOCTRINE.md`, and `docs/queue.md` all link the program docs. A human
   who approves the write can land the same three sentences later.

2. **`docs/queue.md` had a duplicated `## Closed — 2026-09-11 Pages deploy` section** (the same
   block appeared twice, once out of order after "Explicitly NOT started"). Because W0 is
   contracted to update the queue, the second copy was replaced with the W0 close-out entry
   instead of being left as a defect. No content was lost: the first copy is intact and is the
   fuller one.

## Stop point

**Gate A submitted for frontier review. W0 ends here. W1 NOT STARTED — no intake surface, no
datastore, no migration, no adapter, no promotion path exists.** The next authorized action is
an operator/frontier decision on Gate A, followed (if accepted) by authorization of W1.1 only.

---

### Post-change acceptance run (appended by the W0 acceptance step)
```
$ python3 scripts/validate_quotes.py
counts by verification_status: {'unverified': 320, 'verified': 4}
sources.csv: 18 rows, ids: ['1', '10', '11', '12', '13', '14', '15', '16', '17', '18', '2', '3', '4', '5', '6', '7.1', '8', '9']

RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
exit=0

$ python3 scripts/check_program_contracts.py
parsed 38 transitions, 21 required envelope fields, 10 scenarios
vocabularies: corpus=4; curation=5; research=6; work=5

RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
exit=0

$ python3 scripts/validate_homepage_preview_export.py
sha256: 85fa2f6b2882633a683b7449f9e4daf650f78b5ee28faf9e59dbff52222d6bd5

RESULT: PASS
exit=0

$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv

$ diff <(git show main:quotes.csv) quotes.csv ; diff <(git show main:sources.csv) sources.csv  # both silent => byte-identical
byte-identical to main: yes
```
