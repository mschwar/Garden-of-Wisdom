# W1 decomposition — intake + human curation vertical slice

**Status: PROPOSED. W1 IS NOT STARTED AND IS NOT AUTHORIZED BY W0.** These cards are the
bounded decomposition a frontier review needs in order to authorize W1. Nothing here may be
implemented until that authorization exists.

Goal of W1 (from the roadmap): prove the **central human loop** —
`manual submission → durable capture → normalized candidate → duplicate hints → operator
accept/reject/hold/duplicate`.

Gate B passes only if a representative batch of messy manual submissions can be ingested and
reviewed while preserving originals, provenance, decision history, and duplicate hints, and
**no curation action implies verification**.

Unit order: `W1.1 → W1.2 → W1.3 → W1.4 → W1.5 → W1.6`. W1.4 may overlap W1.3; every other
dependency is strict. Cards follow the seed's `WORK_UNIT_TEMPLATE.md` section order.

## Storage and access requirements W1 actually has

The evidence a store must be able to hold, and W1.1 must rule on:

1. Immutable capture records, keyed, never updated after write.
2. Candidate records referencing one or more captures, with normalized fields and an explicit
   normalization-notes field.
3. Duplicate hints as rows (kind/target/basis), rebuildable deterministically.
4. An append-only decision/audit log: who/what, when, from-state, to-state, reason — for every
   curation and work transition.
5. Curation state, research state (always `not_started` in W1), corpus state (`candidate_only`
   in W1), and work state per candidate.
6. A query path for "show me the unreviewed queue, newest first" and "show me every rejected
   item with its reason" that stays fast at low thousands of rows.
7. No network dependency, no server process required for the operator to work, and a
   human-readable, diffable representation of everything that matters.
8. Export of the whole store to text such that the current browser can keep reading
   `quotes.csv` untouched.

Non-requirements in W1: concurrent writers, multi-user auth, embeddings, search indices,
sync, and any write path into `quotes.csv`.

SQLite is the working hypothesis, not a decision. W1.1 decides and records the rationale,
including why not "plain CSV files" if that option is rejected.

---

## W1.1 — Storage decision + minimal schema

**Primary lane:** Platform/governance. **Secondary:** Ingestion/normalization.

**Why it exists:** every other W1 unit writes to a store; choosing it in code before ruling on
it would harden an architecture W0 deliberately left open.

**Inputs / dependencies:** `docs/program/SYSTEM_MODEL.md` §Storage posture;
`docs/program/STATE_MODEL.md` (the four dimensions and their vocabularies);
`docs/program/W1_DECOMPOSITION.md` §Storage and access requirements (this file, above);
`docs/DECISIONS.md` (the no-datastore decision this unit supersedes);
`docs/data/DATA_CONTRACT.md` (what must stay untouched). No prior unit.

**In scope:** the storage decision with a written comparison against the eight requirements
above; schema/DDL for captures, candidates, duplicate hints, decisions (append-only),
and the four state dimensions; a create-from-empty migration and an idempotency rule; a
round-trip test (write → export to text → re-import → identical).

**Out of scope:** migrating `quotes.csv`; any canonical promotion path; performance tuning.

**Human gates:** the storage decision itself is recorded as a decision-log entry; the
operator may veto the technology without further justification.

**Acceptance criteria:** `create → write one candidate → read back → export → re-import`
produces byte-identical text; the decision-log entry names the requirement each rejected
option failed.

**Evidence required:** test output for the round-trip; the migration run from an empty
directory; the decision entry.

**Execution contract:** one isolated branch/worktree → complete bounded implementation → one
PR → independent/foreign QA → resolve findings → record discovered work in `docs/queue.md` →
re-run acceptance → merge → report. Stop before W1.2.

**Stop condition:** schema exists and round-trips. No intake surface, no review surface.

---

## W1.2 — Candidate envelope intake contract + validator

**Primary lane:** Ingestion/normalization.

**Why it exists:** the envelope is the single seam every future source must pass through; it
must be enforced by a deterministic validator before any surface can produce one.

**Inputs / dependencies:** W1.1 (store + schema); `docs/program/CANDIDATE_ENVELOPE.md`
(the contract, 21 required fields, 6 validation rules);
`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md` (immutability + sentinel vocabulary);
`docs/program/fixtures/w0_scenarios.json` (the eleven walkthroughs whose envelopes are already
contract-conforming and can seed the validator fixtures).

**In scope:** implementation of the `garden.candidate-envelope/1` contract
(`CANDIDATE_ENVELOPE.md`) as a serialized form plus a validator implementing validation
rules 1–6; sentinel handling for `unknown`/`und`/`none`/`legacy-import`; fixtures for every
adversarial case kind.

**Out of scope:** any adapter; any decision-making field; any write to `quotes.csv`.

**Human gates:** none — the contract is already ruled.

**Acceptance criteria:** a valid envelope is accepted and stored; each of the six rules has a
fixture that fails it and the validator reports the rule id; re-serialization round-trips
losslessly.

**Evidence required:** validator output over the fixture set (pass and fail cases).

**Execution contract:** one isolated branch/worktree → complete bounded implementation → one
PR → independent/foreign QA → resolve findings → record discovered work in `docs/queue.md` →
re-run acceptance → merge → report. Stop before W1.3.

**Stop condition:** validator green on fixtures; no UI.

---

## W1.3 — Manual capture/submission surface (CLI first)

**Primary lane:** Acquisition/expansion. **Secondary:** Ingestion/normalization.

**Why it exists:** the loop must start with a cheap, low-friction way for the operator to
submit a messy candidate.

**Inputs / dependencies:** W1.1 (store); W1.2 (envelope + validator);
`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md` (what must be preserved verbatim);
`docs/RUNBOOK.md` (how commands in this repo are documented and run).

**In scope:** a CLI that accepts a pasted text + optional attribution/citation/source URL and
creates a capture **and** its candidate envelope; explicit capture-method selection; the raw
input stored verbatim; non-interactive flags for scripted/testing use.

**Out of scope:** a web UI; browser capture extensions; any automated discovery; clipboard
polling.

**Human gates:** none beyond normal use; the CLI never sets a decision.

**Acceptance criteria:** submitting text containing a literal `_`, curly quotes, a wrong
author, and no citation produces a stored envelope where `captured_text` is byte-identical to
the input and `normalization_notes` explains every normalization; a submission with a missing
required field is rejected with the field named.

**Evidence required:** CLI transcripts for a valid and an invalid submission; the stored
record dumped back out.

**Execution contract:** one isolated branch/worktree → complete bounded implementation → one
PR → independent/foreign QA → resolve findings → record discovered work in `docs/queue.md` →
re-run acceptance → merge → report. Stop before W1.4.

**Stop condition:** submissions persist. No review commands.

---

## W1.4 — Normalization + duplicate hints

**Primary lane:** Ingestion/normalization.

**Why it exists:** the review surface is only pleasant if obviously-identical items arrive
grouped, while the current repo's near-duplicate report shows how easily hints become noise.

**Inputs / dependencies:** W1.2 (envelope); W1.3 (submissions to normalize);
`docs/program/CANDIDATE_ENVELOPE.md` §Duplicate hints (kind/target/basis);
`docs/data/DATA_QUALITY_REPORT.md` (the 45 near-duplicate pairs and the generic-`source_ref`
false-positive caveat that the hints must not reproduce).

**In scope:** deterministic normalization (whitespace/quoting-mark/diacritic-form handling)
that records a note for every change; duplicate-hint kinds `exact-text`, `near-text`,
`same-reference`, `same-passage` with explicit basis strings; a documented similarity
threshold; hints recomputed, never hand-edited.

**Out of scope:** auto-merging; auto-rejecting duplicates; semantic/embedding similarity.

**Human gates:** none for hint generation; every `duplicate` decision remains the operator's
(`T-C4`/`T-C7`/`T-C9`).

**Acceptance criteria:** the generic-`source_ref` false-positive pattern from
`../data/DATA_QUALITY_REPORT.md` does not produce a `same-passage` hint unless a citation is
actually specific; every hint carries a basis string; hints never appear in
`curation_state`.

**Evidence required:** hint output for a fixture batch including the known
`"Oral Tradition"` false-positive shape and the id 3 ~ 283 near-text pair.

**Execution contract:** one isolated branch/worktree → complete bounded implementation → one
PR → independent/foreign QA → resolve findings → record discovered work in `docs/queue.md` →
re-run acceptance → merge → report. Stop before W1.5.

**Stop condition:** hints generate deterministically. No decisions.

---

## W1.5 — Curation review + decision recording + audit history

**Primary lane:** Human curation. **Secondary:** Platform/governance.

**Why it exists:** this is the loop's payoff, and the place where conflating taste with truth
would do the most damage.

**Inputs / dependencies:** W1.1 (decisions log + states); W1.2 (envelopes to review);
W1.4 (hints shown in the queue); `docs/program/STATE_MODEL.md` §1 Curation state
(`T-C1…T-C12` and their authorities) and §Transition invariants;
`docs/program/W0_GATE_REPORT.md` (the required scenario walkthrough the surface must not
contradict).

**In scope:** a queue view (text-first; newest-first; showing captured verbatim text, the
normalized proposal, the normalization notes, duplicate hints with their basis, and an
explicit machine-inferred-vs-asserted marker); commands for accept / reject / hold /
duplicate with a required reason; append-only audit entries implementing `T-C1…T-C12`;
research state rendered as read-only and always `not_started`.

**Out of scope:** any research action; any promotion to `eligible`/`canonical` except the
deterministic `T-P1` and the reversal `T-P7`; any UI that implies verification; making the
browser writable.

**Human gates:** every decision in this unit is the operator's; the unit must not contain a
code path that sets `accepted` without an operator action.

**Acceptance criteria:** each of the twelve curation transitions is exercisable and produces
an audit entry with actor, timestamp, from, to, reason; rejecting an item keeps the capture
and the candidate readable; the reversal path (`T-C8` then `T-P7`, or `T-C9` then `T-P7`) is
exercisable and leaves no dimension stranded; no command in the surface writes
`research_state`; a test asserts that no curation action can set research state to anything
but `not_started`.

**Evidence required:** a full transcript over a batch of ≥10 messy candidates covering
accept/hold/reject/duplicate and one reversal; the resulting audit log; the diff showing
`quotes.csv` untouched (`sha256` before/after).

**Execution contract:** one isolated branch/worktree → complete bounded implementation → one
PR → independent/foreign QA → resolve findings → record discovered work in `docs/queue.md` →
re-run acceptance → merge → report. Stop before W1.6.

**Stop condition:** review loop works end to end. No promotion, no research.

---

## W1.6 — End-to-end test pack + Gate B evidence packet

**Primary lane:** Platform/governance.

**Why it exists:** the wave gate needs a reproducible artifact, not a narrative.

**Inputs / dependencies:** W1.1–W1.5 complete; `docs/program/W0_GATE_REPORT.md` (the Gate A
packet this one must mirror in shape); `bootstrap/seed/2026-09-12-garden-corpus-program/ACCEPTANCE_GATES.md`
§Gate B (the pass conditions); `docs/RUNBOOK.md` (where the new command is documented).

**In scope:** a deterministic end-to-end test that submits a messy batch, ingests, normalizes,
hints, reviews, and asserts that originals/provenance/decision history survived and that no
curation action implied verification; a Gate B evidence document.

**Out of scope:** any W2 research functionality; any canonical promotion.

**Human gates:** the operator accepts or rejects the Gate B packet.

**Acceptance criteria:** the end-to-end test runs from a clean clone with one command and
exits 0; `python3 scripts/validate_quotes.py` still exits 0 and `quotes.csv`/`sources.csv` are
byte-identical to pre-W1; the evidence packet names every test and artifact.

**Evidence required:** test output; the CSVs' before/after hashes; the packet.

**Execution contract:** one isolated branch/worktree → complete bounded implementation → one
PR → independent/foreign QA → resolve findings → record discovered work in `docs/queue.md` →
re-run acceptance → merge → report, then stop at the Gate B packet.

**Stop condition:** Gate B packet submitted. **W2 is not started.**

---

## Cross-unit rules for W1

- `quotes.csv` and `sources.csv` are **read-only** for the whole of W1. No row is added,
  edited, or migrated, and the browser keeps working unchanged.
- No promotion path to `canonical` exists in W1; the `T-P*` transitions other than the
  deterministic `T-P1` and the reversals `T-P7`/`T-P8` are W3 work.
- Every unit follows the repo work-unit loop stated in its own Execution contract section.
