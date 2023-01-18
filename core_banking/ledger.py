import csv
from decimal import Decimal
from typing import Optional, Tuple

from redis_om import get_redis_connection
from redis_om.model.model import NotFoundError

from .models import AccountCurrency, AccountStatus, CheckingAccount


def init_from_csv(csv_file, batch_size=1000) -> None:
    batch = []
    for row in csv.DictReader(csv_file):
        try:
            batch.append(_dict_to_account(row))
        except ValueError:
            # ignore lines with invalid data
            pass

        if len(batch) >= batch_size:
            _batch_save_accounts(batch)
            batch.clear()

    if len(batch) >= 0:
        _batch_save_accounts(batch)


def _dict_to_account(row: dict) -> CheckingAccount:
    return CheckingAccount(
        pk=row["account_id"],
        customer_id=row["customer_id"],
        account_id=row["account_id"],
        currency=AccountCurrency(row["currency"]),
        avail_balance=Decimal(row["avail_balance"]),
        balance=Decimal(row["balance"]),
        status=AccountStatus(int(row["status"])),
    )


def _batch_save_accounts(batch: list[CheckingAccount]) -> None:
    redis = get_redis_connection()
    with redis.pipeline() as pipe:
        pipe.multi()
        for account in batch:
            account.save(pipe)
        pipe.execute()


async def get_account(account_id: str) -> Optional[CheckingAccount]:
    try:
        return CheckingAccount.get(account_id)
    except NotFoundError:
        return None


async def transfer(
    debit_acc_in: CheckingAccount, credit_acc_in: CheckingAccount, amount: Decimal
) -> Optional[Tuple[CheckingAccount, CheckingAccount, Decimal, Decimal]]:
    redis = get_redis_connection()
    redis.watch(debit_acc_in.pk, credit_acc_in.pk)

    debit_acc = CheckingAccount.get(debit_acc_in.pk)
    if debit_acc.avail_balance < amount:
        return None

    credit_acc = CheckingAccount.get(credit_acc_in.pk)

    debit_prev_bal = debit_acc.balance
    credit_prev_bal = credit_acc.balance

    debit_bal = debit_prev_bal - amount
    credit_bal = credit_prev_bal + amount

    debit_acc.balance = debit_bal
    debit_acc.avail_balance = debit_bal
    credit_acc.balance = credit_bal
    credit_acc.avail_balance = credit_bal

    with redis.pipeline() as pipe:
        pipe.multi()
        debit_acc.save(pipe)
        credit_acc.save(pipe)
        pipe.execute()

    return debit_acc, credit_acc, debit_prev_bal, credit_prev_bal
