# Candidate envelope contract

The **source-agnostic intake seam**. Every adapter — manual entry, screenshot, transcript,
future crawler — emits this envelope and stops. No adapter writes canonical records, and no
adapter writes a curation or research decision.

Schema key: `garden.candidate-envelope/1` (`intake_schema_version`).

## Required fields

Absence of a value is expressed with an explicit sentinel, never with a missing field.
Sentinel vocabulary: `unknown` (human/agent does not know), `und` (language undetermined),
`none` (known to be absent), `legacy-import` (capture method for archived material).

| Field | Type | Notes |
|---|---|---|
| `intake_schema_version` | string | `"garden.candidate-envelope/1"` |
| `capture_id` | string | Stable id of the capture this envelope derives from |
| `captured_text` | string | Verbatim encounter text (see `PROVENANCE_AND_CAPTURE_CONTRACT.md`) |
| `captured_attribution` | string | Verbatim attribution as encountered, or `unknown` |
| `captured_citation` | string | Verbatim citation as encountered, or `none` |
| `capture_method` | enum | `manual-entry`, `pasted-text`, `photo`, `screenshot`, `web-page`, `book-scan`, `audio-transcript`, `agent-research`, `legacy-import` |
| `captured_at` | string | ISO-8601 with offset |
| `captured_by` | string | Human/agent identity, or `legacy-import` |
| `language` | string | BCP-47 tag, or `und` |
| `source_reference` | string | URL / book+page / transcript line / conversation, or `none` |
| `context_notes` | string | Context, or `none` |
| `raw_artifact_ref` | string | Path/reference to the unmodified artifact, or `none` |
| `candidate_text` | string | Normalized proposal for the Garden-facing text |
| `candidate_author` | string | Normalized attribution proposal, or `unknown` |
| `candidate_source_ref` | string | Normalized citation proposal, or `none` |
| `normalization_notes` | string | Every difference from the capture and why; `identical to capture` when there is none |
| `duplicate_hints` | array | Possibly-empty list of `{kind, target, basis}` — see below |
| `curation_state` | enum | Always `new` at intake (only the operator moves it) |
| `research_state` | enum | Always `not_started` at intake |
| `corpus_state` | enum | Always `candidate_only` at intake |
| `work_state` | enum | Always `queued` at intake |

`normalization_notes` is required even when the normalization was a no-op — "we did not
touch it" must be an assertion, not an omission.

## Duplicate hints

`duplicate_hints` entries are *hints*, never decisions:

```json
{"kind": "exact-text" | "near-text" | "same-reference" | "same-passage",
 "target": "<existing candidate/passage id, or 'external'>",
 "basis": "<what produced the hint: normalized-text match, 0.83 similarity, same citation, …>"}
```

A hint may be produced by any deterministic comparison available at intake. A hint may never
be written into `curation_state`; only the operator sets `duplicate` (`T-C4`/`T-C7`/`T-C9`).
This is the contract-level fix for the current repo's noisy 45-pair near-duplicate report,
where ~half the pairs are generic-`source_ref` false positives
(`../data/DATA_QUALITY_REPORT.md`).

## Optional fields

| Field | Notes |
|---|---|
| `external_id` | Id in the source system, when the source has one |
| `provenance_chain` | Ordered list of witnesses when the encounter is a quotation of a quotation |
| `container` | Where the material lives: book, journal, playlist, series |
| `period_hint` | Date/era hint for faceting |
| `rights_note` | Rights/copyright observation, when the source flags it |

## Validation rules (W1 must implement these as deterministic checks)

1. All required fields present; enums match the declared vocabulary.
2. `captured_text` non-empty after no transformation whatsoever (trailing/leading whitespace
   is *preserved and reported* in `normalization_notes`, not trimmed silently).
3. `curation_state`/`research_state`/`corpus_state` are at their intake values. An envelope
   arriving with a decision already made is rejected.
4. `duplicate_hints[].kind` ∈ declared vocabulary.
5. `captured_text` byte-identical to the capture record referenced by `capture_id`.
6. Re-serializing the envelope round-trips without loss (no field silently dropped).

## Worked example

```json
{
  "intake_schema_version": "garden.candidate-envelope/1",
  "capture_id": "cap-2026-09-12-0001",
  "captured_text": "The earth is but one country, and mankind its citizens.",
  "captured_attribution": "Bahá’u’lláh",
  "captured_citation": "attributed — seen on a quote card",
  "capture_method": "screenshot",
  "captured_at": "2026-09-12T09:14:11-06:00",
  "captured_by": "operator",
  "language": "en",
  "source_reference": "https://example-quotes.example/one-country",
  "context_notes": "Shared in a group chat with no citation beyond the author.",
  "raw_artifact_ref": "captures/2026-09-12/one-country.png",
  "candidate_text": "The earth is but one country, and mankind its citizens.",
  "candidate_author": "Bahá’u’lláh",
  "candidate_source_ref": "none",
  "normalization_notes": "identical to capture; citation weaker than capture implies, left as none",
  "duplicate_hints": [
    {"kind": "near-text", "target": "283", "basis": "0.74 text similarity within tradition"}
  ],
  "curation_state": "new",
  "research_state": "not_started",
  "corpus_state": "candidate_only",
  "work_state": "queued"
}
```

The fixture set in `fixtures/w0_scenarios.json` contains machine-readable envelopes for the
adversarial cases; `scripts/check_program_contracts.py` asserts they satisfy rules 1–4.
