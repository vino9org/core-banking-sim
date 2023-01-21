import asyncio
import os
import sys

import pytest
from httpx import AsyncClient

cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(f"{cwd}/.."))
os.environ["NO_TRACING"] = "true"

from main import app  # noqa


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(app=app, base_url="http://localhost:8080") as client:
        yield client
