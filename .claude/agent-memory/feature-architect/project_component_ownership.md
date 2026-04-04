---
name: Component Ownership Map
description: Which Astro components own which data files and Alpine.js state in Fuel Prices Latvia
type: project
---

Data ownership as of Phase 9:

- PriceCard.astro — reads prices.json (averages, currency, last_updated) and price-history.json (history[1] for prev). Displays DaisyUI stats component. Price values are in stat-value elements with class text-primary.
- PriceChart.astro — reads price-history.json (full history reversed oldest-first) and prices.json (currency). Alpine x-data owns: chart (Chart.js instance), range ('7d'|'30d'|'custom'), fromDate, toDate. Chart.js loaded via CDN script tag at bottom of file (is:inline). Min/max stat values displayed with x-text.
- StationPrices.astro — reads station-prices.json. Alpine x-data owns: fuel ('diesel'|'petrol_95'|'petrol_98'), data (full tableData object serialized at build time), deltaText(), deltaClass(). Fuel selector uses tab buttons with :class binding. Station rows rendered with x-for template.
- NewsFeed.astro — reads news.json; slices to 5 articles; no Alpine state. Each article is a card bg-base-200 inside a space-y-4 div.
- Header.astro — static; navbar with mobile dropdown and desktop horizontal menu. No Alpine state currently.
- BaseLayout.astro — wraps all pages; imports Header, Footer, global.css; main tag has container mx-auto p-4 md:p-8.

**Why:** Knowing exact data sources and Alpine state boundaries prevents agent tasks from accidentally duplicating state or misidentifying where to add attributes.

**How to apply:** When writing instructions that touch data display (tabular numbers, price values), reference the exact element classes listed above. When adding Alpine state, note which x-data block it belongs to.
