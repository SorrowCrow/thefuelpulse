# The Fuel Pulse — Project Status

> **Agents: read before any task. Update relevant section when done.**
> Last updated: 2026-04-11

---

## Live Site
- URL: https://thefuelpulse.com
- Hosting: Netlify/Vercel (static)
- Data updates: GitHub Actions scraper (`.github/workflows/update-data.yml`)

---

## Tech Stack
| Layer | Choice |
|---|---|
| Framework | Astro v5 (SSG, `output/` is project root) |
| Styling | Tailwind v4 CSS-first + DaisyUI v5 |
| Interactivity | Alpine.js via `@astrojs/alpinejs` |
| Charts | Chart.js v4 (CDN, `defer` + preload) |
| Language | TypeScript |

---

## Languages
| Code | Route | Status |
|---|---|---|
| `lv` | `/` (default) | Active |
| `en` | `/en/` | Active |
| `ru` | `/ru/` | Active |

Translation strings: `output/src/i18n/{lv,en,ru}.json`

---

## Pages
| Page | LV | EN | RU | Content component |
|---|---|---|---|---|
| Home | `/` | `/en/` | `/ru/` | `HomePageContent.astro` |
| Articles index | `/articles/` | `/en/articles/` | `/ru/articles/` | `NewsPageContent.astro` |
| Article detail | `/articles/[slug]` | `/en/articles/[slug]` | `/ru/articles/[slug]` | Astro content collections |
| In-depth | `/in-depth/` | `/en/in-depth/` | `/ru/in-depth/` | `InDepthPageContent.astro` |
| About | `/about/` | `/en/about/` | `/ru/about/` | `AboutPageContent.astro` |
| Contact | `/contact/` | `/en/contact/` | `/ru/contact/` | `ContactPageContent.astro` |
| Privacy | `/privacy/` | `/en/privacy/` | `/ru/privacy/` | `PrivacyPageContent.astro` |
| Game | `/game/` | — | — | inline (minimal) |

---

## Components (`output/src/components/`)
| File | Purpose |
|---|---|
| `Header.astro` | Nav + theme toggle + lang switcher |
| `Footer.astro` | Links, mailto contacts (3 emails), Telegram channel button |
| `LanguageSwitcher.astro` | LV / EN / RU switcher |
| `ToggleButton.astro` | Light/dark toggle (localStorage) |
| `PriceCard.astro` | Current price per fuel type + change delta |
| `PriceChart.astro` | Market avg price history + 7-day forecast bands |
| `StationPriceChart.astro` | Per-station history chart (all 5 stations, fuel tabs) |
| `StationPrices.astro` | Current prices table per station |
| `CheapestFuelWidget.astro` | Badge: cheapest station per fuel type |
| `FuelRecommendation.astro` | Recommendation card from `fuel-recommendation.json` |
| `FuelSavingsCalculator.astro` | Interactive savings calculator (Alpine.js) |
| `NewsFeed.astro` | Article card grid |
| `CollapsibleSection.astro` | Accordion/collapsible wrapper |

---

## Data Files (`output/src/data/`)
| File | Updated by | Content |
|---|---|---|
| `prices.json` | Scraper (GH Actions) | Market averages (diesel, 95, 98) + `last_updated` |
| `station-prices.json` | Scraper (GH Actions) | Per-station fuel entries with `scraped_at` |
| `price-history.json` | Scraper (GH Actions) | Daily price history per station |
| `news.json` | Manual / scraper | Processed article metadata |
| `news-raw.json` | Scraper | Raw articles pre-processing |
| `fuel-recommendation.json` | Manual / scraper | Recommendation card data |

---

## Stations Tracked
| Key | Brand | Fuel types |
|---|---|---|
| `virsi` | Virši | diesel, petrol_95, petrol_98, cng, lpg, adblue |
| `circlek` | Circle K | petrol_95, petrol_98, diesel, premium_diesel, xtl, lpg |
| `neste` | Neste | petrol_95, petrol_98, diesel, premium_diesel, hvo |
| `viada` | Viada | petrol_95, petrol_95_premium, petrol_98, diesel, diesel_ecto, lpg, e85 |
| `kool` | Kool | petrol_95, petrol_98, diesel, premium_diesel |

Chart note: Viada renders two series — `viada` (DUS diesel) and `viada_adus` (ADUS diesel_ecto).
Petrol tabs: single Viada series only (ADUS and DUS share same petrol price).

---

## Features Implemented
- [x] Multi-language (lv/en/ru) with hreflang + self-referential canonical per language
- [x] Dark/light theme with localStorage persistence
- [x] Price cards with change delta (vs previous day)
- [x] Market average chart (Chart.js) — diesel/95/98 tabs, 7d/30d/custom range
- [x] 7-day forecast bands on price chart (hidden on today when actuals arrive)
- [x] Per-station price history chart — all 5 stations, fuel type tabs
- [x] Station price comparison table (current prices)
- [x] Cheapest fuel widget
- [x] Fuel savings calculator (Alpine.js, interactive)
- [x] Fuel recommendation card
- [x] Articles (Astro content collections, markdown, categories)
- [x] In-depth analysis page
- [x] Reveal animations (IntersectionObserver, respects prefers-reduced-motion)
- [x] Background blobs + oil rig SVG decoration
- [x] SEO: canonical (self-per-lang), hreflang (lv/en/ru/x-default), OG, Twitter meta
- [x] Google Fonts Inter (non-blocking: print-media swap + preload)
- [x] Google AdSense (async)
- [x] Service worker (prod only)
- [x] Python scraper — 5 brands, runs via GitHub Actions
- [x] Price history persisted in JSON
- [x] Telegram channel CTA — footer button + home page alert banner (https://t.me/thefuelpulse, i18n lv/en/ru)

## GitHub Actions
| Workflow | Trigger | Purpose |
|---|---|---|
| `update-data.yml` | Schedule | Runs scraper, commits updated JSON data |
| `weekly-recap.yml` | Schedule | Weekly recap post (partial) |

---

## Key Utility Files
| File | Purpose |
|---|---|
| `src/i18n/utils.ts` | `t()`, `getCanonicalPath()`, `localePath()`, `getLangFromUrl()` |
| `src/layouts/BaseLayout.astro` | HTML shell: head tags, fonts, chart.js, header, footer |
| `src/utils/chartHelpers.ts` | Shared Chart.js tooltip + scale configs |
| `src/utils/chartColors.ts` | Palette constants |
| `src/utils/priceHelpers.ts` | Price formatting helpers |
| `src/utils/stationHelpers.ts` | Station data helpers |
| `src/utils/dateHelpers.ts` | `formatShortDate()` etc. |
| `src/scripts/alpineRangeFilter.ts` | Reusable Alpine mixin for date range filter |
| `src/middleware.ts` | Redirect middleware |
| `src/types/index.ts` | Shared TypeScript types |
| `scraper/scrape_prices.py` | Python scraper (requests + bs4, 5 brands) |

---

## Known Issues / Tech Debt
- Cloudflare email obfuscation adds ~1 KB `email-decode.min.js` (3 mailto links in Footer/Contact/About — low impact, Cloudflare-side)
- AdSense script cannot defer (Google requirement)

---

## Lighthouse Status (2026-04-11)
- SEO: Canonical fixed to self-referential per language (was pointing to lv hreflang)
- Perf: Google Fonts non-blocking (print-media swap + preload)
- Perf: chart.js now `defer` + head preload hint
- Perf: chart.js pinned to `@4` (7d CDN cache — pin exact version for 1-yr cache)