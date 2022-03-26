import csv
from datetime import datetime
from decimal import Decimal
from threading import Lock
from typing import Optional

import ulid

from .models import CheckingAccount

_ledger_: dict[str, CheckingAccount] = {}

mutex = Lock()


def init_from_csv(csv_file: str) -> None:
    global _ledger_
    with open(csv_file) as f:
        for row in csv.DictReader(f):
            acc_id = row["acc_id"]
            _ledger_[acc_id] = CheckingAccount(
                customer_id=row["cust_id"],
                account_id=row["acc_id"],
                currency=row["currency"],
                avail_balance=Decimal(row["balance"]),
                balance=Decimal(row["balance"]),
                status=row["status"],
            )


async def get_account(account_id: str) -> Optional[CheckingAccount]:
    global _ledger_
    return _ledger_[account_id] if account_id in _ledger_ else None


async def transfer(debit_acc: CheckingAccount, credit_acc: CheckingAccount, amount: Decimal) -> Optional[str]:
    global _ledger_
    if amount <= 0:
        return None

    mutex.acquire()
    try:
        if debit_acc.avail_balance >= amount:
            trx_id = str(ulid.new())
            now = datetime.now()

            debit_acc.balance -= amount
            debit_acc.avail_balance = debit_acc.balance
            debit_acc.updated_at = now

            credit_acc.balance += amount
            credit_acc.avail_balance = credit_acc.balance
            credit_acc.updated_at = now

            return trx_id
    finally:
        mutex.release()

    return None
