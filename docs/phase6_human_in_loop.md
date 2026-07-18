# Phase 6 — Human-in-the-Loop Approval + Supplier Automation

## Goal
Nothing gets ordered automatically without a human saying yes. This phase wires together: get a prediction → get an explanation → show a human → wait for approval → if approved, notify the supplier → log everything.

## Why human-in-the-loop matters (say this to judges)
> "The AI predicts and explains, but a person always makes the final call before anything is ordered. This isn't just a safety feature — it builds trust. Nobody wants a fully autonomous system placing real orders with no oversight."

## Plan
1. Get a prediction from the model service (Phase 4) for the current scenario.
2. If no reorder is needed, log that outcome and stop — no human action required.
3. If a reorder is recommended, get the plain-language explanation from the reasoning agent (Phase 5).
4. Show both the recommendation and the explanation to a human, and wait for an approve/reject decision.
5. If approved:
   - Send a reorder notification to the "supplier" — for a free, hackathon-friendly demo, this can be a simulated notification (e.g., an email sent to a test inbox, or a message posted to a free Slack/Discord webhook).
   - Record that the order was sent.
6. If rejected: record the rejection, and confirm nothing is sent.
7. Every decision — approved, rejected, or no action needed — gets saved to a simple log (a lightweight local database like SQLite works well and is free, with nothing to install beyond what Python already includes).

## Free options for the "supplier notification" step
| Option | Cost | Notes |
|---|---|---|
| Simulated console/log message | Free | Simplest, safest for a demo — just clearly show the "message" that would have been sent |
| Slack incoming webhook | Free | Quick to set up, visually convincing in a live demo |
| Discord webhook | Free | Same idea as Slack, equally easy |
| Email via a free SMTP test service | Free tier | More setup effort than the above — only worth it if you have spare time |

## Connecting the pieces (for judges asking "how does X talk to Y")
> "The model is a separate service that only predicts. Our automation logic calls it, just like it would call any external API. It's deliberately kept as a separate piece from the model, so the same prediction service could later be reused by other tools — including a real workflow automation platform in production."

## Validation ✅
- [ ] The flow correctly shows "no action needed" when stock is sufficient
- [ ] The flow correctly asks for approval when a reorder is recommended
- [ ] Approving triggers the simulated supplier notification; rejecting does not
- [ ] Every decision — approved, rejected, or no action — is recorded in the log with a timestamp
- [ ] You can test the full flow multiple times with different stock levels and see consistent, sensible decisions
