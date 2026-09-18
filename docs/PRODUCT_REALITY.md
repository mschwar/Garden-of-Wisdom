# Garden of Wisdom — Product Reality

> **Standing product/system dashboard.** This file answers what Garden is, what actually works,
> where use breaks, and what boundary should be closed next. It is **not execution authority**.
> For the single authorized work unit, read `docs/program/usability-closure/CURRENT.md`.

## PRODUCT

**Exists to:** let the operator build and use a personally curated, provenance-aware Garden of
**passages worth keeping** — encountered across religious, philosophical, literary, scientific,
artistic, historical, and oral/cultural sources — so they can be rediscovered, understood,
compared, memorized, and reflected on without provenance or uncertainty being hidden.

**Primary operator:** the repository owner / curator.

**Domain object:** **Passage**. “Quote” is a legacy CSV/browser representation, not the durable
product boundary. A passage may be an exact quotation, excerpt, saying/proverb, oral attribution,
translation/version, visibly identified paraphrase, or other bounded text worth retaining.

**Minimum unit of value:** the operator encounters one passage worth keeping and can later find it
in the Garden, understand what it is and where it came from, see what remains uncertain, and use
it.

## DOMAIN PRODUCT VS ENABLING SUBSTRATE

### Domain product

- a personally admitted Garden of passages;
- fast reading, search, filtering, comparison and copying;
- honest provenance and uncertainty;
- rediscovery across themes, traditions, domains and sources;
- eventual memorization/internalization and richer exploration.

### Enabling substrate

- immutable capture and candidate envelopes;
- normalization and duplicate hints;
- human curation and explicit admission state;
- research claims/evidence/adjudication;
- SQLite runtime state plus deterministic committed mirror;
- generated projections, validators, CI, queues, work units, runbooks and agent controls.

The substrate exists to make the Garden dependable. It is not the product.

## SYSTEM BOUNDARY

### Garden owns

A specialized corpus/product for **wisdom-bearing or otherwise personally meaningful passages**:
Garden-specific curation, admission, passage relationships/facets, research status, and
Garden-facing read/use surfaces.

### Initiate owns

The broader lifecycle of **things worth remembering**: cheap capture of arbitrary interesting
encounters, recovery/resolution, source objects, claims/evidence, source extension, memorable
compression, resurfacing, personal forks and composition.

A laboratory-fire anecdote, biography fragment, song recording, image, research dossier or
educational kernel may belong in Initiate without belonging in Garden. Garden may retain a
bounded passage derived from such a source when the operator decides it belongs.

### Relationship

Garden keeps its native direct-capture path. A future Initiate → Garden adapter may emit the same
source-agnostic candidate envelope, but no integration or shared storage is required now.
Repeated real use must earn any shared primitive.

## CONOPS

Ordinary successful use:

```text
encounter a passage
  → capture it cheaply, preserving the encounter
  → normalize without overwriting the capture
  → generate duplicate hints
  → operator decides whether it belongs
  → eligible candidate
  → explicit Garden admission
  → deterministic Garden-facing read model
  → browser/search/rediscovery
  → optional research, enrichment, comparison and memorization
```

Research is orthogonal to admission. A canonical Garden passage may remain unverified,
disputed, unverifiable, or in need of more evidence; the user-facing surface must say so.

## PRIMARY WALKING SKELETON

### Existing Garden

`legacy canonical CSVs → static browser → search/filter/copy`

This walks dependably for the current 324-row seed corpus.

### Growing the Garden

`encounter → capture → normalize → hints → operator curation → eligible → ??? → browser`

The candidate workflow is implemented and tested through `eligible`; U0.1 demonstrated the
restart/reclone recovery mechanism in deterministic lifecycle tests. **U0.3 still owes ecological
proof with a real persistent operator passage.** The admission/projection/browser seam is also not
yet closed.

## USABLE NOW

- Browse/search/filter/copy the existing 324-row Garden.
- See current item type, verification state and surfaced data-quality uncertainty.
- Validate the legacy corpus deterministically.
- Capture a new passage into the corpus store while preserving its raw encounter.
- Normalize it with explicit change notes.
- Generate deterministic duplicate hints.
- Accept / hold / reject / mark duplicate and retain an append-only audit trail.
- Bootstrap the local SQLite store from the committed deterministic mirror.
- Detect stale/divergent mirror/store state and keep operator-facing mutations synchronized.
- Resume execution from repo-native current-state and work-unit documents.

## PARTIAL

### Grow the Garden

The new-item path ends at `eligible`. No operator-facing canonical admission + unified
Garden read model + browser path exists yet.

**Exact missing seam:** `eligible → explicit canonical admission → derived Garden read model → browser`.

### Research / truth loop

State, doctrine and verification contracts exist; a full research workbench does not.

### Exploration / memorization

The browser offers basic rediscovery. Rich relationships, faceted exploration, resurfacing and
memorization/internalization are intended product capabilities, not current ones.

## NOT YET

- Admit a new candidate into the Garden and see it in the browser.
- Investigate a new Garden passage end-to-end through a durable evidence workbench.
- Browse relationships/variants across passages as a first-class product experience.
- Use a dedicated memorization/resurfacing loop.
- Feed Garden from automated discovery or Initiate through an adapter.

## CURRENT CONSTRAINT

The candidate workbench and the Garden-facing corpus are still disconnected.

Persistence and repo legibility are no longer the constraint. The next useful work should advance
a **real passage**, not add more meta-assurance around already-demonstrated documentation checks.

## NEXT CLOSURE

**Gate U0 first:** prove one real operator passage survives the persistent workbench and clean
reconstruction.

**Then Gate U1:** let one real accepted passage cross
`eligible → canonical admission → deterministic Garden read model → browser`.

## ACCEPTANCE PROOF

The decisive U1 demonstration is:

> Given a real passage the operator wants to keep, capture it through the real workbench, make the
> human curation/admission decisions, generate the Garden-facing view, find/copy it in the real
> browser with uncertainty visible, then delete local rebuildable state and reproduce the same
> result from committed authoritative artifacts.

Code existing or tests passing are supporting verification evidence; they do not substitute for
this product demonstration.

## AUTHORITY

- **Product doctrine:** `docs/product/PRODUCT_DOCTRINE.md`
- **Standing product reality:** this file
- **Execution authority:** `docs/program/usability-closure/CURRENT.md`
- **Corpus lifecycle doctrine/model:** `docs/program/`
- **Legacy Garden working data:** `quotes.csv` + `sources.csv`
- **New candidate/curation state:** local SQLite store
- **Portable/versioned store durability:** deterministic `data/store/garden.export.txt`
- **Historical source bytes:** `data/archive/2026-09-11/`
- **Decision history:** `docs/DECISIONS.md`
- **Discovered work:** `docs/queue.md`

Generated projections are derived views, never writable authority.

## CONTROL / RECONCILIATION

- **Observe:** validators, lifecycle status, browser smoke/live checks, current-state documents.
- **Decide:** deterministic machinery for mechanical transitions; operator for taste, canonical
  admission/retirement, terminal research adjudication, and value-laden ontology choices.
- **Act:** corpus CLIs, named data units, projection/export generators, deployment.
- **Feedback:** acceptance suites, negative controls where valuable, browser/live proof, audit log.
- **Supervision:** `CURRENT.md` limits execution authority and names stop/synthesis seams.

## RECOVERY / DEPENDABILITY

The workbench recovery mechanism is implemented and deterministically demonstrated: the committed
mirror can rebuild a fresh local SQLite store, and divergence is detected rather than guessed away.
U0.3 still must prove that path with real persistent operator state. After that, the remaining
product-level dependability gap is that newly curated state cannot yet reach the Garden-facing read
surface.

## WORKLOAD

### Immediate

- one primary human curator;
- hundreds to low-thousands of passages;
- low concurrency;
- local-first/offline-friendly operation;
- occasional agent-assisted batches/research;
- static read surface.

### MVP

Safely support a low-thousands personal corpus and batches of candidate intake without requiring a
server, distributed queue, multi-user auth, Kubernetes, workflow engine, or other distributed
operations substrate.

The current SQLite + deterministic-export architecture is proportionate to that workload.

## TRAJECTORY

1. **U0 — Resumable workbench:** I can trust a real passage to survive interruption/reclone.
2. **U1 — Grow the Garden:** I can put a real passage into my Garden and find it again.
3. **R1 — Investigate a passage:** I can research one Garden passage and preserve evidence honestly.
4. **E1 — Explore connections:** I can navigate facets, variants and relationships without changing
   evidentiary status.
5. **M1 — Internalize:** I can deliberately resurface/memorize passages I chose to keep.
6. **A1 — Cheap upstream feed:** useful sources, potentially including Initiate, can feed candidates
   without bypassing Garden curation.

These are capability horizons, not automatic execution authorization.

## LIFECYCLE / DISPOSITION

**ACTIVE.** The product is real and already useful as a read-only personal corpus. Its active
frontier is not more infrastructure: it is connecting the proven candidate workbench to the
Garden-facing product while preserving the evidence/authority invariants already earned.

Historical gate packets and handoffs remain evidence. Old wave maps remain planning history where
useful; they do not outrank this product reality or `CURRENT.md` execution authority.
