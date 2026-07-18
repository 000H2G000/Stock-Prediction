# Phase 7 — Dashboard (the demo screen)

## Goal
One screen that shows the whole story: pick a scenario, see the forecast, see the AI's reasoning, approve or reject, see the log. This is what you'll actually have on screen during the pitch.

## Why Streamlit
Streamlit is free and open-source, and it's designed to turn a Python script into a working web dashboard with very little extra code — a strong fit for a 1-day hackathon where you want a working visual demo, not a full custom front-end build.

## What should be on the screen
- **A scenario control panel** — lets you pick product, region, month, and toggle flu season / heatwave / Ramadan, and adjust trend/news scores. This is your **"simulate an event"** control — it lets you trigger a demo scenario live instead of waiting for real data to change.
- **Forecast display** — predicted demand vs. current stock, shown as clear numbers and a simple chart.
- **Reorder recommendation + explanation** — the model's decision, plus the plain-language reasoning from Phase 5.
- **Approve / Reject buttons** — the human-in-the-loop step from Phase 6, right on the same screen.
- **A decision log panel** — a running list of past decisions (approved, rejected, or no action), pulled from the same log Phase 6 writes to.

## Plan
1. Build the scenario control panel first — confirm you can pick a product/region/season and see the values update.
2. Connect it to the prediction service (Phase 4) — confirm a forecast displays correctly.
3. Connect the reasoning agent (Phase 5) — confirm the explanation appears alongside the forecast.
4. Add the Approve/Reject buttons, wired to the human-in-the-loop logic (Phase 6).
5. Add the decision log panel, reading from the same log everything else writes to.

## Demo script (practice this exact flow for judges)
1. Show a **normal scenario** first (e.g., summer month, no flu season) → "stock is sufficient, no action needed."
2. Switch to **flu season** in the control panel, same product → forecast jumps, reorder recommended, explanation appears.
3. Click **Approve** → show the simulated supplier notification + the log updating live.
4. Point at the log panel: "every decision — approved, rejected, or no action — is tracked here."

This before/after toggle is your strongest demo moment — it visibly shows cause and effect without needing to wait for real-world data to change.

## Validation ✅
- [ ] Dashboard loads correctly and clearly shows an error (not a crash) if the prediction service isn't running
- [ ] Toggling "flu season" for the same product visibly changes the forecast
- [ ] Approve/Reject buttons both correctly update the log panel
- [ ] Full demo script (steps above) runs smoothly in under 2 minutes — time yourselves
