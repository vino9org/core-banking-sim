from datetime import datetime
from decimal import Decimal

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


class FundTransfer(BaseModel):
    transaction_id: str
    customer_id: str
    account_id: str
    currency: str
    credit_account_id: str
    transfer_amount: Decimal
    memo: str
    transaction_date: str
    prev_balance: Decimal
    prev_avail_balance: Decimal
    new_balance: Decimal
    new_avail_balance: Decimal
    status: str
    limits_req_id: str


class CheckingAccount(BaseModel):
    customer_id: str
    account_id: str
    balance: Decimal
    avail_balance: Decimal
    status: str
    updated_at: datetime = datetime.now()
