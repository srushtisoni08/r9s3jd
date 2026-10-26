from datetime import date

import pandas as pd

from app.services.forecast_selection import (
    build_comparison,
    cutoff_for,
    select_forecasts,
)


def fc(rows):
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    return df


def act(rows):
    df = pd.DataFrame(rows, columns=["startTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df


D = date(2026, 1, 1)  # cutoff = 2025-12-31 09:00 UTC (GMT in winter)


def test_cutoff_winter_is_utc():
    assert cutoff_for(D) == pd.Timestamp("2025-12-31T09:00:00Z")


def test_cutoff_summer_respects_bst():
    # 09:00 BST == 08:00 UTC
    assert cutoff_for(date(2026, 7, 2)) == pd.Timestamp("2026-07-01T08:00:00Z")


def test_selects_latest_eligible_and_excludes_future():
    f = fc([
        ("2026-01-01T12:00Z", "2025-12-30T07:30Z", 100),
        ("2026-01-01T12:00Z", "2025-12-31T07:30Z", 200),
        ("2026-01-01T12:00Z", "2025-12-31T10:30Z", 300),  # after cutoff
    ])
    sel = select_forecasts(f, D)
    assert len(sel) == 1
    assert sel.iloc[0]["generation"] == 200


def test_publish_exactly_at_cutoff_is_eligible():
    f = fc([("2026-01-01T12:00Z", "2025-12-31T09:00Z", 150)])
    assert select_forecasts(f, D).iloc[0]["generation"] == 150


def test_january_boundary_uses_december_forecast():
    f = fc([("2026-01-01T00:00Z", "2025-12-30T20:00Z", 111)])
    sel = select_forecasts(f, D)
    assert len(sel) == 1
    assert sel.iloc[0]["publishTime"] < pd.Timestamp("2026-01-01", tz="UTC")


def test_only_future_forecasts_gives_empty():
    f = fc([("2026-01-01T12:00Z", "2025-12-31T12:00Z", 300)])
    assert select_forecasts(f, D).empty


def test_comparison_joins_on_timestamp_and_signs_error():
    f = fc([("2026-01-01T12:00Z", "2025-12-31T07:30Z", 200)])
    a = act([("2026-01-01T12:00Z", 150), ("2026-01-01T12:30Z", 160)])
    df = build_comparison(a, f, D)
    assert len(df) == 48
    assert df["forecast_slot"].sum() == 24
    row = df[df["startTime"] == pd.Timestamp("2026-01-01T12:00Z")].iloc[0]
    assert row["forecast"] == 200 and row["actual"] == 150 and row["error"] == 50
    half = df[df["startTime"] == pd.Timestamp("2026-01-01T12:30Z")].iloc[0]
    assert pd.isna(half["forecast"]) and half["actual"] == 160