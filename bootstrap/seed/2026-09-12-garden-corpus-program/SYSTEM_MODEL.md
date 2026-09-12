# System model

## Core entities

The program should use distinct entities rather than one overloaded quote row.

### Capture
A raw encounter with material. Preserve exactly what was encountered and where it came from.

### Candidate
A normalized proposal derived from one or more captures. Candidates are reviewable and researchable, but are not yet canonical claims.

### Passage
The conceptual text unit the Garden may retain. A passage can have multiple textual witnesses or translations.

### Attribution
A claim that a person, collective, tradition, or source is responsible for a passage or version of it.

### Source
A work, edition, publication, recording, transcript, archive, webpage, or other witness used as evidence.

### Evidence item
A specific piece of evidence supporting, contradicting, or contextualizing a claim.

### Research case
The bounded investigation of a candidate or passage and its claims. It records hypotheses, evidence, findings, unresolved questions, and outcome.

### Canonical record
The Garden-facing representation of a passage after required curation and research gates. Canonical records may still expose dispute or uncertainty.

### Facet
A classification dimension such as domain, tradition, genre, medium, period, culture, theme, concept, language, or source type. Facets may be multi-valued.

### Relationship
A typed connection between records, such as translation-of, paraphrase-of, variant-of, same-source-passage, or related-theme.

## Key boundaries

- Discovery systems create captures or candidates, never canonical records.
- Human curation acts on candidates, not on truth claims.
- Research produces claims, evidence, and adjudication.
- Enrichment attaches facets and relationships without changing evidence status.
- Export and presentation read canonical records plus visible uncertainty.

## Candidate envelope

W0 should specify a minimum source-agnostic intake envelope that can preserve original text, original attribution/citation as encountered, source reference when available, capture method, capture time, context or notes, normalized candidate text, possible duplicate hints, and workflow state.

## Storage posture

Do not select a database technology in W0. W1 should choose the simplest durable store after the state model and access patterns are explicit. SQLite is the default hypothesis because the system is personal, local-first, relational, and workflow-heavy, but this is not yet a decision.
