import asyncio
import os
import random
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import main
from core_banking import ledger, local_transfer, models
from seed_data import account_for

debit_acc, credit_acc, test_request = None, None, None

ROUNDS = int(os.environ.get("BENCH_ROUNDS", 1000))

client = TestClient(main.app)


def setup_benchmark_test_accounts():
    global debit_acc, credit_acc, test_request
    debit_acc = ledger._dict_to_account(account_for(random.randint(10000, 20000)))
    credit_acc = ledger._dict_to_account(account_for(random.randint(10000, 20000)))
    debit_acc.save()
    credit_acc.save()
    test_request = models.FundTransferRequest(
        debit_customer_id=debit_acc.customer_id,
        debit_account_id=debit_acc.account_id,
        credit_account_id=credit_acc.account_id,
        amount=Decimal(1.0),
        currency="SGD",
        transaction_date=str(date.today()),
        memo="blah",
        ref_id=f"ref_id for {debit_acc.account_id} to {credit_acc.account_id}",
    )


def call_transfer_api():
    loop = asyncio.get_event_loop()
    coroutine = ledger.transfer(debit_acc, credit_acc, Decimal(1.0))
    loop.run_until_complete(coroutine)


def call_ledger_transfer():
    loop = asyncio.get_event_loop()
    coroutine = local_transfer(test_request)
    loop.run_until_complete(coroutine)


def post_to_transfer_api():
    response = client.post(
        "/core-banking/local-transfers", headers={"Content-Type": "application/json"}, data=test_request.json()
    )
    assert response.status_code == 200


@pytest.mark.skipif(os.environ.get("BENCH") != "1", reason="Benchmarks are not run by default")
def test_ledger_transfer(benchmark):
    benchmark.pedantic(
        call_ledger_transfer,
        setup=setup_benchmark_test_accounts,
        rounds=ROUNDS,
        iterations=1,
    )


@pytest.mark.skipif(os.environ.get("BENCH") != "1", reason="Benchmarks are not run by default")
def test_transer_api(benchmark):
    benchmark.pedantic(
        call_transfer_api,
        setup=setup_benchmark_test_accounts,
        rounds=ROUNDS,
        iterations=1,
    )


@pytest.mark.skipif(os.environ.get("BENCH") != "1", reason="Benchmarks are not run by default")
def test_http_transfer_api(benchmark):
    benchmark.pedantic(
        post_to_transfer_api,
        setup=setup_benchmark_test_accounts,
        rounds=ROUNDS,
        iterations=1,
    )
