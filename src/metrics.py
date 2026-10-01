from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BREACH_CREDIT_INR, REPLACEMENT_LOGISTICS_INR, TRANSFER_COST_INR


def overall_metrics(df: pd.DataFrame) -> dict[str, float]:
    completed = int(df["attendance"].sum())
    csat_n = int(df["csat_score"].notna().sum())
    return {
        "tickets": int(len(df)),
        "completed": completed,
        "csat_responses": csat_n,
        "csat_response_rate": csat_n / completed if completed else np.nan,
        "avg_csat": float(df["csat_score"].mean()),
        "median_handle_minutes": float(df.loc[df["attendance"], "handle_minutes"].median()),
        "sla_breach_rate": float(df["sla_breach"].mean()),
        "sla_breaches": int(df["sla_breach"].sum()),
        "sla_credit_cost_inr": float(df["sla_breach"].sum() * BREACH_CREDIT_INR),
        "transfer_cost_inr": float(df["transfers"].fillna(0).sum() * TRANSFER_COST_INR),
        "replacement_spend_inr": float(df["replacement_cost_inr"].sum()),
    }


def monthly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("month", as_index=False)
        .agg(
            tickets=("ticket_id", "size"),
            completed=("attendance", "sum"),
            csat_responses=("csat_score", "count"),
            avg_csat=("csat_score", "mean"),
            median_handle_minutes=("handle_minutes", "median"),
            sla_breach_rate=("sla_breach", "mean"),
            replacements=("is_replacement", "sum"),
            replacement_spend_inr=("replacement_cost_inr", "sum"),
            transfers=("transfers", "sum"),
        )
        .sort_values("month")
    )
    out["replacement_rate"] = out["replacements"] / out["tickets"]
    out["csat_response_rate"] = out["csat_responses"] / out["completed"].replace(0, np.nan)
    return out


def agent_metrics(df: pd.DataFrame) -> pd.DataFrame:
    keys = ["agent_id", "name", "team", "tier", "site", "shift"]
    out = (
        df.groupby(keys, dropna=False, as_index=False)
        .agg(
            tickets=("ticket_id", "size"),
            completed=("attendance", "sum"),
            csat_responses=("csat_score", "count"),
            avg_csat=("csat_score", "mean"),
            median_handle_minutes=("handle_minutes", "median"),
            avg_handle_minutes=("handle_minutes", "mean"),
            sla_breach_rate=("sla_breach", "mean"),
            transfers=("transfers", "sum"),
            transfer_rate=("any_transfer", "mean"),
            replacements=("is_replacement", "sum"),
            replacement_rate=("is_replacement", "mean"),
            replacement_spend_inr=("replacement_cost_inr", "sum"),
        )
    )
    out["csat_response_rate"] = out["csat_responses"] / out["completed"].replace(0, np.nan)

    team_csat = df.groupby("team")["csat_score"].mean()
    team_handle = df.groupby("team")["handle_minutes"].median()
    out["team_avg_csat"] = out["team"].map(team_csat)
    out["team_median_handle_minutes"] = out["team"].map(team_handle)
    out["csat_gap_vs_team"] = out["avg_csat"] - out["team_avg_csat"]
    out["handle_ratio_vs_team"] = (
        out["median_handle_minutes"] / out["team_median_handle_minutes"].replace(0, np.nan)
    )
    return out


def raw_bottom_ten(agent_df: pd.DataFrame, min_csat_responses: int = 30) -> pd.DataFrame:
    eligible = agent_df[agent_df["csat_responses"] >= min_csat_responses].copy()
    return eligible.sort_values(
        ["avg_csat", "median_handle_minutes"], ascending=[True, False]
    ).head(10)


def contextual_bottom_ten(agent_df: pd.DataFrame, min_csat_responses: int = 30) -> pd.DataFrame:
    """Transparent peer-context view: rank CSAT gap within the agent's team first.

    This is deliberately not a black-box firing/training score. It preserves the client's
    requested raw view while exposing whether an agent is low only because their queue/team
    is intrinsically harder.
    """
    eligible = agent_df[agent_df["csat_responses"] >= min_csat_responses].copy()
    return eligible.sort_values(
        ["csat_gap_vs_team", "handle_ratio_vs_team"], ascending=[True, False]
    ).head(10)


def product_lot_alerts(tickets: pd.DataFrame, orders: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Analyze Pulse 2 manufacturing lots using unique orders, not ticket counts.

    The task's email thread says lot codes may be ignored if not useful. They are useful here:
    Pulse 2 lots produced Oct-Dec 2025 show a large replacement-order spike.
    """
    exact = tickets.loc[
        tickets["order_id"].notna(),
        ["ticket_id", "order_id", "replacement_issued"],
    ].copy()
    replaced_order_ids = set(
        exact.loc[exact["replacement_issued"].eq("Y"), "order_id"].dropna().unique()
    )

    pl2 = orders.loc[orders["sku"].eq("VA-EB-PL2")].copy()
    pl2["replaced"] = pl2["order_id"].isin(replaced_order_ids)
    pl2["lot_month"] = pl2["lot_code"].str.extract(r"PL2-(\d{4})", expand=False)

    lot = (
        pl2.groupby(["lot_month", "lot_code"], as_index=False)
        .agg(orders=("order_id", "nunique"), replacement_orders=("replaced", "sum"))
    )
    lot["replacement_order_rate"] = lot["replacement_orders"] / lot["orders"]

    baseline_months = {"2504", "2505", "2506", "2507", "2508", "2509"}
    affected_months = {"2510", "2511", "2512"}
    later_months = {"2601", "2602", "2603", "2604", "2605"}

    base = pl2[pl2["lot_month"].isin(baseline_months)]
    affected = pl2[pl2["lot_month"].isin(affected_months)]
    later = pl2[pl2["lot_month"].isin(later_months)]

    baseline_rate = float(base["replaced"].mean()) if len(base) else np.nan
    affected_rate = float(affected["replaced"].mean()) if len(affected) else np.nan
    later_rate = float(later["replaced"].mean()) if len(later) else np.nan
    affected_orders = int(len(affected))
    actual_replacements = int(affected["replaced"].sum())
    expected_at_baseline = affected_orders * baseline_rate
    excess_replacements = actual_replacements - expected_at_baseline

    # Pulse 2 unit cost is looked up by caller in the enriched ticket data elsewhere;
    # for this alert use the product table value through a constant calculation only
    # after caller passes the known unit cost. We return excess count here.
    summary = {
        "baseline_orders": int(len(base)),
        "baseline_replacement_rate": baseline_rate,
        "affected_orders": affected_orders,
        "affected_replacement_orders": actual_replacements,
        "affected_replacement_rate": affected_rate,
        "later_orders": int(len(later)),
        "later_replacement_rate": later_rate,
        "expected_replacements_at_baseline": float(expected_at_baseline),
        "excess_replacements": float(excess_replacements),
    }
    return lot.sort_values(["lot_month", "lot_code"]), summary


def add_lot_opportunity_money(summary: dict[str, float], pulse2_unit_cost_inr: float) -> dict[str, float]:
    out = dict(summary)
    per_replacement = float(pulse2_unit_cost_inr + REPLACEMENT_LOGISTICS_INR)
    out["replacement_cost_each_inr"] = per_replacement
    out["estimated_excess_replacement_cost_inr"] = (
        out["excess_replacements"] * per_replacement
    )
    return out
