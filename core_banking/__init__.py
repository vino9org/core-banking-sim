import os.path
from typing import Optional, cast

from . import eventing, ledger, models

SEED_DATA_FILE = "seed.csv"


def load_seed_data() -> None:
    if os.path.isfile(SEED_DATA_FILE):
        print("...looading seed data...")
        ledger.init_from_csv(SEED_DATA_FILE)


load_seed_data()


async def local_transfer(request: models.FundTransferRequest) -> Optional[models.FundTransfer]:
    if request.amount <= 0:
        return None

    debit_acc = cast(models.CheckingAccount, await ledger.get_account(request.debit_account_id))
    if debit_acc is not None and debit_acc.customer_id != request.debit_customer_id:
        return None

    credit_acc = await ledger.get_account(request.credit_account_id)
    if credit_acc is None:
        return None

    debit_prev_balance = debit_acc.balance
    credit_prev_balance = credit_acc.balance

    trx_id = await ledger.transfer(debit_acc, credit_acc, request.amount)

    transfer = models.FundTransfer(
        transaction_id=cast(str, trx_id),
        debit_customer_id=request.debit_customer_id,
        debit_account_id=request.debit_account_id,
        debit_prev_avail_balance=debit_prev_balance,
        debit_prev_balance=debit_prev_balance,
        debit_avail_balance=debit_acc.avail_balance,
        debit_balance=debit_acc.balance,
        credit_customer_id=credit_acc.customer_id,
        credit_account_id=request.credit_account_id,
        credit_prev_avail_balance=credit_prev_balance,
        credit_prev_balance=credit_prev_balance,
        credit_avail_balance=credit_acc.avail_balance,
        credit_balance=credit_acc.balance,
        currency=request.currency,
        transfer_amount=request.amount,
        memo=request.memo,
        transaction_date=request.transaction_date,
        status="completed",
        limits_req_id=request.limits_req_id,
    )

    await eventing.enqueue_fund_transfer_event(transfer)

    return transfer
