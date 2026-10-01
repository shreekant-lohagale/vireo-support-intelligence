from __future__ import annotations

import pandas as pd


def data_quality_checks(df: pd.DataFrame) -> pd.DataFrame:
    checks = []

    def add(name: str, passed: bool, detail: str):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    add(
        "Unique ticket_id",
        df["ticket_id"].is_unique,
        f"{df['ticket_id'].duplicated().sum()} duplicate ticket IDs",
    )
    add(
        "All agents joined",
        df["name"].notna().all(),
        f"{df['name'].isna().sum()} tickets missing agent roster match",
    )
    add(
        "All products joined",
        df["product_name"].notna().all(),
        f"{df['product_name'].isna().sum()} tickets missing product match",
    )
    scored = df["csat_score"].dropna()
    add(
        "CSAT is 1-5 or blank",
        scored.between(1, 5).all(),
        f"{(~scored.between(1,5)).sum()} invalid nonblank CSAT values",
    )
    complete = df[df["attendance"] & df["resolved_at_clean"].notna()]
    add(
        "No negative cleaned handle time",
        complete["handle_minutes"].ge(0).all(),
        f"{complete['handle_minutes'].lt(0).sum()} negative cleaned handle times",
    )
    add(
        "No negative first response time",
        df["first_response_minutes"].ge(0).all(),
        f"{df['first_response_minutes'].lt(0).sum()} negative first-response times",
    )
    return pd.DataFrame(checks)
