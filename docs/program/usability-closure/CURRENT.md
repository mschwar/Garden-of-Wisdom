# Garden Usability Closure — CURRENT

> **Execution authority.** This file is intentionally small. Standing product/system reality lives
> in `docs/PRODUCT_REALITY.md`; historical evidence stays in handoffs, decisions, queue entries,
> and gate packets.

## Programme

`USABILITY-CLOSURE`

## Gate

`U0 — resumable workbench`

## Current READY unit

`U0.3 — real persistent operator canary + Gate U0 packet`

## Last completed unit

`U0.2 — truthful front door + current-state routing`

## Last reconciliation

`R0 — product reality & system reconciliation` — COMPLETE. R0 is a one-off product/system
reconciliation outside the numbered U-unit chain; `scripts/check_front_door.py` currently models
“last completed unit” as a `U<gate>.<unit>` execution unit, so U0.2 remains the structural
last-completed U-unit while this explicit field records the later reconciliation.

## What is usable now

- Existing 324-row Garden browser/search/filter/copy surface.
- The existing Garden browser and W1 candidate workbench are usable as summarized in
  `docs/PRODUCT_REALITY.md`; this section exists only as the execution front door's compact
  capability pointer, not as a second product dashboard.
- Store bootstrap/status/sync and front-door resume routing are mechanized; U0.3 is the pending
  real-state ecological proof.

## Current frontier

The repo now has:
- a mechanized SQLite↔mirror persistence lifecycle;
- a truthful execution front door;
- a reconciled product boundary centered on **Passage**, with Garden separated from Initiate;
- a standing product-reality dashboard at `docs/PRODUCT_REALITY.md`.

The frontier is unchanged in substance: **U0.3 must run one real operator passage through the
actual persistent workbench and prove it survives restart/rebuild from the committed mirror.**

## Gate U0 proof target

Fresh clone → hydrate committed store → perform a real operator passage action → persisted mirror
current → delete/rebuild local SQLite from mirror → state identical.

## Stop rule

Do not begin U1 until Gate U0 is accepted by operator/frontier synthesis.

## Update rule

Every merged usability-closure unit must update:
- current gate;
- READY unit;
- last completed U-unit;
- frontier sentence;
- proof target if it changed.

Product reality belongs in `docs/PRODUCT_REALITY.md`, not duplicated here. Update that dashboard
when a merged gate materially changes what is usable, repeatable or dependable; do not turn it into
a per-commit log. Do not append history here; replace current execution state.
