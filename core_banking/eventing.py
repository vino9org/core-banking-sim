import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

import boto3

from .models import FundTransfer


# handles serializatino of Decimal
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


client = boto3.client("events")


def fund_transfer_event(transfer: FundTransfer) -> Dict[Any, Any]:
    return {
        "Time": datetime.now(),
        "Source": "service.fund_transfer",
        "DetailType": "transfer",
        "EventBusName": "default",
        "Detail": json.dumps(dict(transfer), cls=JSONEncoder),
    }


def send_fund_transfer_event(transfer: FundTransfer) -> None:
    event = fund_transfer_event(transfer)
    response = client.put_events(Entries=[event])
    print(response)
