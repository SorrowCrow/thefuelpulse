#!/usr/bin/env python3
"""
AI-powered fuel buy/wait recommendation generator using Google Gemini.

Reads:  output/src/data/news-raw.json
        output/src/data/prices.json
        output/src/data/price-history.json
Writes: output/src/data/fuel-recommendation.json

Requires: GEMINI_API_KEY in .env or environment.

Usage:
  python scraper/generate_recommendation.py
  python scraper/generate_recommendation.py --dry-run   # print prompt, skip API call
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

def _load_env(path: Path) -> None:
    """Minimal .env loader — no external dependencies required."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

_load_env(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "output" / "src" / "data"
DRY_RUN  = "--dry-run" in sys.argv

FUEL_LABELS = {"diesel": "Diesel", "petrol_95": "Petrol 95", "petrol_98": "Petrol 98"}
MODEL_NAME  = "gemini-2.5-flash"

_NEUTRAL_FUEL = {"recommendation": "neutral", "confidence": "low", "summary": "Recommendation not yet generated."}

NEUTRAL_SEED = {
    "diesel":          _NEUTRAL_FUEL,
    "petrol_95":       _NEUTRAL_FUEL,
    "petrol_98":       _NEUTRAL_FUEL,
    "factors":         ["No price trend data analysed yet", "No news context loaded yet"],
    "analysis":        "",
    "sources":         [],
    "generated_at":    datetime.now(timezone.utc).isoformat(),
    "prices_snapshot": {"diesel": None, "petrol_95": None, "petrol_98": None},
}


# ── Data helpers ────────────────────────────────────────────────────────────────

def load(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def get_unique_day_history(raw: list[dict], max_days: int = 7) -> list[dict]:
    """Average multiple polls per day, return newest-first, capped at max_days."""
    buckets: dict[str, dict[str, list]] = defaultdict(
        lambda: {"diesel": [], "petrol_95": [], "petrol_98": []}
    )
    for entry in raw:
        d = entry.get("date", "")
        if not d:
            continue
        for fuel in ("diesel", "petrol_95", "petrol_98"):
            v = entry.get(fuel)
            if v is not None:
                buckets[d][fuel].append(v)

    def avg(lst: list) -> float | None:
        return round(sum(lst) / len(lst), 3) if lst else None

    days = sorted(buckets.keys(), reverse=True)[:max_days]
    return [{"date": d, **{f: avg(buckets[d][f]) for f in ("diesel", "petrol_95", "petrol_98")}}
            for d in days]


def compute_trend(history: list[dict], fuel: str) -> tuple[str, float]:
    """(rising|falling|stable, absolute_change) over available history."""
    vals = [e.get(fuel) for e in history if e.get(fuel) is not None]
    if len(vals) < 2:
        return "stable", 0.0
    change = vals[0] - vals[-1]   # newest - oldest
    pct = change / vals[-1] * 100 if vals[-1] else 0
    if pct > 0.5:
        return "rising", change
    if pct < -0.5:
        return "falling", change
    return "stable", change


# ── Prompt ──────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a fuel price analyst for Latvia. Your job is to give drivers a clear, \
actionable recommendation for each fuel type: should they fill up today, or wait?

Consider BOTH local Latvian price trends AND global factors: crude oil (Brent/WTI), \
OPEC output decisions, geopolitical events (Russia, Iran, Middle East), EU energy policy, \
and refinery capacity news. Global movements typically flow into Latvian retail prices \
within 1-2 weeks, so forward-looking signals matter.

Respond ONLY with a valid JSON object matching this schema exactly:
{
  "diesel":    {"recommendation": "buy"|"wait"|"neutral", "confidence": "high"|"medium"|"low", "summary": "<max 120 chars>"},
  "petrol_95": {"recommendation": "buy"|"wait"|"neutral", "confidence": "high"|"medium"|"low", "summary": "<max 120 chars>"},
  "petrol_98": {"recommendation": "buy"|"wait"|"neutral", "confidence": "high"|"medium"|"low", "summary": "<max 120 chars>"},
  "factors": ["<reason 1>", "<reason 2>", "<reason 3>"],
  "analysis": "<2-3 paragraphs of plain-text analysis citing specific prices, global events, and news>"
}

Rules:
- "buy"     = prices are at a local low or likely to rise — fill up now
- "wait"    = prices are likely to fall — delay if practical
- "neutral" = insufficient signal or prices stable — timing does not matter much
- diesel and petrol can differ (e.g. diesel often tracks crude more closely)
- factors must cite actual figures or headlines from the input data
- analysis must reference both local Latvia trends AND any relevant global signals
- analysis must NOT invent data not present in the context below
- Return ONLY the JSON object, no markdown, no explanation outside it\
"""


def build_user_message(averages: dict, history: list[dict], articles: list[dict]) -> str:
    # Prices + trend
    price_lines = []
    for fuel in ("diesel", "petrol_95", "petrol_98"):
        trend, change = compute_trend(history, fuel)
        val = averages.get(fuel)
        if val is not None:
            price_lines.append(
                f"  {FUEL_LABELS[fuel]:<10}: {val:.3f} EUR/L  ({trend}, {change:+.3f} EUR over {len(history)} days)"
            )
        else:
            price_lines.append(f"  {FUEL_LABELS[fuel]:<10}: N/A")
    prices_block = "CURRENT FUEL PRICES IN LATVIA:\n" + "\n".join(price_lines)

    # History table
    if history:
        rows = [
            f"  {e['date']}  D:{e.get('diesel') or '?'}  P95:{e.get('petrol_95') or '?'}  P98:{e.get('petrol_98') or '?'}"
            for e in history
        ]
        history_block = f"PRICE HISTORY (last {len(history)} days, newest first):\n" + "\n".join(rows)
    else:
        history_block = "PRICE HISTORY: No data yet."

    # News
    if articles:
        lines = []
        for i, a in enumerate(articles, 1):
            pub  = a.get("published_at", "")[:10] or "?"
            desc = a.get("description", "")[:200]
            lines.append(f"  [{i}] [{pub}] {a['title']}\n       {desc}\n       Source: {a['source']}")
        news_block = f"RECENT NEWS ({len(articles)} articles):\n\n" + "\n\n".join(lines)
    else:
        news_block = "RECENT NEWS: No fuel news found today."

    return "\n\n".join([prices_block, history_block, news_block,
                        "Provide your recommendation as JSON."])


# ── Main ────────────────────────────────────────────────────────────────────────

def write_seed() -> None:
    out = DATA_DIR / "fuel-recommendation.json"
    if not out.exists():
        out.write_text(json.dumps(NEUTRAL_SEED, indent=2, ensure_ascii=False))


def main() -> None:
    print(f"\n{'='*50}")
    print("Fuel Recommendation Generator  (Gemini)")
    print(f"{'='*50}\n")

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not DRY_RUN and not api_key:
        print("  ⚠️  GEMINI_API_KEY not set in .env or environment.")
        print("  Add it to .env and re-run.\n")
        write_seed()
        sys.exit(0)

    prices_data  = load(DATA_DIR / "prices.json")
    history_data = load(DATA_DIR / "price-history.json")
    news_data    = load(DATA_DIR / "news-raw.json")

    averages = prices_data.get("averages", {})
    history  = get_unique_day_history(history_data.get("history", []), max_days=7)
    articles = news_data.get("articles", [])

    print(f"  Prices:   {'✅' if averages else '⚠️  missing'}")
    print(f"  History:  {len(history)} days")
    print(f"  Articles: {len(articles)}")

    user_message = build_user_message(averages, history, articles)

    if DRY_RUN:
        print("\n[dry-run] System prompt:\n")
        print(SYSTEM_PROMPT)
        print("\n[dry-run] User message:\n")
        print(user_message)
        return

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    print(f"\n  Calling {MODEL_NAME}...")
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            max_output_tokens=4096,
            temperature=0.3,
        ),
    )
    raw = response.text.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Strip markdown fences if model ignored the mime type hint
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"  ❌ Could not parse response: {e}")
            print(f"     Raw: {raw[:300]}")
            write_seed()
            sys.exit(0)

    # Validate required fields
    valid_vals = ("buy", "wait", "neutral")
    for fuel_key in ("diesel", "petrol_95", "petrol_98"):
        if result.get(fuel_key, {}).get("recommendation") not in valid_vals:
            print(f"  ❌ Unexpected recommendation for {fuel_key}: {result.get(fuel_key)}")
            write_seed()
            sys.exit(0)

    def fuel_block(key: str) -> dict:
        fb = result.get(key, {})
        return {
            "recommendation": fb.get("recommendation", "neutral"),
            "confidence":     fb.get("confidence", "low"),
            "summary":        fb.get("summary", ""),
        }

    output = {
        "diesel":          fuel_block("diesel"),
        "petrol_95":       fuel_block("petrol_95"),
        "petrol_98":       fuel_block("petrol_98"),
        "factors":         result.get("factors", []),
        "analysis":        result.get("analysis", ""),
        "sources":         [
            {"title": a["title"], "url": a["url"], "published_at": a.get("published_at", "")}
            for a in articles[:5]
        ],
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "prices_snapshot": {
            "diesel":    averages.get("diesel"),
            "petrol_95": averages.get("petrol_95"),
            "petrol_98": averages.get("petrol_98"),
        },
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "fuel-recommendation.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False)
    )

    for fk, fl in FUEL_LABELS.items():
        fb = output[fk]
        print(f"  ✅ {fl}: {fb['recommendation'].upper()} ({fb['confidence']}) — {fb['summary'][:80]}")
    print(f"  ✅ Written → {DATA_DIR / 'fuel-recommendation.json'}")
    print(f"\n{'='*50}\nDone.\n{'='*50}\n")


if __name__ == "__main__":
    main()
