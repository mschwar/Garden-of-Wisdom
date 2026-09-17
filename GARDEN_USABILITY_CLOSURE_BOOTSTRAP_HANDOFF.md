# Garden Usability-Closure — Bootstrap Handoff

Date: 2026-09-17. Branch: `usability-closure/bootstrap`. Base: `main` @ `14007e7`.

## What landed

The **Usability Closure** programme is installed under `docs/program/usability-closure/` as a
bounded bridge programme over the already-landed W1 substrate. It closes the distance between
Garden's two strong-but-disconnected systems (the read-only canonical browser and the W1
candidate workbench) and dependable real-world use.

Installed programme documents (all under `docs/program/usability-closure/`):

- `PROGRAM_CHARTER.md` — objective, the two gates (U0 resumable workbench, U1 grow the Garden),
  strict programme order, execution contract, authority, preferred U1.1 architecture hypothesis.
- `EXECUTION_MAP.md` — unit table, READY rule, discovery rule.
- `CURRENT.md` — the small current-state pointer; set so **exactly one unit is READY: U0.1**.
- `OPERATOR_RUNBOOK.md` — non-SWE copy/paste operating loop.
- `RESUME.md` — resume-after-interruption prompt.
- `SYNTHESIS_GATES.md` — S0 (Gate U0), S1 (U1.1 architecture), S2 (Gate U1) frontier prompts.
- `DEFERRED_NOT_NOW.md` — explicitly deferred items (do not fix in passing).
- `QUEUE_PATCH.md` — the queue-integration patch this unit applied.
- `prompts/` — `00_INSTALL_AND_BOOTSTRAP.md`, `GENERIC_BUILDER.md`, `GENERIC_QA.md`,
  `FRONTIER_SYNTHESIS.md`.
- `workunits/` — U0.1, U0.2, U0.3, U1.1, U1.2, U1.3, U1.4, U1.5, each with its own
  **Builder prompt** and **Foreign QA prompt** (verified: all 8 workunits carry both).

Repo patches (not wholesale replacements):

- `docs/queue.md` — a compact "Open — usability closure programme" section near the top,
  pointing to PROGRAM_CHARTER and CURRENT, listing U0.1 READY, U0.2/U0.3 BLOCKED, U1.x
  UNAUTHORIZED/BLOCKED. Existing issues/debt untouched.
- `docs/DECISIONS.md` — dated 2026-09-17 entry recording that the operator authorized
  **Gate U0 only, beginning with U0.1**; U1 remains unauthorized until Gate U0 synthesis; the
  programme does not authorize W2; bootstrap does not implement U0.1.

## Audit assumptions verified against current main

| Assumption | Status | Evidence |
|---|---|---|
| W1 complete / Gate B accepted | ✓ | `docs/queue.md` line 248; `W1_DECOMPOSITION.md`; Gate B packet `W1_6_GATE_B_PACKET.md` |
| Browser usable over legacy corpus | ✓ | 324 rows; smoke test green; Pages live |
| Candidate workflow stops at eligible | ✓ | T-P1 only; no T-P2 path in W1 |
| Local SQLite + committed text mirror | ✓ | `data/store/garden.export.txt` committed; no `garden.sqlite3` present |
| Mirror carries legacy/D3/D4 state, no new-candidate queue | ✓ | export sections: captures=legacy batch, legacy_verification=id 30, legacy_batch_membership; `[candidates]` empty |
| Issue #27 / front-door staleness unresolved | ✓ | `gh issue view 27` → OPEN |

## Acceptance criteria

- **A new agent can read CURRENT and identify exactly one authorized next unit.** ✓
  `CURRENT.md` → "Current READY unit: U0.1 — store lifecycle + mirror freshness invariant".
- **No existing W2/W3 authorization is implied.** ✓ PROGRAM_CHARTER: "This programme does not
  authorize W2." QUEUE_PATCH marks U1.1 UNAUTHORIZED until Gate U0 accepted. DEFERRED_NOT_NOW
  keeps W2/W3/ontology/writable-app downstream.
- **Every programme work unit includes its own builder + foreign-QA prompt.** ✓ All 8 workunits
  have both `## Builder prompt` and `## Foreign QA prompt` sections (grep-verified).
- **Queue, CURRENT, charter, and existing repo doctrine do not contradict each other about what
  is authorized.** ✓ The queue section, CURRENT, and the DECISIONS entry all agree: Gate U0 only,
  U0.1 READY, U1 unauthorized until Gate U0 synthesis.

## Evidence

- `python3 scripts/validate_quotes.py` → `RESULT: PASS` (docs-only change; data untouched).
- `python3 scripts/check_program_contracts.py` → `RESULT: PASS`.
- `python3 scripts/validate_homepage_preview_export.py` → `RESULT: PASS`.
- `quotes.csv` / `sources.csv` byte-identical (`9766db8c…` / `7aafcb67…`) — no data touched.
- No code, workflow, or data file changed; the diff is 22 files, all under `docs/` plus the
  root handoff.

## Out-of-scope findings

- **Front-door staleness (issue #27) is NOT fixed in this unit.** The programme's U0.2 unit is
  explicitly scoped to repair AGENTS/README/program-README front-door truth and close/disposition
  issue #27. Bootstrap deliberately does not touch front-door docs beyond installing the
  programme (per the bootstrap prompt: "Do not implement U0.1" and U0.2's scope).
- **`docs/program/README.md` read order is not updated** to list usability-closure. That is
  front-door routing work, owned by U0.2, not the bootstrap.

## Negative controls / QA

This is a docs-only bootstrap unit. The meaningful falsifiers are the acceptance criteria
themselves, verified above:

- Exactly one READY unit (U0.1) — verified in CURRENT.md.
- No future-gate authorization — verified by grep across PROGRAM_CHARTER / QUEUE_PATCH /
  DEFERRED_NOT_NOW / SYNTHESIS_GATES (no "W2 authorized", no "U1 authorized").
- Every workunit carries builder + foreign-QA prompts — verified by grep (8/8).
- Validators still green — verified by running all three.

Independent QA (fresh context, own re-runs) is expected to re-verify these and check for
authority conflicts and stale claims before merge.

## Exact next authorized action

**U0.1 — Store lifecycle + mirror freshness invariant.** The builder prompt is in
`docs/program/usability-closure/workunits/U0.1_STORE_LIFECYCLE.md` (§Builder prompt). It is the
only READY unit. Do not begin U0.2 until U0.1 merges, and do not begin U1.1 until Gate U0
synthesis (S0) accepts the gate.
