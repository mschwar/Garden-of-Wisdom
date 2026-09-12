# Verification and evidence contract

## Rule

**No claim is `verified` because it is plausible, widely repeated, or confidently asserted by
an agent.** A claim is `verified` when a specific witness has been located, the wording has
been compared to it, the comparison is recorded as evidence, and the outcome is adjudicated.
`verified` is always relative to the claims actually checked, and it never extends to claims
that were not.

## Claims are per-claim, not per-record

A passage record carries a **claim set**. At minimum:

| Claim | Question |
|---|---|
| `wording` | Does this text appear in a specific witness, word for word (modulo a declared normalization)? |
| `attribution` | Does the witness attribute it to this person/collective/tradition? |
| `locus` | Is it in this work / this edition / at this locator? |
| `date` | Is this the date/occasion claimed? |
| `shape` | Is it an exact passage, an excerpt, a paraphrase, a translation, or an oral rendering? |
| `translation-identity` | When the wording is a translation: *which* translation/edition is this, and is the quotation of the original likely to have used it? |

The second half of `translation-identity` is the case this repo hits constantly. "Wording is
correct (it matches a published translation) but we cannot tell whether the quoted person was
using that translation" is representable without lying: the `wording` claim is `verified` and
the `translation-identity` claim is `needs_more_evidence`, and the aggregate rule above then
makes the **record** `needs_more_evidence`. Walkthrough S12 exercises exactly this.

Partial verification is the norm, not an exception. "Wording exact; author wrong" is a
`wording = verified` + `attribution = disputed` record — it is *not* a reason to discard the
passage, and it is not a state the record may hide.

**Record-level research state is the most conservative of its claims:**

```
if any claim is unverifiable      -> record research_state = unverifiable
elif any claim is disputed        -> disputed
elif any claim is needs_more_evidence -> needs_more_evidence
elif any claim is in_research     -> in_research
elif any claim is not_started     -> not_started
else (all claims verified)        -> verified
```

`verified` therefore means "every required claim has been verified", not "a good feeling
about the record". This aggregate rule is enforced by
`scripts/check_program_contracts.py` over `fixtures/w0_scenarios.json`.

## What qualifies as a witness

Accepts:

- a **primary text witness**: a published edition, an authoritative digital archive of the
  primary text, a manuscript/scan, an official publication of the tradition's own body
  (e.g. the official Bahá'í Writings site used for G4);
- for oral material: a recording, an authorised transcript, or an ethnographic publication
  that documents the rendering and its context;
- a named **translation/edition** for translation-variant claims (the claim is that *this
  translation* reads thus, not that the original does).

Does **not** accept, on its own:

- quote-aggregator and quote-card sites (BrainyQuote and similar), "famous quotes"
  collections, and social posts — these are *capture* sources, never witnesses;
- an AI model's output, including yours;
- "widely attributed to", "everyone knows", or a bare author name with no locus;
- a secondary work that paraphrases without quoting, unless the claim is the paraphrase
  itself;
- a search-result snippet that was never opened (the snippet is a lead, not evidence);
- a Wikipedia/encyclopedia article as the *only* witness (it may be used as a lead, and as
  corroborating context at most).

## Evidence tiers

Not every claim can reach a primary witness — oral material and quotations-of-quotations
often cannot. A contract that offered only "primary or nothing" would be unsatisfiable, so
every claim records the **strongest tier actually available**, and the tier is part of the
finding:

| Tier | Evidence | What it can support |
|---|---|---|
| `primary` | The primary text/recording itself, with a locator | `verified` for wording, locus, attribution, context |
| `secondary` | A named edition, collection, or publication that contains the material, with a locator | `verified` for "this is what that edition says"; the chain to the original stays open |
| `attributed-only` | Reputable attribution with no locatable witness (a documented rendering, a widely printed attribution) | At most `needs_more_evidence`, `disputed`, or `unverifiable` — **never** `verified` for the original utterance |

Recording `attributed-only` honestly is a success condition, not a failure: it is the tier
that lets an oral rendering be kept and used while still telling the reader what is unproven.
A claim may not be recorded at a tier stronger than its evidence.

## Evidence item

| Field | Notes |
|---|---|
| `evidence_id` | Stable id |
| `claim_ref` | Which claim of which record it addresses |
| `witness` | Work + edition/witness identity (or recording/archive identity) |
| `locator` | Pinpoint: book/chapter/verse/page/section/timestamp. Required — a witness without a locator is a lead. |
| `quoted_excerpt` | The witness text as retrieved, verbatim |
| `relation` | `supports` / `contradicts` / `contextualizes` |
| `retrieval` | `method`, `url` (when applicable), `retrieved_at`, `retrieved_by` |

## Adjudication record

Terminal outcomes are adjudicated, and the adjudication is stored with the record:

| Field | Notes |
|---|---|
| `outcome` | `verified` / `disputed` / `unverifiable` |
| `adjudicated_by` | Human operator, or a frontier-review pass the operator explicitly authorized |
| `adjudicated_at` | Timestamp |
| `rationale` | Why this outcome follows from these evidence items |
| `evidence_ids` | The evidence items supporting the outcome |
| `contract_version` | Which version of this contract was applied |

An agent may assemble the case, gather witnesses, and *propose* an outcome. It may not record
`adjudicated_by` as itself.

## Standard per claim kind

| Situation | What `verified` requires | Common honest alternative |
|---|---|---|
| **Exact genuine quote** | Witness + locator; wording match including punctuation/diacritics, modulo a declared normalization (e.g. quoting marks) | `disputed` if witnesses disagree on wording |
| **Paraphrase** | Witness + locator for the *source statement*, plus a recorded note that this is the Garden's paraphrase, `shape = paraphrase`. Wording match is explicitly not required; a paraphrase may never be presented as a quotation. | `verified` for `locus`, `wording` = not applicable and never recorded as verified |
| **Wrong author** | `attribution` = `disputed` with the competing attributions' witnesses; the record may still be canonical and useful | Do not "fix" by rewriting the attribution silently — the correction is a new claim with evidence |
| **Wrong work/citation** | `locus` = `disputed`; the corrected citation is a *new* claim with its own evidence | Leave the original citation visible in the capture |
| **Quote of a quote** | Witness for the *intermediary* source, locator, and `provenance_chain`; the primary attribution is verified only if the primary is checked | Mark the chain; a "quoted in" verification is not a primary verification |
| **Translation variant** | Named translation/edition + locator; the claim verified is that *this translation* reads thus | Multiple variants legitimately coexist as one passage with several representations |
| **Fabricated / spurious attribution** | No positive standard — this resolves to `unverifiable` (no early witness exists) or `disputed` (a witness contradicts it) | Never emit as verified; may be retained as an example of misattribution |
| **Oral attribution** | Recording/transcript/ethnographic witness naming the teller/tradition and context; the claim verified is the *documented rendering*, not an absolute original | `unverifiable` is a first-class, respectable outcome |
| **Ambiguous source** | Locator resolved to one witness rather than a family of them | `disputed`/`unverifiable` while unresolved |
| **Genuinely unverifiable** | Not applicable | `unverifiable` — a terminal outcome, not a failure to be forced |

## Precedent in this repo

G4 (2026-09-11) is the working example of this contract at small scale: four donors were
checked against an official primary archive with locators and set `verified`; id 30 was *not*
found at its claimed locus and stayed `unverified`/rejected rather than being softened
(`../DECISIONS.md`). Two locators were corrected as explicit, recorded changes with the quote
text untouched.

## Recorded debt

Today the four `verified` rows carry their evidence only in the export
(`exports/bahai-homepage-preview/v1/`) and the decision log — not in the CSV, which has no
evidence fields. Row-level evidence storage is a W2/W3 deliverable; until then, `verified` in
the CSV is a pointer to the export, and no further row may be set `verified` without an
evidence record of this shape existing somewhere reviewable. This is queued.
