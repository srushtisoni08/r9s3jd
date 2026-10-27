# Wind Procurement Intelligence

Web app that helps a UK energy utility's day-ahead desk see **which wind forecast was actually available when they had to decide**, and **how accurate it was**.

- Scope: GB national wind only, Elexon data only (`FUELHH` actuals, `WINDFOR` forecasts)
- Delivery days: 1-31 January 2026
- Stack: React (Vite, Recharts) + Python (FastAPI, pandas) + Docker

## Live Demo

- **App:** [WindProcure Dashboard](https://r9s3jd.vercel.app/)
- **API:** [Wind Forecast API](https://wind-forecast-api-srushti.vercel.app/) (try `/docs`, `/health`, `/api/accuracy`)

## AI tools disclosure

This project was built with assistance from **Claude (Anthropic)** for design discussion, code generation, debugging and documentation. All code was run, tested and reviewed by the author.

## What the app answers

1. What was the latest wind forecast available at the day-ahead decision cutoff?
2. How wrong was it? (MAE, RMSE, bias, WAPE, daily and monthly)
3. Did later forecast revisions change the picture? (forecast evolution)

## Key results (January 2026, cutoff D-1 09:00 UK time)

| Metric | Value |
|---|---|
| Coverage | 744 / 744 hourly periods |
| MAE | 2,127 MW |
| RMSE | 2,606 MW |
| Bias (forecast - actual) | +1,852 MW (systematic over-forecast) |
| WAPE | 18.4 % |

- Forecasts over-predicted wind on 27 of 31 days.
- Worst day: 28 Jan (forecast avg 11.1 GW vs actual 5.8 GW, WAPE 91.8 %).

## Method (short)

1. For each delivery day D, the decision cutoff is **D-1 at 09:00 UK local time** (DST-aware, configurable).
2. For each target period, take the **latest forecast with `publishTime <= cutoff`**. Later revisions are never used for evaluation.
3. Join to actuals on `startTime`. Error = forecast - actual (positive = over-forecast).
4. Missing values are excluded and reported as reduced coverage. They are never treated as zero.

## Project structure

```
.
├── backend/
│   ├── api/index.py                 # Vercel entrypoint
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, error handling
│   │   ├── config.py                # env-driven settings
│   │   ├── api/routes.py            # /api/* endpoints
│   │   └── services/
│   │       ├── elexon_client.py     # fetch, normalise, cache Elexon data
│   │       ├── forecast_selection.py# cutoff + latest-eligible-forecast logic
│   │       └── metrics.py           # MAE, RMSE, bias, WAPE, coverage
│   ├── data/snapshot.json           # bundled Elexon data (Jan 2026)
│   ├── scripts/export_snapshot.py   # regenerate snapshot from Elexon
│   ├── tests/                       # pytest suite
│   ├── Dockerfile
│   ├── requirements.txt / requirements-dev.txt
│   ├── pytest.ini
│   └── vercel.json
├── frontend/
│   ├── src/
│   │   ├── pages/Dashboard.jsx
│   │   ├── components/              # MetricCard, ForecastChart, ForecastTable,
│   │   │                            # ForecastEvolution, AccuracyChart
│   │   ├── services/api.js          # all backend calls
│   │   └── utils/format.js
│   ├── Dockerfile
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md
```

## Run with Docker (recommended)

Requires Docker Desktop.

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (docs at `/docs`)

Stop with `Ctrl+C`, then `docker compose down`.

## Run without Docker

Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Frontend (new terminal):

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

Covers forecast selection (cutoff, future publications, January boundary, DST), metric correctness on known values, missing data, duplicates, Elexon timeout/HTTP errors, and API validation.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /api/dates` | Delivery dates and their cutoffs |
| `GET /api/forecast?date=YYYY-MM-DD` | Selected forecast vs actual, error, metrics for one day |
| `GET /api/accuracy` | Monthly + daily metrics and error histogram |
| `GET /api/forecast-evolution?target=<ISO time>` | All forecast revisions for one period, with the eligible one marked |
| `GET /api/data-status?refresh=true` | Data row counts and ranges; `refresh=true` refetches from Elexon |

## Configuration

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `VITE_API_BASE_URL` | frontend | `http://localhost:8000` | Backend URL (baked in at build time) |
| `CORS_ORIGINS` | backend | `http://localhost:5173,http://localhost:3000` | Comma-separated allowed origins |
| `DECISION_CUTOFF` | backend | `09:00` | D-1 cutoff, UK local time (HH:MM) |
| `CACHE_DIR` | backend | `/tmp/wind_cache` | Runtime cache location |

## Deployment (Vercel, free tier)

Two Vercel projects from this repo:

1. **Backend:** Root Directory `backend`, preset "Other". Env: `CORS_ORIGINS=<frontend url>`.
2. **Frontend:** Root Directory `frontend`, preset Vite. Env: `VITE_API_BASE_URL=<backend url>`.
3. Disable Deployment Protection on both so the links are public.

Docker is used for local reproducibility. Vercel deploys the backend with its own Python runtime.

## Data and assumptions

- **WINDFOR is hourly**, FUELHH is half-hourly. Forecast accuracy is evaluated on the **hourly forecast grid** (24 periods/day, 744/month). Half-hourly actuals are still plotted. Forecasts are never interpolated.
- **Cutoff is an assumption:** D-1 09:00 UK time, set before the day-ahead auction closes. Configurable via `DECISION_CUTOFF`. To be confirmed with the product manager.
- Forecasts published from 25 Dec 2025 are fetched so 1 Jan can use December forecasts.
- Duplicate actuals: latest `publishTime` wins. Duplicate forecasts: last record wins.
- The deployed backend serves a **bundled snapshot** (`backend/data/snapshot.json`, fetched from Elexon on the date shown in the app's "retrieved" timestamp) for fast, reliable cold starts. Regenerate with `python -m scripts.export_snapshot` from `backend/`, or call `/api/data-status?refresh=true`.

## Limitations

- No demand data (out of scope), so the app reports wind forecast error, not residual demand or cost.
- Single fixed cutoff for all days (not per-market-product).
- Historical analysis only; no live refresh schedule.
- In-memory cache per serverless instance; no database or authentication, by design for this scope.

## Possible next steps

- Configurable cutoff in the UI, plus an error-by-hour-of-day view.
- Reserve-margin suggestion from error quantiles (e.g. P90 under-delivery) per delivery hour.
- Add demand and price data to translate MW error into procurement cost.