# Phase 1 — Dummy Internal Stock Data (Pharma)

## Goal
Create a fake but realistic sales/demand history for a pharmacy or pharma distributor, since real Tunisian sales data isn't publicly available. This becomes the "internal data" half of your model's training set.

## What to simulate
- A handful of medicine categories — pick ones with clearly different demand patterns, for example: a painkiller (steady, year-round demand), a flu/cold remedy (spikes in winter), an allergy medicine (spikes in specific seasons), insulin (steady but slightly affected by heat), an antibiotic (fairly steady).
- A few regions (e.g., Tunis, Sfax, Sousse) — different regions can have different baseline demand levels.
- At least 1–2 years of weekly data — enough history for the model to learn a seasonal pattern.
- Built-in seasonal patterns: a flu-season boost (winter months), a heatwave boost (summer), and a Ramadan-style boost window — plus some random noise so the data doesn't look artificially clean.

## Plan
1. Decide the exact list of products, regions, and the date range you'll simulate.
2. Define, for each product, a "base demand" number and which seasonal events affect it and by how much (e.g., flu season roughly doubles Cold & Flu remedy demand).
3. Generate one row per (week, product, region) combination, applying the base demand, the seasonal boosts, a region-based multiplier, and some random variation.
4. Save the result as a simple table (CSV) with clear columns: date, product, region, units sold.

## Why it's built this way (for explaining to a judge)
> "Since granular pharmacy sales data isn't publicly available in Tunisia, we generated a synthetic dataset with realistic seasonal patterns — flu season, heatwaves, Ramadan — plus random noise, so our model has real signal to learn from. We're transparent that this is simulated data standing in for real historical sales."

## Validation ✅
- [ ] The dataset covers at least 1–2 years, at weekly granularity
- [ ] Winter months clearly show higher flu/cold-remedy demand than summer months
- [ ] Regions show different baseline demand levels (not identical across regions)
- [ ] The data isn't perfectly smooth — some realistic random variation is present
- [ ] Every teammate can regenerate/access this dataset independently
