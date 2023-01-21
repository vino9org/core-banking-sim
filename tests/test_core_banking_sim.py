from decimal import Decimal
from io import BytesIO, StringIO

import pytest

from core_banking import eventing, ledger, models

_TEST_DATA_ = """customer_id,account_id,currency,avail_balance,balance,status,limit
C11,A11,SGD,1000.12,1000.12,1,2000.00,
C22,A22,SGD,2000.00,2000.00,1,2000.00,
"""


@pytest.fixture
async def seed_csv_file():
    yield await ledger.init_from_csv(StringIO(_TEST_DATA_))


async def test_probes(client) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200

    response = await client.get("/ready")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_ledger(seed_csv_file) -> None:
    acc1 = await ledger.get_account("A11")
    assert acc1 is not None
    assert acc1.avail_balance == Decimal("1000.12")

    acc2 = await ledger.get_account("A22")
    assert acc2 is not None
    assert acc2.avail_balance == Decimal(2000)

    assert await ledger.get_account("AXX") is None

    result = await ledger.transfer(acc1, acc2, Decimal("123.45"))
    assert result is not None

    _, acc2_out, _, _ = result
    assert acc2_out.avail_balance == Decimal("2123.45")


async def test_local_transfer_api(client, seed_csv_file) -> None:
    request = models.FundTransferRequest(
        ref_id="uniq_id",
        debit_customer_id="C11",
        debit_account_id="A11",
        credit_account_id="A22",
        amount=Decimal("99.98"),
        currency="SGD",
        transaction_date="2022-03-21",
        memo="test transfer from pytest",
    )

    prev_q_size = eventing._queue_.qsize()

    response = await client.post(
        "/core-banking/local-transfers", headers={"Content-Type": "application/json"}, data=request.json()
    )
    assert response.status_code == 200

    transfer = models.FundTransfer.parse_obj(response.json())
    assert transfer.debit_prev_balance == Decimal("1000.12")
    assert transfer.debit_balance == Decimal("900.14")
    assert transfer.credit_prev_balance == Decimal("2000.00")
    assert transfer.credit_balance == Decimal("2099.98")

    assert eventing._queue_.qsize() == prev_q_size + 1


async def test_invalid_local_transfer(client, seed_csv_file) -> None:
    request = models.FundTransferRequest(
        debit_customer_id="INVALID",
        debit_account_id="DOES NOT EXIST",
        credit_account_id="A22",
        amount=Decimal("-99.98"),
        currency="SGD",
        transaction_date="2022-03-21",
        memo="test transfer from pytest",
        ref_id="AAAA",
    )

    prev_q_size = eventing._queue_.qsize()

    response = await client.post(
        "/core-banking/local-transfers", headers={"Content-Type": "application/json"}, data=request.json()
    )
    assert response.status_code == 422
    assert eventing._queue_.qsize() == prev_q_size


async def test_get_account_by_id(client, seed_csv_file) -> None:
    response = await client.get("/core-banking/accounts/A22")
    assert response.status_code == 200
    assert len(response.json()) > 1


async def test_get_account_by_invalid_id(client, seed_csv_file) -> None:
    response = await client.get("/core-banking/accounts/AXX")
    assert response.status_code == 404


async def test_seed_accounts(client, seed_csv_file) -> None:
    response = await client.post(
        "/core-banking/_internal/seed/",
        files={"content-type": "text/csv", "upload_file": BytesIO(_TEST_DATA_.encode("utf-8"))},
    )
    assert response.status_code == 200

    response = await client.get("/core-banking/accounts/A11")
    assert response.status_code == 200
    assert len(response.json()) > 1

    response = await client.get("/core-banking/accounts/A22")
    assert response.status_code == 200
    assert len(response.json()) > 1

    response = await client.get("/core-banking/accounts/AXX")
    assert response.status_code == 404
