import csv
from decimal import Decimal
from typing import Optional, Tuple

from aredis_om import get_redis_connection
from aredis_om.model.model import NotFoundError

from .models import CheckingAccount


async def init_from_csv(csv_file, batch_size=1000) -> None:
    batch = []
    for row in csv.DictReader(csv_file, delimiter=",", dialect=csv.excel, quoting=csv.QUOTE_NONE):
        try:
            # extra fields the csv reader picks up that we don't need
            row.pop(None, "limit")
            row["pk"] = row["account_id"]
            batch.append(CheckingAccount(**row))
        except ValueError:
            # ignore lines with invalid data
            pass

        if len(batch) >= batch_size:
            await _batch_save_accounts(batch)
            batch.clear()

    if len(batch) >= 0:
        await _batch_save_accounts(batch)


async def _batch_save_accounts(batch: list[CheckingAccount]):
    conn = await get_redis_connection()
    async with await conn.pipeline() as pipe:
        for account in batch:
            await account.save(pipe)
        await pipe.execute()
    await conn.close()


async def get_account(account_id: str) -> Optional[CheckingAccount]:
    try:
        return await CheckingAccount.get(account_id)
    except NotFoundError:
        return None


async def transfer(
    debit_acc_in: CheckingAccount, credit_acc_in: CheckingAccount, amount: Decimal
) -> Optional[Tuple[CheckingAccount, CheckingAccount, Decimal, Decimal]]:
    conn = await get_redis_connection()

    try:
        await conn.watch(debit_acc_in.pk, credit_acc_in.pk)

        debit_acc = await CheckingAccount.get(debit_acc_in.pk)
        if debit_acc.avail_balance < amount:
            return None

        credit_acc = await CheckingAccount.get(credit_acc_in.pk)

        debit_prev_bal = debit_acc.balance
        credit_prev_bal = credit_acc.balance

        debit_bal = debit_prev_bal - amount
        credit_bal = credit_prev_bal + amount

        debit_acc.balance = debit_bal
        debit_acc.avail_balance = debit_bal
        credit_acc.balance = credit_bal
        credit_acc.avail_balance = credit_bal

        async with await conn.pipeline() as pipe:
            await debit_acc.save(pipe)
            await credit_acc.save(pipe)
            await pipe.execute()

        return debit_acc, credit_acc, debit_prev_bal, credit_prev_bal

    finally:
        await conn.close()
