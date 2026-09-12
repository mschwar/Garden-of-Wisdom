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
     `quotes.csv` by the same rule `browser/app.js` uses;
  3. search — typing a term narrows the rendered set to exactly the rows whose
     text/author/source/tags contain it;
  4. view switch — card view leaves no empty table container behind, table view renders one
     row per filtered quote, and clicking a sortable header flips `aria-sort`;
  5. copy — the per-card "Copy quote" button puts that card's quote text on the clipboard;
  6. layout — at 320/375/768px wide the document does not overflow horizontally, in both
     card and table view;
  7. zero console errors, zero page errors, zero failed requests.

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
            page.close()


def run(base_url: str, expected_quotes: list[dict[str, str]]) -> None:
    from playwright.sync_api import sync_playwright

    check_static_layout(base_url)

    expected_total = len(expected_quotes)
    expected_search = sum(1 for row in expected_quotes if matches_search(row, SEARCH_TERM))

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
