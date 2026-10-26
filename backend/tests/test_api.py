import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.elexon_client import ElexonError

client = TestClient(app)


@pytest.fixture
def empty_data(monkeypatch):
    async def fake(refresh=False):
        e = pd.DataFrame(columns=["startTime", "publishTime", "generation"])
        return e, e.copy(), "2026-01-01T00:00:00+00:00"

    monkeypatch.setattr("app.api.routes.load_data", fake)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_dates_lists_31_days():
    assert len(client.get("/api/dates").json()["dates"]) == 31


def test_invalid_date_format_422():
    assert client.get("/api/forecast?date=not-a-date").status_code == 422


def test_out_of_range_date_422():
    r = client.get("/api/forecast?date=2026-02-01")
    assert r.status_code == 422
    assert "between" in r.json()["detail"]


def test_elexon_failure_returns_502(monkeypatch):
    async def boom(refresh=False):
        raise ElexonError("Elexon API timed out")

    monkeypatch.setattr("app.api.routes.load_data", boom)
    r = client.get("/api/forecast?date=2026-01-01")
    assert r.status_code == 502
    assert "timed out" in r.json()["detail"]


def test_no_data_returns_zero_coverage_not_crash(empty_data):
    r = client.get("/api/forecast?date=2026-01-01")
    assert r.status_code == 200
    m = r.json()["metrics"]
    assert m["matched_periods"] == 0
    assert m["coverage_pct"] == 0
    assert m["mae_mw"] is None