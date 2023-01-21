import codecs
import logging
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Response, UploadFile
from fastapi_cprofile.profiler import CProfileMiddleware
from fastapi_utils.tasks import repeat_every

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

logger = logging.getLogger(__name__)

# import after init logger in order to print log entries in the initialization code
from core_banking import ValidationError, eventing, ledger, local_transfer, models  # noqa

app = FastAPI()
if os.environ.get("ENABLE_PROFILING", "") == "1":
    app.add_middleware(
        CProfileMiddleware,
        enable=True,
        print_each_request=False,
        strip_dirs=False,
        server_app=app,
        filename="/tmp/core-banking-sim.pstats",
        sort_by="cumulative",
    )


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


@app.post("/core-banking/_internal/seed/")
async def seed_account_data(upload_file: UploadFile) -> None:
    logger.info("seed account data")
    await ledger.init_from_csv(codecs.iterdecode(upload_file.file, "utf-8"))
    logger.info("seed account data done")


@app.on_event("startup")
@repeat_every(seconds=2)
async def flush_event_queue():
    await eventing.send_events(5000)


@app.on_event("shutdown")
async def flush_event_queue_at_shutdown():
    logger.info("flusing events before shutting down")
    await eventing.send_events(20000)
    await eventing.send_events(20000)


if __name__ == "__main__":
    # override default log format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["access"]["datefmt"] = LOG_DATE_FORMAT
    log_config["formatters"]["default"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["default"]["datefmt"] = LOG_DATE_FORMAT

    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
