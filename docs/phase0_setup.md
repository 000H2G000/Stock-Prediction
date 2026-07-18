# Phase 0 — Setup (Free Tools Only)

## Goal

Get every team member ready to build — accounts created, free API keys in hand — before writing any logic. No paid tools, no local Jupyter/Anaconda install.

## What to install locally

- **Python 3.10+** (most laptops already have this — check by typing `python3 --version` in a terminal)
- **pip** (comes with Python)
- **Git**
- A code editor (VS Code, or anything you're comfortable with)

**Not needed:** Jupyter, Anaconda, or any notebook software locally — model training happens on **Google Colab** instead (see Phase 4), which runs entirely in the browser.

## Free accounts/API keys to get today

| Service                  | What it's for                                 | Where to sign up       | Notes                                                     |
| ------------------------ | --------------------------------------------- | ---------------------- | --------------------------------------------------------- |
| **NewsAPI**        | Pull health-related news headlines            | newsapi.org            | Free tier, limited requests/day — enough for a hackathon |
| **OpenWeatherMap** | Pull current weather data                     | openweathermap.org/api | Free tier, instant key                                    |
| **Groq**           | Free LLM API for the reasoning agent          | console.groq.com       | Free tier, fast, no credit card needed for basic use      |
| **Google account** | For Google Colab (training) and Google Trends | —                     | Most people already have one                              |

Google Trends (via the `pytrends` library) needs **no API key at all** — it's free and open.

## Steps

1. Every team member installs Python, pip, Git, and a code editor.
2. Sign up for NewsAPI, OpenWeatherMap, and Groq — get your free API keys.
3. Make sure at least one team member has a Google account ready for Colab.
4. Keep all API keys in a shared, secure note (not committed to git) so any teammate can plug them in.
5. Decide now who owns which phase, so you're not waiting on each other later.

## Validation ✅

- [ ] Every team member can run `python3 --version` and see 3.10+
- [ ] NewsAPI key obtained and tested (a sample request returns real headlines)
- [ ] OpenWeatherMap key obtained and tested (a sample request returns current weather)
- [ ] Groq API key obtained
- [ ] At least one teammate can open a new Google Colab notebook successfully
- [ ] All keys are shared with the team securely, and nobody plans to commit them to git
