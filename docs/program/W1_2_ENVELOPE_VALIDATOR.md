# W1.2 — Candidate envelope contract, serialized form and validator

**Status: implemented 2026-09-12** on branch `w1/envelope-validator` (W1.2 of
`docs/program/W1_DECOMPOSITION.md`). The contract is `docs/program/CANDIDATE_ENVELOPE.md`. This
document is the written half of the unit: the serialized form, the six rules as implemented
(including where the rule boundaries are drawn and why), the sentinel handling table, the store
bridge into W1.1, and the places the contract was ambiguous. The executable half is
`scripts/garden_envelope.py` (serialized form + validator + store bridge + a read-only diagnostic
CLI) and `scripts/check_garden_envelope.py` (acceptance + evidence, 102 checks).

## 1. The serialized form

One envelope is one **canonical JSON object**, produced by `garden_envelope.serialize`:

- `sort_keys=True` — key insertion order can never change the bytes, so the same envelope always
  serializes the same way;
- compact separators `(",", ":")` — one deterministic layout, no pretty-printing variance;
- `ensure_ascii=False`, encoded UTF-8 — `Bahá’u’lláh` is UTF-8, not `\u00e1` escapes;
- `allow_nan=False` — a value the canonical form cannot represent is a **refusal**, not an
  `Infinity`/`NaN` literal nobody can re-parse;
- no export-time state (no timestamp, no producer string), so it is a pure function of the
  envelope.

`parse` is the inverse and refuses cleanly (never with JSON's own exception): non-UTF-8 bytes,
non-JSON text, and non-object JSON all raise `EnvelopeError`.

**Round-trip (rule 6, and acceptance criterion 3):** `serialize → parse → serialize` is
byte-identical for every valid fixture envelope and for all twelve W0 walkthrough envelopes, and
`parse(serialize(e)) == e` as an object (so no field is silently dropped and no value changes).
The acceptance script additionally serializes the same object built with reversed key insertion
order and asserts the bytes are identical — that is the check a lost `sort_keys` turns red.

A worked serialization (the sentinel-maximal fixture, 683 bytes, one line):

```
{"candidate_author":"unknown","candidate_source_ref":"none","candidate_text":"One finger cannot lift a pebble.","capture_id":"cap-2026-09-12-0002","capture_method":"legacy-import","captured_at":"2026-09-11T00:00:00-06:00","captured_attribution":"unknown","captured_by":"legacy-import","captured_citation":"none","captured_text":"One finger cannot lift a pebble.","context_notes":"none","corpus_state":"candidate_only","curation_state":"new","duplicate_hints":[],"intake_schema_version":"garden.candidate-envelope/1","language":"und","normalization_notes":"identical to capture","raw_artifact_ref":"none","research_state":"not_started","source_reference":"none","work_state":"queued"}
```

## 2. The six rules, as implemented

Rule ids are `rule-1` … `rule-6`, exactly the numbering of `CANDIDATE_ENVELOPE.md` §"Validation
rules". `validate(envelope, captures)` returns a list of `Violation(rule, message)`; each prints
as `[rule-N] …`. **One defect reports one rule id**, which is deliberate: it is why the
rule-by-rule fixtures can be asserted as *exact* rule-id sets (a fixture that reports extra rules
fails the acceptance run), and it is the boundary the next section spells out.

| Rule | What it enforces | Implemented as |
|---|---|---|
| **rule-1** | All required fields present; values well-typed; enums match the declared vocabulary | the 21 required fields must all be keys; string fields must be `str` and `duplicate_hints` a `list`; `intake_schema_version == "garden.candidate-envelope/1"`; `capture_method` ∈ the nine-method list; the four state values ∈ their `STATE_MODEL.md` vocabularies; every string field **except `captured_text`** non-empty; `captured_at` parseable ISO-8601 **with an offset**; a sentinel used on a field the contract does not declare it for |
| **rule-2** | `captured_text` non-empty after no transformation whatsoever | `captured_text == ""` is the only thing this rule rejects. Leading/trailing whitespace and embedded newlines are **legal and preserved** — the capture is stored verbatim and reported in `normalization_notes`, never trimmed |
| **rule-3** | curation / research / corpus (and work) at their intake values | each of the four values must be its intake value (`new` / `not_started` / `candidate_only` / `queued`). An envelope arriving with a decision already made is rejected. `garden_store.INTAKE_STATES` is the single source for this rule *and* for the store's write path |
| **rule-4** | `duplicate_hints[].kind` ∈ the declared vocabulary | each entry must be an object of exactly `{kind, target, basis}`; `kind` ∈ `exact-text`/`near-text`/`same-reference`/`same-passage`; `target` non-empty (an id or `external`); `basis` non-empty (a hint without its basis is not reproducible, and hints are rebuildable, never hand-edited) |
| **rule-5** | `captured_text` byte-identical to the capture record referenced by `capture_id` | compares UTF-8 **bytes**, not Unicode code points, against the capture record's `captured_text`; a `capture_id` that matches no record is also a rule-5 violation. `captures=None` is **not** a skip: it reports that no capture record was supplied |
| **rule-6** | Re-serializing round-trips without loss | serialize → parse → serialize must be byte-identical, the field set must be unchanged, and every value must compare equal. A value the canonical form cannot represent (e.g. an `Infinity` a JSON reader produced from `1e999`) is a violation |

A non-object envelope is a **rule-1 violation, not an exception**: `validate([1,2,3])`,
`validate(None)` and `validate("text")` each return exactly one `rule-1` violation. The CLI
reports malformed input as `RESULT: FAIL` with no traceback.

### Where the rule boundaries are drawn (and why)

- **`captured_text` non-emptiness lives only in rule-2.** Rule-1 still checks that it is a string,
  but does not also flag an empty one, so the rule-2 fixture reports exactly `rule-2`.
- **Out-of-vocabulary vs. non-intake state values.** A state value *outside* its vocabulary is
  rule-1's finding; a value *inside* the vocabulary but not at its intake value is rule-3's. So
  `curation_state: "maybe"` is rule-1 and `curation_state: "accepted"` is rule-3, never both.
- **`captured_text` matching its own capture record.** The rule-2 fixture is captured against an
  **empty capture record** (`cap-rule2-empty` in the fixture), so an empty `captured_text` fails
  rule-2 *and* still matches its record byte-for-byte — otherwise an empty text would trip rule-5
  too and the fixture could not isolate rule-2.

## 3. Sentinel handling

The sentinel vocabulary is `unknown` (the capturer does not know), `und` (language
undetermined), `none` (known to be absent), `legacy-import` (capture method for archived
material) — `PROVENANCE_AND_CAPTURE_CONTRACT.md`, and `garden_store.SENTINELS`.

**A sentinel is a value.** It is never absence, never an empty string, and never a missing field.
The implementation guarantees that three ways:

1. an empty string is a rule-1 violation on every required string field (where the contract
   requires a sentinel instead) — it is never treated as one;
2. every declared sentinel is carried through validation, `serialize`/`parse` and the store
   **verbatim** (the acceptance run asserts `und`/`unknown`/`legacy-import`/`none` read back out
   of SQLite unchanged, not as `""`);
3. a sentinel used on a field the contract does not declare it for is a rule-1 violation.

| Field | Sentinels the contract declares | Notes |
|---|---|---|
| `captured_attribution` | `unknown` | "attributed to X" is text, not a sentinel |
| `captured_citation` | `none` | |
| `captured_by` | `legacy-import` | otherwise a human/agent identity |
| `language` | `und` | otherwise a BCP-47 tag |
| `source_reference` | `none` | |
| `context_notes` | `none` | |
| `raw_artifact_ref` | `none` | |
| `candidate_author` | `unknown` | |
| `candidate_source_ref` | `none` | |
| `normalization_notes` | *(none allowed)* | a bare sentinel is refused: "we did not touch it" must be an assertion (`identical to capture`), not an absence. See §5.4 |
| `capture_method` | — | `legacy-import` is an **enum value** of the method list, not the sentinel; the two are independent (see §5.5) |
| `captured_text`, `candidate_text`, `intake_schema_version`, `capture_id`, `captured_at` | — | unrestricted: a sentinel check here would be an over-reach |

Fields with no entry in the table are unrestricted; the table lives in
`garden_envelope.SENTINEL_ALLOWED` and is derived from the contract's per-field `Notes` prose.

## 4. Store integration (`scripts/garden_store.py`, W1.1)

The contract meets the store in two functions — no parallel store, no second write path:

- `store_capture(store, envelope)` writes the envelope's eleven `captured_*` fields as the
  **immutable capture row** (rules 1, 2 and 6 are enforced first; rule 5 is meaningless before the
  record exists). The store's own triggers make the row un-editable from then on.
- `store_envelope(store, envelope, candidate_id=…)` **validates all six rules against the store's
  own capture records** (`capture_texts(store)` feeds rule 5), then writes the candidate and its
  duplicate hints. It raises `EnvelopeError` listing the violations, each with its rule id,
  instead of writing.
- `read_envelope(store, candidate_id)` reconstructs the envelope's required fields from the store
  (capture + candidate + hints). The acceptance run stores the doc's worked example, reads it back,
  asserts **all 21 required fields are equal**, and re-validates the read-back envelope clean.

**Rule 3 is not duplicated or contradicted.** `garden_store.add_candidate` takes no state
parameters at all — it writes the four dimensions at their intake values — and
`garden_envelope.store_envelope` never passes one. Both sides read the same
`garden_store.INTAKE_STATES`, so the validator's rule 3 and the store's write path cannot drift.
The acceptance run asserts the signature has no state parameter, and that the store path refuses a
decision-already-made envelope with a `[rule-3]` violation.

## 5. Doctrine ambiguities found while implementing (reported, not papered over)

1. **Rule 5 names only `captured_text`.** The contract sentence is "`captured_text` byte-identical
   to the capture record referenced by `capture_id`". An envelope also carries ten other
   `captured_*` fields, and nothing in the contract says they must agree with the stored capture —
   so an envelope could carry a `captured_attribution` that contradicts its own capture record and
   still pass. W1.2 implements rule 5 **exactly as written** (do not silently widen a contract
   rule). The gap is real and is recorded as discovered work in `docs/queue.md`.
2. **The envelope carries no candidate identity.** `capture_id` is the only id in the contract,
   while the store keys candidates by `candidate_id`. W1.2 makes the caller supply the
   `candidate_id` explicitly rather than inventing a derivation scheme the contract does not
   declare. W1.3 (which creates submissions) is the right place to rule on the naming scheme.
3. **The optional fields have nowhere to be stored in W1.1's schema.** Of the nine optional
   fields, only `external_id` has a column (`candidates.external_id`); the other eight
   (`provenance_chain`, `attribution_chain`, `placeholder_markers`, `source_link_state`,
   `locator`, `container`, `period_hint`, `rights_note`) do not. Adding them means a new migration
   — and W1.1's own acceptance run asserts the migration ledger is exactly
   `["0001_create_core"]`, so a W1.2 migration would turn W1.1's run red. **Decided: do not
   migrate.** The serialized form carries all nine losslessly, the store persists the 21 required
   fields, and optional-field persistence is filed as discovered work
   (`docs/queue.md`). Nothing is lost between capture and store; only between the store and the
   optional columns. (W1.1's handoff anticipated this migration as W1.2's; W1.2 declines it for
   the reason above rather than editing another unit's acceptance assertions.)
4. **`normalization_notes` is never listed as sentinel-bearing, but is not forbidden from being
   one either.** The contract requires an assertion even for a no-op, so W1.2 refuses a bare
   sentinel there (`unknown`/`und`/`none`/`legacy-import` are all refused). This is a reading of
   the prose, not a certainty — flagged so the rule can be relaxed deliberately if the operator
   wants sentinel-only notes to be legal.
5. **`legacy-import` is both an enum value and a sentinel.** `capture_method` lists it as one of
   the nine methods; `captured_by` uses it as the archived-material sentinel. They are
   independent: `capture_method: "legacy-import"` with `captured_by: "operator"` is legal, and
   `captured_by: "legacy-import"` with `capture_method: "manual-entry"` is legal. Recorded so
   nobody "simplifies" the two into one check.
6. **Which fields may carry a sentinel is prose, not a table.** The contract declares sentinels
   in the `Notes` column of the required-field table (and in the optional-field table for
   `source_link_state`, which is a tri-state — `resolved`/`unresolved`/`none` — and is **not**
   the sentinel vocabulary, since `none` there means "no citation recorded" as a state of the
   link). W1.2's `SENTINEL_ALLOWED` table is derived from that prose; a reviewer should be able
   to read the two side by side.
7. **Rule 6 needs a reachable falsifier from a JSON fixture.** A repository JSON fixture can only
   produce a value the canonical form cannot represent via a number literal like `1e999`, which a
   JSON reader turns into `Infinity`; with `allow_nan=False` the serializer refuses it. That is
   why the rule-6 fixture uses `1e999` on an optional field — optional fields are not
   type-checked by rule 1, so it is genuinely rule 6 alone that catches it. Noted so the fixture
   is not mistaken for a contrived case.
8. **W0's envelope assertion is a subset, and is not replaced.** `scripts/check_program_contracts.py`
   asserts the twelve W0 scenario envelopes satisfy rules 1–4 (its own, separate reading, over
   `docs/program/**` only). W1.2 does not edit it; instead the acceptance run derives the same
   twelve envelopes and runs the full six-rule validator over them with a capture record each, so
   the two fixture sets cannot diverge silently.

## 6. What this unit does not do

Per the card's stop condition — **validator green on fixtures; no UI**:

- no source adapter, no automated discovery (W2+);
- no intake/submission CLI (W1.3). `scripts/garden_envelope.py`'s CLI is a **read-only diagnostic**
  (`serialize` / `validate` over a file) used to inspect an envelope; it creates no capture and
  records no decision, and it is documented as such in its own docstring;
- no normalization or duplicate-hint *algorithm* (W1.4) — the validator checks the hint shape, it
  does not compute hints;
- no review/UI surface, no decision-making field or transition, no promotion path (W1.5/W3);
- no write to `quotes.csv` / `sources.csv` (hashed before and after by the acceptance run), no
  embeddings, no network access, stdlib only.

## 7. Commands

| Command | Effect |
|---|---|
| `python3 scripts/check_garden_envelope.py` | the full W1.2 acceptance + evidence run (102 checks) |
| `python3 scripts/garden_envelope.py serialize --envelope FILE` | print one envelope's canonical serialized form |
| `python3 scripts/garden_envelope.py validate --envelope FILE [--captures FILE] [--rule N]` | validate one envelope file read-only; one line per violation, each with its rule id |

## 8. Fixtures

`docs/program/fixtures/envelope_fixtures.json` (`garden.envelope-fixtures/1`):

- **4 valid envelopes** — the contract's worked example; a sentinel-maximal envelope (all four
  sentinels, each on its declared field); one carrying all nine optional fields including nested
  structures; one whose `captured_text` preserves leading/trailing whitespace and an embedded
  newline;
- **20 invalid envelopes**, each declaring the `fails_rule` it is built to break: 9 for rule-1
  (missing field, non-array `duplicate_hints`, bad `capture_method`, empty string instead of a
  sentinel, offset-less timestamp, a mis-placed sentinel on `language`, one on `candidate_author`,
  a bare sentinel in `normalization_notes`, an out-of-vocabulary state), 1 for rule-2, 4 for
  rule-3 (one per dimension), 3 for rule-4 (bad kind, no basis, no target), 2 for rule-5
  (byte mismatch, unknown capture id), 1 for rule-6 (a non-lossless `1e999`);
- **5 capture records** (`capture_id` → `captured_text`) so rule 5 has something real to compare
  against.

Negative controls (mutation → observed `FAIL:` line) are recorded in `GARDEN_W1_2_HANDOFF.md`.
