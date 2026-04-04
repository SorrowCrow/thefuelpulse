---
name: Feedback — Agent Instruction Style
description: How to format and scope agent task instructions for the Fuel Prices Latvia project
type: feedback
---

Agent instructions must be self-contained enough that the coding agent can execute without re-reading the codebase. Include exact CSS keyframes, JS snippets, and Astro markup where the content is non-trivial or easily gotten wrong.

**Why:** The user explicitly asked for instructions that include "exact CSS keyframes, JS snippets, and Astro markup where critical." Vague instructions cause agents to guess and introduce bugs.

**How to apply:** For every task that involves animation keyframes, Alpine.js script blocks, or SVG markup — embed the exact code in the instruction. For structural/class changes to existing markup, quote the existing text and show the replacement exactly. Always include the full existing surrounding context for edits so the agent can locate the insertion point unambiguously.
