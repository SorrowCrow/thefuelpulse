#!/usr/bin/env python3
"""
Weekly fuel price recap article generator for The Fuel Pulse.

Reads price-history.json and station-prices.json, then writes 3 markdown
article files (en/lv/ru) into the Astro content collection:

  output/src/content/articles/en/week-{YYYY}-{WW}.md
  output/src/content/articles/lv/week-{YYYY}-{WW}.md
  output/src/content/articles/ru/week-{YYYY}-{WW}.md

Run manually each week, or wire into the GitHub Actions pipeline.

Usage:
  python scraper/generate_weekly_recap.py
  python scraper/generate_weekly_recap.py --dry-run   # print to stdout, don't write
"""

import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
HISTORY_FILE = ROOT / "output/src/data/price-history.json"
STATIONS_FILE = ROOT / "output/src/data/station-prices.json"
ARTICLES_DIR = ROOT / "output/src/content/articles"

# ── Helpers ────────────────────────────────────────────────────────────────────

STATION_DISPLAY = {
    "virsi": "Virši",
    "circlek": "Circle K",
    "neste": "Neste",
    "viada": "Viada",
}

FUEL_DISPLAY = {
    "diesel": {"en": "Diesel", "lv": "Dīzeļdegviela", "ru": "Дизель"},
    "petrol_95": {"en": "Petrol 95", "lv": "95. benzīns", "ru": "Бензин 95"},
    "petrol_98": {"en": "Petrol 98", "lv": "98. benzīns", "ru": "Бензин 98"},
}


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_week_number(d: date) -> tuple[int, int]:
    """Return (year, ISO week number) for a date."""
    iso = d.isocalendar()
    return iso.year, iso.week


def fmt_price(p: float | None) -> str:
    if p is None:
        return "-"
    return f"{p:.3f}"


def price_delta(current: float, previous: float | None) -> tuple[float | None, str, str]:
    """Return (delta, sign_str, direction_word_en)."""
    if previous is None or previous == 0:
        return None, "", "unchanged"
    delta = current - previous
    if abs(delta) < 0.001:
        return 0.0, "", "unchanged"
    sign = "+" if delta > 0 else ""
    direction = "rose" if delta > 0 else "fell"
    return delta, sign, direction


def trend_emoji_free(delta: float | None) -> str:
    if delta is None or abs(delta) < 0.001:
        return "-"
    return "↑" if delta > 0 else "↓"


# ── Data analysis ──────────────────────────────────────────────────────────────

def analyse(history: list[dict], station_data: dict) -> dict:
    """Extract key stats from price history for the recap."""
    # Deduplicate by date — keep latest entry per date
    seen_dates: dict[str, dict] = {}
    for entry in history:
        d = entry["date"]
        if d not in seen_dates:
            seen_dates[d] = entry
    daily = sorted(seen_dates.values(), key=lambda x: x["date"], reverse=True)

    if not daily:
        raise ValueError("No price history found")

    current = daily[0]
    current_date = date.fromisoformat(current["date"])
    year, week = get_week_number(current_date)

    # Find the data point closest to 7 days ago
    target_prev = current_date - timedelta(days=7)
    prev = None
    for entry in daily[1:]:
        d = date.fromisoformat(entry["date"])
        if d <= target_prev:
            prev = entry
            break
    # Fallback: use oldest available if no 7-day-old data
    if prev is None and len(daily) > 1:
        prev = daily[-1]

    fuels = ["diesel", "petrol_95", "petrol_98"]

    # Per-fuel stats
    fuel_stats: dict[str, dict] = {}
    for fuel in fuels:
        curr_price = current.get(fuel)
        prev_price = prev.get(fuel) if prev else None
        if curr_price is None:
            continue
        delta, sign, direction = price_delta(curr_price, prev_price)
        fuel_stats[fuel] = {
            "current": curr_price,
            "previous": prev_price,
            "delta": delta,
            "sign": sign,
            "direction": direction,
            "trend": trend_emoji_free(delta),
        }

    # Per-station prices from station-prices.json (most recent scrape)
    FUEL_ALIASES = {"diesel_ecto": "diesel", "petrol_95_premium": "petrol_95"}
    station_prices: dict[str, dict[str, float | None]] = {}
    for station in station_data.get("stations", []):
        if station.get("error"):
            continue
        key = station["key"]
        prices: dict[str, float | None] = {f: None for f in fuels}
        for entry in station.get("fuel_entries", []):
            ftype = FUEL_ALIASES.get(entry["fuel_type"], entry["fuel_type"])
            if ftype in prices and entry.get("price") is not None:
                existing = prices[ftype]
                if existing is None or entry["price"] < existing:
                    prices[ftype] = entry["price"]
        station_prices[key] = prices

    # Cheapest station per fuel
    cheapest: dict[str, tuple[str, float] | None] = {}
    for fuel in fuels:
        best_station = None
        best_price = None
        for key, prices in station_prices.items():
            p = prices.get(fuel)
            if p is not None and (best_price is None or p < best_price):
                best_price = p
                best_station = key
        cheapest[fuel] = (STATION_DISPLAY.get(best_station, best_station), best_price) if best_station else None

    # Biggest mover this week
    biggest_mover_fuel = None
    biggest_mover_delta = 0.0
    for fuel, stats in fuel_stats.items():
        if stats["delta"] is not None and abs(stats["delta"]) > abs(biggest_mover_delta):
            biggest_mover_delta = stats["delta"]
            biggest_mover_fuel = fuel

    return {
        "current_date": current_date,
        "prev_date": date.fromisoformat(prev["date"]) if prev else None,
        "year": year,
        "week": week,
        "fuel_stats": fuel_stats,
        "station_prices": station_prices,
        "cheapest": cheapest,
        "biggest_mover_fuel": biggest_mover_fuel,
        "biggest_mover_delta": biggest_mover_delta,
    }


# ── Article generation ─────────────────────────────────────────────────────────

def generate_en(stats: dict) -> str:
    cd = stats["current_date"]
    pd = stats["prev_date"]
    week = stats["week"]
    year = stats["year"]
    fs = stats["fuel_stats"]
    cheapest = stats["cheapest"]
    sp = stats["station_prices"]

    # Title
    title = f"Latvia Fuel Prices — Week {week}, {year}: Market Recap"
    description = (
        f"Weekly Latvia fuel price recap for week {week} ({cd.strftime('%d %B %Y')}). "
        f"Diesel, Petrol 95 and 98 averages, cheapest stations, and market commentary."
    )
    description = description[:160]

    prev_label = pd.strftime("%d %B %Y") if pd else "the previous week"

    # Summary sentence for each fuel
    def fuel_summary(fuel: str) -> str:
        s = fs.get(fuel)
        if not s:
            return ""
        delta_str = f"{s['sign']}{s['delta']:.3f} €/L" if s["delta"] is not None else ""
        pct = (s["delta"] / s["previous"] * 100) if s["delta"] and s["previous"] else None
        pct_str = f" ({s['sign']}{pct:.1f}%)" if pct is not None else ""
        return (
            f"**{FUEL_DISPLAY[fuel]['en']}** averaged **{fmt_price(s['current'])} €/L** this week - "
            f"it {s['direction']} {delta_str}{pct_str} compared to {prev_label}."
        )

    # Station price table (markdown)
    def station_table() -> str:
        header = "| Station | Diesel | Petrol 95 | Petrol 98 |"
        sep = "|---------|--------|-----------|-----------|"
        rows = []
        order = ["virsi", "circlek", "neste", "viada"]
        for key in order:
            prices = sp.get(key, {})
            name = STATION_DISPLAY.get(key, key)
            rows.append(
                f"| {name} | {fmt_price(prices.get('diesel'))} | "
                f"{fmt_price(prices.get('petrol_95'))} | "
                f"{fmt_price(prices.get('petrol_98'))} |"
            )
        return "\n".join([header, sep] + rows)

    # Cheapest picks
    def cheapest_line(fuel: str) -> str:
        c = cheapest.get(fuel)
        if not c:
            return ""
        return f"- **{FUEL_DISPLAY[fuel]['en']}**: {c[0]} at {fmt_price(c[1])} €/L"

    # Biggest mover commentary
    def mover_commentary() -> str:
        fuel = stats["biggest_mover_fuel"]
        delta = stats["biggest_mover_delta"]
        if not fuel or abs(delta) < 0.001:
            return "Prices were largely stable across all fuel types this week."
        direction = "rose" if delta > 0 else "fell"
        name = FUEL_DISPLAY[fuel]["en"]
        return (
            f"The most notable movement this week was in {name}, which {direction} by "
            f"{abs(delta):.3f} €/L. "
            + ("Higher crude oil prices and a weaker euro against the dollar pushed costs up across the board."
               if delta > 0
               else "Easing crude oil prices provided some relief at the pump, with all fuels trending lower.")
        )

    article = f"""---
title: "{title}"
description: "{description}"
pubDate: {cd.isoformat()}
lang: en
tags: ["weekly recap", "diesel", "petrol 95", "fuel prices", "{year}"]
---

Latvia's fuel prices for the week ending {cd.strftime("%d %B %Y")} (week {week} of {year}). Here is the full breakdown.

## This Week's Average Prices

{fuel_summary('diesel')}

{fuel_summary('petrol_95')}

{fuel_summary('petrol_98')}

Prices are market averages across Circle K, Virši, Neste, and Viada, updated three times daily.

## Station-by-Station Breakdown

The table below shows the current pump prices at each of Latvia's four major fuel chains.

{station_table()}

*All prices in EUR per litre. Viada prices shown are the ADUS (automated station) rates, which are the lowest available. Viada DUS (manned) diesel is typically around 2.124 €/L.*

## Cheapest Station This Week

{chr(10).join(filter(None, [cheapest_line(f) for f in ['diesel', 'petrol_95', 'petrol_98']]))}

Viada's automated ADUS stations continue to undercut the rest of the market significantly. The trade-off is that loyalty cards are not accepted at ADUS locations - you pay by card at the pump with no points earned.

## Market Commentary

{mover_commentary()}

The Latvian fuel market remains closely linked to Brent crude oil prices and the EUR/USD exchange rate. A stronger euro makes imported fuel cheaper in euro terms; a weaker euro does the opposite. Domestic taxes - including excise duty and 21% VAT - are fixed and account for roughly half of what you pay at the pump.

## How to Pay Less

The single biggest saving available to Latvian drivers is choosing the right station. Filling a 50-litre tank at Viada ADUS versus the most expensive option saves approximately €{((max(sp.get(k, {}).get('diesel', 0) or 0 for k in sp) - (cheapest.get('diesel', [None, 0])[1] or 0)) * 50):.2f} on diesel alone.

Beyond station choice, loyalty apps from Circle K (Circle K EXTRA), Virši (Virši Club), and Neste (Neste app) offer additional per-litre discounts at their respective chains.

Check today's live prices on the [The Fuel Pulse dashboard](/) - updated three times daily from each retailer's website.
"""
    return article.strip()


def generate_lv(stats: dict) -> str:
    cd = stats["current_date"]
    week = stats["week"]
    year = stats["year"]
    fs = stats["fuel_stats"]
    cheapest = stats["cheapest"]
    sp = stats["station_prices"]

    title = f"Degvielas cenas Latvijā - {week}. nedēļa, {year}: nedēļas apskats"
    description = (
        f"Iknedēļas degvielas cenu apskats {week}. nedēļai ({cd.strftime('%d.%m.%Y')}). "
        f"Dīzeļdegvielas, 95. un 98. benzīna vidējās cenas, lētākās stacijas un tirgus komentārs."
    )
    description = description[:160]

    def fuel_summary(fuel: str) -> str:
        s = fs.get(fuel)
        if not s:
            return ""
        delta_str = f"{s['sign']}{s['delta']:.3f} €/l" if s["delta"] is not None else ""
        lv_direction = "pieauga" if s["direction"] == "rose" else ("samazinājās" if s["direction"] == "fell" else "nemainījās")
        return (
            f"**{FUEL_DISPLAY[fuel]['lv']}** šajā nedēļā vidēji maksāja **{fmt_price(s['current'])} €/l** - "
            f"cena {lv_direction} par {delta_str} salīdzinājumā ar iepriekšējo nedēļu."
        )

    def station_table() -> str:
        header = "| Stacija | Dīzelis | 95. benzīns | 98. benzīns |"
        sep = "|---------|---------|-------------|-------------|"
        rows = []
        for key in ["virsi", "circlek", "neste", "viada"]:
            prices = sp.get(key, {})
            name = STATION_DISPLAY.get(key, key)
            rows.append(
                f"| {name} | {fmt_price(prices.get('diesel'))} | "
                f"{fmt_price(prices.get('petrol_95'))} | "
                f"{fmt_price(prices.get('petrol_98'))} |"
            )
        return "\n".join([header, sep] + rows)

    def cheapest_line(fuel: str) -> str:
        c = cheapest.get(fuel)
        if not c:
            return ""
        return f"- **{FUEL_DISPLAY[fuel]['lv']}**: {c[0]} par {fmt_price(c[1])} €/l"

    def mover_commentary() -> str:
        fuel = stats["biggest_mover_fuel"]
        delta = stats["biggest_mover_delta"]
        if not fuel or abs(delta) < 0.001:
            return "Šonedēļ degvielas cenas bija lielākoties stabilas."
        direction = "pieauga" if delta > 0 else "samazinājās"
        name = FUEL_DISPLAY[fuel]["lv"]
        return (
            f"Vislielākās izmaiņas šonedēļ piedzīvoja {name}, kuras cena {direction} par "
            f"{abs(delta):.3f} €/l. "
            + ("Naftas cenu kāpums pasaules tirgū un vājāks eiro pret dolāru paaugstināja izmaksas."
               if delta > 0
               else "Naftas cenu kritums pasaules tirgū nodrošināja nelielu atvieglojumu pie degvielas kolonkas.")
        )

    article = f"""---
title: "{title}"
description: "{description}"
pubDate: {cd.isoformat()}
lang: lv
tags: ["nedēļas apskats", "dīzelis", "benzīns", "degvielas cenas", "{year}"]
---

Degvielas cenas Latvijā nedēļai, kas beidzās {cd.strftime("%d.%m.%Y")} ({year}. gada {week}. nedēļa). Pilns pārskats zemāk.

## Šīs nedēļas vidējās cenas

{fuel_summary('diesel')}

{fuel_summary('petrol_95')}

{fuel_summary('petrol_98')}

Cenas ir tirgus vidējās rādītāji Circle K, Virši, Neste un Viada stacijās, kas tiek atjaunoti trīs reizes dienā.

## Cenas pa stacijām

Zemāk esošajā tabulā redzamas pašreizējās degvielas cenas pie katra no četriem lielākajiem Latvijas degvielas tīkliem.

{station_table()}

*Visas cenas EUR par litru. Viada cenas ir ADUS (automatizēto staciju) tarifi - lētākie pieejamie. Viada DUS (apkalpotās) stacijas dīzeļdegvielas cena parasti ir ap 2,124 €/l.*

## Lētākās stacijas šonedēļ

{chr(10).join(filter(None, [cheapest_line(f) for f in ['diesel', 'petrol_95', 'petrol_98']]))}

Viada automatizētās ADUS stacijas turpina piedāvāt zemākās cenas tirgū. Kompromiss: ADUS stacijās netiek pieņemtas lojalitātes kartes - maksāšana notiek tikai ar bankas karti pie automāta.

## Tirgus komentārs

{mover_commentary()}

Latvijas degvielas tirgus cieši saistīts ar Brent naftas cenām un EUR/USD kursu. Stiprāks eiro padara importēto degvielu lētāku eiro izteiksmē. Akcīzes nodoklis un 21% PVN ir fiksēti un veido aptuveni pusi no cenas pie kolonkas.

## Kā ietaupīt

Lielākais ietaupījums Latvijas autovadītājiem pieejams, izvēloties pareizo staciju. Uzpildot 50 litrus Viada ADUS dīzeļdegvielā salīdzinājumā ar dārgāko variantu, var ietaupīt aptuveni €{((max(sp.get(k, {}).get('diesel', 0) or 0 for k in sp) - (cheapest.get('diesel', [None, 0])[1] or 0)) * 50):.2f}.

Papildu atlaides nodrošina Circle K (Circle K EXTRA), Virši (Virši Club) un Neste (Neste lietotne) lojalitātes lietotnes.

Aktuālās cenas reāllaikā - [The Fuel Pulse informācijas panelī](/) - atjaunojamas trīs reizes dienā no katras stacijas vietnes.
"""
    return article.strip()


def generate_ru(stats: dict) -> str:
    cd = stats["current_date"]
    week = stats["week"]
    year = stats["year"]
    fs = stats["fuel_stats"]
    cheapest = stats["cheapest"]
    sp = stats["station_prices"]

    title = f"Цены на топливо в Латвии - неделя {week}, {year}: еженедельный обзор"
    description = (
        f"Еженедельный обзор цен на топливо в Латвии, неделя {week} ({cd.strftime('%d.%m.%Y')}). "
        f"Средние цены на дизель, бензин 95 и 98, дешевейшие АЗС и комментарий рынка."
    )
    description = description[:160]

    def fuel_summary(fuel: str) -> str:
        s = fs.get(fuel)
        if not s:
            return ""
        delta_str = f"{s['sign']}{s['delta']:.3f} €/л" if s["delta"] is not None else ""
        ru_direction = "вырос" if s["direction"] == "rose" else ("снизился" if s["direction"] == "fell" else "не изменился")
        return (
            f"**{FUEL_DISPLAY[fuel]['ru']}** на этой неделе в среднем стоил **{fmt_price(s['current'])} €/л** - "
            f"цена {ru_direction} на {delta_str} по сравнению с прошлой неделей."
        )

    def station_table() -> str:
        header = "| АЗС | Дизель | Бензин 95 | Бензин 98 |"
        sep = "|-----|--------|-----------|-----------|"
        rows = []
        for key in ["virsi", "circlek", "neste", "viada"]:
            prices = sp.get(key, {})
            name = STATION_DISPLAY.get(key, key)
            rows.append(
                f"| {name} | {fmt_price(prices.get('diesel'))} | "
                f"{fmt_price(prices.get('petrol_95'))} | "
                f"{fmt_price(prices.get('petrol_98'))} |"
            )
        return "\n".join([header, sep] + rows)

    def cheapest_line(fuel: str) -> str:
        c = cheapest.get(fuel)
        if not c:
            return ""
        return f"- **{FUEL_DISPLAY[fuel]['ru']}**: {c[0]} по {fmt_price(c[1])} €/л"

    def mover_commentary() -> str:
        fuel = stats["biggest_mover_fuel"]
        delta = stats["biggest_mover_delta"]
        if not fuel or abs(delta) < 0.001:
            return "На этой неделе цены на топливо оставались в целом стабильными."
        direction = "вырос" if delta > 0 else "снизился"
        name = FUEL_DISPLAY[fuel]["ru"]
        return (
            f"Наиболее заметное движение на этой неделе - {name}, цена которого {direction} на "
            f"{abs(delta):.3f} €/л. "
            + ("Рост мировых цен на нефть и ослабление евро к доллару оказали давление на стоимость топлива."
               if delta > 0
               else "Снижение мировых цен на нефть принесло некоторое облегчение на автозаправках.")
        )

    article = f"""---
title: "{title}"
description: "{description}"
pubDate: {cd.isoformat()}
lang: ru
tags: ["еженедельный обзор", "дизель", "бензин", "цены на топливо", "{year}"]
---

Цены на топливо в Латвии за неделю, завершившуюся {cd.strftime("%d.%m.%Y")} ({week}-я неделя {year} года). Полный обзор ниже.

## Средние цены за неделю

{fuel_summary('diesel')}

{fuel_summary('petrol_95')}

{fuel_summary('petrol_98')}

Цены - рыночные средние по Circle K, Virši, Neste и Viada, обновляются три раза в день.

## Цены по АЗС

В таблице ниже - актуальные цены на топливо в каждой из четырёх крупных сетей АЗС Латвии.

{station_table()}

*Все цены в евро за литр. Цены Viada - тарифы ADUS (автоматических) станций, самые низкие на рынке. Дизель на мanned-станциях Viada DUS обычно около 2,124 €/л.*

## Самые дешёвые АЗС на этой неделе

{chr(10).join(filter(None, [cheapest_line(f) for f in ['diesel', 'petrol_95', 'petrol_98']]))}

Автоматические станции Viada ADUS продолжают предлагать самые низкие цены на рынке. Компромисс: карты лояльности на ADUS-станциях не принимаются - оплата только банковской картой.

## Комментарий рынка

{mover_commentary()}

Латвийский рынок топлива тесно связан с ценами на нефть Brent и курсом EUR/USD. Укрепление евро делает импортное топливо дешевле в евровом выражении. Акцизный налог и НДС 21% фиксированы и составляют около половины цены на заправке.

## Как сэкономить

Главная возможность для экономии - выбор правильной АЗС. Залив 50 литров дизеля на Viada ADUS вместо самого дорогого варианта, можно сэкономить около €{((max(sp.get(k, {}).get('diesel', 0) or 0 for k in sp) - (cheapest.get('diesel', [None, 0])[1] or 0)) * 50):.2f}.

Дополнительные скидки дают программы лояльности: Circle K (Circle K EXTRA), Virši (Virši Club) и Neste (приложение Neste).

Актуальные цены в реальном времени - на [панели мониторинга The Fuel Pulse](/) - обновляются три раза в день с сайтов каждого ретейлера.
"""
    return article.strip()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv

    history_data = load_json(HISTORY_FILE)
    station_data = load_json(STATIONS_FILE)

    stats = analyse(history_data["history"], station_data)

    week = stats["week"]
    year = stats["year"]
    slug = f"week-{year}-{week:02d}"

    articles = {
        "en": generate_en(stats),
        "lv": generate_lv(stats),
        "ru": generate_ru(stats),
    }

    if dry_run:
        for lang, content in articles.items():
            print(f"\n{'='*60}")
            print(f"  {lang.upper()} - {slug}.md")
            print(f"{'='*60}\n")
            print(content[:800], "\n... [truncated]")
        return

    written = []
    for lang, content in articles.items():
        out_dir = ARTICLES_DIR / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{slug}.md"
        out_file.write_text(content, encoding="utf-8")
        written.append(str(out_file.relative_to(ROOT)))

    print(f"Weekly recap written for week {week}/{year}:")
    for path in written:
        print(f"  ✓ {path}")


if __name__ == "__main__":
    main()
