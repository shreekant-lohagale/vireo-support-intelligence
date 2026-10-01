from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

SLA_HOURS = {
    "chat": 0.25,   # 15 minutes
    "voice": 2.0,
    "social": 4.0,
    "email": 8.0,
}

BREACH_CREDIT_INR = 350
TRANSFER_COST_INR = 305
REPLACEMENT_LOGISTICS_INR = 340
AGENT_HOURLY_COST_INR = 165
BLENDED_CONTACT_COST_INR = 290

LEGACY_SOURCE = "legacy_fd"
LEGACY_RESOLUTION_OFFSET_MINUTES = 330  # UTC -> IST (+05:30)

CSAT_MIN = 1
CSAT_MAX = 5
LOW_CSAT_THRESHOLD = 2
