import {
  Bar, BarChart, CartesianGrid, Cell, Legend,
  ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { fmtNum } from "../utils/format";

const tip = {
  contentStyle: { background: "#111a2e", border: "1px solid #22304d" },
  formatter: (v) => (v == null ? "—" : `${fmtNum(v)}`),
};
const axis = { stroke: "#8a99b5", fontSize: 12 };
const shortDay = (d) => d.slice(8);
const pick = (d) => d?.date ?? d?.payload?.date;

export function DailyBiasChart({ daily, selected, onSelect }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={daily} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
        <XAxis dataKey="date" tickFormatter={shortDay} {...axis} />
        <YAxis tickFormatter={(v) => fmtNum(v)} {...axis} />
        <Tooltip {...tip} labelFormatter={(l) => l} />
        <ReferenceLine y={0} stroke="#8a99b5" />
        <Bar
          name="Bias (MW)" dataKey="bias_mw" cursor="pointer"
          onClick={(d) => onSelect(pick(d))}
        >
          {daily.map((d) => (
            <Cell
              key={d.date}
              fill={d.bias_mw > 0 ? "#f87171" : "#34d399"}
              fillOpacity={d.date === selected ? 1 : 0.65}
              stroke={d.date === selected ? "#e6ecf5" : "none"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DailyMaeChart({ daily, selected, onSelect }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={daily} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
        <XAxis dataKey="date" tickFormatter={shortDay} {...axis} />
        <YAxis tickFormatter={(v) => fmtNum(v)} {...axis} />
        <Tooltip {...tip} labelFormatter={(l) => l} />
        <Legend />
        <Bar
          name="MAE (MW)" dataKey="mae_mw" fill="#38bdf8" cursor="pointer"
          onClick={(d) => onSelect(pick(d))}
        />
        <Bar
          name="RMSE (MW)" dataKey="rmse_mw" fill="#a78bfa" cursor="pointer"
          onClick={(d) => onSelect(pick(d))}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ErrorHistogram({ bins }) {
  const data = bins.map((b) => ({
    label: fmtNum((b.from_mw + b.to_mw) / 2),
    mid: (b.from_mw + b.to_mw) / 2,
    count: b.count,
  }));
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
        <XAxis dataKey="label" interval={2} {...axis} />
        <YAxis {...axis} />
        <Tooltip
          contentStyle={tip.contentStyle}
          formatter={(v) => [v, "Hours"]}
          labelFormatter={(l) => `Error ≈ ${l} MW`}
        />
        <Bar dataKey="count" name="Hours">
          {data.map((d, i) => (
            <Cell key={i} fill={d.mid > 0 ? "#f87171" : "#34d399"} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}