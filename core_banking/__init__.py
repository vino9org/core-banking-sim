import logging
import os
from decimal import Decimal
from typing import Optional

from ulid import ULID

from . import eventing, ledger, models

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


async def local_transfer(request: models.FundTransferRequest) -> Optional[models.FundTransfer]:
    if request.amount <= 0:
        raise ValidationError("invalid amount: {request.amount}")

    # BYPASS=true will bypass all backend logic and return a dummy response
    # used in performance testing measure the fastest possible response time
    if os.environ.get("BYPASS") != "true":
        debit_acc = await ledger.get_account(request.debit_account_id)
        if debit_acc is None or debit_acc.customer_id != request.debit_customer_id:
            raise ValidationError("invalid debit account or customer id")

        if debit_acc.avail_balance < request.amount:
            raise ValidationError("insuffcient funds in debit account")

        credit_acc = await ledger.get_account(request.credit_account_id)
        if credit_acc is None:
            raise ValidationError("invalid credit account")

        logger.info(
            f"processing local_transfer from {debit_acc.account_id} to {credit_acc.account_id} amount {request.amount}"
        )

        ret = await ledger.transfer(debit_acc, credit_acc, request.amount)
        if ret is None:
            raise ValidationError("insuffcient funds in debit account")

        debit_acc_out, credit_acc_out, debit_acc_prev_bal, credit_acc_prev_bal = ret

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
    else:
        return models.FundTransfer(
            transaction_id=str(ULID()),
            debit_customer_id=request.debit_customer_id,
            debit_account_id=request.debit_account_id,
            debit_prev_avail_balance=Decimal(0.0),
            debit_prev_balance=Decimal(0.0),
            debit_avail_balance=Decimal(0.0),
            debit_balance=Decimal(0.0),
            credit_customer_id=request.credit_account_id,
            credit_account_id=request.credit_account_id,
            credit_prev_avail_balance=Decimal(0.0),
            credit_prev_balance=Decimal(0.0),
            credit_avail_balance=Decimal(0.0),
            credit_balance=Decimal(0.0),
            currency=request.currency,
            transfer_amount=request.amount,
            memo=request.memo,
            transaction_date=request.transaction_date,
            status="completed",
            ref_id=request.ref_id,
        )
