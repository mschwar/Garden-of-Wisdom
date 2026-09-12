# Acceptance gates

## Gate A — W0 doctrine

Pass only if all are true:

- Curation state and research/evidence state are explicitly separate.
- A source-agnostic candidate envelope is defined.
- Original capture provenance is preserved by contract.
- The verification contract says what evidence is sufficient to mark a claim verified.
- Disputed and unverifiable outcomes are first-class, not errors to be forced into certainty.
- Faceted classification is the working model; no premature single category enum is hardened.
- W1 is decomposed into bounded work units with acceptance criteria.
- No W1 runtime implementation has started.

Required scenario test: walk an uncited, possibly misattributed passage from capture through every plausible curation/research outcome and show which transitions require human authority.

## Gate B — W1 intake/curation

Pass only if a representative batch of messy manual submissions can be ingested and reviewed while preserving originals, provenance, decision history, and duplicate hints. No curation action may imply verification.

## Gate C — W2 research

Pass only if the system truthfully represents the ten adversarial cases in `STATE_MACHINE.md`, with evidence linked to findings and no forced certainty.

## Gate D — W3 canonical/enrichment

Pass only if canonical promotion rules are deterministic, uncertainty remains visible, and classification/relationships cannot silently upgrade evidence status.

## Gate E — W4 discovery

Pass only if one bounded automated source can produce a noisy candidate batch through the same intake seam used by manual capture, with no direct canonical writes.

## Gate F — W5 agentic research

Pass only if repeated agent research cases demonstrate reproducible evidence collection, independent QA, bounded failure behavior, and acceptable cost/quality before scale-up.

## Gate G — W6 intelligence

Pass only if higher-order features consume canonical/provenance-aware data and cannot become an alternate ungoverned source of truth.
