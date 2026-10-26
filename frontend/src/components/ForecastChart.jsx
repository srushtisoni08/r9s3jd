import {
  CartesianGrid, Legend, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { fmtNum, fmtTime } from "../utils/format";

export default function ForecastChart({ rows }) {
  const data = rows.map((r) => ({
    time: fmtTime(r.startTime),
    forecast: r.forecast,
    actual: r.actual,
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
        <XAxis dataKey="time" stroke="#8a99b5" interval={3} fontSize={12} />
        <YAxis
          stroke="#8a99b5" fontSize={12}
          tickFormatter={(v) => fmtNum(v)}
          label={{ value: "MW", angle: -90, position: "insideLeft", fill: "#8a99b5" }}
        />
        <Tooltip
          contentStyle={{ background: "#111a2e", border: "1px solid #22304d" }}
          formatter={(v) => (v == null ? "—" : `${fmtNum(v)} MW`)}
        />
        <Legend />
        <Line
          name="Forecast (hourly)" dataKey="forecast" stroke="#f5a524"
          strokeWidth={2} dot={{ r: 2 }} connectNulls
        />
        <Line
          name="Actual (half-hourly)" dataKey="actual" stroke="#38bdf8"
          strokeWidth={2} dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}