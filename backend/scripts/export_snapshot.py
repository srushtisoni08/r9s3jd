import asyncio
import json

from app import config
from app.services.elexon_client import _fetch_raw


async def main():
    raw = await _fetch_raw()
    config.SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.SNAPSHOT_FILE.write_text(json.dumps(raw, separators=(",", ":")))
    print("actuals:", len(raw["actuals"]), "forecasts:", len(raw["forecasts"]))


asyncio.run(main())