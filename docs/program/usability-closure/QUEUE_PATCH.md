# Queue integration patch

The bootstrap unit should insert a **small current section** near the top of `docs/queue.md`, not duplicate the full programme documents.

Suggested shape:

## Open — usability closure programme

Authority: `docs/program/usability-closure/PROGRAM_CHARTER.md`  
Current pointer: `docs/program/usability-closure/CURRENT.md`

- [ ] U0.1 — store lifecycle + mirror freshness invariant — READY
- [ ] U0.2 — truthful front door + current-state routing — BLOCKED on U0.1
- [ ] U0.3 — real persistent operator canary + Gate U0 packet — BLOCKED on U0.2
- [ ] U1.1 — canonical admission/read-model architecture decision — UNAUTHORIZED until Gate U0 accepted
- [ ] U1.2 — minimum admission metadata + T-P2 promotion — BLOCKED on U1.1 operator decision
- [ ] U1.3 — deterministic unified Garden read model — BLOCKED on U1.2
- [ ] U1.4 — browser consumes unified read model — BLOCKED on U1.3
- [ ] U1.5 — persistent full-loop proof + Gate U1 packet — BLOCKED on U1.4

Do not append execution transcripts to this section. On closeout, change the checkbox/status and put evidence in the unit handoff/gate packet.

Existing issues/debt remain in their current queue sections. If U0.2 closes issue #27, update that issue/queue entry explicitly rather than leaving duplicate open truth.
