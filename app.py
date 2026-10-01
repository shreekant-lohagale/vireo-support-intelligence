from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, BREACH_CREDIT_INR
from src.data import prepare_all
from src.metrics import (
    add_lot_opportunity_money,
    agent_metrics,
    contextual_bottom_ten,
    monthly_metrics,
    overall_metrics,
    product_lot_alerts,
    raw_bottom_ten,
)
from src.model import add_expected_csat, agent_case_mix_context, build_case_mix_model
from src.text_insights import low_csat_themes
from src.validation import data_quality_checks
from src.upload_data import get_uploaded_data_dir

st.set_page_config(
    page_title="Vireo Support Intelligence",
    page_icon="🎧",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
      div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.22); border-radius: 14px; padding: 12px 14px;}
      .small-note {font-size: .88rem; opacity: .78;}
      .callout {padding: 14px 16px; border: 1px solid rgba(128,128,128,.24); border-radius: 14px; margin: 8px 0 14px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_prepared(data_dir: str):
    return prepare_all(Path(data_dir))


@st.cache_resource(show_spinner=False)
def train_model(_tickets: pd.DataFrame):
    return build_case_mix_model(_tickets)


def money(v: float) -> str:
    if abs(v) >= 100000:
        return f"₹{v/100000:.2f}L"
    if abs(v) >= 1000:
        return f"₹{v/1000:.1f}K"
    return f"₹{v:,.0f}"


def duration_minutes(v: float) -> str:
    if pd.isna(v):
        return "—"
    if v < 60:
        return f"{v:.0f} min"
    if v < 48 * 60:
        return f"{v/60:.1f} h"
    return f"{v/(24*60):.1f} d"


REQUIRED_DATA_FILES = [
    "tickets.csv",
    "agents.csv",
    "orders.csv",
    "products.csv",
]

local_data_available = all(
    (DATA_DIR / filename).exists()
    for filename in REQUIRED_DATA_FILES
)

if local_data_available:
    active_data_dir = DATA_DIR
else:
    active_data_dir = get_uploaded_data_dir()

    if active_data_dir is None:
        st.info(
            "Upload all four supplied Vireo CSV files above to start the dashboard."
        )
        st.stop()

data = load_prepared(str(active_data_dir))
tickets = data["tickets_enriched"]
model, model_eval = train_model(tickets)
tickets_model = add_expected_csat(tickets, model)

metrics = overall_metrics(tickets_model)
am = agent_metrics(tickets_model)
raw10 = raw_bottom_ten(am)
context10 = contextual_bottom_ten(am)
case_mix = agent_case_mix_context(tickets_model)
monthly = monthly_metrics(tickets_model)
checks = data_quality_checks(tickets_model)

lot_table, lot_summary = product_lot_alerts(data["tickets"], data["orders"])
pulse2_unit_cost = float(
    data["products"].loc[data["products"]["sku"].eq("VA-EB-PL2"), "unit_cost_inr"].iloc[0]
)
lot_summary = add_lot_opportunity_money(lot_summary, pulse2_unit_cost)

st.title("Vireo Support Intelligence")
st.caption("Agent performance, coaching context, and a product-quality signal — built from the supplied support pack.")

with st.sidebar:
    st.subheader("Scope")
    st.write("Jan 2025 – Jun 2026")
    st.write("44 support agents")
    st.write("Local ML/NLP only")
    st.success("Paid model-call cost: ₹0")
    st.markdown("---")
    min_responses = st.number_input("Minimum CSAT responses for ranking", min_value=10, max_value=100, value=30, step=5)
    st.caption("All 44 agents have at least 42 CSAT responses in the supplied data, so the default does not exclude anyone.")

# Recompute ranking only if user changes threshold.
raw10_view = raw_bottom_ten(am, int(min_responses))
context10_view = contextual_bottom_ten(am, int(min_responses))

overview_tab, agents_tab, coaching_tab, root_tab, validation_tab = st.tabs(
    ["Overview", "Agent rankings", "Coaching drill-down", "Root-cause alert", "Validation"]
)

with overview_tab:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tickets", f"{metrics['tickets']:,}")
    c2.metric("Average CSAT", f"{metrics['avg_csat']:.2f} / 5")
    c3.metric("CSAT response rate", f"{metrics['csat_response_rate']*100:.1f}%")
    c4.metric("Median handle time", duration_minutes(metrics["median_handle_minutes"]))
    c5.metric("Replacement spend", money(metrics["replacement_spend_inr"]))

    st.markdown(
        f"""
        <div class="callout">
        <b>Business signal:</b> CSAT fell to <b>{monthly.loc[monthly['month'].eq('2026-02'),'avg_csat'].iloc[0]:.2f}</b> in Feb 2026,
        while replacement activity rose sharply after the festive period. Raw agent ranking alone does not explain that change.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        fig = px.line(monthly, x="month", y="avg_csat", markers=True, title="Monthly CSAT")
        fig.update_yaxes(range=[1, 5], title="Average CSAT")
        fig.update_xaxes(title="")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.line(monthly, x="month", y="replacement_rate", markers=True, title="Replacement rate by ticket")
        fig.update_yaxes(tickformat=".0%", title="Replacement rate")
        fig.update_xaxes(title="")
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        fig = px.line(monthly, x="month", y="sla_breach_rate", markers=True, title="First-response SLA breach rate")
        fig.update_yaxes(tickformat=".0%", title="Breach rate")
        fig.update_xaxes(title="")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(monthly, x="month", y="replacement_spend_inr", title="Replacement spend")
        fig.update_yaxes(title="INR")
        fig.update_xaxes(title="")
        st.plotly_chart(fig, use_container_width=True)

with agents_tab:
    st.subheader("1) Requested raw bottom ten")
    st.write(
        "This is the client's requested view: agents sorted by raw average CSAT, with handle time shown beside it. "
        "It should not be treated as a training decision by itself."
    )
    display_raw = raw10_view[[
        "agent_id", "name", "team", "tier", "tickets", "csat_responses", "avg_csat",
        "median_handle_minutes", "sla_breach_rate", "replacement_rate"
    ]].copy()
    display_raw["median_handle"] = display_raw["median_handle_minutes"].map(duration_minutes)
    display_raw["sla_breach_rate"] = (display_raw["sla_breach_rate"] * 100).round(1)
    display_raw["replacement_rate"] = (display_raw["replacement_rate"] * 100).round(1)
    display_raw["avg_csat"] = display_raw["avg_csat"].round(2)
    st.dataframe(
        display_raw.drop(columns=["median_handle_minutes"]).rename(columns={
            "avg_csat": "CSAT",
            "sla_breach_rate": "SLA breach %",
            "replacement_rate": "Replacement %",
            "median_handle": "Median handle time",
        }),
        use_container_width=True,
        hide_index=True,
    )

    warranty_in_raw = int(raw10_view["tier"].eq(2).sum())
    st.warning(
        f"{warranty_in_raw} of the raw bottom 10 are Tier-2 Escalations & Warranty agents. "
        "Vireo policy says Tier-2 handles escalated hardware/warranty work and should not be compared with Tier-1 on volume metrics."
    )

    st.subheader("2) Context view for coaching")
    st.write(
        "This view compares each agent's CSAT with their own team's baseline first. It is deliberately transparent: "
        "no hidden composite score and no automatic employment decision."
    )
    display_ctx = context10_view[[
        "agent_id", "name", "team", "tier", "csat_responses", "avg_csat", "team_avg_csat",
        "csat_gap_vs_team", "median_handle_minutes", "handle_ratio_vs_team"
    ]].copy()
    for col in ["avg_csat", "team_avg_csat", "csat_gap_vs_team", "handle_ratio_vs_team"]:
        display_ctx[col] = display_ctx[col].round(2)
    display_ctx["median_handle"] = display_ctx["median_handle_minutes"].map(duration_minutes)
    st.dataframe(
        display_ctx.drop(columns=["median_handle_minutes"]).rename(columns={
            "avg_csat": "CSAT",
            "team_avg_csat": "Team CSAT",
            "csat_gap_vs_team": "Gap vs team",
            "handle_ratio_vs_team": "Handle ratio vs team",
            "median_handle": "Median handle time",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("3) ML case-mix context")
    st.write(
        "A local gradient-boosting model estimates expected CSAT from case mix (channel, category, priority, team, product, source system, tier and month). "
        "agent_id is excluded. The residual is context only, not a firing or promotion score."
    )
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("2026 holdout MAE", f"{model_eval['mae']:.2f} CSAT points")
    mc2.metric("Naive-baseline MAE", f"{model_eval['naive_mae']:.2f}")
    improvement = (1 - model_eval["mae"] / model_eval["naive_mae"]) * 100
    mc3.metric("MAE improvement", f"{improvement:.1f}%")
    st.dataframe(
        case_mix.head(12).round({"actual_csat": 2, "expected_csat": 2, "case_mix_gap": 2}),
        use_container_width=True,
        hide_index=True,
    )

with coaching_tab:
    st.subheader("Agent drill-down")
    agent_lookup = am.sort_values(["name", "agent_id"])[["agent_id", "name", "team"]]
    labels = {
        f"{r.agent_id} — {r['name']} — {r.team}": r.agent_id
        for _, r in agent_lookup.iterrows()
    }
    selected_label = st.selectbox("Choose an agent", list(labels.keys()))
    selected_id = labels[selected_label]
    row = am.loc[am["agent_id"].eq(selected_id)].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CSAT", f"{row['avg_csat']:.2f}", f"{row['csat_gap_vs_team']:+.2f} vs team")
    c2.metric("CSAT responses", f"{int(row['csat_responses'])}")
    c3.metric("Median handle time", duration_minutes(row["median_handle_minutes"]))
    c4.metric("SLA breach rate", f"{row['sla_breach_rate']*100:.1f}%")

    themes = low_csat_themes(tickets_model, selected_id)
    st.markdown("#### Low-CSAT local NLP summary")
    st.caption("This uses the agent's CSAT 1–2 tickets only. Categories come from the supplied ticket field; phrases are TF-IDF extraction. No paid API call is made.")
    if themes["tickets"] == 0:
        st.info("No CSAT 1–2 tickets for this agent.")
    else:
        left, right = st.columns(2)
        with left:
            cat_df = pd.DataFrame(themes["categories"])
            cat_df["share"] = (cat_df["share"] * 100).round(1)
            st.write(f"Low-CSAT tickets: **{themes['tickets']}**")
            st.dataframe(cat_df.rename(columns={"share": "share %"}), use_container_width=True, hide_index=True)
        with right:
            st.write("Common phrases")
            if themes["phrases"]:
                st.write(" · ".join(themes["phrases"]))
            else:
                st.write("Not enough repeated text for stable phrase extraction.")

    selected_tickets = tickets_model[
        (tickets_model["agent_id"].eq(selected_id)) & tickets_model["csat_score"].notna()
    ].sort_values("csat_score").head(12)
    st.markdown("#### Example scored tickets")
    st.dataframe(
        selected_tickets[["ticket_id", "created_at", "channel", "category", "csat_score", "transfers", "replacement_issued"]],
        use_container_width=True,
        hide_index=True,
    )

with root_tab:
    st.subheader("Product-quality signal that raw agent ranking hides")
    base_rate = lot_summary["baseline_replacement_rate"]
    affected_rate = lot_summary["affected_replacement_rate"]
    later_rate = lot_summary["later_replacement_rate"]
    est_cost = lot_summary["estimated_excess_replacement_cost_inr"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pulse 2 Apr–Sep 2025 lots", f"{base_rate*100:.1f}% replacement orders")
    c2.metric("Pulse 2 Oct–Dec 2025 lots", f"{affected_rate*100:.1f}%")
    c3.metric("Pulse 2 Jan–May 2026 lots", f"{later_rate*100:.1f}%")
    c4.metric("Estimated excess cost", money(est_cost))

    st.error(
        f"Pulse 2 lots manufactured Oct–Dec 2025 show {affected_rate*100:.1f}% of orders with a replacement ticket, "
        f"versus {base_rate*100:.1f}% in Apr–Sep 2025 and {later_rate*100:.1f}% in Jan–May 2026. "
        f"At ₹{lot_summary['replacement_cost_each_inr']:,.0f} per Pulse 2 replacement, the excess above the earlier baseline is about {money(est_cost)} across those lots."
    )
    st.write(
        "Interpretation: this pattern is consistent with a manufacturing-lot problem and is a reason not to treat low CSAT in Warranty as pure agent underperformance. "
        "It is an operational flag, not proof of causality; lot-level QA/returns inspection would be the next check."
    )

    plot_lot = lot_table.groupby("lot_month", as_index=False).agg(
        orders=("orders", "sum"), replacement_orders=("replacement_orders", "sum")
    )
    plot_lot["replacement_order_rate"] = plot_lot["replacement_orders"] / plot_lot["orders"]
    fig = px.bar(plot_lot, x="lot_month", y="replacement_order_rate", title="Pulse 2 replacement-order incidence by manufacturing month")
    fig.update_yaxes(tickformat=".0%", title="Orders with replacement ticket")
    fig.update_xaxes(title="Manufacturing month (YYMM)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Business goal")
    st.success(
        f"Keep future Pulse 2 replacement-order incidence near the pre-spike baseline (~{base_rate*100:.1f}%) rather than the {affected_rate*100:.1f}% seen in Oct–Dec 2025 lots. "
        f"On the {lot_summary['affected_orders']:,} affected-quarter orders in this pack, that gap corresponds to about {lot_summary['excess_replacements']:.0f} excess replacements, worth approximately {money(est_cost)}."
    )

with validation_tab:
    st.subheader("How we know the numbers are not silently broken")
    st.dataframe(checks, use_container_width=True, hide_index=True)

    raw_negative = int(
        (
            (pd.to_datetime(data["tickets"]["resolved_at"], errors="coerce")
             - pd.to_datetime(data["tickets"]["first_response_at"], errors="coerce"))
            .dt.total_seconds()
            .lt(0)
        ).sum()
    )
    st.info(
        f"Before the legacy UTC→IST correction, {raw_negative:,} tickets had impossible negative handle time. After the policy-backed correction, the validation check reports zero negative cleaned handle times."
    )

    st.markdown("#### Case-mix model validation")
    st.write(
        f"Temporal holdout: trained on {model_eval['train_rows']:,} scored 2025 tickets and tested on {model_eval['test_rows']:,} scored 2026 tickets. "
        f"MAE = {model_eval['mae']:.2f} CSAT points vs {model_eval['naive_mae']:.2f} for a constant-mean baseline; R² = {model_eval['r2']:.2f}."
    )
    st.warning(
        "Known limitation: the model explains only part of individual survey variation. It is used to add case-mix context, not to make an employment decision. "
        "Free-text phrase extraction can also be noisy on short/junk IVR transcripts."
    )

    st.markdown("#### Cost")
    st.write(
        "The submitted MVP makes no paid model/API calls. The dashboard, gradient-boosting model and TF-IDF text analysis all run locally, so model-call cost is ₹0 per run and ₹0/month at ~650 tickets/week. Compute/hosting is excluded because no production hosting choice was specified."
    )
