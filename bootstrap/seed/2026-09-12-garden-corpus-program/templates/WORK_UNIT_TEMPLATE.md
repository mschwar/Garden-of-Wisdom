# Work unit template

## ID / title

`<WAVE>.<N> — <short title>`

## Primary lane

Name one primary permanent work lane and any secondary lanes.

## Why this exists

State the concrete problem this unit solves and why it is needed for the current wave gate.

## Inputs / dependencies

List canonical docs, prior units, fixtures, schemas, decisions, and repo paths the agent must read.

## In scope

Use explicit, testable deliverables.

## Out of scope

Name adjacent tempting work that must be queued rather than implemented.

## Human gates

List any decisions the agent cannot make autonomously.

## Acceptance criteria

Define observable completion conditions.

## Evidence required

Name tests, validator output, fixtures, screenshots/manual checks, research evidence, or before/after facts needed to support completion.

## Execution contract

Default: one isolated branch/worktree -> complete bounded implementation -> one PR -> independent/foreign QA -> resolve findings -> record discovered work -> rerun acceptance -> merge -> report.

## Stop condition

State exactly where the agent must stop and what the next authorized unit is. Never imply authorization for the next wave.
