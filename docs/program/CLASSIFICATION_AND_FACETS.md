# Classification and facets

## Posture

Classification is **faceted**, not a single exclusive category. A record may belong to several
domains, traditions, themes, periods, and cultures at once, and the vocabulary is **learned
from representative records before it is hardened**. No new closed enum is legislated in W0.

This is the program-level form of the existing doctrine's "description of current scope, not a
hard enum" stance on `tradition` (`../../README.md`).

## Facet set (working model)

| Facet | Cardinality | Notes |
|---|---|---|
| `domain` | multi | e.g. religious, philosophical, literary, scientific, artistic, cultural, oral, proverbial. Intended to be the "browse across domains" axis. |
| `tradition` | single today, possibly multi later | Existing `quotes.csv.tradition` (27 observed values). Open question Q1 below. |
| `theme` | multi | Existing `tags` column (lowercase, singular-preferred). |
| `culture` | multi | Distinct from tradition where a passage is culturally embedded but not doctrinally. |
| `period` | single or range | Not currently recorded. |
| `language` | single (of the representation) | Distinct from the *original* language of the source; both may matter. |
| `source_type` | single | scripture, commentary, poetry, speech, interview, proverb, song, letter, recording… |
| `medium` | multi | text, audio, video, oral performance. |
| `shape` | single | exact passage / excerpt / paraphrase / translation / oral rendering — a candidate successor to today's overloaded `item_type`. |
| `relation` | multi | Typed edges: `translation-of`, `paraphrase-of`, `variant-of`, `same-source-passage`, `related-theme`, `quotes`, `quoted-in`, `supersedes`. |

## Rules

1. **Facet writes never change evidence state.** Enrichment is a different lane from research
   (`WORK_LANES.md`); classification of a passage cannot make it more or less verified.
2. **Facets are additive.** Adding a facet value to a record never removes the value a human
   or researcher set without an audit entry.
3. **Vocabulary growth is a recorded decision.** Adding a new `tradition`/`domain` value is a
   taste-encoding change → operator gate (`CORPUS_PROGRAM_DOCTRINE.md` §Human gates).
4. **Machine-proposed facet values stay distinguishable** from human-asserted ones until
   accepted (invariant 6 in `STATE_MODEL.md`).
5. **No facet is renamed or collapsed to satisfy a schema.** The 27 observed `tradition`
   values stay 27; the 2026-09-11 decision not to collapse them to 7 stands
   (`../DECISIONS.md`).

## Current-field mapping (no migration in W0)

| Current field | Facet | Status |
|---|---|---|
| `tradition` | `tradition` (single-valued) | Kept as-is; documented, not enforced |
| `tags` | `theme` (multi-valued) | Kept as-is |
| `item_type` | `shape` + legacy `source_type` signal | **Overloaded** — `full-passage`/`excerpt`/`paraphrase` are shape; `oral-attribution` is provenance shape, not a text relation. Splitting it is W3 work; do not widen the enum meanwhile. |

## Open ontology questions (explicit, unresolved)

| # | Question | Why it matters | Where it is queued |
|---|---|---|---|
| Q1 | Should `tradition` become multi-valued (a passage that is simultaneously e.g. Christian and Jewish, or Indigenous and Christian)? The 27-value list contains single-tradition cultures that overlap in practice. | Determines whether `tradition` can stay a single column in any future store | `../queue.md` |
| Q2 | Is `domain` genuinely multi-valued in practice, or does it collapse to one value per record most of the time? | Decides whether `domain` earns a facet or a single field | `../queue.md` |
| Q3 | How is a non-text "source" represented (e.g. `Modern Mayan Greeting`, id 344, which is a greeting rather than a work)? Is that a `source_type = greeting`, or is there no Source at all? | D7 (2026-09-13) closed id 344's `source_id` link with a placeholder oral-tradition row so the manifest gap no longer blocks the validator, but the underlying question — what distinguishes that row, a dated speech (id 317), and an ordinary text-bearing work — is unresolved | `../queue.md` |
| Q4 | Does `culture` add anything beyond `tradition` + `source_type` on this corpus, or is it redundant? | Avoids inventing a facet with no data behind it | `../queue.md` |
| Q5 | Does `shape` replace `item_type`, or does `item_type` remain the projection of `shape`? | The current validator and browser both read `item_type`; a rename has migration cost | `../queue.md` |
| Q6 | Should period/era be recorded at all, given how many oral-tradition records have no datable origin? | A facet that is mostly `unknown` may not earn its keep | `../queue.md` |

## Anti-goals

- No embeddings, vector search, or similarity infrastructure in W0/W1
  (`NON_GOALS.md` in the seed; `../product/PRODUCT_DOCTRINE.md` local-first posture).
- No "single canonical category" field that forces a choice between overlapping identities.
- No ontology hardening before representative records exist to learn the vocabulary from.
