from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .config import (
    DATA_DIR,
    LEGACY_SOURCE,
    LEGACY_RESOLUTION_OFFSET_MINUTES,
    REPLACEMENT_LOGISTICS_INR,
    SLA_HOURS,
)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path.name}. Put the task-pack file in {path.parent.resolve()}"
        )
    return pd.read_csv(path)


def load_data(data_dir: str | Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    return {
        "tickets": _read_csv(data_dir / "tickets.csv"),
        "agents": _read_csv(data_dir / "agents.csv"),
        "orders": _read_csv(data_dir / "orders.csv"),
        "products": _read_csv(data_dir / "products.csv"),
    }


def clean_tickets(tickets: pd.DataFrame) -> pd.DataFrame:
    """Apply only transformations justified by the supplied policy/README."""
    df = tickets.copy()

    for col in ["created_at", "first_response_at", "resolved_at"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Policy §9: migrated legacy resolution timestamps came from a UTC event log,
    # while standard helpdesk exports are displayed in IST.
    df["resolved_at_clean"] = df["resolved_at"]
    legacy_mask = df["source_system"].eq(LEGACY_SOURCE) & df["resolved_at"].notna()
    df.loc[legacy_mask, "resolved_at_clean"] = (
        df.loc[legacy_mask, "resolved_at"]
        + pd.to_timedelta(LEGACY_RESOLUTION_OFFSET_MINUTES, unit="m")
    )

    # Policy §10: handle time = first response to resolution.
    df["handle_minutes"] = (
        (df["resolved_at_clean"] - df["first_response_at"]).dt.total_seconds() / 60
    )
    df["first_response_minutes"] = (
        (df["first_response_at"] - df["created_at"]).dt.total_seconds() / 60
    )

    df["sla_target_minutes"] = df["channel"].map(
        {k: v * 60 for k, v in SLA_HOURS.items()}
    )
    df["sla_breach"] = df["first_response_minutes"] > df["sla_target_minutes"]
    df["attendance"] = df["status"].isin(["resolved", "closed"])
    df["month"] = df["created_at"].dt.to_period("M").astype(str)
    df["any_transfer"] = df["transfers"].fillna(0).gt(0)
    df["is_replacement"] = df["replacement_issued"].eq("Y")
    df["low_csat"] = df["csat_score"].notna() & df["csat_score"].le(2)
    return df


def enrich_tickets(
    tickets: pd.DataFrame,
    agents: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    df = clean_tickets(tickets)

    # README/email: join agents on agent_id, never display name.
    df = df.merge(
        agents[["agent_id", "name", "site", "team", "shift", "tier"]],
        on="agent_id",
        how="left",
        validate="many_to_one",
    )

    df = df.merge(
        products[
            [
                "sku",
                "product_name",
                "family",
                "unit_cost_inr",
                "retail_price_inr",
                "warranty_months",
            ]
        ],
        left_on="product_sku",
        right_on="sku",
        how="left",
        validate="many_to_one",
    )

    df["replacement_cost_inr"] = np.where(
        df["is_replacement"],
        df["unit_cost_inr"] + REPLACEMENT_LOGISTICS_INR,
        0.0,
    )
    return df


def prepare_all(data_dir: str | Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    raw = load_data(data_dir)
    enriched = enrich_tickets(raw["tickets"], raw["agents"], raw["products"])
    raw["tickets_enriched"] = enriched
    return raw
