import uvicorn
from fastapi import FastAPI

from core_banking import models

app = FastAPI()


@app.get("/healthz")
async def health():
    return "running"


@app.get("/ready")
async def ready():
    return "ready"


@app.post("/core-banking/local-transfers")
def new_local_transfer(request: models.FundTransferRequest) -> models.FundTransfer:
    pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
