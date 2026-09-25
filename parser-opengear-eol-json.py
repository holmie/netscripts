"""Fetch Opengear End-of-Life product data and emit it as structured JSON.

Parses the four EOL tables on https://opengear.com/end-life-products:

  1. Hardware Lifecycle
  2. Hardware Revisions
  3. Software End of Support
  4. Software Subscriptions End of Sale

Each table becomes a ``{"title", "columns", "rows"}`` object, where every row
maps each column header to a cell object of the form::

    {"text": "Product name", "url": null, "items": ["Product name"]}

Multi-value cells (those separated by ``<br>`` in the source, such as long SKU
or replacement-product lists) also expose an ``items`` list, e.g.::

    {"text": "EMD5000-01 EMD5000-02",
     "url": null,
     "items": ["EMD5000-01", "EMD5000-02"]}

A cell containing a single hyperlink (the EoL/EoS notices) surfaces that URL in
``url`` along with its link text in ``text``.

Example
-------
::

    $ python3 fetch_eol.py
    {
      "source": "https://opengear.com/end-life-products",
      "scrapedAt": "2026-09-25T...+00:00",
      "usedLocalFallback": false,
      "tableCount": 4,
      "tables": [ ... ]
    }

Usage
-----
::

    python3 fetch_eol.py                # fetch live, compact JSON to stdout
    python3 fetch_eol.py > eol.json     # save to a file
    python3 fetch_eol.py --local        # parse the bundled page.html instead
    python3 fetch_eol.py <url>          # parse any other HTML page / URL

The ``--local`` flag, and the automatic fallback below, read from ``page.html``
in the current directory, which is handy for offline use or testing.

Dependencies
------------
* Python 3.8+
* `requests <https://requests.readthedocs.io>`_
* `BeautifulSoup (bs4) <https://pypi.org/project/bs4>`_

Install the runtime dependencies with::

    pip install requests bs4

Robustness
----------
If fetching the live page fails (network error, non-2xx status, timeout) the
script transparently falls back to the local ``page.html`` file. Set
``--local`` to force that path and skip the network entirely.
"""

import json
import re
import sys
import argparse
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://opengear.com/end-life-products"
LOCAL_FALLBACK = "page.html"
USER_AGENT = "Mozilla/5.0 (compatible; OpengearEOL/1.0)"


def parse_cell(cell):
    """Turn a <th>/<td> into a structured cell dict.

    Splitting on <br> yields an "items" list for multi-value cells
    (e.g. long SKU or replacement-product lists). A single link in the cell
    is surfaced as "url".
    """
    for br in cell.find_all("br"):
        br.replace_with(" \n ")
    raw = cell.get_text()
    items = [re.sub(r"\s+", " ", p).strip()
             for p in raw.split("\n")]
    items = [p for p in items if p]
    text = " ".join(items)
    links = [
        {"text": a.get_text(strip=True), "url": a.get("href")}
        for a in cell.find_all("a")
        if a.get("href")
    ]
    return {
        "text": text,
        "url": links[0]["url"] if len(links) == 1 else None,
        "items": items,
    }


def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = []
    for table in soup.find_all("table", class_="eol-table"):
        headers = [th.get_text(strip=True) for th in table.thead.find_all("th")]
        title = table.find_previous("h2")
        title = title.get_text(strip=True) if title else "Unknown"

        rows = []
        for tr in table.find_all("tr"):
            cells = [c for c in tr.children
                     if getattr(c, "name", None) in ("th", "td")]
            if not cells:
                continue  # skip empty rows from malformed/nested <tr>
            if all(c.name == "th" for c in cells):
                continue  # skip the header row
            entry = {}
            for col, cell in zip(headers, cells):
                entry[col] = parse_cell(cell)
            rows.append(entry)

        tables.append({"title": title, "columns": headers, "rows": rows})
    return tables


def fetch_html(url, use_local):
    if use_local:
        with open(LOCAL_FALLBACK, "r", encoding="utf-8") as f:
            return f.read(), True
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        return resp.text, False
    except Exception:
        try:
            with open(LOCAL_FALLBACK, "r", encoding="utf-8") as f:
                return f.read(), True
        except OSError:
            raise


def main():
    ap = argparse.ArgumentParser(
        description="Fetch & parse Opengear EOL data as JSON")
    ap.add_argument("url", nargs="?", default=PAGE_URL, help="HTML page URL")
    ap.add_argument("--local", action="store_true",
                    help="Read from local page.html instead of fetching")
    args = ap.parse_args()

    html, used_local = fetch_html(args.url, args.local)
    result = {
        "source": args.url,
        "sourceUrl": args.url,
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "usedLocalFallback": used_local,
        "tableCount": None,
        "tables": parse_html(html),
    }
    result["tableCount"] = len(result["tables"])

    indent = 2 if not sys.stdout.isatty() else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))


if __name__ == "__main__":
    main()
