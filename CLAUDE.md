# CLAUDE.md

This file provides guidance to Claude Code when working on the Fuel Prices Latvia website.

## Project Overview

**Fuel Prices Latvia** — a static website tracking diesel, petrol 95, and petrol 98 prices across major fuel stations in Latvia.

- **Stack**: Astro v5 + Tailwind v4 + DaisyUI v5 + Chart.js + Alpine.js
- **Deployment**: Static hosting (Netlify/Vercel)
- **Data**: JSON files in `output/src/data/` (scraper-populated)
- **Workflow**: Orchestrator → UI Designer / Developer agents

**Current project state**: see `STATUS.md` (always read this before starting work).
Requirements are in `requirements.md`. Agent instruction template in `agent-instructions-template.md`.

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
