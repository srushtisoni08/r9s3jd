export default function MetricCard({ label, value, unit, hint }) {
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div className="value">
        {value ?? "—"}
        {value != null && unit && <small>{unit}</small>}
      </div>
      {hint && <div className="hint">{hint}</div>}
    </div>
  );
}