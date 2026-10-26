import numpy as np
import pandas as pd


def _r(x, nd=2):
    return None if x is None or pd.isna(x) else round(float(x), nd)


def compute_metrics(df: pd.DataFrame) -> dict:
    """Units: MW. Error = forecast - actual.
    Evaluated on the forecast grid only (WINDFOR is hourly, so :00 slots)."""
    grid = df[df["forecast_slot"]] if "forecast_slot" in df.columns else df
    expected = len(grid)
    valid = grid.dropna(subset=["forecast", "actual"])
    n = len(valid)

    out = {
        "forecast_resolution": "hourly (WINDFOR)",
        "expected_periods": expected,
        "matched_periods": n,
        "missing_forecasts": int(grid["forecast"].isna().sum()),
        "missing_actuals": int(grid["actual"].isna().sum()),
        "coverage_pct": _r(100 * n / expected) if expected else None,
        "mae_mw": None,
        "rmse_mw": None,
        "bias_mw": None,
        "wape_pct": None,
        "avg_forecast_mw": None,
        "avg_actual_mw": None,
    }
    if n == 0:
        return out

    e = valid["error"]
    total_actual = valid["actual"].sum()
    out.update(
        mae_mw=_r(e.abs().mean()),
        rmse_mw=_r(np.sqrt((e**2).mean())),
        bias_mw=_r(e.mean()),
        wape_pct=_r(100 * e.abs().sum() / total_actual) if total_actual > 0 else None,
        avg_forecast_mw=_r(valid["forecast"].mean()),
        avg_actual_mw=_r(valid["actual"].mean()),
    )
    return out