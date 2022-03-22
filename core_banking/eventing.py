import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

import boto3

from .models import FundTransfer


# handles serializatino of Decimal
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


_queue_: asyncio.Queue = asyncio.Queue(maxsize=10000)
client = boto3.client("events")


def fund_transfer_event(transfer: FundTransfer) -> Dict[Any, Any]:
    return {
        "Time": datetime.now(),
        "Source": "service.fund_transfer",
        "DetailType": "transfer",
        "EventBusName": "default",
        "Detail": json.dumps(dict(transfer), cls=JSONEncoder),
    }


async def enqueue_fund_transfer_event(transfer: FundTransfer) -> None:
    await _queue_.put(fund_transfer_event(transfer))


async def dequeue_events(count: int = 10) -> List[FundTransfer]:
    result = []
    for _ in range(0, min(count, _queue_.qsize())):
        result.append(await _queue_.get())
    return result


async def send_events(count: int):
    events = await dequeue_events(count)
    print(f"...send {len(events)} events to EventBridge...")
    if events:
        response = client.put_events(Entries=events)
        print(response)
