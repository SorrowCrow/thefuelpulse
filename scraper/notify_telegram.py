import json
import os
import sys
from datetime import datetime

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "output", "src", "data")

PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
HISTORY_FILE = os.path.join(DATA_DIR, "price-history.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_delta(delta):
    if delta is None:
        return "—"
    if delta > 0:
        return f"▲ +{delta:.3f}"
    if delta < 0:
        return f"▼ {delta:.3f}"
    return "—"


def format_updated(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        dt_local = dt.astimezone(tz=None)
        return dt_local.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str


def find_yesterday_entry(history, today_date):
    """Return the most recent entry whose date differs from today_date, or None."""
    for entry in history:
        if entry.get("date") != today_date:
            return entry
    return None


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

    # History is newest-first: index 0 is today
    today_entry = history[0] if history else None
    today_date = today_entry.get("date") if today_entry else None
    yesterday_entry = find_yesterday_entry(history, today_date) if today_date else None

    fuel_keys = [
        ("diesel",    "Dīzelis"),
        ("petrol_95", "95E    "),
        ("petrol_98", "98E    "),
    ]

    lines = []
    for key, label in fuel_keys:
        price = averages.get(key)
        if price is None:
            continue

        delta = None
        if yesterday_entry is not None:
            yesterday_price = yesterday_entry.get(key)
            if yesterday_price is not None:
                delta = round(price - yesterday_price, 3)

        delta_str = format_delta(delta)
        lines.append(f"{label}:  <b>{price:.3f} €/l</b>  {delta_str}")

    updated_str = format_updated(last_updated) if last_updated else "—"

    message = (
        "<b>⛽ Degvielas cenas Latvijā</b>\n"
        f"<i>Atjaunots: {updated_str}</i>\n"
        "\n"
        + "\n".join(lines)
        + "\n\n🔗 thefuelpulse.com"
    )

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
