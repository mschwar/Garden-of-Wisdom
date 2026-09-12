# Program doctrine

## Purpose

Garden of Wisdom is a personal, curated corpus of memorable passages worth preserving, revisiting, memorizing, and reflecting on. This program adds durable acquisition, curation, provenance, research, and enrichment workflows around that corpus without weakening the repo's existing uncertainty and provenance rules.

## Governing principles

1. **Human taste, machine leverage.** Agents may discover and prepare candidates aggressively; the operator controls admission into the Garden.
2. **Approval is not verification.** Curation answers whether an item is wanted; verification answers what can be supported by evidence.
3. **Preserve the raw encounter.** Keep original captured wording, attribution, URL, notes, and context alongside normalized or researched values.
4. **Uncertainty is first-class.** Unknown, disputed, inferred, and unverifiable claims must remain representable and visible.
5. **Evidence outranks plausibility.** A likely attribution remains provisional until supported.
6. **No silent semantic rewrites.** Normalization, correction, paraphrase detection, and source reconciliation require an audit trail.
7. **High recall upstream; high precision downstream.** Discovery may be noisy. Promotion toward canonical verified records requires stronger gates.
8. **One corpus, multiple state dimensions.** Do not overload one status field with curation, research, publication, and workflow meaning.
9. **Facets over forced buckets.** Classification should support overlap and evolve from observed material.
10. **Repo-native and inspectable.** Doctrine, schemas, tests, decisions, queues, evidence conventions, and execution contracts should live in version control where practical.
11. **Local-first, low-ops by default.** Infrastructure complexity must be earned by a concrete need.
12. **Adapters terminate at intake.** Source-specific collectors emit a common candidate envelope and never write canonical records directly.
13. **Research produces evidence, not merely field edits.** Important factual claims must be traceable to supporting evidence and adjudication.
14. **Canonical does not mean infallible.** It means the record passed defined gates while faithfully representing remaining uncertainty.

## Human gates

The operator must explicitly control candidate acceptance/rejection/hold, changes that weaken provenance standards, promotion rules into canonical states, ontology choices that encode taste, destructive semantic merges, and authorization to proceed between major waves.

## Relationship to existing doctrine

The current `docs/product/PRODUCT_DOCTRINE.md`, `docs/data/DATA_CONTRACT.md`, `docs/DECISIONS.md`, and validators remain authoritative for the existing corpus until W0 explicitly reconciles this seed with them. This packet is planning input, not permission to bypass current non-negotiables.
