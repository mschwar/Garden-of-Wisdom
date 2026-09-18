# Garden Usability Closure — CURRENT

> **Execution authority.** This file is intentionally small. Standing product/system reality lives
> in `docs/PRODUCT_REALITY.md`; historical evidence stays in handoffs, decisions, queue entries,
> and gate packets.

## Programme

`USABILITY-CLOSURE`

## Programme state

`SYNTHESIS REQUIRED — GATE U0` — U0.3 is merged and the Gate U0 packet is submitted
(`docs/program/usability-closure/U0_GATE_PACKET.md`). Execution has stopped here **by design**:
no unit is authorized. Resume with the S0 prompt in
`docs/program/usability-closure/SYNTHESIS_GATES.md`.

## Gate

`U0 — resumable workbench`

## Current READY unit

`none` — while Gate U0 awaits synthesis no unit is READY; `docs/queue.md` names what a later gate would release, marked not authorized.

## Last completed unit

`U0.3 — real persistent operator canary + Gate U0 packet`

## Last reconciliation

`R0 — product reality & system reconciliation` — COMPLETE. R0 is a one-off product/system
reconciliation outside the numbered U-unit chain; it changed no runtime, schema, CSV, store, browser
or CI surface, and `scripts/check_front_door.py` models "last completed unit" as a `U<gate>.<unit>`
execution unit, so R0 is recorded here rather than as a U-unit. The structural last-completed U-unit
is now U0.3.

## What is usable now

- Existing 324-row Garden browser/search/filter/copy surface.
- The existing Garden browser and W1 candidate workbench are usable as summarized in
  `docs/PRODUCT_REALITY.md`; this section exists only as the execution front door's compact
  capability pointer, not as a second product dashboard.
- Store bootstrap/status/sync and front-door resume routing are mechanized.
- **The persistent workbench has been used for real, not only in fixtures** (U0.3): the operator's
  own capture `cap-2026-09-18-0001` and candidate `cand-2026-09-18-0001`, with its curation
  decision, survived mirror sync, deletion of the local SQLite file, bootstrap from the committed
  mirror, and a fresh clone of the pushed branch — the export bytes are identical
  (`3b5c5407f5347835e091ad36bf5fb945c8ff2a4d758cdd902a8ca1c05b4b6377`, 27,091 bytes) in all of them.

## Current frontier

The repo now has:

- a mechanized SQLite↔mirror persistence lifecycle;
- a truthful execution front door;
- a reconciled product boundary centered on **Passage**, with Garden separated from Initiate;
- a standing product-reality dashboard at `docs/PRODUCT_REALITY.md`;
- real-state ecological proof of the workbench (U0.3).

Gate U0 is **submitted and awaiting synthesis**. The evidence — capture, decision transcript, recovery
transcripts and the guard's falsifiers — is in `docs/program/usability-closure/U0_GATE_PACKET.md` and
`GARDEN_U0_3_HANDOFF.md`. What remains is not execution: it is the operator/frontier judgment in
`SYNTHESIS_GATES.md` §S0 that decides whether U1 may begin.

## Gate U0 proof target

Fresh clone → hydrate committed store → perform a real operator passage action → persisted mirror
current → delete/rebuild local SQLite from mirror → state identical. **Demonstrated 2026-09-18**
(U0.3); the recovery transcript is in `U0_GATE_PACKET.md`.

## Stop rule

Do not begin U1 until Gate U0 is accepted by operator/frontier synthesis. While `## Programme state`
reads `SYNTHESIS REQUIRED — GATE U0`, **no unit is authorized**; `scripts/check_front_door.py`
enforces that in both directions (a READY unit declared anywhere while this state holds is a build
failure, and so is declaring this state decoratively while a unit stays READY).

## Update rule

Every merged usability-closure unit must update:
- programme state;
- current gate;
- READY unit;
- last completed U-unit;
- frontier sentence;
- proof target if it changed.

Product reality belongs in `docs/PRODUCT_REALITY.md`, not duplicated here. Update that dashboard
when a merged gate materially changes what is usable, repeatable or dependable; do not turn it into
a per-commit log. Do not append history here; replace current execution state.
