import { useEffect, useState } from "react";
import { getDates, getForecast } from "../services/api";
import MetricCard from "../components/MetricCard";
import ForecastChart from "../components/ForecastChart";
import ForecastTable from "../components/ForecastTable";
import { fmtDateTime, fmtNum } from "../utils/format";

export default function Dashboard() {
  const [dates, setDates] = useState([]);
  const [date, setDate] = useState("2026-01-01");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDates().then((d) => setDates(d.dates)).catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getForecast(date)
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [date]);

  const m = data?.metrics;

  return (
    <div className="container">
      <div className="header">
        <div>
          <h1>Wind Procurement Intelligence</h1>
          <div className="sub">GB national wind generation · January 2026 delivery days</div>
        </div>
        <select value={date} onChange={(e) => setDate(e.target.value)}>
          {(dates.length ? dates.map((d) => d.date) : [date]).map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      {error && <div className="banner error">{error}</div>}
      {loading && !data && <div className="banner">Loading data from Elexon…</div>}

      {data && (
        <>
          <div className="banner">
            Decision cutoff: <b>{fmtDateTime(data.cutoff_local)}</b> (UK time, day before delivery).
            Each forecast shown is the latest published at or before this cutoff.
            Source: {data.source} · retrieved {fmtDateTime(data.fetched_at)}.
          </div>

          {m.coverage_pct < 100 && (
            <div className="banner warn">
              Only {m.matched_periods} of {m.expected_periods} forecast periods could be matched
              ({m.missing_forecasts} missing forecasts, {m.missing_actuals} missing actuals).
              Metrics exclude missing periods.
            </div>
          )}

          <div className="grid" style={{ opacity: loading ? 0.5 : 1 }}>
            <MetricCard label="MAE" value={fmtNum(m.mae_mw)} unit="MW" hint="Mean absolute error" />
            <MetricCard label="RMSE" value={fmtNum(m.rmse_mw)} unit="MW" hint="Penalises large misses" />
            <MetricCard
              label="Bias"
              value={m.bias_mw == null ? null : `${m.bias_mw > 0 ? "+" : ""}${fmtNum(m.bias_mw)}`}
              unit="MW"
              hint={m.bias_mw > 0 ? "Over-forecast: wind lower than expected" : "Under-forecast"}
            />
            <MetricCard label="WAPE" value={fmtNum(m.wape_pct, 1)} unit="%" hint="Total abs. error / total actual" />
            <MetricCard
              label="Coverage"
              value={`${m.matched_periods} / ${m.expected_periods}`}
              hint="Hourly forecast periods matched"
            />
          </div>

          <div className="panel">
            <h2>Forecast vs actual</h2>
            <div className="desc">
              Forecast available at cutoff vs actual wind generation. Forecasts are hourly;
              actuals are half-hourly. Error = forecast − actual.
            </div>
            <ForecastChart rows={data.rows} />
          </div>

          <div className="panel">
            <h2>Forecast details</h2>
            <div className="desc">Positive error (red) = forecast higher than actual.</div>
            <ForecastTable rows={data.rows} />
          </div>
        </>
      )}
    </div>
  );
}