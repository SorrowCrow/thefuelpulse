# CLAUDE.md

This file provides guidance to Claude Code when working on the Fuel Prices Latvia website.

## Project Overview

**Fuel Prices Latvia** — a static website tracking diesel, petrol 95, and petrol 98 prices across major fuel stations in Latvia.

- **Stack**: Astro v5 + Tailwind v4 + DaisyUI v5 + Chart.js + Alpine.js
- **Deployment**: Static hosting (Netlify/Vercel)
- **Data**: Mock JSON files (no backend, no database)
- **Workflow**: Direct Claude Code collaboration — no scripts, no orchestration layer

Requirements are in `requirements.md`. Generated output stages in `output/` before moving to `src/`.

---

## Tech Stack Rules

### Tailwind v4 (CSS-First)
- NO `tailwind.config.mjs` — does not exist in v4
- NO `@apply` directive — deprecated in v4
- NO `@astrojs/tailwind` integration
- USE `@tailwindcss/vite` plugin only
- ALL theme tokens as CSS variables under `@theme` in `global.css`
- NO hardcoded hex colors anywhere

### DaisyUI v5
- Load via `@plugin "daisyui";` in `global.css` (not in any config file)
- Use `data-theme="dark"` on `<html>` tag
- Use DaisyUI component classes: `card`, `btn`, `badge`, `stats`, `navbar`, etc.

### Astro v5
- NO React/Vue/Svelte components
- Alpine.js via `@astrojs/alpinejs` integration only
- Use `:class` binding for dynamic classes (not `class:list` with Alpine)
- `__dirname` is unavailable in ES modules — use `dirname(fileURLToPath(import.meta.url))`
- `tsconfig.json` must extend `"astro/tsconfigs/strict"` and must NOT include `jsx` or `jsxImportSource`
- Vite alias `"@"` → `"src"` in `astro.config.mjs`

### Forbidden Patterns
- `tailwind.config.mjs`
- `@apply` in any CSS
- `@astrojs/tailwind`
- Hardcoded hex colors (e.g. `#fff`, `#1a2b3c`)
- `import React from 'react'`
- Pre-release package versions (alpha/beta/rc/preview) — use stable `^x.y.z`

---

## Phase Roadmap

```
Phase 1  ✅ Project scaffold        Astro config, tsconfig, package.json, global.css
Phase 2  ✅ Mock data + BaseLayout  prices.json, news.json, BaseLayout.astro
Phase 3  ✅ PriceCard               Current price display (DaisyUI stats)
Phase 4  ✅ PriceChart              Chart.js historical price chart
Phase 5  ✅ NewsFeed                News articles list
Phase 6  ✅ Pages                   index.astro, about.astro — English only, shadcn theme
Phase 7  ✅ Real data integration   Python scraper for all 4 brands → station-prices.json + prices.json
Phase 8  ✅ All-fuel pivot          Diesel + Petrol 95 + Petrol 98; StationPrices component, updated PriceCard/Chart
Phase 9  Deployment prep            Netlify/Vercel config, final build verification
```

**Current phase: 9**

## Notes
- **Languages**: Latvian (default, `/`), English (`/en/`), Russian (`/ru/`) — expandable to more
- Translation strings in `src/i18n/{lv,en,ru}.json`. All components accept a `lang: Language` prop.
- Adding a new language: (1) add JSON file, (2) add locale to `astro.config.mjs`, (3) add `src/pages/{code}/` with thin wrapper pages
- No tests (run and gun)
- Theme: shadcn monochrome (black/white/grey) via DaisyUI v5 CSS variable overrides
- `output/` IS the project root — `npm install` and `npm run dev` run from there

---

## Output Staging

- NEVER write generated files directly to `src/`
- ALWAYS stage in `output/` first
- Human reviews output before copying to `src/`

---

## Success Criteria (Before Calling MVP Done)

- Site loads in < 2 seconds
- All pages are mobile responsive
- Chart displays price data accurately for all 3 fuel types
- Zero console errors
- Builds as a static site (`npm run build` succeeds)
- Lighthouse performance > 90
