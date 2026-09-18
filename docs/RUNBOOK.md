# Runbook

## Where are we? (resume here)

Live programme status is not in this file. Read `docs/program/usability-closure/CURRENT.md`
for the current gate, the single READY unit and the last completed unit, then `docs/queue.md`
and `docs/DECISIONS.md`, then the READY unit's document under
`docs/program/usability-closure/workunits/` and the matching `GARDEN_<UNIT>_HANDOFF.md` at repo
root (root handoffs and the W0/W1 gate packets are historical evidence, not status). If the
local store is absent, hydrate it before anything else:
`python3 scripts/garden_store.py bootstrap --dir data/store`, then
`python3 scripts/garden_store.py status --dir data/store` and confirm `CURRENT`. `AGENTS.md`
carries the same resume path plus the full command surface, and
`python3 scripts/check_front_door.py` asserts that routing has not drifted.

## Validate the data

```
python3 scripts/validate_quotes.py
```

Exits 0 with `RESULT: PASS` if there are no hard-integrity failures (parse errors, malformed
UTF-8, duplicate IDs, missing required fields, invalid controlled values, dangling
`source_id` references, or a near-duplicate score that changes when the rows are visited in the
other order). Everything else it prints (near-duplicates, unresolved source links,
unresolved-glyph rows, counts by `item_type`/`verification_status`) is curation-queue signal,
not a failure — read `docs/data/DATA_QUALITY_REPORT.md` for how to interpret it.

Four lines of the near-duplicate block are checks, not signal:

- `pair detection re-run with the corpus rows reversed` — the same sweep over the same rows in the
  other order must produce an identical result, because a pair's number is a property of the pair,
  not of row order;
- `near-duplicate reasons re-derived from the rows and matched` — every printed reason must name the
  evidence that actually holds, including a shared citation that also clears the text threshold;
- the pair set is also re-derived over **every unordered pair of rows with no grouping** and compared
  with the reported sweep, so narrowing the scope (e.g. back to one `tradition`) fails the run naming
  the pairs it would have missed;
- the imported locator rule is pinned on two canonical values and the corpus must still offer pairs
  that rule suppresses, so a silent redefinition of the rule or an empty suppression fails loudly.

Any of them failing is a `RESULT: FAIL`. The score is the **mean of both directional
`difflib.SequenceMatcher.ratio()` values** (that ratio is asymmetric); the sweep is **corpus-wide**,
and a shared `source_ref` counts as evidence only when the citation carries a locator (an Arabic digit,
a Roman numeral or `§`) — the same rule W1.4's store-side hint generator applies, imported from
`scripts/garden_normalize.py`. See the script's docstring and `docs/DECISIONS.md` ("The near-duplicate
sweep is corpus-wide …"). The corpus-wide sweep is every unordered pair (52,326 of them), so the run
takes ~21s; `pair_similarity` pre-filters pairs that provably cannot clear the threshold.

To re-freeze `docs/data/DATA_QUALITY_REPORT.md` after changing the heuristic: run the validator,
paste its stdout verbatim into a new dated section (never overwrite the point-in-time transcript),
and re-derive the pair-class counts the queue's D6 item cites.

## Check the corpus-program doctrine set

```
python3 scripts/check_program_contracts.py
```

Documentation-only test (no data, no runtime): it parses the transition table out of
`docs/program/STATE_MODEL.md` and the required envelope fields out of
`docs/program/CANDIDATE_ENVELOPE.md`, then simulates the twelve scenarios in
`docs/program/fixtures/w0_scenarios.json` (the ten canonical adversarial cases plus the two
supplementary walkthroughs S11/S12) and asserts the state machine, the operator gates, the
per-claim evidence standard, and the visible-uncertainty rule all hold. Exits 0 with
`RESULT: PASS`. Run it after editing anything under `docs/program/`.

## Create and check the corpus store (W1.1)

```
python3 scripts/garden_store.py create --dir DIR
python3 scripts/garden_store.py export --dir DIR
python3 scripts/check_garden_store.py
```

`scripts/garden_store.py` is the W1.1 store of record: one SQLite file (`garden.sqlite3`,
standard-library `sqlite3`, no server, no network) plus a deterministic text export
(`garden.export.txt`) that is the committed, diffable mirror. `create` is idempotent — a second
run applies nothing and says so. `import --dir DIR --from FILE` loads an export (a no-op if the
store already holds that exact text) and `verify --dir DIR` re-runs the
export → re-import → byte-identical comparison. Store lifecycle management (`bootstrap`
to hydrate SQLite from the mirror, `status` to check freshness, and `sync` to refresh the mirror)
is detailed under §"Manage store lifecycle: bootstrap, freshness status, and sync (U0.1)".
`scripts/check_garden_store.py` runs the full
acceptance in a throwaway temp directory — create-from-empty, write, read back, export, wipe,
re-import, byte-identical, plus idempotency, append-only/immutability enforcement, the four
state vocabularies, and requirement 6's queries at ~2,000 rows — and exits non-zero with
`RESULT: FAIL` and one `FAIL:` line per broken check. It never touches `quotes.csv`/`sources.csv`
(it hashes both before and after). See `docs/program/W1_1_STORAGE_AND_SCHEMA.md`.

## Check the candidate envelope contract (W1.2)

```
python3 scripts/check_garden_envelope.py
python3 scripts/garden_envelope.py serialize --envelope FILE
python3 scripts/garden_envelope.py validate  --envelope FILE [--captures FILE] [--rule N]
```

`scripts/garden_envelope.py` implements the `garden.candidate-envelope/1` contract
(`docs/program/CANDIDATE_ENVELOPE.md`) as a canonical serialized JSON form plus a deterministic
validator for rules 1–6, each violation reporting its rule id (`rule-1` … `rule-6`). It also
bridges a valid envelope into W1.1's store: `store_capture` writes the immutable capture row from
the envelope's `captured_*` fields, `store_envelope` validates all six rules against the store's
own capture records and then writes the candidate and its duplicate hints, and `read_envelope`
reconstructs the envelope's required fields from the store. The sentinel vocabulary
(`unknown`/`und`/`none`/`legacy-import`) is carried verbatim — never as an empty string, and a
missing required field is never defaulted. The CLI is a **read-only diagnostic** (it inspects an
envelope file; it creates no capture and records no decision — the intake surface is W1.3).
`scripts/check_garden_envelope.py` runs the full acceptance + evidence suite (102 checks) in a
throwaway temp directory: the serialized form round-trips byte-identically and is key-order
independent, every valid fixture and all twelve W0 scenario envelopes pass all six rules, every
rule has a failing fixture that reports exactly that rule id, sentinels survive validation,
serialization and SQLite verbatim, a valid envelope is stored and read back with all 21 required
fields intact, and `quotes.csv`/`sources.csv` are hashed before and after. Exits non-zero with
`RESULT: FAIL` and one `FAIL:` line per broken check. See
`docs/program/W1_2_ENVELOPE_VALIDATOR.md`.

## Submit a candidate by hand (W1.3)

```
python3 scripts/garden_store.py create --dir data/store          # once; idempotent
python3 scripts/garden_submit.py submit --dir data/store --text 'TEXT' --capture-method pasted-text
python3 scripts/garden_submit.py submit --dir data/store --text-file page.txt --capture-method book-scan
cat page.txt | python3 scripts/garden_submit.py submit --dir data/store --stdin --capture-method pasted-text
python3 scripts/check_garden_submit.py                            # the W1.3 acceptance + evidence run
```

One submission writes **one immutable capture** (the text byte for byte, as encountered) and **one
candidate** at its intake states (`new` / `not_started` / `candidate_only` / `queued`). It records
no decision, sets no research state, and generates no duplicate hints (that is W1.4); there is no
review or accept command (that is W1.5) — the stored record is read back out with
`garden_store.py export --dir DIR` or `dump --dir DIR`.

`--capture-method` is required and has no default: how the text was encountered is evidence. The
raw text is never trimmed, quote-normalized, or glyph-repaired, so a literal `_` placeholder and
curly quotes survive verbatim. Omitting an optional flag (`--attribution`, `--citation`,
`--source-reference`, `--language`, …) uses the contract's sentinel for that field (`unknown` /
`none` / `und`); passing the flag *empty* is refused with the field named. If `--candidate-text` /
`--candidate-author` / `--candidate-source-ref` differ from the capture, `--normalization-notes` is
required — the CLI performs no normalization of its own (W1.4 owns that algorithm) and will not
record one without a reason.

Record ids are allocated as `cap-YYYY-MM-DD-NNNN` / `cand-YYYY-MM-DD-NNNN`, where the day is the
capture day and the number is the store's next free one. Add `--json` for one machine-readable
canonical object, `--emit-envelope FILE` to also write the envelope JSON. A refused submission
writes nothing at all.

The canonical store lives at `data/store/`: `garden.sqlite3` is git-ignored (machine-local,
non-diffable) and `garden.export.txt` next to it is the committed text mirror. See
`docs/program/W1_3_SUBMISSION_CLI.md`.

## Normalize a candidate and generate duplicate hints (W1.4)

```
python3 scripts/garden_normalize.py normalize --dir data/store --all        # write every proposal
python3 scripts/garden_normalize.py normalize --dir data/store --candidate-id cand-2026-09-13-0001
python3 scripts/garden_normalize.py hints     --dir data/store --all        # rebuild every hint set
python3 scripts/garden_normalize.py hints     --dir data/store --candidate-id cand-2026-09-13-0001
python3 scripts/garden_normalize.py classify  --reference 'Oral Tradition'  # specific / generic / none
python3 scripts/garden_normalize.py describe  --text 'The earth is but one country…'
python3 scripts/check_garden_normalize.py                                   # the W1.4 acceptance + evidence run
```

`normalize` writes the Garden-facing **proposal** for a stored candidate — `candidate_text`,
`candidate_author`, `candidate_source_ref`, `normalization_notes` — and never touches the capture:
`captured_text` stays byte for byte the encounter, with its literal `_` placeholders, curly quotes
and untrimmed whitespace intact. The declared transforms are NFC recomposition; curly quotes/primes,
dashes, ellipses and no-break spaces canonicalized; whitespace runs collapsed and boundary
whitespace trimmed; and every change is named, with counts, in `normalization_notes`. When nothing
changed the note is `identical to capture`. A value the algorithm does not declare is never touched,
and the `_` placeholder glyph is **preserved and reported, never guessed**.

`hints` rebuilds a candidate's `{kind, target, basis}` duplicate hints by comparing the store's
candidates: `exact-text`, `near-text` (normalized case-folded similarity >= **0.60**, the mean of the
two directional `difflib` ratios), `same-reference` and `same-passage` — the last two only when the
shared citation is **specific** (it carries a locator: `Gita 2.47`, `Gleanings, CV`, `p. 26`), so a
label like `Oral Tradition` produces no reference hint. Hints are derived data: a rebuild replaces
the rows rather than accumulating them, and **a hint is never a state** — no `curation_state` is
written and no `decisions` row is recorded.

An explicit `--candidate-id` that cannot be normalized is refused and writes nothing; an `--all`
run skips such a candidate with a `SKIPPED: <id>: <reason>` line (a batch that can normalize nothing
fails instead). `normalize` and `hints` only apply while a candidate is `new`: a decided candidate
is history, not a work in progress. See `docs/program/W1_4_NORMALIZATION_HINTS.md`.

## Review a candidate and record the curation decision (W1.5)

```bash
python3 scripts/garden_review.py queue      --dir data/store                        # the unreviewed queue, newest first
python3 scripts/garden_review.py show       --dir data/store --candidate-id cand-2026-09-13-0001
python3 scripts/garden_review.py accept     --dir data/store --candidate-id cand-2026-09-13-0001 --reason 'wanted and pursuable'
python3 scripts/garden_review.py hold       --dir data/store --candidate-id cand-... --reason 'defer until attribution checked'
python3 scripts/garden_review.py reject     --dir data/store --candidate-id cand-... --reason 'not wanted in the Garden'
python3 scripts/garden_review.py duplicate  --dir data/store --candidate-id cand-... --reason 'already represented by cand-2026-09-13-0002'
python3 scripts/garden_review.py reopen     --dir data/store --candidate-id cand-... --reason 'new information arrived'
python3 scripts/garden_review.py audit      --dir data/store [--candidate-id cand-...]   # the append-only decision log
python3 scripts/check_garden_review.py                                 # the W1.5 acceptance + evidence run
```

`queue` prints the unreviewed queue (`curation_state = 'new'`) newest first, rendering the capture
verbatim (marked `asserted`), the normalized proposal (marked `derived (deterministic normalization
of the capture)`), the normalization notes (marked `asserted`), and the duplicate hints (marked
`machine-inferred (a hint is evidence, never a decision)`). `show` renders any one candidate with
its full audit history; `audit` prints the append-only decision log.

Each of `accept / hold / reject / duplicate / reopen` is one **operator** curation decision. It must
have `--reason`, moves the candidate along a legal T-C1…T-C12 transition, and appends the audit row(s)
in the **same transaction** as the state change. Acceptance deterministically promotes
`candidate_only → eligible` (**T-P1**, authority `system` — eligibility means "wanted", never
"true"). A withdrawn acceptance (`accept` then `reject`/`duplicate` — **T-C8**/**T-C9**) fires
**T-P7** `eligible → candidate_only`, so no record is ever left eligible while its curation is
hold/rejected/duplicate. **No curation action writes research state** — it stays `not_started`. Every
decision records actor, timestamp, from, to, transition_id and reason; a refused decision (an illegal
transition, a missing candidate, or an empty `--reason`) writes nothing at all. `--actor` defaults to
`operator`. See `docs/program/W1_5_CURATION_SURFACE.md`.

## Run the whole W1 loop end to end (W1.6, the Gate B pack)

```bash
python3 scripts/check_garden_e2e.py                                # the W1.6 acceptance + Gate B evidence run
```

This is the wave gate's reproducible artifact. From a clean clone, one command (stdlib only — no
Playwright, no pre-seeded store, no browser) drives the **whole loop** through the real CLIs inside
a throwaway temp dir: a messy submission batch (a literal `_` placeholder-glyph row and a curly
apostrophe row read **verbatim from `quotes.csv`**, plus a wrong author, leading/trailing
whitespace, a missing citation, a near-duplicate text pair, and two unrelated rows sharing the
generic `Oral Tradition` label) → `submit` (W1.3) → `normalize --all` + `hints --all` (W1.4) →
`accept/hold/reject/duplicate/reopen` with the full `accept → reject` reversal (W1.5). It asserts —
96 checks, exiting 0 with `RESULT: PASS` / non-zero with `RESULT: FAIL` and one `FAIL:` line per
broken check — that every capture is **byte-identical** to the submitted text after every stage,
that provenance (method, timestamp, wrong author, whitespace, a missing citation's `none`
sentinel) survives on the capture, that normalize + hints never touch the `[captures]` section and
write no decision row, that a hint is never a state, that the generic `Oral Tradition` pair
produces **no** reference hint (the W1.4 false-positive fix), that every decision is audited and
the `decisions` log is append-only, that the reversal (`['T-C1','T-P1','T-C8','T-P7']`) strands no
dimension, and that **no curation action implies verification** (`research_state` stays
`not_started` throughout). It also re-runs `validate_quotes.py`, hashes both CSVs before/after
(byte-identical), and proves the store export (`garden.export/1`) round-trips. Nothing is written
outside the temp dir. See `docs/program/W1_6_E2E_TEST_PACK.md` and the Gate B packet
`docs/program/W1_6_GATE_B_PACKET.md`.

## Record and query the `unverifiable` side-car ledger (D3)

Decision D3 represents a record proven `unverifiable` in a **side-car ledger keyed by legacy
row id** (a `legacy_verification` table in the store), so it is no longer indistinguishable
from a never-checked row. Issue #5 / Garden id 30 is the seeded live instance.

```bash
python3 scripts/garden_ledger.py mark   --dir data/store --row 30 --transition T-R6 \
    --reason "why" [--evidence-ref REF] [--actor NAME]     # mark a legacy row unverifiable
python3 scripts/garden_ledger.py reopen --dir data/store --row 30 --reason "why"   # T-R12 reversal
python3 scripts/garden_ledger.py list   --dir data/store                          # read-only
python3 scripts/check_garden_ledger.py                    # the D3 acceptance + evidence run (45 checks)
```

`mark`/`reopen` each write their `research` audit row in the same transaction and refuse a
bad input before writing anything. The ledger is the `[legacy_verification]` export section,
so it round-trips with the store and diffs in git; the mirror is committed at
`data/store/garden.export.txt`. See `docs/program/D3_UNVERIFIABLE_LEDGER.md`.

## Seed and verify the D4 legacy batch capture

Decision D4 gives the 324 legacy `quotes.csv` rows **ONE batch capture** for the 2026-09-11
rehabilitation import (`cap-2026-09-11-legacy-batch`), explicitly marked `legacy-import` and
explicitly noting that encounter context is unknown. Membership links every legacy row id to
that single capture — no per-row captures, no store candidates.

```bash
python3 scripts/garden_legacy_batch.py seed   --dir data/store   # create capture + 324 membership rows
python3 scripts/garden_legacy_batch.py show   --dir data/store   # summary
python3 scripts/garden_legacy_batch.py verify --dir data/store   # membership == quotes.csv; archive digests match
python3 scripts/check_garden_legacy_batch.py                     # the D4 acceptance + evidence run
```

`seed` is idempotent for the same id set and refuses a conflicting capture or membership.
`quotes.csv` / `sources.csv` are never written. See `docs/program/D4_LEGACY_BATCH_CAPTURE.md`.

## Manage store lifecycle: bootstrap, freshness status, and sync (U0.1)

The machine-local SQLite database (`garden.sqlite3`) and the committed text mirror
(`garden.export.txt`) are managed via deterministic lifecycle commands:

```bash
python3 scripts/garden_store.py bootstrap --dir data/store   # hydrate local SQLite from committed mirror
python3 scripts/garden_store.py status    --dir data/store   # report freshness (CURRENT/STALE/MISSING_DB/MISSING_MIRROR)
python3 scripts/garden_store.py sync      --dir data/store   # atomically refresh committed mirror from store
python3 scripts/check_garden_lifecycle.py                    # acceptance suite (42 checks)
```

Lifecycle semantics and invariants:

1. **Bootstrap / hydrate**: On a fresh clone or whenever local SQLite is absent, `bootstrap`
   reconstructs the local SQLite database from `garden.export.txt`. If SQLite and mirror both
   exist and match, it is a no-op returning `CURRENT`. If they diverge, `bootstrap` refuses
   to guess or clobber either side.
2. **Freshness status**: Reports `CURRENT` (store matches mirror), `STALE` (store and mirror
   differ), `MISSING_DB` (SQLite file absent), or `MISSING_MIRROR` (export file absent).
3. **Mutation invariant**: All operator-facing mutating commands (`garden_submit.py`,
   `garden_normalize.py`, `garden_review.py`, `garden_ledger.py`, `garden_legacy_batch.py`)
   automatically call `sync_mirror()` on success. A successful command never leaves a silently
   stale mirror. If an un-synced mutation occurs, `status` detects `STALE`.
4. **Divergence safety and recovery**: If `status` reports `STALE`, the operator can run
   `garden_store.py sync --dir DIR` to refresh the mirror from the local store, or delete
   `garden.sqlite3` and run `bootstrap` to revert local state from the committed mirror.

## Run the browser locally

```
python3 -m http.server 8000
```

Open `http://localhost:8000/browser/index.html`. See `docs/architecture/QUOTE_BROWSER.md`.

## Smoke-test the browser

```
python3 -m pip install -r requirements-dev.txt      # Playwright (test-only dependency)
python3 -m playwright install chromium
python3 scripts/smoke_quote_browser.py
```

Drives the real page in headless Chromium against a throwaway server rooted at the repo root,
then exits 0 with `RESULT: PASS` / non-zero with `RESULT: FAIL` and one `FAIL:` line per broken
check. It asserts: the two CSVs are served byte-identical at the paths the page fetches (the
repo-root layout contract the Pages deploy depends on), the header/card/table counts equal the row
count parsed out of `quotes.csv`, search narrows the rows and sorting orders them, each of the six
filter dropdowns offers exactly the values in the CSV and selects down to the rows Python counts,
the "Issues only" toggle drops exactly the rows with no issues, a filter+search+sort combination
is counted and ordered correctly, a no-match combination renders "No matching quotes." in both
views (the table's empty-state row and a card-view empty-state message carrying the identical
text), the copy button puts the card's own text on the clipboard, the page lays out
without horizontal overflow at 320/375/768px in both card and table view, and there are no console
errors, page errors, or failed requests. Pass `--base-url http://127.0.0.1:8000` to test a server
you already have running. No expected number is hard-coded — every count is recomputed from the
CSVs, and checks that would otherwise pass vacuously (a search term or filter value that no longer
narrows anything, a toggle that drops nothing) fail loudly instead.

A green run prints 33 `PASS:` lines. Sixteen negative controls are recorded — seven in
`GARDEN_BROWSER_SMOKE_HANDOFF.md`, seven in `GARDEN_FILTER_SMOKE_COVERAGE_HANDOFF.md`, two in
`GARDEN_CARD_EMPTY_STATE_HANDOFF.md`.

CI runs the same script on every PR and on every push to `main`
(`.github/workflows/browser-smoke.yml`), together with the three validators, the Pages
deploy-contract guard, and the seven corpus-program acceptance suites below.

## GitHub Pages (static site)

Published from the repo root by `.github/workflows/pages.yml` on every push to `main` (and by
manual `workflow_dispatch`, main only — the job is guarded with
`if: github.ref == 'refs/heads/main'` so a manual run from a branch cannot overwrite the live
site). Actions-based Pages: `configure-pages` → `upload-pages-artifact` → `deploy-pages`.

URLs once deployed:

- site root (a redirect shim in the repo-root `index.html`) —
  `https://mschwar.github.io/Garden-of-Wisdom/`
- the app — `https://mschwar.github.io/Garden-of-Wisdom/browser/index.html`
- the data the app fetches at runtime — `…/quotes.csv`, `…/sources.csv`

**Precondition that CI assumes but cannot create.** The repo's Pages site must exist with
`build_type: workflow` (Settings → Pages → Source = **GitHub Actions**, not "Deploy from a
branch"). `actions/configure-pages`'s `enablement: true` requires an admin PAT — the default
`GITHUB_TOKEN` cannot do it — so it was enabled once, out of band:

```
gh api repos/mschwar/Garden-of-Wisdom/pages | jq .build_type     # expect "workflow"
gh api -X POST repos/mschwar/Garden-of-Wisdom/pages -f build_type=workflow   # only if 404
```

If that setting is missing or gets flipped, `pages.yml` **fails** rather than mispublishing —
it does not silently publish a wrong thing.

**Hard contract — Pages must stay rooted at the repo root.** `browser/index.html` fetches
`../quotes.csv` and `../sources.csv`, both of which live at the repo root, so the published
site has to be the whole repo (`path: '.'` in the workflow). If anyone repoints the artifact
at `browser/` (or flips Pages back to "Deploy from a branch" with `/docs` or `/browser` as
the folder), the page still loads but renders 0 quotes because both fetches 404. The root
`index.html` is only a redirect shim; it is not the app.

**What actually gets published.** The whole repo root — including `docs/`, `bootstrap/`,
`exports/`, and the frozen `data/archive/` originals — because the app's
`../quotes.csv` / `../sources.csv` fetches require the root layout. All of it is already
public on GitHub, so this adds no exposure. `actions/upload-pages-artifact` always drops
`.git` and `.github` and — **from v4 on** — all top-level dotfiles
(`include-hidden-files: false` makes the action add `--exclude=.[^/]*` to its `tar`). **v3
did not**: it published `./.gitignore`, which is what issue #23 was filed about, so the
action's major version is part of the contract and
`scripts/check_pages_contract.py` fails the pull request if it drops below v4. An
Actions-deployed artifact is served as-is and is never run through Jekyll, so a committed
`.nojekyll` would make no difference and is not needed.

Verify a deploy (automated checklist):

```bash
python3 scripts/check_live_pages.py                                      # live acceptance check against default URL
python3 scripts/check_live_pages.py --base-url https://...               # custom base URL
python3 scripts/check_live_pages.py --self-test                         # offline negative controls & self-tests
```

Exits 0 with `RESULT: PASS` / non-zero with `RESULT: FAIL` and one `FAIL:` line per broken
check (**9** checks: 4 x 200 probes, 3 x 404 probes, and byte-identical sha256 comparison for
both `quotes.csv` and `sources.csv`). Stdlib only; downloads and compares both CSVs against the
local repository bytes. It replaces the manual curl + shasum commands and eliminates transcription
risk (issue #41).

Under the hood, it performs the four 200 probes:

```
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/browser/index.html
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/quotes.csv
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/sources.csv
```

and these three must all be **404** (they cover the ways a deploy can be wrong without
failing: a published top-level dotfile — the #23 class — an unexcluded `.git` directory, and
an unexcluded `.github` directory):

```
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/.gitignore
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/.git/config
curl -s -o /dev/null -w '%{http_code}\n' https://mschwar.github.io/Garden-of-Wisdom/.github/workflows/pages.yml
```

Checking only `/.git/config` is what let #23 ship: the artifact can be rooted correctly and
still publish dotfiles, so probe all three. The artifact itself can be listed without a deploy —
`gh api repos/mschwar/Garden-of-Wisdom/actions/artifacts?per_page=5` to find the newest
`github-pages` artifact, then download its zip and `tar -tf artifact.tar` (no member should
start with `./.` — `tar -tf artifact.tar | grep -E '/\.'` must be empty, at any depth).

To watch a deploy instead: `gh run list --workflow pages.yml --limit 3` then
`gh run watch <id>`.

## Guard the Pages deploy contract

```
python3 scripts/check_pages_contract.py
```

Exits 0 with `RESULT: PASS` / non-zero with `RESULT: FAIL` and one `FAIL:` line per broken
check (**16** checks: 15 contract checks plus a guard on the check count, so deleting a
check fails the run). Stdlib only, no network, writes nothing.

The live page fetches `../quotes.csv` and `../sources.csv`, so a Pages artifact rooted
anywhere else loads and silently renders **0 quotes**, and a regression in the upload
action's hidden-file exclusion silently publishes tracked dotfiles. Neither failure makes
the deploy job fail, and no other test in this repo can see the workflow files at all — the
contract lived only in prose until this guard. It reads `.github/workflows/pages.yml` and
asserts the parts a repo change can break: the workflow still parses into the shape the
guard understands (a single `steps:` list whose entries all sit at one indent — anything else
FAILs and asks for a re-derive rather than passing), `path:` is `'.'`, exactly one step uses
the upload action and it runs **before** the deploy step, that action's major is
**verified** (`VERIFIED_UPLOAD_MAJORS` — v4/v5 exclude top-level dotfiles, v3 does not; `@vN.M.P`
tags are read as major N, and a commit pin FAILs because it cannot be checked against the
table), `include-hidden-files` is not switched on, the artifact name is still `github-pages`,
the `refs/heads/main` guard is present, the `pages` concurrency group never cancels an
in-flight deploy, `pages: write` + `id-token: write` are granted — and then that
`browser/app.js` still fetches those two `../` paths (with `//` comments stripped, so keeping
the old path in a comment does not count), that both CSVs are at the repo root, and that the
root `index.html` shim still **redirects** to `browser/index.html` (its meta-refresh or
`location.replace`, not merely the canonical link).

Two checks exist because they were caught failing to do their job, both by a control rather
than by reading the code: the environment URL is compared **exactly** (a `page_url` →
`page_url_unused` mutation stayed green against a substring test), and the shim is checked at
the level of the redirect mechanism (a substring test was satisfied by the shim's
`<link rel="canonical">` even after the redirect was repointed).

CI runs it (`browser-smoke.yml`, step "Guard the Pages deploy contract"), so a pull request
that breaks the contract is red before it can deploy. It is a *config* guard: it proves the
workflow still asks for a rooted artifact from an action version that excludes hidden files,
not what a given deployment published — that is what the live probes above are for. It was
added after issue #23; its **28** negative controls — one per check, the two shape guards, the
count guard, and the regression cases that must stay green — were recorded in
`GARDEN_PAGES_CONTRACT_GUARD_HANDOFF.md`, and four of them now live in the committed control
table that `scripts/run_negative_controls.py` re-applies on every CI run (see
"Machine-check the checkers' negative controls" below; that script is where the whole control
table for every checker now lives, so it no longer has to be taken on a handoff's word).


## Machine-check the checkers' negative controls

```
python3 scripts/run_negative_controls.py            # every control of every checker (CI runs this)
python3 scripts/run_negative_controls.py --check     # anchors only, no checker is run (fast)
python3 scripts/run_negative_controls.py --list      # print the control table
python3 scripts/run_negative_controls.py --checker scripts/check_pages_contract.py
```

Every checker in this repo is supposed to come with *negative controls*: one mutation per
guard, which must turn the run red with **that guard's own** `FAIL:` line. Until this script
those tables lived only in prose (`GARDEN_*_HANDOFF.md`), produced by a throwaway harness in
`/tmp` that was deleted when the unit ended — so the evidence was not independently
verifiable, and a *vacuous* check was undetectable: the Pages guard's `EXPECTED_CHECKS` fails
when a check is **deleted**, but gutting a check body to `return None` while keeping its
registration leaves the run green (foreign QA mutation `p36`).

`scripts/run_negative_controls.py` (stdlib only) copies the working tree to a throwaway
directory — never mutating it, and excluding `.git`/`.venv`/`__pycache__` — then, for each
control: asserts the control's anchor occurs **exactly once** in its target file, applies the
substitution, runs the checker **from inside the copy**, restores the file's pristine bytes,
and asserts the **first** `FAIL:` line is the one the control aimed at. It also runs each
checker unmutated first and refuses to report a control as fired against an already-red
baseline.

Verdicts that fail the run: `COVERAGE_GAP` (the mutation stayed green — the check has no
falsifier), `MASKED` (a different check refused first), `ROTTEN_ANCHOR` (the anchor no longer
occurs exactly once, so the table has drifted from the files), `FALSE_POSITIVE` (a
contract-preserving edit that must stay green went red), `CRASH`, `INCONSISTENT`, `TIMEOUT`.
Only `FIRED` passes a control that expects a `FAIL:` line. **This is what closes issue #43's
`p36` finding**: gutting a check body makes that check's control report `COVERAGE_GAP` instead
of hiding behind the count guard.

It also carries **its own controls** (the `harness self-tests`, run on every invocation): a
synthetic mini-repo exercises the five verdicts end to end, plus four table-hygiene guards (an
empty table, a checker with no controls, a deleted registration, and the rule that a narrowed
`--checker` selection is never checked against the whole-table count guard) — a harness that can
no longer detect a green mutation is the same defect one level up. `EXPECTED_SELF_TESTS` and
`EXPECTED_CONTROLS` are count guards: deleting either fails the run.

**Cost, measured** (macOS, warm): ~4 minutes, dominated by `validate_quotes.py` (~21s/run) and
`check_garden_e2e.py` (~22s/run); ~6.5–7 minutes in CI on a 2-core runner. `--checker` narrows a
local run; CI runs all of it, because the point is coverage, not a fast green, and the `smoke`
job's budget was raised from 15 to 30 minutes for exactly that reason (a table checked only for
rot would not be evidence). Two checker families are exercised here:
`scripts/smoke_quote_browser.py`'s controls need a real Chromium, so that checker declares
`requires=("playwright",)` and is reported **SKIPPED** (never PASS) where the browser is
missing — with `CI` set, or `--require-all`, a skip is an error rather than a quiet reduction
in coverage.

Known limits, so they are not mistaken for coverage: a control is a **single exact-string
substitution**, so a regression that needs a file deleted, renamed or a multi-file edit is
outside the table's vocabulary; and the table proves each *modelled* break is detected, never
that a guard is complete. As of 2026-09-18 it holds **60** controls over all **15** checkers,
including the five gap mutations issue #45 closed (`n4`, `r4`, `x3`, `l4`, `g4`), the ten
front-door controls `fd1`–`fd10` (U0.2) and `fd11`–`fd13` (U0.3). **Superseded numbers:** this line
read **44** (as of 2026-09-16) until U0.3 re-measured it — U0.2 had already moved the table
47 → 57 without updating this file, so 44 was two units stale, not one. Re-measure from the table
itself (`--list`) rather than trusting any count written in prose.
`docs/architecture/NEGATIVE_CONTROLS.md` has the design and the control-by-control record.


## Re-derive the canonical CSVs from the frozen originals

Only needed if you suspect the canonical `quotes.csv`/`sources.csv` at the repo root have
drifted from what the archived originals + documented transform would produce. This is
idempotent and always reads from `data/archive/2026-09-11/*.original.csv`, never from its own
output:

```
python3 scripts/rehabilitate_2026_09_11.py
```

Re-run `scripts/validate_quotes.py` afterward.

## Homepage-preview export (G4)

Regenerate and validate the versioned collection consumed by `bahai-homepage`
(do not live-read `quotes.csv` from that repo):

```
python3 scripts/export_homepage_preview.py
python3 scripts/validate_homepage_preview_export.py
```

Artifacts live under `exports/bahai-homepage-preview/v1/`. The exporter hard-fails
if an accepted donor’s `quote_text` has drifted from the verified snapshot in
`mapping.json`. See `GARDEN_HOMEPAGE_PREVIEW_EXPORT_HANDOFF.md`.

## Adding a new quote

1. Append a row to `quotes.csv` with all 10 columns filled in. Set `verification_status` to
   `unverified` unless you've actually checked it against a primary source.
2. If it cites a source already in `sources.csv`, set `source_id` accordingly; if not, either
   add a `sources.csv` row first or leave `source_id` blank (don't guess).
3. Run `python3 scripts/validate_quotes.py` and confirm `RESULT: PASS`.

## Recovery if an agent session dies mid-task

1. `git status`
2. Read `AGENTS.md`.
3. Read `docs/program/usability-closure/CURRENT.md` for the current gate and the one READY
   unit, then `docs/queue.md` for the active work unit.
4. Read the READY unit's document under `docs/program/usability-closure/workunits/` and the
   most recent handoff/checkpoint file at repo root.
5. Resume only the named active work unit — don't restart from memory or improvise scope.
6. Re-run the acceptance suites for the surface you touched (`scripts/validate_quotes.py` for
   data, `scripts/check_garden_*.py` for the corpus surfaces) before claiming anything is done.
