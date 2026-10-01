from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import clean_tickets
from src.metrics import overall_metrics


def _tiny_df():
    return pd.DataFrame(
        {
            "ticket_id": ["T1", "T2"],
            "created_at": ["2025-01-01 08:00", "2026-01-01 08:00"],
            "first_response_at": ["2025-01-01 08:15", "2026-01-01 08:10"],
            "resolved_at": ["2025-01-01 03:00", "2026-01-01 09:10"],
            "status": ["resolved", "resolved"],
            "channel": ["chat", "chat"],
            "source_system": ["legacy_fd", "helpdesk"],
            "transfers": [0, 1],
            "replacement_issued": ["N", "N"],
            "csat_score": [5.0, None],
        }
    )


def test_legacy_resolution_is_normalized_to_ist():
    d = clean_tickets(_tiny_df())
    # Legacy 03:00 UTC -> 08:30 IST; first response 08:15 => 15-minute handle time.
    assert d.loc[0, "handle_minutes"] == 15


def test_blank_csat_is_excluded_from_average():
    d = clean_tickets(_tiny_df())
    d["replacement_cost_inr"] = 0
    m = overall_metrics(d)
    assert m["avg_csat"] == 5.0
    assert m["csat_responses"] == 1
