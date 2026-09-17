# Synthesis Gates

These are deliberate places where execution stops and frontier/operator judgment resumes.

## S0 — Gate U0 acceptance

Trigger: U0.3 merged and `CURRENT.md` says `SYNTHESIS REQUIRED — GATE U0`.

### Copy/paste prompt

Audit Gate U0 from fresh repo evidence.

Do not merely summarize the handoff. Independently verify the gate claim:

- persisted store can bootstrap from a clean/no-SQLite state;
- committed mirror reconstructs the same state;
- a real operator candidate/decision survived;
- mirror freshness cannot silently lie after a successful mutation;
- front-door docs accurately route a new agent to the current command surface;
- restart/reclone proof exists;
- open defects are classified as gate-blocking vs deferred.

Then answer:
1. Does the resumable-workbench walking skeleton actually walk?
2. What still depends on operator ritual or tacit knowledge?
3. Is any state authoritative only on one machine?
4. Are there any stale/front-door contradictions?
5. Which findings block U1?
6. If the gate evidence is sufficient, draft the exact repo-native authorization text for U1.1. Do not authorize beyond U1.1.

## S1 — U1.1 architecture/admission synthesis

Trigger: U1.1 PR/evidence complete.

### Copy/paste prompt

Review the U1.1 admission/read-model decision as an architecture gate.

The decision must identify one authoritative relationship among:
- legacy `quotes.csv` / `sources.csv`;
- corpus store canonical items;
- generated Garden-facing read model;
- browser.

Reject any design that creates two writable authorities or makes a generated file authoritative.

Check specifically:
- stable identity for new canonical items;
- minimum admission metadata;
- source/source_id behavior;
- research_state → visible verification projection;
- canonical reversal/retirement behavior;
- deterministic projection/rebuild;
- clean-clone recoverability;
- current browser/parser assumptions;
- backward compatibility for the 324 legacy rows.

Return:
- accepted architecture or blocking concerns;
- exact operator decision text for `docs/DECISIONS.md`;
- exact authorization for U1.2 only.

## S2 — Gate U1 acceptance

Trigger: U1.5 merged and `CURRENT.md` says `SYNTHESIS REQUIRED — GATE U1`.

### Copy/paste prompt

Audit Gate U1 from first principles.

Prove, using current main and the committed persistent artifacts, that one real newly encountered passage can travel:

encounter → capture → normalize → human accept → eligible → explicit canonical admission → deterministic Garden read model → live/local browser → rediscovery after clean rebuild/reclone.

Check that:
- the original capture survived byte-identically;
- every state transition is audited;
- canonical did not imply verified;
- open uncertainty remains visible in the browser;
- the projection is derived, reproducible, and not a second writable authority;
- the browser no longer depends only on the frozen legacy corpus;
- fresh-clone recovery reproduces the item;
- existing 324 legacy rows did not silently change meaning.

Then give a frontier synthesis:
- what is genuinely usable now;
- remaining dependability gaps;
- whether the highest-leverage next move is W2 research, operator ergonomics, release hardening, or something else;
- what should remain deferred.

Do not authorize W2 automatically.
