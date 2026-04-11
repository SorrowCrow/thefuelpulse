# Agent Instructions Template — Fuel Prices Latvia

This file is used by the prompt creation agent (Claude Code) to generate precise, self-contained feature instructions for sub-agents working on separate features of this project. Read this before writing any agent prompt.

---

## How to Use This File

When the user asks for a new feature or phase, use the sections below to compose a complete agent prompt. Each agent prompt must be **fully self-contained** — the agent receiving it has no memory of prior conversations.

### Checklist Before Issuing a Prompt

- [ ] Tech stack constraints included (see "Mandatory Boilerplate" below)
- [ ] Exact file paths given (relative to `output/` which is the project root)
- [ ] Output staging rule stated explicitly
- [ ] Data shape described or referenced
- [ ] Success criteria defined
- [ ] Forbidden patterns listed
- [ ] No ambiguous instructions ("make it nice" → specify what that means)

---

## Project Snapshot (as of Phase 8 complete)

### Location
- **Project root**: `/Users/user/repos/agentsCollab/output/`
- **Run commands from**: `output/` (e.g. `cd output && npm run dev`)

### Existing Source Files
```
output/src/
  components/
    Footer.astro
    Header.astro
    NewsFeed.astro
    PriceCard.astro          # DaisyUI stats — shows diesel/95/98 prices
    PriceChart.astro         # Chart.js line chart — 3 fuel types
    StationPrices.astro      # Per-brand price table
  data/
    news.json
    price-history.json
    prices.json              # Aggregated current prices (all 3 fuel types)
    station-prices.json      # Per-brand scraped prices (Virši, Circle K, Neste, Viada)
  layouts/
    BaseLayout.astro
  pages/
    index.astro
    about.astro
  styles/
    global.css               # Tailwind v4 + DaisyUI v5 theme
  types/
    index.ts
  utils/
    dateHelpers.ts
    priceHelpers.ts
  i18n/
    utils.ts
```

### Data Shapes

**`station-prices.json`**
```json
{
  "scraped_at": "2026-03-28T21:09:13.129009+00:00",
  "stations": [
    {
      "brand": "Virši",
      "key": "virsi",
      "prices": { "diesel": 2.117, "petrol_95": 1.979, "petrol_98": 2.149 },
      "currency": "EUR",
      "error": null
    }
  ]
}
```

**`prices.json`** — aggregated market prices
```json
{
  "diesel": { "current": 2.12, "previous": 2.10, "last_updated": "..." },
  "petrol_95": { "current": 1.99, "previous": 1.97, "last_updated": "..." },
  "petrol_98": { "current": 2.16, "previous": 2.14, "last_updated": "..." }
}
```

**`price-history.json`** — 7-day history per fuel type
```json
{
  "diesel": [{ "date": "2026-03-28", "price": 2.12 }, ...],
  "petrol_95": [...],
  "petrol_98": [...]
}
```

---

## Mandatory Boilerplate (always include in every agent prompt)

```
### Tech Stack Rules — MUST follow exactly

**Tailwind v4**
- No `tailwind.config.mjs` — it does not exist
- No `@apply` directive — deprecated
- No `@astrojs/tailwind` integration
- Use `@tailwindcss/vite` plugin
- Theme tokens as CSS variables under `@theme` in global.css
- No hardcoded hex colors — use oklch() or CSS variables

**DaisyUI v5**
- Loaded via `@plugin "daisyui";` in global.css
- Theme is `data-theme="dark"` on `<html>`
- Use DaisyUI component classes: card, btn, badge, stats, navbar, etc.

**Astro v5**
- No React/Vue/Svelte components
- Alpine.js only — via `@astrojs/alpinejs` integration
- Use `:class` binding (not `class:list`) with Alpine
- Use `dirname(fileURLToPath(import.meta.url))` instead of `__dirname`
- tsconfig.json must extend `"astro/tsconfigs/strict"`, no jsx fields
- Vite alias `"@"` → `"src"` in astro.config.mjs

**Forbidden**
- `tailwind.config.mjs`
- `@apply` in any CSS
- `@astrojs/tailwind`
- Hardcoded hex colors (`#fff`, `#1a2b3c`, etc.)
- `import React from 'react'`
- Pre-release package versions (alpha/beta/rc/preview)
```

---

## Output Staging Rule (always include)

```
**IMPORTANT**: Stage ALL new or modified files under `output/` (the project root).
Do NOT write directly to `src/`. The human will review output before it goes live.
The project root IS `output/` — paths like `output/src/components/Foo.astro` are correct.
```

---

## Theme Reference (always include for UI work)

```
Theme: shadcn monochrome — black/white/grey only, no accent colors.

CSS variable palette (from global.css):
- base-100: oklch(9.5% 0 0)      — card surface
- base-200: oklch(14.5% 0 0)     — elevated elements
- base-300: oklch(28% 0 0)       — borders
- base-content: oklch(97.8% 0 0) — primary text
- primary: oklch(97.8% 0 0)      — white
- secondary: oklch(63% 0 0)      — grey
- success: oklch(64.8% 0.15 143.4)
- error: oklch(62% 0.2 15.4)
- warning: oklch(74.4% 0.15 66.1)
- rounded-box / rounded-btn / rounded-badge: 0.375rem (sharp corners)
```

---

## Prompt Structure Template

Use this skeleton when writing a new agent prompt:

```markdown
# Feature: [Feature Name]

## Context
You are working on **Fuel Prices Latvia** — a static Astro v5 website tracking diesel, petrol 95, and petrol 98 prices across major fuel stations in Latvia.

Project root: `/Users/user/repos/agentsCollab/output/`
Run dev server: `cd /Users/user/repos/agentsCollab/output && npm run dev`

### Existing files relevant to this task
[list only the files the agent needs to read]

### Data available
[describe exactly which JSON files and their shapes]

## Task
[Precise, unambiguous description of what to build]

### Requirements
1. [Specific requirement]
2. [Specific requirement]
...

### Do NOT
- [Anti-pattern or scope boundary]
- [Anti-pattern or scope boundary]

## Output
Stage all files under `output/`. List every file to create or modify:
- `output/src/components/Foo.astro` — [what it does]
- `output/src/pages/bar.astro` — [what it does]

## Success Criteria
- [ ] [Measurable outcome]
- [ ] [Measurable outcome]
- [ ] Zero console errors
- [ ] `npm run build` succeeds in `output/`

---

[INSERT MANDATORY BOILERPLATE HERE]
[INSERT OUTPUT STAGING RULE HERE]
[INSERT THEME REFERENCE HERE IF UI WORK]
```

---

## Common Feature Patterns

### Adding a new page
- Create `output/src/pages/[name].astro`
- Import `BaseLayout` from `@/layouts/BaseLayout.astro`
- Use `data-theme="dark"` is already on `<html>` via BaseLayout — do not add it again
- Page title passed as `<BaseLayout title="...">` prop

### Adding a new component
- Create `output/src/components/[Name].astro`
- Read `station-prices.json` or `prices.json` using `Astro.glob` or `fs` with `fileURLToPath`
- Use DaisyUI classes for layout (card, stats, table, etc.)
- Interactive parts (tabs, toggles) use Alpine.js — no inline `<script>` with framework imports

### Modifying the scraper
- Scraper lives at `/Users/user/repos/agentsCollab/scraper/scrape_prices.py`
- Writes output to `output/src/data/station-prices.json` and `output/src/data/prices.json`
- Python 3, uses `requests` and `beautifulsoup4`
- Do not add new dependencies without noting them

### Deployment / config changes
- Config file: `output/astro.config.mjs`
- Netlify: `output/netlify.toml` (create if needed)
- Vercel: `output/vercel.json` (create if needed)
- Static adapter: `@astrojs/netlify` or `@astrojs/vercel` (stable versions only)

---

## Scope Guards

Always include these in prompts to prevent agents from going out of scope:

```
- Do NOT refactor existing components unless directly required by the task
- Do NOT add bilingual/i18n support — English only
- Do NOT add authentication, APIs, or backend services
- Do NOT install pre-release packages
- Do NOT add tests
- Do NOT modify global.css theme colors unless the task explicitly requires it
```

---

## Example: Fully Composed Agent Prompt (Phase 9 — Deployment Prep)

```markdown
# Feature: Deployment Prep (Phase 9)

## Context
You are working on **Fuel Prices Latvia** — a static Astro v5 website.
Project root: `/Users/user/repos/agentsCollab/output/`

### Relevant existing files
- `output/astro.config.mjs` — current Astro config (read before modifying)
- `output/package.json` — current dependencies
- `output/src/pages/index.astro`, `output/src/pages/about.astro`

## Task
Prepare the site for static deployment on Netlify. Add a Netlify config and verify the static build works.

### Requirements
1. Add `@astrojs/netlify` adapter (stable version) to `astro.config.mjs`
2. Create `output/netlify.toml` with build command `npm run build`, publish dir `dist`
3. Ensure `output/astro.config.mjs` sets `output: 'static'`
4. Verify `npm run build` completes without errors by reading any build error output

### Do NOT
- Modify any component or page files
- Change theme or styling
- Add redirects unless required for static output

## Output
- `output/astro.config.mjs` — updated with static adapter
- `output/netlify.toml` — new file

## Success Criteria
- [ ] `npm run build` exits 0 in `output/`
- [ ] `output/dist/` contains `index.html` and `about/index.html`
- [ ] No console errors during build

---

**Tech Stack Rules — MUST follow exactly**
[... insert mandatory boilerplate ...]

**Output Staging Rule**
[... insert staging rule ...]
```
