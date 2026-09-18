# Product Doctrine

## What Garden of Wisdom is

Garden of Wisdom is a **personal, curated collection of passages worth keeping**, built so the
operator can rediscover, understand, compare, memorize, and reflect on them without provenance or
uncertainty being hidden.

The current 324-row corpus is predominantly religious, philosophical, and oral/cultural material.
That is the **seed/current inventory**, not a permanent product-scope restriction. Garden may admit
passages from religious, philosophical, literary, scientific, artistic, historical, and other
sources when the operator decides they belong.

The durable domain object is **Passage**. “Quote” remains a legitimate legacy CSV/browser term, but
it does not define the product boundary. A passage may be an exact quotation, excerpt,
saying/proverb, oral attribution, translation/version, visibly identified paraphrase, or another
bounded text worth retaining.

Garden is a corpus **and a user product** supported by a curation/research workbench. The workbench,
store, validators, queues and agents are enabling substrate; they exist to make the Garden
dependable.

For the standing answer to what actually works, where the walking skeleton breaks, and what the
current constraint is, read `docs/PRODUCT_REALITY.md`. For execution authority, read
`docs/program/usability-closure/CURRENT.md`.

## What it is not

- Not a generic memory system for every interesting object.
- Not a scholarly critical edition. Provenance is tracked so uncertainty is visible, not so every
  passage is footnoted to publication standard.
- Not `bahai-homepage`. The two repos stay separate. Garden may export explicitly bounded subsets,
  but Garden's schema, scope and curation pace are not dictated by downstream consumers.
- Not an exhaustive anthology. Breadth and useful connection matter more than completeness within a
  tradition, author, source or domain.
- Not a reason to build infrastructure for its own sake. Complexity must close a demonstrated
  usability/dependability boundary.

## Garden and Initiate

`mschwar/initiate` owns the broader lifecycle of **things worth remembering**: cheap capture of an
arbitrary interesting encounter, recovery/resolution, source objects, claims/evidence, source
extension, memorable compression, resurfacing and composition.

Garden owns a specialized corpus/product for **passages the operator wants in the Garden**, including
Garden-specific curation, canonical admission/retirement, passage relationships/facets, research
state, and Garden-facing read/use surfaces.

A biography, laboratory-fire anecdote, song recording, image, research dossier or educational
kernel may belong in Initiate without belonging in Garden. Garden may retain a bounded passage
derived from such a source when the operator decides it belongs.

Garden keeps its native direct-capture path. A future Initiate → Garden adapter may emit the same
source-agnostic candidate envelope, but no shared storage, cross-repo dependency, or integration is
required now. Repeated real use must earn any shared primitive.

## Non-negotiables

1. **Uncertainty must stay visible.** A passage not established by evidence must not be presented as
   settled merely because it is cleanly rendered or admitted to the Garden.
2. **Never silently rewrite wording.** Mechanical encoding restoration is allowed; guessing what a
   garbled, missing, translated, or placeholder character “probably” was is not.
3. **Preserve the raw encounter.** Normalized/corrected representations are additive and traceable
   back to what was actually captured.
4. **Preserve legacy identifiers and history.** IDs assigned in the legacy CSV era remain stable;
   historical evidence is not rewritten to make the present architecture look inevitable.
5. **Human taste controls belonging.** Automation may discover, normalize, research and prepare;
   the operator controls accept/reject/hold/duplicate and canonical Garden admission.
6. **Canonical does not mean verified.** Canonical means admitted to the Garden by a recorded gate.
   Research state remains independent and visible.
7. **Evidence outranks plausibility.** Attribution/wording/source claims may remain uncertain,
   disputed or unverifiable rather than being forced into false certainty.
8. **One authoritative fact, many derived views.** Generated projections are rebuildable views, not
   competing write authorities.
9. **Respect cultural/tradition context without hardening today's inventory into tomorrow's
   ontology.** Classification evolves from observed material and deliberate operator choices.
10. **Deep infrastructure, shallow interface.** Internal sophistication must reduce operator burden
    or preserve a necessary invariant; otherwise it is inventory.

## Current product trajectory

The existing Garden browser is already useful for the legacy/current corpus. The candidate
workbench is also real and now resumable. The active constraint is the seam between an accepted
candidate and the Garden-facing product.

The bounded usability-closure programme exists to prove:

1. **U0:** a real operator passage survives the workbench and clean reconstruction;
2. **U1:** a real accepted passage can be explicitly admitted, projected into the Garden read model,
   and found again in the actual browser.

Research, richer exploration, memorization/resurfacing, discovery adapters and any Initiate feed are
later capability horizons. They are not authorized merely by being named here.

**Live execution status and the single READY unit live in
`docs/program/usability-closure/CURRENT.md`.**
