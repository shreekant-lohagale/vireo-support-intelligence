from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, OUTPUT_DIR
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
from src.validation import data_quality_checks


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = prepare_all(DATA_DIR)
    tickets = data["tickets_enriched"]

    model, model_eval = build_case_mix_model(tickets)
    tickets_model = add_expected_csat(tickets, model)

    am = agent_metrics(tickets_model)
    raw10 = raw_bottom_ten(am)
    context10 = contextual_bottom_ten(am)
    case_mix = agent_case_mix_context(tickets_model)
    monthly = monthly_metrics(tickets_model)
    checks = data_quality_checks(tickets_model)

    lot_table, lot_summary = product_lot_alerts(data["tickets"], data["orders"])
    pulse2_cost = float(
        data["products"].loc[data["products"]["sku"].eq("VA-EB-PL2"), "unit_cost_inr"].iloc[0]
    )
    lot_summary = add_lot_opportunity_money(lot_summary, pulse2_cost)

    am.to_csv(OUTPUT_DIR / "agent_metrics.csv", index=False)
    raw10.to_csv(OUTPUT_DIR / "raw_bottom_10.csv", index=False)
    context10.to_csv(OUTPUT_DIR / "context_bottom_10.csv", index=False)
    case_mix.to_csv(OUTPUT_DIR / "case_mix_agent_context.csv", index=False)
    monthly.to_csv(OUTPUT_DIR / "monthly_metrics.csv", index=False)
    lot_table.to_csv(OUTPUT_DIR / "pulse2_lot_analysis.csv", index=False)
    checks.to_csv(OUTPUT_DIR / "data_quality_checks.csv", index=False)

    summary = {
        "overall": overall_metrics(tickets_model),
        "case_mix_model": model_eval,
        "pulse2_lot_opportunity": lot_summary,
    }
    with open(OUTPUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print("\nRaw bottom 10:")
    print(raw10[["agent_id", "name", "team", "avg_csat", "median_handle_minutes"]].to_string(index=False))
    print("\nContext bottom 10:")
    print(context10[["agent_id", "name", "team", "avg_csat", "csat_gap_vs_team"]].to_string(index=False))
    print("\nData quality checks:")
    print(checks.to_string(index=False))


if __name__ == "__main__":
    main()
