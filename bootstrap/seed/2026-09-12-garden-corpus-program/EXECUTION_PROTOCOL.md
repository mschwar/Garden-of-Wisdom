# Execution protocol

## Program loop

`frontier planning -> bounded packet -> low-cost/local execution -> evidence-bearing stop gate -> frontier review`

The purpose is to avoid holding the program in the operator's head and avoid paying frontier-model cost for routine execution.

## Work-unit loop

Each implementation or research unit should follow:

1. Read canonical doctrine, current wave contract, and unit spec.
2. Confirm repo state and dependencies.
3. Create one isolated branch/worktree/workspace for the unit.
4. Execute the whole bounded unit with minimal operator back-and-forth.
5. Run deterministic tests/validators and collect evidence.
6. Open one PR when code/docs/data changes are involved.
7. Have the same primary agent invoke an independent child/foreign QA pass that did not author the work.
8. Resolve actionable QA findings.
9. Record newly discovered out-of-scope work in the appropriate queue/spec rather than expanding scope.
10. Re-run acceptance evidence.
11. Commit/merge the complete unit.
12. Report outcome, evidence, debt, and exact next authorized unit.

Default expectation: **one task/spec -> one workspace -> one PR -> foreign QA -> fixes -> merge -> report**.

## Agent interaction policy

Agents should prefer reasonable documented assumptions over repeated operator questions. Escalate only when a decision changes doctrine, requires a human gate, risks irreversible semantic loss, or makes the acceptance contract impossible to satisfy.

Do not stop after scaffolding when the unit contract calls for a complete vertical slice. Do not continue into the next work unit merely because the current one finished early.

## Evidence requirement

A claim of completion must point to evidence appropriate to the unit, for example:

- tests/validator output,
- migration round-trip,
- fixture results,
- UI smoke evidence,
- before/after counts,
- research sources and locators,
- state-transition examples,
- foreign QA disposition.

"Implemented" is not evidence.

## Stop gates

A wave-ending agent must stop after producing the wave gate package. It must not begin the next wave. The gate package should include:

- what landed,
- acceptance results,
- unresolved debt,
- decisions made,
- decisions still required,
- adversarial/failure cases,
- recommended next-wave decomposition,
- explicit statement that the next wave is not started.

## Cost posture

Use deterministic scripts/tests first, local or inexpensive agents for bounded execution, and frontier review at architectural or wave boundaries. Escalate expensive models for ambiguity and synthesis, not for mechanical repo work.
