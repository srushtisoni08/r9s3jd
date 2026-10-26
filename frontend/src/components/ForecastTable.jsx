import { useState } from "react";
import { fmtDateTime, fmtNum, fmtTime } from "../utils/format";

export default function ForecastTable({ rows }) {
  const [hourlyOnly, setHourlyOnly] = useState(true);
  const shown = hourlyOnly ? rows.filter((r) => r.forecast_slot) : rows;

  return (
    <>
      <label className="toggle">
        <input
          type="checkbox"
          checked={hourlyOnly}
          onChange={(e) => setHourlyOnly(e.target.checked)}
        />
        Forecast periods only (WINDFOR is hourly)
      </label>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Delivery time</th>
              <th>Forecast published</th>
              <th>Forecast (MW)</th>
              <th>Actual (MW)</th>
              <th>Error (MW)</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) => (
              <tr key={r.startTime}>
                <td>{fmtTime(r.startTime)}</td>
                <td className="dim">{fmtDateTime(r.publishTime)}</td>
                <td>{fmtNum(r.forecast)}</td>
                <td>{fmtNum(r.actual)}</td>
                <td className={r.error > 0 ? "over" : r.error < 0 ? "under" : ""}>
                  {r.error == null ? "—" : `${r.error > 0 ? "+" : ""}${fmtNum(r.error)}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}