#!/usr/bin/env python3
"""Rebuild paginated news pages + homepage Industry Insights from data/briefs.json.

Usage: python3 build_news.py
- data/briefs.json: newest-first list of {date, title, body:[paragraphs], sources}
- Generates: news.html (page 1), news-2.html, news-3.html ... (5 briefs per page)
- Updates: index.html "Industry Insights" first card -> latest brief
Static output (no client JS): SEO-friendly, each page stays small.
"""
import html
import json
import math
import re
from pathlib import Path

BASE = Path(__file__).parent
PER_PAGE = 5


def card(b):
    paras = "\n".join(f"          <p>{html.escape(p)}</p>" for p in b["body"])
    return f"""      <article class="feed-item">
        <div class="feed-meta">
          <span class="feed-num"></span>
          <span class="feed-time">{html.escape(b["date"])}</span>
        </div>
        <h3 class="feed-title">{html.escape(b["title"])}</h3>
        <div class="feed-body">
{paras}
        </div>
        <div class="feed-foot">Sources: {html.escape(b["sources"])}</div>
      </article>"""


def pagination(page, total):
    def url(p):
        return "news.html" if p == 1 else f"news-{p}.html"

    nums = " ".join(
        f'<a href="{url(p)}" class="pg-cur">{p}</a>' if p == page else f'<a href="{url(p)}">{p}</a>'
        for p in range(1, total + 1)
    )
    prev = (
        f'<a class="pg-prev" href="{url(page - 1)}">&larr; Newer</a>'
        if page > 1
        else '<span class="pg-prev pg-dis">&larr; Newer</span>'
    )
    nxt = (
        f'<a class="pg-next" href="{url(page + 1)}">Older &rarr;</a>'
        if page < total
        else '<span class="pg-next pg-dis">Older &rarr;</span>'
    )
    return f"""    <nav class="pagination">
      {prev}
      <span class="pg-nums">{nums}</span>
      <span class="pg-info">Page {page} of {total}</span>
      {nxt}
    </nav>"""


def main():
    briefs = json.loads((BASE / "data" / "briefs.json").read_text(encoding="utf-8"))
    total = len(briefs)
    pages = max(1, math.ceil(total / PER_PAGE))

    shell = (BASE / "news.html").read_text(encoding="utf-8")
    start_marker = "<!-- FEED-LIST-START: new items are prepended right after this line, newest first -->"
    end_marker = "<!-- FEED-LIST-END -->"
    head, rest = shell.split(start_marker, 1)
    head += start_marker
    # rest: [old cards][end_marker]</div>[template comment][page footer...]
    tail_after_end = rest.split(end_marker, 1)[1]
    # strip the big TEMPLATE comment box (═ ruled), keep everything after it
    tail_after_end = re.sub(r"\s*<!--\s*\n\s*═+.*?═+\s*-->", "", tail_after_end, flags=re.S)
    # tail_after_end now starts with "\n    </div>\n\n  </div>\n</section>..." — keep from </div> on
    tail = end_marker + tail_after_end

    for page in range(1, pages + 1):
        chunk = briefs[(page - 1) * PER_PAGE : page * PER_PAGE]
        cards = "\n\n".join(card(b) for b in chunk)
        label = "Latest briefs" if page == 1 else "Briefs archive"
        pg = head + "\n\n" + cards + "\n\n      " + tail
        pg = pg.replace(
            '<div class="feed-day">Latest briefs</div>',
            f'<div class="feed-day">{label}</div>',
        )
        pg = re.sub(
            r'<div class="feed-count"><span id="brief-count">\d+</span> briefs?</div>',
            f'<div class="feed-count"><span id="brief-count">{total}</span> briefs</div>',
            pg,
        )
        # insert pagination right after the closing </div> of .feed-list
        pg = pg.replace(
            end_marker + "\n    </div>",
            end_marker + "\n    </div>\n\n" + pagination(page, pages),
            1,
        )
        out = BASE / ("news.html" if page == 1 else f"news-{page}.html")
        out.write_text(pg, encoding="utf-8")
        print(f"wrote {out.name} ({len(chunk)} briefs)")

    # remove stale archive pages beyond current page count
    n = pages + 1
    while (BASE / f"news-{n}.html").exists():
        (BASE / f"news-{n}.html").unlink()
        print(f"removed stale news-{n}.html")
        n += 1

    # ---- index.html: Industry Insights first card = latest brief ----
    if briefs:
        latest = briefs[0]
        excerpt = latest["body"][0]
        if len(excerpt) > 180:
            excerpt = excerpt[:180].rsplit(" ", 1)[0] + "…"
        idx = (BASE / "index.html").read_text(encoding="utf-8")
        new_card = f"""      <div class="card news-card">
        <div class="news-date">{html.escape(latest["date"])}</div>
        <h3><a href="news.html">{html.escape(latest["title"])}</a></h3>
        <p>{html.escape(excerpt)}</p>
        <a class="more" href="news.html">Read brief &rarr;</a>
      </div>"""
        idx, found = re.subn(
            # Match the whole first news-card: opening line, then lazily consume
            # full lines until the card's own closing </div> at column 6.
            # (Nested divs like news-date are indented deeper, so they can't
            #  match the closing anchor.)
            r'      <div class="card news-card">\n(?:.*\n)*?      </div>\n',
            new_card + "\n",
            idx,
            count=1,
        )
        if found:
            idx = idx.replace(
                "What we're watching in the components market — so you can plan your BOM ahead of the curve.",
                "Short industry briefs on semiconductor pricing, supply and product news — newest first.",
            )
            (BASE / "index.html").write_text(idx, encoding="utf-8")
            print("index.html Industry Insights updated ->", latest["title"][:60])
        else:
            print("WARN: news-card block not found in index.html")


if __name__ == "__main__":
    main()
