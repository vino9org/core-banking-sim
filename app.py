from decimal import Decimal

import ulid
from fastapi import FastAPI
from pydantic import BaseModel


class FundTransferRequest(BaseModel):
    customer_id: str
    account_id: str
    credit_account_id: str
    amount: Decimal
    currency: str
    transaction_date: str
    memo: str
    limits_req_id: str


app = FastAPI()


@app.get("/healthz")
async def health():
    return "running"


@app.get("/ready")
async def ready():
    return "readu"


@app.post("/core-banking/local-transfers")
def local_trnasfer(request: FundTransferRequest):
    print(f"type={type(request.amount)}, value={request.amount}")
    return {
        "transaction_id": str(ulid.new()),
        "customer_id": request.customer_id,
        "account_id": request.account_id,
        "currency": request.currency,
        "ledger_balance": Decimal(1000),
        "avail_balance": Decimal(1000),
    }
