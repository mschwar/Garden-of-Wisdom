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
- Corpus-program **W1 is complete** (W1.1–W1.6 merged; Gate B accepted 2026-09-13): the
  candidate workbench runs as `scripts/garden_*.py` over the persisted SQLite store plus the
  committed mirror `data/store/garden.export.txt`. **W2 is not started.**
- W1 candidate capture → normalization → duplicate hints → operator review through `eligible`.
- CI/acceptance/negative-control machinery around these surfaces.
- Mechanized store lifecycle (bootstrap, status, sync) and mutation invariant keeping committed mirror current.

## Current frontier

The SQLite↔mirror persistence lifecycle is mechanized with automatic mirror sync across all operator mutation surfaces, freshness status detection, divergence protection, and fresh-clone bootstrap. The front-door docs (AGENTS.md, README.md, docs/program/README.md, PRODUCT_DOCTRINE.md) route live status here and are guarded by `scripts/check_front_door.py`. The next frontier is the real persistent operator canary (U0.3): a real operator action must survive a restart and a rebuild of the local store from the committed mirror.

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
