# Diesel Price News Website - MVP Requirements

## Project Goal
Latvia diesel price tracker website.

## Target Audience
- Latvian drivers, fleet managers
- Fuel price trend watchers
- LV/EN bilingual users

## Core Features (MVP)

### 1. Homepage
- Current diesel price prominent
- Price change from prev day (up/down)
- Last update timestamp
- LV/EN switcher

### 2. Price History
- 7-day price chart (Chart.js line)
- Min/max display
- Hoverable data points

### 3. News Feed
- 5-10 recent price news items
- Each: title, date, brief summary
- Covers taxes, global oil factors

### 4. About Page
- Data sources
- Update frequency
- Contact info

## Technical Requirements

### Tech Stack
- **Framework**: Astro v5 (static site generation)
- **Styling**: Tailwind CSS v4
- **Charts**: Chart.js
- **Deployment**: Static hosting ready (Netlify/Vercel)

### Data Source (MVP)
- **Mock data** in JSON files (static)
- `src/data/prices.json` and `src/data/news.json`
- Real API out of scope

### Design Requirements
- Mobile-first responsive
- Clean typography
- Lighthouse > 90
- WCAG 2.1 AA

### Bilingual Support
- All UI text LV + EN
- Header language toggle
- `/` (LV default), `/en/` (English)
- Content duplicated both languages

## Content Structure

### Price Data Format
```json
{
  "current_price": 1.65,
  "currency": "EUR",
  "unit": "liter",
  "last_updated": "2026-03-28T10:00:00Z",
  "history": [
    {"date": "2026-03-28", "price": 1.65},
    {"date": "2026-03-27", "price": 1.63}
  ]
}
```

### News Data Format
```json
{
  "articles": [
    {
      "id": 1,
      "title_lv": "Dīzeļdegvielas cenas pieaug",
      "title_en": "Diesel prices increase",
      "summary_lv": "Cenas pieauga par 2 centiem...",
      "summary_en": "Prices increased by 2 cents...",
      "date": "2026-03-28",
      "category": "price_change"
    }
  ]
}
```

## Pages to Generate

1. `src/pages/index.astro` - Homepage (LV)
2. `src/pages/en/index.astro` - Homepage (EN)
3. `src/pages/about.astro` - About page (LV)
4. `src/pages/en/about.astro` - About page (EN)
5. `src/components/PriceCard.astro` - Current price display
6. `src/components/PriceChart.astro` - Historical chart
7. `src/components/NewsFeed.astro` - News list
8. `src/components/LanguageSwitcher.astro` - Language toggle
9. `src/layouts/BaseLayout.astro` - Base layout with header/footer
10. `src/data/prices.json` - Mock price data
11. `src/data/news.json` - Mock news articles

## Out of Scope (Future Phases)

- Real-time API, auth, alerts, history >7 days
- Admin panel, comments, social, predictions

## Success Criteria

- ✅ Load < 2s
- ✅ Mobile responsive
- ✅ Language switcher works
- ✅ Chart accurate
- ✅ No console errors
- ✅ Static deployable
- ✅ Clean code
- ✅ Both languages complete

## Constraints

- Astro v5 only (no old patterns)
- Tailwind v4 CSS-first (no `@apply`)
- No other CSS frameworks
- All data mockable (no hard API deps)
- Bundle < 100KB initial JS