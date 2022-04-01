import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import main
from core_banking import eventing, ledger, models

client = TestClient(main.app)


@pytest.fixture
def seed_csv_file(tmpdir):
    tmp_csv = tmpdir.join(f"test_{uuid.uuid1().hex}.csv")
    print(f"tmp_file={tmp_csv}\n")
    with open(tmp_csv, "w") as f:
        f.write("cust_id,acc_id,currency,balance,status,limit\n")
        f.write("C11,A11,SGD,1000.12,active,2000.00,\n")
        f.write("C22,A22,SGD,2000.00,active,2000.00,\n")
    yield tmp_csv


def test_probes() -> None:
    assert client.get("/healthz").status_code == 200
    assert client.get("/ready").status_code == 200


async def test_ledger(seed_csv_file) -> None:
    ledger.init_from_csv(seed_csv_file)

    acc1 = await ledger.get_account("A11")
    assert acc1 is not None
    assert acc1.avail_balance == Decimal("1000.12")

    acc2 = await ledger.get_account("A22")
    assert acc2 is not None
    assert acc2.avail_balance == Decimal(2000)

    assert await ledger.get_account("AXX") is None

    trx_id = await ledger.transfer(acc1, acc2, Decimal("123.45"))
    assert trx_id

    assert acc2.avail_balance == Decimal("2123.45")


async def test_local_transfer_api(seed_csv_file) -> None:
    ledger.init_from_csv(seed_csv_file)

    request = models.FundTransferRequest(
        debit_customer_id="C11",
        debit_account_id="A11",
        credit_account_id="A22",
        amount=Decimal("99.98"),
        currency="SGD",
        transaction_date="2022-03-21",
        memo="test transfer from pytest",
        limits_req_id="AAAA",
    )

    prev_q_size = eventing._queue_.qsize()

    response = client.post(
        "/core-banking/local-transfers", headers={"Content-Type": "application/json"}, data=request.json()
    )
    assert response.status_code == 200

    transfer = models.FundTransfer.parse_obj(response.json())
    assert transfer.debit_prev_balance == Decimal("1000.12")
    assert transfer.debit_balance == Decimal("900.14")
    assert transfer.credit_prev_balance == Decimal("2000.00")
    assert transfer.credit_balance == Decimal("2099.98")
    assert eventing._queue_.qsize() == prev_q_size + 1


async def test_invalid_local_transfer(seed_csv_file) -> None:
    ledger.init_from_csv(seed_csv_file)

    request = models.FundTransferRequest(
        debit_customer_id="INVALID",
        debit_account_id="DOES NOT EXIST",
        credit_account_id="A22",
        amount=Decimal("-99.98"),
        currency="SGD",
        transaction_date="2022-03-21",
        memo="test transfer from pytest",
        limits_req_id="AAAA",
    )

    prev_q_size = eventing._queue_.qsize()

    response = client.post(
        "/core-banking/local-transfers", headers={"Content-Type": "application/json"}, data=request.json()
    )
    assert response.status_code == 400
    assert eventing._queue_.qsize() == prev_q_size


async def test_get_all_accounts() -> None:
    response = client.get("/core-banking/accounts")
    assert response.status_code == 200
    assert len(response.json()) > 1
