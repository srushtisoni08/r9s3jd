import { useEffect, useState } from "react";
import { getForecast } from "./services/api";

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getForecast("2026-01-01").then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <p>Error: {error}</p>;
  if (!data) return <p>Loading...</p>;
  return (
    <pre>{JSON.stringify(data.metrics, null, 2)}</pre>
  );
}