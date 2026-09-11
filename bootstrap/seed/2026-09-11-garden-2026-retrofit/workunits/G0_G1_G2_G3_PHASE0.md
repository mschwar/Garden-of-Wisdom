# Garden Work Unit — Phase 0: archaeology + retrofit + data rehabilitation + browser

**State:** authorized by this packet  
**Stop gate:** mandatory human review before donor verification/export

## Scope

### G0 — archaeology
Reconstruct:
- repo intent from README/history,
- exact current files/data shape,
- quote/source counts,
- ID gaps,
- traditions/authors/sources/tags,
- malformed rows,
- duplicate/near-duplicate candidates,
- quote-type ambiguities,
- encoding damage and likely origin.

### G1 — agent-first retrofit
Add the minimum durable layer:
- `AGENTS.md`
- canonical `README.md`
- `docs/product/PRODUCT_DOCTRINE.md`
- `docs/data/DATA_CONTRACT.md`
- `docs/data/DATA_QUALITY_REPORT.md`
- `docs/queue.md`
- `docs/RUNBOOK.md`
- decision log
- validator commands

Do not introduce heavyweight frameworks without evidence they are needed.

### G2 — data rehabilitation
Requirements:
- preserve original quote/source bytes before normalization;
- determine actual source encoding or corruption mechanism;
- produce valid UTF-8 canonical working files;
- do not silently “fix” quote wording;
- represent uncertainty explicitly;
- remove `.DS_Store` from tracked content and add appropriate ignore rule;
- define quote type / verification / provenance fields or an equivalent normalized representation;
- preserve stable legacy IDs even if gaps exist.

### G3 — quote browser/audit console
Build a static, easily served/opened interface that supports:
- global search,
- sort,
- filters for tradition/author/source/tags/type/verification,
- visible counts,
- copy quote,
- copy quote + attribution,
- copy machine-readable record,
- issue/problem badges,
- source/provenance detail,
- duplicate/near-duplicate review support,
- responsive layout.

Prefer plain HTML/CSS/JS or another proportionate static implementation.

## Not authorized
- mass canonical verification of hundreds of quotes,
- deleting records merely because they look wrong,
- importing full source texts,
- rewriting the corpus as if all rows were exact scripture,
- homepage export,
- changing the project's multi-faith identity,
- building a backend/auth/database.

## Required evidence
- before/after file inventory
- encoding diagnosis
- validator output
- browser smoke test
- quote/source counts
- issue counts
- screenshots or equivalent browser evidence
- handoff with open questions
