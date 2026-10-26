from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.api.routes import router
from app.services.elexon_client import ElexonError, load_data

app = FastAPI(title="Wind Procurement Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(ElexonError)
async def elexon_error_handler(_, exc: ElexonError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/data-status")
async def data_status(refresh: bool = False):
    actuals, forecasts, fetched_at = await load_data(refresh=refresh)
    return {
        "fetched_at": fetched_at,
        "actual_rows": len(actuals),
        "forecast_rows": len(forecasts),
        "actual_range": [
            str(actuals["startTime"].min()),
            str(actuals["startTime"].max()),
        ] if len(actuals) else None,
        "forecast_publish_range": [
            str(forecasts["publishTime"].min()),
            str(forecasts["publishTime"].max()),
        ] if len(forecasts) else None,
    }