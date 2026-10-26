const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString();
  let res;
  try {
    res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`);
  } catch {
    throw new Error("Cannot reach the backend. Is it running?");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const getDates = () => get("/api/dates");
export const getForecast = (date) => get("/api/forecast", { date });
export const getAccuracy = () => get("/api/accuracy");
export const getForecastEvolution = (target) =>
  get("/api/forecast-evolution", { target });