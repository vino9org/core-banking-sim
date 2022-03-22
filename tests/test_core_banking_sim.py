import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import main
from core_banking import eventing, ledger, local_transfer, models


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
    client = TestClient(main.app)
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


async def test_corebanking_api(seed_csv_file) -> None:
    ledger.init_from_csv(seed_csv_file)

    request = models.FundTransferRequest(
        customer_id="C11",
        account_id="A11",
        credit_account_id="A22",
        amount=Decimal("99.98"),
        currency="SGD",
        transaction_date="2022-03-21",
        memo="test transfer from pytest",
        limits_req_id="AAAA",
    )

    transfer = await local_transfer(request)

    assert transfer
    assert transfer.new_balance == Decimal("900.14")
    assert eventing._queue_.qsize() == 1
