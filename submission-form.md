# Submission Form — Draft

> Replace the bracketed placeholders before submitting. Keep the answers concise and in your own voice.

## What did you build, and what business outcome does it move? State the number and the money.

I built **Vireo Support Intelligence**, a local Streamlit tool that gives Priya the requested per-agent CSAT, handle time and raw bottom ten, then adds peer/team context so hard queues are not automatically treated as poor agents. It also checks replacement spend and manufacturing lots because the festive-season CSAT decline overlaps a replacement spike.

The strongest business signal is Pulse 2 lots manufactured in **Oct–Dec 2025**: **30.2%** of orders in those lots have a replacement ticket versus **5.0%** for Apr–Sep 2025 lots and **4.7%** for Jan–May 2026 lots. The affected quarter contains 1,979 orders and about **499 excess replacements above the earlier baseline**. At Vireo's planning cost of **₹1,820 per Pulse 2 replacement** (₹1,480 unit cost + ₹340 logistics), that is approximately **₹9.08 lakh** of excess replacement cost. My business goal is to keep future Pulse 2 replacement-order incidence near the ~5% surrounding-lot baseline rather than repeating 30.2%.

## What does one run cost, and what would a month cost at Vireo's volume (roughly 650 tickets a week)? Show the arithmetic. If you used no paid calls, say so.

The delivered MVP makes **no paid model/API calls**. It uses pandas/scikit-learn locally for the case-mix model and TF-IDF text analysis.

- One run: **₹0 paid model-call cost**
- Monthly volume: 650 tickets/week × 4.33 weeks/month ≈ **2,815 tickets/month**
- Paid calls per ticket: **0**
- 2,815 × ₹0 = **₹0/month paid model-call cost**

Hosting/compute is not included because no production hosting platform was specified.

## How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.

I used two layers of checks. First, deterministic data-quality checks run across all **11,750 tickets**: unique ticket IDs, successful agent/product joins, CSAT restricted to 1–5 or blank, non-negative first-response time, and non-negative cleaned handle time. The timestamp check caught a real issue: before applying the policy-documented UTC→IST correction to migrated legacy resolution timestamps, **2,309 tickets** had impossible negative handle times; after correction, the count is zero.

Second, I validated the case-mix CSAT model with a **temporal holdout of 2,400 scored 2026 tickets**, trained only on 2,796 scored 2025 tickets. It has **MAE ≈ 0.87 CSAT points** versus **≈0.98** for a constant-mean baseline (about 11.6% lower MAE). It still gets individual surveys wrong when sentiment/tone, unusual multi-issue cases, or details in free text are not represented by the structured case-mix features. I therefore show its output only as context, never as an automatic retraining decision.

## Did you change, narrow, or push back on the client's ask? What, when, and why. [can only raise your score]

Yes. I kept Priya's requested raw bottom ten, but I pushed back on using that list directly as the training list. **Six of the raw bottom ten are Tier-2 Escalations & Warranty agents**, and the supplied operating policy says Tier-2 handles escalated hardware/warranty work and should not be compared with Tier-1 on volume metrics. I added a transparent team-context view and a case-mix model so Priya can separate queue difficulty from agent performance before spending the ₹4 lakh budget.

I also narrowed scope by not building a chatbot, production database, live helpdesk integration, authentication or forecasting. The dashboard and validation came first.

## What is wrong with what you are handing us? Be specific: bugs, shortcuts, things you know are off. [can only raise your score]

- The case-mix model is directional, not causal; MAE is ~0.87 CSAT points and R² is low, so it does not explain most individual survey variation.
- `assigned_team` is the first-routed team while `agent_id` is the resolving agent; transferred cases can make ownership ambiguous.
- The email warns that ~40 IVR transcripts are junk. I leave those tickets in numeric KPIs but they can make local TF-IDF phrase extraction noisy.
- The Pulse 2 lot result is an operational signal, not proof of a manufacturing defect. QA/returns inspection is needed to confirm causality.
- I did not build automated training recommendations because I do not think the available data justifies an employment decision without human review.
- This is a local MVP, not a production-secured deployment.

## What did you deliberately leave out, and why that rather than something else?

I left out authentication, production storage, live helpdesk ingestion, forecasting, customer segmentation, full semantic analysis of every message, and per-ticket LLM calls. Those features would consume the five-hour cap without improving the core decision as much as correct KPI definitions, fairness/context, validation and the lot-level finding. I also did not use `customers.csv` because customer identity/demographics were not necessary for Priya's decision.

## Anything you built or found that nobody asked for?

Yes. I used the order lot codes only after the core dashboard worked and found that **Pulse 2 Oct–Dec 2025 manufacturing lots have ~30.2% replacement-order incidence**, compared with ~5% before and after. That aligns with the replacement-spend spike and helps explain why warranty agents appear at the bottom of the raw CSAT ranking. The estimated excess replacement cost above the earlier baseline is about **₹9.08 lakh** across those affected-quarter orders.

## What did you use AI for? Which tools and models, where they helped, where they wasted your time, what you threw away. Link your three-minute screen recording here.

For development I used **ChatGPT (GPT-5.6 Sol)** to decompose the client brief, challenge assumptions, inspect data-quality risks, and accelerate Python/Streamlit implementation. In the delivered tool I used a local **scikit-learn GradientBoostingRegressor** for case-mix expected CSAT and local **TF-IDF** for repeated phrases in low-CSAT tickets. I deliberately did not use a paid per-ticket LLM because Finance explicitly asked for a cheap solution and the numeric problem does not require one.

I discarded the idea of a single weighted "bad agent" score because the weights would be arbitrary and could hide the Tier-2 workload problem. I also discarded a full RAG/chatbot and per-ticket LLM classification because they added cost and complexity without improving the five-hour decision enough.

Screen recording: **[PASTE PUBLIC 3-MINUTE RECORDING LINK]**

## Your Public Google Drive Link

**[PASTE GOOGLE DRIVE LINK]**

## Someone picks this up on Monday and you are unreachable. The three things they need to know.

1. **Do not remove the legacy timestamp correction.** `legacy_fd` resolution timestamps are shifted +05:30 before handle-time calculation because the supplied policy says those reconstructed timestamps came from a UTC event log.
2. **Do not treat the raw bottom ten as the training list.** Use the raw view to satisfy the request, then review the team/case-mix context because Tier-2 gets harder cases by design.
3. **Investigate Pulse 2 Oct–Dec 2025 lots with Product/QA.** The ~30.2% replacement-order incidence is the largest business signal in the pack; the dashboard does not prove causality.

## Honest hours spent. One number.

**[FILL WITH YOUR ACTUAL TOTAL HOURS]**

## Github Repo Link

**[PASTE PUBLIC GITHUB REPO URL]**
