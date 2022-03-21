import uuid
from decimal import Decimal

import pytest
from botocore.stub import Stubber
from fastapi.testclient import TestClient

import main
from core_banking import eventing, ledger, local_transfer, models


@pytest.fixture
def seed_csv_file(tmpdir):
    tmp_csv = tmpdir.join(f"test_{uuid.uuid1().hex}.csv")
    print(f"tmp_file={tmp_csv}\n")
    with open(tmp_csv, "w") as f:
        f.write("C11,A11,SGD,1000.12,active,\n")
        f.write("C22,A22,SGD,2000.00,active,\n")
    yield tmp_csv


def test_probes() -> None:
    client = TestClient(main.app)
    assert client.get("/healthz").status_code == 200
    assert client.get("/ready").status_code == 200


def test_ledger(seed_csv_file) -> None:
    ledger.init_from_csv(seed_csv_file)

    acc1 = ledger.get_account("A11")
    assert acc1 is not None
    assert acc1.avail_balance == Decimal("1000.12")

    acc2 = ledger.get_account("A22")
    assert acc2 is not None
    assert acc2.avail_balance == Decimal(2000)

    assert ledger.get_account("AXX") is None

    trx_id = ledger.transfer(acc1, acc2, Decimal("123.45"))
    assert trx_id

    assert acc2.avail_balance == Decimal("2123.45")


def test_corebanking_api(seed_csv_file) -> None:
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

    stubber = Stubber(eventing.client)
    stubber.add_response("put_events", {})
    stubber.activate

    with stubber:
        transfer = local_transfer(request)

    stubber.assert_no_pending_responses()

    assert transfer
    assert transfer.new_balance == Decimal("900.14")
