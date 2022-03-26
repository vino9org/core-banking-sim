import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI, Response
from fastapi_utils.tasks import repeat_every

from core_banking import eventing, local_transfer, models

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/healthz")
async def health():
    return "running"


@app.get("/ready")
async def ready():
    return "ready"


@app.post("/core-banking/local-transfers", response_model=models.FundTransfer)
async def new_local_transfer(request: models.FundTransferRequest, response: Response) -> Optional[models.FundTransfer]:
    logger.info("processing request: ", request)
    transfer = await local_transfer(request)
    response.status_code = 200 if transfer else 400
    return transfer


@app.on_event("startup")
@repeat_every(seconds=5)
async def flush_event_queue():
    await eventing.send_events(100)


@app.on_event("shutdown")
async def flush_event_queue_at_shutdown():
    logger.info("...shutting down...")
    await eventing.send_events(2000)
    await eventing.send_events(2000)


if __name__ == "__main__":
    # override default log format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["access"]["datefmt"] = LOG_DATE_FORMAT
    log_config["formatters"]["default"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["default"]["datefmt"] = LOG_DATE_FORMAT

    uvicorn.run(app, host="0.0.0.0", port=8000)
