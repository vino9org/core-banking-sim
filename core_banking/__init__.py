import logging
import os.path
from typing import Optional

from . import eventing, ledger, models

SEED_DATA_FILE = "seed.csv"

logger = logging.getLogger(__name__)


def load_seed_data() -> None:
    if os.path.isfile(SEED_DATA_FILE):
        logger.info("...looading seed data...")
        ledger.init_from_csv(SEED_DATA_FILE)


load_seed_data()


async def local_transfer(request: models.FundTransferRequest) -> Optional[models.FundTransfer]:
    if request.amount <= 0:
        logger.info("invalid local_transfer request: amount <= 0")
        return None

    debit_acc = await ledger.get_account(request.debit_account_id)
    if debit_acc is None or debit_acc.customer_id != request.debit_customer_id:
        logger.info("invalid local_transfer request: invalid debit account or customer id")
        return None

    credit_acc = await ledger.get_account(request.credit_account_id)
    if credit_acc is None:
        logger.info("invalid local_transfer request: invalid credit account")
        return None

    debit_prev_balance = debit_acc.balance
    credit_prev_balance = credit_acc.balance

    logger.info(
        f"processing local_transfer from {debit_acc.account_id} to {credit_acc.account_id} amount {request.amount}"
    )
    trx_id = await ledger.transfer(debit_acc, credit_acc, request.amount)
    if trx_id is None:
        logger.info("transfer cannot be processed!")
        return None

    transfer = models.FundTransfer(
        transaction_id=trx_id,
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

    logger.info(f"publishing event for local transfer {trx_id}")
    await eventing.enqueue_fund_transfer_event(transfer)

    return transfer
