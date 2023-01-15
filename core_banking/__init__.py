import logging
from typing import Optional

from ulid import ULID

from . import eventing, ledger, models

logger = logging.getLogger(__name__)


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

    logger.info(
        f"processing local_transfer from {debit_acc.account_id} to {credit_acc.account_id} amount {request.amount}"
    )

    try:
        debit_acc_out, credit_acc_out, debit_acc_prev_bal, credit_acc_prev_bal = await ledger.transfer(
            debit_acc, credit_acc, request.amount
        )

        transfer = models.FundTransfer(
            transaction_id=str(ULID()),
            debit_customer_id=request.debit_customer_id,
            debit_account_id=request.debit_account_id,
            debit_prev_avail_balance=debit_acc_prev_bal,
            debit_prev_balance=debit_acc_prev_bal,
            debit_avail_balance=debit_acc_out.avail_balance,
            debit_balance=debit_acc_out.balance,
            credit_customer_id=credit_acc_out.customer_id,
            credit_account_id=request.credit_account_id,
            credit_prev_avail_balance=credit_acc_prev_bal,
            credit_prev_balance=credit_acc_prev_bal,
            credit_avail_balance=credit_acc_out.avail_balance,
            credit_balance=credit_acc_out.balance,
            currency=request.currency,
            transfer_amount=request.amount,
            memo=request.memo,
            transaction_date=request.transaction_date,
            status="completed",
            ref_id=request.ref_id,
        )

        logger.info(f"publishing event for local transfer {request.ref_id}")
        await eventing.enqueue_fund_transfer_event(transfer)

        return transfer
    except Exception as e:
        logger.info(f"transfer cannot be processed due to {e}")
        return None
