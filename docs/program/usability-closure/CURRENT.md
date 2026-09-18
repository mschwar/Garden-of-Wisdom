# Garden Usability Closure — CURRENT

> This file is the small current-state pointer. Historical evidence stays in handoffs, decisions, queue entries, and gate packets.

## Programme

`USABILITY-CLOSURE`

## Gate

`U0 — resumable workbench`

## Current READY unit

`U0.2 — truthful front door + current-state routing`

## Last completed unit

`U0.1 — store lifecycle + mirror freshness invariant`

## What is usable now

- Existing 324-row Garden browser/search/filter/copy surface.
- W1 candidate capture → normalization → duplicate hints → operator review through `eligible`.
- CI/acceptance/negative-control machinery around these surfaces.
- Mechanized store lifecycle (bootstrap, status, sync) and mutation invariant keeping committed mirror current.

## Current frontier

The SQLite↔mirror persistence lifecycle is mechanized with automatic mirror sync across all operator mutation surfaces, freshness status detection, divergence protection, and fresh-clone bootstrap. The front-door docs (README.md, AGENTS.md) still present outdated paths and need truthful current-state routing.

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
