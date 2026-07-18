# Phase 5 — Reasoning Agent (Explain the "Why"), Free LLM

## Goal
The XGBoost model already made the decision (reorder or not, how much). This phase adds an AI agent that **explains that decision in plain language**, using a free-tier LLM, so a pharmacy manager trusts it instead of treating it as a black box.

## Why Groq
Groq offers a free tier for its LLM API and is known for very fast response times — useful for a live demo where you don't want the judges waiting on a slow explanation. Any other free-tier LLM API (e.g., a free Hugging Face-hosted model) would work the same way; Groq is simply a fast, easy-to-set-up option with generous free usage.

## Important: the agent does NOT decide anything
This is a key point to get right, both in how you build it and how you explain it to judges:
- The **model** (Phase 4) makes the actual numeric decision.
- The **agent** (this phase) only explains, in words, why that decision makes sense — using the model's own top contributing factors as its input.

This separation keeps your system explainable: the decision itself is a transparent, testable number, and the explanation is a separate, swappable layer on top.

## Plan
1. Get a free Groq API key (from Phase 0).
2. Take the model's prediction output (predicted demand, current stock, reorder recommendation, reorder quantity, and the top factors that drove the prediction).
3. Write a prompt instructing the LLM to explain this decision in plain language, aimed at a non-technical pharmacy manager, in 2-4 sentences, with no data-science jargon.
4. Send this prompt to the Groq API and return the explanation text.
5. Pass this explanation along to the human-in-the-loop step (Phase 6) and the dashboard (Phase 7), so it's shown right alongside the reorder recommendation.

## Example output style
> "We're recommending a reorder of 220 units of Cold & Flu syrup for Tunis. Demand typically rises sharply during flu season, and search interest for flu-related terms has been climbing. Current stock would run out before demand returns to normal, so ordering now avoids a stockout."

## Why this matters for the pitch
> "A number alone — 'reorder 220 units' — doesn't build trust. Our agent explains the reasoning in plain language, using the same factors the model actually used, so the person approving the order understands why, not just what."

## Validation ✅
- [ ] A test call to the Groq API returns a real, readable explanation (not an error)
- [ ] The explanation is understandable to someone with no data science background — test this by reading it out loud to a non-technical teammate or friend
- [ ] The explanation correctly reflects the actual prediction (e.g., if no reorder is recommended, the explanation shouldn't suggest ordering)
- [ ] The response comes back quickly enough for a live demo (a few seconds at most)
- [ ] You know Groq's free-tier rate limits and have a plan to stay within them during the demo
