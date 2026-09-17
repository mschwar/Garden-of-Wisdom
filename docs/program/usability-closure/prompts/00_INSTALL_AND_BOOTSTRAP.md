# Bootstrap prompt — install the usability-closure programme

Copy/paste this into an agent with write access to `mschwar/Garden-of-Wisdom`.

---

You are bootstrapping a new bounded programme in `mschwar/Garden-of-Wisdom`: **Usability Closure**.

The attached/package directory `repo-patch/docs/program/usability-closure/` is planning input. The repository is authoritative.

First:
1. verify current `main`, git status, recent merged PRs, open PRs/issues, CI, and Pages;
2. read `AGENTS.md`, `README.md`, `docs/product/PRODUCT_DOCTRINE.md`, `docs/RUNBOOK.md`, `docs/queue.md`, `docs/DECISIONS.md`, `docs/program/README.md`, `docs/program/W1_DECOMPOSITION.md`, `docs/program/W1_6_GATE_B_PACKET.md`, `docs/program/STATE_MODEL.md`, and the current store/browser architecture docs;
3. confirm whether the audit assumptions still hold:
   - W1 is complete / Gate B accepted;
   - browser is usable over the legacy corpus;
   - candidate workflow stops at eligible;
   - local SQLite + committed text mirror remain the persistence design;
   - committed store mirror currently carries legacy/D3/D4 state and no ongoing new-candidate queue unless newer work has landed;
   - issue #27/front-door staleness is still unresolved unless newer work closed it.

Then install/adapt the usability-closure programme under:
`docs/program/usability-closure/`

Do NOT blindly copy stale baseline statements. Reconcile them to current main.

Patch `docs/queue.md` with a compact programme section pointing to PROGRAM_CHARTER and CURRENT. Record in `docs/DECISIONS.md` that the operator authorized **Gate U0 only**, beginning with U0.1. U1 remains unauthorized until Gate U0 synthesis.

Set CURRENT so exactly one unit is READY: U0.1.

Do not implement U0.1 in this bootstrap unit.

Execution:
- one branch/worktree;
- docs/programme-install scope only;
- one PR;
- independent QA focused on authority conflicts, stale claims, and whether the programme accidentally authorizes future gates;
- resolve findings;
- merge;
- update CURRENT/queue;
- create `GARDEN_USABILITY_CLOSURE_BOOTSTRAP_HANDOFF.md`;
- STOP.

Acceptance:
- a new agent can read CURRENT and identify exactly one authorized next unit;
- no existing W2/W3 authorization is implied;
- every programme work unit includes its own builder + foreign-QA prompt;
- queue, CURRENT, charter, and existing repo doctrine do not contradict each other about what is authorized.
