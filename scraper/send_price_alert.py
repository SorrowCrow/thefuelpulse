"""
send_price_alert.py — Fuel Prices Latvia

Reads current and previous fuel prices, checks for meaningful changes,
then sends per-language batch email alerts to confirmed subscribers via Resend.
"""

import json
import os
import sys
from datetime import date

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_DATA_DIR = os.path.join(_REPO_ROOT, "output", "src", "data")
_PRICES_PATH = os.path.join(_DATA_DIR, "prices.json")
_HISTORY_PATH = os.path.join(_DATA_DIR, "price-history.json")

PRICE_KEYS = ["diesel", "petrol_95", "petrol_98"]

# ---------------------------------------------------------------------------
# Env vars
# ---------------------------------------------------------------------------
SUPABASE_PROJECT_URL = os.environ.get("SUPABASE_PROJECT_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

_missing = [
    name
    for name, val in [
        ("SUPABASE_PROJECT_URL", SUPABASE_PROJECT_URL),
        ("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY),
        ("RESEND_API_KEY", RESEND_API_KEY),
    ]
    if not val
]
if _missing:
    print(f"Warning: missing env vars: {', '.join(_missing)}. Skipping alert.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
with open(_PRICES_PATH, "r", encoding="utf-8") as fh:
    prices_data = json.load(fh)

with open(_HISTORY_PATH, "r", encoding="utf-8") as fh:
    history_data = json.load(fh)

averages: dict = prices_data["averages"]
history: list = history_data["history"]  # newest first

# ---------------------------------------------------------------------------
# Compute deltas
# ---------------------------------------------------------------------------
today_str = str(date.today())

# Today's entry (may differ from averages if run mid-day, but we trust averages)
# "Yesterday" = most recent history entry whose date differs from today
yesterday_entry = None
for entry in history:
    if entry.get("date") != today_str:
        yesterday_entry = entry
        break

deltas: dict[str, float | None] = {}
for key in PRICE_KEYS:
    current = averages.get(key)
    if yesterday_entry is not None and current is not None:
        prev = yesterday_entry.get(key)
        deltas[key] = round(current - prev, 4) if prev is not None else None
    else:
        deltas[key] = None

# ---------------------------------------------------------------------------
# Check if any price changed by > 0.001 EUR
# ---------------------------------------------------------------------------
any_change = any(d is not None and abs(d) > 0.001 for d in deltas.values())
if not any_change:
    print("No price change, skipping email alert.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Delta format helper
# ---------------------------------------------------------------------------
def fmt_delta(d: float | None) -> str:
    if d is None:
        return "—"
    if d > 0:
        return f" +{d:.3f}"
    if d < 0:
        return f" {d:.3f}"
    return f"  {d:.3f}"

# ---------------------------------------------------------------------------
# Fetch confirmed subscribers from Supabase
# ---------------------------------------------------------------------------
supabase_headers = {
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Content-Type": "application/json",
}

resp = requests.get(
    f"{SUPABASE_PROJECT_URL}/rest/v1/subscribers"
    "?confirmed_at=not.is.null"
    "&select=email,token,language",
    headers=supabase_headers,
    timeout=15,
)
resp.raise_for_status()
subscribers: list[dict] = resp.json()

if not subscribers:
    print("No confirmed subscribers. Skipping email alert.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Group by language
# ---------------------------------------------------------------------------
by_lang: dict[str, list[dict]] = {}
for sub in subscribers:
    lang = sub.get("language") or "lv"
    by_lang.setdefault(lang, []).append(sub)

# ---------------------------------------------------------------------------
# Email body builders
# ---------------------------------------------------------------------------
diesel_price = averages.get("diesel", 0.0)
p95_price = averages.get("petrol_95", 0.0)
p98_price = averages.get("petrol_98", 0.0)

diesel_delta = fmt_delta(deltas.get("diesel"))
p95_delta = fmt_delta(deltas.get("petrol_95"))
p98_delta = fmt_delta(deltas.get("petrol_98"))


def build_email(lang: str, subscriber: dict) -> dict:
    token = subscriber.get("token", "")
    email = subscriber["email"]

    if lang == "lv":
        subject = "Degvielas cenu izmaiņas — The Fuel Pulse"
        body = (
            "Jaunākās degvielas cenas Latvijā:\n"
            "\n"
            f"Dīzelis: {diesel_price:.3f} € ({diesel_delta})\n"
            f"95E:     {p95_price:.3f} € ({p95_delta})\n"
            f"98E:     {p98_price:.3f} € ({p98_delta})\n"
            "\n"
            "Skatīt detaļas: https://thefuelpulse.com\n"
            "\n"
            f"Atteikties no saņemšanas: https://thefuelpulse.com/unsubscribe?token={token}\n"
        )
    elif lang == "en":
        subject = "Fuel price update — The Fuel Pulse"
        body = (
            "Latest fuel prices in Latvia:\n"
            "\n"
            f"Diesel:  {diesel_price:.3f} € ({diesel_delta})\n"
            f"95E:     {p95_price:.3f} € ({p95_delta})\n"
            f"98E:     {p98_price:.3f} € ({p98_delta})\n"
            "\n"
            "View details: https://thefuelpulse.com/en/\n"
            "\n"
            f"Unsubscribe: https://thefuelpulse.com/unsubscribe?token={token}\n"
        )
    elif lang == "ru":
        subject = "Обновление цен на топливо — The Fuel Pulse"
        body = (
            "Актуальные цены на топливо в Латвии:\n"
            "\n"
            f"Дизель:  {diesel_price:.3f} € ({diesel_delta})\n"
            f"95E:     {p95_price:.3f} € ({p95_delta})\n"
            f"98E:     {p98_price:.3f} € ({p98_delta})\n"
            "\n"
            "Подробнее: https://thefuelpulse.com/ru/\n"
            "\n"
            f"Отписаться: https://thefuelpulse.com/unsubscribe?token={token}\n"
        )
    else:
        # Fallback to English for unknown languages
        subject = "Fuel price update — The Fuel Pulse"
        body = (
            "Latest fuel prices in Latvia:\n"
            "\n"
            f"Diesel:  {diesel_price:.3f} € ({diesel_delta})\n"
            f"95E:     {p95_price:.3f} € ({p95_delta})\n"
            f"98E:     {p98_price:.3f} € ({p98_delta})\n"
            "\n"
            "View details: https://thefuelpulse.com/en/\n"
            "\n"
            f"Unsubscribe: https://thefuelpulse.com/unsubscribe?token={token}\n"
        )

    return {
        "from": "The Fuel Pulse <noreply@thefuelpulse.com>",
        "to": [email],
        "subject": subject,
        "text": body,
    }

# ---------------------------------------------------------------------------
# Build full list of email objects
# ---------------------------------------------------------------------------
email_objects: list[dict] = []
for lang, subs in by_lang.items():
    for sub in subs:
        email_objects.append(build_email(lang, sub))

# ---------------------------------------------------------------------------
# Send via Resend batch API (max 100 per request)
# ---------------------------------------------------------------------------
RESEND_BATCH_URL = "https://api.resend.com/emails/batch"
RESEND_HEADERS = {
    "Authorization": f"Bearer {RESEND_API_KEY}",
    "Content-Type": "application/json",
}
BATCH_SIZE = 100

total_sent = 0

for i in range(0, len(email_objects), BATCH_SIZE):
    chunk = email_objects[i : i + BATCH_SIZE]
    r = requests.post(
        RESEND_BATCH_URL,
        headers=RESEND_HEADERS,
        json=chunk,
        timeout=30,
    )
    if not r.ok:
        print(f"Resend API error {r.status_code}: {r.text}")
        sys.exit(1)
    total_sent += len(chunk)

print(f"Sent {total_sent} email(s) to {len(subscribers)} subscriber(s).")
sys.exit(0)
