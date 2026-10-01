# 3-minute screen recording plan

Keep this as a screen walkthrough — no slides.

## 0:00–0:25 — Brief + prompt
Show the task page / prompt history briefly. Say: "I first translated the client email into three requirements: raw CSAT/handle-time ranking, evidence that the ranking is fair enough to use for coaching, and one measurable business outcome."

## 0:25–1:00 — What changed after inspecting the policy/data
Open `src/data.py` and the Validation tab. Explain that the first naive version would have used `resolved_at - first_response_at` directly, but 2,309 legacy rows became negative. Show the +05:30 correction and say you changed the pipeline after reading the policy.

## 1:00–1:40 — What you pushed back on
Open Agent rankings. Show that six of the raw bottom ten are Tier-2 Warranty. Then show the context view and explain: "I kept Priya's raw bottom ten, but I did not equate it with who should be retrained."

## 1:40–2:20 — What nobody asked for
Open Root-cause alert. Show the Pulse 2 lot chart and the 30.2% vs ~5% comparison, plus the ~₹9.08 lakh excess-cost estimate.

## 2:20–2:45 — AI and validation
Open the ML context + Coaching drill-down. Say the runtime uses local Gradient Boosting and TF-IDF, not paid per-ticket calls. Mention the 2,400-ticket temporal holdout and ~0.87 MAE.

## 2:45–3:00 — What you threw away
Show README `Known limitations` or git diff/history if available. Say you dropped the chatbot/RAG idea and an opaque weighted agent score because they consumed scope and were less defensible than the transparent dashboard.
