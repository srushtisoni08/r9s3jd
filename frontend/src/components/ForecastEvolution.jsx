import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid, ComposedChart, Line, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { getForecastEvolution } from "../services/api";
import { fmtDateTime, fmtNum, fmtTime } from "../utils/format";
import MetricCard from "./MetricCard";

const COLORS = { selected: "#f5a524", earlier: "#8a99b5", later: "#f87171" };

export default function ForecastEvolution({ date, rows }) {
  const slots = useMemo(() => rows.filter((r) => r.forecast_slot), [rows]);
  const [target, setTarget] = useState(null);
  const [evo, setEvo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setTarget(slots[12]?.startTime ?? slots[0]?.startTime ?? null);
  }, [date, slots]);

  useEffect(() => {
    if (!target) return;
    let cancelled = false;
    setError(null);
    getForecastEvolution(target)
      .then((d) => !cancelled && setEvo(d))
      .catch((e) => !cancelled && setError(e.message));
    return () => { cancelled = true; };
  }, [target]);

  const points = (evo?.forecasts ?? []).map((f) => ({
    t: new Date(f.publishTime).getTime(),
    generation: f.generation,
    kind: f.selected ? "selected" : f.eligible ? "earlier" : "later",
  }));
  const cutoffMs = evo ? new Date(evo.cutoff_utc).getTime() : null;
  const selected = points.find((p) => p.kind === "selected");
  const latest = points[points.length - 1];

  const renderDot = ({ cx, cy, payload }) =>
    cx == null || cy == null ? null : (
      <circle
        key={payload.t} cx={cx} cy={cy}
        r={payload.kind === "selected" ? 7 : 4}
        fill={COLORS[payload.kind]}
      />
    );

  return (
    <>
      <label className="toggle">
        Delivery period:
        <select value={target ?? ""} onChange={(e) => setTarget(e.target.value)}>
          {slots.map((s) => (
            <option key={s.startTime} value={s.startTime}>{fmtTime(s.startTime)}</option>
          ))}
        </select>
      </label>

      {error && <div className="banner error">{error}</div>}

      {evo && points.length === 0 && (
        <div className="banner warn">No forecasts were published for this period.</div>
      )}

      {evo && points.length > 0 && (
        <>
          <div className="grid">
            <MetricCard
              label="Forecast at cutoff"
              value={selected ? fmtNum(selected.generation) : null}
              unit="MW"
              hint={selected ? `Published ${fmtDateTime(new Date(selected.t).toISOString())}` : "None before cutoff"}
            />
            <MetricCard
              label="Latest forecast"
              value={fmtNum(latest.generation)}
              unit="MW"
              hint={`Published ${fmtDateTime(new Date(latest.t).toISOString())}`}
            />
            <MetricCard label="Actual" value={fmtNum(evo.actual_mw)} unit="MW" />
            <MetricCard label="Revisions" value={points.length} hint="Forecasts published for this period" />
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={points} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
              <XAxis
                dataKey="t" type="number" scale="time"
                domain={["dataMin", "dataMax"]}
                tickFormatter={(v) => fmtDateTime(new Date(v).toISOString())}
                stroke="#8a99b5" fontSize={12}
              />
              <YAxis stroke="#8a99b5" fontSize={12} tickFormatter={(v) => fmtNum(v)} domain={["auto", "auto"]} />
              <Tooltip
                contentStyle={{ background: "#111a2e", border: "1px solid #22304d" }}
                labelFormatter={(v) => `Published ${fmtDateTime(new Date(v).toISOString())}`}
                formatter={(v) => [`${fmtNum(v)} MW`, "Forecast"]}
              />
              <ReferenceLine x={cutoffMs} stroke="#fbbf24" strokeDasharray="4 4"
                label={{ value: "Cutoff", fill: "#fbbf24", fontSize: 12, position: "top" }} />
              {evo.actual_mw != null && (
                <ReferenceLine y={evo.actual_mw} stroke="#38bdf8" strokeDasharray="4 4"
                  label={{ value: "Actual", fill: "#38bdf8", fontSize: 12, position: "insideTopRight" }} />
              )}
              <Line dataKey="generation" stroke="#8a99b5" strokeWidth={1} dot={renderDot} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>

          <div className="desc" style={{ marginTop: 8 }}>
            <span style={{ color: COLORS.selected }}>●</span> used for the decision &nbsp;
            <span style={{ color: COLORS.earlier }}>●</span> earlier, superseded &nbsp;
            <span style={{ color: COLORS.later }}>●</span> published after cutoff (not available when deciding)
          </div>
        </>
      )}
    </>
  );
}