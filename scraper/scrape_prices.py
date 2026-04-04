#!/usr/bin/env python3
"""
Latvian fuel price scraper — diesel, petrol 95, petrol 98.

Scrapes 4 station brands and writes:
  output/src/data/station-prices.json  — per-brand, per-fuel prices
  output/src/data/prices.json          — average prices + history (appended)

Usage:
  python scraper/scrape_prices.py            # scrape and write files
  python scraper/scrape_prices.py --dry-run  # scrape only, print results
"""

import json
import re
import sys
from datetime import datetime, timezone, date
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
    "Accept-Language": "lv-LV,lv;q=0.9,en;q=0.8",
}
TIMEOUT = 20

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "src" / "data"

FUEL_KEYS = ["diesel", "petrol_95", "petrol_98"]
FUEL_LABELS = {
    "diesel":    "Diesel   ",
    "petrol_95": "Petrol 95",
    "petrol_98": "Petrol 98",
}

# ── Scrapers ───────────────────────────────────────────────────────────────────

# Virši uses data-type attributes on price cards.
# "dd" confirmed diesel. "95e"/"98e" confirmed petrol grades.
VIRSI_DATA_TYPES = {
    "diesel":    "dd",
    "petrol_95": "95e",
    "petrol_98": "98e",
}

def scrape_virsi() -> dict[str, float | None]:
    """
    div.price-card[data-type=X] → p.price → last span = price number
    """
    url = "https://www.virsi.lv/lv/privatpersonam/degviela/degvielas-un-elektrouzlades-cenas"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    result: dict[str, float | None] = {}
    for fuel, dtype in VIRSI_DATA_TYPES.items():
        card = soup.find("div", class_="price-card", attrs={"data-type": dtype})
        if not card:
            result[fuel] = None
            continue
        spans = card.select("p.price span")
        try:
            result[fuel] = float(spans[-1].get_text(strip=True)) if len(spans) >= 2 else None
        except (ValueError, IndexError):
            result[fuel] = None
    return result


# Circle K table rows identified by label text.
# "dmiles" is confirmed diesel. Petrol rows assumed to contain "95"/"98".
CIRCLEK_FUEL_PATTERNS = {
    "diesel":    "dmiles",
    "petrol_95": "95",
    "petrol_98": "98",
}

def scrape_circlek() -> dict[str, float | None]:
    """
    table.table tbody tr → first td label matches pattern → second td = price
    """
    url = "https://www.circlek.lv/degviela-miles/degvielas-cenas"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    result: dict[str, float | None] = {f: None for f in CIRCLEK_FUEL_PATTERNS}
    for row in soup.select("table.table tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).lower()
        for fuel, pattern in CIRCLEK_FUEL_PATTERNS.items():
            if result[fuel] is not None:
                continue
            if pattern in label:
                raw = cells[1].get_text(strip=True).replace("EUR", "").strip()
                try:
                    result[fuel] = float(raw)
                except ValueError:
                    pass
                break
    return result


# Neste page does not use a <table> — prices are in styled divs.
# Search the full page text for each fuel name then grab the nearest price.
NESTE_FUEL_PATTERNS = {
    "diesel":    "futura d",
    "petrol_95": "futura 95",
    "petrol_98": "futura 98",
}

def scrape_neste() -> dict[str, float | None]:
    """
    tr → first td label matches pattern (case-insensitive) → second td = price.
    Uses soup.select("tr") directly — the table wrapper tag is unreliable.
    """
    url = "https://www.neste.lv/lv/content/degvielas-cenas"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    result: dict[str, float | None] = {f: None for f in NESTE_FUEL_PATTERNS}
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        label = cells[0].get_text().lower().replace("\xa0", " ")
        for fuel, pattern in NESTE_FUEL_PATTERNS.items():
            if result[fuel] is not None:
                continue
            if pattern in label:
                raw = re.sub(r"[^\d.]", "", cells[1].get_text(strip=True))
                try:
                    result[fuel] = float(raw)
                except ValueError:
                    pass
                break
    return result


# Viada rows identified by img src substrings.
# URLs follow the pattern petrol_d_new.png / petrol_95_new.png / petrol_98_new.png
VIADA_FUEL_SRC_PATTERNS = {
    "diesel":    ("petrol_d",  ["petrol_95", "petrol_98"]),
    "petrol_95": ("petrol_95", []),
    "petrol_98": ("petrol_98", []),
}

def scrape_viada() -> dict[str, float | None]:
    """
    table tr → first td img src matches pattern → second td = price
    Takes minimum when multiple rows match (cheapest variant).
    """
    url = "https://www.viada.lv/zemakas-degvielas-cenas/"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    buckets: dict[str, list[float]] = {f: [] for f in VIADA_FUEL_SRC_PATTERNS}
    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        img = cells[0].find("img")
        if not img:
            continue
        src = img.get("src", "").lower()
        for fuel, (pattern, excludes) in VIADA_FUEL_SRC_PATTERNS.items():
            if pattern in src and not any(ex in src for ex in excludes):
                raw = cells[1].get_text(strip=True).replace("EUR", "").strip()
                try:
                    buckets[fuel].append(float(raw))
                except ValueError:
                    pass

    return {f: min(prices) if prices else None for f, prices in buckets.items()}


# ── Orchestration ──────────────────────────────────────────────────────────────

SCRAPERS = [
    ("Virši",    "virsi",    scrape_virsi),
    ("Circle K", "circlek",  scrape_circlek),
    ("Neste",    "neste",    scrape_neste),
    ("Viada",    "viada",    scrape_viada),
]


def run_scrapers() -> list[dict]:
    results = []
    for brand, key, fn in SCRAPERS:
        try:
            prices = fn()
            for fuel in FUEL_KEYS:
                price = prices.get(fuel)
                if price is not None:
                    print(f"  ✅ {brand:<10} {FUEL_LABELS[fuel]}  {price:.3f} EUR")
                else:
                    print(f"  ⚠️  {brand:<10} {FUEL_LABELS[fuel]}  N/A")
            results.append({"brand": brand, "key": key, "prices": prices, "error": None})
        except Exception as e:
            print(f"  ❌ {brand:<10} FAILED — {e}")
            results.append({
                "brand": brand,
                "key": key,
                "prices": {f: None for f in FUEL_KEYS},
                "error": str(e),
            })
    return results


def build_station_prices(results: list[dict], scraped_at: str) -> dict:
    return {
        "scraped_at": scraped_at,
        "stations": [
            {
                "brand": r["brand"],
                "key": r["key"],
                "prices": r["prices"],
                "currency": "EUR",
                "error": r["error"],
            }
            for r in results
        ],
    }


def compute_averages(results: list[dict], existing_averages: dict) -> tuple[dict, dict, bool]:
    """Returns (new_averages, history_entry, any_valid). Does not print."""
    today_str = date.today().isoformat()
    history_entry: dict = {"date": today_str}
    any_valid = False
    new_averages: dict = {}

    for fuel in FUEL_KEYS:
        valid = [r["prices"].get(fuel) for r in results if r["prices"].get(fuel) is not None]
        if valid:
            avg = round(sum(valid) / len(valid), 3)
            new_averages[fuel] = avg
            history_entry[fuel] = avg
            any_valid = True
        else:
            new_averages[fuel] = existing_averages.get(fuel, 0)

    return new_averages, history_entry, any_valid


def update_prices_json(results: list[dict], scraped_at: str) -> None:
    """Recalculates per-fuel averages and writes prices.json (no history)."""
    prices_path = OUTPUT_DIR / "prices.json"
    existing = json.loads(prices_path.read_text()) if prices_path.exists() else {
        "averages": {f: 0 for f in FUEL_KEYS},
        "currency": "EUR",
        "unit": "liter",
        "last_updated": scraped_at,
    }

    new_averages, _, any_valid = compute_averages(results, existing.get("averages", {}))

    for fuel in FUEL_KEYS:
        if new_averages.get(fuel):
            print(f"  ✅ {FUEL_LABELS[fuel]}  avg {new_averages[fuel]:.3f} EUR")
        else:
            print(f"  ⚠️  {FUEL_LABELS[fuel]}  no valid prices")

    if not any_valid:
        print("  ⚠️  No valid prices scraped — prices.json not updated")
        return

    existing.update({
        "averages": new_averages,
        "last_updated": scraped_at,
    })
    # Remove legacy history field if present
    existing.pop("history", None)

    prices_path.write_text(json.dumps(existing, indent=2))


def update_price_history(results: list[dict], scraped_at: str) -> None:
    """Appends each scrape as a new timestamped entry into price-history.json.
    Multiple entries per date are expected; the chart averages them per day."""
    history_path = OUTPUT_DIR / "price-history.json"
    existing = json.loads(history_path.read_text()) if history_path.exists() else {"history": []}

    prices_data_path = OUTPUT_DIR / "prices.json"
    existing_averages: dict = {}
    if prices_data_path.exists():
        existing_averages = json.loads(prices_data_path.read_text()).get("averages", {})

    _, history_entry, any_valid = compute_averages(results, existing_averages)

    if not any_valid:
        print("  ⚠️  No valid prices scraped — price-history.json not updated")
        return

    history_entry["datetime"] = scraped_at  # full ISO timestamp for this poll
    history_entry["stations"] = {
        r["key"]: r["prices"] for r in results
    }

    history: list[dict] = existing.get("history", [])
    history.insert(0, history_entry)  # prepend; newest first

    history_path.write_text(json.dumps({"history": history}, indent=2))


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    print(f"\n{'='*50}")
    print("Fuel Price Scraper")
    print(f"{'='*50}\n")

    scraped_at = datetime.now(timezone.utc).isoformat()
    results = run_scrapers()

    if dry_run:
        print("\n[dry-run] Would write station-prices.json:")
        print(json.dumps(build_station_prices(results, scraped_at), indent=2))
        print("\n[dry-run] Averages that would be written to prices.json + price-history.json:")
        for fuel in FUEL_KEYS:
            valid = [r["prices"].get(fuel) for r in results if r["prices"].get(fuel) is not None]
            avg = round(sum(valid) / len(valid), 3) if valid else None
            print(f"  {FUEL_LABELS[fuel]}  {avg:.3f} EUR" if avg else f"  {FUEL_LABELS[fuel]}  N/A")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    station_data = build_station_prices(results, scraped_at)
    station_path = OUTPUT_DIR / "station-prices.json"
    station_path.write_text(json.dumps(station_data, indent=2))
    print(f"\n  ✅ station-prices.json written → {station_path}")

    print()
    update_prices_json(results, scraped_at)
    print(f"  ✅ prices.json updated → {OUTPUT_DIR / 'prices.json'}")

    print()
    update_price_history(results, scraped_at)
    print(f"  ✅ price-history.json updated → {OUTPUT_DIR / 'price-history.json'}")

    print(f"\n{'='*50}")
    print("Done.")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
