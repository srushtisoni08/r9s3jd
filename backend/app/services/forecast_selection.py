from datetime import date, datetime, time, timedelta

import pandas as pd

from app import config


def _utc(ts: datetime) -> pd.Timestamp:
    return pd.Timestamp(ts).tz_convert("UTC")


def cutoff_for(delivery_date: date) -> pd.Timestamp:
    """Decision cutoff = D-1 at DECISION_CUTOFF, UK local time, returned in UTC."""
    hh, mm = map(int, config.DECISION_CUTOFF.split(":"))
    local = datetime.combine(
        delivery_date - timedelta(days=1), time(hh, mm), tzinfo=config.UK_TZ
    )
    return _utc(local)


def day_bounds(delivery_date: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[start, end) of a UK-local delivery day, in UTC."""
    start = datetime.combine(delivery_date, time(0, 0), tzinfo=config.UK_TZ)
    end = datetime.combine(
        delivery_date + timedelta(days=1), time(0, 0), tzinfo=config.UK_TZ
    )
    return _utc(start), _utc(end)


def select_forecasts(forecasts: pd.DataFrame, delivery_date: date) -> pd.DataFrame:
    """Per half-hour: latest forecast published at or before the cutoff."""
    cols = ["startTime", "publishTime", "generation"]
    if forecasts.empty:
        return pd.DataFrame(columns=cols)
    start, end = day_bounds(delivery_date)
    cutoff = cutoff_for(delivery_date)
    day = forecasts[(forecasts["startTime"] >= start) & (forecasts["startTime"] < end)]
    eligible = day[day["publishTime"] <= cutoff]
    return (
        eligible.sort_values(["startTime", "publishTime"])
        .drop_duplicates("startTime", keep="last")[cols]
        .reset_index(drop=True)
    )


def build_comparison(
    actuals: pd.DataFrame, forecasts: pd.DataFrame, delivery_date: date
) -> pd.DataFrame:
    """One row per half-hour slot. WINDFOR is hourly, so only :00 slots
    are expected to carry a forecast (forecast_slot=True)."""
    start, end = day_bounds(delivery_date)
    slots = pd.DataFrame(
        {"startTime": pd.date_range(start, end, freq="30min", inclusive="left")}
    )

    sel = select_forecasts(forecasts, delivery_date).rename(
        columns={"generation": "forecast"}
    )
    if actuals.empty:
        act = pd.DataFrame(columns=["startTime", "actual"])
    else:
        act = actuals[(actuals["startTime"] >= start) & (actuals["startTime"] < end)][
            ["startTime", "generation"]
        ].rename(columns={"generation": "actual"})

    for frame in (slots, sel, act):
        frame["startTime"] = pd.to_datetime(frame["startTime"], utc=True).astype(
            "datetime64[ns, UTC]"
        )

    df = slots.merge(sel, on="startTime", how="left").merge(act, on="startTime", how="left")
    df["forecast"] = pd.to_numeric(df["forecast"])
    df["actual"] = pd.to_numeric(df["actual"])
    df["error"] = df["forecast"] - df["actual"]  # + = over-forecast
    df["forecast_slot"] = df["startTime"].dt.minute == 0
    return df