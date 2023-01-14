import csv
from decimal import Decimal
from typing import Optional, Tuple

from redis_om import get_redis_connection
from retrying import retry

from .models import AccountCurrency, AccountStatus, CheckingAccount


def init_from_csv(csv_file: str) -> None:
    with open(csv_file) as f:
        for row in csv.DictReader(f):
            dict_to_account(row).save()


def dict_to_account(row: dict) -> CheckingAccount:
    return CheckingAccount(
        pk=row["account_id"],
        customer_id=row["customer_id"],
        account_id=row["account_id"],
        currency=AccountCurrency(row["currency"]),
        avail_balance=Decimal(row["avail_balance"]),
        balance=Decimal(row["balance"]),
        status=AccountStatus(int(row["status"])),
    )


def get_account(account_id: str) -> Optional[CheckingAccount]:
    return CheckingAccount.get(account_id)


@retry(stop_max_attempt_number=3, wait_random_min=200, wait_random_max=500)
async def transfer(
    debit_acc_in: CheckingAccount, credit_acc_in: CheckingAccount, amount: Decimal
) -> Tuple[CheckingAccount, CheckingAccount, Decimal, Decimal]:
    redis = get_redis_connection()
    redis.watch(debit_acc_in.pk, credit_acc_in.pk)

    debit_acc = CheckingAccount.get(debit_acc_in.pk)
    if debit_acc.avail_balance < amount:
        raise ValueError("insufficient funds")

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
