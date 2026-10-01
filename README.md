# Vireo Support Intelligence

A small AI-assisted support analytics tool for Vireo Audio. It delivers the client's requested per-agent CSAT/handle-time view and raw bottom ten, while adding context so hard queues are not mistaken for poor agents. It also surfaces a product-lot signal that helps explain the festive-season CSAT decline.

## What it does

- Computes CSAT correctly (blank surveys are excluded, not treated as zero).
- Computes handle time using Vireo's policy definition: **first response → resolution**.
- Corrects migrated `legacy_fd` resolution timestamps from UTC to IST before handle-time calculation.
- Shows the client's requested **raw bottom ten** by CSAT.
- Shows a transparent **team-context coaching view** instead of pretending raw rank is a fair retraining decision.
- Trains a local gradient-boosting **case-mix model** that estimates expected CSAT without using `agent_id`.
- Uses local TF-IDF NLP to summarize repeated phrases in low-CSAT cases.
- Calculates replacement cost as **unit cost + ₹340 logistics**.
- Finds a strong Pulse 2 manufacturing-lot replacement spike in Oct–Dec 2025.
- Runs with **₹0 paid model/API cost**.

## Business goal

The strongest non-agent signal in the pack is Pulse 2 manufacturing lots from Oct–Dec 2025. About **30.2%** of orders from those lots have a replacement ticket, versus **5.0%** for Apr–Sep 2025 lots and **4.7%** for Jan–May 2026 lots.

Using Vireo's planning rule for a Pulse 2 replacement (₹1,480 unit cost + ₹340 logistics = ₹1,820), the excess above the earlier baseline is approximately **499 replacements / ₹9.08 lakh** across the 1,979 affected-quarter orders.

Goal: **keep future Pulse 2 replacement-order incidence near 5% rather than repeating the 30.2% affected-lot rate.** The dashboard still fulfills Priya's agent view first; this lot finding is presented as an operational alert, not proof of causality.

## Quick start

Tested for Python 3.10+.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Data files

The evaluator/task pack should be placed in `data/` with these names:

```text
data/
  tickets.csv
  agents.csv
  orders.csv
  products.csv
```

The local bundle used during development also contains `support-policy.pdf`, but the app does not parse the PDF at runtime. Policy constants are encoded in `src/config.py` and documented in code.

The repository `.gitignore` excludes raw CSV/PDF files so customer/support exports are not accidentally published in a public GitHub repository. If the evaluation process explicitly requires the data inside the public repo, remove those ignore lines only after confirming that publishing the pack is permitted.

## Rebuild analysis outputs

```bash
python scripts/build_outputs.py
```

This writes:

```text
outputs/agent_metrics.csv
outputs/raw_bottom_10.csv
outputs/context_bottom_10.csv
outputs/case_mix_agent_context.csv
outputs/monthly_metrics.csv
outputs/pulse2_lot_analysis.csv
outputs/data_quality_checks.csv
outputs/summary.json
```

## Run tests

```bash
pytest -q
```

## Key decisions

### 1. Raw bottom ten is shown, but not equated with "needs retraining"

The supplied policy says Tier-2 Escalations & Warranty owns escalated hardware/warranty work and should not be compared with Tier-1 on volume metrics. The raw bottom ten is heavily populated by Tier-2. The app therefore keeps Priya's requested raw view and adds a peer-context view rather than hiding the requested result.

### 2. No opaque employee score

I deliberately did not create a weighted "bad agent" score. The context view shows explicit gaps versus team peers, sample size, handle time and case-mix expected CSAT. Human review remains required.

### 3. Legacy timestamp correction

Before correction, 2,309 tickets had impossible negative raw handle time. The policy says migrated resolution timestamps were reconstructed from a UTC event log while helpdesk reports are displayed in IST. For `legacy_fd` rows, `resolved_at` is shifted +05:30 before handle time is computed.

### 4. Orders/lot codes were used only after the dashboard worked

The email thread said lot codes could be ignored if not useful. They became useful because replacement spend and CSAT moved sharply after the festive period. The lot analysis is a secondary finding, not the core dashboard.

## AI / ML used in the tool

Runtime is local and has no per-ticket paid calls:

1. **GradientBoostingRegressor** predicts expected CSAT from case mix: channel, category, priority, assigned team, product, source system, tier and month. `agent_id` is intentionally excluded.
2. **TF-IDF** extracts recurring phrases from an agent's CSAT 1–2 tickets.

The case-mix model is validated on a temporal holdout: train on 2025 scored tickets, test on 2026 scored tickets. In the supplied pack it achieves roughly **0.87 MAE**, versus about **0.98 MAE** for a constant-mean baseline. That is useful context, but not accurate enough to justify automatic personnel decisions.

## Paid-call cost

No paid model/API calls are used by the submitted MVP.

- One run: **₹0 model-call cost**
- ~650 tickets/week × 4.33 ≈ **2,815 tickets/month**
- Paid calls per ticket: **0**
- Monthly model-call cost: **₹0**

Local compute/hosting is not included because Vireo did not specify a hosting platform.

## Known limitations

- The case-mix model explains only part of individual CSAT variation and should not be treated as causal.
- `assigned_team` is the first-routed team while `agent_id` is the resolving agent; transfers can make ownership messy.
- The ~40 junk IVR transcripts mentioned in the email can make text phrases noisy. They are not removed from numeric KPIs.
- Lot replacement incidence is based on the supplied orders and matching replacement tickets; it is an operational signal, not a confirmed manufacturing root cause.
- No live helpdesk integration, authentication, production database, forecasting, or automated training recommendation was built inside the five-hour scope.
- No customer-level segmentation is used because it is not required for Priya's decision and increases privacy/scope cost.

## Project structure

```text
.
├── app.py
├── README.md
├── requirements.txt
├── data/
├── memo/
├── outputs/
├── scripts/
│   └── build_outputs.py
├── src/
│   ├── config.py
│   ├── data.py
│   ├── metrics.py
│   ├── model.py
│   ├── text_insights.py
│   └── validation.py
└── tests/
    └── test_metrics.py
```
