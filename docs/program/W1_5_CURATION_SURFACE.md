# W1.5 — Curation review surface + decision recording + audit history

**Lane:** Human curation. **Secondary:** Platform/governance.
**Contract:** `docs/program/W1_DECOMPOSITION.md` section "W1.5". **Unit order:** after W1.4.

W1.5 is the loop's payoff: the operator-facing `accept / hold / reject / duplicate` surface that
makes a curation decision a **recorded, audited transition** — never a silent state flip. It is
also the first unit that falsifies the carried-forward risk from `W0_GATE_REPORT.md`:
*"The reversal rule (T-C8 → T-P7) is legal on paper but untested against a real store."* It is
tested here, against the real store, and asserted not to strand a dimension.

## The one write gate

Every curation decision goes through a **single atomic write** on the store:

```
Store.curate(candidate_id, *, action, actor, reason)
```

`action ∈ {accept, hold, reject, duplicate, reopen}`. `curate`:

1. loads the candidate's current `curation_state` and `corpus_state`;
2. looks the legal curation transition `(from, to)` up in `CURATION_TRANSITIONS`
   (all twelve T-C1…T-C12 from `STATE_MODEL.md` §1) and refuses an illegal move;
3. computes the **required corpus follow-on**:
   - readiness to `accepted` with `corpus_state = candidate_only`
     → appends **T-P1** `candidate_only → eligible` (authority `system`, deterministic);
   - leaving `accepted` (`T-C8` → `rejected` or `T-C9` → `duplicate`) with
     `corpus_state = eligible` → appends **T-P7** `eligible → candidate_only` (authority
     `operator`, the operator who is making the reversal).
     This is the no-stranded-dimension rule from `STATE_MODEL.md` §3;
4. updates `curation_state` (and `corpus_state` when a follow-on fired) and appends **every**
   audit row — the curation decision and each corpus follow-on on the same candidate — **in one
   SQLite transaction**, then commits. There is no window in which the state is updated without
   its audit row, or the audit row appended without the state change.

`curate` writes **only** `curation_state` and `corpus_state`. It has **no research write path**:
`research_state` stays `not_started`, and `work_state` is untouched. This is enforced by the
absence of those columns in the method's `UPDATE`, and asserted by the acceptance run after every
curation action.

## The twelve transitions, as a table

| action | (from → to) | transition | corpus follow-on |
|---|---|---|---|
| `accept` | new → accepted | T-C1 | T-P1 candidate_only → eligible (system) |
| `hold`   | new → hold | T-C2 | — |
| `reject` | new → rejected | T-C3 | — (candidate stays readable; retirement T-P3 is operator, out of W1.5) |
| `duplicate` | new → duplicate | T-C4 | — |
| `accept` | hold → accepted | T-C5 | T-P1 (system) |
| `reject` | hold → rejected | T-C6 | — |
| `duplicate` | hold → duplicate | T-C7 | — |
| `reject` | accepted → rejected | T-C8 | T-P7 eligible → candidate_only (operator) |
| `duplicate` | accepted → duplicate | T-C9 | T-P7 (operator) |
| `reopen` | rejected → new | T-C10 | — |
| `reopen` | duplicate → new | T-C11 | — |
| `accept` | duplicate → accepted | T-C12 | T-P1 (system) |

All twelve curation transitions are reachable through the five commands. Every decision row
carries `actor`, `actor_kind` (always `operator` for the curation decision; `system` for the
deterministic T-P1), a timestamp, `from_state`, `to_state`, the `transition_id`, and the required
`reason`. `reject` from `new`/`hold` does **not** retire the record (T-P3 is operator promotion,
out of W1.5 scope); it keeps the capture and the candidate readable in the store, exactly as the
acceptance criterion requires.

## The queue view

`garden_review.py queue --dir DIR` prints the **unreviewed queue** (`curation_state = 'new'`),
newest first (requirement 6 of W1 — the W1.1 index). `garden_review.py show --dir DIR
--candidate-id ID` prints one candidate in any state. Both render, per candidate:

- the **capture** verbatim (`captured_text`, byte-for-byte the encounter), marked `asserted`;
- the **normalized proposal** (`candidate_text` / `candidate_author` / `candidate_source_ref`),
  marked `derived (normalization)` — it is W1.4's deterministic transform of the capture, always
  explained by `normalization_notes`;
- the **normalization notes**, marked `asserted (recorded)`;
- the **duplicate hints** (`kind`, `target`, `basis`), each marked `machine-inferred` with an
  explicit `a hint is evidence, never a decision` line — W1.4's `STATE_MODEL.md` invariant 6 and
  the W1.2 duplicate-hint contract, made visible where the operator actually reads it;
- the **four states**, with `research_state` labelled `read-only in W1.5 — a curation action
  never changes it` and always rendered `not_started`.

The machine-inferred-vs-asserted split satisfies invariant 6 ("every machine-inferred field that
matters to provenance stays distinguishable from human/evidence-backed assertion until
adjudicated") by *labeling* each field, not by hiding it.

## Recording the decision (audit history)

`garden_review.py audit --dir DIR [--candidate-id ID]` prints the append-only decision log
(whole store, or one candidate), newest first, one transition per line:
`T-C8 accepted -> rejected  operator  2026-09-13T10:04:00-06:00  <reason>`. The `decisions`
table's UPDATE/DELETE triggers (W1.1) are what make this history trustworthy; the acceptance run
re-asserts those two triggers and that a corrected decision is a new row, never an edit.

## The surface's guard rails

- Every decision command (`accept/hold/reject/duplicate/reopen`) **requires `--reason`**; an
  empty reason is refused before anything is written. `curate` enforces the same rule, so a
  future caller cannot bypass the CLI.
- `--actor` defaults to `operator` and is overridable for a real operator's name; `actor_kind`
  for a curation decision is always `operator` and is **not** exposed (a curation action cannot
  masquerade as `system`/`agent`).
- A refused decision **writes nothing at all**: an illegal transition, an unknown/missing
  candidate, or a missing reason leaves the store byte-identical (asserted).
- The read-only commands (`queue`, `show`, `audit`) never write.

## Out of scope

- **Research.** No command touches `research_state`; there is no research surface in W1.5 and no
  code path that can set research state away from `not_started`.
- **Canonical admission and retirement.** `T-P2`…`T-P6` (including `T-P3 candidate_only →
  retired`) are operator promotion decisions and W3/wave work, not W1.5.
- **No migration.** The `decisions` ledger and the four state columns already exist (W1.1); W1.5
  adds no schema and leaves W1.1's exact-ledger assertion (`["0001_create_core"]`) untouched.
- **No write to `quotes.csv` / `sources.csv`** (read-only for the whole of W1), and **no populated
  store mirror is committed** (the only submissions are W1.5's throwaway test fixtures; the first
  real operator-submitted population belongs to Gate B, per the W1.3 decision).

## Acceptance evidence

`scripts/check_garden_review.py` is the W1.5 acceptance + evidence run. It lives entirely in a
throwaway temp directory, drives the real W1.3/W1.4 CLIs as subprocesses to build its fixture
batch, then drives `garden_review.py` itself as a subprocess for every transition and every
refusal. It asserts: all twelve T-C transitions are exercisable and each produces an audit row
with actor/timestamp/from/to/reason; acceptance promotes `candidate_only → eligible` (T-P1);
both reversal paths (`T-C8` then `T-P7`, `T-C9` then `T-P7`) leave **no** dimension stranded
(i.e. no record has `curation ∉ {accepted}` while `corpus = eligible`); rejecting keeps the
capture and the candidate readable; every curation action leaves `research_state` (and
`work_state`) untouched at intake; refused decisions write nothing; the append-only triggers
still hold; `quotes.csv`/`sources.csv` are byte-identical before and after; and nothing is
written outside the temp directory. Negative controls (mutation → observed `FAIL:` line) are
recorded in `GARDEN_W1_5_HANDOFF.md`, and each fires against W1.5's *own* guard (a control that
does not go red is a finding, not a nuisance).