from typing import Union

from . import eventing, ledger, models


def local_transfer(request: models.FundTransferRequest) -> Union[None, models.FundTransfer]:
    if request.amount <= 0:
        return None

    debit_acc = ledger.get_account(request.account_id)
    if debit_acc is not None and debit_acc.customer_id != request.customer_id:
        return None

    credit_acc = ledger.get_account(request.credit_account_id)
    if credit_acc is None:
        return None

    prev_balance = debit_acc.balance
    trx_id = ledger.transfer(debit_acc, credit_acc, request.amount)

    transfer = models.FundTransfer(
        transaction_id=trx_id,
        customer_id=request.customer_id,
        account_id=request.account_id,
        credit_account_id=request.credit_account_id,
        currency=request.currency,
        transfer_amount=request.amount,
        memo=request.memo,
        transaction_date=request.transaction_date,
        prev_avail_balance=prev_balance,
        prev_balance=prev_balance,
        new_avail_balance=debit_acc.avail_balance,
        new_balance=debit_acc.balance,
        status="completed",
        limits_req_id=request.limits_req_id,
    )

    eventing.send_fund_transfer_event(transfer)

    return transfer
