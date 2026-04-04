---
name: Project — Fuel Prices Latvia
description: Core project facts, stack, phase, and output staging rule for the Fuel Prices Latvia static site
type: project
---

Static Astro v5 + Tailwind v4 + DaisyUI v5 + Alpine.js website tracking diesel, petrol 95, and petrol 98 prices across Latvian fuel stations.

**Why:** Direct Claude Code collaboration project; no backend, no test suite. Output is staged in output/ before human reviews and copies to src/.

**How to apply:** Every agent instruction must target output/ as the project root. Never write to src/ directly. Current phase is Phase 9 (deployment prep). Phase 9.5 is a premium visual redesign (animations, custom cursor, reveal effects, oil rig SVG).

Key stack constraints (always enforce in agent tasks):
- No tailwind.config.mjs, no @apply, no @astrojs/tailwind
- No hardcoded hex colors — oklch() or CSS variables only
- No React/Vue/Svelte — Alpine.js only for interactivity
- No pre-release npm packages
- __dirname unavailable — use dirname(fileURLToPath(import.meta.url))
- Tailwind v4 CSS-first: all tokens in @theme block in global.css
- DaisyUI v5 loaded via @plugin "daisyui" in global.css
- data-theme="dark" on html element
- Alpine :class binding (not class:list)
- output/ IS the project root — npm install and npm run dev run from there
