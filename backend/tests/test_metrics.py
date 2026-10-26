import numpy as np
import pandas as pd

from app.services.metrics import compute_metrics


def frame(forecast, actual):
    df = pd.DataFrame({"forecast": forecast, "actual": actual})
    df["error"] = df["forecast"] - df["actual"]
    df["forecast_slot"] = True
    return df


def test_known_values():
    m = compute_metrics(frame([110, 90], [100, 100]))
    assert m["mae_mw"] == 10
    assert m["rmse_mw"] == 10
    assert m["bias_mw"] == 0
    assert m["wape_pct"] == 10
    assert m["matched_periods"] == 2
    assert m["coverage_pct"] == 100


def test_positive_bias_means_over_forecast():
    assert compute_metrics(frame([120, 130], [100, 100]))["bias_mw"] == 25


def test_missing_actual_excluded_and_coverage_reduced():
    m = compute_metrics(frame([110, 90, 50], [100, 100, np.nan]))
    assert m["matched_periods"] == 2
    assert m["missing_actuals"] == 1
    assert m["expected_periods"] == 3
    assert m["coverage_pct"] == 66.67
    assert m["mae_mw"] == 10  # missing never treated as zero


def test_missing_forecast_excluded():
    m = compute_metrics(frame([np.nan, 90], [100, 100]))
    assert m["matched_periods"] == 1
    assert m["missing_forecasts"] == 1


def test_zero_actual_in_one_period_wape_still_defined():
    m = compute_metrics(frame([10, 100], [0, 100]))
    assert m["wape_pct"] == 10


def test_all_zero_actuals_wape_none():
    m = compute_metrics(frame([10], [0]))
    assert m["wape_pct"] is None
    assert m["mae_mw"] == 10


def test_no_matches():
    m = compute_metrics(frame([np.nan], [np.nan]))
    assert m["matched_periods"] == 0
    assert m["mae_mw"] is None


def test_half_hour_slots_ignored_in_metrics():
    df = frame([110, 999], [100, 0])
    df["forecast_slot"] = [True, False]
    m = compute_metrics(df)
    assert m["expected_periods"] == 1
    assert m["mae_mw"] == 10