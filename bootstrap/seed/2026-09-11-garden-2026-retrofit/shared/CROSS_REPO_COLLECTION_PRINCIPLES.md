# Cross-Repo Collection Principles

These are principles, not the final H2B schema.

A homepage collection should minimally answer:

## Collection identity
- stable collection ID
- human label
- version
- description/purpose
- producer/source repository
- provenance/rights note
- default eligibility rules

## Item identity
- stable item ID within the collection
- display text
- author/attribution
- human-readable source reference
- authoritative source URL when available
- item type: `full-passage`, `excerpt`, `paraphrase`, `oral-attribution`, `unknown`
- verification state
- optional tags/curation metadata
- upstream record/occurrence identity

## Runtime behavior
- deterministic date-based selection within the eligible item set
- collection-scoped cache key
- no random fallback
- explicit empty/error behavior
- selected collection persisted locally, with Hidden Words as product default

## Separation of concerns

Garden may contain rich review metadata that the homepage does not need.
The homepage export should contain only what the runtime needs plus enough provenance to remain trustworthy.
