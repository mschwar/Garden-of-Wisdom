# Garden Usability Closure — CURRENT

> This file is the small current-state pointer. Historical evidence stays in handoffs, decisions, queue entries, and gate packets.

## Programme

`USABILITY-CLOSURE`

## Gate

`U0 — resumable workbench`

## Current READY unit

`U0.1 — store lifecycle + mirror freshness invariant`

## Last completed unit

`programme bootstrap`

## What is usable now

- Existing 324-row Garden browser/search/filter/copy surface.
- W1 candidate capture → normalization → duplicate hints → operator review through `eligible`.
- CI/acceptance/negative-control machinery around these surfaces.

## Current frontier

The W1 SQLite store is machine-local while the deterministic export is committed separately. Ordinary mutation can therefore leave the committed mirror stale unless the operator remembers the export ritual. Fresh-clone hydration is also a separate/manual path.

## Gate U0 proof target

Fresh clone → hydrate committed store → perform a real operator candidate action → persisted mirror current → delete/rebuild local SQLite from mirror → state identical.

## Stop rule

Do not begin U1 until Gate U0 is accepted by operator/frontier synthesis.

## Update rule

Every merged usability-closure unit must update:
- current gate;
- READY unit;
- last completed unit;
- frontier sentence;
- proof target if it changed.

Do not append history here. Replace current state.
