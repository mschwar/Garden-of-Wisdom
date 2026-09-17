# Resume Instructions

Use this after any interruption, new chat, machine restart, or day boundary.

## Copy/paste resume prompt

You are resuming the Garden-of-Wisdom usability-closure programme.

Do not infer state from this prompt and do not trust an old handoff as current.

1. Verify current `main`, git status, recent merged work, open PRs, and CI.
2. Read, in this order:
   - `AGENTS.md`
   - `docs/product/PRODUCT_DOCTRINE.md`
   - `docs/program/usability-closure/CURRENT.md`
   - `docs/program/usability-closure/PROGRAM_CHARTER.md`
   - `docs/queue.md`
   - `docs/DECISIONS.md`
   - the work-unit document named READY in CURRENT
   - the most recent handoff for the programme
3. Reconcile the repo, CURRENT, queue, and open PR state.
4. If a unit is partially executed, resume that exact unit; do not start another.
5. If its PR is open, tell me whether the next action is builder work, foreign QA, findings resolution, or merge.
6. If a unit was merged but CURRENT/queue were not advanced, repair the closeout first.
7. If CURRENT says `SYNTHESIS REQUIRED`, stop and give me the synthesis prompt; do not authorize the next unit yourself.
8. If there is a contradiction, report it explicitly and prefer executable/current repo evidence over stale prose.

Return a compact operator brief:
- current main SHA;
- current gate;
- active/READY unit;
- unit state: NOT STARTED / BUILDING / PR OPEN / QA / FIXING / MERGED-CLOSEOUT / SYNTHESIS;
- blocker, if any;
- exact next copy/paste prompt.

Do not start implementation until I paste the returned prompt back.
