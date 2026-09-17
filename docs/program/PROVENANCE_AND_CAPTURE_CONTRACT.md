# Provenance and capture contract

## Rule

**A raw encounter is preserved exactly as encountered, and it is immutable.** Every later
value — normalized text, researched attribution, corrected citation — is an *additional*
field that points back at the capture. Nothing overwrites the encounter.

This is the program-level form of the existing product non-negotiable "never silently
rewrite quote wording" (`../product/PRODUCT_DOCTRINE.md`), extended from quote text to the
whole encounter.

## What exactly is preserved from a raw capture

Required:

| Field | Meaning |
|---|---|
| `captured_text` | The text **exactly as encountered**, including its typos, mojibake, wrong diacritics, and any literal `_`-style placeholder. Never cleaned. |
| `captured_attribution` | The attribution **exactly as encountered** ("— Rumi", "attributed to Gandhi", absent). Absence is the explicit sentinel `unknown`, never an empty field. |
| `capture_method` | How it was encountered: `manual-entry`, `pasted-text`, `photo`, `screenshot`, `web-page`, `book-scan`, `audio-transcript`, `agent-research`, `legacy-import`, … |
| `captured_at` | ISO-8601 timestamp (with offset) of the encounter, or of the import for legacy material. |
| `captured_by` | The human or agent that performed the capture, or `legacy-import`. |
| `language` | BCP-47 language tag of `captured_text`; `und` when undetermined. |

Optional but captured whenever available:

| Field | Meaning |
|---|---|
| `captured_citation` | The citation **as encountered** (may be wrong, may be absent). |
| `source_reference` | Where the encounter physically occurred: URL, book + page, transcript line, conversation. |
| `context_notes` | Surrounding context: the paragraph, the chapter, who said it about what, why it was captured. |
| `raw_artifact_ref` | Reference/path to the unmodified artifact (screenshot, page snapshot, scan, audio file). |

## Invariants

1. `captured_text` is stored verbatim. Encoding rehabilitation is a *separate*, provable,
   mechanical transform on the archived bytes — it does not edit the capture record of a new
   encounter, and it does not edit an existing capture record either.
2. A capture is never deleted because the candidate derived from it was rejected. Rejection
   is curation state on the candidate; the encounter is history.
3. Multiple captures may back one candidate (the same passage seen twice, or once in a book
   and once online). The candidate records all of them; disagreement between captures is
   *data*, not an error to reconcile silently.
4. Normalization differences from the capture must be enumerable as explicit
   `normalization_notes`. If the normalized text differs from `captured_text` in any way, the
   note says what changed and why (whitespace, quoting marks, diacritic restoration,
   translation selection, …). If nothing changed, the note says `identical to capture`.
5. No machine-inferred value is ever written into `captured_*` fields.

## The legacy corpus (all 324 existing rows)

The existing rows in `quotes.csv` have **no reconstructable per-row encounter**: what the
original author saw, where, when, and typed-in-as-is was never recorded. W0 refused to invent
one. Decision D4 (2026-09-12) supersedes the open policy question: the corpus gets **ONE
batch capture** for the 2026-09-11 rehabilitation import — a true, verifiable statement about
the frozen archive + documented transform — not 324 fabricated encounters.

What *is* recorded for those rows, and what future work must treat as their provenance:

- the store capture `cap-2026-09-11-legacy-batch` (`capture_method`/`captured_by` =
  `legacy-import`, `context_notes` explicitly "encounter context is unknown"), plus the
  `legacy_batch_membership` side-car linking every `quotes.csv` `id` to that capture
  (`D4_LEGACY_BATCH_CAPTURE.md`);
- the frozen legacy bytes at `data/archive/2026-09-11/*.original.csv`, hashed and never
  edited (`../data/DATA_CONTRACT.md`; verified byte-identical to git blobs at `ef38aca` in
  `../audit/2026-09-11/PHASE0_FRONTIER_REVIEW.md`);
- git history (2025-era commits) for when each row appeared;
- the 2026-09-11 rehabilitation script, which documents the one mechanical transform applied.

Consequences, stated plainly:

- A legacy row's capture is the **batch** record above; `captured_at` is the archive date and
  `capture_method` is `legacy-import`. Future imports must use those sentinels rather than
  implying a real per-row encounter.
- The "preserve the raw encounter" guarantee applies **going forward**. For the legacy corpus
  it applies through the batch capture + frozen archive, never through invented per-row text.
- Any later *research* on a legacy row adds evidence items to the existing record; it does
  not retroactively fabricate a per-row capture.
