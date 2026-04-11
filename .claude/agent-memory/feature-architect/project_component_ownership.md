---
name: Component Ownership Map
description: Which Astro components own which data files and Alpine.js state in Fuel Prices Latvia
type: project
---

Data ownership as of Phase 9:

- PriceCard.astro — reads prices.json (averages, currency, last_updated) and price-history.json (history[1] for prev). Displays DaisyUI stats component. Price values are in stat-value elements with class text-primary.
- PriceChart.astro — reads price-history.json (full history reversed oldest-first) and prices.json (currency). Alpine x-data owns: chart (Chart.js instance), range ('7d'|'30d'|'custom'), fromDate, toDate. Chart.js loaded via CDN script tag at bottom of file (is:inline). Min/max stat values displayed with x-text.
- StationPrices.astro — reads station-prices.json. Alpine x-data owns: fuel ('diesel'|'petrol_95'|'petrol_98'|'specialty'), data (full tableData object serialized at build time), deltaText(), deltaClass(). Fuel selector uses tab buttons with :class binding. Station rows rendered with x-for template. As of Phase 9 overhaul, station-prices.json uses fuel_entries[] per station (FuelEntry objects) rather than a flat prices{} map. Viada diesel appears as two rows (ADUS/DUS). Specialty tab groups by station.
- PriceCard.astro — reads prices.json (averages, currency, last_updated) and price-history.json. Displays DaisyUI stats for diesel/petrol_95/petrol_98. As of Phase 9 overhaul, also reads station-prices.json to show a horizontally scrollable row of premium/specialty fuel cards below the main stats. stat-value elements carry class text-primary.
- NewsFeed.astro — reads news.json; slices to 5 articles; no Alpine state. Each article is a card bg-base-200 inside a space-y-4 div.
- Header.astro — static; navbar with mobile dropdown and desktop horizontal menu. No Alpine state currently.
- BaseLayout.astro — wraps all pages; imports Header, Footer, global.css; main tag has container mx-auto p-4 md:p-8.
- CheapestFuelWidget.astro — reads station-prices.json; owns FUEL_ALIASES + fuel_entries normalization loop (duplicated in HomePageContent and FuelSavingsCalculator).
- FuelSavingsCalculator.astro — reads station-prices.json + prices.json; owns FUEL_ALIASES + normalization (slightly different output shape: flat {brand, diesel, petrol_95, petrol_98} per station).
- HomePageContent.astro — reads station-prices.json; third copy of FUEL_ALIASES + normalization (adds displayLabels per key).
- FuelRecommendation.astro — reads fuel-recommendation.json; contains 3 collapsible sections using pattern: x-data `open:false` + ToggleButton + x-show + x-transition.
- StationPriceChart.astro — reads price-history.json (station breakdown); owns STATIONS color/config array; Alpine range filter (near-identical to PriceChart).

## Known Duplication (Phase 9 refactor targets)
- FUEL_ALIASES + normalization loop: CheapestFuelWidget (lines 12-25), FuelSavingsCalculator (lines 13-28), HomePageContent (lines 24-44)
- Alpine collapsible pattern: FuelRecommendation lines 124-138 (factors), 141-164 (sources), 167-182 (analysis)
- Chart.js tooltip config object: PriceChart lines 283-295, StationPriceChart lines 161-173 (identical keys, slight label callback difference)
- Chart.js scale config: PriceChart lines 297-314, StationPriceChart lines 175-193 (x scale identical, y grid color differs slightly)
- Fuel color RGBA strings: diesel rgba(100,116,139,x), p95 rgba(110,231,183,x), p98 rgba(252,129,129,x) — appear in PriceChart legend HTML + dataset borderColor + pointBackgroundColor + gradient stops = 6+ occurrences; StationPriceChart uses different per-station colors
- Alpine range filter (range, fromDate, toDate, filteredData, setRange): PriceChart lines 112-150, StationPriceChart lines 89-115

**Why:** Knowing exact data sources and Alpine state boundaries prevents agent tasks from accidentally duplicating state or misidentifying where to add attributes.

**How to apply:** When writing instructions that touch data display (tabular numbers, price values), reference the exact element classes listed above. When adding Alpine state, note which x-data block it belongs to.
