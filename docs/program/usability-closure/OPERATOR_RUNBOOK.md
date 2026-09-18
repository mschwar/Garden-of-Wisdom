# Operator Runbook — non-SWE mode

You can run this programme entirely by copy/paste.

## Normal daily loop

### 1. Reorient

Tell the agent:

> Open Garden-of-Wisdom. Read AGENTS.md, Product Doctrine, docs/PRODUCT_REALITY.md, docs/program/usability-closure/CURRENT.md, docs/queue.md, docs/DECISIONS.md, and the READY work unit. Verify current main. Tell me only: current gate, READY unit, any blocker, and the exact builder prompt I should run. Do not start implementation yet.

If the answer disagrees with `CURRENT.md`, use the resume/synthesis prompt instead of guessing.

### 2. Build one unit

Copy the **Builder prompt** from the READY unit document into the coding agent.

The builder is expected to:

- create its own branch/worktree;
- implement the bounded unit;
- add/modify tests;
- add at least one meaningful falsifier/negative control where appropriate;
- update RUNBOOK/DECISIONS/queue only where the unit requires;
- create a unit handoff;
- open one PR;
- stop for QA.

### 3. Foreign QA

Start a fresh context/agent. Copy the **Foreign QA prompt** from the same unit.

QA must review the PR independently and must not rely on builder claims.

### 4. Resolve and merge

Give the builder the QA output and say:

> Resolve every high/medium finding, address or explicitly disposition low findings, re-run the unit acceptance and relevant repo acceptance, update the handoff with the QA verdict, merge the PR, update docs/queue.md and CURRENT.md, clean up the branch/worktree, and STOP. Do not begin the next unit.

### 5. Repeat only if CURRENT says a normal next unit is READY

If CURRENT says `SYNTHESIS REQUIRED`, use `SYNTHESIS_GATES.md`.

## What you should never need to do manually

You should not need to choose git commands, branch names, test commands, migrations, file paths, or merge mechanics. The unit prompt gives the agent enough context to determine them from the repo.

## What you may be asked for

Only genuine human-gate inputs:

- a real passage you actually want to capture for the U0 canary;
- whether to accept/hold/reject/duplicate that passage;
- whether to approve the U1.1 authoritative-data architecture;
- whether Gate U0/U1 evidence is good enough to proceed.

## If an agent says there is “nothing left”

Do not accept that at face value. Run the resume prompt and compare the repo against the gate proof target. A gate is complete only when its operator-observable outcome is demonstrated.
