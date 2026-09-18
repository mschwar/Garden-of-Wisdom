# Explicitly Deferred — do not fix in passing

These items matter, but they do not define Gate U0/U1.

Keep them in the normal repo queue unless a current unit proves one is a blocker.

- Candidate withdrawal / whitespace-only permanent candidate (existing issue #30).
- Multiple captures attached to one candidate.
- Persistence of all optional candidate-envelope fields.
- Broad verification/research evidence workbench (W2).
- General row-level verification evidence redesign.
- `item_type` ontology cleanup / shape split.
- Multi-valued tradition/domain/period ontology questions.
- Source URL schema expansion.
- Remaining Bahá’í attribution audit.
- Dedicated duplicate-review browser UI.
- Automated discovery adapters.
- Agentic research at scale.
- Broad enrichment/exploration.
- Writable web application.
- Mass migration of the 324 legacy rows into per-item candidate records.
- Branch-protection / deploy-release policy beyond what is strictly needed to prove U0/U1. Queue release hardening separately if it remains materially risky.
- Further front-door/meta-assurance expansion (including the local-only must-stay-green
  battery follow-up and negative-control harness GREEN_OK defect) unless a concrete current
  product/dependability failure proves it is the active constraint. Keep existing guards; do not
  build more checker-for-checker machinery ahead of U0.3/U1.

Rule: if a deferred item blocks the current gate in reality, document the evidence and promote it explicitly through `docs/queue.md`; do not silently broaden a work unit.
