from datetime import date as date_type
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app import config
from app.services.elexon_client import load_data
from app.services.forecast_selection import build_comparison, cutoff_for
from app.services.metrics import compute_metrics

router = APIRouter(prefix="/api")

START = date_type.fromisoformat(config.DELIVERY_START)
END = date_type.fromisoformat(config.DELIVERY_END)


def _all_days() -> list[date_type]:
    return [d.date() for d in pd.date_range(START, END)]


def _validate(d: date_type) -> None:
    if not (START <= d <= END):
        raise HTTPException(
            status_code=422,
            detail=f"date must be between {START} and {END}",
        )


def _iso(ts) -> str | None:
    return None if pd.isna(ts) else ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    for col in ("startTime", "publishTime"):
        if col in out:
            out[col] = out[col].map(_iso)
    out = out.astype(object).where(out.notna(), None)
    return out.to_dict("records")


def _cutoff_info(d: date_type) -> dict:
    c = cutoff_for(d)
    return {
        "cutoff_utc": c.isoformat(),
        "cutoff_local": c.tz_convert(config.UK_TZ).isoformat(),
    }


@router.get("/dates")
def dates():
    return {
        "dates": [{"date": d.isoformat(), **_cutoff_info(d)} for d in _all_days()]
    }


@router.get("/forecast")
async def forecast(delivery_date: date_type = Query(..., alias="date")):
    _validate(delivery_date)
    actuals, forecasts, fetched_at = await load_data()
    df = build_comparison(actuals, forecasts, delivery_date)
    return {
        "date": delivery_date.isoformat(),
        **_cutoff_info(delivery_date),
        "fetched_at": fetched_at,
        "source": "Elexon BMRS (FUELHH, WINDFOR)",
        "unit": "MW",
        "metrics": compute_metrics(df),
        "rows": _records(df),
    }


@router.get("/accuracy")
async def accuracy(
    delivery_date: date_type | None = Query(None, alias="date"),
):
    actuals, forecasts, fetched_at = await load_data()

    daily, frames = [], []
    for d in _all_days():
        df = build_comparison(actuals, forecasts, d)
        frames.append(df)
        daily.append({"date": d.isoformat(), **compute_metrics(df)})

    month = pd.concat(frames, ignore_index=True)
    valid_err = month["error"].dropna()
    if len(valid_err):
        counts, edges = np.histogram(valid_err, bins=20)
        hist = [
            {"from_mw": round(float(edges[i]), 1), "to_mw": round(float(edges[i + 1]), 1), "count": int(counts[i])}
            for i in range(len(counts))
        ]
    else:
        hist = []

    result = {
        "fetched_at": fetched_at,
        "cutoff_rule": f"D-1 {config.DECISION_CUTOFF} UK local time",
        "unit": "MW",
        "monthly": compute_metrics(month),
        "daily": daily,
        "error_histogram": hist,
    }
    if delivery_date:
        _validate(delivery_date)
        result["selected_day"] = next(x for x in daily if x["date"] == delivery_date.isoformat())
    return result


@router.get("/forecast-evolution")
async def forecast_evolution(target: datetime = Query(..., description="Delivery startTime, ISO")):
    t = pd.Timestamp(target)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    d = t.tz_convert(config.UK_TZ).date()
    _validate(d)

    actuals, forecasts, fetched_at = await load_data()
    cutoff = cutoff_for(d)

    rows = forecasts[forecasts["startTime"] == t].sort_values("publishTime").copy()
    rows["eligible"] = rows["publishTime"] <= cutoff
    selected_pub = rows.loc[rows["eligible"], "publishTime"].max() if len(rows) else pd.NaT
    rows["selected"] = rows["publishTime"] == selected_pub
    rows = rows[["publishTime", "generation", "eligible", "selected"]]

    a = actuals[actuals["startTime"] == t]["generation"] if len(actuals) else []
    actual = float(a.iloc[0]) if len(a) else None

    return {
        "target": _iso(t),
        "delivery_date": d.isoformat(),
        **_cutoff_info(d),
        "fetched_at": fetched_at,
        "actual_mw": actual,
        "forecasts": _records(rows),
    }