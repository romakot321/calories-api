import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
async def test_client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
