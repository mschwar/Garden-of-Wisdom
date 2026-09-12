# State model

Four **independent** dimensions. No single status field carries curation, research, corpus,
and execution meaning — that overload is what produced the seed's core warning ("do not
model the system as `intake → approval → final truth`").

Authority vocabulary used in the transition tables below, and enforced by
`scripts/check_program_contracts.py` against `fixtures/w0_scenarios.json`:

- `system` — deterministic consequence of another action; no judgement, must still be audited.
- `agent` — an agent may perform this autonomously; it must be recorded with actor + time.
- `operator` — a human gate. An agent may *propose* the transition but never perform it.

## 1. Curation state — *does the operator want this?*

Vocabulary: `new`, `accepted`, `hold`, `rejected`, `duplicate`.

`accepted` means **"this item is worth pursuing and may belong in the Garden."** It never
means the wording or attribution is accurate. Only the operator (or an explicitly delegated
human gate) may make a final curation decision.

| ID | Dimension | From | To | Authority | Conditions |
|---|---|---|---|---|---|
| T-C1 | curation | new | accepted | operator | operator wants the item pursued/retained if honestly represented |
| T-C2 | curation | new | hold | operator | decision deferred; reason recorded |
| T-C3 | curation | new | rejected | operator | not wanted in the Garden; record retained unless retention policy says otherwise |
| T-C4 | curation | new | duplicate | operator | operator confirms it is represented by another candidate/passage |
| T-C5 | curation | hold | accepted | operator | deferred decision resolved |
| T-C6 | curation | hold | rejected | operator | deferred decision resolved |
| T-C7 | curation | hold | duplicate | operator | deferred decision resolved |
| T-C8 | curation | accepted | rejected | operator | reversal; audit entry required |
| T-C9 | curation | accepted | duplicate | operator | duplicate link established later |
| T-C10 | curation | rejected | new | operator | reopen after new information |
| T-C11 | curation | duplicate | new | operator | duplicate link disproved |
| T-C12 | curation | duplicate | accepted | operator | duplicate link disproved, item wanted |

## 2. Research state — *what can actually be supported?*

Vocabulary: `not_started`, `in_research`, `verified`, `disputed`, `unverifiable`,
`needs_more_evidence`.

Terminal outcomes (`verified`, `disputed`, `unverifiable`) are **human-adjudicated**. W5 may
delegate case *execution* to agents with an evidence package and independent QA, but the
adjudication remains a recorded human/authorized gate — an agent may never self-certify
`verified`. `verified` is tied to `VERIFICATION_CONTRACT.md`, never to agent confidence.

| ID | Dimension | From | To | Authority | Conditions |
|---|---|---|---|---|---|
| T-R1 | research | not_started | in_research | agent | case opened; scope recorded |
| T-R2 | research | in_research | needs_more_evidence | agent | blocked on a witness that is not yet available |
| T-R3 | research | needs_more_evidence | in_research | agent | new lead acquired |
| T-R4 | research | in_research | verified | operator | `VERIFICATION_CONTRACT.md` satisfied: locator + witness recorded + adjudication |
| T-R5 | research | in_research | disputed | operator | competing witnesses or conflicting attributions recorded |
| T-R6 | research | in_research | unverifiable | operator | witnesses exhausted; honest terminal state, not a failure |
| T-R7 | research | needs_more_evidence | unverifiable | operator | the missing witness is not obtainable |
| T-R8 | research | verified | disputed | operator | new evidence contradicts the prior finding |
| T-R9 | research | disputed | verified | operator | evidence resolves the conflict |
| T-R10 | research | disputed | unverifiable | operator | conflict unresolvable |
| T-R11 | research | verified | unverifiable | operator | witness invalidated (misquotation, bad scan, withdrawn source) |
| T-R12 | research | unverifiable | in_research | operator | a new witness appears |
| T-R13 | research | in_research | not_started | operator | case reset/withdrawn |

## 3. Corpus state — *how may this be represented?*

Vocabulary: `candidate_only`, `eligible`, `canonical`, `retired`.

Promotion requirements, exactly:

- `candidate_only → eligible` is **deterministic** and fires on `curation = accepted`
  (`T-P1`). Eligibility is necessary, never sufficient, for canonical status. Research state
  does **not** gate eligibility: a wanted item whose truth is unfinished is legitimately
  eligible.
- `eligible → canonical` is an **operator admission decision** (`T-P2`). It requires
  curation `accepted` and requires that the record carry every open uncertainty visibly
  (see the invariants below). It does **not** require `research = verified`.
- `canonical` therefore does **not** imply `verified`. A canonical record that is
  `unverified`, `disputed`, or `unverifiable` must say so everywhere it is displayed or
  exported.
- `retired` removes a record from the Garden-facing corpus without deleting its history.

| ID | Dimension | From | To | Authority | Conditions |
|---|---|---|---|---|---|
| T-P1 | corpus | candidate_only | eligible | system | fires deterministically on `curation = accepted`; audited |
| T-P2 | corpus | eligible | canonical | operator | curation accepted; all open uncertainty visible on the record |
| T-P3 | corpus | candidate_only | retired | operator | rejected material retained under a retention policy instead of deleted |
| T-P4 | corpus | canonical | retired | operator | removal from the Garden-facing corpus; history retained |
| T-P5 | corpus | retired | canonical | operator | re-admission |
| T-P6 | corpus | eligible | retired | operator | never admitted; history retained |

## 4. Work state — *where is the execution?*

Vocabulary: `queued`, `active`, `qa`, `blocked`, `done`. Work state belongs to work units
and research cases. It **never** describes passage truth, and it must never be the place a
truth question is answered.

| ID | Dimension | From | To | Authority | Conditions |
|---|---|---|---|---|---|
| T-W1 | work | queued | active | agent | unit picked up on its isolated branch |
| T-W2 | work | active | qa | agent | implementation/research complete; evidence collected |
| T-W3 | work | qa | active | agent | foreign-review findings open and are being resolved |
| T-W4 | work | active | blocked | agent | blocked externally; reason + unblocking condition recorded |
| T-W5 | work | blocked | active | agent | blocker cleared |
| T-W6 | work | qa | done | agent | foreign QA recorded; for a wave-gate unit this additionally requires operator acceptance |
| T-W7 | work | done | active | operator | reopened after acceptance |

## Transition invariants

Enforced by `scripts/check_program_contracts.py` over `fixtures/w0_scenarios.json`:

1. Discovery cannot directly create `canonical` records — no transition into `canonical`
   exists from `candidate_only`.
2. Curation acceptance cannot set research outcome to `verified` — `T-R4` requires a research
   case to have actually run (`T-R1`/`T-R3`/`T-R12` earlier in the walkthrough), and its
   authority is `operator`.
3. Research findings cannot silently overwrite the original capture — captures are immutable;
   normalization/research values are additive fields with an audit trail.
4. Reclassification/enrichment cannot upgrade evidence state — facet and relationship writes
   are not research transitions and have no research authority.
5. Rejected material remains auditable unless a separate retention policy says otherwise.
6. Every machine-inferred field that matters to provenance stays distinguishable from
   human/evidence-backed assertion until adjudicated.
7. A transition is relied upon operationally only after deterministic transition tests exist
   for it (W1+).
8. Every operator-authority transition used in a walkthrough must be declared as such in the
   walkthrough — no scenario may perform a human gate implicitly.

## Projection into the current `quotes.csv`

The current CSVs are **not migrated** in W0. They are a lossy, documented projection:

| Model dimension | Current field | Projection rule |
|---|---|---|
| research state | `verification_status` | `verified → verified`; `disputed → disputed`; **all of** `not_started`, `in_research`, `needs_more_evidence`, `unverifiable` → `unverified` |
| corpus state | (implicit) | every row in `quotes.csv` is `canonical` — this is the current canonical working set, gated by the Phase 0 retrofit acceptance + frontier review |
| curation state | (implicit) | `accepted` for all 324 rows (they are in the Garden); not stored |
| work state | (none) | not represented in the CSV |
| facets | `tradition`, `tags` | single-valued tradition facet + multi-valued theme facet |
| shape/relation | `item_type` | overloaded: mixes passage shape (`full-passage`, `excerpt`, `paraphrase`) with provenance shape (`oral-attribution`). Split is W3 work. |
| source link | `source_id` | → Source entity |
| data-quality flag | `has_unresolved_glyph` | Garden-only flag; not a model dimension |

**Known, accepted projection loss:** `unverifiable` is not representable in the 3-valued
enum, so a record adjudicated unverifiable projects to `unverified`. Today's only real
instance is Garden id 30 (issue #5), which is correctly refused by the exporter but is
otherwise indistinguishable in the CSV from a never-checked row. Widening or re-mapping the
enum is a migration unit, not a W0/W1 side effect.

**Explicitly preserved:** legacy `id`s (including the non-contiguous gaps), quote wording
including the literal `_` placeholders, and the frozen archive — per
`../product/PRODUCT_DOCTRINE.md` non-negotiables and `../data/DATA_CONTRACT.md`.

## Canonical test scenario

The model is not ready unless it can represent all ten of these without false certainty. The
machine-readable form is `fixtures/w0_scenarios.json`; the prose walkthroughs for the
required ones are in `W0_GATE_REPORT.md`.

1. exact genuine quote
2. paraphrase
3. wrong author
4. wrong work/citation
5. quote of a quote
6. translation variant
7. fabricated or spurious internet attribution
8. oral attribution
9. ambiguous source
10. genuinely unverifiable item
