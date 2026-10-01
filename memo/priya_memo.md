# To: Priya Raman, Head of Customer Experience
## Subject: Where to point Q3 coaching — and one issue training will not fix

You asked for CSAT and handle time per agent, with the bottom ten flagged. The dashboard provides that view, but I would not use the raw bottom ten as the Q3 training list without context.

The main reason is queue difficulty. Six of the raw bottom ten are in Escalations & Warranty. Those agents handle certified Tier-2 warranty and escalated hardware work, and the operating policy explicitly treats that work differently from Tier-1. Their lower CSAT therefore does not, on its own, show that they are the weakest agents.

I added a second coaching view that compares each agent with their own team before ranking. Four Chat Frontline agents remain materially below their team's CSAT baseline in that view. Those are better candidates for coaching review than simply taking the ten lowest company-wide scores. The dashboard also shows response count, median handle time, SLA breaches and replacement mix so a manager can review the evidence before spending the ₹4 lakh budget.

There is also a larger non-training issue in the data. Pulse 2 manufacturing lots from Oct–Dec 2025 show a replacement-order incidence of about 30.2%, compared with about 5.0% for Apr–Sep 2025 lots and 4.7% for Jan–May 2026 lots. This pattern overlaps the period in which CSAT fell and replacement spend rose. At Vireo's planning cost of ₹1,820 per Pulse 2 replacement, the excess above the earlier baseline is approximately 499 replacements, or about ₹9.08 lakh, across the 1,979 affected-quarter orders in the pack.

I would therefore use the training budget for agents who are weak relative to comparable peers, while sending the Oct–Dec Pulse 2 lots to Product/QA for confirmation. Training warranty agents will not repair a manufacturing problem.

The tool is intentionally small. It runs locally, makes no paid model/API calls, and keeps the requested raw ranking visible. A local case-mix model adds context but is not used to make an automatic employment decision. Its 2026 holdout error is about 0.87 CSAT points, so it is directional rather than causal.

The most important data correction was also operational rather than cosmetic: 2,309 migrated legacy tickets showed impossible negative handle time before applying the policy-documented UTC-to-IST correction to legacy resolution timestamps. After correction, the dashboard has no negative handle times.

**Recommended Q3 action:** review the context-adjusted coaching candidates first; do not automatically retrain the raw bottom ten; and investigate the Pulse 2 Oct–Dec 2025 lots. A practical product goal is to keep future Pulse 2 replacement-order incidence near the ~5% surrounding-lot baseline rather than repeating the 30.2% affected-lot rate.
