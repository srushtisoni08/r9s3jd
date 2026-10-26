import os
from pathlib import Path
from zoneinfo import ZoneInfo

ELEXON_BASE_URL = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))

UK_TZ = ZoneInfo("Europe/London")

# Delivery days in scope (inclusive)
DELIVERY_START = "2026-01-01"
DELIVERY_END = "2026-01-31"

# Day-ahead decision cutoff, UK local time on D-1 (HH:MM).
# Auction gate closes ~09:20 UK; 09:00 is a conservative default.
DECISION_CUTOFF = os.getenv("DECISION_CUTOFF", "09:00")

# Forecasts for 1 Jan can be published well before 31 Dec, so fetch earlier.
FORECAST_PUBLISH_FROM = "2025-12-25"

CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/wind_cache"))
SNAPSHOT_FILE = Path(__file__).resolve().parent.parent / "data" / "snapshot.json"

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if o.strip()
]