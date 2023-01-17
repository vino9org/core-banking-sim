import asyncio
import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Any

import boto3
import nats

from .models import FundTransfer

logger = logging.getLogger(__name__)

aws_client = None
nats_client = None


# handles serializatino of Decimal
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


_queue_: asyncio.Queue = asyncio.Queue(maxsize=50000)


def fund_transfer_event(transfer: FundTransfer) -> dict[Any, Any]:
    return {
        "Time": datetime.now(),
        "Source": "service.fund_transfer",
        "DetailType": "transfer",
        "EventBusName": "default",
        "Detail": json.dumps(dict(transfer), cls=JSONEncoder),
    }


async def enqueue_fund_transfer_event(transfer: FundTransfer) -> None:
    await _queue_.put(fund_transfer_event(transfer))


async def dequeue_events(count: int = 10) -> list[FundTransfer]:
    result = []
    for _ in range(0, min(count, _queue_.qsize())):
        result.append(await _queue_.get())
    return result


async def send_events(count: int):
    global aws_client, nats_client

    events = await dequeue_events(count)
    sink_type = os.environ.get("EVENT_SINK_TYPE", "")
    if events:
        if sink_type == "AWS_EVENTBRIDGE":
            logger.info(f"...send {len(events)} events to EventBridge...")
            aws_client = aws_client or boto3.client("events")
            response = aws_client.put_events(Entries=events)
            logger.info("put_events: ", response)
        elif sink_type == "NATS":
            nats_client = nats_client or await nats.connect(
                os.environ.get("NATS_SERVER_URL", "nats://nats.nats-system.svc.cluster.local:4222")
            )
            js = nats_client.jetstream()
            await js.add_stream(name="transfer-stream", subjects=["transfer.1"])
            for evt in events:
                await js.publish("transfer.1", json.dumps(evt).encode())
        else:
            logger.info("... NO EVENT_SINK_TYPE configured, skip publishing ...")
