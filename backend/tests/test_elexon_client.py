import httpx
import pytest

from app.services.elexon_client import ElexonError, _get, _normalize


def raw(actuals=None, forecasts=None):
    return {"fetched_at": "x", "actuals": actuals or [], "forecasts": forecasts or []}


async def test_timeout_becomes_elexon_error():
    def handler(request):
        raise httpx.ReadTimeout("boom")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(ElexonError, match="timed out"):
            await _get(c, "/x", {})


async def test_http_error_becomes_elexon_error():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(500))
    ) as c:
        with pytest.raises(ElexonError, match="500"):
            await _get(c, "/x", {})


def test_actual_duplicates_keep_latest_publish():
    a = [
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z",
         "publishTime": "2026-01-01T00:30:00Z", "generation": 100},
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z",
         "publishTime": "2026-01-01T01:00:00Z", "generation": 120},
        {"fuelType": "CCGT", "startTime": "2026-01-01T00:00:00Z",
         "publishTime": "2026-01-01T01:00:00Z", "generation": 999},
    ]
    actuals, _ = _normalize(raw(actuals=a))
    assert len(actuals) == 1
    assert actuals.iloc[0]["generation"] == 120


def test_forecast_duplicates_and_nulls_cleaned():
    f = [
        {"startTime": "2026-01-01T00:00:00Z", "publishTime": "2025-12-31T07:30:00Z", "generation": 1},
        {"startTime": "2026-01-01T00:00:00Z", "publishTime": "2025-12-31T07:30:00Z", "generation": 2},
        {"startTime": "2026-01-01T01:00:00Z", "publishTime": "2025-12-31T07:30:00Z", "generation": None},
    ]
    _, forecasts = _normalize(raw(forecasts=f))
    assert len(forecasts) == 2
    assert forecasts.iloc[0]["generation"] == 2  # last record wins (deterministic)
    assert forecasts["generation"].isna().sum() == 1