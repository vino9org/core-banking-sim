from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FundTransferRequest(BaseModel):
    debit_customer_id: str
    debit_account_id: str
    credit_account_id: str
    amount: Decimal
    currency: str
    transaction_date: str
    memo: str
    limits_req_id: str


class FundTransfer(BaseModel):
    transaction_id: str
    debit_customer_id: str
    debit_account_id: str
    currency: str
    credit_customer_id: str
    credit_account_id: str
    transfer_amount: Decimal
    memo: str
    transaction_date: str
    debit_prev_balance: Decimal
    debit_prev_avail_balance: Decimal
    debit_balance: Decimal
    debit_avail_balance: Decimal
    credit_prev_balance: Decimal
    credit_prev_avail_balance: Decimal
    credit_balance: Decimal
    credit_avail_balance: Decimal
    status: str
    limits_req_id: str


class CheckingAccount(BaseModel):
    customer_id: str
    account_id: str
    currency: str
    balance: Decimal
    avail_balance: Decimal
    status: str
    updated_at: datetime = datetime.now()
