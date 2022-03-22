import uvicorn
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from core_banking import eventing, models

app = FastAPI()


@app.get("/healthz")
async def health():
    return "running"


@app.get("/ready")
async def ready():
    return "ready"


@app.post("/core-banking/local-transfers")
async def new_local_transfer(request: models.FundTransferRequest) -> models.FundTransfer:
    pass


@app.on_event("startup")
@repeat_every(seconds=5)
async def flush_event_queue():
    await eventing.send_events(100)


@app.on_event("shutdown")
async def flush_event_queue_at_shutdown():
    print("...shutting down...")
    await eventing.send_events(2000)
    await eventing.send_events(2000)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
