#!/usr/bin/env python3
"""Automated browser smoke test for the quote browser (`browser/index.html`).

Usage:
    python3 scripts/smoke_quote_browser.py
    python3 scripts/smoke_quote_browser.py --base-url http://127.0.0.1:8000

By default this starts its own static server rooted at the **repo root** (the layout the
GitHub Pages deploy uses) on an ephemeral port, drives the page in headless Chromium, and
then shuts the server down. Pass `--base-url` to test an already-running server instead.

What it asserts (all against expectations recomputed from `quotes.csv`/`sources.csv`,
never hard-coded counts):

  1. layout contract — `/browser/index.html`, `/quotes.csv`, `/sources.csv` all return 200,
     with the two CSVs byte-identical to the working tree;
  2. load — the header counts and the rendered card count equal the row count parsed out of
     `quotes.csv` by the same rule `browser/app.js` uses (and `SEARCH_TERM` is asserted to still
     match at least one row, so the search/sort checks can never pass vacuously);
  3. search — typing a term narrows the rendered set to exactly the rows whose
     text/author/source/tags contain it;
  4. filters — each of the six dropdowns offers exactly the values present in `quotes.csv`
     (plus "All"), and selecting a value narrows the rendered set to exactly the rows Python
     counts with the same predicate `browser/app.js` uses (exact match on the column; tag
     membership for `#filter-tag`);
  5. "Issues only" — checking `#filter-issues-only` narrows the set to exactly the rows whose
     `detectIssues()` is non-empty, every rendered card carries an issue badge, and the toggle
     is asserted to actually drop rows (so a toggle that stopped subtracting cannot pass);
  6. combined interaction — a dropdown value plus a search term plus a sort, asserted in table
     view (count and length ordering);
  7. empty result — a filter/search combination with no matches renders "No matching quotes."
     in **both** views: the table view's `td.empty-state` row and a `#results .empty-state`
     element in card view, with the two messages compared to each other; plus no cards;
  8. view switch — card view leaves no empty table container behind, table view renders one
     row per filtered quote, and clicking a sortable header flips `aria-sort`;
  9. copy — the per-card "Copy quote" button puts that card's quote text on the clipboard;
 10. layout — at 320/375/768px wide the document does not overflow horizontally, in both
     card and table view;
 11. zero console errors, zero page errors, zero failed requests.

Requires `playwright` plus its Chromium build:

    python3 -m pip install -r requirements-dev.txt
    python3 -m playwright install chromium

Exits 0 with `RESULT: PASS` when every check passes, non-zero with `RESULT: FAIL` and one
`FAIL:` line per broken check otherwise.
"""
from __future__ import annotations

import argparse
import csv
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
QUOTES_PATH = ROOT / "quotes.csv"
SOURCES_PATH = ROOT / "sources.csv"
APP_PATH = "/browser/index.html"

SEARCH_TERM = "Dhammapada"
# Widths the overflow check sweeps (phone / small phone / tablet), in CSS pixels.
VIEWPORT_WIDTHS = (320, 375, 768)
VIEWPORT_HEIGHT = 800
DESKTOP_WIDTH = 1280
DESKTOP_HEIGHT = 900

failures: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    failures.append(msg)


def warn(msg: str) -> None:
    print(f"WARN: {msg}")
    warnings.append(msg)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    """Parse a CSV the way `browser/app.js` parseCSV does.

    Keeps a data row only when it has the same field count as the header and at least one
    non-empty field — the app drops short/long rows and blank lines the same way, so the
    expected counts below are derived from the data rather than asserted from memory.
    """
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    out = []
    for row in rows[1:]:
        if len(row) != len(header) or not any(v != "" for v in row):
            continue
        out.append(dict(zip(header, row)))
    return out


def matches_search(row: dict[str, str], term: str) -> bool:
    """Mirror of `matchesSearch()` in `browser/app.js`."""
    haystack = " ".join(
        [row.get("quote_text", ""), row.get("author", ""), row.get("source_ref", ""), row.get("tags", "")]
    ).lower()
    return term.lower() in haystack


# The six filter dropdowns, as (quotes.csv column, page selector). Order matches the page.
FILTER_CONTROLS = (
    ("tradition", "#filter-tradition"),
    ("author", "#filter-author"),
    ("source_ref", "#filter-source"),
    ("tags", "#filter-tag"),
    ("item_type", "#filter-item-type"),
    ("verification_status", "#filter-verification"),
)
ISSUES_ONLY_SELECTOR = "#filter-issues-only"
EMPTY_STATE_TEXT = "No matching quotes."


def row_tags(row: dict[str, str]) -> set[str]:
    """Mirror of the tag parsing `browser/app.js` uses (split on comma, trim, drop blanks)."""
    return {t.strip() for t in (row.get("tags") or "").split(",") if t.strip()}


def detect_issues(row: dict[str, str]) -> list[str]:
    """Mirror of `detectIssues()` in `browser/app.js`."""
    issues = []
    if row.get("has_unresolved_glyph") == "true":
        issues.append("unresolved glyph")
    if not row.get("source_id"):
        issues.append("unresolved source link")
    if row.get("item_type") == "unknown":
        issues.append("item type unknown")
    if row.get("verification_status") != "verified":
        issues.append("unverified")
    return issues


def matches_value(row: dict[str, str], column: str, value: str) -> bool:
    """Mirror of one dropdown's predicate in `applyFilters()`: exact match, except tags."""
    if column == "tags":
        return value in row_tags(row)
    return row.get(column, "") == value


def values_for(rows: list[dict[str, str]], column: str) -> list[str]:
    """The option set the page builds for a dropdown (the column's distinct non-empty values)."""
    if column == "tags":
        seen: set[str] = set()
        for row in rows:
            seen |= row_tags(row)
        return sorted(seen)
    return sorted({row.get(column, "") for row in rows if row.get(column, "")})


def count_matching(
    rows: list[dict[str, str]],
    column: str | None = None,
    value: str | None = None,
    term: str = "",
    issues_only: bool = False,
) -> int:
    """Count the rows `browser/app.js` would show for this search/filter/toggle combination."""
    total = 0
    for row in rows:
        if term and not matches_search(row, term):
            continue
        if column is not None and value is not None and not matches_value(row, column, value):
            continue
        if issues_only and not detect_issues(row):
            continue
        total += 1
    return total


def candidate_search_terms(rows: list[dict[str, str]]) -> list[str]:
    """Search terms tried when building filter+search combinations, most common tag first.

    Data-derived on purpose: a term is only used if it still matches rows, and every expected
    count below is recomputed from these terms, so this cannot go stale silently.
    """
    counts: dict[str, int] = {}
    for row in rows:
        for tag in row_tags(row):
            counts[tag] = counts.get(tag, 0) + 1
    ranked = [t for t, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
    terms = [SEARCH_TERM]
    terms += [t for t in ranked if t not in terms]
    return terms


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):  # keep the smoke output readable
        pass


class Server:
    """Throwaway static server rooted at the repo root, on an ephemeral port."""

    def __init__(self, directory: Path) -> None:
        handler = functools.partial(QuietHandler, directory=str(directory))
        self._httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]

    def __enter__(self) -> "Server":
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


def check_static_layout(base_url: str) -> None:
    """Queue item: the Pages deploy must stay rooted at the repo root."""
    for path, local in ((APP_PATH, None), ("/quotes.csv", QUOTES_PATH), ("/sources.csv", SOURCES_PATH)):
        try:
            with urlopen(f"{base_url}{path}") as resp:
                status = resp.status
                body = resp.read()
        except Exception as exc:  # noqa: BLE001 - report any failure as a check failure
            fail(f"GET {path} raised {exc!r}")
            continue
        if status != 200:
            fail(f"GET {path} returned {status}, expected 200")
            continue
        if local is not None:
            expected = local.read_bytes()
            if body != expected:
                fail(f"GET {path} served {len(body)} bytes, not byte-identical to {local.name} ({len(expected)} bytes)")
                continue
        ok(f"GET {path} -> 200{' (byte-identical)' if local is not None else ''}")


_METRICS_JS = """() => ({
  docScroll: document.documentElement.scrollWidth,
  docClient: document.documentElement.clientWidth,
  bodyScroll: document.body.scrollWidth,
  controlsScroll: document.getElementById('controls').scrollWidth,
  controlsClient: document.getElementById('controls').clientWidth,
  widest: (() => {
    // Only report elements whose overflow is NOT contained by a scrolling ancestor
    // (e.g. #table-wrap legitimately clips the wide table).
    const contained = (el) => {
      for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
        if (getComputedStyle(p).overflowX !== 'visible') return true;
      }
      return false;
    };
    let worst = null;
    for (const el of document.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (r.right > window.innerWidth + 1 && !contained(el)) {
        if (!worst || r.right > worst.right) {
          const cls = el.className && typeof el.className === 'string'
            ? '.' + el.className.trim().split(/\\s+/).join('.') : '';
          worst = {right: Math.round(r.right), tag: el.tagName + (el.id ? '#' + el.id : '') + cls};
        }
      }
    }
    return worst;
  })(),
})"""


def wait_for_filtered_count(page, expected: int, context: str, timeout: int = 15000) -> bool:
    """Wait until the page reports `expected` shown quotes; report a clean FAIL on timeout.

    Reporting rather than raising keeps a broken interaction (e.g. a filter that stopped
    filtering) as one `FAIL:` line with RESULT: FAIL, instead of a traceback.
    """
    try:
        page.wait_for_function(
            "expected => Number(document.getElementById('filtered-count').textContent) === expected",
            arg=expected,
            timeout=timeout,
        )
        return True
    except Exception:
        fail(f"{context}: page never showed {expected} quotes within {timeout}ms (filtered-count={page.text_content('#filtered-count')!r})")
        return False


def reset_filters(page, expected_total: int) -> None:
    """Return the page to the unfiltered card view, then confirm all rows are back."""
    page.select_option("#view-mode", "cards")
    for _, selector in FILTER_CONTROLS:
        page.select_option(selector, "")
    if page.is_checked(ISSUES_ONLY_SELECTOR):
        page.uncheck(ISSUES_ONLY_SELECTOR)
    page.fill("#search", "")
    wait_for_filtered_count(page, expected_total, "resetting search/filters")


def check_filter_options(page, expected_quotes: list[dict[str, str]]) -> None:
    """Every dropdown must offer exactly the values present in quotes.csv, plus "All".

    A dropdown that lost an option (or gained a stale one) is invisible to a count-only check
    when the value happens to be unselected, so this asserts the option sets themselves.
    """
    problems = []
    for column, selector in FILTER_CONTROLS:
        expected = values_for(expected_quotes, column)
        actual = sorted(page.eval_on_selector_all(f"{selector} option", "els => els.map(e => e.value)"))
        if actual and actual[0] == "":
            actual = actual[1:]
        if actual != expected:
            missing = sorted(set(expected) - set(actual))[:5]
            extra = sorted(set(actual) - set(expected))[:5]
            problems.append(f"{selector} missing={missing} unexpected={extra}")
        first = page.eval_on_selector(f"{selector} option", "el => el.value")
        if first != "":
            problems.append(f"{selector} first option value is {first!r}, expected '' (All)")
    if problems:
        fail("filter dropdowns do not offer the values in quotes.csv: " + "; ".join(problems))
    else:
        ok(
            f"all {len(FILTER_CONTROLS)} filter dropdowns offer exactly the quotes.csv values "
            "plus an 'All' first option"
        )


def check_filter_counts(page, expected_quotes: list[dict[str, str]]) -> None:
    """Select one narrowing value per dropdown and assert the resulting count and cards."""
    total = len(expected_quotes)
    for column, selector in FILTER_CONTROLS:
        value, expected = next(
            (
                (v, count_matching(expected_quotes, column=column, value=v))
                for v in values_for(expected_quotes, column)
                if 0 < count_matching(expected_quotes, column=column, value=v) < total
            ),
            (None, 0),
        )
        if value is None:
            # Every value matches all rows or none: selecting one would prove nothing.
            fail(
                f"{selector}: no quotes.csv value narrows the set (each matches all {total} rows "
                "or zero) — the filter check would be vacuous"
            )
            continue
        try:
            page.select_option(selector, value)
        except Exception as exc:  # noqa: BLE001 - a missing option is a check failure, not a crash
            fail(f"{selector}: the dropdown does not offer the value {value!r} from quotes.csv ({exc.__class__.__name__})")
            continue
        if not wait_for_filtered_count(page, expected, f"{selector} = {value!r}"):
            continue
        cards = page.locator("#results .card").count()
        if cards != expected:
            fail(f"{selector} = {value!r} rendered {cards} cards, expected {expected}")
            continue
        ok(f"{selector} = {value!r} narrows to {cards} card{'s' if cards != 1 else ''}, matching quotes.csv")
        page.select_option(selector, "")


def check_issues_only(page, expected_quotes: list[dict[str, str]]) -> None:
    """The toggle must show exactly the rows with at least one detected issue, and drop some."""
    total = len(expected_quotes)
    expected = count_matching(expected_quotes, issues_only=True)
    if expected == 0 or expected == total:
        # Either way a broken toggle would still satisfy the count assertion, so refuse to pass.
        fail(
            f"'Issues only' would be vacuous: {expected} of {total} rows carry an issue in "
            "quotes.csv — the check cannot distinguish a working toggle from a broken one"
        )
        return
    page.check(ISSUES_ONLY_SELECTOR)
    if not wait_for_filtered_count(page, expected, "'Issues only' checked"):
        return
    cards = page.locator("#results .card").count()
    if cards != expected:
        fail(f"'Issues only' rendered {cards} cards, expected {expected}")
        return
    with_badge = page.evaluate(
        "() => Array.from(document.querySelectorAll('#results .card'))"
        ".filter(c => c.querySelector('.badge.issue')).length"
    )
    if with_badge != expected:
        fail(f"'Issues only' rendered {cards} cards but only {with_badge} carry an issue badge")
        return
    ok(f"'Issues only' narrows to {cards} cards (dropping {total - expected}), every one badged")


def check_combined_interaction(page, expected_quotes: list[dict[str, str]]) -> None:
    """A dropdown value + a search term + a sort, asserted together in table view."""
    total = len(expected_quotes)
    terms = candidate_search_terms(expected_quotes)
    for column, selector in FILTER_CONTROLS:
        for value in values_for(expected_quotes, column):
            base = count_matching(expected_quotes, column=column, value=value)
            if not 0 < base < total:
                continue
            for term in terms:
                if count_matching(expected_quotes, term=term) == 0:
                    continue
                expected = count_matching(expected_quotes, column=column, value=value, term=term)
                if not 0 < expected < base:
                    continue
                page.select_option(selector, value)
                page.fill("#search", term)
                page.select_option("#view-mode", "table")
                page.select_option("#sort-field", "length")
                # Direction is independent of the sort field, so set it explicitly from the
                # button's own label rather than assuming the previous check left it ascending.
                if "Descending" not in (page.text_content("#sort-dir") or ""):
                    page.click("#sort-dir")
                if not wait_for_filtered_count(
                    page, expected, f"combined {selector} = {value!r} + search {term!r} + sort Length desc"
                ):
                    return
                lens = page.eval_on_selector_all(
                    "#quote-table tbody tr .td-len", "els => els.map(e => Number(e.textContent))"
                )
                if len(lens) != expected:
                    fail(
                        f"combined filter+search rendered {len(lens)} table rows, expected {expected} "
                        f"({selector} = {value!r}, search {term!r})"
                    )
                    return
                if lens != sorted(lens, reverse=True):
                    fail(
                        f"combined filter+search+sort left Length descending order broken "
                        f"({selector} = {value!r}, search {term!r}): {lens[:5]}.."
                    )
                    return
                ok(
                    f"combined {selector} = {value!r} + search {term!r} + Length desc renders "
                    f"{len(lens)} rows in order, matching quotes.csv"
                )
                return
    fail(
        "no filter + search combination narrows the set to a non-empty subset of the filtered "
        "set — the combined-interaction check would be vacuous"
    )


def check_empty_state(page, expected_quotes: list[dict[str, str]]) -> None:
    """A filter/search combination with no matches must explain itself in both views.

    Card view used to render nothing at all at zero matches (issue #17): a blank area under a
    header reading "0 shown", where table view showed its empty-state row. Both views must now
    carry the *same* message, so the two texts are compared with each other rather than each
    being checked against a copy of the string — a one-sided edit cannot pass here.
    """
    terms = candidate_search_terms(expected_quotes)
    for column, selector in FILTER_CONTROLS:
        for value in values_for(expected_quotes, column):
            if count_matching(expected_quotes, column=column, value=value) == 0:
                continue
            for term in terms:
                if count_matching(expected_quotes, term=term) == 0:
                    continue
                if count_matching(expected_quotes, column=column, value=value, term=term) != 0:
                    continue
                page.select_option(selector, value)
                page.fill("#search", term)
                page.select_option("#view-mode", "table")
                context = f"empty result ({selector} = {value!r} + search {term!r})"
                if not wait_for_filtered_count(page, 0, context):
                    return
                cards = page.locator("#results .card").count()
                if cards != 0:
                    fail(f"{context}: card view still rendered {cards} cards at zero matches")
                    return
                empty = page.locator("#quote-table tbody td.empty-state")
                if empty.count() != 1:
                    fail(f"{context}: table view rendered {empty.count()} empty-state cells, expected 1")
                    return
                table_text = (empty.first.text_content() or "").strip()
                if EMPTY_STATE_TEXT not in table_text:
                    fail(f"{context}: empty-state text was {table_text!r}, expected it to contain {EMPTY_STATE_TEXT!r}")
                    return
                ok(f"{context} renders the table's empty-state row {table_text!r}")
                # Card view must explain the same empty result, with the identical message.
                page.select_option("#view-mode", "cards")
                page.wait_for_timeout(150)
                card_empty = page.locator("#results .empty-state")
                if card_empty.count() != 1:
                    fail(
                        f"{context}: card view rendered {card_empty.count()} empty-state elements, "
                        "expected 1 (issue #17: card view must not leave the result area blank)"
                    )
                    return
                card_text = (card_empty.first.text_content() or "").strip()
                if card_text != table_text:
                    fail(
                        f"{context}: card view says {card_text!r}, table view says {table_text!r} — "
                        "the two views share one message and must not drift"
                    )
                    return
                ok(f"{context} renders the same empty state in card view {card_text!r}")
                return
    fail(
        "no filter + search combination yields zero matches — the empty-state check would be "
        "vacuous; add a candidate search term the data can be excluded by"
    )


def check_viewport_overflow(browser, base_url: str, expected_count: int, widths: tuple[int, ...]) -> None:
    """No horizontal overflow at the given viewport widths, in both card and table view."""
    for width_px in widths:
        page = browser.new_page(viewport={"width": width_px, "height": VIEWPORT_HEIGHT})
        try:
            page.goto(f"{base_url}{APP_PATH}", wait_until="load")
            if not wait_for_filtered_count(page, expected_count, f"load at {width_px}px"):
                continue
            for view in ("cards", "table"):
                page.select_option("#view-mode", view)
                page.wait_for_timeout(150)
                metrics = page.evaluate(_METRICS_JS)
                width = metrics["docClient"]
                if metrics["docScroll"] > width or metrics["bodyScroll"] > width:
                    worst = metrics["widest"]
                    where = f" widest overflowing element: {worst}" if worst else ""
                    fail(
                        f"{view} view overflows horizontally at {width_px}px: "
                        f"document scrollWidth={metrics['docScroll']} > clientWidth={width}{where}"
                    )
                elif metrics["controlsScroll"] > metrics["controlsClient"] + 1:
                    fail(
                        f"{view} view: #controls content is clipped at {width_px}px "
                        f"(scrollWidth={metrics['controlsScroll']} > clientWidth={metrics['controlsClient']})"
                    )
                else:
                    ok(f"no horizontal overflow at {width_px}px ({view} view)")
        finally:
            page.close()


def run(base_url: str, expected_quotes: list[dict[str, str]]) -> None:
    from playwright.sync_api import sync_playwright

    check_static_layout(base_url)

    expected_total = len(expected_quotes)
    expected_search = sum(1 for row in expected_quotes if matches_search(row, SEARCH_TERM))
    if expected_search == 0:
        # Fail before the browser starts: with zero matches, the search/sort/table checks
        # would all pass trivially on an empty result set, silently vacating coverage.
        fail(
            f"SEARCH_TERM {SEARCH_TERM!r} matches no row in quotes.csv — the search, sort and "
            "table checks would pass vacuously; update SEARCH_TERM to a term the data still contains"
        )
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": DESKTOP_WIDTH, "height": DESKTOP_HEIGHT},
            permissions=["clipboard-read", "clipboard-write"],
        )
        console_errors: list[str] = []
        page_errors: list[str] = []
        failed_requests: list[str] = []
        context.on("page", lambda p: p.on("pageerror", lambda exc: page_errors.append(str(exc))))
        page = context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url}: {req.failure}"))

        page.goto(f"{base_url}{APP_PATH}", wait_until="load")
        if not wait_for_filtered_count(page, expected_total, "initial load"):
            body = page.text_content("#results") or ""
            fail(f"initial load: #results text was {body[:200]!r}")
            browser.close()
            return
        ok(f"initial load renders all {expected_total} quotes with no error state")

        total_shown = int(page.text_content("#total-count") or "0")
        filtered_shown = int(page.text_content("#filtered-count") or "0")
        if total_shown != expected_total or filtered_shown != expected_total:
            fail(
                f"header counts say {total_shown} total / {filtered_shown} shown, "
                f"quotes.csv parses to {expected_total}"
            )
        else:
            ok(f"header renders {total_shown} total / {filtered_shown} shown, matching quotes.csv")

        card_count = page.locator("#results .card").count()
        if card_count != expected_total:
            fail(f"card view rendered {card_count} cards, expected {expected_total}")
        else:
            ok(f"card view renders {card_count} cards")

        # Card view must not leave the (bordered, scrollable) table container behind: an
        # empty #table-wrap collapses to a stray 2px line under the last card.
        stray = page.evaluate(
            """() => {
                const w = document.getElementById('table-wrap');
                const r = w.getBoundingClientRect();
                return {visible: r.height > 0 && r.width > 0, height: Math.round(r.height)};
            }"""
        )
        if stray["visible"]:
            fail(f"card view leaves an empty table container on the page ({stray['height']}px tall)")
        else:
            ok("card view hides the table container")

        # Search narrows the set to exactly the rows containing the term.
        page.fill("#search", SEARCH_TERM)
        if not wait_for_filtered_count(page, expected_search, f"search {SEARCH_TERM!r}"):
            browser.close()
            return
        searched = page.locator("#results .card").count()
        if searched != expected_search:
            fail(f"search {SEARCH_TERM!r} rendered {searched} cards, expected {expected_search}")
        else:
            ok(f"search {SEARCH_TERM!r} narrows to {searched} cards, matching quotes.csv")

        # Sort direction flip reorders the result set (checked in table view, where the
        # sorted column's values are readable, so we assert the order itself and not just
        # that the first row changed — a tie across the whole set is legitimate).
        page.select_option("#view-mode", "table")
        page.wait_for_timeout(150)
        page.select_option("#sort-field", "length")
        page.wait_for_timeout(150)
        ascending = page.eval_on_selector_all("#quote-table tbody tr .td-len", "els => els.map(e => Number(e.textContent))")
        page.click("#sort-dir")
        page.wait_for_timeout(150)
        descending = page.eval_on_selector_all("#quote-table tbody tr .td-len", "els => els.map(e => Number(e.textContent))")
        if ascending != sorted(ascending) or descending != sorted(descending, reverse=True):
            fail("sorting by Length does not order the rendered rows (ascending or descending)")
        else:
            ok(
                f"sort by Length orders {len(ascending)} rows ascending then descending "
                f"({ascending[0]}..{ascending[-1]} / {descending[0]}..{descending[-1]})"
            )

        # Table view renders one row per filtered quote and sorting flips aria-sort.
        page.fill("#search", SEARCH_TERM)
        if not wait_for_filtered_count(page, expected_search, f"table view after search {SEARCH_TERM!r}"):
            browser.close()
            return
        if not page.is_visible("#table-wrap"):
            fail("table view does not show the table container")
        else:
            ok("table view shows the table container")
        rows = page.locator("#quote-table tbody tr").count()
        if rows != expected_search:
            fail(f"table view rendered {rows} rows, expected {expected_search}")
        else:
            ok(f"table view renders {rows} rows for the filtered set")
        page.click('#quote-table th[data-sort="id"]')
        page.wait_for_timeout(100)
        aria = page.get_attribute('#quote-table th[data-sort="id"]', "aria-sort")
        if aria not in ("ascending", "descending"):
            fail(f"clicking the ID header left aria-sort={aria!r}")
        else:
            ok(f"clicking the ID header sets aria-sort={aria!r}")
        page.select_option("#view-mode", "cards")
        page.fill("#search", "")
        wait_for_filtered_count(page, expected_total, "clearing the search")

        # The copy button puts the card's own quote text on the clipboard.
        first_card = page.locator("#results .card").first
        expected_text = first_card.locator(".quote-text").text_content() or ""
        first_card.locator(".copy-quote").click()
        page.wait_for_timeout(200)
        clipboard = page.evaluate("() => navigator.clipboard.readText()") or ""
        if clipboard != expected_text:
            fail(f"copy button clipboard mismatch: got {clipboard[:60]!r}, expected {expected_text[:60]!r}")
        else:
            ok("copy button writes that card's quote text to the clipboard")

        # Filters: option sets, one narrowing value per dropdown, the "Issues only" toggle,
        # a combined filter+search+sort, and the empty-result state. Every expected count is
        # recomputed from quotes.csv with the same predicates browser/app.js uses.
        check_filter_options(page, expected_quotes)
        check_filter_counts(page, expected_quotes)
        check_issues_only(page, expected_quotes)
        reset_filters(page, expected_total)
        check_combined_interaction(page, expected_quotes)
        reset_filters(page, expected_total)
        check_empty_state(page, expected_quotes)
        reset_filters(page, expected_total)

        if page_errors:
            fail(f"{len(page_errors)} page error(s): {page_errors[:3]}")
        else:
            ok("no page errors")
        if console_errors:
            fail(f"{len(console_errors)} console error(s): {console_errors[:3]}")
        else:
            ok("no console errors")
        if failed_requests:
            fail(f"{len(failed_requests)} failed request(s): {failed_requests[:3]}")
        else:
            ok("no failed requests")

        context.close()
        check_viewport_overflow(browser, base_url, expected_total, VIEWPORT_WIDTHS)
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--base-url",
        default=None,
        help="test an already-running server (e.g. http://127.0.0.1:8000) instead of starting one",
    )
    args = parser.parse_args()
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)

    expected_quotes = load_csv_rows(QUOTES_PATH)
    print(f"quotes.csv parses to {len(expected_quotes)} rows (app.js rule)")

    try:
        if args.base_url:
            run(args.base_url.rstrip("/"), expected_quotes)
        else:
            with Server(ROOT) as server:
                print(f"serving {ROOT} on http://127.0.0.1:{server.port}")
                run(f"http://127.0.0.1:{server.port}", expected_quotes)
    except Exception as exc:  # never exit with a bare traceback: RESULT must still be printed
        fail(f"unexpected error: {exc!r}")

    if failures:
        print(f"\nRESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    print(f"\nRESULT: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
