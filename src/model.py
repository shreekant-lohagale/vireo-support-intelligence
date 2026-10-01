from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


CASE_MIX_FEATURES = [
    "channel",
    "category",
    "priority",
    "assigned_team",
    "product_sku",
    "source_system",
    "tier",
    "month_num",
]

CATEGORICAL_FEATURES = [
    "channel",
    "category",
    "priority",
    "assigned_team",
    "product_sku",
    "source_system",
]


def _feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["month_num"] = x["created_at"].dt.month
    return x[CASE_MIX_FEATURES]


def build_case_mix_model(df: pd.DataFrame) -> tuple[Pipeline, dict[str, float]]:
    """Predict expected CSAT from case mix, explicitly excluding agent_id.

    Validation uses a temporal holdout: 2025 trains, 2026 tests. This model is not used
    to decide employment outcomes; it is a context signal next to raw metrics.
    """
    scored = df[df["csat_score"].notna()].copy()
    train = scored[scored["created_at"] < pd.Timestamp("2026-01-01")]
    test = scored[scored["created_at"] >= pd.Timestamp("2026-01-01")]

    pre = ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="passthrough",
    )
    model = GradientBoostingRegressor(
        random_state=42,
        n_estimators=120,
        learning_rate=0.05,
        max_depth=3,
    )
    pipe = Pipeline([("pre", pre), ("model", model)])

    pipe.fit(_feature_frame(train), train["csat_score"])
    pred = pipe.predict(_feature_frame(test))
    naive = np.repeat(train["csat_score"].mean(), len(test))

    metrics = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "mae": float(mean_absolute_error(test["csat_score"], pred)),
        "r2": float(r2_score(test["csat_score"], pred)),
        "naive_mae": float(mean_absolute_error(test["csat_score"], naive)),
    }

    # Refit on all scored tickets for descriptive expected-CSAT values in the dashboard.
    pipe.fit(_feature_frame(scored), scored["csat_score"])
    return pipe, metrics


def add_expected_csat(df: pd.DataFrame, model: Pipeline) -> pd.DataFrame:
    out = df.copy()
    out["expected_csat"] = np.nan
    mask = out["csat_score"].notna()
    out.loc[mask, "expected_csat"] = model.predict(_feature_frame(out.loc[mask]))
    out["csat_residual"] = out["csat_score"] - out["expected_csat"]
    return out


def agent_case_mix_context(df: pd.DataFrame) -> pd.DataFrame:
    scored = df[df["csat_score"].notna()].copy()
    return (
        scored.groupby(["agent_id", "name", "team", "tier"], as_index=False)
        .agg(
            csat_responses=("csat_score", "size"),
            actual_csat=("csat_score", "mean"),
            expected_csat=("expected_csat", "mean"),
            case_mix_gap=("csat_residual", "mean"),
        )
        .sort_values("case_mix_gap")
    )
