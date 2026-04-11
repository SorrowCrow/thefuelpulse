---
name: Project — Notification System (Telegram + Email)
description: Architecture decisions for the Fuel Prices Latvia notification system — Telegram bot via GH Actions, email via Resend + Supabase, Netlify Functions for form handling
type: project
---

Decided 2026-04-11. Notifications are a new subsystem sitting outside the static Astro site.

**Architecture chosen:**
- Telegram: Python script in scraper/ directory, triggered as an additional step in update-data.yml GH Actions workflow. Reads prices.json and price-history.json. Secret: TELEGRAM_BOT_TOKEN + TELEGRAM_CHANNEL_ID in GitHub Secrets.
- Email: Resend for transactional sends (free tier 3k/mo), Supabase for subscriber storage (free tier, Postgres). Netlify Function handles subscribe/unsubscribe form POSTs. No other backend required.
- GDPR: consent checkbox on subscribe form, unsubscribe token in every email, privacy page already exists at /privacy/.

**Why:** Simplest stack that reuses existing GitHub Actions infrastructure. No new hosting required. Resend + Supabase are both free-tier friendly and have good Node SDKs.

**How to apply:** Telegram task is purely a scraper/ + .github/workflows/ concern (no Astro changes). Email task requires: one Netlify Function, one Astro component (subscribe form), and a Supabase table. GDPR requires privacy page update and unsubscribe route.

**Key file boundaries:**
- Telegram: scraper/notify_telegram.py (new), .github/workflows/update-data.yml (add step)
- Email subscribe form: output/src/components/EmailSubscribeForm.astro (new)
- Netlify function: netlify/functions/subscribe.ts (new), netlify/functions/unsubscribe.ts (new)
- Email send script: scraper/send_price_alert.py (new), triggered from GH Actions
- Supabase table: subscribers(id, email, token, confirmed_at, created_at, language)
- Privacy page: output/src/components/PrivacyPageContent.astro (add email data section)
