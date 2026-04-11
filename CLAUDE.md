# CLAUDE.md

Guidance for Claude Code on Fuel Prices Latvia website.

## Project Overview

**Fuel Prices Latvia** — static site tracking diesel, petrol 95, petrol 98 prices across major Latvia fuel stations.

- **Stack**: Astro v5 + Tailwind v4 + DaisyUI v5 + Chart.js + Alpine.js
- **Deployment**: Static hosting (Netlify/Vercel)
- **Data**: JSON files in `output/src/data/` (scraper-populated)
- **Workflow**: Orchestrator → UI Designer / Developer agents

**Current project state**: see `STATUS.md` (read before starting). Requirements in `requirements.md`. Agent template in `agent-instructions-template.md`.

---

## Tech Stack Rules

### Tailwind v4 (CSS-First)
- NO `tailwind.config.mjs` — not exist in v4
- NO `@apply` — deprecated v4
- NO `@astrojs/tailwind` integration
- USE `@tailwindcss/vite` plugin only
- ALL theme tokens as CSS variables under `@theme` in `global.css`
- NO hardcoded hex colors

### DaisyUI v5
- Load via `@plugin "daisyui";` in `global.css` (not config file)
- Use `data-theme="dark"` on `<html>`
- Use DaisyUI component classes: `card`, `btn`, `badge`, `stats`, `navbar`, etc.

### Astro v5
- NO React/Vue/Svelte components
- Alpine.js via `@astrojs/alpinejs` integration only
- Use `:class` binding for dynamic classes (not `class:list` with Alpine)
- `__dirname` unavailable in ES modules — use `dirname(fileURLToPath(import.meta.url))`
- `tsconfig.json` must extend `"astro/tsconfigs/strict"`, must NOT include `jsx` or `jsxImportSource`
- Vite alias `"@"` → `"src"` in `astro.config.mjs`

### Forbidden Patterns
- `tailwind.config.mjs`
- `@apply` in any CSS
- `@astrojs/tailwind`
- Hardcoded hex colors (e.g. `#fff`, `#1a2b3c`)
- `import React from 'react'`
- Pre-release package versions (alpha/beta/rc/preview) — use stable `^x.y.z`

## Notes
- **Languages**: Latvian (default, `/`), English (`/en/`), Russian (`/ru/`) — expandable
- Translation strings in `src/i18n/{lv,en,ru}.json`. All components accept `lang: Language` prop.
- New language: (1) add JSON file, (2) add locale to `astro.config.mjs`, (3) add `src/pages/{code}/` with thin wrapper pages
- No tests (run and gun)
- Theme: shadcn monochrome (black/white/grey) via DaisyUI v5 CSS variable overrides
- `output/` IS project root — `npm install` and `npm run dev` run from there

---

## Output Staging

- NEVER write generated files directly to `src/`
- ALWAYS stage in `output/` first
- Human reviews output before copying to `src/`

---

## Agent Delegation — Mandatory

**Always delegate implementation work to specialized agents.** Never implement UI, data, or scraper changes inline.

| Task type | Agent to use |
|---|---|
| Layout, components, styling, Alpine.js | `ui-designer` |
| Data wiring, config, build, scraper | `developer` |
| New feature planning / multi-agent breakdown | `feature-architect` |
| Article / content writing | `fuel-writer` |
| Codebase exploration | `Explore` |
| Starting any new phase or feature | `orchestrator` |

Rules:
- Before any implementation task, read `STATUS.md` first
- Independent subtasks → spawn agents in parallel
- Research findings → pass to implementing agent in full brief (never re-derive)

---

## STATUS.md — Mandatory Update Rule

**Update STATUS.md at the end of EVERY task that touches the codebase.** No exceptions. Do it before the final response to the user.

After any task adding, removing, or meaningfully changing a feature, update `STATUS.md` at project root:

1. **New component or page** → add row to Components or Pages table
2. **New feature** → tick in "Features Implemented" or add to "Not Yet Implemented"
3. **New station or data field** → update Stations Tracked table
4. **Bug fix or known issue** → update Known Issues / Tech Debt section
5. **Lighthouse or performance change** → update Lighthouse Status section

One line per entry. Goal: any agent reads STATUS.md, understands full project without reading source.