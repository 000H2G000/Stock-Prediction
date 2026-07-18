# Phase 3 — Merge Internal + External Data into ML-Ready Format

## Goal
Combine the dummy internal sales data (Phase 1) with the external signals (Phase 2) into **one flat table** the model can train on directly — no text, no missing values, categories turned into numbers.

## What "ML-ready" means here
- One row = one (date, product, region) combination.
- Every column is a number — no free text.
- Text categories (like a product name) get turned into separate yes/no columns — this is a standard technique called **one-hot encoding**, and it's how tree-based models like XGBoost expect categorical data to be represented.
- The column you're trying to predict (units sold) is kept clearly separate from the input columns.

## Plan
1. Start from the internal dummy dataset (Phase 1).
2. Add time-based columns that don't need any API: month, week of year, a flag for "is this a flu-season week," a flag for "is this a heatwave-season week."
3. Add calendar event flags using the hardcoded table from Phase 2 (e.g., "is this week inside the Ramadan window").
4. Add the external signal columns from Phase 2: a search-trend score, a weather-based flag, a news signal score.
   - For historical rows (past dates), real historical trend/news data usually isn't available for free — it's standard practice in a prototype to simulate these values with a realistic correlation to the season, and say so clearly.
   - For live/current predictions, these columns get filled in with real values fetched fresh from the Phase 2 sources.
5. Turn product and region into one-hot encoded columns.
6. Save the final table, ready to hand to the model.

## Important honesty note (say this to judges)
> "Time and calendar features are exact. Trend and news scores in the historical training set are simulated with realistic seasonal correlation, since historical search/news data isn't freely available going back years — but at prediction time, the live system pulls real, current trend and news data."

## Validation ✅
- [ ] Every column except the date is numeric (no text fields left)
- [ ] No missing/empty values anywhere in the final table
- [ ] The number of rows matches the internal dummy dataset from Phase 1
- [ ] Product and region are represented as separate numeric columns, not as text
