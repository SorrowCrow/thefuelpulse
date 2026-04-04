#!/usr/bin/env python3
"""
Fuel news scraper — fetches articles from RSS feeds and filters for fuel-related content.

Sources:
  - Google News RSS (Latvian — local prices)
  - Google News RSS (English — Latvia fuel)
  - Google News RSS (Global oil market + geopolitics)
  - Google News RSS (OPEC / Iran / sanctions)
  - Delfi.lv RSS

Writes:
  output/src/data/news-raw.json

Usage:
  python scraper/scrape_news.py            # fetch and write
  python scraper/scrape_news.py --dry-run  # fetch only, print results
"""

import json
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Config ─────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
TIMEOUT = 20
MAX_ARTICLES = 20  # total across all feeds, most recent first

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "src" / "data"

FUEL_KEYWORDS = [
    # Latvian
    "degviela", "benzīns", "dīzelis", "nafta", "degvielas", "naftas",
    "enerģijas cena", "eļļas cena",
    # Station brands
    "virši", "circle k", "neste", "viada",
    # English — local
    "fuel price", "petrol price", "diesel price", "gasoline", "oil price",
    # English — global market & geopolitics
    "crude oil", "brent", "opec", "opec+", "oil supply", "oil demand",
    "oil sanction", "iran", "russia oil", "energy price", "energy market",
    "refinery", "oil production", "barrel",
]

# Two tiers of feeds: Latvia-specific + global market context
RSS_FEEDS = [
    # ── Latvia ──────────────────────────────────────────────────────────
    (
        "Latvia (LV)",
        "https://news.google.com/rss/search?q=degvielas+cenas+latvija&hl=lv&gl=LV&ceid=LV:lv",
    ),
    (
        "Latvia (EN)",
        "https://news.google.com/rss/search?q=fuel+prices+latvia&hl=en&gl=LV&ceid=LV:en",
    ),
    (
        "Delfi.lv",
        "https://www.delfi.lv/rss/",
    ),
    # ── Global oil market ────────────────────────────────────────────────
    (
        "Global oil market",
        "https://news.google.com/rss/search?q=crude+oil+price+brent+WTI&hl=en&gl=US&ceid=US:en",
    ),
    (
        "OPEC & geopolitics",
        "https://news.google.com/rss/search?q=OPEC+oil+supply+iran+sanctions+russia+energy&hl=en&gl=US&ceid=US:en",
    ),
    (
        "Europe energy",
        "https://news.google.com/rss/search?q=europe+fuel+price+energy+diesel&hl=en&gl=GB&ceid=GB:en",
    ),
]


# ── Parsing ─────────────────────────────────────────────────────────────────────

def parse_date(raw: str) -> str:
    """Parse RFC 2822 pubDate to ISO 8601. Returns empty string on failure."""
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        return ""


def is_fuel_related(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in FUEL_KEYWORDS)


def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return []

    try:
        soup = BeautifulSoup(r.content, "xml")
    except Exception:
        soup = BeautifulSoup(r.text, "lxml")

    articles = []
    for item in soup.find_all("item"):
        title_tag = item.find("title")
        link_tag  = item.find("link")
        desc_tag  = item.find("description")
        date_tag  = item.find("pubDate")

        title   = (title_tag.get_text(strip=True)   if title_tag else "").strip()
        url_str = (link_tag.get_text(strip=True)    if link_tag  else "").strip()
        desc    = (desc_tag.get_text(strip=True)    if desc_tag  else "").strip()
        pub     = (date_tag.get_text(strip=True)    if date_tag  else "").strip()

        # Strip HTML from description if present
        if "<" in desc:
            desc = BeautifulSoup(desc, "lxml").get_text(strip=True)

        combined = title + " " + desc
        if not is_fuel_related(combined):
            continue

        articles.append({
            "source":       name,
            "title":        title,
            "url":          url_str,
            "description":  desc[:400],
            "published_at": parse_date(pub),
        })

    print(f"  {'✅' if articles else '⚠️ '} {name}: {len(articles)} fuel articles")
    return articles


# ── Orchestration ───────────────────────────────────────────────────────────────

def run() -> list[dict]:
    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    for name, url in RSS_FEEDS:
        for article in fetch_feed(name, url):
            if article["url"] and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                all_articles.append(article)

    # Sort by published_at descending (empty strings sort last)
    all_articles.sort(key=lambda a: a["published_at"], reverse=True)
    return all_articles[:MAX_ARTICLES]


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    print(f"\n{'='*50}")
    print("Fuel News Scraper")
    print(f"{'='*50}\n")

    articles = run()

    if dry_run:
        print(f"\n[dry-run] {len(articles)} articles would be written:")
        for i, a in enumerate(articles, 1):
            print(f"  {i}. [{a['published_at'][:10] or '?'}] {a['title'][:80]}")
            print(f"      {a['source']} — {a['url'][:70]}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles,
    }
    path = OUTPUT_DIR / "news-raw.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n  ✅ {len(articles)} articles → {path}")
    print(f"\n{'='*50}\nDone.\n{'='*50}\n")


if __name__ == "__main__":
    main()
