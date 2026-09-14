# System model

Entities are deliberately distinct. The single overloaded `quotes.csv` row is **not** the
model of record for new work; it is a projection of it (see `STATE_MODEL.md` §Projection).

## Entities

### Capture
A raw encounter with material, preserved as encountered: verbatim text, verbatim
attribution, verbatim citation, where it was found, how it was found, when, by whom or by
what, plus any raw artifact (screenshot, transcript, page snapshot). A capture is
**immutable**: normalization produces a candidate that *points back* to it. Multiple
captures may describe the same underlying encounter or the same passage.

### Candidate
A normalized proposal derived from one or more captures. Reviewable and researchable, but
not yet a canonical claim. A candidate carries the normalized text/attribution the system
proposes, the normalization notes explaining every difference from the capture, and
duplicate hints.

### Passage
The conceptual text unit the Garden may retain. A passage can have multiple textual
witnesses, translations, or paraphrases. Sibling translations/paraphrases are *separate
representations of one passage*, not duplicates of each other — the distinction the current
repo's near-duplicate candidate pairs keep forcing (45 when this was written; **20** after the
2026-09-13 scope/citation ruling).

### Attribution
A claim that a person, collective, tradition, or source is responsible for a passage or a
version of it. Attribution is a **claim with an evidence status**, not a column of truth.

### Source
A work, edition, publication, recording, transcript, archive, webpage, or other witness used
as evidence. Distinguish the *work* (e.g. the Mahabharata) from the *edition/witness* used to
check wording (e.g. a specific translation, archive URL, or scan).

### Evidence item
A specific piece of evidence supporting, contradicting, or contextualizing a claim: a
witness reference with a locator, a quoted excerpt of the witness, a URL, a retrieved-at
timestamp, and who/what retrieved it. Evidence items are attached to claims, not to whole
records.

### Research case
The bounded investigation of a candidate or passage and its claims. Records hypotheses,
claims under investigation, evidence gathered, findings, unresolved questions, adjudication,
and outcome. A case can end honestly in `verified`, `disputed`, `unverifiable`, or
`needs_more_evidence`.

### Canonical record
The Garden-facing representation of a passage after required curation and research gates.
Canonical records still expose dispute or uncertainty; canonical means "gated and honestly
represented", not "infallible".

### Facet
A classification dimension: domain, tradition, genre, medium, period, culture, theme,
concept, language, source type, and shape/relation. Facets may be **multi-valued**. See
`CLASSIFICATION_AND_FACETS.md`.

### Relationship
A typed connection between records: `translation-of`, `paraphrase-of`, `variant-of`,
`same-source-passage`, `related-theme`, `quotes`, `quoted-in`, `supersedes`.

### Work unit
The bounded execution artifact for a program unit (see
`../bootstrap/seed/2026-09-12-garden-corpus-program/templates/WORK_UNIT_TEMPLATE.md`).
Carries *work state*, which never describes passage truth.

## Key boundaries

- Discovery systems create **captures or candidates**, never canonical records.
- Human curation acts on **candidates**, never on truth claims.
- Research produces **claims, evidence, and adjudication**.
- Enrichment attaches **facets and relationships** without changing evidence status.
- Export and presentation read **canonical records plus visible uncertainty**.

These boundaries exist so that a broad, noisy upstream cannot leak certainty downstream.
Any design that lets one lane write another lane's state is wrong by construction.

## Candidate envelope

The minimum source-agnostic intake contract is specified in `CANDIDATE_ENVELOPE.md`.
Adapters emit envelopes and stop there.

## Storage posture

**No storage technology is selected in W0.** The minimum requirements W1 actually has are
enumerated in `W1_DECOMPOSITION.md` §W1.1. SQLite is the default *hypothesis* — the system is
personal, local-first, relational, and workflow-heavy — but it is not a decision, and the
existing CSV + static-browser stack stays authoritative until W1.1 rules otherwise.

## Non-entities (explicitly out of the model)

- No global "trust score" for a quote. Trust is per-claim and evidence-based.
- No single `status` field spanning curation, research, publication, and execution.
- No notion of an agent-asserted `verified`. Verification is a recorded adjudication.
