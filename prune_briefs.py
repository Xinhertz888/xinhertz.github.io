#!/usr/bin/env python3
"""Prune news briefs older than 7 days from data/briefs.json,
rebuild the static pages, and push. Keeps published.json (dedup ledger) intact
so old stories are never re-published.

Retention rule: keep entries with (today - entry_date).days <= 7,
where "today" is Asia/Shanghai.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

SITE = os.path.expanduser("~/workspace/xinhertz/site")
DATA = os.path.join(SITE, "data/briefs.json")
RETENTION_DAYS = 7
DRY_RUN = "--dry-run" in sys.argv


def parse_date(s):
    return datetime.strptime(s.strip(), "%b %d, %Y").date()


def main():
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    with open(DATA, encoding="utf-8") as f:
        briefs = json.load(f)

    kept, removed = [], []
    for b in briefs:
        try:
            age = (today - parse_date(b["date"])).days
        except (KeyError, ValueError):
            age = 0  # unparseable date: keep, never silently drop
        (kept if age <= RETENTION_DAYS else removed).append(b)

    print(f"today={today} total={len(briefs)} keep={len(kept)} remove={len(removed)}")
    for b in removed:
        print(f"  - {b.get('date')}: {b.get('title','')[:60]}")

    if DRY_RUN:
        print("dry-run: no changes written")
        return
    if not removed:
        print("nothing to prune")
        return

    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    subprocess.run(["python3", "build_news.py"], cwd=SITE, check=True)
    # -A stages modifications AND deletions of tracked files (build_news.py
    # deletes stale news-N.html pages from disk; a bare `git add news-*.html`
    # glob would miss those deletions and leave dead pages published).
    subprocess.run(
        ["git", "add", "-A", "news.html", "news-*.html", "data/briefs.json",
         "index.html", "sitemap.xml"],
        cwd=SITE, check=True,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=SITE, capture_output=True, text=True
    ).stdout.strip()
    if not status:
        print("no file changes after rebuild; nothing committed")
        return
    subprocess.run(
        ["git", "commit", "-m",
         f"news: prune {len(removed)} brief(s) older than {RETENTION_DAYS} days"],
        cwd=SITE, check=True,
    )
    subprocess.run(["git", "push"], cwd=SITE, check=True)
    print(f"pruned {len(removed)} brief(s), pushed")


if __name__ == "__main__":
    main()
