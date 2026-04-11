# Diesel Price News Website - MVP Requirements

## Project Goal
Create a simple, informative website that tracks and displays diesel fuel price movements in Latvia.

## Target Audience
- Latvian drivers and fleet managers
- People interested in fuel price trends
- Bilingual audience (Latvian and English speakers)

## Core Features (MVP)

### 1. Homepage
- Display current diesel price prominently
- Show price change from previous day (up/down indicator)
- Display last update timestamp
- Language switcher (LV/EN)

### 2. Price History
- Visual chart showing last 7 days of diesel prices
- Simple line chart using Chart.js
- Show min/max prices in the period
- Data points should be hoverable

### 3. News Feed
- List of 5-10 recent price-related news items
- Each item: title, date, brief summary
- News about factors affecting diesel prices (taxes, global oil, etc.)

### 4. About Page
- Explanation of data sources
- Update frequency information
- Contact information

## Technical Requirements

### Tech Stack
- **Framework**: Astro v5 (static site generation)
- **Styling**: Tailwind CSS v4
- **Charts**: Chart.js
- **Deployment**: Static hosting ready (Netlify/Vercel)

### Data Source (MVP)
- **Mock data** stored in JSON files (static)
- Structure: `src/data/prices.json` and `src/data/news.json`
- Real API integration is out of scope for MVP

### Design Requirements
- Mobile-first responsive design
- Clean, readable typography
- Fast loading (Lighthouse score > 90)
- Accessible (WCAG 2.1 AA compliance)

### Bilingual Support
- All UI text in both Latvian and English
- Language toggle in header
- URL structure: `/` (LV default) and `/en/` (English)
- All content duplicated in both languages

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

- Real-time price API integration
- User authentication
- Price alerts/notifications
- Historical data beyond 7 days
- Admin panel for content management
- Comments section
- Social media integration
- Price predictions/analytics

## Success Criteria

- ✅ Site loads in < 2 seconds
- ✅ All pages are mobile responsive
- ✅ Language switcher works correctly
- ✅ Chart displays price data accurately
- ✅ No console errors
- ✅ Can be deployed as static site
- ✅ Code is clean and well-structured
- ✅ All content available in both languages

## Constraints

- Use Astro v5 features (no older patterns)
- Tailwind v4 CSS-first approach (no @apply directives)
- No external CSS frameworks besides Tailwind
- All data must be mockable (no hard API dependencies)
- Keep bundle size minimal (< 100KB initial JS)
