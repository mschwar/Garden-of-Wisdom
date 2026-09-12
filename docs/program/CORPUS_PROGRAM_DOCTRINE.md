# Corpus program doctrine

## Purpose

Garden of Wisdom is a personal, curated corpus of memorable passages worth preserving,
revisiting, memorizing, and reflecting on. This program adds durable *acquisition*,
*curation*, *provenance*, *research*, and *enrichment* workflows around that corpus without
weakening the repo's existing uncertainty and provenance rules.

The objective is **not** to accumulate more quotations. It is to separate discovery,
intake, human curation, research, verification, and canonical representation so that
automation may be broad upstream while canonical claims stay evidence-driven downstream.

## Governing principles

1. **Human taste, machine leverage.** Agents may discover and prepare candidates
   aggressively; the operator controls admission into the Garden.
2. **Approval is not verification.** Curation answers *is this wanted?*; verification
   answers *what can be supported by evidence?* These are different questions with
   different state, different authority, and different failure modes.
3. **Preserve the raw encounter.** Original captured wording, attribution, citation, URL,
   notes, and context are preserved alongside any normalized or researched value.
4. **Uncertainty is first-class.** Unknown, disputed, inferred, and unverifiable claims must
   remain *representable and visible*, never squeezed into false certainty.
5. **Evidence outranks plausibility.** A likely attribution remains provisional until
   supported by a witness.
6. **No silent semantic rewrites.** Normalization, correction, paraphrase detection, and
   source reconciliation carry an audit trail.
7. **High recall upstream; high precision downstream.** Discovery may be noisy. Promotion
   toward canonical verified records requires stronger gates.
8. **One corpus, multiple state dimensions.** Never overload one status field with curation,
   research, publication, and workflow meaning. (Current `verification_status` is the one
   documented exception — see `STATE_MODEL.md` §"Projection".)
9. **Facets over forced buckets.** Classification supports overlap and evolves from observed
   material rather than being legislated in advance.
10. **Repo-native and inspectable.** Doctrine, schemas, tests, decisions, queue entries,
    evidence conventions, and execution contracts live in version control.
11. **Local-first, low-ops by default.** Infrastructure complexity must be earned by a
    concrete need.
12. **Adapters terminate at intake.** A source-specific collector emits common candidate
    envelopes and never writes canonical records directly.
13. **Research produces evidence, not merely field edits.** Important factual claims are
    traceable to supporting evidence and an adjudication.
14. **Canonical does not mean infallible.** It means the record passed defined gates while
    faithfully representing remaining uncertainty.

## Reconciliation with existing repo doctrine

The seed packet (`bootstrap/seed/2026-09-12-garden-corpus-program/`) is planning input. W0
reconciled it against the existing repo as follows. Nothing here supersedes
`docs/product/PRODUCT_DOCTRINE.md`; where the seed and existing doctrine differ, the ruling
below is authoritative for the program, and each material ruling is also appended to
`docs/DECISIONS.md`.

| # | Seed position | Existing repo position | Ruling |
|---|---|---|---|
| R1 | W0 produces "corpus/program doctrine" as a canonical doc | `docs/product/PRODUCT_DOCTRINE.md` is the product authority; `docs/data/DATA_CONTRACT.md` the data authority | Program doctrine is **additive**: it lives under `docs/program/` and *inherits* the product doctrine's non-negotiables by reference. `PRODUCT_DOCTRINE.md` is not rewritten, only linked. |
| R2 | Four independent state dimensions; "do not overload one status field" | `quotes.csv.verification_status` is a single 3-valued field (`unverified`/`verified`/`disputed`), and `item_type` is a 5-valued heuristic | The four-dimensional model is adopted **as the model of record**. The current CSVs are not migrated in W0; they are a documented *projection* with a known, recorded loss (`unverifiable` collapses to `unverified`). See `STATE_MODEL.md`. |
| R3 | "Preserve the raw encounter" — capture is a first-class entity | No capture entity exists; 324 legacy rows have no capture record at all | Capture is a first-class entity going forward. For the 324 existing rows, the raw encounter is **not reconstructable**, and W0 does not invent one: their recorded provenance is the frozen archive `data/archive/2026-09-11/*.original.csv` plus git history. This is stated plainly rather than back-filled. |
| R4 | Research state has 6 values | `verification_status` has 3 | Adopted 6 values at the model level; the 3-valued CSV stays the compatibility projection. Do **not** rename or widen the CSV enum in W0/W1 without a migration unit. |
| R5 | `canonical` must not imply `verified` | All but 4 rows are `unverified` yet are today's working corpus | The 324 rows are the current **canonical working set** (`corpus_state = canonical`, mostly `research_state = unverified`), gated by the Phase 0 retrofit acceptance + frontier review. This is the concrete proof that canonical ≠ verified. |
| R6 | Faceted classification; no premature single category enum | `tradition` is single-valued free text with 27 values; `tags` is multi-valued | Facets adopted. `tradition` stays single-valued and unrenamed for now (it is *a* facet with one value), and the 27-value list is documentation of observed scope, not a hardened enum. Overlap/multi-value questions stay open. |
| R7 | Do not choose a datastore in W0 | Repo is CSV + static browser; no DB | Not chosen. SQLite is recorded as the W1 *hypothesis only*, to be decided in W1.1 against explicit storage/access requirements. |
| R8 | W0 must not implement anything | — | Honored. W0 ships docs, decision/queue entries, a planning fixture, and a docs-consistency checker. The checker reads only `docs/` and the fixture; it is a documentation test, not runtime. |

## Human gates

The operator (or a frontier-review pass the operator has explicitly authorized) must
explicitly control:

- candidate **accept / reject / hold / duplicate** decisions (final curation authority);
- any transition to a **terminal research outcome** — `verified`, `disputed`,
  `unverifiable`;
- promotion of a record to `canonical` and retirement from it;
- any change that **weakens provenance standards**;
- ontology/vocabulary choices that encode taste (e.g. adding a tradition, retiring a facet);
- destructive semantic merges (near-duplicate resolution, record merging);
- authorization to proceed between major waves.

Everything else is agent-delegable under audit. The per-transition table in `STATE_MODEL.md`
is the operational form of this list.

## Core loops

1. **Acquisition loop** — discover/capture → normalize → duplicate hints → human review.
2. **Truth loop** — investigate → locate witness → compare wording → establish attribution →
   cite evidence → record outcome → enrich.

Admission into the Garden ends the acquisition loop. It never ends the truth loop: a
canonical, unverified record is exactly a record whose truth loop is unfinished, and it must
look that way in every surface that shows it.
