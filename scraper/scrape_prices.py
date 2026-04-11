#!/usr/bin/env python3
"""
Latvian fuel price scraper — diesel, petrol 95, petrol 98, and specialty fuels.

Scrapes 4 station brands and writes:
  output/src/data/station-prices.json  — per-brand, per-fuel FuelEntry list
  output/src/data/prices.json          — average prices (standard fuels)
  output/src/data/price-history.json   — historical averages + station snapshots

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
import urllib3
from bs4 import BeautifulSoup

# Viada's SSL cert chain is broken — suppress the resulting InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def scrape_virsi() -> list[dict]:
    """
    div.price-card[data-type=X] → p.price → last span = price number.
    Returns a list of FuelEntry dicts.
    """
    url = "https://www.virsi.lv/lv/privatpersonam/degviela/degvielas-un-elektrouzlades-cenas"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Maps data-type attribute value → (fuel_type, fuel_name, category)
    DATA_TYPE_MAP = {
        "dd":     ("diesel",    "Virši DD",  "standard"),
        "95e":    ("petrol_95", "Virši 95E", "standard"),
        "98e":    ("petrol_98", "Virši 98E", "standard"),
        "cng":    ("cng",       "CNG",       "specialty"),
        "lpg":    ("lpg",       "LPG",       "specialty"),
        "adblue": ("adblue",    "AdBlue",    "specialty"),
    }

    entries: list[dict] = []
    for dtype, (fuel_type, fuel_name, category) in DATA_TYPE_MAP.items():
        card = soup.find("div", class_="price-card", attrs={"data-type": dtype})
        if not card:
            continue
        spans = card.select("p.price span")
        try:
            price = float(spans[-1].get_text(strip=True)) if len(spans) >= 2 else None
        except (ValueError, IndexError):
            price = None
        if price is None:
            continue
        entries.append({
            "fuel_type": fuel_type,
            "fuel_name": fuel_name,
            "category":  category,
            "price":     price,
            "currency":  "EUR",
        })
    return entries


def scrape_circlek() -> list[dict]:
    """
    table.table tbody tr → first td label matches pattern → second td = price.
    Returns a list of FuelEntry dicts.
    Check most-specific labels first to avoid false positives.
    """
    url = "https://www.circlek.lv/degviela-miles/degvielas-cenas"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Ordered list: (label_check_fn, fuel_type, fuel_name, category)
    # Check "dmiles+" before "dmiles" and "98" before "95" to avoid false positives.
    LABEL_MAP = [
        (lambda lbl: "dmiles+" in lbl,                      "premium_diesel", "Dmiles+",     "premium"),
        (lambda lbl: "dmiles" in lbl and "+" not in lbl,    "diesel",         "Dmiles",      "standard"),
        (lambda lbl: "xtl" in lbl,                          "xtl",            "miles+ XTL",  "specialty"),
        (lambda lbl: "98" in lbl,                           "petrol_98",      "98miles+",    "standard"),
        (lambda lbl: "95" in lbl and "98" not in lbl,       "petrol_95",      "95miles",     "standard"),
        (lambda lbl: "autogāze" in lbl or "lpg" in lbl,     "lpg",            "Autogāze/LPG","specialty"),
    ]

    entries: list[dict] = []
    seen_fuel_types: set[str] = set()

    for row in soup.select("table.table tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).lower()
        for check_fn, fuel_type, fuel_name, category in LABEL_MAP:
            if fuel_type in seen_fuel_types:
                continue
            if check_fn(label):
                raw = cells[1].get_text(strip=True).replace("EUR", "").strip()
                try:
                    price = float(raw)
                except ValueError:
                    break
                seen_fuel_types.add(fuel_type)
                entries.append({
                    "fuel_type": fuel_type,
                    "fuel_name": fuel_name,
                    "category":  category,
                    "price":     price,
                    "currency":  "EUR",
                })
                break
    return entries


def scrape_neste() -> list[dict]:
    """
    tr → first td label matches pattern (case-insensitive) → second td = price.
    Uses soup.select("tr") directly — the table wrapper tag is unreliable.
    Iterates ALL rows; does not break early.
    Returns a list of FuelEntry dicts.
    """
    url = "https://www.neste.lv/lv/content/degvielas-cenas"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Maps label substring → (fuel_type, fuel_name, category)
    LABEL_MAP = [
        ("futura d",       "diesel",         "Neste Futura D",          "standard"),
        ("futura 95",      "petrol_95",       "Neste Futura 95",         "standard"),
        ("futura 98",      "petrol_98",       "Neste Futura 98",         "standard"),
        ("pro diesel",     "premium_diesel",  "Neste Pro Diesel",        "premium"),
        ("my renewable",   "hvo",             "Neste MY Renewable Diesel","specialty"),
        ("hvo",            "hvo",             "Neste MY Renewable Diesel","specialty"),
    ]

    entries: list[dict] = []
    seen_fuel_types: set[str] = set()

    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        label = cells[0].get_text().lower().replace("\xa0", " ").strip()
        for lbl_pattern, fuel_type, fuel_name, category in LABEL_MAP:
            if fuel_type in seen_fuel_types:
                continue
            if lbl_pattern in label:
                raw = re.sub(r"[^\d.]", "", cells[1].get_text(strip=True))
                try:
                    price = float(raw)
                except ValueError:
                    break
                seen_fuel_types.add(fuel_type)
                entries.append({
                    "fuel_type": fuel_type,
                    "fuel_name": fuel_name,
                    "category":  category,
                    "price":     price,
                    "currency":  "EUR",
                })
                break
    return entries


def scrape_kool() -> list[dict]:
    """
    Kool fuel prices are embedded in a readymag HtmlSnippet page served from the CDN.
    The main page (https://kool.lv/degviela/) embeds ServerData JSON in a <script> tag;
    within that JSON each page object carries an ``htmlUrl`` field pointing to a static
    CDN-hosted HTML fragment.  The fuel-prices page is identified by
    ``pagePath == "degviela"`` and ``pageNestedNum == "5"``.

    Inside the HtmlSnippet every price/label is a ``widget-text-v3`` div whose CSS
    ``left`` pixel position determines its column (fuel type):

      95E  → left  260-320 px
      98*  → left  400-435 px
      DD   → left  535-570 px
      Kool Premium DD → left 680-715 px

    Two station locations appear on the same page (stacked vertically); both price rows
    are parsed and the minimum (cheapest) is reported per fuel type.

    Returns a list of FuelEntry dicts.
    """
    main_url = "https://kool.lv/degviela/"
    r = requests.get(main_url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Locate the ServerData JSON embedded in a <script> tag
    server_data_json: str | None = None
    for script in soup.find_all("script"):
        txt = script.get_text()
        if "ServerData" in txt and "htmlUrl" in txt:
            m = re.search(
                r"window\.ServerData\s*=\s*(\{.+\})\s*;?\s*$", txt, re.DOTALL | re.MULTILINE
            )
            if m:
                server_data_json = m.group(1)
                break

    if not server_data_json:
        raise RuntimeError("Kool: ServerData JSON not found in page source")

    data_str = json.dumps(json.loads(server_data_json))

    # The fuel-prices page object has pagePath "degviela" followed by its htmlUrl
    html_url_m = re.search(
        r'"pagePath"\s*:\s*"degviela".*?"htmlUrl"\s*:\s*"([^"]+)"', data_str
    )
    if not html_url_m:
        raise RuntimeError("Kool: htmlUrl for degviela page not found in ServerData")

    html_url = html_url_m.group(1)

    # Fetch the static HtmlSnippet that contains the price widgets
    r2 = requests.get(html_url, headers=HEADERS, timeout=TIMEOUT)
    r2.raise_for_status()
    snippet = BeautifulSoup(r2.text, "lxml")

    # X-pixel column ranges → (fuel_type, fuel_name, category)
    COLUMN_MAP: list[tuple[int, int, str, str, str]] = [
        (260, 320, "petrol_95",      "Kool 95",          "standard"),
        (400, 435, "petrol_98",      "Kool 98",          "standard"),
        (535, 570, "diesel",         "Kool Diesel",      "standard"),
        (680, 715, "premium_diesel", "Kool Premium DD",  "premium"),
    ]

    # Collect (left_px, price_value) pairs from all text widgets
    candidate_prices: list[tuple[int, float]] = []
    for widget in snippet.find_all(class_="widget-text-v3"):
        style = widget.get("style", "")
        left_m = re.search(r"left:\s*(\d+)px", style)
        if not left_m:
            continue
        left_px = int(left_m.group(1))
        raw = widget.get_text(strip=True).replace("\u200d", "").replace(",", ".").strip()
        try:
            val = float(raw)
        except ValueError:
            continue
        if 1.0 < val < 5.0:
            candidate_prices.append((left_px, val))

    # Group by column, take minimum price per fuel type
    entries: list[dict] = []
    for x_min, x_max, fuel_type, fuel_name, category in COLUMN_MAP:
        column_prices = [v for left_px, v in candidate_prices if x_min <= left_px <= x_max]
        if not column_prices:
            continue
        entries.append({
            "fuel_type": fuel_type,
            "fuel_name": fuel_name,
            "category":  category,
            "price":     min(column_prices),
            "currency":  "EUR",
        })
    return entries


def scrape_viada() -> list[dict]:
    """
    table tr → first td img src matches pattern → second td = price.
    Emits one FuelEntry per matched row. No deduplication or min-price logic.
    Returns a list of FuelEntry dicts.
    """
    url = "https://www.viada.lv/zemakas-degvielas-cenas/"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Ordered list: (src_substring, fuel_type, fuel_name, category, station_type, note)
    # Check "petrol_95ectoplus" before "petrol_95ecto" and "ecto" before "d_new".
    SRC_MAP = [
        ("petrol_95ectoplus", "petrol_95_premium", "95 Ecto+",     "premium",  "ADUS", "Loyalty cards not accepted"),
        ("petrol_95ecto",     "petrol_95",         "95 Ecto",      "standard", "ADUS", "Loyalty cards not accepted"),
        ("petrol_98",         "petrol_98",         "Petrol 98",    "standard", "ADUS", None),
        ("petrol_d_ecto",     "diesel_ecto",       "Diesel Ecto",  "standard", "ADUS", "Loyalty cards not accepted"),
        ("petrol_d_new",      "diesel",            "Diesel",       "standard", "DUS",  None),
        ("gaze",              "lpg",               "LPG",          "specialty","ADUS", None),
        ("petrol_e85",        "e85",               "E85",          "specialty","DUS",  None),
    ]

    entries: list[dict] = []

    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        img = cells[0].find("img")
        if not img:
            continue
        src = img.get("src", "").lower()

        for src_substr, fuel_type, fuel_name, category, station_type, note in SRC_MAP:
            if src_substr in src:
                raw = cells[1].get_text(strip=True).replace("EUR", "").strip()
                try:
                    price = float(raw)
                except ValueError:
                    break
                entry: dict = {
                    "fuel_type":    fuel_type,
                    "fuel_name":    fuel_name,
                    "category":     category,
                    "price":        price,
                    "station_type": station_type,
                    "currency":     "EUR",
                }
                if note is not None:
                    entry["note"] = note
                entries.append(entry)
                break  # one match per row
    return entries


# ── Orchestration ──────────────────────────────────────────────────────────────

SCRAPERS = [
    ("Virši",    "virsi",    scrape_virsi),
    ("Circle K", "circlek",  scrape_circlek),
    ("Neste",    "neste",    scrape_neste),
    ("Viada",    "viada",    scrape_viada),
    ("Kool",     "kool",     scrape_kool),
]


def run_scrapers() -> list[dict]:
    results = []
    for brand, key, fn in SCRAPERS:
        try:
            entries = fn()
            for entry in entries:
                print(
                    f"  {brand:<10} | {entry['fuel_name']:<30} | "
                    f"{entry['price']:.3f} EUR | {entry['category']}"
                )
            results.append({"brand": brand, "key": key, "fuel_entries": entries, "error": None})
        except Exception as e:
            print(f"  FAILED {brand:<10} — {e}")
            results.append({
                "brand": brand,
                "key": key,
                "fuel_entries": [],
                "error": str(e),
            })
    return results


def build_station_prices(results: list[dict], scraped_at: str) -> dict:
    return {
        "scraped_at": scraped_at,
        "stations": [
            {
                "brand":        r["brand"],
                "key":          r["key"],
                "fuel_entries": r["fuel_entries"],
                "error":        r["error"],
            }
            for r in results
        ],
    }


def _get_standard_price(result: dict, fuel_type: str) -> float | None:
    """Return the price of the first standard-category FuelEntry matching fuel_type, or None."""
    for entry in result.get("fuel_entries", []):
        if entry.get("fuel_type") == fuel_type and entry.get("category") == "standard":
            return entry["price"]
    return None


def compute_averages(results: list[dict], existing_averages: dict) -> tuple[dict, dict, bool]:
    """Returns (new_averages, history_entry, any_valid). Does not print."""
    today_str = date.today().isoformat()
    history_entry: dict = {"date": today_str}
    any_valid = False
    new_averages: dict = {}

    for fuel in FUEL_KEYS:
        valid = [
            price for r in results
            if (price := _get_standard_price(r, fuel)) is not None
        ]
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
            print(f"  {FUEL_LABELS[fuel]}  avg {new_averages[fuel]:.3f} EUR")
        else:
            print(f"  {FUEL_LABELS[fuel]}  no valid prices")

    if not any_valid:
        print("  No valid prices scraped — prices.json not updated")
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
        print("  No valid prices scraped — price-history.json not updated")
        return

    history_entry["datetime"] = scraped_at  # full ISO timestamp for this poll
    history_entry["stations"] = {
        r["key"]: {
            entry["fuel_type"]: entry["price"]
            for entry in r["fuel_entries"]
            if entry.get("category") == "standard"
        }
        for r in results
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
        print("\n[dry-run] Entries per station:")
        for r in results:
            print(f"\n  {r['brand']}:")
            for entry in r["fuel_entries"]:
                print(
                    f"    {r['brand']:<10} | {entry['fuel_name']:<30} | "
                    f"{entry['price']:.3f} EUR | {entry['category']}"
                )
        print("\n[dry-run] Averages that would be written to prices.json + price-history.json:")
        for fuel in FUEL_KEYS:
            valid = [
                price for r in results
                if (price := _get_standard_price(r, fuel)) is not None
            ]
            avg = round(sum(valid) / len(valid), 3) if valid else None
            print(f"  {FUEL_LABELS[fuel]}  {avg:.3f} EUR" if avg else f"  {FUEL_LABELS[fuel]}  N/A")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    station_data = build_station_prices(results, scraped_at)
    station_path = OUTPUT_DIR / "station-prices.json"
    station_path.write_text(json.dumps(station_data, indent=2))
    print(f"\n  station-prices.json written → {station_path}")

    print()
    update_prices_json(results, scraped_at)
    print(f"  prices.json updated → {OUTPUT_DIR / 'prices.json'}")

    print()
    update_price_history(results, scraped_at)
    print(f"  price-history.json updated → {OUTPUT_DIR / 'price-history.json'}")

    print(f"\n{'='*50}")
    print("Done.")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
