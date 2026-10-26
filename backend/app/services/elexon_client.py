import json
import logging
from datetime import date, datetime, timedelta, timezone

import httpx
import pandas as pd

from app import config

log = logging.getLogger(__name__)

_memory: dict = {}


class ElexonError(Exception):
    """Raised when the Elexon API is unreachable or returns an error."""


def _windows(start: date, end: date, days: int = 7):
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=days - 1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


async def _get(client: httpx.AsyncClient, path: str, params: dict) -> list[dict]:
    try:
        r = await client.get(f"{config.ELEXON_BASE_URL}{path}", params=params)
        r.raise_for_status()
    except httpx.TimeoutException as e:
        raise ElexonError("Elexon API timed out") from e
    except httpx.HTTPStatusError as e:
        raise ElexonError(f"Elexon API returned {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise ElexonError(f"Elexon API request failed: {e}") from e
    data = r.json()
    return data if isinstance(data, list) else data.get("data", [])


async def _fetch_raw() -> dict:
    start = date.fromisoformat(config.DELIVERY_START)
    end = date.fromisoformat(config.DELIVERY_END)
    pub_from = date.fromisoformat(config.FORECAST_PUBLISH_FROM)

    actuals, forecasts = [], []
    async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
        for s, e in _windows(start, end):
            actuals += await _get(
                client,
                "/datasets/FUELHH/stream",
                {
                    "settlementDateFrom": s.isoformat(),
                    "settlementDateTo": e.isoformat(),
                    "fuelType": ["WIND"],
                },
            )
        # Forecasts published up to end of last delivery day
        for s, e in _windows(pub_from, end):
            forecasts += await _get(
                client,
                "/datasets/WINDFOR/stream",
                {
                    "publishDateTimeFrom": f"{s.isoformat()}T00:00Z",
                    "publishDateTimeTo": f"{(e + timedelta(days=1)).isoformat()}T00:00Z",
                },
            )
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "actuals": actuals,
        "forecasts": forecasts,
    }


def _normalize(raw: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    a = pd.DataFrame(raw["actuals"])
    f = pd.DataFrame(raw["forecasts"])

    if not a.empty:
        a = a[a["fuelType"] == "WIND"].copy()
        a["startTime"] = pd.to_datetime(a["startTime"], utc=True)
        a["publishTime"] = pd.to_datetime(a["publishTime"], utc=True)
        a["generation"] = pd.to_numeric(a["generation"], errors="coerce")
        a = a.dropna(subset=["startTime"])
        # One actual per half-hour: keep the latest published record
        a = (
            a.sort_values("publishTime")
            .drop_duplicates("startTime", keep="last")
            .sort_values("startTime")
            .reset_index(drop=True)
        )
    if not f.empty:
        f["startTime"] = pd.to_datetime(f["startTime"], utc=True)
        f["publishTime"] = pd.to_datetime(f["publishTime"], utc=True)
        f["generation"] = pd.to_numeric(f["generation"], errors="coerce")
        f = f.dropna(subset=["startTime", "publishTime"])
        f = (
            f.drop_duplicates(["startTime", "publishTime"], keep="last")
            .sort_values(["startTime", "publishTime"])
            .reset_index(drop=True)
        )
    return a, f


async def load_data(refresh: bool = False):
    """Return (actuals_df, forecasts_df, fetched_at). Cached in memory + on disk."""
    cache_file = config.CACHE_DIR / "elexon_raw.json"

    if not refresh and "raw" in _memory:
        raw = _memory["raw"]
    elif not refresh and cache_file.exists():
        raw = json.loads(cache_file.read_text())
        _memory["raw"] = raw
    else:
        raw = await _fetch_raw()
        try:
            config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(raw))
        except OSError as e:  # read-only FS on some hosts
            log.warning("Could not write cache: %s", e)
        _memory["raw"] = raw

    if "frames" not in _memory or _memory.get("frames_for") != raw["fetched_at"]:
        _memory["frames"] = _normalize(raw)
        _memory["frames_for"] = raw["fetched_at"]

    a, f = _memory["frames"]
    return a, f, raw["fetched_at"]