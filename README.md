# Pharma Stock AI — Project Plan (Documentation Only)

AI system that predicts pharmacy/pharma distributor stock demand using internal sales data plus external real-world signals (search trends, weather/season, calendar events, health news), decides when to reorder, explains its reasoning in plain language, and — after human approval — sends the reorder to the supplier.

## One-line pitch

"We don't just track stock — we predict what's coming, explain why, and let you approve before it's ordered."

## Constraints for this build

- **Free tools/APIs only** — no paid services anywhere in the stack.
- **No local Jupyter/Anaconda install** — model training happens on **Google Colab** (free, browser-based, nothing to install).
- **No cloud hosting costs** — everything runs locally on your laptops except Colab (training) and the free-tier APIs.

## Architecture (build in this order)

```
[Dummy internal stock data]  +  [Free external APIs: trends, weather, calendar, news]
                    ↓
        [Merged dataset, ML-ready format]
                    ↓<img width="1536" height="1024" alt="5d33af80-4657-4459-9ce6-60a574174da5" src="https://github.com/user-attachments/assets/20ad5d56-807c-4b7e-bd80-bd05b1f3eec3" />

        [XGBoost model, trained on Google Colab → prediction + reorder decision]
                    ↓
        [Free-tier LLM agent explains WHY in plain language]
                    ↓
        [Human approves / rejects the order]
                    ↓
        [Approved → sent to supplier (simulated)]
                    ↓
        [Dashboard shows stock, forecasts, decisions, logs]
```

## Phases (see /docs — each phase has its own file with steps + validation)

1. `docs/phase0_setup.md` — accounts, free API keys, tools to install
2. `docs/phase1_dummy_data.md` — plan for fake pharma stock history
3. `docs/phase2_external_data.md` — free external data sources
4. `docs/phase3_data_merge.md` — combining data into ML-ready format
5. `docs/phase4_model_training.md` — training on Google Colab
6. `docs/phase5_agent_reasoning.md` — free-tier LLM explains the decision
7. `docs/phase6_human_in_loop.md` — approval step before ordering
8. `docs/phase7_dashboard.md` — dashboard, full demo flow

## Full free tech stack

| Layer                 | Tool                          | Cost                             |
| --------------------- | ----------------------------- | -------------------------------- |
| Model training        | Google Colab                  | Free                             |
| ML model              | XGBoost (Python library)      | Free, open-source                |
| Search trend data     | Google Trends via`pytrends` | Free, no key needed              |
| Weather data          | OpenWeatherMap                | Free tier                        |
| News data             | NewsAPI                       | Free tier (limited requests/day) |
| Reasoning agent (LLM) | Groq API                      | Free tier                        |
| Model serving         | FastAPI                       | Free, open-source                |
| Dashboard             | Streamlit                     | Free, open-source                |
| Storage               | SQLite                        | Free, built into Python          |
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/78355ee7-c24b-4fee-b9b9-f85e2ab6b60c" />

