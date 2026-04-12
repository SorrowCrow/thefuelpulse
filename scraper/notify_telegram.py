import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "output", "src", "data")

PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
HISTORY_FILE = os.path.join(DATA_DIR, "price-history.json")

STATION_NAMES = {
    "virsi": "Virši",
    "circlek": "Circle K",
    "neste": "Neste",
    "viada": "Viada DUS",
    "kool": "Kool",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_delta(delta):
    """Return signed delta in parens, or empty string if negligible."""
    if delta is None or abs(delta) < 0.001:
        return ""
    sign = "+" if delta > 0 else ""
    return f" ({sign}{delta:.3f})"


def format_updated(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        dt_local = dt.astimezone(ZoneInfo("Europe/Riga"))
        return dt_local.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str


def find_prev_entry(history, today_date, days_back=1):
    """Return the most recent entry whose date differs from today_date."""
    seen_different = 0
    for entry in history:
        if entry.get("date") != today_date:
            seen_different += 1
            if seen_different >= days_back:
                return entry
    return None


def find_week_entry(history, today_date):
    """Return entry closest to 7 days ago."""
    for entry in reversed(history):
        if entry.get("date") < today_date:
            return entry
    return None


def cheapest_stations(stations_dict, fuel_key):
    """Return (station_display_name, price) for the cheapest station for given fuel.

    When fuel_key is 'diesel', also checks each station's 'diesel_ecto' key.
    If diesel_ecto at viada is cheaper, the display name becomes 'Viada ADUS'.
    """
    best_name, best_price = None, None
    for key, fuels in stations_dict.items():
        price = fuels.get(fuel_key)
        display_name = STATION_NAMES.get(key, key.capitalize())

        # For diesel: also consider diesel_ecto (Viada ADUS discount diesel)
        if fuel_key == "diesel" and key == "viada":
            ecto_price = fuels.get("diesel_ecto")
            if ecto_price is not None:
                if price is None or ecto_price < price:
                    price = ecto_price
                    display_name = "Viada ADUS"

        if price is None:
            continue
        if best_price is None or price < best_price:
            best_price = price
            best_name = display_name
    return best_name, best_price


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping notification.")
        sys.exit(0)

    prices_data = load_json(PRICES_FILE)
    history_data = load_json(HISTORY_FILE)

    averages = prices_data["averages"]
    last_updated = prices_data.get("last_updated", "")

    history = history_data.get("history", [])
    today_entry = history[0] if history else None
    today_date = today_entry.get("date") if today_entry else None
    yesterday_entry = find_prev_entry(history, today_date) if today_date else None
    week_entry = find_week_entry(history, today_date) if today_date else None

    fuel_keys = [
        ("diesel",    "Dīzelis"),
        ("petrol_95", "95E    "),
        ("petrol_98", "98E    "),
    ]

    # --- Price lines with trend ---
    price_lines = []
    for key, label in fuel_keys:
        price = averages.get(key)
        if price is None:
            continue

        delta = None
        if yesterday_entry is not None:
            prev = yesterday_entry.get(key)
            if prev is not None:
                delta = round(price - prev, 3)

        delta_str = format_delta(delta)
        price_lines.append(f"{label}:  <b>{price:.3f} €</b>{delta_str}")

    # --- Week-over-week summary ---
    week_lines = []
    if week_entry is not None:
        for key, label in fuel_keys:
            price = averages.get(key)
            week_price = week_entry.get(key)
            if price is None or week_price is None:
                continue
            week_delta = round(price - week_price, 3)
            if abs(week_delta) >= 0.001:
                sign = "+" if week_delta > 0 else ""
                week_lines.append(f"  {label.strip()}: ({sign}{week_delta:.3f})")

    # --- Cheapest station per fuel ---
    today_stations = today_entry.get("stations", {}) if today_entry else {}
    cheapest_lines = []
    cheapest_fuel_keys = [
        ("diesel",    "Dīzelis"),
        ("petrol_95", "95E"),
        ("petrol_98", "98E"),
    ]
    for key, label in cheapest_fuel_keys:
        name, price = cheapest_stations(today_stations, key)
        if name and price:
            cheapest_lines.append(f"  • {label}: <b>{name}</b> — {price:.3f} €")

    # --- Assemble message ---
    updated_str = format_updated(last_updated) if last_updated else "—"

    parts = [
        f"<b>⛽ Degvielas cenas Latvijā</b>",
        f"<i>{updated_str}</i>",
        "",
        "\n".join(price_lines),
    ]

    if week_lines:
        parts += ["", "📅 <i>7 dienu izmaiņas:</i>"] + week_lines

    if cheapest_lines:
        parts += ["", "💰 <b>Lētākā šodien:</b>"] + cheapest_lines

    parts += ["", "🔗 thefuelpulse.com"]

    message = "\n".join(parts)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    response = requests.post(url, json=payload, timeout=15)

    if not response.ok:
        print(f"Telegram API error {response.status_code}:")
        print(response.text)
        sys.exit(1)

    print("Telegram notification sent.")
    sys.exit(0)


if __name__ == "__main__":
    main()
