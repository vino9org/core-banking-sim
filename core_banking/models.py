from datetime import datetime
from decimal import Decimal
from enum import Enum, IntEnum

from pydantic import BaseModel
from redis_om import HashModel


class FundTransferRequest(BaseModel):
    req_id: str
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
    debit_prev_balance: Decimal
    debit_prev_avail_balance: Decimal
    debit_balance: Decimal
    debit_avail_balance: Decimal

    credit_customer_id: str
    credit_account_id: str
    credit_prev_balance: Decimal
    credit_prev_avail_balance: Decimal
    credit_balance: Decimal
    credit_avail_balance: Decimal

    transfer_amount: Decimal
    currency: str
    memo: str
    transaction_date: str
    status: str

    limits_req_id: str


class AccountCurrency(Enum):
    USD = "USD"
    SGD = "SGD"
    THB = "THB"
    PHP = "PHP"
    VND = "VND"
    MYR = "MYR"
    IDR = "IDR"
    INR = "INR"


class AccountStatus(IntEnum):
    active = 1
    inactive = 0


class CheckingAccount(HashModel):
    customer_id: str
    account_id: str
    currency: AccountCurrency
    balance: Decimal
    avail_balance: Decimal
    status: AccountStatus
    updated_at: datetime = datetime.now()
