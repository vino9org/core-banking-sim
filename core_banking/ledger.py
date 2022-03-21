import csv
from datetime import datetime
from decimal import Decimal
from threading import Lock
from typing import Dict, Union

import ulid

from .models import CheckingAccount

_ledger_: Dict[str, CheckingAccount] = {}

mutex = Lock()


def init_from_csv(csv_file: str) -> None:
    global _ledger_
    with open(csv_file) as f:
        for row in csv.reader(f):
            acc_id = row[1]
            _ledger_[acc_id] = CheckingAccount(
                customer_id=row[0],
                account_id=acc_id,
                currency=row[2],
                avail_balance=row[3],
                balance=row[3],
                status=row[4],
            )


def get_account(account_id: str) -> Union[None, CheckingAccount]:
    global _ledger_
    try:
        return _ledger_[account_id]
    except KeyError:
        return None


def transfer(debit_acc: CheckingAccount, credit_acc: CheckingAccount, amount: Decimal) -> Union[None, str]:
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
