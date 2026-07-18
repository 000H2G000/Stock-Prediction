# Phase 2 — External Real-Time Data (Free Sources Only)

## Goal
Pull real, live external signals that plausibly move pharma demand — all from free sources: what people are searching for, the weather, known calendar events, and health-related news.

## Free sources used and why

| Signal | Source | Cost | Why this one |
|---|---|---|---|
| Search trends | Google Trends (via the `pytrends` library) | Free, no key needed | Search interest for terms like "flu symptoms" or "allergy medicine" often rises *before* people actually buy — an early signal |
| Weather | OpenWeatherMap API | Free tier | Heatwaves and cold snaps correlate with specific medicine demand (antihistamines, flu remedies) |
| Calendar events | A hand-built table (Ramadan, flu season window, public holidays) | Free (no API) | These dates are known in advance — no need for an API, just a lookup table. Ramadan shifts yearly (lunar calendar), so this table needs manual updating each year |
| Health news | NewsAPI free tier | Free (limited requests/day) | Shortage or outbreak headlines are a real leading indicator of demand spikes |

## Plan
1. Set up access to each free source using the API keys from Phase 0.
2. For search trends: decide on a short list of relevant search terms per product category (e.g., "flu symptoms," "allergy medicine," "cold remedy").
3. For weather: decide which regions/cities to query, and define a simple rule for what counts as a "heatwave" (e.g., above a certain temperature).
4. For calendar events: build a simple table of known dates — Ramadan (update yearly), major holidays, and your defined flu-season window.
5. For news: decide on a short list of search keywords relevant to health/pharma demand (e.g., "flu," "shortage," "medicine Tunisia") and define how you'll turn a batch of headlines into a simple numeric "signal score" (e.g., how many matching articles appeared recently).
6. Test each source independently to confirm it returns real, current data.

## Important honesty note (say this to judges)
> "Trends, weather, and news are pulled from real, free live APIs. Calendar events like Ramadan are hardcoded, since these are publicly known dates in advance — no need to call an API for something we already know."

Also be upfront that "real-time" here means **polling** — checking a source periodically for the latest data — not a continuous live stream. That's a completely normal and accurate way to describe it, and NewsAPI's free tier in particular has a daily request limit, so build your polling frequency around that limit.

## Validation ✅
- [ ] A test search-trend query returns real, non-zero numbers for your chosen keywords
- [ ] A test weather query returns a real current temperature for your target city
- [ ] The calendar table correctly flags a date that falls inside a known event window (e.g., a date during Ramadan)
- [ ] A test news query returns real, current headlines (not empty)
- [ ] You know your NewsAPI daily request limit and have a plan that stays within it during the demo
