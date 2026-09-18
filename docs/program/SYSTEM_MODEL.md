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
The Garden-facing representation of a passage after explicit operator admission.
**Research verification is not an admission prerequisite.** A canonical record may be
`not_started`, `in_research`, `verified`, `disputed`, `unverifiable`, or
`needs_more_evidence` according to the research model; every Garden-facing view must preserve
that uncertainty. Canonical means **admitted**, never “proven.”

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


## Product boundary: Garden and Initiate

This model governs **Garden passages**, not every memorable object.

`mschwar/initiate` owns the broader lifecycle of arbitrary things worth remembering. Garden
owns the specialized curation/admission/research/read experience for passages the operator wants
in the Garden. Garden's native capture path remains valid. A future Initiate adapter may terminate
at the source-agnostic candidate envelope; it may not bypass Garden curation/admission or become a
second authority.

## Candidate envelope

The minimum source-agnostic intake contract is specified in `CANDIDATE_ENVELOPE.md`.
Adapters emit envelopes and stop there.

## Storage posture

W1.1 selected **SQLite** as the machine-local mutable store for new capture/candidate/workflow
state, paired with the deterministic committed text mirror
`data/store/garden.export.txt` for portable/versioned recovery and review. U0.1 subsequently
mechanized bootstrap, freshness status, divergence protection and mirror synchronization across
operator mutation surfaces.

The SQLite file is rebuildable machine-local runtime state; the committed mirror is the durable
cross-clone recovery representation. Neither replaces the legacy `quotes.csv` / `sources.csv`
authority for the existing 324-row Garden. U1.1 must rule the authoritative relationship before
new canonical store items are projected into the Garden-facing read model. Generated projections
must remain derived and rebuildable.

## Non-entities (explicitly out of the model)

- No global "trust score" for a quote. Trust is per-claim and evidence-based.
- No single `status` field spanning curation, research, publication, and execution.
- No notion of an agent-asserted `verified`. Verification is a recorded adjudication.
