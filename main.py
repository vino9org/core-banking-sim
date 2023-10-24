import asyncio
import logging
import os
import sys
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi_utils.tasks import repeat_every

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=logging.getLevelName(LOG_LEVEL), format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


logger = logging.getLogger(__name__)

# import after init logger in order to print log entries in the initialization code
from core_banking import ValidationError, eventing, ledger, local_transfer, models  # noqa

app = FastAPI()


@app.get("/healthz")
async def health():
    return "running"


@app.get("/ready")
async def ready():
    return "ready"


@app.get("/core-banking/accounts/{account_id}", response_model=models.CheckingAccount)
async def account_detail(account_id: str):
    account = await ledger.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return account


@app.post("/core-banking/local-transfers", response_model=models.FundTransfer)
async def new_local_transfer(request: models.FundTransferRequest, response: Response) -> Optional[models.FundTransfer]:
    logger.info("processing request: %s", request)
    try:
        return await local_transfer(request)
    except ValidationError:
        raise HTTPException(status_code=422, detail="validation error for the request")


@app.on_event("startup")
@repeat_every(seconds=2)
async def flush_event_queue():
    logger.info(f"flusing {await eventing.send_events(5000)} events")


@app.on_event("shutdown")
async def flush_event_queue_at_shutdown():
    logger.info(f"flusing {await eventing.send_events(20000)} events before shutting down")


def start_server(port: int = 8000, n_workers: int = 1):
    # override default log format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["access"]["datefmt"] = LOG_DATE_FORMAT
    log_config["formatters"]["default"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["default"]["datefmt"] = LOG_DATE_FORMAT

    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=n_workers)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--seed":
        csv_f = open(sys.argv[2], "r")
        asyncio.run(ledger.init_from_csv(csv_f))
        csv_f.close()
    else:
        start_server()
