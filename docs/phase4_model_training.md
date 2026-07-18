# Phase 4 — Train the Model on Google Colab

## Goal
Train an XGBoost model to predict weekly demand, without installing Jupyter or Anaconda locally, then serve it as a simple prediction service.

## Why Google Colab
Colab is a free, browser-based notebook environment from Google — nothing to install, works on any laptop, and comes with Python and common data science libraries pre-installed. It's the fastest way to get a "notebook-style" training environment without the local setup overhead of Jupyter/Anaconda.

## Plan
1. Open a new notebook at colab.research.google.com (free Google account required).
2. Upload your ML-ready dataset from Phase 3 (Colab supports direct file upload, or you can load it from Google Drive).
3. Install any missing libraries directly inside a Colab cell (Colab lets you run install commands right in a notebook cell — no separate terminal needed).
4. Split the dataset into a training portion and a testing portion, so you can check how well the model performs on data it hasn't seen.
5. Train an XGBoost regression model on the training portion.
6. Check two numbers on the test portion:
   - **Mean Absolute Error (MAE)** — on average, how far off are the predictions, in units? Lower is better.
   - **R² score** — how much of the demand variation the model explains, from 0 to 1. Closer to 1 is better.
7. Look at which input factors mattered most to the model's predictions (feature importance) — this becomes useful later for the reasoning agent (Phase 5).
8. Download the trained model file from Colab to your local machine, so it can be used by the prediction service.

## Why XGBoost (short version for judges)
> "This is tabular regression with several interacting signals — season, region, trends, news. Plain linear regression can't capture those interactions well. Deep learning needs more data than we realistically have. XGBoost handles feature interactions well, performs strongly on smaller datasets, and lets us clearly show which factors drove each prediction — which matters both for trust and for the reasoning agent in the next phase."

## After training: serving the model
Once you have a trained model file, it needs to be wrapped in a small prediction service so other parts of the system (the reasoning agent, the automation, the dashboard) can ask it for a prediction. This service:
- Takes in the current situation (product, region, season, trend score, news score, current stock)
- Returns a predicted demand number and a reorder recommendation (yes/no, and how much)

This service runs locally on your laptop during the hackathon — no hosting cost.

## Validation ✅
- [ ] Model trains successfully on Colab with no errors
- [ ] MAE and R² are recorded — write these down, they're your "quantified impact" numbers for the pitch
- [ ] Feature importance results make intuitive sense (e.g., "is flu season" should matter a lot for a flu remedy's demand)
- [ ] Trained model file is successfully downloaded from Colab to your local project folder
- [ ] The local prediction service correctly loads the downloaded model and returns a sensible prediction for a test scenario
